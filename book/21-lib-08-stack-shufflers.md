# Chapter 21 — Stack shufflers

Suppose a buffer's address and length are on the stack, and you now push
the output descriptor. You have `addr count fd`, but `write` needs
`fd addr count`. All three values are correct; their positions are wrong.

Stack shufflers adapt one word's results to another word's inputs.
`nip`, `rot`, `2dup`, and `2drop` give names to four arrangements we
will need repeatedly:

| Word | Stack effect |
|---|---|
| `nip` | `( a b -- b )` |
| `rot` | `( a b c -- b c a )` |
| `2dup` | `( a b -- a b a b )` |
| `2drop` | `( a b -- )` |

## `nip`: keep the top

To discard `a` while keeping `b`, put `a` where `drop` can reach it
(primitive contracts in [Chapter 13](13-primitive-reference.md#the-table)).
The shuffle block opens with this definition in
`forth-bootstrap/forth/010-lib.fth:139`:

```forth file=forth/010-lib.fth
\ ===== Stack shuffles =====
\ Standard Forth stack-manipulation words built on the seed primitives
\ swap, dup, drop, >r, r>, plus over (defined above).

\ nip ( a b -- b )  drop second-from-top.
: nip   swap drop ;

```

| Step | Data stack |
|---|---|
| entry | `a b` |
| `swap` | `b a` |
| `drop` | `b` |

The exchange is essential: dropping immediately would keep the wrong operand.

## `rot`: bring the deepest operand to the top

A swap alone cannot reach `a` in `a b c`. Temporarily parking `c` makes
`a` accessible; the body in `forth-bootstrap/forth/010-lib.fth:146`
then restores `c` into its destination:

```forth file=forth/010-lib.fth
\ rot ( a b c -- b c a )  rotate third-from-top to top.
: rot   >r swap r> swap ;

```

| Step | Data stack | Saved data on return stack |
|---|---|---|
| entry | `a b c` | — |
| `>r` | `a b` | `c` |
| `swap` | `b a` | `c` |
| `r>` | `b a c` | — |
| `swap` | `b c a` | — |

The last swap puts `a` above the restored `c`. The saved-data column
omits return addresses; the temporary `c` is recovered before the word
returns. Values below `a` stay in place.

## `2dup`: copy the pair in order

After `over` copies `a`, the next `over` sees `b` beneath that copy
([Chapter 17](17-lib-04-return-stack-over-subtract.md)). This changing
position is what makes the repeated operation in
`forth-bootstrap/forth/010-lib.fth:149` duplicate the whole pair:

```forth file=forth/010-lib.fth
\ 2dup ( a b -- a b a b )  duplicate the top pair.
: 2dup  over over ;

```

| Step | Data stack |
|---|---|
| entry | `a b` |
| first `over` | `a b a` |
| second `over` | `a b a b` |

The copies preserve the original order. Repeating `dup` would copy only
`b`; repeating `over` reaches each member of the pair in turn.

## `2drop`: discard the pair

No rearrangement is needed when both top operands are unwanted.
The definition in `forth-bootstrap/forth/010-lib.fth:152` consumes them
in the order they become exposed:

```forth file=forth/010-lib.fth
\ 2drop ( a b -- )  drop the top pair.
: 2drop drop drop ;

```

The first `drop` consumes `b`; the second consumes the newly exposed `a`.
Anything beneath that pair survives. A caller can now say “discard this
address and length” without tracing the two drops again.

## Use the vocabulary at an interface

Return to the output problem. Trace two rotations on paper before the
call to `write` from Chapter 18:

| Step | Stack |
|---|---|
| Buffer and descriptor ready | `addr count fd` |
| First `rot` | `count fd addr` |
| Second `rot` | `fd addr count` |
| `write` returns | `written-or-error` |

No bytes moved in the buffer. Only the values describing the operation
changed places. A single `swap` would exchange the top two operands and
still leave the descriptor in the wrong position.

If the caller needs the original buffer pair afterward, apply `2dup`
to `addr count` *before* pushing the descriptor. The same two rotations
and `write` consume the copied operands, leaving
`addr count written-or-error`. That is a useful way to design a short
Forth body: write the next word's required inputs, then account for
which values must survive its call.

## Try it

Run this from the `forth-bootstrap` checkout at `./forth-bootstrap`, using
the seed built in Part 1. `head -n 154` loads the library through `2drop`,
stopping before the memory updates. The command supplies character codes
and prints the results from the top down:

<!-- tryit: expect "B\nACB\nBABA\nBA" -->
```sh
{ head -n 154 forth/010-lib.fth
  printf '%s\n' \
    '[lit] 65 [lit] 66 nip emit [lit] 10 emit' \
    '[lit] 65 [lit] 66 [lit] 67 rot emit emit emit [lit] 10 emit' \
    '[lit] 65 [lit] 66 2dup emit emit emit emit [lit] 10 emit' \
    '[lit] 65 [lit] 66 [lit] 67 [lit] 68 2drop emit emit [lit] 10 emit' \
    'bye'
} | ./seed-forth
# prints "B\nACB\nBABA\nBA"
```

Observed output:

```text
B
ACB
BABA
BA
```

`nip` keeps `B`. `rot` leaves `B C A`, so emission produces `ACB`.
`2dup` leaves `A B A B`, printed as `BABA`. `2drop` removes `C D`,
leaving `A B` to print as `BA`.

## Exercise

**Trace (easy).** Starting with `a b c d`, trace `rot nip` one component
word at a time. Which original operands survive, and in what order?

<details>
<summary>Self-check: four inputs, two shufflers</summary>

With the top at the right, `rot` acts only on `b c d`:
`a b c d → a c d b`. Then `nip` removes `d`, leaving `a c b`.
The original `a` never enters the rotation. With character codes for
`A B C D`, three `emit` calls consume the result top-first and print
`BCA`; the printed order is the reverse of the surviving stack order.

</details>
