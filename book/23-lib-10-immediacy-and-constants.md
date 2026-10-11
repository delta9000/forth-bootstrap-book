# Chapter 23 — Immediacy and constants

`[lit] 90 constant zed` gives a value a callable name. Building that word requires
choosing what runs during definition and what becomes the new word's body.
The library makes that choice explicit with `immediate`, native-code emitters,
and `constant`, then uses them to compile character literals.

There are three moments to keep apart. This table is a reading model
for the definitions below:

| Moment | What runs | What it leaves behind |
|---|---|---|
| Load the library's definition of `constant` | The seed's colon compiler | A word that knows how to construct another word |
| Read `[lit] 90 constant zed` | That constructor | A dictionary entry and machine-code body for `zed` |
| Call `zed` | The newly generated body | The value 90 on the data stack |

The middle step is the new ability. The value arrives on the stack;
the name comes from the remaining input; the constructor turns both into
a callable dictionary entry. The generated body needs to preserve the
old top, push 90, and return. We will build its fixed instruction bytes
and its value field separately.

## The IMMEDIATE flag: `immediate`

The flags address is `latest @` plus the header's flags offset
(Chapter 9). The marking word at `forth-bootstrap/forth/010-lib.fth:180`
uses that address:

```forth file=forth/010-lib.fth
\ ===== immediate flag toggle =====
\ immediate ( -- )  Set the IMMEDIATE bit in the flags byte of the most-recent
\ dict entry.  An immediate word executes at compile time even when STATE=1
\ (inside : ... ;).  Mirrors the manual `01` flags byte on `;` in 000-seed.hex0.
\
\ Layout reminder: a dict entry is  link(8) flags(1) name-len(1) name(N) body.
\ `latest` is a seed primitive — it pushes the address of the LATEST sysvar
\ cell; `latest @` fetches the current dict tail pointer; `+ 8` is the
\ flags-byte address.
: immediate  latest @ [lit] 8 + [lit] 1 swap c! ;

```

`immediate` stores `1` at `latest @ + 8`. The `swap` puts the value beneath
the destination for `c!`. This overwrites the entire flags byte; it does
not merge a bit into the previous value.

Place `immediate` after the terminating `;` of the definition to mark.
It changes the newest entry, so placing another definition between them
would mark the wrong word. The marker itself is an ordinary word;
`[char]` below is the definition that receives the flag.

## Building the runtime body

The body should push the supplied value and return. Its instruction skeleton
and return emitter appear together in `forth-bootstrap/forth/010-lib.fth:191`:

```forth file=forth/010-lib.fth
\ ===== the push body: constant (and create / variable, further below) =====
\ constant is defined early so branch-xt/0branch-xt can use it: the
\ control-flow combinators below need the xts of branch/0branch, and
\ hard-coding them as numeric literals would break every time
\ 000-seed.hex0's dictionary layout changes; instead, resolve them at load
\ time via the seed's `'` (tick) primitive, captured into a constant.
\
\ A word that pushes one value has a 19-byte runtime body:
\   48 83 ED 08          sub rbp, 8       ; make data-stack room
\   48 89 7D 00          mov [rbp+0], rdi ; spill old TOS
\   48 BF <imm64>        movabs rdi, V    ; load the value as the new TOS
\   C3                   ret
\ constant, create and variable all lay it down; they differ only in V
\ and in what follows the ret.

\ ret, ( -- )  emit C3, the x86 `ret` instruction.
: ret,  [lit] 195 c, ;

```

`ret,` appends the opcode `195` (`C3`) to the future body.
Call this distinction **emit versus execute**: an emitter runs now to write
instructions that another word will execute later. `create` and
`variable` belong to Chapter 25.

The value-dependent part is the immediate operand of `movabs`.
`forth-bootstrap/forth/010-lib.fth:209` writes the fixed instruction bytes
before consuming the value with `,8`:

```forth file=forth/010-lib.fth
\ push-imm64, ( v -- )  emit the 18 bytes that push v: the body minus ret.
: push-imm64,
  [lit] 72 c, [lit] 131 c, [lit] 237 c, [lit] 8 c,         \ 48 83 ED 08  sub rbp, 8
  [lit] 72 c, [lit] 137 c, [lit] 125 c, [lit] 0 c,         \ 48 89 7D 00  mov [rbp], rdi
  [lit] 72 c, [lit] 191 c,                                 \ 48 BF        movabs rdi, ...
  ,8 ;                                                     \ imm64 = v (consumes v)

```

The input `v` stays on the stack while the fixed bytes are emitted.
The final `,8` places it directly into the instruction's operand field.
`push-imm64,` writes 18 bytes without a return; adding `ret,` gives the
19-byte runtime body. The count is the fixed instruction bytes
`4 + 4 + 2`, the eight-byte operand, and the final byte.

### `constant` and the two modes

`constant` reuses `:` (Chapter 10) for the header but supplies its own body.
The composition in `forth-bootstrap/forth/010-lib.fth:216` separates body
emission from naming:

```forth file=forth/010-lib.fth
\ push-body, ( v -- )  emit the whole 19-byte body of a word that pushes v.
: push-body,  push-imm64, ret, ;

\ constant ( v "name" -- )  define name as a word that pushes v.
\ `:` parses the name, builds the header and sets STATE=1; we emit the body
\ by hand and set STATE back to 0 (a `;` here would end constant itself).
: constant  : push-body, [lit] 0 state ! ;

```

`push-body,` combines the value emitter and the return emitter.
`constant` calls `:` to obtain the new header, calls `push-body,` with
the waiting value, and restores interpret mode with `[lit] 0 state !`.
No `here-addr` adjustment is needed: the emitters advance HERE themselves.

Here is the subtle part of the middle row in the opening table. Calling
the stored `:` reads `zed` and changes STATE, but execution continues
through the rest of `constant`. STATE governs the outer token loop;
it does not interrupt instructions already running inside a word.

The constructor must therefore finish the new body itself. `ret,`
writes its return, and the explicit store restores STATE. Writing `;`
directly in the constructor's source would have closed `constant` while the
library was loading. The completed `zed` is an ordinary word: using it
inside another definition compiles a call to its body.

## `call,`: emit a call from Forth

Character-literal compilation needs the same operation as the seed's
`compile_call`, exposed as a library word. Notice where HERE points after
the opcode store in `forth-bootstrap/forth/010-lib.fth:224`:

```forth file=forth/010-lib.fth
\ ===== call, and character literals =====

\ call, ( target -- )  Emit a 5-byte x86-64 CALL to absolute `target`
\ at HERE.  rel32 = target - (HERE + 5).  After `[lit] 232 c,` advances
\ HERE by 1, HERE points at the rel32's first byte and HERE+4 points just
\ past the 5-byte CALL — so rel32 = target - (HERE_now + 4).
\ Kept here so [char] and the control-flow combinators do not need another
\ assembler layer.
: call,
  [lit] 232 c,                 \ 0xE8 CALL opcode
  here [lit] 4 + - ,4 ;        \ rel32 = target - (HERE+4); emit 4 LE bytes
```

The input is an absolute execution address. After emitting `232` (`E8`),
HERE points at the displacement field. Adding four therefore identifies
the end of the call, and subtraction leaves `target - end` for `,4`.
The result is a five-byte CALL. Adding five at this point would count the
opcode twice and make the destination wrong.

This is emit versus execute again: `call,` consumes an address and writes
a future call; it does not call the target itself. Chapter 24 uses this
interface for control-flow combinators.

The target for a literal is available by lookup, without a fixed machine
address. `forth-bootstrap/forth/010-lib.fth:235` captures it as a constant:

```forth file=forth/010-lib.fth

\ lit-xt — the xt of the seed's `lit` primitive, which pushes the cell that
\ follows its CALL (the runtime half of [lit]).
' lit constant lit-xt

```

`' lit` leaves the execution token that `constant` embeds in `lit-xt`.
Executing `lit-xt` retrieves that address; it does not execute `lit`.
This keeps the emitter independent of the primitive's position in the seed.

## `char` and `[char]`: read now, push later

A character literal inside a definition needs two actions: read its
spelling now, then arrange for its value to appear when the word runs.
Start with the reader. The token-buffer accessor and `char` in
`forth-bootstrap/forth/010-lib.fth:240` supply the value on the current
stack, without emitting anything:

```forth file=forth/010-lib.fth
\ tib ( -- a )  the seed's token buffer, where its reader leaves the token
\ it read last.  It sits 2048 bytes below the sysvar page, which starts at
\ STATE's cell: 0x413000 - 2048 = 0x412800.
: tib  state [lit] 2048 - ;

\ char ( "tok" -- c )  read the next token and push its first byte.
\ The seed's one Forth-callable token reader is ' (tick): it reads a token
\ into the TIB and looks it up.  We drop its answer (an xt, or 0 when no word
\ has that name) and take the byte straight from the TIB.
: char  ' drop tib c@ ;

```

`tib` locates the buffer relative to `state`. `char` uses tick for its
input-reading effect and discards the lookup result, so the spelling need
not name an existing word. It returns only the token's first byte:
`char Z` and `char Zebra` both produce the character `Z`.

The immediate wrapper connects that byte to code emission in
`forth-bootstrap/forth/010-lib.fth:251`:

```forth file=forth/010-lib.fth
\ [char] ( "tok" -- )  IMMEDIATE, used inside : ... ;  Compile the next
\ token's first byte as a literal: CALL lit and the cell, the same 13 bytes
\ `[lit] N` lays down.  So `[char] ;` compiles exactly what `[lit] 59` does.
: [char]  char lit-xt call, , ;
immediate

```

While `[char]` executes, `char` leaves the character value and `lit-xt`
puts the call target above it. `call,` consumes the target; `,` consumes
the remaining character value as a full inline cell. This reproduces
`[lit]`'s CALL-to-`lit` encoding, occupying 13 bytes. The next token is
read as data, so in `: semi [char] ; emit ;` the first semicolon supplies
the character and the final semicolon closes the definition.

`[char]` has no STATE test. Its intended use is inside a definition;
in interpret mode it would still emit bytes at HERE. Use `char` when the
character is needed on the current data stack.

Some spellings disappear into whitespace or comment handling before `char`
can read them. The constants in `forth-bootstrap/forth/010-lib.fth:257`
supply those values directly:

```forth file=forth/010-lib.fth
\ Characters char cannot quote.  The reader never makes a token of
\ whitespace, and a token that is exactly \ or ( starts a comment.
[lit]  9 constant tab
[lit] 10 constant nl
[lit] 32 constant bl
[lit] 40 constant lparen                    \ (
[lit] 92 constant backslash

```

`tab`, `nl`, and `bl` name whitespace; `lparen` and `backslash` name the
comment-opening characters. Each is an ordinary constant built with the
same runtime body.

## Try it

Run this from the `forth-bootstrap` checkout at `./forth-bootstrap`, using
the seed built in Part 1. `head -n 264` loads the library through the
character constants, stopping before the control-flow combinators.

<!-- tryit: expect "ZZ\n;Z\nNA" -->
```sh
{ head -n 264 forth/010-lib.fth
  printf '%s\n' \
    '[lit] 90 constant zed zed emit : use-zed zed emit ; use-zed nl emit' \
    ': semi [char] ; emit ; semi char Z emit nl emit' \
    'here [lit] 65 push-body, here over - [lit] 19 = [lit] 79 + emit execute emit nl emit' \
    'bye'
} | ./seed-forth
# prints "ZZ\n;Z\nNA"
```

Observed output:

```text
ZZ
;Z
NA
```

`ZZ` checks a constant used directly and through a compiled call.
`;Z` checks the immediate character compiler and the interpreting reader.
The final test saves the body address, emits a standalone push body, and
compares HERE's advance with `19`. Equality yields the true flag, whose
addition to `79` prints `N`; executing the saved address then prints `A`
from the embedded value `65`.

## Exercise

**Trace (easy).** Follow `: semi [char] ; emit ;` token by token.
Which word reads each semicolon? Track the character value and the
execution token through `[char]`'s body, and explain why neither remains
on the compilation-time data stack.

<details>
<summary>Hint 1: identify who owns the next token</summary>

The REPL reads `[char]` and executes it because it is immediate. While
that word runs, the REPL is waiting. Follow `char` into tick to find who
reads the next input token.

</details>

<details>
<summary>Hint 2: distinguish the two execution tokens</summary>

Tick finds the first semicolon's execution token, but `char` drops it.
The later `lit-xt` supplies a different token: the address of `lit`.
Trace which of those addresses is merely found and which is compiled
into the new body.

</details>

<details>
<summary>Check the consumed semicolon and the closing semicolon</summary>

The REPL reads `:`; that word consumes `semi` as the name and sets STATE
to 1. The REPL next reads `[char]` and executes it. Its `char` calls tick,
which consumes the first `;` and finds its code address without executing
it. `drop` removes that lookup result; `tib c@` leaves 59, the byte for
`;`. STATE is still 1: this semicolon has been consumed as input data.

With `S` naming the older compilation-time stack, the rest of `[char]`
traces `S 59` → `S 59 xt-lit` after `lit-xt` → `S 59` after `call,`
→ `S` after `,`. The emitter writes a five-byte call to `lit` followed
by the eight-byte value 59. Neither value is left on the current stack.

The REPL resumes at `emit`, compiles its call, then reads the final `;`.
This time the REPL dispatches the semicolon itself: it appends `ret`
and resets STATE to 0. Calling `semi` later pushes 59, emits `;`, and
returns. The checkpoint above executes this exact definition and prints
`;` as the first character of its second output line.

If your trace closed the definition at the first semicolon, separate
finding a word from executing it. If it left 59 on the compile-time
stack, include the final comma's consumption of its operand.

</details>
