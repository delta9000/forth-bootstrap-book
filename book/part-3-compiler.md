# Part 3 — compiler

Part 3 builds a C compiler in Forth. Its layers, `cc/020` through
`cc/141`, are loaded by the seed after the library. They read C source
from standard input and write an executable or a relocatable object
directly. No C compiler on the host runs in this Part.

The Part has two halves. Chapters 27–38 build a compiler for the C subset
that M2-Planet is written in. The first half ends with Stage A: the
Forth compiler's M1 for M2-Planet equals a GCC-built M2-Planet's. Chapters 39–49 extend the same compiler toward GCC 4.0.4's own
source, adding the storage model, objects, calls and language features
that compiler needs.

- [Chapter 27](27-arena-and-io-buffers.md) sets up the arena and the I/O
  buffers that every later layer shares.
- [Chapters 28](28-the-preprocessor.md) and [29](29-the-lexer.md) turn
  source text into preprocessed tokens.
- [Chapter 30](30-types-and-symbols.md) records types and symbols.
- [Chapters 31](31-elf-and-codegen-part-1.md) and
  [32](32-codegen-part-2.md) emit ELF, instructions, calls and globals
  straight from Forth words.
- [Chapters 33](33-expressions-part-1.md)–[36](36-statements-if-while-for-return.md)
  parse expressions, declarations and statements.
- [Chapter 37](37-functions-and-scope.md) assembles whole translation
  units, and [Chapter 38](38-main-and-bootstrap-chain.md) adds the entry
  word and runs Stage A.
- [Chapters 39](39-lp64-storage-and-initializers.md)–[42](42-linker-and-archives.md)
  add LP64 storage, relocatable objects, System V calls, and a Forth
  linker with archives.
- [Chapters 43](43-runtime-and-libc.md) and [44](44-target-headers.md)
  supply the C runtime, libc and target headers.
- [Chapters 45](45-typed-constants.md)–[49](49-aggregate-abi.md) add typed
  constant expressions, varargs, floating values, bitfields and records
  passed by value.

Each checkpoint compiles a small C program with the layers built so far,
then runs it.
