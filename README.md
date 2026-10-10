# forth-bootstrap-book

The literate book of [forth-bootstrap](https://github.com/delta9000/forth-bootstrap):
how a 1,772-byte hex0 Forth, the Forth library on it, a C compiler written
in that Forth, and the chain from there to Linux are built, chapter by
chapter.  Every code block tagged `file=PATH`
quotes forth-bootstrap's `PATH` (`seed/000-seed.hex0`, `forth/*.fth`,
`cc/*.fth`) byte for byte, so the book and the sources cannot drift apart
unnoticed.

It is in four parts: the seed's machine code, the Forth library and
assembler, the C compiler, and the bootstrap from seed-cc through GCC to
Linux under K0 and K1.  It is published at
https://delta9000.github.io/forth-bootstrap-book/.  The book came from
seed-forth, where forth-bootstrap also started; the routes that stayed
there are described in Appendix C.

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
