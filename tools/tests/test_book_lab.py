"""Exercise the reader CLI with isolated Markdown and an inert seed only."""

import contextlib
import importlib.util
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    "book_lab", Path(__file__).resolve().parents[1] / "book-lab.py")
LAB = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LAB)


class Output(io.TextIOWrapper):
    def __init__(self):
        super().__init__(io.BytesIO(), encoding="utf-8")

    def bytes(self):
        self.flush()
        return self.buffer.getvalue()


class BookLabTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="book-lab-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.book = self.root / "book"
        self.book.mkdir()
        self.source = self.root / "source checkout"
        (self.source / "seed").mkdir(parents=True)
        (self.source / "seed/000-seed.hex0").touch()
        seed = self.source / "seed-forth"
        seed.write_text("#!/bin/sh\ncat\n")
        seed.chmod(0o755)
        for name, value in (("BOOK", str(self.book)), ("ROOT", str(self.source)),
                            ("BOOK_ROOT", str(self.root))):
            patcher = patch.object(LAB.TRYIT, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        for name, value in (("system", "Linux"), ("machine", "x86_64")):
            patcher = patch.object(LAB.platform, name, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def publish(self, text, chapter=26):
        path = self.book / f"{chapter:02d}-fixture.md"
        path.write_text(text, encoding="utf-8")
        with (self.book / "SUMMARY.md").open("a") as summary:
            summary.write(f"- [Fixture]({path.name})\n")
        return path

    def fence(self, body, metadata="", chapter=26):
        self.publish(metadata + "\n```sh\n" + body + "\n```\n", chapter)

    def cli(self, *arguments):
        stdout, stderr = Output(), Output()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            status = LAB.main(list(arguments))
        return status, stdout.bytes(), stderr.bytes()

    def test_selectors_include_excluded_fences_but_not_transcripts_or_source(self):
        self.publish("```text\noutput\n```\n```\ntranscript\n```\n"
                     "```forth file=example.fth\nbye\n```\n"
                     "<!-- tryit: skip -->\n```sh\nprintf skipped | ./seed-forth\n```\n"
                     "```bash\nprintf chosen | ./seed-forth\n```\n")
        retired = self.book / "26-retired.md"
        retired.write_text("```sh\nfalse\n```\n")
        self.assertEqual([lab["selector"] for lab in LAB.inventory()], ["26.1", "26.2"])
        status, stdout, _ = self.cli("list", "26")
        self.assertEqual(status, 0)
        self.assertIn(b"26.1   EXCLUDED", stdout)
        self.assertIn(b"26.2   READY", stdout)
        self.assertIn(b"requires: Linux x86-64", stdout)
        self.assertEqual(self.cli("run", "26.2")[1], b"chosen")

    def test_show_reads_exact_current_fence_even_when_excluded(self):
        body = "# Keep spacing and a blank line.\n\nprintf 'x  y\\n' | ./seed-forth\n"
        path = self.publish("<!-- tryit: skip -->\n```sh\n" + body + "```\n")
        self.assertEqual(self.cli("show", "26.1"), (0, body.encode(), b""))
        path.write_text(path.read_text().replace("x  y", "changed"))
        self.assertIn(b"changed", self.cli("show", "26.1")[1])

    def test_run_uses_source_root_and_preserves_exact_output_bytes(self):
        self.fence("test -f seed/000-seed.hex0 || exit 4\nprintf '\\377' | ./seed-forth")
        status, output, errors = self.cli("run", "26.1")
        self.assertEqual((status, output), (0, b"\xff"))
        self.assertIn(b"no expected-output metadata", errors)
        self.assertIn(str(self.source).encode(), errors)

    def test_expectation_checks_utf8_and_trailing_newlines(self):
        self.fence("printf 'é\\n\\n' | ./seed-forth", '<!-- tryit: expect "é" -->')
        status, stdout, stderr = self.cli("run", "26.1")
        self.assertEqual(status, 0, stderr)
        self.assertEqual(stdout, "é\n\n".encode())
        self.assertIn(b"stdout matches expected metadata", stderr)

    def test_expectation_mismatch_is_failure(self):
        self.fence("printf wrong | ./seed-forth", '<!-- tryit: expect "right" -->')
        status, _, stderr = self.cli("run", "26.1")
        self.assertEqual(status, 1)
        self.assertIn(b"expected UTF-8 stdout 'right'", stderr)

    def test_nonzero_shell_status_is_preserved(self):
        self.fence("printf ok | ./seed-forth\nexit 19", '<!-- tryit: expect "ok" -->')
        status, stdout, stderr = self.cli("run", "26.1")
        self.assertEqual((status, stdout), (19, b"ok"))
        self.assertIn(b"shell exited 19", stderr)

    def test_deliberate_nonzero_program_status_can_be_handled_by_fence(self):
        self.fence("status=0\n./seed-forth < /dev/null\n"
                   "bash -c 'exit 42' || status=$?\ntest \"$status\" -eq 42")
        self.assertEqual(self.cli("run", "26.1")[0], 0)

    def test_runner_does_not_inject_errexit_or_pipefail(self):
        self.fence("false | ./seed-forth\nprintf 'pipeline status %s' \"$?\"\n"
                   "false\nprintf ' reached end'",
                   '<!-- tryit: expect "pipeline status 0 reached end" -->')
        self.assertEqual(self.cli("run", "26.1")[0], 0)

    def test_unsafe_to_automate_fences_never_start_process(self):
        cases = [("<!-- tryit: skip -->", "printf ok | ./seed-forth", 26),
                 ("<!-- tryit: loops -->", "printf ok | ./seed-forth", 26),
                 ("", "tests/cc/stage-a-check.sh\nprintf ok | ./seed-forth", 38),
                 ("", "printf ok | ./seed-forth", 50),
                 ("", "cd forth-bootstrap && ./seed/build.sh", 4),
                 ("", "./seed-forth", 26),
                 ("<!-- tryit: expect nope -->", "printf ok | ./seed-forth", 26)]
        for metadata, body, chapter in cases:
            with self.subTest(body=body, metadata=metadata, chapter=chapter):
                (self.book / "SUMMARY.md").unlink(missing_ok=True)
                self.fence(body, metadata, chapter)
                with patch.object(LAB.subprocess, "Popen") as popen:
                    status, _, stderr = self.cli("run", f"{chapter}.1")
                self.assertEqual(status, 2, stderr)
                self.assertIn(b"excluded", stderr)
                popen.assert_not_called()

    def test_missing_checkout_and_seed_provide_setup_commands(self):
        self.fence("printf ok | ./seed-forth")
        (self.source / "seed/000-seed.hex0").unlink()
        (self.source / "seed-forth").unlink()
        status, _, stderr = self.cli("run", "26.1")
        self.assertEqual(status, 2)
        self.assertIn(b"git submodule update --init --recursive", stderr)
        self.assertIn(b"./seed/build.sh", stderr)

    def test_source_globs_are_prerequisites_not_truncated_paths(self):
        (self.source / "cc").mkdir()
        (self.source / "cc/020-cc-arena.fth").write_text("hello")
        self.fence("cat cc/0[2-9]*-cc-*.fth | ./seed-forth")
        self.assertEqual(self.cli("run", "26.1")[:2], (0, b"hello"))
        (self.source / "cc/020-cc-arena.fth").unlink()
        self.assertIn(b"missing source prerequisite: cc/0[2-9]*-cc-*.fth",
                      self.cli("run", "26.1")[2])

    def test_missing_host_tool_is_a_blocked_prerequisite(self):
        self.fence("readelf -h seed-forth")
        real_which = LAB.shutil.which
        with patch.object(LAB.shutil, "which", side_effect=lambda name: None if name == "readelf" else real_which(name)):
            status, stdout, _ = self.cli("list", "26")
            self.assertEqual(status, 0)
            self.assertIn(b"BLOCKED", stdout)
            self.assertIn(b"missing host tool: readelf", stdout)

    def test_timeout_allows_cleanup_and_kills_descendants(self):
        self.fence("./seed-forth < /dev/null\n"
                   "trap 'printf cleaned > cleanup; exit 143' TERM\n"
                   "sleep 30 &\nchild=$!\nprintf '%s' \"$child\" > child.pid\nwait")
        status, _, stderr = self.cli("run", "26.1", "--timeout", "0.1")
        self.assertEqual(status, 124, stderr)
        self.assertIn(b"timed out", stderr)
        self.assertEqual((self.source / "cleanup").read_text(), "cleaned")
        pid = int((self.source / "child.pid").read_text())
        # A dead child may briefly remain a zombie under the container's PID1.
        stat = Path(f"/proc/{pid}/stat")
        self.assertTrue(not stat.exists() or stat.read_text().split()[2] == "Z")

    def test_inherited_bash_startup_file_is_not_executed(self):
        self.fence("printf ok | ./seed-forth")
        startup = self.root / "startup.sh"
        startup.write_text("printf unwanted\n")
        with patch.dict(os.environ, {"BASH_ENV": str(startup)}):
            self.assertEqual(self.cli("run", "26.1")[:2], (0, b"ok"))

    def test_timeout_kills_child_that_ignores_term(self):
        self.fence("./seed-forth < /dev/null\n"
                   "bash -c 'trap \"\" TERM; printf ready > child.ready; sleep 30' &\n"
                   "printf '%s' \"$!\" > child.pid\nwait")
        status, _, stderr = self.cli("run", "26.1", "--timeout", "0.2")
        self.assertEqual(status, 124, stderr)
        self.assertEqual((self.source / "child.ready").read_text(), "ready")
        pid = int((self.source / "child.pid").read_text())
        stat = Path(f"/proc/{pid}/stat")
        self.assertTrue(not stat.exists() or stat.read_text().split()[2] == "Z")


if __name__ == "__main__":
    unittest.main()
