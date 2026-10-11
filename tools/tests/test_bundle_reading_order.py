"""Keep optional appendices out of an earlier chapter's prerequisite bundle."""

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("bundle_reading_order", ROOT / "tools/make-bundle.py")
BUNDLE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUNDLE)


class BundleReadingOrderTests(unittest.TestCase):
    def test_summary_order_overrides_stable_numeric_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            book = Path(directory)
            outline = book / "outline"
            outline.mkdir()
            (book / "SUMMARY.md").write_text(
                "- [Library](25-library.md)\n"
                "- [Compiler](27-compiler.md)\n"
                "- [Appendix I](26-assembler.md)\n"
                "- [Index](WORD-INDEX.md)\n")
            for name in ("25-library", "26-assembler", "27-compiler", "64-word-index", "99-unpublished"):
                (outline / (name + ".md")).write_text("# " + name + "\n")
            with patch.object(BUNDLE, "BOOK", str(book)), patch.object(BUNDLE, "OUTLINE", str(outline)):
                self.assertEqual([nn for nn, _, _ in BUNDLE.stubs()], ["25", "27", "26", "64", "99"])
                self.assertEqual(BUNDLE.prior_chapters("27"), {"25"})
                self.assertEqual(BUNDLE.prior_chapters("26"), {"25", "27"})

    def test_compiler_bundle_does_not_assume_optional_assembler_reading(self):
        earlier = BUNDLE.prior_chapters("27")
        self.assertIn("25", earlier)
        self.assertNotIn("26", earlier)


if __name__ == "__main__":
    unittest.main()
