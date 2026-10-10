# Chapter 7 — Arithmetic and logic in machine code

The seed has one logic primitive, `nand`, beside `+`, `0=`, `/` and `*`.
This chapter ties each one's result and stack effect to its
machine code, then runs all five at the REPL. Chapter 16 builds logic on these contracts,
Chapter 17 builds subtraction, and Chapter 20 builds comparisons.

Recall the stack and memory operations from Chapter 6 and the
instruction-decoding conventions from Chapter 4.

The path through the seed is: stack and memory → **arithmetic and logic** →
Linux boundary → dictionary → compiler → REPL. Chapter 8 takes the next step;
the library definitions remain in Part 2.

## The shape before the instructions

Recall the cached-top pattern from Chapter 4 and the slot-release operation
from Chapter 6. For a binary operation on `a b`, the skeleton is:

> Read `a` from `[rbp]`, combine it with `b`, release `a`'s slot, and
> leave the result in `rdi` before returning.

Call this the **binary reduction pattern**. Some bodies compute directly in
`rdi`; others use temporary registers and copy the answer back. `0=` is the
unary exception: it replaces the top without releasing a slot.

Each primitive's instructions follow its dictionary header. Chapter 9
teaches those headers.

## Addition contract

<a id="plus-contract"></a>

**`+` — `( a b -- sum )`:** retain the cell-sized low part of `a+b`.
The return stack is unchanged after the return; `rdi` holds the sum and
`rbp` advances by a cell.

In `forth-bootstrap/seed/000-seed.hex0:191`, `plus_code` adds the memory
operand directly into the cached operand, without a temporary register.

```hex0 chunk=plus
;; --- + @ 0x1AC --- header
8D 01 40 00 00 00 00 00                   ; link  = 0x40018D (c!)
00                                        ; flags = 0
01                                        ; nlen  = 1
2B                                        ; name  = "+"
;; ----- plus_code @ 0x1B7  ( a b -- a+b ) -----
48 03 7D 00                               ; add rdi, [rbp]
48 83 C5 08                               ; add rbp, 8
C3                                        ; ret

```

`48 03` selects the cell-width register-from-memory addition.
The remaining addressing bytes select `rdi` and `[rbp]`, using Chapter 4's
ModRM rules. The following `add rbp, 8`
is stack bookkeeping, not part of the numeric result. `ret` completes the
same return convention used in Chapter 6.

The body is 9 bytes. It has no branch on carry or signed overflow, so the
result wraps modulo the cell range. Unlike signed overflow in C, wrapping
here is a property of the actual instruction sequence. Chapter 17 uses
this [addition contract](#plus-contract) for subtraction.

## Bitwise NAND contract

<a id="nand-contract"></a>

**`nand` — `( a b -- bits )`:** return the cell-wide complement of `a & b`.
This is a bitwise operation; its inputs need not be truth values.

In `forth-bootstrap/seed/000-seed.hex0:201`, `nand_code` computes NAND
with AND followed by NOT, using the same binary reduction pattern.

```hex0 chunk=nand
;; --- nand @ 0x1C0 --- header
AC 01 40 00 00 00 00 00                   ; link  = 0x4001AC (+)
00                                        ; flags = 0
04                                        ; nlen  = 4
6E 61 6E 64                               ; name  = "nand"
;; ----- nand_code @ 0x1CE  ( a b -- ~(a&b) ) -----
48 23 7D 00                               ; and rdi, [rbp]
48 F7 D7                                  ; not rdi
48 83 C5 08                               ; add rbp, 8
C3                                        ; ret

```

`48 23` selects AND into the register, and `48 F7 D7` complements `rdi`;
the stack-release and return instructions repeat addition's ending.
The body is 12 bytes. A bit in the result is clear exactly when the
corresponding bits in both inputs are set. This is C's `~(a & b)` on
cell-sized unsigned bit patterns, not C's logical `!(a && b)`.

Chapter 16 derives the library logic words from this
[NAND contract](#nand-contract).

## Zero-test contract

<a id="zero-equal-contract"></a>

**`0=` — `( n -- flag )`:** return zero for nonzero input and an all-set
cell for zero input; interpreted as a signed cell, that true value is `-1`.
`rbp` does not move.

In `forth-bootstrap/seed/000-seed.hex0:212`, `zeq_code` turns an instruction
condition into a full-cell flag by testing, materializing, widening, and
negating the result.

```hex0 chunk=zeq
;; --- 0= @ 0x1DA --- header
C0 01 40 00 00 00 00 00                   ; link  = 0x4001C0 (nand)
00                                        ; flags = 0
02                                        ; nlen  = 2
30 3D                                     ; name  = "0="
;; ----- zeq_code @ 0x1E6  ( n -- flag ) -----
48 85 FF                                  ; test rdi, rdi
40 0F 94 C7                               ; sete dil           ; dil = (rdi == 0)
48 0F B6 FF                               ; movzx rdi, dil
48 F7 DF                                  ; neg rdi            ; 1 -> -1 (Forth true)
C3                                        ; ret

```

`test rdi, rdi` sets the zero condition without changing the operand.
`sete dil` writes a byte containing zero or one. Because that write leaves
the rest of `rdi` untouched, `movzx rdi, dil` is necessary before
negation: it removes the old operand's remaining bits. Finally, `neg rdi`
turns one into `-1` and leaves zero unchanged. The body is 15 bytes.

Recall REX from Chapter 4: the `40` prefix on `sete dil` selects the low-byte
register naming that includes `dil`; without it, this encoding names `bh`.
The prefix matters even though no extended register is involved.

This **canonical flag** convention lets a true result also serve as an
all-set bit mask. It does not make arbitrary outputs of `nand` canonical:
only a zero test guarantees this normalization. Chapter 19's predicates
can refer to this [zero-test contract](#zero-equal-contract).

## Unsigned division contract

<a id="divide-contract"></a>

**`/` — `( a b -- quotient )`:** interpret both operands as unsigned cells,
require a nonzero divisor `b`, and return the integer quotient, discarding
the remainder. It clobbers `rax` and `rdx` as well as updating the data-stack
registers.

In `forth-bootstrap/seed/000-seed.hex0:224`, `divide_code` uses temporary
registers to supply the dividend where the processor requires it, then
finishes the binary reduction pattern.

```hex0 chunk=divide
;; --- / @ 0x1F5 --- header
DA 01 40 00 00 00 00 00                   ; link  = 0x4001DA (0=)
00                                        ; flags = 0
01                                        ; nlen  = 1
2F                                        ; name  = "/"
;; ----- divide_code @ 0x200  ( a b -- a/b ) unsigned 64-bit divide -----
;; rdx:rax / rdi -> rax = quotient, rdx = remainder.  rdx is zeroed, so the
;; dividend is 64-bit.  b = 0 traps (SIGFPE); callers must not pass it.
48 8B 45 00                               ; mov rax, [rbp]     ; rax = a (dividend)
48 31 D2                                  ; xor rdx, rdx       ; high half = 0
48 F7 F7                                  ; div rdi            ; rdx:rax / rdi
48 83 C5 08                               ; add rbp, 8         ; pop a
48 89 C7                                  ; mov rdi, rax       ; TOS = quotient
C3                                        ; ret

```

The order matters. `mov rax, [rbp]` loads the dividend `a`, while `rdi`
retains the divisor `b`. `xor rdx, rdx` clears the high half of the
processor's dividend pair, `rdx:rax`. `div rdi` places the quotient in
`rax` and the remainder in `rdx`. Releasing the consumed slot and moving
`rax` into `rdi` restores the primitive's exit contract. The remainder is
not a Forth result. The body is 18 bytes.

An old remainder in `rdx` would change the next dividend, so clearing the
high half is necessary for correctness.
With the high half clear and a nonzero cell-sized divisor, the quotient
fits in a cell.

The opcode is unsigned `DIV`, not signed `IDIV`. An all-set cell is therefore
treated as the largest unsigned operand, even though we call the same bit
pattern `-1` when interpreting a canonical flag. Division by zero has no
fallback in this body; the source identifies it as a trap. Do not use it
as ordinary input.
Chapter 20 builds comparisons from this [division contract](#divide-contract).

## Low-product contract

<a id="multiply-contract"></a>

**`*` — `( a b -- product )`:** retain the low cell of the product, with
wrapping on overflow. `rax` is temporary; the result returns in `rdi`.

In `forth-bootstrap/seed/000-seed.hex0:239`, `star_code` computes the
product through `rax`, then finishes the binary reduction pattern.

```hex0 chunk=star
;; --- * @ 0x212 --- header
F5 01 40 00 00 00 00 00                   ; link  = 0x4001F5 (/)
00                                        ; flags = 0
01                                        ; nlen  = 1
2A                                        ; name  = "*"
;; ----- star_code @ 0x21D  ( a b -- a*b ) signed 64-bit multiply, low half -----
48 89 F8                                  ; mov rax, rdi       ; rax = b
48 0F AF 45 00                            ; imul rax, [rbp]    ; rax = a*b (low 64 bits)
48 83 C5 08                               ; add rbp, 8         ; pop a
48 89 C7                                  ; mov rdi, rax       ; TOS = a*b
C3                                        ; ret

```

`mov rax, rdi` copies `b`; `imul rax, [rbp]` multiplies it by `a`.
This form of `IMUL` keeps only the low cell in its destination. It does
not produce a separate high-half result in `rdx`. The final move restores
the cached top, and the body occupies 16 bytes.

Although the instruction is named signed multiply, signed and unsigned
interpretations give the same low cell of the product. This is why the
[multiplication contract](#multiply-contract) can describe bit patterns
without choosing a signed interpretation. Division cannot make that same
promise: its quotient depends on the interpretation of the operands.

## Contracts for Part 2

The Part 2 library words build on these contracts.

| Primitive contract | Result rule | Later reader |
|---|---|---|
| [`+`](#plus-contract) | Low cell of the sum | Chapter 17, subtraction |
| [`nand`](#nand-contract) | Cell-wide `~(a & b)` | Chapter 16, logic |
| [`0=`](#zero-equal-contract) | Canonical flag for zero | Chapter 19, predicates |
| [`/`](#divide-contract) | Unsigned quotient; divisor must be nonzero | Chapter 20, comparisons |
| [`*`](#multiply-contract) | Low cell of the product | Part 2 arithmetic users |

## Try it: complete-seed arithmetic checkpoint

This checkpoint uses the complete seed; Chapter 12 explains its REPL
implementation.

Recall the initialized cached zero from Chapter 5. The first `dup`
preserves it while the first `0=` supplies an all-set operand. The arithmetic
results in order are `-1`, `-2`, `4`, `1`, `-2`, and `0`: addition doubles the flag,
multiplication squares that result, division divides the square by itself,
and NAND complements the intersection before the final zero test.
The final `drop`, from Chapter 6, restores the initial stack state.

The checkpoint checks successful exit and absence of diagnostics; it does
not assert printed values. The result sequence above is a worked trace.
It needs no output word or literal-loading word from a later chapter.
End of input exits the complete seed.

The seed writes its unknown-word diagnostic to standard output
(`echo nosuchword | ./seed-forth` prints `nosuchword?`), so empty output
means no diagnostic. The shell wrapper prints its message only when the
output is empty.

Run these commands from the `forth-bootstrap` checkout. The build command
in `forth-bootstrap/seed/build.sh:27` writes `seed-forth` there.

```sh
./seed/build.sh > /dev/null
output=$(printf '%s\n' 'dup 0= dup + dup * dup / dup nand 0= drop' | ./seed-forth) &&
  test -z "$output" && printf '%s\n' 'Arithmetic checkpoint: clean exit, no diagnostics.'
# prints "Arithmetic checkpoint: clean exit, no diagnostics."
```

Observed output from this command:

```text
Arithmetic checkpoint: clean exit, no diagnostics.
```

## Exercise

**Trace — easy.** Trace `test`, `sete`, `movzx`, and `neg` in `zeq_code`
for an input with a set bit outside its low byte. Which instruction keeps
that bit out of the false result? Why does the body need no slot-release
instruction?

**Trace — moderate.** Trace the checkpoint's stack on paper, using signed
notation for the all-set cell. After each arithmetic word, record the
cached top and whether `rbp` moved. Why does division receive a nonzero
divisor even though the sequence begins with zero?
