"""Run published shell wrappers with inert sources and fake generators only.

Every shared output and temporary-directory template is redirected into a
TemporaryDirectory. No real /tmp/cc-out, seed, compiler, or bootstrap runs.
Run with: python3 -m unittest discover -s tools/tests -p test_checkpoint_safety.py -v
"""

import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


BOOK = Path(__file__).resolve().parents[2] / "book"
SHELL_FENCE = re.compile(r"^```sh\n(.*?)^```$", re.M | re.S)
TEMPLATE = "/tmp/book-probe.XXXXXXXXXX"


def fences(chapter):
    path, = [p for p in BOOK.glob(f"{chapter:02d}-*.md")
             if p.name != "34-direct-tinycc.md"]
    return [m[1] for m in SHELL_FENCE.finditer(path.read_text())]


class CheckpointSafetyTests(unittest.TestCase):
    def setUp(self):
        # Short, space-free fixture paths also fit the book's Forth token rule.
        self.temp = tempfile.TemporaryDirectory(prefix="book-safety-", dir="/tmp")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def directory(self, name):
        path = self.root / name
        path.mkdir()
        return path

    def isolate(self, body, directory):
        self.assertIn(TEMPLATE, body)
        body = body.replace("/tmp/cc-out", str(directory / "cc-out"))
        body = body.replace(TEMPLATE, str(directory / "book-probe.XXXXXXXXXX"))
        self.assertNotIn("/tmp/cc-out", body)
        # Fail closed if a later checkpoint edit introduces another /tmp path.
        self.assertNotIn("/tmp/", body.replace(str(self.root), "FIXTURE_ROOT"))
        return body

    def run_shell(self, body, directory, errexit):
        env = {k: v for k, v in os.environ.items()
               if k not in ("BASH_ENV", "ENV", "SHELLOPTS", "BASHOPTS")}
        command = ["bash"] + (["-e"] if errexit else []) + ["-c", body]
        return subprocess.run(command, cwd=directory, env=env,
                              text=True, capture_output=True, timeout=10)

    def assert_status(self, result, expected):
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)

    def inert_sources(self, body, directory):
        for relative in re.findall(r"\b(?:forth|cc)/[\w.-]+\.fth", body):
            path = directory / relative
            path.parent.mkdir(exist_ok=True)
            path.touch()

    def fake_generator(self, directory, status, generator_fails=False, shared=False):
        # Consume all input, avoiding unrelated SIGPIPE effects in producers.
        executable = "#!/bin/sh\n#" + " padding" * 25 + f"\nexit {status}\n"
        script = "#!/bin/bash\ncat > /dev/null\n"
        if shared:
            output = directory / "cc-out"
            script += f"cat > '{output}' <<'PROGRAM'\n{executable}PROGRAM\n"
        else:
            script += f"cat <<'PROGRAM'\n{executable}PROGRAM\n"
        script += "exit 17\n" if generator_fails else "exit 0\n"
        path = directory / "seed-forth"
        path.write_text(script)
        path.chmod(0o755)

    def test_all_canonical_checkpoint_fences_parse(self):
        count = 0
        for chapter in range(27, 50):
            for index, body in enumerate(fences(chapter)):
                with self.subTest(chapter=chapter, fence=index):
                    result = subprocess.run(["bash", "-n"], input=body,
                                            text=True, capture_output=True, timeout=10)
                    self.assert_status(result, 0)
                    count += 1
        self.assertGreaterEqual(count, 27)

    def test_forth_generated_paths_use_checked_short_template(self):
        for chapter in range(40, 50):
            for index, body in enumerate(fences(chapter)):
                if "s, %s" not in body:
                    continue
                with self.subTest(chapter=chapter, fence=index):
                    self.assertIn(f'work=$(mktemp -d {TEMPLATE}) || exit "$?"', body)
                    self.assertLess(len(TEMPLATE.replace("XXXXXXXXXX", "0123456789")
                                        + "/caller.o"), 255)

    def test_shared_output_preservation_failure_paths(self):
        kinds = ("normal", "absent", "symlink", "directory", "backup_fail",
                 "restore_fail", "remove_fail", "mktemp_fail", "generation_fail",
                 "assert_fail", "signal")
        for chapter, index in ((38, 0), (38, 1), (39, 0), (44, 0)):
            for kind in kinds:
                for errexit in (False, True):
                    with self.subTest(chapter=chapter, fence=index,
                                      kind=kind, errexit=errexit):
                        self.shared_case(chapter, index, kind, errexit)

    def shared_case(self, chapter, index, kind, errexit):
        directory = self.directory(f"shared-{chapter}-{index}-{kind}-{errexit}")
        original = directory / "cc-out"
        if kind == "symlink":
            original.symlink_to("missing-target")
        elif kind == "directory":
            original.mkdir()
            (original / "precious").write_text("original")
        elif kind != "absent":
            original.write_text("original")
        body = fences(chapter)[index]
        markers = ("compiler_status=0\n", "layers=$(cc/compiler-layers.sh)",
                   "stage_status=0\n")
        cut = min(body.index(marker) for marker in markers if marker in body)
        # Test the published preservation preamble/trap with controlled outcomes.
        body = self.isolate(body[:cut], directory)
        prefix = ""
        if kind in ("backup_fail", "restore_fail"):
            comparison = "!=" if kind == "backup_fail" else "=="
            # mv -T -- SOURCE DEST: SOURCE is positional argument 3.
            prefix = ('mv() { if [[ "$3" ' + comparison + ' *saved-cc-out ]]; '
                      'then return 73; fi; command mv "$@"; }\n')
        elif kind == "mktemp_fail":
            prefix = "mktemp() { return 72; }\n"
        elif kind == "remove_fail":
            prefix = ('rm() { if [[ "$3" == "' + str(original) + '" ]]; '
                      'then return 74; fi; command rm "$@"; }\n')
        final = f'printf generated > "{original}"\n'
        final += {"assert_fail": "test 1 -eq 2\n", "generation_fail": "exit 17\n",
                  "signal": 'kill -TERM "$BASHPID"\n'}.get(kind, "exit 0\n")
        result = self.run_shell(prefix + body + final + ")\n", directory, errexit)
        backups = list(directory.glob("book-probe.*/saved-cc-out"))
        if kind == "backup_fail":
            self.assert_status(result, 1)
            self.assertEqual(original.read_text(), "original")
            self.assertEqual(backups, [])
        elif kind == "mktemp_fail":
            self.assert_status(result, 72)
            self.assertEqual(original.read_text(), "original")
        elif kind in ("restore_fail", "remove_fail"):
            self.assert_status(result, 1)
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(), "original")
            self.assertIn(str(backups[0].parent), result.stderr)
        elif kind == "absent":
            self.assert_status(result, 0)
            self.assertFalse(original.exists())
        elif kind == "symlink":
            self.assert_status(result, 0)
            self.assertTrue(original.is_symlink())
            self.assertEqual(os.readlink(original), "missing-target")
        elif kind == "directory":
            self.assert_status(result, 0)
            self.assertEqual((original / "precious").read_text(), "original")
        else:
            expected = {"generation_fail": 17, "assert_fail": 1, "signal": 143}.get(kind, 0)
            self.assert_status(result, expected)
            self.assertEqual(original.read_text(), "original")
        if kind not in ("backup_fail", "restore_fail", "remove_fail", "mktemp_fail"):
            self.assertEqual(list(directory.glob("book-probe.*")), [])

    def test_private_output_complete_wrappers(self):
        expected = {31: 42, 32: 0, 33: 14, 34: 7, 35: 1, 36: 8, 37: 7}
        modes = ("success", "generator_fail", "program_fail", "mktemp_fail")
        for chapter, correct in expected.items():
            for mode in modes:
                for errexit in (False, True):
                    with self.subTest(chapter=chapter, mode=mode, errexit=errexit):
                        directory = self.directory(f"private-{chapter}-{mode}-{errexit}")
                        body = self.isolate(fences(chapter)[0], directory)
                        self.inert_sources(body, directory)
                        self.fake_generator(directory, 99 if mode == "program_fail" else correct,
                                            generator_fails=mode == "generator_fail")
                        if mode == "mktemp_fail":
                            body = "mktemp() { return 72; }\n" + body
                        result = self.run_shell(body, directory, errexit)
                        want = {"success": 0, "generator_fail": 17,
                                "program_fail": 1, "mktemp_fail": 72}[mode]
                        self.assert_status(result, want)
                        self.assertEqual(list(directory.glob("book-probe.*")), [])
                        if mode == "generator_fail":
                            self.assertNotIn("program exit:", result.stdout)
                            self.assertNotIn("exit status)", result.stdout)

    def test_shared_output_complete_wrappers(self):
        for chapter, correct in ((38, 0), (39, 40), (44, 0)):
            for mode in ("success", "generator_fail", "program_fail"):
                for errexit in (False, True):
                    with self.subTest(chapter=chapter, mode=mode, errexit=errexit):
                        directory = self.directory(f"complete-{chapter}-{mode}-{errexit}")
                        original = directory / "cc-out"
                        original.write_text("original")
                        body = self.isolate(fences(chapter)[0], directory)
                        self.inert_sources(body, directory)
                        helper = directory / "cc/compiler-layers.sh"
                        helper.parent.mkdir(exist_ok=True)
                        helper.write_text("#!/bin/sh\nprintf 'cc/120-cc-main.fth\\n'\n")
                        helper.chmod(0o755)
                        (directory / "cc/120-cc-main.fth").touch()
                        self.fake_generator(directory, 99 if mode == "program_fail" else correct,
                                            generator_fails=mode == "generator_fail", shared=True)
                        result = self.run_shell(body, directory, errexit)
                        self.assert_status(result, {"success": 0, "generator_fail": 17,
                                                    "program_fail": 1}[mode])
                        self.assertEqual(original.read_text(), "original")
                        self.assertEqual(list(directory.glob("book-probe.*")), [])
                        if mode == "generator_fail":
                            self.assertNotIn("program exit:", result.stdout)
                            self.assertNotIn("target contract exit:", result.stdout)

    def test_failed_stage_a_retains_work_and_restores_output(self):
        for errexit in (False, True):
            with self.subTest(errexit=errexit):
                directory = self.directory(f"stage-failure-{errexit}")
                original = directory / "cc-out"
                original.write_text("original")
                fake = directory / "tests/cc/stage-a-check.sh"
                fake.parent.mkdir(parents=True)
                fake.write_text('#!/bin/bash\nmkdir -p "$BUILDROOT"\n'
                                'printf diagnostic > "$BUILDROOT/log"\nexit 19\n')
                fake.chmod(0o755)
                body = self.isolate(fences(38)[1], directory)
                result = self.run_shell(body, directory, errexit)
                self.assert_status(result, 19)
                self.assertEqual(original.read_text(), "original")
                retained = list(directory.glob("book-probe.*"))
                self.assertEqual(len(retained), 1)
                self.assertEqual((retained[0] / "stage-a/log").read_text(), "diagnostic")
                self.assertIn(str(retained[0]), result.stdout)
                self.assertFalse((retained[0] / "saved-cc-out").exists())


if __name__ == "__main__":
    unittest.main()
