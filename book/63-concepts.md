# Concept index and dependencies

Find a topic below, then follow its link to the source walkthrough. The
[capability checks](#capability-checks-at-the-transitions) help you choose
what to recover when entering a new part. The dependency table records
the outline's chapter order; it does not measure what you can already do.
Definitions are in the [Glossary](62-glossary.md), and individual words are
in the [word index](WORD-INDEX.md).

## Focused reading routes

Start with [Chapter 1](01-reading-the-book.md) to establish the source
checkout and run your first word. For the full construction, continue in
sidebar order. For a specific question, use one of these routes.

Choose a route according to the question you brought:

- **Understand the whole construction.** Read in sidebar order. At each
  part boundary, use its map to name the artifact you have gained and
  the next thing it must build.
- **See a compiler work, then open it up.** Establish the [Chapter 1 setup](01-reading-the-book.md#try-it-establish-the-setup),
  read the [Forth notation](14-lib-01-stacks-and-words.md), then follow
  the [expression checkpoint](34-expressions-part-2.md#try-it) and the
  first [compiler-entry checkpoint](38-main-and-bootstrap-chain.md#try-it).
  Return to Chapters 27–37 to explain each layer those commands load.
- **Audit the bootstrap claim.** Read Chapters 2–3, the
  [Stage A comparison](38-main-and-bootstrap-chain.md#stage-a-the-parity-proof),
  and Chapters 50–55. Track who builds each artifact, what gets compared,
  and which host or guest runs it. The long runs have their own resource
  requirements; reading their evidence does not require launching them.

Part 3's [C-reading bridge](part-3-compiler.md#reading-the-c-input)
introduces the pointer, array, and record notation used by the compiler's
inputs. No prior course in C implementation or calling conventions is
needed. The capability checks below help you recover earlier mechanisms
when returning after a break.

## Topic → chapter quick reference

### Part 1: Machine and seed

- Allocation cursor — [Chapter 9](09-dictionary.md)
- Binary reduction pattern — [Chapter 7](07-arithmetic-and-logic.md)
- Cached-top pattern — [Chapter 4](04-x86-64-and-two-stacks.md)
- Canonical flag — [Chapter 7](07-arithmetic-and-logic.md)
- Cell — [Chapter 4](04-x86-64-and-two-stacks.md)
- Colon definition — [Chapter 10](10-colon-compiler.md)
- Compilation state — [Chapter 10](10-colon-compiler.md)
- Compile mode — [Chapter 10](10-colon-compiler.md)
- Consumed-slot property — [Chapter 11](11-branches.md)
- Data stack — [Chapter 4](04-x86-64-and-two-stacks.md)
- Decimal accumulation — [Chapter 12](12-repl.md)
- Dictionary — [Chapter 9](09-dictionary.md)
- Dictionary header — [Chapter 9](09-dictionary.md)
- ELF header — [Chapter 5](05-elf-and-entry.md)
- Endianness — See Little-endian. [Chapter 4](04-x86-64-and-two-stacks.md)
- Execution token (xt) — [Chapter 9](09-dictionary.md#the-header-layout)
- Fixed-base contract — [Chapter 5](05-elf-and-entry.md)
- Forth boolean — See Canonical flag. [Chapter 7](07-arithmetic-and-logic.md)
- hex0 — [Chapter 5](05-elf-and-entry.md)
- I/O scratch byte — [Chapter 8](08-seed-io.md)
- Immediate operand — [Chapter 4](04-x86-64-and-two-stacks.md)
- Immediate word — [Chapter 10](10-colon-compiler.md)
- Inherited executable — [Chapter 3](03-where-this-fits.md)
- Inherited source — [Chapter 3](03-where-this-fits.md)
- Inline-cell convention — [Chapter 10](10-colon-compiler.md)
- Interpret mode — [Chapter 10](10-colon-compiler.md)
- Linux syscall register convention — [Chapter 8](08-seed-io.md#the-linux-register-boundary)
- Little-endian — [Chapter 4](04-x86-64-and-two-stacks.md)
- Loadable segment — [Chapter 5](05-elf-and-entry.md)
- ModR/M — See ModRM. [Chapter 4](04-x86-64-and-two-stacks.md)
- ModRM — [Chapter 4](04-x86-64-and-two-stacks.md)
- Newest-first lookup — [Chapter 9](09-dictionary.md)
- Prepare–call–recover — [Chapter 8](08-seed-io.md)
- Primitive — [Chapter 6](06-stack-primitives.md)
- rel32 — [Chapter 4](04-x86-64-and-two-stacks.md)
- REPL dispatch — [Chapter 12](12-repl.md)
- Return stack — [Chapter 4](04-x86-64-and-two-stacks.md#the-machine-before-the-instructions)
- Return-address shelter — [Chapter 6](06-stack-primitives.md)
- REX — [Chapter 4](04-x86-64-and-two-stacks.md)
- Second on stack — [Chapter 4](04-x86-64-and-two-stacks.md)
- Signed displacement decoding — [Chapter 4](04-x86-64-and-two-stacks.md#reading-a-negative-displacement)
- Seed memory map — [Chapter 5](05-elf-and-entry.md)
- SIB — [Chapter 4](04-x86-64-and-two-stacks.md)
- stage0-posix — [Chapter 3](03-where-this-fits.md)
- Subroutine threading — [Chapter 10](10-colon-compiler.md)
- System-variable cells — [Chapter 5](05-elf-and-entry.md)
- Sysvar — See System-variable cells. [Chapter 5](05-elf-and-entry.md)
- Token buffer — [Chapter 9](09-dictionary.md)
- Top of stack — [Chapter 4](04-x86-64-and-two-stacks.md)
- TOS — See Top of stack. [Chapter 4](04-x86-64-and-two-stacks.md)
- Under-TOS — See Second on stack. [Chapter 4](04-x86-64-and-two-stacks.md)
- xt — See Execution token (xt). [Chapter 9](09-dictionary.md)

### Part 2: Forth library and assembler

- Back-patching — See Emit, remember, patch. [Chapter 24](24-lib-11-control-flow-combinators.md)
- Backward loops — [Chapter 24](24-lib-11-control-flow-combinators.md#backward-loops-begin--while--repeat)
- Canonicalisation — [Chapter 20](20-lib-07-comparisons-from-division.md)
- Chained fixups — [Chapter 24](24-lib-11-control-flow-combinators.md)
- Comparison cascade — [Chapter 20](20-lib-07-comparisons-from-division.md)
- Counted name — [Chapter 9](09-dictionary.md)
- De Morgan's law — [Chapter 16](16-lib-03-logic-from-nand.md#or-in-six-words)
- Deferred words — [Chapter 25](25-lib-12-defining-words-and-bytes-eq.md#defer-and-is-a-name-now-a-meaning-later)
- Division as a right shift — [Chapter 22](22-lib-09-memory-and-cell-writers.md#why-divide-by-256)
- Early return — [Chapter 24](24-lib-11-control-flow-combinators.md)
- Emit versus execute — [Chapter 23](23-lib-10-immediacy-and-constants.md)
- Emit, remember, patch — [Chapter 24](24-lib-11-control-flow-combinators.md#forward-branches-if-and-then-as-a-pair)
- Emit-and-divide — [Chapter 22](22-lib-09-memory-and-cell-writers.md)
- Fixup on the stack — [Chapter 24](24-lib-11-control-flow-combinators.md#forward-branches-if-and-then-as-a-pair)
- Functional completeness of NAND — [Chapter 16](16-lib-03-logic-from-nand.md#why-logic-from-nand-matters)
- hex2 — [Chapter 26](26-m1-and-hex2.md)
- Label table — [Chapter 26](26-m1-and-hex2.md)
- Little-endian cell writers — [Chapter 22](22-lib-09-memory-and-cell-writers.md#4-and-8-cell-sized-emission)
- M1 — [Chapter 26](26-m1-and-hex2.md)
- M1 macro — [Chapter 26](26-m1-and-hex2.md)
- Pad-and-call — [Chapter 18](18-lib-05-syscalls.md)
- Postfix evaluation — [Chapter 14](14-lib-01-stacks-and-words.md#postfix-evaluation)
- Range-check trick — [Chapter 19](19-lib-06-character-classification.md#the-range-check-trick-digit)
- Reverse Polish notation — See Postfix evaluation. [Chapter 14](14-lib-01-stacks-and-words.md#postfix-evaluation)
- RPN — See Postfix evaluation. [Chapter 14](14-lib-01-stacks-and-words.md)
- Runtime body — [Chapter 23](23-lib-10-immediacy-and-constants.md)
- Self-NAND — [Chapter 16](16-lib-03-logic-from-nand.md)
- Sigil — [Chapter 26](26-m1-and-hex2.md)
- Sign test by division — [Chapter 20](20-lib-07-comparisons-from-division.md)
- Signed-overflow domain — [Chapter 20](20-lib-07-comparisons-from-division.md)
- Stack trace — [Chapter 14](14-lib-01-stacks-and-words.md)
- Stack-effect notation — [Chapter 14](14-lib-01-stacks-and-words.md#stack-effect-comments)
- Store-and-advance — [Chapter 15](15-lib-02-code-emission-and-here.md)
- Two's complement — [Chapter 4: decode signed fields](04-x86-64-and-two-stacks.md#reading-a-negative-displacement); [Chapter 17: derive negation](17-lib-04-return-stack-over-subtract.md#--from--and-nand)
- Two-pass assembly — [Chapter 26](26-m1-and-hex2.md)
- Word — [Chapter 14](14-lib-01-stacks-and-words.md)

### Part 3: Compiler

- C declaration reading — [Part 3 bridge](part-3-compiler.md#reading-the-c-input)
- ABI — See System V AMD64 calling convention. [Chapter 41](41-system-v-calls.md)
- Aggregate classification — [Chapter 49](49-aggregate-abi.md)
- Aligned outgoing argument block — [Chapter 41](41-system-v-calls.md)
- Allocation metadata — [Chapter 43](43-runtime-and-libc.md)
- Arena — [Chapter 27](27-arena-and-io-buffers.md)
- Array node — [Chapter 30](30-types-and-symbols.md)
- Array-based va_list — [Chapter 46](46-varargs.md)
- Assignment — [Chapter 34](34-expressions-part-2.md)
- Atomic object publication — [Chapter 40](40-objects-and-relocations.md)
- Binary fold — [Chapter 33](33-expressions-part-1.md)
- Bitfield slice — [Chapter 48](48-bitfields.md)
- Bootstrap chain — [Chapter 38](38-main-and-bootstrap-chain.md#the-wider-chain)
- Bounded formatting count — [Chapter 43](43-runtime-and-libc.md)
- Break/continue fixup lists — [Chapter 36](36-statements-if-while-for-return.md#breakcontinue-fixup-lists)
- Buffered key handoff — [Chapter 27](27-arena-and-io-buffers.md)
- Bump allocator — See Arena. [Chapter 27](27-arena-and-io-buffers.md)
- Call transport plan — [Chapter 49](49-aggregate-abi.md)
- Checked constant arithmetic — [Chapter 45](45-typed-constants.md)
- Checked relocation assignment — [Chapter 42](42-linker-and-archives.md)
- Code generation — [Chapter 31](31-elf-and-codegen-part-1.md)
- Codegen — See Code generation. [Chapter 31](31-elf-and-codegen-part-1.md)
- Compact type encoding — [Chapter 30](30-types-and-symbols.md)
- Compiler diagnostic — [Chapter 27](27-arena-and-io-buffers.md)
- Computed include operand — [Chapter 28](28-the-preprocessor.md)
- Conditional compilation — [Chapter 28](28-the-preprocessor.md)
- Constant expressions — [Chapter 34](34-expressions-part-2.md#constant-expressions)
- Constant pool watermark — [Chapter 45](45-typed-constants.md)
- Declarator-local pointer depth — [Chapter 35](35-declarations-types-globals.md)
- Dictionary hash index — [Chapter 27](27-arena-and-io-buffers.md)
- Direct destination rounding — [Chapter 47](47-floats.md)
- ELF wrapper — [Chapter 31](31-elf-and-codegen-part-1.md)
- Entry stub — [Chapter 37](37-functions-and-scope.md#the-entry-stub-and-the-top-level-driver)
- Evaluation stack — [Chapter 33](33-expressions-part-1.md)
- Exact floating ratio — [Chapter 47](47-floats.md)
- Explicit relocation addend — [Chapter 40](40-objects-and-relocations.md)
- Expression accumulator — [Chapter 31](31-elf-and-codegen-part-1.md)
- Extended floating value — [Chapter 49](49-aggregate-abi.md)
- Fail-closed bootstrap runtime — [Chapter 39](39-lp64-storage-and-initializers.md#a-finite-linux-boundary)
- Failure-preserving realloc — [Chapter 43](43-runtime-and-libc.md)
- Floating payload transport — [Chapter 47](47-floats.md)
- Floating representation — [Chapter 47](47-floats.md)
- for-step rewind — [Chapter 36](36-statements-if-while-for-return.md#for-with-step-rewind)
- Forward-call fixup list — [Chapter 32](32-codegen-part-2.md#movabs-rdi-imm64-and-the-forward-call-fixup-list)
- Frame pointer — [Chapter 31](31-elf-and-codegen-part-1.md)
- Frameless adapter — [Chapter 43](43-runtime-and-libc.md)
- Full-width immediate placeholder — [Chapter 32](32-codegen-part-2.md)
- Function frame — [Chapter 37](37-functions-and-scope.md)
- Function pre-registration — [Chapter 37](37-functions-and-scope.md)
- Global definition selection — [Chapter 42](42-linker-and-archives.md)
- Global redeclaration reuse — [Chapter 37](37-functions-and-scope.md)
- Global-address fixups — [Chapter 32](32-codegen-part-2.md#file-scope-globals-and-deferred-vaddr-fixups)
- Grammar notation — [Chapter 33](33-expressions-part-1.md#the-shape-of-the-cascade)
- GNU archive index — [Chapter 42](42-linker-and-archives.md)
- Include pool — [Chapter 28](28-the-preprocessor.md)
- Independent argument cursors — [Chapter 46](46-varargs.md)
- Inline allocator state — [Chapter 32](32-codegen-part-2.md)
- Inline/fallback compilation — [Chapter 27](27-arena-and-io-buffers.md)
- Input identity protection — [Chapter 42](42-linker-and-archives.md)
- Integer literal classification — [Chapter 30](30-types-and-symbols.md)
- Labels and goto — [Chapter 36](36-statements-if-while-for-return.md#labels-and-goto)
- Late shim selection — [Chapter 37](37-functions-and-scope.md)
- Lazy member selection — [Chapter 42](42-linker-and-archives.md)
- Left associativity — [Chapter 33](33-expressions-part-1.md#cc-parse-add-just-like-mul-looser)
- Lexer — [Chapter 29](29-the-lexer.md)
- Lexer state block — [Chapter 27](27-arena-and-io-buffers.md#the-lexers-state-block)
- libc shims — [Chapter 32](32-codegen-part-2.md#the-libc-shims-writereadopenclosemmap)
- Local-first symbol numbering — [Chapter 40](40-objects-and-relocations.md)
- Logical source location — [Chapter 28](28-the-preprocessor.md)
- LP64 native object storage — [Chapter 39](39-lp64-storage-and-initializers.md#native-declarations-and-aligned-storage)
- Lvalue — [Chapter 34](34-expressions-part-2.md)
- Lvalue tracking — [Chapter 34](34-expressions-part-2.md#lvalue-tracking)
- M2-Planet — [Chapter 38](38-main-and-bootstrap-chain.md)
- Macro expansion — [Chapter 28](28-the-preprocessor.md#macro-expansion)
- Macro table — [Chapter 28](28-the-preprocessor.md)
- Monolith — [Chapter 38](38-main-and-bootstrap-chain.md)
- Native redirection — [Chapter 27](27-arena-and-io-buffers.md)
- Nonlocal continuation — [Chapter 43](43-runtime-and-libc.md)
- Numeric token spelling — [Chapter 29](29-the-lexer.md)
- One buffer per responsibility — [Chapter 27](27-arena-and-io-buffers.md)
- Operand snapshot — [Chapter 33](33-expressions-part-1.md)
- Operator table — [Chapter 33](33-expressions-part-1.md#the-operator-table)
- Output back-patching — [Chapter 27](27-arena-and-io-buffers.md)
- Owed newlines — [Chapter 28](28-the-preprocessor.md)
- Parser — [Chapter 33](33-expressions-part-1.md)
- Per-object placement — [Chapter 42](42-linker-and-archives.md)
- Per-operator normalization — [Chapter 45](45-typed-constants.md)
- Persistent call-save span — [Chapter 41](41-system-v-calls.md)
- Postfix operators — [Chapter 34](34-expressions-part-2.md#the-postfix-operators)
- Precedence cascade — [Chapter 33](33-expressions-part-1.md#the-level-template-cc-parse-mul)
- Preprocessor — [Chapter 28](28-the-preprocessor.md)
- Preserving store — [Chapter 48](48-bitfields.md)
- Private all-stack ABI — [Chapter 39](39-lp64-storage-and-initializers.md#private-stack-calls-and-whole-programs)
- Prologue and epilogue — [Chapter 31](31-elf-and-codegen-part-1.md)
- Prototype reuse — [Chapter 37](37-functions-and-scope.md)
- Ranked array descriptor — [Chapter 41](41-system-v-calls.md)
- Raw syscall result — [Chapter 43](43-runtime-and-libc.md)
- rel32 placeholder and patch — [Chapter 31](31-elf-and-codegen-part-1.md)
- Remainder-based rounding — [Chapter 47](47-floats.md)
- Runtime-aware entry — [Chapter 43](43-runtime-and-libc.md)
- Rvalue — [Chapter 34](34-expressions-part-2.md)
- Save-switch-restore — [Chapter 28](28-the-preprocessor.md)
- Scope stack — [Chapter 30](30-types-and-symbols.md#scopes-are-a-stack-of-integers)
- Scoped external identity — [Chapter 41](41-system-v-calls.md)
- Section-relative value — [Chapter 40](40-objects-and-relocations.md)
- Shared call signature — [Chapter 41](41-system-v-calls.md)
- Shared errno storage — [Chapter 43](43-runtime-and-libc.md)
- Shared escape decoder — [Chapter 29](29-the-lexer.md)
- Short-circuit logical AND/OR — [Chapter 33](33-expressions-part-1.md)
- Sign extension — [Chapter 31](31-elf-and-codegen-part-1.md)
- Stable object record — [Chapter 41](41-system-v-calls.md)
- Stable symbol handle — [Chapter 40](40-objects-and-relocations.md)
- Stack-buffer pattern — [Chapter 32](32-codegen-part-2.md)
- Stage-A parity comparison — [Chapter 38](38-main-and-bootstrap-chain.md#stage-a-the-parity-proof)
- Static initializer lowering — [Chapter 39](39-lp64-storage-and-initializers.md#initializers-reuse-expression-fixups)
- Static local storage — [Chapter 35](35-declarations-types-globals.md)
- Sticky-half unsigned conversion — [Chapter 47](47-floats.md)
- Stream state — [Chapter 43](43-runtime-and-libc.md)
- Struct descriptor — [Chapter 30](30-types-and-symbols.md#how-types-and-symbols-connect)
- Struct tag pre-registration — [Chapter 35](35-declarations-types-globals.md)
- Symbol table — [Chapter 30](30-types-and-symbols.md#the-symbol-table-parallel-arrays)
- Symbolic address operand — [Chapter 41](41-system-v-calls.md)
- System V AMD64 calling convention — [Chapter 41](41-system-v-calls.md)
- Target macro contract — [Chapter 44](44-target-headers.md)
- Typed conditional selection — [Chapter 45](45-typed-constants.md)
- Typed constant record — [Chapter 45](45-typed-constants.md)
- Typed integer emission — [Chapter 32](32-codegen-part-2.md)
- Unavailable tokens — [Chapter 28](28-the-preprocessor.md)
- Variadic cursor copying — [Chapter 46](46-varargs.md)
- Variadic register-save area — [Chapter 46](46-varargs.md)
- Withheld identities — [Chapter 44](44-target-headers.md)
- Workspace selection — [Chapter 27](27-arena-and-io-buffers.md)

### Part 4: Bootstrap and kernels

- Address translation and privilege — [Chapter 54](54-k0-and-k1.md#two-virtual-addresses-one-physical-byte)
- AMD64 recipe runner — [Chapter 54](54-k0-and-k1.md)
- Archive member comparison — [Chapter 52](52-gcc-4-fixed-point.md)
- Archive pin agreement — [Chapter 53](53-sealed-run.md)
- Compiler census — [Chapter 52](52-gcc-4-fixed-point.md)
- Compiler climb — [Chapter 55](55-linux-and-kexec.md)
- Compiler driver stream — [Chapter 50](50-seed-cc-fixed-point.md)
- Compiler fixed point — [Chapter 52](52-gcc-4-fixed-point.md)
- Direct Linux recipe — [Chapter 55](55-linux-and-kexec.md)
- Direct map — [Chapter 54](54-k0-and-k1.md#two-virtual-addresses-one-physical-byte)
- Direct recipes — [Chapter 51](51-owning-the-tools.md)
- Embedded initramfs — [Chapter 55](55-linux-and-kexec.md)
- Executable publication — [Chapter 53](53-sealed-run.md)
- Execve trace audit — [Chapter 53](53-sealed-run.md)
- Fixed configuration — [Chapter 51](51-owning-the-tools.md)
- Guarded configure probes — [Chapter 51](51-owning-the-tools.md)
- Identity map — [Chapter 54](54-k0-and-k1.md#two-virtual-addresses-one-physical-byte)
- Interrupted execve join — [Chapter 53](53-sealed-run.md)
- K0 serialized fork — [Chapter 54](54-k0-and-k1.md)
- K0 syscall fallbacks — [Chapter 54](54-k0-and-k1.md)
- K0-to-K1 handoff — [Chapter 54](54-k0-and-k1.md)
- K1 operating boundary — [Chapter 54](54-k0-and-k1.md)
- Kaem recipe runner — [Chapter 51](51-owning-the-tools.md)
- kexec-style handover — [Chapter 55](55-linux-and-kexec.md)
- Late tools — [Chapter 52](52-gcc-4-fixed-point.md)
- Libgcc — [Chapter 52](52-gcc-4-fixed-point.md)
- Linux boot parameters — [Chapter 55](55-linux-and-kexec.md)
- Output pin scope — [Chapter 55](55-linux-and-kexec.md)
- Physical address — [Chapter 54](54-k0-and-k1.md#two-virtual-addresses-one-physical-byte)
- RAM-tree import — [Chapter 54](54-k0-and-k1.md)
- Reproducible build — [Chapter 52](52-gcc-4-fixed-point.md)
- Result export — [Chapter 55](55-linux-and-kexec.md)
- Runtime link order — [Chapter 50](50-seed-cc-fixed-point.md)
- Sealed executable boundary — [Chapter 53](53-sealed-run.md)
- Seed-only driver construction — [Chapter 50](50-seed-cc-fixed-point.md)
- Source generator — [Chapter 52](52-gcc-4-fixed-point.md)
- Sysroot — [Chapter 52](52-gcc-4-fixed-point.md)
- Temporary scanner bootstrap — [Chapter 51](51-owning-the-tools.md)
- Virtual address — [Chapter 54](54-k0-and-k1.md#two-virtual-addresses-one-physical-byte)

### Appendix references

- Historical reproducibility and diverse double-compiling — [Appendix C](57-historical-reproducibility.md).
- Worked source-reading exercises — [Appendix D](58-worked-exercises.md).
- Forth, compiler, and bootstrap reading — [Appendix E](59-further-reading.md).
- Supported C language and ABI boundaries — [Appendix F](60-c-subset.md).
- Compiler diagnostics and exit codes — [Appendix G](61-error-codes.md).
- Exercise hints and feedback — [Appendix H](66-exercise-feedback.md).

## Capability checks at the transitions

The useful prerequisite is an action you can carry out, not a chapter you
have visited. These short checks sample the skills needed at the main
transitions. Try one before opening its feedback; if its notation is new,
read the linked explanation first. If a check comes easily, move on
without rereading the walkthrough behind it.

| Next task | Try before continuing | Explanation or repair route |
|---|---|---|
| Read the Forth library (Part 2) | With top at the right, trace `[lit] 2 [lit] 3 swap +` above an untouched `x`. Which final value is cached in `rdi`? | [The two-stack representation](04-x86-64-and-two-stacks.md#the-machine-before-the-instructions), then [stack-effect notation and tracing](14-lib-01-stacks-and-words.md#stack-effect-comments) |
| Read compiler helpers (Part 3) | If HERE starts at address `H`, trace `here [lit] 0 ,`. Separate the stack result, bytes written, and new HERE. | [Code emission and HERE](15-lib-02-code-emission-and-here.md), then [compile-time fixups](24-lib-11-control-flow-combinators.md#forward-branches-if-and-then-as-a-pair) |
| Give the type records a C meaning (Part 3) | Use the [C-input check](part-3-compiler.md#reading-the-c-input) to distinguish a pointer's stored address, its pointed-to value, an array element, and a record field. | The bridge teaches this notation locally; [Chapter 30](30-types-and-symbols.md) then encodes it. [Chapters 31](31-elf-and-codegen-part-1.md) and [34](34-expressions-part-2.md#lvalue-tracking) teach how the compiler emits address/value operations. |
| Follow a multi-file build (Part 4) | One object defines `helper`; another contains a call whose final address is unknown. Which stage places the objects and resolves that call? Would producing one runnable executable establish a compiler fixed point? | [Object relocations](40-objects-and-relocations.md), [linker placement](42-linker-and-archives.md), and [the generation comparison](50-seed-cc-fixed-point.md) |

<details>
<summary>Compare the three short traces</summary>

- The stack goes `x 2`, `x 2 3`, `x 3 2`, `x 5`. The final cached
  top in `rdi` is 5; `x` remains below it. If the value is right but you
  removed `x`, recover the call-boundary meaning of a stack effect.
- `here` leaves `H`; the literal adds 0; comma consumes that 0 and writes
  an eight-byte cell there. The final stack retains `H`, memory at `H`
  through `H+7` contains zero bytes, and HERE is `H+8`. Confusing `H` with
  those bytes is the address/value distinction to recover before reading
  arena and code-output helpers.
- The linker places sections and applies the relocation using the
  resolved symbol address. A working executable is only one build result.
  A fixed-point claim also needs specified generations, matched inputs,
  and a stated comparison of the outputs; Chapter 50 supplies that
  procedure for the two seed tools.

The C-input check has its own hidden feedback beside the bridge. If one
step was uncertain, compare its intermediate state with the explanation,
then retry with different values rather than memorizing this answer.

</details>

Some later transitions need a new representation even if the earlier
part went well. Before following exact rounding, use
[Chapter 47's floating representation bridge](47-floats.md). Before
following K1's page tables and Linux handover, use
[Chapter 54's address-translation bridge](54-k0-and-k1.md).

Come back after intervening work: for example, after Chapter 36, explain
which state belongs to the running Forth compiler and which stack changes
will occur only when its emitted C program executes. Reuse the
[Chapter 34 trace](34-expressions-part-2.md) if those two timelines have
merged in your account.

## Dependency graph

The prerequisite column transcribes the `Prerequisites:` line in each
chapter's matching `book/outline/NN-*.md` file. Most of these are editorial
reading-order edges: following the chain recovers the recommended first
pass, not a demonstrated minimum set of skills for every later task. Use
the capability checks above to select a repair or a familiar entry point.
The last column selects earlier explanations to revisit, not an
additional set of requirements. A reference can be a comparison or an
optional consultation; a forward pointer alone does not add a dependency.

| Chapter | Prerequisites from outline | Selected earlier explanations |
|---|---|---|
| [4 — x86-64 encoding and the two-stack machine](04-x86-64-and-two-stacks.md) | [3](03-where-this-fits.md) | — |
| [5 — ELF, entry, and the memory map](05-elf-and-entry.md) | [4](04-x86-64-and-two-stacks.md) | [4](04-x86-64-and-two-stacks.md) |
| [6 — Stack and memory primitives](06-stack-primitives.md) | [5](05-elf-and-entry.md) | [4](04-x86-64-and-two-stacks.md), [5](05-elf-and-entry.md) |
| [7 — Arithmetic and logic in machine code](07-arithmetic-and-logic.md) | [6](06-stack-primitives.md) | [4](04-x86-64-and-two-stacks.md), [5](05-elf-and-entry.md), [6](06-stack-primitives.md) |
| [8 — The seed’s Linux boundary](08-seed-io.md) | [7](07-arithmetic-and-logic.md) | [4](04-x86-64-and-two-stacks.md), [5](05-elf-and-entry.md), [6](06-stack-primitives.md) |
| [9 — The dictionary and token reader](09-dictionary.md) | [8](08-seed-io.md) | [4](04-x86-64-and-two-stacks.md), [5](05-elf-and-entry.md), [6](06-stack-primitives.md), [8](08-seed-io.md) |
| [10 — The colon compiler](10-colon-compiler.md) | [9](09-dictionary.md) | [4](04-x86-64-and-two-stacks.md), [9](09-dictionary.md) |
| [11 — Branches and inline cells](11-branches.md) | [10](10-colon-compiler.md) | [9](09-dictionary.md), [10](10-colon-compiler.md) |
| [12 — Decimal parsing and the REPL](12-repl.md) | [11](11-branches.md) | [8](08-seed-io.md), [9](09-dictionary.md), [10](10-colon-compiler.md) |
| [13 — The 32 seed primitives: reference](13-primitive-reference.md) | [4](04-x86-64-and-two-stacks.md), [12](12-repl.md) | [5](05-elf-and-entry.md), [6](06-stack-primitives.md), [7](07-arithmetic-and-logic.md), [8](08-seed-io.md), [9](09-dictionary.md), [10](10-colon-compiler.md), [11](11-branches.md), [12](12-repl.md) |
| [14 — Stacks and words](14-lib-01-stacks-and-words.md) | [13](13-primitive-reference.md) | [9](09-dictionary.md), [10](10-colon-compiler.md), [12](12-repl.md), [13](13-primitive-reference.md) |
| [15 — Code emission and HERE](15-lib-02-code-emission-and-here.md) | [14](14-lib-01-stacks-and-words.md), [13](13-primitive-reference.md) | [4](04-x86-64-and-two-stacks.md), [5](05-elf-and-entry.md), [6](06-stack-primitives.md), [9](09-dictionary.md), [13](13-primitive-reference.md) |
| [16 — Logic from NAND](16-lib-03-logic-from-nand.md) | [15](15-lib-02-code-emission-and-here.md), [13](13-primitive-reference.md) | [7](07-arithmetic-and-logic.md), [10](10-colon-compiler.md), [13](13-primitive-reference.md) |
| [17 — The return stack, over, and subtraction](17-lib-04-return-stack-over-subtract.md) | [16](16-lib-03-logic-from-nand.md), [13](13-primitive-reference.md) | [6](06-stack-primitives.md), [7](07-arithmetic-and-logic.md), [13](13-primitive-reference.md), [16](16-lib-03-logic-from-nand.md) |
| [18 — Linux syscall wrappers](18-lib-05-syscalls.md) | [17](17-lib-04-return-stack-over-subtract.md), [13](13-primitive-reference.md) | [4](04-x86-64-and-two-stacks.md), [8](08-seed-io.md), [13](13-primitive-reference.md), [15](15-lib-02-code-emission-and-here.md), [17](17-lib-04-return-stack-over-subtract.md) |
| [19 — Character classification](19-lib-06-character-classification.md) | [18](18-lib-05-syscalls.md), [13](13-primitive-reference.md) | [7](07-arithmetic-and-logic.md), [13](13-primitive-reference.md), [16](16-lib-03-logic-from-nand.md), [17](17-lib-04-return-stack-over-subtract.md) |
| [20 — Comparisons from unsigned division](20-lib-07-comparisons-from-division.md) | [19](19-lib-06-character-classification.md), [13](13-primitive-reference.md) | [7](07-arithmetic-and-logic.md), [13](13-primitive-reference.md), [19](19-lib-06-character-classification.md) |
| [21 — Stack shufflers](21-lib-08-stack-shufflers.md) | [20](20-lib-07-comparisons-from-division.md), [13](13-primitive-reference.md) | [13](13-primitive-reference.md), [17](17-lib-04-return-stack-over-subtract.md) |
| [22 — Memory updates and cell writers](22-lib-09-memory-and-cell-writers.md) | [21](21-lib-08-stack-shufflers.md), [13](13-primitive-reference.md) | [13](13-primitive-reference.md), [15](15-lib-02-code-emission-and-here.md) |
| [23 — Immediacy and constants](23-lib-10-immediacy-and-constants.md) | [22](22-lib-09-memory-and-cell-writers.md), [13](13-primitive-reference.md) | [9](09-dictionary.md), [10](10-colon-compiler.md) |
| [24 — Control-flow combinators](24-lib-11-control-flow-combinators.md) | [23](23-lib-10-immediacy-and-constants.md), [13](13-primitive-reference.md) | [9](09-dictionary.md), [11](11-branches.md) |
| [25 — Defining words and byte equality](25-lib-12-defining-words-and-bytes-eq.md) | [24](24-lib-11-control-flow-combinators.md), [13](13-primitive-reference.md) | [23](23-lib-10-immediacy-and-constants.md), [24](24-lib-11-control-flow-combinators.md) |
| [26 — The M1 assembler and hex2 linker](26-m1-and-hex2.md) | [25](25-lib-12-defining-words-and-bytes-eq.md) | [12](12-repl.md), [25](25-lib-12-defining-words-and-bytes-eq.md) |
| [27 — Arena and I/O buffers](27-arena-and-io-buffers.md) | [26](26-m1-and-hex2.md) | [20](20-lib-07-comparisons-from-division.md), [23](23-lib-10-immediacy-and-constants.md) |
| [28 — The preprocessor](28-the-preprocessor.md) | [27](27-arena-and-io-buffers.md) | [25](25-lib-12-defining-words-and-bytes-eq.md), [27](27-arena-and-io-buffers.md) |
| [29 — The lexer](29-the-lexer.md) | [28](28-the-preprocessor.md) | [27](27-arena-and-io-buffers.md), [28](28-the-preprocessor.md) |
| [30 — Types and symbols](30-types-and-symbols.md) | [29](29-the-lexer.md) | [27](27-arena-and-io-buffers.md), [29](29-the-lexer.md) |
| [31 — ELF emission and instruction encoding](31-elf-and-codegen-part-1.md) | [30](30-types-and-symbols.md) | [4](04-x86-64-and-two-stacks.md), [5](05-elf-and-entry.md) |
| [32 — Calls, shims, and globals](32-codegen-part-2.md) | [31](31-elf-and-codegen-part-1.md) | [29](29-the-lexer.md), [31](31-elf-and-codegen-part-1.md) |
| [33 — Expressions: precedence](33-expressions-part-1.md) | [32](32-codegen-part-2.md) | [29](29-the-lexer.md), [30](30-types-and-symbols.md) |
| [34 — Expressions: operands and assignment](34-expressions-part-2.md) | [33](33-expressions-part-1.md) | [30](30-types-and-symbols.md), [33](33-expressions-part-1.md) |
| [35 — Declarations and storage](35-declarations-types-globals.md) | [34](34-expressions-part-2.md) | [30](30-types-and-symbols.md), [32](32-codegen-part-2.md) |
| [36 — Statements and control flow](36-statements-if-while-for-return.md) | [35](35-declarations-types-globals.md) | [31](31-elf-and-codegen-part-1.md), [32](32-codegen-part-2.md) |
| [37 — Functions and translation units](37-functions-and-scope.md) | [36](36-statements-if-while-for-return.md) | [31](31-elf-and-codegen-part-1.md), [32](32-codegen-part-2.md) |
| [38 — Compiler entry and Stage A](38-main-and-bootstrap-chain.md) | [37](37-functions-and-scope.md) | [27](27-arena-and-io-buffers.md), [37](37-functions-and-scope.md) |
| [39 — LP64 storage and initializers](39-lp64-storage-and-initializers.md) | [38](38-main-and-bootstrap-chain.md) | [30](30-types-and-symbols.md), [35](35-declarations-types-globals.md) |
| [40 — Objects and relocations](40-objects-and-relocations.md) | [39](39-lp64-storage-and-initializers.md) | [31](31-elf-and-codegen-part-1.md), [32](32-codegen-part-2.md) |
| [41 — System V calls and separate compilation](41-system-v-calls.md) | [40](40-objects-and-relocations.md) | [31](31-elf-and-codegen-part-1.md), [39](39-lp64-storage-and-initializers.md) |
| [42 — Linker and archives](42-linker-and-archives.md) | [41](41-system-v-calls.md) | [40](40-objects-and-relocations.md) |
| [43 — Runtime, libc, streams, and formatting](43-runtime-and-libc.md) | [42](42-linker-and-archives.md) | [40](40-objects-and-relocations.md), [41](41-system-v-calls.md) |
| [44 — Target headers](44-target-headers.md) | [43](43-runtime-and-libc.md) | [28](28-the-preprocessor.md), [39](39-lp64-storage-and-initializers.md) |
| [45 — Typed constants](45-typed-constants.md) | [44](44-target-headers.md) | [34](34-expressions-part-2.md), [41](41-system-v-calls.md) |
| [46 — System V varargs](46-varargs.md) | [45](45-typed-constants.md) | [41](41-system-v-calls.md), [43](43-runtime-and-libc.md) |
| [47 — Floating values and exact literals](47-floats.md) | [46](46-varargs.md) | [41](41-system-v-calls.md), [45](45-typed-constants.md) |
| [48 — Record bitfields](48-bitfields.md) | [47](47-floats.md) | [39](39-lp64-storage-and-initializers.md), [45](45-typed-constants.md) |
| [49 — Aggregates and extended floating values](49-aggregate-abi.md) | [48](48-bitfields.md) | [41](41-system-v-calls.md), [46](46-varargs.md), [47](47-floats.md), [48](48-bitfields.md) |
| [50 — Building seed-cc and seed-ar](50-seed-cc-fixed-point.md) | [49](49-aggregate-abi.md) | [41](41-system-v-calls.md), [42](42-linker-and-archives.md) |
| [51 — Owning the tools](51-owning-the-tools.md) | [50](50-seed-cc-fixed-point.md) | [42](42-linker-and-archives.md), [50](50-seed-cc-fixed-point.md) |
| [52 — GCC 4.0.4: stages C and D](52-gcc-4-fixed-point.md) | [51](51-owning-the-tools.md) | [42](42-linker-and-archives.md), [51](51-owning-the-tools.md) |
| [53 — The sealed host run](53-sealed-run.md) | [52](52-gcc-4-fixed-point.md) | [52](52-gcc-4-fixed-point.md) |
| [54 — K0 and K1](54-k0-and-k1.md) | [53](53-sealed-run.md) | [18](18-lib-05-syscalls.md), [51](51-owning-the-tools.md) |
| [55 — Linux 7.2.8 and kexec under QEMU](55-linux-and-kexec.md) | [54](54-k0-and-k1.md) | [52](52-gcc-4-fixed-point.md), [54](54-k0-and-k1.md) |
| [56 — Epilogue: onward to GCC 15.2](56-gcc-15-epilogue.md) | [55](55-linux-and-kexec.md) | [55](55-linux-and-kexec.md) |
| [57 — Appendix C: historical reproducibility routes](57-historical-reproducibility.md) | [55](55-linux-and-kexec.md) | [38](38-main-and-bootstrap-chain.md), [50](50-seed-cc-fixed-point.md), [52](52-gcc-4-fixed-point.md), [53](53-sealed-run.md), [54](54-k0-and-k1.md), [55](55-linux-and-kexec.md), [56](56-gcc-15-epilogue.md) |
| [58 — Appendix D: worked exercises](58-worked-exercises.md) | D.1: [24](24-lib-11-control-flow-combinators.md); D.2: [10](10-colon-compiler.md) and [12](12-repl.md); D.3: [33](33-expressions-part-1.md) for the trace, [38](38-main-and-bootstrap-chain.md) for the full compiler run | [10](10-colon-compiler.md), [12](12-repl.md), [24](24-lib-11-control-flow-combinators.md), [33](33-expressions-part-1.md) |
| [59 — Appendix E: further reading](59-further-reading.md) | [26](26-m1-and-hex2.md), [38](38-main-and-bootstrap-chain.md) | [33](33-expressions-part-1.md) |
| [60 — Appendix F: the C subset](60-c-subset.md) | [26](26-m1-and-hex2.md), [38](38-main-and-bootstrap-chain.md) | [28](28-the-preprocessor.md), [30](30-types-and-symbols.md), [32](32-codegen-part-2.md), [33](33-expressions-part-1.md), [34](34-expressions-part-2.md), [35](35-declarations-types-globals.md), [36](36-statements-if-while-for-return.md), [37](37-functions-and-scope.md), [38](38-main-and-bootstrap-chain.md), [39](39-lp64-storage-and-initializers.md), [40](40-objects-and-relocations.md), [41](41-system-v-calls.md), [42](42-linker-and-archives.md), [43](43-runtime-and-libc.md), [44](44-target-headers.md), [45](45-typed-constants.md), [46](46-varargs.md), [47](47-floats.md), [48](48-bitfields.md), [49](49-aggregate-abi.md), [50](50-seed-cc-fixed-point.md), [51](51-owning-the-tools.md), [52](52-gcc-4-fixed-point.md) |
| [61 — Appendix G: compiler error codes](61-error-codes.md) | [26](26-m1-and-hex2.md), [38](38-main-and-bootstrap-chain.md) | [9](09-dictionary.md), [26](26-m1-and-hex2.md), [27](27-arena-and-io-buffers.md), [28](28-the-preprocessor.md), [30](30-types-and-symbols.md), [32](32-codegen-part-2.md), [33](33-expressions-part-1.md), [34](34-expressions-part-2.md), [35](35-declarations-types-globals.md), [36](36-statements-if-while-for-return.md), [37](37-functions-and-scope.md), [39](39-lp64-storage-and-initializers.md), [40](40-objects-and-relocations.md), [41](41-system-v-calls.md), [42](42-linker-and-archives.md), [45](45-typed-constants.md), [46](46-varargs.md), [47](47-floats.md), [48](48-bitfields.md), [49](49-aggregate-abi.md), [50](50-seed-cc-fixed-point.md) |

The prose references often reach past the immediately preceding chapter: the outlines preserve reading order, while the last column locates the particular machinery being reused. The historical appendix also points to the epilogue; a cross-reference alone does not add a prerequisite.

## Reading orders

### First pass

Read [Chapters 1–3](01-reading-the-book.md) for orientation, then Chapters 4–56 in sidebar order. Consult the appendices when a topic calls for them. This respects the main route's outline order. Appendix D can be used one exercise at a time at the points shown above; it does not require finishing Part 3 first.

### Compiler-only path

Begin with [Part 3](part-3-compiler.md), Chapters 27–49, if you can trace
Forth stack effects, distinguish compilation from execution, and follow
memory stores and emitted bytes. The transition checks above help locate
the specific earlier explanation if one of those is rusty; Chapter 26
explains the M1 format compared at Stage A. Use the local
C-input bridge before type and parser records. Stop at
[Chapter 38](38-main-and-bootstrap-chain.md) for the core compiler and
Stage A, or continue through [Chapter 49](49-aggregate-abi.md) for the
extended compiler. Keep [Appendix F](60-c-subset.md) and
[Appendix G](61-error-codes.md) nearby as references.

### Bootstrap-only path

Start at [Part 4](part-4-bootstrap.md), then read Chapters 50–56 in order.
To explain its build route, distinguish source, builder executables,
objects, archives, linking, and generation comparisons. Chapter 50's
controller additionally needs the Forth and object-format skills above.
Return to Chapters 40–42 for the object/linker mechanics rather than
assuming that every detail of Chapters 4–49 must be recalled first.
Reading the provenance argument and tracing every compiler helper are
different goals. Running the route has separate archive, platform, tool,
and resource requirements named by each checkpoint; the reading checks
do not replace those requirements. The local floating-point and paging
bridges remain available when you reach those mechanisms.
