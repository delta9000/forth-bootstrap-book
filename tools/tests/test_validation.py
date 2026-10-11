"""Focused false-green regressions; no bootstrap executables are run.

Run with: python3 -m unittest discover -s tools/tests -v
Each CLI test uses a tiny, independent temporary book/source checkout.
"""
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


TOOLS = Path(__file__).resolve().parents[1]


class BookFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="book-checker-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ("tools", "book", "forth-bootstrap/seed", "forth-bootstrap/forth",
                     "forth-bootstrap/cc", "rendered"):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        for tool in ("check-links.py", "check-numbers.py", "gen-index.py", "tangle.sh", "tangle.awk"):
            shutil.copy2(TOOLS / tool, self.root / "tools" / tool)
        self.write("book/SUMMARY.md", "- [Chapter](01-test.md)\n")
        self.write("book/01-test.md", "# Chapter\n")

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def run_tool(self, tool, *args):
        command = ["bash" if tool.endswith(".sh") else sys.executable,
                   str(self.root / "tools" / tool), *args]
        env = {k: v for k, v in os.environ.items() if k != "FORTH_BOOTSTRAP"}
        return subprocess.run(command, cwd=self.root, env=env, capture_output=True,
                              text=True, timeout=10)

    def load(self, tool):
        spec = importlib.util.spec_from_file_location("checker_under_test", self.root / "tools" / tool)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


class RenderedLinksTests(BookFixture):
    def check_html(self):
        return self.run_tool("check-links.py", "--html", str(self.root / "rendered"))

    def test_missing_published_page_fails(self):
        result = self.check_html()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing rendered page", result.stdout)

    def test_missing_expected_heading_fails(self):
        self.write("rendered/01-test.html", '<h1 id="different">Chapter</h1>')
        result = self.check_html()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expected anchor #chapter missing", result.stdout)

    def test_non_heading_ids_and_extra_renderer_ids_are_valid(self):
        self.write("book/01-test.md", '# Chapter\n<a id="raw"></a>\n[raw](#raw)\n')
        self.write("rendered/01-test.html",
                   "<h1 id='chapter'>Chapter</h1><div id='raw'></div><nav id='menu'></nav>")
        result = self.check_html()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_explicit_anchor_fails(self):
        self.write("book/01-test.md", '# Chapter\n<a id="raw"></a>\n[raw](#raw)\n')
        self.write("rendered/01-test.html", '<h1 id="chapter">Chapter</h1>')
        result = self.check_html()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expected anchor #raw missing", result.stdout)

    def test_retired_page_does_not_need_rendering(self):
        self.write("book/99-retired.md", "# Retired\n")
        self.write("rendered/01-test.html", '<h1 id="chapter">Chapter</h1>')
        result = self.check_html()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class CanonicalCoverageTests(BookFixture):
    def setUp(self):
        super().setUp()
        self.write("tools/canonical-sources.txt", "seed/000-seed.hex0\nforth/010-lib.fth\n")
        self.write("tools/check-only-sources.txt", "# No exceptions in the minimal fixture.\n")
        self.write("forth-bootstrap/seed/000-seed.hex0", "00\n")
        self.write("forth-bootstrap/forth/010-lib.fth", ": test ;\n")
        self.seed_fence = "```hex0 file=seed/000-seed.hex0\n00\n```\n"
        self.forth_fence = "```forth file=forth/010-lib.fth\n: test ;\n```\n"
        self.write("book/01-test.md", "# Chapter\n" + self.seed_fence + self.forth_fence)

    def verify(self):
        return self.run_tool("tangle.sh", "verify", "--strict")

    def test_complete_published_coverage_passes(self):
        result = self.verify()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_whole_missing_root_fails(self):
        self.write("book/01-test.md", "# Chapter\n" + self.seed_fence)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no published file= coverage", result.stderr)

    def test_no_roots_never_passes_even_non_strict(self):
        self.write("book/01-test.md", "# Chapter\n")
        for args in (("verify",), ("verify", "--strict")):
            with self.subTest(args=args):
                result = self.run_tool("tangle.sh", *args)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("no file= blocks", result.stderr)

    def test_retired_fences_cannot_supply_required_coverage(self):
        self.write("book/01-test.md", "# Chapter\n" + self.seed_fence)
        self.write("book/99-retired.md", "# Retired\n" + self.forth_fence)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("forth/010-lib.fth", result.stderr)

    def test_new_numbered_source_requires_inventory_entry(self):
        self.write("forth-bootstrap/cc/020-new.fth", ": new ;\n")
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("absent from canonical-sources.txt", result.stderr)

    def test_removed_required_source_fails(self):
        (self.root / "forth-bootstrap/forth/010-lib.fth").unlink()
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("required source file is missing", result.stderr)

    def test_missing_published_chapter_fails(self):
        self.write("book/SUMMARY.md", "- [Missing](02-missing.md)\n")
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("published chapter 02-missing.md is missing", result.stderr)

    def add_check_only_source(self):
        self.write("forth-bootstrap/forth/130-asm.fth", ": assembler ;\n")
        self.write("forth-bootstrap/tests/asm/hi-check.sh",
                   f'#!/bin/sh\ntouch "{self.root / "checkpoint-was-executed"}"\nexit 99\n')
        (self.root / "forth-bootstrap/tests/asm/hi-check.sh").chmod(0o755)
        self.write("tools/check-only-sources.txt",
                   "# Explicit static mapping; do not execute.\n"
                   "forth/130-asm.fth tests/asm/hi-check.sh\n")

    def test_registered_check_only_source_does_not_need_fences(self):
        self.add_check_only_source()
        result = self.verify()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("CHECK-ONLY  forth/130-asm.fth", result.stdout)
        self.assertIn("tests/asm/hi-check.sh registered; not executed", result.stdout)
        self.assertIn("2 canonical sources byte-identical; check-only registrations: 1", result.stdout)
        self.assertNotIn("OK    forth/130-asm.fth", result.stdout)
        self.assertFalse((self.root / "checkpoint-was-executed").exists())

    def test_status_reports_check_only_without_claiming_taught_coverage(self):
        self.add_check_only_source()
        result = self.run_tool("tangle.sh", "status")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        lines = [line for line in result.stdout.splitlines() if "forth/130-asm.fth" in line]
        self.assertEqual(len(lines), 1)
        self.assertIn("CHECK-ONLY", lines[0])
        self.assertIn("not executed", lines[0])
        self.assertNotIn("%", lines[0])
        self.assertFalse((self.root / "checkpoint-was-executed").exists())

    def test_extract_omits_check_only_source(self):
        self.add_check_only_source()
        output = self.root / "tangled"
        result = self.run_tool("tangle.sh", "extract", str(output))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(sorted(str(path.relative_to(output)) for path in output.rglob("*")
                                if path.is_file()), ["forth/010-lib.fth", "seed/000-seed.hex0"])

    def test_check_only_source_does_not_excuse_missing_canonical_coverage(self):
        self.add_check_only_source()
        self.write("book/01-test.md", "# Chapter\n" + self.seed_fence)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("forth/010-lib.fth  (no published file= coverage", result.stderr)

    def test_check_only_source_does_not_excuse_byte_mismatch(self):
        self.add_check_only_source()
        self.write("forth-bootstrap/forth/010-lib.fth", ": changed ;\n")
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("book does not tangle to byte-identical source", result.stderr)
        self.assertNotIn("2 canonical sources byte-identical", result.stdout)

    def test_unknown_source_fails_even_with_valid_check_only_exception(self):
        self.add_check_only_source()
        self.write("forth-bootstrap/cc/020-new.fth", ": new ;\n")
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cc/020-new.fth  (numbered source absent", result.stderr)

    def test_missing_check_only_inventory_fails(self):
        (self.root / "tools/check-only-sources.txt").unlink()
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing check-only inventory", result.stderr)

    def test_empty_check_only_inventory_is_valid_only_without_exceptions(self):
        self.write("tools/check-only-sources.txt", "")
        result = self.verify()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.add_check_only_source()
        self.write("tools/check-only-sources.txt", "")
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("forth/130-asm.fth  (numbered source absent", result.stderr)

    def test_stale_check_only_source_fails(self):
        self.add_check_only_source()
        (self.root / "forth-bootstrap/forth/130-asm.fth").unlink()
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("check-only source file is missing", result.stderr)

    def test_stale_check_only_checkpoint_fails_verify_and_status(self):
        self.add_check_only_source()
        (self.root / "forth-bootstrap/tests/asm/hi-check.sh").unlink()
        for args in (("verify", "--strict"), ("status",)):
            with self.subTest(args=args):
                result = self.run_tool("tangle.sh", *args)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("check-only checkpoint is missing", result.stderr)
                self.assertNotIn("registered; not executed", result.stdout)

    def test_duplicate_check_only_source_fails_even_with_different_checkpoints(self):
        self.add_check_only_source()
        self.write("forth-bootstrap/tests/asm/other.sh", "#!/bin/sh\nexit 0\n")
        for checkpoint in ("tests/asm/hi-check.sh", "tests/asm/other.sh"):
            with self.subTest(checkpoint=checkpoint):
                self.write("tools/check-only-sources.txt",
                           "forth/130-asm.fth tests/asm/hi-check.sh\n"
                           f"forth/130-asm.fth {checkpoint}\n")
                result = self.verify()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("duplicate check-only source entry", result.stderr)

    def test_overlapping_canonical_and_check_only_source_fails(self):
        self.add_check_only_source()
        self.write("tools/check-only-sources.txt",
                   "forth/130-asm.fth tests/asm/hi-check.sh\n"
                   "forth/010-lib.fth tests/asm/hi-check.sh\n")
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source is both canonical and check-only", result.stderr)

    def test_check_only_source_cannot_have_published_canonical_fences(self):
        self.add_check_only_source()
        self.write("book/01-test.md", "# Chapter\n" + self.seed_fence + self.forth_fence
                   + "```forth file=forth/130-asm.fth\n: assembler ;\n```\n")
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("check-only source has published file= coverage", result.stderr)
        self.assertNotIn("OK    forth/130-asm.fth", result.stdout)

    def test_malformed_check_only_entries_fail(self):
        self.add_check_only_source()
        for entry in ("forth/130-asm.fth",
                      "forth/130-asm.fth tests/asm/hi-check.sh unexpected-field",
                      "forth/not-numbered.fth tests/asm/hi-check.sh",
                      "../forth/130-asm.fth tests/asm/hi-check.sh",
                      "forth/130-asm.fth /tests/asm/hi-check.sh",
                      "forth/130-asm.fth tests/../tests/asm/hi-check.sh",
                      "forth/130-asm.fth tests//asm/hi-check.sh",
                      "forth/130-asm.fth tests/./asm/hi-check.sh",
                      "forth/130-asm.fth scripts/build.sh"):
            with self.subTest(entry=entry):
                self.write("tools/check-only-sources.txt", entry + "\n")
                result = self.verify()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("invalid check-only entry", result.stderr)

    def test_manifest_final_line_does_not_need_newline(self):
        self.add_check_only_source()
        self.write("tools/canonical-sources.txt", "seed/000-seed.hex0\nforth/010-lib.fth")
        self.write("tools/check-only-sources.txt", "forth/130-asm.fth tests/asm/hi-check.sh")
        result = self.verify()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_duplicate_canonical_source_fails(self):
        self.write("tools/canonical-sources.txt",
                   "seed/000-seed.hex0\nforth/010-lib.fth\nforth/010-lib.fth\n")
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate canonical source entry", result.stderr)

    def test_invalid_canonical_source_entry_fails(self):
        for entry in ("../forth/010-lib.fth", "forth/010-lib.fth unexpected-field"):
            with self.subTest(entry=entry):
                self.write("tools/canonical-sources.txt", "seed/000-seed.hex0\n" + entry + "\n")
                result = self.verify()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("invalid canonical source entry", result.stderr)

    def test_missing_empty_or_comments_only_canonical_inventory_fails(self):
        for contents in (None, "", "# No required sources.\n"):
            with self.subTest(contents=contents):
                if contents is None:
                    (self.root / "tools/canonical-sources.txt").unlink()
                else:
                    self.write("tools/canonical-sources.txt", contents)
                result = self.verify()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("required-source inventory", result.stderr)


class NumberAndCitationTests(BookFixture):
    def seed_fixture(self):
        # The numeric checker reads size only. This file is never executable.
        self.write("forth-bootstrap/seed-forth", "xx")
        self.write("forth-bootstrap/seed/000-seed.hex0",
                   ";; ----- foo_code @ 0x0\n00\n;; ----- next_code @ 0x1\n01\n")
        self.write("forth-bootstrap/forth/010-lib.fth", ": test-word [lit] 1 ;\n")

    def test_fix_preserves_unfixable_numeric_error(self):
        self.seed_fixture()
        self.write("book/01-test.md", "# Chapter\n`foo_code` is 9 bytes.\n\n"
                   "`test-word` (`forth-bootstrap/forth/010-lib.fth:9`).\n")
        result = self.run_tool("check-numbers.py", "--fix")
        text = (self.root / "book/01-test.md").read_text()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("1 MISMATCH", result.stdout)
        self.assertIn("1 FIXED", result.stdout)
        self.assertIn("010-lib.fth:1", text)
        self.assertIn("`foo_code` is 9 bytes", text)

    def test_fixable_citation_alone_passes_after_reread(self):
        self.seed_fixture()
        self.write("book/01-test.md", "# Chapter\n"
                   "`test-word` (`forth-bootstrap/forth/010-lib.fth:9`).\n")
        result = self.run_tool("check-numbers.py", "--fix")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("0 MISMATCH", result.stdout)

    def test_range_citation_is_not_rewritten_as_a_single_definition(self):
        self.seed_fixture()
        self.write("forth-bootstrap/forth/010-lib.fth", "\\ header\n: test-word [lit] 1 ;\n")
        text = "# Chapter\n`test-word` (`forth-bootstrap/forth/010-lib.fth:1–2`).\n"
        self.write("book/01-test.md", text)
        result = self.run_tool("check-numbers.py", "--fix")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.root / "book/01-test.md").read_text(), text)

    def test_all_source_types_ranges_and_lists_without_seed_binary(self):
        for name in ("script.sh", "header.h", "source.c", "recipe", "notes.md"):
            self.write("forth-bootstrap/" + name, "one\ntwo\nthree\n")
        self.write("book/01-test.md", "# Chapter\n" + "\n".join(
            f"`forth-bootstrap/{name}:1,2–3`" for name in
            ("script.sh", "header.h", "source.c", "recipe", "notes.md")))
        result = self.run_tool("check-numbers.py", "--citations-only")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("5 OK", result.stdout)

    def test_missing_zero_out_of_bounds_and_reversed_citations_fail(self):
        self.write("forth-bootstrap/script.sh", "one\ntwo\nthree\n")
        self.write("book/01-test.md", "# Chapter\n"
                   "`forth-bootstrap/missing.c:1`\n"
                   "`forth-bootstrap/script.sh:0`\n"
                   "`forth-bootstrap/script.sh:-1`\n"
                   "`forth-bootstrap/script.sh:1-4`\n"
                   "`forth-bootstrap/script.sh:3–2`\n"
                   "`forth-bootstrap/script.sh:1,8`\n")
        result = self.run_tool("check-numbers.py", "--citations-only")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("6 MISMATCH", result.stdout)
        self.assertIn("source file does not exist", result.stdout)

    def test_unpublished_citations_do_not_change_publication_gate(self):
        self.write("book/99-retired.md", "# Retired\n`forth-bootstrap/old.c:1000`\n")
        result = self.run_tool("check-numbers.py", "--citations-only")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_explicit_checkout_path_is_not_resolved_by_basename(self):
        self.seed_fixture()
        self.write("book/01-test.md", "# Chapter\n`forth-bootstrap/010-lib.fth:1`\n")
        result = self.run_tool("check-numbers.py", "--citations-only")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source file does not exist", result.stdout)


class IndexTests(BookFixture):
    def setUp(self):
        super().setUp()
        self.write("book/01-test.md", "# Chapter\n## Real heading\n"
                   "```forth file=forth/010-lib.fth\n: word ;\n```\n")
        self.write("book/99-retired.md", "# Retired\n## Hidden heading\n")
        self.index = self.load("gen-index.py")

    def test_only_published_chapters_are_selected(self):
        self.assertEqual(self.index.reading_order(), ["01-test.md"])

    def test_missing_concept_target_is_fatal_even_with_other_valid_target(self):
        self.index.CONCEPTS = [("Concept", [("01-", "Real heading"), ("99-", "Hidden heading")])]
        with self.assertRaisesRegex(ValueError, "no published chapter"):
            self.index.render(self.index.load_chapters())

    def test_failed_generation_preserves_existing_index(self):
        self.index.CONCEPTS = [("Concept", [("99-", "Hidden heading")])]
        self.write("book/WORD-INDEX.md", "Existing index\n")
        with patch.object(sys, "argv", ["gen-index.py"]), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(self.index.main(), 1)
        self.assertEqual((self.root / "book/WORD-INDEX.md").read_text(), "Existing index\n")

    def test_preamble_matches_published_edition_and_rendered_count(self):
        self.index.CONCEPTS = [("Concept", [("01-", "Real heading")])]
        result = self.index.render(self.index.load_chapters())
        for expected in ("check.sh runs", "Part 1", "Part 2", "Chapter 13", "cc/141-archive.fth",
                         "1 names and 1 ideas"):
            self.assertIn(expected, result)
        self.assertNotIn("check-all.sh", result)


if __name__ == "__main__":
    unittest.main()
