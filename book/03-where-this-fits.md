# Chapter 3 — Where this fits: routes and history

A source bootstrap inherits tools and branches into onward routes.
Trace those dependencies to place its seed among the surrounding projects.
That gives you a way to distinguish this book's current route from the older
seed-forth routes you may encounter in project history.

## The projects around the seed

The bootstrappable-builds community supplies much of the surrounding work.
The project's credits name Jeremiah Orians' stage0-posix, mescc-tools,
M2-Planet and M2libc, alongside live-bootstrap
(`forth-bootstrap/CREDITS.md:42`). Their connections to this checkout are
concrete:

| Project | Connection to forth-bootstrap | Source |
| --- | --- | --- |
| stage0-posix | Supplies the starting `hex0-seed` binary and the mescc-tools-extra utility sources. | `forth-bootstrap/CREDITS.md:12–13` |
| mescc-tools | Supplies kaem, the shell source used by the route. | `forth-bootstrap/CREDITS.md:14` |
| M2-Planet | Supplies the C compiler source used for the Stage A comparison. | `forth-bootstrap/CREDITS.md:15` |
| live-bootstrap | Supplies patches and much of the ordering followed by the GCC climb. | `forth-bootstrap/CREDITS.md:16–17`, `forth-bootstrap/CREDITS.md:44` |

These are different kinds of dependency. An inherited executable is already
machine code when the route begins. Inherited source requires a builder.
A borrowed patch or build order carries knowledge about how to make
upstream packages work together. Keep those distinctions when reading a claim
that a project builds “from source.”

The connection to stage0-posix is visible before the C compiler enters the
picture. The seed build script selects its vendored AMD64 `hex0-seed` by
default, then gives it `seed/000-seed.hex0` as input and `seed-forth` as output
(`forth-bootstrap/seed/build.sh:14`, `forth-bootstrap/seed/build.sh:27`).
The upstream seed is the assembler; the Forth executable from Chapter 2 is
its product. They occupy different places in the dependency chain.

## How the route changed

forth-bootstrap began as route D of the older **seed-forth project**, then
moved into its own repository (`forth-bootstrap/README.md:243`). Distinguish
that project name from the executable named `seed-forth`, which remains in
this checkout (`forth-bootstrap/README.md:15`).

The older project explored several onward routes. Its history records a
route to self-hosted M2-Planet and a handoff into stage0-posix's recipes;
it also records direct TinyCC and pnut routes. Those routes stayed in the
older project when forth-bootstrap split off
(`forth-bootstrap/HISTORY.md:14–29`). Read their reproducibility account as
history in Appendix C, rather than as the operating instructions for this
checkout.

The current route has a different center: the Forth C compiler leads to
`seed-cc`, the tools it builds, and GCC. That is the route identified as D
in the project history (`forth-bootstrap/HISTORY.md:7–10`). The plumbing
recipe orders the tool-building stages before invoking the GCC chain
(`forth-bootstrap/chain/plumbing/chain.kaem:12–16`). Chapter 50 follows
`seed-cc`; Chapter 51 follows those tools; Chapter 52 follows the GCC rebuilds.

What sets this route apart is its middle. After the 229-byte `hex0-seed`
assembles the Forth seed, a C compiler written in that Forth builds the
driver, shell and first Unix tools, and those build GCC 4.0.4, then GCC
10.5.0, then Linux 7.2.8, with no compiler brought in from outside
(`forth-bootstrap/README.md:3–7`). The project history calls it the route
that reaches Linux with no other compiler at all
(`forth-bootstrap/HISTORY.md:7–8`).

M2-Planet still has a role here as a comparison target. Stage A compares
assembly emitted by a Forth-built M2-Planet with assembly emitted by a
GCC-built reference on the same M2-Planet source. The script compares those
outputs, not the compiler executables themselves
(`forth-bootstrap/tests/cc/stage-a-check.sh:59–76`). Chapter 38 returns to
that check. Agreement on this input is a bounded result, not a claim about
every C program. The history explains the names; from Chapter 4 on, the
book reads the machinery itself.

## Try it: measure the shared starting point

Recall the checkpoint working directory from Chapter 1. Run this block from
the `forth-bootstrap` root, with the seed built there. `wc -c` measures the
stage0-posix executable beside its Forth product. The final command uses the
seed's `bye`, taught in Chapter 8, and produces no output.

```sh
wc -c vendor/stage0-posix/bootstrap-seeds/POSIX/AMD64/hex0-seed seed-forth
echo bye | ./seed-forth
```

Observed output:

```text
 229 vendor/stage0-posix/bootstrap-seeds/POSIX/AMD64/hex0-seed
1772 seed-forth
2001 total
```

## Exercise

**Verify — easy.** Use the source citations above to identify which project
supplied the executable that assembles the Forth seed. Then read the checkpoint
output: which file is the inherited executable, and which is the product?
Explain why adding their byte counts does not measure all the source a reader
would need to audit in the later route.
