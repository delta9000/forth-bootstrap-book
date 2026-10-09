# Chapter 12 — Decimal parsing and the REPL

You can read the seed's primitives, but you have not yet followed how an input stream selects them or supplies decimal values. A token loop joins dictionary lookup to execution and compilation, while `[lit]` requests decimal conversion explicitly. By the end, you can build the complete seed and trace input through its REPL.

## The shape of the loop

The REPL's skeleton is **read → look up → execute or compile → repeat**.
End of input exits; a lookup miss reports the token and returns to reading.
There is no number-parser branch after a miss. A decimal token reaches the
parser only when `[lit]` reads it as its argument.

Keep these routes separate: the REPL decides what to do with a word, and
`[lit]` decides what to do with a value. `[lit]` reads a decimal value and either leaves it on the
stack or compiles a literal. Its conversion helper is the missing piece.

## Decimal conversion: `parse_decimal_code`

`parse_decimal_code` accepts `( c-addr u )` and returns either `( n true )`
or `( 0 false )`. Its skeleton is **reject empty input → accumulate digits
→ return value and flag**. It is an internal helper, without a dictionary
entry; typing its label does not call it.

Empty input must fail before the helper attempts a byte load. The setup in
`forth-bootstrap/seed/000-seed.hex0:633` takes the address into `rsi`, checks
the length, and initializes an accumulator and a remaining-byte counter.

```hex0 chunk=parse-decimal
;; ----- parse_decimal_code @ 0x644  ( c-addr u -- n true | 0 false ) -----
;; Not a dictionary word ([lit] calls it).  Unsigned decimal only: an
;; empty token or any byte outside '0'..'9' fails.  n = n*10 + digit.
48 8B 75 00                               ; mov rsi, [rbp]     ; rsi = c-addr
48 83 C5 08                               ; add rbp, 8
48 85 FF                                  ; test rdi, rdi
74 38                                     ; jz .fail  (rel8 = 0x689 - 0x651)      ; empty token
48 31 C0                                  ; xor rax, rax       ; n = 0
48 89 F9                                  ; mov rcx, rdi       ; rcx = bytes left
```

The accumulator `rax` starts at zero. The counter `rcx` starts at the
supplied length. Neither register carries a Forth result until conversion
succeeds.

Each byte must pass the digit check before it changes the accumulator.
The digit loop in `forth-bootstrap/seed/000-seed.hex0:642` implements
**decimal accumulation**, `n = n * 10 + digit`.

```hex0 chunk=parse-decimal
;; .loop:
48 0F B6 16                               ; movzx rdx, byte [rsi]
48 83 EA 30                               ; sub rdx, 0x30      ; - '0'
78 28                                     ; js .fail  (rel8 = 0x689 - 0x661)      ; below '0'
48 83 FA 09                               ; cmp rdx, 9
7F 22                                     ; jg .fail  (rel8 = 0x689 - 0x667)      ; above '9'
48 8D 04 80                               ; lea rax, [rax+rax*4] ; n * 5
48 01 C0                                  ; add rax, rax       ; n * 10
48 01 D0                                  ; add rax, rdx       ; + digit
48 FF C6                                  ; inc rsi
48 FF C9                                  ; dec rcx
75 DE                                     ; jnz .loop  (rel8 = 0x657 - 0x679)
```

Subtracting ASCII `'0'` gives the digit value. `js` rejects a byte below
`'0'`; the comparison against 9 rejects a byte above `'9'`. A leading minus
sign, a base prefix, or a letter therefore rejects the whole token. This
parser does not return a successfully converted prefix.

`lea` forms five times the old accumulator; `add rax, rax` doubles it.
Adding the digit completes the decimal accumulation. For `42`, the
successive values are `0 * 10 + 4 = 4` and `4 * 10 + 2 = 42`.
The loop advances the address and reduces the remaining length after each
accepted digit. There is no overflow check: arithmetic keeps only the
bits that fit in the accumulator.

The caller needs to distinguish a parsed zero from failure. The return
paths in `forth-bootstrap/seed/000-seed.hex0:654` therefore supply a flag
alongside the value.

```hex0 chunk=parse-decimal
48 83 ED 08                               ; sub rbp, 8
48 89 45 00                               ; mov [rbp], rax     ; push n
48 C7 C7 FF FF FF FF                      ; mov rdi, -1        ; true
C3                                        ; ret
;; .fail:
48 83 ED 08                               ; sub rbp, 8
48 C7 45 00 00 00 00 00                   ; mov qword [rbp], 0 ; push 0
48 31 FF                                  ; xor rdi, rdi       ; false
C3                                        ; ret

```

Success stores the accumulator beneath a true flag (-1); failure stores
zero there and clears the flag. The separate flag lets the caller
accept zero without confusing it with rejection.

## The REPL loop

The loop needs a token before it can choose a word. Its entry in
`forth-bootstrap/seed/000-seed.hex0:664` connects `read_word` directly to
`find_code`; recall those interfaces from Chapter 9 (The dictionary and
token reader).

```hex0 chunk=repl
;; ----- repl @ 0x699  read a token, find it, run or compile it; loop -----
;; Not a dictionary word.  _start jumps here; it never returns.
E8 23 FD FF FF                            ; call read_word  (rel32 = 0x3C1 - 0x69E) ; ( -- c-addr u )
48 85 FF                                  ; test rdi, rdi
0F 84 93 FB FF FF                         ; jz bye_code  (rel32 = 0x23A - 0x6A7)  ; u = 0: end of input, exit(0)
E8 57 FC FF FF                            ; call find_code  (rel32 = 0x303 - 0x6AC) ; ( c-addr u -- xt | 0 )
48 85 FF                                  ; test rdi, rdi
75 0F                                     ; jnz .found  (rel8 = 0x6C0 - 0x6B1)
```

An empty token takes the end-of-input exit. Otherwise lookup consumes the
token's address and length, leaving an execution token on a match or zero
on a miss. The branch to `.found` separates successful lookup from recovery.

A miss must restore the stack before reading again. The recovery path in
`forth-bootstrap/seed/000-seed.hex0:672` reports the token, discards the
lookup result, and jumps back to the loop entry.

```hex0 chunk=repl
;; Miss: print the token and '?', drop the 0, read on.
E8 A3 FD FF FF                            ; call report_token  (rel32 = 0x459 - 0x6B6)
48 8B 7D 00                               ; mov rdi, [rbp]
48 83 C5 08                               ; add rbp, 8
EB D9                                     ; jmp repl  (rel8 = 0x699 - 0x6C0)
```

Recall `report_token` from Chapter 9: it reports the rejected token with
`?`. The reload after that call matters because reporting clobbers `rdi`.
Restoring the prior top afterward preserves the stack across the miss.
There is no call to the decimal parser along this route: bare `42` is a
name to look up, just like any other token.

A found word needs a dispatch decision. The tail in
`forth-bootstrap/seed/000-seed.hex0:677` tests the IMMEDIATE flag before
STATE and hands ordinary words to `compile_call` in compile mode; recall
all three from Chapter 10 (The colon compiler).

```hex0 chunk=repl
;; .found:
48 8B 04 25 18 30 41 00                   ; mov rax, [LAST_FOUND]
0F B6 48 08                               ; movzx ecx, byte [rax+8] ; flags
F6 C1 01                                  ; test cl, 1         ; IMMEDIATE?
75 14                                     ; jnz .execute  (rel8 = 0x6E5 - 0x6D1)  ; yes: run it now, in either mode
48 8B 04 25 00 30 41 00                   ; mov rax, [STATE]
48 85 C0                                  ; test rax, rax
74 07                                     ; jz .execute  (rel8 = 0x6E5 - 0x6DE)   ; interpret mode: run it
E8 8A FE FF FF                            ; call compile_call  (rel32 = 0x56D - 0x6E3) ; compile mode: CALL xt at HERE
EB B4                                     ; jmp repl  (rel8 = 0x699 - 0x6E5)
;; .execute:
E8 CA FC FF FF                            ; call execute_code  (rel32 = 0x3B4 - 0x6EA)
EB AD                                     ; jmp repl  (rel8 = 0x699 - 0x6EC)
```

The order gives an immediate word priority over compilation state.
An ordinary word reaches `compile_call` only when STATE is nonzero;
otherwise it reaches `execute_code`. Both routes consume the execution token and
return control to the input loop when their work returns.

This is **REPL dispatch**: lookup chooses the word, then its flag and STATE
choose when it runs. The REPL itself never emits a numeric literal.

## Why no auto-number parsing?

Consider `[lit] 42 emit`. Lookup finds `[lit]`, and its immediate flag sends
it to execution. That word reads `42` itself, calls the decimal parser,
and leaves the converted value for `emit`. The REPL next reads `emit`,
looks it up, and executes it. The decimal token never passes through
REPL lookup.

In `: star [lit] 42 emit ;`, the dispatch of `[lit]` is the same. The
compilation state changes what happens inside that word: it emits a
literal instead of leaving the value for immediate use. `emit` follows
the ordinary-word compilation route. When `star` later runs, its compiled
literal supplies the value to its compiled call of `emit`.

A malformed decimal argument takes a different error route from a
lookup miss. `[lit]` uses the parser's false flag to enter `fatal_token`,
the exit path from Chapter 9. The checkpoint below contrasts an unknown
numeric name with a malformed argument to `[lit]`.

## Accounting for the seed

`parse_decimal_code` is 85 bytes and `repl` is 83 bytes. Together they add
168 bytes to the walkthrough.

**Running count: 1,772 of 1,772 bytes read.**

| Chapter | What you read | Bytes | Running total |
|---------|---------------|------:|--------------:|
| 5 | ELF, entry, and the memory map | 186 | 186 |
| 6 | Stack and memory primitives | 242 | 428 |
| 7 | Arithmetic and logic in machine code | 129 | 557 |
| 8 | The seed’s Linux boundary | 200 | 757 |
| 9 | The dictionary and token reader | 493 | 1,250 |
| 10 | The colon compiler | 287 | 1,537 |
| 11 | Branches and inline cells | 67 | 1,604 |
| 12 | Decimal parsing and the REPL | 168 | 1,772 |

These totals include dictionary headers as well as instructions. They
come from the offsets and sizes printed by
`python3 tools/check-numbers.py --dump`; `./check.sh` checks each row
against the chunks its chapter defines.

Chapter 13 collects the primitive contracts as a reference. Chapter 14
begins using the seed to build the Forth library.

## Exercises

- **Trace — easy.** Follow `: star [lit] 42 emit ; star` through the
  dispatch paths. Which input tokens does the REPL read, and which does
  another word consume? Identify when decimal conversion happens and
  when output happens.
- **Trace — intermediate.** Move the stack reload in the miss path before
  `report_token` on paper. Explain why the reordered path fails to preserve
  the prior stack top.

## Try it

Run these commands from the `forth-bootstrap` checkout. From the book
repository, enter it with `cd forth-bootstrap`.

Build the seed with its supplied script:

```sh
seed/build.sh
```

Observed output:

```text
Built seed-forth (1772 bytes) using vendor/stage0-posix/bootstrap-seeds/POSIX/AMD64/hex0-seed
```

Confirm that the REPL accepts `bye`:

```sh
echo 'bye' | ./seed-forth
printf 'exit status: %s\n' "$?"
```

Observed output (`bye` itself is silent):

```text
exit status: 0
```

Exercise decimal conversion first through interpretation, then through a
compiled definition. Recall `emit` from Chapter 8 (The seed’s Linux
boundary); the final literal supplies a newline.

```sh
echo '[lit] 42 emit [lit] 10 emit bye' | ./seed-forth # prints "*"
echo ': star [lit] 42 emit ; star [lit] 10 emit bye' | ./seed-forth # prints "*"
```

Observed output:

```text
*
*
```

Finally, compare a lookup miss with a rejected decimal argument. Capture
the failing status in the shell so the final command can report it.

```sh
echo '42 bye' | ./seed-forth # prints "42?"
printf 'exit status: %s\n' "$?"
echo '[lit] 12a bye' | ./seed-forth || printf 'exit status: %s\n' "$?"
```

Observed output:

```text
42?
exit status: 0
12a?
exit status: 2
```
