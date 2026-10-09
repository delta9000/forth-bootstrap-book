# Existing chapter mapping

Every existing top-level book Markdown file except SUMMARY.md has one row. The destination is its planned chapter; chapter 34 is retired from the reading sequence and appears only in the final Retired section of SUMMARY.md, while the LP64 stub mines its storage material. Source spans absent from INVENTORY.md remain explicit TODOs.

| Old file | Old title | New part | New stub | Action |
|---|---|---|---|---|
| [00-prologue.md](../02-prologue.md) | Prologue — Seventeen Hundred and Seventy-Two Bytes | front matter | [Prologue: Seventeen hundred and seventy-two bytes](02-prologue.md) | keep |
| [01-stacks-and-words.md](../01-stacks-and-words.md) | Chapter 1 — Stacks and Words | 2 | [Stacks and words](14-lib-01-stacks-and-words.md) | shorten |
| [02-code-emission-and-here.md](../02-code-emission-and-here.md) | Chapter 2 — Code Emission and the HERE Pointer | 2 | [Code emission and HERE](15-lib-02-code-emission-and-here.md) | shorten |
| [03-logic-from-nand.md](../03-logic-from-nand.md) | Chapter 3 — Logic from One Primitive | 2 | [Logic from NAND](16-lib-03-logic-from-nand.md) | shorten |
| [04-return-stack-over-subtract.md](../04-return-stack-over-subtract.md) | Chapter 4 — The Return Stack: `over` and Subtract | 2 | [The return stack, over, and subtraction](17-lib-04-return-stack-over-subtract.md) | shorten |
| [05-syscalls.md](../05-syscalls.md) | Chapter 5 — Talking to Linux: `syscall6` Wrappers | 2 | [Linux syscall wrappers](18-lib-05-syscalls.md) | shorten |
| [06-character-classification.md](../06-character-classification.md) | Chapter 6 — Character Classification | 2 | [Character classification](19-lib-06-character-classification.md) | shorten |
| [07-comparisons-from-division.md](../07-comparisons-from-division.md) | Chapter 7 — Comparisons from Unsigned Division | 2 | [Comparisons from unsigned division](20-lib-07-comparisons-from-division.md) | shorten |
| [08-stack-shufflers.md](../08-stack-shufflers.md) | Chapter 8 — Stack Shufflers | 2 | [Stack shufflers](21-lib-08-stack-shufflers.md) | shorten |
| [09-memory-and-cell-writers.md](../09-memory-and-cell-writers.md) | Chapter 9 — Memory Updates and Cell Writers | 2 | [Memory updates and cell writers](22-lib-09-memory-and-cell-writers.md) | shorten |
| [10-immediacy-and-constants.md](../10-immediacy-and-constants.md) | Chapter 10 — Immediacy and Constants | 2 | [Immediacy and constants](23-lib-10-immediacy-and-constants.md) | shorten |
| [11-control-flow-combinators.md](../11-control-flow-combinators.md) | Chapter 11 — Control-Flow Combinators (the climax of Part I) | 2 | [Control-flow combinators](24-lib-11-control-flow-combinators.md) | shorten |
| [12-defining-words-and-bytes-eq.md](../12-defining-words-and-bytes-eq.md) | Chapter 12 — `allot`, `create`, `variable`, `bytes-eq` | 2 | [Defining words and byte equality](25-lib-12-defining-words-and-bytes-eq.md) | shorten |
| [13-elf-and-entry.md](../13-elf-and-entry.md) | Chapter 13 — The ELF and the Entry Point | 1 | [ELF, entry, and the memory map](05-elf-and-entry.md) | keep |
| [14-stack-primitives.md](../06-stack-primitives.md) | Chapter 14 — Stack Primitives in Machine Code | 1 | [Stack and memory primitives](06-stack-primitives.md) | keep |
| [15-arithmetic-and-logic.md](../07-arithmetic-and-logic.md) | Chapter 15 — Arithmetic, Logic, Comparison | 1 | [Arithmetic and logic in machine code](07-arithmetic-and-logic.md) | keep |
| [16-io-emit-key-syscall6.md](../08-seed-io.md) | Chapter 16 — I/O: `emit`, `key`, `syscall6` | 1 | [The seed’s Linux boundary](08-seed-io.md) | keep |
| [17-the-dictionary.md](../09-dictionary.md) | Chapter 17 — The Dictionary | 1 | [The dictionary and token reader](09-dictionary.md) | keep |
| [18-the-colon-compiler.md](../10-colon-compiler.md) | Chapter 18 — The Colon Compiler | 1 | [The colon compiler](10-colon-compiler.md) | keep |
| [19-branches-and-inline-cells.md](../11-branches.md) | Chapter 19 — Branches and Inline Cells | 1 | [Branches and inline cells](11-branches.md) | keep |
| [20-number-parser-and-repl.md](../12-repl.md) | Chapter 20 — The Number Parser and REPL | 1 | [Decimal parsing and the REPL](12-repl.md) | keep |
| [21-arena-and-io-buffers.md](../21-arena-and-io-buffers.md) | Chapter 21 — Arena and I/O Buffers | 3 | [Arena and I/O buffers](27-arena-and-io-buffers.md) | keep |
| [22-the-preprocessor.md](../22-the-preprocessor.md) | Chapter 22 — The Preprocessor | 3 | [The preprocessor](28-the-preprocessor.md) | keep |
| [23-the-lexer.md](../23-the-lexer.md) | Chapter 23 — The Lexer | 3 | [The lexer](29-the-lexer.md) | keep |
| [24-types-and-symbols.md](../24-types-and-symbols.md) | Chapter 24 — Types and Symbols | 3 | [Types and symbols](30-types-and-symbols.md) | keep |
| [25-elf-and-codegen-part-1.md](../25-elf-and-codegen-part-1.md) | Chapter 25 — ELF Emission and Codegen, Part 1: Instructions | 3 | [ELF emission and instruction encoding](31-elf-and-codegen-part-1.md) | keep |
| [26-codegen-part-2.md](../26-codegen-part-2.md) | Chapter 26 — Codegen, Part 2: Calls, Shims, and Globals | 3 | [Calls, shims, and globals](32-codegen-part-2.md) | keep |
| [27-expressions-part-1.md](../27-expressions-part-1.md) | Chapter 27 — Expressions, Part 1: The Precedence Cascade | 3 | [Expressions: precedence](33-expressions-part-1.md) | keep |
| [28-expressions-part-2.md](../28-expressions-part-2.md) | Chapter 28 — Expressions, Part 2: Primary, Unary, Assignment | 3 | [Expressions: operands and assignment](34-expressions-part-2.md) | keep |
| [29-declarations-types-globals.md](../29-declarations-types-globals.md) | Chapter 29 — Declarations: Types, Structs, Locals | 3 | [Declarations and storage](35-declarations-types-globals.md) | keep |
| [30-statements-if-while-for-return.md](../30-statements-if-while-for-return.md) | Chapter 30 — Statements: `if`, `while`, `for`, `switch`, `break`, `continue`, `goto` | 3 | [Statements and control flow](36-statements-if-while-for-return.md) | keep |
| [31-functions-and-scope.md](../31-functions-and-scope.md) | Chapter 31 — Functions: Parameters, Calls, Globals, Entry Stub | 3 | [Functions and translation units](37-functions-and-scope.md) | keep |
| [32-main-and-bootstrap-chain.md](../32-main-and-bootstrap-chain.md) | Chapter 32 — End to End: Main and the Bootstrap Chain | 3 | [Compiler entry and Stage A](38-main-and-bootstrap-chain.md) | keep |
| [33-the-assembler.md](../33-the-assembler.md) | Chapter 33 — The Assembler: M1 and hex2 in Forth | 2 | [The M1 assembler and hex2 linker](26-m1-and-hex2.md) | keep |
| [34-direct-tinycc.md](../34-direct-tinycc.md) | Chapter 34 — Compiling TinyCC Directly | 3 | [LP64 storage and initializers](39-lp64-storage-and-initializers.md) | retire |
| [35-direct-gcc-objects.md](../35-direct-gcc-objects.md) | Chapter 35 — Forth-written relocatable objects | 3 | [Objects and relocations](40-objects-and-relocations.md) | regroup |
| [36-direct-gcc-calls.md](../36-direct-gcc-calls.md) | Chapter 36: Scalar calls across the System V boundary | 3 | [System V calls and separate compilation](41-system-v-calls.md) | regroup |
| [37-direct-gcc-linker.md](../37-direct-gcc-linker.md) | Chapter 37 — Linking independent AMD64 objects | 3 | [Linker and archives](42-linker-and-archives.md) | regroup |
| [38-direct-gcc-runtime.md](../38-direct-gcc-runtime.md) | 38. The runtime syscall boundary | 3 | [Runtime, libc, streams, and formatting](43-runtime-and-libc.md) | regroup |
| [39-direct-gcc-libc.md](../39-direct-gcc-libc.md) | 39. A bounded C runtime from source | 3 | [Runtime, libc, streams, and formatting](43-runtime-and-libc.md) | regroup |
| [40-direct-gcc-target.md](../40-direct-gcc-target.md) | 40. Choosing the target header dialect | 3 | [Target headers](44-target-headers.md) | regroup |
| [41-direct-gcc-constants.md](../41-direct-gcc-constants.md) | 41. Typed constants without executing target code | 3 | [Typed constants](45-typed-constants.md) | regroup |
| [42-direct-gcc-varargs.md](../42-direct-gcc-varargs.md) | 42. Variadic lists across the System V boundary | 3 | [System V varargs](46-varargs.md) | regroup |
| [43-direct-gcc-stdio.md](../43-direct-gcc-stdio.md) | 43. Generator streams and integer formatting | 3 | [Runtime, libc, streams, and formatting](43-runtime-and-libc.md) | regroup |
| [44-direct-gcc-archives.md](../44-direct-gcc-archives.md) | Chapter 44 — Indexed archives and lazy member selection | 3 | [Linker and archives](42-linker-and-archives.md) | regroup |
| [45-direct-gcc-binary64.md](../45-direct-gcc-binary64.md) | 45. Binary32 and binary64 scalar values | 3 | [Floating values and exact literals](47-floats.md) | regroup |
| [46-direct-gcc-float-literals.md](../46-direct-gcc-float-literals.md) | Chapter 46 — Exact decimal binary64 literals | 3 | [Floating values and exact literals](47-floats.md) | regroup |
| [47-direct-gcc-bitfields.md](../47-direct-gcc-bitfields.md) | Chapter 47 — Integer record bitfields | 3 | [Record bitfields](48-bitfields.md) | regroup |
| [48-direct-gcc-aggregate-abi.md](../48-direct-gcc-aggregate-abi.md) | 48. Record values at the System V boundary | 3 | [Aggregates and extended floating values](49-aggregate-abi.md) | regroup |
| [49-direct-gcc-cc1.md](../49-direct-gcc-cc1.md) | Chapter 49 — Building GCC's compiler proper | 4 | [GCC 4.0.4: stages C and D](52-gcc-4-fixed-point.md) | keep |
| [A1-32-seed-primitives.md](../A1-32-seed-primitives.md) | Appendix A — The 32 seed primitives | 1 | [The 32 seed primitives: reference](13-primitive-reference.md) | keep |
| [A2-memory-map.md](../A2-memory-map.md) | Appendix B — The memory map | 1 | [ELF, entry, and the memory map](05-elf-and-entry.md) | keep |
| [A3-reproducibility-chain.md](../A3-reproducibility-chain.md) | Appendix C — Reproducibility: the full hex0 → seed → M2-Planet chain | back matter | [Appendix C: historical reproducibility routes](57-historical-reproducibility.md) | shorten |
| [A4-worked-exercises.md](../A4-worked-exercises.md) | Appendix D — Three worked exercises, one each from Parts I–III | back matter | [Appendix D: worked exercises](58-worked-exercises.md) | keep |
| [A5-further-reading.md](../A5-further-reading.md) | Appendix E — Further reading | back matter | [Appendix E: further reading](59-further-reading.md) | keep |
| [A6-c-subset.md](../A6-c-subset.md) | Appendix F — The C subset | back matter | [Appendix F: the C subset](60-c-subset.md) | keep |
| [A7-error-codes.md](../A7-error-codes.md) | Appendix G — Compiler error codes | back matter | [Appendix G: compiler exit codes](61-error-codes.md) | keep |
| [CONCEPTS.md](../CONCEPTS.md) | Concept index, rung map, and dependency graph | back matter | [Concept index and dependencies](63-concepts.md) | regroup |
| [GLOSSARY.md](../GLOSSARY.md) | Glossary | back matter | [Glossary](62-glossary.md) | keep |
| [LEARNING_STORY_PLAN.md](../LEARNING_STORY_PLAN.md) | Learning Story Plan — third version (post-rollout) | back matter | [Editorial notes](65-editorial-notes.md) | regroup |
| [README.md](../01-reading-the-book.md) | Forth From a 1772-Byte Seed | front matter | [Reading the book](01-reading-the-book.md) | keep |
| [WORD-INDEX.md](../WORD-INDEX.md) | Index | back matter | [Word index](64-word-index.md) | keep |
| [WRITING.md](../WRITING.md) | How to write a chapter | back matter | [Editorial notes](65-editorial-notes.md) | regroup |
| [where-this-fits.md](../03-where-this-fits.md) | Where this fits in the bootstrap ecosystem | front matter | [Where this fits: routes and history](03-where-this-fits.md) | shorten |
