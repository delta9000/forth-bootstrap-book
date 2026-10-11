# Chapter 3 — What builds the seed?

We have run `seed-forth` and measured its bytes. But before we could run
it, another program had to make that executable. The build message names
that program: `hex0-seed`.

Its job is small. It reads pairs of hexadecimal digits from
`seed/000-seed.hex0` and writes their byte values to `seed-forth`, ignoring
comments. The source's opening `7F 45 4C 46` becomes the four bytes we
inspected in Chapter 2. The source file already specifies the machine
instructions; this assembler does not have to choose instructions for us.

## Builder, source, product

There are three things to keep separate in the first build:

| Role | File | What it contributes |
|---|---|---|
| Builder | `hex0-seed` | The running program that translates the hexadecimal |
| Source | `seed/000-seed.hex0` | The annotated byte values we can read and change |
| Product | `seed-forth` | The executable the builder writes |

The script selects the vendored AMD64 `hex0-seed`, then gives it the
source path and output path (`forth-bootstrap/seed/build.sh:14`,
`forth-bootstrap/seed/build.sh:27`). The builder comes from
[stage0-posix](https://github.com/oriansj/stage0-posix), which this project
credits for its starting binary (`forth-bootstrap/CREDITS.md:12`).

This is where the construction starts: the 229-byte `hex0-seed` arrives
as an **inherited executable**, already in machine-code form. We use it
to build the 1,772-byte Forth seed from the source in front of us. We have
not built the starting assembler in this step, and adding its size to the
Forth seed's size would not describe the whole environment. Linux is
already running both programs on the processor.

## How a small builder leads to larger ones

The next handoff works differently. We run `seed-forth` and feed it Forth
source. As with `hello`, it compiles those definitions into its own running
process. A library supplies more words; further definitions make a C
compiler. That compiler can write separate executables for the tools that
follow.

This lets us use much larger sources without bringing in an already-built
C compiler. The route goes through its own C compiler and Unix tools to
GCC 4.0.4, then GCC 10.5.0, and Linux 7.2.8
(`forth-bootstrap/README.md:3–7`). Those later programs bring substantial
**inherited source**: upstream code that still needs a builder. Starting
with a small executable does not make all that source small or remove the
need to inspect it.

The later build chapters follow each builder and what it produces. They
also distinguish building an artifact from comparing it with another
build or running it. For now, we have one completed handoff to examine:
hexadecimal source has become a Forth executable. Part 1 explains how the
bytes in that executable let us add and run a word.

The [project history and credits](57-historical-reproducibility.md#the-projects-around-the-seed)
place this route among the other bootstrap projects. They are useful
background when you want to compare routes; the seed walkthrough does not
require those project names.

## Try it: measure the shared starting point

Recall the checkpoint working directory from Chapter 1. Run this block from
the `forth-bootstrap` root, with the seed built there. `wc -c` measures the
stage0-posix executable beside its Forth product. The final command asks the seed to exit with `bye`, as in Chapter 1,
and produces no output.

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

**Verify (easy).** Use the source citations above to identify which project
supplied the executable that assembles the Forth seed. Then read the checkpoint
output: which file is the inherited executable, and which is the product?
Explain why adding their byte counts does not measure all the source a reader
would need to audit in the later route.
