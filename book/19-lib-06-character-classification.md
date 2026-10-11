# Chapter 19 — Character classification

Is the character `5` a digit, and is `/` just below the digit range?
Answering those questions needs a character predicate; subtracting a range's
base and testing its unsigned quotient supplies one without a branch.
The resulting words classify digits, letters, and whitespace for the input
parsers built later.

## The range-check trick: `digit?`

The skeleton is **subtract the base → divide by the range size → test for
zero**. Use unsigned `/`, `0=`, and canonical flags (Chapter 7),
with contracts collected in
[Chapter 13](13-primitive-reference.md#the-table).
The range-check trick uses `/` and `0=` with Chapter 17's subtraction.

For a byte `c`, the expression `(c - base) / range` followed by `0=`
accepts the contiguous interval starting at `base` and ending just before
`base + range`. Inside that interval, the difference is smaller than the
positive divisor, so the quotient is zero. At or above the upper bound,
the difference is at least the divisor, so the quotient is nonzero.

The lower bound is the subtle part. Below `base`, subtraction wraps to a
large unsigned cell value. Unsigned division keeps its quotient nonzero,
so the test rejects the byte. This argument applies to the ASCII ranges
here: their upper bounds fit in a byte and their sizes are small compared
with a wrapped cell value.

The digit interval supplies the first concrete base and size in
`forth-bootstrap/forth/010-lib.fth:71`:

```forth file=forth/010-lib.fth
\ ===== Character classification helpers =====
\ All return -1 if true, 0 if false (Forth boolean convention).
\ Approach: just hard-code the literal byte values and use 0= equality chains.
\ (char / [char] come later, in the section on immediate words, so these
\ few spell their ASCII codes in decimal.)

\ digit? ( c -- flag )  true if c is in '0'..'9' (ASCII 48..57)
\ Approach: compute (c-48)/10.  If c<48 the subtract underflows to a huge
\ unsigned, /10 is huge, 0= is 0.  If c in 48..57, (c-48)/10 = 0, 0= is -1.
\ If c >= 58, (c-48)/10 >= 1, 0= is 0.  ✓
: digit?  [lit] 48 - [lit] 10 / 0= ;

```

Digits occupy ASCII `48` through `57`, so the base is `48` and the range
size is `10`. Trace the values at the boundaries and at `5`:

| Input byte | After subtracting `48` (unsigned) | After dividing by `10` | Flag |
|---|---|---|---|
| `/` (`47`) | `18446744073709551615` | `1844674407370955161` | `0` |
| `0` (`48`) | `0` | `0` | `-1` |
| `5` (`53`) | `5` | `0` | `-1` |
| `9` (`57`) | `9` | `0` | `-1` |
| `:` (`58`) | `10` | `1` | `0` |

The `/` character is a useful failure probe. Its mathematical difference
from the base is `-1`. Signed division truncating toward zero would turn
that difference into a zero quotient and incorrectly accept it. The
seed's unsigned quotient rejects it. Substituting a Forth implementation
with signed `/` would change the predicate's behavior.

## `alpha-lower?` and `alpha-upper?`: change the interval

Lowercase and uppercase letters each occupy a contiguous ASCII block.
Only the base changes between their definitions in
`forth-bootstrap/forth/010-lib.fth:83`:

```forth file=forth/010-lib.fth
\ alpha-lower? ( c -- flag )  true if c is 'a'..'z' (97..122)
\ Same trick: (c-97)/26 = 0 iff c in 97..122.
: alpha-lower?  [lit] 97 - [lit] 26 / 0= ;

\ alpha-upper? ( c -- flag )  true if c is 'A'..'Z' (65..90)
: alpha-upper?  [lit] 65 - [lit] 26 / 0= ;

```

`alpha-lower?` uses base `97` and accepts `a` through `z`, ending at `122`.
`alpha-upper?` uses base `65` and accepts `A` through `Z`, ending at `90`.
Both blocks contain `26` characters. The range-check trick rejects the
byte immediately before each block and the byte immediately after it.
These are ASCII predicates, with no locale-dependent letter classes.

## `alpha?`: combine the letter tests

The gap between the uppercase and lowercase blocks contains punctuation.
A single interval from `A` through `z` would accept that gap, so the
combined predicate tests the blocks separately, using `or` (Chapter 16)
at the end of `forth-bootstrap/forth/010-lib.fth:90`:

```forth file=forth/010-lib.fth
\ alpha? ( c -- flag )  true if c is alphabetic
: alpha?  dup alpha-lower? swap alpha-upper? or ;

```

Call this the *preserve-and-combine* pattern: keep the input available
until every component test has consumed its copy, then combine the flags.
For `alpha?`, the stack evolves as follows:

| After | Stack |
|---|---|
| entry | `c` |
| `dup alpha-lower?` | `c lower-flag` |
| `swap alpha-upper?` | `lower-flag upper-flag` |
| `or` | `letter-flag` |

`swap` exposes the saved character to the uppercase test. Without it,
that test would classify the lowercase test's flag. The result accepts
either letter block while rejecting the punctuation between them.

## `space?`: four-way OR

Whitespace here is an explicit set: space (`32`), tab (`9`), LF (`10`),
and CR (`13`). A range spanning those codes would include unwanted
bytes. Each component instead subtracts its target code and tests the
difference for zero. The preserve-and-combine pattern carries the
character through the chain in `forth-bootstrap/forth/010-lib.fth:93`:

```forth file=forth/010-lib.fth
\ space? ( c -- flag )  true if c is ' '|tab|LF|CR
: space?  dup [lit] 32 - 0= over [lit]  9 - 0= or
          over [lit] 10 - 0= or  swap [lit] 13 - 0= or ;

```

Use `over` (Chapter 17) for the middle tests. The running stack state is
`c accumulated-flag`:

| After | Stack |
|---|---|
| space test | `c space-flag` |
| tab test and `or` | `c space-or-tab-flag` |
| LF test and `or` | `c space-or-tab-or-LF-flag` |
| CR test and `or` | `whitespace-flag` |

Each middle `over` retrieves the saved character beneath the accumulated
flag. The last test uses `swap` because it can consume that character
without preserving it again. Every test runs; this chain has no
short-circuit branch.

Vertical tab (`11`) and form feed (`12`) are outside this predicate's
set. Do not substitute the broader meaning of a C library whitespace
classifier. Chapter 29 builds the lexer; Chapter 20 develops general
comparison words from unsigned division.

## Try it

Run the following command from the `forth-bootstrap` checkout at
`./forth-bootstrap`, using the seed built in Part 1. `head -n 96` loads
the library header and definitions through `space?`, stopping before the
comparison words. Decimal character codes keep the checkpoint independent
of `char` and `[char]`, which Chapter 23 builds.

The temporary word `show-flag` prints `1` for an accepted byte and `0` for
a rejected byte: `0=` followed by addition of `49` maps the predicate's
flag to the corresponding ASCII digit for `emit`.

<!-- tryit: expect "01110\n0110\n0110\n1100\n1111000" -->
```sh
{ head -n 96 forth/010-lib.fth
  printf '%s\n' \
    ': show-flag 0= [lit] 49 + emit ;' \
    '[lit] 47 digit? show-flag [lit] 48 digit? show-flag [lit] 53 digit? show-flag [lit] 57 digit? show-flag [lit] 58 digit? show-flag [lit] 10 emit' \
    '[lit] 96 alpha-lower? show-flag [lit] 97 alpha-lower? show-flag [lit] 122 alpha-lower? show-flag [lit] 123 alpha-lower? show-flag [lit] 10 emit' \
    '[lit] 64 alpha-upper? show-flag [lit] 65 alpha-upper? show-flag [lit] 90 alpha-upper? show-flag [lit] 91 alpha-upper? show-flag [lit] 10 emit' \
    '[lit] 65 alpha? show-flag [lit] 97 alpha? show-flag [lit] 91 alpha? show-flag [lit] 48 alpha? show-flag [lit] 10 emit' \
    '[lit] 32 space? show-flag [lit] 9 space? show-flag [lit] 10 space? show-flag [lit] 13 space? show-flag [lit] 11 space? show-flag [lit] 12 space? show-flag [lit] 88 space? show-flag [lit] 10 emit' \
    'bye'
} | ./seed-forth
# prints "01110\n0110\n0110\n1100\n1111000"
```

Observed output:

```text
01110
0110
0110
1100
1111000
```

The output rows belong to `digit?`, `alpha-lower?`, `alpha-upper?`,
`alpha?`, and `space?`, in that order. The range rows test both endpoints
and the adjacent outside bytes; the digit row also tests `5`.
The combined letter row accepts `A` and `a`, then rejects `[` and `0`.
The whitespace row accepts each named whitespace byte, then rejects
vertical tab, form feed, and `X`.

## Exercise

**Trace (easy).** Trace `space?` on a tab, retaining the saved character
and accumulated flag at each step. If the final `swap` were replaced by
`over`, which extra value would remain beneath the result? Explain why
the printed classification alone would miss that stack error.
