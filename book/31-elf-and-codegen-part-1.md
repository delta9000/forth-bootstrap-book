# Chapter 31 — ELF emission and instruction encoding

An executable that exits with status 42 needs only a header and a short instruction sequence. Emitter words turn operations into instructions in the output buffer. By the checkpoint, you can write and run that executable directly, including a patched jump that skips an unwanted assignment.

## One byte, three coordinates

Before writing bytes, choose what their addresses mean. The output buffer
is `cc-out-buf`; this ELF layout puts a 120-byte header before the code and
loads the image at `0x400000` (Chapter 5). The first instruction byte
therefore has three coordinates:

| Coordinate | Value for that byte | Who uses it? |
|---|---|---|
| Compiler memory address | `cc-out-buf + 120` | The running Forth compiler, to write or patch the byte |
| File offset | `120`, or `0x78` | The output cursor and saved patch positions |
| Program virtual address | `0x400000 + 0x78 = 0x400078` | The loader and the eventual machine code |

Writing the output copies the bytes into a file; it does not preserve
`cc-out-buf` as their runtime address. An absolute address in an instruction
must use the third row. A patch operation uses the second row to locate
bytes in the first. Relative branches can subtract two file offsets because
both receive the same load base when the program runs.

## `080-cc-elf.fth`: the ELF wrapper

The output side has this shape:

```text
cc-emit-elf-header → instruction emitters → cc-finalize-elf
       header          code bytes           size patches
                         cc-out-buf
```

The constants below encode that layout. `cc-here-vaddr` turns the output cursor into the next byte's execution address; the saved size-field offsets let finalization revisit the header (`forth-bootstrap/cc/080-cc-elf.fth:14`):

```forth file=cc/080-cc-elf.fth
\ 080-cc-elf.fth — ELF64 header + program header emission for our compiled output.
\
\ Layout: 64-byte ELF64_Ehdr + 56-byte Elf64_Phdr (one PT_LOAD) = 120 bytes.
\ Code begins at vaddr 0x400078, file offset 120.
\
\ Depends on 030-cc-io.fth (cc-emit-byte, cc-emit-4le, cc-emit-8le, cc-out-pos,
\ cc-out-patch-4le).

[lit] 4194304 constant cc-base-vaddr            \ 0x400000
[lit] 4194424 constant cc-entry-vaddr           \ 0x400078

\ cc-here-vaddr ( -- vaddr )  The address the next emitted byte will have
\ when the output runs: its file offset (cc-out-pos) plus the load address.
: cc-here-vaddr  cc-base-vaddr cc-out-pos @ + ;

\ p_filesz lives at file offset 96, 8 bytes LE.
\ p_memsz lives at file offset 104.
[lit] 96 constant cc-filesz-offset
[lit] 104 constant cc-memsz-offset

```

`cc-base-vaddr` is the base added to file offsets. `cc-entry-vaddr` points just beyond the header, so the first emitted instruction must be the program's entry code. `cc-here-vaddr` returns an address in that future executable, not an address in the running Forth process.

`cc-emit-elf-header` starts by identifying the output as an AMD64 executable (`forth-bootstrap/cc/080-cc-elf.fth:23`):

```forth file=cc/080-cc-elf.fth
\ cc-emit-elf-header ( -- )  Emit the 120-byte header at start of cc-out-buf.
\ p_filesz left at 0 (patched in cc-finalize-elf).
: cc-emit-elf-header
  \ e_ident: 7F 45 4C 46 (magic), class=2, data=1, version=1, osabi=0, pad=8
  [lit] 127 cc-emit-byte [lit]  69 cc-emit-byte
  [lit]  76 cc-emit-byte [lit]  70 cc-emit-byte
  [lit]   2 cc-emit-byte [lit]   1 cc-emit-byte [lit]   1 cc-emit-byte
  [lit]   0 cc-emit-byte
  [lit]   0 cc-emit-byte [lit]   0 cc-emit-byte [lit]   0 cc-emit-byte [lit]   0 cc-emit-byte
  [lit]   0 cc-emit-byte [lit]   0 cc-emit-byte [lit]   0 cc-emit-byte [lit]   0 cc-emit-byte
  \ e_type=2 (ET_EXEC), e_machine=0x3E (AMD64) — both 16-bit LE
  [lit] 2 cc-emit-byte [lit] 0 cc-emit-byte
  [lit] 62 cc-emit-byte [lit] 0 cc-emit-byte
  \ e_version (32-bit LE)
  [lit] 1 cc-emit-4le
```

The entry and table fields describe the layout already chosen; no section-header table is emitted (`forth-bootstrap/cc/080-cc-elf.fth:36`):

```forth file=cc/080-cc-elf.fth
  \ e_entry (64-bit LE) = 0x400078
  cc-entry-vaddr cc-emit-8le
  \ e_phoff = 64
  [lit] 64 cc-emit-8le
  \ e_shoff = 0
  [lit] 0 cc-emit-8le
  \ e_flags
  [lit] 0 cc-emit-4le
  \ e_ehsize=64, e_phentsize=56, e_phnum=1, then 6 bytes of zero
  [lit] 64 cc-emit-byte [lit] 0 cc-emit-byte
  [lit] 56 cc-emit-byte [lit] 0 cc-emit-byte
  [lit]  1 cc-emit-byte [lit] 0 cc-emit-byte
  [lit]  0 cc-emit-byte [lit] 0 cc-emit-byte
  [lit]  0 cc-emit-byte [lit] 0 cc-emit-byte
  [lit]  0 cc-emit-byte [lit] 0 cc-emit-byte
```

The program header leaves file size unresolved and starts memory size at a minimum of 81920 bytes (`forth-bootstrap/cc/080-cc-elf.fth:51`):

```forth file=cc/080-cc-elf.fth
  \ Program header (56 bytes, one PT_LOAD):
  [lit] 1 cc-emit-4le                            \ p_type = PT_LOAD
  [lit] 7 cc-emit-4le                            \ p_flags = R|W|X
  [lit] 0 cc-emit-8le                            \ p_offset = 0
  cc-base-vaddr cc-emit-8le                      \ p_vaddr = 0x400000
  cc-base-vaddr cc-emit-8le                      \ p_paddr = 0x400000
  [lit] 0 cc-emit-8le                            \ p_filesz (patched later)
  [lit] 81920 cc-emit-8le                        \ p_memsz = 0x14000
  [lit] 4096 cc-emit-8le ;                       \ p_align = 0x1000

```

Code and data share the writable, executable segment. Its memory size includes the file image; the minimum is not an extra allocation added to every output.

`cc-bss-size` records the zero-filled storage needed beyond that image. `cc-finalize-elf` patches `cc-filesz-offset` with the completed output size and enlarges `cc-memsz-offset` only when image plus BSS exceeds the minimum (`forth-bootstrap/cc/080-cc-elf.fth:73`):

```forth file=cc/080-cc-elf.fth
\ cc-bss-size ( -- a )  Bytes of zeroed memory the program needs after its
\ file image (its bss, 090-cc-emit.fth); cc-finalize-globals sets it.
variable cc-bss-size

\ cc-finalize-elf ( -- )  After codegen, patch p_filesz to current cc-out-pos.
\ We patch only the low 4 bytes — our outputs are well under 4 GiB and the
\ high 4 bytes were already emitted as zero.  p_memsz covers the file image
\ plus the bss; it keeps the 0x14000 it was emitted with unless that is
\ too small (otherwise large outputs like the M2-Planet monolith — well
\ past the 0x14000 default — would produce an invalid ELF that the kernel
\ won't load correctly).  Small outputs keep the 0x14000 minimum as
\ headroom past their file image.
: cc-finalize-elf
  cc-out-pos @ cc-filesz-offset cc-out-patch-4le
  cc-out-pos @ cc-bss-size @ +                   ( memsz )
  dup [lit] 81920 > if,
    cc-memsz-offset cc-out-patch-4le
  else,
    drop
  then, ;
```

Only the low part of each size field is patched. This relies on the output and requested memory fitting the field width used by `cc-out-patch-4le`. Chapter 37 supplies the global placement that sets `cc-bss-size`; the checkpoint sets it to zero explicitly.

## `090-cc-emit.fth`: register convention

The instruction helpers assign fixed roles to registers so their callers can combine operations without a register allocator (`forth-bootstrap/cc/090-cc-emit.fth:1`):

```forth file=cc/090-cc-emit.fth
\ 090-cc-emit.fth — code-emission helpers for the C-subset compiler.
\ Builds tiny instruction-encoders on top of cc-emit-byte / cc-emit-4le from
\ 030-cc-io.fth.  All output goes to cc-out-buf; nothing here touches the seed's
\ HERE pointer.
\
\ Register convention for the compiled code:
\   rdi  — scratch / current expression result
\   rcx  — temp for binary-op right operand
\   rax  — used by idiv (low quotient/remainder); also by SYS-V return
\   rbp  — frame base; locals at [rbp - 8*(slot+1)]
\
\ Depends on 020-cc-arena.fth (cc-die, cc-check-cap, cc-alloc) and
\ 030-cc-io.fth (cc-emit-byte, cc-emit-4le, cell[]).  cc-decode-escape comes
\ from 050-cc-lex.fth.

```

`rdi` is the accumulator for the current C expression. `rcx` holds a binary operation's right operand, `rax` bridges division and function results, and `rbp` anchors local storage. These roles describe the emitted program. Calling an emitter in Forth appends bytes; it does not perform the named C operation immediately.

The System V AMD64 calling convention provides the function boundary: integer and pointer arguments start in `rdi`, `rsi`, `rdx`, `rcx`, `r8`, and `r9`, and an integer or pointer result returns in `rax`. The expression accumulator therefore needs explicit transfers at calls and returns. The spill and move helpers below provide those transfers. Chapter 41 handles the complete separate-compilation boundary, including stack arguments, alignment, and preservation obligations.

## Stack ops and immediate loads

An immediate expression needs a value in `rdi`. The encoding vocabulary is unchanged (Chapter 4); this helper fixes the register and accepts only the immediate (`forth-bootstrap/cc/090-cc-emit.fth:16`):

```forth file=cc/090-cc-emit.fth
\ ===========================================================================
\ Immediate-load instructions (REX.W + C7 /0 + imm32)
\ ===========================================================================

\ cc-emit-mov-rdi-imm32 ( v -- )   48 C7 C7 <imm32>
: cc-emit-mov-rdi-imm32
  [lit]  72 cc-emit-byte
  [lit] 199 cc-emit-byte
  [lit] 199 cc-emit-byte
  cc-emit-4le ;

```

`cc-emit-mov-rdi-imm32` emits a sign-extended immediate. Its caller must choose a value that fits; the helper does not check. Chapter 32 supplies the wider immediate loader.

Stack operations can report their effect while the compiler emits them. `cc-emit-track-push-fwd` and `cc-emit-track-pop-fwd` initially run `cc-emit-track-noop`, which emits nothing (`forth-bootstrap/cc/090-cc-emit.fth:32`):

```forth file=cc/090-cc-emit.fth
\ ===========================================================================
\ Stack ops
\ ===========================================================================

\ Optional compile-time accounting; native defaults emit no extra bytes.
: cc-emit-track-noop ;
defer cc-emit-track-push-fwd
defer cc-emit-track-pop-fwd
' cc-emit-track-noop is cc-emit-track-push-fwd
' cc-emit-track-noop is cc-emit-track-pop-fwd

```

The following family saves an accumulator or recovers a saved value into the register that needs it:

| Helper | Input → result in the emitted program |
|---|---|
| `cc-emit-push-rdi` | `rdi` → machine stack |
| `cc-emit-pop-rdi` | stack top → accumulator |
| `cc-emit-pop-rsi`, `cc-emit-pop-rdx` | stack top → argument register |
| `cc-emit-pop-rcx` | stack top → right operand or argument |
| `cc-emit-pop-r8`, `cc-emit-pop-r9` | stack top → extended argument register |
| `cc-emit-push-rbx`, `cc-emit-pop-rbx` | saved selection value → stack → restored value |

Accumulator saves and the first argument-register pops invoke the tracking hooks before appending their instruction (`forth-bootstrap/cc/090-cc-emit.fth:38`):

```forth file=cc/090-cc-emit.fth
\ push rdi: 0x57
: cc-emit-push-rdi  cc-emit-track-push-fwd [lit]  87 cc-emit-byte ;

\ pop rdi:  0x5F
: cc-emit-pop-rdi   cc-emit-track-pop-fwd [lit]  95 cc-emit-byte ;

\ pop rsi:  0x5E
: cc-emit-pop-rsi   cc-emit-track-pop-fwd [lit]  94 cc-emit-byte ;

\ pop rdx:  0x5A
: cc-emit-pop-rdx   cc-emit-track-pop-fwd [lit]  90 cc-emit-byte ;

```

The extended-register pops follow the same tracking policy; the `rbx` pair emits its instructions directly (`forth-bootstrap/cc/090-cc-emit.fth:50`):

```forth file=cc/090-cc-emit.fth
\ pop rcx:  0x59
: cc-emit-pop-rcx   cc-emit-track-pop-fwd [lit]  89 cc-emit-byte ;

\ pop r8:   0x41 0x58  (REX.B + pop)
: cc-emit-pop-r8    cc-emit-track-pop-fwd [lit]  65 cc-emit-byte [lit]  88 cc-emit-byte ;

\ pop r9:   0x41 0x59
: cc-emit-pop-r9    cc-emit-track-pop-fwd [lit]  65 cc-emit-byte [lit]  89 cc-emit-byte ;

\ push rbx (0x53) / pop rbx (0x5B).  Used by switch to preserve the outer
\ value of rbx across the switch (which uses rbx to hold the scrutinee).
: cc-emit-push-rbx  [lit]  83 cc-emit-byte ;
: cc-emit-pop-rbx   [lit]  91 cc-emit-byte ;

```

<details>
<summary>Operand access: local slots, pointers, and argument registers</summary>

The checkpoint needs immediate loads and a jump. These helpers extend
the same emitter vocabulary to values stored in memory and passed to
functions. The declaration parser will choose a slot; these words only
encode access to it. Keep that division in mind when returning here from
Chapters 34–37.

## Local-variable addressing

A local's slot number selects storage below the frame pointer: `[rbp - 8*(slot+1)]`. Slot zero is nearest `rbp`. `cc-disp8-from-slot` computes the low byte of that displacement; it does not decide whether the displacement fits (`forth-bootstrap/cc/090-cc-emit.fth:78`):

```forth file=cc/090-cc-emit.fth
\ ===========================================================================
\ Local-variable access
\ ===========================================================================
\ Locals live at [rbp - 8*(slot+1)].  Slots 0..15 have displacements
\ -8..-128, which fit a signed disp8 (ModR/M mod=01); deeper slots need the
\ disp32 form (mod=10).  cc-emit-local-ea picks the right one per slot.
\ Note: the frame itself is fixed at 256 bytes = 32 slots (cc-frame-slots in
\ 110-cc-decl.fth, which dies rather than hand out a 33rd) — the encoding
\ handles any slot; the frame does not.
\
\ cc-disp8-from-slot ( slot -- byte )
\   = (256 - 8*(slot+1)) AND 255 = the unsigned-byte representation of the
\   signed displacement -8*(slot+1).  Only valid for slots 0..15.

: cc-disp8-from-slot
  1+ [lit] 8 *                                   \ 8 * (slot+1)
  [lit] 0 swap -                                  \ negate
  [lit] 255 and ;                                 \ low byte

```

The shared **local-address tail**, `cc-emit-local-ea`, makes that decision for every local access. Its caller supplies the slot and the short-form ModRM byte (`forth-bootstrap/cc/090-cc-emit.fth:88`):

```forth file=cc/090-cc-emit.fth
\ cc-emit-local-ea ( slot modrm8 -- )
\   Emit the ModR/M byte + displacement for [rbp + disp] access to a local
\   slot.  modrm8 is the mod=01 (disp8) form of the ModR/M byte.  Slots
\   0..15 emit it unchanged plus a disp8; deeper slots switch to mod=10
\   (modrm8 + 0x40) plus the 32-bit two's-complement displacement.
: cc-emit-local-ea
  over [lit] 16 < >r over [lit] 0 [lit] 16 - >= r> and if,
    cc-emit-byte
    cc-disp8-from-slot cc-emit-byte
  else,
    [lit] 64 + cc-emit-byte                       \ mod=01 -> mod=10
    1+ [lit] 8 *                                  \ 8 * (slot+1)
    [lit] 0 swap - cc-emit-4le                    \ negate; low 4 bytes = disp32
  then, ;

```

The code accepts slots from -16 through 15 in the short form. Ordinary nonnegative locals use zero through 15; slot 16 needs the long displacement. Negative slots can describe addresses above the frame pointer. The comments describe ordinary locals, while the predicate also permits those positive displacements.

A larger displacement changes the encoding, not the amount of stack storage reserved. Chapter 35 explains slot allocation; the prologue below accepts the frame size separately.

Loads and stores share the local-address tail, so the boundary cannot drift between readers and writers (`forth-bootstrap/cc/090-cc-emit.fth:98`):

```forth file=cc/090-cc-emit.fth
\ mov rdi, [rbp + disp]:  48 8B 7D <disp8>  (or 48 8B BD <disp32>)
: cc-emit-load-local                              ( slot -- )
  [lit]  72 cc-emit-byte
  [lit] 139 cc-emit-byte
  [lit] 125 cc-emit-local-ea ;

\ mov [rbp + disp], rdi:  48 89 7D <disp8>  (or 48 89 BD <disp32>)
: cc-emit-store-local                             ( slot -- )
  [lit]  72 cc-emit-byte
  [lit] 137 cc-emit-byte
  [lit] 125 cc-emit-local-ea ;

```

`cc-emit-load-local` replaces `rdi` with the slot's contents. `cc-emit-store-local` copies `rdi` into the slot without changing the accumulator.

### Addresses and dereferences

Address-of must retain the location rather than fetch its contents; `cc-emit-lea-rdi-local` uses the same local-address tail for that purpose (`forth-bootstrap/cc/090-cc-emit.fth:113`):

```forth file=cc/090-cc-emit.fth
\ lea rdi, [rbp + disp]:  48 8D 7D <disp8>  (or 48 8D BD <disp32>)
\ ModR/M(mod=01, reg=rdi=7, rm=rbp=5) = 0x7D.  Loads the *address* of the local
\ slot into rdi (used to implement `&local`).
: cc-emit-lea-rdi-local                           ( slot -- )
  [lit]  72 cc-emit-byte
  [lit] 141 cc-emit-byte
  [lit] 125 cc-emit-local-ea ;

```

Once an address is in `rdi`, dereference no longer needs a slot number. These loaders distinguish a full-width value from a zero-extended byte (`forth-bootstrap/cc/090-cc-emit.fth:118`):

```forth file=cc/090-cc-emit.fth
\ mov rdi, [rdi]:  48 8B 3F
\ ModR/M(mod=00, reg=rdi=7, rm=rdi=7) = 0x3F.  Loads the qword at the address
\ currently in rdi into rdi (dereference).
: cc-emit-load-via-rdi
  [lit]  72 cc-emit-byte
  [lit] 139 cc-emit-byte
  [lit]  63 cc-emit-byte ;

\ movzx rdi, BYTE PTR [rdi]:  48 0F B6 3F
\ Zero-extends a single byte from [rdi] into rdi.  Used by `s[i]` rvalue use
\ where s is `char*` (or any other byte-element access path).
: cc-emit-load-byte-via-rdi
  [lit]  72 cc-emit-byte
  [lit]  15 cc-emit-byte
  [lit] 182 cc-emit-byte
  [lit]  63 cc-emit-byte ;
```

`cc-emit-zx-byte-rdi` handles a value already in a register: it retains the low byte and clears the rest without reading memory (`forth-bootstrap/cc/090-cc-emit.fth:138`):

```forth file=cc/090-cc-emit.fth

\ movzx edi, dil:  40 0F B6 FF
\ Keeps only rdi's low byte (writing edi clears the upper half of rdi).
\ REX=0x40 selects dil rather than bh.  Used by a (char) cast.
: cc-emit-zx-byte-rdi
  [lit]  64 cc-emit-byte
  [lit]  15 cc-emit-byte
  [lit] 182 cc-emit-byte
  [lit] 255 cc-emit-byte ;
```

Stores keep the destination address in `rcx` while `rdi` supplies the value. The byte variant writes only its low byte (`forth-bootstrap/cc/090-cc-emit.fth:143`):

```forth file=cc/090-cc-emit.fth

\ mov [rcx], rdi:  48 89 39
\ ModR/M(mod=00, reg=rdi=7, rm=rcx=1) = 0x39.  Stores rdi to the qword address
\ in rcx (assignment via dereference).
: cc-emit-store-via-rcx
  [lit]  72 cc-emit-byte
  [lit] 137 cc-emit-byte
  [lit]  57 cc-emit-byte ;

\ mov BYTE PTR [rcx], dil:  40 88 39
\ Stores the low byte of rdi to [rcx].  REX=0x40 is needed to select dil
\ instead of bh.  Used by `s[i] = c;` where s is char*.
: cc-emit-store-byte-via-rcx
  [lit]  64 cc-emit-byte
  [lit] 136 cc-emit-byte
  [lit]  57 cc-emit-byte ;
```

### Pointer offsets

An index must become a byte offset before it can be added to an address. `cc-emit-shl-rdi-imm8` supplies a constant shift, and `cc-emit-shl-rdi-3` specializes it for the cell-sized elements of the core storage model (`forth-bootstrap/cc/090-cc-emit.fth:159`):

```forth file=cc/090-cc-emit.fth

\ shl rdi, imm8:  48 C1 E7 <imm8>
\ ModR/M(mod=11, reg=/4 = SHL, rm=rdi=7) = 11_100_111 = 0xE7.  Multiplies rdi
\ by 2^imm8 (used to scale array index by sizeof(T) when T is 8 bytes).
: cc-emit-shl-rdi-imm8                            ( imm8 -- )
  [lit]  72 cc-emit-byte
  [lit] 193 cc-emit-byte
  [lit] 231 cc-emit-byte
  cc-emit-byte ;

\ Convenience: rdi <<= 3 (multiply by 8 = sizeof(int)/sizeof(ptr)).
: cc-emit-shl-rdi-3   [lit] 3 cc-emit-shl-rdi-imm8 ;

```

A known field offset instead needs an immediate addition to the base address (`forth-bootstrap/cc/090-cc-emit.fth:172`):

```forth file=cc/090-cc-emit.fth
\ add rdi, imm32:  48 81 C7 <imm32>
\ ModR/M(mod=11, reg=/0 = ADD, rm=rdi=7) = 11_000_111 = 0xC7.  Used to bias
\ a struct base/pointer in rdi by a field offset.  imm32 is sign-extended.
: cc-emit-add-rdi-imm32                           ( imm32 -- )
  [lit]  72 cc-emit-byte
  [lit] 129 cc-emit-byte
  [lit] 199 cc-emit-byte
  cc-emit-4le ;

```

`cc-emit-add-rdi-imm32` sign-extends its immediate, just like the immediate loader. These helpers know neither the pointed-to type nor the field name; the expression code in Chapter 34 chooses the offset and operation.

### Argument spills and indirect calls

An incoming argument needs a stable home if later expression evaluation will overwrite its register. The spill family uses the local-address tail with a different source register:

| Helper | Register input → local-slot result |
|---|---|
| `cc-emit-store-local` | `rdi` → selected slot |
| `cc-emit-store-local-from-rsi` | `rsi` → selected slot |
| `cc-emit-store-local-from-rdx` | `rdx` → selected slot |
| `cc-emit-store-local-from-rcx` | `rcx` → selected slot |
| `cc-emit-store-local-from-r8` | `r8` → selected slot |
| `cc-emit-store-local-from-r9` | `r9` → selected slot |

The first variants establish the parameter-spill pattern (`forth-bootstrap/cc/090-cc-emit.fth:181`):

```forth file=cc/090-cc-emit.fth
\ Param-spill helpers: store the SYS-V argument register holding the i'th
\ argument into local slot i.  Each one is `mov [rbp + disp8], <reg>`.
\ ModR/M byte: mod=01 (disp8), rm=rbp(=5).  reg field varies per source reg.
\ REX byte is 48 (W only) for rsi/rdx/rcx, 4C (W+R) for r8/r9.
\
\   reg=rsi(6): 01_110_101 = 0x75
\   reg=rdx(2): 01_010_101 = 0x55
\   reg=rcx(1): 01_001_101 = 0x4D
\   reg=r8 (0 with R bit): 01_000_101 = 0x45
\   reg=r9 (1 with R bit): 01_001_101 = 0x4D

: cc-emit-store-local-from-rsi                    ( slot -- )
  [lit]  72 cc-emit-byte
  [lit] 137 cc-emit-byte
  [lit] 117 cc-emit-local-ea ;                    \ 0x75

: cc-emit-store-local-from-rdx                    ( slot -- )
  [lit]  72 cc-emit-byte
  [lit] 137 cc-emit-byte
  [lit]  85 cc-emit-local-ea ;                    \ 0x55

```

The remaining variants change register selection while retaining the same slot handling (`forth-bootstrap/cc/090-cc-emit.fth:202`):

```forth file=cc/090-cc-emit.fth
: cc-emit-store-local-from-rcx                    ( slot -- )
  [lit]  72 cc-emit-byte
  [lit] 137 cc-emit-byte
  [lit]  77 cc-emit-local-ea ;                    \ 0x4D

: cc-emit-store-local-from-r8                     ( slot -- )
  [lit]  76 cc-emit-byte                          \ REX.W+R = 0x4C
  [lit] 137 cc-emit-byte
  [lit]  69 cc-emit-local-ea ;                    \ 0x45

: cc-emit-store-local-from-r9                     ( slot -- )
  [lit]  76 cc-emit-byte
  [lit] 137 cc-emit-byte
  [lit]  77 cc-emit-local-ea ;                    \ 0x4D

```

An indirect call needs its target without disturbing argument registers. `cc-emit-load-local-into-rax` fetches a saved function pointer, and `cc-emit-call-rax` calls it (`forth-bootstrap/cc/090-cc-emit.fth:217`):

```forth file=cc/090-cc-emit.fth
\ mov rax, [rbp + disp]:  48 8B 45 <disp8>  (or 48 8B 85 <disp32>)
\ ModR/M(mod=01, reg=rax=0, rm=rbp=5) = 01_000_101 = 0x45.  Used to load a
\ function-pointer local into rax just before an indirect `call rax` — keeps
\ rdi/rsi/etc. (already loaded with SYS-V args) untouched.
: cc-emit-load-local-into-rax                     ( slot -- )
  [lit]  72 cc-emit-byte
  [lit] 139 cc-emit-byte
  [lit]  69 cc-emit-local-ea ;                    \ 0x45

\ call rax:  FF D0   (no REX needed; rax = reg 0).
\ ModR/M(mod=11, reg=/2 = CALL r/m64, rm=rax=0) = 11_010_000 = 0xD0.
: cc-emit-call-rax
  [lit] 255 cc-emit-byte
  [lit] 208 cc-emit-byte ;

```

Chapter 37 connects these primitives to function parameters and call expressions.

</details>

## Register-to-register moves, ALU, and prologue/epilogue

Register moves connect the accumulator to the roles around it:

| Helper | Input → result |
|---|---|
| `cc-emit-mov-rcx-rdi` | accumulator → right-operand temporary |
| `cc-emit-mov-rax-rdi` | accumulator → return/division register |
| `cc-emit-mov-rdi-rax` | function result → accumulator |
| `cc-emit-mov-rbx-rdi` | accumulator → saved selection value |

The first transfers either save a right operand or place a result in the return register. The historical comment groups IMUL with ADD/SUB too broadly: the ADD/SUB forms here use ModR/M `reg=source, r/m=destination`, but two-operand `0F AF` IMUL uses `reg=destination, r/m=source`. The later IMUL encoder uses that latter direction (`forth-bootstrap/cc/090-cc-emit.fth:232`):

```forth file=cc/090-cc-emit.fth
\ ===========================================================================
\ Register-to-register moves
\ ===========================================================================
\ ADD/SUB/IMUL r/m64, r64 has reg-field=src, rm-field=dst.  We use rdi as the
\ destination accumulator and rcx for the right-operand temp.

\ mov rcx, rdi:  48 89 F9     (89 /r, mod=11 reg=rdi=7 rm=rcx=1 -> 11_111_001 = F9)
: cc-emit-mov-rcx-rdi
  [lit]  72 cc-emit-byte
  [lit] 137 cc-emit-byte
  [lit] 249 cc-emit-byte ;

\ mov rax, rdi:  48 89 F8     (mod=11 reg=rdi=7 rm=rax=0 -> 11_111_000 = F8)
: cc-emit-mov-rax-rdi
  [lit]  72 cc-emit-byte
  [lit] 137 cc-emit-byte
  [lit] 248 cc-emit-byte ;

```

The reverse transfer brings a returned value back into expression evaluation (`forth-bootstrap/cc/090-cc-emit.fth:250`):

```forth file=cc/090-cc-emit.fth
\ mov rdi, rax:  48 89 C7     (mod=11 reg=rax=0 rm=rdi=7 -> 11_000_111 = C7)
\ Used after a function call to transfer the SYS-V return value into our
\ scratch rdi so the rest of the expression machinery sees it.
: cc-emit-mov-rdi-rax
  [lit]  72 cc-emit-byte
  [lit] 137 cc-emit-byte
  [lit] 199 cc-emit-byte ;

```

A saved selection value can be compared repeatedly without replacing it. `cc-emit-cmp-rbx-imm32` updates flags using a sign-extended constant; Chapter 36 uses this pair for switch dispatch (`forth-bootstrap/cc/090-cc-emit.fth:269`):

```forth file=cc/090-cc-emit.fth
\ mov rbx, rdi:  48 89 FB   (89 /r, mod=11 reg=rdi=7 rm=rbx=3 -> 11_111_011 = FB)
\ Used at switch entry to stash the scrutinee in a callee-saved register so
\ it survives across case-body codegen (including any function calls).
: cc-emit-mov-rbx-rdi
  [lit]  72 cc-emit-byte
  [lit] 137 cc-emit-byte
  [lit] 251 cc-emit-byte ;

\ cmp rbx, imm32:  48 81 FB <imm32>   (81 /7, mod=11 /7=111 rm=rbx=3 -> FB)
\ Used by switch dispatch to compare the saved scrutinee against each case
\ constant.  Sets ZF iff rbx == imm32.  imm32 is sign-extended to 64 bits.
: cc-emit-cmp-rbx-imm32                           ( v -- )
  [lit]  72 cc-emit-byte
  [lit] 129 cc-emit-byte
  [lit] 251 cc-emit-byte
  cc-emit-4le ;

```

An implicit zero result needs no immediate operand (`forth-bootstrap/cc/090-cc-emit.fth:275`):

```forth file=cc/090-cc-emit.fth
\ xor rax, rax:  48 31 C0     (zero rax in 3 bytes; for implicit return).
: cc-emit-xor-rax-rax
  [lit]  72 cc-emit-byte
  [lit]  49 cc-emit-byte
  [lit] 192 cc-emit-byte ;

```

### Binary arithmetic

The **binary-operation setup** leaves the left operand in `rdi` and the right in `rcx`. Saving the left on the machine stack lets evaluation of the right reuse the accumulator. Addition consumes that arrangement directly (`forth-bootstrap/cc/090-cc-emit.fth:281`):

```forth file=cc/090-cc-emit.fth
\ ===========================================================================
\ ALU on rdi using rcx as the right operand
\ ===========================================================================
\ The binary-op pattern emitted by the parser is:
\     <eval left>          ; rdi = left
\     push rdi
\     <eval right>         ; rdi = right
\     mov rcx, rdi         ; rcx = right
\     pop rdi              ; rdi = left
\     <op> rdi, rcx        ; rdi = left <op> right
\
\ ADD r/m64, r64 (0x01 /r): rm=dst, reg=src.
\   add rdi, rcx -> mod=11 reg=rcx=1 rm=rdi=7 -> 11_001_111 = 0xCF
: cc-emit-add-rdi-rcx
  [lit]  72 cc-emit-byte
  [lit]   1 cc-emit-byte
  [lit] 207 cc-emit-byte ;

```

Apply that setup by hand to `((4) * (4))`, the text left by our macro
example. Emit a load of 4 and a push, then a second load of 4. Move the
right value to `rcx`, pop the left back into `rdi`, and emit multiplication.
When those instructions run, `rdi` will hold 16. We are choosing emitter
calls ourselves here; these words do not read the parentheses or `*`.
Chapter 33 makes the parser choose this sequence from tokens.

Subtraction keeps the same left/right order. Multiplication has the same register-level contract even though its instruction encoding selects operands differently (`forth-bootstrap/cc/090-cc-emit.fth:299`):

```forth file=cc/090-cc-emit.fth
\ SUB r/m64, r64 (0x29 /r): same encoding shape.
\   sub rdi, rcx -> 0xCF
: cc-emit-sub-rdi-rcx
  [lit]  72 cc-emit-byte
  [lit]  41 cc-emit-byte
  [lit] 207 cc-emit-byte ;

\ IMUL r64, r/m64 (0x0F AF /r): reg=dst, rm=src (NOTE the operand order is
\ flipped from add/sub).
\   imul rdi, rcx -> mod=11 reg=rdi=7 rm=rcx=1 -> 11_111_001 = 0xF9
: cc-emit-imul-rdi-rcx
  [lit]  72 cc-emit-byte
  [lit]  15 cc-emit-byte
  [lit] 175 cc-emit-byte
  [lit] 249 cc-emit-byte ;

```

Division needs a temporary departure from the accumulator convention: both helpers move the dividend into `rax`, prepare `rdx`, divide by `rcx`, then move the requested result back (`forth-bootstrap/cc/090-cc-emit.fth:315`):

```forth file=cc/090-cc-emit.fth
\ Signed division: idiv divides rdx:rax by r/m64, leaving quotient in rax,
\ remainder in rdx.  We want rdi := rdi / rcx (or rdi % rcx).  Sequence:
\     mov rax, rdi      ; 48 89 F8
\     cqo               ; 48 99            (sign-extend rax into rdx)
\     idiv rcx          ; 48 F7 F9         (F7 /7, mod=11 rm=rcx=1 -> 11_111_001=0xF9)
\     mov rdi, rax|rdx  ; 48 89 C7 (rax) or 48 89 D7 (rdx)
: cc-emit-idiv-quotient
  [lit]  72 cc-emit-byte [lit] 137 cc-emit-byte [lit] 248 cc-emit-byte
  [lit]  72 cc-emit-byte [lit] 153 cc-emit-byte
  [lit]  72 cc-emit-byte [lit] 247 cc-emit-byte [lit] 249 cc-emit-byte
  [lit]  72 cc-emit-byte [lit] 137 cc-emit-byte [lit] 199 cc-emit-byte ;

: cc-emit-idiv-remainder
  [lit]  72 cc-emit-byte [lit] 137 cc-emit-byte [lit] 248 cc-emit-byte
  [lit]  72 cc-emit-byte [lit] 153 cc-emit-byte
  [lit]  72 cc-emit-byte [lit] 247 cc-emit-byte [lit] 249 cc-emit-byte
  [lit]  72 cc-emit-byte [lit] 137 cc-emit-byte [lit] 215 cc-emit-byte ;

```

`cc-emit-idiv-quotient` selects `rax`; `cc-emit-idiv-remainder` selects `rdx`. Both overwrite those scratch registers. Chapter 33 connects the binary-operation setup to parsed expressions.

### Frame entry and return

A stable `rbp` lets pushes and pops change `rsp` without moving local addresses. `cc-emit-prologue` saves the caller's frame pointer, establishes the new one, and reserves the requested frame size (`forth-bootstrap/cc/090-cc-emit.fth:339`):

```forth file=cc/090-cc-emit.fth
\ ===========================================================================
\ Function prologue / epilogue
\ ===========================================================================
\ Prologue:  push rbp ; mov rbp, rsp ; sub rsp, imm32
\ Epilogue:  mov rsp, rbp ; pop rbp ; ret

: cc-emit-prologue                                ( frame-bytes -- )
  [lit]  85 cc-emit-byte                          \ push rbp
  [lit]  72 cc-emit-byte
  [lit] 137 cc-emit-byte
  [lit] 229 cc-emit-byte                          \ mov rbp, rsp
  [lit]  72 cc-emit-byte
  [lit] 129 cc-emit-byte
  [lit] 236 cc-emit-byte                          \ sub rsp, imm32 prefix
  cc-emit-4le ;

```

Returning discards that reservation by restoring `rsp` from `rbp`. Before doing so, `cc-emit-epilogue` invokes a restoration hook; its initial target, `cc-emit-restore-noop`, emits nothing (`forth-bootstrap/cc/090-cc-emit.fth:349`):

```forth file=cc/090-cc-emit.fth
: cc-emit-restore-noop ;
defer cc-emit-restore-callee-fwd
' cc-emit-restore-noop is cc-emit-restore-callee-fwd

: cc-emit-epilogue
  cc-emit-restore-callee-fwd
  [lit]  72 cc-emit-byte
  [lit] 137 cc-emit-byte
  [lit] 236 cc-emit-byte                          \ mov rsp, rbp
  [lit]  93 cc-emit-byte                          \ pop rbp
  [lit] 195 cc-emit-byte ;                        \ ret

```

The epilogue does not move the expression accumulator into `rax`. The caller of these emitters must arrange the return value separately. Nor does the prologue by itself satisfy every calling-convention obligation; these words provide the frame mechanics.

## Comparisons and conditional set

Comparisons use the binary-operation setup but replace the accumulator with a C truth value. `cc-emit-cmp-set` clears `rax` before comparing, because `setcc` writes only `al`; clearing afterward would destroy the flags being tested (`forth-bootstrap/cc/090-cc-emit.fth:373`):

```forth file=cc/090-cc-emit.fth
\ ===========================================================================
\ Comparisons: set rdi to 0 or 1 based on signed comparison of left/right.
\ ===========================================================================
\ The binary-op pattern (same as ALU) leaves rdi=left, rcx=right.  Each helper
\ emits 12 bytes:
\     xor rax, rax     48 31 C0
\     cmp rdi, rcx     48 39 CF      (sets flags from rdi - rcx = left - right)
\     setX al          0F 9X C0      (X = 4=E, 5=NE, C=L, D=GE, E=LE, F=G)
\     mov rdi, rax     48 89 C7
\
\ cc-emit-cmp-set ( setX-opcode -- )  Common tail; caller passes the second
\ byte of the setcc opcode (0x94, 0x95, 0x9C, 0x9D, 0x9E, 0x9F).
: cc-emit-cmp-set
  [lit]  72 cc-emit-byte [lit]  49 cc-emit-byte [lit] 192 cc-emit-byte   \ xor rax,rax
  [lit]  72 cc-emit-byte [lit]  57 cc-emit-byte [lit] 207 cc-emit-byte   \ cmp rdi,rcx
  [lit]  15 cc-emit-byte                                                  \ 0F prefix
  cc-emit-byte                                                            \ setX opcode
  [lit] 192 cc-emit-byte                                                  \ ModR/M for AL
  [lit]  72 cc-emit-byte [lit] 137 cc-emit-byte [lit] 199 cc-emit-byte ; \ mov rdi,rax

```

Each wrapper supplies the condition opcode to that common sequence:

| Helper | Inputs `left`, `right` → true condition |
|---|---|
| `cc-emit-cmp-eq` | `left == right` |
| `cc-emit-cmp-ne` | `left != right` |
| `cc-emit-cmp-lt` | `left < right`, signed |
| `cc-emit-cmp-ge` | `left >= right`, signed |
| `cc-emit-cmp-le` | `left <= right`, signed |
| `cc-emit-cmp-gt` | `left > right`, signed |

Selecting the opcode is all the wrappers need to do (`forth-bootstrap/cc/090-cc-emit.fth:381`):

```forth file=cc/090-cc-emit.fth
: cc-emit-cmp-eq  [lit] 148 cc-emit-cmp-set ;     \ 0x94 setE
: cc-emit-cmp-ne  [lit] 149 cc-emit-cmp-set ;     \ 0x95 setNE
: cc-emit-cmp-lt  [lit] 156 cc-emit-cmp-set ;     \ 0x9C setL
: cc-emit-cmp-ge  [lit] 157 cc-emit-cmp-set ;     \ 0x9D setGE
: cc-emit-cmp-le  [lit] 158 cc-emit-cmp-set ;     \ 0x9E setLE
: cc-emit-cmp-gt  [lit] 159 cc-emit-cmp-set ;     \ 0x9F setG

```

The final move delivers zero or one in `rdi`, suitable as a C expression value. The ordered comparisons here are signed; their names do not imply unsigned support.

## Branches and `rel32` placeholders

Recall `if,` and `then,` from Chapter 24: reserve an unfinished field,
remember where it is, and fill it when the destination is known. Here the
field belongs to the output buffer and holds a relative displacement;
the original library words kept an absolute destination in an inline cell.

A conditional jump reads processor flags, so it needs a test of the expression value. `cc-emit-test-rdi` tests the accumulator without changing it (`forth-bootstrap/cc/090-cc-emit.fth:393`):

```forth file=cc/090-cc-emit.fth
\ ===========================================================================
\ Conditional / unconditional branches with rel32 fixups.
\ ===========================================================================

\ test rdi, rdi  -> 48 85 FF  (sets ZF=1 iff rdi == 0).
: cc-emit-test-rdi
  [lit]  72 cc-emit-byte
  [lit] 133 cc-emit-byte
  [lit] 255 cc-emit-byte ;

```

The branch family returns an output-buffer offset identifying the displacement to patch:

| Helper | Emitted transfer → condition |
|---|---|
| `cc-emit-jz-rel32-placeholder` | jump → zero flag set |
| `cc-emit-jmp-rel32-placeholder` | jump → unconditional |
| `cc-emit-call-rel32-placeholder` | call → unconditional, with return address |
| `cc-emit-jnz-rel32-placeholder` | jump → zero flag clear |

Saving `cc-out-pos` after the opcode makes the returned offset point at the displacement field, not the instruction start (`forth-bootstrap/cc/090-cc-emit.fth:398`):

```forth file=cc/090-cc-emit.fth
\ cc-emit-jz-rel32-placeholder ( -- patch-offset )
\ Emits `0F 84 00 00 00 00`; returns the file-offset of the rel32 cell
\ so the caller can later patch it with cc-patch-rel32-to-here.
: cc-emit-jz-rel32-placeholder
  [lit]  15 cc-emit-byte
  [lit] 132 cc-emit-byte
  cc-out-pos @
  [lit] 0 cc-emit-4le ;

\ cc-emit-jmp-rel32-placeholder ( -- patch-offset )
\ Emits `E9 00 00 00 00`; returns the rel32 file-offset.
: cc-emit-jmp-rel32-placeholder
  [lit] 233 cc-emit-byte
  cc-out-pos @
  [lit] 0 cc-emit-4le ;

```

Calls and nonzero branches expose the same patch-offset interface (`forth-bootstrap/cc/090-cc-emit.fth:414`):

```forth file=cc/090-cc-emit.fth
\ cc-emit-call-rel32-placeholder ( -- patch-offset )
\ Emits `E8 00 00 00 00`; returns the rel32 file-offset.  Used for forward
\ function calls whose target vaddr is not yet known.  The caller threads the
\ patch offset onto a fixup list attached to the callee's prototype symbol;
\ the list is walked and patched when the function is later defined.
: cc-emit-call-rel32-placeholder
  [lit] 232 cc-emit-byte
  cc-out-pos @
  [lit] 0 cc-emit-4le ;

\ cc-emit-jnz-rel32-placeholder ( -- patch-offset )
\ Emits `0F 85 00 00 00 00`; returns the rel32 file-offset.  Used by `||`'s
\ short-circuit fast-path: if LHS is non-zero, skip RHS and produce 1.
: cc-emit-jnz-rel32-placeholder
  [lit]  15 cc-emit-byte
  [lit] 133 cc-emit-byte
  cc-out-pos @
  [lit] 0 cc-emit-4le ;

```

`cc-patch-rel32-to-here` targets the next byte to be emitted. It subtracts the end of the displacement field from the current output position; the shared load base cancels from that difference (`forth-bootstrap/cc/090-cc-emit.fth:435`):

```forth file=cc/090-cc-emit.fth
\ cc-patch-rel32-to-here ( patch-offset -- )
\ rel32 = current cc-out-pos - (patch-offset + 4).
: cc-patch-rel32-to-here
  cc-out-pos @                                    ( patch-off target-off )
  over [lit] 4 + -                                ( patch-off rel32 )
  swap cc-out-patch-4le ;

\ NOTE: cc-emit-jmp-vaddr (which emits a backward unconditional jump to an
\ absolute vaddr — needed for `while`/`for` loops) lives in 112-cc-stmt.fth
\ alongside the loop constructs that use it, not here with the primitive
\ encoders.  Both cc-base-vaddr and cc-out-pos are already available when this
\ file loads, so the split is organizational, not a load-order dependency.

```

The checkpoint puts a jump before an unwanted assignment, emits that assignment, then patches the jump to the following instruction. Chapter 32 keeps multiple unresolved call sites in fixup lists; Chapter 36 builds statement-level control flow and backward jumps.

Derive that checkpoint's displacement before running it. The header ends
at file offset 120. The first immediate load uses seven bytes, the register
move three, and the load of 42 seven: the jump opcode is therefore at
offset 137. Its four-byte field starts at 138 and ends just before 142.
The seven-byte load of 99 follows, so the target is 149. The patch is
`149 - (138 + 4) = 7`, encoded `07 00 00 00`. At runtime the processor adds
7 to the address immediately after the jump. Using the opcode's offset as
the subtraction base would land one byte too late.

<figure class="mechanism" aria-labelledby="branch-caption">
<div class="mechanism-title">Where does the jump measure from?</div>
<div class="byte-track">
<div><span class="diagram-label">137 · opcode</span><code>E9</code></div>
<div class="diagram-accent"><span class="diagram-label">138–141 · displacement</span><code>07 00 00 00</code></div>
<div><span class="diagram-label">142–148 · skipped load</span><code>mov rdi, 99</code></div>
<div class="diagram-accent"><span class="diagram-label">149 · target</span><strong>Continue here</strong></div>
</div>
<div class="diagram-equation"><span>End of jump: <strong>142</strong></span><span>+</span><span>Displacement: <strong>7</strong></span><span>=</span><span>Target: <strong>149</strong></span></div>
<figcaption id="branch-caption">File offsets in the checkpoint; box widths are not to scale. The patch is stored at 138, but the processor measures the jump from 142, after the complete displacement field. Read the byte sequence from left to right; on narrow screens it continues downward.</figcaption>
</figure>

## Try it

Run from the `forth-bootstrap` checkout root. This driver loads the library and compiler layers through the ELF writer, then only the first 445 lines of the emitter file: the helpers just read. It constructs the opening executable, writes the output buffer to standard output, and lets the shell capture it in a fresh temporary directory.

The program sets up the exit syscall, puts 42 in `rdi`, and jumps over an assignment of 99. The final raw bytes are the `syscall` instruction. `od` skips the 120-byte header to show the emitted instructions; the shell then runs the executable and removes the temporary directory.

<!-- tryit: expect "driver exit: 0\n 48 c7 c7 3c 00 00 00 48 89 f8 48 c7 c7 2a 00 00\n 00 e9 07 00 00 00 48 c7 c7 63 00 00 00 0f 05\nprogram exit: 42" -->
```sh
(
set -o pipefail
probe_dir=$(mktemp -d /tmp/book-probe.XXXXXXXXXX) || exit "$?"
trap 'status=$?; rm -rf -- "$probe_dir" || status=1; exit "$status"' EXIT
compiler_status=0
{
  cat forth/010-lib.fth cc/020-cc-arena.fth cc/030-cc-io.fth \
      cc/040-cc-prep.fth cc/050-cc-lex.fth \
      cc/060-cc-types.fth cc/070-cc-sym.fth cc/080-cc-elf.fth || exit "$?"
  head -n 445 cc/090-cc-emit.fth || exit "$?"
  cat <<'FORTH' || exit "$?"
cc-out-init  [lit] 0 cc-bss-size !  cc-emit-elf-header
[lit] 60 cc-emit-mov-rdi-imm32  cc-emit-mov-rax-rdi
[lit] 42 cc-emit-mov-rdi-imm32
cc-emit-jmp-rel32-placeholder
[lit] 99 cc-emit-mov-rdi-imm32
cc-patch-rel32-to-here
[lit] 15 cc-emit-byte  [lit] 5 cc-emit-byte
cc-finalize-elf
[lit] 1 cc-out-buf cc-out-pos @ write drop
bye
FORTH
} | ./seed-forth > "$probe_dir/exit42" || compiler_status=$?
printf 'driver exit: %s\n' "$compiler_status" # prints 'driver exit: 0'
test "$compiler_status" -eq 0 || exit "$compiler_status"
od -An -v -tx1 -j120 "$probe_dir/exit42" || exit "$?"
chmod +x "$probe_dir/exit42" || exit "$?"
program_status=0
"$probe_dir/exit42" || program_status=$?
printf 'program exit: %s\n' "$program_status" # prints 'program exit: 42'
test "$program_status" -eq 42
)
```

Observed output:

```text
driver exit: 0
 48 c7 c7 3c 00 00 00 48 89 f8 48 c7 c7 2a 00 00
 00 e9 07 00 00 00 48 c7 c7 63 00 00 00 0f 05
program exit: 42
```

The `e9 07 00 00 00` jump skips the immediate load containing `63`, the hexadecimal spelling of 99. The observed status shows that the skipped assignment did not overwrite 42. This checks header finalization, immediate loads, a register move, and a patched jump; it does not exercise every encoder above.

## Exercise

Hints and feedback are in [Appendix H](66-exercise-feedback.md#chapter-31-relative-displacements).

**Trace (easy).** In the checkpoint, identify the displacement's file offset and the target's file offset. Apply `cc-patch-rel32-to-here` by hand and match the result to the displayed jump bytes.

**Modify (moderate).** Replace the skipped assignment with a local load for slot 15, then slot 16, without executing either load. Predict how the jump displacement changes, rerun the driver, and explain the difference using the local-address tail.
