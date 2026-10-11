# forth-bootstrap

**Read the bytes. Build the tools. Follow the chain to Linux.**

This is the literate book of
[forth-bootstrap](https://github.com/delta9000/forth-bootstrap): a
1,772-byte Forth, its Forth library, a C compiler written in that Forth,
and the tools that carry the route through GCC to Linux. The book
connects the actual source to worked traces, runnable checkpoints, and
exercises with feedback. The separate M1/hex2 assembler remains covered
by an [assembler regression check](book/26-m1-and-hex2.md), outside the
book's teaching route.

[Read the book](https://delta9000.github.io/forth-bootstrap-book/) ·
[Start with your first word](book/01-reading-the-book.md) ·
[Open the workshop](book/labs.md)

The four parts cover the seed's machine code, the Forth library, the C
compiler, and the bootstrap through GCC and the K0/K1 guest kernels.
Start in order to understand the whole construction, or use the
[focused reading routes](book/63-concepts.md#focused-reading-routes) for compiler mechanisms and bootstrap evidence. Basic
shell use and the ability to follow a short function are enough to begin;
the book introduces Forth and assembly notation as they become necessary.

## Run your first word

Use Linux x86-64, Bash, and ordinary shell utilities. From the book
repository root, initialize the pinned source and its vendor checkouts:

```sh
git submodule update --init --recursive
```

Build the seed, define `hello`, and call it. This block keeps your shell
in the book root afterward:

```sh
(
  set -euo pipefail
  cd forth-bootstrap
  ./seed/build.sh
  printf '%s\n' ': hello [lit] 72 emit [lit] 105 emit [lit] 10 emit ; hello bye' | ./seed-forth
)
```

The build reports 1,772 bytes; the new word prints `Hi`. Chapter 1
explains the command, and Chapters 8–12 explain how the seed reads,
compiles, and executes it.

The [optional lab companion](book/labs.md) uses Python 3 to show and run
short checkpoints directly from the chapters. Begin with `hello`; return
to the companion when you want another milestone.

## Build and check the book

Publication verifies that canonical source fences (`file=` and `chunk=`)
reassemble the 34 book-taught files in `tools/canonical-sources.txt` byte
for byte. This scope excludes `forth/130-asm.fth`, which stays in the
pinned source checkout and is exercised by the assembler regression
check. Regression, citation, index, example and link checks complement
that source check:

```sh
./check.sh
./check.sh --static
mdbook build                            # mdBook 0.5.4; writes docs/
python3 tools/check-links.py --html docs
python3 tools/check-highlighting.py --html docs
python3 tools/package-book.py            # Python 3.11+; writes the offline ZIP
```

`./check.sh` checks against the `forth-bootstrap` submodule, or against
another checkout named by `FORTH_BOOTSTRAP=/path/to/forth-bootstrap`. It
needs Bash, Python 3.11 or newer, Node.js 22 or newer, coreutils and awk;
selected seed-pipeline examples
run `seed-forth`, which `check.sh` builds first using its pinned vendored
hex0-seed. The checker reports executed, skipped and unselected blocks;
it does not run every shell checkpoint or verify every displayed
transcript. Long compiler-chain and QEMU runs remain separate, explicit
tasks. Full logs are retained in CI.

For prose-only work, `./check.sh --static` runs the structural checks
without executing the seed. Use the full check and the affected chapter's
checkpoint when changing examples. The
[editorial notes](book/65-editorial-notes.md) explain source fidelity,
chapter conventions, and evidence to retain.

Forth listings use the pinned seed's own token rules: definition names,
comma-suffixed control words, `[lit]` decimal operands, character/string
operands, and comments have distinct styles. The local highlighter preserves
copied source, supports all five reading themes, and needs no network. Its
contrast and DOM tests run in `./check.sh`; the rendered-asset check above
also executes mdBook's bundled highlighting setup before testing the Forth
extension. These automated checks do not replace browser or screen-reader QA.
The [highlighter notes](theme/README.md) describe the supported dialect and
excerpt-context limits.

The offline edition is `dist/forth-bootstrap-book.zip`. Extract it and
open `forth-bootstrap-book/index.html`; fonts, search, and reading assets
are included. Its manifest records the source pin, working-tree state,
and SHA-256 hashes. Packaging requires Python 3.11 or newer and a fresh
mdBook render. CI retains the ZIP as a downloadable build artifact.

The book's text is under [CC BY 4.0](LICENSE-CC-BY-4.0); its code,
including the listings quoted from forth-bootstrap, is under the
[MIT License](LICENSE). The book and project grew out of seed-forth;
Appendix C records the historical routes that remained there.
