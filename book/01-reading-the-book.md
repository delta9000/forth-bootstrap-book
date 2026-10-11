# Chapter 1 — Reading the book

In this chapter you will build a 1,772-byte program, give it a new word,
and run that word. The rest of the book follows what becomes possible when
each tool can build the next: a Forth library, a C compiler, a Unix
toolchain, and a Linux kernel built from source.

You work with a complete, pinned source checkout from the first chapter.
The book opens that working system one mechanism at a time. Read to
explain what changes; run a checkpoint to test the result; change a small
input to find out whether your explanation holds.

## Follow the route

Chapter 2 introduces the starting artifact; Chapter 3 places it among
source bootstrap projects. The four parts then climb this ladder:

| Where | Capability gained | Artifact the next stage uses |
|---|---|---|
| [Part 1, Chapters 4–13](part-1-asm.md) | Turn annotated hexadecimal into a program that compiles and runs Forth words | `seed-forth`, built from `seed/000-seed.hex0` by the inherited `hex0-seed` |
| [Part 2, Chapters 14–26](part-2-forth.md) | Express control flow, manage memory, and assemble a separate executable | `forth/010-lib.fth`, shared by the M1 assembler and the C compiler |
| [Part 3, Chapters 27–49](part-3-compiler.md) | Compile C, write object files, resolve symbols, and supply a runtime | The Forth compiler, linker, target headers, and C runtime |
| [Part 4, Chapters 50–53](part-4-bootstrap.md) | Build the command-line tools and repeat GCC's construction | `seed-cc`, `seed-ar`, build tools, and compared GCC 4.0.4 installations |
| [Part 4, Chapters 54–55](54-k0-and-k1.md) | Rebuild the toolchain inside a guest, then build and boot Linux | K0, K1, GCC 10.5.0, and the Linux kernel |

The Forth library is a source file loaded by a running seed. The compiler
is also Forth source, loaded into that process. Keeping that distinction
between a file and the program running it will make the later handoffs
easier to follow.

Choose a route according to the question you brought:

- **Understand the whole construction.** Read in sidebar order. At each
  part boundary, use its map to name the artifact you have gained and
  the next thing it must build.
- **See a compiler work, then open it up.** Establish the setup below,
  read the [Forth notation](14-lib-01-stacks-and-words.md), then follow
  the [expression checkpoint](34-expressions-part-2.md#try-it) and the
  first [compiler-entry checkpoint](38-main-and-bootstrap-chain.md#try-it).
  Return to Chapters 27–37 to explain each layer those commands load.
- **Audit the bootstrap claim.** Read Chapters 2–3, the
  [Stage A comparison](38-main-and-bootstrap-chain.md#stage-a-the-parity-proof),
  and Chapters 50–55. Track who builds each artifact, what gets compared,
  and which host or guest runs it. The long runs have their own resource
  requirements; reading their evidence does not require launching them.

The [glossary](62-glossary.md) gives definitions, the
[concept index](63-concepts.md) finds mechanisms, and the
[word index](WORD-INDEX.md) finds individual Forth words. Use these as
return paths when following a focused route.

Appendix lettering starts at C to preserve references in the quoted
source. The former primitive-reference and memory-map appendices are now
Chapters 13 and 5.

## Starting skills and tools

The intended reader can follow a short function and wants to understand
how source becomes an executable. No Forth or assembly-language experience
is assumed. You should be able to edit a text file and use a shell's
working directory, pipes (`|`), and redirection (`>`). Expect binary and
hexadecimal notation: a byte is eight bits, and two hexadecimal digits
represent one byte. For example, `0x10` is decimal 16, and `0xFF` is 255.
Chapter 4 teaches the instruction fields; Chapter 6 gives the compact
stack notation before Chapter 14 develops it fully.

Part 3 adds a different reading task: recognizing the C declarations and
expressions that the Forth compiler consumes. Its
[C-reading bridge](part-3-compiler.md#reading-the-c-input) introduces the
pointer, array, and record notation needed for that step, with a short
self-check. No prior course in C implementation or calling conventions
is needed. Use the
[capability checks](63-concepts.md#capability-checks-at-the-transitions)
when entering a later part or returning after a break; the sidebar is a
reading sequence, not a test of what you already know.

A quick self-check: from the book root, what file does
`forth-bootstrap/seed-forth` name, and how many bytes do `48 83 ED 08`
represent? The answers are the executable inside the source checkout and
four bytes. If either is unfamiliar, use the working-directory section
below and the opening of Chapter 4 before continuing. You can read and
trace the listings while arranging the Linux environment for execution.

Alongside Bash and ordinary shell utilities, the early inspection
checkpoints use `objdump` and `readelf` from GNU binutils. These are host
inspection tools: they display instructions and ELF fields in an already
built file. They do not build the seed. Their checkpoints explain the
options they use.

## Read source, then run a checkpoint

A source fragment answers “how does this work?” Its introduction names the file and line so you can locate it in the checkout. Read the surrounding explanation before following the instructions or definitions. A code block tagged `file=` or `chunk=` belongs to the book's source representation; it is not a shell command to paste into a terminal.

A **checkpoint** answers “did this particular operation produce the stated result?” Paste its shell commands into a terminal and compare the output. Read the conditions next to the command: a result applies to that input and environment. Building the seed, for example, does not establish that the later compiler or Linux build works. Those checks belong with the chapters that introduce them.

You can read a fragment without building what precedes it, but a checkpoint needs the setup its chapter names.

For a useful reading session, stop at one mechanism and do three things:

1. Name its input, the state it changes, and the result another layer uses.
2. Predict the chapter's checkpoint before running it. Compare the output
   and exit status with the stated result.
3. Attempt one **Trace** or **Verify** exercise. Use the linked feedback
   afterward to revise your explanation, then retry with a different input.

You can stop after a short checkpoint and return later. Definitions live
in one seed process; the next invocation starts fresh. The chapter's load
commands recreate the library and compiler state they require, so there
is no interactive session you must keep alive through the book.

<details>
<summary>Exit statuses and temporary paths in later checkpoints</summary>

Some test programs deliberately return a nonzero value. Checkpoints capture
that status before asserting it, so an inherited Bash `-e` setting does not
mistake the expected result for an interrupted test. Generated-path examples
use checked, short `/tmp/book-probe.XXXXXXXXXX` directories: the Forth `s,`
reader accepts a single token, so shell quoting cannot make a path with
spaces (or more than 255 token bytes) safe inside generated Forth source.
Follow any fixed-output-path warning and do not run those examples concurrently.

</details>

## Choose the working directory

The book repository and the source checkout have different roots. In this layout, the book lives in `book/`, and the source checkout lives at `./forth-bootstrap`. From the book repository root, enter it with `cd forth-bootstrap`. **Checkpoint commands run from the `forth-bootstrap` repository root**, unless a checkpoint explicitly changes directory. Paths such as `seed/000-seed.hex0` are relative to that root. Source citations include the `forth-bootstrap/` prefix to distinguish the checkout from the book.

Use a Linux x86-64 environment for the seed checkpoints. If your machine uses another platform, provide that environment through a VM or emulation before running them. For the setup below, have Bash, the usual shell utilities, and the checked-out executable at `vendor/stage0-posix/bootstrap-seeds/POSIX/AMD64/hex0-seed` available. The repository's README gives the recursive submodule setup command. The build script reports a missing assembler and gives narrower setup instructions if it cannot find one. Further chapters introduce their own tool requirements.

## Try it: establish the setup

After entering `forth-bootstrap`, run the following in Bash. The file check confirms that the working directory contains the seed source; the build creates `seed-forth` there using the assembler selected by the script (`forth-bootstrap/seed/build.sh:12`). The last line starts the new seed and stops it with `bye`.

```sh
(
set -euo pipefail
basename "$PWD"
test -f seed/000-seed.hex0
./seed/build.sh
echo bye | ./seed-forth
)
```

The observed output follows. The first line is the working directory, which should be your `forth-bootstrap` checkout. The `test` command and the seed's `bye` produce no output.

```text
forth-bootstrap
Built seed-forth (1772 bytes) using vendor/stage0-posix/bootstrap-seeds/POSIX/AMD64/hex0-seed
```

Now give the seed a word it did not start with:

<!-- tryit: expect "Hi" -->
```sh
printf '%s\n' ': hello [lit] 72 emit [lit] 105 emit [lit] 10 emit ; hello bye' | ./seed-forth
```

Observed output:

```text
Hi
```

The colon starts the definition of `hello`; the semicolon finishes it.
Each `[lit]` supplies the following decimal value, and `emit` writes that
value as a byte: 72 is `H`, 105 is `i`, and 10 is the newline. The final
`hello` calls the new word and `bye` exits. Chapters 8–12 open the seed
mechanisms behind those steps.

The program has extended its vocabulary using only its own input. Part 2
uses that same ability to load the library; Part 3 uses it to load the C
compiler.

For later sessions, the [workshop](labs.md) collects useful short
checkpoints. From the **book repository root**, use
`python3 tools/book-lab.py list 1` to see this chapter's commands,
`python3 tools/book-lab.py show 1.2` to inspect the `hello` checkpoint,
and `python3 tools/book-lab.py run 1.2` to execute it and compare its
output. The companion reads the chapter's code directly and runs it
from the source checkout; it reports blocks that require manual setup
or a longer build.

## Exercise

**Verify (easy).** After the checkpoint, find `seed-forth` relative to the book repository root and give its path from there. Then explain why a later command containing `./seed-forth`, run from the book repository root instead of `forth-bootstrap`, would name the wrong file.

**Modify (easy).** Change 105 to 111 in the `hello` definition. Predict
the output using the fact that byte 111 is `o`, then run the whole command
again. Explain why running only `hello` in a new seed process would not
recover the definition from the earlier one.
