# Chapter 5 — ELF, entry, and the memory map

Linux learns where to load the seed, and where to start running it, from the first bytes of the file. ELF headers establish a fixed address map, and entry
code prepares the state that uses it. Together they define the complete
seed's loading and startup contract: Chapter 6 uses this initialized
machine, and Chapter 31 builds an ELF emitter for compiled programs.

Recall the instruction-reading method and register conventions from
Chapter 4. Before the seed can enter its main loop, storage must exist,
pointers must be initialized, and control must reach the intended code.

The route through the file is:

**ELF header → loadable segment → entry registers → system-variable cells → REPL**.

The **fixed-base contract** relates a file offset to its loaded address:
for a byte in this seed image, its address is `0x400000 + file offset`.
The program header establishes that contract; the entry address and initial
pointers rely on it.

## The source skeleton

The root block at `forth-bootstrap/seed/000-seed.hex0:1` lists the chunks
in file order. It is an assembly manifest; Chapters 6–12 supply the chunks
after `jmp-to-repl`.

```hex0 file=seed/000-seed.hex0
<<file-header-comment>>
<<elf-header>>
<<program-header>>
<<entry-point>>
<<sysvar-init>>
<<jmp-to-repl>>
<<dup>>
<<drop>>
<<swap>>
<<to-r>>
<<r-from>>
<<r-at>>
<<fetch>>
<<store>>
<<cfetch>>
<<cstore>>
<<plus>>
<<nand>>
<<zeq>>
<<divide>>
<<star>>
<<bye>>
<<emit>>
<<key>>
<<syscall6>>
<<find>>
<<here>>
<<comma>>
<<execute>>
<<read-word>>
<<read-char>>
<<report-token>>
<<state>>
<<latest>>
<<tick>>
<<colon>>
<<semicolon>>
<<compile-call>>
<<lit>>
<<bracket-lit>>
<<branch>>
<<zbranch>>
<<parse-decimal>>
<<repl>>
```

The source comments retain the earlier edition's chapter numbering.
Its primitive walkthrough spans Chapters 6–12 here; its REPL chapter is Chapter 12.

The preamble at `forth-bootstrap/seed/000-seed.hex0:1`
records how to read the source; preserve it with the bytes it documents.

```hex0 chunk=file-header-comment
;; 000-seed.hex0 — x86-64 Linux Forth Seed
;;
;; This file is a synthesis artifact of AI-collaborative research.
;; Co-authored by an ensemble of LLMs (Claude, Gemini, Codex, DeepSeek,
;; Qwen, Kimi, Gemma, MiniMax) under human architectural direction.
;;
;; License: MIT (see /LICENSE)
;;
;; How to read this file: after the two ELF headers and the boot code,
;; each of the 32 primitives is one unit — its dictionary header (link,
;; flags, nlen, name) directly followed by its machine code, so a word's
;; execution token (xt) is simply the address of its code.  The units
;; appear in the order the book teaches them; the six
;; unnamed helpers and the REPL sit alongside the words that use them.
;; Every line is one field or one instruction; the text after ';' is a
;; comment (hex0 ignores it).  Addresses are file offsets; the image
;; loads at 0x400000, so offset 0xNNN is address 0x400NNN.
;;
```

The preamble contributes no machine bytes; the ELF header is the first
material the loader will read.

## Identify the executable and its entry

The ELF header at `forth-bootstrap/seed/000-seed.hex0:19` identifies the
executable and tells Linux where to find its program header and entry point.

```hex0 chunk=elf-header
;; ===== ELF64 header (64 bytes) @ 0x000 =====
;; Layout reference: man 5 elf, Elf64_Ehdr
7F 45 4C 46                               ; e_ident[0..3]     = magic "\x7fELF"
02                                        ; e_ident[EI_CLASS] = ELFCLASS64
01                                        ; e_ident[EI_DATA]  = ELFDATA2LSB (little-endian)
01                                        ; e_ident[EI_VERSION] = EV_CURRENT
00                                        ; e_ident[EI_OSABI] = ELFOSABI_NONE (System V)
00                                        ; e_ident[EI_ABIVERSION] = 0
00 00 00 00 00 00 00                      ; e_ident padding (7 zero bytes)
02 00                                     ; e_type      = ET_EXEC
3E 00                                     ; e_machine   = EM_X86_64
01 00 00 00                               ; e_version   = 1
78 00 40 00 00 00 00 00                   ; e_entry     = 0x400078 (_start)
40 00 00 00 00 00 00 00                   ; e_phoff     = 64
00 00 00 00 00 00 00 00                   ; e_shoff     = 0 (no section headers)
00 00 00 00                               ; e_flags     = 0
40 00                                     ; e_ehsize    = 64
38 00                                     ; e_phentsize = 56
01 00                                     ; e_phnum     = 1
00 00                                     ; e_shentsize = 0
00 00                                     ; e_shnum     = 0
00 00                                     ; e_shstrndx  = 0

```

Recall little-endian from Chapter 4 when comparing the byte columns with
the field values in the comments.

Read the fields in groups. `e_ident`, `e_type`, and `e_machine` identify an
ELF64 executable for x86-64. `e_entry` selects the first instruction's
virtual address. `e_phoff`, `e_phentsize`, and `e_phnum` locate and describe
the program-header table. The section-header fields are zero: this seed
has no section table, and its loading recipe comes from the program header.

The distinction between an offset and an address matters immediately.
`e_phoff = 64` is a position in the file; `e_entry = 0x400078` is a position
in the process's address space. The fixed-base contract connects them only
after we know what the program header maps.

## Make storage exist

The program header at `forth-bootstrap/seed/000-seed.hex0:42` supplies the
mapping that makes the seed's embedded addresses usable.

```hex0 chunk=program-header
;; ===== Program header (56 bytes) @ 0x040, one PT_LOAD =====
01 00 00 00                               ; p_type   = PT_LOAD
07 00 00 00                               ; p_flags  = R|W|X
00 00 00 00 00 00 00 00                   ; p_offset = 0
00 00 40 00 00 00 00 00                   ; p_vaddr  = 0x400000
00 00 40 00 00 00 00 00                   ; p_paddr  = 0x400000 (ignored on Linux)
EC 06 00 00 00 00 00 00                   ; p_filesz = 1772 (the whole file)
00 00 00 01 00 00 00 00                   ; p_memsz  = 0x1000000 (16 MiB; the kernel zero-fills past the file)
00 10 00 00 00 00 00 00                   ; p_align  = 0x1000

```

This requests a single loadable segment containing both the file image and
additional zero-filled storage. `p_offset = 0` and `p_vaddr = 0x400000`
establish the fixed-base contract: the beginning of the file becomes the
beginning of this mapping.

Distinguish `p_filesz`, the bytes supplied by the file, from `p_memsz`, the
bytes provided in memory. Here the file supplies 1,772 bytes, while the
segment spans 16 MiB. The interval after the file image is zero-filled,
so the seed can store data beyond its on-disk bytes.
These are virtual addresses; the header does not promise that all of that
storage is physically resident at startup.

The permission flags allow reading, writing, and executing throughout the
segment. That accommodates the seed's mutable data and the machine code it
will later write; Chapter 10 teaches that compiler. `p_align = 0x1000`
records the segment alignment, with file offset and virtual address
congruent at that alignment.

Compute the entry position from the header sizes. The ELF header occupies
64 bytes and its program header occupies 56 bytes: together they occupy
120 bytes, or `0x78`. Applying the fixed-base contract gives
`0x400000 + 0x78 = 0x400078`, exactly `e_entry`. The entry is immediately
after the headers, not at the ELF magic.

## Give the registers their starting values

The entry code at `forth-bootstrap/seed/000-seed.hex0:52` records the seed's
address conventions and initializes the data-stack registers.

```hex0 chunk=entry-point
;; ===== Code at 0x400078 =====
;; Register and memory conventions used by every routine below:
;;   rbp      = data-stack pointer (grows down); rdi = top of stack (TOS)
;;   rsp      = return stack (the x86 call stack)
;;   rbx      = length of the last token read_word read
;;   0x411000 = data-stack base (first push lands at 0x410FF8)
;;   0x412000 = single-byte I/O scratch (emit, key)
;;   0x412800 = token buffer, TIB (read_word)
;;   0x413000 = sysvar page, 8 bytes each: STATE, LATEST, HERE, LAST_FOUND
;;              (0x413000, 0x413008, 0x413010, 0x413018)
;;
;; ----- _start @ 0x078  entry point: set up the data stack -----
48 BD 00 10 41 00 00 00 00 00             ; mov rbp, 0x411000
48 31 FF                                  ; xor rdi, rdi

```

The entry instructions set `rbp = 0x411000` and clear `rdi`; recall the
cached-top pattern from Chapter 4. Chapter 6 follows the stack transfers.
The instructions here occupy 13 bytes, so the next startup responsibility
begins at file offset `0x085`.

There is no assignment to `rsp` in this startup code. The seed keeps the
process stack supplied at entry for its return stack; recall `rsp` from
Chapter 4. It is separate from the data-stack address reserved inside the
loadable segment, and has no fixed address in this map.

## Initialize the mutable system variables

Mapped storage alone does not choose the seed's initial state. The stores
at `forth-bootstrap/seed/000-seed.hex0:67` initialize the system-variable
cells before execution enters the loop.

```hex0 chunk=sysvar-init
;; ----- sysvar_init @ 0x085  STATE, LATEST, HERE, LAST_FOUND -----
48 C7 04 25 00 30 41 00 00 00 00 00       ; mov qword [STATE], 0
48 C7 04 25 08 30 41 00 17 06 40 00       ; mov qword [LATEST], 0x400617 (0branch header)
48 C7 04 25 10 30 41 00 00 10 40 00       ; mov qword [HERE], 0x401000
48 C7 04 25 18 30 41 00 00 00 00 00       ; mov qword [LAST_FOUND], 0

```

These stores set the initial mode, dictionary head, allocation cursor, and
lookup scratch value. Each writes a cell at its named absolute address;
the operation initializes existing storage.

| Cell address | Name | Initial contents | Meaning here |
|---|---|---|---|
| `0x413000` | `STATE` | `0` | Begin in interpret mode |
| `0x413008` | `LATEST` | `0x400617` | Identify the last built-in dictionary header |
| `0x413010` | `HERE` | `0x401000` | Select where new dictionary storage begins |
| `0x413018` | `LAST_FOUND` | `0` | Start with no remembered lookup hit |

Keep the cell's address separate from its contents. The address of the
`HERE` cell is `0x413010`; the initial value stored there is `0x401000`.
Changing the contents moves the cursor without moving the cell itself.
Likewise, `LATEST` stores an address inside the file image, whereas `HERE`
starts in the zero-filled extension. This is the fixed-base contract again,
now supporting pointers rather than the entry address.

Chapter 9 teaches dictionary headers, lookup, and the allocation cursor's
operations. Chapter 10 teaches the mode changes that use `STATE`. The stores
to `STATE` and `LAST_FOUND` explicitly write zero even though those cells
are in the zero-filled part of the segment.

## Read the seed memory map

The program header and startup conventions give this memory map.
Range ends are exclusive.

| Address or interval | Role at startup |
|---|---|
| `0x400000` to `0x400078` | ELF and program headers |
| `0x400078` to `0x4000BA` | Entry instructions, system-variable stores, and jump |
| `0x4000BA` to `0x4006EC` | Remaining seed image: built-in dictionary, code, and helpers |
| `0x4006EC` to `0x401000` | Zero-filled gap after the file image |
| `0x401000`, growing upward | Initial dictionary allocation area |
| Below `0x411000`, growing downward | Data stack addressed by `rbp` |
| `0x412000` | I/O scratch byte; Chapter 8 teaches its use |
| `0x412800` | Token buffer; Chapter 9 teaches its use |
| `0x413000` through the `LAST_FOUND` cell | System-variable cells |
| `0x1400000` | End of the loadable segment |
| Process stack, address supplied at entry | Return stack addressed by `rsp`, outside this fixed map |

The dictionary and data stack grow toward each other. The program header
does not divide them into separately protected regions: crossing a logical
boundary within the segment can overwrite other seed storage. In particular,
this map does not promise a guarded or automatically growing data stack.

The end of the file image comes from `0x400000 + 0x6EC = 0x4006EC`;
the end of the segment comes from `0x400000 + 0x1000000 = 0x1400000`.
Do not mistake either endpoint for the initial allocation cursor.

This is the seed's map before loading the compiler. Chapter 27 owns the
compiler arena and I/O buffers; Chapters 28 and 30 own preprocessor and
symbol storage, and Chapter 32 owns generated runtime shims. Their storage
layouts are not part of this startup contract.

## Hand control to the loop

The jump at `forth-bootstrap/seed/000-seed.hex0:73` transfers control to
the REPL after all startup assignments have finished.

```hex0 chunk=jmp-to-repl
;; ----- jmp_repl @ 0x0B5  enter the REPL -----
E9 DF 05 00 00                            ; jmp repl  (rel32 = 0x699 - 0x0BA)

```

Recall `rel32` from Chapter 4: check the displacement against the next
instruction, here at file offset `0x0BA`.
Adding `0x5DF` gives `0x699`, so the fixed-base contract places the target at
`0x400699`. Chapter 12 teaches what happens inside that loop; Chapter 6
next begins the primitive walkthrough.

## Try it: check the loading contract

Run these commands from the `forth-bootstrap` checkout at `./forth-bootstrap`.
Build the complete seed so the startup code has its real destination.
The build script at `forth-bootstrap/seed/build.sh:27` invokes its hex0
assembler and writes `seed-forth` in that checkout.

```sh
./seed/build.sh
```

Observed output:

```text
Built seed-forth (1772 bytes) using vendor/stage0-posix/bootstrap-seeds/POSIX/AMD64/hex0-seed
```

Use `readelf` to inspect the loading recipe and `od` to read the entry bytes
at the calculated file offset. Then supply empty input and print the exit
status. This checks header acceptance and the startup path through to exit;
it does not test every future use of the memory map. Empty input takes the
loop's end-of-input path at `forth-bootstrap/seed/000-seed.hex0:664`, without
requiring a Forth word from a later chapter. Chapter 12 teaches that path.

```sh
readelf -lW ./seed-forth
od -An -tx1 -j 120 -N 13 ./seed-forth
printf '' | ./seed-forth
printf 'exit status %s\n' "$?"
# prints "exit status 0"
```

Observed output:

```text

Elf file type is EXEC (Executable file)
Entry point 0x400078
There is 1 program header, starting at offset 64

Program Headers:
  Type           Offset   VirtAddr           PhysAddr           FileSiz  MemSiz   Flg Align
  LOAD           0x000000 0x0000000000400000 0x0000000000400000 0x0006ec 0x1000000 RWE 0x1000
 48 bd 00 10 41 00 00 00 00 00 48 31 ff
exit status 0
```

## Exercises

- **Trace — easy.** Calculate `e_entry` from the end of the program header,
  then calculate the final startup jump's target. Explain why one uses
  the file base and the other uses the next instruction.
- **Verify — easy.** Match the checkpoint's `LOAD` fields `FileSiz`,
  `MemSiz`, and `VirtAddr` to the map. Identify the entry instructions
  in the `od` output.
- **Trace — medium.** Locate the `HERE` cell and its initial contents.
  Which address lies in the system-variable area? Which points into
  the dictionary allocation area?
