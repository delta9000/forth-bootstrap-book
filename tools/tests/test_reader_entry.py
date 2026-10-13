"""Keep the sequential opening and its first runnable lab connected."""

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("reader_entry_lab", ROOT / "tools/book-lab.py")
LAB = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LAB)


class ReaderEntryTests(unittest.TestCase):
    def test_prologue_follows_first_word_without_a_reference_detour(self):
        published = [Path(path).name for path in LAB.TRYIT.published_files()]
        self.assertEqual(published[:4], ["00-introduction.md", "01-reading-the-book.md",
                                         "02-prologue.md", "03-where-this-fits.md"])
        self.assertEqual(published.count("labs.md"), 1)
        self.assertGreater(published.index("labs.md"),
                           published.index("56-gcc-15-epilogue.md"))

    def test_first_word_keeps_its_runnable_selector_and_expected_output(self):
        labs = {lab["selector"]: lab for lab in LAB.inventory()}
        hello = labs["1.2"]
        self.assertIsNone(LAB.exclusion(hello))
        self.assertEqual(hello["expected"], "Hi")
        self.assertIn(": hello [lit] 72 emit [lit] 105 emit [lit] 10 emit ; hello bye",
                      LAB.code(hello))
        self.assertIsNotNone(LAB.exclusion(labs["1.1"]))

    def test_entry_jump_setup_uses_the_readers_source_directory(self):
        setup = next(lab for lab in LAB.inventory() if lab["selector"] == "4.1")
        self.assertEqual(LAB.code(setup).strip(), "./seed/build.sh")
        self.assertIsNone(LAB.exclusion(setup))


if __name__ == "__main__":
    unittest.main()
