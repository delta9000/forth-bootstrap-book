#!/usr/bin/env python3
"""Derive Appendix G's numeric lookup and row anchors from its compiler tables.

Run with --check to detect drift. The file-first tables remain the only edited
catalogue; this is navigation over those tables, not a source-code error census.
Controller, seed, driver and runtime statuses are intentionally outside it.
"""
import argparse
from collections import defaultdict
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'book/61-error-codes.md'
START = '<!-- BEGIN GENERATED NUMERIC LOOKUP -->'
END = '<!-- END GENERATED NUMERIC LOOKUP -->'
ANCHOR = re.compile(r'<a id="diagnostic-[^"]+"></a>')
ROW = re.compile(r'^\|\s*`?(\d+)`?\s*\|\s*`forth-bootstrap/cc/([^`:]+):[^`]+`\s*\|')
PREFIXES = (
    ('cc-va-die', 'varargs:'),
    ('cc-bf-die', 'bitfield:'),
    ('cc-ag-die', 'aggregate-abi:'),
    ('cc-ld-die', 'long-double:'),
    ('cc-f64-fail', 'cc-f64-literal:'),
)


def render(text):
    """Replace the marked lookup and refresh anchors, preserving table contents."""
    if text.count(START) != 1 or text.count(END) != 1:
        raise ValueError('expected exactly one numeric lookup marker pair')
    before, rest = text.split(START)
    _, after = rest.split(END)
    text = before + START + END + after
    lines = ANCHOR.sub('', text).splitlines()
    active = False
    counts = defaultdict(int)
    entries = defaultdict(list)
    for i, line in enumerate(lines):
        if line == '## Codes in detail':
            active = True
        elif line == "## The build controller's codes":
            active = False
        match = ROW.match(line) if active else None
        if match is None:
            # Fail closed on a new numeric table form instead of omitting it.
            if active and re.match(r'^\|\s*`?\d', line):
                raise ValueError(f'unrecognized diagnostic row: {line}')
            continue
        code, filename = match.groups()
        base = f'diagnostic-{code}-{filename.replace(".", "-")}'
        counts[base] += 1
        anchor = base if counts[base] == 1 else f'{base}-{counts[base]}'
        # Keep the numeric cell unchanged for the citation validator. Put
        # HTML inside the source cell so Markdown still renders one table.
        source_start = line.index("`", line.index("|", 1))
        lines[i] = line[:source_start] + f'<a id="{anchor}"></a>' + line[source_start:]
        route = line.split('|')[3]
        prefix = next((value for word, value in PREFIXES if word in route), None)
        label = f'`{filename}`'
        if prefix:
            label += f' (`{prefix}`)'
        if counts[base] > 1:
            label += ' (shared check)'
        entries[int(code)].append(f'[{label}](#{anchor})')
    if not entries:
        raise ValueError('no compiler diagnostic rows found')
    lookup = [START,
              '<!-- Generated from the tables below by tools/gen-error-index.py. -->',
              '| Code | Candidate source files and special prefixes |',
              '|---:|---|']
    lookup += [f'| {code} | ' + ' · '.join(routes) + ' |'
               for code, routes in sorted(entries.items())]
    lookup += [END]
    return '\n'.join(lines).replace(START + END, '\n'.join(lookup)) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    old = PAGE.read_text(encoding='utf-8')
    try:
        new = render(old)
    except ValueError as error:
        parser.error(str(error))
    if args.check:
        if old != new:
            print('gen-error-index: stale; run python3 tools/gen-error-index.py')
            return 1
        print('gen-error-index: numeric lookup is up to date')
    else:
        PAGE.write_text(new, encoding='utf-8')
        print('gen-error-index: updated numeric lookup and diagnostic anchors')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
