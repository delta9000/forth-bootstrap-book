# Inventory of the current book

Generated from book/*.md and the forth-bootstrap submodule: every chapter, its length, and the source lines its `file=` blocks teach.

| chapter file | title | lines | file= spans (source lines in root blocks; chunk-assembled files are listed under "Chunks by chapter") |
|---|---|---|---|
| 00-prologue.md | Prologue: Seventeen hundred and seventy-two bytes | 134 |  |
| 01-stacks-and-words.md | Stacks and words | 425 | forth/010-lib.fth 1-10 |
| 02-code-emission-and-here.md | Code emission and the HERE pointer | 228 | forth/010-lib.fth 11-24 |
| 03-logic-from-nand.md | Logic from one primitive | 312 | forth/010-lib.fth 25-33 |
| 04-return-stack-over-subtract.md | The return stack: `over` and subtract | 280 | forth/010-lib.fth 34-46 |
| 05-syscalls.md | Talking to Linux: syscall6 wrappers | 286 | forth/010-lib.fth 47-70 |
| 06-character-classification.md | Character classification | 283 | forth/010-lib.fth 71-96 |
| 07-comparisons-from-division.md | Comparisons from unsigned division | 337 | forth/010-lib.fth 97-138 |
| 08-stack-shufflers.md | Stack shufflers | 194 | forth/010-lib.fth 139-154 |
| 09-memory-and-cell-writers.md | Memory updates and cell writers | 293 | forth/010-lib.fth 155-179 |
| 10-immediacy-and-constants.md | Immediacy and constants | 451 | forth/010-lib.fth 180-264 |
| 11-control-flow-combinators.md | Control-flow combinators | 593 | forth/010-lib.fth 265-373 |
| 12-defining-words-and-bytes-eq.md | `allot`, `create`, `variable`, `bytes-eq` | 488 | forth/010-lib.fth 374-469 |
| 13-elf-and-entry.md | The ELF and the entry point | 464 | seed/000-seed.hex0 1-44 |
| 14-stack-primitives.md | Stack primitives in machine code | 464 |  |
| 15-arithmetic-and-logic.md | Arithmetic, logic, comparison | 305 |  |
| 16-io-emit-key-syscall6.md | I/O: `emit`, `key`, `syscall6` | 302 |  |
| 17-the-dictionary.md | The dictionary | 700 |  |
| 18-the-colon-compiler.md | The colon compiler | 451 |  |
| 19-branches-and-inline-cells.md | Branches and inline cells | 343 |  |
| 20-number-parser-and-repl.md | The number parser and REPL | 484 |  |
| 21-arena-and-io-buffers.md | Arena and I/O buffers | 1316 | cc/020-cc-arena.fth 1-457; cc/030-cc-io.fth 1-287 |
| 22-the-preprocessor.md | The preprocessor | 3303 | cc/040-cc-prep.fth 1-2339 |
| 23-the-lexer.md | The lexer | 1066 | cc/050-cc-lex.fth 1-691 |
| 24-types-and-symbols.md | Types and symbols | 1000 | cc/060-cc-types.fth 1-340; cc/070-cc-sym.fth 1-204 |
| 25-elf-and-codegen-part-1.md | ELF emission and codegen, part 1 | 966 | cc/080-cc-elf.fth 1-80; cc/090-cc-emit.fth 1-445 |
| 26-codegen-part-2.md | Codegen, part 2: calls, shims, and globals | 1439 | cc/090-cc-emit.fth 446-1384 |
| 27-expressions-part-1.md | Expressions, part 1: the precedence cascade | 1080 | cc/100-cc-expr.fth 1-20 |
| 28-expressions-part-2.md | Expressions, part 2: primary, unary, assignment | 2484 |  |
| 29-declarations-types-globals.md | Declarations: types, structs, locals | 1217 | cc/110-cc-decl.fth 1-808 |
| 30-statements-if-while-for-return.md | Statements: if, while, for, switch, break, continue, goto | 1351 | cc/112-cc-stmt.fth 1-905 |
| 31-functions-and-scope.md | Functions: parameters, calls, globals, entry stub | 1939 | cc/114-cc-func.fth 1-310; cc/116-cc-prog.fth 1-884 |
| 32-main-and-bootstrap-chain.md | End to end: main and the bootstrap chain | 535 | cc/120-cc-main.fth 1-40 |
| 33-the-assembler.md | The assembler: M1 and hex2 in Forth | 1644 | forth/130-asm.fth 1-785 |
| 34-direct-tinycc.md | Compiling TinyCC directly | 1526 | cc/115-cc-native.fth 1-647; cc/117-cc-native-program.fth 1-100; cc/118-cc-native-init.fth 1-321; cc/119-cc-native-runtime.fth 1-111 |
| 35-direct-gcc-objects.md | Relocatable objects | 723 | cc/081-cc-object.fth 1-507 |
| 36-direct-gcc-calls.md | System V calls | 2491 | cc/121-cc-sysv.fth 1-1359; cc/123-cc-object-program.fth 1-483 |
| 37-direct-gcc-linker.md | The Forth ELF linker | 782 | cc/140-cc-link.fth 1-613 |
| 38-direct-gcc-runtime.md | The runtime syscall boundary | 302 | cc/122-cc-sysv-runtime.fth 1-187 |
| 39-direct-gcc-libc.md | A bounded C runtime | 224 |  |
| 40-direct-gcc-target.md | The target header dialect | 94 | cc/124-cc-target.fth 1-21 |
| 41-direct-gcc-constants.md | Typed constants | 877 | cc/125-cc-consteval.fth 1-610 |
| 42-direct-gcc-varargs.md | System V variadic lists | 491 | cc/126-cc-varargs.fth 1-234 |
| 43-direct-gcc-stdio.md | Streams and formatting | 216 |  |
| 44-direct-gcc-archives.md | Indexed archives | 541 | cc/141-archive.fth 1-413 |
| 45-direct-gcc-binary64.md | Binary64 values | 472 | cc/127-cc-binary64.fth 1-291 |
| 46-direct-gcc-float-literals.md | Exact floating literals | 761 | cc/128-cc-float-literal.fth 1-575 |
| 47-direct-gcc-bitfields.md | Record bitfields | 379 | cc/129-cc-bitfield.fth 1-193 |
| 48-direct-gcc-aggregate-abi.md | 48. Record values at the System V boundary | 1116 | cc/131-cc-aggregate-abi.fth 1-544; cc/132-cc-long-double.fth 1-239 |
| 49-direct-gcc-cc1.md | Building GCC’s compiler proper | 273 |  |
| A1-32-seed-primitives.md | A — The 32 seed primitives | 130 |  |
| A2-memory-map.md | B — The memory map | 239 |  |
| A3-reproducibility-chain.md | C — Reproducibility: the full hex0 → seed → M2-Planet chain | 447 |  |
| A4-worked-exercises.md | D — Three worked exercises, one each from Parts I–III | 299 |  |
| A5-further-reading.md | E — Further reading | 177 |  |
| A6-c-subset.md | F — The C subset | 310 |  |
| A7-error-codes.md | G — Compiler exit codes | 399 |  |
| CONCEPTS.md | Concept index and dependency graph | 380 |  |
| GLOSSARY.md | Glossary | 426 |  |
| LEARNING_STORY_PLAN.md |  | 221 |  |
| README.md | Seed Forth | 178 |  |
| SUMMARY.md |  | 88 |  |
| WORD-INDEX.md | Index | 3106 |  |
| WRITING.md |  | 265 |  |
| where-this-fits.md | Where this fits in the bootstrap ecosystem | 486 |  |

Source sizes (forth-bootstrap):
- cc/020-cc-arena.fth: 457 lines, all covered by fences: True
- cc/030-cc-io.fth: 287 lines, all covered by fences: True
- cc/040-cc-prep.fth: 2339 lines, all covered by fences: True
- cc/050-cc-lex.fth: 691 lines, all covered by fences: True
- cc/060-cc-types.fth: 340 lines, all covered by fences: True
- cc/070-cc-sym.fth: 204 lines, all covered by fences: True
- cc/080-cc-elf.fth: 80 lines, all covered by fences: True
- cc/081-cc-object.fth: 507 lines, all covered by fences: True
- cc/090-cc-emit.fth: 1384 lines, all covered by fences: True
- cc/100-cc-expr.fth: 2657 lines, assembled from chunks (below); tangle --strict proves it complete
- cc/110-cc-decl.fth: 808 lines, all covered by fences: True
- cc/112-cc-stmt.fth: 905 lines, all covered by fences: True
- cc/114-cc-func.fth: 310 lines, all covered by fences: True
- cc/115-cc-native.fth: 647 lines, all covered by fences: True
- cc/116-cc-prog.fth: 884 lines, all covered by fences: True
- cc/117-cc-native-program.fth: 100 lines, all covered by fences: True
- cc/118-cc-native-init.fth: 321 lines, all covered by fences: True
- cc/119-cc-native-runtime.fth: 111 lines, all covered by fences: True
- cc/120-cc-main.fth: 40 lines, all covered by fences: True
- cc/121-cc-sysv.fth: 1359 lines, all covered by fences: True
- cc/122-cc-sysv-runtime.fth: 187 lines, all covered by fences: True
- cc/123-cc-object-program.fth: 483 lines, all covered by fences: True
- cc/124-cc-target.fth: 21 lines, all covered by fences: True
- cc/125-cc-consteval.fth: 610 lines, all covered by fences: True
- cc/126-cc-varargs.fth: 234 lines, all covered by fences: True
- cc/127-cc-binary64.fth: 291 lines, all covered by fences: True
- cc/128-cc-float-literal.fth: 575 lines, all covered by fences: True
- cc/129-cc-bitfield.fth: 193 lines, all covered by fences: True
- cc/131-cc-aggregate-abi.fth: 544 lines, all covered by fences: True
- cc/132-cc-long-double.fth: 239 lines, all covered by fences: True
- cc/140-cc-link.fth: 613 lines, all covered by fences: True
- cc/141-archive.fth: 413 lines, all covered by fences: True
- forth/010-lib.fth: 469 lines, all covered by fences: True
- forth/130-asm.fth: 785 lines, all covered by fences: True
- seed/000-seed.hex0: 689 lines, assembled from chunks (below); tangle --strict proves it complete

## Chunks by chapter

Two files are assembled from `<<chunk>>` references rather than read straight through: `seed/000-seed.hex0` (root block in 13-elf-and-entry.md) and `cc/100-cc-expr.fth` (root block in 27-expressions-part-1.md).  For each chapter, the chunks it defines, by source file, in definition order:

- 13-elf-and-entry.md: seed/000-seed.hex0: file-header-comment, elf-header, program-header, entry-point, sysvar-init, jmp-to-repl
- 14-stack-primitives.md: seed/000-seed.hex0: dup, drop, swap, to-r, r-from, r-at, fetch, store, cfetch, cstore
- 15-arithmetic-and-logic.md: seed/000-seed.hex0: plus, nand, zeq, divide, star
- 16-io-emit-key-syscall6.md: seed/000-seed.hex0: bye, emit, key, syscall6
- 17-the-dictionary.md: seed/000-seed.hex0: find, here, comma, execute, read-word, read-char, report-token, state, latest, tick
- 18-the-colon-compiler.md: seed/000-seed.hex0: colon, semicolon, compile-call, lit, bracket-lit
- 19-branches-and-inline-cells.md: seed/000-seed.hex0: branch, zbranch
- 20-number-parser-and-repl.md: seed/000-seed.hex0: parse-decimal, repl
- 27-expressions-part-1.md: cc/100-cc-expr.fth: expr-header, expr-tok-tests, expr-fwd-refs, expr-binops, expr-mul, expr-add, expr-shift, expr-rel, expr-eq, expr-bit, expr-log
- 28-expressions-part-2.md: cc/100-cc-expr.fth: expr-lvalue, expr-struct-field, expr-array-index, expr-primary, expr-primary-postfix, expr-primary-operand, expr-primary-literals, expr-primary-ident, expr-primary-fn-rvalue, expr-primary-global, expr-primary-local, expr-primary-paren, expr-primary-postfix-incdec, expr-primary-postfix-index, expr-primary-postfix-field, expr-unary, expr-ternary, expr-assign, expr-top
- 31-functions-and-scope.md: cc/100-cc-expr.fth: expr-call
