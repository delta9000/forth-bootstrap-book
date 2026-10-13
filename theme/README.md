# Seed-Forth highlighting

`forth-highlight.js` is a small, local DOM highlighter for the source pin in
this book. mdBook 0.5.4 bundles highlight.js 10.1.1 without Forth support.
The extension runs after mdBook's normal highlighting, only on
`pre > code.language-forth`. It does not replace highlight.js, infer Forth
from unlabeled text, rewrite fences, or change copied source. All generated
markup is made with DOM text nodes, never interpolated HTML.

## Dialect contract

The scanner follows `seed/000-seed.hex0`'s `read_word` and
`parse_decimal_code` and the source-reading words in `forth/010-lib.fth`,
`cc/020-cc-arena.fth`, `cc/050-cc-lex.fth` and `cc/100-cc-expr.fth`:

- Only space, tab, CR and LF split tokens; dictionary matching is case-sensitive.
- Exact tokens `\` and `(` start comments. Line comments end at LF;
  parenthesized comments end at the first `)`, without nesting.
- Only an unsigned ASCII-decimal operand of `[lit]` is numeric syntax.
  Bare `123`, `1+`, `2^63`, `0branch-xt`, signs and hex notation are not numbers.
- `[char]` consumes one token. Interpreted `char`, `s,`, `kw,` and `token`
  also consume one token; quotes and backslashes within that token are data.
  There is no invented `s"`/`."` grammar, escape syntax or base-switch syntax.
- `:`, `constant`, `create`, `variable`, `defer` and `code:` identify a
  following definition name when interpreted. Tick and `is` identify one
  reference; `cc-binop,` identifies two. Comments may intervene.
- `if,`/`else,`/`then,`, `begin,`/`while,`/`repeat,`/`until,`/`again,`,
  `exit,`, `branch` and `0branch` are exact control-word matches. A compiler
  word such as `cc-parse-if` remains an ordinary word.

Inside a colon definition, ordinary source-reading words are compiled calls;
their next source token is not an operand. `[lit]` and `[char]` still consume
operands. Thus `: constant : push-body, ... ;` does not invent a definition
named `push-body,`, and `[char] ;` does not terminate the current definition.

A body excerpt with an unquoted `;` before any opening `:` starts in
compile context. Otherwise an excerpt starts in interpret context. This is a
bounded lexical heuristic for the book's current excerpts, not a Forth
interpreter: arbitrary `STATE` writes, redefined immediate words and new custom
source readers cannot be inferred. For example, standalone `' ;` is ambiguous
without surrounding context. Binary/NUL input is outside this text grammar.
When changing the source pin or adding a new source reader, update the rules
and fixtures together. Source reconstruction remains the independent authority.

## Presentation and checks

Definitions and control words are bold; comments are italic, so some structure
also survives monochrome printing. Light/rust and coal/navy/ayu have separate
explicit palettes; every small-text foreground exceeds WCAG's 4.5:1 contrast
threshold against its listing background. Print uses dark text on white.
Aligned source scrolls horizontally on narrow screens; overflowing listings
get a keyboard tab stop that is removed when the listing fits. Print softly
wraps long lines. In `reader.js`, unmodified Left/Right events from any fenced
code listing stop before mdBook's chapter shortcut, leaving the browser's native
scrolling, selection and editing action intact. This applies at scroll boundaries
and after resizing to fit, so an extra arrow press cannot leave the chapter.
Tab, modified keys, and chapter arrows outside listings keep their existing
behavior. None of this inserts characters into copied code.

Run `./check.sh`, `mdbook build`, and
`python3 tools/check-highlighting.py --html docs`. The latter checks actual
script order/assets, source-to-HTML Forth coverage and the bundled highlight.js
setup, then tests DOM preservation and repeat highlighting on the rendered
listings including the print edition. It also executes the rendered mdBook
chapter-navigation handler before the rendered reader script: the regression
reproduces the original conflict, then checks event propagation, native-default
preservation, scroll bounds, other languages, modifiers and outside-code arrows.
These are code/DOM and calculated-color
checks, not screenshots, measured layout, printed output or screen-reader tests.
