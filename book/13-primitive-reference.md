# Chapter 13 — The 32 seed primitives: reference

A primitive’s stack effect, code offset, and behavior belong together.
The table pairs each contract with a link to its decoding chapter. Keep it
beside a Forth definition to check each primitive’s inputs and results.

## The table

The 32 dictionary words appear in source order. “Code offset” locates the
first instruction in the built seed image, not its dictionary header.
For the loaded address, apply the fixed-base contract from
[Chapter 5](05-elf-and-entry.md). Offsets below were checked with
`python3 tools/check-numbers.py --dump`.

| Word | Stack effect | Code offset | Behavior | Decoded in |
|---|---|---|---|---|
| `dup` | ( n -- n n ) | `0x0C7` | Copy the top value. | [Chapter 6](06-stack-primitives.md) |
| `drop` | ( n -- ) | `0x0DE` | Discard the top value. | [Chapter 6](06-stack-primitives.md) |
| `swap` | ( a b -- b a ) | `0x0F5` | Exchange the top values. | [Chapter 6](06-stack-primitives.md) |
| `>r` | ( n -- ; R: -- n ) | `0x10D` | Move a value to the caller’s return stack. | [Chapter 6](06-stack-primitives.md) |
| `r>` | ( -- n ; R: n -- ) | `0x125` | Move a saved return-stack value to the data stack. | [Chapter 6](06-stack-primitives.md) |
| `r@` | ( -- n ; R: n -- n ) | `0x13D` | Copy the caller’s return-stack top. | [Chapter 6](06-stack-primitives.md) |
| `@` | ( addr -- v ) | `0x159` | Fetch a cell. | [Chapter 6](06-stack-primitives.md) |
| `!` | ( v addr -- ) | `0x168` | Store a cell. | [Chapter 6](06-stack-primitives.md) |
| `c@` | ( addr -- b ) | `0x188` | Fetch a byte, zero-extended. | [Chapter 6](06-stack-primitives.md) |
| `c!` | ( b addr -- ) | `0x199` | Store the low byte. | [Chapter 6](06-stack-primitives.md) |
| `+` | ( a b -- a+b ) | `0x1B7` | Return the low cell of the sum. | [Chapter 7](07-arithmetic-and-logic.md) |
| `nand` | ( a b -- bits ) | `0x1CE` | Return the cell-wide complement of a & b. | [Chapter 7](07-arithmetic-and-logic.md) |
| `0=` | ( n -- flag ) | `0x1E6` | Return an all-set flag for zero, otherwise zero. | [Chapter 7](07-arithmetic-and-logic.md) |
| `/` | ( a b -- quotient ) | `0x200` | Return the unsigned quotient; b must be nonzero. | [Chapter 7](07-arithmetic-and-logic.md) |
| `*` | ( a b -- product ) | `0x21D` | Return the low cell of the product. | [Chapter 7](07-arithmetic-and-logic.md) |
| `bye` | ( -- ) | `0x23A` | Exit with status zero; does not return. | [Chapter 8](08-seed-io.md) |
| `emit` | ( c -- ) | `0x254` | Write the low byte to stdout. | [Chapter 8](08-seed-io.md) |
| `key` | ( -- c ) | `0x28F` | Read a byte from stdin; return zero at EOF. | [Chapter 8](08-seed-io.md) |
| `syscall6` | ( a b c d e f n -- rax ) | `0x2D0` | Invoke syscall n with arguments a through f; return its raw result. | [Chapter 8](08-seed-io.md) |
| `find` | ( c-addr u -- xt &#124; 0 ) | `0x303` | Look up the address-length name; return its execution token or zero. | [Chapter 9](09-dictionary.md) |
| `here` | ( -- addr ) | `0x367` | Push the allocation cursor’s value. | [Chapter 9](09-dictionary.md) |
| `,` | ( v -- ) | `0x383` | Append a cell at HERE and advance HERE. | [Chapter 9](09-dictionary.md) |
| `execute` | ( xt -- ) | `0x3B4` | Enter the execution token; the selected word adds its own stack effect. | [Chapter 9](09-dictionary.md) |
| `state` | ( -- addr ) | `0x497` | Push the address of STATE. | [Chapter 9](09-dictionary.md) |
| `latest` | ( -- addr ) | `0x4BA` | Push the address of LATEST. | [Chapter 9](09-dictionary.md) |
| `'` | ( -- xt &#124; 0 ) | `0x4D8` | Read the next name and look it up. | [Chapter 9](09-dictionary.md) |
| `:` | ( -- ) | `0x4ED` | Read a name, create its header, and enter compile mode. | [Chapter 10](10-colon-compiler.md) |
| `;` | ( -- ) | `0x54A` | Immediate: append a return and leave compile mode. | [Chapter 10](10-colon-compiler.md) |
| `lit` | ( -- v ) | `0x5A0` | Push the cell following its compiled call and resume past it. | [Chapter 10](10-colon-compiler.md) |
| `[lit]` | ( -- n ) interpreting; ( -- ) compiling | `0x5C1` | Immediate: read unsigned decimal input; push it or compile a literal; invalid input is fatal. | [Chapter 10](10-colon-compiler.md) |
| `branch` | ( -- ) | `0x611` | Jump to the absolute address in the inline cell. | [Chapter 11](11-branches.md) |
| `0branch` | ( flag -- ) | `0x628` | Consume flag; jump on zero, otherwise resume past the inline cell. | [Chapter 11](11-branches.md) |

`R:` describes the caller’s saved data, as in
[Chapter 6](06-stack-primitives.md); balance return-stack transfers before
that caller returns. The inline operands required by `lit`, `branch`, and
`0branch` belong in compiled bodies, as in
[Chapter 10](10-colon-compiler.md) and [Chapter 11](11-branches.md).

## Internal routines

These source labels have no dictionary entries. Use the linked chapter to
find their register contracts and callers.

- `read_word` — read the next token, skipping whitespace and comments;
  [Chapter 9](09-dictionary.md).
- `read_char` — supply an input byte and a whitespace verdict;
  [Chapter 9](09-dictionary.md).
- `report_token` — print the last token followed by `?` and a newline;
  [Chapter 9](09-dictionary.md).
- `fatal_token` — report the last token and terminate with a failure status;
  [Chapter 9](09-dictionary.md).
- `compile_call` — append a native call to the supplied execution token;
  [Chapter 10](10-colon-compiler.md).
- `parse_decimal_code` — convert an unsigned decimal token and return a
  success flag; [Chapter 12](12-repl.md).
- `repl` — read names and dispatch execution or compilation;
  [Chapter 12](12-repl.md).

## Try it

Run from the `forth-bootstrap` checkout at `./forth-bootstrap`. Build the
seed:

```sh
seed/build.sh
```

Observed output:

```text
Built seed-forth (1772 bytes) using vendor/stage0-posix/bootstrap-seeds/POSIX/AMD64/hex0-seed
```

Check the `bye` entry, then use the table to follow a value through copying,
addition, and output. The shell reports the silent exit’s status; the last
literal supplies a newline.

<!-- tryit: expect "exit status: 0\nAB" -->
```sh
echo 'bye' | ./seed-forth
printf 'exit status: %s\n' "$?"
# prints "exit status: 0"
echo '[lit] 32 dup + [lit] 1 + dup emit [lit] 1 + emit [lit] 10 emit bye' | ./seed-forth
# prints "AB"
```

Observed output:

```text
exit status: 0
AB
```

## Exercise

**Trace — easy.** Use the table to predict the checkpoint’s stack after
each `dup`, `+`, and `emit`. Identify the word that consumes each decimal
token. Check your prediction against the output, then follow a decoding
link for any contract you had to look up.
