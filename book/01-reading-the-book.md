# Chapter 1 — Your first word

How much machinery does a program need before it can build something
larger than itself? We will begin with a 1,772-byte program, teach it a
new word, and call that word. The same way of adding words will eventually
give us a C compiler. From there, the book follows the tools that build
GCC and a Linux kernel from source.

You do not need to know Forth or assembly language to start. If you can
follow a short function, edit a text file, and use a shell, you have the
starting skills. We will introduce the machine notation when we reach it.

## Try it: establish the setup

The commands need Linux on an x86-64 processor, Git, Bash, and ordinary
shell utilities. On another platform, use a Linux x86-64 VM or emulation.
You can also follow the example on the page and return to the commands
when that environment is ready.

If you do not have the book checkout, obtain it with
`git clone https://github.com/delta9000/forth-bootstrap-book.git`, then
enter it with `cd forth-bootstrap-book`. This is the **book root**, the
directory containing `book.toml`.

The book contains a second repository, `forth-bootstrap`, with the source
we will study. The first command below initializes that source and its
pinned dependencies; it may download missing checkouts. If that succeeds, the next command
enters the source directory. The remaining commands build the seed and
ask it to exit.

<!-- Run this setup manually from the book root; it initializes dependencies and changes directory. -->
<!-- tryit: skip -->
```sh
git submodule update --init --recursive &&
cd forth-bootstrap &&
(
set -euo pipefail
basename "$PWD"
test -f seed/000-seed.hex0
./seed/build.sh
echo bye | ./seed-forth
)
```

After any Git progress messages, the final output should be:

```text
forth-bootstrap
Built seed-forth (1772 bytes) using vendor/stage0-posix/bootstrap-seeds/POSIX/AMD64/hex0-seed
```

The parentheses run the build checks in a subshell; `set -euo pipefail`
stops that check if a command fails. The build uses the checked-out
`hex0-seed` assembler (`forth-bootstrap/seed/build.sh:12`), which we will
meet in Chapter 3. If it is missing, the script gives setup instructions.
The seed's `bye` produces no output.

Your shell is now in `forth-bootstrap`. **Later checkpoint commands run
from this source directory unless they say otherwise.** Here,
`./seed-forth` names the program we just built, and `seed/000-seed.hex0`
names a source file inside its `seed` directory.

Now give the seed a word it did not start with:

<!-- tryit: expect "Hi" -->
```sh
printf '%s\n' ': hello [lit] 72 emit [lit] 105 emit [lit] 10 emit ; hello bye' | ./seed-forth
```

Observed output:

```text
Hi
```

The shell's `printf` sends a line of text through the pipe, `|`, to the
seed. The text between the single quotes is our first Forth program:

- `: hello` starts a definition named `hello`.
- Each `[lit]` puts the following decimal value into the definition.
  When `hello` runs, that value is supplied to `emit`, which writes one
  byte. Byte 72 is `H`, 105 is `i`, and 10 is a newline.
- `;` finishes the definition. The following `hello` calls it, and `bye`
  exits the seed.

A **word** is a named Forth operation. Some words, such as `emit`, are
built in; `hello` is one we have added. The seed has turned our definition
into instructions it can run. We did not rebuild its executable to do so.
The new definition lives in this running process: start `./seed-forth`
again and you must supply the definition again.

## Try a change

**Modify (easy).** Change 105 to 111 in the `hello` definition. Predict
the output using the fact that byte 111 is `o`, then run the whole command
again. Explain why running only `hello` in a new seed process would not
recover the definition from the earlier one.

## What we will build from here

The first question is how a program this small can read a name, remember
a definition, and execute it. Part 1 opens the seed to answer that
question. The later parts use the ability we have just tried:

1. [The machine-code seed](part-1-asm.md). Follow bytes, stacks, and
   names until you can trace `hello` through the whole program.
2. [The Forth library](part-2-forth.md). Add words for loops, memory,
   and writing bytes, giving the C compiler its working vocabulary.
3. [The C compiler](part-3-compiler.md). Load more Forth definitions
   that read C source and produce programs, then add linking and a runtime.
4. [The bootstrap](part-4-bootstrap.md). Use those tools to build
   larger tools, rebuild GCC, and build and boot Linux.

The library and compiler begin as Forth source loaded into the seed,
much as the `hello` definition was. The main path goes from the completed
library in Chapter 25 straight to the compiler in Chapter 27; the separate
M1/hex2 assembler is an optional [Appendix I](26-m1-and-hex2.md). Later
chapter numbers keep their existing references. For now, Chapter 2 takes
a closer look at the small executable we have in hand.

## Reading and trying

The book keeps the complete source nearby and explains it a piece at a
time. A listing with a source path shows the implementation; a **Try it**
checkpoint gives shell commands and a result to compare. Source listings
are for reading, not shell commands to paste. Fences tagged `file=` or
`chunk=` preserve the exact source, including its comments.

At a checkpoint, predict the result before running it. Then try an
exercise with a changed input. If your prediction differs from the
result, use the chapter's trace and any linked hints or feedback to find
the step that changed.
You can stop after a short checkpoint; later commands reload the state
they need, so there is no session you must keep alive through the book.

The [lab companion](labs.md) is an optional way to run these same commands
and return to short milestones. The [glossary](62-glossary.md),
[concept index](63-concepts.md), and [word index](WORD-INDEX.md) are there
when you need to find a term again. If you already know the lower layers,
the [focused reading routes](63-concepts.md#focused-reading-routes) lead
into the compiler and bootstrap chapters.

## Exercise

**Verify (easy).** After the checkpoint, find `seed-forth` relative to the
book repository root and give its path from there. Then explain why a
command containing `./seed-forth`, run from the book repository root
instead of `forth-bootstrap`, would name the wrong file.
