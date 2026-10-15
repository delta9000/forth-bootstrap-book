# Chapter 16 — Logic from NAND

Two library lines turn the seed's single `nand` into `and` and `or`.
Feeding a value to both inputs of NAND supplies the missing
complement operation. With that pattern, the library gains both words
without adding machine code to the seed.

## `and` in three words

Use `nand` (Chapter 7), with its contract in
[Chapter 13](13-primitive-reference.md#the-table).
Here `~` means bitwise complement, `&` bitwise AND, and `|` bitwise OR.
The skeleton for `and` is to compute NAND, then complement its result.

Call `dup nand` **self-NAND**. For a value `x`, it computes
`~(x & x)`, which is `~x`. The library uses self-NAND to cancel the
complement left by the first NAND in `forth-bootstrap/forth/010-lib.fth:25`:

```forth file=forth/010-lib.fth
\ ----- bool / bitwise helpers built on nand -----
\ All derived because nand is the only logical primitive in the seed.

\ and ( a b -- a&b ) = ~~(a&b) = nand of nand-of-itself
: and  nand dup nand ;

```

The combined effect is `( a b -- a&b )`. Track the intermediate
result as `t = ~(a & b)`:

| After | Stack | Meaning |
|---|---|---|
| input | `a b` | operands |
| `nand` | `t` | complemented intersection |
| `dup` | `t t` | inputs for self-NAND |
| `nand` | `~t` | intersection, because the complements cancel |

For masks, `and` retains a bit only where both inputs have it set.
For example, the low bits of decimal 12 and 10 are `1100` and `1010`;
their intersection is `1000`, or decimal 8.

## `or` in six words

An OR must retain a bit when either input has it set. **De Morgan's
law** gives the construction: `a | b = ~(~a & ~b)`. Complement each
operand, then NAND those complements. This is De Morgan's law as code:
the final NAND supplies both the intersection and its outer complement.

The stack must expose each operand to self-NAND in turn. That ordering
appears in `forth-bootstrap/forth/010-lib.fth:31`:

```forth file=forth/010-lib.fth
\ or  ( a b -- a|b ) via De Morgan: ~(~a & ~b)
: or   dup nand swap dup nand nand ;

```

The effect is `( a b -- a|b )`:

| After | Stack | Meaning |
|---|---|---|
| input | `a b` | operands |
| `dup` | `a b b` | prepare self-NAND on `b` |
| `nand` | `a ~b` | complemented `b` |
| `swap` | `~b a` | expose `a` |
| `dup` | `~b a a` | prepare self-NAND on `a` |
| `nand` | `~b ~a` | complemented operands |
| `nand` | `~(~b & ~a)` | `a \| b` by De Morgan's law |

The reversed operand order does not change the intersection. The
`swap` matters because omitting it would apply self-NAND to `~b`
again, undoing that complement and leaving `a` untouched. For the same
masks, `1100` OR `1010` gives `1110`, or decimal 14.

## Flags and masks

With canonical flags (Chapter 7), as recorded in
[Chapter 13](13-primitive-reference.md#the-table),
the bitwise operations also implement Boolean conjunction and disjunction:

| `a` | `b` | `a and b` | `a or b` |
|---|---|---|---|
| false | false | false | false |
| false | true | false | true |
| true | false | false | true |
| true | true | true | true |

These are truth tables written side by side. Each output remains a
canonical flag, so it can feed another Boolean combination.

Arbitrary nonzero cells do not have that property. Decimal 1 and 2
are both nonzero, but their set bits do not overlap: their `and` is 0.
Their `or` is 3, which is nonzero but not canonical true. Use the
words as bitwise mask operations on arbitrary cells, or as Boolean
operations on canonical flags. They do not perform C's short-circuit
`&&` or `||`: both operands are already on the stack when the word runs.

## Why "logic from nand" matters

**Functional completeness of NAND** means that every Boolean function
of finitely many inputs can be expressed using NAND, with inputs
copied and reused as needed. Self-NAND supplies NOT; canceling a NAND's
complement supplies AND; De Morgan's law supplies OR.

Start with one row of a truth table. If that row requires `a` to be true
and `b` to be false, the Boolean expression `a AND NOT b` is true only for
that combination. With more inputs, AND together each required input or
its complement to recognize exactly one row.

Now build one such term for every row whose result should be true, and
OR those terms together. The result matches the whole table. If no row
should be true, use an input AND its complement, which is always false.
Finally, replace every NOT, AND and OR with the NAND constructions above.
NAND is the only logical operation left.

This is a statement about expressive power. It does not promise that
every construction is equally short or equally fast.

## What this buys

A **derived word** expresses its behavior through words the seed already
knows; a primitive is defined directly in the seed's machine code. With
subroutine threading (Chapter 10), `and` uses three calls and `or` uses
six, rather than a dedicated machine instruction for each operation.

The byte trade concerns where those implementations live. Deriving
`and` and `or` avoids adding their headers and machine-code bodies to
the seed image. Loading the library still allocates dictionary
entries and compiled bodies for them. The cost moves into code built
by the seed, and the extra calls remain an execution cost. There is no
fixed byte saving to claim without specifying alternative primitive
implementations.

Chapter 17 reuses self-NAND in subtraction. Chapter 19 uses these
Boolean words in character predicates; Chapter 27 covers the compiler's
own vocabulary.

## Try it

Run from the `forth-bootstrap` checkout at `./forth-bootstrap`, using
the seed built in Part 1. `head -n 33` loads the library header and
the definitions through `and` and `or`, stopping before Chapter 17's
`over`.

`0=` (Chapter 7) turns a zero test into a canonical flag. The command uses
`[lit] 0 0=` to supply true. After each Boolean result, `0= [lit] 49 +`
converts false to the character `0` and true to `1` for `emit`.
The first output line checks `and` in the truth table's row order;
the next checks `or`. The last line checks bit masks: the intersection
of 12 and 10 prints as `8`, and their union plus 51 prints as `A`.

<!-- tryit: expect "0001\n0111\n8A" -->
```sh
{ head -n 33 forth/010-lib.fth
  printf '%s\n' \
    '[lit] 0 [lit] 0 and 0= [lit] 49 + emit' \
    '[lit] 0 [lit] 0 0= and 0= [lit] 49 + emit' \
    '[lit] 0 0= [lit] 0 and 0= [lit] 49 + emit' \
    '[lit] 0 0= [lit] 0 0= and 0= [lit] 49 + emit' \
    '[lit] 10 emit' \
    '[lit] 0 [lit] 0 or 0= [lit] 49 + emit' \
    '[lit] 0 [lit] 0 0= or 0= [lit] 49 + emit' \
    '[lit] 0 0= [lit] 0 or 0= [lit] 49 + emit' \
    '[lit] 0 0= [lit] 0 0= or 0= [lit] 49 + emit' \
    '[lit] 10 emit' \
    '[lit] 12 [lit] 10 and [lit] 48 + emit' \
    '[lit] 12 [lit] 10 or [lit] 51 + emit' \
    '[lit] 10 emit bye'
} | ./seed-forth
# prints "0001\n0111\n8A"
```

Observed output:

```text
0001
0111
8A
```

## Exercise

**Trace (easy).** Trace `or` with false beneath true, writing the
stack after every word. Then remove `swap` on paper and trace the
same inputs. Explain the difference using self-NAND. Do the final flags
distinguish the two bodies for this input? Choose a second input pair
that distinguishes them, and show both results.

<details>
<summary>Hint: keep the operands symbolic</summary>

After the first `dup nand`, the stack is `a ~b`. In the original, which
operand does the next self-NAND complement? What happens if `swap` is
missing? Here `~` means bitwise complement.

</details>

<details>
<summary>Check both traces</summary>

The original finishes `~(~b & ~a)`, which is OR. Without `swap`, the
second self-NAND restores `b`, so the result is `~(a & b)`, NAND. For
`a=0, b=-1`, the omitted swap would exchange two zeroes; even the numeric
states hide the mistake, and both results are `-1`. With `0 0`, OR gives
`0` and the altered body gives `-1`; with `-1 -1`, they give `-1` and `0`.
Use one of those pairs to recheck your symbolic derivation.

</details>
