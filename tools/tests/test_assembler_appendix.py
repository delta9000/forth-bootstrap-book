"""Keep the optional assembler published without breaking its old links."""

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


INDEX = load_tool("appendix_index", "gen-index.py")
LINKS = load_tool("appendix_links", "check-links.py")


class AssemblerAppendixTests(unittest.TestCase):
    def test_main_route_skips_assembler_and_back_matter_publishes_it_once(self):
        summary = (ROOT / "book/SUMMARY.md").read_text(encoding="utf-8")
        published = re.findall(r"\]\(([^)#]+\.md)\)", summary)
        self.assertEqual(published.count(PAGE), 1)
        last_library = published.index("25-lib-12-defining-words-and-bytes-eq.md")
        self.assertEqual(published[last_library + 1], "part-3-compiler.md")
        appendix_h = published.index("66-exercise-feedback.md")
        self.assertEqual(published[appendix_h + 1], PAGE)
        self.assertIn(f"[Appendix I: the M1 assembler and hex2 linker]({PAGE})",
                      summary.split("# Back matter", 1)[1])

    def test_legacy_url_retains_every_former_heading_anchor(self):
        path = ROOT / "book" / PAGE
        self.assertTrue(path.read_text(encoding="utf-8").startswith(
            "# Appendix I — The M1 assembler and hex2 linker\n"))
        anchors, _ = LINKS.scan(path)
        legacy = {
            "chapter-26--the-m1-assembler-and-hex2-linker",
            "m1-and-hex2-in-brief", "carry-one-input-through-both-passes",
            "pause-and-predict", "supported-input-language", "buffers-and-a-cursor",
            "selecting-and-reading-a-buffer", "appending-expanded-text",
            "the-output-side", "the-label-table", "numbers", "reading-tokens",
            "one-token-one-decision", "token-diagnostics", "field-bounds",
            "sigils-and-references", "hex-bytes-and-dispatch", "two-passes",
            "macro-expansion-definitions", "macro-expansion-copying",
            "macro-expansion-strings", "macro-expansion-the-walk", "asm-main",
            "capacity-and-failure", "try-it", "exercise",
        }
        self.assertLessEqual(legacy, anchors)

    def test_index_uses_appendix_label_with_the_legacy_section_targets(self):
        rendered = INDEX.render(INDEX.load_chapters())
        rows = [line for line in rendered.splitlines() if f"]({PAGE}#" in line]
        self.assertTrue(rows)
        for row in rows:
            self.assertIn("[App. I,", row)
            self.assertNotIn("[Ch 26,", row)
        main = next(row for row in rows if row.startswith("- `asm-main` —"))
        self.assertIn(f"[App. I, `asm-main`]({PAGE}#asm-main)", main)


if __name__ == "__main__":
    unittest.main()
