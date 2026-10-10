# Chapter 42 — Linker and archives

A Forth linker turns `caller.o` and `add.o` into an executable without the host linker. It chooses definitions, places their sections, and repairs references; an archive supplies definitions only when demanded. The resulting executable contains only the archive members needed to satisfy its references.

## The public boundary

The shape is `lnk-init` → add inputs → `lnk-entry` → `lnk-link`. Object addition registers names immediately; final linking assigns addresses. The header fixes the accepted object format (Chapter 40) and the resource policy.

The limits bound allocation and alignment; `lnk-base-address` supplies the image’s virtual base (`forth-bootstrap/cc/140-cc-link.fth:1`):

```forth file=cc/140-cc-link.fth
\ 140-cc-link.fth -- bounded static AMD64 ELF linker, written in Forth.
\ Load after 010-lib.fth, 020-cc-arena.fth, and 030-cc-io.fth.
\ The input is 081's ten-section ELF64 ET_REL contract; no host linker.
\ API: lnk-init, lnk-add-object ( NUL-path -- ),
\      lnk-entry ( name length -- ), lnk-link ( NUL-output-path -- ).
\ Errors: 250 metadata, 251 capacity, 252 duplicate strong definition,
\ 253 unresolved symbol/entry, 254 relocation/range, 255 file I/O.

[lit] 1024 constant lnk-object-cap
[lit] 65536 constant lnk-symbol-cap
[lit] 65536 constant lnk-global-cap
[lit] 131072 constant lnk-hash-cap
[lit] 268435456 constant lnk-byte-cap
[lit] 1048576 constant lnk-align-cap
[lit] 128 constant lnk-object-size
\ The image's virtual address: 4 MiB unless a driver stores another
\ 2 MiB-aligned address here before lnk-link (K1 links at 2 MiB).
variable lnk-base-address
[lit] 4194304 lnk-base-address !
: lnk-base ( -- address ) lnk-base-address @ ;
```

`lnk-objects` owns input records; the remaining state separates counts, entry, output extents, and current object/section/symbol cursors. `lnk-np` and `lnk-nl` are unused (`forth-bootstrap/cc/140-cc-link.fth:21`):

```forth file=cc/140-cc-link.fth
create lnk-objects  lnk-object-cap lnk-object-size * allot
variable lnk-count
variable lnk-globals
variable lnk-global-count
variable lnk-entry-name
variable lnk-entry-len
variable lnk-image
variable lnk-file-size
variable lnk-memory-size
variable lnk-rx-size
variable lnk-rw-start
variable lnk-entry-value
variable lnk-op
variable lnk-si
variable lnk-oi
variable lnk-sp
variable lnk-np
variable lnk-nl

```

The object record keeps file views beside eventual placements:

| Byte offsets | Fields |
|---|---|
| 0, 8 | owned bytes, length |
| 16, 24, 32 | sections, symbols, symbol count |
| 40, 48, 56 | strings, string size, first nonlocal index |
| 64, 72, 80, 88 | text, rodata, data, BSS placements |
| 104, 112, 120 | device, inode, borrowed path |

Input identities survive independently of selected members, so even an unused archive remains protected from output replacement (`forth-bootstrap/cc/140-cc-link.fth:40`):

```forth file=cc/140-cc-link.fth
\ Track source identities independently of selected archive members.
[lit] 1024 constant lnk-input-cap
create lnk-inputs lnk-input-cap [lit] 16 * allot
variable lnk-input-count
: lnk-note-input ( device inode -- )
  lnk-input-count @ 1+ lnk-input-cap [lit] 251 cc-check-cap
  lnk-input-count @ [lit] 16 * lnk-inputs + >r
  r@ [lit] 8 + ! r> ! [lit] 1 lnk-input-count +! ;

```

## Validate before dereferencing

These small helpers give wire fields and object records a common vocabulary:

| Input | Result or operation |
|---|---|
| failed predicate / excessive size | `lnk-need`, `lnk-bad`, `lnk-cap`, `lnk-nonnegative` reject it |
| wire address / value and address | `lnk-u16`, `lnk-u32` read; `lnk-w16`, `lnk-w32` write |
| allocation size | `lnk-map` returns owned, zeroed storage |
| record index or offset | `lnk-object`, `lnk-field`, `lnk-section`, `lnk-place`, `lnk-symbol` locate it |
| symbol address | `lnk-binding`, `lnk-shndx` extract classification |

(`forth-bootstrap/cc/140-cc-link.fth:49`):

```forth file=cc/140-cc-link.fth
: lnk-bad  [lit] 250 cc-die ;
: lnk-need  0= if, lnk-bad then, ;
: lnk-cap  lnk-byte-cap [lit] 251 cc-check-cap ;
: lnk-nonnegative  dup 0< if, lnk-bad then, ;
: lnk-u16  dup c@ swap 1+ c@ [lit] 256 * + ;
: lnk-u32
  dup lnk-u16 swap [lit] 2 + lnk-u16 [lit] 65536 * + ;
: lnk-w16  >r dup r@ c! [lit] 256 / r> 1+ c! ;
: lnk-w32
  >r dup r@ lnk-w16 [lit] 65536 / r> [lit] 2 + lnk-w16 ;
```

(`forth-bootstrap/cc/140-cc-link.fth:59`):

```forth file=cc/140-cc-link.fth
: lnk-map
  dup 0= if, drop [lit] 1 then,
  [lit] 0 swap [lit] 3 [lit] 34 true [lit] 0 [lit] 9 syscall6
  dup 0< if, [lit] 251 cc-die then, ;
: lnk-object  lnk-object-size * lnk-objects + ;
: lnk-field  lnk-op @ + ;
: lnk-section  [lit] 64 * [lit] 16 lnk-field @ + ;
: lnk-place  [lit] 8 * [lit] 56 + lnk-field ;
: lnk-symbol  [lit] 24 * [lit] 24 lnk-field @ + ;
: lnk-binding  [lit] 4 + c@ [lit] 16 / ;
: lnk-shndx  [lit] 6 + lnk-u16 ;

```

`lnk-span` proves offset ≤ size and length ≤ remaining bytes before adding pointers. `lnk-alignment` accepts bounded powers of two; `lnk-align` rounds placement; `lnk-copy` transfers bytes (`forth-bootstrap/cc/140-cc-link.fth:71`):

```forth file=cc/140-cc-link.fth
\ All offsets are checked by subtraction, before pointer arithmetic.
: lnk-span ( offset size -- address )
  lnk-nonnegative >r lnk-nonnegative
  dup [lit] 8 lnk-field @ <= lnk-need
  [lit] 8 lnk-field @ over - r> >= lnk-need
  lnk-op @ @ + ;
: lnk-alignment ( alignment -- alignment )
  dup [lit] 0 > lnk-need
  dup lnk-align-cap <= lnk-need
  dup dup 1- and 0= lnk-need ;
: lnk-align ( offset alignment -- aligned )
  1- dup >r + r> dup nand and ;
: lnk-copy ( source destination size -- )
  begin, dup while,
    >r over c@ over c! 1+ swap 1+ swap r> 1-
  repeat, drop 2drop ;

```

## Keep input storage alive

`lnk-read-file` sizes and maps the input, completes short reads, retries interruption, and records device/inode identity. `lnk-fd`, `lnk-size`, `lnk-done`, and `lnk-stat-buffer` retain progress; `lnk-path` also serves output publication.

(`forth-bootstrap/cc/140-cc-link.fth:88`):

```forth file=cc/140-cc-link.fth
variable lnk-fd
variable lnk-size
variable lnk-done
variable lnk-path
create lnk-stat-buffer  [lit] 144 allot
: lnk-fstat ( fd -- )
  lnk-stat-buffer [lit] 0 [lit] 0 [lit] 0 [lit] 0 [lit] 5 syscall6
  0= 0= if, [lit] 255 cc-die then, ;
: lnk-read-file ( path -- address size )
  dup [lit] 120 lnk-field !
  [lit] 0 [lit] 0 open dup 0< if, [lit] 255 cc-die then,
  lnk-fd !
  lnk-fd @ [lit] 0 [lit] 2 [lit] 0 [lit] 0 [lit] 0 [lit] 8 syscall6
  dup 0< if, [lit] 255 cc-die then,
  dup lnk-cap lnk-size !
  lnk-fd @ [lit] 0 [lit] 0 [lit] 0 [lit] 0 [lit] 0 [lit] 8 syscall6
  0= 0= if, [lit] 255 cc-die then,
  lnk-size @ lnk-map lnk-op @ !
```

Read completion and the object-header minimum (`forth-bootstrap/cc/140-cc-link.fth:106`):

```forth file=cc/140-cc-link.fth
  [lit] 0 lnk-done !
  begin, lnk-done @ lnk-size @ < while,
    lnk-fd @ lnk-op @ @ lnk-done @ + lnk-size @ lnk-done @ - read
    dup [lit] 0 [lit] 4 - = if, drop
    else,
      dup [lit] 0 > 0= if, [lit] 255 cc-die then,
      lnk-done +!
    then,
  repeat,
  lnk-fd @ lnk-fstat
  lnk-stat-buffer @ [lit] 104 lnk-field !
  lnk-stat-buffer [lit] 8 + @ [lit] 112 lnk-field !
  lnk-stat-buffer @ lnk-stat-buffer [lit] 8 + @ lnk-note-input
  lnk-fd @ close 0= 0= if, [lit] 255 cc-die then,
  lnk-op @ @ lnk-size @ ;
: lnk-read-object ( path -- address size )
  lnk-read-file dup [lit] 64 < if, [lit] 250 cc-die then, ;

```

Names must terminate inside their string table: `lnk-string-base`, `lnk-string-size`, and `lnk-string-end` bound the scan used by `lnk-symbol-name`
(`forth-bootstrap/cc/140-cc-link.fth:124`):

```forth file=cc/140-cc-link.fth
\ Find a terminating NUL strictly inside a previously validated string table.
variable lnk-string-end
variable lnk-string-base
variable lnk-string-size
: lnk-string ( index base size -- address length )
  lnk-string-size ! lnk-string-base !
  lnk-nonnegative dup lnk-string-size @ < lnk-need
  lnk-string-base @ + [lit] 0
  lnk-string-base @ lnk-string-size @ + lnk-string-end !
  begin,
    2dup + lnk-string-end @ < lnk-need
    2dup + c@
  while, 1+ repeat, ;

: lnk-symbol-name ( symbol -- address length )
  lnk-u32 [lit] 40 lnk-field @ [lit] 48 lnk-field @ lnk-string ;

```

`lnk-release` unmaps owned inputs, globals, and image. `lnk-init` resets the session; `lnk-entry` borrows the caller’s name, which must remain alive through linking (`forth-bootstrap/cc/140-cc-link.fth:141`):

```forth file=cc/140-cc-link.fth
: lnk-unmap ( address length -- )
  [lit] 0 [lit] 0 [lit] 0 [lit] 0 [lit] 11 syscall6
  0= 0= if, [lit] 251 cc-die then, ;
: lnk-release
  [lit] 0 lnk-oi !
  begin, lnk-oi @ lnk-count @ < while,
    lnk-oi @ lnk-object dup @ swap [lit] 8 + @ lnk-unmap
    [lit] 1 lnk-oi +!
  repeat,
  lnk-globals @ if,
    lnk-globals @ lnk-hash-cap [lit] 32 * lnk-unmap
  then,
  lnk-image @ if, lnk-image @ lnk-file-size @ lnk-unmap then,
  [lit] 0 lnk-count ! [lit] 0 lnk-globals ! [lit] 0 lnk-image ! ;
: lnk-init
  lnk-release
  [lit] 1 cc-src-line !
  [lit] 0 lnk-count ! [lit] 0 lnk-global-count ! [lit] 0 lnk-input-count !
  [lit] 0 lnk-entry-name ! [lit] 0 lnk-entry-len !
  lnk-hash-cap [lit] 32 * lnk-map lnk-globals ! ;
: lnk-entry  lnk-entry-len ! lnk-entry-name ! ;

```

## Accept the object contract

Section types and flags are positional requirements. `lnk-zero?` checks reserved bytes; `lnk-multiple24` rejects partial table entries (`forth-bootstrap/cc/140-cc-link.fth:163`):

```forth file=cc/140-cc-link.fth
\ Ten section roles are fixed by the object-writer boundary.
create lnk-section-types
  [lit] 0 , [lit] 1 , [lit] 1 , [lit] 1 , [lit] 8 ,
  [lit] 4 , [lit] 4 , [lit] 2 , [lit] 3 , [lit] 3 ,
create lnk-section-flags
  [lit] 0 , [lit] 6 , [lit] 2 , [lit] 3 , [lit] 3 ,
  [lit] 0 , [lit] 0 , [lit] 0 , [lit] 0 , [lit] 0 ,
variable lnk-sh
variable lnk-shstr
variable lnk-shstrlen
: lnk-zero? ( address length -- flag )
  begin, dup while,
    over c@ if, 2drop [lit] 0 exit, then,
    1- swap 1+ swap
  repeat, 2drop true ;
: lnk-multiple24 ( size -- count )
  lnk-nonnegative dup [lit] 24 / dup >r [lit] 24 * = lnk-need r> ;
```

`lnk-header` rejects incompatible ELF metadata before exposing the section table (`forth-bootstrap/cc/140-cc-link.fth:180`):

```forth file=cc/140-cc-link.fth
: lnk-header
  lnk-op @ @ lnk-sh !
  lnk-sh @ lnk-u32 [lit] 1179403647 = lnk-need
  lnk-sh @ [lit] 4 + c@ [lit] 2 = lnk-need
  lnk-sh @ [lit] 5 + c@ [lit] 1 = lnk-need
  lnk-sh @ [lit] 6 + c@ [lit] 1 = lnk-need
  lnk-sh @ [lit] 7 + c@ dup 0= swap [lit] 3 = or lnk-need
  lnk-sh @ [lit] 8 + [lit] 8 lnk-zero? lnk-need
  lnk-sh @ [lit] 16 + lnk-u16 [lit] 1 = lnk-need
  lnk-sh @ [lit] 18 + lnk-u16 [lit] 62 = lnk-need
  lnk-sh @ [lit] 20 + lnk-u32 [lit] 1 = lnk-need
  lnk-sh @ [lit] 24 + @ 0= lnk-need
  lnk-sh @ [lit] 32 + @ 0= lnk-need
  lnk-sh @ [lit] 48 + lnk-u32 0= lnk-need
  lnk-sh @ [lit] 52 + lnk-u16 [lit] 64 = lnk-need
  lnk-sh @ [lit] 54 + lnk-u16 0= lnk-need
  lnk-sh @ [lit] 56 + lnk-u16 0= lnk-need
  lnk-sh @ [lit] 58 + lnk-u16 [lit] 64 = lnk-need
  lnk-sh @ [lit] 60 + lnk-u16 [lit] 10 = lnk-need
  lnk-sh @ [lit] 62 + lnk-u16 [lit] 9 = lnk-need
  lnk-sh @ [lit] 40 + @ [lit] 640 lnk-span [lit] 16 lnk-field !
  [lit] 0 lnk-section [lit] 64 lnk-zero? lnk-need ;
```

`lnk-sections` checks payload spans, alignment, table links, and entry sizes, then installs validated symbol/string views. BSS has memory size without a file payload. The final pass bounds every section name and checks the null symbol.

(`forth-bootstrap/cc/140-cc-link.fth:202`):

```forth file=cc/140-cc-link.fth
: lnk-sections
  [lit] 1 lnk-si !
  begin, lnk-si @ [lit] 10 < while,
    lnk-si @ lnk-section lnk-sh !
    lnk-sh @ [lit] 4 + lnk-u32
    lnk-si @ lnk-section-types cell[] @ = lnk-need
    lnk-sh @ [lit] 8 + @
    lnk-si @ lnk-section-flags cell[] @ = lnk-need
    lnk-sh @ [lit] 16 + @ 0= lnk-need
    lnk-sh @ [lit] 32 + @ lnk-nonnegative dup lnk-cap drop
    lnk-si @ [lit] 4 <> if,
      lnk-sh @ [lit] 24 + @ lnk-sh @ [lit] 32 + @ lnk-span drop
    then,
    lnk-sh @ [lit] 48 + @ lnk-alignment drop
    lnk-si @ [lit] 5 < if,
      lnk-sh @ [lit] 40 + lnk-u32 0= lnk-need
      lnk-sh @ [lit] 44 + lnk-u32 0= lnk-need
      lnk-sh @ [lit] 56 + @ 0= lnk-need
    else,
```

Table-specific requirements (`forth-bootstrap/cc/140-cc-link.fth:221`):

```forth file=cc/140-cc-link.fth
      lnk-si @ [lit] 8 < if,
        lnk-sh @ [lit] 48 + @ [lit] 8 = lnk-need
        lnk-sh @ [lit] 56 + @ [lit] 24 = lnk-need
        lnk-sh @ [lit] 32 + @ lnk-multiple24 drop
        lnk-si @ [lit] 7 < if,
          lnk-sh @ [lit] 40 + lnk-u32 [lit] 7 = lnk-need
          lnk-sh @ [lit] 44 + lnk-u32
          lnk-si @ [lit] 5 - [lit] 2 * 1+ = lnk-need
        else,
          lnk-sh @ [lit] 40 + lnk-u32 [lit] 8 = lnk-need
        then,
      else,
        lnk-sh @ [lit] 40 + lnk-u32 0= lnk-need
        lnk-sh @ [lit] 44 + lnk-u32 0= lnk-need
        lnk-sh @ [lit] 56 + @ 0= lnk-need
        lnk-sh @ [lit] 48 + @ [lit] 1 = lnk-need
      then,
    then,
    [lit] 1 lnk-si +!
  repeat,
```

Validated views and names (`forth-bootstrap/cc/140-cc-link.fth:241`):

```forth file=cc/140-cc-link.fth
  [lit] 7 lnk-section lnk-sh !
  lnk-sh @ [lit] 24 + @ lnk-op @ @ + [lit] 24 lnk-field !
  lnk-sh @ [lit] 32 + @ lnk-multiple24
  dup [lit] 0 > lnk-need
  dup lnk-symbol-cap [lit] 251 cc-check-cap [lit] 32 lnk-field !
  lnk-sh @ [lit] 44 + lnk-u32
  dup [lit] 0 > lnk-need
  dup [lit] 32 lnk-field @ <= lnk-need [lit] 56 lnk-field !
  [lit] 8 lnk-section lnk-sh !
  lnk-sh @ [lit] 24 + @ lnk-op @ @ + [lit] 40 lnk-field !
  lnk-sh @ [lit] 32 + @ dup [lit] 0 > lnk-need [lit] 48 lnk-field !
  [lit] 40 lnk-field @ c@ 0= lnk-need
  [lit] 9 lnk-section lnk-sh !
  lnk-sh @ [lit] 24 + @ lnk-op @ @ + lnk-shstr !
  lnk-sh @ [lit] 32 + @ dup [lit] 0 > lnk-need lnk-shstrlen !
  lnk-shstr @ c@ 0= lnk-need
  [lit] 0 lnk-si !
  begin, lnk-si @ [lit] 10 < while,
    lnk-si @ lnk-section lnk-u32 lnk-shstr @ lnk-shstrlen @ lnk-string 2drop
    [lit] 1 lnk-si +!
  repeat,
  [lit] 0 lnk-symbol [lit] 24 lnk-zero? lnk-need ;

```

## Resolve a name once

`lnk-find` hashes `lnk-hname`/`lnk-hlen`, probes from `lnk-hash`, and returns `lnk-hslot`. Each occupied slot retains the selected symbol and its owning object
(`forth-bootstrap/cc/140-cc-link.fth:264`):

```forth file=cc/140-cc-link.fth
\ Global names use open addressing, at most half full. Each slot stores
\ name pointer, name length, the chosen symbol, and its owning object.
variable lnk-hname
variable lnk-hlen
variable lnk-hash
variable lnk-hi
variable lnk-hslot
: lnk-find ( name length -- slot )
  lnk-hlen ! lnk-hname ! [lit] 5381 lnk-hash ! [lit] 0 lnk-hi !
  begin, lnk-hi @ lnk-hlen @ < while,
    lnk-hash @ [lit] 33 * lnk-hname @ lnk-hi @ + c@ +
    [lit] 2147483647 and lnk-hash ! [lit] 1 lnk-hi +!
  repeat,
  begin,
    lnk-hash @ lnk-hash-cap 1- and dup lnk-hash !
    [lit] 32 * lnk-globals @ + lnk-hslot !
    lnk-hslot @ @ 0= if, lnk-hslot @ exit, then,
    lnk-hslot @ [lit] 8 + @ lnk-hlen @ = if,
      lnk-hslot @ @ lnk-hname @ lnk-hlen @ bytes-eq if,
        lnk-hslot @ exit,
      then,
    then,
    [lit] 1 lnk-hash +!
  again, ;
```

`lnk-register` upgrades undefined weak demand to strong, prefers definitions over references and strong definitions over weak. First weak wins; duplicate strong definitions fail. `lnk-choose` updates symbol and owner together (`forth-bootstrap/cc/140-cc-link.fth:288`):

```forth file=cc/140-cc-link.fth
variable lnk-slot
variable lnk-old
: lnk-choose
  lnk-sp @ lnk-slot @ [lit] 16 + !
  lnk-op @ lnk-slot @ [lit] 24 + ! ;
: lnk-register
  lnk-sp @ lnk-symbol-name
  dup [lit] 0 > lnk-need lnk-find lnk-slot !
  lnk-slot @ @ 0= if,
    lnk-global-count @ 1+ lnk-global-cap [lit] 251 cc-check-cap
    [lit] 1 lnk-global-count +!
    lnk-hname @ lnk-slot @ ! lnk-hlen @ lnk-slot @ [lit] 8 + !
    lnk-choose exit,
  then,
  lnk-slot @ [lit] 16 + @ lnk-old !
  lnk-sp @ lnk-shndx 0= if,
    lnk-old @ lnk-shndx 0=
    lnk-old @ lnk-binding [lit] 2 = and
    lnk-sp @ lnk-binding [lit] 1 = and if, lnk-choose then,
    exit,
  then,
  lnk-old @ lnk-shndx 0= if, lnk-choose exit, then,
  lnk-sp @ lnk-binding [lit] 2 = if, exit, then,
  lnk-old @ lnk-binding [lit] 2 = if, lnk-choose exit, then,
  [lit] 252 cc-die ;
```

## Register accepted objects

`lnk-validate-symbol` checks binding order and supported classifications. `lnk-index`, `lnk-value`, and `lnk-length` bound section-relative extents; absolute values bypass placement checks
(`forth-bootstrap/cc/140-cc-link.fth:313`):

```forth file=cc/140-cc-link.fth
variable lnk-symbol-index
variable lnk-index
variable lnk-value
variable lnk-length
: lnk-validate-symbol
  lnk-sp @ lnk-symbol-name 2drop
  lnk-sp @ lnk-binding dup [lit] 2 <= lnk-need
  lnk-symbol-index @ [lit] 56 lnk-field @ < if,
    0= lnk-need
  else,
    [lit] 0 > lnk-need
  then,
  lnk-sp @ [lit] 4 + c@ [lit] 15 and [lit] 4 <= lnk-need
  lnk-sp @ [lit] 5 + c@ [lit] 3 <= lnk-need
  lnk-sp @ lnk-shndx lnk-index !
  lnk-index @ 0= if,
    lnk-sp @ [lit] 8 + @ 0= lnk-need
    lnk-sp @ [lit] 16 + @ 0= lnk-need
    lnk-symbol-index @ 0= 0= if,
      lnk-sp @ lnk-binding [lit] 0 > lnk-need
    then,
  else,
    lnk-index @ [lit] 65521 <> if,
      lnk-index @ [lit] 4 <= lnk-need
      lnk-sp @ [lit] 8 + @ lnk-nonnegative lnk-value !
      lnk-sp @ [lit] 16 + @ lnk-nonnegative lnk-length !
      lnk-index @ lnk-section [lit] 32 + @
      dup lnk-value @ >= lnk-need
      lnk-value @ - lnk-length @ >= lnk-need
    then,
  then,
  ;
```

`lnk-check-symbol` registers only nonlocals. `lnk-accept-object` validates before counting the input; `lnk-add-object` supplies its owned bytes (`forth-bootstrap/cc/140-cc-link.fth:345`):

```forth file=cc/140-cc-link.fth
: lnk-check-symbol
  lnk-validate-symbol lnk-sp @ lnk-binding if, lnk-register then, ;
: lnk-accept-object
  lnk-header lnk-sections
  [lit] 0 lnk-symbol-index !
  begin, lnk-symbol-index @ [lit] 32 lnk-field @ < while,
    lnk-symbol-index @ lnk-symbol lnk-sp ! lnk-check-symbol
    [lit] 1 lnk-symbol-index +!
  repeat,
  [lit] 1 lnk-count +! ;
: lnk-add-object
  lnk-count @ 1+ lnk-object-cap [lit] 251 cc-check-cap
  lnk-count @ lnk-object lnk-op !
  lnk-read-object [lit] 8 lnk-field ! drop lnk-accept-object ;
```

Archive bytes follow the same acceptance path: `lnk-add-buffer` copies `lnk-buffer-a`/`lnk-buffer-n`, keeping names valid after the archive mapping closes
(`forth-bootstrap/cc/140-cc-link.fth:359`):

```forth file=cc/140-cc-link.fth
\ Archive members are copied: ordinary object release owns every mapping.
variable lnk-buffer-a
variable lnk-buffer-n
: lnk-add-buffer ( address size -- )
  lnk-buffer-n ! lnk-buffer-a !
  lnk-buffer-n @ [lit] 64 >= lnk-need
  lnk-count @ 1+ lnk-object-cap [lit] 251 cc-check-cap
  lnk-count @ lnk-object lnk-op !
  lnk-buffer-n @ lnk-map lnk-op @ !
  lnk-buffer-n @ [lit] 8 lnk-field !
  lnk-buffer-a @ lnk-op @ @ lnk-buffer-n @ lnk-copy
  lnk-accept-object ;

```

## Index candidate definitions

An archive index maps names to candidate members. It does not register every definition. First build that index from validated objects; the reader will turn its entries into demand-driven additions.

`arc-members` stores member rows, `arc-index` stores name/length/member triples, and `arc-view` lends the linker a temporary object record (`forth-bootstrap/cc/141-archive.fth:1`):

```forth file=cc/141-archive.fth
\ 141-archive.fth -- deterministic indexed ar and lazy archive linking.
\ Load on 010/020/030/140. All archive bytes and selection are Forth.
\ Newly reconstructed; regular GNU ar envelope, not thin archives.
\ API: arc-init, arc-add-object (nul-path --), arc-write (nul-path --).
\      lnk-add-archive (nul-path --), arc-check (nul-path --).
\ Errors reuse 250 malformed/unsupported, 251 capacity, 255 file I/O.

[lit] 256 constant arc-member-cap
[lit] 65536 constant arc-index-cap
[lit] 64 constant arc-member-size
create arc-members arc-member-cap arc-member-size * allot
create arc-index arc-index-cap [lit] 24 * allot
create arc-view lnk-object-size allot
```

Counts and sizes govern the collections; `arc-i`/`arc-j` and `arc-mp`/`arc-ip` walk them. Image, output, name, index, and long-name pairs retain slices; `arc-total`/`arc-pos` track layout; `arc-changed`/`arc-needed` track selection (`forth-bootstrap/cc/141-archive.fth:14`):

```forth file=cc/141-archive.fth
variable arc-count
variable arc-nindex
variable arc-long-size
variable arc-names-size
variable arc-image
variable arc-size
variable arc-i
variable arc-j
variable arc-mp
variable arc-ip
variable arc-total
variable arc-pos
variable arc-output
variable arc-output-size
variable arc-name
variable arc-nlen
variable arc-path
variable arc-changed
variable arc-needed
variable arc-index-data
variable arc-index-size
variable arc-long-data
variable arc-long-length
```

Format constants distinguish magic, BSD extended names and forbidden BSD indexes. `arc-member`/`arc-entry` locate rows, `arc-even` includes padding, and `arc-zero` clears bytes (`forth-bootstrap/cc/141-archive.fth:37`):

```forth file=cc/141-archive.fth
create arc-magic [lit] 33 c, s, <arch> [lit] 10 c,
create arc-bsd s, #1/
create arc-bsd-index s, __.SYMDEF
create arc-mode s, 100644
create arc-bsd-64 s, __.SYMDEF_64
: arc-name-allowed ( address length -- )
  dup [lit] 9 = if,
    over arc-bsd-index [lit] 9 bytes-eq 0= lnk-need
  then,
  dup [lit] 12 = if,
    over arc-bsd-64 [lit] 12 bytes-eq 0= lnk-need
  then, 2drop ;
: arc-member ( index -- row ) arc-member-size * arc-members + ;
: arc-entry ( index -- row ) [lit] 24 * arc-index + ;
: arc-even ( count -- count ) dup [lit] 1 and + ;
: arc-zero ( address count -- )
  begin, dup while, over [lit] 0 swap c! swap 1+ swap 1- repeat, 2drop ;
```

`arc-release` frees writer-owned members; `arc-init` also resets linker state and accumulated index/name sizes (`forth-bootstrap/cc/141-archive.fth:54`):

```forth file=cc/141-archive.fth
: arc-release
  [lit] 0 arc-i !
  begin, arc-i @ arc-count @ < while,
    arc-i @ arc-member dup @ swap [lit] 8 + @ lnk-unmap
    [lit] 1 arc-i +!
  repeat,
  [lit] 0 arc-count ! ;
: arc-init
  arc-release lnk-init
  [lit] 0 arc-nindex ! [lit] 0 arc-long-size ! [lit] 0 arc-names-size ! ;
```

## Collect names without resolving them

`arc-basename` strips directories and rejects empty, reserved, or nonprinting names. `arc-add-index` records a name slice and member index, including space for its terminator (`forth-bootstrap/cc/141-archive.fth:64`):

```forth file=cc/141-archive.fth
: arc-basename ( nul-path -- address length )
  dup arc-name ! [lit] 0 arc-nlen !
  begin, dup c@ while,
    dup c@ [lit] 47 = if,
      dup 1+ arc-name ! [lit] 0 arc-nlen !
    else, [lit] 1 arc-nlen +! then, 1+
  repeat, drop
  arc-nlen @ [lit] 0 > lnk-need
  arc-nlen @ [lit] 4095 [lit] 251 cc-check-cap
  [lit] 0 arc-j !
  begin, arc-j @ arc-nlen @ < while,
    arc-name @ arc-j @ + c@ dup [lit] 32 > lnk-need
    [lit] 127 < lnk-need [lit] 1 arc-j +!
  repeat,
  arc-name @ arc-nlen @ 2dup arc-name-allowed ;
: arc-add-index ( name length member-index -- )
  arc-nindex @ 1+ arc-index-cap [lit] 251 cc-check-cap
  arc-nindex @ arc-entry >r
  r@ [lit] 16 + ! dup 1+ arc-names-size +!
  r@ [lit] 8 + ! r> ! [lit] 1 arc-nindex +! ;
```

`arc-add-object` validates each symbol but indexes only global or weak definitions. Undefined names and locals cannot advertise a member; relocations wait until linking (`forth-bootstrap/cc/141-archive.fth:84`):

```forth file=cc/141-archive.fth
: arc-add-object ( nul-path -- )
  arc-count @ 1+ arc-member-cap [lit] 251 cc-check-cap
  dup arc-path ! arc-basename
  arc-count @ arc-member arc-mp !
  arc-mp @ [lit] 24 + ! arc-mp @ [lit] 16 + !
  arc-long-size @ arc-mp @ [lit] 56 + !
  arc-nlen @ [lit] 15 > if, arc-nlen @ [lit] 2 + arc-long-size +! then,
  arc-view lnk-op ! arc-path @ lnk-read-object
  arc-mp @ [lit] 8 + ! arc-mp @ !
  arc-mp @ [lit] 8 + @ [lit] 8 lnk-field !
  lnk-header lnk-sections
  [lit] 0 lnk-symbol-index !
  begin, lnk-symbol-index @ [lit] 32 lnk-field @ < while,
    lnk-symbol-index @ lnk-symbol lnk-sp ! lnk-validate-symbol
    lnk-sp @ lnk-binding if,
      lnk-sp @ lnk-symbol-name dup [lit] 0 > lnk-need 2drop
    then,
    lnk-sp @ lnk-binding 0= 0= lnk-sp @ lnk-shndx 0= 0= and if,
      lnk-sp @ lnk-symbol-name arc-count @ arc-add-index
    then,
    [lit] 1 lnk-symbol-index +!
  repeat,
  [lit] 1 arc-count +! ;

```

## Plan a deterministic archive

Header numbers are left justified: `arc-digits`/`arc-ndigit` stage reversed digits before `arc-decimal` writes within `arc-dest`/`arc-width`
(`forth-bootstrap/cc/141-archive.fth:108`):

```forth file=cc/141-archive.fth
\ Decimal fields are left justified, as required by portable ar headers.
create arc-digits [lit] 32 allot
variable arc-ndigit
variable arc-dest
variable arc-width
: arc-decimal ( value destination width -- )
  arc-width ! arc-dest ! [lit] 0 arc-ndigit !
  begin,
    dup dup [lit] 10 / [lit] 10 * - [lit] 48 + arc-digits arc-ndigit @ + c!
    [lit] 1 arc-ndigit +! [lit] 10 / dup 0=
  until, drop
  arc-ndigit @ arc-width @ <= lnk-need
  begin, arc-ndigit @ while,
    [lit] 1 arc-ndigit -!
    arc-digits arc-ndigit @ + c@ arc-dest @ c!
    [lit] 1 arc-dest +!
  repeat, ;
```

The GNU index uses big-endian fields: `arc-put-be32` emits them and `arc-be32` reads them (`forth-bootstrap/cc/141-archive.fth:125`):

```forth file=cc/141-archive.fth
: arc-put-be32 ( value address -- )
  >r dup [lit] 16777216 / r@ c!
  dup [lit] 65536 / r@ 1+ c!
  dup [lit] 256 / r@ [lit] 2 + c! r> [lit] 3 + c! ;
: arc-be32 ( address -- value )
  dup c@ [lit] 16777216 * over 1+ c@ [lit] 65536 * +
  over [lit] 2 + c@ [lit] 256 * + swap [lit] 3 + c@ + ;
```

`arc-header` fills `arc-header-p` with spaces, fixed metadata, size, and trailer. `arc-pad` adds a newline after odd payloads, outside the recorded size (`forth-bootstrap/cc/141-archive.fth:132`):

```forth file=cc/141-archive.fth
variable arc-header-p
: arc-header ( size -- )
  arc-output @ arc-pos @ + arc-header-p !
  [lit] 0
  begin, dup [lit] 60 < while,
    dup arc-header-p @ + [lit] 32 swap c! 1+
  repeat, drop
  [lit] 48 arc-header-p @ [lit] 16 + c!
  [lit] 48 arc-header-p @ [lit] 28 + c!
  [lit] 48 arc-header-p @ [lit] 34 + c!
  arc-mode arc-header-p @ [lit] 40 + [lit] 6 lnk-copy
  arc-header-p @ [lit] 48 + [lit] 10 arc-decimal
  [lit] 96 arc-header-p @ [lit] 58 + c!
  [lit] 10 arc-header-p @ [lit] 59 + c!
  [lit] 60 arc-pos +! ;
: arc-pad
  arc-pos @ [lit] 1 and if,
    [lit] 10 arc-output @ arc-pos @ + c! [lit] 1 arc-pos +!
  then, ;
```

`arc-plan` reserves index and long-name space before assigning member-header offsets. The complete bounded allocation lets the index precede the objects it locates (`forth-bootstrap/cc/141-archive.fth:151`):

```forth file=cc/141-archive.fth
: arc-plan
  arc-nindex @ [lit] 4 * [lit] 4 + arc-names-size @ + arc-index-size !
  [lit] 68 arc-index-size @ arc-even + arc-total !
  arc-long-size @ if, arc-long-size @ arc-even [lit] 60 + arc-total +! then,
  [lit] 0 arc-i !
  begin, arc-i @ arc-count @ < while,
    arc-i @ arc-member arc-mp !
    arc-total @ arc-mp @ [lit] 48 + !
    arc-mp @ [lit] 8 + @ arc-even [lit] 60 + arc-total +!
    arc-total @ lnk-cap [lit] 1 arc-i +!
  repeat,
  arc-total @ lnk-cap
  arc-total @ lnk-map arc-output ! arc-total @ arc-output-size ! ;
```

## Emit the index and members

The emitters share `arc-pos`; each consumes the offsets established by `arc-plan`. Their input → output relationships are:

| Emitter | Input → result |
|---|---|
| `arc-emit-index` | name/member rows → `/` count, header offsets, NUL-terminated names |
| `arc-emit-longs` | long basenames → `//` slash-newline records |
| `arc-emit-members` | member rows → headers and unchanged object payloads |
| `arc-write` | output path → magic, emitted members, published archive |

(`forth-bootstrap/cc/141-archive.fth:164`):

```forth file=cc/141-archive.fth
: arc-emit-index
  arc-index-size @ arc-header
  [lit] 47 arc-header-p @ c!
  arc-output @ arc-pos @ + arc-index-data !
  arc-nindex @ arc-index-data @ arc-put-be32
  [lit] 4 arc-pos +!
  [lit] 0 arc-i !
  begin, arc-i @ arc-nindex @ < while,
    arc-i @ arc-entry [lit] 16 + @ arc-member [lit] 48 + @
    arc-output @ arc-pos @ + arc-put-be32
    [lit] 4 arc-pos +! [lit] 1 arc-i +!
  repeat,
  [lit] 0 arc-i !
  begin, arc-i @ arc-nindex @ < while,
    arc-i @ arc-entry arc-ip !
    arc-ip @ @ arc-output @ arc-pos @ + arc-ip @ [lit] 8 + @ lnk-copy
    arc-ip @ [lit] 8 + @ 1+ arc-pos +! [lit] 1 arc-i +!
  repeat, arc-pad ;
```

(`forth-bootstrap/cc/141-archive.fth:182`):

```forth file=cc/141-archive.fth
: arc-emit-longs
  arc-long-size @ 0= if, exit, then,
  arc-long-size @ arc-header
  [lit] 47 arc-header-p @ c! [lit] 47 arc-header-p @ 1+ c!
  [lit] 0 arc-i !
  begin, arc-i @ arc-count @ < while,
    arc-i @ arc-member arc-mp !
    arc-mp @ [lit] 24 + @ [lit] 15 > if,
      arc-mp @ [lit] 16 + @ arc-output @ arc-pos @ +
      arc-mp @ [lit] 24 + @ lnk-copy
      arc-mp @ [lit] 24 + @ arc-pos +!
      [lit] 47 arc-output @ arc-pos @ + c!
      [lit] 10 arc-output @ arc-pos @ 1+ + c! [lit] 2 arc-pos +!
    then, [lit] 1 arc-i +!
  repeat, arc-pad ;
```

(`forth-bootstrap/cc/141-archive.fth:197`):

```forth file=cc/141-archive.fth
: arc-emit-members
  [lit] 0 arc-i !
  begin, arc-i @ arc-count @ < while,
    arc-i @ arc-member arc-mp !
    arc-pos @ arc-mp @ [lit] 48 + @ = lnk-need
    arc-mp @ [lit] 8 + @ arc-header
    arc-mp @ [lit] 24 + @ [lit] 15 > if,
      [lit] 47 arc-header-p @ c!
      arc-mp @ [lit] 56 + @ arc-header-p @ 1+ [lit] 15 arc-decimal
    else,
      arc-mp @ [lit] 16 + @ arc-header-p @ arc-mp @ [lit] 24 + @ lnk-copy
      [lit] 47 arc-header-p @ arc-mp @ [lit] 24 + @ + c!
    then,
    arc-mp @ @ arc-output @ arc-pos @ + arc-mp @ [lit] 8 + @ lnk-copy
    arc-mp @ [lit] 8 + @ arc-pos +! arc-pad [lit] 1 arc-i +!
  repeat, ;
```

(`forth-bootstrap/cc/141-archive.fth:213`):

```forth file=cc/141-archive.fth
: arc-write ( nul-path -- )
  arc-path ! arc-plan
  arc-magic arc-output @ [lit] 8 lnk-copy [lit] 8 arc-pos !
  arc-emit-index arc-emit-longs arc-emit-members
  arc-pos @ arc-output-size @ = lnk-need
  arc-output @ lnk-image ! arc-output-size @ lnk-file-size !
  arc-path @ lnk-path ! lnk-write
  arc-output @ arc-output-size @ lnk-unmap [lit] 0 lnk-image ! ;

```

## Validate the envelope before selecting a member

`arc-number-field` bounds a digit scan with `arc-numeric-a`/`arc-numeric-end`, accumulates `arc-number` in `arc-num-base`, and requires `arc-any`. `arc-span` bounds archive slices (`forth-bootstrap/cc/141-archive.fth:222`):

```forth file=cc/141-archive.fth
\ Archive reader: validate the whole envelope and index, not every payload.
\ Rows hold data,size,name,length,selected,header-offset,reserved,reserved.
variable arc-number
variable arc-numeric-end
variable arc-numeric-a
variable arc-num-base
variable arc-any
: arc-number-field ( address length base -- value )
  arc-num-base ! over + arc-numeric-end ! arc-numeric-a !
  [lit] 0 arc-number ! [lit] 0 arc-any !
  begin, arc-numeric-a @ arc-numeric-end @ < while,
    arc-numeric-a @ c@ [lit] 32 = if,
      begin, arc-numeric-a @ arc-numeric-end @ < while,
        arc-numeric-a @ c@ [lit] 32 = lnk-need [lit] 1 arc-numeric-a +!
      repeat,
    else,
      arc-numeric-a @ c@ [lit] 48 - dup [lit] 0 >= lnk-need
      dup arc-num-base @ < lnk-need
      arc-number @ [lit] 268435456 <= lnk-need
      arc-number @ arc-num-base @ * + arc-number !
      true arc-any ! [lit] 1 arc-numeric-a +!
    then,
  repeat,
  arc-any @ lnk-need arc-number @ ;
: arc-span ( offset size -- address )
  lnk-nonnegative >r lnk-nonnegative
  dup arc-size @ <= lnk-need arc-size @ over - r> >= lnk-need
  arc-image @ + ;
```

`arc-read-name` trims header spaces. `arc-ordinary` records payload, name, selection flag, header offset, and name kind without interpreting object bytes (`forth-bootstrap/cc/141-archive.fth:250`):

```forth file=cc/141-archive.fth
variable arc-member-data
variable arc-member-length
variable arc-name-kind
: arc-read-name
  [lit] 0 arc-name-kind !
  arc-header-p @ arc-name ! [lit] 16 arc-nlen !
  begin, arc-nlen @ while,
    arc-name @ arc-nlen @ 1- + c@ [lit] 32 <> if, exit, then,
    [lit] 1 arc-nlen -!
  repeat, lnk-bad ;
: arc-ordinary
  arc-count @ 1+ arc-member-cap [lit] 251 cc-check-cap
  arc-count @ arc-member arc-mp !
  arc-member-data @ arc-mp @ ! arc-member-length @ arc-mp @ [lit] 8 + !
  arc-name @ arc-mp @ [lit] 16 + ! arc-nlen @ arc-mp @ [lit] 24 + !
  [lit] 0 arc-mp @ [lit] 32 + ! arc-pos @ arc-mp @ [lit] 40 + !
  arc-name-kind @ arc-mp @ [lit] 48 + ! [lit] 1 arc-count +! ;
```

`arc-record-member` distinguishes `/`, `//`, GNU long-name offsets, BSD inline names, and ordinary names. Inline names consume payload bytes; their trailing NUL padding is removed (`forth-bootstrap/cc/141-archive.fth:267`):

```forth file=cc/141-archive.fth
: arc-record-member
  arc-read-name
  arc-name @ c@ [lit] 47 = if,
    arc-nlen @ [lit] 1 = if,
      arc-index-data @ 0= lnk-need
      arc-member-data @ arc-index-data ! arc-member-length @ arc-index-size ! exit,
    then,
    arc-nlen @ [lit] 2 = arc-name @ 1+ c@ [lit] 47 = and if,
      arc-long-data @ 0= lnk-need
      arc-member-data @ arc-long-data ! arc-member-length @ arc-long-length ! exit,
    then,
    arc-name @ 1+ arc-nlen @ 1- [lit] 10 arc-number-field
    arc-name ! [lit] 1 arc-name-kind ! arc-ordinary exit,
  then,
  arc-nlen @ [lit] 3 > if,
    arc-name @ arc-bsd [lit] 3 bytes-eq if,
      arc-name @ [lit] 3 + arc-nlen @ [lit] 3 - [lit] 10 arc-number-field
      dup [lit] 0 > lnk-need dup arc-member-length @ <= lnk-need
      arc-member-data @ arc-name ! dup arc-nlen !
      dup arc-member-data +! arc-member-length @ swap - arc-member-length !
      begin, arc-nlen @ while,
        arc-name @ arc-nlen @ 1- + c@ if, arc-ordinary exit, then,
        [lit] 1 arc-nlen -!
      repeat, lnk-bad
    then,
  then,
  arc-name @ arc-nlen @ 1- + c@ [lit] 47 = if, [lit] 1 arc-nlen -! then,
  arc-ordinary ;
```

`arc-resolve-names` requires GNU offsets to start at record boundaries and find slash-newline terminators. `arc-check-name` applies basename restrictions to every ordinary member (`forth-bootstrap/cc/141-archive.fth:295`):

```forth file=cc/141-archive.fth
: arc-check-name
  arc-nlen @ [lit] 0 > lnk-need
  arc-nlen @ [lit] 4095 [lit] 251 cc-check-cap
  arc-name @ arc-nlen @ arc-name-allowed
  [lit] 0 arc-j !
  begin, arc-j @ arc-nlen @ < while,
    arc-name @ arc-j @ + c@ dup [lit] 32 > lnk-need [lit] 127 < lnk-need
    [lit] 1 arc-j +!
  repeat, ;
: arc-resolve-names
  [lit] 0 arc-i !
  begin, arc-i @ arc-count @ < while,
    arc-i @ arc-member arc-mp !
    arc-mp @ [lit] 16 + @ arc-name ! arc-mp @ [lit] 24 + @ arc-nlen !
    arc-mp @ [lit] 48 + @ if,
      arc-long-data @ [lit] 0 <> lnk-need
      arc-name @ arc-long-length @ < lnk-need
      arc-name @ if,
        arc-long-data @ arc-name @ + 1- c@ [lit] 10 = lnk-need
      then,
      arc-long-data @ arc-name @ + arc-name ! [lit] 0 arc-nlen !
      begin,
        arc-name @ arc-nlen @ + arc-long-data @ arc-long-length @ + < lnk-need
        arc-name @ arc-nlen @ + c@ [lit] 10 <>
      while, [lit] 1 arc-nlen +! repeat,
      arc-nlen @ [lit] 1 > lnk-need
      arc-name @ arc-nlen @ 1- + c@ [lit] 47 = lnk-need [lit] 1 arc-nlen -!
      arc-name @ arc-mp @ [lit] 16 + ! arc-nlen @ arc-mp @ [lit] 24 + !
    then,
    arc-check-name [lit] 1 arc-i +!
  repeat, ;
```

## Turn the index into linker demand

`arc-parse-index` translates wire header offsets into member indexes, using `arc-found` as a member index plus one. Names must terminate before `arc-index-end`; `arc-index-cursor` consumes them in order. A nonempty member collection requires an index.

(`forth-bootstrap/cc/141-archive.fth:326`):

```forth file=cc/141-archive.fth
variable arc-index-offset
variable arc-index-cursor
variable arc-index-end
variable arc-found
: arc-parse-index
  arc-index-data @ 0= if, arc-count @ 0= lnk-need exit, then,
  arc-index-size @ [lit] 4 >= lnk-need
  arc-index-data @ arc-be32 dup arc-index-cap [lit] 251 cc-check-cap arc-nindex !
  arc-nindex @ [lit] 4 * [lit] 4 + arc-index-size @ <= lnk-need
  arc-index-data @ arc-nindex @ [lit] 4 * [lit] 4 + + arc-index-cursor !
  arc-index-data @ arc-index-size @ + arc-index-end !
  [lit] 0 arc-i !
  begin, arc-i @ arc-nindex @ < while,
    arc-index-data @ arc-i @ [lit] 4 * [lit] 4 + + arc-be32 arc-index-offset !
    [lit] 0 arc-j ! [lit] 0 arc-found !
    begin, arc-j @ arc-count @ < while,
      arc-j @ arc-member [lit] 40 + @ arc-index-offset @ = if,
        arc-j @ arc-found ! [lit] 1 arc-found +! 
      then, [lit] 1 arc-j +!
    repeat,
    arc-found @ [lit] 0 > lnk-need
```

Bounded name records and trailing padding (`forth-bootstrap/cc/141-archive.fth:347`):

```forth file=cc/141-archive.fth
    arc-i @ arc-entry arc-ip !
    arc-found @ 1- arc-ip @ [lit] 16 + !
    arc-index-cursor @ arc-ip @ ! [lit] 0 arc-nlen !
    begin,
      arc-index-cursor @ arc-index-end @ < lnk-need
      arc-index-cursor @ c@
    while, [lit] 1 arc-index-cursor +! [lit] 1 arc-nlen +! repeat,
    arc-nlen @ [lit] 0 > lnk-need arc-nlen @ arc-ip @ [lit] 8 + !
    [lit] 1 arc-index-cursor +! [lit] 1 arc-i +!
  repeat,
  begin, arc-index-cursor @ arc-index-end @ < while,
    arc-index-cursor @ c@ 0= lnk-need [lit] 1 arc-index-cursor +!
  repeat, ;
```

`arc-parse` checks magic, headers, payload bounds, and odd padding before names and index. `arc-open` owns the mapping; `arc-close` releases it; `arc-check` validates without selecting (`forth-bootstrap/cc/141-archive.fth:360`):

```forth file=cc/141-archive.fth
: arc-parse
  [lit] 0 arc-count ! [lit] 0 arc-nindex !
  [lit] 0 arc-index-data ! [lit] 0 arc-long-data !
  [lit] 0 [lit] 8 arc-span arc-magic [lit] 8 bytes-eq lnk-need
  [lit] 8 arc-pos !
  begin, arc-pos @ arc-size @ < while,
    arc-pos @ [lit] 60 arc-span arc-header-p !
    arc-header-p @ [lit] 58 + c@ [lit] 96 = lnk-need
    arc-header-p @ [lit] 59 + c@ [lit] 10 = lnk-need
    arc-header-p @ [lit] 48 + [lit] 10 [lit] 10 arc-number-field arc-member-length !
    arc-pos @ [lit] 60 + arc-member-length @ arc-span arc-member-data !
    arc-member-length @ >r arc-record-member
    r@ [lit] 1 and if,
      arc-pos @ [lit] 60 + r@ + [lit] 1 arc-span c@ [lit] 10 = lnk-need
    then,
    r> arc-even [lit] 60 + arc-pos +!
    arc-pos @ arc-size @ <= lnk-need
  repeat,
  arc-resolve-names arc-parse-index ;
: arc-open ( nul-path -- )
  arc-release arc-view lnk-op ! lnk-read-file arc-size ! arc-image ! arc-parse ;
: arc-close arc-image @ arc-size @ lnk-unmap [lit] 0 arc-count ! ;
: arc-check ( nul-path -- ) arc-open arc-close ;

```

The index proposes a member; the linker table decides whether it is needed. `arc-member-needed` looks for a currently undefined strong name. `lnk-add-archive` registers selected members and rescans while `arc-changed` is true. Their new references can demand earlier members.

(`forth-bootstrap/cc/141-archive.fth:384`):

```forth file=cc/141-archive.fth
\ Member order is stable; repeat the archive until no new member is needed.
\ Only strong unresolved names trigger extraction; weak definitions may serve
\ them. Local symbols never enter the archive index or global demand table.
: arc-member-needed ( member-index -- flag )
  arc-needed ! [lit] 0 arc-j !
  begin, arc-j @ arc-nindex @ < while,
    arc-j @ arc-entry arc-ip !
    arc-ip @ [lit] 16 + @ arc-needed @ = if,
      arc-ip @ @ arc-ip @ [lit] 8 + @ lnk-find
      dup @ if,
        [lit] 16 + @ dup lnk-shndx 0= swap lnk-binding [lit] 1 = and
        if, true exit, then,
      else, drop then,
    then, [lit] 1 arc-j +!
  repeat, [lit] 0 ;
```

(`forth-bootstrap/cc/141-archive.fth:399`):

```forth file=cc/141-archive.fth
: lnk-add-archive ( nul-path -- )
  arc-open
  begin,
    [lit] 0 arc-changed ! [lit] 0 arc-i !
    begin, arc-i @ arc-count @ < while,
      arc-i @ arc-member arc-mp !
      arc-mp @ [lit] 32 + @ 0= if,
        arc-i @ arc-member-needed if,
          true arc-mp @ [lit] 32 + ! true arc-changed !
          arc-mp @ @ arc-mp @ [lit] 8 + @ lnk-add-buffer
        then,
      then, [lit] 1 arc-i +!
    repeat,
    arc-changed @ 0=
  until, arc-close ;
```

With `caller.o` registered, `add` is undefined and strong. The first indexed `add.o` supplies it; the duplicate stays unselected.

A weak undefined name alone extracts nothing. A weak definition can satisfy strong demand, leaving an unneeded strong member untouched. Selection validates that member’s object metadata; unused payloads remain uninterpreted. Later inputs do not automatically revisit an earlier archive.

## Place bytes and zero-filled memory

`lnk-layout-section` advances `lnk-cursor` through each object’s alignment. `lnk-layout` places text, rodata, data, then BSS; file size stops before BSS while memory size includes it (`forth-bootstrap/cc/140-cc-link.fth:372`):

```forth file=cc/140-cc-link.fth
\ Place sections in four passes. Text and rodata share an RX mapping;
\ data and BSS share an RW mapping. BSS consumes no bytes in the file.
variable lnk-cursor
: lnk-layout-section
  [lit] 0 lnk-oi !
  begin, lnk-oi @ lnk-count @ < while,
    lnk-oi @ lnk-object lnk-op !
    lnk-si @ lnk-section lnk-sh !
    lnk-cursor @ lnk-sh @ [lit] 48 + @ lnk-align
    dup lnk-cap dup lnk-si @ lnk-place !
    lnk-sh @ [lit] 32 + @ + dup lnk-cap lnk-cursor !
    [lit] 1 lnk-oi +!
  repeat, ;
: lnk-layout
  lnk-count @ [lit] 0 > lnk-need
  [lit] 4096 lnk-cursor !
  [lit] 1 lnk-si ! lnk-layout-section
  [lit] 2 lnk-si ! lnk-layout-section
  lnk-cursor @ lnk-rx-size !
  lnk-cursor @ [lit] 4096 lnk-align dup lnk-cap
  dup lnk-rw-start ! lnk-cursor !
  [lit] 3 lnk-si ! lnk-layout-section
  lnk-cursor @ lnk-file-size !
  [lit] 4 lnk-si ! lnk-layout-section
  lnk-cursor @ lnk-memory-size !
  lnk-file-size @ lnk-map lnk-image ! ;
```

`lnk-copy-sections` copies initialized payloads. `lnk-defined-value` adds the owning section’s placement and image base, except for absolute or undefined symbols (`forth-bootstrap/cc/140-cc-link.fth:398`):

```forth file=cc/140-cc-link.fth
: lnk-copy-sections
  [lit] 0 lnk-oi !
  begin, lnk-oi @ lnk-count @ < while,
    lnk-oi @ lnk-object lnk-op ! [lit] 1 lnk-si !
    begin, lnk-si @ [lit] 4 < while,
      lnk-si @ lnk-section lnk-sh !
      lnk-sh @ [lit] 24 + @ lnk-op @ @ +
      lnk-si @ lnk-place @ lnk-image @ +
      lnk-sh @ [lit] 32 + @ lnk-copy
      [lit] 1 lnk-si +!
    repeat,
    [lit] 1 lnk-oi +!
  repeat, ;
: lnk-defined-value ( symbol -- value )
  dup lnk-shndx 0= if, drop [lit] 0 exit, then,
  dup lnk-shndx [lit] 65521 = if, [lit] 8 + @ exit, then,
  dup [lit] 8 + @ swap lnk-shndx lnk-place @ + lnk-base + ;
```

`lnk-resolve` keeps locals in their object and resolves other names through `lnk-selected` and its owner. Undefined weak references become zero; `lnk-check-unresolved` rejects remaining strong demand (`forth-bootstrap/cc/140-cc-link.fth:415`):

```forth file=cc/140-cc-link.fth
variable lnk-reference
variable lnk-selected
variable lnk-resolved-slot
: lnk-resolve ( symbol -- value )
  dup lnk-binding 0= if, lnk-defined-value exit, then,
  dup lnk-reference ! lnk-symbol-name lnk-find lnk-resolved-slot !
  lnk-resolved-slot @ @ 0= if, [lit] 253 cc-die then,
  lnk-resolved-slot @ [lit] 16 + @ lnk-selected !
  lnk-selected @ lnk-shndx 0= if,
    lnk-reference @ lnk-binding [lit] 2 <> if, [lit] 253 cc-die then,
    [lit] 0 exit,
  then,
  lnk-op @ >r lnk-resolved-slot @ [lit] 24 + @ lnk-op !
  lnk-selected @ lnk-defined-value r> lnk-op ! ;
: lnk-check-unresolved
  [lit] 0 lnk-oi !
  begin, lnk-oi @ lnk-count @ < while,
    lnk-oi @ lnk-object lnk-op ! [lit] 1 lnk-symbol-index !
    begin, lnk-symbol-index @ [lit] 32 lnk-field @ < while,
      lnk-symbol-index @ lnk-symbol dup lnk-binding if,
        lnk-resolve drop
      else, drop then,
      [lit] 1 lnk-symbol-index +!
    repeat,
    [lit] 1 lnk-oi +!
  repeat, ;
```

The requested entry must name a definition inside text; `lnk-find-entry` saves its placed value (`forth-bootstrap/cc/140-cc-link.fth:441`):

```forth file=cc/140-cc-link.fth
: lnk-find-entry
  lnk-entry-len @ [lit] 0 > 0= if, [lit] 253 cc-die then,
  lnk-entry-name @ lnk-entry-len @ lnk-find lnk-slot !
  lnk-slot @ @ 0= if, [lit] 253 cc-die then,
  lnk-slot @ [lit] 16 + @ lnk-sp !
  lnk-sp @ lnk-shndx [lit] 1 <> if, [lit] 253 cc-die then,
  lnk-slot @ [lit] 24 + @ lnk-op !
  lnk-sp @ [lit] 8 + @ [lit] 1 lnk-section [lit] 32 + @
  < 0= if, [lit] 253 cc-die then,
  lnk-sp @ lnk-defined-value lnk-entry-value ! ;

```

## Apply checked relocations

The relocation arithmetic consumes the records already emitted by the object writer. Here `S` is the resolved symbol, `A` its addend, and `P` the placed field address:

| Kind | Assignment |
|---|---|
| `R_X86_64_64` | `S + A` |
| `R_X86_64_PC32`, `R_X86_64_PLT32` | `S + A - P`, requiring sign extension |
| `R_X86_64_32` | `S + A`, requiring zero extension |
| `R_X86_64_32S` | `S + A`, requiring sign extension |

Relocation cursors retain type, offset, width, target, patch position, and value. `lnk-signed32?` reconstructs sign extension to test representability without overflowing a signed comparison
(`forth-bootstrap/cc/140-cc-link.fth:452`):

```forth file=cc/140-cc-link.fth
\ RELA's addend is a signed 64-bit cell. Arithmetic is modulo 2^64;
\ 32-bit relocations then explicitly check zero or sign extension.
variable lnk-rp
variable lnk-rend
variable lnk-rtype
variable lnk-roff
variable lnk-rwidth
variable lnk-target
variable lnk-patch
variable lnk-rvalue
: lnk-reloc-fail  [lit] 254 cc-die ;
: lnk-signed32? ( value -- flag )
  dup [lit] 4294967295 and
  dup [lit] 2147483648 and if,
    [lit] 0 [lit] 4294967296 - or
  then, = ;
```

`lnk-relocation` validates type, complete target span, and symbol index before resolving the value. It applies the addend and optional PC subtraction, checks the narrow representation, then writes the field.

(`forth-bootstrap/cc/140-cc-link.fth:468`):

```forth file=cc/140-cc-link.fth
: lnk-relocation
  lnk-rp @ [lit] 8 + lnk-u32 lnk-rtype !
  lnk-rtype @ [lit] 1 = if,
    [lit] 8 lnk-rwidth !
  else,
    lnk-rtype @ [lit] 2 = lnk-rtype @ [lit] 4 = or
    lnk-rtype @ [lit] 10 = or lnk-rtype @ [lit] 11 = or
    0= if, lnk-reloc-fail then,
    [lit] 4 lnk-rwidth !
  then,
  lnk-rp @ @ dup 0< if, lnk-reloc-fail then, lnk-roff !
  lnk-target @ lnk-section [lit] 32 + @
  dup lnk-roff @ < if, lnk-reloc-fail then,
  lnk-roff @ - lnk-rwidth @ < if, lnk-reloc-fail then,
  lnk-rp @ [lit] 12 + lnk-u32
  dup [lit] 32 lnk-field @ >= if, lnk-reloc-fail then,
  lnk-symbol lnk-resolve lnk-rp @ [lit] 16 + @ + lnk-rvalue !
  lnk-target @ lnk-place @ lnk-roff @ + lnk-patch !
```

Representation checks before assignment (`forth-bootstrap/cc/140-cc-link.fth:486`):

```forth file=cc/140-cc-link.fth
  lnk-rtype @ [lit] 2 = lnk-rtype @ [lit] 4 = or if,
    lnk-rvalue @ lnk-patch @ lnk-base + - lnk-rvalue !
  then,
  lnk-rtype @ [lit] 10 = if,
    lnk-rvalue @ [lit] 4294967296 / 0= 0=
    if, lnk-reloc-fail then,
  then,
  lnk-rtype @ [lit] 2 = lnk-rtype @ [lit] 4 = or
  lnk-rtype @ [lit] 11 = or if,
    lnk-rvalue @ lnk-signed32? 0= if, lnk-reloc-fail then,
  then,
  lnk-rvalue @ lnk-image @ lnk-patch @ +
  lnk-rwidth @ [lit] 8 = if, ! else, lnk-w32 then, ;
```

`lnk-relocate` visits each accepted object’s relocation tables, with `lnk-rp`/`lnk-rend` bounding the walk (`forth-bootstrap/cc/140-cc-link.fth:499`):

```forth file=cc/140-cc-link.fth
: lnk-relocate
  [lit] 0 lnk-oi !
  begin, lnk-oi @ lnk-count @ < while,
    lnk-oi @ lnk-object lnk-op ! [lit] 5 lnk-si !
    begin, lnk-si @ [lit] 7 < while,
      lnk-si @ lnk-section lnk-sh !
      lnk-sh @ [lit] 44 + lnk-u32 lnk-target !
      lnk-sh @ [lit] 24 + @ lnk-op @ @ + dup lnk-rp !
      lnk-sh @ [lit] 32 + @ + lnk-rend !
      begin, lnk-rp @ lnk-rend @ < while,
        lnk-relocation [lit] 24 lnk-rp +!
      repeat,
      [lit] 1 lnk-si +!
    repeat,
    [lit] 1 lnk-oi +!
  repeat, ;

```

## Describe the executable image

`lnk-output-header` uses the completed layout: headers, text, and rodata occupy the read/execute segment; data and BSS occupy the read/write segment. `lnk-ph` advances between them. The writable segment’s memory extent exceeds its file extent when BSS needs storage.

(`forth-bootstrap/cc/140-cc-link.fth:516`):

```forth file=cc/140-cc-link.fth
\ The executable needs program headers only. No dynamic loader or runtime
\ section table participates in loading these two page-congruent segments.
variable lnk-ph
: lnk-output-header
  lnk-image @ lnk-sh !
  [lit] 1179403647 lnk-sh @ lnk-w32
  [lit] 2 lnk-sh @ [lit] 4 + c!
  [lit] 1 lnk-sh @ [lit] 5 + c!
  [lit] 1 lnk-sh @ [lit] 6 + c!
  [lit] 2 lnk-sh @ [lit] 16 + lnk-w16
  [lit] 62 lnk-sh @ [lit] 18 + lnk-w16
  [lit] 1 lnk-sh @ [lit] 20 + lnk-w32
  lnk-entry-value @ lnk-sh @ [lit] 24 + !
  [lit] 64 lnk-sh @ [lit] 32 + !
  [lit] 64 lnk-sh @ [lit] 52 + lnk-w16
  [lit] 56 lnk-sh @ [lit] 54 + lnk-w16
  [lit] 2 lnk-sh @ [lit] 56 + lnk-w16
  lnk-sh @ [lit] 64 + lnk-ph !
  [lit] 1 lnk-ph @ lnk-w32
  [lit] 5 lnk-ph @ [lit] 4 + lnk-w32
  lnk-base lnk-ph @ [lit] 16 + !
  lnk-base lnk-ph @ [lit] 24 + !
  lnk-rx-size @ lnk-ph @ [lit] 32 + !
  lnk-rx-size @ lnk-ph @ [lit] 40 + !
  [lit] 4096 lnk-ph @ [lit] 48 + !
```

Writable segment extents (`forth-bootstrap/cc/140-cc-link.fth:541`):

```forth file=cc/140-cc-link.fth
  [lit] 56 lnk-ph +!
  [lit] 1 lnk-ph @ lnk-w32
  [lit] 6 lnk-ph @ [lit] 4 + lnk-w32
  lnk-rw-start @ lnk-ph @ [lit] 8 + !
  lnk-rw-start @ lnk-base + dup lnk-ph @ [lit] 16 + !
  lnk-ph @ [lit] 24 + !
  lnk-file-size @ lnk-rw-start @ - lnk-ph @ [lit] 32 + !
  lnk-memory-size @ lnk-rw-start @ - lnk-ph @ [lit] 40 + !
  [lit] 4096 lnk-ph @ [lit] 48 + ! ;
```

## Publish only a completed link

Before replacing a path, `lnk-check-output-alias` compares its device/inode against every recorded input identity, including archives that contributed nothing
(`forth-bootstrap/cc/140-cc-link.fth:550`):

```forth file=cc/140-cc-link.fth
\ Complete validation precedes output creation. Refuse input aliases by
\ inode/device, then publish through an exclusive sibling temporary file.
create lnk-temp-path  [lit] 4096 allot
create lnk-temp-suffix  s, .lnk-
create lnk-hex-digits  s, 0123456789abcdef
variable lnk-temp-length
variable lnk-pid
variable lnk-ti
: lnk-check-output-alias
  lnk-path @ lnk-stat-buffer [lit] 0 [lit] 0 [lit] 0 [lit] 0 [lit] 4 syscall6
  dup [lit] 0 [lit] 2 - = if, drop exit, then,
  0= 0= if, [lit] 255 cc-die then,
  [lit] 0 lnk-oi !
  begin, lnk-oi @ lnk-input-count @ < while,
    lnk-oi @ [lit] 16 * lnk-inputs +
    dup @ lnk-stat-buffer @ =
    swap [lit] 8 + @ lnk-stat-buffer [lit] 8 + @ = and
    if, [lit] 255 cc-die then,
    [lit] 1 lnk-oi +!
  repeat, ;
```

`lnk-make-temp-path` appends a process-derived suffix using `lnk-temp-length`, `lnk-pid`, and `lnk-ti`. `lnk-abandon-output` closes and removes a failed temporary output (`forth-bootstrap/cc/140-cc-link.fth:570`):

```forth file=cc/140-cc-link.fth
: lnk-make-temp-path
  [lit] 0 lnk-temp-length !
  begin, lnk-path @ lnk-temp-length @ + c@ dup while,
    lnk-temp-length @ [lit] 4069 > if, [lit] 255 cc-die then,
    lnk-temp-path lnk-temp-length @ + c!
    [lit] 1 lnk-temp-length +!
  repeat, drop
  lnk-temp-suffix lnk-temp-path lnk-temp-length @ + [lit] 5 lnk-copy
  [lit] 5 lnk-temp-length +!
  [lit] 0 [lit] 0 [lit] 0 [lit] 0 [lit] 0 [lit] 0 [lit] 39 syscall6 lnk-pid !
  [lit] 16 lnk-ti !
  begin, lnk-ti @ while,
    [lit] 0 [lit] 1 - lnk-ti +!
    lnk-hex-digits lnk-pid @ [lit] 15 and + c@
    lnk-temp-path lnk-temp-length @ + lnk-ti @ + c!
    lnk-pid @ [lit] 16 / lnk-pid !
  repeat,
  [lit] 0 lnk-temp-path lnk-temp-length @ + [lit] 16 + c! ;
: lnk-abandon-output
  lnk-fd @ close drop
  lnk-temp-path [lit] 0 [lit] 0 [lit] 0 [lit] 0 [lit] 0 [lit] 87 syscall6 drop
  [lit] 255 cc-die ;
```

`lnk-write` exclusively creates the sibling temporary, completes writes, closes, and renames. `lnk-link` replaces its previous image, retaining inputs, and finishes all validation before publication (`forth-bootstrap/cc/140-cc-link.fth:592`):

```forth file=cc/140-cc-link.fth
: lnk-write
  lnk-check-output-alias lnk-make-temp-path
  lnk-temp-path [lit] 193 [lit] 493 open
  dup 0< if, [lit] 255 cc-die then, lnk-fd !
  [lit] 0 lnk-done !
  begin, lnk-done @ lnk-file-size @ < while,
    lnk-fd @ lnk-image @ lnk-done @ + lnk-file-size @ lnk-done @ - write
    dup [lit] 0 [lit] 4 - = if, drop
    else,
      dup [lit] 0 <= if, lnk-abandon-output then, lnk-done +!
    then,
  repeat,
  lnk-fd @ close 0= 0= if, lnk-abandon-output then,
  lnk-temp-path lnk-path @ [lit] 0 [lit] 0 [lit] 0 [lit] 0 [lit] 82 syscall6
  0= 0= if, lnk-abandon-output then, ;
: lnk-link
  lnk-path !
  lnk-image @ if,
    lnk-image @ lnk-file-size @ lnk-unmap [lit] 0 lnk-image !
  then,
  lnk-layout lnk-check-unresolved lnk-find-entry
  lnk-copy-sections lnk-relocate lnk-output-header lnk-write ;
```

Atomic publication follows the object writer (Chapter 40). This linker additionally rejects input aliases; it does not promise crash-durable storage.

## Try it

Run from the `forth-bootstrap` checkout root with the seed already built. The compilation loop is unchanged from the preceding checkpoint. A small entry object supplies `call main; mov edi,eax; mov eax,60; syscall` using the existing object writer. The linker requires an explicit entry; choosing `main` itself would leave its return without a caller.

All generated files use a `mktemp -d` directory. The archive deliberately contains `add.o` twice. After adding the entry and caller, the archive path asserts that only one member joined them; extracting both would cause a duplicate strong definition.

<!-- tryit: expect "direct link returned 42\narchive link returned 42" -->
```sh
(
set -o pipefail
work=$(mktemp -d /tmp/book-probe.XXXXXXXXXX) || exit "$?"
trap 'status=$?; rm -rf -- "$work" || status=1; exit "$status"' EXIT
cat > "$work/add.c" <<'C' || exit "$?"
long add(long *base, long a, long b, long c, long d,
         long e, long f, long g) {
    return *base + a + b + c + d + e + f + g;
}
C
cat > "$work/caller.c" <<'C' || exit "$?"
extern long add(long *, long, long, long, long, long, long, long);
int main(void) {
    long base;
    base = 14;
    return add(&base, 1, 2, 3, 4, 5, 6, 7);
}
C
for unit in add caller; do
  {
    cat forth/010-lib.fth cc/0[2-9]*-cc-*.fth cc/1[01]*-cc-*.fth \
        cc/121-cc-sysv.fth cc/123-cc-object-program.fth || exit "$?"
    printf 'create output-path s, %s/%s.o [lit] 0 c,\n' "$work" "$unit"
    cat <<'FORTH' || exit "$?"
cc-sysv-object-enable
: object-main
  cc-load-stdin cc-preprocess cc-out-init cc-globals-init
  cc-sysv-object-program output-path cc-obj-write bye ;
object-main
FORTH
    cat "$work/$unit.c" || exit "$?"
  } | ./seed-forth || exit "$?"
done
{
  cat forth/010-lib.fth cc/020-cc-arena.fth cc/030-cc-io.fth cc/081-cc-object.fth || exit "$?"
  printf 'create output-path s, %s/start.o [lit] 0 c,\n' "$work"
  cat <<'FORTH' || exit "$?"
cc-obj-init
[lit] 232 cc-obj-byte [lit] 0 cc-obj-4le
[lit] 137 cc-obj-byte [lit] 199 cc-obj-byte
[lit] 184 cc-obj-byte [lit] 60 cc-obj-4le
[lit] 15 cc-obj-byte [lit] 5 cc-obj-byte
create entry-name s, _start
create main-name s, main
entry-name [lit] 6 cc-obj-global cc-obj-func cc-obj-default cc-obj-text [lit] 0 [lit] 14 cc-obj-symbol drop
main-name [lit] 4 cc-obj-global cc-obj-func cc-obj-default cc-obj-undef [lit] 0 [lit] 0 cc-obj-symbol
>r cc-obj-text [lit] 1 cc-obj-plt32 r> [lit] 0 [lit] 4 - cc-obj-reloc
output-path cc-obj-write bye
FORTH
} | ./seed-forth || exit "$?"
for mode in direct archive; do
  {
    cat forth/010-lib.fth cc/020-cc-arena.fth cc/030-cc-io.fth \
        cc/140-cc-link.fth cc/141-archive.fth || exit "$?"
    for name in start.o caller.o add.o libadd.a "$mode"; do
      printf 'create p-%s s, %s/%s [lit] 0 c,\n' "$name" "$work" "$name"
    done
    printf '%s\n' 'create entry-name s, _start'
    if [ "$mode" = archive ]; then
      printf '%s\n' 'arc-init p-add.o arc-add-object p-add.o arc-add-object' \
        'p-libadd.a arc-write arc-release'
    fi
    printf '%s\n' 'lnk-init p-start.o lnk-add-object p-caller.o lnk-add-object'
    if [ "$mode" = direct ]; then
      printf '%s\n' 'p-add.o lnk-add-object'
    else
      printf '%s\n' 'p-libadd.a lnk-add-archive' \
        ': check-selection lnk-count @ [lit] 3 <> if, [lit] 1 die then, ;' \
        'check-selection'
    fi
    printf 'entry-name [lit] 6 lnk-entry p-%s lnk-link lnk-release bye\n' "$mode"
  } | ./seed-forth || exit "$?"
  result=0
  "$work/$mode" || result=$?
  printf '%s link returned %s\n' "$mode" "$result"
  test "$result" -eq 42 || exit 1
done
)
```

Observed output:

```text
direct link returned 42
archive link returned 42
```

## Exercise

Hints and feedback are in [Appendix H](66-exercise-feedback.md#chapter-42-archive-demand-is-time-dependent).

**Trace — easy.** Reverse the caller and archive additions. Explain which name is unresolved and why a second archive occurrence would repair the link.

