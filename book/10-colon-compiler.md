# Chapter 10 — The colon compiler

`: double dup + ;` defines a new word that doubles the top of the stack. The colon compiler writes a native call for each ordinary word
in a definition and a return instruction at its end. With inline literals,
those definitions can also carry values to use when they run.

## Start with an empty body

The smallest definition is `: empty ;`. The colon reads `empty` as the
new name and opens its body; the semicolon closes it. Running `empty`
then returns without changing the data stack. A useful body grows between
those delimiters: `: letter [lit] 65 emit ;` will emit `A` when called.

Keep compilation and execution separate. While reading the definition,
the compiler writes instructions at HERE. Later, calling `letter` runs
those instructions. This arrangement is **subroutine threading**: a
compiled word calls the native code of its component words.

## `colon_code`: give the body a name

The new body needs a header before it can receive instructions; recall the
header layout from Chapter 9 (The dictionary and token reader).
The `:` entry and its implementation in
`forth-bootstrap/seed/000-seed.hex0:515` construct that header at HERE:

```hex0 chunk=colon
;; --- : @ 0x4E2 --- header
CD 04 40 00 00 00 00 00                   ; link  = 0x4004CD (')
00                                        ; flags = 0
01                                        ; nlen  = 1
3A                                        ; name  = ":"
;; ----- colon_code @ 0x4ED  ( -- ) read a name, lay down its header at HERE, STATE = 1 -----
E8 CF FE FF FF                            ; call read_word  (rel32 = 0x3C1 - 0x4F2) ; ( -- c-addr u )
48 8B 0C 25 08 30 41 00                   ; mov rcx, [LATEST]
48 8B 14 25 10 30 41 00                   ; mov rdx, [HERE]    ; rdx = the new entry
48 89 0A                                  ; mov [rdx], rcx     ; link  = old LATEST
C6 42 08 00                               ; mov byte [rdx+8], 0 ; flags = 0
40 88 7A 09                               ; mov [rdx+9], dil   ; nlen  = u
48 89 14 25 08 30 41 00                   ; mov [LATEST], rdx  ; the new entry is the newest
48 89 F9                                  ; mov rcx, rdi       ; count = u
48 8B 75 00                               ; mov rsi, [rbp]     ; from = c-addr
48 8D 7A 0A                               ; lea rdi, [rdx+10]  ; to = the name field
F3 A4                                     ; rep movsb          ; copy the name; rdi ends just past it
48 89 3C 25 10 30 41 00                   ; mov [HERE], rdi    ; HERE = entry + 10 + u
48 8B 7D 08                               ; mov rdi, [rbp+8]   ; drop c-addr and u
48 83 C5 10                               ; add rbp, 16
48 C7 04 25 00 30 41 00 01 00 00 00       ; mov qword [STATE], 1
C3                                        ; ret

```

The first call obtains the name through `read_word`, recalled from
Chapter 9. The code captures the old LATEST in `rcx` and the allocation
address in `rdx`. It writes the new entry's link, clears its flags, stores
the name length, and makes the entry LATEST.

For the name copy, `rcx` becomes the count, `rsi` the source, and `rdi`
the destination. `rep movsb` copies the name and leaves `rdi` at the
start of the body. Saving that address in HERE lets subsequent emissions
follow the header without a separate allocation step.

The final instructions discard the name and length, restore the earlier
data-stack top, and set STATE to 1. That value requests compilation;
STATE equal to 0 requests interpretation. The header is already linked,
but the body is still unfinished. The compiler has not written a return
instruction yet.

## Why `;` is IMMEDIATE

A closing delimiter must act while the definition is being compiled.
An ordinary body word contributes a call to be executed later. If `;`
did that, it would leave compilation active instead of closing the body.
Its IMMEDIATE flag requests execution during compilation. Chapter 12
follows the dispatch code that honors this flag; Chapter 23 builds the
Forth-level tools for setting it.

Closing the body requires an emitted return and a state change, as shown
by the `;` entry in `forth-bootstrap/seed/000-seed.hex0:538`:

```hex0 chunk=semicolon
;; --- ; @ 0x53F --- header  IMMEDIATE
E2 04 40 00 00 00 00 00                   ; link  = 0x4004E2 (:)
01                                        ; flags = 1 (IMMEDIATE)
01                                        ; nlen  = 1
3B                                        ; name  = ";"
;; ----- semicolon_code @ 0x54A  ( -- ) IMMEDIATE: append ret, STATE = 0 -----
48 8B 04 25 10 30 41 00                   ; mov rax, [HERE]
C6 00 C3                                  ; mov byte [rax], 0xC3 ; the ret opcode
48 FF C0                                  ; inc rax
48 89 04 25 10 30 41 00                   ; mov [HERE], rax
48 C7 04 25 00 30 41 00 00 00 00 00       ; mov qword [STATE], 0
C3                                        ; ret

```

There are different jobs for the return instructions here. The store of
`0xC3` appends a `ret` to the new word. The final `C3` in
`semicolon_code` returns from the compiler operation itself. Between
those actions, HERE advances past the emitted byte and STATE becomes 0.
For `empty`, that emitted `ret` is the entire body.

## `compile_call`: append a body instruction

A nonempty body needs calls between its header and its closing return.
The helper `compile_call` consumes the target execution token and writes
the call at HERE. It has no dictionary entry: compiler code calls it
directly.

Recall rel32 branches from Chapter 4; the call emitter in
`forth-bootstrap/seed/000-seed.hex0:551` applies that encoding to the
current allocation address:

```hex0 chunk=compile-call
;; ----- compile_call @ 0x56D  ( xt -- ) lay down CALL xt (E8 rel32) at HERE -----
;; Not a dictionary word: the REPL's compile path and [lit] share it.
48 8B 04 25 10 30 41 00                   ; mov rax, [HERE]
C6 00 E8                                  ; mov byte [rax], 0xE8 ; the CALL opcode
48 83 C0 05                               ; add rax, 5         ; rax = address after the CALL
48 29 C7                                  ; sub rdi, rax       ; rel32 = xt - (HERE + 5)
89 78 FC                                  ; mov [rax-4], edi
48 89 04 25 10 30 41 00                   ; mov [HERE], rax    ; HERE += 5
48 8B 7D 00                               ; mov rdi, [rbp]
48 83 C5 08                               ; add rbp, 8
C3                                        ; ret

```

After writing the opcode, the helper advances `rax` to the end of the
call. It subtracts that address from the target in `rdi`, stores the
result through `edi`, and commits `rax` to HERE. It then consumes the
target from the data stack.

The body of `: twice letter letter ;` therefore consists of calls to
`letter` followed by the return emitted by `;`. This is subroutine
threading again: calling a compiled word uses the same body instruction
as calling a primitive. The compiler needs the target address, not the
source that produced it.

## `lit_code` and the inline-cell trick

A call carries a destination, but `letter` also needs a value to pass to
`emit`. The compiler places that value immediately after a call to
`lit_code`. Call this the **inline-cell convention**: a helper reads data
beside its call and resumes execution beyond it.

The return address identifies the inline cell, so the runtime in
`forth-bootstrap/seed/000-seed.hex0:563` can recover the value without
receiving an explicit pointer:

```hex0 chunk=lit
;; --- lit @ 0x593 --- header
3F 05 40 00 00 00 00 00                   ; link  = 0x40053F (;)
00                                        ; flags = 0
03                                        ; nlen  = 3
6C 69 74                                  ; name  = "lit"
;; ----- lit_code @ 0x5A0  ( -- v ) push the 8-byte cell after the CALL, skip it -----
58                                        ; pop rax            ; rax = return address = the cell
48 83 ED 08                               ; sub rbp, 8
48 89 7D 00                               ; mov [rbp], rdi
48 8B 38                                  ; mov rdi, [rax]     ; TOS = the cell
48 83 C0 08                               ; add rax, 8         ; step past it
50                                        ; push rax
C3                                        ; ret                ; resume after the cell

```

`pop rax` takes the address of the cell off the return stack. The next
instructions preserve the old data-stack top and load the cell into
`rdi`. Before returning, `lit_code` advances `rax` past the cell and
pushes that adjusted address back onto the return stack.

Without the adjustment, `ret` would try to execute the literal's bytes.
With it, execution resumes at the following body instruction. The inline
cell is data even though it lives among instructions. Chapter 11 uses
this convention for branch destinations.

## `bracket_lit_code`: write what `lit_code` will read

`lit_code` runs when a compiled definition executes. `[lit]` supplies its
input earlier, when the definition is compiled. Like `;`, `[lit]` is
IMMEDIATE because it must act while the compiler is reading the body.
It reads the following token as a decimal value; the conversion routine
it calls belongs to Chapter 12.

The same literal syntax also works outside a definition, so
`forth-bootstrap/seed/000-seed.hex0:577` selects its action using STATE:

```hex0 chunk=bracket-lit
;; --- [lit] @ 0x5B2 --- header  IMMEDIATE
93 05 40 00 00 00 00 00                   ; link  = 0x400593 (lit)
01                                        ; flags = 1 (IMMEDIATE)
05                                        ; nlen  = 5
5B 6C 69 74 5D                            ; name  = "[lit]"
;; ----- bracket_lit_code @ 0x5C1  ( -- n ) IMMEDIATE: read a decimal number -----
;; Interpret mode: leave n on the stack.  Compile mode: compile CALL lit
;; and the cell n.  A token that is not a decimal number is fatal.
E8 FB FD FF FF                            ; call read_word  (rel32 = 0x3C1 - 0x5C6) ; ( -- c-addr u )
E8 79 00 00 00                            ; call parse_decimal_code  (rel32 = 0x644 - 0x5CB) ; ( c-addr u -- n flag )
48 85 FF                                  ; test rdi, rdi
0F 84 A3 FE FF FF                         ; jz fatal_token  (rel32 = 0x477 - 0x5D4) ; not a number: report and exit
48 8B 7D 00                               ; mov rdi, [rbp]
48 83 C5 08                               ; add rbp, 8         ; drop the flag: ( n )
48 8B 04 25 00 30 41 00                   ; mov rax, [STATE]
48 85 C0                                  ; test rax, rax
75 01                                     ; jnz .compile  (rel8 = 0x5EA - 0x5E9)
C3                                        ; ret                ; interpret: n stays on the stack
;; .compile:
48 83 ED 08                               ; sub rbp, 8
48 89 7D 00                               ; mov [rbp], rdi
BF A0 05 40 00                            ; mov edi, 0x4005A0 ; ( n lit-xt )
E8 71 FF FF FF                            ; call compile_call  (rel32 = 0x56D - 0x5FC) ; ( n ) CALL lit
E9 82 FD FF FF                            ; jmp comma_code  (rel32 = 0x383 - 0x601) ; ( ) the cell n, tail call

```

After conversion, the data stack contains the value and a success flag.
A false flag takes the fatal-error path, recalled from Chapter 9.
Otherwise the code drops the flag and tests STATE. In interpretation
mode it returns with the value on the data stack.

The compile path preserves the value while placing `lit_code`'s execution
token above it. `compile_call` consumes that token and emits the call,
leaving the value ready to append. Recall `,` from Chapter 9: the final
jump delegates the cell write to `comma_code`. Its return goes directly
to the caller of `[lit]`.

For `: letter [lit] 65 emit ;`, compilation proceeds as follows:

- `:` creates the entry named `letter` and starts its body.
- `[lit]` reads `65` and emits a call to `lit_code` followed by the cell.
- `emit` contributes a call to the existing primitive.
- `;` appends the return instruction and leaves compilation mode.

No call to `[lit]` appears in that body. When `letter` runs, `lit_code`
loads the cell and returns past it, `emit` consumes the value, and the
body's final return finishes the call. Defining `twice` in terms of
`letter` adds another level of calls without changing this sequence.

## Try it

From the book repository, enter the source checkout with
`cd forth-bootstrap`. Build the complete seed:

```sh
./seed/build.sh
```

Observed output:

```text
Built seed-forth (1772 bytes) using vendor/stage0-posix/bootstrap-seeds/POSIX/AMD64/hex0-seed
```

Run this checkpoint from the same checkout. It compiles `letter`, compiles
calls to it inside `twice`, then executes `twice`. The final `[lit]`
runs in interpretation mode and supplies the newline to `emit`.

```sh
printf '%s\n' ': letter [lit] 65 emit ; : twice letter letter ; twice [lit] 10 emit bye' | ./seed-forth
# prints "AA\n"
```

Observed output:

```text
AA
```

## Exercise

**Trace — easy.** Follow the return addresses when `twice` calls `letter`
in the checkpoint above. Which return address does `lit_code` adjust?
Which return instruction brings execution back into `twice`? Explain why
the inline cell is never executed as an instruction.
