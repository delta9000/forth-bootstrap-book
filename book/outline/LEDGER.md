# Ledger: concepts taught, by chapter

One line per concept: `term | chapter | definition`, chapter as the new stub number and title.  Seeded from book/CONCEPTS.md (concept index) and book/WORD-INDEX.md (first section that defines or explains each word or idea), mapped from old chapters to new stubs with book/outline/MAPPING.md.  Chapter writers add their terms in their reports; the ledger is edited by hand, not by writers.

term | chapter | definition
--- | --- | ---
Checkpoint | 01 Reading the book | a command and its observed result that test one specific operation
Checkpoint working directory | 01 Reading the book | the forth-bootstrap checkout root, where checkpoint commands run
Inherited executable | 03 Where this fits: routes and history | machine code already present when a bootstrap route begins (here, the 229-byte hex0-seed)
Inherited source | 03 Where this fits: routes and history | upstream source that still needs a builder inside the route
Cached-top pattern | 04 x86-64 encoding and the two-stack machine | `rdi` holds the top of the data stack; `rbp` points at the next value in memory, so a push stores the old top and moves `rbp` down
Return stack (`rsp`) | 04 x86-64 encoding and the two-stack machine | the stack `rsp` addresses: hardware return addresses, and data a routine saves there explicitly
Cell | 04 x86-64 encoding and the two-stack machine | an eight-byte (64-bit) stack value
Little-endian | 04 x86-64 encoding and the two-stack machine | multi-byte values are stored least significant byte first
ModRM | 04 x86-64 encoding and the two-stack machine | the byte whose mod, reg and r/m fields select an instruction's registers or memory-addressing form
SIB | 04 x86-64 encoding and the two-stack machine | the scale/index/base byte that some memory-addressing forms add after ModRM
REX | 04 x86-64 encoding and the two-stack machine | the 0100WRXB prefix: W selects a 64-bit operand; R, X and B extend the reg, index and base fields
rel32 | 04 x86-64 encoding and the two-stack machine | a signed 32-bit displacement added to the address of the next instruction
Linux syscall register convention | 04 x86-64 encoding and the two-stack machine | number in rax; arguments in rdi, rsi, rdx, r10, r8, r9; result in rax; syscall clobbers rcx and r11
`_start` | 05 ELF, entry, and the memory map | seed label; `_start` at `0x400078`
`jmp_repl` | 05 ELF, entry, and the memory map | seed label; `JMP repl` at `0x0B5`
`sysvar_init` | 05 ELF, entry, and the memory map | seed label; The sysvar init at `0x085`
ELF + program header | 05 ELF, entry, and the memory map | concept (Seed VM internals (Part II)); introduced in old Ch 13
ELF header and program header | 05 ELF, entry, and the memory map | idea; The ELF magic and `Elf64_Ehdr`
Entry point (_start) | 05 ELF, entry, and the memory map | idea; `_start` at `0x400078`
Memory map | 05 ELF, entry, and the memory map | idea; The seed-Forth memory map (`PT_LOAD` covers `0x400000..0x1400000`)
Sysvar page (STATE, LATEST, HERE, LAST_FOUND) | 05 ELF, entry, and the memory map | idea; The sysvar init at `0x085`
The 16 MiB single segment | 05 ELF, entry, and the memory map | concept (Seed VM internals (Part II)); introduced in old Ch 13
The data-stack-in-`rdi`/`rbp` convention | 05 ELF, entry, and the memory map | concept (Seed VM internals (Part II)); introduced in old Ch 13
The I/O scratch byte at `0x412000` | 05 ELF, entry, and the memory map | concept (Seed VM internals (Part II)); introduced in old Ch 13
The sysvar page at `0x413000` | 05 ELF, entry, and the memory map | concept (Seed VM internals (Part II)); introduced in old Ch 13
The token buffer at `0x412800` | 05 ELF, entry, and the memory map | concept (Seed VM internals (Part II)); introduced in old Ch 13
ELF header | 05 ELF, entry, and the memory map | identifies the executable and locates its entry point and program headers
Loadable segment | 05 ELF, entry, and the memory map | a program-header entry giving file-backed bytes, zero-filled storage, the load address and permissions
Fixed-base contract | 05 ELF, entry, and the memory map | a seed image byte loads at its file offset plus 0x400000
Entry initialization | 05 ELF, entry, and the memory map | the startup code that sets the data-stack registers and the system variables before entering the REPL
Seed memory map | 05 ELF, entry, and the memory map | where the image, the dictionary allocation area, the stacks, the buffers and the system variables lie
System-variable cells | 05 ELF, entry, and the memory map | fixed mutable cells holding STATE, LATEST, HERE and LAST_FOUND (0x413000-0x413018)
`!` | 06 Stack and memory primitives | seed primitive; compiler word (`cc/020-cc-arena.fth`); `!` ( value addr -- )
`>r` | 06 Stack and memory primitives | seed primitive; compiler word (`cc/020-cc-arena.fth`); `>r` ( n -- ; R: -- n )
`@` | 06 Stack and memory primitives | seed primitive; compiler word (`cc/020-cc-arena.fth`); `@` ( addr -- value )
`c!` | 06 Stack and memory primitives | seed primitive; compiler word (`cc/020-cc-arena.fth`); `c!` ( byte addr -- )
`c@` | 06 Stack and memory primitives | seed primitive; compiler word (`cc/020-cc-arena.fth`); `c@` ( addr -- byte )
`cfetch_code` | 06 Stack and memory primitives | seed label; `c@` ( addr -- byte )
`cstore_code` | 06 Stack and memory primitives | seed label; `c!` ( byte addr -- )
`drop_code` | 06 Stack and memory primitives | seed label; `drop` in 9 bytes
`drop` | 06 Stack and memory primitives | seed primitive; compiler word (`cc/020-cc-arena.fth`); `drop` in 9 bytes
`dup_code` | 06 Stack and memory primitives | seed label; `dup` in 9 bytes
`dup` | 06 Stack and memory primitives | seed primitive; compiler word (`cc/020-cc-arena.fth`); `dup` in 9 bytes
`fetch_code` | 06 Stack and memory primitives | seed label; `@` ( addr -- value )
`r>` | 06 Stack and memory primitives | seed primitive; compiler word (`cc/020-cc-arena.fth`); `r>` ( -- n ; R: n -- )
`r@` | 06 Stack and memory primitives | seed primitive; compiler word (`cc/020-cc-arena.fth`); `r@` ( -- n ; R: n -- n )
`r_at_code` | 06 Stack and memory primitives | seed label; `r@` ( -- n ; R: n -- n )
`r_from_code` | 06 Stack and memory primitives | seed label; `r>` ( -- n ; R: n -- )
`store_code` | 06 Stack and memory primitives | seed label; `!` ( value addr -- )
`swap_code` | 06 Stack and memory primitives | seed label; `swap` in 12 bytes
`swap` | 06 Stack and memory primitives | seed primitive; compiler word (`cc/020-cc-arena.fth`); `swap` in 12 bytes
`to_r_code` | 06 Stack and memory primitives | seed label; `>r` ( n -- ; R: -- n )
TOS in rdi / data stack at rbp | 06 Stack and memory primitives | idea; The push and pop shapes
`dup` | 06 Stack and memory primitives | copies the cached top into a new data-stack slot ( a -- a a )
`drop` | 06 Stack and memory primitives | discards the top and reloads the next value ( a -- )
`swap` | 06 Stack and memory primitives | exchanges the top two values through a temporary register ( a b -- b a )
Return-address shelter | 06 Stack and memory primitives | holding a primitive's own return address aside while it moves data on the return stack
`>r` | 06 Stack and memory primitives | moves the data-stack top onto the caller's return stack ( n -- ; R: -- n )
`r>` | 06 Stack and memory primitives | moves a saved return-stack value onto the data stack ( -- n ; R: n -- )
`r@` | 06 Stack and memory primitives | copies the saved return-stack value without removing it ( -- n ; R: n -- n )
`@` | 06 Stack and memory primitives | replaces an address with the cell stored there ( addr -- v )
`!` | 06 Stack and memory primitives | stores a cell and consumes both operands ( v addr -- )
`c@` | 06 Stack and memory primitives | loads a byte and zero-extends it ( addr -- b )
`c!` | 06 Stack and memory primitives | stores the value's low byte and consumes both operands ( b addr -- )
Binary reduction pattern | 07 Arithmetic and logic in machine code | combine operands, release the consumed slot, and return the result in rdi
`+` | 07 Arithmetic and logic in machine code | returns the low cell of the sum ( a b -- sum )
`nand` | 07 Arithmetic and logic in machine code | returns the cell-wide complement of the operands' bitwise intersection ( a b -- bits )
Canonical flag | 07 Arithmetic and logic in machine code | zero is false; an all-set cell (-1) is true
`0=` | 07 Arithmetic and logic in machine code | normalizes a zero test into a canonical flag ( n -- flag )
`/` | 07 Arithmetic and logic in machine code | returns the unsigned quotient; the divisor must be nonzero ( a b -- quotient )
`*` | 07 Arithmetic and logic in machine code | returns the low cell of the product ( a b -- product )
`bye` | 08 The seed’s Linux boundary | terminates the process with status zero ( -- )
`emit` | 08 The seed’s Linux boundary | consumes a character and writes its low byte to stdout ( c -- )
`key` | 08 The seed’s Linux boundary | reads a byte from stdin, returning zero at EOF ( -- c )
`syscall6` | 08 The seed’s Linux boundary | transfers stack operands to syscall registers and returns the kernel result ( a b c d e f n -- rax )
Prepare–call–recover | 08 The seed’s Linux boundary | prepare kernel operands, invoke Linux, then establish the resulting Forth stack
Dictionary header | 09 The dictionary and token reader | link, flags, and counted name immediately preceding the code
Execution token (xt) | 09 The dictionary and token reader | address of a word's first instruction: header + 10 + name length
Newest-first lookup | 09 The dictionary and token reader | search linked headers from LATEST toward older entries; the newest match wins
`find` | 09 The dictionary and token reader | resolves an address-length name to an xt or zero ( c-addr u -- xt-or-0 )
`here` | 09 The dictionary and token reader | returns the current allocation cursor ( -- addr )
`,` | 09 The dictionary and token reader | appends a cell and advances the allocation cursor ( v -- )
`execute` | 09 The dictionary and token reader | consumes an xt and tail-jumps to its code ( xt -- )
read_word | 09 The dictionary and token reader | collects a token while skipping whitespace and comments ( -- c-addr u )
read_char | 09 The dictionary and token reader | returns an input byte in rdx and a whitespace verdict in ZF
report_token / fatal_token | 09 The dictionary and token reader | report rejected input as token?; fatal_token then exits with status 2
`state` / `latest` | 09 The dictionary and token reader | push the addresses of the STATE and LATEST cells ( -- addr )
`'` (tick) | 09 The dictionary and token reader | reads the next token and looks it up ( -- xt-or-0 )
Subroutine threading | 10 The colon compiler | compiled bodies call the native code of their component words
Colon definition | 10 The colon compiler | a named body opened by `:` and completed by `;`
Compilation state | 10 The colon compiler | STATE 0 interprets, STATE 1 compiles
IMMEDIATE flag | 10 The colon compiler | header flag that makes a word execute during compilation
compile_call | 10 The colon compiler | appends a native CALL rel32 to an xt at HERE ( xt -- )
Inline-cell convention | 10 The colon compiler | data follows a call; the helper reads it and resumes beyond it
`lit` | 10 The colon compiler | pushes the inline cell after its call and returns past it ( -- v )
`[lit]` | 10 The colon compiler | reads a decimal value and pushes it, or compiles CALL lit plus the cell ( -- n )
`*` | 07 Arithmetic and logic in machine code | seed primitive; compiler word (`cc/020-cc-arena.fth`); `*` and the `IMUL` instruction
`+` | 07 Arithmetic and logic in machine code | seed primitive; compiler word (`cc/020-cc-arena.fth`); `+` in 9 bytes
`/` | 07 Arithmetic and logic in machine code | seed primitive; compiler word (`cc/020-cc-arena.fth`); `/` and the `DIV` instruction
`0=` | 07 Arithmetic and logic in machine code | seed primitive; compiler word (`cc/020-cc-arena.fth`); `0=` in 15 bytes
`DIV` unsigned, `IDIV` signed | 07 Arithmetic and logic in machine code | concept (Seed VM internals (Part II)); introduced in old Ch 15
`divide_code` | 07 Arithmetic and logic in machine code | seed label; `/` and the `DIV` instruction
`nand_code` | 07 Arithmetic and logic in machine code | seed label; `nand` in 12 bytes
`plus_code` | 07 Arithmetic and logic in machine code | seed label; `+` in 9 bytes
`star_code` | 07 Arithmetic and logic in machine code | seed label; `*` and the `IMUL` instruction
`zeq_code` | 07 Arithmetic and logic in machine code | seed label; `0=` in 15 bytes
`bye_code` | 08 The seed’s Linux boundary | seed label; `bye_code` in 12 bytes
`bye` | 08 The seed’s Linux boundary | seed primitive; `bye_code` in 12 bytes
`emit_code` | 08 The seed’s Linux boundary | seed label; `emit_code` in 46 bytes
`emit` | 08 The seed’s Linux boundary | seed primitive; `emit_code` in 46 bytes
`key_code` | 08 The seed’s Linux boundary | seed label; `key_code` in 47 bytes
`key` | 08 The seed’s Linux boundary | seed primitive; `key_code` in 47 bytes
`syscall6_code` | 08 The seed’s Linux boundary | seed label; `syscall6_code` in 37 bytes
`'` | 09 The dictionary and token reader | seed primitive; `tick_code`: from name to xt
`,` | 09 The dictionary and token reader | seed primitive; `here_code` and `comma_code`
`comma_code` | 09 The dictionary and token reader | seed label; `here_code` and `comma_code`
`execute_code` | 09 The dictionary and token reader | seed label; `execute_code` ( xt -- )
`execute` | 09 The dictionary and token reader | seed primitive; `execute_code` ( xt -- )
`fatal_token` | 09 The dictionary and token reader | seed label; `report_token` and `fatal_token`: failing out loud
`find_code` | 09 The dictionary and token reader | seed label; `find_code` ( c-addr u -- xt-or-0 )
`find` | 09 The dictionary and token reader | seed primitive; `find_code` ( c-addr u -- xt-or-0 )
`find`, `'`, `execute`, `read_word` | 09 The dictionary and token reader | concept (Forth primitives (treated as black boxes in Part I)); introduced in old Ch 17
`here_code` | 09 The dictionary and token reader | seed label; `here_code` and `comma_code`
`here` | 09 The dictionary and token reader | seed primitive; `here_code` and `comma_code`
`latest_code` | 09 The dictionary and token reader | seed label; `state_code` and `latest_code`
`latest` | 09 The dictionary and token reader | seed primitive; `state_code` and `latest_code`
`read_char` | 09 The dictionary and token reader | seed label; `read_char`, one byte and a verdict
`read_word` | 09 The dictionary and token reader | seed label; `read_word`, the token reader
`report_token` | 09 The dictionary and token reader | seed label; `report_token` and `fatal_token`: failing out loud
`state_code` | 09 The dictionary and token reader | seed label; `state_code` and `latest_code`
`state` | 09 The dictionary and token reader | seed primitive; `state_code` and `latest_code`
`tick_code` | 09 The dictionary and token reader | seed label; `tick_code`: from name to xt
Comment skipping and loud token errors | 09 The dictionary and token reader | concept (Seed VM internals (Part II)); introduced in old Ch 17
Linear dictionary search | 09 The dictionary and token reader | idea; `find_code` ( c-addr u -- xt-or-0 )
Loud token errors (token?, exit 2) | 09 The dictionary and token reader | idea; `report_token` and `fatal_token`: failing out loud
Small tables, linear search, newest wins | 09 The dictionary and token reader | concept (C compiler ideas (Part III)); introduced in old Ch 17
Token reader and comment skipping | 09 The dictionary and token reader | idea; `read_word`, the token reader
`:` | 10 The colon compiler | seed primitive; `colon_code`'s anatomy
`;` | 10 The colon compiler | seed primitive; `semicolon_code` in five operations
`[lit]` | 10 The colon compiler | seed primitive; compiler word (`cc/020-cc-arena.fth`); `bracket_lit_code`: interpreting and compiling literals
`branch` | 11 Branches and inline cells | transfers control to the inline destination without changing the data stack ( -- )
`0branch` | 11 Branches and inline cells | consumes a flag; branches to the inline destination on zero, else continues past the cell ( flag -- )
Consumed-slot property | 11 Branches and inline cells | a branch removes the return address that points at its inline cell, leaving no extra return-stack entry
`bracket_lit_code` | 10 The colon compiler | seed label; `bracket_lit_code`: interpreting and compiling literals
`colon_code` | 10 The colon compiler | seed label; `colon_code`'s anatomy
`compile_call` | 10 The colon compiler | seed label; `compile_call`: one `CALL`, laid down at HERE
`lit_code` | 10 The colon compiler | seed label; `lit_code` and the inline-cell trick
`lit` | 10 The colon compiler | seed primitive; `lit_code` and the inline-cell trick
`semicolon_code` | 10 The colon compiler | seed label; `semicolon_code` in five operations
In-line cell after CALL site | 10 The colon compiler | concept (Seed VM internals (Part II)); introduced in old Ch 18
Inline cell after a CALL | 10 The colon compiler | idea; `lit_code` and the inline-cell trick
Subroutine threading | 10 The colon compiler | idea; `compile_call`: one `CALL`, laid down at HERE
`0branch` | 11 Branches and inline cells | seed primitive; `zbranch_code` in eleven instructions
`branch_code` | 11 Branches and inline cells | seed label; `branch_code` in four instructions
`branch` | 11 Branches and inline cells | seed primitive; `branch_code` in four instructions
`branch`, `0branch` | 11 Branches and inline cells | concept (Forth primitives (treated as black boxes in Part I)); introduced in old Ch 19
`zbranch_code` | 11 Branches and inline cells | seed label; `zbranch_code` in eleven instructions
Consumed-slot property | 11 Branches and inline cells | concept (Seed VM internals (Part II)); introduced in old Ch 19
Decimal accumulation | 12 Decimal parsing and the REPL | convert digits by repeatedly computing n * 10 + digit
parse_decimal_code | 12 Decimal parsing and the REPL | validates an unsigned decimal token; returns the value and a true flag, or 0 and false ( c-addr u -- n flag )
REPL dispatch | 12 Decimal parsing and the REPL | look up a token, then IMMEDIATE and STATE choose execution or call compilation; a miss reports token? and continues
Postfix evaluation (reverse Polish notation) | 14 Stacks and words | operands precede operators and wait on the data stack; word order replaces precedence and parentheses
Stack-effect notation | 14 Stacks and words | ( before -- after ) describes a word's inputs and results, top of stack at the right
Stack trace | 14 Stacks and words | apply each component word's contract in body order to check a definition's combined effect
`here-addr` | 15 Code emission and HERE | pushes the address of the HERE cell, for updating the allocation cursor ( -- a )
`c,` | 15 Code emission and HERE | stores the low byte at HERE and advances HERE by one ( b -- )
Store-and-advance | 15 Code emission and HERE | write a payload at HERE, then advance HERE by the payload's width
`and` | 16 Logic from NAND | bitwise intersection: NAND, then self-NAND to complement ( a b -- a&b )
`or` | 16 Logic from NAND | bitwise union via De Morgan: self-NAND each operand, then NAND ( a b -- a-or-b )
Self-NAND | 16 Logic from NAND | `dup nand` complements a cell
De Morgan's law | 16 Logic from NAND | a or b = ~(~a & ~b)
De Morgan's law as code | 16 Logic from NAND | complement each operand, then combine with NAND
Functional completeness of NAND | 16 Logic from NAND | NAND constructions express every Boolean function
Primitive vs derived word (the byte trade) | 16 Logic from NAND | derived words cost no seed bytes but need compiled storage and calls
push rax; ret (indirect jump) | 11 Branches and inline cells | idea; Why `push rax; ret` and not `jmp rax`?
`parse_decimal_code` | 12 Decimal parsing and the REPL | seed label; `parse_decimal_code` ( c-addr u -- n true \| 0 false )
`repl` | 12 Decimal parsing and the REPL | seed label; The REPL loop
Number parser | 12 Decimal parsing and the REPL | idea; `parse_decimal_code` ( c-addr u -- n true \| 0 false )
REPL (interpret/compile loop) | 12 Decimal parsing and the REPL | idea; The REPL loop
`+`, `dup`, `drop`, `swap` | 14 Stacks and words | concept (Forth primitives (treated as black boxes in Part I)); introduced in old Ch 1
`emit`, `key` | 14 Stacks and words | concept (Forth primitives (treated as black boxes in Part I)); introduced in old Ch 1
`nand` | 14 Stacks and words | concept (Forth primitives (treated as black boxes in Part I)); introduced in old Ch 1
Data stack | 14 Stacks and words | idea; .1  Reverse Polish, one more time
Reverse Polish notation | 14 Stacks and words | idea; .1  Reverse Polish, one more time
RPN / postfix evaluation | 14 Stacks and words | concept (Vocabulary and conventions); introduced in old Ch 1
Stack (data stack) | 14 Stacks and words | concept (Vocabulary and conventions); introduced in old Ch 1
Stack-effect notation | 14 Stacks and words | idea; .2  Stack-effect comments
Stack-effect notation `( a b -- c )` | 14 Stacks and words | concept (Vocabulary and conventions); introduced in old Ch 1
`@`, `!`, `c@`, `c!` | 15 Code emission and HERE | concept (Forth primitives (treated as black boxes in Part I)); introduced in old Ch 2
`c,` | 15 Code emission and HERE | Forth word (`forth/010-lib.fth`); `c,` and the workhorse pattern
`here-addr`, `c,` | 15 Code emission and HERE | concept (Forth primitives (treated as black boxes in Part I)); introduced in old Ch 2
Cells (8-byte) and bytes (1-byte) | 15 Code emission and HERE | concept (Vocabulary and conventions); introduced in old Ch 2
HERE (dictionary pointer) | 15 Code emission and HERE | idea; Why a "HERE" exists at all
`and` | 16 Logic from NAND | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); `and` in three words
`or` | 16 Logic from NAND | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); `or` in six words
De Morgan's law | 16 Logic from NAND | idea; `or` in six words
De Morgan's law as code | 16 Logic from NAND | concept (Forth-level ideas); introduced in old Ch 3
Functional completeness of NAND | 16 Logic from NAND | concept (Forth-level ideas); introduced in old Ch 3
Primitive vs derived word (the byte trade) | 16 Logic from NAND | idea; What this buys
`over` | 17 The return stack, over, and subtraction | copies the second item to the top via a balanced return-stack transfer ( a b -- a b a )
`-` | 17 The return stack, over, and subtraction | subtracts by adding the two's-complement negation ( a b -- a-b )
`1+` | 17 The return stack, over, and subtraction | adds one with cell wraparound ( n -- n+1 )
`1-` | 17 The return stack, over, and subtraction | subtracts one using the derived `-` ( n -- n-1 )
Two's complement | 17 The return stack, over, and subtraction | ~b + 1 is the additive inverse of b in cell arithmetic
`-` | 17 The return stack, over, and subtraction | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); `-` from `+` and `nand`
`1+` | 17 The return stack, over, and subtraction | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); Why subtraction isn't a primitive
`1-` | 17 The return stack, over, and subtraction | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); Why subtraction isn't a primitive
`>r`, `r>`, `r@` | 17 The return stack, over, and subtraction | concept (Forth primitives (treated as black boxes in Part I)); introduced in old Ch 4
`over` | 17 The return stack, over, and subtraction | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); `over` via the return stack
Return stack | 17 The return stack, over, and subtraction | concept (Vocabulary and conventions); introduced in old Ch 4
Two's complement | 17 The return stack, over, and subtraction | concept (Forth-level ideas); introduced in old Ch 4
`open` | 18 Linux syscall wrappers | path flags mode, three padding zeros, syscall 2; returns fd or a raw negative error ( path flags mode -- fd )
`read` | 18 Linux syscall wrappers | fd buf count, padding, syscall 0; returns bytes read or a raw negative error ( fd buf count -- n )
`write` | 18 Linux syscall wrappers | fd buf count, padding, syscall 1; returns bytes written or a raw negative error ( fd buf count -- n )
`close` | 18 Linux syscall wrappers | fd and five padding zeros, syscall 3 ( fd -- err )
`die` | 18 Linux syscall wrappers | exits unconditionally with status n via syscall 60 ( n -- )
Pad-and-call | 18 Linux syscall wrappers | caller arguments, zero padding, a fixed syscall number, then syscall6
`digit?` | 19 Character classification | (c-48)/10 0= accepts ASCII 48..57 ( c -- flag )
`alpha-lower?` | 19 Character classification | (c-97)/26 0= accepts ASCII a..z ( c -- flag )
`alpha-upper?` | 19 Character classification | (c-65)/26 0= accepts ASCII A..Z ( c -- flag )
`alpha?` | 19 Character classification | lowercase or uppercase test, combined with `or` ( c -- flag )
`space?` | 19 Character classification | accepts space, tab, LF or CR ( c -- flag )
Range-check trick | 19 Character classification | subtract the base, divide unsigned by the range size, test for zero; below-range bytes wrap and fail
Preserve-and-combine | 19 Character classification | keep the input available for every component test, then combine the flags
`true` | 20 Comparisons from unsigned division | the canonical true flag, made as 0 0= ( -- -1 )
`2^63` | 20 Comparisons from unsigned division | pushes 9223372036854775808, the sign-bit value ( -- u )
`0<` | 20 Comparisons from unsigned division | 2^63 / 0= 0= : -1 for a signed-negative cell, else 0 ( n -- f )
`=` | 20 Comparisons from unsigned division | - 0= ( a b -- f )
`<>` | 20 Comparisons from unsigned division | = 0= ( a b -- f )
`<` | 20 Comparisons from unsigned division | - 0< ; exact only while a - b fits in 64 signed bits ( a b -- f )
`>` | 20 Comparisons from unsigned division | swap < ( a b -- f )
`<=` | 20 Comparisons from unsigned division | > 0= ( a b -- f )
`>=` | 20 Comparisons from unsigned division | < 0= ( a b -- f )
Canonicalisation (0= 0=) | 20 Comparisons from unsigned division | preserves zero and turns any nonzero cell into -1
Sign test by division (2^63) | 20 Comparisons from unsigned division | unsigned division by 2^63 gives the sign bit as 0 or 1
Signed-overflow domain of < | 20 Comparisons from unsigned division | exact while a and b are less than 2^63 apart; outside it the subtraction wraps
Comparison cascade | 20 Comparisons from unsigned division | > <= >= derived from < by operand reversal and flag negation
`nip` | 21 Stack shufflers | swap drop ( a b -- b )
`rot` | 21 Stack shufflers | >r swap r> swap ( a b c -- b c a )
`2dup` | 21 Stack shufflers | over over ( a b -- a b a b )
`2drop` | 21 Stack shufflers | drop drop ( a b -- )
`close` | 18 Linux syscall wrappers | Forth word (`forth/010-lib.fth`); `close`: one real arg, five padding zeros
`die` | 18 Linux syscall wrappers | Forth word (`forth/010-lib.fth`); `die`: exit unconditionally
`open` | 18 Linux syscall wrappers | Forth word (`forth/010-lib.fth`); `open`: three real args, three padding zeros
`read` | 18 Linux syscall wrappers | Forth word (`forth/010-lib.fth`); `read` and `write`: a symmetric pair
`syscall6` | 18 Linux syscall wrappers | concept (Forth primitives (treated as black boxes in Part I)); introduced in old Ch 5
`write` | 18 Linux syscall wrappers | Forth word (`forth/010-lib.fth`); `read` and `write`: a symmetric pair
Syscall ABI (x86-64 Linux) | 18 Linux syscall wrappers | idea; A sidebar on the syscall ABI
`/`, `*`, `0=` | 19 Character classification | concept (Forth primitives (treated as black boxes in Part I)); introduced in old Ch 6
`alpha-lower?` | 19 Character classification | Forth word (`forth/010-lib.fth`); `digit?`, `alpha-lower?`, `alpha-upper?`, `alpha?`
`alpha-upper?` | 19 Character classification | Forth word (`forth/010-lib.fth`); `digit?`, `alpha-lower?`, `alpha-upper?`, `alpha?`
`alpha?` | 19 Character classification | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); `digit?`, `alpha-lower?`, `alpha-upper?`, `alpha?`
`digit?` | 19 Character classification | Forth word (`forth/010-lib.fth`); `digit?`, `alpha-lower?`, `alpha-upper?`, `alpha?`
`space?` | 19 Character classification | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); `space?`: four-way OR
Forth boolean convention (`-1`/`0`) | 19 Character classification | concept (Vocabulary and conventions); introduced in old Ch 6
Range-check trick | 19 Character classification | idea; The range-check trick
Range-check trick `(c-base)/range == 0` | 19 Character classification | concept (Forth-level ideas); introduced in old Ch 6
`0<` | 20 Comparisons from unsigned division | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); `0<` and the `0= 0=` canonicalisation
`2^63` | 20 Comparisons from unsigned division | Forth word (`forth/010-lib.fth`); The `2^63` trick
`<=` | 20 Comparisons from unsigned division | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); The cascade
`<>` | 20 Comparisons from unsigned division | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); `=` and `<>`: two tokens each
`<` | 20 Comparisons from unsigned division | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); The cascade
`=` | 20 Comparisons from unsigned division | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); `=` and `<>`: two tokens each
`>=` | 20 Comparisons from unsigned division | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); The cascade
`>` | 20 Comparisons from unsigned division | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); The cascade
`true` | 20 Comparisons from unsigned division | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); `0<` and the `0= 0=` canonicalisation
Canonicalisation (0= 0=) | 20 Comparisons from unsigned division | idea; `0<` and the `0= 0=` canonicalisation
Forth boolean (-1 / 0) | 20 Comparisons from unsigned division | idea; `0<` and the `0= 0=` canonicalisation
Sign test by division (2^63) | 20 Comparisons from unsigned division | idea; The `2^63` trick
Sign-extraction via `/2^63` | 20 Comparisons from unsigned division | concept (Forth-level ideas); introduced in old Ch 7
Signed-overflow domain of < | 20 Comparisons from unsigned division | idea; The cascade
`2drop` | 21 Stack shufflers | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); The four shuffles
`+!` | 22 Memory updates and cell writers | swap over @ + swap ! : adds n to the cell at addr ( n addr -- )
`-!` | 22 Memory updates and cell writers | subtracts n from the cell at addr ( n addr -- )
`,4` | 22 Memory updates and cell writers | appends the low four bytes of v at HERE, little-endian ( v -- )
`,8` | 22 Memory updates and cell writers | appends all eight bytes of v at HERE: low ,4 then high ,4 ( v -- )
Division as a right shift | 22 Memory updates and cell writers | unsigned / 256 shifts right by eight bits
Little-endian cell writers | 22 Memory updates and cell writers | emit a value from its least significant byte upward
Emit-and-divide | 22 Memory updates and cell writers | write the low byte, then divide by 256 to expose the next byte
`immediate` | 23 Immediacy and constants | stores 1 in the newest entry's flags byte ( -- )
`ret,` | 23 Immediacy and constants | emits C3 ( -- )
`push-imm64,` | 23 Immediacy and constants | emits the 18 bytes that push v: sub rbp,8; mov [rbp],rdi; movabs rdi,v ( v -- )
`push-body,` | 23 Immediacy and constants | push-imm64, ret, : the 19-byte runtime body ( v -- )
`constant` | 23 Immediacy and constants | : push-body, 0 state ! ( v "name" -- )
`call,` | 23 Immediacy and constants | emits a 5-byte CALL rel32 to an absolute target ( target -- )
`lit-xt` | 23 Immediacy and constants | constant holding the xt of the seed's lit ( -- xt )
`tib` | 23 Immediacy and constants | the token buffer address, state - 2048 ( -- a )
`char` | 23 Immediacy and constants | reads the next token and pushes its first byte ( "tok" -- c )
`[char]` | 23 Immediacy and constants | IMMEDIATE: compiles CALL lit plus the character cell, 13 bytes ( "tok" -- )
`tab` `nl` `bl` `lparen` `backslash` | 23 Immediacy and constants | constants for characters char cannot quote
Emit versus execute | 23 Immediacy and constants | an emitter runs now to write instructions another word executes later
`branch-xt` `0branch-xt` | 24 Control-flow combinators | constants capturing the xts of branch and 0branch at load time ( -- xt )
`if,` | 24 Control-flow combinators | IMMEDIATE: emits CALL 0branch plus a zero slot; leaves the slot address ( -- F )
`then,` | 24 Control-flow combinators | IMMEDIATE: patches the slot to HERE ( F -- )
`else,` | 24 Control-flow combinators | IMMEDIATE: emits CALL branch and a new slot, patches the if-slot to here ( I -- E )
`begin,` | 24 Control-flow combinators | IMMEDIATE: records HERE as the back-target ( -- B )
`while,` | 24 Control-flow combinators | IMMEDIATE: emits a conditional exit slot above the back-target ( B -- B F )
`repeat,` | 24 Control-flow combinators | IMMEDIATE: emits a branch to B and patches the exit slot ( B F -- )
`until,` | 24 Control-flow combinators | IMMEDIATE: emits 0branch to B; false repeats ( B -- )
`again,` | 24 Control-flow combinators | IMMEDIATE: emits an unconditional branch to B ( B -- )
`exit,` | 24 Control-flow combinators | IMMEDIATE: emits ret; the return stack must be clean on that path ( -- )
Emit, remember, patch | 24 Control-flow combinators | reserve a destination slot, keep its address, fill it when the destination is known
Fixup on the stack | 24 Control-flow combinators | the address of an unresolved slot, kept on the data stack during compilation
Chained fixups | 24 Control-flow combinators | else, resolves one slot while passing a new one to then,
Backward loops | 24 Control-flow combinators | branches to a destination recorded earlier by begin,
`2dup` | 21 Stack shufflers | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); The four shuffles
`nip` | 21 Stack shufflers | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); The four shuffles
`rot` | 21 Stack shufflers | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); The four shuffles
`+!` | 22 Memory updates and cell writers | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); `+!` and `-!`: idiomatic increment
`,4` | 22 Memory updates and cell writers | Forth word (`forth/010-lib.fth`); `,4` and `,8`: cell-sized emission
`,8` | 22 Memory updates and cell writers | Forth word (`forth/010-lib.fth`); `,4` and `,8`: cell-sized emission
`-!` | 22 Memory updates and cell writers | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); `+!` and `-!`: idiomatic increment
Division as a right shift | 22 Memory updates and cell writers | idea; Why divide by 256?
Little-endian cell writers | 22 Memory updates and cell writers | idea; `,4` and `,8`: cell-sized emission
Little-endian writers (`,4`, `,8`) | 22 Memory updates and cell writers | concept (Forth-level ideas); introduced in old Ch 9
`:`, `;`, `[lit]`, `lit`, `compile_call` | 23 Immediacy and constants | concept (Forth primitives (treated as black boxes in Part I)); introduced in old Ch 10
`[char]` (character literals compiled as `[lit]` bytes) | 23 Immediacy and constants | concept (Forth-level ideas); introduced in old Ch 10
`call,` (compile a 5-byte rel32 CALL) | 23 Immediacy and constants | concept (Forth-level ideas); introduced in old Ch 10
`constant` | 23 Immediacy and constants | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); `constant`'s runtime body
`immediate` | 23 Immediacy and constants | Forth word (`forth/010-lib.fth`); `immediate`: a one-liner
`lit-xt` | 23 Immediacy and constants | Forth word (constant, `forth/010-lib.fth`); Canonical source
`push-body,` | 23 Immediacy and constants | Forth word (`forth/010-lib.fth`); `constant`'s runtime body
`push-imm64,` | 23 Immediacy and constants | Forth word (`forth/010-lib.fth`); `constant`'s runtime body
`ret,` | 23 Immediacy and constants | Forth word (`forth/010-lib.fth`); `constant`'s runtime body
`state`, `latest` | 23 Immediacy and constants | concept (Forth primitives (treated as black boxes in Part I)); introduced in old Ch 10
Dictionary entry layout | 23 Immediacy and constants | concept (Vocabulary and conventions); introduced in old Ch 10
Dictionary header layout | 23 Immediacy and constants | idea; Dictionary header layout
IMMEDIATE flag | 23 Immediacy and constants | idea; The IMMEDIATE flag
Runtime body (push-imm64) | 23 Immediacy and constants | idea; `constant`'s runtime body
STATE (interpret vs compile mode) | 23 Immediacy and constants | concept (Forth-level ideas); introduced in old Ch 10
The 19-byte runtime body | 23 Immediacy and constants | concept (Forth-level ideas); introduced in old Ch 10
The IMMEDIATE flag | 23 Immediacy and constants | concept (Forth-level ideas); introduced in old Ch 10
`0branch-xt` | 24 Control-flow combinators | Forth word (constant, `forth/010-lib.fth`); `branch-xt` and `0branch-xt`: a load-time snapshot
`again,` | 24 Control-flow combinators | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); `until,`, `again,` and `exit,`
`begin,` | 24 Control-flow combinators | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); Backward loops: `begin,` / `while,` / `repeat,`
`branch-xt` | 24 Control-flow combinators | Forth word (constant, `forth/010-lib.fth`); `branch-xt` and `0branch-xt`: a load-time snapshot
`else,` | 24 Control-flow combinators | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); `else,`: chained fixups
`exit,` | 24 Control-flow combinators | Forth word (`forth/010-lib.fth`); `until,`, `again,` and `exit,`
`if,` | 24 Control-flow combinators | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); Forward branches: `if,` and `then,` as a pair
`repeat,` | 24 Control-flow combinators | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); Backward loops: `begin,` / `while,` / `repeat,`
`then,` | 24 Control-flow combinators | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); Forward branches: `if,` and `then,` as a pair
`until,` | 24 Control-flow combinators | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); `until,`, `again,` and `exit,`
`while,` | 24 Control-flow combinators | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); Backward loops: `begin,` / `while,` / `repeat,`
Backward loops | 24 Control-flow combinators | idea; Backward loops: `begin,` / `while,` / `repeat,`
`allot` | 25 Defining words and byte equality | advances HERE by n bytes without initializing them ( n -- )
`skip-vm-pages` | 25 Defining words and byte equality | moves HERE to state + 4096, above the seed's fixed pages ( -- )
`create` | 25 Defining words and byte equality | defines a word whose 19-byte body pushes the address just past it ( "name" -- )
`variable` | 25 Defining words and byte equality | create plus one zero cell ( "name" -- )
`fetch-xt` `execute-xt` | 25 Defining words and byte equality | constants holding the xts of @ and execute ( -- xt )
`defer-code-size` | 25 Defining words and byte equality | 29, the offset of a deferred word's target cell ( -- n )
`defer` | 25 Defining words and byte equality | defines a word that fetches and executes the xt stored in its cell ( "name" -- )
`is` | 25 Defining words and byte equality | stores an xt into a deferred word's target cell ( xt "name" -- )
Deferred words | 25 Defining words and byte equality | a stable entry point whose target can be set later
`token` | 25 Defining words and byte equality | reads the next token; leaves its buffer address and length ( "tok" -- a u )
`bytes,` | 25 Defining words and byte equality | copies a byte range to HERE ( a u -- )
`s,` | 25 Defining words and byte equality | token bytes, : copies the next token's bytes, no length or terminator ( "tok" -- )
`bytes-eq` | 25 Defining words and byte equality | compares two byte ranges, returning early on the first mismatch ( a b u -- f )
Chained fixups (else,) | 24 Control-flow combinators | idea; `else,`: chained fixups
Early exit (exit,) | 24 Control-flow combinators | idea; `until,`, `again,` and `exit,`
Early return with `exit,` (return stack must be clean) | 24 Control-flow combinators | concept (Forth-level ideas); introduced in old Ch 11
Emit, remember, patch | 24 Control-flow combinators | concept (Forth-level ideas); introduced in old Ch 11
Execution token (xt) | 24 Control-flow combinators | idea; `branch-xt` and `0branch-xt`: a load-time snapshot
Fixup on the stack | 24 Control-flow combinators | idea; Forward branches: `if,` and `then,` as a pair
Fixup-on-the-stack | 24 Control-flow combinators | concept (Forth-level ideas); introduced in old Ch 11
`allot` | 25 Defining words and byte equality | Forth word (`forth/010-lib.fth`); `allot` in one line
`bytes,` | 25 Defining words and byte equality | Forth word (`forth/010-lib.fth`); `s,`: names as data
`bytes-eq` | 25 Defining words and byte equality | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); `bytes-eq`: stop at the first mismatch
Self-contained assembler | 26 The M1 assembler and hex2 linker | 130-asm.fth runs on the seed and 010-lib.fth alone: load both, then asm-main
Label table | 26 The M1 assembler and hex2 linker | records of name slice and address; newest-first slice lookup, newest declaration wins
M1 macro | 26 The M1 assembler and hex2 linker | DEFINE name value: textual, non-recursive substitution before assembly
Sigil | 26 The M1 assembler and hex2 linker | ! @ ~ % (relative, 1-4 bytes, from field end), $ & (absolute, 2 and 4 bytes); %a>b gives a - b
Two-pass assembly | 26 The M1 assembler and hex2 linker | pass 1 counts bytes and records labels, pass 2 resolves and emits
Prospective-size check | 26 The M1 assembler and hex2 linker | asm-check-cap: die with a code unless the size after an append fits
Newest-first slice lookup | 26 The M1 assembler and hex2 linker | search records newest to oldest by length then bytes-eq; shared by labels and macros
asm buffers and cursor | 26 The M1 assembler and hex2 linker | asm-src-* asm-exp-* asm-cur-* asm-use-src asm-use-exp asm-reset-pos asm-load-stdin asm-eof? asm-peek-char asm-next-char
asm output | 26 The M1 assembler and hex2 linker | asm-out-* asm-emit-byte asm-emit-le asm-write-output (fixed path /tmp/asm-out)
asm labels | 26 The M1 assembler and hex2 linker | asm-labels asm-rec asm-count asm-store-label asm-find-label asm-base asm-ip asm-pass
asm numbers and bounds | 26 The M1 assembler and hex2 linker | asm-parse-number asm-dec-* asm-hex-char? hex-val asm-label-bounds asm-number-bounds asm-fit
asm tokens and dispatch | 26 The M1 assembler and hex2 linker | asm-read-token asm-skip-ws asm-process-token asm-do-ref asm-do-pct-ref asm-do-hex asm-check-hex asm-do-label-decl asm-tok-err
asm macros | 26 The M1 assembler and hex2 linker | asm-defs asm-def-store asm-def-find asm-is-define? asm-exp-bytes asm-exp-string-double asm-exp-string-single asm-expand-pass
`asm-main` | 26 The M1 assembler and hex2 linker | load stdin, expand, pass 1, rewind, pass 2, write /tmp/asm-out, bye
`create` | 25 Defining words and byte equality | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); `create`'s runtime body
`defer-code-size` | 25 Defining words and byte equality | Forth word (constant, `forth/010-lib.fth`); `defer` and `is`: a name now, a meaning later
`defer` | 25 Defining words and byte equality | Forth word (`forth/010-lib.fth`); `defer` and `is`: a name now, a meaning later
`execute-xt` | 25 Defining words and byte equality | Forth word (constant, `forth/010-lib.fth`); `defer` and `is`: a name now, a meaning later
`fetch-xt` | 25 Defining words and byte equality | Forth word (constant, `forth/010-lib.fth`); `defer` and `is`: a name now, a meaning later
`is` | 25 Defining words and byte equality | Forth word (`forth/010-lib.fth`); `defer` and `is`: a name now, a meaning later
`s,` | 25 Defining words and byte equality | Forth word (`forth/010-lib.fth`); `s,`: names as data
`skip-vm-pages` | 25 Defining words and byte equality | concept (Forth primitives (treated as black boxes in Part I)); introduced in old Ch 12
`token` | 25 Defining words and byte equality | Forth word (`forth/010-lib.fth`); `s,`: names as data
`variable` | 25 Defining words and byte equality | Forth word (`forth/010-lib.fth`); compiler word (`cc/020-cc-arena.fth`); `variable` = `create` + a cell
Counted names as data (s,) | 25 Defining words and byte equality | idea; `s,`: names as data
Deferred words | 25 Defining words and byte equality | idea; `defer` and `is`: a name now, a meaning later
Deferred words (`defer`/`is`: call a word defined later) | 25 Defining words and byte equality | concept (Forth-level ideas); introduced in old Ch 12
`asm-base` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); The label table
`asm-cap` | 26 The M1 assembler and hex2 linker | assembler word (constant, `forth/130-asm.fth`); The label table
`asm-check-cap` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); Buffers and a cursor
`asm-check-hex` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); One token, one decision
`asm-count` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); The label table
`asm-cp-addr` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); Macro expansion
`asm-cp-i` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); Macro expansion
`asm-cp-len` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); Macro expansion
`asm-cur-buf` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); Buffers and a cursor
`asm-cur-len` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); Buffers and a cursor
`asm-cur-pos` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); Buffers and a cursor
`asm-dec-addr` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); Numbers
`asm-dec-hex` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); Numbers
`asm-dec-i` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); Numbers
`asm-dec-len` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); Numbers
`asm-dec-neg` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); Numbers
`asm-dec-val` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); Numbers
`asm-def-cap` | 26 The M1 assembler and hex2 linker | assembler word (constant, `forth/130-asm.fth`); Macro expansion
`asm-def-count` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); Macro expansion
`asm-def-find` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); Macro expansion
`asm-def-rec-size` | 26 The M1 assembler and hex2 linker | assembler word (constant, `forth/130-asm.fth`); Macro expansion
`asm-def-rec` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); Macro expansion
`asm-def-store` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); Macro expansion
`asm-deff-addr` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); Macro expansion
`asm-deff-len` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); Macro expansion
`asm-define-kw` | 26 The M1 assembler and hex2 linker | assembler word (create, `forth/130-asm.fth`); Macro expansion
`asm-defs` | 26 The M1 assembler and hex2 linker | assembler word (create, `forth/130-asm.fth`); Macro expansion
`asm-do-hex` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); One token, one decision
`asm-do-label-decl` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); One token, one decision
`asm-do-pct-ref` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); One token, one decision
`asm-do-ref` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); One token, one decision
`asm-emit-byte` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); The output side
`asm-emit-le` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); Numbers
`asm-eof?` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); Buffers and a cursor
`asm-exp-buf` | 26 The M1 assembler and hex2 linker | assembler word (create, `forth/130-asm.fth`); Buffers and a cursor
`asm-exp-bytes` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); Macro expansion
`asm-exp-cap` | 26 The M1 assembler and hex2 linker | assembler word (constant, `forth/130-asm.fth`); Buffers and a cursor
`asm-exp-emit-byte` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); Buffers and a cursor
`asm-exp-len` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); Buffers and a cursor
`asm-exp-string-double` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); Macro expansion
`asm-exp-string-single` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); Macro expansion
`asm-expand-pass` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); Macro expansion
`asm-find-addr` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); The label table
`asm-find-gt` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); One token, one decision
`asm-find-label` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); The label table
`asm-find-len` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); The label table
`asm-fit-hi` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); One token, one decision
`asm-fit-lo` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); One token, one decision
`asm-fit` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); One token, one decision
`asm-gt-pos` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); One token, one decision
`asm-half` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); One token, one decision
`asm-hex-char?` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); Numbers
`asm-hex-digit` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); Macro expansion
`asm-hex-i` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); One token, one decision
`asm-init` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); Two passes
`asm-ip` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); The label table
`asm-is-define?` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); Macro expansion
`asm-label-bounds` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); One token, one decision
`asm-labels` | 26 The M1 assembler and hex2 linker | assembler word (create, `forth/130-asm.fth`); The label table
`asm-load-stdin` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); Buffers and a cursor
`asm-main` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); `asm-main`
Native redirection | 27 Arena and I/O buffers | code: makes a fresh header; native! patches an old word's entry to JMP rel32 to the new body
Inline/fallback compilation | 27 Arena and I/O buffers | emit native instructions when compiling, run the saved implementation when interpreting
Buffered key handoff | 27 Arena and I/O buffers | prefetched input passes through key-drain before further reads
Dictionary hash index | 27 Arena and I/O buffers | index new Forth headers to speed lookup without changing its result
Lexer state block | 27 Arena and I/O buffers | reader and token state kept together so it can be snapshotted and restored
Error codes and cc-die | 27 Arena and I/O buffers | report the source line and a caller-chosen code, then exit; cc-check-cap bounds appends
Bump allocator | 27 Arena and I/O buffers | cc-alloc rounds a length and advances a bounded region's pointer
One buffer per responsibility | 27 Arena and I/O buffers | separate raw input, preprocessed source and emitted output buffers
Output back-patching | 27 Arena and I/O buffers | rewrite earlier output fields by offset without moving the append cursor
Workspace selection | 27 Arena and I/O buffers | switch buffer addresses and capacities between default and mapped storage
Preprocessor | 28 The preprocessor | rewrites raw C into a flattened source buffer before lexing
Macro table | 28 The preprocessor | parallel arrays of macro names, bodies, parameters and suppression state
Macro expansion | 28 The preprocessor | collect arguments, substitute, then rescan the replacement
Include pool | 28 The preprocessor | keeps included files while nested scans use their bytes
Conditional compilation | 28 The preprocessor | take, seek and done states for nested #if/#ifdef groups
Save-switch-restore | 28 The preprocessor | suspend a region or sink, process nested text, resume the caller
Owed newlines | 28 The preprocessor | consumed newlines emitted later to keep line positions and token boundaries
Unavailable tokens | 28 The preprocessor | shadow marks keep a macro from re-expanding across rescans
Computed include operand | 28 The preprocessor | expand macros before validating and opening a header name
Logical source location | 28 The preprocessor | presumed file and line, tracked apart from physical include paths
Numeric token spelling | 29 The lexer | the token keeps its source slice, so base and suffix survive beside the wrapped value
Shared escape decoder | 29 The lexer | cc-decode-escape returns a byte and the source length it consumed
Consume-peek-commit | 29 The lexer | consume the first punctuation byte, peek at the rest, consume a continuation only when it completes a longer token
Lexer extension hook | 29 The lexer | cc-lex-extra-fwd may supply a token before ordinary classification (used by Chapter 47)
Putback, mark and reset | 29 The lexer | putback re-offers the current token; mark/reset copy the whole lexer state block for lookahead
`asm-next-char` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); Buffers and a cursor
`asm-nl-byte` | 26 The M1 assembler and hex2 linker | assembler word (create, `forth/130-asm.fth`); The output side
`asm-number-bounds` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); One token, one decision
`asm-out-buf` | 26 The M1 assembler and hex2 linker | assembler word (create, `forth/130-asm.fth`); The output side
`asm-out-cap` | 26 The M1 assembler and hex2 linker | assembler word (constant, `forth/130-asm.fth`); The output side
`asm-out-init` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); The output side
`asm-out-path` | 26 The M1 assembler and hex2 linker | assembler word (create, `forth/130-asm.fth`); `asm-main`
`asm-out-pos` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); The output side
`asm-parse-number` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); Numbers
`asm-pass-loop` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); Two passes
`asm-pass` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); The label table
`asm-peek-char` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); Buffers and a cursor
`asm-process-token` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); One token, one decision
`asm-quote-char` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); Reading tokens
`asm-read-bareword` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); Reading tokens
`asm-read-quoted` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); Reading tokens
`asm-read-token` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); Reading tokens
`asm-rec-size` | 26 The M1 assembler and hex2 linker | assembler word (constant, `forth/130-asm.fth`); The label table
`asm-rec` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); The label table
`asm-ref-name` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); One token, one decision
`asm-reset-pos` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); Buffers and a cursor
`asm-scan-i` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); One token, one decision
`asm-skip-rest-of-line` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); Reading tokens
`asm-skip-ws` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); Reading tokens
`asm-src-buf` | 26 The M1 assembler and hex2 linker | assembler word (create, `forth/130-asm.fth`); Buffers and a cursor
`asm-src-cap` | 26 The M1 assembler and hex2 linker | assembler word (constant, `forth/130-asm.fth`); Buffers and a cursor
`asm-src-len` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); Buffers and a cursor
`asm-store-label` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); The label table
`asm-tok-err` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); One token, one decision
`asm-tok-len` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); Reading tokens
`asm-tok-numeric?` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); One token, one decision
`asm-tok-start` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); Reading tokens
`asm-token-len-tmp` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); One token, one decision
`asm-token-start-tmp` | 26 The M1 assembler and hex2 linker | assembler word (variable, `forth/130-asm.fth`); One token, one decision
`asm-use-exp` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); Buffers and a cursor
`asm-use-src` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); Buffers and a cursor
`asm-write-output` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); The output side
`hex-val` | 26 The M1 assembler and hex2 linker | assembler word (`forth/130-asm.fth`); Numbers
Label table (name slice + address, newest wins) | 26 The M1 assembler and hex2 linker | concept (Assembler ideas (Part IV)); introduced in old Ch 33
M1 macro (`DEFINE name value`, textual substitution) | 26 The M1 assembler and hex2 linker | concept (Assembler ideas (Part IV)); introduced in old Ch 33
Self-contained program (depends on `010-lib.fth` only) | 26 The M1 assembler and hex2 linker | concept (Assembler ideas (Part IV)); introduced in old Ch 33
Sigil (`! @ ~ % $ &`: field width, absolute or end-of-field relative) | 26 The M1 assembler and hex2 linker | concept (Assembler ideas (Part IV)); introduced in old Ch 33
Two-pass assembly (pass 1 counts, pass 2 emits) | 26 The M1 assembler and hex2 linker | concept (Assembler ideas (Part IV)); introduced in old Ch 33
`0=,` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`add-rbp-8,` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`and,` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`cc-alloc` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); The arena
`cc-arena-base` | 27 Arena and I/O buffers | compiler word (create, `cc/020-cc-arena.fth`); The arena
`cc-arena-cap` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); The arena
`cc-arena-limit` | 27 Arena and I/O buffers | compiler word (variable, `cc/020-cc-arena.fth`); The arena
`cc-arena-map` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); The arena
`cc-arena-ptr` | 27 Arena and I/O buffers | compiler word (variable, `cc/020-cc-arena.fth`); The arena
`cc-arena-start` | 27 Arena and I/O buffers | compiler word (variable, `cc/020-cc-arena.fth`); The arena
`cc-check-cap` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Failing: `cc-die`
`cc-die-end` | 27 Arena and I/O buffers | compiler word (create, `cc/020-cc-arena.fth`); Failing: `cc-die`
`cc-die-what` | 27 Arena and I/O buffers | compiler word (create, `cc/020-cc-arena.fth`); Failing: `cc-die`
`cc-die-where` | 27 Arena and I/O buffers | compiler word (create, `cc/020-cc-arena.fth`); Failing: `cc-die`
`cc-die` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Failing: `cc-die`
`cc-emit-4le` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); The output buffer
`cc-emit-8le` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); The output buffer
`cc-emit-byte` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); The output buffer
`cc-eof?` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); The input and source buffers and the reader
`cc-err-dec` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Failing: `cc-die`
`cc-err-digits` | 27 Arena and I/O buffers | compiler word (create, `cc/020-cc-arena.fth`); Failing: `cc-die`
`cc-err-write` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Failing: `cc-die`
`cc-in-buf` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); The input and source buffers and the reader
`cc-in-buffer` | 27 Arena and I/O buffers | compiler word (variable, `cc/030-cc-io.fth`); The input and source buffers and the reader
`cc-in-cap` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); The input and source buffers and the reader
`cc-in-default-buf` | 27 Arena and I/O buffers | compiler word (create, `cc/030-cc-io.fth`); The input and source buffers and the reader
`cc-in-default-cap` | 27 Arena and I/O buffers | compiler word (constant, `cc/030-cc-io.fth`); The input and source buffers and the reader
`cc-in-direct-cap` | 27 Arena and I/O buffers | compiler word (constant, `cc/030-cc-io.fth`); Shared helpers
`cc-in-len` | 27 Arena and I/O buffers | compiler word (variable, `cc/030-cc-io.fth`); The input and source buffers and the reader
`cc-in-limit` | 27 Arena and I/O buffers | compiler word (variable, `cc/030-cc-io.fth`); The input and source buffers and the reader
`cc-io-default-workspace` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); Shared helpers
`cc-io-direct-base` | 27 Arena and I/O buffers | compiler word (variable, `cc/030-cc-io.fth`); Shared helpers
`cc-io-direct-workspace` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); Shared helpers
`cc-lex-state-size` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); The lexer's state block
`cc-lex-state` | 27 Arena and I/O buffers | compiler word (create, `cc/020-cc-arena.fth`); The lexer's state block
`cc-load-stdin` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); The input and source buffers and the reader
`cc-name-buckets` | 27 Arena and I/O buffers | compiler word (constant, `cc/030-cc-io.fth`); Shared helpers
`cc-name-find` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); Shared helpers
`cc-name-hash` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); Shared helpers
`cc-next-char` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); The input and source buffers and the reader
`cc-nf-a` | 27 Arena and I/O buffers | compiler word (variable, `cc/030-cc-io.fth`); Shared helpers
`cc-nf-addrs` | 27 Arena and I/O buffers | compiler word (variable, `cc/030-cc-io.fth`); Shared helpers
`cc-nf-lens` | 27 Arena and I/O buffers | compiler word (variable, `cc/030-cc-io.fth`); Shared helpers
`cc-nf-u` | 27 Arena and I/O buffers | compiler word (variable, `cc/030-cc-io.fth`); Shared helpers
`cc-out-buf` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); The output buffer
`cc-out-buffer` | 27 Arena and I/O buffers | compiler word (variable, `cc/030-cc-io.fth`); The output buffer
`cc-out-cap` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); The output buffer
`cc-out-default-buf` | 27 Arena and I/O buffers | compiler word (create, `cc/030-cc-io.fth`); The output buffer
`cc-out-default-cap` | 27 Arena and I/O buffers | compiler word (constant, `cc/030-cc-io.fth`); The output buffer
`cc-out-direct-cap` | 27 Arena and I/O buffers | compiler word (constant, `cc/030-cc-io.fth`); Shared helpers
`cc-out-init` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); The output buffer
`cc-out-limit` | 27 Arena and I/O buffers | compiler word (variable, `cc/030-cc-io.fth`); The output buffer
`cc-out-patch-4le` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); The output buffer
`cc-out-patch-8le` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); The output buffer
`cc-out-patch-byte` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); The output buffer
`cc-out-pos` | 27 Arena and I/O buffers | compiler word (variable, `cc/030-cc-io.fth`); The output buffer
`cc-peek-char` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); The input and source buffers and the reader
`cc-ra-buf` | 27 Arena and I/O buffers | compiler word (variable, `cc/030-cc-io.fth`); The input and source buffers and the reader
`cc-ra-cap` | 27 Arena and I/O buffers | compiler word (variable, `cc/030-cc-io.fth`); The input and source buffers and the reader
`cc-ra-code` | 27 Arena and I/O buffers | compiler word (variable, `cc/030-cc-io.fth`); The input and source buffers and the reader
`cc-ra-fd` | 27 Arena and I/O buffers | compiler word (variable, `cc/030-cc-io.fth`); The input and source buffers and the reader
`cc-ra-n` | 27 Arena and I/O buffers | compiler word (variable, `cc/030-cc-io.fth`); The input and source buffers and the reader
`cc-read-all` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); The input and source buffers and the reader
`cc-src-buf` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); The input and source buffers and the reader
`cc-src-buffer` | 27 Arena and I/O buffers | compiler word (variable, `cc/030-cc-io.fth`); The input and source buffers and the reader
`cc-src-cap` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); The input and source buffers and the reader
`cc-src-default-buf` | 27 Arena and I/O buffers | compiler word (create, `cc/030-cc-io.fth`); The input and source buffers and the reader
`cc-src-default-cap` | 27 Arena and I/O buffers | compiler word (constant, `cc/030-cc-io.fth`); The input and source buffers and the reader
`cc-src-direct-cap` | 27 Arena and I/O buffers | compiler word (constant, `cc/030-cc-io.fth`); Shared helpers
`cc-src-init` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); The input and source buffers and the reader
`cc-src-len` | 27 Arena and I/O buffers | compiler word (variable, `cc/030-cc-io.fth`); The input and source buffers and the reader
`cc-src-limit` | 27 Arena and I/O buffers | compiler word (variable, `cc/030-cc-io.fth`); The input and source buffers and the reader
`cc-src-line` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); The lexer's state block
`cc-src-pos` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); The lexer's state block
`cc-tok-pending` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); The lexer's state block
`cc-workspace-map` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); Shared helpers
`cc-workspace-round` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); Shared helpers
`cc-workspace-syscall-fwd` | 27 Arena and I/O buffers | compiler word (defer, `cc/030-cc-io.fth`); Shared helpers
`cc-workspace-syscall` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); Shared helpers
`cc-write-output` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); Writing the file
`cell[]` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); Shared helpers
`code-start` | 27 Arena and I/O buffers | compiler word (variable, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`code:` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`compiling?` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`fh-a` | 27 Arena and I/O buffers | compiler word (variable, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`fh-buckets` | 27 Arena and I/O buffers | compiler word (variable, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`fh-find` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`fh-hash` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`fh-index` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`fh-insert` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`fh-latest` | 27 Arena and I/O buffers | compiler word (variable, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`fh-pool` | 27 Arena and I/O buffers | compiler word (variable, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`fh-pos` | 27 Arena and I/O buffers | compiler word (variable, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`fh-u` | 27 Arena and I/O buffers | compiler word (variable, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`flag-al,` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`flag-test,` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`forth-<=` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`forth-<>` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`forth->=` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`forth->` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`here-13` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`here-8` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`ident-cont?` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); Shared helpers
`ident-start?` | 27 Arena and I/O buffers | compiler word (`cc/030-cc-io.fth`); Shared helpers
`in-range,` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`jmp-back,` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`jmp-fwd,` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`jmp-seed->r,` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`jmp-seed-r>,` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`jmp-seed-r@,` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`jmp-xt,` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`jz-back,` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`jz-fwd,` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`kd-buf` | 27 Arena and I/O buffers | compiler word (variable, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`kd-cap` | 27 Arena and I/O buffers | compiler word (variable, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`kd-n` | 27 Arena and I/O buffers | compiler word (variable, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`key-buffer-size` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`key-buffer` | 27 Arena and I/O buffers | compiler word (create, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`key-drain` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`key-len` | 27 Arena and I/O buffers | compiler word (variable, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`key-pos` | 27 Arena and I/O buffers | compiler word (variable, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`mov-rax-[rbp],` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`mov-rdi-rax,` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`movabs-rdx,` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`movabs-rsi,` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`native!` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`native-0<` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`native-1+` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`native-1-` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`native-<` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`native-=` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`native-and` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`native-minus` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`native-or` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`native-over` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`or,` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`poc-xt` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`pop-rsub,` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`pop-sub,` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`pop-tos,` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`push-or-compile` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`push-tos,` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`rel32!` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`sar63,` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`seed-0=` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`seed->r` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`seed-cfetch` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`seed-cstore` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`seed-drop` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`seed-dup` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`seed-fetch` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`seed-lit` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`seed-nand` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`seed-over` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`seed-plus` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`seed-r>` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`seed-r@` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`seed-slash` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`seed-star` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`seed-store` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`seed-swap` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`sub-rax-rdi,` | 27 Arena and I/O buffers | compiler word (`cc/020-cc-arena.fth`); Arithmetic, input and a light optimizing compile
`tok-kind` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); The lexer's state block
`tok-kw-id` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); The lexer's state block
`tok-num` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); The lexer's state block
`tok-str-addr` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); The lexer's state block
`tok-str-len` | 27 Arena and I/O buffers | compiler word (constant, `cc/020-cc-arena.fth`); The lexer's state block
Arena (bump allocator) | 27 Arena and I/O buffers | idea; The arena
Bump allocator | 27 Arena and I/O buffers | concept (C compiler ideas (Part III)); introduced in old Ch 21
Error codes and cc-die | 27 Arena and I/O buffers | idea; Failing: `cc-die`
Failing with a line and a code (`cc-die`, `cc-check-cap`) | 27 Arena and I/O buffers | concept (C compiler ideas (Part III)); introduced in old Ch 21
Input, source and output buffers | 27 Arena and I/O buffers | idea; The input and source buffers and the reader
Lexer state as one block (mark / reset look-ahead) | 27 Arena and I/O buffers | concept (C compiler ideas (Part III)); introduced in old Ch 21
Lexer state block | 27 Arena and I/O buffers | idea; The lexer's state block
One buffer instead of streaming | 27 Arena and I/O buffers | idea; Why one big buffer instead of streaming?
One buffer per responsibility | 27 Arena and I/O buffers | concept (C compiler ideas (Part III)); introduced in old Ch 21
Source buffer / output buffer / back-patching | 27 Arena and I/O buffers | concept (C compiler ideas (Part III)); introduced in old Ch 21
#define and macro expansion | 28 The preprocessor | idea; Macro expansion
#include and the include pool | 28 The preprocessor | idea; `#include` and its bounded file pool
`cc-builtin-name-EOF` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The built-in macros and the pass driver
`cc-builtin-name-EXIT_FAILURE` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The built-in macros and the pass driver
`cc-builtin-name-EXIT_SUCCESS` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The built-in macros and the pass driver
`cc-builtin-name-NULL` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The built-in macros and the pass driver
`cc-builtin-name-O_CREAT` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The built-in macros and the pass driver
`cc-builtin-name-O_RDONLY` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The built-in macros and the pass driver
`cc-builtin-name-O_TRUNC` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The built-in macros and the pass driver
`cc-builtin-name-O_WRONLY` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The built-in macros and the pass driver
`cc-builtin-name-stderr` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The built-in macros and the pass driver
`cc-builtin-name-stdin` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The built-in macros and the pass driver
`cc-builtin-name-stdout` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The built-in macros and the pass driver
`cc-macro-add` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The macro table
`cc-macro-body-addr-buffer` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); The macro table
`cc-macro-body-addr` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The macro table
`cc-macro-body-len-buffer` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); The macro table
`cc-macro-body-len` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The macro table
`cc-macro-bucket` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The macro table
`cc-macro-busy-buffer` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); The macro table
`cc-macro-busy-cell` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-macro-busy` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The macro table
`cc-macro-cap` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The macro table
`cc-macro-count` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); The macro table
`cc-macro-default-body-addr` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The macro table
`cc-macro-default-body-len` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The macro table
`cc-macro-default-busy` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The macro table
`cc-macro-default-cap` | 28 The preprocessor | compiler word (constant, `cc/040-cc-prep.fth`); The macro table
`cc-macro-default-name-addr` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The macro table
`cc-macro-default-name-len` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The macro table
`cc-macro-default-params` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The macro table
`cc-macro-direct-base` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); The macro table
`cc-macro-direct-cap` | 28 The preprocessor | compiler word (constant, `cc/040-cc-prep.fth`); The macro table
`cc-macro-find` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The macro table
`cc-macro-hash-reset` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The macro table
`cc-macro-hnext` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The macro table
`cc-macro-limit` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); The macro table
`cc-macro-link` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The macro table
`cc-macro-name-addr-buffer` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); The macro table
`cc-macro-name-addr` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The macro table
`cc-macro-name-len-buffer` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); The macro table
`cc-macro-name-len` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The macro table
`cc-macro-params-buffer` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); The macro table
`cc-macro-params` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The macro table
`cc-macro-pool-cap` | 28 The preprocessor | compiler word (constant, `cc/040-cc-prep.fth`); The macro table
`cc-macro-pool-pos` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); The macro table
`cc-macro-pool` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The macro table
`cc-macro-record` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The macro table
`cc-mf-a` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); The macro table
`cc-mf-u` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); The macro table
`cc-pp-arg-expanded?` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-arg-index` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-arg-paste` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-args-max` | 28 The preprocessor | compiler word (constant, `cc/040-cc-prep.fth`); Macro expansion
`cc-pp-at-spliced?` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-pp-block-comment` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-pp-ca-depth` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Macro expansion
`cc-pp-ca-n` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Macro expansion
`cc-pp-ca-record` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Macro expansion
`cc-pp-ca-recs` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Macro expansion
`cc-pp-ca-start` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Macro expansion
`cc-pp-collect-args` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Macro expansion
`cc-pp-comment-splice?` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-pp-comment` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Conditional groups and the walker
`cc-pp-cond-cap` | 28 The preprocessor | compiler word (constant, `cc/040-cc-prep.fth`); Conditional groups and the walker
`cc-pp-cond-depth` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Conditional groups and the walker
`cc-pp-cond-directive` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#if` and friends
`cc-pp-cond-open` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#if` and friends
`cc-pp-cond-push` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#if` and friends
`cc-pp-cond-top` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Conditional groups and the walker
`cc-pp-cond` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); Conditional groups and the walker
`cc-pp-copy-body` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#define` and `#undef`
`cc-pp-copy-byte-default` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-copy-byte-fwd` | 28 The preprocessor | compiler word (defer, `cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-copy-hash` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#define` and `#undef`
`cc-pp-copy-marked-byte` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-copy-number` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-pp-copy4` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-count-raw-lines` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-current-name` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-defined-name?` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#if` and friends
`cc-pp-defined` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Macro expansion
`cc-pp-drop-splice` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-pp-drop-splices` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-pp-duplicate-args` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Macro expansion
`cc-pp-emit-bytes` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-eval` | 28 The preprocessor | compiler word (defer, `cc/040-cc-prep.fth`); `#if` and friends
`cc-pp-expand-args` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Macro expansion
`cc-pp-expand-call-body` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-expand-call` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-expand-object-body` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-expand-object` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-expand-text` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Macro expansion
`cc-pp-expand-used-args` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-file-base` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-pp-file-cursor` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-pp-file-end` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-pp-file-line` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-pp-file-name-len` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-pp-file-names` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-pp-file-offset` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-pp-file-splice-safe?` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Conditional groups and the walker
`cc-pp-flag-address` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-flags-base` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-flags-init` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-flush-nl` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-pp-from-pool` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The macro table
`cc-pp-ident-work` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-ident` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Conditional groups and the walker
`cc-pp-if-value` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#if` and friends
`cc-pp-in-if` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Macro expansion
`cc-pp-line-blanks` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Parsing C line control
`cc-pp-line-comment` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-pp-line-continuation?` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-pp-line-control` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-pp-line-decimal` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Parsing C line control
`cc-pp-line-escape` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Parsing C line control
`cc-pp-line-filename` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Parsing C line control
`cc-pp-line-hex` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Parsing C line control
`cc-pp-line-map-find` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-line-map-note` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-line-map-on` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-line-map` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-line-name-size` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Parsing C line control
`cc-pp-line-number` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Parsing C line control
`cc-pp-line-octal?` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Parsing C line control
`cc-pp-line-slice` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-pp-line-splice-boundary` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-pp-literal-splices` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-pp-literal` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-pp-location-at` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-pp-location-begin` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-pp-location-cell` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-pp-location-depth` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-pp-location-digit-count` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-location-digits` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-location-enabled` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-pp-location-end` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-pp-location-enter` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-pp-location-filename` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-location-line` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-pp-location-number` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-location-object-root` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-pp-location-rescan` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-pp-location-string-byte` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-logical-name` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-pp-map-resume` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-n-defined` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); Macro expansion
`cc-pp-n-elif` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); `#if` and friends
`cc-pp-n-else` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); `#if` and friends
`cc-pp-n-endif` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); `#if` and friends
`cc-pp-n-if` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); `#if` and friends
`cc-pp-n-ifdef` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); `#if` and friends
`cc-pp-n-ifndef` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); `#if` and friends
`cc-pp-name-file` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The built-in macros and the pass driver
`cc-pp-name-line` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The built-in macros and the pass driver
`cc-pp-need-group` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#if` and friends
`cc-pp-need-name` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-pp-need-rparen` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-pp-out-cap` | 28 The preprocessor | compiler word (constant, `cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-out-code` | 28 The preprocessor | compiler word (constant, `cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-out-flags` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-out-pos` | 28 The preprocessor | compiler word (constant, `cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-out` | 28 The preprocessor | compiler word (constant, `cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-param-addr` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); `#define` and `#undef`
`cc-pp-param-blanks` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#define` and `#undef`
`cc-pp-param-count` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); `#define` and `#undef`
`cc-pp-param-ident` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#define` and `#undef`
`cc-pp-param-len` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); `#define` and `#undef`
`cc-pp-param-splices` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#define` and `#undef`
`cc-pp-param?` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#define` and `#undef`
`cc-pp-params-max` | 28 The preprocessor | compiler word (constant, `cc/040-cc-prep.fth`); `#define` and `#undef`
`cc-pp-paren-ahead?` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Macro expansion
`cc-pp-paste-ahead?` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-paste-bytes` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-pending-nl` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-pp-pool-copy` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The macro table
`cc-pp-put-mode` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-pp-put` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-pp-read-direct-params` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#define` and `#undef`
`cc-pp-read-params` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#define` and `#undef`
`cc-pp-rescan-tail-fwd` | 28 The preprocessor | compiler word (defer, `cc/040-cc-prep.fth`); Macro expansion
`cc-pp-rescan-tail` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-scan-char` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Conditional groups and the walker
`cc-pp-scan-fwd` | 28 The preprocessor | compiler word (defer, `cc/040-cc-prep.fth`); Macro expansion
`cc-pp-scan` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Conditional groups and the walker
`cc-pp-scratch-alloc` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-scratch-cap` | 28 The preprocessor | compiler word (constant, `cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-scratch-top` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-scratch` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-select-flags-default` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-select-flags-fwd` | 28 The preprocessor | compiler word (defer, `cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-select-flags` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-sink-depth` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-sink-pop` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-sink-push` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-sink` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-sinks-cap` | 28 The preprocessor | compiler word (constant, `cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-sinks` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-skip-char` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Conditional groups and the walker
`cc-pp-skipping?` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Conditional groups and the walker
`cc-pp-splice-next` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Conditional groups and the walker
`cc-pp-splice-skip` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-pp-stdin-name` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-string-a` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-string-at?` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-string-byte` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-string-comment` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-string-escape` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-string-peek` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-string-quote` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-string-space` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-string-start` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-string-step` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-string-u` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-stringify` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-sub-argument` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-sub-joining` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-sub-n` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Macro expansion
`cc-pp-sub-raw` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Macro expansion
`cc-pp-sub-recs` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Macro expansion
`cc-pp-substitute-direct` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-substitute-legacy` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Macro expansion
`cc-pp-substitute` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-t0` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The built-in macros and the pass driver
`cc-pp-t1` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The built-in macros and the pass driver
`cc-pp-t2` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The built-in macros and the pass driver
`cc-pp-t512` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The built-in macros and the pass driver
`cc-pp-t64` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The built-in macros and the pass driver
`cc-pp-tail-end` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-tail-name` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-tail-start` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-take-continuation` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-pp-take` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-pp-temp-begin` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-temp-cap` | 28 The preprocessor | compiler word (constant, `cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-temp-end` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-teof` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The built-in macros and the pass driver
`cc-pp-to-pool` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The macro table
`cc-pp-trim-slice` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Unavailable tokens across rescans
`cc-pp-trim` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#define` and `#undef`
`cc-pp-unavailable?` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-pp-whole-punct?` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Conditional groups and the walker
`cc-prep-add-include` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-advance` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-prep-append` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-at-directive?` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Conditional groups and the walker
`cc-prep-at-line-start` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-prep-at?` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-prep-build-path` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-builtins` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The built-in macros and the pass driver
`cc-prep-config-reset` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-copy-path` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-current-path` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-default-workspace` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-direct-depth` | 28 The preprocessor | compiler word (constant, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-direct-workspace` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-direct` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-prep-directive-blanks` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Conditional groups and the walker
`cc-prep-directive-prefix` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Conditional groups and the walker
`cc-prep-directory` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-emit-byte` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The contract, the sink and the scratch area
`cc-prep-eor?` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-prep-file-lens` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-file-paths` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-handle-define` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#define` and `#undef`
`cc-prep-handle-directive-fwd` | 28 The preprocessor | compiler word (defer, `cc/040-cc-prep.fth`); Macro expansion
`cc-prep-handle-directive` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The dispatcher
`cc-prep-handle-include` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Computed include operands
`cc-prep-handle-line` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Parsing C line control
`cc-prep-handle-undef` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#define` and `#undef`
`cc-prep-ident-addr` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-prep-ident-len` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-prep-ident=` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-prep-in-file` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-prep-inc-buf` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-inc-buffer` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-inc-cap` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-inc-depth` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-inc-direct-base` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-inc-direct-cap` | 28 The preprocessor | compiler word (constant, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-inc-end` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); `#include`
`cc-prep-inc-expanded` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); `#include`
`cc-prep-inc-limit` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-inc-mode` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-inc-pool` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-inc-slot-addr` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-inc-slot-cap` | 28 The preprocessor | compiler word (constant, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-inc-slot-count` | 28 The preprocessor | compiler word (constant, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-inc-top` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-include-count` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-include-dirs` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-include-lens` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-include-literal` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#include`
`cc-prep-include-max` | 28 The preprocessor | compiler word (constant, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-isd-save-pos` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Conditional groups and the walker
`cc-prep-line-is-directive?` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Conditional groups and the walker
`cc-prep-load-file` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-load-name-a` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-load-name-u` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-location-builtins` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The built-in macros and the pass driver
`cc-prep-name-define` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The dispatcher
`cc-prep-name-error` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The dispatcher
`cc-prep-name-include` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The dispatcher
`cc-prep-name-line` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The dispatcher
`cc-prep-name-undef` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); The dispatcher
`cc-prep-open-include` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-path-buf` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-path-cap` | 28 The preprocessor | compiler word (constant, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-path-out` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-peek2` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-prep-peek` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-prep-read-ident` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-prep-record-path` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-save-addr` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); `#include`
`cc-prep-save-count` | 28 The preprocessor | compiler word (constant, `cc/040-cc-prep.fth`); `#include`
`cc-prep-save-len` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); `#include`
`cc-prep-save-pos` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); `#include`
`cc-prep-save-slot` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#include`
`cc-prep-skip-blanks` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-prep-skip-to-eol` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-prep-source-len` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-source-name` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-source-path` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-src-addr` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-prep-src-len` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-prep-src-pos` | 28 The preprocessor | compiler word (variable, `cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`cc-prep-target-default` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The built-in macros and the pass driver
`cc-prep-target-fwd` | 28 The preprocessor | compiler word (defer, `cc/040-cc-prep.fth`); The built-in macros and the pass driver
`cc-prep-tests-prefix-len` | 28 The preprocessor | compiler word (constant, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-tests-prefix` | 28 The preprocessor | compiler word (create, `cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-prep-try-open` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); `#include` and its bounded file pool
`cc-preprocess` | 28 The preprocessor | compiler word (`cc/040-cc-prep.fth`); The built-in macros and the pass driver
`cond-done` | 28 The preprocessor | compiler word (constant, `cc/040-cc-prep.fth`); Conditional groups and the walker
`cond-seek` | 28 The preprocessor | compiler word (constant, `cc/040-cc-prep.fth`); Conditional groups and the walker
`cond-take` | 28 The preprocessor | compiler word (constant, `cc/040-cc-prep.fth`); Conditional groups and the walker
`put-count` | 28 The preprocessor | compiler word (constant, `cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`put-drop` | 28 The preprocessor | compiler word (constant, `cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
`put-emit` | 28 The preprocessor | compiler word (constant, `cc/040-cc-prep.fth`); Regions, owed newlines and the byte walkers
Conditional compilation (#if, #ifdef) | 28 The preprocessor | idea; Conditional groups and the walker
Macro table | 28 The preprocessor | idea; The macro table
Macro table (parallel arrays) | 28 The preprocessor | concept (C compiler ideas (Part III)); introduced in old Ch 22
Preprocessor | 28 The preprocessor | idea; The built-in macros and the pass driver
`cc-check-keyword` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); The keyword table
`cc-cspace?` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); Whitespace and comments
`cc-decode-escape` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); Number, identifier, string, char
`cc-esc-a` | 29 The lexer | compiler word (variable, `cc/050-cc-lex.fth`); Number, identifier, string, char
`cc-esc-n` | 29 The lexer | compiler word (variable, `cc/050-cc-lex.fth`); Number, identifier, string, char
`cc-esc-v` | 29 The lexer | compiler word (variable, `cc/050-cc-lex.fth`); Number, identifier, string, char
`cc-hex-digit-val` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); Number, identifier, string, char
`cc-hex-digit?` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); Number, identifier, string, char
`cc-lex-char` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); Number, identifier, string, char
`cc-lex-copy` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); The parser's interface: putback, mark and reset
`cc-lex-extra-default` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); The top-level driver
`cc-lex-extra-fwd` | 29 The lexer | compiler word (defer, `cc/050-cc-lex.fth`); The top-level driver
`cc-lex-ident-or-kw` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); Number, identifier, string, char
`cc-lex-mark` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); The parser's interface: putback, mark and reset
`cc-lex-number-dec` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); Number, identifier, string, char
`cc-lex-number-hex` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); Number, identifier, string, char
`cc-lex-number-oct` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); Number, identifier, string, char
`cc-lex-number` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); Number, identifier, string, char
`cc-lex-punct` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); Punctuation: a fan-out
`cc-lex-reset` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); The parser's interface: putback, mark and reset
`cc-lex-string` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); Number, identifier, string, char
`cc-next-token-keep` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); The parser's interface: putback, mark and reset
`cc-next-token` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); The top-level driver
`cc-octal-digit?` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); Number, identifier, string, char
`cc-peek-char-2` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); The keyword table
`cc-peek-mark` | 29 The lexer | compiler word (create, `cc/050-cc-lex.fth`); The parser's interface: putback, mark and reset
`cc-punct-amp` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); Punctuation: a fan-out
`cc-punct-bang` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); Punctuation: a fan-out
`cc-punct-caret` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); Punctuation: a fan-out
`cc-punct-dot` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); Punctuation: a fan-out
`cc-punct-eq` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); Punctuation: a fan-out
`cc-punct-gt` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); Punctuation: a fan-out
`cc-punct-lt` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); Punctuation: a fan-out
`cc-punct-minus` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); Punctuation: a fan-out
`cc-punct-percent` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); Punctuation: a fan-out
`cc-punct-pipe` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); Punctuation: a fan-out
`cc-punct-plus` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); Punctuation: a fan-out
`cc-punct-slash` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); Punctuation: a fan-out
`cc-punct-star` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); Punctuation: a fan-out
`cc-putback-token` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); The parser's interface: putback, mark and reset
`cc-skip-block-comment` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); Whitespace and comments
`cc-skip-line-comment` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); Whitespace and comments
`cc-skip-ws-and-comments` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); Whitespace and comments
`kw,` | 29 The lexer | compiler word (`cc/050-cc-lex.fth`); The keyword table
`kw-auto` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-bool` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-break` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-case` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-char` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-const` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-continue` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-default` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-do` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-double` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-else` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-enum` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-extern` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-float` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-for` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-goto` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-if` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-inline` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-int` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-long` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-register` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-restrict` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-return` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-short` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-signed` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-sizeof` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-static` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-struct` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-switch` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-table` | 29 The lexer | compiler word (create, `cc/050-cc-lex.fth`); The keyword table
`kw-typedef` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-union` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-unsigned` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-void` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-volatile` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`kw-while` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); The keyword table
`pt-amp-eq` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
`pt-and-and` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
`pt-arrow` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
`pt-bang-eq` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
`pt-caret-eq` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
`pt-ellipsis` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
`pt-eq-eq` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
`pt-ge` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
`pt-le` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
`pt-minus-eq` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
`pt-minus-minus` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
`pt-or-or` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
`pt-percent-eq` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
`pt-pipe-eq` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
`pt-plus-eq` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
`pt-plus-plus` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
`pt-shl-eq` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
`pt-shl` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
`pt-shr-eq` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
`pt-shr` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
`pt-slash-eq` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
`pt-star-eq` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
`tk-chr` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
`tk-eof` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
`tk-float` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
`tk-ident` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
`tk-kw` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
`tk-num` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
`tk-punct` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
`tk-str` | 29 The lexer | compiler word (constant, `cc/050-cc-lex.fth`); Token kinds and punctuation IDs
Keyword table | 29 The lexer | idea; The keyword table
Putback, mark and reset | 29 The lexer | idea; The parser's interface: putback, mark and reset
Compact type encoding | 30 Types and symbols | base kind and pointer depth packed into one type word
Array node | 30 Types and symbols | element type, dimensions, size, alignment and qualifiers kept beside the type
Integer literal classification | 30 Types and symbols | suffix, spelling and magnitude select an integer literal's type
Struct descriptor | 30 Types and symbols | a stable 56-byte header pointing to a separately allocated, growable field table
Symbol table | 30 Types and symbols | parallel columns of name, kind, type and payload for each live declaration
Field qualification | 30 Types and symbols | the newest matching list entry supplies a field's qualifiers
Scope stack | 30 Types and symbols | saved symbol counts mark the rows removed and unlinked on scope exit
Token kinds | 29 The lexer | idea; Token kinds and punctuation IDs
Token kinds (`KW_*`, `ID`, `PUNCT`, `NUM`, `STR`, `CHR`) | 29 The lexer | concept (C compiler ideas (Part III)); introduced in old Ch 23
`cc-ad-align` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-ad-count` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-ad-desc` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-ad-inner` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-ad-qualified` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-ad-size` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-ad-type` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-bootstrap-floatbits` | 30 Types and symbols | compiler word (variable, `cc/060-cc-types.fth`); The one-word type encoding
`cc-field-qualified` | 30 Types and symbols | compiler word (`cc/070-cc-sym.fth`); The symbol-table parallel arrays
`cc-field-set-qualified` | 30 Types and symbols | compiler word (`cc/070-cc-sym.fth`); The symbol-table parallel arrays
`cc-integer-literal-check` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-integer-literal-type` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-integer-suffix-l` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-integer-suffix-letter?` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-integer-suffix-start` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-integer-suffix-u` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-integer-suffix` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-literal-long` | 30 Types and symbols | compiler word (variable, `cc/060-cc-types.fth`); The one-word type encoding
`cc-literal-unsigned` | 30 Types and symbols | compiler word (variable, `cc/060-cc-types.fth`); The one-word type encoding
`cc-qualified-fields` | 30 Types and symbols | compiler word (variable, `cc/070-cc-sym.fth`); The symbol-table parallel arrays
`cc-scope-cap` | 30 Types and symbols | compiler word (constant, `cc/070-cc-sym.fth`); The symbol-table parallel arrays
`cc-scope-depth` | 30 Types and symbols | compiler word (variable, `cc/070-cc-sym.fth`); The symbol-table parallel arrays
`cc-scope-pop` | 30 Types and symbols | compiler word (`cc/070-cc-sym.fth`); Scopes are a stack of integers
`cc-scope-push` | 30 Types and symbols | compiler word (`cc/070-cc-sym.fth`); Scopes are a stack of integers
`cc-scope-stack` | 30 Types and symbols | compiler word (create, `cc/070-cc-sym.fth`); The symbol-table parallel arrays
`cc-sd-align` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sd-alloc` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sd-field-cap` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sd-field-count` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sd-field-rec` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sd-grow-desc` | 30 Types and symbols | compiler word (variable, `cc/060-cc-types.fth`); The one-word type encoding
`cc-sd-grow` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sd-header-bytes` | 30 Types and symbols | compiler word (constant, `cc/060-cc-types.fth`); The one-word type encoding
`cc-sd-initial-fields` | 30 Types and symbols | compiler word (constant, `cc/060-cc-types.fth`); The one-word type encoding
`cc-sd-lp64-max-fields` | 30 Types and symbols | compiler word (constant, `cc/060-cc-types.fth`); The one-word type encoding
`cc-sd-max-fields` | 30 Types and symbols | compiler word (constant, `cc/060-cc-types.fth`); The one-word type encoding
`cc-sd-record-bytes-default` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sd-record-bytes` | 30 Types and symbols | compiler word (defer, `cc/060-cc-types.fth`); The one-word type encoding
`cc-sd-set-align` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sd-set-field-count` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sd-set-total-size` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sd-set-union` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sd-table-cap` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sd-table-moved-default` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sd-table-moved` | 30 Types and symbols | compiler word (defer, `cc/060-cc-types.fth`); The one-word type encoding
`cc-sd-table` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sd-total-size` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sd-union?` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sf-array-inner-default` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sf-array-inner` | 30 Types and symbols | compiler word (defer, `cc/060-cc-types.fth`); The one-word type encoding
`cc-sf-array-len` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sf-desc` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sf-name-addr` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sf-name-len` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sf-offset` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sf-set-array-inner-default` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sf-set-array-inner` | 30 Types and symbols | compiler word (defer, `cc/060-cc-types.fth`); The one-word type encoding
`cc-sf-set-array-len` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sf-set-desc` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sf-set-name-addr` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sf-set-name-len` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sf-set-offset` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sf-set-type` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sf-type` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`cc-sym-add` | 30 Types and symbols | compiler word (`cc/070-cc-sym.fth`); Adding and finding symbols
`cc-sym-addr-fixups-default` | 30 Types and symbols | compiler word (`cc/070-cc-sym.fth`); Adding and finding symbols
`cc-sym-addr-fixups` | 30 Types and symbols | compiler word (defer, `cc/070-cc-sym.fth`); Adding and finding symbols
`cc-sym-array-inner-of` | 30 Types and symbols | compiler word (`cc/070-cc-sym.fth`); Adding and finding symbols
`cc-sym-array-len-of` | 30 Types and symbols | compiler word (`cc/070-cc-sym.fth`); Adding and finding symbols
`cc-sym-bucket-of` | 30 Types and symbols | compiler word (`cc/070-cc-sym.fth`); The symbol-table parallel arrays
`cc-sym-bucket` | 30 Types and symbols | compiler word (create, `cc/070-cc-sym.fth`); The symbol-table parallel arrays
`cc-sym-call-fixups-default` | 30 Types and symbols | compiler word (`cc/070-cc-sym.fth`); Adding and finding symbols
`cc-sym-call-fixups` | 30 Types and symbols | compiler word (defer, `cc/070-cc-sym.fth`); Adding and finding symbols
`cc-sym-cap` | 30 Types and symbols | compiler word (constant, `cc/070-cc-sym.fth`); The symbol-table parallel arrays
`cc-sym-count` | 30 Types and symbols | compiler word (variable, `cc/070-cc-sym.fth`); The symbol-table parallel arrays
`cc-sym-desc` | 30 Types and symbols | compiler word (create, `cc/070-cc-sym.fth`); The symbol-table parallel arrays
`cc-sym-extra2` | 30 Types and symbols | compiler word (create, `cc/070-cc-sym.fth`); The symbol-table parallel arrays
`cc-sym-extra` | 30 Types and symbols | compiler word (create, `cc/070-cc-sym.fth`); The symbol-table parallel arrays
`cc-sym-find-default` | 30 Types and symbols | compiler word (`cc/070-cc-sym.fth`); Adding and finding symbols
`cc-sym-find-tag` | 30 Types and symbols | compiler word (defer, `cc/070-cc-sym.fth`); Adding and finding symbols
`cc-sym-find` | 30 Types and symbols | compiler word (defer, `cc/070-cc-sym.fth`); Adding and finding symbols
`cc-sym-hnext` | 30 Types and symbols | compiler word (create, `cc/070-cc-sym.fth`); The symbol-table parallel arrays
`cc-sym-inner` | 30 Types and symbols | compiler word (create, `cc/070-cc-sym.fth`); The symbol-table parallel arrays
`cc-sym-kind-of` | 30 Types and symbols | compiler word (`cc/070-cc-sym.fth`); Adding and finding symbols
`cc-sym-kind` | 30 Types and symbols | compiler word (create, `cc/070-cc-sym.fth`); The symbol-table parallel arrays
`cc-sym-link` | 30 Types and symbols | compiler word (`cc/070-cc-sym.fth`); The symbol-table parallel arrays
`cc-sym-name-addr` | 30 Types and symbols | compiler word (create, `cc/070-cc-sym.fth`); The symbol-table parallel arrays
`cc-sym-name-len` | 30 Types and symbols | compiler word (create, `cc/070-cc-sym.fth`); The symbol-table parallel arrays
`cc-sym-object-size-of` | 30 Types and symbols | compiler word (`cc/070-cc-sym.fth`); Adding and finding symbols
`cc-sym-qualified` | 30 Types and symbols | compiler word (create, `cc/070-cc-sym.fth`); The symbol-table parallel arrays
`cc-sym-set-array-inner` | 30 Types and symbols | compiler word (`cc/070-cc-sym.fth`); Adding and finding symbols
`cc-sym-set-array-len` | 30 Types and symbols | compiler word (`cc/070-cc-sym.fth`); Adding and finding symbols
`cc-sym-set-object-size` | 30 Types and symbols | compiler word (`cc/070-cc-sym.fth`); Adding and finding symbols
`cc-sym-set-struct-desc` | 30 Types and symbols | compiler word (`cc/070-cc-sym.fth`); Adding and finding symbols
`cc-sym-struct-desc-of` | 30 Types and symbols | compiler word (`cc/070-cc-sym.fth`); Adding and finding symbols
`cc-sym-type-of` | 30 Types and symbols | compiler word (`cc/070-cc-sym.fth`); Adding and finding symbols
`cc-sym-type` | 30 Types and symbols | compiler word (create, `cc/070-cc-sym.fth`); The symbol-table parallel arrays
`cc-sym-unlink` | 30 Types and symbols | compiler word (`cc/070-cc-sym.fth`); The symbol-table parallel arrays
`cc-sym-val-of` | 30 Types and symbols | compiler word (`cc/070-cc-sym.fth`); Adding and finding symbols
`cc-sym-val` | 30 Types and symbols | compiler word (create, `cc/070-cc-sym.fth`); The symbol-table parallel arrays
`cc-target-lp64` | 30 Types and symbols | compiler word (variable, `cc/060-cc-types.fth`); The one-word type encoding
`cc-zalloc` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`sk-enum` | 30 Types and symbols | compiler word (constant, `cc/070-cc-sym.fth`); The symbol-table parallel arrays
`sk-func` | 30 Types and symbols | compiler word (constant, `cc/070-cc-sym.fth`); The symbol-table parallel arrays
`sk-global` | 30 Types and symbols | compiler word (constant, `cc/070-cc-sym.fth`); The symbol-table parallel arrays
`sk-local` | 30 Types and symbols | compiler word (constant, `cc/070-cc-sym.fth`); The symbol-table parallel arrays
`sk-struct` | 30 Types and symbols | compiler word (constant, `cc/070-cc-sym.fth`); The symbol-table parallel arrays
`sk-typedef` | 30 Types and symbols | compiler word (constant, `cc/070-cc-sym.fth`); The symbol-table parallel arrays
`ty-align` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`ty-array` | 30 Types and symbols | compiler word (constant, `cc/060-cc-types.fth`); The one-word type encoding
`ty-base` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`ty-bool` | 30 Types and symbols | compiler word (constant, `cc/060-cc-types.fth`); The one-word type encoding
`ty-char` | 30 Types and symbols | compiler word (constant, `cc/060-cc-types.fth`); The one-word type encoding
`ty-double` | 30 Types and symbols | compiler word (constant, `cc/060-cc-types.fth`); The one-word type encoding
`ty-float` | 30 Types and symbols | compiler word (constant, `cc/060-cc-types.fth`); The one-word type encoding
`ty-func` | 30 Types and symbols | compiler word (constant, `cc/060-cc-types.fth`); The one-word type encoding
`ty-int` | 30 Types and symbols | compiler word (constant, `cc/060-cc-types.fth`); The one-word type encoding
`ty-ldouble` | 30 Types and symbols | compiler word (constant, `cc/060-cc-types.fth`); The one-word type encoding
`ty-llong` | 30 Types and symbols | compiler word (constant, `cc/060-cc-types.fth`); The one-word type encoding
`ty-long-long?` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`ty-long` | 30 Types and symbols | compiler word (constant, `cc/060-cc-types.fth`); The one-word type encoding
`ty-make` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`ty-ptr` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`ty-short` | 30 Types and symbols | compiler word (constant, `cc/060-cc-types.fth`); The one-word type encoding
`ty-size` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`ty-struct` | 30 Types and symbols | compiler word (constant, `cc/060-cc-types.fth`); The one-word type encoding
`ty-uchar` | 30 Types and symbols | compiler word (constant, `cc/060-cc-types.fth`); The one-word type encoding
`ty-uint` | 30 Types and symbols | compiler word (constant, `cc/060-cc-types.fth`); The one-word type encoding
`ty-ullong` | 30 Types and symbols | compiler word (constant, `cc/060-cc-types.fth`); The one-word type encoding
`ty-ulong` | 30 Types and symbols | compiler word (constant, `cc/060-cc-types.fth`); The one-word type encoding
`ty-unsigned?` | 30 Types and symbols | compiler word (`cc/060-cc-types.fth`); The one-word type encoding
`ty-ushort` | 30 Types and symbols | compiler word (constant, `cc/060-cc-types.fth`); The one-word type encoding
`ty-void` | 30 Types and symbols | compiler word (constant, `cc/060-cc-types.fth`); The one-word type encoding
Compact type encoding (one word per type) | 30 Types and symbols | concept (C compiler ideas (Part III)); introduced in old Ch 24
Scope stack | 30 Types and symbols | idea; Scopes are a stack of integers
ELF wrapper | 31 ELF emission and instruction encoding | cc-emit-elf-header lays down a 120-byte ELF header and program header; cc-finalize-elf patches sizes
Register convention (rdi accumulator) | 31 ELF emission and instruction encoding | emitted expressions keep their current result in rdi; binary operations put the right operand in rcx
Frame-pointer local addressing | 31 ELF emission and instruction encoding | locals are rbp-relative slots; cc-emit-local-ea picks the short or long displacement form
System V AMD64 calling convention | 31 ELF emission and instruction encoding | integer and pointer arguments go in rdi rsi rdx rcx r8 r9; results return in rax
rel32 placeholder and patch | 31 ELF emission and instruction encoding | emit a jump with a zero displacement, then cc-patch-rel32-to-here fixes it to the current position
Full-width immediate placeholder | 32 Calls, shims, and globals | movabs rdi with an empty imm64 field, patched once an absolute address is known
Forward-call fixup list | 32 Calls, shims, and globals | arena nodes of patch offset plus old head; walked to patch every call site once the target exists
Escape decoding (string literals) | 32 Calls, shims, and globals | cc-emit-string-bytes emits decoded bytes and a terminating NUL
Stack-buffer pattern | 32 Calls, shims, and globals | a pushed value doubles as a one-byte I/O buffer for write and read
Inline allocator state | 32 Calls, shims, and globals | the calloc shim keeps heap_base and heap_pos after its own ret, reached rip-relative
libc shims | 32 Calls, shims, and globals | small emitted runtime routines (putchar, getchar, fopen, calloc, memcpy...) with narrower behaviour than libc
Global-address fixups | 32 Calls, shims, and globals | parallel columns pair an output patch position with a data or BSS slot until placement
Typed integer emission | 32 Calls, shims, and globals | storage width, value conversion and unsigned operations kept separate
Precedence cascade | 33 Expressions: precedence | one parser per precedence level; each asks the next tighter level for complete operands
Binary fold | 33 Expressions: precedence | save the left operand, parse the right, restore the left, emit the operation
Operator table | 33 Expressions: precedence | rows tie punctuation and compound forms to grammar level, emitter and evaluator
Left associativity | 33 Expressions: precedence | each loop iteration's result becomes the next iteration's left operand
Short-circuit logical AND/OR | 33 Expressions: precedence | conditional branches skip the right operand when the left decides the result
Operand snapshot | 33 Expressions: precedence | saved left-operand metadata survives recursive parsing of the right operand
Lvalue vs rvalue | 34 Expressions: operands and assignment | an operand designating storage becomes a value only through a delayed read
Lvalue tracking | 34 Expressions: operands and assignment | expression metadata keeps storage location, type, qualifiers and array shape
Postfix operators | 34 Expressions: operands and assignment | suffix handlers transform an operand while keeping the metadata later operations need
Assignment (snapshot, recurse, store) | 34 Expressions: operands and assignment | save destination state, parse the source recursively, then emit the store
Constant expressions | 34 Expressions: operands and assignment | evaluate expression syntax at compile time, suppressing arithmetic in unselected arms
Scope stack (push/pop count) | 30 Types and symbols | concept (C compiler ideas (Part III)); introduced in old Ch 24
Struct descriptor | 30 Types and symbols | idea; How types and symbols connect
Struct descriptor (16 + 40·N legacy, 32 + 48·N LP64 bytes) | 30 Types and symbols | concept (C compiler ideas (Part III)); introduced in old Ch 24
Symbol table | 30 Types and symbols | idea; The symbol-table parallel arrays
Symbol table (parallel arrays) | 30 Types and symbols | concept (C compiler ideas (Part III)); introduced in old Ch 24
Type encoding (one word per type) | 30 Types and symbols | idea; The one-word type encoding
`cc-base-vaddr` | 31 ELF emission and instruction encoding | compiler word (constant, `cc/080-cc-elf.fth`); `080-cc-elf.fth`: the ELF wrapper
`cc-bss-size` | 31 ELF emission and instruction encoding | compiler word (variable, `cc/080-cc-elf.fth`); `080-cc-elf.fth`: the ELF wrapper
`cc-disp8-from-slot` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Local-variable addressing
`cc-emit-add-rdi-imm32` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Local-variable addressing
`cc-emit-add-rdi-rcx` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Register-to-register moves, ALU, and prologue/epilogue
`cc-emit-call-rax` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Local-variable addressing
`cc-emit-call-rel32-placeholder` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Branches and `rel32` placeholders
`cc-emit-cmp-eq` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Comparisons and conditional set
`cc-emit-cmp-ge` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Comparisons and conditional set
`cc-emit-cmp-gt` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Comparisons and conditional set
`cc-emit-cmp-le` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Comparisons and conditional set
`cc-emit-cmp-lt` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Comparisons and conditional set
`cc-emit-cmp-ne` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Comparisons and conditional set
`cc-emit-cmp-rbx-imm32` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Register-to-register moves, ALU, and prologue/epilogue
`cc-emit-cmp-set` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Comparisons and conditional set
`cc-emit-elf-header` | 31 ELF emission and instruction encoding | compiler word (`cc/080-cc-elf.fth`); `080-cc-elf.fth`: the ELF wrapper
`cc-emit-epilogue` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Register-to-register moves, ALU, and prologue/epilogue
`cc-emit-idiv-quotient` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Register-to-register moves, ALU, and prologue/epilogue
`cc-emit-idiv-remainder` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Register-to-register moves, ALU, and prologue/epilogue
`cc-emit-imul-rdi-rcx` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Register-to-register moves, ALU, and prologue/epilogue
`cc-emit-jmp-rel32-placeholder` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Branches and `rel32` placeholders
`cc-emit-jnz-rel32-placeholder` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Branches and `rel32` placeholders
`cc-emit-jz-rel32-placeholder` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Branches and `rel32` placeholders
`cc-emit-lea-rdi-local` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Local-variable addressing
`cc-emit-load-byte-via-rdi` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Local-variable addressing
`cc-emit-load-local-into-rax` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Local-variable addressing
`cc-emit-load-local` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Local-variable addressing
`cc-emit-load-via-rdi` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Local-variable addressing
`cc-emit-local-ea` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Local-variable addressing
`cc-emit-mov-rax-rdi` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Register-to-register moves, ALU, and prologue/epilogue
`cc-emit-mov-rbx-rdi` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Register-to-register moves, ALU, and prologue/epilogue
`cc-emit-mov-rcx-rdi` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Register-to-register moves, ALU, and prologue/epilogue
`cc-emit-mov-rdi-imm32` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Stack ops and immediate loads
`cc-emit-mov-rdi-rax` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Register-to-register moves, ALU, and prologue/epilogue
`cc-emit-pop-r8` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Stack ops and immediate loads
`cc-emit-pop-r9` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Stack ops and immediate loads
`cc-emit-pop-rbx` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Stack ops and immediate loads
`cc-emit-pop-rcx` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Stack ops and immediate loads
`cc-emit-pop-rdi` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Stack ops and immediate loads
`cc-emit-pop-rdx` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Stack ops and immediate loads
`cc-emit-pop-rsi` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Stack ops and immediate loads
`cc-emit-prologue` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Register-to-register moves, ALU, and prologue/epilogue
`cc-emit-push-rbx` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Stack ops and immediate loads
`cc-emit-push-rdi` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Stack ops and immediate loads
`cc-emit-restore-callee-fwd` | 31 ELF emission and instruction encoding | compiler word (defer, `cc/090-cc-emit.fth`); Register-to-register moves, ALU, and prologue/epilogue
`cc-emit-restore-noop` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Register-to-register moves, ALU, and prologue/epilogue
`cc-emit-shl-rdi-3` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Local-variable addressing
`cc-emit-shl-rdi-imm8` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Local-variable addressing
`cc-emit-store-byte-via-rcx` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Local-variable addressing
`cc-emit-store-local-from-r8` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Local-variable addressing
`cc-emit-store-local-from-r9` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Local-variable addressing
`cc-emit-store-local-from-rcx` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Local-variable addressing
`cc-emit-store-local-from-rdx` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Local-variable addressing
`cc-emit-store-local-from-rsi` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Local-variable addressing
`cc-emit-store-local` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Local-variable addressing
`cc-emit-store-via-rcx` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Local-variable addressing
`cc-emit-sub-rdi-rcx` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Register-to-register moves, ALU, and prologue/epilogue
`cc-emit-test-rdi` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Branches and `rel32` placeholders
`cc-emit-track-noop` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Stack ops and immediate loads
`cc-emit-track-pop-fwd` | 31 ELF emission and instruction encoding | compiler word (defer, `cc/090-cc-emit.fth`); Stack ops and immediate loads
`cc-emit-track-push-fwd` | 31 ELF emission and instruction encoding | compiler word (defer, `cc/090-cc-emit.fth`); Stack ops and immediate loads
`cc-emit-xor-rax-rax` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Register-to-register moves, ALU, and prologue/epilogue
`cc-emit-zx-byte-rdi` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Local-variable addressing
`cc-entry-vaddr` | 31 ELF emission and instruction encoding | compiler word (constant, `cc/080-cc-elf.fth`); `080-cc-elf.fth`: the ELF wrapper
`cc-filesz-offset` | 31 ELF emission and instruction encoding | compiler word (constant, `cc/080-cc-elf.fth`); `080-cc-elf.fth`: the ELF wrapper
`cc-finalize-elf` | 31 ELF emission and instruction encoding | compiler word (`cc/080-cc-elf.fth`); `080-cc-elf.fth`: the ELF wrapper
`cc-here-vaddr` | 31 ELF emission and instruction encoding | compiler word (`cc/080-cc-elf.fth`); `080-cc-elf.fth`: the ELF wrapper
`cc-memsz-offset` | 31 ELF emission and instruction encoding | compiler word (constant, `cc/080-cc-elf.fth`); `080-cc-elf.fth`: the ELF wrapper
`cc-patch-rel32-to-here` | 31 ELF emission and instruction encoding | compiler word (`cc/090-cc-emit.fth`); Branches and `rel32` placeholders
Frame pointer `rbp` + local-at-`-8n` addressing | 31 ELF emission and instruction encoding | concept (C compiler ideas (Part III)); introduced in old Ch 25
Local-variable addressing (rbp - 8n) | 31 ELF emission and instruction encoding | idea; Local-variable addressing
Register convention (rdi accumulator) | 31 ELF emission and instruction encoding | idea; `090-cc-emit.fth`, part 1: register convention
System V AMD64 calling convention | 31 ELF emission and instruction encoding | concept (C compiler ideas (Part III)); introduced in old Ch 25
`cc-add-fixup-to-list` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); `movabs rdi, imm64` and the forward-call fixup list
`cc-bss-alloc` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); File-scope globals and deferred vaddr fixups
`cc-bss-base-vaddr` | 32 Calls, shims, and globals | compiler word (variable, `cc/090-cc-emit.fth`); File-scope globals and deferred vaddr fixups
`cc-bss-cap` | 32 Calls, shims, and globals | compiler word (constant, `cc/090-cc-emit.fth`); File-scope globals and deferred vaddr fixups
`cc-bss-flag` | 32 Calls, shims, and globals | compiler word (constant, `cc/090-cc-emit.fth`); File-scope globals and deferred vaddr fixups
`cc-bss-pos` | 32 Calls, shims, and globals | compiler word (variable, `cc/090-cc-emit.fth`); File-scope globals and deferred vaddr fixups
`cc-emit-and-rdi-rcx` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); Bitwise, shifts, inc/dec, and unary `!`
`cc-emit-calloc-shim` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); The libc shims: write/read/open/close/mmap
`cc-emit-cmp-uge` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); LP64 integer encoders
`cc-emit-cmp-ugt` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); LP64 integer encoders
`cc-emit-cmp-ule` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); LP64 integer encoders
`cc-emit-cmp-ult` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); LP64 integer encoders
`cc-emit-convert-rcx` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); LP64 integer encoders
`cc-emit-convert-rdi` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); LP64 integer encoders
`cc-emit-convert-right-default` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); LP64 integer encoders
`cc-emit-convert-right` | 32 Calls, shims, and globals | compiler word (defer, `cc/090-cc-emit.fth`); LP64 integer encoders
`cc-emit-convert-value-default` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); LP64 integer encoders
`cc-emit-convert-value` | 32 Calls, shims, and globals | compiler word (defer, `cc/090-cc-emit.fth`); LP64 integer encoders
`cc-emit-dec-mem-local` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); Bitwise, shifts, inc/dec, and unary `!`
`cc-emit-dec-via-rcx` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); Bitwise, shifts, inc/dec, and unary `!`
`cc-emit-exit-shim` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); The libc shims: write/read/open/close/mmap
`cc-emit-fclose-shim` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); The libc shims: write/read/open/close/mmap
`cc-emit-fopen-shim` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); The libc shims: write/read/open/close/mmap
`cc-emit-fputc-shim` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); The libc shims: write/read/open/close/mmap
`cc-emit-fputs-shim` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); The libc shims: write/read/open/close/mmap
`cc-emit-fread-shim` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); The libc shims: write/read/open/close/mmap
`cc-emit-free-shim` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); The libc shims: write/read/open/close/mmap
`cc-emit-fwrite-shim` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); The libc shims: write/read/open/close/mmap
`cc-emit-getchar-shim` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); The libc shims: write/read/open/close/mmap
`cc-emit-global-ref` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); File-scope globals and deferred vaddr fixups
`cc-emit-inc-mem-local` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); Bitwise, shifts, inc/dec, and unary `!`
`cc-emit-inc-via-rcx` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); Bitwise, shifts, inc/dec, and unary `!`
`cc-emit-load-local-typed` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); LP64 integer encoders
`cc-emit-load-typed-via-rdi` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); LP64 integer encoders
`cc-emit-load-via-rcx` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); Bitwise, shifts, inc/dec, and unary `!`
`cc-emit-malloc-shim` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); The libc shims: write/read/open/close/mmap
`cc-emit-memcpy-shim` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); The libc shims: write/read/open/close/mmap
`cc-emit-mov-rdi-int` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); `movabs rdi, imm64` and the forward-call fixup list
`cc-emit-movabs-rdi-imm64-placeholder` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); `movabs rdi, imm64` and the forward-call fixup list
`cc-emit-movabs-rdi-imm64` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); `movabs rdi, imm64` and the forward-call fixup list
`cc-emit-neg-rdi` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); Bitwise, shifts, inc/dec, and unary `!`
`cc-emit-not-rdi` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); Bitwise, shifts, inc/dec, and unary `!`
`cc-emit-not-zero-flag` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); Bitwise, shifts, inc/dec, and unary `!`
`cc-emit-or-rdi-rcx` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); Bitwise, shifts, inc/dec, and unary `!`
`cc-emit-putchar-shim` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); The libc shims: write/read/open/close/mmap
`cc-emit-sar-rdi-cl` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); Bitwise, shifts, inc/dec, and unary `!`
`cc-emit-shl-rdi-cl` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); Bitwise, shifts, inc/dec, and unary `!`
`cc-emit-shr-rdi-cl` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); LP64 integer encoders
`cc-emit-store-local-typed` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); LP64 integer encoders
`cc-emit-store-typed-via-rcx` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); LP64 integer encoders
`cc-emit-string-bytes` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); String-literal bytes with C-escape decoding
`cc-emit-strlen-shim` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); The libc shims: write/read/open/close/mmap
`cc-emit-strrchr-shim` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); The libc shims: write/read/open/close/mmap
`cc-emit-syscall-shim` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); The libc shims: write/read/open/close/mmap
`cc-emit-type-check-fwd` | 32 Calls, shims, and globals | compiler word (defer, `cc/090-cc-emit.fth`); LP64 integer encoders
`cc-emit-type-check-noop` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); LP64 integer encoders
`cc-emit-udiv-quotient` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); LP64 integer encoders
`cc-emit-udiv-remainder` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); LP64 integer encoders
`cc-emit-xor-rdi-rcx` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); Bitwise, shifts, inc/dec, and unary `!`
`cc-gfixup-add` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); File-scope globals and deferred vaddr fixups
`cc-gfixup-cap` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); File-scope globals and deferred vaddr fixups
`cc-gfixup-count` | 32 Calls, shims, and globals | compiler word (variable, `cc/090-cc-emit.fth`); File-scope globals and deferred vaddr fixups
`cc-gfixup-default-cap` | 32 Calls, shims, and globals | compiler word (constant, `cc/090-cc-emit.fth`); File-scope globals and deferred vaddr fixups
`cc-gfixup-default-out-pos` | 32 Calls, shims, and globals | compiler word (create, `cc/090-cc-emit.fth`); File-scope globals and deferred vaddr fixups
`cc-gfixup-default-slot` | 32 Calls, shims, and globals | compiler word (create, `cc/090-cc-emit.fth`); File-scope globals and deferred vaddr fixups
`cc-gfixup-default-workspace` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); File-scope globals and deferred vaddr fixups
`cc-gfixup-direct-base` | 32 Calls, shims, and globals | compiler word (variable, `cc/090-cc-emit.fth`); File-scope globals and deferred vaddr fixups
`cc-gfixup-direct-cap` | 32 Calls, shims, and globals | compiler word (constant, `cc/090-cc-emit.fth`); File-scope globals and deferred vaddr fixups
`cc-gfixup-direct-workspace` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); File-scope globals and deferred vaddr fixups
`cc-gfixup-limit` | 32 Calls, shims, and globals | compiler word (variable, `cc/090-cc-emit.fth`); File-scope globals and deferred vaddr fixups
`cc-gfixup-out-pos-buffer` | 32 Calls, shims, and globals | compiler word (variable, `cc/090-cc-emit.fth`); File-scope globals and deferred vaddr fixups
`cc-gfixup-out-pos` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); File-scope globals and deferred vaddr fixups
`cc-gfixup-slot-buffer` | 32 Calls, shims, and globals | compiler word (variable, `cc/090-cc-emit.fth`); File-scope globals and deferred vaddr fixups
`cc-gfixup-slot` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); File-scope globals and deferred vaddr fixups
`cc-globals-alloc` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); File-scope globals and deferred vaddr fixups
`cc-globals-base-vaddr` | 32 Calls, shims, and globals | compiler word (variable, `cc/090-cc-emit.fth`); File-scope globals and deferred vaddr fixups
`cc-globals-buf` | 32 Calls, shims, and globals | compiler word (create, `cc/090-cc-emit.fth`); File-scope globals and deferred vaddr fixups
`cc-globals-cap` | 32 Calls, shims, and globals | compiler word (constant, `cc/090-cc-emit.fth`); File-scope globals and deferred vaddr fixups
`cc-globals-init` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); File-scope globals and deferred vaddr fixups
`cc-globals-pos` | 32 Calls, shims, and globals | compiler word (variable, `cc/090-cc-emit.fth`); File-scope globals and deferred vaddr fixups
`cc-globals-store-8le` | 32 Calls, shims, and globals | compiler word (`cc/090-cc-emit.fth`); File-scope globals and deferred vaddr fixups
Escape decoding (string literals) | 32 Calls, shims, and globals | idea; String-literal bytes with C-escape decoding
Forward-call fixup list | 32 Calls, shims, and globals | idea; `movabs rdi, imm64` and the forward-call fixup list
Global-address fixups | 32 Calls, shims, and globals | idea; File-scope globals and deferred vaddr fixups
libc shims | 32 Calls, shims, and globals | idea; The libc shims: write/read/open/close/mmap
`bo-compound` | 33 Expressions: precedence | compiler word (constant, `cc/100-cc-expr.fth`); The operator table
`bo-emitter` | 33 Expressions: precedence | compiler word (constant, `cc/100-cc-expr.fth`); The operator table
`bo-eval` | 33 Expressions: precedence | compiler word (constant, `cc/100-cc-expr.fth`); The operator table
`bo-level` | 33 Expressions: precedence | compiler word (constant, `cc/100-cc-expr.fth`); The operator table
`bo-op` | 33 Expressions: precedence | compiler word (constant, `cc/100-cc-expr.fth`); The operator table
`bo-size` | 33 Expressions: precedence | compiler word (constant, `cc/100-cc-expr.fth`); The operator table
`cc-abs` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-array-binop-default` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-array-binop-fwd` | 33 Expressions: precedence | compiler word (defer, `cc/100-cc-expr.fth`); The operator table
`cc-array-compound-default` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-array-compound-fwd` | 33 Expressions: precedence | compiler word (defer, `cc/100-cc-expr.fth`); The operator table
`cc-array-ternary-default` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-array-ternary-fwd` | 33 Expressions: precedence | compiler word (defer, `cc/100-cc-expr.fth`); The operator table
`cc-binop,` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-binop-apply` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-binop-row` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-binop?` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-binops` | 33 Expressions: precedence | compiler word (create, `cc/100-cc-expr.fth`); The operator table
`cc-check-static-init` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); Forward references for mutual recursion
`cc-div` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-divisor` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-eq` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-expr-common-desc` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-expr-common-inner` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-expr-common-type-default` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-expr-common-type` | 33 Expressions: precedence | compiler word (defer, `cc/100-cc-expr.fth`); The operator table
`cc-expr-common` | 33 Expressions: precedence | compiler word (variable, `cc/100-cc-expr.fth`); The operator table
`cc-expr-left-desc` | 33 Expressions: precedence | compiler word (variable, `cc/100-cc-expr.fth`); The operator table
`cc-expr-left-inner` | 33 Expressions: precedence | compiler word (variable, `cc/100-cc-expr.fth`); The operator table
`cc-expr-left-null` | 33 Expressions: precedence | compiler word (variable, `cc/100-cc-expr.fth`); The operator table
`cc-expr-left-qualified` | 33 Expressions: precedence | compiler word (variable, `cc/100-cc-expr.fth`); The operator table
`cc-expr-left-step` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-expr-left-type` | 33 Expressions: precedence | compiler word (variable, `cc/100-cc-expr.fth`); The operator table
`cc-expr-long-long-common` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-expr-op-row` | 33 Expressions: precedence | compiler word (variable, `cc/100-cc-expr.fth`); The operator table
`cc-expr-promote` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-expr-right-desc` | 33 Expressions: precedence | compiler word (variable, `cc/100-cc-expr.fth`); The operator table
`cc-expr-right-inner` | 33 Expressions: precedence | compiler word (variable, `cc/100-cc-expr.fth`); The operator table
`cc-expr-right-null` | 33 Expressions: precedence | compiler word (variable, `cc/100-cc-expr.fth`); The operator table
`cc-expr-right-qualified` | 33 Expressions: precedence | compiler word (variable, `cc/100-cc-expr.fth`); The operator table
`cc-expr-right-step` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-expr-right-type` | 33 Expressions: precedence | compiler word (variable, `cc/100-cc-expr.fth`); The operator table
`cc-expr-save-native-types` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-expr-save-types` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-expr-unevaluated` | 33 Expressions: precedence | compiler word (variable, `cc/100-cc-expr.fth`); Forward references for mutual recursion
`cc-flag` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-ge` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-gt` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-invert` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-le` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-lt` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-mod` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-native-binop-apply` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-native-binop-emit-default` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-native-binop-emit` | 33 Expressions: precedence | compiler word (defer, `cc/100-cc-expr.fth`); The operator table
`cc-native-static-init` | 33 Expressions: precedence | compiler word (variable, `cc/100-cc-expr.fth`); Forward references for mutual recursion
`cc-ne` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-negate` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-parse-add` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); `cc-parse-add`: just like `mul`, looser
`cc-parse-assign-fwd` | 33 Expressions: precedence | compiler word (defer, `cc/100-cc-expr.fth`); Forward references for mutual recursion
`cc-parse-bit-and` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The bitwise trio
`cc-parse-bit-or` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The bitwise trio
`cc-parse-bit-xor` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The bitwise trio
`cc-parse-comma-fwd` | 33 Expressions: precedence | compiler word (defer, `cc/100-cc-expr.fth`); Forward references for mutual recursion
`cc-parse-const-fwd` | 33 Expressions: precedence | compiler word (defer, `cc/100-cc-expr.fth`); Forward references for mutual recursion
`cc-parse-eq` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); Relational and equality
`cc-parse-expr-fwd` | 33 Expressions: precedence | compiler word (defer, `cc/100-cc-expr.fth`); Forward references for mutual recursion
`cc-parse-log-and` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); Short-circuit `&&` and `\|\|`
`cc-parse-log-or` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); Short-circuit `&&` and `\|\|`
`cc-parse-mul` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The level template: `cc-parse-mul`
`cc-parse-rel` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); Relational and equality
`cc-parse-shift` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); Shifts: between relational and additive
`cc-parse-unary-fwd` | 33 Expressions: precedence | compiler word (defer, `cc/100-cc-expr.fth`); Forward references for mutual recursion
`cc-pow2` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-sar` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-shl` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`cc-sizeof-type-fwd` | 33 Expressions: precedence | compiler word (defer, `cc/100-cc-expr.fth`); Forward references for mutual recursion
`cc-sizeof-type-start-fwd` | 33 Expressions: precedence | compiler word (defer, `cc/100-cc-expr.fth`); Forward references for mutual recursion
`cc-tok-kw?` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); One token of putback
`cc-tok-punct?` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); One token of putback
`cc-try-cast-fwd` | 33 Expressions: precedence | compiler word (defer, `cc/100-cc-expr.fth`); Forward references for mutual recursion
`cc-xor` | 33 Expressions: precedence | compiler word (`cc/100-cc-expr.fth`); The operator table
`level-add` | 33 Expressions: precedence | compiler word (constant, `cc/100-cc-expr.fth`); The operator table
`level-bit-and` | 33 Expressions: precedence | compiler word (constant, `cc/100-cc-expr.fth`); The operator table
`level-bit-or` | 33 Expressions: precedence | compiler word (constant, `cc/100-cc-expr.fth`); The operator table
`level-bit-xor` | 33 Expressions: precedence | compiler word (constant, `cc/100-cc-expr.fth`); The operator table
`level-eq` | 33 Expressions: precedence | compiler word (constant, `cc/100-cc-expr.fth`); The operator table
`level-mul` | 33 Expressions: precedence | compiler word (constant, `cc/100-cc-expr.fth`); The operator table
`level-rel` | 33 Expressions: precedence | compiler word (constant, `cc/100-cc-expr.fth`); The operator table
`level-shift` | 33 Expressions: precedence | compiler word (constant, `cc/100-cc-expr.fth`); The operator table
Left associativity | 33 Expressions: precedence | idea; `cc-parse-add`: just like `mul`, looser
Operator table | 33 Expressions: precedence | idea; The operator table
Precedence cascade | 33 Expressions: precedence | concept (C compiler ideas (Part III)); introduced in old Ch 27
Short-circuit && and \|\| | 33 Expressions: precedence | idea; Short-circuit `&&` and `\|\|`
`cc-aggregate-assignment-default` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Assignment: snapshot, recurse, store
`cc-aggregate-assignment-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); Assignment: snapshot, recurse, store
`cc-aggregate-compound-default` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Assignment: snapshot, recurse, store
`cc-aggregate-compound-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); Assignment: snapshot, recurse, store
`cc-aggregate-ternary-default` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-aggregate-ternary-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-apply-compound-op` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Assignment: snapshot, recurse, store
`cc-array-address-default` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); `cc-parse-unary`: prefix operators
`cc-array-address-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); `cc-parse-unary`: prefix operators
`cc-array-decay-default` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-array-decay-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-assign-desc` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); Assignment: snapshot, recurse, store
`cc-assign-field` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); Assignment: snapshot, recurse, store
`cc-assign-op?` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Assignment: snapshot, recurse, store
`cc-assign-op` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); Assignment: snapshot, recurse, store
`cc-assign-qualified` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); Assignment: snapshot, recurse, store
`cc-assign-type` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); Assignment: snapshot, recurse, store
`cc-change-check-default` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); The postfix operators
`cc-change-check-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); The postfix operators
`cc-change-delta` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); The postfix operators
`cc-change-desc` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); The postfix operators
`cc-change-field` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); The postfix operators
`cc-change-postfix` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); The postfix operators
`cc-change-qualified` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); The postfix operators
`cc-change-type` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); The postfix operators
`cc-change-value-default` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); The postfix operators
`cc-change-value-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); The postfix operators
`cc-char-ptr?` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-const-address-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); Constant expressions
`cc-const-ident-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); Constant expressions
`cc-const-string-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); Constant expressions
`cc-const-unsupported` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Constant expressions
`cc-cx-and` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Constant expressions
`cc-cx-binary` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Constant expressions
`cc-cx-comparison` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); Constant expressions
`cc-cx-eval` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Constant expressions
`cc-cx-lt` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Constant expressions
`cc-cx-op` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); Constant expressions
`cc-cx-operand` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Constant expressions
`cc-cx-or` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Constant expressions
`cc-cx-pp` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); Constant expressions
`cc-cx-save` | 34 Expressions: operands and assignment | compiler word (create, `cc/100-cc-expr.fth`); Constant expressions
`cc-cx-skip` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); Constant expressions
`cc-cx-typed?` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Constant expressions
`cc-cx-ult` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Constant expressions
`cc-cx-unary` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Constant expressions
`cc-cx-unsigned` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); Constant expressions
`cc-deref-pending?` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-emit-load-via-rdi-or-byte` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Assignment: snapshot, recurse, store
`cc-emit-materialize` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-emit-scale-rcx` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-emit-scale-rdi` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-expr-pointee-size` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-expr-pointee-type` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-expr-symbol-desc` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-expr-type-size` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-ff-desc` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); Struct-field lookup
`cc-ff-needle-addr` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); Struct-field lookup
`cc-ff-needle-len` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); Struct-field lookup
`cc-ff-result-array` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); Struct-field lookup
`cc-ff-result-desc` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); Struct-field lookup
`cc-ff-result-record` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); Struct-field lookup
`cc-ff-result-type` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); Struct-field lookup
`cc-field-load-default` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-field-load-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-field-store-default` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-field-store-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-field-use-default` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-field-use-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-field-value-type-default` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-field-value-type-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-find-field` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Struct-field lookup
`cc-index-base-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); The postfix operators
`cc-last-expr-array-inner` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-last-expr-array-len` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-last-expr-null` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-last-expr-qualified` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-last-expr-type` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-last-field-rec` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-last-ident-slot` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-last-lvalue-kind` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-last-struct-desc` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-mark-deref` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-mark-int-value` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-mark-local-lvalue` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-mark-not-lvalue` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-mark-typed-deref` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-mark-typed-value` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-mark` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-member-base-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); The postfix operators
`cc-name-alone?` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); `cc-parse-unary`: prefix operators
`cc-native-call-qualified-default` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Identifiers, calls, and subscripts
`cc-native-call-qualified-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); Identifiers, calls, and subscripts
`cc-native-inc-dec` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); The postfix operators
`cc-native-intrinsic-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); Identifiers, calls, and subscripts
`cc-native-intrinsic-noop` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Identifiers, calls, and subscripts
`cc-native-local-load-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); Locals
`cc-native-sizeof-expr-size` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); `cc-parse-unary`: prefix operators
`cc-native-sizeof` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); `cc-parse-unary`: prefix operators
`cc-native-string-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); String literals
`cc-native-unknown-ident-default` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Identifiers, calls, and subscripts
`cc-native-unknown-ident-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); Identifiers, calls, and subscripts
`cc-opaque-scalar-default` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-opaque-scalar-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-parse-array-index` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Array indexing helper
`cc-parse-assign` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Assignment: snapshot, recurse, store
`cc-parse-comma` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); The top-level driver
`cc-parse-const-default` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Constant expressions
`cc-parse-const` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); Constant expressions
`cc-parse-expr` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); The top-level driver
`cc-parse-func-ref` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); A function name as a value
`cc-parse-global-ref` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Globals
`cc-parse-ident` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Identifiers, calls, and subscripts
`cc-parse-local-ref` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Locals
`cc-parse-native-assign` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Assignment: snapshot, recurse, store
`cc-parse-native-string-literal` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); String literals
`cc-parse-operand` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); The top: operand, then postfix loop
`cc-parse-paren` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Parentheses
`cc-parse-postfix-field` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); The postfix operators
`cc-parse-postfix-inc-dec` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); The postfix operators
`cc-parse-postfix-index` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); The postfix operators
`cc-parse-postfix-ops` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); The top: operand, then postfix loop
`cc-parse-prefix-inc-dec` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); `cc-parse-unary`: prefix operators
`cc-parse-primary` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); The top: operand, then postfix loop
`cc-parse-sizeof` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); `cc-parse-unary`: prefix operators
`cc-parse-static-const-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); Constant expressions
`cc-parse-string-literal` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); String literals
`cc-parse-ternary` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Ternary
`cc-parse-unary` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); `cc-parse-unary`: prefix operators
`cc-postfix-base-default` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); The postfix operators
`cc-postfix-op?` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); The top: operand, then postfix loop
`cc-pp-eval-text` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Constant expressions
`cc-sizeof-bytes` | 34 Expressions: operands and assignment | compiler word (variable, `cc/100-cc-expr.fth`); `cc-parse-unary`: prefix operators
`cc-sizeof-count-stars-add` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); `cc-parse-unary`: prefix operators
`cc-sizeof-type-size-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); `cc-parse-unary`: prefix operators
`cc-unary-type` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-value-complement-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-value-init-default` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-value-init-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-value-integer-use-default` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-value-integer-use-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-value-literal-default` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-value-literal-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-value-negate-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-value-not-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-value-plus-default` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-value-plus-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-value-shape-default` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-value-shape-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-value-ternary-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-value-ternary-noop` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-value-ternary-split-default` | 34 Expressions: operands and assignment | compiler word (`cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-value-ternary-split-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`cc-value-test-fwd` | 34 Expressions: operands and assignment | compiler word (defer, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`lv-deref-byte` | 34 Expressions: operands and assignment | compiler word (constant, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`lv-deref` | 34 Expressions: operands and assignment | compiler word (constant, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`lv-local` | 34 Expressions: operands and assignment | compiler word (constant, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`lv-temporary` | 34 Expressions: operands and assignment | compiler word (constant, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
`lv-value` | 34 Expressions: operands and assignment | compiler word (constant, `cc/100-cc-expr.fth`); Lvalue tracking: four globals, four kinds
Assignment (snapshot, recurse, store) | 34 Expressions: operands and assignment | idea; Assignment: snapshot, recurse, store
Constant expressions | 34 Expressions: operands and assignment | idea; Constant expressions
Consume-and-check | 35 Declarations and storage | advance to a token, reject the wrong kind, then test its payload
Struct tag pre-registration | 35 Declarations and storage | register an empty descriptor before parsing fields so self-references resolve
Declarator-local pointer depth | 35 Declarations and storage | each name adds its own stars to the inherited pointer depth
Static local storage | 35 Declarations and storage | a locally scoped name that refers to persistent global storage
Cast policy separation | 35 Declarations and storage | type acceptance, value conversion and null provenance use separate hooks
Break/continue fixup lists | 36 Statements and control flow | pending jumps grouped by enclosing construct and destination, patched when the target is known
for-step rewind | 36 Statements and control flow | the step is skipped on first reading; after the body the lexer rewinds to it so its code follows the body
Labels and goto | 36 Statements and control flow | named destinations via function-local label entries plus pending jumps
Native goto adjustment paths | 36 Statements and control flow | forward jumps resolved through code that balances lexical switch depth
Function pre-registration | 37 Functions and translation units | the function's name is published before its local scope, so recursion works and the name survives the body
Prototype reuse | 37 Functions and translation units | a later prototype keeps the existing function entry and its pending calls
Global redeclaration reuse | 37 Functions and translation units | repeated scalar declarations share one storage slot and initializer
Late shim selection | 37 Functions and translation units | runtime shim bodies are emitted only for names that still have pending references
Entry stub | 37 Functions and translation units | emitted start code that calls main and passes its result to exit
Lvalue tracking | 34 Expressions: operands and assignment | idea; Lvalue tracking: four globals, four kinds
Lvalue vs rvalue | 34 Expressions: operands and assignment | concept (C compiler ideas (Part III)); introduced in old Ch 28
Postfix operators | 34 Expressions: operands and assignment | idea; The postfix operators
`cc-call-main-patch` | 35 Declarations and storage | compiler word (variable, `cc/110-cc-decl.fth`); File header and bookkeeping
`cc-cast-desc` | 35 Declarations and storage | compiler word (variable, `cc/110-cc-decl.fth`); Type names and casts
`cc-cast-null-default` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Type names and casts
`cc-cast-null-fwd` | 35 Declarations and storage | compiler word (defer, `cc/110-cc-decl.fth`); Type names and casts
`cc-cast-types-default` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Type names and casts
`cc-cast-types-fwd` | 35 Declarations and storage | compiler word (defer, `cc/110-cc-decl.fth`); Type names and casts
`cc-cast-value-default` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Type names and casts
`cc-cast-value-fwd` | 35 Declarations and storage | compiler word (defer, `cc/110-cc-decl.fth`); Type names and casts
`cc-count-stars` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Expectation helpers and ignored specifiers
`cc-decl-base` | 35 Declarations and storage | compiler word (variable, `cc/110-cc-decl.fth`); Function pointers and the declaration engine
`cc-decl-extern` | 35 Declarations and storage | compiler word (variable, `cc/110-cc-decl.fth`); Expectation helpers and ignored specifiers
`cc-decl-static` | 35 Declarations and storage | compiler word (variable, `cc/110-cc-decl.fth`); Expectation helpers and ignored specifiers
`cc-decl-storage` | 35 Declarations and storage | compiler word (variable, `cc/110-cc-decl.fth`); Expectation helpers and ignored specifiers
`cc-emit-switch-unwind` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); `cc-parse-return`
`cc-expect-ident` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Expectation helpers and ignored specifiers
`cc-expect-kw-id` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Expectation helpers and ignored specifiers
`cc-expect-punct-c` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Expectation helpers and ignored specifiers
`cc-fn-add-slots` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); File header and bookkeeping
`cc-fn-local-count` | 35 Declarations and storage | compiler word (variable, `cc/110-cc-decl.fth`); File header and bookkeeping
`cc-frame-slots` | 35 Declarations and storage | compiler word (constant, `cc/110-cc-decl.fth`); File header and bookkeeping
`cc-lookup-struct-tag-soft` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Struct definitions
`cc-lookup-struct-tag` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Struct definitions
`cc-loop-switch-depth` | 35 Declarations and storage | compiler word (variable, `cc/110-cc-decl.fth`); `cc-parse-return`
`cc-main-vaddr` | 35 Declarations and storage | compiler word (variable, `cc/110-cc-decl.fth`); File header and bookkeeping
`cc-more-type-kws` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Function pointers and the declaration engine
`cc-native-decl-fwd` | 35 Declarations and storage | compiler word (defer, `cc/110-cc-decl.fth`); File header and bookkeeping
`cc-native-float-types-default` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); File header and bookkeeping
`cc-native-float-types-fwd` | 35 Declarations and storage | compiler word (defer, `cc/110-cc-decl.fth`); File header and bookkeeping
`cc-native-frame-limit` | 35 Declarations and storage | compiler word (variable, `cc/110-cc-decl.fth`); File header and bookkeeping
`cc-native-return-desc` | 35 Declarations and storage | compiler word (variable, `cc/110-cc-decl.fth`); File header and bookkeeping
`cc-native-return-type` | 35 Declarations and storage | compiler word (variable, `cc/110-cc-decl.fth`); File header and bookkeeping
`cc-native-sizeof-type` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Takeaways
`cc-native-type-name-fwd` | 35 Declarations and storage | compiler word (defer, `cc/110-cc-decl.fth`); File header and bookkeeping
`cc-native-type-start-fwd` | 35 Declarations and storage | compiler word (defer, `cc/110-cc-decl.fth`); File header and bookkeeping
`cc-parse-decl-with-base` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Function pointers and the declaration engine
`cc-parse-decl` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Function pointers and the declaration engine
`cc-parse-fnptr-decl` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Function pointers and the declaration engine
`cc-parse-local-declarator` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Function pointers and the declaration engine
`cc-parse-return` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); `cc-parse-return`
`cc-parse-struct-def` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Struct definitions
`cc-parse-struct-local-decl` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Struct-local declarations
`cc-parse-type-name` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Type names and casts
`cc-peek-fnptr?` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Function pointers and the declaration engine
`cc-pending-struct-desc` | 35 Declarations and storage | compiler word (variable, `cc/110-cc-decl.fth`); File header and bookkeeping
`cc-prefix-qualified` | 35 Declarations and storage | compiler word (variable, `cc/110-cc-decl.fth`); Expectation helpers and ignored specifiers
`cc-qual-note-noop` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Expectation helpers and ignored specifiers
`cc-qual-note` | 35 Declarations and storage | compiler word (defer, `cc/110-cc-decl.fth`); Expectation helpers and ignored specifiers
`cc-qualifier-bit` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Expectation helpers and ignored specifiers
`cc-qualifier?` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Expectation helpers and ignored specifiers
`cc-return-shape-default` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); `cc-parse-return`
`cc-return-shape-fwd` | 35 Declarations and storage | compiler word (defer, `cc/110-cc-decl.fth`); `cc-parse-return`
`cc-sd-append-field` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Struct definitions
`cc-sd-build-desc` | 35 Declarations and storage | compiler word (variable, `cc/110-cc-decl.fth`); Struct definitions
`cc-sd-build-field-desc` | 35 Declarations and storage | compiler word (variable, `cc/110-cc-decl.fth`); Struct definitions
`cc-sd-build-field-ty` | 35 Declarations and storage | compiler word (variable, `cc/110-cc-decl.fth`); Struct definitions
`cc-sd-build-fname-a` | 35 Declarations and storage | compiler word (variable, `cc/110-cc-decl.fth`); Struct definitions
`cc-sd-build-fname-u` | 35 Declarations and storage | compiler word (variable, `cc/110-cc-decl.fth`); Struct definitions
`cc-skip-enum-tag` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Expectation helpers and ignored specifiers
`cc-skip-fnptr-params` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Function pointers and the declaration engine
`cc-skip-qualifiers` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Expectation helpers and ignored specifiers
`cc-skip-storage-quals` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Expectation helpers and ignored specifiers
`cc-sld-desc` | 35 Declarations and storage | compiler word (variable, `cc/110-cc-decl.fth`); Struct-local declarations
`cc-sld-name-a` | 35 Declarations and storage | compiler word (variable, `cc/110-cc-decl.fth`); Struct-local declarations
`cc-sld-name-u` | 35 Declarations and storage | compiler word (variable, `cc/110-cc-decl.fth`); Struct-local declarations
`cc-sld-ptr-depth` | 35 Declarations and storage | compiler word (variable, `cc/110-cc-decl.fth`); Struct-local declarations
`cc-switch-depth` | 35 Declarations and storage | compiler word (variable, `cc/110-cc-decl.fth`); `cc-parse-return`
`cc-tok-is-basic-type-kw?` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Function pointers and the declaration engine
`cc-try-cast` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Type names and casts
`cc-type-name-array` | 35 Declarations and storage | compiler word (variable, `cc/110-cc-decl.fth`); File header and bookkeeping
`cc-type-name-inner` | 35 Declarations and storage | compiler word (variable, `cc/110-cc-decl.fth`); File header and bookkeeping
`cc-type-name-qualified` | 35 Declarations and storage | compiler word (variable, `cc/110-cc-decl.fth`); Expectation helpers and ignored specifiers
`cc-type-start?` | 35 Declarations and storage | compiler word (`cc/110-cc-decl.fth`); Type names and casts
`cc-value-return-fwd` | 35 Declarations and storage | compiler word (defer, `cc/110-cc-decl.fth`); `cc-parse-return`
Casts | 35 Declarations and storage | idea; Type names and casts
Expectation helpers | 35 Declarations and storage | idea; Expectation helpers and ignored specifiers
Function pointers | 35 Declarations and storage | idea; Function pointers and the declaration engine
`cc-add-break-fixup` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); Break/continue fixup lists
`cc-add-continue-fixup` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); Break/continue fixup lists
`cc-add-switch-case` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); `switch` with deferred dispatch
`cc-break-stack-head` | 36 Statements and control flow | compiler word (variable, `cc/112-cc-stmt.fth`); Break/continue fixup lists
`cc-continue-stack-head` | 36 Statements and control flow | compiler word (variable, `cc/112-cc-stmt.fth`); Break/continue fixup lists
`cc-define-label` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); Labels and `goto`
`cc-emit-je-vaddr` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); Loop helpers and absolute backward branches
`cc-emit-jmp-vaddr` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); Loop helpers and absolute backward branches
`cc-emit-jnz-vaddr` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); Loop helpers and absolute backward branches
`cc-emit-switch-compare` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); `switch` with deferred dispatch
`cc-emit-switch-dispatch` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); `switch` with deferred dispatch
`cc-fixup-target-tmp` | 36 Statements and control flow | compiler word (variable, `cc/112-cc-stmt.fth`); Break/continue fixup lists
`cc-for-end-fixup` | 36 Statements and control flow | compiler word (variable, `cc/112-cc-stmt.fth`); Break/continue fixup lists
`cc-for-step-end` | 36 Statements and control flow | compiler word (variable, `cc/112-cc-stmt.fth`); Break/continue fixup lists
`cc-for-step-start` | 36 Statements and control flow | compiler word (variable, `cc/112-cc-stmt.fth`); Break/continue fixup lists
`cc-for-top-vaddr` | 36 Statements and control flow | compiler word (variable, `cc/112-cc-stmt.fth`); Break/continue fixup lists
`cc-label-cap` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); Labels and `goto`
`cc-label-count` | 36 Statements and control flow | compiler word (variable, `cc/112-cc-stmt.fth`); Labels and `goto`
`cc-label-create` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); Labels and `goto`
`cc-label-default-cap` | 36 Statements and control flow | compiler word (constant, `cc/112-cc-stmt.fth`); Labels and `goto`
`cc-label-default-fixup` | 36 Statements and control flow | compiler word (create, `cc/112-cc-stmt.fth`); Labels and `goto`
`cc-label-default-name-addr` | 36 Statements and control flow | compiler word (create, `cc/112-cc-stmt.fth`); Labels and `goto`
`cc-label-default-name-len` | 36 Statements and control flow | compiler word (create, `cc/112-cc-stmt.fth`); Labels and `goto`
`cc-label-default-switch-depth` | 36 Statements and control flow | compiler word (create, `cc/112-cc-stmt.fth`); Labels and `goto`
`cc-label-default-vaddr` | 36 Statements and control flow | compiler word (create, `cc/112-cc-stmt.fth`); Labels and `goto`
`cc-label-default-workspace` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); Labels and `goto`
`cc-label-direct-base` | 36 Statements and control flow | compiler word (variable, `cc/112-cc-stmt.fth`); Labels and `goto`
`cc-label-direct-cap` | 36 Statements and control flow | compiler word (constant, `cc/112-cc-stmt.fth`); Labels and `goto`
`cc-label-direct-workspace` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); Labels and `goto`
`cc-label-find-or-create` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); Labels and `goto`
`cc-label-find` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); Labels and `goto`
`cc-label-fixup-buffer` | 36 Statements and control flow | compiler word (variable, `cc/112-cc-stmt.fth`); Labels and `goto`
`cc-label-fixup` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); Labels and `goto`
`cc-label-fixups` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); Labels and `goto`
`cc-label-limit` | 36 Statements and control flow | compiler word (variable, `cc/112-cc-stmt.fth`); Labels and `goto`
`cc-label-name-addr-buffer` | 36 Statements and control flow | compiler word (variable, `cc/112-cc-stmt.fth`); Labels and `goto`
`cc-label-name-addr` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); Labels and `goto`
`cc-label-name-len-buffer` | 36 Statements and control flow | compiler word (variable, `cc/112-cc-stmt.fth`); Labels and `goto`
`cc-label-name-len` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); Labels and `goto`
`cc-label-set-vaddr` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); Labels and `goto`
`cc-label-switch-depth-buffer` | 36 Statements and control flow | compiler word (variable, `cc/112-cc-stmt.fth`); Labels and `goto`
`cc-label-switch-depth` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); Labels and `goto`
`cc-label-vaddr-buffer` | 36 Statements and control flow | compiler word (variable, `cc/112-cc-stmt.fth`); Labels and `goto`
`cc-label-vaddr-of` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); Labels and `goto`
`cc-label-vaddr` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); Labels and `goto`
`cc-native-finish-gotos` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); Labels and `goto`
`cc-native-goto-adjust` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); Labels and `goto`
`cc-native-goto-fixup` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); Labels and `goto`
`cc-parse-break-stmt` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); Break and continue
`cc-parse-compound` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); The forward reference, compound blocks, and `if`
`cc-parse-continue-stmt` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); Break and continue
`cc-parse-do-while` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); `do`/`while`
`cc-parse-expr-stmt` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); The dispatcher
`cc-parse-for` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); `while` and `for` (with step rewind)
`cc-parse-goto-stmt` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); Labels and `goto`
`cc-parse-ident-stmt` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); The dispatcher
`cc-parse-if` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); The forward reference, compound blocks, and `if`
`cc-parse-stmt-fwd` | 36 Statements and control flow | compiler word (defer, `cc/112-cc-stmt.fth`); The forward reference, compound blocks, and `if`
`cc-parse-stmt` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); The dispatcher
`cc-parse-switch` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); `switch` with deferred dispatch
`cc-parse-while` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); `while` and `for` (with step rewind)
`cc-peek-after-is-colon?` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); The dispatcher
`cc-switch-case` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); `switch` with deferred dispatch
`cc-switch-cases-head` | 36 Statements and control flow | compiler word (variable, `cc/112-cc-stmt.fth`); `switch` with deferred dispatch
`cc-switch-default-vaddr` | 36 Statements and control flow | compiler word (variable, `cc/112-cc-stmt.fth`); `switch` with deferred dispatch
`cc-switch-default` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); `switch` with deferred dispatch
`cc-switch-label` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); `switch` with deferred dispatch
`cc-switch-type` | 36 Statements and control flow | compiler word (variable, `cc/112-cc-stmt.fth`); `switch` with deferred dispatch
`cc-walk-and-patch-fixups` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); Break/continue fixup lists
`cc-walk-and-patch-imm64-to-vaddr` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); Break/continue fixup lists
`cc-walk-and-patch-to-vaddr` | 36 Statements and control flow | compiler word (`cc/112-cc-stmt.fth`); Break/continue fixup lists
Break/continue fixup lists | 36 Statements and control flow | idea; Break/continue fixup lists
for-step rewind | 36 Statements and control flow | idea; `while` and `for` (with step rewind)
Labels and goto | 36 Statements and control flow | idea; Labels and `goto`
switch with deferred dispatch | 36 Statements and control flow | idea; `switch` with deferred dispatch
`cc-block-end?` | 37 Functions and translation units | compiler word (`cc/114-cc-func.fth`); Setup
`cc-check-fns-defined` | 37 Functions and translation units | compiler word (`cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-emit-call-vaddr` | 37 Functions and translation units | compiler word (`cc/100-cc-expr.fth`); The call codegen
`cc-emit-close-shim` | 37 Functions and translation units | compiler word (`cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-emit-entry-stub` | 37 Functions and translation units | compiler word (`cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-emit-external-protos` | 37 Functions and translation units | compiler word (`cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-emit-late-shims` | 37 Functions and translation units | compiler word (`cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-emit-libc-typedefs` | 37 Functions and translation units | compiler word (`cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-emit-malloc-late` | 37 Functions and translation units | compiler word (`cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-emit-open-shim` | 37 Functions and translation units | compiler word (`cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-emit-pop-by-arg-index` | 37 Functions and translation units | compiler word (`cc/100-cc-expr.fth`); The call codegen
`cc-emit-pops-for-args` | 37 Functions and translation units | compiler word (`cc/100-cc-expr.fth`); The call codegen
`cc-emit-read-shim` | 37 Functions and translation units | compiler word (`cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-emit-shims` | 37 Functions and translation units | compiler word (`cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-emit-spill-params` | 37 Functions and translation units | compiler word (`cc/114-cc-func.fth`); Parameter lists and the spill
`cc-emit-write-shim` | 37 Functions and translation units | compiler word (`cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-enum-def-ahead?` | 37 Functions and translation units | compiler word (`cc/116-cc-prog.fth`); File-scope globals
`cc-enum-next-val` | 37 Functions and translation units | compiler word (variable, `cc/116-cc-prog.fth`); Enums and typedefs
`cc-finalize-globals` | 37 Functions and translation units | compiler word (`cc/116-cc-prog.fth`); File-scope globals
`cc-fn-name-addr` | 37 Functions and translation units | compiler word (variable, `cc/114-cc-func.fth`); Setup
`cc-fn-name-len` | 37 Functions and translation units | compiler word (variable, `cc/114-cc-func.fth`); Setup
`cc-fn-param-count` | 37 Functions and translation units | compiler word (variable, `cc/114-cc-func.fth`); Setup
`cc-fn-prior-sym-id` | 37 Functions and translation units | compiler word (variable, `cc/114-cc-func.fth`); Setup
`cc-gdecl-add` | 37 Functions and translation units | compiler word (`cc/116-cc-prog.fth`); File-scope globals
`cc-gdecl-base` | 37 Functions and translation units | compiler word (variable, `cc/116-cc-prog.fth`); File-scope globals
`cc-gdecl-declarator` | 37 Functions and translation units | compiler word (`cc/116-cc-prog.fth`); File-scope globals
`cc-gdecl-declared` | 37 Functions and translation units | compiler word (`cc/116-cc-prog.fth`); File-scope globals
`cc-gdecl-desc` | 37 Functions and translation units | compiler word (variable, `cc/116-cc-prog.fth`); File-scope globals
`cc-gdecl-name-a` | 37 Functions and translation units | compiler word (variable, `cc/116-cc-prog.fth`); File-scope globals
`cc-gdecl-name-u` | 37 Functions and translation units | compiler word (variable, `cc/116-cc-prog.fth`); File-scope globals
`cc-gdecl-ptr-depth` | 37 Functions and translation units | compiler word (variable, `cc/116-cc-prog.fth`); File-scope globals
`cc-gdecl-scalar-bytes` | 37 Functions and translation units | compiler word (`cc/116-cc-prog.fth`); File-scope globals
`cc-gdecl-slot` | 37 Functions and translation units | compiler word (variable, `cc/116-cc-prog.fth`); File-scope globals
`cc-is-main?` | 37 Functions and translation units | compiler word (`cc/114-cc-func.fth`); Setup
`cc-late-shims` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-main-name-bytes` | 37 Functions and translation units | compiler word (create, `cc/114-cc-func.fth`); Setup
`cc-name-calloc` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-close` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-exit` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-fclose` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-FILE` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-fopen` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-fputc` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-fputs` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-fread` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-free` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-fwrite` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-getchar` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-int16_t` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-int32_t` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-int64_t` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-int8_t` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-intptr_t` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-malloc` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-memcpy` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-memset` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-open` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-putchar` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-read` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-size_t` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-ssize_t` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-strlen` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-strrchr` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-uint16_t` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-uint32_t` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-uint64_t` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-uint8_t` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-name-write` | 37 Functions and translation units | compiler word (create, `cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-native-call-fwd` | 37 Functions and translation units | compiler word (defer, `cc/100-cc-expr.fth`); The call codegen
`cc-native-call-result-fwd` | 37 Functions and translation units | compiler word (defer, `cc/100-cc-expr.fth`); The call codegen
`cc-native-call-result` | 37 Functions and translation units | compiler word (`cc/100-cc-expr.fth`); The call codegen
`cc-native-drop-args` | 37 Functions and translation units | compiler word (`cc/100-cc-expr.fth`); The call codegen
`cc-native-function-desc-fwd` | 37 Functions and translation units | compiler word (defer, `cc/100-cc-expr.fth`); The call codegen
`cc-native-function-desc` | 37 Functions and translation units | compiler word (`cc/100-cc-expr.fth`); The call codegen
`cc-native-indirect-fwd` | 37 Functions and translation units | compiler word (defer, `cc/100-cc-expr.fth`); The call codegen
`cc-native-load-call-target` | 37 Functions and translation units | compiler word (`cc/100-cc-expr.fth`); The call codegen
`cc-native-parse-args` | 37 Functions and translation units | compiler word (`cc/100-cc-expr.fth`); The call codegen
`cc-native-reverse-args` | 37 Functions and translation units | compiler word (`cc/100-cc-expr.fth`); The call codegen
`cc-native-swap-args` | 37 Functions and translation units | compiler word (`cc/100-cc-expr.fth`); The call codegen
`cc-parse-call` | 37 Functions and translation units | compiler word (`cc/100-cc-expr.fth`); The call codegen
`cc-parse-enum-def` | 37 Functions and translation units | compiler word (`cc/116-cc-prog.fth`); Enums and typedefs
`cc-parse-fn-return-type` | 37 Functions and translation units | compiler word (`cc/114-cc-func.fth`); Parameter lists and the spill
`cc-parse-function-list` | 37 Functions and translation units | compiler word (`cc/116-cc-prog.fth`); File-scope globals
`cc-parse-function` | 37 Functions and translation units | compiler word (`cc/114-cc-func.fth`); Function definitions
`cc-parse-global-decl` | 37 Functions and translation units | compiler word (`cc/116-cc-prog.fth`); File-scope globals
`cc-parse-indirect-call` | 37 Functions and translation units | compiler word (`cc/100-cc-expr.fth`); The call codegen
`cc-parse-native-call` | 37 Functions and translation units | compiler word (`cc/100-cc-expr.fth`); The call codegen
`cc-parse-param-list-loop` | 37 Functions and translation units | compiler word (`cc/114-cc-func.fth`); Parameter lists and the spill
`cc-parse-param-list` | 37 Functions and translation units | compiler word (`cc/114-cc-func.fth`); Parameter lists and the spill
`cc-parse-program` | 37 Functions and translation units | compiler word (`cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-parse-top-decl` | 37 Functions and translation units | compiler word (`cc/116-cc-prog.fth`); File-scope globals
`cc-parse-typedef` | 37 Functions and translation units | compiler word (`cc/116-cc-prog.fth`); Enums and typedefs
`cc-patch-call-main` | 37 Functions and translation units | compiler word (`cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-register-fn-proto` | 37 Functions and translation units | compiler word (`cc/116-cc-prog.fth`); Top-level elision
`cc-register-late-shims` | 37 Functions and translation units | compiler word (`cc/116-cc-prog.fth`); The entry stub and the top-level driver
`cc-struct-def-ahead?` | 37 Functions and translation units | compiler word (`cc/116-cc-prog.fth`); File-scope globals
`cc-td-ty` | 37 Functions and translation units | compiler word (variable, `cc/116-cc-prog.fth`); Enums and typedefs
`cc-top-classify` | 37 Functions and translation units | compiler word (`cc/116-cc-prog.fth`); Top-level elision
`cc-top-depth` | 37 Functions and translation units | compiler word (variable, `cc/116-cc-prog.fth`); Top-level elision
`cc-top-skip-to-semi` | 37 Functions and translation units | compiler word (`cc/116-cc-prog.fth`); Top-level elision
`cc-top-var-seen` | 37 Functions and translation units | compiler word (variable, `cc/116-cc-prog.fth`); Top-level elision
`top-fndef` | 37 Functions and translation units | compiler word (constant, `cc/116-cc-prog.fth`); Top-level elision
`top-proto` | 37 Functions and translation units | compiler word (constant, `cc/116-cc-prog.fth`); Top-level elision
`top-var` | 37 Functions and translation units | compiler word (constant, `cc/116-cc-prog.fth`); Top-level elision
Calling convention (six register arguments) | 37 Functions and translation units | idea; The call codegen
Entry stub | 37 Functions and translation units | idea; The entry stub and the top-level driver
`cc-main` | 38 Compiler entry and Stage A | load stdin, preprocess, reset output and globals, emit header, parse program, place globals, finalize ELF, write /tmp/cc-out, bye
`cc-out-path` | 38 Compiler entry and Stage A | the NUL-terminated fixed output path /tmp/cc-out
Stage-A parity proof | 38 Compiler entry and Stage A | Forth-built and GCC-built M2-Planet emit identical M1 (2,367,260 bytes) on M2-Planet's own sources; not executable equality, not correctness for all C
Bootstrap chain | 38 Compiler entry and Stage A | tools built from source supply the means to build the next tools; followed in Part 4
Enums and typedefs | 37 Functions and translation units | idea; Enums and typedefs
Fixed 256-byte function frame | 37 Functions and translation units | concept (C compiler ideas (Part III)); introduced in old Ch 31
Function frame (256 bytes, 32 slots) | 37 Functions and translation units | idea; Parameter lists and the spill
Top-level classification | 37 Functions and translation units | idea; Top-level elision
`cc-main` | 38 Compiler entry and Stage A | compiler word (`cc/120-cc-main.fth`); `cc-main`: nine words and a `bye`
`cc-out-path` | 38 Compiler entry and Stage A | compiler word (create, `cc/120-cc-main.fth`); `cc-main`: nine words and a `bye`
Bootstrap chain | 38 Compiler entry and Stage A | idea; The wider chain
LP64 native object storage | 39 LP64 storage and initializers | object widths and alignment decide native storage placement and record layout
Private all-stack ABI | 39 LP64 storage and initializers | generated functions receive arguments in caller-owned stack slots
Static initializer lowering | 39 LP64 storage and initializers | queued initialization routines reuse expression fixups and run before main
Fail-closed bootstrap runtime | 39 LP64 storage and initializers | explicitly unavailable operations report and terminate when executed
Stage-A parity (byte-identical M1 output) | 38 Compiler entry and Stage A | concept (C compiler ideas (Part III)); introduced in old Ch 32
Stage-A parity proof | 38 Compiler entry and Stage A | idea; Stage A: the parity proof
`cc-nadd-field` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-naggregate-fwd` | 39 LP64 storage and initializers | compiler word (defer, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-naggregate` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nalign` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nalignment` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-narray-extra-default` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-narray-extra-fwd` | 39 LP64 storage and initializers | compiler word (defer, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-narray-suffix` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-native-declaration` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-native-emit-raw` | 39 LP64 storage and initializers | compiler word (`cc/119-cc-native-runtime.fth`); A finite Linux boundary
`cc-native-entry` | 39 LP64 storage and initializers | compiler word (`cc/117-cc-native-program.fth`); Private stack calls and whole programs
`cc-native-frame-patch` | 39 LP64 storage and initializers | compiler word (variable, `cc/117-cc-native-program.fth`); Private stack calls and whole programs
`cc-native-function-fwd` | 39 LP64 storage and initializers | compiler word (defer, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-native-function` | 39 LP64 storage and initializers | compiler word (`cc/117-cc-native-program.fth`); Private stack calls and whole programs
`cc-native-implicit-base-fwd` | 39 LP64 storage and initializers | compiler word (defer, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-native-implicit-base-noop` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-native-init-entry-fwd` | 39 LP64 storage and initializers | compiler word (defer, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-native-init-finish-fwd` | 39 LP64 storage and initializers | compiler word (defer, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-native-init-fwd` | 39 LP64 storage and initializers | compiler word (defer, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-native-init-noop` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-native-init-prepare-fwd` | 39 LP64 storage and initializers | compiler word (defer, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-native-initializer` | 39 LP64 storage and initializers | compiler word (`cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-native-local-declaration` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-native-local-layout-default` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-native-local-layout-fwd` | 39 LP64 storage and initializers | compiler word (defer, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-native-name-access` | 39 LP64 storage and initializers | compiler word (create, `cc/119-cc-native-runtime.fth`); A finite Linux boundary
`cc-native-name-chmod` | 39 LP64 storage and initializers | compiler word (create, `cc/119-cc-native-runtime.fth`); A finite Linux boundary
`cc-native-name-close` | 39 LP64 storage and initializers | compiler word (create, `cc/119-cc-native-runtime.fth`); A finite Linux boundary
`cc-native-name-exit` | 39 LP64 storage and initializers | compiler word (create, `cc/119-cc-native-runtime.fth`); A finite Linux boundary
`cc-native-name-gettimeofday` | 39 LP64 storage and initializers | compiler word (create, `cc/119-cc-native-runtime.fth`); A finite Linux boundary
`cc-native-name-ldexp` | 39 LP64 storage and initializers | compiler word (create, `cc/119-cc-native-runtime.fth`); A finite Linux boundary
`cc-native-name-localtime` | 39 LP64 storage and initializers | compiler word (create, `cc/119-cc-native-runtime.fth`); A finite Linux boundary
`cc-native-name-longjmp` | 39 LP64 storage and initializers | compiler word (create, `cc/119-cc-native-runtime.fth`); A finite Linux boundary
`cc-native-name-lseek` | 39 LP64 storage and initializers | compiler word (create, `cc/119-cc-native-runtime.fth`); A finite Linux boundary
`cc-native-name-mkdir` | 39 LP64 storage and initializers | compiler word (create, `cc/119-cc-native-runtime.fth`); A finite Linux boundary
`cc-native-name-mprotect` | 39 LP64 storage and initializers | compiler word (create, `cc/119-cc-native-runtime.fth`); A finite Linux boundary
`cc-native-name-open` | 39 LP64 storage and initializers | compiler word (create, `cc/119-cc-native-runtime.fth`); A finite Linux boundary
`cc-native-name-read` | 39 LP64 storage and initializers | compiler word (create, `cc/119-cc-native-runtime.fth`); A finite Linux boundary
`cc-native-name-time` | 39 LP64 storage and initializers | compiler word (create, `cc/119-cc-native-runtime.fth`); A finite Linux boundary
`cc-native-name-unlink` | 39 LP64 storage and initializers | compiler word (create, `cc/119-cc-native-runtime.fth`); A finite Linux boundary
`cc-native-name-write` | 39 LP64 storage and initializers | compiler word (create, `cc/119-cc-native-runtime.fth`); A finite Linux boundary
`cc-native-param-count` | 39 LP64 storage and initializers | compiler word (variable, `cc/117-cc-native-program.fth`); Private stack calls and whole programs
`cc-native-params` | 39 LP64 storage and initializers | compiler word (`cc/117-cc-native-program.fth`); Private stack calls and whole programs
`cc-native-primitive` | 39 LP64 storage and initializers | compiler word (`cc/119-cc-native-runtime.fth`); A finite Linux boundary
`cc-native-program` | 39 LP64 storage and initializers | compiler word (`cc/117-cc-native-program.fth`); Private stack calls and whole programs
`cc-native-qual-note` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-native-runtime-fwd` | 39 LP64 storage and initializers | compiler word (defer, `cc/117-cc-native-program.fth`); Private stack calls and whole programs
`cc-native-runtime-noop` | 39 LP64 storage and initializers | compiler word (`cc/117-cc-native-program.fth`); Private stack calls and whole programs
`cc-native-runtime` | 39 LP64 storage and initializers | compiler word (`cc/119-cc-native-runtime.fth`); A finite Linux boundary
`cc-native-scalar-init` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-native-sysarg` | 39 LP64 storage and initializers | compiler word (`cc/119-cc-native-runtime.fth`); A finite Linux boundary
`cc-native-syscall` | 39 LP64 storage and initializers | compiler word (`cc/119-cc-native-runtime.fth`); A finite Linux boundary
`cc-native-trap-length` | 39 LP64 storage and initializers | compiler word (variable, `cc/119-cc-native-runtime.fth`); A finite Linux boundary
`cc-native-trap-message` | 39 LP64 storage and initializers | compiler word (variable, `cc/119-cc-native-runtime.fth`); A finite Linux boundary
`cc-native-trap-prefix-length` | 39 LP64 storage and initializers | compiler word (constant, `cc/119-cc-native-runtime.fth`); A finite Linux boundary
`cc-native-trap-prefix` | 39 LP64 storage and initializers | compiler word (create, `cc/119-cc-native-runtime.fth`); A finite Linux boundary
`cc-native-type-name` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-native-type-shape-default` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-native-type-shape-fwd` | 39 LP64 storage and initializers | compiler word (defer, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-native-type-start` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-native-unavailable` | 39 LP64 storage and initializers | compiler word (`cc/119-cc-native-runtime.fth`); A finite Linux boundary
`cc-nbase-fwd` | 39 LP64 storage and initializers | compiler word (defer, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nbase-next-specifier` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nbase-raw` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nbase-scalar-default` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nbase-scalar-fwd` | 39 LP64 storage and initializers | compiler word (defer, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nbase-specifiers-default` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nbase-specifiers-fwd` | 39 LP64 storage and initializers | compiler word (defer, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nbase-trailing-default` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nbase-trailing-fwd` | 39 LP64 storage and initializers | compiler word (defer, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nbase` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-ncontext` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-ncopy` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nctx-bytes` | 39 LP64 storage and initializers | compiler word (constant, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nctx` | 39 LP64 storage and initializers | compiler word (variable, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-ndeclarator-check-fwd` | 39 LP64 storage and initializers | compiler word (defer, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-ndeclarator-check-noop` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-ndeclarator` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nenum-desc-default` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nenum-desc-fwd` | 39 LP64 storage and initializers | compiler word (defer, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nenum` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nfind-tag` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nfnptr-default` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nfnptr-fwd` | 39 LP64 storage and initializers | compiler word (defer, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nfnptr-name-default` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nfnptr-name-fwd` | 39 LP64 storage and initializers | compiler word (defer, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nfunction-suffix` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-ngroup-name` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-ngrouped-declarator` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-ngstore` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-ni-address` | 39 LP64 storage and initializers | compiler word (`cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-aggregate?` | 39 LP64 storage and initializers | compiler word (`cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-char-array` | 39 LP64 storage and initializers | compiler word (`cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-child-count` | 39 LP64 storage and initializers | compiler word (`cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-child` | 39 LP64 storage and initializers | compiler word (`cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-copy-bytes` | 39 LP64 storage and initializers | compiler word (`cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-count-rcx` | 39 LP64 storage and initializers | compiler word (`cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-entry-patch` | 39 LP64 storage and initializers | compiler word (variable, `cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-entry` | 39 LP64 storage and initializers | compiler word (`cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-field-default` | 39 LP64 storage and initializers | compiler word (`cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-field-fwd` | 39 LP64 storage and initializers | compiler word (defer, `cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-finish` | 39 LP64 storage and initializers | compiler word (`cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-frame` | 39 LP64 storage and initializers | compiler word (variable, `cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-head` | 39 LP64 storage and initializers | compiler word (variable, `cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-infer` | 39 LP64 storage and initializers | compiler word (`cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-list` | 39 LP64 storage and initializers | compiler word (`cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-mov-rsi-rdi` | 39 LP64 storage and initializers | compiler word (`cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-queue` | 39 LP64 storage and initializers | compiler word (`cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-scalar-fwd` | 39 LP64 storage and initializers | compiler word (defer, `cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-scalar` | 39 LP64 storage and initializers | compiler word (`cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-scan-brace` | 39 LP64 storage and initializers | compiler word (variable, `cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-scan-count` | 39 LP64 storage and initializers | compiler word (variable, `cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-scan-depth` | 39 LP64 storage and initializers | compiler word (variable, `cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-scan-have` | 39 LP64 storage and initializers | compiler word (variable, `cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-scan-mark` | 39 LP64 storage and initializers | compiler word (variable, `cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-static` | 39 LP64 storage and initializers | compiler word (variable, `cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-string-fwd` | 39 LP64 storage and initializers | compiler word (defer, `cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-string-size` | 39 LP64 storage and initializers | compiler word (`cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-string` | 39 LP64 storage and initializers | compiler word (`cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-tail` | 39 LP64 storage and initializers | compiler word (variable, `cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-value-fwd` | 39 LP64 storage and initializers | compiler word (defer, `cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-value` | 39 LP64 storage and initializers | compiler word (`cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ni-zero-object` | 39 LP64 storage and initializers | compiler word (`cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-ninstall-symbol` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nmax` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nmember-default` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nmember-fwd` | 39 LP64 storage and initializers | compiler word (defer, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nminus-rot` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nmove-bytes` | 39 LP64 storage and initializers | compiler word (variable, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nmove-new` | 39 LP64 storage and initializers | compiler word (variable, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nmove-old` | 39 LP64 storage and initializers | compiler word (variable, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nmove-tentative` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nobject-fwd` | 39 LP64 storage and initializers | compiler word (defer, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nobject-size` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nobject` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-npick` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-npointer-array-default` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-npointer-array-fwd` | 39 LP64 storage and initializers | compiler word (defer, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-npromote-fields` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nqualified-move` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nsize` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nspec-base` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nspec-bool` | 39 LP64 storage and initializers | compiler word (constant, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nspec-check-default` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nspec-check-fwd` | 39 LP64 storage and initializers | compiler word (defer, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nspec-count` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nspec-counts` | 39 LP64 storage and initializers | compiler word (create, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nspec-double` | 39 LP64 storage and initializers | compiler word (constant, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nspec-float` | 39 LP64 storage and initializers | compiler word (constant, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nspec-keyword?` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nspec-note` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nspec-slots` | 39 LP64 storage and initializers | compiler word (constant, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-nstorage-context` | 39 LP64 storage and initializers | compiler word (variable, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-ntag-a` | 39 LP64 storage and initializers | compiler word (variable, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-ntag-u` | 39 LP64 storage and initializers | compiler word (variable, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-ntypedef-check-fwd` | 39 LP64 storage and initializers | compiler word (defer, `cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-ntypedef-check-noop` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`cc-value-static-init-default` | 39 LP64 storage and initializers | compiler word (`cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`cc-value-static-init-fwd` | 39 LP64 storage and initializers | compiler word (defer, `cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`nc-array` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`nc-base-array` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`nc-base-inner` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`nc-base-qualified` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`nc-base` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`nc-bound-mask` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`nc-desc` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`nc-extern` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`nc-func` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`nc-id` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`nc-inner` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`nc-name` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`nc-nlen` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`nc-params` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`nc-prefix-qualified` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`nc-qualified` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`nc-sdesc` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`nc-slot` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`nc-static` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`nc-storage` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`nc-td` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`nc-top` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`nc-ty` | 39 LP64 storage and initializers | compiler word (`cc/115-cc-native.fth`); Native declarations and aligned storage
`ni-array` | 39 LP64 storage and initializers | compiler word (`cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`ni-brace` | 39 LP64 storage and initializers | compiler word (`cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`ni-desc` | 39 LP64 storage and initializers | compiler word (`cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`ni-index` | 39 LP64 storage and initializers | compiler word (`cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`ni-inner` | 39 LP64 storage and initializers | compiler word (`cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`ni-nested` | 39 LP64 storage and initializers | compiler word (`cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`ni-offset` | 39 LP64 storage and initializers | compiler word (`cc/118-cc-native-init.fth`); Initializers reuse expression fixups
`ni-type` | 39 LP64 storage and initializers | compiler word (`cc/118-cc-native-init.fth`); Initializers reuse expression fixups
Direct TinyCC bootstrap | 39 LP64 storage and initializers | idea; What the bootstrap result proves
Fail-closed bootstrap runtime | 39 LP64 storage and initializers | idea; A finite Linux boundary
Section-relative value | 40 Objects and relocations | a symbol's value is its offset within its section until linking
Stable symbol handle | 40 Objects and relocations | an insertion ID kept independent of the ELF symbol order
Local-first symbol numbering | 40 Objects and relocations | serialization puts local symbols first and remaps relocation targets
Explicit relocation addend | 40 Objects and relocations | RELA records carry the adjustment apart from the field being repaired
Atomic object publication | 40 Objects and relocations | write, close, then rename into place
Shared call signature | 41 System V calls and separate compilation | one retained signature drives both incoming parameters and outgoing calls
Aligned outgoing argument block | 41 System V calls and separate compilation | arguments past the sixth integer register go in a 16-byte-aligned stack block above the return address
Persistent call-save span | 41 System V calls and separate compilation | frame slots keep rsp and live expression values across calls
Scoped external identity | 41 System V calls and separate compilation | an external's signature and fixups outlive the block-scoped parser symbol
Ranked array descriptor | 41 System V calls and separate compilation | recursive element nodes keep array shape and row qualifiers
Stable object record | 41 System V calls and separate compilation | storage identity survives parser scope reuse until object export
Symbolic address operand | 41 System V calls and separate compilation | a record plus addend stands for an address without loading it
Global definition selection | 42 Linker and archives | strong definitions override weak ones; two strong definitions fail
Per-object placement | 42 Linker and archives | each input section gets an aligned position in the executable
Checked relocation assignment | 42 Linker and archives | resolve and range-check a relocation before writing its field
GNU archive index | 42 Linker and archives | symbol names map to candidate member-header offsets
Lazy member selection | 42 Linker and archives | extract only members that satisfy unresolved strong demand, until nothing new is needed
Input identity protection | 42 Linker and archives | device/inode checks stop the output from replacing one of its inputs
Runtime-aware entry | 43 Runtime, libc, streams, and formatting | start code initializes library state before main and routes its return through library exit
Raw syscall result | 43 Runtime, libc, streams, and formatting | the kernel's result is left unchanged for public wrappers to translate
Shared errno storage | 43 Runtime, libc, streams, and formatting | single-threaded error state reached through __errno_location
Frameless adapter | 43 Runtime, libc, streams, and formatting | a machine-code leaf that keeps the stack layout its contract requires
Nonlocal continuation | 43 Runtime, libc, streams, and formatting | saved registers, stack pointer and return address for resuming a live caller (setjmp/longjmp)
Allocation metadata | 43 Runtime, libc, streams, and formatting | extent and requested size kept with each block for free and realloc
Failure-preserving realloc | 43 Runtime, libc, streams, and formatting | failed growth leaves the original allocation intact
Stream state | 43 Runtime, libc, streams, and formatting | ownership, buffered bytes, position, error and EOF tracked beyond the descriptor
Bounded formatting count | 43 Runtime, libc, streams, and formatting | the logical output length keeps counting even when the destination truncates
Target macro contract | 44 Target headers | in System V mode the preprocessor predefines __STDC__ 1, __STDC_HOSTED__ 0, __SEED_FORTH__, __linux__, __x86_64__ and __LP64__
Withheld identities | 44 Target headers | no __GNUC__ or __STDC_VERSION__: headers must not select GCC extensions or a later C version
Typed constant record | 45 Typed constants | value, C type, descriptor and relocation symbol carried together
Per-operator normalization | 45 Typed constants | each operator's result is cut to its C width before the next operator
Checked constant arithmetic | 45 Typed constants | signed overflow is rejected; unsigned arithmetic wraps
Typed conditional selection | 45 Typed constants | both arm types decide the result type before the chosen value is converted
Constant pool watermark | 45 Typed constants | temporary allocations are released after each public parse
Array-based va_list | 46 System V varargs | va_list is an array of one record, so passing it shares one cursor while its storage stays local
Variadic register-save area | 46 System V varargs | each variadic call saves its incoming argument registers in its own frame
Independent argument cursors | 46 System V varargs | GP and XMM offsets advance separately; overflow arguments share one stack cursor
Variadic cursor copying | 46 System V varargs | va_copy copies the cursor fields, so two traversals share the saved arguments
Floating payload transport | 47 Floating values and exact literals | floating bits ride in expression cells and move into SSE registers only to compute
Sticky-half unsigned conversion | 47 Floating values and exact literals | large unsigned integers convert through signed SSE instructions without losing the rounding decision
Exact floating ratio | 47 Floating values and exact literals | a decimal literal is kept as an exact integer numerator and denominator
Remainder-based rounding | 47 Floating values and exact literals | twice the exact remainder is compared with the divisor to round to nearest, ties to even
Direct destination rounding | 47 Floating values and exact literals | the destination format is chosen before a literal or constant operation is rounded
Bitfield slice | 48 Record bitfields | a field is a width and bit shift inside a containing storage unit at a byte offset
Preserving store | 48 Record bitfields | a bitfield store masks the unit and merges new bits, leaving neighbours unchanged; signed fields sign-extend on load
Aggregate classification | 49 Aggregates and extended floating values | a record is MEMORY, one or two INTEGER eightbytes, scalar SSE or X87 by size and leaf types; floating members and mixed classes are rejected
Call transport plan | 49 Aggregates and extended floating values | each argument gets an explicit register or stack location before any value moves
Extended floating value | 49 Aggregates and extended floating values | long double travels as a 16-byte-aligned stack copy and returns in st(0); no x87 state is kept between operations
Seed-only driver construction | 50 Building seed-cc and seed-ar | the seed alone builds seed-cc and seed-ar by fork/exec of ./seed-forth on assembled Forth input streams
Compiler driver stream | 50 Building seed-cc and seed-ar | each compilation's input is the compiler layers, a fixed driver and one C source
Runtime link order | 50 Building seed-cc and seed-ar | start.o, then the program objects, then libseed.a, so the archive supplies only what is still unresolved
Kaem recipe runner | 51 Owning the tools | kaem, built by seed-cc, runs the build recipes before any shell exists
Fixed configuration | 51 Owning the tools | hand-written config.h answers replace running configure for the first tools
Direct recipes | 51 Owning the tools | the first Makefiles run commands without a shell interpreting them
Temporary scanner bootstrap | 51 Owning the tools | Heirloom lex builds an intermediate flex that then generates flex's own scanner
Guarded configure probes | 51 Owning the tools | explicit tool settings and failing guard scripts keep configure from finding host tools
Compiler census | 52 GCC 4.0.4: stages C and D | the configured Makefile names the cc1 objects; seed-cc compiles and links each one
Source generator | 52 GCC 4.0.4: stages C and D | a build-time program whose output is compiled later; built by seed-cc rather than shipped
Sysroot | 52 GCC 4.0.4: stages C and D | the directory tree holding the target headers and libraries the compiler's output uses
Libgcc | 52 GCC 4.0.4: stages C and D | target support routines that generated code calls, built by the new GCC rather than seed-cc
Compiler fixed point | 52 GCC 4.0.4: stages C and D | stage 2 = 3 = 4: successive GCC generations install the same files
Archive member comparison | 52 GCC 4.0.4: stages C and D | archives that differ as wholes still match when member names, order and bytes agree
Late tools | 52 GCC 4.0.4: stages C and D | make 4.4.1, bash 5.2, coreutils 9.5 and the rest, built by the fixed-point GCC with their own configure
Sealed executable boundary | 53 The sealed host run | the prepared root starts with hex0-seed as its only executable file
Executable publication | 53 The sealed host run | the host grants seed-forth's execute bit between entries; it supplies no program bytes
Execve trace audit | 53 The sealed host run | every successful execve path must resolve to hex0-seed, the host's bwrap, or a program the chain built
Interrupted execve join | 53 The sealed host run | strace's unfinished and resumed lines are joined by pid before counting
Archive pin agreement | 53 The sealed host run | each stage's pin file agrees with MANIFEST.sha256 (tools/check-pins.py)
K0 serialized fork | 54 K0 and K1 | K0 runs a forked child to completion before resuming the parent, so no scheduler is needed
K0 syscall fallbacks | 54 K0 and K1 | k0-syscalls.fth retries or fakes the few calls K0 lacks, only after ENOSYS
AMD64 recipe runner | 54 K0 and K1 | amd64-runner runs recipe lines (cat, run, same, rename) with explicit paths and checked exit status
K0-to-K1 handoff | 54 K0 and K1 | K0 loads the seed-built K1 with its ordinary program loader; K1 takes the machine
K1 operating boundary | 54 K0 and K1 | protected processes and the Linux syscall subset the bootstrap tools use; static ELF only
RAM-tree import | 54 K0 and K1 | K1 imports hda as its RAM root and keeps K0's files under /k0/
Direct Linux recipe | 55 Linux 7.2.8 and kexec under QEMU | direct-linux.recipe extends the guest recipe through the compiler climb, Linux, export and handover
gcc64 compiler climb | 55 Linux 7.2.8 and kexec under QEMU | chain-built compilers in turn, from GCC 4.0.4 through 4.7.4 to GCC 10.5.0 with binutils 2.41
Output pin scope | 55 Linux 7.2.8 and kexec under QEMU | chain/gcc64/HASHES pins are any (path-free) or root (only at /build-out/g64)
Embedded initramfs | 55 Linux 7.2.8 and kexec under QEMU | the static init from chain/ladder/init.c travels inside bzImage
hdb result export | 55 Linux 7.2.8 and kexec under QEMU | finish.sh writes the Linux output and logs as a tar to hdb before the handover
Linux boot parameters | 55 Linux 7.2.8 and kexec under QEMU | K1 builds boot_params, the command line and the e820 map before jumping to Linux
kexec-style handover | 55 Linux 7.2.8 and kexec under QEMU | the running K1 loads its successor kernel and jumps to it without firmware
Init greeting evidence | 55 Linux 7.2.8 and kexec under QEMU | init's greeting and /proc/version show the built kernel ran a chain-built program
LP64 native object storage | 39 LP64 storage and initializers | idea; Two profiles, one compiler
Private all-stack ABI | 39 LP64 storage and initializers | idea; Private stack calls and whole programs
Static initializer lowering | 39 LP64 storage and initializers | idea; Initializers reuse expression fixups
`cc-obj-4le` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); The interface between compiler and linker
`cc-obj-8le` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); The interface between compiler and linker
`cc-obj-abandon-output` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-abs` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); The interface between compiler and linker
`cc-obj-align` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); The interface between compiler and linker
`cc-obj-base` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-bound` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-bss-cap` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); Canonical source
`cc-obj-bss` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); The interface between compiler and linker
`cc-obj-build` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); The interface between compiler and linker
`cc-obj-byte` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); The interface between compiler and linker
`cc-obj-bytes` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); The interface between compiler and linker
`cc-obj-check-align` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-check-definition` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-check-id` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-check-output` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-check-section` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-check-symbols` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-current` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-data` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); The interface between compiler and linker
`cc-obj-default-payload` | 40 Objects and relocations | compiler word (create, `cc/081-cc-object.fth`); Canonical source
`cc-obj-default-relocs` | 40 Objects and relocations | compiler word (create, `cc/081-cc-object.fth`); Canonical source
`cc-obj-default-strings` | 40 Objects and relocations | compiler word (create, `cc/081-cc-object.fth`); Canonical source
`cc-obj-default-symbols` | 40 Objects and relocations | compiler word (create, `cc/081-cc-object.fth`); Canonical source
`cc-obj-default-workspace` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-default` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); Canonical source
`cc-obj-define` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); The interface between compiler and linker
`cc-obj-direct-base` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-direct-payload-bytes` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-direct-symbol-bytes` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-direct-workspace` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-emit-relocs` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-emit-sh` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-emit-symbol` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-end-section` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-fd` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-func` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); Canonical source
`cc-obj-global` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); Canonical source
`cc-obj-here` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); The interface between compiler and linker
`cc-obj-hex-digits` | 40 Objects and relocations | compiler word (create, `cc/081-cc-object.fth`); Canonical source
`cc-obj-hidden` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); Canonical source
`cc-obj-i` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-init` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); The interface between compiler and linker
`cc-obj-initialized` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-internal` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); Canonical source
`cc-obj-length` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-local-end` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-local` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); Canonical source
`cc-obj-make-temp-path` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-next-index` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-notype` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); Canonical source
`cc-obj-nrel` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-nstr` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-nsym` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-object` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); Canonical source
`cc-obj-out-align` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-out-bytes` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-out-zero` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-pass` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-patch-4le` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-patch-8le` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-patch-a` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-patch-n` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-patch` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-path` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-payload-buffer` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-payload` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-pc32` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); The interface between compiler and linker
`cc-obj-pid` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-plt32` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); The interface between compiler and linker
`cc-obj-protected` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); Canonical source
`cc-obj-put-definition` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-r-add` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-r-kind` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-r-off` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-r-sec` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-r-sym` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-r32` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); The interface between compiler and linker
`cc-obj-r32s` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); The interface between compiler and linker
`cc-obj-r64` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); The interface between compiler and linker
`cc-obj-rel` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-reloc-cap` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-reloc-default-cap` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); Canonical source
`cc-obj-reloc-direct-cap` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); Canonical source
`cc-obj-reloc-limit` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-reloc-width` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-reloc` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); The interface between compiler and linker
`cc-obj-relocs-buffer` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-relocs` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-require-init` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-reserve` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); The interface between compiler and linker
`cc-obj-reset-write` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-rodata` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); The interface between compiler and linker
`cc-obj-room` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-s-a` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-s-bind` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-s-row` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-s-sec` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-s-size` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-s-type` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-s-u` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-s-value` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-s-vis` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-section-cap` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Bounds and failures
`cc-obj-section-default-cap` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); Canonical source
`cc-obj-section-direct-cap` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); Canonical source
`cc-obj-section-limit` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-section` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); Canonical source
`cc-obj-sections` | 40 Objects and relocations | compiler word (create, `cc/081-cc-object.fth`); Canonical source
`cc-obj-sh-init` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-sh` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-shnames-size` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); Canonical source
`cc-obj-shnames` | 40 Objects and relocations | compiler word (create, `cc/081-cc-object.fth`); Canonical source
`cc-obj-shoff` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-start-section` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-stat-buffer` | 40 Objects and relocations | compiler word (create, `cc/081-cc-object.fth`); Canonical source
`cc-obj-string-cap` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-string-default-cap` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); Canonical source
`cc-obj-string-direct-cap` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); Canonical source
`cc-obj-string-limit` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-strings-buffer` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-strings` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-sym` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-symbol-cap` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-symbol-default-cap` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); Canonical source
`cc-obj-symbol-direct-cap` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); Canonical source
`cc-obj-symbol-limit` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-symbol-pass` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-symbol` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); The interface between compiler and linker
`cc-obj-symbols-buffer` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-symbols` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-temp-length` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-temp-owned` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-temp-path` | 40 Objects and relocations | compiler word (create, `cc/081-cc-object.fth`); Canonical source
`cc-obj-temp-suffix` | 40 Objects and relocations | compiler word (create, `cc/081-cc-object.fth`); Canonical source
`cc-obj-text-cap` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-obj-text-default-cap` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); Canonical source
`cc-obj-text-direct-cap` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); Canonical source
`cc-obj-text-limit` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-text` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); The interface between compiler and linker
`cc-obj-ti` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-undef` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); The interface between compiler and linker
`cc-obj-use` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); The interface between compiler and linker
`cc-obj-weak` | 40 Objects and relocations | compiler word (constant, `cc/081-cc-object.fth`); Canonical source
`cc-obj-write` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); The interface between compiler and linker
`cc-obj-written` | 40 Objects and relocations | compiler word (variable, `cc/081-cc-object.fth`); Canonical source
`cc-obj-zero` | 40 Objects and relocations | compiler word (`cc/081-cc-object.fth`); Canonical source
`cc-const-qualified` | 41 System V calls and separate compilation | compiler word (variable, `cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-ld-desc` | 41 System V calls and separate compilation | compiler word (variable, `cc/121-cc-sysv.fth`); Canonical source
`cc-ld-descriptor` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Save the registers the caller owns
`cc-ld-die` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Save the registers the caller owns
`cc-ld-error-prefix` | 41 System V calls and separate compilation | compiler word (create, `cc/121-cc-sysv.fth`); Canonical source
`cc-ld-mismatch` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Save the registers the caller owns
`cc-ld?` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Save the registers the caller owns
`cc-om-address-array` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-address-cast-fwd` | 41 System V calls and separate compilation | compiler word (defer, `cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-address-deref` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-address-frame` | 41 System V calls and separate compilation | compiler word (variable, `cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-address-ident` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-address-index-fwd` | 41 System V calls and separate compilation | compiler word (defer, `cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-address-index` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-address-member` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-address-operand` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-address-unary-fwd` | 41 System V calls and separate compilation | compiler word (defer, `cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-address-value` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-bucket` | 41 System V calls and separate compilation | compiler word (create, `cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-buffer` | 41 System V calls and separate compilation | compiler word (variable, `cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-cap` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-compatible-object` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-const-address` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-const-ident` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-const-string` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-count` | 41 System V calls and separate compilation | compiler word (variable, `cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-default-cap` | 41 System V calls and separate compilation | compiler word (constant, `cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-default-records` | 41 System V calls and separate compilation | compiler word (create, `cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-default-workspace` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-direct-base` | 41 System V calls and separate compilation | compiler word (variable, `cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-direct-cap` | 41 System V calls and separate compilation | compiler word (constant, `cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-direct-workspace` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-export-needed?` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-export` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-finalize-storage` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-find-length` | 41 System V calls and separate compilation | compiler word (variable, `cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-find-name` | 41 System V calls and separate compilation | compiler word (variable, `cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-find` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-flag` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-from-symbol` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-function-calls` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-hash-reset` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-hnext` | 41 System V calls and separate compilation | compiler word (create, `cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-initializer` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-install-object` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-limit` | 41 System V calls and separate compilation | compiler word (variable, `cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-link` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-new` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-record` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-records` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-reference` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-reloc` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-relocations` | 41 System V calls and separate compilation | compiler word (variable, `cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-scalar-initializer` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-size-from-declaration` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-string-initializer` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-string-name` | 41 System V calls and separate compilation | compiler word (create, `cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-string-piece` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-string` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-value-default` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-om-value-fwd` | 41 System V calls and separate compilation | compiler word (defer, `cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-sysv-abi-type-default` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-abi-type-fwd` | 41 System V calls and separate compilation | compiler word (defer, `cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-address-fixups` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-adjust-array-parameter` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-adjust-function-parameter` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-arg-cap` | 41 System V calls and separate compilation | compiler word (constant, `cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-argument-check-default` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-argument-check-fwd` | 41 System V calls and separate compilation | compiler word (defer, `cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-array-address` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Ranked fixed-array descriptors
`cc-sysv-array-binop` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-array-compound` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-array-decay` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Ranked fixed-array descriptors
`cc-sysv-array-extra` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-array-node` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-array-operands?` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-array-pair-check` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-array-rank-limit` | 41 System V calls and separate compilation | compiler word (constant, `cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-array-rank` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-array-tail` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-array-ternary` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-base-trailing` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-block-function` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); One signature, two places to use it
`cc-sysv-call-fixups` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-call-qualified` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-call-result` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-call-staged-target` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-call` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-cast-null` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-cast-types` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); One signature, two places to use it
`cc-sysv-cast-value` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-check-callable` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-check-declarator` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-check-implicit-defined` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-check-implicit-signature` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-check-scalar-default` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-check-scalar` | 41 System V calls and separate compilation | compiler word (defer, `cc/121-cc-sysv.fth`); Carry code and storage into a relocatable object
`cc-sysv-check-signature` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-comparison-param` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-compatible-signatures-fwd` | 41 System V calls and separate compilation | compiler word (defer, `cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-compatible-signatures` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-compatible-types` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-declaration-specifiers` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-declarator-signature` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); One signature, two places to use it
`cc-sysv-default-compatible?` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-default-type` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-enable` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Goal
`cc-sysv-entry` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-extension-name` | 41 System V calls and separate compilation | compiler word (create, `cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-extension?` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-find-ordinary` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-find-parameter` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-find-tag` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-finish-call` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-float-types` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-fnptr-name` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-fnptr` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-frame-patch` | 41 System V calls and separate compilation | compiler word (variable, `cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-function-desc` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-function-pointer?` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-function-signature` | 41 System V calls and separate compilation | compiler word (variable, `cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-function-typedef` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); One signature, two places to use it
`cc-sysv-function` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-grouped-array` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-identifier-list` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-implicit-at` | 41 System V calls and separate compilation | compiler word (create, `cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-implicit-base` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-implicit-close` | 41 System V calls and separate compilation | compiler word (create, `cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-implicit-count` | 41 System V calls and separate compilation | compiler word (variable, `cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-implicit-declarator-fwd` | 41 System V calls and separate compilation | compiler word (defer, `cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-implicit-declarator-noop` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-implicit-declarator` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-implicit-declared-fwd` | 41 System V calls and separate compilation | compiler word (defer, `cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-implicit-declared-noop` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-implicit-die` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-implicit-error` | 41 System V calls and separate compilation | compiler word (variable, `cc/121-cc-sysv.fth`); One signature, two places to use it
`cc-sysv-implicit-find` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-implicit-head` | 41 System V calls and separate compilation | compiler word (variable, `cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-implicit-message` | 41 System V calls and separate compilation | compiler word (create, `cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-implicit-record` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-implicit-symbol` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-index-base` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-indirect-call` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-inherit-array` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-integral?` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-known-params?` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-lex-extra` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); One signature, two places to use it
`cc-sysv-lex-number-fwd` | 41 System V calls and separate compilation | compiler word (defer, `cc/121-cc-sysv.fth`); One signature, two places to use it
`cc-sysv-load-gp` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-load-staged` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-local-layout` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-local-load` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-member-base` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-object-declaration` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-sysv-object-enable` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-sysv-object-function-desc` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-sysv-object-function` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-sysv-object-implicit` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-sysv-object-mode` | 41 System V calls and separate compilation | compiler word (variable, `cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-sysv-object-program` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-sysv-object-size-limit` | 41 System V calls and separate compilation | compiler word (constant, `cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-object-size` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-object-string` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`cc-sysv-old-parameters` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-parameter-base` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-parameter-context` | 41 System V calls and separate compilation | compiler word (variable, `cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-parameter-register` | 41 System V calls and separate compilation | compiler word (variable, `cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-parameter-specifiers` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-parameter-type` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-params-fwd` | 41 System V calls and separate compilation | compiler word (defer, `cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-params` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-parse-args` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-prepare-call` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-program` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-prototype?` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-qualified-node` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-qualify-node` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Ranked fixed-array descriptors
`cc-sysv-restore-callee` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-restore-live` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-result-value-fwd` | 41 System V calls and separate compilation | compiler word (defer, `cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-return-check-default` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-return-check-fwd` | 41 System V calls and separate compilation | compiler word (defer, `cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-row-qualifier-check` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Ranked fixed-array descriptors
`cc-sysv-row-set` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-same-types` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Ranked fixed-array descriptors
`cc-sysv-save-callee` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-save-live` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-scalar-base` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-sig-count` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-sig-desc` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-sig-name` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-sig-param` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-sig-return` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-sig-varargs` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-signature-fwd` | 41 System V calls and separate compilation | compiler word (defer, `cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-signature-result` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-signature-tag` | 41 System V calls and separate compilation | compiler word (constant, `cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-signature` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-signatures` | 41 System V calls and separate compilation | compiler word (create, `cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-size-product` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-sizeof-type` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-skip-extensions` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-spec-bad` | 41 System V calls and separate compilation | compiler word (variable, `cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-spec-check` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); One signature, two places to use it
`cc-sysv-spec-fail` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-spec-only` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-spec-total` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-stack-count` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-stack-depth` | 41 System V calls and separate compilation | compiler word (variable, `cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-storage-keyword?` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-storage-note` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-storage-specifier?` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); One signature, two places to use it
`cc-sysv-store-gp` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-store-outgoing` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-store-params-default` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-store-params-fwd` | 41 System V calls and separate compilation | compiler word (defer, `cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-symbol-signature` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-ternary-split` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-track-pop` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-track-push` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-translation-unit` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-type-name-raw` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-type-name` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-type-shape` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-typedef-check` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-unknown-ident` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); One signature, two places to use it
`cc-sysv-value-shape` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Ranked fixed-array descriptors
`cc-sysv-value-type-check` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-varargs-prepare-default` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-varargs-prepare-fwd` | 41 System V calls and separate compilation | compiler word (defer, `cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-varargs-save-default` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-varargs-save-fwd` | 41 System V calls and separate compilation | compiler word (defer, `cc/121-cc-sysv.fth`); Canonical source
`cc-sysv-zero-vector-count` | 41 System V calls and separate compilation | compiler word (`cc/121-cc-sysv.fth`); Canonical source
`cc-target-sysv` | 41 System V calls and separate compilation | compiler word (variable, `cc/121-cc-sysv.fth`); Canonical source
`oa-array` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`oa-desc` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`oa-inner` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`oa-lvalue` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`oa-qualified` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`oa-record` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`oa-type` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`oa-value` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`om-align` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`om-array` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`om-bind` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`om-desc` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`om-flags` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`om-implicit` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`om-inner` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`om-kind` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`om-name` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`om-nlen` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`om-offset` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`om-output` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`om-section` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`om-size` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`om-symbol` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`om-type` | 41 System V calls and separate compilation | compiler word (`cc/123-cc-object-program.fth`); Carry code and storage into a relocatable object
`arc-add-index` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Canonical source
`arc-add-object` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Make an archive without a host archiver
`arc-any` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-basename` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Canonical source
`arc-be32` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Canonical source
`arc-bsd-64` | 42 Linker and archives | compiler word (create, `cc/141-archive.fth`); Canonical source
`arc-bsd-index` | 42 Linker and archives | compiler word (create, `cc/141-archive.fth`); Canonical source
`arc-bsd` | 42 Linker and archives | compiler word (create, `cc/141-archive.fth`); Canonical source
`arc-changed` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-check-name` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Canonical source
`arc-check` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Validate the envelope before selecting a member
`arc-close` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Canonical source
`arc-count` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-decimal` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Canonical source
`arc-dest` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-digits` | 42 Linker and archives | compiler word (create, `cc/141-archive.fth`); Canonical source
`arc-emit-index` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Canonical source
`arc-emit-longs` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Canonical source
`arc-emit-members` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Canonical source
`arc-entry` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Canonical source
`arc-even` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Canonical source
`arc-found` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-header-p` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-header` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Canonical source
`arc-i` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-image` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-index-cap` | 42 Linker and archives | compiler word (constant, `cc/141-archive.fth`); Canonical source
`arc-index-cursor` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-index-data` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-index-end` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-index-offset` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-index-size` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-index` | 42 Linker and archives | compiler word (create, `cc/141-archive.fth`); Canonical source
`arc-init` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Make an archive without a host archiver
`arc-ip` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-j` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-long-data` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-long-length` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-long-size` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-magic` | 42 Linker and archives | compiler word (create, `cc/141-archive.fth`); Canonical source
`arc-member-cap` | 42 Linker and archives | compiler word (constant, `cc/141-archive.fth`); Canonical source
`arc-member-data` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-member-length` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-member-needed` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Canonical source
`arc-member-size` | 42 Linker and archives | compiler word (constant, `cc/141-archive.fth`); Canonical source
`arc-member` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Canonical source
`arc-members` | 42 Linker and archives | compiler word (create, `cc/141-archive.fth`); Canonical source
`arc-mode` | 42 Linker and archives | compiler word (create, `cc/141-archive.fth`); Canonical source
`arc-mp` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-name-allowed` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Canonical source
`arc-name-kind` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-name` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-names-size` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-ndigit` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-needed` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-nindex` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-nlen` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-num-base` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-number-field` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Canonical source
`arc-number` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-numeric-a` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-numeric-end` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-open` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Canonical source
`arc-ordinary` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Canonical source
`arc-output-size` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-output` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-pad` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Canonical source
`arc-parse-index` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Canonical source
`arc-parse` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Canonical source
`arc-path` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-plan` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Canonical source
`arc-pos` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-put-be32` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Canonical source
`arc-read-name` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Canonical source
`arc-record-member` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Canonical source
`arc-release` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Canonical source
`arc-resolve-names` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Canonical source
`arc-size` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-span` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Canonical source
`arc-total` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-view` | 42 Linker and archives | compiler word (create, `cc/141-archive.fth`); Canonical source
`arc-width` | 42 Linker and archives | compiler word (variable, `cc/141-archive.fth`); Canonical source
`arc-write` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Make an archive without a host archiver
`arc-zero` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Canonical source
`lnk-abandon-output` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-accept-object` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-add-archive` | 42 Linker and archives | compiler word (`cc/141-archive.fth`); Validate the envelope before selecting a member
`lnk-add-buffer` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); The public boundary
`lnk-add-object` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); The public boundary
`lnk-align-cap` | 42 Linker and archives | compiler word (constant, `cc/140-cc-link.fth`); Canonical source
`lnk-align` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-alignment` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-bad` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-base-address` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Place bytes and zero-filled memory
`lnk-base` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-binding` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-buffer-a` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-buffer-n` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-byte-cap` | 42 Linker and archives | compiler word (constant, `cc/140-cc-link.fth`); Canonical source
`lnk-cap` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-check-output-alias` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-check-symbol` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-check-unresolved` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-choose` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-copy-sections` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-copy` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-count` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-cursor` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-defined-value` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-done` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-entry-len` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-entry-name` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-entry-value` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-entry` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); The public boundary
`lnk-fd` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-field` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-file-size` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-find-entry` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-find` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-fstat` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-global-cap` | 42 Linker and archives | compiler word (constant, `cc/140-cc-link.fth`); Canonical source
`lnk-global-count` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-globals` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-hash-cap` | 42 Linker and archives | compiler word (constant, `cc/140-cc-link.fth`); Canonical source
`lnk-hash` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-header` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-hex-digits` | 42 Linker and archives | compiler word (create, `cc/140-cc-link.fth`); Canonical source
`lnk-hi` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-hlen` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-hname` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-hslot` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-image` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-index` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-init` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); The public boundary
`lnk-input-cap` | 42 Linker and archives | compiler word (constant, `cc/140-cc-link.fth`); Canonical source
`lnk-input-count` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-inputs` | 42 Linker and archives | compiler word (create, `cc/140-cc-link.fth`); Canonical source
`lnk-layout-section` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-layout` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-length` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-link` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); The public boundary
`lnk-make-temp-path` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-map` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-memory-size` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-multiple24` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-need` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-nl` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-nonnegative` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-note-input` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-np` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-object-cap` | 42 Linker and archives | compiler word (constant, `cc/140-cc-link.fth`); Canonical source
`lnk-object-size` | 42 Linker and archives | compiler word (constant, `cc/140-cc-link.fth`); Canonical source
`lnk-object` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-objects` | 42 Linker and archives | compiler word (create, `cc/140-cc-link.fth`); Canonical source
`lnk-oi` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-old` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-op` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-output-header` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-patch` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-path` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-ph` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-pid` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-place` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-read-file` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-read-object` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-reference` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-register` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-release` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); The public boundary
`lnk-reloc-fail` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-relocate` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-relocation` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-rend` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-resolve` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-resolved-slot` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-roff` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-rp` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-rtype` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-rvalue` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-rw-start` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-rwidth` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-rx-size` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-section-flags` | 42 Linker and archives | compiler word (create, `cc/140-cc-link.fth`); Canonical source
`lnk-section-types` | 42 Linker and archives | compiler word (create, `cc/140-cc-link.fth`); Canonical source
`lnk-section` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-sections` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-selected` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-sh` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-shndx` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-shstr` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-shstrlen` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-si` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-signed32?` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-size` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-slot` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-sp` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-span` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Validate before dereferencing
`lnk-stat-buffer` | 42 Linker and archives | compiler word (create, `cc/140-cc-link.fth`); Canonical source
`lnk-string-base` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-string-end` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-string-size` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-string` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-symbol-cap` | 42 Linker and archives | compiler word (constant, `cc/140-cc-link.fth`); Canonical source
`lnk-symbol-index` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-symbol-name` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-symbol` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-target` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-temp-length` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-temp-path` | 42 Linker and archives | compiler word (create, `cc/140-cc-link.fth`); Canonical source
`lnk-temp-suffix` | 42 Linker and archives | compiler word (create, `cc/140-cc-link.fth`); Canonical source
`lnk-ti` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-u16` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-u32` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-unmap` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-validate-symbol` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-value` | 42 Linker and archives | compiler word (variable, `cc/140-cc-link.fth`); Canonical source
`lnk-w16` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-w32` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-write` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`lnk-zero?` | 42 Linker and archives | compiler word (`cc/140-cc-link.fth`); Canonical source
`cc-sysrt-code` | 43 Runtime, libc, streams, and formatting | compiler word (create, `cc/122-cc-sysv-runtime.fth`); 
`cc-sysrt-errno-code` | 43 Runtime, libc, streams, and formatting | compiler word (create, `cc/122-cc-sysv-runtime.fth`); 
`cc-sysrt-errno-name` | 43 Runtime, libc, streams, and formatting | compiler word (create, `cc/122-cc-sysv-runtime.fth`); 
`cc-sysrt-errno-object` | 43 Runtime, libc, streams, and formatting | compiler word (`cc/122-cc-sysv-runtime.fth`); 
`cc-sysrt-errno-storage` | 43 Runtime, libc, streams, and formatting | compiler word (create, `cc/122-cc-sysv-runtime.fth`); 
`cc-sysrt-exit-name` | 43 Runtime, libc, streams, and formatting | compiler word (create, `cc/122-cc-sysv-runtime.fth`); 
`cc-sysrt-frame-code` | 43 Runtime, libc, streams, and formatting | compiler word (create, `cc/122-cc-sysv-runtime.fth`); 
`cc-sysrt-frame-name` | 43 Runtime, libc, streams, and formatting | compiler word (create, `cc/122-cc-sysv-runtime.fth`); 
`cc-sysrt-frame-object` | 43 Runtime, libc, streams, and formatting | compiler word (`cc/122-cc-sysv-runtime.fth`); 
`cc-sysrt-init-name` | 43 Runtime, libc, streams, and formatting | compiler word (create, `cc/122-cc-sysv-runtime.fth`); 
`cc-sysrt-longjmp-code` | 43 Runtime, libc, streams, and formatting | compiler word (create, `cc/122-cc-sysv-runtime.fth`); Nonlocal return for the original Flex source
`cc-sysrt-longjmp-name` | 43 Runtime, libc, streams, and formatting | compiler word (create, `cc/122-cc-sysv-runtime.fth`); Nonlocal return for the original Flex source
`cc-sysrt-longjmp-object` | 43 Runtime, libc, streams, and formatting | compiler word (`cc/122-cc-sysv-runtime.fth`); Nonlocal return for the original Flex source
`cc-sysrt-main-name` | 43 Runtime, libc, streams, and formatting | compiler word (create, `cc/122-cc-sysv-runtime.fth`); 
`cc-sysrt-name` | 43 Runtime, libc, streams, and formatting | compiler word (create, `cc/122-cc-sysv-runtime.fth`); 
`cc-sysrt-object` | 43 Runtime, libc, streams, and formatting | compiler word (`cc/122-cc-sysv-runtime.fth`); 
`cc-sysrt-runtime-start-code` | 43 Runtime, libc, streams, and formatting | compiler word (create, `cc/122-cc-sysv-runtime.fth`); 
`cc-sysrt-runtime-start-object` | 43 Runtime, libc, streams, and formatting | compiler word (`cc/122-cc-sysv-runtime.fth`); 
`cc-sysrt-setjmp-code` | 43 Runtime, libc, streams, and formatting | compiler word (create, `cc/122-cc-sysv-runtime.fth`); Nonlocal return for the original Flex source
`cc-sysrt-setjmp-name` | 43 Runtime, libc, streams, and formatting | compiler word (create, `cc/122-cc-sysv-runtime.fth`); Nonlocal return for the original Flex source
`cc-sysrt-setjmp-object` | 43 Runtime, libc, streams, and formatting | compiler word (`cc/122-cc-sysv-runtime.fth`); Nonlocal return for the original Flex source
`cc-sysrt-sigreturn-code` | 43 Runtime, libc, streams, and formatting | compiler word (create, `cc/122-cc-sysv-runtime.fth`); 
`cc-sysrt-sigreturn-name` | 43 Runtime, libc, streams, and formatting | compiler word (create, `cc/122-cc-sysv-runtime.fth`); 
`cc-sysrt-sigreturn-object` | 43 Runtime, libc, streams, and formatting | compiler word (`cc/122-cc-sysv-runtime.fth`); 
`cc-sysrt-start-code` | 43 Runtime, libc, streams, and formatting | compiler word (create, `cc/122-cc-sysv-runtime.fth`); 
`cc-sysrt-start-name` | 43 Runtime, libc, streams, and formatting | compiler word (create, `cc/122-cc-sysv-runtime.fth`); 
`cc-sysrt-start-object` | 43 Runtime, libc, streams, and formatting | compiler word (`cc/122-cc-sysv-runtime.fth`); 
`cc-target-name-amd64` | 44 Target headers | compiler word (create, `cc/124-cc-target.fth`); 
`cc-target-name-hosted` | 44 Target headers | compiler word (create, `cc/124-cc-target.fth`); 
`cc-target-name-linux` | 44 Target headers | compiler word (create, `cc/124-cc-target.fth`); 
`cc-target-name-lp64` | 44 Target headers | compiler word (create, `cc/124-cc-target.fth`); 
`cc-target-name-seed` | 44 Target headers | compiler word (create, `cc/124-cc-target.fth`); 
`cc-target-name-stdc` | 44 Target headers | compiler word (create, `cc/124-cc-target.fth`); 
`cc-target-predefines` | 44 Target headers | compiler word (`cc/124-cc-target.fth`); 
`cc-const-a` | 45 Typed constants | compiler word (variable, `cc/125-cc-consteval.fth`); Canonical source
`cc-const-add` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-address-binary` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-address-cast` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-address-index` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-address-unary` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-address?` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-arithmetic?` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-b` | 45 Typed constants | compiler word (variable, `cc/125-cc-consteval.fth`); Canonical source
`cc-const-binary-apply` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-binary` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-bool?` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-boolean` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Floating constants are exact records
`cc-const-cap` | 45 Typed constants | compiler word (constant, `cc/125-cc-consteval.fth`); Canonical source
`cc-const-cast` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-cells` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-change` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Floating constants are exact records
`cc-const-check-integer` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-check-result` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-common` | 45 Typed constants | compiler word (variable, `cc/125-cc-consteval.fth`); Canonical source
`cc-const-conditional-fwd` | 45 Typed constants | compiler word (defer, `cc/125-cc-consteval.fth`); Canonical source
`cc-const-conditional` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-convert` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Keep the numeric boundary explicit
`cc-const-desc` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-divide` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-evaluate` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-extended-compare` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-extended-nan?` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-float-binary` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Floating constants are exact records
`cc-const-float-bool` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Keep the numeric boundary explicit
`cc-const-float-compare` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-float-key` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-float-operand` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-float-spelling` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-float?` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Floating constants are exact records
`cc-const-format` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-from-float` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-initial` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Keep the numeric boundary explicit
`cc-const-int-type` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-integer?` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-left` | 45 Typed constants | compiler word (variable, `cc/125-cc-consteval.fth`); Canonical source
`cc-const-less` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-literal-base` | 45 Typed constants | compiler word (variable, `cc/125-cc-consteval.fth`); Canonical source
`cc-const-literal-check` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-literal-digit` | 45 Typed constants | compiler word (variable, `cc/125-cc-consteval.fth`); Canonical source
`cc-const-literal-value` | 45 Typed constants | compiler word (variable, `cc/125-cc-consteval.fth`); Canonical source
`cc-const-logical-and` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-logical-or` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-multiply` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-new` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-null?` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-op` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-operand` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-promote` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-range` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-right` | 45 Typed constants | compiler word (variable, `cc/125-cc-consteval.fth`); Canonical source
`cc-const-row` | 45 Typed constants | compiler word (variable, `cc/125-cc-consteval.fth`); Canonical source
`cc-const-scalar?` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-select` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-shift` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-sign` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-signed-min` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-slt` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-subtract` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-symbol` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-to-float` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-truth` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Floating constants are exact records
`cc-const-type` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-ult` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-unary-fwd` | 45 Typed constants | compiler word (defer, `cc/125-cc-consteval.fth`); Canonical source
`cc-const-unary` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-unsigned?` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-const-used` | 45 Typed constants | compiler word (variable, `cc/125-cc-consteval.fth`); Canonical source
`cc-const-values` | 45 Typed constants | compiler word (create, `cc/125-cc-consteval.fth`); Canonical source
`cc-f80-new` | 45 Typed constants | compiler word (defer, `cc/125-cc-consteval.fth`); Canonical source
`cc-fp-arith-fwd` | 45 Typed constants | compiler word (defer, `cc/125-cc-consteval.fth`); Floating constants are exact records
`cc-fp-decimal-fwd` | 45 Typed constants | compiler word (defer, `cc/125-cc-consteval.fth`); Floating constants are exact records
`cc-fp-integer-fwd` | 45 Typed constants | compiler word (defer, `cc/125-cc-consteval.fth`); Floating constants are exact records
`cc-fp-resize-fwd` | 45 Typed constants | compiler word (defer, `cc/125-cc-consteval.fth`); Floating constants are exact records
`cc-fp-truncate-fwd` | 45 Typed constants | compiler word (defer, `cc/125-cc-consteval.fth`); Floating constants are exact records
`cc-parse-integer-const` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Keep the numeric boundary explicit
`cc-parse-static-const` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Carry an address without knowing its final location
`cc-parse-target-const` | 45 Typed constants | compiler word (`cc/125-cc-consteval.fth`); Canonical source
`cc-va-arg-name` | 46 System V varargs | compiler word (create, `cc/126-cc-varargs.fth`); Canonical source
`cc-va-arg` | 46 System V varargs | compiler word (`cc/126-cc-varargs.fth`); Canonical source
`cc-va-check-result-type` | 46 System V varargs | compiler word (`cc/126-cc-varargs.fth`); Canonical source
`cc-va-copy-name` | 46 System V varargs | compiler word (create, `cc/126-cc-varargs.fth`); Canonical source
`cc-va-copy-word` | 46 System V varargs | compiler word (`cc/126-cc-varargs.fth`); Canonical source
`cc-va-copy` | 46 System V varargs | compiler word (`cc/126-cc-varargs.fth`); Canonical source
`cc-va-descriptor` | 46 System V varargs | compiler word (`cc/126-cc-varargs.fth`); Canonical source
`cc-va-die` | 46 System V varargs | compiler word (`cc/126-cc-varargs.fth`); Canonical source
`cc-va-end-name` | 46 System V varargs | compiler word (create, `cc/126-cc-varargs.fth`); Canonical source
`cc-va-end` | 46 System V varargs | compiler word (`cc/126-cc-varargs.fth`); Canonical source
`cc-va-error-prefix` | 46 System V varargs | compiler word (create, `cc/126-cc-varargs.fth`); Canonical source
`cc-va-expect` | 46 System V varargs | compiler word (`cc/126-cc-varargs.fth`); Canonical source
`cc-va-field` | 46 System V varargs | compiler word (`cc/126-cc-varargs.fth`); Canonical source
`cc-va-intrinsic` | 46 System V varargs | compiler word (`cc/126-cc-varargs.fth`); Canonical source
`cc-va-last-named` | 46 System V varargs | compiler word (`cc/126-cc-varargs.fth`); Canonical source
`cc-va-last-slot-default` | 46 System V varargs | compiler word (`cc/126-cc-varargs.fth`); Canonical source
`cc-va-last-slot-fwd` | 46 System V varargs | compiler word (defer, `cc/126-cc-varargs.fth`); Four intrinsics with ordinary C spelling
`cc-va-layout-default` | 46 System V varargs | compiler word (`cc/126-cc-varargs.fth`); Canonical source
`cc-va-layout-fwd` | 46 System V varargs | compiler word (defer, `cc/126-cc-varargs.fth`); Canonical source
`cc-va-name?` | 46 System V varargs | compiler word (`cc/126-cc-varargs.fth`); Canonical source
`cc-va-next-address` | 46 System V varargs | compiler word (`cc/126-cc-varargs.fth`); Canonical source
`cc-va-next-double-address` | 46 System V varargs | compiler word (`cc/126-cc-varargs.fth`); Canonical source
`cc-va-next-x87-address` | 46 System V varargs | compiler word (`cc/126-cc-varargs.fth`); Four intrinsics with ordinary C spelling
`cc-va-operand` | 46 System V varargs | compiler word (`cc/126-cc-varargs.fth`); Canonical source
`cc-va-prepare` | 46 System V varargs | compiler word (`cc/126-cc-varargs.fth`); Canonical source
`cc-va-record-default` | 46 System V varargs | compiler word (`cc/126-cc-varargs.fth`); Canonical source
`cc-va-record-fwd` | 46 System V varargs | compiler word (defer, `cc/126-cc-varargs.fth`); Four intrinsics with ordinary C spelling
`cc-va-register-slot` | 46 System V varargs | compiler word (variable, `cc/126-cc-varargs.fth`); Canonical source
`cc-va-save-registers` | 46 System V varargs | compiler word (`cc/126-cc-varargs.fth`); Canonical source
`cc-va-save-xmm` | 46 System V varargs | compiler word (`cc/126-cc-varargs.fth`); Canonical source
`cc-va-signature` | 46 System V varargs | compiler word (variable, `cc/126-cc-varargs.fth`); Save incoming registers before using them
`cc-va-start-name` | 46 System V varargs | compiler word (create, `cc/126-cc-varargs.fth`); Canonical source
`cc-va-start` | 46 System V varargs | compiler word (`cc/126-cc-varargs.fth`); Canonical source
`cc-va-store-frame-address` | 46 System V varargs | compiler word (`cc/126-cc-varargs.fth`); Canonical source
`cc-va-store-u32` | 46 System V varargs | compiler word (`cc/126-cc-varargs.fth`); Canonical source
`cc-va-tag-name` | 46 System V varargs | compiler word (create, `cc/126-cc-varargs.fth`); Canonical source
`cc-va-void-result` | 46 System V varargs | compiler word (`cc/126-cc-varargs.fth`); Canonical source
`cc-bool-convert` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Conversion to `_Bool`
`cc-bool-type?` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-f32-type?` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-f64-a-e` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-a-m` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-a-negative` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-advance` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-allow-hex` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-any-digit` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-arith` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-b-e` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-b-m` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-b-negative` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-bi-a` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-bi-add` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Constant arithmetic on exact pairs
`cc-f64-bi-append` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-bi-b` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-bi-bits` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-bi-carry` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-bi-cell` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-bi-compare` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-bi-copy` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Constant arithmetic on exact pairs
`cc-f64-bi-get` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-bi-i` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-bi-m` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-bi-muladd` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-bi-set` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Constant arithmetic on exact pairs
`cc-f64-bi-shift` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-bi-subtract` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-bi-ten-power` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-bi-times` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Constant arithmetic on exact pairs
`cc-f64-bi-trim` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-bi-zero` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-big-size` | 47 Floating values and exact literals | compiler word (constant, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-d` | 47 Floating values and exact literals | compiler word (create, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-decimal` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Goal and source coverage
`cc-f64-decode` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-e` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-emax` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-emin` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-error-digits-len` | 47 Floating values and exact literals | compiler word (constant, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-error-digits` | 47 Floating values and exact literals | compiler word (create, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-error-exponent-len` | 47 Floating values and exact literals | compiler word (constant, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-error-exponent` | 47 Floating values and exact literals | compiler word (create, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-error-hex-len` | 47 Floating values and exact literals | compiler word (constant, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-error-hex` | 47 Floating values and exact literals | compiler word (create, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-error-malformed-len` | 47 Floating values and exact literals | compiler word (constant, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-error-malformed` | 47 Floating values and exact literals | compiler word (create, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-error-overflow-len` | 47 Floating values and exact literals | compiler word (constant, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-error-overflow` | 47 Floating values and exact literals | compiler word (create, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-error-prefix-len` | 47 Floating values and exact literals | compiler word (constant, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-error-prefix` | 47 Floating values and exact literals | compiler word (create, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-error-suffix-len` | 47 Floating values and exact literals | compiler word (constant, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-error-suffix` | 47 Floating values and exact literals | compiler word (create, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-error-token-len` | 47 Floating values and exact literals | compiler word (constant, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-error-token` | 47 Floating values and exact literals | compiler word (create, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-error-workspace-len` | 47 Floating values and exact literals | compiler word (constant, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-error-workspace` | 47 Floating values and exact literals | compiler word (create, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-exponent-negative` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-exponent` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-fail` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-format` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-fraction` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-fractional` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-has-exponent` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-hex` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-integer` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-left` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-lex` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-f64-limb-cap` | 47 Floating values and exact literals | compiler word (constant, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-literal` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Checked boundaries
`cc-f64-malformed` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-mantissa` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-mask` | 47 Floating values and exact literals | compiler word (constant, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-n` | 47 Floating values and exact literals | compiler word (create, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-negative?` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-normalize` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-number-char?` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-f64-one-denominator` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-operands` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-order` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-overflow` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-p` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-pack` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Constant arithmetic on exact pairs
`cc-f64-parse` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Goal and source coverage
`cc-f64-peek` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-point` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-power` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-product` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-q-carry` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-q` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-quotient` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-radix` | 47 Floating values and exact literals | compiler word (constant, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-ratio` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-read-exponent` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-resize` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-round` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); One rounding step for two widths
`cc-f64-scale` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-scan-hex` | 47 Floating values and exact literals | compiler word (variable, `cc/127-cc-binary64.fth`); Canonical source
`cc-f64-scan-prev` | 47 Floating values and exact literals | compiler word (variable, `cc/127-cc-binary64.fth`); Canonical source
`cc-f64-scan-seen` | 47 Floating values and exact literals | compiler word (variable, `cc/127-cc-binary64.fth`); Canonical source
`cc-f64-scan-start` | 47 Floating values and exact literals | compiler word (variable, `cc/127-cc-binary64.fth`); Canonical source
`cc-f64-sign-of-product` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-sign` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-significant` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-spelling` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-sum` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-t` | 47 Floating values and exact literals | compiler word (create, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-third` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-truncate` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Constant arithmetic on exact pairs
`cc-f64-type?` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-f64-unit` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f64-unpack` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Constant arithmetic on exact pairs
`cc-f64-use` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); One rounding step for two widths
`cc-f80-a-inf` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f80-allocate` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f80-b-inf` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f80-hex-digit?` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f80-hex-mantissa` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f80-hex-value` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f80-inf` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f80-nan-signed` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f80-nan` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f80-resize-nan` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f80-resize-sign` | 47 Floating values and exact literals | compiler word (variable, `cc/128-cc-float-literal.fth`); Canonical source
`cc-f80-round` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f80-special-arith` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-f80-zero` | 47 Floating values and exact literals | compiler word (`cc/128-cc-float-literal.fth`); Canonical source
`cc-fp-binop` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-change-check` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-change-value` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Checked boundaries
`cc-fp-common-type` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-comparison-flags` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-comparison` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-complement` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-convert-right` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-convert` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Conversion to `_Bool`
`cc-fp-double-to-u64` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-flip-sign` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-initialize` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-integer-use` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-jcc` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-negate` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-not` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-prefix` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-rdi-from-xmm0` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-result` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-return` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-scalar-check` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-signed-from-rdi` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-sse` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-storage-type` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-ternary` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-test` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-truncate-rdi` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-type?` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-u64-to-value` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-width-convert` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-xmm0-from-rdi` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-xmm1-from-rax` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-fp-xmm1-from-rcx` | 47 Floating values and exact literals | compiler word (`cc/127-cc-binary64.fth`); Canonical source
`cc-bf-add` | 48 Record bitfields | compiler word (`cc/129-cc-bitfield.fth`); Canonical source
`cc-bf-array-inner` | 48 Record bitfields | compiler word (`cc/129-cc-bitfield.fth`); Canonical source
`cc-bf-desc` | 48 Record bitfields | compiler word (variable, `cc/129-cc-bitfield.fth`); Canonical source
`cc-bf-die` | 48 Record bitfields | compiler word (`cc/129-cc-bitfield.fth`); Canonical source
`cc-bf-enum-desc` | 48 Record bitfields | compiler word (`cc/129-cc-bitfield.fth`); Canonical source
`cc-bf-enum-origin` | 48 Record bitfields | compiler word (create, `cc/129-cc-bitfield.fth`); Canonical source
`cc-bf-error-prefix` | 48 Record bitfields | compiler word (create, `cc/129-cc-bitfield.fth`); Canonical source
`cc-bf-init-offset` | 48 Record bitfields | compiler word (variable, `cc/129-cc-bitfield.fth`); Canonical source
`cc-bf-init-record` | 48 Record bitfields | compiler word (variable, `cc/129-cc-bitfield.fth`); Canonical source
`cc-bf-initializer` | 48 Record bitfields | compiler word (`cc/129-cc-bitfield.fth`); Canonical source
`cc-bf-layout-check` | 48 Record bitfields | compiler word (`cc/129-cc-bitfield.fth`); Canonical source
`cc-bf-load` | 48 Record bitfields | compiler word (`cc/129-cc-bitfield.fth`); Canonical source
`cc-bf-mask` | 48 Record bitfields | compiler word (`cc/129-cc-bitfield.fth`); Canonical source
`cc-bf-member` | 48 Record bitfields | compiler word (`cc/129-cc-bitfield.fth`); Canonical source
`cc-bf-position` | 48 Record bitfields | compiler word (variable, `cc/129-cc-bitfield.fth`); Canonical source
`cc-bf-record-bytes` | 48 Record bitfields | compiler word (`cc/129-cc-bitfield.fth`); Canonical source
`cc-bf-record` | 48 Record bitfields | compiler word (variable, `cc/129-cc-bitfield.fth`); Canonical source
`cc-bf-set-array-inner` | 48 Record bitfields | compiler word (`cc/129-cc-bitfield.fth`); Canonical source
`cc-bf-shift-r8` | 48 Record bitfields | compiler word (`cc/129-cc-bitfield.fth`); Canonical source
`cc-bf-shift-rdi` | 48 Record bitfields | compiler word (`cc/129-cc-bitfield.fth`); Canonical source
`cc-bf-static-initializer` | 48 Record bitfields | compiler word (`cc/129-cc-bitfield.fth`); Canonical source
`cc-bf-store` | 48 Record bitfields | compiler word (`cc/129-cc-bitfield.fth`); Canonical source
`cc-bf-truncate` | 48 Record bitfields | compiler word (`cc/129-cc-bitfield.fth`); Canonical source
`cc-bf-type?` | 48 Record bitfields | compiler word (`cc/129-cc-bitfield.fth`); Canonical source
`cc-bf-unit` | 48 Record bitfields | compiler word (variable, `cc/129-cc-bitfield.fth`); Canonical source
`cc-bf-use` | 48 Record bitfields | compiler word (`cc/129-cc-bitfield.fth`); Canonical source
`cc-bf-value-type` | 48 Record bitfields | compiler word (`cc/129-cc-bitfield.fth`); Canonical source
`cc-bf-width` | 48 Record bitfields | compiler word (variable, `cc/129-cc-bitfield.fth`); Canonical source
`cc-bf?` | 48 Record bitfields | compiler word (`cc/129-cc-bitfield.fth`); Canonical source
`cc-sd-bit-end` | 48 Record bitfields | compiler word (`cc/129-cc-bitfield.fth`); Canonical source
`cc-sf-bit-shift` | 48 Record bitfields | compiler word (`cc/129-cc-bitfield.fth`); Canonical source
`cc-sf-bit-width` | 48 Record bitfields | compiler word (`cc/129-cc-bitfield.fth`); Canonical source
`ag-arg` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`ag-class` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`ag-count` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`ag-desc` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`ag-fp` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`ag-gp` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`ag-indirect` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`ag-live` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`ag-offset` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`ag-register` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`ag-result` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`ag-return-class` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`ag-return-size` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`ag-signature` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`ag-size` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`ag-slot` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`ag-stack` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`ag-target` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`ag-type` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-abi-type` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-argument-check` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-assignment` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-call-begin` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-call` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-cast-types` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-check-entry` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-class` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Carry long double as X87 data
`cc-ag-common-type` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-complement` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-convert` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-copy-to-slot` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-die` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-emit-call` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-error-prefix` | 49 Aggregates and extended floating values | compiler word (create, `cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-field-load` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-frame` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-function-plan` | 49 Aggregates and extended floating values | compiler word (variable, `cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-indirect-call` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-initialize` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-integer-use` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-last-use` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-load-gp` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-load-xmm` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-locate` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-negate` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-new-plan` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-not` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-other` | 49 Aggregates and extended floating values | compiler word (variable, `cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-parameters` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-parse-arguments` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Start with the source and the ABI
`cc-ag-plan` | 49 Aggregates and extended floating values | compiler word (variable, `cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-plus` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-prepare-call` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-result` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-return-check` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-return` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-save-target` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-scalar-use` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-sret-slot` | 49 Aggregates and extended floating values | compiler word (variable, `cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-store-gp` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-store-parameters` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-store-xmm` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-ternary` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-test` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-type?` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-va-last-slot` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-va-layout` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-va-record` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Carry long double as X87 data
`cc-ag-walk-fwd` | 49 Aggregates and extended floating values | compiler word (defer, `cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-walk` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-x87` | 49 Aggregates and extended floating values | compiler word (variable, `cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ag-xmm-local` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ld-compound` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ld-ni-scalar` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ld-scalar-use` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-ld-value-shape` | 49 Aggregates and extended floating values | compiler word (`cc/131-cc-aggregate-abi.fth`); Canonical source
`cc-x87-arithmetic?` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-binop-check` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-binop` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-cast` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-change-check` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-change` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-common` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-convert` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-field-load` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-field-store` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-initialize` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-initializer` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-last?` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-literal` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-load` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-negate` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-ni-scalar` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-not` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-op` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-plus` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-power` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-right` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-save` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-scalar-check` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-shape` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-stage` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-ternary` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-test` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-to-u64` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-truncate` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
`cc-x87-type?` | 49 Aggregates and extended floating values | compiler word (`cc/132-cc-long-double.fth`); Scalar computation source
Diverse double-compiling | 57 Appendix C: historical reproducibility routes | idea; Cross-check against stage0-posix (diverse double-compiling)
GCC-free build | 57 Appendix C: historical reproducibility routes | idea; The GCC-free build
C subset (what is supported) | 60 Appendix F: the C subset | idea; Types
