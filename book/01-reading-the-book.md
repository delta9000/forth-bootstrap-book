# Chapter 1 — Reading the book

This book follows one route from a 229-byte hex0 program to a Linux kernel built from source, reading the code at each step. Each chapter pairs source reading with a checkpoint: read to explain a mechanism, then run a command to test a concrete result. This chapter sets out that route and leaves a built `seed-forth` in the working directory the checkpoints use.

## Follow the route

Start with Chapter 2 for the starting artifact and Chapter 3 for its place among source bootstrap projects. Then follow the sidebar's table of contents, recorded in `book/SUMMARY.md`, through the four parts:

- **Part 1 — asm, Chapters 4–13.** Learn to read the seed itself. Chapter 4 introduces the instruction encoding and stack conventions. Chapter 5 covers the executable's entry and memory map; Chapters 6–8 follow its stack, arithmetic, and Linux operations. Chapters 9–12 connect the dictionary, compiler, branches, and input loop. Chapter 13 collects the primitive contracts for reference.
- **Part 2 — Forth, Chapters 14–26.** Build a library above the seed, then an assembler and linker. Chapter 14 introduces the notation for reading Forth definitions. Chapter 24 builds structured control flow, and Chapter 26 brings the assembler and linker together.
- **Part 3 — compiler, Chapters 27–49.** Follow the C compiler from input handling through executable output, then through the object files, calling conventions, and language support needed by the bootstrap route. Chapter 38 joins the compiler's initial layers; Chapters 39–49 extend them.
- **Part 4 — bootstrap, Chapters 50–56.** Follow the compiler and tools into the larger build chain. Chapter 50 builds seed-cc and seed-ar, Chapter 51 the tools, and Chapter 52 the GCC rebuilds. Chapter 53 audits the sealed host run. Chapters 54–55 take the route through K0 and K1 to Linux under QEMU; Chapter 56 looks beyond that route.

Read in this order on a first pass. You do not need prior Forth knowledge. Keep the [glossary](62-glossary.md) nearby for unfamiliar terms and the [word index](WORD-INDEX.md) for finding a definition again. The part headings and top-level entries in the table of contents give the reading order.

## Read source, then run a checkpoint

A source fragment answers “how does this work?” Its introduction names the file and line so you can locate it in the checkout. Read the surrounding explanation before following the instructions or definitions. A fence tagged `file=` or `chunk=` belongs to the book's source representation; it is not a shell command to paste into a terminal.

A **checkpoint** answers “did this particular operation produce the stated result?” Paste its shell commands into a terminal and compare the output. Read the conditions next to the command: a result applies to that input and environment. Building the seed, for example, does not establish that the later compiler or Linux build works. Those checks belong with the chapters that introduce them.

You can read a fragment without building what precedes it, but a checkpoint needs the setup its chapter names.

## Choose the working directory

The book repository and the source checkout have different roots. In this layout, the book lives in `book/`, and the source checkout lives at `./forth-bootstrap`. From the book repository root, enter it with `cd forth-bootstrap`. **Checkpoint commands run from the `forth-bootstrap` repository root**, unless a checkpoint explicitly changes directory. Paths such as `seed/000-seed.hex0` are relative to that root. Source citations include the `forth-bootstrap/` prefix to distinguish the checkout from the book.

Use a Linux x86-64 environment for the seed checkpoints. If your machine uses another platform, provide that environment through a VM or emulation before running them. For the setup below, have Bash, the usual shell utilities, and the checked-out executable at `vendor/stage0-posix/bootstrap-seeds/POSIX/AMD64/hex0-seed` available. The build script reports a missing assembler and gives submodule setup instructions if it cannot find one. Further chapters introduce their own tool requirements.

## Try it: establish the setup

After entering `forth-bootstrap`, run the following in Bash. The file check confirms that the working directory contains the seed source; the build creates `seed-forth` there using the assembler selected by the script (`forth-bootstrap/seed/build.sh:12`). The last line starts the new seed and stops it with `bye`.

```sh
basename "$PWD"
test -f seed/000-seed.hex0
./seed/build.sh
echo bye | ./seed-forth
```

Observed output is below. The first line is the name of the working directory, which should be your `forth-bootstrap` checkout. The `test` command and the seed's `bye` produce no output.

```text
forth-bootstrap
Built seed-forth (1772 bytes) using vendor/stage0-posix/bootstrap-seeds/POSIX/AMD64/hex0-seed
```

## Exercise

**Verify — easy.** After the checkpoint, find `seed-forth` relative to the book repository root and give its path from there. Then explain why a later command containing `./seed-forth`, run from the book repository root instead of `forth-bootstrap`, would name the wrong file.
