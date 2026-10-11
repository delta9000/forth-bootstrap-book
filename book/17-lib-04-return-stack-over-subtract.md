# Chapter 17 — The return stack, `over`, and subtraction

`over` copies the operand beneath the top of the data stack; `-`
subtracts the top operand from the one beneath it. Both need a
construction from the words already available: temporary storage
exposes the buried operand, and complementing a cell makes subtraction
possible through addition. The resulting library also names the common
steps `1+` and `1-`.

## `over` via the return stack

The skeleton is **save, copy, restore, reorder**. Starting with `a b`,
save `b` so that `dup` can reach `a`, then restore `b` and position the
copy above it. Recall Chapter 6's balanced return-stack transfers
`>r`, `r>`, and `r@`; their contracts are in
[Chapter 13](13-primitive-reference.md#the-table).

The saved value belongs to this invocation of `over`. The body in
`forth-bootstrap/forth/010-lib.fth:34` brackets the copy with a save
and a restore:

```forth file=forth/010-lib.fth
\ over ( a b -- a b a )  copy second-from-top to top.
\ Standard Forth idiom, missing from our seed primitives.
: over  >r dup r> swap ;

```

Follow the body with `a` and `b` left symbolic. The return-stack column
shows only the temporary borrowed by `over`, omitting return addresses.

| After | Data stack | Borrowed temporary |
|---|---|---|
| input | `a b` | empty |
| `>r` | `a` | `b` |
| `dup` | `a a` | `b` |
| `r>` | `a a b` | empty |
| `swap` | `a b a` | empty |

Saving `b` exposes the operand that must be copied. The final `swap`
matters just as much: without it, the copy would sit below `b`.
The body restores its borrowed slot before returning. It does not
need `r@`, because it needs to recover `b`, not leave it saved.

## `-` from `+` and `nand`

Subtraction has the skeleton `a + (-b)`. The wrapping `+` (Chapter 7;
[Chapter 13](13-primitive-reference.md#the-table)) lets us construct
the additive inverse of `b`.

For a cell of width `w`, `b + ~b` has every bit set: its unsigned
value is `2^w - 1`. Adding one gives zero modulo `2^w`. Therefore
`~b + 1` is the cell that cancels `b` under addition. This is
**two's complement** negation. Interpreted as signed, the high bit
has negative weight; interpreted as unsigned, the same bits represent
the wrapped result. Here `~` has its C bitwise meaning.

Apply self-NAND (Chapter 16) to `b`, add one, and add the result to `a`, as in
`forth-bootstrap/forth/010-lib.fth:38`:

```forth file=forth/010-lib.fth
\ - ( a b -- a-b )  subtract via 2's complement (we have + and nand).
\ Used by classifier helpers and the local rel32 CALL encoder below.
: -  dup nand [lit] 1 + + ;

```

The placement of the additions determines which operand is negated:

| After | Data stack | Purpose |
|---|---|---|
| input | `a b` | keep the minuend beneath the subtrahend |
| `dup nand` | `a ~b` | complement the subtrahend |
| `[lit] 1` | `a ~b 1` | supply the increment |
| first `+` | `a (~b+1)` | form the additive inverse |
| last `+` | `a+(~b+1)` | leave `a-b` |

With `10 3`, the negated subtrahend is the cell representing `-3`,
and the result is `7`. With `3 10`, the result is `-7`: the cell
`0xfffffffffffffff9`. The latter is a negative result under the signed
interpretation, not an arithmetic failure. This identity concerns cell
arithmetic; it does not import C's rules for signed overflow.

Zero tests the wraparound in the negation itself. Complementing zero
sets every bit; adding one wraps to zero. Subtracting zero therefore
leaves the other operand unchanged.

## Step by one: `1+` and `1-`

A pointer advance or a length decrement should not require spelling
out a literal at every use. The names in
`forth-bootstrap/forth/010-lib.fth:42` package those steps:

```forth file=forth/010-lib.fth
\ 1+ ( n -- n+1 )   1- ( n -- n-1 )  Step by one: the commonest arithmetic
\ in the C compiler (pointers, counters, lengths), so it gets a name.
: 1+  [lit] 1 + ;
: 1-  [lit] 1 - ;

```

`1+` adds one directly. `1-` supplies one as the subtrahend to the
new `-`, so it inherits the same wraparound behavior. Starting from
`4`, they produce `5` and `3`, respectively.

## Why subtraction isn't a primitive

The primitive-versus-derived byte trade (Chapter 16) applies to `-`:
addition and self-NAND already suffice. `1-` then uses
that definition without needing another arithmetic mechanism.
Chapter 19 applies subtraction to character predicates; Chapter 27
covers the compiler's own vocabulary.

## Try it

Run this command from the `forth-bootstrap` checkout at
`./forth-bootstrap`, using the seed built in Part 1. The prefix selected
by `head -n 46` includes the library header and definitions through
`1-`, stopping before the syscall wrappers.

The `over` check starts with `2 5`; consuming the resulting stack from
the top prints `252`. The subtraction checks cover a positive result,
a negative result canceled by addition, and zero minus zero. In the
zero checks, `0= [lit] 49 + emit` prints `0` for success and `1` for
failure. The last line checks increment and decrement from `4`.

<!-- tryit: expect "252\n7\n0\n0\n53" -->
```sh
{ head -n 46 forth/010-lib.fth
  printf '%s\n' \
    '[lit] 2 [lit] 5 over [lit] 48 + emit [lit] 48 + emit [lit] 48 + emit [lit] 10 emit' \
    '[lit] 10 [lit] 3 - [lit] 48 + emit [lit] 10 emit' \
    '[lit] 3 [lit] 10 - [lit] 7 + 0= [lit] 49 + emit [lit] 10 emit' \
    '[lit] 0 [lit] 0 - 0= [lit] 49 + emit [lit] 10 emit' \
    '[lit] 4 1+ [lit] 48 + emit [lit] 4 1- [lit] 48 + emit [lit] 10 emit bye'
} | ./seed-forth
# prints "252\n7\n0\n0\n53"
```

Observed output:

```text
252
7
0
0
53
```

## Exercise

**Trace (easy).** Trace `over` on `a b`, then repeat the trace with
its final `swap` omitted. Give the altered stack effect and explain
why restoring the borrowed return-stack slot alone does not establish
`over`'s contract.
