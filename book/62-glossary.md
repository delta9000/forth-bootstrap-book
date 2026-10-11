# Glossary

Definitions are grouped by the Part that introduces each concept, then alphabetically. Each entry links to its teaching page; individual seed names and Forth words belong in the [word index](WORD-INDEX.md). For C APIs, use the teaching chapter or book search; the generated index does not enumerate C functions.

## Part 1: Machine and seed

**Allocation cursor** — The next dictionary byte available for emitted code or allocated data, held in HERE. [Chapter 9](09-dictionary.md).

**Binary reduction pattern** — Combine operands, release the consumed slot, and return the result in rdi. [Chapter 7](07-arithmetic-and-logic.md).

**Cached-top pattern** — `rdi` holds the top of the data stack; `rbp` points at the next value in memory, so a push stores the old top and moves `rbp` down. [Chapter 4](04-x86-64-and-two-stacks.md).

**Canonical flag** — Zero denotes false; a cell with every bit set denotes true. [Chapter 7](07-arithmetic-and-logic.md).

**Cell** — The seed's eight-byte (64-bit) native unit for stack values and full-width memory operations. [Chapter 4](04-x86-64-and-two-stacks.md).

**Colon definition** — A named body opened by `:` and completed by `;`. [Chapter 10](10-colon-compiler.md).

**Compilation state** — The interpreter state that selects execution of words or compilation of calls to them. [Chapter 10](10-colon-compiler.md).

**Compile mode** — The compilation state in which ordinary parsed words append calls to the current definition. [Chapter 10](10-colon-compiler.md).

**Consumed-slot property** — A branch removes the return address that points at its inline cell, leaving no extra return-stack entry. [Chapter 11](11-branches.md).

**Data stack** — The last-in, first-out stack holding Forth operands and results. [Chapter 4](04-x86-64-and-two-stacks.md).

**Decimal accumulation** — Convert a decimal digit sequence by multiplying the accumulated value by the base and adding each digit. [Chapter 12](12-repl.md).

**Dictionary** — The linked collection of named Forth definitions searched by the token interpreter. [Chapter 9](09-dictionary.md).

**Dictionary header** — Link, flags, and counted name immediately preceding the code. [Chapter 9](09-dictionary.md).

**ELF header** — Identifies the executable and locates its entry point and program headers. [Chapter 5](05-elf-and-entry.md).

**Endianness** — See **Little-endian**. [Chapter 4](04-x86-64-and-two-stacks.md).

**Execution token (xt)** — The address of a word's first instruction, immediately after its dictionary name. [Chapter 9](09-dictionary.md).

**Fixed-base contract** — A seed image byte loads at its file offset plus a fixed base address. [Chapter 5](05-elf-and-entry.md).

**Forth boolean** — See **Canonical flag**. [Chapter 7](07-arithmetic-and-logic.md).

**hex0** — A source format containing hexadecimal bytes and comments, assembled by hex0-seed. [Chapter 5](05-elf-and-entry.md).

**I/O scratch byte** — Temporary storage shared by the seed’s byte-input and byte-output operations. [Chapter 8](08-seed-io.md).

**Immediate operand** — A literal value encoded in an instruction rather than fetched from a register or memory. [Chapter 4](04-x86-64-and-two-stacks.md).

**Immediate word** — A word whose header flag requests execution even while other words are being compiled. [Chapter 10](10-colon-compiler.md).

**Inherited executable** — Machine code already present when a bootstrap route begins. [Chapter 3](03-where-this-fits.md).

**Inherited source** — Upstream source requiring a builder inside the route. [Chapter 3](03-where-this-fits.md).

**Inline-cell convention** — Data follows a call; the helper reads it and resumes beyond it. [Chapter 10](10-colon-compiler.md).

**Interpret mode** — The compilation state in which ordinary parsed words execute immediately. [Chapter 10](10-colon-compiler.md).

**Linux syscall register convention** — Number in rax; arguments in rdi, rsi, rdx, r10, r8, r9; result in rax; syscall clobbers rcx and r11. [Chapter 8](08-seed-io.md#the-linux-register-boundary).

**Little-endian** — Multi-byte values are stored least significant byte first. [Chapter 4](04-x86-64-and-two-stacks.md).

**Loadable segment** — A region an ELF loader maps into memory. Its program-header entry specifies file-backed bytes, zero-filled storage, the load address and permissions. [Chapter 5](05-elf-and-entry.md).

**ModR/M** — See **ModRM**. [Chapter 4](04-x86-64-and-two-stacks.md).

**ModRM** — The byte whose mod, reg and r/m fields select an instruction's registers or memory-addressing form. [Chapter 4](04-x86-64-and-two-stacks.md).

**Newest-first lookup** — Search linked headers from LATEST toward older entries; the newest match wins. [Chapter 9](09-dictionary.md).

**Prepare–call–recover** — Prepare kernel operands, invoke Linux, then establish the resulting Forth stack. [Chapter 8](08-seed-io.md).

**Primitive** — A Forth word implemented directly in the seed’s machine code. [Chapter 6](06-stack-primitives.md).

**rel32** — A signed displacement added to the address immediately after the instruction. [Chapter 4](04-x86-64-and-two-stacks.md).

**REPL dispatch** — Look up a token, then use the word's IMMEDIATE flag and the interpreter's STATE to choose execution or call compilation. A miss reports `token?` and continues. [Chapter 12](12-repl.md).

**Return stack** — The stack `rsp` addresses: hardware return addresses, and data a routine saves there explicitly. [Chapter 4](04-x86-64-and-two-stacks.md).

**Return-address shelter** — Holding a primitive's own return address aside while it moves data on the return stack. [Chapter 6](06-stack-primitives.md).

**REX** — An instruction prefix selecting operand width and extending register fields. [Chapter 4](04-x86-64-and-two-stacks.md).

**Second on stack** — The data-stack value immediately below the cached top, addressed through rbp. [Chapter 4](04-x86-64-and-two-stacks.md).

**Seed memory map** — Where the image, the dictionary allocation area, the stacks, the buffers and the system variables lie. [Chapter 5](05-elf-and-entry.md).

**SIB** — The scale/index/base byte that some memory-addressing forms add after ModRM. [Chapter 4](04-x86-64-and-two-stacks.md).

**stage0-posix** — The project supplying the inherited hex0-seed executable and utility sources used in this route. [Chapter 3](03-where-this-fits.md).

**Subroutine threading** — Compiled bodies call the native code of their component words. [Chapter 10](10-colon-compiler.md).

**System-variable cells** — Fixed mutable cells holding compilation state, the dictionary head, the allocation cursor and the last lookup result. [Chapter 5](05-elf-and-entry.md).

**Sysvar** — See **System-variable cells**. [Chapter 5](05-elf-and-entry.md).

**Token buffer** — Storage in which the token reader assembles the current whitespace-delimited name. [Chapter 9](09-dictionary.md).

**Top of stack** — The most recently pushed live data-stack value, cached in rdi in the seed. [Chapter 4](04-x86-64-and-two-stacks.md).

**TOS** — See **Top of stack**. [Chapter 4](04-x86-64-and-two-stacks.md).

**Under-TOS** — See **Second on stack**. [Chapter 4](04-x86-64-and-two-stacks.md).

**xt** — See **Execution token (xt)**. [Chapter 9](09-dictionary.md).

<a id="part-2-forth-library-and-assembler"></a>

## Part 2: Forth library

**Back-patching** — See **Emit, remember, patch**. [Chapter 24](24-lib-11-control-flow-combinators.md).

**Backward loops** — Loops whose branch destination was recorded before their body was emitted. [Chapter 24](24-lib-11-control-flow-combinators.md).

**Canonicalisation** — Preserves zero and converts any nonzero cell to an all-set true flag. [Chapter 20](20-lib-07-comparisons-from-division.md).

**Chained fixups** — A control-flow emitter patches an earlier destination slot and passes a fresh unresolved slot to the next combinator. [Chapter 24](24-lib-11-control-flow-combinators.md).

**Comparison cascade** — Ordering predicates derived from a basic comparison by reversing operands and negating flags. [Chapter 20](20-lib-07-comparisons-from-division.md).

**Counted name** — A name stored with its length in a dictionary header. [Chapter 9](09-dictionary.md).

**De Morgan's law** — An OR equals the complement of the AND of the complemented operands. [Chapter 16](16-lib-03-logic-from-nand.md).

**Deferred words** — A stable entry point whose target can be set later. [Chapter 25](25-lib-12-defining-words-and-bytes-eq.md).

**Division as a right shift** — Unsigned division by a power of the binary base discards the corresponding low bits. [Chapter 22](22-lib-09-memory-and-cell-writers.md).

**Early return** — A compiled return that leaves a word before its final semicolon; temporary return-stack data must already be balanced. [Chapter 24](24-lib-11-control-flow-combinators.md).

**Emit versus execute** — An emitter runs now to write instructions another word executes later. [Chapter 23](23-lib-10-immediacy-and-constants.md).

**Emit, remember, patch** — Reserve a destination slot, keep its address, fill it when the destination is known. [Chapter 24](24-lib-11-control-flow-combinators.md).

**Emit-and-divide** — Write the low byte, then divide away that byte to expose the next. [Chapter 22](22-lib-09-memory-and-cell-writers.md).

**Fixup on the stack** — The address of an unresolved slot, kept on the data stack during compilation. [Chapter 24](24-lib-11-control-flow-combinators.md).

**Functional completeness of NAND** — NAND constructions express every Boolean function. [Chapter 16](16-lib-03-logic-from-nand.md).

**Little-endian cell writers** — Emit a value from its least significant byte upward. [Chapter 22](22-lib-09-memory-and-cell-writers.md).

**Pad-and-call** — Caller arguments, zero padding, a fixed syscall number, then syscall6. [Chapter 18](18-lib-05-syscalls.md).

**Postfix evaluation** — Operands precede operators and wait on the data stack; word order replaces precedence and parentheses. [Chapter 14](14-lib-01-stacks-and-words.md).

**Range-check trick** — Subtract the base, divide unsigned by the range size, test for zero; below-range bytes wrap and fail. [Chapter 19](19-lib-06-character-classification.md).

**Reverse Polish notation** — See **Postfix evaluation**. [Chapter 14](14-lib-01-stacks-and-words.md).

**RPN** — See **Postfix evaluation**. [Chapter 14](14-lib-01-stacks-and-words.md).

**Runtime body** — The native sequence shared by constants and data-defining words that pushes an embedded value. [Chapter 23](23-lib-10-immediacy-and-constants.md).

**Self-NAND** — `dup nand` complements a cell. [Chapter 16](16-lib-03-logic-from-nand.md).

**Sign test by division** — Unsigned division by the value of the high bit isolates that bit, allowing a signed-negative test. [Chapter 20](20-lib-07-comparisons-from-division.md).

**Signed-overflow domain** — The subtraction-based signed comparison is valid only when the operand difference does not overflow. [Chapter 20](20-lib-07-comparisons-from-division.md).

**Stack trace** — Apply each component word's contract in body order to check a definition's combined effect. [Chapter 14](14-lib-01-stacks-and-words.md).

**Stack-effect notation** — ( before -- after ) describes a word's inputs and results, top of stack at the right. [Chapter 14](14-lib-01-stacks-and-words.md).

**Store-and-advance** — Write a payload at HERE, then advance HERE by the payload's width. [Chapter 15](15-lib-02-code-emission-and-here.md).

**Two's complement** — A signed `w`-bit field with its high bit set represents its unsigned value minus `2^w`; [Chapter 4](04-x86-64-and-two-stacks.md#reading-a-negative-displacement) applies that rule to displacements. Complementing a value and adding one produces its additive inverse in wrapping cell arithmetic; [Chapter 17](17-lib-04-return-stack-over-subtract.md) derives that operation.

**Word** — A named Forth operation identified by a dictionary entry and executable through its execution token. [Chapter 14](14-lib-01-stacks-and-words.md).

## Part 3: Compiler

**ABI** — An application binary interface: the agreed placement of arguments, results and records between separately built code. The book meets a private all-stack ABI (Chapter 39) and the System V AMD64 ABI. [Chapter 41](41-system-v-calls.md).

**Aggregate classification** — Record size and leaf types determine register classes or memory transport; the implemented subset rejects unsupported floating and mixed layouts. [Chapter 49](49-aggregate-abi.md).

**Aligned outgoing argument block** — Stack-passed arguments occupy an aligned caller-owned block above the return address. [Chapter 41](41-system-v-calls.md).

**Allocation metadata** — Extent and requested size kept with each block for free and realloc. [Chapter 43](43-runtime-and-libc.md).

**Arena** — A bounded compiler region whose allocation rounds a request and advances a cursor, without individual frees (a bump allocator). [Chapter 27](27-arena-and-io-buffers.md).

**Array node** — Element type, dimensions, size, alignment and qualifiers kept beside the type. [Chapter 30](30-types-and-symbols.md).

**Array-based va_list** — A variadic cursor represented as an array containing a record, so passing it shares the cursor while storage remains local. [Chapter 46](46-varargs.md).

**Assignment** — Save destination state, parse the source recursively, then emit the store. [Chapter 34](34-expressions-part-2.md).

**Atomic object publication** — Write, close, then rename into place. [Chapter 40](40-objects-and-relocations.md).

**Binary fold** — Save the left operand, parse the right, restore the left, emit the operation. [Chapter 33](33-expressions-part-1.md).

**Bitfield slice** — A field is a width and bit shift inside a containing storage unit at a byte offset. [Chapter 48](48-bitfields.md).

**Bootstrap chain** — Tools built from source supply the means to build the next tools; followed in Part 4. [Chapter 38](38-main-and-bootstrap-chain.md).

**Bounded formatting count** — The logical output length keeps counting even when the destination truncates. [Chapter 43](43-runtime-and-libc.md).

**Break/continue fixup lists** — Pending jumps grouped by enclosing construct and destination, patched when the target is known. [Chapter 36](36-statements-if-while-for-return.md).

**Buffered key handoff** — Prefetched input passes through key-drain before further reads. [Chapter 27](27-arena-and-io-buffers.md).

**Bump allocator** — See **Arena**. [Chapter 27](27-arena-and-io-buffers.md).

**Call transport plan** — Each argument gets an explicit register or stack location before any value moves. [Chapter 49](49-aggregate-abi.md).

**Checked constant arithmetic** — Signed arithmetic overflow is checked for addition, subtraction, multiplication and division; unsigned results wrap. Valid-count signed left shifts deliberately retain low bits, including negative or overflowing operands. [Chapter 45](45-typed-constants.md).

**Checked relocation assignment** — Resolve and range-check a relocation before writing its field. [Chapter 42](42-linker-and-archives.md).

**Code generation** — Translation of parsed operations into machine instructions and executable fields. [Chapter 31](31-elf-and-codegen-part-1.md).

**Codegen** — See **Code generation**. [Chapter 31](31-elf-and-codegen-part-1.md).

**Compact type encoding** — Base kind and pointer depth packed into one type word. [Chapter 30](30-types-and-symbols.md).

**Compiler diagnostic** — A source-line report and caller-chosen error code emitted when a compiler check fails. [Chapter 27](27-arena-and-io-buffers.md).

**Computed include operand** — Expand macros before validating and opening a header name. [Chapter 28](28-the-preprocessor.md).

**Conditional compilation** — Nested directive groups select which source regions enter the flattened input. [Chapter 28](28-the-preprocessor.md).

**Constant expressions** — Evaluate expression syntax at compile time, suppressing arithmetic in unselected arms. [Chapter 34](34-expressions-part-2.md).

**Constant pool watermark** — A saved allocation position to which the constant pool returns after a public parse, releasing temporary records. [Chapter 45](45-typed-constants.md).

**Declarator-local pointer depth** — Each name adds its own stars to the inherited pointer depth. [Chapter 35](35-declarations-types-globals.md).

**Dictionary hash index** — Index new Forth headers to speed lookup without changing its result. [Chapter 27](27-arena-and-io-buffers.md).

**Direct destination rounding** — The destination format is chosen before a literal or constant operation is rounded. [Chapter 47](47-floats.md).

**ELF wrapper** — The executable header and program header placed before emitted code, with sizes patched after emission. [Chapter 31](31-elf-and-codegen-part-1.md).

**Entry stub** — Emitted start code that calls main and passes its result to exit. [Chapter 37](37-functions-and-scope.md).

**Evaluation stack** — The runtime stack storage used by emitted expression code to preserve intermediate operands. [Chapter 33](33-expressions-part-1.md).

**Exact floating ratio** — A decimal literal is kept as an exact integer numerator and denominator. [Chapter 47](47-floats.md).

**Explicit relocation addend** — RELA records carry the adjustment apart from the field being repaired. [Chapter 40](40-objects-and-relocations.md).

**Expression accumulator** — Emitted expressions keep their current result in rdi; binary operations put the right operand in rcx. [Chapter 31](31-elf-and-codegen-part-1.md).

**Extended floating value** — A long double carried as an aligned stack copy and returned through the x87 result register; x87 state is transient. [Chapter 49](49-aggregate-abi.md).

**Fail-closed bootstrap runtime** — Explicitly unavailable operations report and terminate when executed. [Chapter 39](39-lp64-storage-and-initializers.md).

**Failure-preserving realloc** — Failed growth leaves the original allocation intact. [Chapter 43](43-runtime-and-libc.md).

**Floating payload transport** — Binary32/binary64 bits ride in expression cells and move into SSE registers for computation and argument/result ABI transport. Long double uses the later x87 path. [Chapter 47](47-floats.md).

**for-step rewind** — The step is skipped on first reading; after the body the lexer rewinds to it so its code follows the body. [Chapter 36](36-statements-if-while-for-return.md).

**Forward-call fixup list** — Arena nodes of patch offset plus old head; walked to patch every call site once the target exists. [Chapter 32](32-codegen-part-2.md).

**Frame pointer** — The register, `rbp`, anchoring local addresses in generated C functions. The seed uses that register for its data stack while running Forth. [Chapter 31](31-elf-and-codegen-part-1.md).

**Frameless adapter** — A machine-code leaf that keeps the stack layout its contract requires. [Chapter 43](43-runtime-and-libc.md).

**Full-width immediate placeholder** — An empty native-immediate field reserved for an absolute address determined later. [Chapter 32](32-codegen-part-2.md).

**Function frame** — A function’s stack storage for saved state, local objects and parameter slots. [Chapter 37](37-functions-and-scope.md).

**Function pre-registration** — The function's name is published before its local scope, so recursion works and the name survives the body. [Chapter 37](37-functions-and-scope.md).

**Global definition selection** — Strong definitions override weak ones; conflicting strong definitions fail. [Chapter 42](42-linker-and-archives.md).

**Global redeclaration reuse** — Repeated scalar declarations share one storage slot and initializer. [Chapter 37](37-functions-and-scope.md).

**Global-address fixups** — Parallel columns pair an output patch position with a data or BSS slot until placement. [Chapter 32](32-codegen-part-2.md).

**GNU archive index** — Symbol names map to candidate member-header offsets. [Chapter 42](42-linker-and-archives.md).

**Include pool** — Keeps included files while nested scans use their bytes. [Chapter 28](28-the-preprocessor.md).

**Independent argument cursors** — GP and XMM offsets advance separately; overflow arguments share one stack cursor. [Chapter 46](46-varargs.md).

**Inline allocator state** — The calloc shim keeps heap_base and heap_pos after its own ret, reached rip-relative. [Chapter 32](32-codegen-part-2.md).

**Inline/fallback compilation** — Emit native instructions when compiling, run the saved implementation when interpreting. [Chapter 27](27-arena-and-io-buffers.md).

**Input identity protection** — Device/inode checks stop the output from replacing one of its inputs. [Chapter 42](42-linker-and-archives.md).

**Integer literal classification** — Suffix, spelling and magnitude select an integer literal's type. [Chapter 30](30-types-and-symbols.md).

**Labels and goto** — Named destinations via function-local label entries plus pending jumps. [Chapter 36](36-statements-if-while-for-return.md).

**Late shim selection** — Runtime shim bodies are emitted only for names that still have pending references. [Chapter 37](37-functions-and-scope.md).

**Lazy member selection** — Extract only members that satisfy unresolved strong demand, until nothing new is needed. [Chapter 42](42-linker-and-archives.md).

**Left associativity** — Each loop iteration's result becomes the next iteration's left operand. [Chapter 33](33-expressions-part-1.md).

**Lexer** — The source reader that classifies characters into identifiers, keywords, literals and punctuation tokens. [Chapter 29](29-the-lexer.md).

**Lexer state block** — Reader and token state kept together so it can be snapshotted and restored. [Chapter 27](27-arena-and-io-buffers.md).

**libc shims** — Small emitted runtime routines (putchar, getchar, fopen, calloc, memcpy...) with narrower behaviour than libc. [Chapter 32](32-codegen-part-2.md).

**Local-first symbol numbering** — Serialization puts local symbols first and remaps relocation targets. [Chapter 40](40-objects-and-relocations.md).

**Logical source location** — Presumed file and line, tracked apart from physical include paths. [Chapter 28](28-the-preprocessor.md).

**LP64 native object storage** — Object widths and alignment decide native storage placement and record layout. [Chapter 39](39-lp64-storage-and-initializers.md).

**Lvalue** — An expression designating an object. The compiler retains its location until an operation requires either the stored value or the address as a destination. [Chapter 34](34-expressions-part-2.md).

**Lvalue tracking** — Expression metadata keeps storage location, type, qualifiers and array shape. [Chapter 34](34-expressions-part-2.md).

**M1** — The textual assembly format emitted by M2-Planet; Stage A compares two such output files byte for byte. [Chapter 38](38-main-and-bootstrap-chain.md#stage-a-the-parity-proof).

**M2-Planet** — The C compiler used as Stage A’s comparison target, built by both the Forth compiler and a reference compiler. [Chapter 38](38-main-and-bootstrap-chain.md).

**Macro expansion** — Collect arguments, substitute, then rescan the replacement. [Chapter 28](28-the-preprocessor.md).

**Macro table** — Parallel arrays of macro names, bodies, parameters and suppression state. [Chapter 28](28-the-preprocessor.md).

**Monolith** — A combined source file used to compile M2-Planet as a single input. [Chapter 38](38-main-and-bootstrap-chain.md).

**Native redirection** — A fresh native body replaces an earlier implementation by patching its entry point to jump to the new code. [Chapter 27](27-arena-and-io-buffers.md).

**Nonlocal continuation** — Saved registers, stack pointer and return address for resuming a live caller (setjmp/longjmp). [Chapter 43](43-runtime-and-libc.md).

**Numeric token spelling** — The token keeps its source slice, so base and suffix survive beside the wrapped value. [Chapter 29](29-the-lexer.md).

**One buffer per responsibility** — Separate raw input, preprocessed source and emitted output buffers. [Chapter 27](27-arena-and-io-buffers.md).

**Operand snapshot** — Saved left-operand metadata survives recursive parsing of the right operand. [Chapter 33](33-expressions-part-1.md).

**Operator table** — Rows tie punctuation and compound forms to grammar level, emitter and evaluator. [Chapter 33](33-expressions-part-1.md).

**Output back-patching** — Rewrite earlier output fields by offset without moving the append cursor. [Chapter 27](27-arena-and-io-buffers.md).

**Owed newlines** — Consumed newlines emitted later to keep line positions and token boundaries. [Chapter 28](28-the-preprocessor.md).

**Parser** — Recursive-descent routines that consume tokens according to C syntax and emit code while parsing. [Chapter 33](33-expressions-part-1.md).

**Per-object placement** — Each input section gets an aligned position in the executable. [Chapter 42](42-linker-and-archives.md).

**Per-operator normalization** — Each operator's result is cut to its C width before the next operator. [Chapter 45](45-typed-constants.md).

**Persistent call-save span** — Frame slots keep rsp and live expression values across calls. [Chapter 41](41-system-v-calls.md).

**Postfix operators** — Suffix handlers transform an operand while keeping the metadata later operations need. [Chapter 34](34-expressions-part-2.md).

**Precedence cascade** — One parser per precedence level; each asks the next tighter level for complete operands. [Chapter 33](33-expressions-part-1.md).

**Preprocessor** — Rewrites raw C into a flattened source buffer before lexing. [Chapter 28](28-the-preprocessor.md).

**Preserving store** — A bitfield store masks the unit and merges new bits, leaving neighbours unchanged; signed fields sign-extend on load. [Chapter 48](48-bitfields.md).

**Private all-stack ABI** — Generated functions receive arguments in caller-owned stack slots. [Chapter 39](39-lp64-storage-and-initializers.md).

**Prologue and epilogue** — Function-entry and function-exit code that establish and restore the call frame. [Chapter 31](31-elf-and-codegen-part-1.md).

**Prototype reuse** — A later prototype keeps the existing function entry and its pending calls. [Chapter 37](37-functions-and-scope.md).

**Ranked array descriptor** — Recursive element nodes keep array shape and row qualifiers. [Chapter 41](41-system-v-calls.md).

**Raw syscall result** — The kernel's result is left unchanged for public wrappers to translate. [Chapter 43](43-runtime-and-libc.md).

**rel32 placeholder and patch** — Emit a jump with a zero displacement, then cc-patch-rel32-to-here fixes it to the current position. [Chapter 31](31-elf-and-codegen-part-1.md).

**Remainder-based rounding** — Twice the exact remainder is compared with the divisor to round to nearest, ties to even. [Chapter 47](47-floats.md).

**Runtime-aware entry** — Start code initializes library state before main and routes its return through library exit. [Chapter 43](43-runtime-and-libc.md).

**Rvalue** — An expression’s computed value, distinguished from the storage location tracked for an lvalue. [Chapter 34](34-expressions-part-2.md).

**Save-switch-restore** — Suspend a region or sink, process nested text, resume the caller. [Chapter 28](28-the-preprocessor.md).

**Scope stack** — Saved symbol counts mark the rows removed and unlinked on scope exit. [Chapter 30](30-types-and-symbols.md).

**Scoped external identity** — An external's signature and fixups outlive the block-scoped parser symbol. [Chapter 41](41-system-v-calls.md).

**Section-relative value** — A symbol's value is its offset within its section until linking. [Chapter 40](40-objects-and-relocations.md).

**Shared call signature** — One retained signature drives both incoming parameters and outgoing calls. [Chapter 41](41-system-v-calls.md).

**Shared errno storage** — Single-threaded error state reached through __errno_location. [Chapter 43](43-runtime-and-libc.md).

**Shared escape decoder** — A shared routine converts a source escape to a byte and reports how much spelling it consumed. [Chapter 29](29-the-lexer.md).

**Short-circuit logical AND/OR** — Conditional branches skip the right operand when the left decides the result. [Chapter 33](33-expressions-part-1.md).

**Sign extension** — Widening a signed value by copying its sign bit into the added high bits. [Chapter 31](31-elf-and-codegen-part-1.md).

**Stable object record** — Storage identity survives parser scope reuse until object export. [Chapter 41](41-system-v-calls.md).

**Stable symbol handle** — An insertion ID kept independent of the ELF symbol order. [Chapter 40](40-objects-and-relocations.md).

**Stack-buffer pattern** — A pushed value supplies temporary buffer storage for byte I/O. [Chapter 32](32-codegen-part-2.md).

**Stage-A parity comparison** — Forth-built and GCC-built M2-Planet emit identical M1 for the same M2-Planet inputs; this checks assembly parity rather than correctness for all C. [Chapter 38](38-main-and-bootstrap-chain.md).

**Static initializer lowering** — Queued initialization routines reuse expression fixups and run before main. [Chapter 39](39-lp64-storage-and-initializers.md).

**Static local storage** — A locally scoped name that refers to persistent global storage. [Chapter 35](35-declarations-types-globals.md).

**Sticky-half unsigned conversion** — Large unsigned integers convert through signed SSE instructions without losing the rounding decision. [Chapter 47](47-floats.md).

**Stream state** — Ownership, buffered bytes, position, error and EOF tracked beyond the descriptor. [Chapter 43](43-runtime-and-libc.md).

**Struct descriptor** — A stable record-layout header pointing to a separately allocated, growable field table. [Chapter 30](30-types-and-symbols.md).

**Struct tag pre-registration** — Register an empty descriptor before parsing fields so self-references resolve. [Chapter 35](35-declarations-types-globals.md).

**Symbol table** — Parallel columns of name, kind, type and payload for each live declaration. [Chapter 30](30-types-and-symbols.md).

**Symbolic address operand** — A record plus addend stands for an address without loading it. [Chapter 41](41-system-v-calls.md).

**System V AMD64 calling convention** — The first six eligible INTEGER argument slots use rdi rsi rdx rcx r8 r9, with further arguments on the stack; ordinary integer/pointer scalar results use rax. Floating and aggregate arguments/results have additional transport rules. [Chapter 41](41-system-v-calls.md).

**Target macro contract** — Predefined macros publish the target platform and a bounded ANSI C header dialect. [Chapter 44](44-target-headers.md).

**Typed conditional selection** — Both arm types decide the result type before the chosen value is converted. [Chapter 45](45-typed-constants.md).

**Typed constant record** — Value, C type, descriptor and relocation symbol carried together. [Chapter 45](45-typed-constants.md).

**Typed integer emission** — Storage width, value conversion and unsigned operations kept separate. [Chapter 32](32-codegen-part-2.md).

**Unavailable tokens** — Shadow marks keep a macro from re-expanding across rescans. [Chapter 28](28-the-preprocessor.md).

**Variadic cursor copying** — Copying cursor fields permits independent traversals of the same saved arguments. [Chapter 46](46-varargs.md).

**Variadic register-save area** — Each variadic function invocation saves incoming argument registers in its own frame. [Chapter 46](46-varargs.md).

**Withheld identities** — Target headers receive neither a GCC identity nor a later C-version claim, avoiding unsupported dialect branches. [Chapter 44](44-target-headers.md).

**Workspace selection** — Switch buffer addresses and capacities between default and mapped storage. [Chapter 27](27-arena-and-io-buffers.md).

## Part 4: Bootstrap and kernels

**AMD64 recipe runner** — The guest program that executes recipe operations with explicit paths and checked process status. [Chapter 54](54-k0-and-k1.md).

**Archive member comparison** — For readable archives with simple, unique member names, compare ordered names and each named member's bytes while permitting container metadata to differ. Repeated names need a separate audit because named extraction does not identify each occurrence. [Chapter 52](52-gcc-4-fixed-point.md).

**Archive pin agreement** — Agreement between stage-specific source digests and the central input manifest. [Chapter 53](53-sealed-run.md).

**Compiler census** — A build that asks the configured Makefile which objects belong to `cc1`, compiles those objects with seed-cc, and optionally links them into `cc1`. [Chapter 52](52-gcc-4-fixed-point.md).

**Compiler climb** — Successive chain-built compilers supply the language and target support needed to build Linux. [Chapter 55](55-linux-and-kexec.md).

**Compiler driver stream** — Each compilation's input is the compiler layers, a fixed driver and one C source. [Chapter 50](50-seed-cc-fixed-point.md).

**Compiler fixed point** — Successive generations agree under the stated installed-output comparator. This route compares bytes first, then permits archive-container differences under the bounded **Archive member comparison** above. [Chapter 52](52-gcc-4-fixed-point.md).

**Direct Linux recipe** — The guest recipe extending tool construction through the compiler climb, Linux build, export and handover. [Chapter 55](55-linux-and-kexec.md).

**Direct map** — A kernel mapping in which adding a fixed base to a physical address gives a virtual address for the same memory. The address arithmetic requires matching page tables. [Chapter 54](54-k0-and-k1.md#two-virtual-addresses-one-physical-byte).

**Direct recipes** — The first Makefiles run commands without a shell interpreting them. [Chapter 51](51-owning-the-tools.md).

**Embedded initramfs** — An initial filesystem archive carried inside the kernel image. Here it supplies the static `/init` program and a console device node. [Chapter 55](55-linux-and-kexec.md).

**Executable publication** — The host grants seed-forth's execute bit between entries; it supplies no program bytes. [Chapter 53](53-sealed-run.md).

**Execve trace audit** — Account for each successful execve path using the starting executable, the host's bwrap entry, a chain-built program, or a script interpreted by the built shell. Failed attempts are separate evidence. [Chapter 53](53-sealed-run.md).

**Fixed configuration** — Hand-written config.h answers replace running configure for the first tools. [Chapter 51](51-owning-the-tools.md).

**Guarded configure probes** — Explicit tool settings and failing guard scripts keep configure from finding host tools. [Chapter 51](51-owning-the-tools.md).

**Identity map** — A mapping in which a virtual address translates to the same numeric physical address. It does not change addresses already held in registers. [Chapter 54](54-k0-and-k1.md#two-virtual-addresses-one-physical-byte).

**Interrupted execve join** — Pairing a trace’s unfinished and resumed syscall records by process identity before classifying the result. [Chapter 53](53-sealed-run.md).

**K0 serialized fork** — K0 runs a forked child to completion before resuming the parent, so no scheduler is needed. [Chapter 54](54-k0-and-k1.md).

**K0 syscall fallbacks** — Compatibility routines that retry or synthesize the few missing calls needed for the K0 build, after an unsupported-call result. [Chapter 54](54-k0-and-k1.md).

**K0-to-K1 handoff** — K0 loads the seed-built K1 with its ordinary program loader; K1 takes the machine. [Chapter 54](54-k0-and-k1.md).

**K1 operating boundary** — Protected processes and the Linux syscall subset the bootstrap tools use; static ELF only. [Chapter 54](54-k0-and-k1.md).

**Kaem recipe runner** — Kaem, built by seed-cc, runs the build recipes before any shell exists. [Chapter 51](51-owning-the-tools.md).

**kexec-style handover** — The running K1 loads its successor kernel and jumps to it without firmware. [Chapter 55](55-linux-and-kexec.md).

**Late tools** — Build tools rebuilt by the fixed-point compiler using their own configuration machinery. [Chapter 52](52-gcc-4-fixed-point.md).

**Libgcc** — Target support routines that generated code calls, built by the new GCC rather than seed-cc. [Chapter 52](52-gcc-4-fixed-point.md).

**Linux boot parameters** — The boot-state structure, command line and physical-memory map prepared before entering Linux. [Chapter 55](55-linux-and-kexec.md).

**Output pin scope** — An artifact digest may apply at any build path or only at the declared root when outputs embed configured paths. [Chapter 55](55-linux-and-kexec.md).

**Physical address** — The memory address reached after translation through page tables, distinct from the virtual address used by an instruction. [Chapter 54](54-k0-and-k1.md#two-virtual-addresses-one-physical-byte).

**RAM-tree import** — K1 imports hda as its RAM root and keeps K0's files under /k0/. [Chapter 54](54-k0-and-k1.md).

**Reproducible build** — A build whose repeated inputs and conditions yield byte-identical outputs. [Chapter 52](52-gcc-4-fixed-point.md).

**Result export** — Writing selected Linux outputs and build logs as a tar archive to the output disk before the kernel handover. [Chapter 55](55-linux-and-kexec.md).

**Runtime link order** — The startup object precedes program objects and the runtime archive, so archive selection answers outstanding references. [Chapter 50](50-seed-cc-fixed-point.md).

**Sealed executable boundary** — The prepared root starts with hex0-seed as its only executable file. [Chapter 53](53-sealed-run.md).

**Seed-only driver construction** — The seed alone builds seed-cc and seed-ar by fork/exec of ./seed-forth on assembled Forth input streams. [Chapter 50](50-seed-cc-fixed-point.md).

**Source generator** — A program that runs during the build and produces source to be compiled in a later step. In the initial GCC build, seed-cc builds these generators. [Chapter 52](52-gcc-4-fixed-point.md).

**Sysroot** — The directory tree holding the target headers and libraries the compiler's output uses. [Chapter 52](52-gcc-4-fixed-point.md).

**Temporary scanner bootstrap** — Heirloom lex builds an intermediate flex that then generates flex's own scanner. [Chapter 51](51-owning-the-tools.md).

**Virtual address** — The address a program uses for a memory access. Page tables translate it and determine whether the access is permitted; distinct virtual addresses can reach the same physical byte. [Chapter 54](54-k0-and-k1.md#two-virtual-addresses-one-physical-byte).
