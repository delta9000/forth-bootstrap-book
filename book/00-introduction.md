# Introduction

Every compiler you have used was built by another compiler. That one was
built by an earlier one, and so on back through decades of binaries that
nobody now has the source or the patience to reread. In 1984 Ken Thompson
showed why this matters: a compiler can be made to insert code into the
programs it builds, including into the next version of itself, while the
source of every program involved stays clean. Reading the source of your
compiler does not tell you what your compiler's executable does. Only
the chain of executables that built it can.

This book follows one answer to that problem from start to finish. Begin
with a program small enough to read completely, byte by byte. Use it to
build everything else from source, and record at each step which program
built which. If the starting program is honest and every later step is
built from source you can inspect, then no compiler binary of unknown
origin has touched the result.

## The route

The starting program is `hex0-seed`, 229 bytes from the
[stage0-posix](https://github.com/oriansj/stage0-posix) project. All it
does is turn pairs of hexadecimal digits into bytes. We use it once, to
build a 1,772-byte Forth written as annotated hexadecimal: 32 built-in
words and a compiler for new ones. Everything above that point is source.

1. A Forth library, loaded into the running seed, adds loops, memory
   management and byte writers.
2. A C compiler written in that Forth reads C and writes x86-64
   executables, object files and archives.
3. That compiler builds a C driver and archiver, a shell, `make` and the
   other Unix tools that a real build expects.
4. Those tools build binutils and GCC 4.0.4. GCC then rebuilds itself
   until three successive builds produce the same installed files.
5. The route climbs through later compilers to GCC 10.5.0 and builds
   Linux 7.2.8.

The whole route can also run inside two small kernels under QEMU: K0,
written in hexadecimal like the seed, and K1, a C kernel that the seed's
compiler builds. At the end, K1 hands the machine to the Linux kernel the
route has just built, and that kernel boots. No compiler from outside the
route takes part. A host `gcc` appears only in the checks, as a reference
to compare against.

Forth is what makes the first step small. A Forth system is mostly a way
of adding new words to itself, so the seed needs only enough machine code
to read a name, compile a definition and run it. Every later layer is
text that the seed reads, rather than more hand-written machine code.

The route does not remove trust; it moves it somewhere you can see. You
still rely on `hex0-seed`, on the processor, on the kernel that runs the
early stages (the host's Linux, or QEMU in the guest run), and on the
upstream source releases, whose archives are pinned by hash. A small seed does not make GCC's source small. What the route
removes is the inherited compiler binary, the one link that reading source
cannot check.

## Who this book is for

You need to be able to follow a short function, edit a text file and use
a shell. You do not need to know Forth, assembly language or compiler
construction; the book introduces each notation when it is first needed.
If you already know the lower layers, the
[focused reading routes](63-concepts.md#focused-reading-routes) take you
straight to the compiler or to the bootstrap evidence.

The book suits three kinds of reader: someone who wants to see how source
becomes a running program with nothing hidden underneath, someone who
wants to watch a compiler being built one feature at a time, and someone
who wants to audit a bootstrap claim and decide how much it proves.

## What you will build

You will build the seed in the first chapter and give it a word of your
own. From there the checkpoints build the Forth library, compile C
programs with the Forth compiler, and check that compiler against a
GCC-built reference: the Forth compiler builds the M2-Planet C compiler,
and its output must match a GCC-built M2-Planet's byte for byte. You will
then build the C driver and archiver and see them rebuild themselves
identically. The long runs, the host build to GCC's fixed point and the
guest run to Linux, need hours and a capable machine. The book explains
them in full and shows their recorded results, so you can follow them
without running them.

## How the book is organized

| Part | What it teaches | What you have at the end |
|---|---|---|
| Chapters 1–3 | The first word, the seed's size, and what builds it | A running seed and the question the book follows |
| [Part 1 — asm](part-1-asm.md) | x86-64 encoding, ELF loading and every byte of the seed | A full trace of a word through the machine code |
| [Part 2 — Forth](part-2-forth.md) | The Forth library the compiler is written in | A vocabulary for loops, memory and output |
| [Part 3 — compiler](part-3-compiler.md) | A C compiler in Forth, then objects, linking and a runtime | A compiler that can build real C programs |
| [Part 4 — bootstrap](part-4-bootstrap.md) | The tools, GCC's fixed point, K0, K1 and Linux | The chain from 229 bytes to a booted kernel |

Each chapter explains a piece of real source, gives a **Try it**
checkpoint with commands and the output to expect, and ends with
exercises. [Appendix H](66-exercise-feedback.md) has feedback on the
exercises. The [glossary](62-glossary.md), the
[concept index](63-concepts.md) and the [word index](WORD-INDEX.md) help
you find a term or a word again.

## How the book was built and checked

The book is literate. It does not paraphrase the source; it quotes it.
Its code listings, put back together in order, reproduce the seed, the
Forth library and the C compiler exactly: 34 files from a pinned
checkout of [forth-bootstrap](https://github.com/delta9000/forth-bootstrap).
Every change to the book runs `./check.sh`, which reassembles those files
and compares them byte for byte with the source. The same check runs the
selected seed checkpoints and compares their output, checks the byte counts,
offsets and line counts quoted in the prose against the source, and
confirms that every link and index entry resolves. If a listing or a
number in the text drifts from the code, the check fails.

The project itself was built and checked the same way, by comparing bytes
rather than trusting that something works. The C compiler grew one
feature at a time, each behind a passing test. Its output for M2-Planet
matches a GCC-built M2-Planet's exactly. The C driver rebuilds itself
byte for byte. GCC 4.0.4 rebuilds itself until stages 2, 3 and 4 agree.
A second full run of the route produced the same Linux kernel image, bit
for bit. Where the book reports a run that takes hours, it labels the
output as recorded and names the report it comes from.

The project's [HISTORY.md](https://github.com/delta9000/forth-bootstrap/blob/main/HISTORY.md)
tells how the code was written and the tools and methods used to write
it. [CREDITS.md](https://github.com/delta9000/forth-bootstrap/blob/main/CREDITS.md)
lists the upstream projects the route builds on.

## Where to start

Read in order to understand the whole construction. Begin with
[Chapter 1](01-reading-the-book.md), which builds the seed and teaches it
its first word.
