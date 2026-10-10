# Summary

# Front matter

- [Reading the book](01-reading-the-book.md)
- [Prologue: Seventeen hundred and seventy-two bytes](02-prologue.md)
- [Where this fits: routes and history](03-where-this-fits.md)

# Part 1 — asm

- [Part 1 — asm](part-1-asm.md)
- [x86-64 encoding and the two-stack machine](04-x86-64-and-two-stacks.md)
- [ELF, entry, and the memory map](05-elf-and-entry.md)
- [Stack and memory primitives](06-stack-primitives.md)
- [Arithmetic and logic in machine code](07-arithmetic-and-logic.md)
- [The seed’s Linux boundary](08-seed-io.md)
- [The dictionary and token reader](09-dictionary.md)
- [The colon compiler](10-colon-compiler.md)
- [Branches and inline cells](11-branches.md)
- [Decimal parsing and the REPL](12-repl.md)
- [The 32 seed primitives: reference](13-primitive-reference.md)

# Part 2 — Forth

- [Part 2 — Forth](part-2-forth.md)
- [Stacks and words](14-lib-01-stacks-and-words.md)
- [Code emission and HERE](15-lib-02-code-emission-and-here.md)
- [Logic from NAND](16-lib-03-logic-from-nand.md)
- [The return stack, over, and subtraction](17-lib-04-return-stack-over-subtract.md)
- [Linux syscall wrappers](18-lib-05-syscalls.md)
- [Character classification](19-lib-06-character-classification.md)
- [Comparisons from unsigned division](20-lib-07-comparisons-from-division.md)
- [Stack shufflers](21-lib-08-stack-shufflers.md)
- [Memory updates and cell writers](22-lib-09-memory-and-cell-writers.md)
- [Immediacy and constants](23-lib-10-immediacy-and-constants.md)
- [Control-flow combinators](24-lib-11-control-flow-combinators.md)
- [Defining words and byte equality](25-lib-12-defining-words-and-bytes-eq.md)
- [The M1 assembler and hex2 linker](26-m1-and-hex2.md)

# Part 3 — compiler

- [Part 3 — compiler](part-3-compiler.md)
- [Arena and I/O buffers](27-arena-and-io-buffers.md)
- [The preprocessor](28-the-preprocessor.md)
- [The lexer](29-the-lexer.md)
- [Types and symbols](30-types-and-symbols.md)
- [ELF emission and instruction encoding](31-elf-and-codegen-part-1.md)
- [Calls, shims, and globals](32-codegen-part-2.md)
- [Expressions: precedence](33-expressions-part-1.md)
- [Expressions: operands and assignment](34-expressions-part-2.md)
- [Declarations and storage](35-declarations-types-globals.md)
- [Statements and control flow](36-statements-if-while-for-return.md)
- [Functions and translation units](37-functions-and-scope.md)
- [Compiler entry and Stage A](38-main-and-bootstrap-chain.md)
- [LP64 storage and initializers](39-lp64-storage-and-initializers.md)
- [Objects and relocations](40-objects-and-relocations.md)
- [System V calls and separate compilation](41-system-v-calls.md)
- [Linker and archives](42-linker-and-archives.md)
- [Runtime, libc, streams, and formatting](43-runtime-and-libc.md)
- [Target headers](44-target-headers.md)
- [Typed constants](45-typed-constants.md)
- [System V varargs](46-varargs.md)
- [Floating values and exact literals](47-floats.md)
- [Record bitfields](48-bitfields.md)
- [Aggregates and extended floating values](49-aggregate-abi.md)

# Part 4 — bootstrap

- [Part 4 — bootstrap](part-4-bootstrap.md)
- [Building seed-cc and seed-ar](50-seed-cc-fixed-point.md)
- [Owning the tools](51-owning-the-tools.md)
- [GCC 4.0.4: stages C and D](52-gcc-4-fixed-point.md)
- [The sealed host run](53-sealed-run.md)
- [K0 and K1](54-k0-and-k1.md)
- [Linux 7.2.8 and kexec under QEMU](55-linux-and-kexec.md)
- [Epilogue: onward to GCC 15.2](56-gcc-15-epilogue.md)

# Back matter

- [Appendix C: historical reproducibility routes](57-historical-reproducibility.md)
- [Appendix D: worked exercises](58-worked-exercises.md)
- [Appendix E: further reading](outline/59-further-reading.md)
  - [Appendix E — Further reading](A5-further-reading.md)
- [Appendix F: the C subset](outline/60-c-subset.md)
  - [Appendix F — The C subset](A6-c-subset.md)
- [Appendix G: compiler exit codes](outline/61-error-codes.md)
  - [Appendix G — Compiler error codes](A7-error-codes.md)
- [Glossary](outline/62-glossary.md)
  - [Glossary](GLOSSARY.md)
- [Concept index and dependencies](outline/63-concepts.md)
  - [Concept index, rung map, and dependency graph](CONCEPTS.md)
- [Word index](outline/64-word-index.md)
  - [Index](WORD-INDEX.md)
- [Editorial notes](outline/65-editorial-notes.md)
  - [How to write a chapter](WRITING.md)
  - [Learning Story Plan — third version (post-rollout)](LEARNING_STORY_PLAN.md)

# Retired

- [Chapter 34 — Compiling TinyCC Directly](34-direct-tinycc.md)
