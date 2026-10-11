# Chapter 15 — Code emission and HERE

`c,` appends an instruction byte and advances the allocation cursor. The key is to separate
the destination of an emitted byte from the address of the cell that records
the destination. `here-addr` and `c,` give the library a byte emitter built
from the seed's memory operations.

## The address of the cursor

Recall `here`, `,`, and the HERE cell from [Chapter 9](09-dictionary.md).
The byte emitter has a short skeleton: store at the current cursor, then
advance the cursor. Its first step needs the value returned by `here`;
its second needs somewhere to store the updated pointer.

Call the address of the HERE cell `H`, and its current contents `A`.
The byte belongs at `A`. The updated pointer belongs at `H`. In C terms,
this is the distinction between a pointer variable's value and its address.
Writing a new pointer at `A` would overwrite dictionary storage and leave
the cursor unchanged.

The helper derives `H` from the neighbouring LATEST cell, using the layout
from Chapter 5. The address calculation is in
`forth-bootstrap/forth/010-lib.fth:11`:

```forth file=forth/010-lib.fth

\ here-addr ( -- a )  push the address of the HERE sysvar cell.
\ Useful because most "advance HERE" idioms want to update the cell, not just
\ read its current value (which is what `here` does).  The seed's sysvars are
\ consecutive cells STATE, LATEST, HERE, so HERE's cell follows LATEST's.
: here-addr  latest [lit] 8 + ;         \ &HERE = &LATEST + 8 = 0x413010

```

`here-addr` has effect `( -- a )`: its result is `H`, independent of how
much dictionary storage has been used. Adding the cell stride of 8 to
`latest` reaches HERE's cell. This avoids copying its absolute address
into the definition, while still depending on the cells' relative layout.

## `c,` and the workhorse pattern

Use the memory contracts from Chapter 6, collected in
[Chapter 13's primitive reference](13-primitive-reference.md#the-table),
for `@`, `!`, `c@`, and `c!`. The important choice here is what each access
is *for*: a byte store writes the payload; a cell fetch and cell store
update the pointer that locates it.

The emitter joins those operations in **store-and-advance** order in
`forth-bootstrap/forth/010-lib.fth:18`:

```forth file=forth/010-lib.fth
\ c, ( b -- )  store low byte of TOS at HERE and advance HERE by 1.
\ This is the workhorse for any code-emission vocabulary built in Forth.
: c,
  here c!                                 \ *HERE = byte
  here-addr @ [lit] 1 + here-addr !       \ HERE += 1
;

```

`c,` ("c-comma") has effect `( b -- )`. Follow its body with byte value
`b` on the stack and `A` in the HERE cell:

| After | Data stack | Memory effect |
|---|---|---|
| `here` | `b A` | none |
| `c!` | empty | low byte of `b` written at `A` |
| `here-addr @` | `A` | none |
| `[lit] 1 +` | `A+1` | none |
| `here-addr !` | empty | cell at `H` contains `A+1` |

The payload store consumes its destination, so the update fetches the
cursor again. The final `here-addr` supplies `H` alongside the new value.
Replacing it with `here` would put that value into the dictionary instead
of recording where the next emission should go.

The update must use `!` even though the payload used `c!`. The pointer is
a whole cell; changing only its low byte would fail when advancing the
cursor needs a carry into the rest of the pointer.

## Byte versus cell emission

Using the cell size from Chapter 4, the store-and-advance choices are:

| Emitter | Payload written | Cursor afterward, starting at `A` |
|---|---|---|
| `c,` | low byte: 1 byte | `A+1` |
| `,` | whole cell: 8 bytes | `A+8` |

The value alone does not choose the width. A character value passed to
`,` still occupies a cell. Passed to `c,`, it occupies a byte. Mixing the
emitters therefore requires tracking each payload's starting address;
the next address is not always the previous address plus a cell.

Chapter 22 builds further cell writers and memory-update helpers.
Chapter 23 uses emission to construct constants, and Chapter 24 builds
control-flow combinators.

## Try it

Run from the `forth-bootstrap` checkout at `./forth-bootstrap`, with the
seed built in Part 1. `head -n 24` supplies the library header and the
complete definitions of `here-addr` and `c,`, stopping before the next
library section.

Save the starting cursor, then emit a byte, a cell, and a byte. Their
starting offsets are 0, 1, and 9. Read the cell with `@` and the bytes
with `c@`. Finally, save the destination obtained through `here-addr @`,
emit another byte, and read it back there. The character codes make
these reads visible through `emit`.

<!-- tryit: expect "ABCD" -->
```sh
{ head -n 24 forth/010-lib.fth
  printf '%s\n' \
    'here [lit] 65 c, [lit] 66 , [lit] 67 c,' \
    'dup c@ emit' \
    'dup [lit] 1 + @ emit' \
    '[lit] 9 + c@ emit' \
    'here-addr @ [lit] 68 c, c@ emit' \
    '[lit] 10 emit bye'
} | ./seed-forth
# prints "ABCD"
```

Observed output:

```text
ABCD
```

## Exercise

**Trace (easy).** Begin with HERE containing `A` and run the body of `c,`
for a byte `b`, then for a byte `d`. Write the destination of each store
and the contents of HERE after each call. Explain which store would go
to the wrong address if the final `here-addr` were replaced with `here`.
