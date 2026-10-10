# Chapter 20 — Comparisons from unsigned division

How can unsigned division decide whether a signed value is negative?
The sign test comes from dividing by the value of the sign bit;
turning that quotient into a flag gives `0<` and the comparison words
built on it. The resulting library supports equality and signed ordering,
with an explicit limit on the subtraction used for ordering.

The skeleton is **subtract → extract the sign → canonicalise** for `<`;
equality stops at a zero test (unsigned `/`, `0=` and the -1/0 flag,
Chapter 7; contracts in [Chapter 13](13-primitive-reference.md#the-table)).

## `true`: name the canonical flag

A caller that needs an unconditional true value should be able to name it.
The comparison block begins by manufacturing that value in
`forth-bootstrap/forth/010-lib.fth:97`:

```forth file=forth/010-lib.fth
\ ===== Comparison operators =====
\ All return -1 (true) / 0 (false), Forth boolean convention.

\ true ( -- -1 )  the canonical true flag, all 64 bits set.  The decimal
\ literal parser is unsigned-only, so -1 cannot be written as [lit] -1;
\ `0 0=` manufactures it (0 is zero, so 0= answers -1).
: true  [lit] 0 0= ;

```

`true` has no input. Its body supplies zero to the existing zero test,
leaving the all-set cell.

## `=` and `<>`: two tokens each

Equality only asks whether subtraction leaves zero, as in
`forth-bootstrap/forth/010-lib.fth:105`:

```forth file=forth/010-lib.fth
\ = ( a b -- f )  -1 if a = b, else 0.  Equal iff (a - b) = 0.
: =   - 0= ;

\ <> ( a b -- f )  inverse of =.
: <>  = 0= ;

```

`=` consumes `a b` and tests their difference; `<>` consumes the same
operands and negates the equality result. Each body has two tokens.
Neither word needs a signed interpretation: subtraction modulo the cell
width is zero exactly when the operand bit patterns match. Overflow can
change the sign of a difference, but it cannot make unequal cells equal.

## The `2^63` trick

Ordering needs the sign of a difference, rather than just whether it
vanishes. A quotient can identify which interval contains a value, the
same quotient-as-interval idea as Chapter 19's range-check trick. Here the dividing point separates cell
patterns with the sign bit clear from those with it set.

The divisor gets a name in `forth-bootstrap/forth/010-lib.fth:111`:

```forth file=forth/010-lib.fth
\ 2^63 ( -- 2^63 )  9223372036854775808 = 0x8000000000000000, the sign bit
\ of a 64-bit signed integer.  The literal round-trips through
\ parse_decimal_code because that parser uses an unsigned 64-bit
\ accumulator.
: 2^63  [lit] 9223372036854775808 ;

```

`2^63` pushes `9223372036854775808`, or `0x8000000000000000`.
For an unsigned cell `u` below that divisor, the quotient is `0`.
For a cell at or above it, the quotient is `1`: even the largest cell is
less than twice the divisor. Those intervals are exactly the nonnegative
and negative signed bit patterns.

| Cell interpreted as unsigned | Quotient after `2^63 /` | Signed interpretation |
|---|---|---|
| `0` | `0` | zero |
| `100` | `0` | positive |
| `9223372036854775807` | `0` | largest positive |
| `9223372036854775808` | `1` | most negative |
| `18446744073709551615` | `1` | `-1` |

This sign-extraction via `/2^63` applies to every cell pattern. It relies
on the seed's unsigned `/`; replacing that operation with signed division
breaks the interval argument.

## `0<` and the `0= 0=` canonicalisation

The quotient has the right truth value but the wrong representation for
true. The final operations in `forth-bootstrap/forth/010-lib.fth:117`
convert it to the same canonical flag that `true` supplies:

```forth file=forth/010-lib.fth
\ 0< ( n -- f )  -1 if n is signed-negative (bit 63 set), else 0.
\ Strategy: the seed's `/` is unsigned (DIV instruction).  A value with
\ bit 63 set, divided by 2^63, yields exactly 1; any non-negative value
\ yields 0.  Then `0= 0=` canonicalises (1 -> -1, 0 -> 0).
: 0<  2^63 / 0= 0= ;

```

Trace the quotient through both zero tests:

| Quotient | After first `0=` | After second `0=` |
|---|---|---|
| `0` | `-1` | `0` |
| `1` | `0` | `-1` |

Call `0= 0=` **canonicalisation**: it preserves zero and converts any
nonzero cell to `-1`. The intermediate result reverses the truth value;
the final test restores it in canonical form. Thus `0< ( n -- f )`
returns true for a signed-negative input and false otherwise, including
zero. Unlike subtraction-based ordering, this sign test has no overflow
restriction: it inspects the input's existing sign bit.

## The cascade

For `a < b`, subtracting `b` from `a` reduces ordering to the sign test.
The source puts the domain next to the definition in
`forth-bootstrap/forth/010-lib.fth:123`:

```forth file=forth/010-lib.fth
\ < ( a b -- f )  signed less-than: a < b iff (a - b) is negative.
\ Domain: exact only while a - b fits in 64 signed bits, i.e. when a and b
\ are less than 2^63 apart — always so for operands of the same sign, and
\ for every size, count, offset and character the compiler compares.
\ Outside it the subtraction wraps: MAX-INT -1 < answers -1 (true).
: <   - 0< ;

```

Treat the last clause as the source's stated assumption about its callers.

The rule is stated as a distance on purpose: `>` and `<=` subtract in the
other order, and a distance under 2^63 keeps both `a - b` and `b - a` in
range.

For a failure probe, subtract `-1` from the largest positive signed cell,
`9223372036854775807`. The mathematical result is positive, but the cell
wraps to the most-negative signed pattern. `0<` correctly identifies that
pattern as negative, so `<` incorrectly reports true. Canonicalisation
cannot recover the sign lost through overflow.

Reversing the operands and negating flags supplies the remaining ordering
words in `forth-bootstrap/forth/010-lib.fth:130`:

```forth file=forth/010-lib.fth
\ > ( a b -- f )  signed greater-than: b < a.  Same domain as <.
: >   swap < ;

\ <= ( a b -- f )  not (a > b).
: <=  > 0= ;

\ >= ( a b -- f )  not (a < b).
: >=  < 0= ;

```

`>` swaps `a b` to `b a` and delegates to `<`. `<=` negates `>`;
`>=` negates `<`. This is the **comparison cascade**: reversal and negation reuse the
same ordering decision. They also inherit its limitation. In particular,
`>` and `<=` test the sign of `b - a`, whereas `<` and `>=` use `a - b`.
None is a general unsigned comparison.

## Try it

Run this command from the `forth-bootstrap` checkout at `./forth-bootstrap`,
using the seed built in Part 1. `head -n 138` loads the library through
`>=`, stopping before Chapter 21's stack shufflers. The temporary
`show-flag` uses Chapter 19's display convention: `1` for true, `0` for
false, with `49` as the ASCII digit code and `10` as the newline.

```sh
{ head -n 138 forth/010-lib.fth
  printf '%s\n' \
    ': show-flag 0= [lit] 49 + emit ;' \
    'true show-flag [lit] 0 0< show-flag [lit] 100 0< show-flag 2^63 [lit] 1 - 0< show-flag 2^63 0< show-flag true 0< show-flag [lit] 10 emit' \
    '[lit] 7 [lit] 7 = show-flag [lit] 7 [lit] 8 = show-flag [lit] 7 [lit] 7 <> show-flag [lit] 7 [lit] 8 <> show-flag [lit] 10 emit' \
    '[lit] 3 [lit] 5 < show-flag [lit] 5 [lit] 3 < show-flag [lit] 5 [lit] 3 > show-flag [lit] 3 [lit] 5 > show-flag [lit] 10 emit' \
    '[lit] 3 [lit] 3 <= show-flag [lit] 4 [lit] 3 <= show-flag [lit] 3 [lit] 3 >= show-flag [lit] 3 [lit] 4 >= show-flag [lit] 10 emit' \
    '2^63 0< true = show-flag [lit] 0 0< [lit] 0 = show-flag [lit] 10 emit' \
    '2^63 [lit] 1 - true < show-flag [lit] 10 emit' \
    'bye'
} | ./seed-forth
# prints "100011\n1001\n1010\n1010\n11\n1"
```

Observed output:

```text
100011
1001
1010
1010
11
1
```

The first row prints `true`, then sign tests for zero, a positive value,
the largest positive cell, the most-negative cell, and the all-set cell.
The next rows pair equality with inequality, less-than with greater-than,
and the inclusive comparisons at and beyond equality.

The `11` row checks the exact canonical results of `0<`, not just their
truth values. The final `1` is the deliberate overflow failure described
above: it demonstrates the boundary of this implementation's contract.

## Exercise

**Trace — moderate.** Find two operands of opposite sign for which `>`
gives the wrong answer, and say which subtraction overflowed.
