"""Keep the retired assembler walkthrough as a runnable check only."""

import importlib.util
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
PAGE = "26-m1-and-hex2.md"


def load_tool(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


INDEX = load_tool("check_index", "gen-index.py")
LINKS = load_tool("check_links", "check-links.py")
LAB = load_tool("assembler_lab", "book-lab.py")
BUNDLE = load_tool("assembler_bundle", "make-bundle.py")


class AssemblerCheckTests(unittest.TestCase):
    def test_main_route_skips_assembler_and_check_is_published_once(self):
        summary = (ROOT / "book/SUMMARY.md").read_text(encoding="utf-8")
        published = re.findall(r"\]\(([^)#]+\.md)\)", summary)
        self.assertEqual(published.count(PAGE), 1)
        last_library = published.index("25-lib-12-defining-words-and-bytes-eq.md")
        self.assertEqual(published[last_library + 1], "part-3-compiler.md")
        self.assertNotIn("Appendix I", summary)
        self.assertIn(f"[Assembler regression check]({PAGE})",
                      summary.split("# Checks and references", 1)[1])

    def test_legacy_url_has_a_concise_check_not_a_source_walkthrough(self):
        path = ROOT / "book" / PAGE
        text = path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Assembler regression check\n"))
        self.assertLess(len(text.splitlines()), 150)
        self.assertNotRegex(text, re.compile(r"^```[^\n]*(?:file|chunk)=", re.M), "canonical source must not reappear")
        self.assertNotIn("## Exercise", text)
        anchors, _ = LINKS.scan(path)
        self.assertLessEqual({"chapter-26--the-m1-assembler-and-hex2-linker",
                              "appendix-i--the-m1-assembler-and-hex2-linker",
                              "run-the-check", "try-it"}, anchors)

    def test_index_does_not_claim_to_teach_assembler_definitions(self):
        rendered = INDEX.render(INDEX.load_chapters())
        self.assertNotIn("assembler word", rendered)
        self.assertNotIn(f"]({PAGE}#", rendered)
        self.assertNotIn("- `asm-main`", rendered)

    def test_legacy_selector_is_still_the_runnable_regression_check(self):
        labs = [lab for lab in LAB.inventory()
                if Path(lab["filename"]).name == PAGE]
        self.assertEqual([lab["selector"] for lab in labs], ["26.1"])
        self.assertIsNone(LAB.exclusion(labs[0]))
        self.assertEqual(labs[0]["expected"], "hi\nexit: 42\n160")
        self.assertIn("forth/010-lib.fth forth/130-asm.fth", LAB.code(labs[0]))
        self.assertIn('test "$status" -eq 42 || exit 1', LAB.code(labs[0]))

    def test_authoring_outline_does_not_restore_assembler_source_ownership(self):
        outline = (ROOT / "book/outline" / PAGE).read_text(encoding="utf-8")
        self.assertIn("Sources taught: None.\n\nCheck source:", outline)
        self.assertNotIn("forth/130-asm.fth 1-", outline)
        self.assertEqual(BUNDLE.field(outline, "Sources taught"), "None.")
        ledger = (ROOT / "book/outline/LEDGER.md").read_text(encoding="utf-8")
        self.assertNotIn(" | 26 Appendix I:", ledger)
        self.assertIn("Prospective-size check | 27 Arena and I/O buffers", ledger)


if __name__ == "__main__":
    unittest.main()
