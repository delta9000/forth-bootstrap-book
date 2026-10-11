"""Keep index destinations and reader-facing chapter labels consistent."""

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("index_navigation", ROOT / "tools/gen-index.py")
INDEX = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INDEX)


class IndexNavigationTests(unittest.TestCase):
    def test_numeric_appendix_files_use_their_published_letters(self):
        chapters = {chapter.file: chapter for chapter in INDEX.load_chapters()}
        expected = {
            "57-historical-reproducibility.md": "App. C",
            "58-worked-exercises.md": "App. D",
            "59-further-reading.md": "App. E",
            "60-c-subset.md": "App. F",
            "61-error-codes.md": "App. G",
            "66-exercise-feedback.md": "App. H",
            "26-m1-and-hex2.md": "Check",
            "38-main-and-bootstrap-chain.md": "Ch 38",
        }
        for filename, label in expected.items():
            with self.subTest(filename=filename):
                self.assertEqual(chapters[filename].label, label)

        chapter = chapters["58-worked-exercises.md"]
        heading = chapter.find_heading("Where left-associativity comes from")
        self.assertEqual(
            INDEX.link(chapter, heading),
            "[App. D, Where left-associativity comes from]"
            "(58-worked-exercises.md#where-left-associativity-comes-from)",
        )

    def test_c_macro_expansion_does_not_resolve_to_the_m1_assembler(self):
        rendered = INDEX.render(INDEX.load_chapters())
        row = next(line for line in rendered.splitlines()
                   if line.startswith("- **#define and macro expansion**"))
        self.assertIn("28-the-preprocessor.md#macro-expansion", row)
        self.assertIn("28-the-preprocessor.md#define-and-undef", row)
        self.assertNotIn("26-m1-and-hex2.md", row)


if __name__ == "__main__":
    unittest.main()
