"""Keep similarly named C and assembler mechanisms distinct in the index."""

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("index_navigation", ROOT / "tools/gen-index.py")
INDEX = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(INDEX)


class IndexNavigationTests(unittest.TestCase):
    def test_c_macro_expansion_does_not_resolve_to_the_m1_assembler(self):
        rendered = INDEX.render(INDEX.load_chapters())
        row = next(line for line in rendered.splitlines()
                   if line.startswith("- **#define and macro expansion**"))
        self.assertIn("28-the-preprocessor.md#macro-expansion", row)
        self.assertIn("28-the-preprocessor.md#define-and-undef", row)
        self.assertNotIn("26-m1-and-hex2.md", row)


if __name__ == "__main__":
    unittest.main()
