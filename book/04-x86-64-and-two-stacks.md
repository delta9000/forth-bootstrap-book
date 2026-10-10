# Chapter 4 — x86-64 encoding and the two-stack machine

The bytes `48 83 ED 08` mean `sub rbp, 8`: they make room for one more cell on the seed's data stack. Reading the seed means decoding bytes like these against its register and stack conventions. This chapter gives a register map and a repeatable method for checking instructions by hand; Chapter 5 applies it to the executable headers and entry code.

## The machine before the instructions

The seed's register assignments differ from those of a C function prologue. Its data stack and the processor's call stack occupy separate places. The register convention appears in `forth-bootstrap/seed/000-seed.hex0:53–61`:

| Register | Seed role | Named chunks that use it |
| --- | --- | --- |
| `rdi` | Cached top of stack | `dup`, `drop`, `plus` |
| `rbp` | Points at the second item on the stack | `entry-point`, `dup`, `drop` |
| `rsp` | Pointer to the return stack, also used by hardware calls | `to-r`, `r-from`, `r-at` |
| `rbx` | Length of the last token read | `read-word` |
| `rax`, `rcx`, `rdx`, `rsi` | Working registers whose meanings depend on the routine | `find`, `read-word`, `syscall6` |

The source labels sometimes differ from chunk names: `to_r_code` is in `to-r`, for example. Chapter 6 walks through the stack transfers; Chapter 9 explains token handling.

A *cell* is an eight-byte, 64-bit value. If the logical data stack holds `a`, then `b`, then `c` with `c` on top, the live values are arranged like this; the right side sketches the return stack while a called routine is running.

```text
Data stack                         Return stack
rdi       c  (cached top)           rsp -> current return address
rbp ->    b                        higher addresses: older return
rbp+8 ->  a                        addresses or explicitly saved data
Memory grows downward on push      Hardware pushes grow downward too
```

`rbp` points to the second item on the stack; it does not point to `rdi`. A data-stack push preserves the old `rdi` by moving `rbp` downward and storing there. It then installs a new top in `rdi`. Call this the **cached-top pattern**. A data-stack pop reverses that movement by loading the next value into `rdi` and moving `rbp` upward.

A hardware `call` instead saves the address of the following instruction on the stack addressed by `rsp`; `ret` takes an address from there and resumes execution at it. Neither instruction performs a data-stack push or pop. The return stack can also hold explicitly saved Forth data, so a routine must distinguish its own return address from that data. Chapter 6 explains how the transfer words preserve that distinction.

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

The source uses Intel operand order: `mov destination, source`; brackets mean memory at an address. A displacement adjusts a memory address, whereas an immediate operand supplies a value directly. Multi-byte values in these examples are little-endian: the least significant byte comes first. Chapter 5 applies that byte order to the executable's fields.

## ModRM: where do the operands live?

The store in `dup` shows the cached-top pattern (`forth-bootstrap/seed/000-seed.hex0:83`). The byte line is copied verbatim; the following comments annotate its encoding.

```text
48 89 7D 00                               ; mov [rbp], rdi
; 48       REX prefix: use a full-width operand
; 89       opcode: move register into register-or-memory operand
; 7D       ModRM: 01 | 111 | 101
; 00       signed displacement: zero
```

`48` selects a 64-bit operand for this instruction. Opcode `89` takes its source from the ModRM register field and its destination from the register-or-memory field. The ModRM byte divides into a two-bit `mod` field, a three-bit `reg` field, and a three-bit `r/m` field:

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

## REX: width and extended registers

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

`E9` is followed by a signed 32-bit displacement. Reading `DF 05 00 00` little-endian gives `0x05DF`, or 1503. The instruction begins at file offset `0x0B5` and occupies five bytes, so its following address is at offset `0x0BA`. Add the displacement there:

`target = next address + signed displacement = 0x0BA + 0x05DF = 0x699`.

The source identifies `0x699` as `repl`. File offsets suffice for this subtraction because both locations receive the same load-address adjustment; Chapter 5 establishes that adjustment. A backward displacement is negative and is encoded in two's complement. The same next-address rule applies to `E8` relative calls, which additionally save that next address on the return stack. Chapter 10 uses this rule when emitting calls; Chapter 11 covers the seed's Forth branch words.

## The Linux register boundary

The Linux syscall register convention temporarily gives registers a different job. The syscall number goes in `rax` and arguments go, in order, in `rdi`, `rsi`, `rdx`, `r10`, `r8`, and `r9`. The result comes back in `rax`; `syscall` clobbers `rcx` and `r11`. The argument register after `rdx` is `r10`, not the C function-call convention's `rcx`.

The setup and transition in `emit` show how to read a request from its registers (`forth-bootstrap/seed/000-seed.hex0:269–273`). Chapter 8 covers the scratch-buffer store immediately before it.

```text
B8 01 00 00 00                            ; mov eax, 1         ; SYS_write
BF 01 00 00 00                            ; mov edi, 1         ; fd 1 (stdout)
48 BE 00 20 41 00 00 00 00 00             ; mov rsi, 0x412000  ; buf (movabs)
BA 01 00 00 00                            ; mov edx, 1         ; count 1
0F 05                                     ; syscall            ; clobbers rcx, r11
```

The request is `write(stdout, buffer, count)`: `eax=1` chooses Linux `write`, `edi=1` selects standard output, `rsi` holds the buffer address, and `edx=1` asks for one byte. The narrower register writes also establish the corresponding full-width values. `0F 05` then enters the kernel. This is a syscall transition, not a Forth `call` followed by `ret`.

The syscall conflicts with the cached-top pattern: `rdi` cannot simultaneously hold the Forth top and the syscall's first argument. A boundary routine must arrange the data before assigning the Linux roles. Chapter 8 follows that arrangement and the handling of the result through the complete `emit`, `key`, `bye`, and `syscall6` chunks. Chapter 18 later gives those calls library wrappers.

## Try it: read the entry jump

Check the entry jump’s bytes in the built executable, then compare your hand-decoded destination with the disassembler’s result. This uses the host's `objdump` from GNU binutils; Chapter 5 uses its companion `readelf` to inspect ELF headers.

From the book checkout, build with `forth-bootstrap/seed/build.sh:12–29`, which selects the assembler and writes `seed-forth` in the source checkout:

```sh
cd forth-bootstrap && seed/build.sh
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

**Trace — easy.** Decode `48 8B 7D 00` at `forth-bootstrap/seed/000-seed.hex0:92` without looking at its assembly comment. Name the destination, effective address, and instruction length. Compare it with the store above. Why does changing the opcode reverse the direction while the ModRM byte stays the same?

For a second trace, recover the entry jump's destination from its bytes. What error results from adding the displacement at the instruction's start instead of its end?
