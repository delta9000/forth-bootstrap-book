# Chapter 40 — Objects and relocations

A relocatable object can name a function whose address is still unknown. The writer stores section bytes, symbol definitions, and instructions for repairing address fields, leaving final placement to a linker. The result is an ELF object that a host inspection tool can read before any executable exists.

## The interface between compiler and linker

The writer grows an object in this order: select a workspace, initialize section metadata, append payload bytes, register symbols and relocations, serialize, then publish. A section-relative value locates a symbol; a relocation identifies a field for the linker to fill. The ELF wrapper (Chapter 31) produced a complete executable; this writer leaves final addresses to the linker.

The linker in Chapter 42 consumes these objects (`forth-bootstrap/cc/140-cc-link.fth:3`). Chapter 50 uses both pieces to compile runtime and tool sources, archive the runtime, and link the tools (`forth-bootstrap/cc/driver/seed-cc-start.fth:309` and `forth-bootstrap/cc/driver/seed-cc-start.fth:335`). All object construction happens inside the Forth process.

Follow one unfinished call through the writer checkpoint. Its `.text`
starts with `E8 00 00 00 00 C3`: a call with an empty four-byte field,
then a return. Three records give those zero bytes a meaning:

- The section holds the instruction bytes, with the field at offset 1.
- The symbol record names `external` and says its definition is missing.
- The relocation connects that field to that symbol, with the call's
  relative kind and an addend of −4.

Zero alone could be a valid displacement, so the linker cannot discover
unfinished work by scanning for zeroes. It needs the relocation record.
The writer can validate and serialize all three records before knowing
where `external` will land. Keep its symbol handle separate from the ELF
symbol-table index: serialization assigns the latter after putting local
symbols first. Chapter 42 will supply final addresses and explain why
the call's addend is −4. The checkpoint here inspects the records that
carry that obligation forward.

The source header establishes the writer's dependencies and stable-handle contract (`forth-bootstrap/cc/081-cc-object.fth:1`):

```forth file=cc/081-cc-object.fth
\ 081-cc-object.fth — bounded ELF64/AMD64 relocatable object writer.
\ Depends only on 010-lib, 020-cc-arena, 030-cc-io. No tool subprocesses.
\ ELF layout follows the System V gABI and AMD64 psABI.
\ API symbol IDs are stable; ELF indexes are assigned locals-first at build.
\ Errors: 244 section/range/alignment, 245 capacity, 246 symbol,
\ 247 relocation, 248 file I/O. Generic output overflow remains error 21.

```
Section identity stays separate from symbol metadata. `cc-obj-undef` means that a definition is still missing; `cc-obj-abs` gives a value independent of section placement. The remaining constants describe where payload belongs and how names are exported (`forth-bootstrap/cc/081-cc-object.fth:8`):

```forth file=cc/081-cc-object.fth
[lit] 0 constant cc-obj-undef
[lit] 1 constant cc-obj-text
[lit] 2 constant cc-obj-rodata
[lit] 3 constant cc-obj-data
[lit] 4 constant cc-obj-bss
[lit] 65521 constant cc-obj-abs
[lit] 0 constant cc-obj-local
[lit] 1 constant cc-obj-global
[lit] 2 constant cc-obj-weak
[lit] 0 constant cc-obj-notype
[lit] 1 constant cc-obj-object
[lit] 2 constant cc-obj-func
[lit] 3 constant cc-obj-section
[lit] 0 constant cc-obj-default
[lit] 1 constant cc-obj-internal
[lit] 2 constant cc-obj-hidden
[lit] 3 constant cc-obj-protected
```

`cc-obj-text` holds instructions, `cc-obj-rodata` read-only bytes, `cc-obj-data` writable initialized bytes, and `cc-obj-bss` zero-filled storage without a file payload. The existing native layout supplies object sizes and alignment; this interface supplies a section and an offset instead of a final address.

A local name belongs to its object; global and weak names participate in linking. A weak definition can yield to a strong one. Visibility is another independent field: default permits ordinary external visibility, internal and hidden restrict it, and protected preserves a definition's binding within its defining component. This writer records those choices; it does not resolve them.
A relocation kind tells the eventual linker how to interpret the reserved field (`forth-bootstrap/cc/081-cc-object.fth:25`):

```forth file=cc/081-cc-object.fth
[lit] 1 constant cc-obj-r64
[lit] 2 constant cc-obj-pc32
[lit] 4 constant cc-obj-plt32
[lit] 10 constant cc-obj-r32
[lit] 11 constant cc-obj-r32s

```

Absolute relocations request full-width addresses or narrower signed or unsigned values. `cc-obj-pc32` requests a displacement from the relocation place; `cc-obj-plt32` identifies the call-target form. The writer validates the field width, while Chapter 42 performs resolution and range checking.

## Choose a bounded workspace

Independent limits keep an oversized name table from borrowing storage reserved for instructions. Each mutable limit is read through its matching `-cap` accessor (`forth-bootstrap/cc/081-cc-object.fth:31`):

```forth file=cc/081-cc-object.fth
[lit] 524288 constant cc-obj-text-default-cap
variable cc-obj-text-limit
cc-obj-text-default-cap cc-obj-text-limit !
: cc-obj-text-cap ( -- bytes ) cc-obj-text-limit @ ;
[lit] 262144 constant cc-obj-section-default-cap
variable cc-obj-section-limit
cc-obj-section-default-cap cc-obj-section-limit !
: cc-obj-section-cap ( -- bytes ) cc-obj-section-limit @ ;
[lit] 1073741824 constant cc-obj-bss-cap
[lit] 2048 constant cc-obj-symbol-default-cap
variable cc-obj-symbol-limit
cc-obj-symbol-default-cap cc-obj-symbol-limit !
: cc-obj-symbol-cap ( -- entries ) cc-obj-symbol-limit @ ;
[lit] 4096 constant cc-obj-reloc-default-cap
variable cc-obj-reloc-limit
cc-obj-reloc-default-cap cc-obj-reloc-limit !
: cc-obj-reloc-cap ( -- entries ) cc-obj-reloc-limit @ ;
[lit] 65536 constant cc-obj-string-default-cap
variable cc-obj-string-limit
cc-obj-string-default-cap cc-obj-string-limit !
: cc-obj-string-cap ( -- bytes ) cc-obj-string-limit @ ;
```

The backing arrays use the same indirection as the limits.

The `-buffer` cells let a workspace selection change the addresses without changing callers (`forth-bootstrap/cc/081-cc-object.fth:52`):

```forth file=cc/081-cc-object.fth
create cc-obj-default-payload cc-obj-text-default-cap cc-obj-section-default-cap [lit] 2 * + allot
variable cc-obj-payload-buffer
cc-obj-default-payload cc-obj-payload-buffer !
: cc-obj-payload ( -- address ) cc-obj-payload-buffer @ ;
create cc-obj-default-symbols cc-obj-symbol-default-cap 1+ [lit] 64 * allot
variable cc-obj-symbols-buffer
cc-obj-default-symbols cc-obj-symbols-buffer !
: cc-obj-symbols ( -- address ) cc-obj-symbols-buffer @ ;
create cc-obj-default-relocs cc-obj-reloc-default-cap [lit] 40 * allot
variable cc-obj-relocs-buffer
cc-obj-default-relocs cc-obj-relocs-buffer !
: cc-obj-relocs ( -- address ) cc-obj-relocs-buffer @ ;
create cc-obj-default-strings cc-obj-string-default-cap allot
variable cc-obj-strings-buffer
cc-obj-default-strings cc-obj-strings-buffer !
: cc-obj-strings ( -- address ) cc-obj-strings-buffer @ ;
```

The extra symbol row reserves the null entry. The string capacity includes the initial empty name and every terminating NUL. `.bss` needs only a length, so it has no backing slice.
Larger translation units can select a mapped workspace whose slices are sized by the direct-profile constants (`forth-bootstrap/cc/081-cc-object.fth:68`):

```forth file=cc/081-cc-object.fth
\ Complete original insn-attrtab.c needs 3,328,178 text bytes and 20,568
\ relocations. Round independently to whole MiB / 512-entry quanta.
[lit] 4194304 constant cc-obj-text-direct-cap
[lit] 20992 constant cc-obj-reloc-direct-cap
\ Complete original insn-output.c needs 7,772 symbols, excluding row zero,
\ and 77,487 string bytes. Round rows to 512 and string storage to 4 KiB.
[lit] 8192 constant cc-obj-symbol-direct-cap
[lit] 77824 constant cc-obj-string-direct-cap
\ Complete binutils 2.30 i386-dis.c needs 841,448 .data bytes (its opcode
\ tables); GCC's largest .rodata is 120,874. Rodata and data each get the
\ measured maximum plus 25%, rounded up to whole MiB: 2 MiB.
[lit] 2097152 constant cc-obj-section-direct-cap
variable cc-obj-direct-base
: cc-obj-direct-payload-bytes ( -- bytes )
  cc-obj-text-direct-cap cc-obj-section-direct-cap [lit] 2 * + ;
: cc-obj-direct-symbol-bytes ( -- bytes )
  cc-obj-symbol-direct-cap 1+ [lit] 64 * ;
```

`cc-obj-direct-base` retains the mapping for reuse. The measurements in these source comments are historical evidence, not measurements repeated by this chapter's checkpoint.

## Switch storage as a unit

Returning to the default workspace must restore addresses and capacities together (`forth-bootstrap/cc/081-cc-object.fth:85`):

```forth file=cc/081-cc-object.fth
: cc-obj-default-workspace ( -- )
  cc-obj-text-default-cap cc-obj-text-limit !
  cc-obj-section-default-cap cc-obj-section-limit !
  cc-obj-reloc-default-cap cc-obj-reloc-limit !
  cc-obj-symbol-default-cap cc-obj-symbol-limit !
  cc-obj-string-default-cap cc-obj-string-limit !
  cc-obj-default-payload cc-obj-payload-buffer !
  cc-obj-default-relocs cc-obj-relocs-buffer !
  cc-obj-default-symbols cc-obj-symbols-buffer !
  cc-obj-default-strings cc-obj-strings-buffer ! ;
```
The mapped selection allocates only on its first use, then derives every table address from the same base (`forth-bootstrap/cc/081-cc-object.fth:95`):

```forth file=cc/081-cc-object.fth
: cc-obj-direct-workspace ( -- )
  cc-obj-direct-base @ 0= if,
    cc-obj-direct-payload-bytes cc-obj-reloc-direct-cap [lit] 40 * +
    cc-obj-direct-symbol-bytes + cc-obj-string-direct-cap +
    [lit] 245 cc-workspace-map cc-obj-direct-base !
  then,
  cc-obj-text-direct-cap cc-obj-text-limit !
  cc-obj-section-direct-cap cc-obj-section-limit !
  cc-obj-reloc-direct-cap cc-obj-reloc-limit !
  cc-obj-symbol-direct-cap cc-obj-symbol-limit !
  cc-obj-string-direct-cap cc-obj-string-limit !
  cc-obj-direct-base @ cc-obj-payload-buffer !
  cc-obj-direct-base @ cc-obj-direct-payload-bytes +
  dup cc-obj-relocs-buffer !
  cc-obj-reloc-direct-cap [lit] 40 * +
  dup cc-obj-symbols-buffer !
  cc-obj-direct-symbol-bytes + cc-obj-strings-buffer ! ;
```

Workspace selection neither migrates live rows nor resets counts. Choose it before `cc-obj-init`. A section fitting its own limit does not guarantee that the complete serialized object fits the shared output buffer; headers, names, symbols, and relocations consume output space too.

## Keep object state separate from publication

Section descriptions and object counts remain separate from payload storage (`forth-bootstrap/cc/081-cc-object.fth:112`):

```forth file=cc/081-cc-object.fth
\ Section metadata is nine CELLS, not an in-memory Elf64_Shdr:
\ name/type/flags/file-offset/size/link/info/alignment/entry-size.
create cc-obj-sections  [lit] 720 allot
variable cc-obj-current
variable cc-obj-nsym
variable cc-obj-nrel
variable cc-obj-nstr
variable cc-obj-shoff
variable cc-obj-local-end
variable cc-obj-initialized
```

`cc-obj-current` selects the emission section; `cc-obj-initialized` guards public operations.
A failed file operation needs enough state to distinguish an owned temporary from someone else's file (`forth-bootstrap/cc/081-cc-object.fth:122`):

```forth file=cc/081-cc-object.fth
\ Publication state is separate from object metadata and reset between writes.
create cc-obj-temp-path  [lit] 4096 allot
create cc-obj-temp-suffix  s, .obj-
create cc-obj-hex-digits  s, 0123456789abcdef
create cc-obj-stat-buffer  [lit] 144 allot
variable cc-obj-path
variable cc-obj-fd
variable cc-obj-written
variable cc-obj-temp-owned
variable cc-obj-temp-length
variable cc-obj-pid
variable cc-obj-ti
: cc-obj-reset-write ( -- )
  true cc-obj-fd ! [lit] 0 cc-obj-path ! [lit] 0 cc-obj-written !
  [lit] 0 cc-obj-temp-owned ! [lit] 0 cc-obj-temp-length !
  [lit] 0 cc-obj-pid ! [lit] 0 cc-obj-ti ! [lit] 0 cc-obj-temp-path c! ;

```

`cc-obj-temp-path` names the sibling temporary. `cc-obj-reset-write` invalidates the descriptor and clears publication state without discarding object records.

## Check before growing

Address helpers translate section and relocation indexes into rows and select each backed section's slice (`forth-bootstrap/cc/081-cc-object.fth:139`):

```forth file=cc/081-cc-object.fth
: cc-obj-sh ( section -- a )  [lit] 72 * cc-obj-sections + ;
: cc-obj-rel ( index -- a )  [lit] 40 * cc-obj-relocs + ;
: cc-obj-base ( section -- a )
  dup cc-obj-text = if, drop cc-obj-payload exit, then,
  [lit] 2 - cc-obj-section-cap * cc-obj-text-cap + cc-obj-payload + ;
: cc-obj-length ( section -- n )  cc-obj-sh [lit] 32 + @ ;
: cc-obj-zero ( a n -- )
  begin, dup while,
    over [lit] 0 swap c! swap 1+ swap 1-
  repeat, 2drop ;

```

Reservation uses `cc-obj-zero` so a reused workspace cannot expose an earlier object’s bytes.
An invalid index must fail before multiplication can turn it into an address (`forth-bootstrap/cc/081-cc-object.fth:150`):

```forth file=cc/081-cc-object.fth
\ Reject high-bit values explicitly: the library's comparisons are signed.
: cc-obj-bound ( n maximum code -- )
  >r over 0< if, r@ cc-die then,
  > if, r@ cc-die then, r> drop ;
\ IDs include reserved row zero. Check before multiplying, in either workspace.
: cc-obj-sym ( id -- a )
  dup cc-obj-symbol-cap [lit] 246 cc-obj-bound
  [lit] 64 * cc-obj-symbols + ;
: cc-obj-check-section ( section -- )
  dup [lit] 4 [lit] 244 cc-obj-bound
  0= if, [lit] 244 cc-die then, ;
```

`cc-obj-bound` explicitly rejects a high-bit value before applying the signed comparison. `cc-obj-sym` checks the selected symbol capacity, including the reserved row. `cc-obj-check-section` excludes both the null section and indexes beyond the payload sections.
Section selection and growth share initialization, alignment, and remaining-capacity checks (`forth-bootstrap/cc/081-cc-object.fth:161`):

```forth file=cc/081-cc-object.fth
: cc-obj-check-align ( n -- )
  dup [lit] 4096 [lit] 244 cc-obj-bound
  dup 0= if, [lit] 244 cc-die then,
  dup 1- and if, [lit] 244 cc-die then, ;
: cc-obj-require-init ( -- )
  cc-obj-initialized @ 0= if, [lit] 244 cc-die then, ;
: cc-obj-use ( section -- )
  cc-obj-require-init dup cc-obj-check-section cc-obj-current ! ;
: cc-obj-here ( -- offset )
  cc-obj-require-init cc-obj-current @ cc-obj-length ;
: cc-obj-room ( count -- )
  cc-obj-current @ cc-obj-bss = if,
    cc-obj-bss-cap
  else, cc-obj-current @ cc-obj-text = if,
    cc-obj-text-cap else, cc-obj-section-cap then, then,
  cc-obj-here - [lit] 245 cc-obj-bound ;

```

`cc-obj-check-align` accepts nonzero powers of two up to the source limit. `cc-obj-room` subtracts the used length before comparing the request, avoiding a potentially wrapping used-plus-request calculation.

## Append or patch section bytes

Reservation advances the logical length in every section, but clears memory only when file-backed bytes exist (`forth-bootstrap/cc/081-cc-object.fth:178`):

```forth file=cc/081-cc-object.fth
\ Reserve zeroed bytes; .bss grows in memory without backing file bytes.
: cc-obj-reserve ( count -- offset )
  dup cc-obj-room
  cc-obj-here >r
  cc-obj-current @ cc-obj-bss <> if,
    dup cc-obj-current @ cc-obj-base r@ + swap cc-obj-zero
  then,
  cc-obj-current @ cc-obj-sh [lit] 32 + +! r> ;
: cc-obj-align ( alignment -- )
  cc-obj-require-init dup cc-obj-check-align
  dup cc-obj-current @ cc-obj-sh [lit] 56 + @ > if,
    dup cc-obj-current @ cc-obj-sh [lit] 56 + !
  then,
  dup cc-obj-here + 1- over / * cc-obj-here -
  cc-obj-reserve drop ;
```

`cc-obj-reserve` returns the old offset, so a caller can retain the object's start. `cc-obj-align` raises the section's declared alignment when necessary and reserves padding up to the next aligned offset. Alignment therefore survives serialization as metadata as well as padding.

All emitters reach the same section bound through `cc-obj-byte`; direct byte emission into `.bss` is rejected (`forth-bootstrap/cc/081-cc-object.fth:193`):

```forth file=cc/081-cc-object.fth
: cc-obj-byte ( byte -- )
  cc-obj-current @ cc-obj-bss = if, [lit] 244 cc-die then,
  [lit] 1 cc-obj-reserve cc-obj-current @ cc-obj-base + c! ;
: cc-obj-4le ( value -- )
  dup cc-obj-byte [lit] 256 / dup cc-obj-byte
  [lit] 256 / dup cc-obj-byte [lit] 256 / cc-obj-byte ;
: cc-obj-8le ( value -- )
  dup cc-obj-4le [lit] 4294967296 / cc-obj-4le ;
: cc-obj-bytes ( address count -- )
  dup cc-obj-room
  begin, dup while,
    over c@ cc-obj-byte swap 1+ swap 1-
  repeat, 2drop ;

```
A local fixup may overwrite an existing field, but must not create bytes or cross the section end (`forth-bootstrap/cc/081-cc-object.fth:207`):

```forth file=cc/081-cc-object.fth
\ A patch must fit wholly inside already emitted file-backed bytes.
variable cc-obj-patch-a
variable cc-obj-patch-n
: cc-obj-patch ( value section offset width -- )
  cc-obj-require-init cc-obj-patch-n ! >r
  dup cc-obj-check-section
  dup cc-obj-bss = if, [lit] 244 cc-die then,
  r@ over cc-obj-length [lit] 244 cc-obj-bound
  cc-obj-patch-n @ over cc-obj-length r@ - [lit] 244 cc-obj-bound
  cc-obj-base r> + cc-obj-patch-a !
  begin, cc-obj-patch-n @ while,
    dup cc-obj-patch-a @ c! [lit] 256 /
    [lit] 1 cc-obj-patch-a +! [lit] 1 cc-obj-patch-n -!
  repeat, drop ;
: cc-obj-patch-4le ( value section offset -- )  [lit] 4 cc-obj-patch ;
: cc-obj-patch-8le ( value section offset -- )  [lit] 8 cc-obj-patch ;

```

The range checks validate the starting offset and then the complete field. `cc-obj-patch-4le` and `cc-obj-patch-8le` supply the width; neither records work for a linker.

## Give symbols stable handles

A symbol definition pairs a section-relative value with an extent that must fit the section (`forth-bootstrap/cc/081-cc-object.fth:224`):

```forth file=cc/081-cc-object.fth
\ Symbol cells: string-offset, binding, type, visibility, section, value,
\ size, final ELF index. Names are copied; caller storage may be reused.
variable cc-obj-s-a
variable cc-obj-s-u
variable cc-obj-s-bind
variable cc-obj-s-type
variable cc-obj-s-vis
variable cc-obj-s-sec
variable cc-obj-s-value
variable cc-obj-s-size
variable cc-obj-s-row
: cc-obj-check-definition ( -- )
  cc-obj-s-sec @ cc-obj-abs = if, exit, then,
  cc-obj-s-sec @ [lit] 4 [lit] 246 cc-obj-bound
  cc-obj-s-sec @ 0= if,
    cc-obj-s-value @ cc-obj-s-size @ or if, [lit] 246 cc-die then,
  else,
    cc-obj-s-value @ cc-obj-s-sec @ cc-obj-length [lit] 246 cc-obj-bound
    cc-obj-s-size @ cc-obj-s-sec @ cc-obj-length cc-obj-s-value @ -
    [lit] 246 cc-obj-bound
  then, ;
```

`cc-obj-check-definition` permits an absolute symbol without a section extent. An undefined symbol must have zero value and size; a section-defined symbol must fit entirely within bytes or memory already reserved.
Finishing a forward declaration updates its existing row, preserving every reference to its handle (`forth-bootstrap/cc/081-cc-object.fth:245`):

```forth file=cc/081-cc-object.fth
: cc-obj-put-definition ( -- )
  cc-obj-s-sec @ cc-obj-s-row @ [lit] 32 + !
  cc-obj-s-value @ cc-obj-s-row @ [lit] 40 + !
  cc-obj-s-size @ cc-obj-s-row @ [lit] 48 + ! ;
: cc-obj-check-id ( id -- )
  dup cc-obj-nsym @ [lit] 246 cc-obj-bound
  0= if, [lit] 246 cc-die then, ;
: cc-obj-define ( id section value size -- )
  cc-obj-require-init cc-obj-s-size ! cc-obj-s-value ! cc-obj-s-sec !
  dup cc-obj-check-id cc-obj-sym cc-obj-s-row !
  cc-obj-s-row @ [lit] 16 + @ cc-obj-section = if,
    cc-obj-s-value @ cc-obj-s-size @ or if, [lit] 246 cc-die then,
    cc-obj-s-sec @ cc-obj-check-section
  then,
  cc-obj-check-definition cc-obj-put-definition ;
```

`cc-obj-check-id` requires an allocated non-null handle. `cc-obj-define` applies the same definition check as initial insertion, with the additional restrictions for a section symbol.

## Copy names into object storage

Symbol insertion validates metadata before allocating a row or copying the name (`forth-bootstrap/cc/081-cc-object.fth:260`):

```forth file=cc/081-cc-object.fth
: cc-obj-symbol ( name length binding type visibility section value size -- id )
  cc-obj-require-init
  cc-obj-s-size ! cc-obj-s-value ! cc-obj-s-sec ! cc-obj-s-vis !
  cc-obj-s-type ! cc-obj-s-bind ! cc-obj-s-u ! cc-obj-s-a !
  cc-obj-nsym @ 1+ cc-obj-symbol-cap [lit] 245 cc-obj-bound
  cc-obj-s-bind @ [lit] 2 [lit] 246 cc-obj-bound
  cc-obj-s-type @ [lit] 3 [lit] 246 cc-obj-bound
  cc-obj-s-vis @ [lit] 3 [lit] 246 cc-obj-bound
  cc-obj-s-u @ cc-obj-string-cap cc-obj-nstr @ - 1- [lit] 245 cc-obj-bound
  cc-obj-check-definition
  cc-obj-s-type @ cc-obj-section = if,
    cc-obj-s-bind @ cc-obj-local <> cc-obj-s-u @ or
    cc-obj-s-value @ or cc-obj-s-size @ or if, [lit] 246 cc-die then,
    cc-obj-s-sec @ cc-obj-check-section
  then,
  cc-obj-s-u @ 0= cc-obj-s-type @ cc-obj-section <> and if,
    [lit] 246 cc-die
  then,
```

`cc-obj-symbol` accepts the argument sequence in its stack comment and returns a stable ID. It checks row and string capacity independently. A section symbol is local, unnamed, and has zero value and size; every other symbol needs a name. Ordinary names cannot contain an embedded NUL.
Only validated names and metadata enter the persistent tables (`forth-bootstrap/cc/081-cc-object.fth:278`):

```forth file=cc/081-cc-object.fth
  [lit] 0
  begin, dup cc-obj-s-u @ < while,
    dup cc-obj-s-a @ + c@ 0= if, [lit] 246 cc-die then, 1+
  repeat, drop
  [lit] 1 cc-obj-nsym +!
  cc-obj-nsym @ cc-obj-sym cc-obj-s-row !
  cc-obj-nstr @ cc-obj-s-row @ !
  cc-obj-s-bind @ cc-obj-s-row @ [lit] 8 + !
  cc-obj-s-type @ cc-obj-s-row @ [lit] 16 + !
  cc-obj-s-vis @ cc-obj-s-row @ [lit] 24 + !
  cc-obj-put-definition
  [lit] 0
  begin, dup cc-obj-s-u @ < while,
    dup cc-obj-s-a @ + c@ cc-obj-strings cc-obj-nstr @ + c!
    [lit] 1 cc-obj-nstr +! 1+
  repeat, drop
  [lit] 0 cc-obj-strings cc-obj-nstr @ + c! [lit] 1 cc-obj-nstr +!
  cc-obj-nsym @ ;

```

The handle is the insertion count. A string-table offset lets the caller reuse its name buffer immediately. Serialization assigns the ELF index.

## Record unfinished addresses

An explicit relocation addend keeps the adjustment separate from the bytes that will be repaired (`forth-bootstrap/cc/081-cc-object.fth:297`):

```forth file=cc/081-cc-object.fth
\ RELA stores an explicit signed addend, including negative values, as 8 LE
\ bytes. The field in .text/.data is not used as an implicit addend.
variable cc-obj-r-sec
variable cc-obj-r-off
variable cc-obj-r-kind
variable cc-obj-r-sym
variable cc-obj-r-add
: cc-obj-reloc-width ( kind -- width )
  dup cc-obj-r64 = if, drop [lit] 8 exit, then,
  dup cc-obj-pc32 = over cc-obj-plt32 = or
  over cc-obj-r32 = or swap cc-obj-r32s = or
  0= if, [lit] 247 cc-die then, [lit] 4 ;
```

The forward-call fixup list and global-address fixups become persistent records (Chapter 32). `cc-obj-reloc-width` rejects unsupported kinds before insertion.
The whole relocation field must exist before the writer accepts a repair instruction (`forth-bootstrap/cc/081-cc-object.fth:309`):

```forth file=cc/081-cc-object.fth
: cc-obj-reloc ( section offset kind id addend -- )
  cc-obj-require-init
  cc-obj-r-add ! cc-obj-r-sym ! cc-obj-r-kind ! cc-obj-r-off ! cc-obj-r-sec !
  cc-obj-r-sec @ cc-obj-text = cc-obj-r-sec @ cc-obj-data = or
  0= if, [lit] 247 cc-die then,
  cc-obj-r-sym @ cc-obj-check-id
  cc-obj-r-off @ cc-obj-r-sec @ cc-obj-length [lit] 247 cc-obj-bound
  cc-obj-r-kind @ cc-obj-reloc-width
  cc-obj-r-sec @ cc-obj-length cc-obj-r-off @ - [lit] 247 cc-obj-bound
  cc-obj-nrel @ 1+ cc-obj-reloc-cap [lit] 245 cc-obj-bound
  cc-obj-nrel @ cc-obj-rel >r
  cc-obj-r-sec @ r@ ! cc-obj-r-off @ r@ [lit] 8 + !
  cc-obj-r-kind @ r@ [lit] 16 + ! cc-obj-r-sym @ r@ [lit] 24 + !
  cc-obj-r-add @ r> [lit] 32 + ! [lit] 1 cc-obj-nrel +! ;

```

`cc-obj-reloc` allows targets in `.text` or `.data`, checks the symbol handle, and bounds the entire field. The record retains the handle rather than a premature ELF index.

For a relative call, the displacement field begins four bytes before the next instruction. The call relocation uses addend -4 to account for that distance. The linker will combine the symbol address, explicit addend, and relocation place; the field's old bytes are not an implicit addend. A full-width address initializer can instead request `cc-obj-r64` in `.data`, leaving the pointee unresolved while preserving the initializer's storage layout.

## Describe the ELF sections

Section names have their own string table, and metadata initialization stores offsets into it (`forth-bootstrap/cc/081-cc-object.fth:324`):

```forth file=cc/081-cc-object.fth
create cc-obj-shnames
[lit] 0 c, s, .text [lit] 0 c, s, .rodata [lit] 0 c,
s, .data [lit] 0 c, s, .bss [lit] 0 c,
s, .rela.text [lit] 0 c, s, .rela.data [lit] 0 c,
s, .symtab [lit] 0 c, s, .strtab [lit] 0 c, s, .shstrtab [lit] 0 c,
here cc-obj-shnames - constant cc-obj-shnames-size

\ Metadata initializer (name type flags alignment index --).
: cc-obj-sh-init
  cc-obj-sh >r r@ [lit] 56 + ! r@ [lit] 16 + !
  r@ [lit] 8 + ! r> ! ;
```

`cc-obj-sh-init` fills a metadata row's name, type, flags, and alignment; the row is not yet an on-disk section header.
Starting an object clears previous lengths and counts before installing the fixed section layout (`forth-bootstrap/cc/081-cc-object.fth:335`):

```forth file=cc/081-cc-object.fth
: cc-obj-init ( -- )
  cc-obj-reset-write
  cc-obj-sections [lit] 720 cc-obj-zero
  [lit] 0 cc-obj-nsym ! [lit] 0 cc-obj-nrel ! [lit] 1 cc-obj-nstr !
  [lit] 0 cc-obj-strings c! cc-obj-text cc-obj-current !
  [lit] 1 [lit] 1 [lit] 6 [lit] 1 [lit] 1 cc-obj-sh-init
  [lit] 7 [lit] 1 [lit] 2 [lit] 1 [lit] 2 cc-obj-sh-init
  [lit] 15 [lit] 1 [lit] 3 [lit] 1 [lit] 3 cc-obj-sh-init
  [lit] 21 [lit] 8 [lit] 3 [lit] 1 [lit] 4 cc-obj-sh-init
  [lit] 26 [lit] 4 [lit] 0 [lit] 8 [lit] 5 cc-obj-sh-init
  [lit] 37 [lit] 4 [lit] 0 [lit] 8 [lit] 6 cc-obj-sh-init
  [lit] 48 [lit] 2 [lit] 0 [lit] 8 [lit] 7 cc-obj-sh-init
  [lit] 56 [lit] 3 [lit] 0 [lit] 1 [lit] 8 cc-obj-sh-init
  [lit] 64 [lit] 3 [lit] 0 [lit] 1 [lit] 9 cc-obj-sh-init
```

`cc-obj-init` leaves `.text` selected and reserves the empty symbol name. Text is executable and allocated; rodata is allocated; data and bss are writable and allocated. `.bss` uses `SHT_NOBITS`, so its size describes memory without a file payload.
The remaining metadata connects tables to the sections they describe (`forth-bootstrap/cc/081-cc-object.fth:349`):

```forth file=cc/081-cc-object.fth
  [lit] 7 [lit] 5 cc-obj-sh [lit] 40 + !
  [lit] 7 [lit] 6 cc-obj-sh [lit] 40 + !
  [lit] 8 [lit] 7 cc-obj-sh [lit] 40 + !
  [lit] 1 [lit] 5 cc-obj-sh [lit] 48 + !
  [lit] 3 [lit] 6 cc-obj-sh [lit] 48 + !
  [lit] 24 [lit] 5 cc-obj-sh [lit] 64 + !
  [lit] 24 [lit] 6 cc-obj-sh [lit] 64 + !
  [lit] 24 [lit] 7 cc-obj-sh [lit] 64 + !
  true cc-obj-initialized ! ;

```

Each relocation section's link selects `.symtab`, while its info field selects `.text` or `.data`. The symbol table links to `.strtab`; its first-nonlocal index is filled during serialization. The entry sizes describe ELF records, not the larger internal rows.

## Serialize with local symbols first

The checkpoint deliberately inserts its local symbol last. Its internal
handles follow insertion order, but ELF must put locals before globals:

| Name | Writer handle | Serialized ELF index |
|---|---:|---:|
| `caller` | 1 | 2 |
| `external` | 2 | 3 |
| `value` (local) | 3 | 1 |

This manual mapping explains the extra index cell in every symbol row.
The pending call still refers to handle 2 throughout construction. Only
serialization translates it to ELF index 3. Copying the handle directly
into the relocation would make that call name `caller` instead. Symbols
therefore serialize before relocations, even though the relocation was
created before `value` existed. The shared output buffer holds the final
on-disk representation; the writer's records retain their stable identities.

File offsets are captured only after output alignment, so metadata describes the actual serialized position (`forth-bootstrap/cc/081-cc-object.fth:359`):

```forth file=cc/081-cc-object.fth
: cc-obj-out-zero ( count -- )
  begin, dup while, [lit] 0 cc-emit-byte 1- repeat, drop ;
: cc-obj-out-bytes ( address count -- )
  begin, dup while, over c@ cc-emit-byte swap 1+ swap 1- repeat, 2drop ;
: cc-obj-out-align ( alignment -- )
  dup cc-out-pos @ + 1- over / * cc-out-pos @ - cc-obj-out-zero ;
: cc-obj-start-section ( index -- )
  cc-obj-sh >r r@ [lit] 56 + @ cc-obj-out-align
  cc-out-pos @ r> [lit] 24 + ! ;
: cc-obj-end-section ( index -- )
  cc-obj-sh >r cc-out-pos @ r@ [lit] 24 + @ - r> [lit] 32 + ! ;
```
ELF requires local symbols before nonlocal symbols, even when callers inserted them in another order (`forth-bootstrap/cc/081-cc-object.fth:370`):

```forth file=cc/081-cc-object.fth
: cc-obj-emit-symbol ( row -- )
  >r r@ @ cc-emit-4le
  r@ [lit] 8 + @ [lit] 16 * r@ [lit] 16 + @ or cc-emit-byte
  r@ [lit] 24 + @ cc-emit-byte
  r@ [lit] 32 + @ dup cc-emit-byte [lit] 256 / cc-emit-byte
  r@ [lit] 40 + @ cc-emit-8le r> [lit] 48 + @ cc-emit-8le ;

variable cc-obj-i
variable cc-obj-next-index
variable cc-obj-pass
: cc-obj-symbol-pass ( local? -- )
  cc-obj-pass ! [lit] 1 cc-obj-i !
  begin, cc-obj-i @ cc-obj-nsym @ <= while,
    cc-obj-i @ cc-obj-sym >r
    r@ [lit] 8 + @ 0= cc-obj-pass @ = if,
      cc-obj-next-index @ r@ [lit] 56 + ! [lit] 1 cc-obj-next-index +!
      r@ cc-obj-emit-symbol
    then,
    r> drop [lit] 1 cc-obj-i +!
  repeat, ;
```

`cc-obj-emit-symbol` packs binding and type into the shared info byte and writes the other fields at their ELF widths. `cc-obj-symbol-pass` selects rows by binding and records each emitted row’s ELF index. A local inserted after a global therefore moves ahead in the file without changing either handle.
An unresolved local name cannot be delegated to another object (`forth-bootstrap/cc/081-cc-object.fth:390`):

```forth file=cc/081-cc-object.fth
: cc-obj-check-symbols ( -- )
  [lit] 1 cc-obj-i !
  begin, cc-obj-i @ cc-obj-nsym @ <= while,
    cc-obj-i @ cc-obj-sym >r
    r@ [lit] 8 + @ 0= r@ [lit] 32 + @ 0= and if,
      [lit] 246 cc-die
    then,
    r> drop [lit] 1 cc-obj-i +!
  repeat, ;
```

`cc-obj-check-symbols` rejects that case before building. Undefined global and weak symbols remain representable in the output.
Relocations are serialized only after every symbol row has its final ELF index (`forth-bootstrap/cc/081-cc-object.fth:399`):

```forth file=cc/081-cc-object.fth
: cc-obj-emit-relocs ( target-section -- )
  cc-obj-r-sec ! [lit] 0 cc-obj-i !
  begin, cc-obj-i @ cc-obj-nrel @ < while,
    cc-obj-i @ cc-obj-rel >r
    r@ @ cc-obj-r-sec @ = if,
      r@ [lit] 8 + @ cc-emit-8le
      r@ [lit] 16 + @ cc-emit-4le
      r@ [lit] 24 + @ cc-obj-sym [lit] 56 + @ cc-emit-4le
      r@ [lit] 32 + @ cc-emit-8le
    then,
    r> drop [lit] 1 cc-obj-i +!
  repeat, ;
```

`cc-obj-emit-relocs` filters records by their target section. It emits the field offset, then the relocation kind and remapped symbol index that together form ELF's info field, then the signed addend. A late local symbol cannot silently redirect an earlier relocation.

## Assemble the file

Section headers translate the internal metadata into ELF fields and leave virtual addresses unset (`forth-bootstrap/cc/081-cc-object.fth:411`):

```forth file=cc/081-cc-object.fth
: cc-obj-emit-sh ( index -- )
  cc-obj-sh >r r@ @ cc-emit-4le r@ [lit] 8 + @ cc-emit-4le
  r@ [lit] 16 + @ cc-emit-8le [lit] 0 cc-emit-8le
  r@ [lit] 24 + @ cc-emit-8le r@ [lit] 32 + @ cc-emit-8le
  r@ [lit] 40 + @ cc-emit-4le r@ [lit] 48 + @ cc-emit-4le
  r@ [lit] 56 + @ cc-emit-8le r> [lit] 64 + @ cc-emit-8le ;
```

`cc-obj-emit-sh` inserts a zero address because placement belongs to the linker.
The ELF header identifies a relocatable AMD64 object and reserves space for the later section-table offset (`forth-bootstrap/cc/081-cc-object.fth:417`):

```forth file=cc/081-cc-object.fth
: cc-obj-build ( -- )
  cc-obj-require-init cc-obj-check-symbols cc-out-init [lit] 64 cc-obj-out-zero
  [lit] 1179403647 [lit] 0 cc-out-patch-4le
  [lit] 2 [lit] 4 cc-out-patch-byte
  [lit] 1 [lit] 5 cc-out-patch-byte [lit] 1 [lit] 6 cc-out-patch-byte
  [lit] 1 [lit] 16 cc-out-patch-byte [lit] 62 [lit] 18 cc-out-patch-byte
  [lit] 1 [lit] 20 cc-out-patch-byte [lit] 64 [lit] 52 cc-out-patch-byte
  [lit] 64 [lit] 58 cc-out-patch-byte [lit] 10 [lit] 60 cc-out-patch-byte
  [lit] 9 [lit] 62 cc-out-patch-byte
```

`cc-obj-build` clears the output buffer after checking symbols. Its header has no entry point or program headers. The section-table offset remains zero until the payloads have been serialized.
Payload order can differ from section-table order, which lets symbol numbering finish before relocation emission (`forth-bootstrap/cc/081-cc-object.fth:426`):

```forth file=cc/081-cc-object.fth
  [lit] 1 cc-obj-i !
  begin, cc-obj-i @ [lit] 4 < while,
    cc-obj-i @ cc-obj-start-section
    cc-obj-i @ cc-obj-base cc-obj-i @ cc-obj-length cc-obj-out-bytes
    [lit] 1 cc-obj-i +!
  repeat,
  [lit] 4 cc-obj-start-section
  \ Emit symbols first in the file so every relocation can use its ELF index.
  \ Section-table order is independent of the order of section file bytes.
  [lit] 7 cc-obj-start-section [lit] 24 cc-obj-out-zero
  [lit] 1 cc-obj-next-index ! true cc-obj-symbol-pass
  cc-obj-next-index @ dup cc-obj-local-end ! [lit] 7 cc-obj-sh [lit] 48 + !
  [lit] 0 cc-obj-symbol-pass [lit] 7 cc-obj-end-section
```

The backed sections are copied first. `.bss` receives an aligned offset without copied bytes. The symbol table starts with a null record, then the local pass; the resulting next index becomes both `cc-obj-local-end` and the table's first-nonlocal field. The nonlocal pass follows.
With the symbol map complete, the builder can emit relocations, names, and finally the section headers (`forth-bootstrap/cc/081-cc-object.fth:439`):

```forth file=cc/081-cc-object.fth
  [lit] 5 cc-obj-start-section cc-obj-text cc-obj-emit-relocs [lit] 5 cc-obj-end-section
  [lit] 6 cc-obj-start-section cc-obj-data cc-obj-emit-relocs [lit] 6 cc-obj-end-section
  [lit] 8 cc-obj-start-section cc-obj-strings cc-obj-nstr @ cc-obj-out-bytes
  [lit] 8 cc-obj-end-section
  [lit] 9 cc-obj-start-section cc-obj-shnames cc-obj-shnames-size cc-obj-out-bytes
  [lit] 9 cc-obj-end-section
  [lit] 8 cc-obj-out-align cc-out-pos @ dup cc-obj-shoff ! [lit] 40 cc-out-patch-8le
  [lit] 0 cc-obj-i !
  begin, cc-obj-i @ [lit] 10 < while,
    cc-obj-i @ cc-obj-emit-sh [lit] 1 cc-obj-i +!
  repeat, ;

```

The final output position supplies `cc-obj-shoff`, which is patched into the ELF header. Rebuilding the same object repeats the ordering and recomputes output positions. The generic output emitter still enforces its independent capacity limit.

## Publish a complete object

Publication must reject unsuitable destinations before creating a temporary (`forth-bootstrap/cc/081-cc-object.fth:451`):

```forth file=cc/081-cc-object.fth
\ Validate/build before creating a sibling temporary. Never truncate the old
\ output; only publish after every byte and close succeed. Refuse special files.
: cc-obj-check-output ( -- )
  cc-obj-path @ cc-obj-stat-buffer [lit] 0 [lit] 0 [lit] 0 [lit] 0 [lit] 4 syscall6
  dup [lit] 0 [lit] 2 - = if, drop exit, then,
  0= 0= if, [lit] 248 cc-die then,
  cc-obj-stat-buffer [lit] 24 + @ [lit] 61440 and [lit] 32768 <>
  if, [lit] 248 cc-die then, ;
```

`cc-obj-check-output` allows an absent destination or a path whose stat result describes a regular file. It rejects other results. A symlink to a regular file passes this check, but the later rename replaces the symlink itself.
A sibling pathname keeps the temporary on the destination's filesystem (`forth-bootstrap/cc/081-cc-object.fth:459`):

```forth file=cc/081-cc-object.fth
: cc-obj-make-temp-path ( -- )
  begin, cc-obj-path @ cc-obj-temp-length @ + c@ dup while,
    cc-obj-temp-length @ [lit] 4074 >= if, [lit] 248 cc-die then,
    cc-obj-temp-path cc-obj-temp-length @ + c!
    [lit] 1 cc-obj-temp-length +!
  repeat, drop
  cc-obj-temp-length @ 0= if, [lit] 248 cc-die then,
  begin, cc-obj-ti @ [lit] 5 < while,
    cc-obj-temp-suffix cc-obj-ti @ + c@
    cc-obj-temp-path cc-obj-temp-length @ + cc-obj-ti @ + c!
    [lit] 1 cc-obj-ti +!
  repeat,
  [lit] 5 cc-obj-temp-length +!
```

`cc-obj-make-temp-path` checks space while copying the destination, rejects an empty name, and appends `.obj-`. The buffer bound does not override filesystem pathname or component limits.
Hexadecimal process-ID digits distinguish the temporary name without requiring a formatting library (`forth-bootstrap/cc/081-cc-object.fth:472`):

```forth file=cc/081-cc-object.fth
  [lit] 0 [lit] 0 [lit] 0 [lit] 0 [lit] 0 [lit] 0 [lit] 39 syscall6 cc-obj-pid !
  [lit] 16 cc-obj-ti !
  begin, cc-obj-ti @ while,
    [lit] 1 cc-obj-ti -!
    cc-obj-hex-digits cc-obj-pid @ [lit] 15 and + c@
    cc-obj-temp-path cc-obj-temp-length @ + cc-obj-ti @ + c!
    cc-obj-pid @ [lit] 16 / cc-obj-pid !
  repeat,
  [lit] 0 cc-obj-temp-path cc-obj-temp-length @ + [lit] 16 + c! ;
```

Exclusive creation decides ownership of the NUL-terminated temporary pathname; the naming scheme alone cannot establish it.

## Write, close, then rename

Failure cleanup must never unlink a temporary that this invocation did not create (`forth-bootstrap/cc/081-cc-object.fth:481`):

```forth file=cc/081-cc-object.fth
: cc-obj-abandon-output ( -- )
  cc-obj-fd @ 0< 0= if, cc-obj-fd @ close drop true cc-obj-fd ! then,
  cc-obj-temp-owned @ if,
    cc-obj-temp-path [lit] 0 [lit] 0 [lit] 0 [lit] 0 [lit] 0 [lit] 87 syscall6 drop
    [lit] 0 cc-obj-temp-owned !
  then,
  [lit] 248 cc-die ;
```

`cc-obj-abandon-output` closes the descriptor, attempts to remove an owned temporary, and terminates through the file-I/O diagnostic.
The write loop advances by the actual byte count and retries interrupted writes (`forth-bootstrap/cc/081-cc-object.fth:488`):

```forth file=cc/081-cc-object.fth
: cc-obj-write ( nul-terminated-path -- )
  cc-obj-require-init cc-obj-reset-write cc-obj-path ! cc-obj-build
  cc-obj-make-temp-path cc-obj-check-output
  \ O_WRONLY | O_CREAT | O_EXCL; an existing temporary is never ours to unlink.
  cc-obj-temp-path [lit] 193 [lit] 420 open
  dup 0< if, [lit] 248 cc-die then, cc-obj-fd !
  true cc-obj-temp-owned !
  begin, cc-obj-written @ cc-out-pos @ < while,
    cc-obj-fd @ cc-out-buf cc-obj-written @ + cc-out-pos @ cc-obj-written @ - write
    dup [lit] 0 [lit] 4 - = if, drop
    else,
      dup [lit] 0 <= if, cc-obj-abandon-output then,
      cc-obj-written +!
    then,
  repeat,
```

`cc-obj-write` validates and builds before opening anything. Exclusive creation avoids truncating a pre-existing temporary; the ownership flag is set only after open succeeds. A short positive write advances `cc-obj-written`; a nonpositive result other than interruption abandons the publication.
The destination changes only after all bytes and the close have succeeded (`forth-bootstrap/cc/081-cc-object.fth:503`):

```forth file=cc/081-cc-object.fth
  \ Linux may release the descriptor even when close reports an error.
  cc-obj-fd @ close true cc-obj-fd ! 0= 0= if, cc-obj-abandon-output then,
  cc-obj-temp-path cc-obj-path @ [lit] 0 [lit] 0 [lit] 0 [lit] 0 [lit] 82 syscall6
  0= 0= if, cc-obj-abandon-output then,
  cc-obj-reset-write ;
```

The descriptor is marked invalid before a close error is handled, because Linux may already have released it. Rename publishes the finished file, and a successful write clears publication state for reuse. This protects an existing output from diagnosed write or close failure; it does not promise crash durability. There is no `fsync`, and abrupt termination can leave a temporary.

The API uses shared scratch cells throughout, so calls are sequential, not reentrant. Section/range/alignment failures use error 244, capacity failures 245, symbol failures 246, relocation failures 247, and publication failures 248. The shared output emitter retains error 21. These failures terminate through `cc-die`.

## Preview: the C producer in Chapter 41

`cc-sysv-object-enable` selects C object mode in `forth-bootstrap/cc/123-cc-object-program.fth:462`, and `cc-sysv-object-program` transfers compiled text, exports symbols, and records fixups immediately below it. Chapter 41 teaches that adapter. This optional preview uses the adapter as a supplied C producer.

From the `forth-bootstrap` checkout root, compile the following C source in a fresh temporary directory. The load-order helper puts the executing main last (`forth-bootstrap/cc/compiler-layers.sh:6`); the loop excludes it and supplies an object-writing entry instead. Output goes to `example.o` there, avoiding the fixed-path main and shared `/tmp/cc-out`.

The fixed, short `/tmp/book-probe.XXXXXXXXXX` template keeps generated paths within the one-token, 255-byte limit of Forth's `s,`; shell quoting alone would not make a whitespace-containing `TMPDIR` safe. Creation is checked before any cleanup trap is installed.

```sh
(
set -o pipefail
work=$(mktemp -d /tmp/book-probe.XXXXXXXXXX) || exit "$?"
trap 'status=$?; rm -rf -- "$work" || status=1; exit "$status"' EXIT
cat > "$work/example.c" <<'C' || exit "$?"
extern int external(void);
int caller(void) { return external(); }
int value(void) { return 7; }
C
bash cc/compiler-layers.sh > "$work/layers" || exit "$?"
{
  cat forth/010-lib.fth || exit "$?"
  while IFS= read -r layer; do
    case "$layer" in */120-cc-main.fth) continue ;; esac
    cat "$layer" || exit "$?"
  done < "$work/layers"
  printf 'create output-path s, %s/example.o [lit] 0 c,\n' "$work"
  cat <<'FORTH' || exit "$?"
cc-sysv-object-enable
: object-main
  cc-load-stdin cc-preprocess cc-out-init cc-globals-init
  cc-sysv-object-program output-path cc-obj-write bye ;
object-main
FORTH
  cat "$work/example.c" || exit "$?"
} | ./seed-forth || exit "$?"
readelf -h -S -s -r -W "$work/example.o" > "$work/inspection" || exit "$?"
sed -n '/Type:/p; /Machine:/p; /Entry point/p; /Number of program headers/p; /\[ *[1457]\]/p; /^Relocation section/,$p' "$work/inspection" || exit "$?"
)
```

Observed output, trimmed by the same filter used in the checkpoint:

```text
  Type:                              REL (Relocatable file)
  Machine:                           Advanced Micro Devices X86-64
  Entry point address:               0x0
  Number of program headers:         0
  [ 1] .text             PROGBITS        0000000000000000 000040 00007e 00  AX  0   0  1
  [ 4] .bss              NOBITS          0000000000000000 0000be 000000 00  WA  0   0  1
  [ 5] .rela.text        RELA            0000000000000000 000120 000018 18      7   1  8
  [ 7] .symtab           SYMTAB          0000000000000000 0000c0 000060 18      8   1  8
Relocation section '.rela.text' at offset 0x120 contains 1 entry:
    Offset             Info             Type               Symbol's Value  Symbol's Name + Addend
0000000000000024  0000000100000004 R_X86_64_PLT32         0000000000000000 external - 4

Symbol table '.symtab' contains 4 entries:
   Num:    Value          Size Type    Bind   Vis      Ndx Name
     0: 0000000000000000     0 NOTYPE  LOCAL  DEFAULT  UND 
     1: 0000000000000000     0 FUNC    GLOBAL DEFAULT  UND external
     2: 0000000000000000    77 FUNC    GLOBAL DEFAULT    1 caller
     3: 000000000000004d    49 FUNC    GLOBAL DEFAULT    1 value
```

The C producer exports both definitions as global functions. `external` has no definition in this translation unit, so its call remains a relocation. No executable is linked or run here.

## Try it

Run from the `forth-bootstrap` checkout root with the seed already built. This checkpoint loads the complete library, arena, I/O layer, and object writer. It writes a caller with an unresolved call and a local function named `value`, inserting the local symbol last to exercise ELF index remapping. These are object-format test bytes; this checkpoint inspects them without linking or executing them.

The output path is inside a fresh temporary directory, so the writer does not touch the compiler's usual `/tmp/cc-out`. `readelf` inspects the header, sections, symbols, and relocations. The final filter trims the report to selected header fields and sections, followed by all relocations and symbols.

```sh
(
set -o pipefail
work=$(mktemp -d /tmp/book-probe.XXXXXXXXXX) || exit "$?"
trap 'status=$?; rm -rf -- "$work" || status=1; exit "$status"' EXIT
{
  cat forth/010-lib.fth cc/020-cc-arena.fth cc/030-cc-io.fth cc/081-cc-object.fth || exit "$?"
  printf 'create output-path s, %s/writer.o [lit] 0 c,\n' "$work"
  cat <<'FORTH' || exit "$?"
cc-obj-init
cc-obj-text cc-obj-use
[lit] 232 cc-obj-byte [lit] 0 cc-obj-4le [lit] 195 cc-obj-byte
[lit] 184 cc-obj-byte [lit] 7 cc-obj-4le [lit] 195 cc-obj-byte
create caller-name s, caller
create external-name s, external
create value-name s, value
caller-name [lit] 6 cc-obj-global cc-obj-func cc-obj-default cc-obj-text [lit] 0 [lit] 6 cc-obj-symbol drop
external-name [lit] 8 cc-obj-global cc-obj-func cc-obj-default cc-obj-undef [lit] 0 [lit] 0 cc-obj-symbol
>r cc-obj-text [lit] 1 cc-obj-plt32 r> [lit] 0 [lit] 4 - cc-obj-reloc
value-name [lit] 5 cc-obj-local cc-obj-func cc-obj-default cc-obj-text [lit] 6 [lit] 6 cc-obj-symbol drop
output-path cc-obj-write
bye
FORTH
} | ./seed-forth || exit "$?"
readelf -h -S -s -r -W "$work/writer.o" > "$work/inspection" || exit "$?"
sed -n '/Type:/p; /Machine:/p; /Entry point/p; /Number of program headers/p; /\[ *[1457]\]/p; /^Relocation section/,$p' "$work/inspection" || exit "$?"
)
```

Observed output:

```text
  Type:                              REL (Relocatable file)
  Machine:                           Advanced Micro Devices X86-64
  Entry point address:               0x0
  Number of program headers:         0
  [ 1] .text             PROGBITS        0000000000000000 000040 00000c 00  AX  0   0  1
  [ 4] .bss              NOBITS          0000000000000000 00004c 000000 00  WA  0   0  1
  [ 5] .rela.text        RELA            0000000000000000 0000b0 000018 18      7   1  8
  [ 7] .symtab           SYMTAB          0000000000000000 000050 000060 18      8   2  8
Relocation section '.rela.text' at offset 0xb0 contains 1 entry:
    Offset             Info             Type               Symbol's Value  Symbol's Name + Addend
0000000000000001  0000000300000004 R_X86_64_PLT32         0000000000000000 external - 4

Symbol table '.symtab' contains 4 entries:
   Num:    Value          Size Type    Bind   Vis      Ndx Name
     0: 0000000000000000     0 NOTYPE  LOCAL  DEFAULT  UND 
     1: 0000000000000006     6 FUNC    LOCAL  DEFAULT    1 value
     2: 0000000000000000     6 FUNC    GLOBAL DEFAULT    1 caller
     3: 0000000000000000     0 FUNC    GLOBAL DEFAULT  UND external
```

`value` precedes `caller` in the symbol table despite being inserted later. The relocation names `external`, which remains undefined. Its field offset lies in `.text`; the relocation section's link and info columns identify the symbol table and target section.

## Exercise

Hints and feedback are in [Appendix H](66-exercise-feedback.md#chapter-40-identity-versus-serialization).

**Trace (easy).** In the writer checkpoint, follow the handle returned for `external` through `cc-obj-reloc`, both symbol passes, and `cc-obj-emit-relocs`. Explain why inserting `value` last does not change the relocation target, even though it changes the target's ELF index.

**Verify (moderate).** Add a reservation in `.bss` before writing the object. Inspect its section size and compare the file sizes before and after. Explain why reserved memory does not become an equally large payload in the file.
