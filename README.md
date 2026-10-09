# forth-bootstrap-book

The literate book of [forth-bootstrap](forth-bootstrap/): how a 1,772-byte
hex0 Forth, the Forth library on it and a C compiler written in that Forth
are built, chapter by chapter.  Every code block tagged `file=PATH`
quotes forth-bootstrap's `PATH` (`seed/000-seed.hex0`, `forth/*.fth`,
`cc/*.fth`) byte for byte, so the book and the sources cannot drift apart
unnoticed.

The book came from seed-forth, where forth-bootstrap also started, and is
being rewritten in four parts.  Until then, some chapters still cite
seed-forth's files and its other routes (TinyCC, pnut, its test suites and
scripts).

```sh
git submodule update --init --recursive   # forth-bootstrap, and its vendor/ submodules
./check.sh                                # tangle --strict, numbers, "Try it" blocks, index, links
mdbook build                              # optional: renders book/ into docs/ (book.toml)
```

`./check.sh` checks against the `forth-bootstrap` submodule, or against
another checkout named by `FORTH_BOOTSTRAP=/path/to/forth-bootstrap`.  It
needs bash, python3 and coreutils; the "Try it" blocks run forth-bootstrap's
`seed-forth`, which `check.sh` builds first.

`tools/` holds the checkers: `tangle.sh` and `tangle.awk` (extract and
verify the `file=` blocks), `check-numbers.py`, `check-tryit.py`,
`gen-index.py` (writes `book/WORD-INDEX.md`) and `check-links.py`.  The
book is under the MIT License, as forth-bootstrap is (its `LICENSE`).
