# Part 2 — Forth

Part 2 grows the seed's vocabulary in Forth source, one short group of
definitions at a time, in `forth/010-lib.fth`. The seed reads the library
as written: no assembler or compiler outside the seed runs in this Part.
By the end, it supplies the memory, control flow and byte-writing words
that the C compiler loads before its own definitions.

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
  signed comparisons. Their range and sign tests use unsigned division
  rather than branches.
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

Chapter 14 starts with seed words alone. Later checkpoints load the
needed library prefix before the chapter's own words; Chapter 25 uses
the completed library. Each exercises only words introduced so far.

The handoff to Part 3 is the library itself. Before proceeding, be able
to trace a definition's stack effect and distinguish a word that emits
an instruction from the instruction that eventually runs. The
`if,`/`then,` pair in Chapter 24 is the key example: emit a branch,
remember its unfinished destination, and patch it when that destination
is known. Continue to [Part 3](part-3-compiler.md), beginning with
[Chapter 27](27-arena-and-io-buffers.md), where the C compiler will reuse
that pattern on a larger scale.
