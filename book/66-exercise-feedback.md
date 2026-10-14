# Appendix H — Compiler and bootstrap exercise feedback

This appendix covers the exercises in Chapters 27–56. For earlier material,
look beside the corresponding exercise for local feedback or a self-check;
[Appendix D](58-worked-exercises.md) supplies selected additional worked
examples, not a complete early answer key. Some prompts still rely on
your own trace or verification: for example, [Chapter 12](12-repl.md#exercises)
works the reordered miss path but leaves its first dispatch trace to you.

Try the chapter's exercise before opening its answer. Start with the hint;
then compare intermediate states, not only the final number. The answers
are worked out from the source. Where an exercise asks for a run, its
answer does not replace your own observed result; where it asks you to
classify recorded evidence, no new build is required. When you adapt a
checkpoint, keep its layers and setup, and update its labels and expected
results to match the changed program.

For a changed exercise, a useful self-check has three parts: what state
must survive, which transition changes it, and what observation would
distinguish the right mechanism from a plausible wrong one. If a numeric
answer matches but that explanation does not, revisit the indicated
transition before trying a different input.

## Chapter 27: allocation and patching

[Return to the exercises](27-arena-and-io-buffers.md#exercise).

**Hint.** Separate the old top, the prospective top, and bytes used since
the arena's selected base. Patching bytes is different from appending them.

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**27.1.** For a fresh arena beginning at A, requesting 16 rounds to 16,
returns A, and stores A+16 as the new top. The capacity check compares
`(A+16)-A` with the selected limit. With prior usage, the checked amount
is old usage plus 16. Rounding increments to multiples of eight preserves
the base's alignment; it cannot prove A itself is eight-byte aligned.

**27.2.** Before the test's final Boolean check, patch the existing eight
bytes with `0x0102030405060708` (decimal 72623859790382856). Check individual
bytes `08 07 06 05 04 03 02 01` in increasing address order, and check that
the output position is still 8. Preserve the test's Boolean accumulator.
A different value with eight distinguishable bytes is equally useful.
The patch API does not reserve a missing span, so emit it first.
Run the copy in place of the original test; assertions after its final
`die` are unreachable. A pass of the original test alone is not evidence
that the added patch assertions ran.

</details>

## Chapter 28: expansion and inactive text

[Return to the exercises](28-the-preprocessor.md#exercise).

**Hint.** Keep raw argument collection, argument expansion, substitution,
and replacement rescanning as separate steps. Use the legacy profile.

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**28.1.** `ROWS` is first recorded as the raw argument. Expanding it gives
`4`, with two separator blanks on each side: one pair from expanding the
argument region and another pair from expanding the ROWS replacement.
Legacy substitution adds a further blank on each side at both x markers,
giving `((   4   ) * (   4   ))`. Rescanning the function replacement adds
outer separators too. Existing source/body whitespace accounts for any
additional surrounding blanks. SQUARE produces an expression containing
two number tokens; preprocessing does not multiply them into 16.

**28.2.** With ABSENT undefined, retain `int w[1];` on original source
line 6, blank the excluded line 4, and preserve directive newlines. The
following `if` remains on line 8. ROWS is still defined, so the later
`SQUARE(ROWS)` still substitutes 4. Testing whether another name exists
does not remove an unrelated macro definition.

</details>

## Chapter 29: lookahead and replay

[Return to the exercises](29-the-lexer.md#exercise).

**Hint.** The cursor points after the current token. A pending token can
be replayed without reading any source byte.

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**29.1.** After consuming the first dot, `..` has only one dot available
to look ahead at. It therefore returns ordinary punctuation `.` (46)
without consuming that second dot. For `...`, both lookahead dots exist;
the lexer consumes them and returns `pt-ellipsis`. Consuming the second
dot before confirming the third would lose the second token of `..`
unless the lexer also implemented rollback.

**29.2.** Use `abc;`. After reading the identifier, cursor=3 and its
payload is the three-byte slice `abc`. With pending=0, mark, advance to
`;` at cursor 4, then reset. Identifier kind, payload, line, cursor 3 and
pending=0 must all return; the next advance reads `;` again. Repeat after
putback with pending=true: reset must restore true, so the first advance
replays `abc` and leaves cursor 3, while the second reads `;`. Keep the
source unchanged, and use separate buffers for nested marks. A check of
token kind alone cannot establish complete restoration.

With source bytes `abc`, newline, `;`, the saved identifier remains at
cursor 3 on line 1. Reading the punctuation consumes the newline and
reaches cursor 5 on line 2. Reset must restore cursor 3 and line 1.
A pending replay keeps that restored line and cursor; the following
advance reaches the punctuation on line 2. EOF then leaves cursor 5
and line 2 unchanged. These assertions catch a partial reset that a
one-line test would miss.

</details>

## Chapter 30: shadowed symbols

[Return to the exercise](30-types-and-symbols.md#exercise).

**Hint.** Bucket heads store symbol ID plus one; zero means no head.

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**30.1.** In the fresh test, outer x has ID 0, foo ID 1 and inner x ID 2.
For x's bucket, logical heads change `0 → 2 → 0`; encoded heads change
`1 → 3 → 1`. Inner x links to ID 0. Scope exit lowers the count from 3 to
2 and unlinks inner x, restoring the older head. Merely lowering the
count leaves a bucket pointing at a discarded row that can later be
reused. The invariant is that every reachable hash row is still live.

</details>

## Chapter 31: relative displacements

[Return to the exercises](31-elf-and-codegen-part-1.md#exercise).

**Hint.** A rel32 displacement is relative to the byte after its four-byte
field, not to the opcode or the start of the file.

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**31.1.** The header ends at offset 120. The first immediate adds 7,
the move to RAX adds 3, and the second immediate adds 7, placing JMP at
137 and its displacement field at 138. The field ends at 142. Skipping
the following seven-byte load reaches 149, so the displacement is
`149-(138+4)=7`: bytes `e9 07 00 00 00`.

**31.2.** Slot 15 is at displacement −128 and uses `48 8b 7d 80`, four
bytes. Replacing only the skipped load makes the target 146 and rel32=4.
Slot 16 is at −136 and uses `48 8b bd 78 ff ff ff`, seven bytes; target
149 and rel32=7. Both loads stay unreachable, so they require no live
RBP frame and the program still exits 42. Executing either would be a
different, invalid experiment without first constructing that frame.

</details>

## Chapter 32: fixup lists and shim limits

[Return to the exercises](32-codegen-part-2.md#exercise).

**Hint.** Node addresses, output-field offsets and target virtual addresses
are three different quantities.

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**32.1.** The first call creates N1=`{P1,0}` and head=N1. The second creates
N2=`{P2,N1}` and head=N2. Walking N2 then N1 writes
`target-(patch+4)` independently at each site. In this checkpoint the
fields are at 128 and 140, and the shim begins at offset 161, so the
displacements are 29 and 17 respectively. Patching does not advance the
output position; both calculations retain the same target. Arena node
addresses need not be fixed numeric constants, and reversing traversal
order would not change the patched result.

**32.2.** The minimal emitted fopen shim examines only the first mode
byte. Both `rb` and `r+` therefore choose read-only flags zero. Ignoring
`b` adds no text/binary distinction here; ignoring `+` loses the requested
read/write behavior. Do not substitute Chapter 43's separate source-built
FILE implementation for the shim being examined.

</details>

## Chapter 33: folds and short-circuit joins

[Return to the exercises](33-expressions-part-1.md#exercise).

**Hint.** Ask which parser reads the right operand, and which Boolean
result the enclosing operator tests.

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**33.1.** The additive loop saves a, parses b at multiplicative precedence,
and emits a−b. That tighter parser leaves the next minus for the additive
loop's next iteration, which computes `(a−b)−c`. With 10,3,2 this is 5;
parsing the entire remaining additive expression on the right would give
9 instead. [Appendix D](58-worked-exercises.md) gives the fuller loop trace.

**33.2.** `a && b || c` groups as `(a && b) || c`.

| Condition reached | What is skipped? | What must run next? |
|---|---|---|
| a is false | b | c, because the conjunction is false |
| a true, b false | Nothing in the conjunction | c |
| a true, b true | c | Join with true result |

The final value is normalized to integer 0 or 1. A branch that skips both
b and c when a is false confuses the AND's false join with the OR's true
join.

</details>

## Chapter 34: an address through parentheses

[Return to the exercises](34-expressions-part-2.md#exercise).

**Hint.** Parentheses group an expression; they need not fetch the object
it denotes. Distinguish postfix's returned value from its stored value.
For the assignment chain, follow the recursive call before applying the
saved `+=`; for each grouped case, inspect the inner expression's final kind.

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**34.1.** Assume p points to writable character storage. Unary `*` first
materializes p to get the pointer, then records a pending byte dereference
with that address in RDI. Grouping preserves this lvalue metadata. Postfix
`++` saves the address, loads the old byte, preserves that old value,
increments and stores the byte, then returns the old value. For a byte
initially 5, storage becomes 6 and the expression yields 5. p itself does
not change; `*p++` groups differently and increments p.

**34.2.** `(-3>0)?7:9` chooses 9 under this core signed-comparison path.
Change the source token, displayed expression/label and wrapper's expected
status from 7 to 9.
Literal arms check selection, but cannot alone establish that side effects
in an unselected arm would be skipped.

**34.3.** `a += b = 7` groups as `a += (b = 7)`. The outer call saves
`a`'s slot and the `+=` operator on the compiler return stack and emits
a push of `a`'s old value. The inner call emits the store of 7 into `b`
and supplies 7 to the outer operation. At runtime, that operation adds
the saved 1 to 7, stores 8 into `a`, and supplies 8 as the expression
value: `a=8`, `b=7`, result 8.

`(a) = b` retains `a`'s local slot: it stores 2 into `a`, leaves `b=2`,
and yields 2. In `(a += b) = 7`, the inner compound assignment finishes
as `lv-value`. Parentheses preserve that kind, so the outer assignment
fails with compiler error 120. There is no runtime result or executed
store from this failed compilation.

If the first answer is 7, check whether the old left value was discarded
as though `+=` were `=`. If the rejected case is said to change `a` to 3,
separate code emission from later execution, then trace where compilation
stops. Keep destination metadata, saved runtime contents, and the inner
assignment's returned value distinct.

</details>

## Chapter 35: descriptor identity and observable casts

[Return to the exercises](35-declarations-types-globals.md#exercise).

**Hint.** An incomplete descriptor can already have a stable address.
For a cast test, make the conversion visible before shell status truncation.

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**35.1.** Allocate and register T's initially empty descriptor before
parsing members. Lookup for `struct T *next` now retrieves that same
descriptor address. Completing T fills it in place, so next continues to
refer to the completed shape. A genuinely unknown tag in this core soft
lookup yields zero; it is not a deferred identity repaired by a later
definition. This answer concerns the displayed core parser.

**35.2.** Core character conversion retains `321 mod 256 = 65`.
Consequently `(char)321 == 321` is false and yields status 0. Omitting the
conversion would incorrectly make that comparison true. Merely returning
321 or 65 would yield shell status 65 in both cases, hiding the error.
Update the printed comparison from `==65` to `==321` and the wrapper's
expected status from 1 to 0 too.

</details>

## Chapter 36: leaving the right construct

[Return to the exercises](36-statements-if-while-for-return.md#exercise).

**Hint.** In this `for` loop, `continue` targets the step, while `break` targets the
nearest enclosing breakable construct. A jump can bypass saved-state cleanup.

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**36.1.** The continue at i=2 is patched to the step: it increments to 3
and tests again. The break at i=5 is patched after the loop. Contributions
are `0+1+3+4=8`. Patching continue to exit would stop at 2 with sum 1;
patching break to the step would fail to leave at 5.

**36.2.** Replace only the continue test by
`switch(i){case 2:continue;}`, keeping the i=5 break outside the switch.
At i=2, restore the switch's saved RBX before jumping to the enclosing
loop step, since the normal switch epilogue will not execute. Other cases
leave the switch normally. Sum remains 8. If retaining the single-token
Forth `s,` construction, represent required whitespace with `/**/`, as in
`case/**/2:`. Moving the break inside the switch would change its target
and would test a different program.

</details>

## Chapter 37: resolving a function

[Return to the exercises](37-functions-and-scope.md#exercise).

**Hint.** A newer symbol can shadow a prototype without erasing fixup
nodes already attached to the older row.

For the argument test, make the two positions contribute differently.
The last argument pushed is the first value popped, but it is not the
first parameter.

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**37.1.** The prototype creates a persistent add symbol with no body
address. The call in main emits a rel32 placeholder and records its node
on that symbol's call list. When the definition receives an address, the
parser patches and clears the prior row's list. It installs the function
symbol before opening the parameter/body scope, so scope exit removes
locals while preserving the function definition. Earlier builtin entries
mean its absolute symbol ID is not a useful fixed answer.

**37.2.** Keeping the prototype but moving add's definition before main
makes the call find a known body address. It can emit the call immediately
instead of queuing an unresolved site. The result is still `4+3=7`.
Same result, different resolution path, is the intended comparison.

**37.3.** With `10*a+b`, predict 34 for `(3,4)` and 43 for `(4,3)`.
Both stay the same when the definition moves before `main`; only the
call-resolution path changes. For `(3,4)`, the emitted pushes save 3 then
4; the pops put 4 in `rsi`, then 3 in `rdi`. The parameter spills give
`a` the first register's value in slot 0 and `b` the second in slot 1.
An observable reversal would exchange the two results. Addition would
return 7 for both orders and hide it.

Record all four compiler/program results and explain why the chosen
input distinguishes the proposed mistake. The four programs return the
predicted statuses at this source pin. They cover this scalar two-argument
path; they neither establish full ABI correctness nor exclude mutually
cancelling caller/callee mistakes. A wrong result calls for tracing the
transfer and calculation, rather than immediately blaming one emitter.
If the order is unclear, sketch the stack with 4 on top before the pops,
then label each destination register and local slot.

</details>

## Chapter 38: handoff and Stage A evidence

[Return to the exercises](38-main-and-bootstrap-chain.md#exercise).

**Hint.** Locate the token that executes the compiler, then name the exact
two artifacts Stage A compares.

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**38.1.** The final bare Forth token `cc-main`, not its defining occurrence
after `:`, triggers the handoff. Its first operation, `cc-load-stdin`,
reads the remaining stream as C. Appending a Forth definition there puts
it in C input; it does not install a new Forth word and will generally
cause a C parse error.

**38.2.** Retain the Stage A result directory using the checkpoint's
documented retention method, then compare `self-v1-amd64.M1` with
`self-ref-amd64.M1`. The criterion is identical M1 bytes for the same
input/options. The two M2-Planet executables may use different instructions
or layouts. Neither their executable-byte equality nor general compiler
correctness follows from this one compilation. A completed answer includes
the actual comparison result and identifies the retained artifacts; the
names alone are not execution evidence.

</details>

## Chapter 39: object layout and initializer timing

[Return to the exercises](39-lp64-storage-and-initializers.md#exercise).

**Hint.** First align the next field's start, then round the completed
record's extent to its maximum alignment.

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**39.1.** tag occupies offset 0, size 1. value requires alignment 8, so
its offset is 8 after seven padding bytes. It ends at 16; final rounding
to maximum alignment 8 leaves size 16. These are object byte offsets,
not parameter-slot indices.

With the declarations reversed, `value` starts at 0 and `tag` at 8.
The final field ends at byte 9; rounding to alignment 8 still gives size
16. Adjacent array elements are 16 bytes apart, keeping both `value`
fields aligned. Reverse the initializer too, to `{7, 3}`, so the values
stay the same. The checkpoint still prints `LP64` plus newline and
returns `8 + 6 + 16 + 3 + 7 = 40`. Nine is the end of the last field,
not the completed record size.

**39.2.** Move the ordinary, non-static declarations and their initializers
into main. Predicted output remains `LP64` plus newline and status
`8+6+16+3+7=40`. Automatic arrays/aggregates receive inline initialization,
including zero-fill before explicit leaves. Their initializers no longer
belong to the pre-main static initialization queue. Adding `static` would
change the storage/lifetime question rather than perform this move.

</details>

## Chapter 40: identity versus serialization

[Return to the exercises](40-objects-and-relocations.md#exercise).

**Hint.** A relocation stores the API's stable handle until output order
is known. BSS describes memory extent without supplying payload bytes.

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**40.1.** Handles are caller=1, external=2, local value=3. Locals-first ELF
serialization puts null at 0, value at 1, caller at 2, external at 3.
The relocation retains handle 2, consults external's original row, and
emits its final ELF index 3. Using the handle itself as the ELF index would
refer to caller instead.

**40.2.** Reserving N positive BSS bytes without adding symbols, names,
relocations or extra alignment increases the NOBITS section's memory
size by N. It adds no N-byte payload; only an existing section-header
field changes, so serialized file length stays unchanged. If you also
add a symbol or name, metadata can increase file size. Keep that separate
from BSS payload when interpreting your measurement.

For example, inserting
`cc-obj-bss cc-obj-use [lit] 37 cc-obj-reserve drop` before the write
changes `.bss` from zero to 37 bytes (hexadecimal `25`). In the pinned
checkpoint, both files measure 944 bytes. Print the byte count inside
each block before cleanup; a missing file after the block ends reflects
its temporary-file lifecycle, not the object writer's result.

</details>

## Chapter 41: stack arguments and nested lifetimes

[Return to the exercises](41-system-v-calls.md#exercise).

**Hint.** Draw the stack at three moments: before call, after call's
return-address push, and after the callee saves RBP.

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**41.1.** `&base` and 1–5 use RDI, RSI, RDX, RCX, R8, R9. Values 6 and 7
are outgoing `[rsp+0]` and `[rsp+8]`. At callee entry they are +8 and +16;
after `push rbp; mov rbp,rsp` they are `[rbp+16]` and `[rbp+24]`. Saved
RBP is +0 and the return address +8. Padding follows the outgoing arguments
and cannot shift the first stack argument's position.

**41.2.** Replacing only the final argument gives
`add(&base,1,2,3,4,5,6,add(&base,1,2,3,4,5,6,7))`.
The inner call returns 42. With base=14 the outer result is
`14+1+2+3+4+5+6+42=77`. Its seven earlier argument cells must survive the
inner call's staging and outgoing block. The live-save protocol protects
that span in frame storage and restores it afterward. Update output labels
and expected status to 77. Explain why those seven cells survive; the
returned value alone does not show which mechanism preserved them.

</details>

## Chapter 42: archive demand is time-dependent

[Return to the exercises](42-linker-and-archives.md#exercise).

**Hint.** List unresolved strong names at the moment the archive is visited.
For the relocation trace, locate the first byte after `E8`: that is `P`.
Apply `S + A - P` with `A=-4` to the call, and `S + 0` to the pointer.
Change only the quantities the question moves.

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**42.1.** Before caller.o is added, no current strong unresolved `add`
selects the archive member. Adding caller afterward creates that demand,
but the completed archive visit is not automatically repeated. A second
archive occurrence after caller now selects the member defining add.
Startup's main reference is satisfied by caller; add is the relevant
remaining demand. This assumes the checkpoint's other inputs stay fixed.

**42.2.** The opcode is now `0x401010`, so `P=0x401011`.
The displacement is `0x401020 - 4 - 0x401011 = 0x0B`; the field contains
`0B 00 00 00`. The CPU continues from `0x401015` and adds 11 to reach
`0x401020`. The absolute pointer remains `0x401020`, because its target
did not move. A whole-image move changes both `S` and `P`, cancelling in
the relative expression, but still changes absolute pointer values.
Thus one unchanged call does not establish whole-image position independence.

A displacement of `0x1B` incorrectly applies whole-image invariance when
only the caller moved. `0x0F` loses the addend; subtracting four again
from `0x0B` applies it twice. Moving the pointer's value by 16 confuses
its target with the call field. In the second prediction, the target
becomes `0x401030`: the call displacement returns to `0x1B`, and the
pointer must now hold `0x401030`. These are manual layout derivations.

</details>

## Chapter 43: realloc and ownership

[Return to the exercise](43-runtime-and-libc.md#exercise).

**Hint.** At which line does ownership of the old allocation end?

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**43.1.** If the replacement allocation fails, realloc returns NULL before
copying or freeing. The original pointer and contents remain valid.
Freeing first would invalidate them; copying first would write through a
NULL destination. The caller should keep the old pointer until a temporary
holding realloc's result is known non-NULL. Assigning the result directly
over the sole old pointer can lose the only ownership handle on failure.

</details>

## Chapter 44: defined is different from true

[Return to the exercise](44-target-headers.md#exercise).

**Hint.** `#ifdef` asks about the table entry; `#if` evaluates replacement text.

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**44.1.** The 15-character name `__STDC_HOSTED__` exists with one-character
replacement `0`. Therefore `#ifdef __STDC_HOSTED__` succeeds and
`#if __STDC_HOSTED__` is false. The checkpoint separately rejects absence
and a nonzero value. A present zero correctly advertises the selected
freestanding target.

</details>

## Chapter 45: typed intermediate values and dead arms

[Return to the exercises](45-typed-constants.md#exercise).

**Hint.** Normalize to the expression's type after each operation, before
using its result in a comparison.

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**45.1.** Both `0xffffffffU` and `2U` are 32-bit unsigned int. Their sum
4294967297 reduces modulo `2^32` to 1. Thus `(0xffffffffU+2U)<2U` is true.
Keeping the Forth cell's wider sum until storage would incorrectly make
that comparison false. Other comparisons that expose the same distinction
are valid; equality with 2 would not distinguish these two implementations.

**45.2.** Use `1 ? sizeof(long)*3+(1<<4) : 1/0` for the initializer.
The selected value remains 40; the other probes remain 29 and 0. The wrap
probe returns success zero after checking its typed result internally. Skip
state causes the dead binary division to bypass evaluation while its syntax is
still parsed. Changing the condition to 0 selects division, reaches the
zero-divisor check: the pinned exercise run reports `cc: line 1: error 124`
and exits with status 124. The compilation guard stops the block before
linking or running, so no `x`, `pointer`, or `wrap` result lines appear.
That is the expected rejection for this version, not a failed executable
run. This tests integer binary evaluation. It does not
establish that later floating casts suppress every range diagnostic in
dead arms; Chapter 47 names that separate boundary.

</details>

## Chapter 46: a varargs cursor crosses banks

[Return to the exercises](46-varargs.md#exercise).

**Hint.** Track both GP offset and overflow pointer even when only one moves.

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**46.1.** After named n, GP offset is 8 and the overflow pointer addresses
unnamed value 6. FP offset stays 48 throughout this integer-only probe.

| Retrieval | Source | GP offset afterward | Overflow movement |
|---|---|---:|---|
| 1–5 | Register-save offsets 8,16,24,32,40 | 16,24,32,40,48 | None |
| 6 | First stack value | 48 | +8 |
| 7 | Next stack value | 48 | Another +8 |
| 8 | Next stack value | 48 | Another +8 |

The first retrieval leaving GP offset unchanged is number 6, or zero-based
loop index 5. Sum is 36. This does not test floating-register retrieval.

**46.2.** Consuming 1–6 gives prefix total 21, GP offset 48 and overflow
already past value 6. Copying the list copies cursor fields, not argument
bytes. Each list can independently read 7,8 for suffix total 15. Adding
that suffix to a separately retained prefix gives full total 36 for each.
One accumulator that deliberately adds both suffix traversals instead gives
51; that is a different tally, not a cursor defect. End both lists. If the
program returns a changed tally, update its shell guard; alternatively,
check cursor independence internally and keep return 36.

</details>

## Chapter 47: exact halfway rounding

[Return to the exercises](47-floats.md#exercise).

**Hint.** At a tie both adjacent values are equally near; inspect the low
bit of the retained significand, not the decimal spelling's last digit.

**Comparison hint.** Start from the unordered row. ZF alone cannot
distinguish it from equality; PF supplies the missing distinction.

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**47.1.** Compare twice the exact remainder with the denominator. Smaller
means keep q, larger means increment. At equality increment only if q is
odd, making q+1 even; an already even q stays. A carry can then require
an exponent adjustment. This is nearest-even rounding from exact division.

**47.2.** The decimal ending in `03125` is exactly `1+2^-53`, halfway
between 1 and `1+2^-52`. Unity has integer significand `2^52`, which is
even, so the rounded value is 1.0, encoded as `0x3ff0000000000000`,
decimal 4607182418800017408. Change the C bit comparison
and printed/expected bit-pattern labels to that encoding. The comparison
still returns Boolean 1, so its numeric shell guard remains 1. The addition,
comparison and unsigned-rounding probes remain 30, 1 and 1 respectively.

**47.3.** With the quiet NaN, `q <= x` yields 0 but `!(q > x)` yields 1.
Unordered gives ZF=1, PF=1, CF=1. The raw less-or-equal test sees CF-or-ZF
and produces 1, but the PF-clear mask removes it. Greater-than requires
CF and ZF both clear, so it produces 0; logical negation then produces 1.
For 1.0 and 2.0, ZF=0, PF=0, CF=1: less-or-equal survives the orderedness
mask, and greater-than is false, so both expressions yield 1.
The finite example alone would miss the bad rewrite. Unorderedness is a
fourth comparison outcome, so “not greater” need not mean “less or equal.”
This is runtime reasoning; the chapter's separate constant-operation
boundary still applies.

</details>

## Chapter 48: preserve neighboring fields

[Return to the exercises](48-bitfields.md#exercise).

**Hint.** Work in bit offsets inside the storage unit before applying
record alignment.

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**48.1.** low's three bits start at shift 0, delta's five at shift 3,
and high's four at shift 8, all at containing-byte offset 0. The cursor
ends at bit 12, giving two raw bytes and size 4 after alignment. delta's
sign bit is unit bit 7. Replacing low masks bits 0–2 only and preserves
that sign. Initial low 12 bits `0x9ed` become `0x9ea` when low becomes 2.

**48.2.** For a concrete five-bit signed value choose −4, within −16…15.
Insert `flags.delta=-4;` after the existing checks of initialization and
the low-field update, then verify low=2, delta=−4, high=9. The low 12 bits
become `0x9e2`. Returned-value probes should report 2,−4,9,4; raw status 252
is decoded to −4. Update the wrapper's delta expectation. Inserting the
assignment before an old −3 guard instead requires changing that guard
as well. Either placement is valid if all checks describe the program
being tested. The restricted checkpoint uses returned-value probes rather
than a printf runtime.

</details>

## Chapter 49: whole-record decisions

[Return to the exercises](49-aggregate-abi.md#exercise).

**Hint.** Classify the whole record before committing register consumption.
An argument copy is not the caller's original object. For the pointer-field
trace, draw two 16-byte records and one separate `long` object; keep the
pointer field and the pointed-to object as different storage locations.

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**49.1.** Pair occupies two INTEGER eightbytes, passed in RDI/RSI.
The independent SSE bank carries delta in XMM0. The caller snapshots the
original bytes, the callee reconstructs and modifies its own p, and the
returned Pair uses RAX/RDX. The caller captures that result before assigning
answer. Original stays `{20,30}` and answer becomes `{23,32}`. No hidden
MEMORY-result pointer is needed for this Pair. Temporary frame slot numbers
are implementation choices, not fixed ABI offsets.

**49.2.** Removing `e` leaves four leading integers in RDI, RSI, RDX, and
RCX. Pair now fits entirely in the two remaining GP registers, R8 and R9.
The following `tail` has no GP register left, so it travels on the stack.
The sum changes from 72 to 67: `1 + 2 + 3 + 4 + 20 + 30 + 7`.
Remove `e` from the definition's checks and addition, remove its parameter
from both signatures, and remove `5` from the call before changing the
expected result. With five leading integers, the pair did not consume
the last register because it could not fit there in full; removing one
integer makes the pair consume two registers and pushes the tail out.
Two sides compiled by this compiler check self-consistency; an independent
host-compiled peer in both directions would test interoperability more strongly.

**49.3.** The results are `10`, `40`, `&target`, and `30`. This `Parcel`
is 16 bytes: `inside[0]` is the first INTEGER eightbyte, passed in RDI;
the copied pointer is the second, passed in RSI. The callee reconstructs
a distinct record. Its array element becomes 30 while the caller's stays
10. Both pointer fields initially hold `&target`, so `*p.shared = 40`
writes to the separate caller object. `p.shared = 0` changes only the
callee's pointer field; it neither changes `original.shared` nor reverses
the completed store.

Leaving `target` unchanged would confuse copying a pointer with copying
its pointee. Changing the original array to 30 would treat the record
call as though an array pointer had been passed instead. Mark the byte
range copied for the argument, then locate each assignment's destination.

</details>

## Chapter 50: which stream contains C?

[Return to the exercise](50-seed-cc-fixed-point.md#exercise).

**Hint.** Distinguish source bytes in a child stream from objects named by
commands in that stream.

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**50.1.** Each compile-unit child receives Forth library/compiler layers,
a unit driver, then one C translation unit. Runtime units use runtime-unit;
tool units use tools-unit. The driver's final invocation consumes the C tail.
Archive children instead receive Forth linker/archive layers, an archive
head, generated object-add commands and an archive tail. Link children
receive Forth layers and a link driver. Those streams contain Forth only;
referenced object bytes are data loaded by commands, not appended C source.

Adding `start.o` directly introduces its reference to `main`.
The supplied tool object satisfies that reference before archive search.
If startup appears only in the archive, nothing requests `_start`, so
the linker leaves its member unselected. Recording `_start` as the entry
name does not create an unresolved reference; the final entry lookup can
therefore fail even though the tool object defines `main`. In a different
link where `main` itself lives in an archive, adding startup directly also
creates the demand that selects `main`'s member. Track the unresolved
names at each archive visit to distinguish these cases.

</details>

## Chapter 51: bootstrap a generator

[Return to the exercise](51-owning-the-tools.md#exercise).

**Hint.** Building an executable and executing it are different make targets.

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**51.1.** `scan.c` is the first scanner target that runs the recipe-built
generator, using `./flex-tmp scan.l`. The dependency chain is
scan.lex.l → scan-ascii.l → heirloom-scan.c → scan-tmp.c → scan-tmp.o →
flex-tmp → scan.c → scan.o → installed flex. lexer-prepare performs the
preparation steps; Heirloom lex produces heirloom-scan.c; oyacc supplies
the parser inputs beside this chain, and linking uses Heirloom's libl.a.
The flex-tmp target links the temporary program but does not run it.
Removing lex after deleting shipped generated C leaves the temporary
scanner C absent. A compiler that can compile C cannot replace its missing
generator. Assume a clean build, not stale generated files.

</details>

## Chapter 52: the comparison relation

[Return to the exercise](52-gcc-4-fixed-point.md#exercise).

**Hint.** Read both the per-file comparison and the final path-list check.

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**52.1.** A missing installed header fails the path-list comparison even
if the count of differing common-file contents is zero. A changed archive
timestamp alone is accepted when ordered member names and extracted member
bytes still match. Reordering distinguishable members fails the ordered
`ar t` comparison. Changing an object's bytes fails the corresponding
`ar p` comparison. These answers assume readable corresponding archives
with simple, unique member names; they do not prove behavior for duplicate names or make
an invisible exchange of byte-identical members observable.

</details>

## Chapter 53: attempts, successful execution and provenance

[Return to the exercises](53-sealed-run.md#exercise).

**Hint.** Join an unfinished execve with its resumed record by PID before
classifying it. Resolve a path in the traced process's root, not your shell's.

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**53.1.** Changing the resumed result to `-1 ENOENT` predicts these lines,
in this order:

```text
ok /hex0-seed
fail /usr/bin/arch
fail /build-out/plumbing/bin/bash
```

The unfinished call stores PID 102's path without emitting a verdict.
PID 103's complete failure is emitted first; resuming 102 retrieves and
removes its stored path, then emits its failure. Counting only literal
`execve(` lines either misclassifies the unfinished attempt or loses the
successful/failed result carried by the resumed line. There is one success
and two failures in this changed example.

With the resumed line removed, only `ok /hex0-seed` and
`fail /usr/bin/arch` are emitted, in that order. PID 102's unfinished
record leaves a pending bash path; nothing consumes it or reports a result.
The awk command still exits successfully. That status says the filter ran,
not that the trace is complete. Bash's absence from both lists does not
establish either success or failure. Retain the unfinished record and seek
its missing continuation; if it is unavailable, record the outcome as
unknown rather than inventing a verdict.

**53.2.** One recorded candidate is
`//build-out/chain/stage-c/toolchain/as`. Under the prepared Linux root it
resolves to `/build-out/chain/stage-c/toolchain/as`; with the default host
root, its backing path is
`build-out/plumbing-root/build-out/chain/stage-c/toolchain/as`.
Stage C's input step copies the verified Stage B `gas/as-new` artifact to
toolchain/as. The earlier binutils recipe built that assembler with
seed-cc and the chain's generated parser/scanner inputs.

To complete your own verification, retain the completed root and raw
execve record, establish result 0 and the root mount, and connect the actual
file to its producing/copy step and report hash. For a relative path, also
establish the process's cwd. A failed `/usr/bin/arch` attempt is not evidence
that arch executed. The chapter's raw ENOENT record explains that instance;
a generic failed-row summary alone cannot distinguish absence from permission
or executable-format failures.

</details>

## Chapter 54: carrying a generated runner into K1

[Return to the exercises](54-k0-and-k1.md#exercise).

**Hint.** Identify each artifact's producer separately from the image that
supplies its source or recipe.

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**54.1.** The host-prepared K0 boot image supplies the launcher and source
inputs. The launcher builds `build-out/amd64-runner` under K0, marks it
executable and uses it to build K1. On the normal disk-present path, K1
imports hda as its root, then imports K0's filesystem under `/k0`. That
carries the generated runner to `/k0/build-out/amd64-runner`. hda supplies
`/k1.args` and `/k1.recipe`; the arguments name the runner, `--recipe`, and
that recipe. Importing only hda supplies the recipe but not the K0-built
executable. The boot image supplies inputs to its construction, not a
prebuilt copy of the final runner.

**54.2.** In a fresh smoke run, locate the seed-cc compile of direct-smoke.c
to direct-smoke.o, the seed-ar `rcs` creation of libsmoke.a from that object,
and the static seed-cc link using `-Lbuild-out/k1-smoke -lsmoke`. The link
has no explicit application object: startup's unresolved main selects the
archive member.

The program's “all 26 checks passed” means its assertions completed. The
guest recipe's `k1: PASS` also follows its checked kaem invocation, including
later mkdir and sha256sum work. The host's `run-chain: PASS (--direct-smoke)`
requires the expected QEMU debug-exit status 1 and both required guest
markers. Neither the program message nor QEMU status alone proves the
whole sequence. Experimental completion requires your serial log at
`build-out/k1-direct-smoke/serial.log` and corresponding host result;
these answer descriptions are not a substitute for them.

</details>

## Chapter 55: producing bytes versus transferring control

[Return to the exercises](55-linux-and-kexec.md#exercise).

**Hint.** Mark each step as production, copying, machine-state preparation,
or control transfer. Then bound what each success message can establish.
For the compiler question, separate the incoming `CC`/`CXX` settings
from the requested output languages.

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**55.1.** The Linux stage builds static init and its initramfs list, sets
INITRAMFS_SOURCE, builds bzImage and copies it to `/build-out/linux`.
finish exports selected trees to hdb, copies bzImage to `/boot`, writes
the command line and executes kexec. Those operations preserve or produce
files; none is the kernel jump. kexec requests K1's reboot operation with
command `0x45584543`, which enters the Linux loader rather than firmware
reboot or ordinary ELF exec.

The loader validates the image, finds the protected payload at
`(setup_sects+1)*512`, reserves at least its declared init_size and payload
length, with minimum 2 MiB alignment and a minimum 16 MiB preferred-address
floor, and copies that payload. It prepares boot parameters, e820 and
command-line data, an optional external initrd, and identity mappings while
retaining the direct map needed by its current stack. The final jump disables
interrupts, replaces CR3, clears EBP/EDI and jumps to `load+0x200` with RSI
pointing to boot parameters. That is the transfer of control; subsequent
Linux output shows that the successor executed. An embedded initramfs belongs
to the kernel image, so the absence of optional `/boot/initrd.cpio` does
not remove the embedded init.

**55.2.** Each observation has a narrower conclusion than “the chain works”:

| Observation | Failure it rules out at that boundary | Failure still possible |
|---|---|---|
| Archive SHA-256 matches its expected digest | Byte divergence from those expected input bytes, under the hash assumption | Flawed source or later miscompilation |
| One gcc64 artifact matches its applicable pin | Divergence of that checked artifact | Another missing/wrong artifact or failed boot |
| finish reports export | Under the shown checked flow, tar failed before that marker | Bad readback or failure of the later handoff |
| Linux prints its version | Failure to begin Linux execution and reach that print | Failure to start init or a later panic |
| Init prints its greeting | Failure to execute init up to its greeting | Later failure, including the following proc-version read |

A root-scoped pin needs the corresponding root. A skipped check is not a
match, one pin is not all pins, and an export marker is not a readback.
Accept other accurate failure pairs if they respect the same evidence boundary.

**55.3.** Stage 8 invokes `$W/g47/bin/g++` on `cxx-test.cc`; the proposed
C-only output cannot supply that compiler. Stage 10 also passes
`$W/g47/bin/g++` as the second argument to `build-gcc10.sh`, which uses
it as the incoming `CXX`. In the actual intermediate build, `CXX=false`
concerns the incoming configuration environment, while
`--enable-languages=c,c++` selects the produced front ends. Confusing
those roles would make the language bridge appear circular. This is a
source-derived prediction, not an observed failed build.

</details>

## Chapter 56: plan a port without inheriting its measurements

[Return to the exercise](56-gcc-15-epilogue.md#exercise).

**Hint.** Make three lists: usable predecessor inputs, changes to integrate,
and results that only a new guest run can establish. Use the external
recipe snapshot identified by the chapter; mutable upstream contents are
not interchangeable evidence.

<details>
<summary>Check your reasoning: solutions and evaluation criteria</summary>

**56.1.** A complete plan preserves the direct bootstrap route and its
existing GCC 10.5/binutils/musl/tool prerequisites, then adds the GCC 15
source archive and matching input pins, final build/verification recipes,
guest input inventory and stage selection. Audit compatibility patches
and required C/C++ test sources rather than assuming an external host
recipe can be copied unchanged. Keep the gcc64 verification stage distinct
from the ladder's Linux-building stage. Invoke the new work before export.

Map each proposed success claim to evidence that would actually survive
export:

- Input integrity: exact recipe/source revisions, reconciled pin declarations,
  complete input inventory and successful checks, without missing-input skips.
- Compiler bootstrap comparison: its log, configuration and required
  stage-two/stage-three comparison result, not merely installation success.
- Usable C/C++ compiler: test sources/options, outputs and exit results.
- Correct toolchain paths: sysroot, assembler/linker and program-search
  reports; include path-audit files even if they live outside the default
  exported logs directory.
- Output repeatability: appropriately scoped new output pins, the actual
  comparison result and the selected produced artifacts or a retained set.
- Feasibility under K1: newly measured elapsed/phase time, peak memory and
  storage, with measurement method and retained logs.

Historical output digests supply expected values; they do not establish
that a guest produced or checked any output. Root, configuration or input
changes can legitimately change bytes. Even a real matching hash remains
separate from bootstrap comparison, executing test programs, checking tool
paths and booting Linux. This exercise is an integration/evidence plan
until those new measurements exist.

</details>
