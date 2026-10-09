# Chapter 06 — Stack and memory primitives

Missing capability: we can locate the seed's stacks but cannot yet audit the words that move their contents.  
New idea: read each primitive as a sequence of register and memory changes that realizes its stack effect.  
Artifact after this chapter: the stack-transfer and memory-access bodies are decoded and ready to trace.  
Payoff link: Chapter 7 uses these operand movements for arithmetic, and Chapter 17 combines them into Forth definitions.

For a reader who knows C and a little assembly, the useful question is concrete:
which instruction preserves a value, which overwrites it, and which changes the
stack boundary? Recall the cached-top pattern from Chapter 4 and the initialized
memory map from Chapter 5; we will apply those contracts without rebuilding them.

| Rung | Built in | Artifact | Relied on by |
|---|---|---|---|
| Machine convention | Chapters 4–5 | Registers and initialized storage | This chapter's primitive bodies |
| **Stack and memory operations** | **Chapter 6** | **Transfers, loads, and stores** | Chapters 7 and 17 |
| Composed operations | Chapters 17 and 22 | Forth definitions using these primitives | Later library and compiler code |

Our route is entry → **stack and memory bodies** → arithmetic → Linux boundary
→ dictionary → compiler → REPL. Chapter 5 made storage available; Chapter 7
will compute with the operands we learn to move here.

## The push and pop shapes

Start with the source's skeleton, before filling in any body: each owned chunk
has a header, a `*_code` label carrying its stack effect, an instruction sequence,
and a final `ret`. The headers are **context** throughout this chapter; Chapter 9
explains them. The instructions below each code label are **focus**. This lets us
keep the source intact while attending to a single operation at a time.

Call the recurring register work **spill-and-reload**, the implementation of the
cached-top pattern from Chapter 4. In the following traces, `p` names the incoming
`rbp`, and letters name arbitrary cell values. Read the stack effects using
Chapter 4's machine convention; Chapter 14 develops their use in Forth definitions.

### `dup`: preserve the old top

To realize `( a -- a a )`, the body must give the cached value a memory slot
without replacing the cache; here is the focus body with its context header in
`forth-bootstrap/seed/000-seed.hex0:76`, immediately after the entry jump.

```hex0 chunk=dup
;; --- dup @ 0x0BA --- header
00 00 00 00 00 00 00 00                   ; link  = 0 (end of chain)
00                                        ; flags = 0
03                                        ; nlen  = 3
64 75 70                                  ; name  = "dup"
;; ----- dup_code @ 0x0C7  ( a -- a a ) -----
48 83 ED 08                               ; sub rbp, 8
48 89 7D 00                               ; mov [rbp], rdi
C3                                        ; ret

```

Now `a` survives both in `rdi` and in the new slot addressed by `rbp`.

Decode `48 83 ED 08` using Chapter 4's REX and ModRM primer: `48` selects the
cell-width operation, `83` takes a short immediate, and `ED` selects register
`rbp` and the subtraction operation. The immediate `08` makes room for a cell.
In `48 89 7D 00`, opcode `89` stores the register operand; ModRM `7D` selects
`rdi` and the displaced `rbp` address. Its trailing `00` is the displacement,
not another instruction. `C3` returns to the caller. There is no assignment to
`rdi`: with input `rdi=a, rbp=p`, the result is `rdi=a, rbp=p-8, [p-8]=a`.

### `drop`: replace the old top

To realize `( a -- )`, reverse the spill-and-reload direction: the focus body at
`forth-bootstrap/seed/000-seed.hex0:86`, following `dup`, promotes the next value.

```hex0 chunk=drop
;; --- drop @ 0x0D0 --- header
BA 00 40 00 00 00 00 00                   ; link  = 0x4000BA (dup)
00                                        ; flags = 0
04                                        ; nlen  = 4
64 72 6F 70                               ; name  = "drop"
;; ----- drop_code @ 0x0DE  ( a -- ) -----
48 8B 7D 00                               ; mov rdi, [rbp]
48 83 C5 08                               ; add rbp, 8
C3                                        ; ret

```

Now the previous value of `rdi` is discarded, and the next value becomes the top.

Opcode `8B` in `48 8B 7D 00` loads through the same displaced `rbp` operand that
`dup` stored through. In `48 83 C5 08`, ModRM `C5` selects addition to `rbp`,
releasing the slot just read; `C3` returns. If `rdi=a` and `[p]=b` on entry,
then `rdi=b` and `rbp=p+8` on return. The released memory need not be erased:
the pointer change removes it from the live stack.

### `swap`: preserve depth, exchange positions

For `( a b -- b a )`, neither value may be lost, so the focus body following
`drop`, at `forth-bootstrap/seed/000-seed.hex0:96`, uses a temporary register.

```hex0 chunk=swap
;; --- swap @ 0x0E7 --- header
D0 00 40 00 00 00 00 00                   ; link  = 0x4000D0 (drop)
00                                        ; flags = 0
04                                        ; nlen  = 4
73 77 61 70                               ; name  = "swap"
;; ----- swap_code @ 0x0F5  ( a b -- b a ) -----
48 8B 45 00                               ; mov rax, [rbp]
48 89 7D 00                               ; mov [rbp], rdi
48 89 C7                                  ; mov rdi, rax
C3                                        ; ret

```

Now the operands have exchanged positions while `rbp` remains unchanged.

In `48 8B 45 00`, ModRM `45` selects `rax` as the destination of the load from
`[rbp]`. The next instruction is the familiar store of `rdi` into that slot.
Finally `48 89 C7` uses a register operand: ModRM `C7` moves `rax` into `rdi`;
`C3` returns. Trace the responsibility of each instruction:

| Point | `rax` | `[p]` | `rdi` |
|---|---|---|---|
| Entry | irrelevant | `a` | `b` |
| After load | `a` | `a` | `b` |
| After store | `a` | `b` | `b` |
| After register move | `a` | `b` | `a` |

The temporary matters because writing `[p]` before saving `a` would destroy an
operand. This is the same hazard as exchanging C variables without a temporary.

## Return-address shelter: bridging the two stacks

Recall the return stack from Chapter 4. These bodies must distinguish the
primitive's own return address from the caller's saved data. Name their recurring
maneuver **return-address shelter**: hold the return address aside while moving
data, then restore it before `ret`. A peek can instead address beyond it.

### `>r`: move a value beneath the return address

The focus body at `forth-bootstrap/seed/000-seed.hex0:107`, following `swap`,
uses return-address shelter to implement `( n -- ; R: -- n )`.

```hex0 chunk=to-r
;; --- >r @ 0x101 --- header
E7 00 40 00 00 00 00 00                   ; link  = 0x4000E7 (swap)
00                                        ; flags = 0
02                                        ; nlen  = 2
3E 72                                     ; name  = ">r"
;; ----- to_r_code @ 0x10D  ( n -- ; R: -- n ) -----
58                                        ; pop rax            ; our own return address
57                                        ; push rdi           ; n onto the return stack
50                                        ; push rax           ; return address back on top
48 8B 7D 00                               ; mov rdi, [rbp]
48 83 C5 08                               ; add rbp, 8
C3                                        ; ret

```

Now the caller's return stack holds `n`, and the data stack has lost that value.

The short register opcodes need no ModRM: `58` pops the primitive's return
address into `rax`, `57` pushes `rdi`, and `50` pushes the sheltered address
back. The remaining load and add are `drop`'s spill-and-reload sequence, followed
by `C3`. Just before `ret`, the address is above `n`; just after it, `n` is
exposed on the caller's return stack.

That exposure is a constraint on the caller: it must remove the saved value
before returning through its own return address. Otherwise a later `ret` would
treat data as an instruction address. Chapter 17 uses balanced transfers in
Forth definitions.

### `r>`: recover the saved value

The inverse transfer needs a free data-stack slot before it overwrites `rdi`,
so the focus body following `>r`, at `forth-bootstrap/seed/000-seed.hex0:120`,
starts with a spill.

```hex0 chunk=r-from
;; --- r> @ 0x119 --- header
01 01 40 00 00 00 00 00                   ; link  = 0x400101 (>r)
00                                        ; flags = 0
02                                        ; nlen  = 2
72 3E                                     ; name  = "r>"
;; ----- r_from_code @ 0x125  ( -- n ; R: n -- ) -----
48 83 ED 08                               ; sub rbp, 8
48 89 7D 00                               ; mov [rbp], rdi
58                                        ; pop rax            ; our own return address
5F                                        ; pop rdi            ; n from the return stack is the new TOS
50                                        ; push rax           ; return address back on top
C3                                        ; ret

```

Now the saved value is the data-stack top, and it has been removed from the
caller's return stack.

The initial subtract and store are exactly `dup`'s spill-and-reload prefix.
Then `58` shelters the return address, `5F` pops the saved value into `rdi`,
and `50` restores the address. `C3` returns with the transfer complete.
Notice why `r>` cannot begin with `pop rdi`: at entry that would recover the
primitive's return address, not the value beneath it.

### `r@`: copy without removing

A read can leave the return address in place; the focus body following `r>`,
at `forth-bootstrap/seed/000-seed.hex0:133`, looks beyond it.

```hex0 chunk=r-at
;; --- r@ @ 0x131 --- header
19 01 40 00 00 00 00 00                   ; link  = 0x400119 (r>)
00                                        ; flags = 0
02                                        ; nlen  = 2
72 40                                     ; name  = "r@"
;; ----- r_at_code @ 0x13D  ( -- n ; R: n -- n ) -----
;; r@ is CALLed, so [rsp] is our own return address and the caller's
;; top of return stack is one cell further, at [rsp+8].
48 8B 44 24 08                            ; mov rax, [rsp+8]   ; skip our ret addr; rax = caller's TOR
48 83 ED 08                               ; sub rbp, 8
48 89 7D 00                               ; mov [rbp], rdi
48 89 C7                                  ; mov rdi, rax
C3                                        ; ret

```

Now the saved value is copied onto the data stack while remaining on the
caller's return stack.

Decode the unfamiliar load `48 8B 44 24 08` with Chapter 4's ModRM and SIB
rules. ModRM `44` selects `rax` and a displaced address with a SIB byte;
SIB `24` selects `rsp` as the base without an index. Displacement `08`
skips the primitive's return address. The subtract and store spill the old
top, `48 89 C7` installs the copy from `rax`, and `C3` returns.

**Peeking does not balance a transfer.** After `>r` followed by `r@`, the
original saved value still needs an `r>` before the caller returns. This is
what distinguishes `( -- n ; R: n -- n )` from `r>`'s effect.

## Cell access: replace an address or consume a pair

The next bodies connect data-stack values to memory. Recall the cell and
little-endian conventions from Chapter 4; these operations use the address
supplied by the caller, which must designate suitable mapped memory.

### `@`: replace an address with its contents

The focus body at `forth-bootstrap/seed/000-seed.hex0:147`, following `r@`,
needs no spill because `( addr -- v )` preserves stack depth.

```hex0 chunk=fetch
;; --- @ @ 0x14E --- header
31 01 40 00 00 00 00 00                   ; link  = 0x400131 (r@)
00                                        ; flags = 0
01                                        ; nlen  = 1
40                                        ; name  = "@"
;; ----- fetch_code @ 0x159  ( addr -- v ) -----
48 8B 3F                                  ; mov rdi, [rdi]
C3                                        ; ret

```

Now `rdi` contains the cell read from the address that `rdi` held on entry.

In `48 8B 3F`, ModRM `3F` selects `rdi` as both the destination register and
the base of an undisplaced memory operand. The processor uses the old register
value to calculate the address before replacing it with the load result.
`C3` returns; `rbp` has not moved. For a C reader, the operation resembles
replacing a pointer-sized integer with the cell obtained by dereferencing it.

### `!`: store, then consume the operands

The address is cached above the value, so the focus body following `@`, at
`forth-bootstrap/seed/000-seed.hex0:156`, first loads the value into a temporary.

```hex0 chunk=store
;; --- ! @ 0x15D --- header
4E 01 40 00 00 00 00 00                   ; link  = 0x40014E (@)
00                                        ; flags = 0
01                                        ; nlen  = 1
21                                        ; name  = "!"
;; ----- store_code @ 0x168  ( v addr -- ) -----
48 8B 45 00                               ; mov rax, [rbp]     ; rax = v
48 89 07                                  ; mov [rdi], rax     ; *addr = v
48 83 C5 08                               ; add rbp, 8
48 8B 7D 00                               ; mov rdi, [rbp]
48 83 C5 08                               ; add rbp, 8
C3                                        ; ret

```

Now memory contains the supplied cell, and both operands have left the data stack.

The opening `48 8B 45 00` is `swap`'s load into `rax`. In `48 89 07`, ModRM
`07` selects a store from `rax` through the undisplaced address in `rdi`.
The first add advances past the value's slot; the load restores the value
beneath the consumed pair; the final add releases that restored value's old
memory slot. `C3` returns.

For a destination outside the live stack, trace `rdi=addr, [p]=v, [p+8]=older`:
the store writes `v` to `addr`, then leaves `rdi=older, rbp=p+16`. The cached address
never occupied a slot at `[p]`; spill-and-reload accounts for the pointer
movement through the value cells.

## Byte access: change the memory width

### `c@`: widen a byte into a cell

The focus body following `!`, at `forth-bootstrap/seed/000-seed.hex0:169`,
keeps `@`'s stack effect but loads a byte instead of a cell.

```hex0 chunk=cfetch
;; --- c@ @ 0x17C --- header
5D 01 40 00 00 00 00 00                   ; link  = 0x40015D (!)
00                                        ; flags = 0
02                                        ; nlen  = 2
63 40                                     ; name  = "c@"
;; ----- cfetch_code @ 0x188  ( addr -- b ) -----
48 0F B6 3F                               ; movzx rdi, byte [rdi]
C3                                        ; ret

```

Now the top contains the byte's unsigned value, with all higher bits clear.

The opcode pair `0F B6` selects a zero-extending byte load, while `48` gives
the destination cell width. ModRM `3F` is the same destination-and-address
selection as in `@`; `C3` returns. No old address bits survive the replacement,
and `rbp` stays put.

### `c!`: narrow the store, preserve the cleanup

To realize `( b addr -- )`, the focus body following `c@`, at
`forth-bootstrap/seed/000-seed.hex0:178`, changes the store instruction while
retaining `!`'s operand cleanup.

```hex0 chunk=cstore
;; --- c! @ 0x18D --- header
7C 01 40 00 00 00 00 00                   ; link  = 0x40017C (c@)
00                                        ; flags = 0
02                                        ; nlen  = 2
63 21                                     ; name  = "c!"
;; ----- cstore_code @ 0x199  ( b addr -- ) -----
48 8B 45 00                               ; mov rax, [rbp]     ; rax = b
88 07                                     ; mov [rdi], al      ; store the low byte only
48 83 C5 08                               ; add rbp, 8
48 8B 7D 00                               ; mov rdi, [rbp]
48 83 C5 08                               ; add rbp, 8
C3                                        ; ret

```

Now only the addressed byte has changed, and both data-stack operands are consumed.

The load into `rax` still fetches a complete value cell. But `88 07` is a byte
store from `al`, the low byte of `rax`, through `rdi`; it has no cell-width REX
prefix. Higher bits of the supplied value are not written, and neighboring
bytes in memory are left alone. The add, reload, add, and `C3` follow `!`
exactly. Distinguish **store width** from **operand width**: narrowing the memory
write does not change how many stack operands the word consumes.

Chapter 22 combines these accesses into memory-update words. Their definitions
are outside this instruction walkthrough.

## Exercises

- **Trace — easy.** Starting from `[p]=a, rdi=b`, follow `swap` and then
  `drop`; name the surviving top and the final `rbp` relative to `p`.
- **Trace — medium.** Draw the return stack just before and just after each
  instruction in `>r`, labeling the primitive's return address separately from
  the saved data; explain why replacing the balancing `r>` with `r@` fails.
- **Verify — easy.** In the checkpoint disassembly, match each operand to the
  `swap` trace above; identify the instruction that prevents `a` from being lost.

## Try it

Run these commands from the `forth-bootstrap` checkout, at `./forth-bootstrap`
relative to the book repository. The build writes `seed-forth`
(`forth-bootstrap/seed/build.sh:27`). The first command below rebuilds that
complete image; the disassembly is a **focus** view of its `swap` body, and the
pipeline is a **context** smoke test using only this chapter's stack words.

```sh
./seed/build.sh
objdump -D -b binary -m i386:x86-64 -Mintel --start-address=0xf5 --stop-address=0x101 seed-forth
printf 'dup dup swap drop >r r@ drop r> drop\n' | ./seed-forth
printf 'exit status %s\n' "$?"
# prints "exit status 0"
```

The smoke test prints nothing itself, and the shell then reports its exit
status, 0. It checks that the balanced sequence runs; it does not inspect the resulting values or exercise
the memory-access words. Use the disassembly to verify the distinct-operand
trace of `swap`. End-of-input terminates the seed
(`forth-bootstrap/seed/000-seed.hex0:668`); Chapter 12 explains that loop.
Here is the output observed from the commands above:

```text
Built seed-forth (1772 bytes) using vendor/stage0-posix/bootstrap-seeds/POSIX/AMD64/hex0-seed

seed-forth:     file format binary


Disassembly of section .data:

00000000000000f5 <.data+0xf5>:
  f5:	48 8b 45 00          	mov    rax,QWORD PTR [rbp+0x0]
  f9:	48 89 7d 00          	mov    QWORD PTR [rbp+0x0],rdi
  fd:	48 89 c7             	mov    rdi,rax
 100:	c3                   	ret
exit status 0
```

