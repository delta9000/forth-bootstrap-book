# Chapter 22 — Memory updates and cell writers

A counter update and a binary writer both change memory, but they need different
interfaces. `+!` and `-!` package an update to an
existing cell; `,4` and `,8` append a value in little-endian byte order.

The contracts separate updates from appends:

| Word | Stack effect | Memory effect |
|---|---|---|
| `+!` | `( n addr -- )` | Add `n` to the cell at `addr` |
| `-!` | `( n addr -- )` | Subtract `n` from the cell at `addr` |
| `,4` | `( v -- )` | Append the low four bytes of `v` at HERE |
| `,8` | `( v -- )` | Append all eight bytes of `v` at HERE |

<a id="-and---idiomatic-increment"></a>

## `+!` and `-!`: update a stored value

An update must keep the destination address available while it calculates
the replacement value. The read-modify-write helpers in
`forth-bootstrap/forth/010-lib.fth:155` do this with a saved copy on the data
stack:

```forth file=forth/010-lib.fth
\ ===== Memory update helpers =====

\ +! ( n addr -- )  add n to the cell at addr.
: +!  swap over @ + swap ! ;

\ -! ( n addr -- )  subtract n from the cell at addr.
: -!  swap over @ swap - swap ! ;

```

In C notation, their effects are `*addr += n` and `*addr -= n`.
Using the primitive contracts from [Chapter 13](13-primitive-reference.md#the-table),
let `old` stand for the cell's initial contents:

| Step | `+!` data stack | `-!` data stack |
|---|---|---|
| Entry | `n addr` | `n addr` |
| `swap over @` | `addr n old` | `addr n old` |
| Arithmetic | `addr (n+old)` after `+` | `addr (old-n)` after `swap -` |
| Final `swap` | `(n+old) addr` | `(old-n) addr` |
| `!` | empty | empty |

The leading address survives the arithmetic and becomes the store's
destination. Subtraction needs the extra exchange: `old` must be beneath
`n` when `-` runs. Replacing `+` with `-` without that exchange would
compute `n-old`.

Both helpers consume the amount and address. They leave the result in memory,
so a caller that also needs the result must retain an address and fetch it.
They do not advance HERE unless the caller explicitly supplies the address
of the HERE cell.

## `,4` and `,8`: cell-sized emission

The writers use `c,` and the HERE allocation model from
[Chapter 15](15-lib-02-code-emission-and-here.md).
For `,4`, the problem is preserving the rest of the value after each byte is
written. The body in `forth-bootstrap/forth/010-lib.fth:163` retains a copy
until the final emission:

```forth file=forth/010-lib.fth
\ ===== 4-byte little-endian writer =====
\ ,4 ( v -- )  emit low 4 bytes of v at HERE in LE order.
\ Used by call, (rel32) and any Forth-level code emitter that needs
\ compact little-endian immediates.
: ,4
  dup c,                       \ byte 0
  [lit] 256 / dup c,           \ byte 1
  [lit] 256 / dup c,           \ byte 2
  [lit] 256 / c, ;             \ byte 3

```

Call the repeated step **emit-and-divide**: emit the low byte, then divide
the retained value to expose the next byte. Each `dup c,` leaves a value
for the next division. The final `c,` consumes the remaining value.
The result is four bytes at consecutive addresses, with HERE advanced by
four. Higher bytes of the input are discarded.

For example, the checkpoint uses decimal `5208208757389214273`, whose
hexadecimal representation is `0x4847464544434241`. Following its low bytes
through `,4` gives this trace; the hexadecimal notation here describes values,
not seed input tokens:

| Value before emission | Byte written |
|---|---|
| `0x4847464544434241` | `0x41` (`A`) |
| `0x48474645444342` | `0x42` (`B`) |
| `0x484746454443` | `0x43` (`C`) |
| `0x4847464544` | `0x44` (`D`) |

This writer constructs the little-endian representation explicitly through
byte stores. Its last `c,` writes `D` even though the remaining value still
contains higher bytes.

### Why divide by 256?

For an unsigned value, integer division by `256`, or `2^8`, has the same
result as a logical right shift by eight bits. The quotient discards the
low byte and fills the vacated high bits with zero. That is exactly what
emit-and-divide needs after writing the low byte.

The seed's `/` is unsigned. Even when the input's sign bit is set, dividing
its bit pattern exposes the next byte without propagating that sign bit.
The writer therefore handles every cell bit pattern with the same sequence.

### `,8`: emit the low half, then the high half

A full cell can reuse the shorter writer if the original value survives
the first call. In `forth-bootstrap/forth/010-lib.fth:173`, `dup` preserves
that value and the division cascade brings its high half into reach:

```forth file=forth/010-lib.fth
\ ,8 ( v -- )  emit all 8 bytes of v at HERE in LE order.
\ Used for movabs imm64 in defining words and for 8-byte branch target slots.
: ,8
  dup ,4                                                 \ low 4 bytes
  [lit] 256 / [lit] 256 / [lit] 256 / [lit] 256 /        \ shift right 32
  ,4 ;                                                   \ high 4 bytes

```

The first `,4` consumes the copy and writes the low four bytes.
The four divisions shift the retained original right by a total of
32 bits. The second `,4` then writes the high four bytes, also low byte first.
Together they append eight bytes and consume the input.

On the traced value, the first call writes `ABCD` and the second writes
`EFGH`. No separate cursor adjustment is needed between the calls:
each emission has already advanced HERE. Chapter 23 uses these writers
to build runtime bodies for constants.

## Try it

Run this from the `forth-bootstrap` checkout at `./forth-bootstrap`, using
the seed built in Part 1. `head -n 179` loads the library through `,8`,
stopping before the immediate-flag code. Define the byte-reading helper
before reserving test data so its compiled body cannot occupy that data.

<!-- tryit: expect "CB\n4ABCD\n8ABCDEFGH" -->
```sh
{ head -n 179 forth/010-lib.fth
  printf '%s\n' \
    ': next-byte dup c@ emit 1+ ;' \
    'here [lit] 65 ,8 [lit] 2 over +! dup @ emit [lit] 1 over -! @ emit [lit] 10 emit' \
    'here [lit] 5208208757389214273 ,4 here over - [lit] 48 + emit next-byte next-byte next-byte next-byte drop [lit] 10 emit' \
    'here [lit] 5208208757389214273 ,8 here over - [lit] 48 + emit next-byte next-byte next-byte next-byte next-byte next-byte next-byte next-byte drop [lit] 10 emit' \
    'bye'
} | ./seed-forth
# prints "CB\n4ABCD\n8ABCDEFGH"
```

Observed output:

```text
CB
4ABCD
8ABCDEFGH
```

The initial cell contains `65`; adding `2` produces `C`, and subtracting
`1` produces `B`. Each writer test prints its HERE advance as a digit by
adding `48`, then reads back the bytes in ascending address order.
Thus `4ABCD` checks both truncation and cursor movement, while `8ABCDEFGH`
checks both halves of the full-cell writer.

## Exercise

**Trace (easy).** In `-!`, remove the `swap` immediately before `-`.
Trace the changed body with `n` smaller than the stored value. Which
subtraction does it perform, and does it still store at the correct address?
