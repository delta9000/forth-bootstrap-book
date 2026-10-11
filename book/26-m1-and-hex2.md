# Chapter 26 — The M1 assembler and hex2 linker

A small M1 program can name its opcodes and jump to a label whose address
has not been calculated. Macro substitution followed by two-pass assembly
turns that text into executable bytes. The completed assembler runs on the
seed and library alone and produces the program exercised at the end.

For a first run before the longer source walkthrough, use the
[checkpoint](#try-it) to assemble a program that prints `hi` and exits
with status 42. Then return to the small fragment below: it keeps the
same macro, label, and string mechanisms while leaving the ELF header
out of the trace.

## M1 and hex2 in brief

The implementation has this shape:

```text
stdin → asm-src-buf → macro expansion → asm-exp-buf
                                      → count bytes and record labels
                                      → rewind, resolve labels, emit bytes
                                      → asm-out-buf → the asm-out-name file
```

M1 gives byte sequences names: `DEFINE syscall 0F05` makes a later
`syscall` token stand for `0F05`. The hex2 side assigns addresses to
`:label` declarations and replaces references with numeric fields.
Here those jobs share a program. References begin with a marker, or
*sigil*, such as `!` or `&`; expansion leaves them for the assembly
passes to handle.

“Self-contained” describes its dependency boundary: load `010-lib.fth`,
then this file, then invoke `asm-main`. No compiler layer supplies a
missing definition. The checkpoint below runs exactly that sequence.
The header's claims of agreement with mescc-tools and an M2-Planet
self-compile are the source's own; this chapter checks only the standalone
result below.

## Carry one input through both passes

Before reading the implementation, trace this small input on paper. It
produces an eight-byte fragment, not a runnable ELF file; the checkpoint
later supplies a complete executable. The trace is derived from the
source's expansion, reference, and pass rules
(`forth-bootstrap/forth/130-asm.fth:492–541,561–594,697–714,729–783`).

```text
DEFINE hop EB
:base hop !target
:message "A"
:target &message
```

Use the default load base `0x600000`. File offsets and field widths below
are in **output bytes**, not characters of input text; a two-digit hex
pair emits one byte. IP is the target address being assigned, so
`IP = 0x600000 + output offset`. Multi-byte fields are little-endian.
In any Forth stack trace, the top is at the right; it is a separate state
from the assembler's IP.

**Expansion.** `DEFINE` records `hop` → `EB` and emits no token of its
own. Substitution replaces the later `hop`; the double-quoted string
becomes the byte for `A` followed by a NUL. With whitespace normalized,
the expanded token stream is:

```text
:base EB !target :message 41 00 :target &message
```

Expansion has not resolved either label reference. Both assembly passes
read this same expanded stream.

**Pass 1: lay out bytes and record addresses.** Start at offset 0.
Labels occupy no bytes. A sigil reference reserves its field width even
when its target has not yet been seen. Follow rows from top to bottom:

| Token(s) | Offset before → after | Label recorded or reason |
| --- | --- | --- |
| `:base` | 0 → 0 | `base = 0x600000` |
| `EB` | 0 → 1 | One opcode byte |
| `!target` | 1 → 2 | Reserve one relative-field byte |
| `:message` | 2 → 2 | `message = 0x600002` |
| `41 00` | 2 → 4 | Character and terminating NUL |
| `:target` | 4 → 4 | `target = 0x600004` |
| `&message` | 4 → 8 | Reserve four absolute-field bytes |

The completed table supplies even the forward reference to `target`.
Nothing about looking up that name is needed to count its one-byte field.

**Pass 2: rewind, resolve, and emit.** Reset IP to `0x600000` and retain
the label table. Emit `EB` at offset 0. For `!target`, the field begins
at address `0x600001` and ends at `0x600002`; the relative value is
`0x600004 - 0x600002 = 2`, emitted as `02`. The helper's calculation
`over asm-ip @ + -` takes data stack `1 0x600004` to
`1 0x600004 1 0x600001`, then `1 0x600004 0x600002`, then `1 2`.
Here `1` is the field width in bytes, and the helper has already removed
its other arguments to the return stack. This is subtraction from the
field's **end**, not its first byte or the opcode.

The `41 00` tokens emit unchanged. For `&message`, resolve the absolute
address `0x600002` and emit its four low bytes as `02 00 60 00`. There is
no IP subtraction in this absolute form. The complete predicted fragment
is:

```text
Offset:  00 01 02 03 04 05 06 07
Byte:    EB 02 41 00 02 00 60 00
```

The branch at offset 0 skips the two string bytes: the CPU adds `02` to
its next-instruction offset 2 and reaches `target` at offset 4. The final
four bytes illustrate an address field; they are not a suitable body to
execute after that jump.

### Pause and predict

1. Extend `"A"` to `"AB"`. Fill in the new offsets after `41 42 00`,
   at `:target`, and after `&message`, then predict the relative byte.
2. A proposed fixup emits `03` for the original `!target` by subtracting
   the field's starting address. At what offset does the CPU actually
   arrive, and why is that not `target`?
3. Change the format to a small data record with a four-byte offset
   relative to a named base. Independently derive both passes and all
   output bytes for the following input. It has no branch opcode and is
   not an executable; `%target>base` explicitly uses two labels, not IP.

```text
:base %target>base
:message "AB"
:target &message
```

<details>
<summary>Hint: count field width before resolving its value</summary>

For the first task, the `!` field stays one byte wide. For the third,
`%` reserves four bytes even before `target` is known. A double-quoted string
includes its NUL. Neither `:base` nor another label advances IP.

</details>

<details>
<summary>Check the three predictions</summary>

1. The string ends at offset 5, so `target=0x600005`; the final field
   ends at offset 9. `!target` emits `5-2=3`, while `&message` stays
   `02 00 60 00` because the message's start did not move.
2. The CPU still adds the displacement to offset 2, so `03` reaches
   offset 5, one byte beyond the original target. Changing how the
   assembler calculates a field cannot change the CPU's origin rule.
3. Expansion gives `:base %target>base :message 41 42 00 :target &message`.
   Pass 1 records `base=0x600000`, `message=0x600004`, and
   `target=0x600007`, ending at offset 11. Pass 2 emits `target-base=7`
   as `07 00 00 00`, then `41 42 00`, then the message address as
   `04 00 60 00`. Subtracting the percent field's end would incorrectly
   give 3: an explicit base changes the reference rule.

</details>

You can now take the source walkthrough in three sittings. Read buffers
through [the label table](#the-label-table) to find the storage for the
states above; resume at [numbers](#numbers) through hex bytes and dispatch
to follow token meanings; then resume at [two passes](#two-passes) for the
pass driver and macro expansion. At each pause, keep the small input and
its offsets beside you. The full implementation below remains in source
order, so use the preview to distinguish its runtime phase order.

## Supported input language

The header states the supported input language and its exclusions in
`forth-bootstrap/forth/130-asm.fth:1`:

```forth file=forth/130-asm.fth
\ 130-asm.fth — M1 + hex2 assembler / linker in Forth.
\
\ Closes the bootstrap gap below the Forth C compiler: consumes the
\ M1 macro syntax that M2-Planet emits and produces ELF bytes directly,
\ removing the need to trust GCC-built mescc-tools (M1, hex2).  Stage0-
\ posix's M1+hex2 stays in the picture as an independent byte-level
\ witness; both pipelines are expected to produce identical bytes.
\
\ Self-contained: depends only on 010-lib.fth (and the seed primitives
\ it builds on).  No cross-import from the C-compiler layers — forth-asm
\ sits cleanly below the cc in the bootstrap chain rather than alongside.
\
\ What is implemented (phase 2 complete):
\   - M1 macro expansion: 'DEFINE name value' + name substitution
\   - Six sigils: '!' (1-byte rel), '@' (2-byte rel), '~' (3-byte rel),
\     '%' (4-byte rel, with optional '>base' explicit base), '$' (2-byte
\     abs), '&' (4-byte abs).  Each handles numeric form ('!42', '%0x3C',
\     '%-1', decimal / hex / negative) and label form.
\   - Quoted strings: '"text"' hex-encodes bytes with NUL terminator;
\     "'text'" passes content through verbatim.
\   - ':label' decls; '#' and ';' comments to end of line.
\   - Two-pass label resolution; cmp-identical to mescc-tools' M1+hex2
\     output for the exit42 smoke test, the m1-jump42 fixture, and the
\     full M2-Planet self-compile (~2.4 MiB M1 in, 220 KiB ELF out).
\
\ What is checked, as mescc-tools checks it: a label reference must fit
\ its field (hex2's rule; 244), a number must fit its field (M1's rule;
\ 245), and a bare token must be an even number of hex digits (246, 247),
\ so a misspelled macro name is an error, not bytes.
\
\ Not implemented (no real-world inputs use these on amd64; the token
\ forms among them die with 246 or 247 rather than assembling differently):
\   - '<N' padding directive
\   - nibble accumulation across whitespace within a hex pair
\   - architecture-specific ARM/AArch64/RISC-V displacement quirks
\   - the rare unary-'<' / '^' alignment markers used by ARM
\   - a quoted DEFINE body

```

## Buffers and a cursor

Source text and expanded text must remain alive while table entries point
into them. The assembler reserves separate buffers and selects one through
a cursor; it never overwrites a token to terminate its name.

Keep the opening example beside these allocations. Its three
representations have different jobs and different lifetimes:

| Buffer | What it holds from the example | What depends on it |
|---|---|---|
| Raw source | `DEFINE hop EB` and the later use of `hop` | Macro records point at names and bodies here during expansion |
| Expanded text | `:base EB !target :message 41 00 ...` | Both assembly passes read it; label names point into it |
| Binary output | `EB 02 41 00 02 00 60 00` | The final file write copies these bytes |

The ellipsis in the middle row abbreviates the earlier token
stream, not source to type. Reusing the raw buffer for expansion would
risk overwriting a macro body before its last use. Reusing the expanded
buffer for machine bytes would destroy input still needed by a pass.
Separate storage makes those lifetime rules straightforward.

Allocation starts above the VM pages. The shared size guard follows in
`forth-bootstrap/forth/130-asm.fth:39`:

```forth file=forth/130-asm.fth
\ ============================================================================
\ A. Buffers + cursor abstraction
\ ============================================================================
\ Skip past the VM's fixed pages (data stack 0x410000..0x411000, I/O scratch
\ 0x412000, token buffer 0x412800, sysvars 0x413000..0x414000) so our buffers
\ do not overlap runtime VM state.
skip-vm-pages                                   \ HERE = 0x414000

\ asm-check-cap ( n cap code -- )  Die with code unless n <= cap: the
\ assembler's copy of cc-check-cap (020), since this program loads none of
\ the compiler's files.  n is how full a buffer or table will be once the
\ write about to happen is done.  Codes are 230..249 (Appendix G).
: asm-check-cap
  >r > if, r> die then,
  r> drop ;

```

Call the shared **prospective-size check** with the size after the proposed
append. Equality with the capacity is permitted; a larger value exits with the
supplied code. The input reader deliberately uses a stricter request.

Buffer ownership is explicit in `forth-bootstrap/forth/130-asm.fth:55`:

```forth file=forth/130-asm.fth
\ Raw M1 source (filled by asm-load-stdin).
\ Sized for M2-Planet's ~2.4 MiB self-compile output plus libc + defs + ELF.
[lit] 4194304 constant asm-src-cap            \ 4 MiB
create asm-src-buf  asm-src-cap allot
variable asm-src-len

\ Expanded buffer (filled by asm-expand-pass: M1 macros substituted, DEFINEs
\ stripped).  Passes 1 and 2 read from here, not from asm-src-buf.
[lit] 4194304 constant asm-exp-cap            \ 4 MiB
create asm-exp-buf  asm-exp-cap allot
variable asm-exp-len
```

The capacity reserves storage; the length says how much of it contains
input. A macro can expand to more characters than its name, so the used
lengths of these equally sized allocations need not agree.

## Selecting and reading a buffer

A cursor selection needs an address, a length, and a fresh offset.
The selection words appear in `forth-bootstrap/forth/130-asm.fth:66`:

```forth file=forth/130-asm.fth

\ Cursor: read primitives look at whichever buffer asm-cur-* points to.
\ asm-use-src and asm-use-exp swap the cursor between the two buffers.
variable asm-cur-buf
variable asm-cur-len
variable asm-cur-pos

: asm-use-src
  asm-src-buf asm-cur-buf !
  asm-src-len @ asm-cur-len !
  [lit] 0 asm-cur-pos ! ;

: asm-use-exp
  asm-exp-buf asm-cur-buf !
  asm-exp-len @ asm-cur-len !
  [lit] 0 asm-cur-pos ! ;

: asm-reset-pos  [lit] 0 asm-cur-pos ! ;

```

Selecting a buffer changes all three facts the reader needs: where its
bytes begin, where they end, and where reading resumes. A rewind changes
only the last. That is the operation the second assembly pass will need:
read the same expanded bytes again, with the first pass's labels intact.

Requesting all remaining buffer space avoids a syscall for each input byte in
`forth-bootstrap/forth/130-asm.fth:85`:

```forth file=forth/130-asm.fth
\ asm-load-stdin ( -- )  Read all of fd 0 into asm-src-buf.  Each read asks
\ for all the room left; a source that fills the buffer dies with 239 (a
\ full buffer and a longer input look the same, so one byte stays unused).
: asm-load-stdin
  [lit] 0 asm-src-len !
  begin,
    [lit] 0 asm-src-buf asm-src-len @ +  asm-src-cap asm-src-len @ -  read
    dup [lit] 0 >
  while,
    asm-src-len +!
    asm-src-len @ 1+ asm-src-cap [lit] 239 asm-check-cap
  repeat,
  drop ;

```

`asm-load-stdin` adds each positive read result to the used length.
Its prospective-size check asks whether another byte would fit, so input
that exactly fills the allocation is rejected too. A nonpositive result
ends the loop: this code does not distinguish a read error from EOF.

EOF and byte access stay behind the cursor interface in
`forth-bootstrap/forth/130-asm.fth:99`:

```forth file=forth/130-asm.fth
\ asm-eof? ( -- f )
: asm-eof?  asm-cur-pos @ asm-cur-len @ >= ;

\ asm-peek-char ( -- c )  Byte at current position; 0 at EOF.
: asm-peek-char
  asm-eof? if,
    [lit] 0
  else,
    asm-cur-buf @ asm-cur-pos @ + c@
  then, ;

\ asm-next-char ( -- c )  Returns current byte, advances pos.
: asm-next-char
  asm-peek-char
  [lit] 1 asm-cur-pos +! ;

```

`asm-eof?` tests the offset against the limit. `asm-peek-char` returns
zero at EOF; `asm-next-char` advances even then, so readers must check EOF
before consuming.

## Appending expanded text

Expansion uses a bounded append operation
(`forth-bootstrap/forth/130-asm.fth:115`):

```forth file=forth/130-asm.fth
\ asm-exp-emit-byte ( b -- )  Append a byte to asm-exp-buf; die 240 if full.
: asm-exp-emit-byte
  asm-exp-len @ 1+ asm-exp-cap [lit] 240 asm-check-cap
  asm-exp-buf asm-exp-len @ + c!
  [lit] 1 asm-exp-len +! ;

```

`asm-exp-emit-byte` applies the prospective-size check, stores at the used
end, and advances `asm-exp-len`.

## The output side

Expanded text and emitted bytes have different lengths. Binary output
therefore has its own position (`forth-bootstrap/forth/130-asm.fth:121`):

```forth file=forth/130-asm.fth
\ ============================================================================
\ B. Output buffer + emit helpers
\ ============================================================================
[lit] 1048576 constant asm-out-cap
create asm-out-buf  asm-out-cap allot
variable asm-out-pos

: asm-out-init  [lit] 0 asm-out-pos ! ;

\ asm-emit-byte ( b -- )  Append a byte to asm-out-buf; die 241 if full.
: asm-emit-byte
  asm-out-pos @ 1+ asm-out-cap [lit] 241 asm-check-cap
  asm-out-buf asm-out-pos @ + c!
  [lit] 1 asm-out-pos +! ;

```

Here the position counts output bytes. In the opening example it ends
at eight, regardless of how much text expressed those bytes.
`asm-out-init` resets that position; every append checks the prospective
size before writing. The check must precede the store, because noticing
an overflow afterward would leave memory already corrupted.

The file is opened only after assembly has produced the complete output buffer in
`forth-bootstrap/forth/130-asm.fth:136`:

```forth file=forth/130-asm.fth
\ ============================================================================
\ C. Output file write
\ ============================================================================
\ Open flags: O_WRONLY=1, O_CREAT=64, O_TRUNC=512 → 577.  Mode 0o755 = 493.

\ asm-write-output ( path-addr -- )  path-addr must point at NUL-terminated bytes.
: asm-write-output
  [lit] 577 [lit] 493 open                      ( fd )
  dup 0< if,
    drop [lit] 230 die
  then,
  >r                                            ( ; R: fd )
  r@ asm-out-buf asm-out-pos @ write drop
  r> close drop ;

\ Newline byte for stderr diagnostics.
create asm-nl-byte  nl c,

```

`asm-write-output` creates or truncates the supplied NUL-terminated path
and requests executable permissions. It checks the open result, saves the
descriptor across the write, then closes it. It drops the write and close
results: neither a short write nor a close error is reported.
`asm-nl-byte` supplies the newline used by token diagnostics.

## The label table

A label record keeps a name slice and the address assigned to that name.
The slice points into the expanded buffer, which stays fixed through both
assembly passes. Recording a label therefore requires no name allocation.

The declarations in `forth-bootstrap/forth/130-asm.fth:154` distinguish
table storage from target-address state:

```forth file=forth/130-asm.fth
\ ============================================================================
\ Label table — flat array of (name-addr, name-len, ip) triples.
\ ============================================================================

[lit]   24 constant asm-rec-size
[lit] 8192 constant asm-cap                   \ headroom: M2-Planet uses ~4k labels
create asm-labels  asm-rec-size asm-cap * allot
variable asm-count

\ Base address.  Default matches mescc-tools' --base-address 0x00600000
\ for the M2-Planet self-compile path.  Callers can override by storing a
\ different value before invoking asm-main, e.g. for GNU Mes (0x1000000):
\
\   cat 010-lib.fth 130-asm.fth                   \ defines words
\   echo '[lit] 16777216 asm-base !'              \ override
\   echo 'asm-main'                                \ then run
\
variable asm-base
[lit] 6291456 asm-base !                          \ 0x600000 default
variable asm-ip
variable asm-pass

\ asm-rec ( i -- a )  Address of the i-th label record.
: asm-rec  asm-rec-size *  asm-labels + ;

```

`asm-rec` turns an entry index into a record address by multiplying by
the stride and adding the table base. In the opening example, the record
for `message` will hold a slice naming `message` and the value
`0x600002`. That value belongs to the program being assembled; it is
neither the address of this record nor a pointer into the output buffer.
`asm-ip` is how the counting pass assigns those future program addresses.

A declaration must capture the address at its position in the input.
Here is the record append (`forth-bootstrap/forth/130-asm.fth:179`):

```forth file=forth/130-asm.fth
\ asm-store-label ( name-addr name-len -- )  Die 242 if the table is full.
: asm-store-label
  asm-count @ 1+ asm-cap [lit] 242 asm-check-cap
  asm-count @ asm-rec                       ( addr len rec )
  >r                                         ( addr len ; R: rec )
  r@ [lit] 8 + !                             \ rec[8] = len
  r@ !                                       \ rec[0] = addr
  asm-ip @ r> [lit] 16 + !                   \ rec[16] = ip
  [lit] 1 asm-count +! ;

```

The stack arrives as `name-addr name-len`. `asm-store-label` parks the
record address while it stores the length, the name address, and `asm-ip`.
Only after those stores does it increase the count.

Search starts at the newest record, making repeated names shadow earlier
ones. The lookup is in `forth-bootstrap/forth/130-asm.fth:189`:

```forth file=forth/130-asm.fth
variable asm-find-addr
variable asm-find-len

\ asm-find-label ( name-addr name-len -- ip flag )
\ Linear scan from newest to oldest entry.  flag = -1 if found (returning
\ at once, with exit,), else ip = flag = 0.
: asm-find-label
  asm-find-len !  asm-find-addr !
  asm-count @
  begin,
    dup [lit] 0 >
  while,
    1-                                       ( i )
    dup asm-rec                              ( i rec )
    dup [lit] 8 + @ asm-find-len @ = if,
      dup @ asm-find-addr @ asm-find-len @ bytes-eq if,
        nip [lit] 16 + @ true exit,          ( ip -1 )
      then,
    then,
    drop                                     ( i )
  repeat,
  drop [lit] 0 [lit] 0 ;

```

`asm-find-addr` and `asm-find-len` retain the query while the loop walks
records. Only equal-length names reach `bytes-eq` (Chapter 25). On a match,
`asm-find-label` returns the stored address and true; exhaustion returns
zero and false. The flag distinguishes a missing label from a valid label
at address zero. This **newest-first slice lookup** will also serve macros.

## Numbers

A sigil's body can be a label or a literal. Literal conversion accepts a
leading minus and a hexadecimal prefix; field emission receives the same
cell value regardless of which notation produced it.

Hexadecimal conversion is separate from validation in
`forth-bootstrap/forth/130-asm.fth:212`:

```forth file=forth/130-asm.fth
\ ============================================================================
\ Hex digit utilities + decimal parser + variable-width emit
\ ============================================================================

\ hex-val ( c -- v )  Convert one hex digit char to 0-15.
\ Caller must ensure c is a valid hex digit (asm-hex-char?, below).
: hex-val
  dup digit? if,
    [char] 0 -
  else,
    dup [char] a - [lit] 6 / 0= if,
      [lit] 87 -                             \ 'a'..'f' -> 10..15
    else,
      [lit] 55 -                             \ 'A'..'F' -> 10..15
    then,
  then, ;

\ asm-hex-char? ( c -- f )  True for 0-9, a-f and A-F, the characters
\ hex2 reads as digits.
: asm-hex-char?
  dup digit?
  over [char] a - [lit] 6 / 0= or
  swap [char] A - [lit] 6 / 0= or ;

```

`asm-hex-char?` accepts decimal digits and either case of hexadecimal
letters. `hex-val` converts a character already known to be valid.
The bare-hex path enforces that precondition; the numeric parser does not.

The parser first records its input slice and removes the sign and radix prefix from the scan in
`forth-bootstrap/forth/130-asm.fth:236`:

```forth file=forth/130-asm.fth
variable asm-dec-addr
variable asm-dec-len
variable asm-dec-val
variable asm-dec-neg
variable asm-dec-hex
variable asm-dec-i

\ asm-parse-number ( addr len -- value )
\ Decimal or hex integer: optional leading '-', then an optional '0x' / '0X'
\ prefix for hex.
\ (Matches a subset of mescc-tools' strtoint sufficient for amd64 inputs;
\ 0b binary and bare-0 octal are not used by M2-Planet's M1 output.)
: asm-parse-number
  asm-dec-len ! asm-dec-addr !
  [lit] 0 asm-dec-val !
  [lit] 0 asm-dec-neg !
  [lit] 0 asm-dec-hex !
  [lit] 0 asm-dec-i !
  \ Leading '-'?
  asm-dec-len @ [lit] 0 > if,
    asm-dec-addr @ c@ [char] - = if,
      true asm-dec-neg !
      [lit] 1 asm-dec-i !
    then,
  then,
  \ '0x' / '0X' hex prefix?
  asm-dec-len @ asm-dec-i @ - [lit] 2 >= if,
    asm-dec-addr @ asm-dec-i @ + c@ [char] 0 = if,
      asm-dec-addr @ asm-dec-i @ + 1+ c@
      dup [char] x = swap [char] X = or if,
        true asm-dec-hex !
        [lit] 2 asm-dec-i +!
      then,
    then,
  then,
```

The `asm-dec-*` cells hold address, length, accumulator, negative flag,
hexadecimal flag, and index. `asm-parse-number` initializes them on every
call. After a minus, it checks for `0x` or `0X` at the updated index.

The rest of the parser selects a radix-specific loop, then applies the
saved sign (`forth-bootstrap/forth/130-asm.fth:271`):

```forth file=forth/130-asm.fth
  asm-dec-hex @ if,
    begin,
      asm-dec-i @ asm-dec-len @ <
    while,
      asm-dec-addr @ asm-dec-i @ + c@ hex-val
      asm-dec-val @ [lit] 16 * +
      asm-dec-val !
      [lit] 1 asm-dec-i +!
    repeat,
  else,
    begin,
      asm-dec-i @ asm-dec-len @ <
    while,
      asm-dec-addr @ asm-dec-i @ + c@ [char] 0 -
      asm-dec-val @ [lit] 10 * +
      asm-dec-val !
      [lit] 1 asm-dec-i +!
    repeat,
  then,
  asm-dec-val @
  asm-dec-neg @ if,
    [lit] 0 swap -
  then, ;

```

The decimal branch uses the decimal accumulation from Chapter 12;
the hexadecimal branch changes the radix and digit converter. Neither
branch validates every character or detects arithmetic overflow. Thus the
later field bounds check is not a complete numeric-syntax check.

A caller-selected width controls how many low bytes reach the output buffer in
`forth-bootstrap/forth/130-asm.fth:295`:

```forth file=forth/130-asm.fth
\ asm-emit-le ( v width -- )  Emit the low width bytes of v, little-endian.
: asm-emit-le
  begin,
    dup
  while,
    over asm-emit-byte                     ( v width )
    swap [lit] 256 / swap 1-               ( v/256 width-1 )
  repeat,
  2drop ;

```

`asm-emit-le` keeps `v width` on the stack and exhausts the width.
The output buffer's byte store truncates each emitted value. This also
emits the low bytes of negative values without a separate signed path.

## Reading tokens

Tokenization returns slices of the selected buffer. It treats whitespace
and comments as separators outside quotes; inside quotes they are data.

Before starting a token, the reader must consume comments as well as
whitespace. The skipping helpers are in `forth-bootstrap/forth/130-asm.fth:305`:

```forth file=forth/130-asm.fth
\ ============================================================================
\ Whitespace / comment skipper and token reader
\ ============================================================================
\
\ asm-skip-rest-of-line ( -- )  Consume bytes until newline or EOF.
: asm-skip-rest-of-line
  begin,
    asm-eof? if, exit, then,
    asm-next-char nl =
  until, ;

\ asm-skip-ws ( -- )  Advance past whitespace and '#'/';' comments.
: asm-skip-ws
  begin,
    asm-eof? if, exit, then,
    asm-peek-char dup space? if,
      drop asm-next-char drop
    else,
      dup [char] # =  swap [char] ; =  or 0= if, exit, then,
      asm-next-char drop
      asm-skip-rest-of-line
    then,
  again, ;

```

`asm-skip-rest-of-line` stops after newline or at EOF. `asm-skip-ws`
repeats whitespace removal and recognizes both `#` and `;` as comment
openers. Its early return leaves the cursor at a nonseparator.

Quoted and bare tokens advance the cursor under different stopping rules in
`forth-bootstrap/forth/130-asm.fth:329`:

```forth file=forth/130-asm.fth
variable asm-tok-start
variable asm-tok-len
variable asm-quote-char

\ asm-read-quoted ( -- )  At an opening quote: count bytes through the
\ matching close quote (whitespace and newlines inside are body bytes).
: asm-read-quoted
  asm-next-char asm-quote-char !
  [lit] 1 asm-tok-len +!
  begin,
    asm-eof? if, exit, then,
    [lit] 1 asm-tok-len +!
    asm-next-char asm-quote-char @ =
  until, ;

\ asm-read-bareword ( -- )  Count bytes up to whitespace, '#', ';' or EOF.
: asm-read-bareword
  begin,
    asm-eof? if, exit, then,
    asm-peek-char  dup space?  over [char] # = or  swap [char] ; = or
    if, exit, then,
    asm-next-char drop
    [lit] 1 asm-tok-len +!
  again, ;

```

`asm-tok-start` and `asm-tok-len` describe the token; `asm-quote-char`
remembers its opening delimiter. `asm-read-quoted` includes the delimiters
in the length and permits embedded newlines. It has no escape processing
or missing-close diagnostic. `asm-read-bareword` stops before whitespace
or a comment opener, leaving the separator for the next skip.

The public reader chooses the scan from the opening character in
`forth-bootstrap/forth/130-asm.fth:354`:

```forth file=forth/130-asm.fth
\ asm-read-token ( -- start len )
\ Whitespace/comment-delimited token slice of the active buffer; (0 0) at EOF.
\ '"' and "'" start a quoted string token that runs until the matching close
\ quote.  The returned slice includes both quote characters.
: asm-read-token
  asm-skip-ws
  asm-eof? if, [lit] 0 [lit] 0 exit, then,
  asm-cur-buf @ asm-cur-pos @ + asm-tok-start !
  [lit] 0 asm-tok-len !
  asm-peek-char dup [char] " = swap [char] ' = or if,
    asm-read-quoted
  else,
    asm-read-bareword
  then,
  asm-tok-start @ asm-tok-len @ ;

```

`asm-read-token` first skips separators, then saves the cursor's current
address and clears the token length. Its EOF result is `0 0`; every real
token has positive length. Consumers use that length to end their loops.

For our small input, this reader first returns slices for `DEFINE`,
`hop`, and `EB`. The expansion pass will give those slices their macro
meaning. Later, with the expanded buffer selected, the same reader
returns `:base`, `EB`, and `!target` to the assembly passes. Reading a
slice does not yet decide whether it names a macro, a label, or bytes.

## One token, one decision

Assembly saves the current token in scratch cells so every handler can
inspect it and report it on failure. A leading colon declares a label;
a leading sigil requests a numeric field; anything else must be raw hex.

Numeric classification looks only at the first character after the sigil in
`forth-bootstrap/forth/130-asm.fth:370`:

```forth file=forth/130-asm.fth
\ ============================================================================
\ Per-token processing
\ ============================================================================

variable asm-token-start-tmp
variable asm-token-len-tmp
variable asm-gt-pos
variable asm-scan-i
variable asm-hex-i

\ asm-tok-numeric? ( -- f )  Token's body starts with digit or '-' -> numeric form.
\ Token in asm-token-start-tmp / asm-token-len-tmp.
: asm-tok-numeric?
  asm-token-len-tmp @ [lit] 2 < if,
    [lit] 0
  else,
    asm-token-start-tmp @ 1+ c@
    dup [char] - = swap digit? or
  then, ;

```

`asm-token-start-tmp` and `asm-token-len-tmp` retain the whole token.
`asm-gt-pos` records an explicit-base separator, `asm-scan-i` searches
for it, and `asm-hex-i` walks hex digits. `asm-tok-numeric?` selects the
numeric path for a digit or minus; it does not validate the remaining body.

An explicit-base reference needs the position of its separator in
`forth-bootstrap/forth/130-asm.fth:390`:

```forth file=forth/130-asm.fth
\ asm-find-gt ( -- )  Set asm-gt-pos to position of '>' in token name, or -1.
: asm-find-gt
  [lit] 1 asm-scan-i !
  begin,
    asm-scan-i @ asm-token-len-tmp @ <
  while,
    asm-token-start-tmp @ asm-scan-i @ + c@ [char] > = if,
      asm-scan-i @ 1- asm-gt-pos ! exit,
    then,
    [lit] 1 asm-scan-i +!
  repeat,
  true asm-gt-pos ! ;

```

A declaration affects only the counting pass. Its handler is in
`forth-bootstrap/forth/130-asm.fth:403`:

```forth file=forth/130-asm.fth
\ asm-do-label-decl ( -- )
: asm-do-label-decl
  asm-pass @ [lit] 1 = if,
    asm-token-start-tmp @ 1+
    asm-token-len-tmp @ 1-
    asm-store-label
  then, ;

```

`asm-find-gt` records the length of the name before `>`, excluding the
sigil; absent `>` leaves a negative sentinel. `asm-do-label-decl` strips
the colon and records the slice only in the first pass. The second pass
must preserve that completed label table.

## Token diagnostics

A rejected token should identify itself. The diagnostic writer precedes
the bounds documentation in `forth-bootstrap/forth/130-asm.fth:411`:

```forth file=forth/130-asm.fth
\ asm-tok-err ( code -- )  Write current token + newline to fd 2, then exit code.
: asm-tok-err
  [lit] 2 asm-token-start-tmp @ asm-token-len-tmp @ write drop
  [lit] 2 asm-nl-byte [lit] 1 write drop
  die ;

\ ---- Range checks ----
\ mescc-tools refuses a value that does not fit its field, and so does
\ this file.  A label's value is hex2's to check, a number's is M1's, and
\ their bounds differ.  Neither checks a 4-byte field (% and &).
\
\   field               label (hex2)          number (M1)
\   ! 1-byte relative   -128..127             -129..256
\   @ 2-byte relative   -32768..32767         -32769..32768
\   ~ 3-byte relative   -8388608..8388607     -8388609..8388608
\   $ 2-byte absolute   0..65535              -32769..65536

```

`asm-tok-err` writes the saved token and `asm-nl-byte`, then exits with
the caller's code. The comments attribute the distinct label and literal
bounds to hex2 and M1.

## Field bounds

Label bounds depend on width and whether the field is relative in
`forth-bootstrap/forth/130-asm.fth:428`:

```forth file=forth/130-asm.fth
variable asm-fit-lo
variable asm-fit-hi

\ asm-half ( width -- n )  Half the values a width-byte field holds:
\ 128, 32768 or 8388608.
: asm-half
  [lit] 128 swap
  begin,
    1- dup
  while,
    swap [lit] 256 * swap
  repeat,
  drop ;

\ asm-label-bounds ( width relative? -- )  hex2's range for a label: signed
\ for a relative field, unsigned for an absolute one.
: asm-label-bounds
  swap asm-half swap if,                    ( half )
    dup [lit] 0 swap - asm-fit-lo !
    1- asm-fit-hi !
  else,
    [lit] 0 asm-fit-lo !
    dup + 1- asm-fit-hi !
  then, ;

```

`asm-half` computes half the field's possible values. `asm-label-bounds`
uses it to set `asm-fit-lo` and `asm-fit-hi`: a signed interval for
relative references, or an unsigned interval for absolute references.

Literal bounds deliberately differ from label bounds in
`forth-bootstrap/forth/130-asm.fth:453`:

```forth file=forth/130-asm.fth
\ asm-number-bounds ( width relative? -- )  M1's range for a number: one
\ below hex2's signed low end, and up to half (relative) or all (absolute,
\ and M1's 1-byte relative) of the field's values.
: asm-number-bounds
  swap dup asm-half                         ( relative? width half )
  dup [lit] 0 swap - 1- asm-fit-lo !
  swap [lit] 1 =  rot 0=  or if,            ( half )
    dup +
  then,
  asm-fit-hi ! ;

\ asm-fit ( width v code -- width v )  Die with code, echoing the token,
\ unless width is 4 or asm-fit-lo <= v <= asm-fit-hi.
: asm-fit
  >r over [lit] 4 < if,                     ( width v ; R: code )
    dup asm-fit-lo @ <  over asm-fit-hi @ >  or if,
      r> asm-tok-err
    then,
  then,
  r> drop ;

```

`asm-number-bounds` permits a value below the signed minimum and a high
endpoint beyond the label rule; the narrowest relative field also gets
the wider high endpoint. `asm-fit` compares against the selected inclusive
bounds while preserving `width v`. It bypasses checking for a width of
4, so `%` and `&` emit the low field bytes even for larger cell values.
The bounds are compatibility choices, not a general integer validator.

## Sigils and references

A sigil specifies the field width and how a label address is transformed.
A relative label field contains `target - (asm-ip + width)`: its origin
is the end of the field. A numeric body is emitted directly, even with a
relative sigil.

The dispatch parameters and common body slice are documented in
`forth-bootstrap/forth/130-asm.fth:474`:

```forth file=forth/130-asm.fth
\ ---- Sigil references ----
\ A token that starts with one of the six sigils stands for a number of
\ width bytes: its body is either a number (`!42`, `%-1`, `$0x3C`), emitted
\ as is, or a label, whose address is emitted either absolute or relative
\ to the end of the field.  Pass 1 only advances the IP by width; pass 2
\ emits the bytes.
\
\   sigil  width  label form
\     !      1    relative
\     @      2    relative
\     ~      3    relative
\     %      4    relative, or %target>base: target - base
\     $      2    absolute
\     &      4    absolute

\ asm-ref-name ( -- a u )  The token's body: everything after the sigil.
: asm-ref-name  asm-token-start-tmp @ 1+  asm-token-len-tmp @ 1- ;

```

`!`, `@`, `~`, and `%` select relative fields of increasing width;
`$` and `&` select absolute fields. These are characters in the input
language, not calls to similarly named Forth words. `asm-ref-name`
returns everything after the sigil.

Counting a reference requires only its width. The same handler resolves
its value on the emitting pass (`forth-bootstrap/forth/130-asm.fth:492`):

```forth file=forth/130-asm.fth
\ asm-do-ref ( width relative? err -- )  Handle a sigil token of width
\ bytes.  A label that is not defined dies with err (after echoing the
\ token); a value that does not fit the field dies with 244 (label) or
\ 245 (number).
: asm-do-ref
  asm-pass @ [lit] 1 = if,
    2drop asm-ip +! exit,                   \ pass 1: count the bytes
  then,
  >r >r                                     ( width ; R: err relative? )
  asm-tok-numeric? if,
    dup r@ asm-number-bounds
    asm-ref-name asm-parse-number           ( width v )
    [lit] 245 asm-fit
  else,
    asm-ref-name asm-find-label 0= if,      ( width ip )
      r> drop r> asm-tok-err                \ undefined label: exits
    then,
    r@ if,                                  \ relative to the field's end
      over asm-ip @ + -                     ( width ip-IP-width )
    then,
    over r@ asm-label-bounds
    [lit] 244 asm-fit
  then,
  r> drop r> drop                           ( width v )
  over asm-emit-le                          ( width )
  asm-ip +! ;

```

In the first pass, `asm-do-ref` drops the relativity flag and error code,
then advances `asm-ip` by the width. In the second, it saves those
parameters and chooses numeric conversion or newest-first slice lookup.
Only a label on the relative path subtracts the end-of-field address.

The chosen bounds feed `asm-fit`; the saved parameters are removed
before emission. At `over asm-emit-le`, the duplicate width lets the
emitter consume `v width` while the original width remains for the final
IP update. Undefined labels exit with the sigil's supplied error code.

This is the handler behind our opening `!target`: width 1 reserves one
byte in pass 1, and the saved label address produces displacement 2 in
pass 2. The same handler processes `&message` with width 4 and a false
relativity flag, so it emits the address without subtracting IP. One
piece of code accounts for the two different fields in that fragment.

A difference between named addresses supplies file offsets and sizes without using the current IP in
`forth-bootstrap/forth/130-asm.fth:519`:

```forth file=forth/130-asm.fth
\ asm-do-pct-ref ( -- )  '%': asm-do-ref's 4-byte relative form, plus
\ '%target>base', which emits target - base (two labels, no IP).
: asm-do-pct-ref
  asm-pass @ [lit] 2 =  asm-tok-numeric? 0=  and if,
    asm-find-gt
    asm-gt-pos @ [lit] 0 >= if,
      asm-token-start-tmp @ 1+
      asm-gt-pos @
      asm-find-label                        ( target flag )
      0= if,
        drop [lit] 233 asm-tok-err          \ target undefined
      then,
      asm-token-start-tmp @ 1+ asm-gt-pos @ + 1+
      asm-token-len-tmp @ asm-gt-pos @ - [lit] 2 -
      asm-find-label                        ( target base flag )
      0= if,
        2drop [lit] 232 asm-tok-err         \ base undefined
      then,
      - [lit] 4 asm-emit-le
      [lit] 4 asm-ip +! exit,
    then,
  then,
  [lit] 4 true [lit] 234 asm-do-ref ;

```

`asm-do-pct-ref` recognizes `%target>base` during emission, resolves both
slices, and emits `target - base`. Its first pass follows the ordinary
percent path and counts the same width. A numeric percent token bypasses
the separator scan. Without `>`, `%label` is relative to the field end.
In the checkpoint, `%ELF_end>ELF_base` fills the file and memory sizes.

## Hex bytes and dispatch

Raw hex needs validation before conversion. Otherwise a misspelled macro
could become arbitrary digit values (`forth-bootstrap/forth/130-asm.fth:543`):

```forth file=forth/130-asm.fth
\ asm-check-hex ( -- )  A bare token must be hex digits (else 246: a
\ misspelled macro name lands here, as M1's "invalid other") and an even
\ number of them (else 247: hex2 would carry the odd digit into the next
\ token, which this file does not do).
: asm-check-hex
  [lit] 0 asm-hex-i !
  begin,
    asm-hex-i @ asm-token-len-tmp @ <
  while,
    asm-token-start-tmp @ asm-hex-i @ + c@ asm-hex-char? 0= if,
      [lit] 246 asm-tok-err
    then,
    [lit] 1 asm-hex-i +!
  repeat,
  asm-token-len-tmp @ [lit] 1 and if,
    [lit] 247 asm-tok-err
  then, ;

```

`asm-check-hex` validates every character and then rejects odd length.
It does not carry a pending half-byte across token boundaries. A name
made entirely of an even run of hex digits remains valid byte input,
so this check cannot detect every misspelled macro.

A valid hex token has a known size before any bytes are emitted in
`forth-bootstrap/forth/130-asm.fth:561`:

```forth file=forth/130-asm.fth
\ asm-do-hex ( -- )  Token of hex digits -> 1 byte per pair.  Pass 1
\ checks it, so pass 2 only ever sees whole pairs of digits.
: asm-do-hex
  asm-pass @ [lit] 1 = if,
    asm-check-hex
    asm-token-len-tmp @ [lit] 2 / asm-ip +!
  else,
    [lit] 0 asm-hex-i !
    begin,
      asm-hex-i @ asm-token-len-tmp @ <
    while,
      asm-token-start-tmp @ asm-hex-i @ + c@ hex-val [lit] 16 *
      asm-token-start-tmp @ asm-hex-i @ 1+ + c@ hex-val
      +
      asm-emit-byte
      [lit] 1 asm-ip +!
      [lit] 2 asm-hex-i +!
    repeat,
  then, ;

```

`asm-do-hex` validates and counts pairs during the first pass.
During the second it combines each high and low digit, emits the byte,
and advances IP. The expanded buffer must remain unchanged between
passes for the earlier validation to remain sufficient.

The leading character reduces dispatch to a handler and a small set of parameters in
`forth-bootstrap/forth/130-asm.fth:581`:

```forth file=forth/130-asm.fth
\ asm-process-token ( start len -- )  Dispatch on the token's first char:
\ a label declaration, one of the six sigils (width, relative?, and the
\ code for an undefined label), or else hex bytes.
: asm-process-token
  asm-token-len-tmp !  asm-token-start-tmp !
  asm-token-start-tmp @ c@                  ( c )
  dup [char] : = if, drop asm-do-label-decl                   exit, then,
  dup [char] ! = if, drop [lit] 1 true    [lit] 235 asm-do-ref exit, then,
  dup [char] @ = if, drop [lit] 2 true    [lit] 236 asm-do-ref exit, then,
  dup [char] ~ = if, drop [lit] 3 true    [lit] 237 asm-do-ref exit, then,
  dup [char] % = if, drop asm-do-pct-ref                      exit, then,
  dup [char] $ = if, drop [lit] 2 [lit] 0 [lit] 238 asm-do-ref exit, then,
  dup [char] & = if, drop [lit] 4 [lit] 0 [lit] 231 asm-do-ref exit, then,
  drop asm-do-hex ;

```

`asm-process-token` saves the slice before reading its first character.
Each recognized case exits after its handler. The final fallthrough is
`asm-do-hex`, so a bare unknown name is checked as hex rather than searched
as a label. Labels require a sigil when referenced.

## Two passes

Two-pass assembly separates layout from value resolution. The first
walk counts every field and records declarations; the second emits using
the completed table. Forward references work because field size never
depends on a label's eventual value.

The loop itself is independent of the selected pass. Initialization is
kept separate in `forth-bootstrap/forth/130-asm.fth:596`:

```forth file=forth/130-asm.fth
\ ============================================================================
\ Two-pass driver
\ ============================================================================

: asm-pass-loop
  begin,
    asm-read-token
    dup [lit] 0 = if, 2drop exit, then,
    asm-process-token
  again, ;

: asm-init
  asm-base @ asm-ip !
  [lit] 0 asm-count ! ;

```

`asm-pass-loop` consumes each nonempty token exactly once per walk.
`asm-init` resets IP from `asm-base` and clears the label count. Calling it
between walks would destroy the table needed for resolution. The driver
must instead rewind the cursor and reset only the emission state. During
emission, IP equals the base plus the output position after each token.

## Macro expansion: definitions

We have followed the expanded stream through layout and emission. Now
return to the earlier step that changed `hop` into `EB`. An M1 macro
is textual substitution of a name by a stored body slice. The expander
builds its separate text buffer before either assembly pass begins;
neither pass needs to know that a byte sequence once had a mnemonic.

Macro records keep both name and replacement slices in
`forth-bootstrap/forth/130-asm.fth:611`:

```forth file=forth/130-asm.fth
\ ============================================================================
\ M1 macro expansion (phase 2b)
\ ============================================================================
\ Single linear pass over the raw source.  Tokens:
\   - "DEFINE" -> consume next 2 tokens (name, value), store in defs table;
\     emit nothing to asm-exp-buf.
\   - defined name -> emit its body bytes (followed by a space separator).
\   - any other token -> copy verbatim to asm-exp-buf (followed by a space).
\ DEFINEs always appear before use in real M1 sources, so single-pass works.

[lit]   32 constant asm-def-rec-size          \ name-addr 8 + name-len 8 + body-addr 8 + body-len 8
[lit] 4096 constant asm-def-cap
create asm-defs  asm-def-rec-size asm-def-cap * allot
variable asm-def-count

: asm-def-rec  asm-def-rec-size * asm-defs + ;

```

Storing a macro fills the record from the top of the supplied stack.
The append operation is in `forth-bootstrap/forth/130-asm.fth:628`:

```forth file=forth/130-asm.fth
\ asm-def-store ( name-addr name-len body-addr body-len -- )  Die 243 if
\ the table is full.
: asm-def-store
  asm-def-count @ 1+ asm-def-cap [lit] 243 asm-check-cap
  asm-def-count @ asm-def-rec                ( name-a name-l body-a body-l rec )
  >r                                          ( name-a name-l body-a body-l ; R: rec )
  r@ [lit] 24 + !                             \ rec[24] = body-len
  r@ [lit] 16 + !                             \ rec[16] = body-addr
  r@ [lit] 8 + !                              \ rec[8] = name-len
  r> !                                        \ rec[0] = name-addr
  [lit] 1 asm-def-count +! ;
```

`asm-def-rec-size` gives the record stride, `asm-def-cap` the limit,
`asm-defs` the storage, and `asm-def-count` the used count.
`asm-def-rec` computes a record address. `asm-def-store` applies the
prospective-size check, then stores name address, name length, body
address, and body length. These slices point into the raw source buffer.

A repeated definition shadows its predecessor through newest-first slice lookup in
`forth-bootstrap/forth/130-asm.fth:639`:

```forth file=forth/130-asm.fth

variable asm-deff-addr
variable asm-deff-len

\ asm-def-find ( name-addr name-len -- body-addr body-len flag )
\ flag = -1 if found, 0 otherwise; body-* are 0 when not found.
: asm-def-find
  asm-deff-len !  asm-deff-addr !
  asm-def-count @
  begin,
    dup [lit] 0 >
  while,
    1-                                       ( i )
    dup asm-def-rec                          ( i rec )
    dup [lit] 8 + @ asm-deff-len @ = if,
      dup @ asm-deff-addr @ asm-deff-len @ bytes-eq if,
        nip dup [lit] 16 + @ swap [lit] 24 + @ true exit,
      then,
    then,
    drop                                     ( i )
  repeat,
  drop [lit] 0 [lit] 0 [lit] 0 ;

```

`asm-deff-addr` and `asm-deff-len` hold the query. `asm-def-find`
returns the matching body slice plus a flag, or zero placeholders and
false. Definitions must precede their uses; this lookup cannot see a
later declaration.

## Macro expansion: copying

The directive keyword is recognized as a whole token before ordinary macro lookup in
`forth-bootstrap/forth/130-asm.fth:662`:

```forth file=forth/130-asm.fth
\ asm-define-kw: the 6 bytes of "DEFINE".
create asm-define-kw  s, DEFINE

\ asm-is-define? ( addr len -- f )  True if token equals "DEFINE".
: asm-is-define?
  dup [lit] 6 = if,
    drop asm-define-kw [lit] 6 bytes-eq
  else,
    drop drop [lit] 0
  then, ;

variable asm-cp-addr
variable asm-cp-len
variable asm-cp-i
```

`asm-define-kw` holds the keyword bytes. `asm-is-define?` checks length
before comparing them. The `asm-cp-*` cells hold a copy's source address,
length, and index; copying and string conversion reuse that scratch state.

Replacement text and generated hex share the checked expansion writer in
`forth-bootstrap/forth/130-asm.fth:676`:

```forth file=forth/130-asm.fth

\ asm-exp-bytes ( addr len -- )  Copy len bytes from addr to asm-exp-buf.
: asm-exp-bytes
  asm-cp-len !  asm-cp-addr !
  [lit] 0 asm-cp-i !
  begin,
    asm-cp-i @ asm-cp-len @ <
  while,
    asm-cp-addr @ asm-cp-i @ + c@ asm-exp-emit-byte
    [lit] 1 asm-cp-i +!
  repeat, ;

\ asm-hex-digit ( n -- c )  Map 0..15 to ASCII '0'..'9' / 'A'..'F'.
: asm-hex-digit
  dup [lit] 10 < if,
    [char] 0 +
  else,
    [lit] 55 +
  then, ;

```

`asm-exp-bytes` copies a complete slice through `asm-exp-emit-byte`.
`asm-hex-digit` performs the reverse conversion from a digit value to
an uppercase hex character. It is used when input characters themselves
must become bytes in the assembled output.

## Macro expansion: strings

Double quotes mean character data. This conversion writes hex text and
adds the terminating NUL (`forth-bootstrap/forth/130-asm.fth:696`):

```forth file=forth/130-asm.fth
\ asm-exp-string-double ( start len -- )
\ Token = '"' body '"' (len includes both quotes).  Emit hex-encoded body
\ bytes (separated by spaces) plus a trailing 00 NUL terminator, matching
\ mescc-tools M1's double-quoted-string semantics.
: asm-exp-string-double
  asm-cp-len !  asm-cp-addr !
  [lit] 1 asm-cp-i !
  begin,
    asm-cp-i @ asm-cp-len @ 1- <
  while,
    asm-cp-addr @ asm-cp-i @ + c@
    dup [lit] 16 / asm-hex-digit asm-exp-emit-byte
    [lit] 15 and asm-hex-digit asm-exp-emit-byte
    bl asm-exp-emit-byte
    [lit] 1 asm-cp-i +!
  repeat,
  \ NUL terminator: "00 "
  [char] 0 asm-exp-emit-byte [char] 0 asm-exp-emit-byte
  bl asm-exp-emit-byte ;

```

`asm-exp-string-double` scans inside the delimiters, emits each body
byte as hex text, and separates encoded bytes with spaces. It then appends
`00 `. The literal newline inside the checkpoint's string therefore
becomes a newline byte in the program, followed by a NUL.

Single quotes instead expose their contents as assembly text in
`forth-bootstrap/forth/130-asm.fth:716`:

```forth file=forth/130-asm.fth
\ asm-exp-string-single ( start len -- )
\ Token = "'" body "'".  Emit body bytes verbatim, then a space separator.
: asm-exp-string-single
  asm-cp-len !  asm-cp-addr !
  [lit] 1 asm-cp-i !
  begin,
    asm-cp-i @ asm-cp-len @ 1- <
  while,
    asm-cp-addr @ asm-cp-i @ + c@ asm-exp-emit-byte
    [lit] 1 asm-cp-i +!
  repeat,
  bl asm-exp-emit-byte ;

```

`asm-exp-string-single` copies the interior unchanged and appends a
separator. It lets an input such as `'0F 05'` become ordinary hex tokens
for the assembly walks. Neither string helper verifies a closing quote;
the reader's missing-close behavior therefore matters here.

## Macro expansion: the walk

Directive handling, string conversion, and substitution meet in the expansion loop in
`forth-bootstrap/forth/130-asm.fth:729`:

```forth file=forth/130-asm.fth
\ asm-expand-pass ( -- )  Walk current cursor (asm-src-buf), build defs table,
\ write expanded text into asm-exp-buf.
: asm-expand-pass
  [lit] 0 asm-exp-len !
  [lit] 0 asm-def-count !
  begin,
    asm-read-token                            ( start len )
    dup [lit] 0 = if, 2drop exit, then,
    2dup asm-is-define? if,
      2drop
      asm-read-token                          ( name-a name-l )
      asm-read-token                          ( name-a name-l body-a body-l )
      asm-def-store
    else,
      \ Quoted strings: dispatch on first char.
      over c@ [char] " = if,
        asm-exp-string-double
      else,
        over c@ [char] ' = if,
          asm-exp-string-single
        else,
          2dup asm-def-find                   ( start len body-a body-l flag )
          if,
            asm-exp-bytes
            drop drop
          else,
            drop drop
            asm-exp-bytes
          then,
          bl asm-exp-emit-byte
        then,
      then,
    then,
  again, ;

```

`asm-expand-pass` clears the expansion length and definition count,
then reads raw-source tokens. `DEFINE` consumes a name and body and stores
them without emitting text. Direct quoted tokens select their string
helper before macro lookup.

For a macro hit, the stack contains the original token slice beneath
the replacement slice. `asm-exp-bytes` consumes the replacement; the
following drops remove the original. On a miss, the drops instead remove
the lookup's zero placeholders, and the original token is copied.

Substitution is not recursive: the replacement bytes enter the expansion
buffer without returning to this dispatcher. A replacement naming another
macro is not expanded again. A quoted replacement likewise does not go
through a string helper, which explains the header's quoted-body exclusion.
A separator follows copied text so adjacent replacements cannot merge.

## `asm-main`

The entry point makes the pass order explicit. Read the resets between
walks in `forth-bootstrap/forth/130-asm.fth:764`:

```forth file=forth/130-asm.fth
\ The output path: asm-out-name holds the address of a NUL-terminated path,
\ "/tmp/asm-out" unless the caller stores its own there before asm-main.
create asm-out-path  s, /tmp/asm-out  [lit] 0 c,
variable asm-out-name  asm-out-path asm-out-name !

: asm-main
  asm-load-stdin
  asm-use-src
  asm-expand-pass             \ build defs table + write asm-exp-buf
  asm-use-exp
  asm-init
  [lit] 1 asm-pass !
  asm-pass-loop
  asm-reset-pos
  asm-base @ asm-ip !
  asm-out-init
  [lit] 2 asm-pass !
  asm-pass-loop
  asm-out-name @ asm-write-output
  bye ;

\ The caller invokes 'asm-main' (after optionally setting 'asm-base' and
\ 'asm-out-name').
\ Existing pipelines append it on stdin between the Forth prelude and the M1
\ source; see tests/asm/*.sh.
```

`asm-out-name` holds the address of a NUL-terminated output path, initially
`/tmp/asm-out`. The caller can store a different path's address there.
`asm-main` drains the remaining stdin into source storage, expands it,
and selects the expanded
buffer. It initializes the label table only before counting. Between
assembly walks it rewinds the cursor, restores IP from the base, and
clears the output position while retaining labels.

Loading the file defines `asm-main` without calling it. The checkpoint
sends the invocation after the Forth definitions and before M1 text, so
the assembler owns the remaining input. `tests/asm/hi-check.sh` is the
repository's own check of the program in Try it.

## Capacity and failure

The prospective-size check protects each bounded append. Buffer and table
limits, and their exit codes, come from the declarations and checks above:

| Resource | Limit | Exit code |
| --- | ---: | ---: |
| Raw source | less than 4194304 bytes | 239 |
| Expanded text | 4194304 bytes | 240 |
| Binary output | 1048576 bytes | 241 |
| Label records | 8192 entries | 242 |
| Macro records | 4096 entries | 243 |

Token errors print the token to stderr before exiting. Undefined ordinary
references use 231 for `&`, 234 for `%`, 235 for `!`, 236 for `@`, 237 for
`~`, and 238 for `$`. Explicit percent references use 232 for a missing
base and 233 for a missing target. Label and literal range failures use
244 and 245; invalid hex and odd digit counts use 246 and 247.
An output-open failure uses 230.

These checks do not make all failures visible. Numeric syntax, unterminated
quotes, missing `DEFINE` operands, read errors, and short writes lack
complete diagnostics. A failure before opening the output leaves any old
output file in place. Treat a successful assembly and the generated
program's behavior as separate observations.

The implementation also excludes padding directives, cross-token hex
pairs, and architecture-specific displacement or alignment forms listed
in its header. The runnable example exercises the supported subset.

## Try it

Run from the `forth-bootstrap` checkout at `./forth-bootstrap`, with the
seed built in Part 1. The pipeline loads the complete library and assembler,
then gives `asm-main` a hand-written program including its ELF header.
The temporary directory holds the input and executable. A Forth line before
`asm-main` sets `asm-out-name` to the executable pathname's address. The
explicit `/tmp` template keeps this pathname free of whitespace, even when the
shell's `TMPDIR` contains spaces. The `||` guard captures the program's
intentional status 42 even in a shell with `set -e`; the separate `test`
checks that expected status.

<!-- tryit: expect "hi\nexit: 42\n160" -->
```sh
(
set -o pipefail
d=$(mktemp -d /tmp/book-probe.XXXXXXXXXX) || exit "$?"
trap 'status=$?; rm -rf -- "$d" || status=1; exit "$status"' EXIT
cat > "$d/hi.M1" <<'M1' || exit "$?"
DEFINE mov_eax, B8
DEFINE mov_edi, BF
DEFINE mov_esi, BE
DEFINE mov_edx, BA
DEFINE jmp8 EB
DEFINE syscall 0F05

:ELF_base                                   # the file loads at 0x600000
'7F454C46 02 01 01 03 00 00000000000000'    # e_ident
'0200 3E00 01000000'                        # ET_EXEC, AMD64, version 1
&_start '00000000'                          # e_entry
%ELF_phdr>ELF_base '00000000'               # e_phoff
'0000000000000000 00000000'                 # e_shoff, e_flags
'4000 3800 0100 0000 0000 0000'             # sizes; one program header
:ELF_phdr
'01000000 07000000 0000000000000000'        # PT_LOAD, RWX, offset 0
&ELF_base '00000000' &ELF_base '00000000'   # vaddr, paddr
%ELF_end>ELF_base '00000000'                # filesz
%ELF_end>ELF_base '00000000'                # memsz
'0100000000000000'                          # align

:_start
    mov_eax, %1  mov_edi, %1                # write(1,
    mov_esi, &msg  mov_edx, %3              #   msg, 3)
    syscall
    jmp8 !done                              # hop over the data
:msg "hi
"
:done
    mov_eax, %60  mov_edi, %42  syscall     # exit(42)
:ELF_end
M1
{ cat forth/010-lib.fth forth/130-asm.fth || exit "$?"
  echo "create out s, $d/hi [lit] 0 c,  out asm-out-name !"
  echo asm-main; cat "$d/hi.M1"; } | ./seed-forth || exit "$?"
chmod +x "$d/hi" || exit "$?"
status=0
"$d/hi" || status=$?             # prints "hi"
printf 'exit: %s\n' "$status"  # prints "exit: 42"
test "$status" -eq 42 || exit 1
wc -c < "$d/hi"             # prints: 160
)
```

Observed output:

```text
hi
exit: 42
160
```

The executable prints `hi` followed by newline, exits with status 42,
and occupies 160 bytes. Macro substitution supplies instruction bytes;
`&msg` supplies an absolute address; `!done` supplies a forward relative
jump; `%ELF_end>ELF_base` supplies header sizes. The double-quoted string
includes a NUL after the newline, which the write length excludes.
The ELF structure is supplied by the input, not invented by the assembler.
This completes the library's standalone program; Chapter 27 begins the
compiler's arena and I/O buffers.

## Exercise

**Trace (easy).** Follow `jmp8 !done` in the checkpoint. Mark the field's
start and end, then count the string bytes between the field end and
`:done`. Include the terminating NUL. Explain why counting the opcode as
part of the displacement would give the wrong destination.

**Modify (moderate).** The checkpoint removes its temporary directory.
Edit the `hi.M1` here-document in a copy of the commands above and rerun
the whole block, including `mktemp`, to make fresh input. Change the
message to `hey` followed by newline and its write length to `%4`.
Predict which label addresses, relative field, and header sizes change,
then assemble and run it, comparing against your new output and size
prediction. Explain why the numeric write length does not undergo the
relative-label subtraction. For another attempt, choose a different
short message; keep the jump distance within its signed one-byte range.

<details>
<summary>Hint: track starts separately from lengths</summary>

The ELF and program headers occupy 120 bytes. Four five-byte moves
and a two-byte syscall precede `jmp8`. Mark the opcode, the one-byte
field, and the field end separately. An extra string byte moves labels
after the string, but not the address where the string begins.

</details>

<details>
<summary>Check the checkpoint calculations</summary>

The opcode is at offset 142, its field at 143, and the field ends at
144. Original `hi`, newline, and NUL take four bytes, so `done` is at
148: the correct encoding is `EB 04`. Counting from the opcode would
produce 6, which the CPU adds to 144 and reaches 150.

For `hey` plus newline, the string takes five bytes including NUL.
`done` moves to 149 and `ELF_end` to 161; `!done` becomes `05` and both
`%ELF_end>ELF_base` size fields become `A1 00 00 00` followed by their
unchanged four zero high bytes. `msg` stays at `0x600090`, so `&msg`
stays `90 00 60 00`; `_start`, `ELF_base`, and `ELF_phdr` also stay put.
`%4` is numeric: it emits `04 00 00 00` directly without any address
subtraction. Predicted output is `hey` followed by newline, status 42,
and a 161-byte executable. Update the output and size comments in your
copy so that they describe the modified program rather than the old one.

</details>

