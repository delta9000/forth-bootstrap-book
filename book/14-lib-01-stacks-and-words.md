# Chapter 14 — Stacks and words

A library definition passes values from word to word on the data stack.
Stack-effect notation lets you carry a symbolic stack through
its body and check the result against its promise. By the end, you will
have a method for reading those definitions and the conventions that
open `forth/010-lib.fth`.

Part 2 builds a Forth vocabulary on the completed seed:

- Chapters 14–17 establish notation, code emission, logic, and the return-stack
  helpers. Chapter 17 builds `over` and subtraction.
- Chapters 18–22 add Linux interfaces, character classification, comparisons,
  stack shufflers, and memory updates. Chapter 21 owns `nip`, `rot`, `2dup`,
  and `2drop`.
- Chapters 23–25 build immediacy, constants, control flow, and defining words.
- Chapter 26 uses that vocabulary for the M1 assembler and hex2 linker.

## Postfix evaluation

In C, `(2 + 3) * 4` uses parentheses to make addition happen first.
Forth uses **postfix**, or **reverse Polish notation**: operands precede
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
\     is the only path; see Ch 20 for the parser.  Characters use char /
\     [char] (defined below), so no ASCII code needs a comment to explain it.
\   - No seed address is typed in: sysvar cells are found from the seed's
\     state and latest primitives, and primitive xts with ' (tick).
```

The literal convention uses `[lit]` from Chapter 10 throughout the
library. The header’s “Ch 20” is an older source comment; the decimal
parser is covered in [Chapter 12](12-repl.md) in this book. The character
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

The trace checks the definition at its call boundary:

| Position | Symbolic stack |
|---|---|
| Entry | `a b` |
| After `+` | `a+b` |
| After `emit` | empty |

With `x` below the inputs, the trace ends with `x`. Thus `( a b -- )`
describes the consumed inputs without requiring an otherwise empty stack.
The invocation supplies values whose sum emits `A`; the final literal and
`emit` supply the newline.

## Exercise

**Trace — easy.** For a body consisting of `+ emit`, begin with the symbolic
stack `a b`. Use Chapter 13 to write the stack after each word, then write
the body’s combined stack-effect comment. Repeat with an untouched value
`x` below `a b`. Check your answer against the trace in Try it above.
