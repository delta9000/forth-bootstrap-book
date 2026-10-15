# Mechanism figures

The SVG assets in `book/images/mechanisms/` are the editable, self-contained
figures for Chapters 28, 37 and 50. All text and geometry are local SVG elements;
there are no downloaded images or remote font requests. The intentional
light drawing surface stays readable in dark reader themes. On narrow screens,
the chapter viewport scrolls horizontally; the full-size link opens the vector
for browser zoom. Print rules fit each figure and its caption on a page.

## Reproduce

Use Python 3 and `svgwrite==1.4.3` for the scope and process generators. The macro
generator uses only Python's standard library. Install the pinned dependency in
your development environment with `python3 -m pip install -r tools/figures/requirements.txt`.
The book build itself needs no Python drawing dependency: SVGs are checked in.

Run from any directory; default output paths are relative to the repository:

```sh
python3 tools/figures/draw_scope_storage.py
python3 tools/figures/generate_macro.py
python3 tools/figures/generate_process.py
```

Each script also accepts an optional output SVG path, useful for comparing a
fresh generation without overwriting the checked-in asset. The parent directory
must exist. DejaVu Sans and DejaVu Sans Mono are preferred for rendering; SVG
text remains editable. Inkscape can export vector PDFs or PNG previews, e.g.
`inkscape book/images/mechanisms/process-handoff.svg --export-filename=process.pdf`.

## Evidence and boundaries

All three figures were checked against the book's pinned `forth-bootstrap`
revision `b25487ad4d62adb950c3372de43564dfcfabdd87`. Their SVG title/description,
chapter alt text, and nearby prose provide text equivalents.

- **Scope:** the Chapter 37 core-profile, no-parameter trace. Symbol rows can be
  reused after scope pop; `cc-fn-local-count` still increases. Slots are eight
  bytes; 32 slots occupy the fixed 256-byte frame. The compiler and runtime
  timelines are separate. Hatched slots denote earlier allocation, not live
  objects or known byte values. Sources: `cc/070-cc-sym.fth:96–138,187–204`,
  `cc/110-cc-decl.fth:34–46,496–503`, `cc/090-cc-emit.fth:67–69,335–359`,
  `cc/112-cc-stmt.fth:19–33`, `cc/114-cc-func.fth:273–310`.
- **Macro:** the Chapter 28 top-level legacy `SQUARE(ROWS)` expansion. The bars
  show lifetimes, not byte-proportional allocation sizes. The final output is
  in `cc-src-buf`; a nested call may instead emit to an older temporary below
  its saved cursor. A source-derived allocation trace accompanies an executed
  checkpoint that returned `\n\n ((   4   ) * (   4   )) \n`; the figure omits
  separator blanks. Sources: `cc/040-cc-prep.fth:171–187,937–944,1027–1084,1367–1394`.
- **Process:** a manual, successful host-Linux trace, not captured execution.
  The example assumes standard descriptors 0/1/2 are open and not close-on-exec,
  the child PID is 202, open returns descriptor 3, and subsequent operations
  succeed. Lane order is not a cross-process schedule. This does not depict
  K0's serialized implementation. Sources: `cc/driver/seed-cc-start.fth:65–75,281–314`
  and `cc/driver/seed-cc-boot/tools-unit.fth`.

The figures have been technically and visually reviewed; no novice learning
study has been performed. Structural tests in `tools/tests/test_diagrams.py`
check local references, captions, SVG metadata, and the scope exercise's reveal
boundary. Generator reproduction and rendered proof remain additional checks.

`tools/tests/test_figure_contrast.py` checks the actual SVG paints with the
[WCAG sRGB contrast formula](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html):
at least 4.5:1 for every text label, without relying on the large-text exception
when figures are scaled. It resolves the surface at each reviewed label anchor
in paint order, includes all hatch paints beneath text, and composites opacity.
It also conservatively checks strokes and dark graphical glyphs against every
used light surface at 3:1. The light hatch texture is redundant with readable
labels/history marks, so it is treated as a background, not an essential glyph.
These source-color checks need no optional drawing dependencies and run in
`./check.sh`. They do not establish full WCAG conformance or replace rendered
checks for text extent, overlap, clipping, or readability at the final size.
