# forth-bootstrap-book

The literate book of [forth-bootstrap](https://github.com/delta9000/forth-bootstrap):
how a 1,772-byte hex0 Forth, the Forth library on it, a C compiler written
in that Forth, and the chain from there to Linux are built, chapter by
chapter.  Every code block tagged `file=PATH`
quotes forth-bootstrap's `PATH` (`seed/000-seed.hex0`, `forth/*.fth`,
`cc/*.fth`) byte for byte, and publication is gated on that check, so the
book and the sources cannot drift apart unnoticed.

It is in four parts: the seed's machine code, the Forth library and
assembler, the C compiler, and the bootstrap from seed-cc through GCC to
Linux under K0 and K1.  It is published at
https://delta9000.github.io/forth-bootstrap-book/.  The book came from
seed-forth, where forth-bootstrap also started; the routes that stayed
there are described in Appendix C.

```sh
git submodule update --init --recursive   # forth-bootstrap, and its vendor/ submodules
./check.sh                                # regressions, tangle, numeric/citation checks, selected seed examples, index, local links
./check.sh --static                       # structural checks without executing the seed
mdbook build                              # mdBook 0.5.4; renders book/ into docs/ (book.toml)
python3 tools/check-links.py --html docs   # require published pages and their target anchors
```

`./check.sh` checks against the `forth-bootstrap` submodule, or against
another checkout named by `FORTH_BOOTSTRAP=/path/to/forth-bootstrap`.  It
needs bash, Python 3, coreutils and awk; selected seed-pipeline examples run
forth-bootstrap's `seed-forth`, which `check.sh` builds first using its pinned
vendored hex0-seed. The runner reports executed, skipped and unselected blocks;
it does not run every shell checkpoint or verify every displayed transcript.
Long compiler-chain and QEMU runs remain separate, explicit tasks. Full logs
are retained in CI. See [the editorial notes](book/65-editorial-notes.md#checks)
for the exact verification boundaries.

`tools/` holds the checkers: `tangle.sh` and `tangle.awk` (extract and
verify the `file=` blocks), `check-numbers.py`, `check-tryit.py`,
`gen-index.py` (writes `book/WORD-INDEX.md`) and `check-links.py`.  The
book is under the [MIT License](LICENSE), as forth-bootstrap is.
