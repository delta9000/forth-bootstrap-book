# Part 2 — Forth

Part 2 grows the seed's vocabulary in Forth source, one short group of
definitions at a time, in `forth/010-lib.fth`. The seed reads the library
as written: no assembler or compiler outside the seed runs in this Part.
By the end, the library is large enough to carry an M1 assembler and a
hex2 linker, which turn assembly text into a running executable.

- [Chapter 14](14-lib-01-stacks-and-words.md) introduces stack-effect
  notation and the conventions that open the library.
- [Chapter 15](15-lib-02-code-emission-and-here.md) builds the byte emitter
  on the allocation cursor.
- [Chapters 16](16-lib-03-logic-from-nand.md) and
  [17](17-lib-04-return-stack-over-subtract.md) derive `and`, `or`, `over`
  and subtraction from the seed's few primitives.
- [Chapter 18](18-lib-05-syscalls.md) wraps the Linux calls the later
  layers need: `open`, `read`, `write`, `close` and `die`.
- [Chapters 19](19-lib-06-character-classification.md) and
  [20](20-lib-07-comparisons-from-division.md) build character classes and
  signed comparisons. Neither uses a branch: both come from unsigned
  division.
- [Chapters 21](21-lib-08-stack-shufflers.md) and
  [22](22-lib-09-memory-and-cell-writers.md) add stack shufflers, memory
  updates and little-endian writers.
- [Chapter 23](23-lib-10-immediacy-and-constants.md) separates what runs
  while a word is being defined from what runs when it is called, with
  `immediate` and `constant`.
- [Chapter 24](24-lib-11-control-flow-combinators.md) builds conditionals
  and loops inside colon definitions.
- [Chapter 25](25-lib-12-defining-words-and-bytes-eq.md) completes the
  library with defining words, buffers and byte comparison.
- [Chapter 26](26-m1-and-hex2.md) uses the finished library to assemble and
  link an M1 program that prints `hi` and exits with status 42.

Chapter 14 starts with seed words alone. Later checkpoints load the
needed library prefix before the chapter's own words; Chapter 26 loads
the complete library and assembler. Each exercises only words introduced
so far.
