# Chapter 24 — Control-flow combinators

A conditional needs a destination that has not been written yet. Keeping
the address of its unfinished destination cell on the data stack lets
library words build that conditional without a new parser rule. The same
mechanism gives us loops and early returns inside colon definitions.

The checkpoint will define
`: choose if, [char] T emit else, [char] F emit then, ;`.
Its caller supplies a flag: nonzero prints `T`, zero prints `F`.
Before reading the emitters, identify the two jumps this behavior needs:

```text
test flag ──zero──> false arm ──> following code
    │                               ↑
 nonzero                            │
    └──> true arm ──jump past false──┘
```

During compilation, `if,` knows where to put the first jump but cannot
yet know where the false arm starts. At `else,`, that start becomes
known, while the end of the whole conditional is still ahead. At
`then,`, the second destination finally becomes known. We need a way
to carry each unfinished obligation until the source reaches its
destination. The data stack already gives us one.

## `branch-xt` and `0branch-xt`: a load-time snapshot

The code has a repeated shape: emit a call to a branch primitive, then
supply its destination cell. It uses the absolute inline destination and
consumed-slot contracts of [`branch`](11-branches.md#branch) and
[`0branch`](11-branches.md#0branch) (Chapter 11); the source records that
shape in `forth-bootstrap/forth/010-lib.fth:265`:

```forth file=forth/010-lib.fth
\ ===== Control-flow combinators =====
\ Compile-time helpers that emit calls to the seed's `branch` and `0branch`
\ primitives, plus inline 8-byte target slots, structured per traditional
\ Forth idiom (begin/until/again/while/repeat/if/else/then).
\
\ The seed's branch/0branch primitives work with inline 8-byte target cells.
\ Their x86 machine code is:
\     pop rax           ; rax = return address = address of inline slot
\     mov rax, [rax]    ; rax = contents of slot = branch destination
\     push rax          ; push destination as new return address
\     ret               ; "return" to destination (indirect jump)
\
\ zbranch_code is the same except it first inspects TOS (in rdi/rdx) and
\ either loads the slot (branch taken) or skips past it (fall through).
\
\ This means the combinators must emit a 5-byte CALL rel32 followed
\ immediately by an 8-byte absolute target address.  The CALL lands
\ inside branch_code / zbranch_code which pop their own return address
\ (pointing at the slot), dereference it, and jump.
\
\ The slot is thus "consumed" — it does NOT remain on the return stack.
\ backward branches simply emit the back-target cell; forward branches
\ reserve a slot, return its address as a fixup, and patch it later.
\
```

A backward destination is already known. A forward destination needs a
reserved cell whose address survives while the intervening body is compiled.
The layout comment leads into the saved primitive targets in
`forth-bootstrap/forth/010-lib.fth:289`:

```forth file=forth/010-lib.fth
\ slot-layout for a forward branch (e.g. if, ... then,):
\     E8 xx xx xx xx    ; CALL rel32 -> 0branch_code
\     <8-byte slot>     ; initially 0, patched by then, to target HERE
\ After CALL, rax -> slot; zbranch_code tests flag, either:
\   - flag==0: mov rax,[rax] -> load slot -> push -> ret to target
\   - flag!=0: add rax,8    -> skip slot -> push -> ret past slot
\
\ Names end in `,` per Forth-asm convention ("emits code") and to keep them
\ distinct from any plain runtime `if`/`then` words.
\
\ branch-xt / 0branch-xt — the xts of the seed's `branch` and `0branch`
\ primitives, captured via `'` at load time so any 000-seed.hex0 layout change
\ is automatically tracked.
' branch  constant branch-xt
' 0branch constant 0branch-xt

```

The execution tokens obtained by tick (Chapter 9) are captured when these
lines load. `branch-xt` and `0branch-xt` keep those particular targets;
a later definition with the same primitive name does not replace the saved
value. Loading the library against a changed seed captures its new addresses
without a numeric address in the library source.

During loading, the stack traces are `( ) → ( xt-branch ) → ( )` across
`' branch` and `constant branch-xt`, and `( ) → ( xt-0branch ) → ( )` across
`' 0branch` and `constant 0branch-xt`. Later, the constants supply
`( S -- S xt-branch )` and `( S -- S xt-0branch )` to an emitter.
Here and below, `S` stands for the untouched stack beneath the items shown.

## Forward branches: `if,` and `then,` as a pair

Call the pattern **emit, remember, patch**: emit a branch with an unfinished
destination, remember the destination cell's address, and patch that cell
when the destination becomes known. That remembered address is a **fixup
on the stack**. It is an address to write into, not the eventual jump target.

The conditional's body can be compiled before its end address is known
because `if,` reserves the cell first in
`forth-bootstrap/forth/010-lib.fth:305`:

```forth file=forth/010-lib.fth
\ if, ( -- fixup )  At compile time: emit `CALL 0branch` + reserved 8-byte
\ target slot.  Returns the slot's address as a fixup for `then,` or `else,`.
\ Runtime semantics: pops a flag; if flag = 0, jumps to the patched target
\ (the matching `then,`/`else,`'s HERE).  If flag is non-zero, falls through.
: if,
  0branch-xt call,
  here                         \ slot address, returned as fixup
  [lit] 0 ,                    \ reserve 8 bytes (` ,` emits a cell)
;
immediate

```

Let `F` be HERE just after the branch call. The compile-time trace follows
the emitter, not the future conditional:

| Executed by `if,` | Data stack after execution |
| --- | --- |
| entry | `S` |
| `0branch-xt` | `S xt-0branch` |
| `call,` | `S` |
| `here` | `S F` |
| `[lit] 0` | `S F 0` |
| `,` | `S F` |

The comma consumes the placeholder value, leaving `F` for the partner word.
No condition flag is needed during compilation. The future caller supplies
that flag when the emitted conditional runs.

Once compilation reaches the end of the guarded body, the destination is
HERE. The patcher in `forth-bootstrap/forth/010-lib.fth:316` writes that
address through the waiting fixup:

```forth file=forth/010-lib.fth
\ then, ( fixup -- )  Patch the fixup slot to current HERE so the matching
\ if,/while,/else, jumps here when its branch is taken.
: then,
  here swap ! ;
immediate

```

With `H` denoting the current HERE, `then,` traces
`S F → S F H → S H F → S` through `here`, `swap`, and `!`.
It emits no instruction and does not advance HERE.

In the checkpoint's `choose` definition, the literal and `emit` between
`if,` and its partner become future instructions; `F` stays on the
compilation-time stack throughout. Nested conditionals work for the same
reason: an inner `if,` leaves its fixup above the outer one, and its partner
removes the inner fixup first. Any other immediate code between partners
must preserve these waiting addresses. They have no separate type tag or
protected storage.

## `else,`: chained fixups

An alternative arm creates another unknown destination: the end of the
whole conditional. The true arm must jump over the alternative, while the
false arm must start after that jump. The implementation in
`forth-bootstrap/forth/010-lib.fth:322` replaces the old fixup with a new one:

```forth file=forth/010-lib.fth
\ else, ( fixup-if -- fixup-else )  Emit unconditional `CALL branch` + slot
\ to leap over the else-arm; patch the if-fixup to land at the start of the
\ else-arm; return the new (else-arm-end) fixup for `then,` to patch.
: else,
  branch-xt call,
  here                         \ start of new (else-end) target slot
  [lit] 0 ,                    \ reserve 8 bytes
  swap                         \ ( fixup-else fixup-if )
  here swap !                  \ patch fixup-if -> just past unconditional branch
;
immediate
```

Let `I` be the incoming if-fixup, `E` the new end-fixup, and `A` the
start of the alternative arm.

| Executed by `else,` | Data stack after execution |
| --- | --- |
| entry | `S I` |
| `branch-xt call,` | `S I` |
| `here` | `S I E` |
| `[lit] 0 ,` | `S I E` |
| `swap` | `S E I` |
| `here` | `S E I A` |
| `swap !` | `S E` |

The store patches `I` to `A`. The matching `then,` later consumes `E` and
patches it to the end of the alternative arm. These are **chained fixups**:
the unresolved obligation passes from one slot to the next, with no linked
list in memory.

Order matters. Patching `I` before emitting the unconditional branch would
send the false path into the jump that skips the alternative. Patching it
after the new destination cell puts the false path at the alternative's
first instruction. This is emit, remember, patch with an intermediate
patch point.

## Backward loops: `begin,` / `while,` / `repeat,`

A loop has a destination available before its body is compiled: the start
of the next iteration. Saving that address needs no emitted instruction,
as `forth-bootstrap/forth/010-lib.fth:333` shows:

```forth file=forth/010-lib.fth

\ begin, ( -- back-target )  Mark the top of a loop; just records HERE.
: begin,  here ;
immediate

```

`begin,` traces `( S -- S B )` through `here`, where `B` is the
back-target. Unlike a fixup, `B` is a destination to jump to, not a slot to
patch. Keeping that distinction makes the loop's stack order readable.

A conditional exit must wait for the loop's end. The implementation of
`while,` in `forth-bootstrap/forth/010-lib.fth:338` preserves `B` beneath
its new fixup:

```forth file=forth/010-lib.fth
\ while, ( back-target -- back-target fixup )  Test flag, exit loop if false.
\ Emits `CALL 0branch` + reserved slot; returns the slot addr as the loop-exit
\ fixup, leaving back-target underneath for repeat,.
: while,
  0branch-xt call,
  here [lit] 0 , ;
immediate

```

Its trace is `S B → S B xt-0branch → S B → S B F → S B F`
through `0branch-xt`, `call,`, `here`, and `[lit] 0 ,`.
This is the same emit, remember, patch pattern as `if,`, with a
back-target underneath. The runtime flag comes from the code compiled
between `begin,` and `while,`.

The loop closer must use both addresses in different ways. In
`forth-bootstrap/forth/010-lib.fth:346`, the comma writes the known
back-target and the store resolves the forward exit:

```forth file=forth/010-lib.fth
\ repeat, ( back-target fixup -- )  Emit unconditional jump back to begin-target;
\ patch the loop-exit fixup to land just past it.
: repeat,
  swap branch-xt call, ,       \ unconditional `CALL branch` + back-target cell
  here swap !                  \ patch loop-exit fixup -> just-past-repeat
;
immediate

```

| Executed by `repeat,` | Data stack after execution |
| --- | --- |
| entry | `S B F` |
| `swap` | `S F B` |
| `branch-xt call,` | `S F B` |
| `,` | `S F` |
| `here` | `S F H` |
| `swap !` | `S` |

`H` lies after the complete backward branch, including its destination
cell. The exit fixup therefore skips that branch instead of taking it.

For the checkpoint's `down`, compilation proceeds as follows:

| Source point | Compile-time stack | Meaning |
| --- | --- | --- |
| `begin,` | `S B` | Record the address before `dup`. |
| `dup` | `S B` | Compile the future condition producer. |
| `while,` | `S B F` | Reserve the exit slot. |
| `dup [lit] 48 + emit 1-` | `S B F` | Compile the body without disturbing the marks. |
| `repeat,` | `S` | Write `B` as a target and patch `F` to the following `drop`. |

At runtime, a nonzero count enters the body, prints its digit, and
decrements. When `dup` supplies a zero flag, the exit lands on `drop`,
which removes the remaining count. Putting the test before the body lets
an initially zero count skip the body entirely. The position of `while,`
determines how much work happens before each test.

## `until,` and `again,`: closing a known destination

A test at the bottom needs no forward fixup. Its false path returns to
the known back-target; its true path continues after the loop.
`forth-bootstrap/forth/010-lib.fth:354` supplies that closer:

```forth file=forth/010-lib.fth
\ until, ( back-target -- )  Pop a flag; jump back to begin, while it is 0.
\ A post-test loop: begin, BODY until, runs BODY at least once.
: until,
  0branch-xt call, , ;         \ `CALL 0branch` + back-target cell
immediate

```

`until,` traces `S B → S B xt-0branch → S B → S` through
`0branch-xt`, `call,`, and `,`. The final comma writes `B` directly into
the destination cell. In `begin, BODY until,`, BODY runs before the test
and must leave the runtime flag: false repeats, true finishes. The
checkpoint's `tail-down` tests the count after decrementing it.

Dropping the condition gives the unconditional closer in
`forth-bootstrap/forth/010-lib.fth:360`:

```forth file=forth/010-lib.fth
\ again, ( back-target -- )  Jump back to begin, unconditionally: a loop
\ that only exit, can leave.
: again,
  branch-xt call, , ;          \ `CALL branch` + back-target cell
immediate

```

`again,` traces `S B → S B xt-branch → S B → S` through
`branch-xt`, `call,`, and `,`. It consumes the compile-time back-target
without consuming a runtime flag. The source comment describes the common
case of returning from such a loop; a separately compiled forward branch
can also leave it. `again,` itself provides no exit test.

## `exit,`: early return with a clean return stack

A successful search can return from inside its loop instead of completing
another iteration. The emitter in `forth-bootstrap/forth/010-lib.fth:366`
puts the return at that point in the body:

```forth file=forth/010-lib.fth
\ exit, ( -- )  Compile a `ret`: return from the word being defined, here.
\ Every colon word is x86 code entered by CALL, so a ret anywhere in its body
\ returns to its caller.  Rule: the return stack must be as the word found
\ it, so an exit, between >r and its r> must first r> (or r> drop) what it
\ pushed.  Loops and if, keep nothing on the return stack, so they are safe.
: exit,  ret, ;
immediate

```

The compile-time trace is `( S -- S )`: `ret,` emits the return and leaves
any outstanding fixups and back-targets alone. Compilation continues past
`exit,`, so a surrounding `if,` still needs `then,`, and an enclosing
`begin,` still needs its closer. Only execution of the generated return
leaves the word early.

A clean return stack means that any values this word saved with `>r` have
been removed before the early return. Every path to `exit,` must perform
that cleanup. The combinators' compile-time marks are a separate matter:
they live on the data stack and are consumed while constructing the word.
There is no loop frame to unwind when the generated return runs.

The checkpoint's `leave-down` places `exit,` in a conditional inside a
`begin,` / `again,` loop. At compile time its marks progress
`S B`, `S B F`, `S B F`, `S B`, `S` across `begin,`, `if,`, `exit,`,
`then,`, and `again,`. At runtime the zero case returns before reaching
the back-branch. Chapter 25 uses early return in byte equality.

## Try it

Run this from the `forth-bootstrap` checkout at `./forth-bootstrap`, using
the seed built in Part 1. `head -n 373` loads the library through `exit,`
and its trailing blank line, stopping before the defining words.

<!-- tryit: expect "TF\n54321\n321\n321E" -->
```sh
{ head -n 373 forth/010-lib.fth
  printf '%s\n' \
    ': choose if, [char] T emit else, [char] F emit then, ;' \
    '[lit] 1 choose [lit] 0 choose nl emit' \
    ': down begin, dup while, dup [lit] 48 + emit 1- repeat, drop ;' \
    '[lit] 5 down [lit] 0 down nl emit' \
    ': tail-down begin, dup [lit] 48 + emit 1- dup 0= until, drop ;' \
    '[lit] 3 tail-down nl emit' \
    ': leave-down begin, dup 0= if, drop [char] E emit exit, then, dup [lit] 48 + emit 1- again, ;' \
    '[lit] 3 leave-down nl emit' \
    'bye'
} | ./seed-forth
# prints "TF\n54321\n321\n321E"
```

Observed output:

```text
TF
54321
321
321E
```

`TF` exercises both arms and their convergence. `54321` checks the
backward jump and the patched loop exit; the following zero-count call
prints nothing. `321` checks the post-test loop with a positive input.
`321E` checks the unconditional back-branch and the conditional early
return. The post-test example requires a positive starting count; it
performs its decrement before testing for zero.

## Exercise

**Trace (easy).** Follow the compile-time marks in `leave-down` from
`begin,` to `again,`. Identify which address is a destination and which
is a slot. Explain why executing `exit,` during compilation cannot remove
either mark, even though the generated return leaves the loop at runtime.

**Modify (moderate).** Change `choose` so the true arm contains another
conditional. Draw the order of its fixups before running it, then supply
flags that exercise every arm. Give each arm a distinct output character
and check that every path consumes the flags it uses.

<details>
<summary>Hint: separate emitted control flow from the current marks</summary>

For `leave-down`, write `B` for the destination saved by `begin,` and
`F` for the forward slot left by `if,`. Does `exit,` execute a return in
the word being compiled, or append one to that word's future body?
For nested `choose`, declare a stack contract first; one useful choice
is `( inner outer -- )` on every path.

</details>

<details>
<summary>Check the marks and test all paths</summary>

`leave-down`'s marks are `S B` → `S B F` → `S B F` → `S B` → `S`
after `begin,`, `if,`, `exit,`, `then,`, and `again,`. `exit,` emits a
return byte; it does not execute that byte or consume either mark.

For `( inner outer -- )`, put an inner `if,` in the outer true arm and
`drop` the unused inner flag in the outer false arm. Name the outer and
inner slots `O` and `I`. The nested fixups progress `O` → `O I` →
`O J` → `O` → `K` → empty: inner `else,` patches `I` and leaves its new
slot `J`; inner `then,` patches `J`; outer `else,` patches `O` and leaves
`K`; the last `then,` patches `K`.

Give the inner true, inner false, and outer false arms characters `A`,
`B`, and `C`. In `(inner,outer)` order, test `(1,1)`, `(0,1)`, `(1,0)`,
and `(0,0)`; predict `A`, `B`, `C`, `C`. Keep a distinct older character
beneath the two flags and emit it after each call to check stack depth,
not just branch selection. Other declared contracts are valid if their
paths and tests agree.

</details>
