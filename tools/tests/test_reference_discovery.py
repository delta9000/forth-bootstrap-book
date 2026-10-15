"""Regression checks for the curated idea and diagnostic discovery layers."""
import importlib.util
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


INDEX = load('reference_word_index', 'gen-index.py')
ERRORS = load('reference_error_index', 'gen-error-index.py')


class ReferenceDiscoveryTests(unittest.TestCase):
    def test_extended_ideas_resolve_in_their_named_chapters(self):
        chapters = INDEX.load_chapters()
        covered = set()
        for term, targets in INDEX.CONCEPTS:
            for prefix, needle in targets:
                number = re.match(r'(\d+)-', prefix)
                if number is None or not 40 <= int(number[1]) <= 56:
                    continue
                with self.subTest(term=term, prefix=prefix):
                    matches = [chapter for chapter in chapters
                               if chapter.file.startswith(prefix)]
                    self.assertEqual(len(matches), 1)
                    self.assertIsNotNone(matches[0].find_heading(needle))
                covered.add(int(number[1]))
        self.assertEqual(covered, set(range(40, 57)))

    def test_core_call_and_frame_labels_offer_later_routes(self):
        concepts = dict(INDEX.CONCEPTS)
        for term in ('Calling convention (core: six register arguments)',
                     'Function frame (core: 256 bytes, 32 slots)'):
            targets = concepts[term]
            self.assertTrue(any(prefix.startswith('37-') for prefix, _ in targets))
            self.assertTrue(any(prefix.startswith('41-') for prefix, _ in targets))

    def test_numeric_lookup_is_current_and_idempotent(self):
        page = ERRORS.PAGE.read_text(encoding='utf-8')
        self.assertEqual(ERRORS.render(page), page)
        self.assertEqual(ERRORS.render(ERRORS.render(page)), page)

    def test_ambiguous_code_keeps_all_candidate_rows_and_prefixes(self):
        page = ERRORS.render(ERRORS.PAGE.read_text(encoding='utf-8'))
        lookup = page.split(ERRORS.START)[1].split(ERRORS.END)[0]
        row = next(line for line in lookup.splitlines() if line.startswith('| 248 |'))
        for filename in ('081-cc-object.fth', '128-cc-float-literal.fth',
                         '129-cc-bitfield.fth'):
            self.assertIn(filename, row)
        self.assertIn('bitfield:', row)
        self.assertIn('cc-f64-literal:', row)
        anchors = re.findall(r'<a id="(diagnostic-[^"]+)"></a>', page)
        self.assertEqual(len(anchors), len(set(anchors)))
        targets = re.findall(r'\]\(#(diagnostic-[^)]+)\)', lookup)
        self.assertEqual(set(targets), set(anchors))
        self.assertNotIn('seed-cc-start.fth', lookup)
        self.assertNotIn('seed-cc.c', lookup)

    def test_lookup_updates_from_tables_without_a_second_catalogue(self):
        page = ERRORS.PAGE.read_text(encoding='utf-8')
        clean = ERRORS.ANCHOR.sub('', page)
        old = '| 248 | `forth-bootstrap/cc/129-cc-bitfield.fth:'
        self.assertIn(old, clean)
        changed = clean.replace(old, '| 999 | `forth-bootstrap/cc/129-cc-bitfield.fth:', 1)
        rendered = ERRORS.render(changed)
        lookup = rendered.split(ERRORS.START)[1].split(ERRORS.END)[0]
        row = next(line for line in lookup.splitlines() if line.startswith('| 999 |'))
        self.assertIn('129-cc-bitfield.fth', row)
        self.assertIn('bitfield:', row)
        old_row = next(line for line in lookup.splitlines() if line.startswith('| 248 |'))
        self.assertNotIn('129-cc-bitfield.fth', old_row)

    def test_row_anchors_preserve_the_numeric_citation_shape(self):
        page = ERRORS.render(ERRORS.PAGE.read_text(encoding='utf-8'))
        for line in page.splitlines():
            if '<a id="diagnostic-' not in line:
                continue
            self.assertRegex(line, r'^\|\s*`?\d+`?\s*\| <a id=')

    def test_unpadded_source_cell_keeps_anchor_outside_code_span(self):
        page = ERRORS.ANCHOR.sub('', ERRORS.PAGE.read_text(encoding='utf-8'))
        source_row = next(line for line in page.splitlines()
                          if re.match(r'^\|\s*`?\d+`?\s*\| `forth-bootstrap/cc/', line))
        unpadded_row = source_row.replace('| `forth-bootstrap/cc/',
                                          '|`forth-bootstrap/cc/', 1)
        page = page.replace(source_row, unpadded_row, 1)

        rendered = ERRORS.render(page)
        filename = re.search(r'forth-bootstrap/cc/([^`:]+)', unpadded_row)[1]
        code = re.match(r'^\|\s*`?(\d+)', unpadded_row)[1]
        row = next(line for line in rendered.splitlines()
                   if '<a id=' in line and filename in line
                   and re.match(rf'^\|\s*`?{code}`?\s*\|', line))
        self.assertRegex(row, r'\|<a id="diagnostic-[^"]+"></a>`forth-bootstrap/cc/')
        self.assertEqual(ERRORS.render(rendered), rendered)

    def test_unknown_numeric_row_format_fails_closed(self):
        page = ERRORS.PAGE.read_text(encoding='utf-8')
        page = page.replace('## Codes in detail',
                            '## Codes in detail\n\n| 999 | unmapped source |')
        with self.assertRaisesRegex(ValueError, 'unrecognized diagnostic row'):
            ERRORS.render(page)


if __name__ == '__main__':
    unittest.main()
