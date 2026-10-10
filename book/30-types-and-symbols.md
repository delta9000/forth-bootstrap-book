# Chapter 30 — Types and symbols

A pointer-to-int type and an enum name such as `x` need records that survive beyond their source tokens. The type helpers encode the pointer's base and depth; the symbol table remembers the name's kind and value. By the checkpoint, you can construct that type, query its size, and add and find the symbol without a C parser.

In `int *p`, the star declares a pointer; reading `*p` later follows it.
If that distinction, arrays, struct tags or `const` are unfamiliar, try the
[Part 3 C-reading bridge](part-3-compiler.md#reading-the-c-input) before
packing them into compiler records.

## The one-word type encoding

The files divide the work this way:

```text
060-cc-types: base + pointer depth → type word → scalar size/alignment
             array node or record descriptor → aggregate details
070-cc-sym:   name → symbol id → kind, type, value, auxiliary facts
             scope boundary → discard younger symbols
```

A type word records the kind and pointer depth; a separate descriptor identifies the aggregate layout (`forth-bootstrap/cc/060-cc-types.fth:1`):

```forth file=cc/060-cc-types.fth
\ 060-cc-types.fth — C type encoding for the C-subset compiler.
\
\ A type is one machine word:
\   bits[ 0.. 7] = pointer depth (0 = scalar T, 1 = T*, 2 = T**, ...)
\   bits[ 8..15] = always 0
\   bits[16..31] = base kind (one of ty-* below)
\
\ Struct and function types use base = ty-struct / ty-func.  The type word
\ does not say which struct: the descriptor pointer lives in the symbol
\ table — the tag's sk-struct entry keeps it in val, and a struct-typed
\ variable keeps it in its struct-desc cell (070-cc-sym.fth) — and in a
\ field record's pointee slot (below).  The caller resolves it before any
\ size-of/field-offset query.
\
\ Depends on 010-lib.fth: constant, variable, [lit], if,/then,/else,, exit,,
\   begin,/while,/repeat,, +, -, *, /, =, dup, swap, drop, and, or, >, 1+,
\   @, !, c!, over; 020-cc-arena.fth: cc-check-cap, cc-alloc.

```

The base-kind constants distinguish C types even when their storage matches. In particular, `ty-llong` and `ty-ullong` retain an identity distinct from `ty-long` and `ty-ulong`; `ty-struct`, `ty-func` and `ty-array` identify shapes whose details need other records (`forth-bootstrap/cc/060-cc-types.fth:19`):

```forth file=cc/060-cc-types.fth
[lit] 0 constant ty-void
[lit] 1 constant ty-char
[lit] 2 constant ty-int                       \ legacy 64-bit; LP64 32-bit
[lit] 3 constant ty-struct
[lit] 4 constant ty-func
[lit] 5 constant ty-short
[lit] 6 constant ty-long
[lit] 7 constant ty-float
[lit] 8 constant ty-double
[lit] 9 constant ty-uchar
[lit] 10 constant ty-ushort
[lit] 11 constant ty-uint
[lit] 12 constant ty-ulong
[lit] 13 constant ty-ldouble
[lit] 14 constant ty-array
\ LP64 long long kinds share long's representation but not its identity:
\ only the LP64 data model spells them, and they rank above long.
[lit] 15 constant ty-llong
[lit] 16 constant ty-ullong
\ C99 _Bool: one byte holding 0 or 1, an unsigned type of lowest rank.
\ Conversion to it tests for nonzero; storage and loads are a byte's.
[lit] 17 constant ty-bool

```

## Array metadata beside the type

An array node records its element and dimension information separately from the encoded type. These readers all take the node address; the table names the result of each (`forth-bootstrap/cc/060-cc-types.fth:42`).

| Input → result | Reader |
|---|---|
| node → element type | `cc-ad-type` |
| node → element aggregate descriptor | `cc-ad-desc` |
| node → element count | `cc-ad-count` |
| node → inner array node | `cc-ad-inner` |
| node → total storage size | `cc-ad-size` |
| node → required alignment | `cc-ad-align` |
| node → element qualifier set | `cc-ad-qualified` |

```forth file=cc/060-cc-types.fth
\ Array nodes carry element type/descriptor, dimensions, size and alignment.
\ The last cell is the elements' qualifier set (110's cc-qualifier-bit:
\ const 1, volatile 2, restrict 4), 0 when unqualified: a pointer to the
\ node then points to qualified elements, as a pointer to const T would.
: cc-ad-type @ ;
: cc-ad-desc [lit] 8 + @ ;
: cc-ad-count [lit] 16 + @ ;
: cc-ad-inner [lit] 24 + @ ;
: cc-ad-size [lit] 32 + @ ;
: cc-ad-align [lit] 40 + @ ;
: cc-ad-qualified [lit] 48 + @ ;

```

The inner link preserves nested dimensions. Qualifiers sit beside the type word, so the same base and pointer depth can describe differently qualified elements. For the bridge's array, the element count is separate from `int`; adding `const` would add qualification, not another pointer level. Chapter 35 builds declarations from these records.

## Packing types and choosing scalar storage

Storage depends on the selected target. `cc-target-lp64` defaults off; `cc-bootstrap-floatbits` independently enables a restricted floating-storage approximation when LP64 is selected, without supplying floating arithmetic (`forth-bootstrap/cc/060-cc-types.fth:54`):

```forth file=cc/060-cc-types.fth
\ The M2-Planet route (Stage A) keeps the original data model unless opted in.
variable cc-target-lp64
[lit] 0 cc-target-lp64 !

\ Restricted first-stage bootstrap approximation, never the default ABI.
\ Portable bootstrap float values travel as integer bits in 8-byte cells.
\ This flag does not implement IEEE floating arithmetic or conversions.
variable cc-bootstrap-floatbits
[lit] 0 cc-bootstrap-floatbits !

```

Packing preserves the base while pointer depth changes. `ty-make` multiplies the base by 65536 and adds the depth; `ty-base` and `ty-ptr` recover the fields. Callers must keep the depth within its byte because the constructor does not mask it (`forth-bootstrap/cc/060-cc-types.fth:64`):

```forth file=cc/060-cc-types.fth
\ ty-make ( base ptrdepth -- ty )  Pack base and ptr-depth into one word.
: ty-make
  swap [lit] 65536 *  swap +  ;               \ (base << 16) | ptr-depth

\ ty-base ( ty -- base )  Extract the base kind (bits 16..31).
: ty-base
  [lit] 65536 /  [lit] 65535 and ;            \ shift right 16, mask low 16

\ ty-ptr ( ty -- depth )  Extract pointer depth (bits 0..7).
: ty-ptr
  [lit] 255 and ;

```

A pointer's storage is independent of its pointee. `ty-size` tests depth first, then selects scalar widths; the final fallback cannot supply a struct's actual size because the type word has no layout (`forth-bootstrap/cc/060-cc-types.fth:82`):

```forth file=cc/060-cc-types.fth
\ ty-size ( ty -- bytes )  Scalar/pointer storage size, not aggregate size.
\ The caller resolves struct descriptors before asking their size/alignment.
\ LP64 is the AMD64 System V model: int=4, long/pointer=8, long double=16.
\ Both long long kinds take the final eight-byte answer, exactly as long.
\ The default retains the original char=1 and other non-void scalars=8;
\ _Bool is one byte in both models.
: ty-size
  dup ty-ptr [lit] 0 > if, drop [lit] 8 exit, then,
  ty-base
  dup ty-void = if, drop [lit] 0 exit, then,
  dup ty-char = over ty-bool = or if, drop [lit] 1 exit, then,
  cc-target-lp64 @ if,
    cc-bootstrap-floatbits @ if,
      dup ty-float = over ty-double = or over ty-ldouble = or if,
        drop [lit] 8 exit,
      then,
    then,
    dup ty-uchar = if, drop [lit] 1 exit, then,
    dup ty-short = over ty-ushort = or if, drop [lit] 2 exit, then,
    dup ty-int = over ty-uint = or over ty-float = or if,
      drop [lit] 4 exit,
    then,
    dup ty-ldouble = if, drop [lit] 16 exit, then,
  then,
  drop [lit] 8 ;

```

In the default model, `char` and `_Bool` occupy a byte and `int` takes the fallback size. LP64 selects the narrower integer widths shown in the branches. Chapter 39 uses those widths for storage, and Chapter 47 supplies floating operations.

Size alone cannot decide unsigned comparison or distinguish scalar `long long` from a pointer to it. The predicates preserve those distinctions; scalar alignment follows size, with a nonzero alignment for `void` (`forth-bootstrap/cc/060-cc-types.fth:102`):

```forth file=cc/060-cc-types.fth
\ ty-unsigned? ( ty -- flag )  Pointers compare as unsigned addresses.
\ Plain char is signed in LP64; legacy byte expressions are zero-extended.
: ty-unsigned?
  dup ty-ptr [lit] 0 > if, drop true exit, then,
  ty-base
  dup ty-uchar = over ty-ushort = or
  over ty-uint = or over ty-ulong = or over ty-ullong = or
  over ty-bool = or
  swap ty-char = cc-target-lp64 @ 0= and or ;

\ ty-long-long? ( ty -- flag )  Scalar long long, signed or unsigned.
: ty-long-long?
  dup ty-ptr if, drop [lit] 0 exit, then,
  ty-base dup ty-llong = swap ty-ullong = or ;

\ ty-align ( ty -- bytes )  Scalar/pointer alignment; void uses 1.
\ Struct/union alignment is cc-sd-align, not the type word's fallback.
: ty-align  ty-size dup 0= if, drop [lit] 1 then, ;

```

`ty-unsigned?` includes pointers and the explicit unsigned kinds. Plain `char` takes unsigned semantics only in the default model. Struct and union callers use descriptor alignment instead of `ty-align`.

## Validating an integer suffix

The numeric token spelling (Chapter 29) supplies the suffix bytes. `cc-literal-unsigned` records whether a `U` was consumed; `cc-literal-long` records absent, single or doubled `L`. The unsigned reader consumes at most one marker across the whole parse (`forth-bootstrap/cc/060-cc-types.fth:121`):

```forth file=cc/060-cc-types.fth
\ cc-integer-suffix ( addr len -- flag )  The one integer-suffix parser,
\ shared by literal typing below and the constant evaluator (125).  The
\ text addr len starts at the suffix's first letter; flag is true only if
\ all of it is one C suffix: an optional U on either side of an optional
\ l, L, ll or LL (C90 6.1.3.2 plus long long).  So 1LLL, 1lL, 1LUL and
\ 1uu are false.  cc-literal-unsigned and cc-literal-long (0, 1 or 2)
\ record what was read.
variable cc-literal-unsigned
variable cc-literal-long
: cc-integer-suffix-u ( addr len -- addr' len' )
  dup 0= if, exit, then,
  cc-literal-unsigned @ if, exit, then,
  over c@ dup [char] u = swap [char] U = or if,
    true cc-literal-unsigned ! swap 1+ swap 1-
  then, ;
```

A doubled long suffix must repeat the same letter case. The parser tries unsigned, long, then unsigned again, so either order is accepted, but leftover text makes the whole suffix invalid (`forth-bootstrap/cc/060-cc-types.fth:136`):

```forth file=cc/060-cc-types.fth
: cc-integer-suffix-l ( addr len -- addr' len' )
  dup 0= if, exit, then,
  over c@ dup [char] l = swap [char] L = or 0= if, exit, then,
  [lit] 1 cc-literal-long !
  over c@ >r swap 1+ swap 1-                      ( addr' len' ; R: letter )
  dup if,
    over c@ r@ = if, [lit] 2 cc-literal-long ! swap 1+ swap 1- then,
  then,
  r> drop ;
: cc-integer-suffix ( addr len -- flag )
  [lit] 0 cc-literal-unsigned ! [lit] 0 cc-literal-long !
  cc-integer-suffix-u cc-integer-suffix-l cc-integer-suffix-u
  nip 0= ;

```

The suffix boundary needs only the set of suffix letters, since none is a hexadecimal digit. `cc-integer-suffix-start` returns the remaining slice and `cc-integer-literal-check` rejects a malformed suffix with code 240 (`forth-bootstrap/cc/060-cc-types.fth:150`):

```forth file=cc/060-cc-types.fth
\ cc-integer-suffix-letter? ( c -- flag )  u, U, l or L.
: cc-integer-suffix-letter?
  dup [char] u = over [char] U = or
  over [char] l = or swap [char] L = or ;

\ cc-integer-suffix-start ( addr len -- addr' len' )  Step over the
\ digits to the first suffix letter, or to the end.
: cc-integer-suffix-start
  begin, dup while,
    over c@ cc-integer-suffix-letter? if, exit, then,
    swap 1+ swap 1-
  repeat, ;

\ cc-integer-literal-check ( -- )  Parse the current tk-num token's
\ suffix, the letters the lexer (050) kept after the digits; no hex digit
\ is one of them.  A malformed suffix is 240, the constant evaluator's
\ code for an unsupported constant form, in every expression context.
: cc-integer-literal-check
  tok-str-addr @ tok-str-len @ cc-integer-suffix-start
  cc-integer-suffix 0= if, [lit] 240 cc-die then, ;

```

The check word validates the current token when called. The typing word below returns early in the default model, so that path does not itself perform suffix validation. Chapter 45 also uses the suffix parser for typed constants.

## Choosing an integer literal's type

LP64 typing combines suffix and magnitude. A doubled long suffix selects the long-long family; a single long suffix selects the long family. Within either family, an unsigned marker or a value beyond the signed range selects the unsigned kind (`forth-bootstrap/cc/060-cc-types.fth:171`):

```forth file=cc/060-cc-types.fth
\ cc-integer-literal-type ( -- ty )  Type of the current tk-num token.
\ The original spelling (050) distinguishes decimal from hex/octal and
\ preserves U/L/LL suffixes without expanding the lexer's snapshot state.
\ LP64 long and long long share one 64-bit representation, so only a
\ two-letter LL suffix selects long long; its value picks the signedness.
\ As a bootstrap extension, a decimal value beyond signed long uses ulong.
\ Range tests use unsigned division, so bit-63-set constants stay correct.
: cc-integer-literal-type
  cc-target-lp64 @ 0= if, ty-int [lit] 0 ty-make exit, then,
  cc-integer-literal-check
  cc-literal-long @ [lit] 1 > if,
    cc-literal-unsigned @ tok-num @ 2^63 / or if,
      ty-ullong
    else, ty-llong then,
    [lit] 0 ty-make exit,
  then,
  cc-literal-long @ if,
    cc-literal-unsigned @ tok-num @ 2^63 / or if,
      ty-ulong
    else, ty-long then,
```

Without a long suffix, `U` chooses between `uint` and `ulong`. Without any suffix, a small value gets `int`; a larger octal or hexadecimal value can get `uint` before the long family is needed. The continuation uses the leading source character to make that distinction (`forth-bootstrap/cc/060-cc-types.fth:191`):

```forth file=cc/060-cc-types.fth
  else,
    cc-literal-unsigned @ if,
      tok-num @ [lit] 4294967296 / if, ty-ulong else, ty-uint then,
    else,
      tok-num @ [lit] 2147483648 / 0= if,
        ty-int
      else,
        tok-str-addr @ c@ [char] 0 =
        tok-num @ [lit] 4294967296 / 0= and if,
          ty-uint
        else,
          tok-num @ 2^63 / if, ty-ulong else, ty-long then,
        then,
      then,
    then,
  then,
  [lit] 0 ty-make ;

```

The unsigned divisions compare magnitudes without treating the high bit as a negative sign. A decimal value beyond signed-long range gets `ulong` as a bootstrap extension. The final `ty-make` wraps the selected base as a scalar type.

## Record descriptors: stable identity, movable fields

A struct descriptor has a fixed header and a separate field table. Keeping the header address stable lets a symbol or a self-referential field retain the descriptor while its fields are being assembled (`forth-bootstrap/cc/060-cc-types.fth:209`):

```forth file=cc/060-cc-types.fth
\ ===========================================================================
\ Struct descriptor accessors.
\ ===========================================================================
\ A struct/union descriptor (allocated via cc-sd-alloc) is a fixed header
\ whose address never changes, plus a separately allocated field table:
\
\   offset  0: total-size (bytes)
\   offset  8: field-count
\   offset 16: aggregate alignment (LP64)
\   offset 24: is-union flag (LP64)
\   offset 32: target cell (SysV: bitfield cursor, 129-cc-bitfield.fth)
\   offset 40: field-table address (0 until the first field)
\   offset 48: field-table capacity, in records
\
\ Field i's record is at table + i*record-bytes.  LP64 records are 6 cells:
\     +  0: name-addr
\     +  8: name-len
\     + 16: field type (array element type when array-len is nonzero)
\     + 24: field offset (bytes from aggregate base)
\     + 32: aggregate/pointee descriptor, or 0
\     + 40: array length (0 for a scalar)
\
```

The table grows only when a requested field exceeds its capacity. Old tables remain allocated, so memory use includes the growth history; the comment's "fewer than twice" bound applies after the initial small-table allocation, not to a single-field record (`forth-bootstrap/cc/060-cc-types.fth:231`):

```forth file=cc/060-cc-types.fth
\ Legacy records keep only the first five cells (40 bytes) and legacy
\ code reads only the first two header cells.  The table starts with room
\ for 8 records and doubles when an append needs more, so small structs
\ stay small.  The live table holds fewer than twice the records in use,
\ but each outgrown table stays behind in the bump arena: together they
\ hold 8 + 16 + ... + C records for a final capacity C, under four times
\ the member count.  513 members leave tables of 8, 16, ... 512 and the
\ capped 1023, 2,039 records (about 4x).  The cap
\ is policy, not storage: LP64 allows 1023 members, C99's translation
\ limit for one struct or union (5.2.4.1).  That is over four times the
\ largest in GCC 4.0.4 (JNINativeInterface, 232 members) and seven times
\ bfd's (elf_backend_data, 143).  The legacy M2-Planet subset
\ keeps its documented 16-field limit and small arena.

```

The member limit is policy, separate from allocated capacity. `cc-sd-field-cap` chooses the limit, and the replaceable `cc-sd-record-bytes` chooses the record stride (`forth-bootstrap/cc/060-cc-types.fth:250`):

```forth file=cc/060-cc-types.fth
[lit] 16 constant cc-sd-max-fields
[lit] 1023 constant cc-sd-lp64-max-fields
[lit] 56 constant cc-sd-header-bytes
[lit] 8 constant cc-sd-initial-fields

: cc-sd-field-cap
  cc-target-lp64 @ if, cc-sd-lp64-max-fields else, cc-sd-max-fields then, ;

: cc-sd-record-bytes-default
  cc-target-lp64 @ if, [lit] 48 else, [lit] 40 then, ;
defer cc-sd-record-bytes
' cc-sd-record-bytes-default is cc-sd-record-bytes

```

The current header occupies 56 bytes in either model. Legacy field records occupy 40 bytes and LP64 records 48; the separate table is allocated by capacity, not exactly by member count.

## Allocating and reading a descriptor

Fresh headers and replacement tables must start cleared. `cc-zalloc` uses `cc-alloc` (Chapter 27), clears the requested byte range, and returns its start; `cc-sd-alloc` requests a header with no field table yet (`forth-bootstrap/cc/060-cc-types.fth:258`):

```forth file=cc/060-cc-types.fth
\ cc-zalloc ( bytes -- addr )  Arena storage cleared to zero, so cells a
\ target adds read as 0 even where the arena reuses mapped memory.
: cc-zalloc
  dup cc-alloc                                   ( bytes addr )
  dup >r swap over +                             ( start end ; R: addr )
  begin, over over < while,
    swap [lit] 0 over c! 1+ swap
  repeat,
  drop drop r> ;

\ cc-sd-alloc ( -- desc )  A zeroed header with no field table yet.
: cc-sd-alloc  cc-sd-header-bytes cc-zalloc ;

```

The header keeps layout facts apart from table-management facts. The readers take a descriptor; each paired setter takes a value followed by that descriptor (`forth-bootstrap/cc/060-cc-types.fth:271`).

| Input → result | Reader | Setter |
|---|---|---|
| descriptor → total size | `cc-sd-total-size` | `cc-sd-set-total-size` |
| descriptor → member count | `cc-sd-field-count` | `cc-sd-set-field-count` |
| descriptor → aggregate alignment | `cc-sd-align` | `cc-sd-set-align` |
| descriptor → union flag | `cc-sd-union?` | `cc-sd-set-union` |
| descriptor → field table | `cc-sd-table` | growth updates it |
| descriptor → table capacity | `cc-sd-table-cap` | growth updates it |

```forth file=cc/060-cc-types.fth
: cc-sd-total-size      @ ;                            \ ( desc -- size )
: cc-sd-field-count     [lit] 8 + @ ;                  \ ( desc -- n )
: cc-sd-align           [lit] 16 + @ ;                 \ ( desc -- align )
: cc-sd-union?          [lit] 24 + @ ;                 \ ( desc -- flag )
: cc-sd-set-total-size  ! ;                            \ ( v desc -- )
: cc-sd-set-field-count [lit] 8 + ! ;                  \ ( v desc -- )
: cc-sd-set-align       [lit] 16 + ! ;                 \ ( v desc -- )
: cc-sd-set-union       [lit] 24 + ! ;                 \ ( v desc -- )
: cc-sd-table           [lit] 40 + @ ;                 \ ( desc -- addr )
: cc-sd-table-cap       [lit] 48 + @ ;                 \ ( desc -- n )

```

Allocation does not calculate field offsets or update the member count. Chapter 35 makes those layout decisions and stores their results here.

## Growing the field table

A side table keyed by field-record address must follow a move. `cc-sd-table-moved` exposes that event; its default ignores it, while `cc-sd-grow-desc` keeps the descriptor available during copying (`forth-bootstrap/cc/060-cc-types.fth:282`):

```forth file=cc/060-cc-types.fth
\ cc-sd-grow ( desc need -- )  Replace the table with a zeroed one holding
\ at least need records (double, at least 8, at most the field cap) and
\ copy the old records across.  The old table stays behind in the arena,
\ so a record address taken before an append to the same descriptor is
\ stale afterwards; callers fetch each record after any such append.
\ cc-sd-table-moved ( old new bytes -- ) lets side tables keyed by record
\ address follow the records (115-cc-native.fth: field qualification).
: cc-sd-table-moved-default  drop 2drop ;
defer cc-sd-table-moved
' cc-sd-table-moved-default is cc-sd-table-moved
variable cc-sd-grow-desc
```

Growth doubles capacity until it meets the request, applies the member cap, then copies the old table into cleared storage. The move hook runs before the header is updated (`forth-bootstrap/cc/060-cc-types.fth:293`):

```forth file=cc/060-cc-types.fth
: cc-sd-grow
  swap cc-sd-grow-desc !                         ( need )
  cc-sd-grow-desc @ cc-sd-table-cap [lit] 2 *    ( need cap )
  dup cc-sd-initial-fields < if, drop cc-sd-initial-fields then,
  begin, over over > while, [lit] 2 * repeat,
  nip dup cc-sd-field-cap > if, drop cc-sd-field-cap then,
  dup cc-sd-record-bytes * cc-zalloc             ( cap new )
  cc-sd-grow-desc @ cc-sd-table over             ( cap new old new )
  cc-sd-grow-desc @ cc-sd-table-cap cc-sd-record-bytes *
  begin, dup while,                              ( cap new src dst n )
    >r over c@ over c! 1+ swap 1+ swap r> 1-
  repeat, drop 2drop                             ( cap new )
  cc-sd-grow-desc @ cc-sd-table over
  cc-sd-grow-desc @ cc-sd-table-cap cc-sd-record-bytes * cc-sd-table-moved
  cc-sd-grow-desc @ [lit] 40 + !
  cc-sd-grow-desc @ [lit] 48 + ! ;

```

A field-record address becomes stale when its table moves. Fetch it again after any operation that can append fields to the same descriptor.

The public record lookup checks the member cap before requesting growth. Afterward, index times stride selects the record in the current table (`forth-bootstrap/cc/060-cc-types.fth:310`):

```forth file=cc/060-cc-types.fth
\ cc-sd-field-rec ( desc i -- rec-addr )  Error 50 if record i would exceed
\ the target's member cap; grow the table when i is past its capacity.
: cc-sd-field-rec
  dup 1+ cc-sd-field-cap [lit] 50 cc-check-cap
  over cc-sd-table-cap over > 0= if, over over 1+ cc-sd-grow then,
  cc-sd-record-bytes * swap cc-sd-table + ;

```

## Field records and pointee identity

A field carries both an encoded type and an optional descriptor. For a struct pointer field such as `next`, the latter identifies the pointee layout needed to resolve a following field access. These accessor pairs keep that distinction explicit (`forth-bootstrap/cc/060-cc-types.fth:317`).

| Input → result | Reader | Setter |
|---|---|---|
| record → name address | `cc-sf-name-addr` | `cc-sf-set-name-addr` |
| record → name length | `cc-sf-name-len` | `cc-sf-set-name-len` |
| record → type | `cc-sf-type` | `cc-sf-set-type` |
| record → byte offset | `cc-sf-offset` | `cc-sf-set-offset` |
| record → aggregate/pointee descriptor | `cc-sf-desc` | `cc-sf-set-desc` |
| LP64 record → array length | `cc-sf-array-len` | `cc-sf-set-array-len` |

```forth file=cc/060-cc-types.fth
\ Field-record accessors / mutators.  Each takes rec-addr on TOS.
\ Alignment, union and array-length accessors are for LP64 descriptors only.
: cc-sf-name-addr       @ ;                            \ ( rec -- a )
: cc-sf-name-len        [lit]  8 + @ ;                 \ ( rec -- u )
: cc-sf-type            [lit] 16 + @ ;                 \ ( rec -- ty )
: cc-sf-offset          [lit] 24 + @ ;                 \ ( rec -- off )
: cc-sf-desc            [lit] 32 + @ ;                 \ ( rec -- desc )
: cc-sf-array-len       [lit] 40 + @ ;                 \ ( rec -- n )

: cc-sf-set-name-addr   ! ;                            \ ( a rec -- )
: cc-sf-set-name-len    [lit]  8 + ! ;                 \ ( u rec -- )
: cc-sf-set-type        [lit] 16 + ! ;                 \ ( ty rec -- )
: cc-sf-set-offset      [lit] 24 + ! ;                 \ ( off rec -- )
: cc-sf-set-desc        [lit] 32 + ! ;                 \ ( desc rec -- )
: cc-sf-set-array-len   [lit] 40 + ! ;                 \ ( n rec -- )

```

Nested-array metadata has a separate extension point. The default reader reports no inner node; the default setter accepts absence and rejects a nonzero node with code 213 (`forth-bootstrap/cc/060-cc-types.fth:333`):

```forth file=cc/060-cc-types.fth
\ Targets may extend field shape without changing legacy/native records.
: cc-sf-array-inner-default ( rec -- n ) drop [lit] 0 ;
: cc-sf-set-array-inner-default ( n rec -- )
  drop if, [lit] 213 cc-die then, ;
defer cc-sf-array-inner
defer cc-sf-set-array-inner
' cc-sf-array-inner-default is cc-sf-array-inner
' cc-sf-set-array-inner-default is cc-sf-set-array-inner
```

## The symbol-table parallel arrays

A symbol id selects the same row across each column. Its kind determines how to interpret `val`: a location for an object or function, a descriptor for a tag, a value for an enum constant, or an aliased type for a typedef (`forth-bootstrap/cc/070-cc-sym.fth:1`):

```forth file=cc/070-cc-sym.fth
\ 070-cc-sym.fth — symbol table for the C-subset compiler.
\
\ Ten parallel arrays indexed by symbol id (cell[], 030-cc-io.fth):
\   cc-sym-name-addr [id] : pointer into cc-src-buf where the name begins
\   cc-sym-name-len  [id] : length of the name in bytes
\   cc-sym-kind      [id] : sk-* (global/local/func/struct/enum/typedef)
\   cc-sym-type      [id] : encoded type word from cc-types
\   cc-sym-val       [id] : kind-specific payload
\                            sk-global/sk-func: globals-buf offset / vaddr
\                            sk-local         : slot index (disp -8*(slot+1))
\                            sk-struct        : arena-pointer to descriptor
\                            sk-enum          : integer value
\                            sk-typedef       : encoded type word
\   cc-sym-extra     [id] : one more fact, whose meaning depends on the symbol
\   cc-sym-extra2    [id] : and, for sk-func only, a second one
\ Nothing outside this file names the two extra arrays: each meaning has its
\ own accessor (see "Field accessors" below).
\
\ Scope markers stored in cc-scope-stack (push records the current sym-count;
\ pop restores it, discarding all symbols added since the matching push).
\
\ Depends on 010-lib.fth (constant, variable, create, allot, [lit], if,/then,,
\   0=, 1+, !, @, +!, -!, drop, swap, >r, r@, r>), 020-cc-arena.fth (cc-die,
\   cc-check-cap) and 030-cc-io.fth (cell[], cc-name-find).

[lit] 8192 constant cc-sym-cap

```

The columns reserve space for simultaneously live declarations, bounded by `cc-sym-cap`. `cc-sym-desc` and `cc-sym-inner` separate aggregate and nested-array metadata, while `cc-sym-qualified` keeps qualifier provenance outside the type word (`forth-bootstrap/cc/070-cc-sym.fth:28`):

```forth file=cc/070-cc-sym.fth
create cc-sym-name-addr  cc-sym-cap [lit] 8 * allot
create cc-sym-name-len   cc-sym-cap [lit] 8 * allot
create cc-sym-kind       cc-sym-cap [lit] 8 * allot
create cc-sym-type       cc-sym-cap [lit] 8 * allot
create cc-sym-val        cc-sym-cap [lit] 8 * allot
create cc-sym-extra      cc-sym-cap [lit] 8 * allot
create cc-sym-extra2     cc-sym-cap [lit] 8 * allot
create cc-sym-desc        cc-sym-cap [lit] 8 * allot
create cc-sym-inner       cc-sym-cap [lit] 8 * allot
\ Qualification provenance is separate from the encoded C type.
create cc-sym-qualified cc-sym-cap [lit] 8 * allot
```

Field qualification uses a different key: a field-record address. `cc-qualified-fields` heads a list whose newest matching entry wins; `cc-field-set-qualified` adds only nonzero sets, so passing zero does not erase an older entry (`forth-bootstrap/cc/070-cc-sym.fth:46`):

```forth file=cc/070-cc-sym.fth
variable cc-qualified-fields
\ A field's qualifier set (110's cc-qualifier-bit) lives in a list of
\ { next, record, set } nodes; the newest node for a record wins.
: cc-field-qualified ( record -- set )
  cc-qualified-fields @ begin, dup while,
    2dup [lit] 8 + @ = if, nip [lit] 16 + @ exit, then, @
  repeat, 2drop [lit] 0 ;
: cc-field-set-qualified ( set record -- )
  over if,
    [lit] 24 cc-alloc dup >r [lit] 8 + ! r@ [lit] 16 + !
    cc-qualified-fields @ r@ ! r> cc-qualified-fields !
  else, 2drop then, ;
variable cc-sym-count

```

The getter returns zero when no entry matches. This address-keyed list is why descriptor growth exposes a move hook; Chapter 39 supplies the relocation work for qualifications.

## Linking live symbols by name

The hash index stores a bucket head as id-plus-one, leaving zero for an empty bucket. Links in `cc-sym-hnext` instead use the id directly and end at negative one; `cc-sym-bucket-of` finds the bucket from the stored name (`forth-bootstrap/cc/070-cc-sym.fth:62`):

```forth file=cc/070-cc-sym.fth
\ Lookup by name goes through a hash table, as the preprocessor's macros
\ do (040): cc-sym-bucket holds, per cc-name-hash bucket (030), one more
\ than the id of the newest live symbol there (0 for none), and
\ cc-sym-hnext links each symbol to the next older one in its bucket (-1
\ at the end).  cc-scope-pop unlinks what it discards.
create cc-sym-bucket  cc-name-buckets [lit] 8 * allot
create cc-sym-hnext   cc-sym-cap [lit] 8 * allot

\ cc-sym-bucket-of ( id -- addr )  The bucket of symbol id's name.
: cc-sym-bucket-of
  dup cc-sym-name-addr cell[] @ swap cc-sym-name-len cell[] @
  cc-name-hash cc-sym-bucket cell[] ;

```

Reusing a row must not link it to discarded entries. `cc-sym-link` skips ids at or above the new id before inserting it; `cc-sym-unlink` restores the next older head and requires its argument to be the newest symbol in that bucket (`forth-bootstrap/cc/070-cc-sym.fth:66`):

```forth file=cc/070-cc-sym.fth
\ cc-sym-link ( id -- )  Put symbol id, whose name is filed, at the head
\ of its bucket.  Entries at id or above were discarded without
\ cc-scope-pop (a count stored directly): leave them out of the chain.
: cc-sym-link
  >r  r@ cc-sym-bucket-of
  dup @ 1-
  begin, dup r@ < 0= while, cc-sym-hnext cell[] @ repeat,
  r@ cc-sym-hnext cell[] !
  r> 1+ swap ! ;

\ cc-sym-unlink ( id -- )  Take symbol id, the newest in its bucket, out.
: cc-sym-unlink
  dup cc-sym-hnext cell[] @ 1+  swap cc-sym-bucket-of ! ;

```

Scope markers need only a saved row count. `cc-scope-stack` holds those counts, `cc-scope-depth` selects the next marker, and `cc-scope-cap` bounds nesting. The kind constants distinguish the row payloads described above (`forth-bootstrap/cc/070-cc-sym.fth:80`):

```forth file=cc/070-cc-sym.fth
[lit] 64 constant cc-scope-cap
create cc-scope-stack  cc-scope-cap [lit] 8 * allot
variable cc-scope-depth

\ Symbol kinds.
[lit] 0 constant sk-global
[lit] 1 constant sk-local
[lit] 2 constant sk-func
[lit] 3 constant sk-struct
[lit] 4 constant sk-enum
[lit] 5 constant sk-typedef

\ ===========================================================================
\ Add / lookup
\ ===========================================================================
```

## Adding and finding symbols

Appending a symbol checks capacity before touching a column. The id stays on the return stack while the payload values are consumed from right to left; every auxiliary column is cleared before the row becomes live (`forth-bootstrap/cc/070-cc-sym.fth:95`):

```forth file=cc/070-cc-sym.fth

\ cc-sym-add ( name-addr name-len kind type val -- id )
\ Append a new symbol; return its id.  Dies with code 60 if the table
\ already holds cc-sym-cap symbols.
\ Stores fields by parking the new id on the return stack so each store
\ has a fresh copy to compute the slot address.
: cc-sym-add
  cc-sym-count @ 1+ cc-sym-cap [lit] 60 cc-check-cap
  cc-sym-count @                                 ( a u k t v id )
  >r                                              \ R: id
  r@ cc-sym-val       cell[] !                   \ store val
  r@ cc-sym-type      cell[] !                   \ store type
  r@ cc-sym-kind      cell[] !                   \ store kind
  r@ cc-sym-name-len  cell[] !                   \ store name-len
  r@ cc-sym-name-addr cell[] !                   \ store name-addr
  r@ cc-sym-link                                 \ file it under its hash
  \ Extra is reused across scope pops; zero it on every add so callers don't
  \ inherit a stale value (sk-local array-len, sk-func fixup-list, etc.).
  [lit] 0 r@ cc-sym-extra  cell[] !
  [lit] 0 r@ cc-sym-extra2 cell[] !
  [lit] 0 r@ cc-sym-desc cell[] !
  [lit] 0 r@ cc-sym-inner cell[] !
  [lit] 0 r@ cc-sym-qualified cell[] !
  [lit] 1 cc-sym-count +!
  r> ;

```

Clearing matters when scope exit makes an old row reusable: an ordinary scalar must not inherit an array length, descriptor or pending function reference.

Lookup follows the selected bucket and returns the first matching live row, or negative one. `cc-sym-find` and `cc-sym-find-tag` initially share this implementation; Chapter 41 separates ordinary and tag namespaces (`forth-bootstrap/cc/070-cc-sym.fth:121`):

```forth file=cc/070-cc-sym.fth
\ cc-sym-find ( name-addr name-len -- id-or-neg1 )
\ The walk goes newest first along the name's bucket and returns at the
\ first match, which gives innermost-scope semantics: -1 means "not
\ found", anything >= 0 is the matched id.
\ The default keeps the original single lookup for the bootstrap dialect.
\ A target can separate C's ordinary and tag namespaces without replacing
\ the shared symbol records or their scope lifetime.
: cc-sym-find-default
  cc-nf-u ! cc-nf-a !
  cc-nf-a @ cc-nf-u @ cc-name-hash cc-sym-bucket cell[] @ 1-     ( id )
  begin, dup 0< 0= while,
    dup cc-sym-count @ < over cc-sym-name-len cell[] @ cc-nf-u @ = and if,
      dup cc-sym-name-addr cell[] @ cc-nf-a @ cc-nf-u @ bytes-eq if, exit, then,
    then,
    cc-sym-hnext cell[] @
  repeat, ;
defer cc-sym-find
defer cc-sym-find-tag
' cc-sym-find-default is cc-sym-find
' cc-sym-find-default is cc-sym-find-tag

```

The count check excludes discarded rows, and the length check precedes byte comparison. Shadowing depends on insertion order within the bucket, not on a scope number stored in each row.

## Reading a symbol's payload

Named accessors prevent callers from confusing the meanings of shared columns. Here is the read interface; setters take the new value followed by the id. The fixup accessors return a cell address so callers can update a list head (`forth-bootstrap/cc/070-cc-sym.fth:142`).

| Input → result | Accessor | Storage |
|---|---|---|
| id → kind / type / value | `cc-sym-kind-of`, `cc-sym-type-of`, `cc-sym-val-of` | corresponding column |
| id → array length | `cc-sym-array-len-of` | `cc-sym-extra` |
| id → struct descriptor | `cc-sym-struct-desc-of` | legacy extra; LP64 desc |
| id → inner array node | `cc-sym-array-inner-of` | `cc-sym-inner` |
| function id → call-list head cell | `cc-sym-call-fixups` | default extra |
| function id → address-list head cell | `cc-sym-addr-fixups` | default extra2 |
| object id → storage size | `cc-sym-object-size-of` | `cc-sym-extra2` |

```forth file=cc/070-cc-sym.fth
\ ===========================================================================
\ Field accessors / mutators (all take id on TOS).
\ ===========================================================================

: cc-sym-kind-of       cc-sym-kind      cell[] @ ;       \ ( id -- kind )
: cc-sym-type-of       cc-sym-type      cell[] @ ;       \ ( id -- ty   )
: cc-sym-val-of        cc-sym-val       cell[] @ ;       \ ( id -- val  )

\ The extra cell means one of three things, depending on the symbol; each
\ meaning has its own accessors, all over the same cc-sym-extra array.
\   array length: an array local or global's element count; 0 for a scalar.
: cc-sym-array-len-of     cc-sym-extra     cell[] @ ;  \ ( id -- n    )
: cc-sym-set-array-len    cc-sym-extra     cell[] ! ;  \ ( n id --    )
\   struct descriptor: a struct or struct-pointer local or global's
\   descriptor (060-cc-types.fth).  Its type's base is ty-struct, which is
\   how readers tell this meaning from an array length (so the subset has
\   no arrays of structs).
: cc-sym-struct-desc-of
  cc-target-lp64 @ if, cc-sym-desc else, cc-sym-extra then, cell[] @ ;  \ ( id -- desc )
: cc-sym-set-struct-desc
  cc-target-lp64 @ if, cc-sym-desc else, cc-sym-extra then, cell[] ! ;
: cc-sym-array-inner-of cc-sym-inner cell[] @ ;
: cc-sym-set-array-inner cc-sym-inner cell[] ! ;  \ ( desc id -- )
```

Legacy array length and struct identity share a column, which constrains their simultaneous use. LP64 gives struct identity its own column. The setters `cc-sym-set-array-len`, `cc-sym-set-struct-desc` and `cc-sym-set-array-inner` follow the same choices as their readers.

A function can be referenced before its address is known. The default call and address accessors expose separate pending-reference heads; object-size accessors reuse the latter column for objects. Chapter 32 builds the fixup machinery, and Chapter 37 resolves function references (`forth-bootstrap/cc/070-cc-sym.fth:165`):

```forth file=cc/070-cc-sym.fth
\   call fixups: for an sk-func not yet defined, the head of the list of
\   `call rel32` sites waiting for its address.  This word gives the cell's
\   address, so the list code can push onto it (0 = no pending calls).
: cc-sym-call-fixups-default cc-sym-extra cell[] ;
defer cc-sym-call-fixups
' cc-sym-call-fixups-default is cc-sym-call-fixups    \ ( id -- cell )
\ The extra2 cell has one meaning, for sk-func only.
\   address fixups: the head of the list of `movabs rdi, imm64` sites that
\   load the function's address before it is defined (a forward-declared
\   function used as a value, e.g. `common_recursion(expression)` before
\   expression's body).  cc-parse-function patches each imm64 to the real
\   vaddr when it reaches the definition.  0 = no pending loads.
: cc-sym-addr-fixups-default cc-sym-extra2 cell[] ;
defer cc-sym-addr-fixups
' cc-sym-addr-fixups-default is cc-sym-addr-fixups
: cc-sym-object-size-of cc-sym-extra2 cell[] @ ;
: cc-sym-set-object-size cc-sym-extra2 cell[] ! ;    \ ( id -- cell )

```

## Scopes are a stack of integers

Pushing a scope saves `cc-sym-count` at the next marker and advances the depth. The capacity check rejects excessive nesting before writing the marker (`forth-bootstrap/cc/070-cc-sym.fth:183`):

```forth file=cc/070-cc-sym.fth
\ ===========================================================================
\ Scopes
\ ===========================================================================

\ cc-scope-push ( -- )  Mark the current sym-count as a scope boundary.
\ Dies with code 61 past cc-scope-cap nested scopes.
: cc-scope-push
  cc-scope-depth @ 1+ cc-scope-cap [lit] 61 cc-check-cap
  cc-sym-count @
  cc-scope-depth @ cc-scope-stack cell[] !
  [lit] 1 cc-scope-depth +! ;

```

Popping must undo bucket links as well as reduce the count. It discards rows in reverse insertion order, ensuring each discarded row is still its bucket's newest member (`forth-bootstrap/cc/070-cc-sym.fth:195`):

```forth file=cc/070-cc-sym.fth
\ cc-scope-pop ( -- )  Discard any symbols added since the matching push;
\ pops the marker off cc-scope-stack.  A pop with no push to match is a
\ parser bug: die with code 62.
: cc-scope-pop
  cc-scope-depth @ 0= if, [lit] 62 cc-die then,
  [lit] 1 cc-scope-depth -!
  cc-scope-depth @ cc-scope-stack cell[] @       ( mark )
  begin, cc-sym-count @ over > while,
    [lit] 1 cc-sym-count -!  cc-sym-count @ cc-sym-unlink
  repeat, drop ;
```

A pop without a matching push dies with code 62. Rows below the saved count survive, so an outer `x` becomes visible again after an inner `x` is removed. Scope exit leaves the old bytes in the columns; the next addition overwrites and clears the reused row.

## How types and symbols connect

For `struct point p`, the type word identifies a struct, the descriptor identifies `point`'s layout, and `p`'s symbol holds its storage payload. A tag symbol carries the descriptor in `val`; an object symbol uses `cc-sym-set-struct-desc`. The descriptor supplies aggregate size and field offsets, which cannot be recovered from `ty-struct` alone.

These records retain the decisions that Chapter 35's declaration parser makes. Chapter 34 consumes field and type information for expressions; instruction emission begins in Chapter 31.

## Try it

Run from the `forth-bootstrap` checkout root. This driver constructs the opening pointer-to-int example, then inserts enum name `x` with value 7 and looks it up. `digit-out` prints the single-digit results used here.

<!-- tryit: expect "8 2 1\n4 7\ndriver exit: 0" -->
```sh
(
set -o pipefail
status=0
{
  cat forth/010-lib.fth cc/020-cc-arena.fth cc/030-cc-io.fth \
      cc/040-cc-prep.fth cc/050-cc-lex.fth \
      cc/060-cc-types.fth cc/070-cc-sym.fth || exit "$?"
  cat <<'FORTH' || exit "$?"
: digit-out [lit] 48 + emit ;
ty-int [lit] 1 ty-make
  dup ty-size digit-out [lit] 32 emit
  dup ty-base digit-out [lit] 32 emit
  ty-ptr digit-out [lit] 10 emit
[lit] 120 cc-src-buf c!
cc-src-buf [lit] 1 sk-enum ty-int [lit] 0 ty-make [lit] 7
  cc-sym-add drop
cc-src-buf [lit] 1 cc-sym-find
  dup cc-sym-kind-of digit-out [lit] 32 emit
  cc-sym-val-of digit-out [lit] 10 emit
bye
FORTH
} | ./seed-forth || status=$? # prints '8 2 1\n4 7'
printf 'driver exit: %s\n' "$status" # prints 'driver exit: 0'
test "$status" -eq 0
)
```

Observed output:

```text
8 2 1
4 7
driver exit: 0
```

The first line is pointer size, base kind (`ty-int`) and depth. The second is the found symbol's kind (`sk-enum`) and value. The shell reports the driver's exit status afterward.

For the coverage check, run just the layer-test pipelines selected by `forth-bootstrap/test.sh:123` and `forth-bootstrap/test.sh:128`:

<!-- tryit: expect "types exit: 0\nsymbols exit: 0" -->
```sh
(
set -o pipefail
status=0
cat forth/010-lib.fth cc/020-cc-arena.fth cc/030-cc-io.fth \
    cc/040-cc-prep.fth cc/050-cc-lex.fth cc/060-cc-types.fth \
    cc/test-060-cc-types.fth | timeout 5 ./seed-forth || status=$?
printf 'types exit: %s\n' "$status" # prints 'types exit: 0'
test "$status" -eq 0 || exit "$status"
status=0
cat forth/010-lib.fth cc/020-cc-arena.fth cc/030-cc-io.fth \
    cc/040-cc-prep.fth cc/050-cc-lex.fth cc/060-cc-types.fth \
    cc/070-cc-sym.fth cc/test-070-cc-sym.fth | timeout 5 ./seed-forth || status=$?
printf 'symbols exit: %s\n' "$status" # prints 'symbols exit: 0'
test "$status" -eq 0
)
```

Observed output:

```text
types exit: 0
symbols exit: 0
```

The type test checks base/depth round trips and default-model sizes (`forth-bootstrap/cc/test-060-cc-types.fth:10`). The symbol test checks insertion, successful and missing lookup, local kind and payload, global payload, shadowing, count restoration and reappearance of the outer binding (`forth-bootstrap/cc/test-070-cc-sym.fth:9`). These are smoke tests: they do not check LP64 widths, unsigned predicates, integer suffixes, descriptor allocation or growth, array metadata, qualifier lists, namespace rebinding, fixup heads or capacity-error paths. Passing them does not establish those behaviors.

## Exercise

Hints and feedback are in [Appendix H](66-exercise-feedback.md#chapter-30-shadowed-symbols).

**Trace — easy.** Follow the symbol test's inner `x` through `cc-sym-link` and `cc-scope-pop`. Identify the bucket head before the inner insertion, after it, and after the pop. Explain why decrementing `cc-sym-count` alone would leave the bucket pointing at a discarded row.
