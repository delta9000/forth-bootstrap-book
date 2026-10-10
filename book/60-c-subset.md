# Appendix F — The C subset

The C subset is a contract between accepted source, object layout and the calling convention. A construct can parse in the Stage A core without having the representation an ISO C program expects. Use the tables below to choose the target and find the chapter that establishes each boundary.

## Choose the compiler target

The compiler has a shared parser with target hooks, rather than a separate grammar for every build. Loading the later layers does not select their target: `cc-target-lp64` starts false, and `cc-sysv-enable` explicitly enables LP64 storage, System V calls and direct preprocessing (`forth-bootstrap/cc/060-cc-types.fth:55`; `forth-bootstrap/cc/121-cc-sysv.fth:1339`).

| Target | Language and ABI boundary | Where it is taught |
|---|---|---|
| Stage A core | The default uses the original integer and slot model, emits a whole executable and supplies built-in runtime shims. The entry reads C from stdin (`forth-bootstrap/cc/120-cc-main.fth:29`). | [Chapter 38 — Compiler entry and Stage A](38-main-and-bootstrap-chain.md) |
| LP64 storage | Width-aware objects, declarations and initializers. The standalone native program layer uses the private all-stack ABI, so selecting LP64 alone does not establish System V compatibility (`forth-bootstrap/cc/117-cc-native-program.fth:6`). | [Chapter 39 — LP64 storage and initializers](39-lp64-storage-and-initializers.md) |
| System V object target | Explicit target selection, relocatable objects and separate translation units; later hooks add varargs, floating values, bitfields and aggregate calls. The seed-cc bootstrap selects this object target (`forth-bootstrap/cc/driver/seed-cc-boot/tools-unit.fth:5`). | [Chapter 41 — System V calls and separate compilation](41-system-v-calls.md) |

The remaining `cc-bootstrap-floatbits` switch describes restricted integer-bit transport for floating data. It does not implement floating arithmetic, and System V selection clears it (`forth-bootstrap/cc/060-cc-types.fth:58`; `forth-bootstrap/cc/121-cc-sysv.fth:1339`). It is not the floating contract below.

## Types

Object width and expression storage are different questions. In the core, integer spellings collapse to the same type; LP64 preserves their widths and signedness. This is the principal reason a source program accepted by the core cannot be assumed to have an ordinary C memory layout.

| Type or form | Stage A core | LP64 / full System V target | Where it is taught |
|---|---|---|---|
| `int`, `short`, `long`, `long long`, signed/unsigned spellings | One signed 8-byte integer representation; the extra keywords do not select distinct integer widths (`forth-bootstrap/cc/110-cc-decl.fth:546`). | `short` is 2 bytes, `int` 4, `long` and `long long` 8; unsigned kinds are distinct. Long long has its own rank (`forth-bootstrap/cc/060-cc-types.fth:34`; `forth-bootstrap/cc/060-cc-types.fth:84`). | [Chapter 30 — Types and symbols](30-types-and-symbols.md); [Chapter 39](39-lp64-storage-and-initializers.md) |
| `char` | Byte access through a character pointer zero-extends. Ordinary local scalars and array elements reserve 8-byte slots; a character cast masks to a byte (`forth-bootstrap/cc/090-cc-emit.fth:126`; `forth-bootstrap/cc/110-cc-decl.fth:463`; `forth-bootstrap/cc/110-cc-decl.fth:657`). | `char` and `unsigned char` occupy 1 byte; plain char is signed (`forth-bootstrap/cc/060-cc-types.fth:84`; `forth-bootstrap/cc/060-cc-types.fth:107`). | [Chapter 35 — Declarations and storage](35-declarations-types-globals.md); [Chapter 39](39-lp64-storage-and-initializers.md) |
| `void`, pointers | Void return types and the `(void)` parameter sentinel; pointer depth is retained (`forth-bootstrap/cc/114-cc-func.fth:123`; `forth-bootstrap/cc/110-cc-decl.fth:132`). | Pointers occupy 8 bytes; void has no object storage (`forth-bootstrap/cc/060-cc-types.fth:84`). | [Chapter 37 — Functions and translation units](37-functions-and-scope.md); [Chapter 39](39-lp64-storage-and-initializers.md) |
| Enum and typedef names | Enumerators are integer constants. Typedefs register aliases; built-in library typedefs all alias the core integer (`forth-bootstrap/cc/116-cc-prog.fth:33`; `forth-bootstrap/cc/116-cc-prog.fth:815`). | Typedef lookup preserves aggregate descriptors and System V array shape (`forth-bootstrap/cc/115-cc-native.fth:218`; `forth-bootstrap/cc/121-cc-sysv.fth:99`). | [Chapter 37](37-functions-and-scope.md); [Chapter 39](39-lp64-storage-and-initializers.md); [Chapter 41](41-system-v-calls.md) |
| Fixed arrays | Local arrays allocate slots; a second dimension is outside the core declarator (`forth-bootstrap/cc/110-cc-decl.fth:459`). | Element-sized storage; System V adds recursively typed fixed dimensions and pointer-to-array shape (`forth-bootstrap/cc/121-cc-sysv.fth:108`). | [Chapter 35](35-declarations-types-globals.md); [Chapter 41](41-system-v-calls.md) |
| Function pointers | Local pointer declarators skip signature types. Explicit function-pointer parameter declarators are outside this parser; typedef spellings supply the core alternative (`forth-bootstrap/cc/110-cc-decl.fth:405`; `forth-bootstrap/cc/114-cc-func.fth:74`). | System V retains signatures and checks compatible declarations and calls (`forth-bootstrap/cc/121-cc-sysv.fth:55`). | [Chapter 35](35-declarations-types-globals.md); [Chapter 37](37-functions-and-scope.md); [Chapter 41](41-system-v-calls.md) |
| `_Bool` | Not a core declaration type (`forth-bootstrap/cc/110-cc-decl.fth:534`). | A byte type with nonzero-to-true conversion (`forth-bootstrap/cc/060-cc-types.fth:37`; `forth-bootstrap/cc/125-cc-consteval.fth:82`). | [Chapter 30](30-types-and-symbols.md); [Chapter 47 — Floating values and exact literals](47-floats.md) |
| Records, bitfields and floating types | Do not infer support from the keyword table. | Storage, value operations and ABI transport have separate boundaries, listed below. | [Chapter 48 — Record bitfields](48-bitfields.md); [Chapter 49 — Aggregates and extended floating values](49-aggregate-abi.md) |

## Operators

The shared precedence ladder covers the following operators. The table runs from weakest binding to strongest; target hooks change operand semantics, not this order (`forth-bootstrap/cc/100-cc-expr.fth:5`).

| Family | Accepted forms | Boundary and teaching chapter |
|---|---|---|
| Assignment | `=`, `+=`, `-=`, `*=`, `/=`, `%=`, `<<=`, `>>=`, `&=`, `\|=`, `^=` | Requires an lvalue; LP64 dispatches to typed assignment (`forth-bootstrap/cc/100-cc-expr.fth:2330`). [Chapter 34 — Expressions: operands and assignment](34-expressions-part-2.md) |
| Conditional and logical | `?:`, `\|\|`, `&&` | Selected conditional arm and short-circuit logical evaluation (`forth-bootstrap/cc/100-cc-expr.fth:2056`). [Chapter 33 — Expressions: precedence](33-expressions-part-1.md); [Chapter 34](34-expressions-part-2.md) |
| Bitwise, comparison and shifts | `\|`, `^`, `&`, `==`, `!=`, `<`, `<=`, `>`, `>=`, `<<`, `>>` | Core comparisons and right shift use signed emitters; LP64 selects unsigned operations from operand types (`forth-bootstrap/cc/100-cc-expr.fth:1669`; `forth-bootstrap/cc/100-cc-expr.fth:1793`). [Chapter 33](33-expressions-part-1.md) |
| Arithmetic | `+`, `-`, `*`, `/`, `%` | Core pointer addition is unscaled. LP64 scales pointer arithmetic and divides pointer differences by element size (`forth-bootstrap/cc/100-cc-expr.fth:1818`; `forth-bootstrap/cc/100-cc-expr.fth:1898`). [Chapter 33](33-expressions-part-1.md) |
| Unary and casts | `*`, `&`, `-`, `!`, `~`, prefix `++`/`--`, `(T)`, `sizeof` | Unary plus requires LP64. Core casts chiefly change tracked type, with byte masking for char; LP64 converts values (`forth-bootstrap/cc/110-cc-decl.fth:642`; `forth-bootstrap/cc/100-cc-expr.fth:1567`). [Chapter 34](34-expressions-part-2.md); [Chapter 35](35-declarations-types-globals.md); [Chapter 32](32-codegen-part-2.md) |
| Postfix | Calls, subscripts, `.`, `->`, postfix `++`/`--` | Subscripts and members carry lvalue information; signatures and record calls require later target hooks (`forth-bootstrap/cc/100-cc-expr.fth:1030`). [Chapter 34](34-expressions-part-2.md); [Chapter 41](41-system-v-calls.md); [Chapter 49](49-aggregate-abi.md) |
| Comma expression | `a, b` | Enabled under LP64; not a core expression operator (`forth-bootstrap/cc/100-cc-expr.fth:2427`). [Chapter 34](34-expressions-part-2.md) |

## Statements

| Form | Supported boundary | Where it is taught |
|---|---|---|
| Empty/expression statement, block, `if`/`else`, `while`, `do`/`while`, `return` | Core statement dispatch includes these forms (`forth-bootstrap/cc/112-cc-stmt.fth:881`). | [Chapter 36 — Statements and control flow](36-statements-if-while-for-return.md) |
| `for` | Core accepts expression clauses, including omitted clauses. Declaration-form initialization is enabled under LP64 (`forth-bootstrap/cc/112-cc-stmt.fth:247`). | [Chapter 36](36-statements-if-while-for-return.md) |
| `switch`, `case`, `default` | Core switch handling; LP64 also dispatches case/default labels from the ordinary statement parser (`forth-bootstrap/cc/112-cc-stmt.fth:870`). | [Chapter 36](36-statements-if-while-for-return.md) |
| `break`, `continue` | Intended for valid loop/switch contexts. The parser does not diagnose every out-of-context jump (`forth-bootstrap/cc/112-cc-stmt.fth:605`). | [Chapter 36](36-statements-if-while-for-return.md) |
| Labels and `goto` | Function-local labels. Core goto assumes its destination is outside a switch; native handling adds switch-stack trampolines (`forth-bootstrap/cc/112-cc-stmt.fth:734`; `forth-bootstrap/cc/112-cc-stmt.fth:787`). | [Chapter 36](36-statements-if-while-for-return.md) |
| Local declarations | Core scalars, pointers and fixed arrays; static locals receive persistent storage. LP64 dispatches to the native declaration parser (`forth-bootstrap/cc/110-cc-decl.fth:459`; `forth-bootstrap/cc/112-cc-stmt.fth:877`). | [Chapter 35](35-declarations-types-globals.md); [Chapter 39](39-lp64-storage-and-initializers.md) |

## Declarations and storage

| Area | Stage A core | Later target boundary and chapter |
|---|---|---|
| Functions and prototypes | Definitions, prototypes and forward-call fixups. Calls admit at most 6 arguments (`forth-bootstrap/cc/114-cc-func.fth:235`; `forth-bootstrap/cc/100-cc-expr.fth:625`). | System V checks signatures, supports stack arguments and handles identifier-list definitions (`forth-bootstrap/cc/121-cc-sysv.fth:55`; `forth-bootstrap/cc/121-cc-sysv.fth:1182`). [Chapter 37](37-functions-and-scope.md); [Chapter 41](41-system-v-calls.md) |
| Globals | Scalar constant initialization and zeroed arrays (`forth-bootstrap/cc/116-cc-prog.fth:397`). | Native storage has aligned objects; object mode retains extern, tentative, initialized and static identities (`forth-bootstrap/cc/123-cc-object-program.fth:62`). [Chapter 39](39-lp64-storage-and-initializers.md); [Chapter 40 — Objects and relocations](40-objects-and-relocations.md) |
| Initializers | No general brace-list initialization in the core local declarator (`forth-bootstrap/cc/110-cc-decl.fth:516`). | Brace lists, zero fill, character-array strings and inferred outer bounds. System V objects use typed static constants and relocations (`forth-bootstrap/cc/118-cc-native-init.fth:64`; `forth-bootstrap/cc/118-cc-native-init.fth:203`; `forth-bootstrap/cc/123-cc-object-program.fth:233`). [Chapter 39](39-lp64-storage-and-initializers.md); [Chapter 45 — Typed constants](45-typed-constants.md) |
| Qualifiers and storage classes | Core consumes qualifiers; static locals have storage semantics (`forth-bootstrap/cc/110-cc-decl.fth:145`). | Later code retains qualification and checks declaration contexts. `inline` is consumed rather than an optimization promise (`forth-bootstrap/cc/115-cc-native.fth:410`; `forth-bootstrap/cc/121-cc-sysv.fth:485`; `forth-bootstrap/cc/110-cc-decl.fth:174`). [Chapter 35](35-declarations-types-globals.md); [Chapter 41](41-system-v-calls.md) |
| Separate compilation | Whole-program executable output (`forth-bootstrap/cc/120-cc-main.fth:29`). | Relocatable output, symbol resolution and archives (`forth-bootstrap/cc/123-cc-object-program.fth:1`; `forth-bootstrap/cc/140-cc-link.fth:1`). [Chapter 40](40-objects-and-relocations.md); [Chapter 42 — Linker and archives](42-linker-and-archives.md) |

## Preprocessor

Direct preprocessing is selected independently of the original include policy. The System V target enables it explicitly; it must not be inferred merely from loading the preprocessor (`forth-bootstrap/cc/121-cc-sysv.fth:1339`).

| Form | Core policy | Direct / System V policy and chapter |
|---|---|---|
| Quoted and angle `#include` | Quoted names are opened literally, then under `tests/cc/`; angle includes are dropped (`forth-bootstrap/cc/040-cc-prep.fth:860`; `forth-bootstrap/cc/040-cc-prep.fth:1841`). | Real quoted/angle files; quoted search starts beside the includer, then uses configured directories. Missing files fail. Macro-computed operands are supported with checked syntax (`forth-bootstrap/cc/040-cc-prep.fth:866`; `forth-bootstrap/cc/040-cc-prep.fth:1864`). [Chapter 28 — The preprocessor](28-the-preprocessor.md) |
| Object/function `#define`, `#undef` | Replacement and rescanning; function arguments are substituted (`forth-bootstrap/cc/040-cc-prep.fth:1271`; `forth-bootstrap/cc/040-cc-prep.fth:2148`). | Adds stringizing and token pasting. Variadic macro parameter lists remain unsupported (`forth-bootstrap/cc/040-cc-prep.fth:2057`; `forth-bootstrap/cc/040-cc-prep.fth:2082`). [Chapter 28](28-the-preprocessor.md) |
| `#if`, `#ifdef`, `#ifndef`, `#elif`, `#else`, `#endif` | Conditional groups are handled even while text is being dropped (`forth-bootstrap/cc/040-cc-prep.fth:2219`). | LP64 conditional expressions track integer signedness (`forth-bootstrap/cc/100-cc-expr.fth:2468`). [Chapter 28](28-the-preprocessor.md); [Chapter 34](34-expressions-part-2.md) |
| `#error`, other directives | Active `#error` stops compilation; unrecognized directives are dropped (`forth-bootstrap/cc/040-cc-prep.fth:2205`). | Location-enabled mode interprets `#line` with checked operands (`forth-bootstrap/cc/040-cc-prep.fth:1966`). [Chapter 28](28-the-preprocessor.md) |
| Built-in names | Library constants such as `NULL`, `EOF`, stream names and open flags substitute for dropped headers (`forth-bootstrap/cc/040-cc-prep.fth:2273`). | System V adds `__FILE__`, `__LINE__` and explicit target predefines. It advertises a freestanding target, not GCC identity or a C99/C11 language version (`forth-bootstrap/cc/124-cc-target.fth:1`; `forth-bootstrap/cc/124-cc-target.fth:11`). [Chapter 44 — Target headers](44-target-headers.md) |

## Structs and unions

| Feature | Core boundary | Later boundary and chapter |
|---|---|---|
| Record layout and members | Tagged struct definitions without array fields or bitfield syntax; unions require LP64. Every field occupies an 8-byte slot. Member count is capped at 16 (`forth-bootstrap/cc/110-cc-decl.fth:208`; `forth-bootstrap/cc/060-cc-types.fth:245`). | Aligned structs/unions, nested records, array members, forward tags, anonymous member promotion and descriptor-preserving aliases (`forth-bootstrap/cc/115-cc-native.fth:410`; `forth-bootstrap/cc/115-cc-native.fth:455`). [Chapter 35](35-declarations-types-globals.md); [Chapter 39](39-lp64-storage-and-initializers.md) |
| Whole-record values | Core assignment rejects a scalar struct destination; core parameter spilling does not transport object bytes (`forth-bootstrap/cc/100-cc-expr.fth:2411`; `forth-bootstrap/cc/114-cc-func.fth:147`). Use record pointers at this boundary. | LP64 copies objects. System V transports eligible record bytes in integer registers or stack copies, including variadic retrieval; binary32/binary64 members are rejected by the ABI classifier (`forth-bootstrap/cc/118-cc-native-init.fth:154`; `forth-bootstrap/cc/131-cc-aggregate-abi.fth:19`). [Chapter 39](39-lp64-storage-and-initializers.md); [Chapter 49](49-aggregate-abi.md) |
| Bitfields | Outside the core field grammar (`forth-bootstrap/cc/110-cc-decl.fth:297`). | System V supports selected integer types and `_Bool`, preserving neighbouring bits on stores. Enum bitfields and unsupported widths fail; volatile operations provide no atomicity (`forth-bootstrap/cc/129-cc-bitfield.fth:1`; `forth-bootstrap/cc/129-cc-bitfield.fth:46`). [Chapter 48](48-bitfields.md) |

## Floating types in the direct-GCC System V target

Floating storage is not evidence of floating value support. The full System V layers provide scalar operations and call transport; the record classifier still restricts which floating members can cross a call boundary.

| Type | Supported operations and transport | Boundary and teaching chapter |
|---|---|---|
| `float`, `double` | Binary32/binary64 storage (4 and 8 bytes respectively), arithmetic, comparisons, conversions, updates and scalar results in XMM0 (`forth-bootstrap/cc/127-cc-binary64.fth:1`; `forth-bootstrap/cc/127-cc-binary64.fth:94`). Named arguments use the SSE class; variadic float promotes to double, and `va_arg` retrieves double (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:51`; `forth-bootstrap/cc/121-cc-sysv.fth:850`; `forth-bootstrap/cc/126-cc-varargs.fth:1`). | Floating leaves in records are rejected at the aggregate ABI boundary, even when their storage layout exists (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:29`). [Chapter 46 — System V varargs](46-varargs.md); [Chapter 47](47-floats.md); [Chapter 49](49-aggregate-abi.md) |
| Floating literals and static values | Exact conversion uses integer Forth arithmetic. Typed static values are written into object data; the mapped executable route rejects binary32/binary64 static leaves (`forth-bootstrap/cc/128-cc-float-literal.fth:1`; `forth-bootstrap/cc/123-cc-object-program.fth:233`; `forth-bootstrap/cc/127-cc-binary64.fth:288`). | Literal grammar, exponent and workspace limits are checked. Extended constant arithmetic includes explicit NaN and infinity cases (`forth-bootstrap/cc/128-cc-float-literal.fth:9`; `forth-bootstrap/cc/128-cc-float-literal.fth:504`). [Chapter 47](47-floats.md); [Chapter 49](49-aggregate-abi.md) |
| `long double` | Extended values occupy 16-byte aligned objects; scalar computation uses x87. Arguments travel in stack copies and results in `st(0)` (`forth-bootstrap/cc/121-cc-sysv.fth:255`; `forth-bootstrap/cc/132-cc-long-double.fth:1`; `forth-bootstrap/cc/131-cc-aggregate-abi.fth:1`). | Integer-only operations and incompatible scalar shapes fail. Long-double-only records can use X87 return transport; other eligible records use MEMORY when their leaves require it. Binary32/binary64 record leaves remain unsupported (`forth-bootstrap/cc/132-cc-long-double.fth:115`; `forth-bootstrap/cc/131-cc-aggregate-abi.fth:51`). [Chapter 49](49-aggregate-abi.md) |

## What an ISO C programmer should expect not to find

These are boundaries of the implemented subset, not an exhaustive conformance inventory. Accepted syntax alone does not establish ISO C semantics or a complete system library.

| Missing or bounded facility | Source boundary | Relevant chapter |
|---|---|---|
| Variable-length arrays | System V array bounds pass through constant parsing and checked size products, not runtime allocation (`forth-bootstrap/cc/121-cc-sysv.fth:139`). | [Chapter 41](41-system-v-calls.md) |
| Designated initializers | The initializer walker consumes elements in order; no designator branch exists (`forth-bootstrap/cc/118-cc-native-init.fth:203`). | [Chapter 39](39-lp64-storage-and-initializers.md) |
| Compound literals and GNU statement expressions | The operand parser handles parenthesized expressions or casts, not brace-delimited expressions (`forth-bootstrap/cc/100-cc-expr.fth:949`; `forth-bootstrap/cc/110-cc-decl.fth:642`). | [Chapter 34](34-expressions-part-2.md) |
| Vector aggregate ABI classes | The classifier implements INTEGER, scalar SSE, X87 and MEMORY with restricted record leaves (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:51`). | [Chapter 49](49-aggregate-abi.md) |
| Complete hosted libc | Core shims are a bounded built-in set; called but undefined functions fail. The System V route supplies a separate seed runtime, selected by its bootstrap driver (`forth-bootstrap/cc/116-cc-prog.fth:848`; `forth-bootstrap/cc/driver/seed-cc-boot/tools-unit.fth:13`). | [Chapter 32 — Calls, shims, and globals](32-codegen-part-2.md); [Chapter 43 — Runtime, libc, streams, and formatting](43-runtime-and-libc.md) |
| General ISO conformance inferred from `__STDC__` | The target's predefines describe an explicit C90-oriented freestanding mode; they do not certify every language or library facility (`forth-bootstrap/cc/124-cc-target.fth:1`). | [Chapter 44](44-target-headers.md) |

## Coverage in practice

The compiler's demonstrated scope is the source chain it builds. Each row cites where the route builds that workload and what its check compares.

| Workload | Evidence and scope | Teaching chapter |
|---|---|---|
| M2-Planet Stage A | The parity script builds M2-Planet with the Forth compiler and compares its self-compilation M1 output with a GCC-built reference. This is an output comparison, not ISO conformance (`forth-bootstrap/tests/cc/stage-a-check.sh:1`). | [Chapter 38 — Compiler entry and Stage A](38-main-and-bootstrap-chain.md) |
| seed-cc and seed-ar | The Forth controller compiles the runtime and both tool sources, archives runtime objects and links the drivers (`forth-bootstrap/cc/driver/seed-cc-start.fth:339`). | [Chapter 50 — Building seed-cc and seed-ar](50-seed-cc-fixed-point.md) |
| Plumbing tools | seed-cc compiles kaem and stage0 utilities, followed by make, text/file/archive tools, parser generators and bash through the plumbing recipes (`forth-bootstrap/chain/plumbing/README.md:18`; `forth-bootstrap/chain/plumbing/stage1.kaem:23`; `forth-bootstrap/chain/plumbing/chain.kaem:13`). | [Chapter 51 — Owning the tools](51-owning-the-tools.md) |
| GCC 4.0.4 compiler proper and supporting programs | Configure selects seed-cc for target and build-time C compilation. The census requests the Makefile's cc1 objects and links cc1; Stage C then requests xgcc, cpp and collect2. Subsequent libgcc and musl builds use the resulting GCC (`forth-bootstrap/chain/gcc-direct/configure.sh:96`; `forth-bootstrap/chain/gcc-direct/census.sh:63`; `forth-bootstrap/chain/gcc-direct/stage-c.sh:178`). | [Chapter 52 — GCC 4.0.4: stages C and D](52-gcc-4-fixed-point.md) |

## Try it

Run from the `forth-bootstrap` checkout root with the seed built in Part 1. The layer list keeps the executing main last (`forth-bootstrap/cc/compiler-layers.sh:6`). No target-enable word is invoked, so this probes the core array limitation. The diagnostic and status are printed; the final test checks that the rejection was the one listed here.

```sh
(
{ cat forth/010-lib.fth $(cc/compiler-layers.sh); printf '%s\n' 'int main(void) { int a[2][3]; return 0; }'; } | ./seed-forth 2>&1
status=$?
printf 'compiler status: %s\n' "$status"
test "$status" -eq 159
)
```

Observed output:

```text
cc: line 1: error 159
compiler status: 159
```
