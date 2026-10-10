"""Regression fixtures for the selected-example harness; no bootstrap binaries."""

import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    "check_tryit", Path(__file__).resolve().parents[1] / "check-tryit.py")
TRYIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TRYIT)


class TryItTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        seed = self.root / "seed-forth"
        seed.write_text("#!/bin/sh\ncat\n")
        seed.chmod(0o755)
        root_patch = patch.object(TRYIT, "ROOT", str(self.root))
        root_patch.start()
        self.addCleanup(root_patch.stop)

    def markdown(self, text):
        md = self.root / "fixture.md"
        md.write_text(text)
        return str(md)

    def check(self, body, metadata=""):
        md = self.markdown(metadata + "\n```sh\n" + body + "\n```\n")
        block, = TRYIT.find_blocks(md)
        return TRYIT.run_block(md, block, 2, False, True)

    def assertFails(self, body, message=""):
        status, _, note, _ = self.check(body)
        self.assertEqual(status, "FAIL", note)
        self.assertIn(message, note)

    def test_quiet_failing_prerequisite_is_not_masked(self):
        self.assertFails("test -f missing\nprintf ok | ./seed-forth", "exited 1")

    def test_quiet_failure_inside_compound_is_not_masked(self):
        self.assertFails("(\nfalse\nprintf ok | ./seed-forth\n)", "`false` exited 1")

    def test_failed_producer_is_not_masked_by_successful_seed(self):
        self.assertFails("false | ./seed-forth", "pipeline statuses: 1 0")

    def test_failed_producer_inside_group_is_not_masked(self):
        self.assertFails("{\nfalse\nprintf ok\n} | ./seed-forth", "`false` exited 1")

    def test_failure_log_survives_subshell_directory_change(self):
        self.assertFails("(\ncd /\nfalse\ntrue\n)\nprintf ok | ./seed-forth",
                         "`false` exited 1")

    def test_harness_survives_disappearing_absolute_temporary_path(self):
        # Approximate unshare hiding /tmp without requiring mount privileges:
        # the shell retains its cwd while the old absolute path disappears.
        original, renamed = self.root / "original", self.root / "renamed"
        (original / "work").mkdir(parents=True)
        (original / "out").mkdir()
        script, _ = TRYIT.build_script([TRYIT.Chunk(["false", "true"])], "../out")
        (original / "block.sh").write_text(script)
        proc = subprocess.Popen(
            ["bash", "--noprofile", "--norc", "-c",
             "read -r ready; exec bash --noprofile --norc ../block.sh"],
            cwd=original / "work", stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        original.rename(renamed)
        stdout, stderr = proc.communicate("ready\n", timeout=2)
        self.assertEqual(proc.returncode, 0, (stdout, stderr))
        self.assertEqual(stderr, "")
        self.assertFalse(original.exists())
        self.assertEqual((renamed / "out" / "0.rc").read_text(), "0\n")
        self.assertTrue((renamed / "out" / "failures").read_text().startswith("1\t"))

    def test_status_observation_does_not_hide_producer_failure(self):
        self.assertFails("false | ./seed-forth\nprintf 'status %s\\n' \"$?\"\n"
                         "# prints 'status 1'", "pipeline statuses: 1 0")

    def test_status_print_keeps_intentional_nonzero_value(self):
        result = self.check("printf ok | ./seed-forth\nstatus=0\n"
                            "bash -c 'exit 42' || status=$?\n"
                            "printf 'status %s\\n' \"$status\" # prints 'status 42'")
        self.assertEqual(result[0], "OK", result)

    def test_status_print_still_checks_expected_value(self):
        self.assertFails("printf ok | ./seed-forth\nstatus=0\n"
                         "bash -c 'exit 42' || status=$?\n"
                         "printf 'status %s\\n' \"$status\" # prints 'status 43'",
                         "expected 'status 43'")

    def test_intentional_status_capture_inside_compound(self):
        result = self.check("(\nprintf ok | ./seed-forth\nstatus=0\n"
                            "bash -c 'exit 42' || status=$?\ntest \"$status\" -eq 42\n)")
        self.assertEqual(result[0], "OK", result)

    def test_wrong_status_assertion_inside_compound_fails(self):
        self.assertFails("(\nprintf ok | ./seed-forth\nstatus=0\n"
                         "bash -c 'exit 42' || status=$?\ntest \"$status\" -eq 41\n)", "exited 1")

    def test_status_capture_cannot_excuse_earlier_command_on_pipeline_line(self):
        self.assertFails('false; printf ok | ./seed-forth\nstatus=$?\ntest "$status" -eq 0',
                         "exited 1")

    def test_status_capture_cannot_excuse_earlier_command_on_plain_line(self):
        self.assertFails('printf ok | ./seed-forth\nfalse; true\nstatus=$?\ntest "$status" -eq 0',
                         "exited 1")

    def test_unguarded_nonzero_status_requires_explicit_shell_guard(self):
        self.assertFails("printf ok | ./seed-forth\nbash -c 'exit 42'\n"
                         "status=$?\ntest \"$status\" -eq 42", "exited 42")

    def test_explicit_conditional_status_handling_is_preserved(self):
        result = self.check("printf ok | ./seed-forth\nstatus=0\n"
                            "false || status=$?\ntest \"$status\" -eq 1\n"
                            "if false; then false; fi")
        self.assertEqual(result[0], "OK", result)

    def test_literal_status_text_is_not_a_status_observation(self):
        self.assertFails("false\necho '$?'\nprintf ok | ./seed-forth", "exited 1")
        self.assertFails("false\necho \\$?\nprintf ok | ./seed-forth", "exited 1")

    def test_command_not_found_is_never_excused_by_status_capture(self):
        self.assertFails("tryit_command_that_does_not_exist\nstatus=$?\n"
                         "printf ok | ./seed-forth", "rc 127")

    def test_early_successful_exit_does_not_skip_remaining_chunks(self):
        self.assertFails("exit 0\nprintf ok | ./seed-forth", "chunks completed")

    def test_explicit_metadata_checks_multiline_output(self):
        result = self.check("printf 'one\\ntwo\\n' | ./seed-forth",
                            '<!-- tryit: expect "one\\ntwo" -->')
        self.assertEqual(result[0], "OK", result)
        self.assertIn("1 output check", result[2])

    def test_explicit_metadata_mismatch_fails(self):
        result = self.check("printf wrong | ./seed-forth", '<!-- tryit: expect "right" -->')
        self.assertEqual(result[0], "FAIL", result)
        self.assertIn("metadata expects", result[2])

    def test_malformed_metadata_fails_instead_of_dropping_assertion(self):
        for marker in ('<!-- tryit: expect nope -->', '<!-- tryit: expect 42 -->'):
            with self.subTest(marker=marker):
                result = self.check("printf ok | ./seed-forth", marker)
                self.assertEqual(result[0], "FAIL", result)
                self.assertIn("invalid tryit expectation", result[2])

    def test_adjacent_markers_preserve_skip(self):
        result = self.check("printf ok | ./seed-forth",
                            '<!-- tryit: skip -->\n<!-- tryit: expect "ok" -->')
        self.assertEqual(result[0], "SKIP", result)

    def test_summary_separates_selection_omissions_and_skips(self):
        md = self.markdown("```sh\nprintf ok | ./seed-forth\n```\n"
                           "```sh\n./seed-forth < input\n```\n"
                           "```\ntranscript\n```\n"
                           "<!-- tryit: skip -->\n```sh\nfalse | ./seed-forth\n```\n")
        self.assertEqual(len(TRYIT.find_blocks(md)), 2)
        output = io.StringIO()
        with patch.object(TRYIT, "can_unshare", return_value=False), contextlib.redirect_stdout(output):
            status = TRYIT.main([md])
        self.assertEqual(status, 0, output.getvalue())
        self.assertIn("2 selected; 1 OK, 1 SKIP, 0 FAIL; 2 OMIT", output.getvalue())
        self.assertIn("0 output checks", output.getvalue())

    def test_default_run_excludes_unlisted_retired_page(self):
        self.markdown("```sh\nprintf ok | ./seed-forth\n```\n")
        retired = self.root / "WRITING.md"
        retired.write_text("```sh\nfalse | ./seed-forth\n```\n")
        (self.root / "SUMMARY.md").write_text("# Summary\n- [Current](fixture.md)\n")
        output = io.StringIO()
        with patch.object(TRYIT, "BOOK", str(self.root)), \
                patch.object(TRYIT, "can_unshare", return_value=False), \
                contextlib.redirect_stdout(output):
            status = TRYIT.main([])
        self.assertEqual(status, 0, output.getvalue())
        self.assertIn("1 selected; 1 OK, 0 SKIP, 0 FAIL", output.getvalue())
        self.assertNotIn("WRITING.md", output.getvalue())
        # Explicit filenames intentionally keep the authoring/debug workflow.
        with patch.object(TRYIT, "can_unshare", return_value=False), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(TRYIT.main([str(retired)]), 1)

    def test_missing_published_chapter_fails_before_execution(self):
        (self.root / "SUMMARY.md").write_text("# Summary\n- [Missing](missing.md)\n")
        output = io.StringIO()
        with patch.object(TRYIT, "BOOK", str(self.root)), \
                patch.object(TRYIT, "run_block") as run_block, \
                contextlib.redirect_stdout(output):
            status = TRYIT.main([])
        self.assertEqual(status, 1, output.getvalue())
        self.assertIn("missing published chapter 'missing.md'", output.getvalue())
        run_block.assert_not_called()

    def test_missing_summary_does_not_fall_back_to_all_markdown(self):
        self.markdown("```sh\nprintf ok | ./seed-forth\n```\n")
        output = io.StringIO()
        with patch.object(TRYIT, "BOOK", str(self.root)), contextlib.redirect_stdout(output):
            status = TRYIT.main([])
        self.assertEqual(status, 1, output.getvalue())
        self.assertIn("SUMMARY.md", output.getvalue())


if __name__ == "__main__":
    unittest.main()
