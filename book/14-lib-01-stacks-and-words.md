# Chapter 14 — Stacks and words

The body `+ emit` adds two values and prints the low byte of their sum. Does it
leave the sum available afterward? We can answer without decoding a
single instruction: `+` consumes two values and leaves one; `emit`
consumes that one. The combined body leaves neither input nor sum.

That kind of reasoning is how we will read the library. Part 1 gave
each primitive a contract. Now we compose those contracts, carrying
values from word to word and checking that each new definition leaves
what its caller expects.

## Postfix evaluation

In C, `(2 + 3) * 4` uses parentheses to make addition happen first.
Forth uses **postfix evaluation**: operands precede
operators, and the data stack is where operands wait for a word to use them.
The seed needs `[lit]` for numbers (Chapter 12).

Read `[lit] 2 [lit] 3 + [lit] 4 *` from left to right. Starting with an
empty stack, each row shows the stack after the word runs, with the top
at the right:

| Word (with its input token, if any) | Data stack afterward |
|---|---|
| `[lit] 2` | `2` |
| `[lit] 3` | `2 3` |
| `+` | `5` |
| `[lit] 4` | `5 4` |
| `*` | `20` |

The sum stays on the stack while the next operand arrives. Word order
makes addition precede multiplication; no precedence rule or grouping
parentheses are needed.

## Stack-effect comments

Read `( before -- after )` as a contract at the call boundary. The names
on the left describe the inputs; the names on the right describe the
results. Within either side, the rightmost name is the top of the stack.
Names such as `a`, `b`, and `sum` are labels for the reader, not local
variables declared by the comment.

For example, `( a b -- sum )` promises a result in place of the named
inputs. `( a b -- )` leaves no result from those inputs. Neither notation
says the *entire* stack must start with exactly those values: deeper
values remain outside the contract unless the notation mentions them.
Repeated names denote the same value; a changed name can denote a computed
result. These comments describe stack shape and intent, not a type check.

To read a definition, use the familiar colon form from
[Chapter 10](10-colon-compiler.md): `: name ( before -- after ) body ;`.
Separate the call contract from the steps in the body. The contract tells
you what must be true when the word runs; it does not describe the stack
while the definition is being compiled.

Keep [Chapter 13’s primitive reference](13-primitive-reference.md#the-table)
open for each component word’s contract. Apply those contracts in body
order, carrying each result into the next step. Call this a **stack trace**.
The definition is consistent when the final trace matches its declared
effect and no step asks for an unavailable input.

A name in the body must also resolve through the dictionary lookup from
[Chapter 9](09-dictionary.md). A plausible stack comment cannot make an
unknown word available. That is why reading the library in source order
matters: each definition depends on names already available at that point.

Apply the method to the opening `+ emit` body. This is a symbolic hand
trace; `x` stands for an older value the caller wants to keep:

| Position | Symbolic stack |
|---|---|
| Entry | `x a b` |
| After `+` | `x a+b` |
| After `emit` | `x` |

The body's contract is `( a b -- )`. Leaving `x` out of that comment
means the body does not need to know it exists. We can therefore call
the same word with other useful values waiting beneath its operands.
The checkpoint gives this body the name `sum-byte` and makes its one
visible effect easy to recognize.

## Turning an operation into vocabulary

Giving `+ emit` the name `sum-byte` makes that combined behavior available
wherever an ordinary word can be used. We can supply two values and try
it at the input loop before including it in a larger definition. Lookup finds
its name just as it finds `+`; the caller uses its stack contract just
as it uses a primitive's. No new rule in the input loop is needed for
the new name.

This is **factoring**: give a useful operation a name and use that name
as a component of larger operations. The useful boundary is one you can
describe by its purpose and inputs and outputs. `sum-byte` promises to
consume two values and print their sum's low byte; a caller does not need
to repeat its internal stack trace. Short definitions help us check
those promises, while meaningful names keep the purpose of later code
visible through its stack operations.

Leo Brodie develops this design discipline in
[*Thinking Forth*](https://thinking-forth.sourceforge.net/tf-kindle.pdf),
Chapter 6, "Factoring." The aim is to expose useful concepts through
names and manageable interfaces. Splitting a sequence merely to make
each definition shorter can leave callers with more names to learn and
no clearer account of what the program does.

## The library’s opening conventions

Before any definitions, the header establishes how the library names
values and reaches the seed’s interfaces. Preserve this opening from
`forth-bootstrap/forth/010-lib.fth:1`:

```forth file=forth/010-lib.fth
\ 010-lib.fth — minimal helpers built on top of the 32 hand-encoded primitives.
\ Loaded before any Forth-level vocabulary.
\
\ Conventions:
\   - All arithmetic constants use [lit] (the decimal literal compiler)
\     because the seed has no interpret-mode number parser at all — [lit]
\     is the only path (the seed's parse_decimal_code).  Characters use char /
\     [char] (defined below), so no ASCII code needs a comment to explain it.
\   - No seed address is typed in: sysvar cells are found from the seed's
\     state and latest primitives, and primitive xts with ' (tick).
```

The library uses `[lit]` (Chapter 10) throughout. The decimal parser the header names is covered in
[Chapter 12](12-repl.md). The character
words named in the comment belong to Chapter 23; they are not needed here.

The address convention keeps the library tied to named seed interfaces
rather than copied numeric addresses. Consult Chapter 13 for `state`,
`latest`, and tick when those names occur. Chapter 15 applies this
convention to code emission and HERE.

## Try it

Run from the `forth-bootstrap` checkout at `./forth-bootstrap`, with the
seed built in Part 1. This scratch definition puts its contract
beside its body. It uses only seed words; it is not an addition to the
library source.

<!-- tryit: expect "A" -->
```sh
cat <<'FORTH' | ./seed-forth
: sum-byte ( a b -- )
  +
  emit
;
[lit] 32 [lit] 33 sum-byte
[lit] 10 emit
bye
FORTH
# prints "A"
```

Observed output:

```text
A
```

The inputs add to 65, so the emitted byte is `A`. The sum has been
consumed; the final literal supplies a fresh value for the newline.
The printed character checks one observable effect. The symbolic trace
explains why no extra value remains for the next word to trip over.

## Exercise

**Modify (easy).** Change `sum-byte` to print the byte and leave the sum
for its caller: `( a b -- sum )`. With the same inputs 32 and 33,
follow the call with `[lit] 1 + emit`; the result should be `AB` before
the newline. Decide where a copy is needed, trace the new body with an
older value `x` beneath its inputs, then run your version. Explain why
placing `dup` before `+` would compute a different result.

<details>
<summary>Hint: preserve the result at the point it exists</summary>

Which word first produces the sum? Which word consumes it? Put the copy
between those two responsibilities, then check the stack one step at a time.

</details>

<details>
<summary>Check the new contract</summary>

The body is `+ dup emit`. The hand trace is
`x a b` → `x sum` → `x sum sum` → `x sum`.
The first `emit` consumes only the copy. The caller's `[lit] 1 + emit`
turns the retained 65 into 66 and prints `B`, leaving the older `x` alone.

Putting the copy before the addition gives `dup + emit`:
`x a b` → `x a b b` → `x a 2b` → `x a`.
For 32 and 33, that body prints `B` and leaves 32. The caller adds one
and prints `!`, so the changed checkpoint produces `B!` rather than `AB`.
The two versions leave the same number of values, but different values:
stack depth alone cannot establish the contract.

</details>
