# Chapter 4 — x86-64 encoding and the two-stack machine

When `hello` runs, it supplies a number to `emit`. Where does that number
wait, and how does `emit` get it? Forth words pass values through a
**data stack**. We will first follow that stack, then see where the seed
stores it, and finally read the bytes of instructions that change it.

By the end, you can explain the seed's two stacks, decode a small load or
store, and calculate where a relative jump lands. These are the tools we
need to open the executable in Chapter 5.

## Values before storage

A stack keeps values in order and gives access to the most recently added
one, called the **top**. Adding a value is a **push**; removing the top is
a **pop**. In our written traces, the top is on the right. Thus `72 105`
means that 72 was added first and 105 is now on top.

During `hello`, the first literal supplies 72 to the data stack, and
`emit` consumes it to print `H`. Then the next literal supplies 105 for
`emit` to print `i`. Any values beneath those characters remain in place.
A different word, `dup`, duplicates the top without changing its value:

| Before `dup` | After `dup` | What changed |
|---|---|---|
| `72 105` | `72 105 105` | A second copy of 105 is now on top |

This is the word's effect, independent of where the values are stored.
We can also write the values as `a b c` when their particular numbers do
not matter. The rightmost value, `c`, is still the top.

## The machine before the instructions

The processor has a small set of named storage locations called
**registers**, such as `rdi` and `rbp`. These registers each hold 64 bits.
Memory is addressed by byte: an **address** is the number used to locate
a byte, and a **pointer** is a value used as an address. A register can
hold a number we are calculating with, or an address of data in memory.

The seed keeps the current top in register `rdi`. Older stack values live
in memory, and `rbp` holds the address of the next one down. In assembly
notation, `rdi` means the value in that register; `[rbp]` means memory at
the address held in `rbp`. The brackets make a different operation: look
through the pointer rather than use the pointer's own numeric value.

A hardware `call` instead saves the address of the following instruction on the stack addressed by `rsp`; `ret` takes an address from there and resumes execution at it. Neither instruction performs a data-stack push or pop. The return stack can also hold explicitly saved Forth data, so a routine must distinguish its own return address from that data. Chapter 6 explains how the transfer words preserve that distinction.

The data stack answers “which values is this word working on?” The
return stack answers “where should execution resume when this call
finishes?” Keeping those questions separate will matter whenever a word
calls another word.

For example, entering `emit` must save a return address while leaving the
character ready for `emit` to consume. Separate stacks let both happen:
the return address goes on one, and the character stays on top of the
other. A word can therefore find its operands in the same places however
deeply calls are nested. The seed's choice of `rsp` for returns and
`rdi`/`rbp` for data implements that separation on x86-64; those register
names are choices of this implementation, not part of a Forth word's
interface.

A *cell* in this seed is an eight-byte, 64-bit value. If the logical data stack holds `a`, then `b`, then `c` with `c` on top, the live values are arranged like this; the separate return-stack panel shows the state while a called routine is running.

<figure class="mechanism" aria-labelledby="stacks-caption">
<div class="mechanism-title">A logical stack is split between a register and memory</div>
<div class="diagram-routes diagram-stacks">
<div><span class="diagram-label">Data stack · logical order a b c</span><div class="stack-register diagram-accent"><span class="diagram-label">CPU register</span><code>rdi</code><strong>c · cached top</strong></div><div class="stack-memory"><span class="diagram-label">Data-stack memory</span><div class="memory-cell"><code>[rbp]</code><strong>b · second item</strong></div><div class="memory-cell"><code>[rbp + 8]</code><strong>a · older item</strong></div></div><span>Push: rbp moves to a lower address; the old rdi is stored there.</span></div>
<div><span class="diagram-label">Return stack · separate storage</span><div class="memory-cell diagram-accent"><code>[rsp]</code><strong>Current return address</strong></div><div class="memory-cell"><span>Higher addresses</span><span>Older return addresses or explicitly saved data</span></div><span>call pushes a return address; ret consumes one.</span></div>
</div>
<figcaption id="stacks-caption">Each data-stack memory cell is eight bytes. Within each memory region, rows run toward higher addresses, while pushes grow toward lower addresses. The cached c is in a register, not a memory cell above b. Hardware call and ret affect the return stack, not the logical data stack.</figcaption>
</figure>

`rbp` points to the second item on the stack; it does not point to `rdi`. A data-stack push preserves the old `rdi` by moving `rbp` downward and storing there. It then installs a new top in `rdi`. Call this the **cached-top pattern**. A data-stack pop reverses that movement by loading the next value into `rdi` and moving `rbp` upward.

The source records the register assignments in `forth-bootstrap/seed/000-seed.hex0:53–61`:

| Register | Seed role | Named chunks that use it |
| --- | --- | --- |
| `rdi` | Cached top of stack | `dup`, `drop`, `plus` |
| `rbp` | Points at the second item on the stack | `entry-point`, `dup`, `drop` |
| `rsp` | Pointer to the return stack, also used by hardware calls | `to-r`, `r-from`, `r-at` |
| `rbx` | Length of the last token read | `read-word` |
| `rax`, `rcx`, `rdx`, `rsi` | Working registers whose meanings depend on the routine | `find`, `read-word`, `syscall6` |

The source labels sometimes differ from chunk names: `to_r_code` is in `to-r`, for example. Chapter 6 walks through the stack transfers; Chapter 9 explains token handling.

## Reading hexadecimal bytes

A byte has eight bits. Each hexadecimal digit represents four of them,
so an instruction written `48 83 ED 08` occupies four bytes. The prefix
`0x` marks a hexadecimal number in prose: `0x10` is decimal 16.

A multi-byte number here is **little-endian**: its least significant
byte comes first. For example, the bytes `34 12` encode `0x1234`, because
`0x34 + 256 × 0x12 = 0x1234`. This orders the bytes of a field, not all
the bytes of an instruction. First identify the field; then read its value.

## A skeleton for reading bytes

Start with an instruction boundary established by the source, rather than guessing from an arbitrary byte in the image. An x86 instruction has a variable layout: the opcode determines which of these pieces are present.

```text
prefixes       select operand properties or extend register fields
opcode         selects the operation and operand direction
ModRM          selects registers or a memory-addressing form, if needed
SIB            adds scale/index/base addressing, if needed
displacement / immediate   address adjustment / literal operand
```

Follow **prefix → opcode → operands → next address**. That last step matters because the next instruction does not begin at a fixed distance from the current one.

The source uses Intel operand order: `mov destination, source`. Thus
`mov [rbp], rdi` stores the value from `rdi` into memory at `rbp`; it does
not change `rbp`. A **displacement** adjusts a memory address, whereas an
**immediate operand** supplies a value directly. For example,
`sub rbp, 8` subtracts the immediate value 8 from the pointer itself.

## ModRM: where do the operands live?

Return to `dup`. Suppose `rdi` holds the top value 105 and `rbp` points
to the older value 72. To keep two copies of 105, the seed first subtracts
8 from `rbp`, making room for an eight-byte cell. Then it stores 105 at
the new address, leaving 105 in `rdi` as well. The logical stack is now
`72 105 105`: the old 72 did not move, but the pointer did.

Here is that store (`forth-bootstrap/seed/000-seed.hex0:83`). The byte
line is copied verbatim; the following comments annotate its encoding.

```text
48 89 7D 00                               ; mov [rbp], rdi
; 48       REX prefix: use a full-width operand
; 89       opcode: move register into register-or-memory operand
; 7D       ModRM: 01 | 111 | 101
; 00       signed displacement: zero
```

`48` selects a 64-bit operand for this instruction. Opcode `89` takes its source from the ModRM register field and its destination from the register-or-memory field. The ModRM byte divides into a two-bit `mod` field, a three-bit `reg`
field, and a three-bit `r/m` field. To see the split, hexadecimal `7` is
binary `0111`, and hexadecimal `D` (decimal 13) is binary `1101`.
Together `7D` is `01111101`; grouping those eight bits gives
`01 | 111 | 101`:

| Part of `7D` | Decoded meaning here |
| --- | --- |
| `01` | Memory addressing with a signed byte displacement |
| `111` | Register code 7: `rdi`, the source |
| `101` | Base-register code 5: `rbp` |
| Following `00` | Add zero to that base address |

The destination is memory at `rbp`, and the value comes from `rdi`: `mov [rbp], rdi`. The instruction occupies four bytes. The explicit zero displacement is necessary for this encoding of an `rbp` base: the no-displacement mode with that base code has a special meaning instead.

For reference, the unextended full-width register codes are:

| Code | Register | Code | Register |
| --- | --- | --- | --- |
| 0 | `rax` | 4 | `rsp` |
| 1 | `rcx` | 5 | `rbp` |
| 2 | `rdx` | 6 | `rsi` |
| 3 | `rbx` | 7 | `rdi` |

The opcode determines whether `reg` names the source. The load at `forth-bootstrap/seed/000-seed.hex0:92` reverses the move direction: `48 8B 7D 00` uses opcode `8B` to load `rdi` from `[rbp]`.

With `mod=11`, the `r/m` field names a register instead of memory. The move at `forth-bootstrap/seed/000-seed.hex0:104`, `48 89 C7`, has ModRM fields `11 | 000 | 111` and means `mov rdi, rax`. Some opcodes use the `reg` field to select an operation rather than a register. Decode the opcode before assigning operands.

Not every memory operand stops at ModRM. A SIB byte provides scale, index, and base fields when the addressing form requires it. The instruction at `forth-bootstrap/seed/000-seed.hex0:141`, `48 8B 44 24 08`, uses a SIB byte to address `[rsp+8]`; do not mistake `24` for another opcode. Chapter 6 decodes that return-stack access in context.

**Pause and predict.** In the schematic load `48 8B 45 08`, which
register receives a value, which address is read, and does `rbp` change?

<details>
<summary>Check the changed load</summary>

ModRM `45` splits into `01 | 000 | 101`: a signed-byte displacement,
destination `rax`, base `rbp`. The load reads `[rbp+8]` into `rax`.
It does not change `rbp`; addressing a different slot is not moving
the stack boundary.

</details>

## REX: width and extended registers

On a first pass, keep the full-width `48` prefix in mind; return to the
extension bits below when Chapter 8 uses `r9`. The displacement rules
in the next section are needed throughout the seed walkthrough.

A REX prefix has the bit layout `0100WRXB`. `W` requests a 64-bit operand for the moves used here; `R` extends the ModRM `reg` field; `X` extends a SIB index; `B` extends the base or register field selected by the encoding. The prefix `48` is `01001000`, so only `W` is set.

The load in `syscall6` uses REX to select an extended register as well as the operand width (`forth-bootstrap/seed/000-seed.hex0:309`):

```text
4C 8B 4D 00                               ; mov r9, [rbp]      ; f
; 4C       REX prefix: W and R set
; 8B       opcode: move register-or-memory operand into register
; 4D       ModRM: 01 | 001 | 101
; 00       signed displacement: zero
```

Apply prefix → opcode → operands → next address. `4C` is `01001100`: both `W` and `R` are set. `8B` makes the register field the destination. ModRM `4D` divides as `01 | 001 | 101`; its base remains `rbp`, but the destination code is extended from 1 to 9, giving `r9`. The final zero byte is the displacement, so the result is `mov r9, [rbp]`, ending after four bytes. Chapter 8 explains why that value belongs in `r9`.

A REX prefix can matter even when all of its extension bits are clear. The byte store at `forth-bootstrap/seed/000-seed.hex0:268`, `40 88 38`, stores `dil`, the low byte of `rdi`, through `rax`. The `40` prefix makes that byte-register selection mean `dil`; do not discard it as redundant. Also distinguish a full register from its narrower aliases: writing `eax` clears the upper half of `rax`, while writing `dil` changes only the low byte of `rdi`.

## rel32: count from the next instruction

A relative branch encodes a distance, not an absolute destination. The seed's entry jump in `jmp-to-repl` uses a signed displacement (`forth-bootstrap/seed/000-seed.hex0:74`):

```text
E9 DF 05 00 00                            ; jmp repl  (rel32 = 0x699 - 0x0BA)
; E9          opcode: near relative jump
; DF 05 00 00 signed little-endian displacement
; 0x0B5       start of this instruction, as a file offset
; 0x0BA       position immediately after this instruction
```

`E9` is followed by a signed 32-bit displacement. Reading `DF 05 00 00` little-endian gives `0x05DF`, or 1503. The instruction begins at file offset `0x0B5` and occupies five bytes, so the next instruction is at offset `0x0BA`. Add the displacement there:

`target = next address + signed displacement = 0x0BA + 0x05DF = 0x699`.

The source identifies `0x699` as `repl`. File offsets suffice for this subtraction because both locations receive the same load-address adjustment; Chapter 5 establishes that adjustment. A backward displacement is negative and is encoded in two's complement. The same next-address rule applies to `E8` relative calls, which additionally save that next address on the return stack. Chapter 10 uses this rule when emitting calls; Chapter 11 covers the seed's Forth branch words.

### Reading a negative displacement

First assemble the field's bytes as an unsigned number `u`. For a signed
field of `w` bits, its value is `u` when the high bit is clear and
`u - 2^w` when the high bit is set. The width belongs to the field:
`rel8` has 8 bits; `rel32` has 32. This is the reading rule for two's
complement; Chapter 17 derives the corresponding negation operation.

For example, the dictionary's backward jump is `EB E8`
(`forth-bootstrap/seed/000-seed.hex0:350`). Here `EB` is the opcode and
`E8` is a one-byte displacement, not another opcode. Its unsigned value is
232, so its signed value is `232 - 256 = -24`. The next instruction is at
offset `0x344`; the target is `0x344 - 24 = 0x32C`. The rule is still
**add the signed distance to the next address**.

Try a changed, schematic case before revealing the answer: an `E9`
instruction begins at `0x200` and has displacement bytes `F8 FF FF FF`.
Where does it jump? Separately, what address does a signed byte
displacement `FC` select in `[rax + displacement]` when `rax = 0x200`?

<details>
<summary>Check the field width and address base</summary>

`F8 FF FF FF` is unsigned `0xFFFFFFF8`, or `2^32 - 8`, so the signed
distance is `-8`. The five-byte instruction ends at `0x205`; its target is
`0x1FD`. Using the start would give the wrong answer, `0x1F8`.
`FC` is unsigned 252 in an eight-bit field, hence `-4`. The memory
operand selects `0x1FC`: a memory displacement is added to its base
register, not to the next instruction. Return to the field-width rule if
you got a large positive distance; return to the instruction skeleton if
you added at the wrong base.

</details>

The same registers will later carry requests into Linux. We will learn
that separate convention in [Chapter 8](08-seed-io.md#the-linux-register-boundary),
when `emit` needs it. For now, keep the data stack, return address, and
next-instruction address distinct while checking the entry jump.

## Try it: read the entry jump

Check the entry jump’s bytes in the built executable, then compare your hand-decoded destination with the disassembler’s result. This uses the host's `objdump` from GNU binutils; Chapter 5 uses its companion `readelf` to inspect ELF headers.

From the `forth-bootstrap` source directory, build the seed. The script
selects the assembler and writes `seed-forth` there
(`forth-bootstrap/seed/build.sh:12–29`):

```sh
./seed/build.sh
```

Observed output:

```text
Built seed-forth (1772 bytes) using vendor/stage0-posix/bootstrap-seeds/POSIX/AMD64/hex0-seed
```

In the same `forth-bootstrap` directory, read the entry jump's bytes:

```sh
od -A x -t x1 -j 0xb5 -N 5 seed-forth
```

Observed output:

```text
0000b5 e9 df 05 00 00
0000ba
```

Decode the displacement and add it to the next instruction’s offset. Cross-check with:

```sh
objdump -D -b binary -m i386:x86-64 --start-address=0xb5 --stop-address=0xba seed-forth
```

Observed output:

```text

seed-forth:     file format binary


Disassembly of section .data:

00000000000000b5 <.data+0xb5>:
  b5:	e9 df 05 00 00       	jmp    0x699
```

## Exercise

**Trace (easy).** Decode `48 8B 45 00` at
`forth-bootstrap/seed/000-seed.hex0:102` without looking at its assembly
comment. Name the destination, effective address, and instruction length.
Then change only the last byte to `F8` on paper and assume `rbp=0x200`.
Which address does the changed instruction read? Identify the fields that
choose the operand width, destination register, and memory address.

For a second trace, recover the entry jump's destination from its bytes. What error results from adding the displacement at the instruction's start instead of its end?

<details>
<summary>Hint: separate the register field from the displacement</summary>

Split `45` into `mod | reg | r/m` before using the register-code table.
Then interpret the final byte at the width selected by `mod`; do not use
the register's width for that field.

</details>

<details>
<summary>Check the changed load and the jump</summary>

`48` selects a 64-bit operand, `8B` loads into the register field, and
`45` splits as `01 | 000 | 101`: destination `rax`, base `rbp`, signed
byte displacement. The original is the four-byte `mov rax, [rbp]`.
With `F8`, the displacement is `248-256=-8`, so the load reads at `0x1F8`;
it does not change `rbp`. If you chose `rdi`, recheck the `reg` field.
If you chose `0x2F8`, recheck the displacement's signed width.

The entry jump uses `0x0BA + 0x05DF = 0x699`. Starting at `0x0B5`
instead would give `0x694`, five bytes too early. Relative control flow
uses the next instruction; the changed load uses its base register.

</details>
