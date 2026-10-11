# Chapter 28 — The preprocessor

The lexer should see `4` wherever a macro says that `ROWS` stands for `4`.
That sounds like text replacement until the replacement contains another
macro, or an argument contains a quoted comma. Then the preprocessor needs
to know which text it is reading, where to put the result, and where to
resume afterward.

## A worked expansion before the machinery

A C **macro** associates a name with replacement text before the lexer
reads the program. A `#define` directive records that association. An
object-like macro needs only its name; a function-like macro also takes
arguments to substitute into its replacement. Consider one of each:

```c
#define ROWS 4
#define SQUARE(x) ((x) * (x))
SQUARE(ROWS)
```

Trace this by hand in the legacy profile used by the chapter's checkpoint.
We are following tokens here; the checkpoint below shows the actual
whitespace. The result contains two `4` tokens and a multiplication. The
preprocessor does not calculate 16.

| Step | Text being handled | What must survive the step |
|---|---|---|
| Collect the argument | `ROWS` inside `SQUARE(ROWS)` | Where to resume after the closing `)` |
| Expand the argument | `ROWS` becomes `4` | The surrounding source and its output buffer |
| Substitute | Each `x` in the stored body receives the expanded argument | The completed argument text until both copies are made |
| Rescan the replacement | The tokens of `((4) * (4))` | The caller's position while nested text is scanned |
| Resume | The source after `SQUARE(ROWS)` | No temporary text is needed after its last use |

Each row introduces a storage obligation. A **region** records the text
being read and the position within it. A **sink** records the buffer being
written and its used length. The scratch area keeps argument and
replacement text alive across nested scans. Saving and restoring these
three things is the central operation of the chapter.

There is one more guard: a macro is marked busy while its replacement is
scanned, so it cannot keep expanding itself. Quoted strings and comments
have their own walkers. Change the argument to `","` and collection must
still find one argument; that comma is inside a string. These are C
preprocessing rules.

The implementation also supports a direct profile with different include
and substitution rules. We will identify those branches as they appear.
The region/sink model applies to both; the legacy whitespace and argument
policy used in this trace does not describe direct `#` and `##` handling.

## The contract, the sink and the scratch area

The code has this shape:

```text
cc-in-buf → region walker → cc-src-buf
                ↕
       include regions and macro replacements
                ↕
       temporary sinks, macro table, conditional stack
```

The source builds the storage before the recursive walker that uses it.
Read each buffer below against the expansion: the outer source must wait
while its argument is expanded, and the argument must wait while the
replacement is assembled. Include files introduce another region to
suspend and resume; they do not require another model of reading text.

The header names the supported directives (`forth-bootstrap/cc/040-cc-prep.fth:1`):

```forth file=cc/040-cc-prep.fth
\ 040-cc-prep.fth — the C preprocessor.
\
\ One pass over the raw source, before the lexer sees anything:
\   1. Legacy #include "FILE" searches as given, then under tests/cc/;
\      angle includes are dropped in favour of built-in header shims.
\      Direct mode resolves quoted names relative to their includer, then
\      explicit include directories; angle names use those directories.
\   2. #define NAME BODY and #define NAME(PARAMS) BODY record a macro, and
\      #undef NAME forgets it.  Outside directives every identifier is
\      looked up: a macro's name is replaced by its body (for a function-
\      like macro, with the call's arguments put in for the parameters),
\      and the replacement is scanned again for more macros.
\   3. #if, #ifdef, #ifndef, #elif, #else and #endif keep or drop lines;
\      #if and #elif evaluate a constant expression in which
\      `defined NAME` asks whether NAME is a macro.
\   4. #error stops the compiler. SysV #line sets presumed source locations;
\      GNU numeric markers fail explicitly. Other directives are dropped.
\   5. Everything else is copied through unchanged.
```

A dropped line still leaves its newline behind. The header connects that rule to the input and source buffers (Chapter 27), with a separate evaluator hook for conditional expressions (`forth-bootstrap/cc/040-cc-prep.fth:19`):

```forth file=cc/040-cc-prep.fth
\
\ Every source line keeps its line number, so cc-die's "line N" is the line
\ of the spliced-together program: a dropped line or directive leaves its
\ newline behind, and the newlines a directive or a macro call spanning
\ several lines swallows are written out right after it.
\
\ The pass reads a region (addr, len, pos) byte by byte and writes to a
\ sink.  The first region is the program in cc-in-buf; an #include pushes
\ the included file as a new region, and a macro expansion pushes the
\ replacement text.  The sink is cc-src-buf, the buffer the lexer reads
\ (030), except while an argument or a replacement is being built in a
\ temporary buffer.
\
\ Depends on 010-lib.fth (open/close, digit?, bytes-eq, control flow),
\ 020-cc-arena.fth (cc-src-line, cc-die, cc-check-cap) and 030-cc-io.fth
\ (cc-in-buf, cc-src-buf, cc-src-init, cc-read-all, ident-start?/ident-cont?,
\ cell[], cc-name-find).  #if's expression evaluator comes from
\ 100-cc-expr.fth, through the deferred word cc-pp-eval.

```

Output goes to a *sink*: a buffer, its written length, its capacity and its failure code. Keeping that state together lets nested expansion park and restore it (`forth-bootstrap/cc/040-cc-prep.fth:38`):

```forth file=cc/040-cc-prep.fth
\ ===========================================================================
\ The sink
\ ===========================================================================
\ Where output bytes go: one 4-cell block, so a sink can be parked and
\ restored by copying the block.

create cc-pp-sink  [lit] 32 allot
cc-pp-sink             constant cc-pp-out          \ buffer address
cc-pp-sink [lit]  8 +  constant cc-pp-out-pos      \ bytes written so far
cc-pp-sink [lit] 16 +  constant cc-pp-out-cap      \ buffer size
cc-pp-sink [lit] 24 +  constant cc-pp-out-code     \ die code when it fills

\ Direct mode keeps unavailable-token metadata outside the C byte stream.
\ The selected sink's shadow bytes are derived from its existing buffer.
variable cc-prep-direct                         \ explicit headers; no shim macros
variable cc-pp-out-flags
: cc-pp-select-flags-default ;
defer cc-pp-select-flags-fwd
' cc-pp-select-flags-default is cc-pp-select-flags-fwd

\ cc-prep-emit-byte ( b -- )  Append b to the sink; die with the sink's
```

Every append checks the sink's bound and clears stale token metadata before storing a byte. Slice copies go through a hook so they can preserve metadata when needed (`forth-bootstrap/cc/040-cc-prep.fth:59`):

```forth file=cc/040-cc-prep.fth
\ code if it is full.  Counts lines as it goes, so a failure during the
\ pass reports the line of the output it had reached.
: cc-prep-emit-byte
  cc-pp-out-pos @ 1+ cc-pp-out-cap @ cc-pp-out-code @ cc-check-cap
  cc-pp-out-flags @ if, [lit] 0 cc-pp-out-flags @ cc-pp-out-pos @ + c! then,
  dup cc-pp-out @ cc-pp-out-pos @ + c!
  [lit] 1 cc-pp-out-pos +!
  nl = if, [lit] 1 cc-src-line +! then, ;

: cc-pp-copy-byte-default c@ cc-prep-emit-byte ;
defer cc-pp-copy-byte-fwd
' cc-pp-copy-byte-default is cc-pp-copy-byte-fwd

\ cc-pp-emit-bytes ( a u -- )  Append u bytes from a.
: cc-pp-emit-bytes
  begin, dup while,
    over cc-pp-copy-byte-fwd
    1- swap 1+ swap
  repeat,
  2drop ;

```

The parked-sink stack holds suspended destinations; `cc-pp-copy4` moves the complete sink record. Scratch capacity bounds how many temporary sinks can be live (`forth-bootstrap/cc/040-cc-prep.fth:81`):

```forth file=cc/040-cc-prep.fth
\ cc-pp-copy4 ( src dst -- )  Copy one 4-cell block (a sink).
: cc-pp-copy4
  [lit] 32
  begin, dup while,
    [lit] 8 -                                    ( src dst off )
    >r  over r@ + @  over r@ + !  r>
  repeat,
  drop 2drop ;

\ Parked sinks, innermost last.  Every sink parked here but the first
\ two (the source buffer and the macro pool, §2) belongs to a temp
\ buffer, and each temp buffer takes cc-pp-temp-cap bytes of the scratch
\ area below, so the scratch runs out (code 43) before this stack could:
\ it has room for as many temp buffers as the scratch holds, plus two.
[lit] 34 constant cc-pp-sinks-cap
create cc-pp-sinks  cc-pp-sinks-cap [lit] 32 * allot
variable cc-pp-sink-depth

```

Sink push and pop apply save-switch-restore: push installs a new sink, and pop resumes the previous destination with its corresponding flags (`forth-bootstrap/cc/040-cc-prep.fth:98`):

```forth file=cc/040-cc-prep.fth
\ cc-pp-sink-push ( addr pos cap code -- )  Park the current sink and make
\ a new one.
: cc-pp-sink-push
  cc-pp-sink  cc-pp-sink-depth @ [lit] 32 * cc-pp-sinks +  cc-pp-copy4
  [lit] 1 cc-pp-sink-depth +!
  cc-pp-out-code ! cc-pp-out-cap ! cc-pp-out-pos ! cc-pp-out !
  cc-pp-select-flags-fwd ;

\ cc-pp-sink-pop ( -- )  Resume writing to the most recently parked sink.
: cc-pp-sink-pop
  [lit] 1 cc-pp-sink-depth -!
  cc-pp-sink-depth @ [lit] 32 * cc-pp-sinks +  cc-pp-sink  cc-pp-copy4
  cc-pp-select-flags-fwd ;

```

### Temporary text and token marks

A macro call builds arguments and replacement text in scratch storage. Each finished temporary retains only the space its text uses. When expansion ends, the call releases all the scratch space it reserved (`forth-bootstrap/cc/040-cc-prep.fth:112`):

```forth file=cc/040-cc-prep.fth
\ ===========================================================================
\ Scratch space for temporary text
\ ===========================================================================
\ A macro call's arguments and its replacement are built here, in temporary
\ sinks allocated from the top of a stack.  A temp buffer being written
\ owns cc-pp-temp-cap bytes; once finished it keeps only its text.  Each
\ macro call gives back everything it took when it is done.

[lit] 2097152 constant cc-pp-scratch-cap          \ 2 MiB
create cc-pp-scratch  cc-pp-scratch-cap allot
variable cc-pp-scratch-top                        \ first free byte
[lit] 65536 constant cc-pp-temp-cap               \ one temp buffer's room
```

An identifier encountered while its macro is disabled must remain unavailable during later rescans. Direct mode stores that property in shadow bytes alongside scratch and source text, leaving C spelling unchanged (`forth-bootstrap/cc/040-cc-prep.fth:124`):

```forth file=cc/040-cc-prep.fth

\ A copied identifier that encountered a disabled macro remains unavailable
\ during every later argument/replacement rescan. One shadow byte per text
\ byte retains that token property without changing spelling or line counts.
\ Only scratch and final-source sinks can contain expanded tokens; raw input,
\ includes and stored replacement bodies have no such flags.
variable cc-pp-flags-base
: cc-pp-flag-address ( address -- shadow-address-or-zero )
  cc-prep-direct @ 0= cc-pp-flags-base @ 0= or if, drop [lit] 0 exit, then,
  dup cc-pp-scratch >= over cc-pp-scratch cc-pp-scratch-cap + < and if,
    cc-pp-scratch - cc-pp-flags-base @ + exit,
  then,
  dup cc-src-buf >= over cc-src-buf cc-src-cap + < and if,
    cc-src-buf - cc-pp-flags-base @ cc-pp-scratch-cap + + exit,
  then, drop [lit] 0 ;
: cc-pp-unavailable? ( address -- flag )
  cc-pp-flag-address dup if, c@ then, ;
: cc-pp-select-flags
  cc-pp-out @ cc-pp-flag-address cc-pp-out-flags ! ;
' cc-pp-select-flags is cc-pp-select-flags-fwd
```

Forwarding a byte must capture its mark before the append clears the destination mark, including when source and destination coincide (`forth-bootstrap/cc/040-cc-prep.fth:144`):

```forth file=cc/040-cc-prep.fth
: cc-pp-copy-marked-byte ( address -- )
  dup cc-pp-unavailable? >r c@ cc-prep-emit-byte
  r> cc-pp-out-flags @ 0= 0= and if,
    true cc-pp-out-flags @ cc-pp-out-pos @ + 1- c!
  then, ;
' cc-pp-copy-marked-byte is cc-pp-copy-byte-fwd
: cc-pp-flags-init
  [lit] 0 cc-pp-out-flags !
```

The shadow mapping is allocated on demand and reused. Pasting marked text is rejected because this text engine cannot preserve the full token-level rules for that case (`forth-bootstrap/cc/040-cc-prep.fth:152`):

```forth file=cc/040-cc-prep.fth
  cc-prep-direct @ if,
    cc-src-cap cc-src-direct-cap > if, [lit] 43 cc-die then,
    cc-pp-flags-base @ 0= if,
      cc-pp-scratch-cap cc-src-direct-cap + [lit] 43 cc-workspace-map
      cc-pp-flags-base !
    then,
  then,
  cc-pp-select-flags ;
\ A paste containing an unavailable token needs token-level placemarker
\ rules beyond this text engine. Reject it instead of re-expanding a token
\ or leaking metadata into its spelling. Ordinary paste operands are intact.
: cc-pp-paste-bytes ( address count -- )
  2dup begin, dup while,
    over cc-pp-unavailable? if, [lit] 47 cc-die then,
    swap 1+ swap 1-
  repeat, 2drop cc-pp-emit-bytes ;

\ cc-pp-scratch-alloc ( n -- a )  Take n bytes; die 43 if they aren't
\ there (macro calls nested some 32 deep inside each other's arguments).
```

`cc-pp-temp-begin` reserves room and switches the sink; `cc-pp-temp-end` returns the text, releases unused room and restores the parked sink. The allocator checks the scratch bound before advancing (`forth-bootstrap/cc/040-cc-prep.fth:171`):

```forth file=cc/040-cc-prep.fth
: cc-pp-scratch-alloc
  cc-pp-scratch-top @ swap over +                  ( a new-top )
  dup cc-pp-scratch - cc-pp-scratch-cap [lit] 43 cc-check-cap
  cc-pp-scratch-top ! ;

\ cc-pp-temp-begin ( -- )  Park the sink; write to a new temp buffer.  A
\ temp buffer that fills dies with 37.
: cc-pp-temp-begin
  cc-pp-temp-cap cc-pp-scratch-alloc  [lit] 0  cc-pp-temp-cap  [lit] 37
  cc-pp-sink-push ;

\ cc-pp-temp-end ( -- a u )  Finish the temp buffer: answer its text, give
\ back the room it did not use, and resume the parked sink.
: cc-pp-temp-end
  cc-pp-out @ cc-pp-out-pos @                      ( a u )
  2dup + cc-pp-scratch-top !
  cc-pp-sink-pop ;

```

## The macro table

The opening definitions must survive more than one invocation. `ROWS`
keeps the body `4`; `SQUARE` keeps a body with two references to its one
parameter. A call's argument text belongs in scratch, but those stored
definitions must still exist after that scratch is released. This is why
the macro table and its text pool have a different lifetime from the
temporary sinks just built.

A macro number indexes parallel arrays for its name, body, parameter count and busy flag. Names and bodies must outlive the source region that supplied them (`forth-bootstrap/cc/040-cc-prep.fth:189`):

```forth file=cc/040-cc-prep.fth
\ ===========================================================================
\ The macro table
\ ===========================================================================
\ Parallel arrays indexed by macro number (cell[], 030).  A macro's name
\ and body are copied into cc-macro-pool: the source they came from may be
\ an include-pool slot that the next #include at that depth overwrites.
\   name-addr / name-len  the name; #undef sets the length to 0, so the
\                         entry can never match again
\   body-addr / body-len  the replacement text.  In a function-like macro's
\                         body ordinary parameter k is encoded as 1, k.
\                         Direct mode also uses 2, k for #k and 3 for ##.
\   params                -1 for an object-like macro; else how many
\                         parameters the function-like macro has
\   busy                  -1 while the macro's own replacement is being
\                         scanned: a macro met inside itself is not
\                         expanded again, so no expansion loops.


```

The name and body fields each have a default array, a selected-buffer variable and an accessor. All fields use the same macro index (`forth-bootstrap/cc/040-cc-prep.fth:207`):

```forth file=cc/040-cc-prep.fth
[lit] 4096 constant cc-macro-default-cap
variable cc-macro-limit
cc-macro-default-cap cc-macro-limit !
: cc-macro-cap ( -- entries ) cc-macro-limit @ ;
create cc-macro-default-name-addr cc-macro-default-cap [lit] 8 * allot
variable cc-macro-name-addr-buffer
cc-macro-default-name-addr cc-macro-name-addr-buffer !
: cc-macro-name-addr ( -- address ) cc-macro-name-addr-buffer @ ;
create cc-macro-default-name-len cc-macro-default-cap [lit] 8 * allot
variable cc-macro-name-len-buffer
cc-macro-default-name-len cc-macro-name-len-buffer !
: cc-macro-name-len ( -- address ) cc-macro-name-len-buffer @ ;
create cc-macro-default-body-addr cc-macro-default-cap [lit] 8 * allot
variable cc-macro-body-addr-buffer
cc-macro-default-body-addr cc-macro-body-addr-buffer !
: cc-macro-body-addr ( -- address ) cc-macro-body-addr-buffer @ ;
create cc-macro-default-body-len cc-macro-default-cap [lit] 8 * allot
variable cc-macro-body-len-buffer
cc-macro-default-body-len cc-macro-body-len-buffer !
: cc-macro-body-len ( -- address ) cc-macro-body-len-buffer @ ;
```

The parameter field distinguishes object-like macros from function-like macros; the busy field disables recursive replacement. The direct-GCC workspace has a separate capacity and mapping base, while the text pool remains shared (`forth-bootstrap/cc/040-cc-prep.fth:227`):

```forth file=cc/040-cc-prep.fth
create cc-macro-default-params cc-macro-default-cap [lit] 8 * allot
variable cc-macro-params-buffer
cc-macro-default-params cc-macro-params-buffer !
: cc-macro-params ( -- address ) cc-macro-params-buffer @ ;
create cc-macro-default-busy cc-macro-default-cap [lit] 8 * allot
variable cc-macro-busy-buffer
cc-macro-default-busy cc-macro-busy-buffer !
: cc-macro-busy ( -- address ) cc-macro-busy-buffer @ ;
variable cc-macro-count

[lit] 262144 constant cc-macro-pool-cap           \ 256 KiB
create cc-macro-pool  cc-macro-pool-cap allot
variable cc-macro-pool-pos

\ Direct GCC maps six equally sized parallel arrays; the text pool is unchanged.
\ Fixed opt-in policy; changing one array never changes legacy macro limits.
[lit] 4608 constant cc-macro-direct-cap
variable cc-macro-direct-base
\ The selectors that switch these arrays follow the include pool below.
```

Allocated storage and the admission limit are separate:

| Preprocessing policy and selected workspace | Admitted macro records | Macro-text sink limit |
|---|---:|---:|
| Legacy policy, including with larger selected arrays | 1,024 | 65,536 bytes |
| Direct policy, default arrays | 4,096 | 262,144 bytes |
| Direct policy, direct-GCC workspace | 4,608 | 262,144 bytes |

The default text pool physically has 262,144 bytes in every row. Selecting
larger arrays does not enable direct semantics, and the historical
`cc-macro-cap` comment below describes the direct branch, not the legacy
1,024-record check.

A definition read from an include slot cannot retain pointers into that slot: a later include may overwrite it. `cc-pp-pool-copy` uses save-switch-restore to give names and bodies lasting storage (`forth-bootstrap/cc/040-cc-prep.fth:260`):

```forth file=cc/040-cc-prep.fth

\ cc-pp-to-pool ( -- )  Make the macro pool the sink (die 35 when full).
: cc-pp-to-pool
  cc-macro-pool cc-macro-pool-pos @
  cc-prep-direct @ if, cc-macro-pool-cap else, [lit] 65536 then, [lit] 35
  cc-pp-sink-push ;

\ cc-pp-from-pool ( -- )  Keep what was written to the pool; resume the
\ parked sink.
: cc-pp-from-pool
  cc-pp-out-pos @ cc-macro-pool-pos !
  cc-pp-sink-pop ;

\ cc-pp-pool-copy ( a u -- a' u )  Copy u bytes into the pool.
: cc-pp-pool-copy
  cc-macro-pool cc-macro-pool-pos @ + >r          ( a u ; R: a' )
  cc-pp-to-pool  dup >r cc-pp-emit-bytes  cc-pp-from-pool
  r> r> swap ;
```

### Recording and finding definitions

Hash buckets narrow each lookup to a chain of definitions. A bucket holds an encoded head index, and `cc-macro-hnext` links older entries; resetting clears the heads (`forth-bootstrap/cc/040-cc-prep.fth:264`):

```forth file=cc/040-cc-prep.fth

\ Lookup goes through a hash table (cc-name-hash, 030): cc-macro-bucket
\ holds, per bucket, one more than the index of the newest macro whose name
\ hashes there (0 for none), and cc-macro-hnext links each macro to the
\ next older one in its bucket (-1 at the end), so a chain is walked
\ newest-first.
create cc-macro-bucket  cc-name-buckets [lit] 8 * allot
create cc-macro-hnext   cc-macro-direct-cap [lit] 8 * allot

\ cc-macro-hash-reset ( -- )  Empty every bucket (with cc-macro-count 0).
: cc-macro-hash-reset
  [lit] 0 begin, dup cc-name-buckets < while,
    [lit] 0 over cc-macro-bucket cell[] !  1+
  repeat, drop ;
cc-macro-hash-reset
```

Linking inserts the new record at its bucket's head. `cc-macro-record` checks the policy's effective limit, fills the parallel fields and clears the new entry's busy flag (`forth-bootstrap/cc/040-cc-prep.fth:291`):

```forth file=cc/040-cc-prep.fth

\ cc-macro-link ( i -- )  Put macro i, whose name is filed, at the head of
\ its bucket.
: cc-macro-link
  >r
  r@ cc-macro-name-addr cell[] @  r@ cc-macro-name-len cell[] @  cc-name-hash
  dup cc-macro-bucket cell[] @ 1-  r@ cc-macro-hnext cell[] !
  r> 1+ swap cc-macro-bucket cell[] ! ;

\ cc-macro-record ( name-a name-u body-a body-u params -- )  Add an entry
\ whose name and body already sit in the pool.  Dies with code 34 if the
\ table already holds cc-macro-cap macros.
: cc-macro-record
  cc-macro-count @ 1+
  cc-prep-direct @ if, cc-macro-cap else, [lit] 1024 then,
  [lit] 34 cc-check-cap
  cc-macro-count @ >r
  r@ cc-macro-params    cell[] !
  r@ cc-macro-body-len  cell[] !
  r@ cc-macro-body-addr cell[] !
  r@ cc-macro-name-len  cell[] !
  r@ cc-macro-name-addr cell[] !
  r@ cc-macro-link
  [lit] 0 r> cc-macro-busy cell[] !
  [lit] 1 cc-macro-count +! ;
```

`cc-macro-add` copies built-in text before recording it. Lookup saves the queried slice in `cc-mf-a` and `cc-mf-u`, then walks the bucket newest-first so a later definition shadows an earlier one (`forth-bootstrap/cc/040-cc-prep.fth:307`):

```forth file=cc/040-cc-prep.fth

\ cc-macro-add ( name-a name-u body-a body-u -- )  Add an object-like
\ macro, copying name and body into the pool (the built-in macros).
: cc-macro-add
  >r >r cc-pp-pool-copy r> r> cc-pp-pool-copy
  true cc-macro-record ;

\ cc-macro-find ( a u -- i | -1 )  The newest macro named a u, so a later
\ #define of the same name wins: the newest of its bucket's chain whose
\ length and bytes match.
variable cc-mf-a
variable cc-mf-u
: cc-macro-find
  cc-mf-u ! cc-mf-a !
  cc-mf-a @ cc-mf-u @ cc-name-hash cc-macro-bucket cell[] @ 1-   ( i )
  begin, dup 0< 0= while,
    dup cc-macro-name-len cell[] @ cc-mf-u @ = if,
      dup cc-macro-name-addr cell[] @ cc-mf-a @ cc-mf-u @ bytes-eq if, exit, then,
    then,
    cc-macro-hnext cell[] @
  repeat, ;

```

## Regions, owed newlines and the byte walkers

The walker reads a *region*: base address, length and position. Its file flag distinguishes source that may contain directives from replacement text that must not create directives (`forth-bootstrap/cc/040-cc-prep.fth:326`):

```forth file=cc/040-cc-prep.fth
\ ===========================================================================
\ The region being read
\ ===========================================================================
\ cc-prep-in-file is true while the region is a source file, where a line
\ may be a directive; false while it is macro text being scanned again.

variable cc-prep-src-addr
variable cc-prep-src-len
variable cc-prep-src-pos
variable cc-prep-in-file
variable cc-prep-at-line-start                    \ true at the start of a line

\ cc-prep-eor? ( -- f )  End-of-region.
: cc-prep-eor?
  cc-prep-src-pos @ cc-prep-src-len @ >= ;

\ cc-prep-peek ( -- c )  Current byte; 0 at EOR.
: cc-prep-peek
  cc-prep-eor? if,
    [lit] 0
  else,
    cc-prep-src-addr @ cc-prep-src-pos @ + c@
  then, ;
```

The cursor helpers inspect or advance whichever region is active. Blank skipping leaves newlines visible, and paired-byte tests recognize delimiters (`forth-bootstrap/cc/040-cc-prep.fth:349`):

```forth file=cc/040-cc-prep.fth

\ cc-prep-advance ( -- )
: cc-prep-advance
  [lit] 1 cc-prep-src-pos +! ;

\ cc-prep-peek2 ( -- c )  The byte one past pos; 0 if that is at/after EOR.
\ Used to recognise two-byte markers such as /* and */.
: cc-prep-peek2
  cc-prep-src-pos @ 1+ cc-prep-src-len @ >= if,
    [lit] 0
  else,
    cc-prep-src-addr @ cc-prep-src-pos @ + 1+ c@
  then, ;

\ cc-prep-skip-blanks ( -- )  Skip spaces and tabs (NOT newlines).
: cc-prep-skip-blanks
  begin,
    cc-prep-eor? 0=
    cc-prep-peek dup bl = swap tab = or  and
  while,
    cc-prep-advance
  repeat, ;

\ cc-prep-at? ( c1 c2 -- f )  True if the next two bytes are c1 c2.
: cc-prep-at?
  cc-prep-peek2 = swap cc-prep-peek = and ;

```

A directive, comment or macro call can consume newlines without emitting them immediately. These are *owed newlines*: `cc-pp-flush-nl` pays them back after the construct so later source lines retain their positions (`forth-bootstrap/cc/040-cc-prep.fth:386`):

```forth file=cc/040-cc-prep.fth
\ ===========================================================================
\ Newlines that are owed
\ ===========================================================================
\ A newline swallowed without being written (inside a directive's comment,
\ a continued line, a macro call's arguments) is counted here and written
\ out after the directive or the macro call, so later lines keep their
\ numbers.

variable cc-pp-pending-nl

: cc-pp-flush-nl
  begin, cc-pp-pending-nl @ while,
    nl cc-prep-emit-byte
    [lit] 1 cc-pp-pending-nl -!
  repeat, ;

```

### Walking comments and literals

A quote inside a comment is inert, as is a comment opener inside a literal. Shared walkers consume each construct whole; the caller selects whether its bytes are emitted, its newlines counted, or everything dropped (`forth-bootstrap/cc/040-cc-prep.fth:392`):

```forth file=cc/040-cc-prep.fth
\ ===========================================================================
\ Walking comments and literals
\ ===========================================================================
\ One walker per construct; what happens to each byte walked over is set by
\ cc-pp-put-mode: put-emit copies it to the sink, put-count only counts its
\ newlines as owed, put-drop does nothing.

[lit] 0 constant put-drop
[lit] 1 constant put-emit
[lit] 2 constant put-count
variable cc-pp-put-mode
variable cc-pp-line-control                     \ -1 operand, 2 prefix scan
variable cc-pp-location-enabled                 \ direct profile: phase two

\ cc-pp-put ( c -- )  Dispose of one walked-over byte.
: cc-pp-put
  cc-pp-put-mode @ put-emit = if, cc-prep-emit-byte exit, then,
  cc-pp-put-mode @ put-count = if,
    nl = if, [lit] 1 cc-pp-pending-nl +! then, exit,
  then,
  drop ;

\ cc-pp-take ( -- )  Put the current byte and step past it.
: cc-pp-take  cc-prep-peek cc-pp-put cc-prep-advance ;
```

Continuation detection accepts LF and CRLF endings. Consuming a continuation sends only its newline through the selected disposal mode while advancing past every physical byte (`forth-bootstrap/cc/040-cc-prep.fth:416`):

```forth file=cc/040-cc-prep.fth

\ Source #line operands fail closed on unsupported splices inside comments.
\ Detect CRLF as well as LF, even though the general engine only splices LF.
: cc-pp-line-continuation?
  backslash nl cc-prep-at? if, true exit, then,
  backslash [lit] 13 cc-prep-at? if,
    cc-prep-src-pos @ [lit] 2 + cc-prep-src-len @ < if,
      cc-prep-src-addr @ cc-prep-src-pos @ + [lit] 2 + c@ nl = exit,
    then,
  then, [lit] 0 ;

\ Consume a known LF or CRLF continuation, disposing of only its newline
\ through the caller's put mode. The physical source cursor still moves
\ past every byte, so location macros retain physical line accounting.
: cc-pp-take-continuation
  cc-prep-advance
  cc-prep-peek [lit] 13 = if, cc-prep-advance then,
  cc-pp-take ;
```

Comment delimiters may be separated by continuations in the location-enabled profile. Lookahead skips those continuations without moving the caller's cursor (`forth-bootstrap/cc/040-cc-prep.fth:434`):

```forth file=cc/040-cc-prep.fth

\ Phase two deletes every backslash-newline before comments are found, so
\ in the direct profile a comment delimiter may be split by continuations
\ ("*\<newline>/" closes a comment) and a continuation inside a comment
\ simply vanishes (a "//" comment goes on to the next line).

\ cc-pp-splice-skip ( u -- u' )  The source offset past the run of LF or
\ CRLF continuations that starts at offset u.  pos is kept.
: cc-pp-splice-skip
  cc-prep-src-pos @ >r cc-prep-src-pos !
  begin, cc-pp-line-continuation? while,
    cc-prep-advance
    cc-prep-peek [lit] 13 = if, cc-prep-advance then,
    cc-prep-advance
  repeat,
  cc-prep-src-pos @ r> cc-prep-src-pos ! ;
```

`cc-pp-at-spliced?` compares delimiter bytes across continuations. Deleting a splice inside an emitted comment owes its newline instead of writing it there, where it could end a line comment or split a closer (`forth-bootstrap/cc/040-cc-prep.fth:453`):

```forth file=cc/040-cc-prep.fth

\ cc-pp-at-spliced? ( c1 c2 -- f )  Like cc-prep-at?, but in the direct
\ profile continuations may stand between c1 and c2.
: cc-pp-at-spliced?
  cc-pp-location-enabled @ 0= if, cc-prep-at? exit, then,
  swap cc-prep-peek <> if, drop [lit] 0 exit, then,
  cc-prep-src-pos @ 1+ cc-pp-splice-skip
  dup cc-prep-src-len @ >= if, 2drop [lit] 0 exit, then,
  cc-prep-src-addr @ + c@ = ;

\ cc-pp-comment-splice? ( -- f )  A continuation that phase two deletes.
: cc-pp-comment-splice?
  cc-pp-location-enabled @ cc-pp-line-continuation? and ;

\ cc-pp-drop-splice ( -- )  Delete the continuation at pos. Its newline goes
\ through the put mode, except that an emitted comment owes it instead:
\ written inside the comment it could end a "//" or split a "*/".
: cc-pp-drop-splice
  cc-prep-advance
  cc-prep-peek [lit] 13 = if, cc-prep-advance then,
  cc-pp-put-mode @ put-emit = if,
    cc-prep-advance [lit] 1 cc-pp-pending-nl +!
  else, cc-pp-take then, ;

\ cc-pp-drop-splices ( -- )  Delete a run of continuations.
: cc-pp-drop-splices
  begin, cc-pp-comment-splice? while, cc-pp-drop-splice repeat, ;
```

### Comment and literal boundaries

Block comments stop at their closing delimiter; line comments leave the ending newline for their caller. At end of region, an unterminated block comment raises error 49 only while `cc-pp-line-control` is set, as in guarded directive-prefix and line-control processing. The historical comment's broader promise does not cover ordinary macro-body copying: initialization clears the guard, so a legacy input ending with `#define X /*` can return from this walker without that diagnostic. This is a boundary of the shown control flow, not a claim that the malformed input is valid (`forth-bootstrap/cc/040-cc-prep.fth:477`):

```forth file=cc/040-cc-prep.fth

\ cc-pp-block-comment ( -- )  pos at "/*": walk through the closing "*/",
\ or to EOR.  An unterminated comment in a directive dies with 49.
: cc-pp-block-comment
  cc-pp-take cc-pp-drop-splices cc-pp-take
  begin,
    cc-prep-eor? if,
      cc-pp-line-control @ if, [lit] 49 cc-die then, exit,
    then,
    [char] * [char] / cc-pp-at-spliced? 0=
  while,
    cc-pp-comment-splice? if, cc-pp-drop-splice else, cc-pp-take then,
  repeat,
  cc-pp-take cc-pp-drop-splices cc-pp-take ;

\ cc-pp-line-comment ( -- )  pos at "//": walk to the newline, which is
\ left for the caller.
: cc-pp-line-comment
  begin,
    cc-prep-eor? 0= cc-prep-peek nl <> and
  while,
    cc-pp-comment-splice? if, cc-pp-drop-splice else, cc-pp-take then,
  repeat, ;
```

Literal copying removes LF continuations and handles escapes, so an escaped quote does not close the literal. The removed newlines are owed; this copier does not support ordinary CRLF literal splicing (`forth-bootstrap/cc/040-cc-prep.fth:500`):

```forth file=cc/040-cc-prep.fth

\ cc-pp-literal-splices ( -- )  Remove physical continuations before
\ interpreting escapes, including between a backslash and its escaped byte.
: cc-pp-literal-splices
  begin, backslash nl cc-prep-at? while,
    cc-prep-advance cc-prep-advance
    cc-pp-put-mode @ put-drop <> if, [lit] 1 cc-pp-pending-nl +! then,
  repeat, ;

\ cc-pp-literal ( -- )  pos at a ' or ": walk through the closing quote.
\ A backslash takes the next logical byte with it; an unclosed literal
\ stops at the end of its logical line.
: cc-pp-literal
  cc-prep-peek cc-pp-take                          ( q )
  begin,
    cc-pp-literal-splices
    cc-prep-eor? if, drop exit, then,
    cc-prep-peek nl = if, drop exit, then,
    cc-prep-peek backslash = if,
      cc-pp-take cc-pp-literal-splices
      cc-prep-eor? 0= if, cc-pp-take then,
    else,
      cc-prep-peek over = if, drop cc-pp-take exit, then,
      cc-pp-take
    then,
  again, ;
```

### Directive slices and names

Finishing a directive must step over a trailing block comment whole, even across physical lines. Otherwise a leftover comment closer would leak into the rewritten source (`forth-bootstrap/cc/040-cc-prep.fth:526`):

```forth file=cc/040-cc-prep.fth

\ cc-prep-skip-to-eol ( -- )  Step to the end of the line: pos stops on the
\ newline (or at EOR).  A /* comment */ or a backslash-newline on the way
\ is stepped over whole, and the newlines inside it are owed.  In the
\ direct profile a // comment is walked too, so a "/*" inside it is inert.
: cc-prep-skip-to-eol
  put-count cc-pp-put-mode !
  begin,
    cc-prep-eor? 0= cc-prep-peek nl <> and
  while,
    [char] / [char] * cc-pp-at-spliced? if,
      cc-pp-block-comment
    else,
      cc-pp-location-enabled @ [char] / [char] / cc-pp-at-spliced? and if,
        cc-pp-line-comment
      else,
        backslash nl cc-prep-at? if, cc-prep-advance then,
        cc-pp-take
      then,
    then,
  repeat, ;
```

A continuation joining nonblank bytes could change a token. In a line-control operand, this boundary check rejects that unsupported join rather than treating it as harmless whitespace (`forth-bootstrap/cc/040-cc-prep.fth:547`):

```forth file=cc/040-cc-prep.fth

\ The shared text engine does not join split identifier tokens or splice
\ line comments. In #line operands fail closed on those phase-two forms;
\ whitespace-separated and literal continuations retain their usual path.
: cc-pp-line-splice-boundary
  cc-pp-line-control @ 0= if, exit, then,
  cc-prep-src-pos @ 0= if, exit, then,
  cc-prep-src-addr @ cc-prep-src-pos @ + 1- c@ space? if, exit, then,
  cc-prep-src-pos @ [lit] 2 + cc-prep-src-len @ >= if, exit, then,
  cc-prep-src-addr @ cc-prep-src-pos @ + [lit] 2 + c@ space? 0= if,
    [lit] 49 cc-die
  then, ;
```

`cc-pp-line-slice` returns the unexpanded operand through its logical line end. Comments and continuations remain in the slice for the subsequent expansion walk to account for (`forth-bootstrap/cc/040-cc-prep.fth:563`):

```forth file=cc/040-cc-prep.fth

\ cc-pp-line-slice ( -- a u )  The rest of the directive line, from pos to
\ (not including) the newline that ends it; pos moves there.  Comments and
\ backslash-newlines stay in the slice (scanning it counts their newlines).
: cc-pp-line-slice
  cc-prep-src-addr @ cc-prep-src-pos @ +  cc-prep-src-pos @   ( a start )
  put-drop cc-pp-put-mode !
  begin,
    cc-prep-eor? 0= cc-prep-peek nl <> and
  while,
    cc-prep-peek dup [char] " = swap [char] ' = or if,
      cc-pp-literal
    else,
      [char] / [char] / cc-pp-at-spliced? if,
        cc-pp-line-comment
      else,
        [char] / [char] * cc-pp-at-spliced? if,
          cc-pp-block-comment
        else,
          backslash nl cc-prep-at? if,
            cc-pp-line-splice-boundary cc-prep-advance
          then,
          cc-prep-advance
        then,
      then,
    then,
  repeat,
  cc-prep-src-pos @ swap - ;
```

### Identifiers and preprocessing numbers

An identifier is retained as an address-length slice of the current region. Reading advances the cursor past the name without copying it (`forth-bootstrap/cc/040-cc-prep.fth:587`):

```forth file=cc/040-cc-prep.fth

\ ===========================================================================
\ Identifiers and numbers
\ ===========================================================================

variable cc-prep-ident-addr
variable cc-prep-ident-len

\ cc-prep-read-ident ( -- )  Reads an identifier at cc-prep-src-pos into
\ cc-prep-ident-{addr,len}.  Pre: peek is ident-start.  Advances pos past it.
: cc-prep-read-ident
  cc-prep-src-addr @ cc-prep-src-pos @ +  cc-prep-ident-addr !
  cc-prep-src-pos @                                ( start )
  begin,
    cc-prep-eor? 0=
    cc-prep-peek ident-cont? and
  while,
    cc-prep-advance
  repeat,
  cc-prep-src-pos @ swap -  cc-prep-ident-len ! ;

```

Directive-name comparison checks length before bytes. Required-name and closing-parenthesis helpers reject malformed operands at the point where the grammar needs them (`forth-bootstrap/cc/040-cc-prep.fth:608`):

```forth file=cc/040-cc-prep.fth
\ cc-prep-ident= ( a u -- f )  True if the identifier just read is a u.
: cc-prep-ident=
  dup cc-prep-ident-len @ = if,
    cc-prep-ident-addr @ swap bytes-eq
  else,
    2drop [lit] 0
  then, ;

\ cc-pp-need-name ( -- )  Read the name a directive requires (#ifdef NAME,
\ defined NAME) into cc-prep-ident-{addr,len}; die 42 if there is none.
: cc-pp-need-name
  cc-prep-skip-blanks
  cc-prep-peek ident-start? 0= if, [lit] 42 cc-die then,
  cc-prep-read-ident ;

\ cc-pp-need-rparen ( -- )  Step past the ')' that closes `defined(NAME`
\ or a #define's parameter list; die 47 if it isn't there.
: cc-pp-need-rparen
  cc-prep-skip-blanks
  cc-prep-peek [char] ) <> if, [lit] 47 cc-die then,
  cc-prep-advance ;

```

A preprocessing number is copied with its letters and dots, so a suffix or hexadecimal digit sequence is not mistaken for a macro name. This bounded scan does not absorb exponent signs (`forth-bootstrap/cc/040-cc-prep.fth:630`):

```forth file=cc/040-cc-prep.fth
\ cc-pp-copy-number ( -- )  A number is copied whole, suffix and all, so
\ the letters in 0x1F or 10UL are never taken for an identifier.
: cc-pp-copy-number
  begin,
    cc-prep-peek ident-cont?  cc-prep-peek [char] . = or
  while,
    cc-prep-peek cc-prep-emit-byte cc-prep-advance
  repeat, ;

```

<details>
<summary>Include files: path search, source locations, and bounded storage</summary>

An include suspends the current region, reads another file, and restores
the caller at its next line. This section supplies the file lookup and
location bookkeeping around that operation. The macro-expansion section
that follows uses the same region discipline with text already in memory.

## `#include` and its bounded file pool

An included file must remain live while its nested includes are scanned. Legacy mode assigns a fixed slot to each nesting depth (`forth-bootstrap/cc/040-cc-prep.fth:639`):

```forth file=cc/040-cc-prep.fth
\ ===========================================================================
\ Include buffer pool (4 slots × 256 KiB).
\ ===========================================================================

[lit] 262144 constant cc-prep-inc-slot-cap
[lit] 4      constant cc-prep-inc-slot-count

create cc-prep-inc-pool  cc-prep-inc-slot-cap cc-prep-inc-slot-count * allot
variable cc-prep-inc-depth
variable cc-prep-inc-top                         \ direct-mode bytes in use
[lit] 32 constant cc-prep-direct-depth

\ cc-prep-inc-slot-addr ( depth -- addr )
: cc-prep-inc-slot-addr
  cc-prep-inc-slot-cap *  cc-prep-inc-pool + ;
```

Direct mode packs live files at `cc-prep-inc-top` instead of reserving a slot per file. Its selected pool has an address and capacity; the direct-GCC workspace supplies a separately mapped pool (`forth-bootstrap/cc/040-cc-prep.fth:654`):

```forth file=cc/040-cc-prep.fth

\ Direct mode packs the live include stack at cc-prep-inc-top into a
\ selected pool: by default the dictionary pool above, 1 MiB.  The
\ direct-GCC workspace maps a separate pool instead.  Every live byte
\ outside a directive or skipped group is also copied into the expanded
\ source, so the pool shares that buffer's bound (030): 7 MiB, from the
\ binutils 2.30 i386-opc.c measurement (5,334,945 bytes live in i386-tbl.h,
\ 5,415,887 expanded) plus 25%, rounded up to whole MiB.
cc-src-direct-cap constant cc-prep-inc-direct-cap
variable cc-prep-inc-buffer
variable cc-prep-inc-limit
variable cc-prep-inc-direct-base
: cc-prep-inc-buf ( -- address ) cc-prep-inc-buffer @ ;
: cc-prep-inc-cap ( -- bytes ) cc-prep-inc-limit @ ;

```

The default selector restores every macro-array pointer and the dictionary include pool together. It neither migrates live data nor resets counts (`forth-bootstrap/cc/040-cc-prep.fth:669`):

```forth file=cc/040-cc-prep.fth
\ Workspace selection for the macro arrays above and the packed include
\ pool.  Neither selector migrates live data or resets a count.
: cc-prep-default-workspace ( -- )
  cc-macro-default-cap cc-macro-limit !
  cc-macro-default-name-addr cc-macro-name-addr-buffer !
  cc-macro-default-name-len cc-macro-name-len-buffer !
  cc-macro-default-body-addr cc-macro-body-addr-buffer !
  cc-macro-default-body-len cc-macro-body-len-buffer !
  cc-macro-default-params cc-macro-params-buffer !
  cc-macro-default-busy cc-macro-busy-buffer !
  cc-prep-inc-pool cc-prep-inc-buffer !
  cc-prep-inc-slot-cap cc-prep-inc-slot-count * cc-prep-inc-limit !
;
cc-prep-default-workspace
```

The direct selector maps storage only on first use, then selects disjoint slices for all macro fields and the packed include pool. Capacity and addresses must describe the same workspace (`forth-bootstrap/cc/040-cc-prep.fth:683`):

```forth file=cc/040-cc-prep.fth
: cc-prep-direct-workspace ( -- )
  cc-macro-direct-base @ 0= if,
    cc-macro-direct-cap [lit] 48 *
    [lit] 34 cc-workspace-map cc-macro-direct-base !
  then,
  cc-prep-inc-direct-base @ 0= if,
    cc-prep-inc-direct-cap [lit] 32 cc-workspace-map cc-prep-inc-direct-base !
  then,
  cc-macro-direct-cap cc-macro-limit !
  cc-macro-direct-base @ cc-macro-direct-cap [lit] 0 * + cc-macro-name-addr-buffer !
  cc-macro-direct-base @ cc-macro-direct-cap [lit] 8 * + cc-macro-name-len-buffer !
  cc-macro-direct-base @ cc-macro-direct-cap [lit] 16 * + cc-macro-body-addr-buffer !
  cc-macro-direct-base @ cc-macro-direct-cap [lit] 24 * + cc-macro-body-len-buffer !
  cc-macro-direct-base @ cc-macro-direct-cap [lit] 32 * + cc-macro-params-buffer !
  cc-macro-direct-base @ cc-macro-direct-cap [lit] 40 * + cc-macro-busy-buffer !
  cc-prep-inc-direct-base @ cc-prep-inc-buffer !
  cc-prep-inc-direct-cap cc-prep-inc-limit !
;
```

### Building include paths

A bounded path builder appends bytes while reserving room for a terminator. The legacy fallback prefix is stored alongside that builder (`forth-bootstrap/cc/040-cc-prep.fth:701`):

```forth file=cc/040-cc-prep.fth

\ ===========================================================================
\ Path building.  Concat prefix + name + NUL into cc-prep-path-buf.
\ ===========================================================================

[lit] 1024 constant cc-prep-path-cap
create cc-prep-path-buf  cc-prep-path-cap allot
variable cc-prep-path-out

create cc-prep-tests-prefix  s, tests/cc/

[lit] 9 constant cc-prep-tests-prefix-len

\ cc-prep-append ( src-addr src-len -- )  Append bytes to cc-prep-path-buf.
\ Dies with code 33 if they and the closing NUL would not fit.
: cc-prep-append
  cc-prep-path-out @ over + 1+ cc-prep-path-cap [lit] 33 cc-check-cap
  begin,
    dup [lit] 0 >
  while,
    over c@
    cc-prep-path-buf cc-prep-path-out @ + c!
    [lit] 1 cc-prep-path-out +!
    swap 1+ swap
    1-
  repeat,
  drop drop ;
```

`cc-prep-build-path` joins a prefix and name. Direct configuration separately records include directories, the main source pathname and each live file's physical path (`forth-bootstrap/cc/040-cc-prep.fth:731`):

```forth file=cc/040-cc-prep.fth

\ cc-prep-build-path ( pa pu na nu -- )
\ Build NUL-terminated cc-prep-path-buf = prefix + name + 0.
: cc-prep-build-path
  >r >r                                            ( pa pu ; R: nu na )
  [lit] 0 cc-prep-path-out !
  cc-prep-append                                   \ append prefix
  r> r>                                            ( na nu )
  cc-prep-append                                   \ append name
  [lit] 0 cc-prep-path-buf cc-prep-path-out @ + c! ;  \ NUL

\ Direct mode keeps include directories explicit and relative to the process
\ working directory.  Quote includes first search the including file's
\ directory; angle includes search only the configured directories.
[lit] 32 constant cc-prep-include-max
create cc-prep-include-dirs  cc-prep-include-max cc-prep-path-cap * allot
create cc-prep-include-lens  cc-prep-include-max [lit] 8 * allot
variable cc-prep-include-count
create cc-prep-source-path  cc-prep-path-cap allot
variable cc-prep-source-len
create cc-prep-file-paths  cc-prep-direct-depth 1+ cc-prep-path-cap * allot
create cc-prep-file-lens   cc-prep-direct-depth 1+ [lit] 8 * allot
variable cc-prep-inc-mode                         \ 1=quote, 2=angle
```

### Physical and logical locations

A replacement inherits its invocation location, while a raw argument can recover its own physical line. Each include depth keeps an independent physical cursor, logical offset and optional logical filename (`forth-bootstrap/cc/040-cc-prep.fth:751`):

```forth file=cc/040-cc-prep.fth

\ Source provenance is separate from flattened diagnostic line numbers.
\ Each live file caches a physical-line cursor. Macro replacement text keeps
\ its invocation location; raw argument slices can recover their own lines.
\ (cc-pp-location-enabled is declared with the comment walkers above.)
variable cc-pp-location-line
variable cc-pp-location-rescan
variable cc-pp-location-depth
variable cc-pp-location-object-root
: cc-pp-location-begin ( object-like? -- )
  cc-pp-location-depth @ 0= if, cc-pp-location-object-root ! else, drop then,
  [lit] 1 cc-pp-location-depth +! ;
: cc-pp-location-end [lit] 1 cc-pp-location-depth -! ;
create cc-pp-file-base    cc-prep-direct-depth 1+ [lit] 8 * allot
create cc-pp-file-end     cc-prep-direct-depth 1+ [lit] 8 * allot
create cc-pp-file-cursor  cc-prep-direct-depth 1+ [lit] 8 * allot
create cc-pp-file-line    cc-prep-direct-depth 1+ [lit] 8 * allot
\ Physical cursors never change for #line: an offset supplies the logical
\ line, including when argument prescan revisits an earlier source slice.
\ Virtual names never change cc-prep-file-paths, used for include search.
create cc-pp-file-offset  cc-prep-direct-depth 1+ [lit] 8 * allot
create cc-pp-file-names   cc-prep-direct-depth 1+ cc-prep-path-cap * allot
create cc-pp-file-name-len cc-prep-direct-depth 1+ [lit] 8 * allot
```

Entering a file starts its physical cursor and clears its logical override. A virtual filename used by `#line` never changes the path used for relative include search (`forth-bootstrap/cc/040-cc-prep.fth:774`):

```forth file=cc/040-cc-prep.fth
: cc-pp-logical-name
  cc-prep-inc-depth @ cc-prep-path-cap * cc-pp-file-names + ;
: cc-pp-location-cell  cc-prep-inc-depth @ swap cell[] ;
: cc-pp-location-enter
  cc-prep-src-addr @ dup cc-pp-file-base cc-pp-location-cell !
  dup cc-pp-file-cursor cc-pp-location-cell !
  cc-prep-src-len @ + cc-pp-file-end cc-pp-location-cell !
  [lit] 1 cc-pp-file-line cc-pp-location-cell !
  [lit] 0 cc-pp-file-offset cc-pp-location-cell !
  true cc-pp-file-name-len cc-pp-location-cell ! ;
```

Argument prescan may revisit an earlier slice. `cc-pp-location-at` subtracts or adds the intervening newlines from its cached cursor, then applies the logical offset (`forth-bootstrap/cc/040-cc-prep.fth:784`):

```forth file=cc/040-cc-prep.fth
: cc-pp-location-at ( address -- )
  cc-pp-location-enabled @ 0= cc-pp-location-rescan @ or if, drop exit, then,
  dup cc-pp-file-base cc-pp-location-cell @ < if, drop exit, then,
  dup cc-pp-file-end cc-pp-location-cell @ >= if, drop exit, then,
  dup cc-pp-file-cursor cc-pp-location-cell @ < if,
    \ Behind the cursor: take back the newlines between the two, rather
    \ than counting again from the start of the file.
    cc-pp-file-cursor cc-pp-location-cell @            ( address cursor )
    begin, 2dup < while,
      1- dup c@ nl = if, true cc-pp-file-line cc-pp-location-cell +! then,
    repeat,
    cc-pp-file-cursor cc-pp-location-cell !
  then,
  cc-pp-file-cursor cc-pp-location-cell @
  begin, 2dup > while,
    dup c@ nl = if, [lit] 1 cc-pp-file-line cc-pp-location-cell +! then,
    1+
  repeat,
  nip cc-pp-file-cursor cc-pp-location-cell !
  cc-pp-file-line cc-pp-location-cell @
  cc-pp-file-offset cc-pp-location-cell @ + cc-pp-location-line ! ;
```

### Configuring and searching directories

Configuration reset clears direct mode, registered directories and the source name. Copying paths includes a fresh terminator so later searches do not depend on old buffer contents (`forth-bootstrap/cc/040-cc-prep.fth:805`):

```forth file=cc/040-cc-prep.fth

: cc-prep-config-reset
  [lit] 0 cc-prep-direct !  [lit] 0 cc-prep-include-count !
  [lit] 0 cc-prep-source-len ! ;

\ cc-prep-copy-path ( a u dst -- )  Copy a path including a new terminator.
: cc-prep-copy-path
  >r dup cc-prep-path-cap 1- [lit] 33 cc-check-cap
  begin, dup while,
    over c@ r@ c!  r> 1+ >r  swap 1+ swap 1-
  repeat,
  2drop [lit] 0 r> c! ;

: cc-prep-source-name
  dup cc-prep-source-len ! cc-prep-source-path cc-prep-copy-path ;
```

Registered directories receive a trailing slash when needed. Their lengths and bytes are kept together for ordered searches (`forth-bootstrap/cc/040-cc-prep.fth:820`):

```forth file=cc/040-cc-prep.fth

: cc-prep-add-include
  cc-prep-include-count @ 1+ cc-prep-include-max [lit] 33 cc-check-cap
  [lit] 0 cc-prep-path-out ! cc-prep-append
  cc-prep-path-out @ if,
    cc-prep-path-buf cc-prep-path-out @ + 1- c@ [char] / <> if,
      [char] / cc-prep-path-buf cc-prep-path-out @ + c!
      [lit] 1 cc-prep-path-out +!
    then,
  then,
  cc-prep-path-out @ dup cc-prep-include-count @ cc-prep-include-lens cell[] !
  cc-prep-path-buf swap
  cc-prep-include-count @ cc-prep-path-cap * cc-prep-include-dirs +
  cc-prep-copy-path
  [lit] 1 cc-prep-include-count +! ;
```

Relative quote includes start from the includer's physical directory. The successful path is copied into the next depth's record before the shared path buffer is reused (`forth-bootstrap/cc/040-cc-prep.fth:835`):

```forth file=cc/040-cc-prep.fth

\ cc-prep-directory ( a u -- a dir-u )  Prefix through the final slash.
: cc-prep-directory
  begin, dup while,
    2dup + 1- c@ [char] / = if, exit, then,
    1-
  repeat, ;

: cc-prep-current-path
  cc-prep-inc-depth @ cc-prep-path-cap * cc-prep-file-paths + ;

: cc-prep-record-path
  cc-prep-path-out @ cc-prep-inc-depth @ 1+ cc-prep-file-lens cell[] !
  cc-prep-path-buf cc-prep-path-out @
  cc-prep-inc-depth @ 1+ cc-prep-path-cap * cc-prep-file-paths +
  cc-prep-copy-path ;
```

Absolute include names are already complete. Otherwise, a quoted name first tries the includer's directory; failure falls through to the configured search list (`forth-bootstrap/cc/040-cc-prep.fth:851`):

```forth file=cc/040-cc-prep.fth

\ ===========================================================================
\ File loading.  Reads a file into the current include-pool slot.
\ ===========================================================================
\ Linux O_RDONLY = 0.
: cc-prep-try-open  [lit] 0 [lit] 0 open ;         ( path-addr -- fd )

variable cc-prep-load-name-a
variable cc-prep-load-name-u

\ cc-prep-load-file ( path-a path-u -- buf-a buf-u )
\ Legacy mode tries the literal name then tests/cc/<name>, using a slot
\ per depth.  Direct mode uses the includer and explicit directories,
\ packing live files into the selected pool.  Dies with 31 at the depth
\ limit, 30 if no path opens, and 32 when the slot or pool is full.
: cc-prep-open-include
  \ Absolute names are already complete in either include form.
  cc-prep-load-name-u @ if,
    cc-prep-load-name-a @ c@ [char] / = if,
      [lit] 0 [lit] 0 cc-prep-load-name-a @ cc-prep-load-name-u @
      cc-prep-build-path cc-prep-path-buf cc-prep-try-open exit,
    then,
  then,
  cc-prep-inc-mode @ [lit] 1 = if,
    cc-prep-current-path cc-prep-inc-depth @ cc-prep-file-lens cell[] @
    cc-prep-directory cc-prep-load-name-a @ cc-prep-load-name-u @
    cc-prep-build-path cc-prep-path-buf cc-prep-try-open
    dup 0< 0= if, exit, then, drop
  then,
```

The remaining search walks registered directories in order and returns the first successful descriptor. Exhaustion returns failure to the loader (`forth-bootstrap/cc/040-cc-prep.fth:880`):

```forth file=cc/040-cc-prep.fth
  [lit] 0
  begin, dup cc-prep-include-count @ < while,
    dup cc-prep-path-cap * cc-prep-include-dirs +
    over cc-prep-include-lens cell[] @
    cc-prep-load-name-a @ cc-prep-load-name-u @ cc-prep-build-path
    cc-prep-path-buf cc-prep-try-open
    dup 0< 0= if, nip exit, then, drop 1+
  repeat,
  drop true ;
```

### Loading an include region

The loader checks nesting before opening anything. Legacy mode tries the literal name and then the test-directory fallback; direct mode delegates to the explicit search policy (`forth-bootstrap/cc/040-cc-prep.fth:889`):

```forth file=cc/040-cc-prep.fth

: cc-prep-load-file
  cc-prep-load-name-u ! cc-prep-load-name-a !
  cc-prep-inc-depth @ 1+
  cc-prep-direct @ if, cc-prep-direct-depth else, cc-prep-inc-slot-count then,
  [lit] 31 cc-check-cap
  cc-prep-direct @ if,
    cc-prep-open-include
  else,
    [lit] 0 [lit] 0 cc-prep-load-name-a @ cc-prep-load-name-u @
    cc-prep-build-path cc-prep-path-buf cc-prep-try-open
    dup 0< if,
      drop cc-prep-tests-prefix cc-prep-tests-prefix-len
      cc-prep-load-name-a @ cc-prep-load-name-u @
      cc-prep-build-path cc-prep-path-buf cc-prep-try-open
    then,
  then,
  dup 0< if, drop [lit] 30 cc-die then,
```

Direct files occupy the free tail of the packed pool; legacy files occupy their depth's slot. `cc-read-all` supplies the bytes, and the descriptor is closed before scanning begins (`forth-bootstrap/cc/040-cc-prep.fth:907`):

```forth file=cc/040-cc-prep.fth
  >r
  cc-prep-direct @ if,
    cc-prep-record-path
    cc-prep-inc-buf cc-prep-inc-top @ +
    r@ over cc-prep-inc-cap
    cc-prep-inc-top @ - [lit] 32 cc-read-all
    dup cc-prep-inc-top +!
  else,
    cc-prep-inc-depth @ cc-prep-inc-slot-addr
    r@ over cc-prep-inc-slot-cap [lit] 32 cc-read-all
  then,
  r> close drop ;
```

</details>

## Macro expansion

Return to `SQUARE(ROWS)`. The sink and region helpers are in place; now the
walker needs to invoke them recursively without losing its caller.

Expansion is walking: `cc-pp-expand-text` parks the active region, scans a replacement as non-file text and restores the caller. Deferred words (Chapter 25) connect the mutually recursive walker and dispatcher. Separator blanks prevent an expansion from accidentally creating a different token (`forth-bootstrap/cc/040-cc-prep.fth:937`):

```forth file=cc/040-cc-prep.fth

\ ===========================================================================
\ Scanning: the main walker and macro expansion
\ ===========================================================================
\ cc-pp-scan walks the current region to its end.  A macro use pushes the
\ replacement as a new region and scans it (cc-pp-expand-text), which
\ calls cc-pp-scan again: the two are mutually recursive, and the
\ directive dispatcher (defined further on) is reached from the walker as
\ well, so both go through deferred words (010-lib.fth).

defer cc-pp-scan-fwd
defer cc-prep-handle-directive-fwd
defer cc-pp-rescan-tail-fwd

\ cc-pp-expand-text ( a u -- )  Scan the text a u (macro text, never a
\ file) as a region of its own, then return to the region we were in.  A
\ blank on either side keeps the replacement from gluing onto its
\ neighbours (`-N` with N defined as -1 is `- -1`, not `--1`).
: cc-pp-expand-text
  cc-prep-src-addr @ >r  cc-prep-src-len @ >r  cc-prep-src-pos @ >r
  cc-prep-in-file @ >r  cc-prep-at-line-start @ >r
  cc-prep-src-len ! cc-prep-src-addr !  [lit] 0 cc-prep-src-pos !
  [lit] 0 cc-prep-in-file !
  bl cc-prep-emit-byte  cc-pp-scan-fwd  bl cc-prep-emit-byte
  r> cc-prep-at-line-start !  r> cc-prep-in-file !
  r> cc-prep-src-pos !  r> cc-prep-src-len !  r> cc-prep-src-addr ! ;
```

Inside a conditional expression, `defined NAME` must test the macro table before `NAME` expands. `cc-pp-in-if` enables that special treatment only while expanding such an operand (`forth-bootstrap/cc/040-cc-prep.fth:945`):

```forth file=cc/040-cc-prep.fth

\ ---------------------------------------------------------------------------
\ `defined` in #if and #elif
\ ---------------------------------------------------------------------------
\ While an #if line is being expanded, cc-pp-in-if is true and
\ `defined NAME` / `defined(NAME)` becomes 1 or 0, before NAME itself could
\ be expanded.

variable cc-pp-in-if
create cc-pp-n-defined  s, defined

\ cc-pp-defined ( -- )  `defined` has just been read.
: cc-pp-defined
  cc-prep-skip-blanks
  cc-prep-peek lparen = dup if, cc-prep-advance then,
  cc-pp-need-name
  cc-prep-ident-addr @ cc-prep-ident-len @ cc-macro-find 0< 0=   ( paren? f )
  swap if, cc-pp-need-rparen then,
  if, [char] 1 else, [char] 0 then, cc-prep-emit-byte ;
```

A function-like macro name becomes a call only when an opening parenthesis follows. Lookahead can cross whitespace and continuations, but restores the cursor if no call is found (`forth-bootstrap/cc/040-cc-prep.fth:964`):

```forth file=cc/040-cc-prep.fth

\ ---------------------------------------------------------------------------
\ Function-like macro calls
\ ---------------------------------------------------------------------------

\ cc-pp-paren-ahead? ( -- f )  After a function-like macro's name: true,
\ with pos past it, if the next thing (blanks, newlines and LF or CRLF
\ continuations skipped) is '('.  Otherwise pos is left where it was, and
\ the name is not a call.
: cc-pp-paren-ahead?
  cc-prep-src-pos @ [lit] 0                        ( pos0 nls )
  begin,
    cc-pp-line-continuation? if,                   \ leave pos at its nl
      cc-prep-advance cc-prep-peek [lit] 13 = if, cc-prep-advance then,
    then,
    cc-prep-peek bl =  cc-prep-peek tab = or  cc-prep-peek nl = or
  while,
    cc-prep-peek nl = if, 1+ then,
    cc-prep-advance
  repeat,
  cc-prep-peek lparen = if,
    cc-pp-pending-nl +!  drop  cc-prep-advance  true
  else,
    drop  cc-prep-src-pos !  [lit] 0
  then, ;
```

### Collecting arguments

Argument records point into the current region. The collector tracks the current slice and parenthesis depth, recording a slice only when its boundary is known (`forth-bootstrap/cc/040-cc-prep.fth:989`):

```forth file=cc/040-cc-prep.fth

\ A call's arguments are recorded as (addr, len) pairs, 16 bytes each, in a
\ record block taken from the scratch space.
[lit] 16 constant cc-pp-args-max

variable cc-pp-ca-recs                            \ the record block
variable cc-pp-ca-n                               \ arguments so far
variable cc-pp-ca-depth                           \ ( ) nesting inside the call
variable cc-pp-ca-start                           \ where this argument began

\ cc-pp-ca-record ( -- )  The argument from cc-pp-ca-start to pos is done.
\ Dies with 46 past cc-pp-args-max arguments.
: cc-pp-ca-record
  cc-pp-ca-n @ 1+ cc-pp-args-max [lit] 46 cc-check-cap
  cc-pp-ca-recs @ cc-pp-ca-n @ [lit] 16 * +                 ( rec )
  cc-prep-src-addr @ cc-pp-ca-start @ + over !
  cc-prep-src-pos @ cc-pp-ca-start @ -  swap [lit] 8 + !
  [lit] 1 cc-pp-ca-n +! ;

```

Commas inside literals, comments or nested parentheses do not separate arguments. The collector delegates those constructs to the shared walkers before testing a comma at the call's outer depth (`forth-bootstrap/cc/040-cc-prep.fth:1008`):

```forth file=cc/040-cc-prep.fth
\ cc-pp-collect-args ( recs -- n )  pos is just past the call's '('.  Split
\ the arguments at the commas outside inner parentheses, record each as a
\ slice of the region, and stop past the closing ')'.  A call that runs off
\ the end of its region dies with 44.
: cc-pp-collect-args
  cc-pp-ca-recs !  [lit] 0 cc-pp-ca-n !  [lit] 1 cc-pp-ca-depth !
  cc-prep-src-pos @ cc-pp-ca-start !
  put-drop cc-pp-put-mode !
  begin,
    cc-prep-eor? if, [lit] 44 cc-die then,
    cc-prep-peek
    dup [char] " =  over [char] ' = or if, drop cc-pp-literal else,
    [char] / [char] * cc-pp-at-spliced? if, drop cc-pp-block-comment else,
    [char] / [char] / cc-pp-at-spliced? if, drop cc-pp-line-comment else,
    dup lparen = if, drop [lit] 1 cc-pp-ca-depth +! cc-prep-advance else,
    dup [char] , =  cc-pp-ca-depth @ [lit] 1 = and if,
      drop cc-pp-ca-record cc-prep-advance
      cc-prep-src-pos @ cc-pp-ca-start !
    else,
```

The closing parenthesis finishes the final argument only when the nested depth returns to the call boundary. Running out of region first is a malformed call (`forth-bootstrap/cc/040-cc-prep.fth:1027`):

```forth file=cc/040-cc-prep.fth
    [char] ) = if,
      [lit] 1 cc-pp-ca-depth -!
      cc-pp-ca-depth @ 0= if,
        cc-pp-ca-record cc-prep-advance cc-pp-ca-n @ exit,
      then,
      cc-prep-advance
    else,
      cc-prep-advance
    then, then, then, then, then, then,
  again, ;

```

### Raw and expanded arguments

For `SQUARE(ROWS)`, collection has found one slice, `ROWS`, and left the
source cursor after the call's closing parenthesis. Prescan will produce
the text containing `4`. Substitution must be able to use that completed
text twice without advancing or destroying it after the first `x`.

Ordinary substitution needs expanded arguments, while stringification and pasting need raw spelling. The duplicated record block preserves the original slices before expansion replaces their addresses and lengths (`forth-bootstrap/cc/040-cc-prep.fth:1038`):

```forth file=cc/040-cc-prep.fth
\ cc-pp-expand-args ( recs n -- )  Expand every argument fully, before it
\ is substituted (C's rule), and record the expanded text in its place.
: cc-pp-expand-args
  begin, dup while,
    1- 2dup [lit] 16 * +                           ( recs k rec )
    dup >r  dup @ swap [lit] 8 + @                 ( recs k a u ; R: rec )
    cc-pp-temp-begin cc-pp-expand-text cc-pp-temp-end
    r@ [lit] 8 + !  r> !
  repeat,
  2drop ;

\ Argument records retain both spellings: ordinary substitution uses the
\ fully expanded argument; # and ## use its unexpanded spelling.
: cc-pp-duplicate-args
  [lit] 16 * dup cc-pp-scratch-alloc >r
  r@ swap
  begin, dup while,
    [lit] 8 - >r over r@ + @ over r@ + ! r>
  repeat,
  drop 2drop r> ;

```

Legacy substitution replaces each encoded parameter with expanded argument text between separator blanks. Missing arguments contribute no bytes, and ordinary body bytes pass through (`forth-bootstrap/cc/040-cc-prep.fth:1059`):

```forth file=cc/040-cc-prep.fth
variable cc-pp-sub-raw
variable cc-pp-sub-recs
variable cc-pp-sub-n

\ cc-pp-substitute ( a u -- )  Write a function-like macro's body, each
\ parameter marker (1, k) replaced by argument k's expanded text between
\ blanks; a parameter with no argument is empty.
: cc-pp-substitute-legacy
  begin, dup while,
    over c@ [lit] 1 = if,
      over 1+ c@                                   ( a u k )
      dup cc-pp-sub-n @ < if,
        [lit] 16 * cc-pp-sub-recs @ +
        bl cc-prep-emit-byte
        dup @ swap [lit] 8 + @ cc-pp-emit-bytes
        bl cc-prep-emit-byte
      else,
        drop
      then,
      swap [lit] 2 + swap [lit] 2 -
    else,
      over c@ cc-prep-emit-byte
      swap 1+ swap 1-
    then,
  repeat,
  2drop ;

```

### Stringification

Our legacy `SQUARE` uses the expanded record at both parameter positions.
The next direct-profile branches explain why the raw record is retained
too: stringifying that same argument needs the spelling `ROWS`, not the
replacement `4`. Keep the two records distinct as the substitution code
chooses between them; the legacy checkpoint does not exercise `#` or `##`.

Stringification needs its own cursor and quote state because it reads raw argument spelling. Edge trimming serves paste operands; the string-byte writer escapes quotes and backslashes for the new C literal (`forth-bootstrap/cc/040-cc-prep.fth:1086`):

```forth file=cc/040-cc-prep.fth
\ cc-pp-trim-slice ( a u -- a' u' )  Strip argument-edge whitespace.
: cc-pp-trim-slice
  begin, dup if, over c@ space? else, [lit] 0 then, while,
    swap 1+ swap 1-
  repeat,
  begin, dup if, 2dup + 1- c@ space? else, [lit] 0 then, while, 1- repeat, ;

variable cc-pp-string-quote
variable cc-pp-string-escape
variable cc-pp-string-space
variable cc-pp-string-start

: cc-pp-string-byte
  dup [char] " = over backslash = or if, backslash cc-prep-emit-byte then,
  cc-prep-emit-byte ;

variable cc-pp-string-a
variable cc-pp-string-u
: cc-pp-string-peek  cc-pp-string-a @ c@ ;
: cc-pp-string-step
  [lit] 1 cc-pp-string-a +! [lit] 1 cc-pp-string-u -! ;
: cc-pp-string-at?
  cc-pp-string-u @ [lit] 1 > if,
    cc-pp-string-a @ 1+ c@ = swap cc-pp-string-peek = and
  else, 2drop [lit] 0 then, ;

```

Comments outside literal tokens contribute whitespace during stringification. The comment walker consumes their contents so embedded quotes cannot affect string state (`forth-bootstrap/cc/040-cc-prep.fth:1112`):

```forth file=cc/040-cc-prep.fth
: cc-pp-string-comment
  [char] / [char] * cc-pp-string-at? if,
    cc-pp-string-step cc-pp-string-step
    begin, cc-pp-string-u @ while,
      [char] * [char] / cc-pp-string-at? if,
        cc-pp-string-step cc-pp-string-step exit,
      then,
      cc-pp-string-step
    repeat,
  else,
    begin, cc-pp-string-u @ if, cc-pp-string-peek nl <> else, [lit] 0 then,
    while, cc-pp-string-step repeat,
  then, ;

```

The opening of `cc-pp-stringify` clears state and emits the opening quote. Inside a literal token, it preserves spelling while tracking escapes and the matching closing quote (`forth-bootstrap/cc/040-cc-prep.fth:1128`):

```forth file=cc/040-cc-prep.fth
\ # collapses whitespace and comments, preserving literal contents and
\ escaping quotes/backslashes in the resulting C string token.
: cc-pp-stringify
  \ Whitespace is collapsed below, after physical splices are removed.
  cc-pp-string-u ! cc-pp-string-a !
  [lit] 0 cc-pp-string-quote ! [lit] 0 cc-pp-string-escape !
  [lit] 0 cc-pp-string-space ! true cc-pp-string-start !
  [char] " cc-prep-emit-byte
  begin, cc-pp-string-u @ while,
    backslash nl cc-pp-string-at? if,
      \ Raw-argument line accounting is done by argument prescan.
      cc-pp-string-step cc-pp-string-step
    else,
    cc-pp-string-peek
    cc-pp-string-quote @ if,
      dup cc-pp-string-byte
      cc-pp-string-escape @ if,
        drop [lit] 0 cc-pp-string-escape !
      else,
        dup backslash = if, true cc-pp-string-escape ! then,
        cc-pp-string-quote @ = if, [lit] 0 cc-pp-string-quote ! then,
      then,
      cc-pp-string-step
```

Outside literals, pending whitespace and comments collapse to a separator only before another token. That suppresses leading and trailing space before the closing quote is emitted (`forth-bootstrap/cc/040-cc-prep.fth:1149`):

```forth file=cc/040-cc-prep.fth
    else,
      dup space? if,
        drop true cc-pp-string-space ! cc-pp-string-step
      else,
        [char] / [char] * cc-pp-string-at?
        [char] / [char] / cc-pp-string-at? or if,
          drop true cc-pp-string-space ! cc-pp-string-comment
        else,
          cc-pp-string-space @ cc-pp-string-start @ 0= and if,
            bl cc-prep-emit-byte
          then,
          [lit] 0 cc-pp-string-space ! [lit] 0 cc-pp-string-start !
          dup [char] " = over [char] ' = or if, dup cc-pp-string-quote ! then,
          cc-pp-string-byte cc-pp-string-step
        then,
      then,
    then,
    then,
  repeat,
  [char] " cc-prep-emit-byte ;

```

### Choosing which arguments to expand

A parameter next to a paste marker needs its raw spelling. `cc-pp-paste-ahead?` looks beyond body whitespace while `cc-pp-arg-paste` remembers the preceding marker (`forth-bootstrap/cc/040-cc-prep.fth:1173`):

```forth file=cc/040-cc-prep.fth
variable cc-pp-sub-joining

\ The next nonblank body byte after this parameter is the paste marker.
: cc-pp-paste-ahead?
  swap [lit] 2 + swap [lit] 2 - cc-pp-trim-slice
  dup if, drop c@ [lit] 3 = else, 2drop [lit] 0 then, ;

variable cc-pp-arg-index
variable cc-pp-arg-paste
```

Only a parameter used outside stringification and pasting requires prescan. `cc-pp-arg-expanded?` searches the encoded body for such an occurrence, skipping markers and their parameter indices (`forth-bootstrap/cc/040-cc-prep.fth:1180`):

```forth file=cc/040-cc-prep.fth
\ Only parameters used outside # and ## undergo argument prescan.
: cc-pp-arg-expanded?
  cc-pp-arg-index !
  dup cc-macro-body-addr cell[] @ swap cc-macro-body-len cell[] @
  [lit] 0 cc-pp-arg-paste !
  begin, dup while,
    over c@
    dup [lit] 1 = if,
      drop
      over 1+ c@ cc-pp-arg-index @ = if,
        2dup cc-pp-paste-ahead? cc-pp-arg-paste @ or 0= if,
          2drop true exit,
        then,
      then,
      [lit] 0 cc-pp-arg-paste ! swap [lit] 2 + swap [lit] 2 -
    else,
    dup [lit] 2 = if,
      drop [lit] 0 cc-pp-arg-paste ! swap [lit] 2 + swap [lit] 2 -
    else,
    dup [lit] 3 = if,
      drop true cc-pp-arg-paste ! swap 1+ swap 1-
    else,
      space? 0= if, [lit] 0 cc-pp-arg-paste ! then,
      swap 1+ swap 1-
    then, then, then,
  repeat, 2drop [lit] 0 ;

```

An unused or raw-only argument still owes its physical newlines. The selective expansion loop either expands its slice or counts those newlines, keeping the macro index safe across nested calls (`forth-bootstrap/cc/040-cc-prep.fth:1206`):

```forth file=cc/040-cc-prep.fth
\ Arguments used only by #/## (or not used) still owe their source
\ newlines even though no argument prescan walks them.
: cc-pp-count-raw-lines
  begin, dup while,
    over c@ nl = if, [lit] 1 cc-pp-pending-nl +! then,
    swap 1+ swap 1-
  repeat, 2drop ;

\ ( recs n macro -- )  The macro number lives on the return stack while
\ expanding each argument, so nested calls cannot overwrite it.
: cc-pp-expand-used-args
  >r
  begin, dup while,
    1- r@ over cc-pp-arg-expanded? if,
      2dup [lit] 16 * +
      dup >r dup @ swap [lit] 8 + @
      cc-pp-temp-begin cc-pp-expand-text cc-pp-temp-end
      r@ [lit] 8 + ! r> !
    else,
      2dup [lit] 16 * + dup @ swap [lit] 8 + @ cc-pp-count-raw-lines
    then,
  repeat,
  2drop r> drop ;

```

### Direct substitution

`cc-pp-sub-argument` chooses the raw or expanded record. Direct substitution trims the sink before a paste and sends a stringification marker's raw argument through the string encoder (`forth-bootstrap/cc/040-cc-prep.fth:1230`):

```forth file=cc/040-cc-prep.fth
: cc-pp-sub-argument
  \ ( k raw? -- a u )  Missing parameters have empty text.
  if, cc-pp-sub-raw @ else, cc-pp-sub-recs @ then,
  over cc-pp-sub-n @ < if,
    swap [lit] 16 * + dup @ swap [lit] 8 + @
  else, 2drop [lit] 0 [lit] 0 then, ;

: cc-pp-substitute-direct
  [lit] 0 cc-pp-sub-joining !
  begin, dup while,
    over c@
    dup [lit] 3 = if,
      drop
      begin, cc-pp-out-pos @ if,
        cc-pp-out @ cc-pp-out-pos @ + 1- c@ space?
      else, [lit] 0 then, while, [lit] 1 cc-pp-out-pos -! repeat,
      true cc-pp-sub-joining !
      swap 1+ swap 1- cc-pp-trim-slice
    else,
    dup [lit] 2 = if,
      drop over 1+ c@ true cc-pp-sub-argument cc-pp-stringify
      [lit] 0 cc-pp-sub-joining !
      swap [lit] 2 + swap [lit] 2 -
    else,
```

Ordinary parameter markers use expanded text unless either edge is pasted. Marked paste operands are rejected by the earlier copying guard; unmarked joins are rescanned afterward. The selected substitution mode shares the same macro busy cell (`forth-bootstrap/cc/040-cc-prep.fth:1254`):

```forth file=cc/040-cc-prep.fth
    [lit] 1 = if,
      2dup cc-pp-paste-ahead? cc-pp-sub-joining @ or >r
      over 1+ c@ r@ cc-pp-sub-argument
      r@ if,
        cc-pp-trim-slice cc-pp-paste-bytes
      else,
        bl cc-prep-emit-byte cc-pp-emit-bytes bl cc-prep-emit-byte
      then,
      r> drop [lit] 0 cc-pp-sub-joining !
      swap [lit] 2 + swap [lit] 2 -
    else,
      over c@ cc-prep-emit-byte
      [lit] 0 cc-pp-sub-joining ! swap 1+ swap 1-
    then, then, then,
  repeat, 2drop ;

: cc-pp-substitute
  cc-prep-direct @ if, cc-pp-substitute-direct else, cc-pp-substitute-legacy then, ;

\ The busy flag of macro i.
: cc-macro-busy-cell  cc-macro-busy cell[] ;       ( i -- cell )

```

<details>
<summary>Source locations: filename spellings and flattened line maps</summary>

Macro expansion is ready to rescan its substituted text. These helpers
let built-in location macros describe that text's origin; they do not
change the save-and-restore sequence of `SQUARE(ROWS)`.

### Spelling source locations

Dynamic location macros need C text as their result. The number writer emits decimal digits in forward order, and the filename-byte writer escapes bytes that cannot appear literally in a C string (`forth-bootstrap/cc/040-cc-prep.fth:1276`):

```forth file=cc/040-cc-prep.fth
create cc-pp-location-digits [lit] 24 allot
variable cc-pp-location-digit-count
: cc-pp-location-number ( unsigned -- )
  [lit] 0 cc-pp-location-digit-count !
  begin,
    dup [lit] 10 / swap over [lit] 10 * - [char] 0 +
    cc-pp-location-digits cc-pp-location-digit-count @ + c!
    [lit] 1 cc-pp-location-digit-count +!
    dup 0=
  until, drop
  begin, cc-pp-location-digit-count @ while,
    [lit] 1 cc-pp-location-digit-count -!
    cc-pp-location-digits cc-pp-location-digit-count @ + c@ cc-prep-emit-byte
  repeat, ;
: cc-pp-location-string-byte ( byte -- )
  dup [char] " = over backslash = or if,
    backslash cc-prep-emit-byte cc-prep-emit-byte exit,
  then,
  dup [lit] 32 >= over [lit] 127 < and if, cc-prep-emit-byte exit, then,
  backslash cc-prep-emit-byte
  dup [lit] 64 / [char] 0 + cc-prep-emit-byte
  dup [lit] 8 / [lit] 7 and [char] 0 + cc-prep-emit-byte
  [lit] 7 and [char] 0 + cc-prep-emit-byte ;
```

A logical filename overrides the physical path; unnamed input uses `<stdin>`. `cc-pp-location-filename` surrounds the selected spelling with quotes and encodes each byte (`forth-bootstrap/cc/040-cc-prep.fth:1306`):

```forth file=cc/040-cc-prep.fth
create cc-pp-stdin-name s, <stdin>
\ cc-pp-current-name ( -- a u )  The current file's __FILE__ spelling.
: cc-pp-current-name
  cc-pp-file-name-len cc-pp-location-cell @ dup 0< if,
    drop cc-prep-current-path cc-prep-inc-depth @ cc-prep-file-lens cell[] @
    dup 0= if, 2drop cc-pp-stdin-name [lit] 7 then,
  else, cc-pp-logical-name swap then, ;
: cc-pp-location-filename
  [char] " cc-prep-emit-byte
  cc-pp-current-name
  begin, dup while,
    over c@ cc-pp-location-string-byte swap 1+ swap 1-
  repeat, 2drop [char] " cc-prep-emit-byte ;

```

### Mapping flattened lines

An optional line map records where a file's text resumes in the flattened output. Each arena record links to the previous record and stores the output line, source line and filename (`forth-bootstrap/cc/040-cc-prep.fth:1313`):

```forth file=cc/040-cc-prep.fth
\ An optional map from output lines back to source files, for a diagnostic
\ that must name the user's file and line (121's error 228). Entering a file
\ and returning from an include each record the output line where that
\ file's text continues, with the file's name and logical line there. Every
\ source newline reaches the output, spliced and macro-argument ones too, so
\ a later output line counts on from the latest record. Records are arena
\ entries: next, output line, source line, name length, then the name.
variable cc-pp-line-map-on
[lit] 0 cc-pp-line-map-on !
variable cc-pp-line-map
create cc-pp-map-resume  cc-prep-direct-depth 1+ [lit] 8 * allot
: cc-pp-line-map-note ( source-line -- )
  cc-pp-line-map-on @ 0= if, drop exit, then,
  cc-pp-current-name dup [lit] 32 + cc-alloc >r
  dup r@ [lit] 24 + ! r@ [lit] 32 + swap
  begin, dup while,
    >r over c@ over c! 1+ swap 1+ swap r> 1-
  repeat, drop 2drop
  r@ [lit] 16 + ! cc-src-line @ r@ [lit] 8 + !
  cc-pp-line-map @ r@ ! r> cc-pp-line-map ! ;
```

Lookup chooses the latest record at or before the requested output line, then adds the distance from that record. Chapter 41 uses the map in diagnostics; this layer only maintains it (`forth-bootstrap/cc/040-cc-prep.fth:1333`):

```forth file=cc/040-cc-prep.fth
\ cc-pp-line-map-find ( output-line -- a u source-line true | false )
: cc-pp-line-map-find
  cc-pp-line-map-on @ 0= if, drop [lit] 0 exit, then,
  cc-pp-line-map @
  begin, dup while,
    2dup [lit] 8 + @ < 0= if,
      swap over [lit] 8 + @ - over [lit] 16 + @ + >r
      dup [lit] 32 + swap [lit] 24 + @ r> true exit,
    then, @
  repeat, 2drop [lit] 0 ;

```

</details>

### Expanding a replacement

Dynamic object macros emit the current line or filename directly. An ordinary object macro is marked busy while its body is walked, so `#define SELF SELF` leaves the inner name rather than recursing forever (`forth-bootstrap/cc/040-cc-prep.fth:1344`):

```forth file=cc/040-cc-prep.fth
\ cc-pp-expand-object ( i -- )  Scan object-like macro i's body in place of
\ its name.
: cc-pp-expand-object-body
  dup cc-macro-params cell[] @ [lit] 0 [lit] 2 - = if,
    drop cc-pp-location-line @ cc-pp-location-number exit,
  then,
  dup cc-macro-params cell[] @ [lit] 0 [lit] 3 - = if,
    drop cc-pp-location-filename exit,
  then,
  cc-pp-out-pos @ >r
  true over cc-macro-busy-cell !
  dup cc-macro-body-addr cell[] @  over cc-macro-body-len cell[] @
  cc-pp-expand-text
  [lit] 0 swap cc-macro-busy-cell !
  r> cc-prep-direct @ if, cc-pp-rescan-tail-fwd else, drop then, ;
: cc-pp-expand-object
  true cc-pp-location-begin cc-pp-expand-object-body cc-pp-location-end ;

```

A function-like macro call saves the scratch cursor, collects arguments and preserves their raw slices. Direct mode expands only arguments that need prescan; legacy mode expands every argument (`forth-bootstrap/cc/040-cc-prep.fth:1362`):

```forth file=cc/040-cc-prep.fth
\ cc-pp-expand-call ( i -- )  The '(' of function-like macro i's call has
\ been read.  Collect and expand the arguments, substitute them into the
\ body, and scan the result in place of the call.  A call with more
\ arguments than the macro has parameters dies with 45 (a macro with no
\ parameters takes one empty argument).
: cc-pp-expand-call-body
  cc-pp-out-pos @ >r
  cc-pp-scratch-top @ >r                           ( i ; R: top )
  cc-pp-args-max [lit] 16 * cc-pp-scratch-alloc    ( i recs )
  dup cc-pp-collect-args >r                        ( i recs ; R: top n )
  over cc-macro-params cell[] @ r@ <  r@ [lit] 1 > and if,
    [lit] 45 cc-die
  then,
  r>                                               ( i recs n )
  2dup cc-pp-duplicate-args >r
  cc-prep-direct @ if,
    2dup >r >r
    >r over r> swap cc-pp-expand-used-args
    r> r>
  else,
    2dup cc-pp-expand-args
  then,                                           ( i recs n )
```

The substituted body is built in a temporary sink, then rescanned with the macro busy. Restoring the saved scratch top releases the arguments and body together before any tail rescan (`forth-bootstrap/cc/040-cc-prep.fth:1384`):

```forth file=cc/040-cc-prep.fth
  r> cc-pp-sub-raw !
  cc-pp-temp-begin
  cc-pp-sub-n ! cc-pp-sub-recs !                   ( i )
  dup cc-macro-body-addr cell[] @  over cc-macro-body-len cell[] @
  cc-pp-substitute
  cc-pp-temp-end                                   ( i a u )
  rot true over cc-macro-busy-cell ! >r            ( a u ; R: top i )
  cc-pp-expand-text
  [lit] 0 r> cc-macro-busy-cell !
  r> cc-pp-scratch-top !
  r> cc-prep-direct @ if, cc-pp-rescan-tail-fwd else, drop then, ;
: cc-pp-expand-call
  [lit] 0 cc-pp-location-begin cc-pp-expand-call-body cc-pp-location-end ;

```

The opening expansion can now finish. Argument prescan leaves the text
containing `4` in scratch; substitution copies it into both parameter
positions in another temporary. Rescanning that temporary writes the
tokens of `((4) * (4))` into the caller's sink. Only then can the saved
scratch top be restored. The result survives because its bytes have been
copied out, and the suspended source resumes after `SQUARE(ROWS)`.

### Unavailable tokens across rescans

A function-like name at a replacement's end may find its opening parenthesis in the surrounding source. Tail rescanning first trims output whitespace and locates that final identifier (`forth-bootstrap/cc/040-cc-prep.fth:1398`):

```forth file=cc/040-cc-prep.fth
\ Rescan the final token together with the surrounding source.  This is
\ essential for both an alias (DEF_BWLX(mov)) and a computed name such as
\ ELFW(ST_INFO)(bind,type): the final function-like macro's '(' belongs
\ to the outer region, not to the replacement text just scanned.
variable cc-pp-tail-start
variable cc-pp-tail-end
variable cc-pp-tail-name
: cc-pp-rescan-tail
  cc-pp-tail-start !
  cc-pp-out-pos @ cc-pp-tail-end !
  begin, cc-pp-tail-end @ cc-pp-tail-start @ > if,
    cc-pp-out @ cc-pp-tail-end @ + 1- c@ space?
  else, [lit] 0 then, while, [lit] 1 cc-pp-tail-end -! repeat,
  cc-pp-tail-end @ cc-pp-tail-name !
  begin, cc-pp-tail-name @ cc-pp-tail-start @ > if,
    cc-pp-out @ cc-pp-tail-name @ + 1- c@ ident-cont?
  else, [lit] 0 then, while, [lit] 1 cc-pp-tail-name -! repeat,
  cc-pp-tail-name @ cc-pp-tail-end @ = if, exit, then,
```

A tail token already marked unavailable must stay unexpanded even after its definition stops being busy. An eligible function macro can consume the outer source's parenthesis, replacing the previously emitted name (`forth-bootstrap/cc/040-cc-prep.fth:1416`):

```forth file=cc/040-cc-prep.fth
  cc-pp-out @ cc-pp-tail-name @ + cc-pp-unavailable? if, exit, then,
  cc-pp-out @ cc-pp-tail-name @ + dup c@ ident-start? 0= if, drop exit, then,
  cc-pp-tail-end @ cc-pp-tail-name @ - cc-macro-find
  dup 0< if, drop exit, then,
  dup cc-macro-busy-cell @ if, drop exit, then,
  dup cc-macro-params cell[] @ 0< if, drop exit, then,
  cc-pp-paren-ahead? if,
    cc-pp-tail-name @ cc-pp-out-pos !
    cc-pp-location-rescan @ >r
    cc-pp-location-object-root @ cc-pp-location-rescan !
    cc-pp-expand-call
    r> cc-pp-location-rescan !
  else, drop then, ;
' cc-pp-rescan-tail is cc-pp-rescan-tail-fwd

```

The busy flag and an unavailable-token mark have different lifetimes.
Consider `#define gen_lowpart rtl_hooks.gen_lowpart` in direct mode.
While expanding `gen_lowpart`, the walker reaches the same name after
`rtl_hooks.`. The busy flag stops that inner occurrence from expanding,
so the walker copies it and marks it unavailable.

When this expansion finishes, the macro's busy flag clears. An enclosing
macro can still rescan the copied text. Without the retained mark, that
rescan could expand the member name again: its spelling alone does not
record why it was copied. `cc-pp-ident-work` checks the mark before macro
lookup, preserving that decision while leaving the C text unchanged
(`forth-bootstrap/cc/040-cc-prep.fth:1431`):

```forth file=cc/040-cc-prep.fth
\ cc-pp-ident ( -- )  pos is at an identifier.  Replace it if it names a
\ macro that is not busy (a function-like one only when '(' follows);
\ otherwise copy it.  Newlines a file-level call swallowed are owed; write
\ them now.
: cc-pp-ident-work
  cc-prep-read-ident
  cc-pp-in-if @ if,
    cc-pp-n-defined [lit] 7 cc-prep-ident= if, cc-pp-defined exit, then,
  then,
  cc-prep-ident-addr @ cc-pp-unavailable? if,
    cc-prep-ident-addr @ cc-prep-ident-len @ cc-pp-emit-bytes exit,
  then,
  cc-prep-ident-addr @ cc-prep-ident-len @ cc-macro-find     ( i )
  dup 0< 0= if,
    dup cc-macro-busy-cell @ if,
      drop cc-pp-out-pos @ >r
      cc-prep-ident-addr @ cc-prep-ident-len @ cc-pp-emit-bytes
      cc-pp-out-flags @ if, true cc-pp-out-flags @ r@ + c! then,
      r> drop exit,
    then,
  then,
```

An ordinary name is copied; an eligible macro uses object or call expansion. File-level calls pay back owed newlines, and the wrapper restores the caller's invocation location after nested expansion (`forth-bootstrap/cc/040-cc-prep.fth:1452`):

```forth file=cc/040-cc-prep.fth
  dup 0< if,
    drop cc-prep-ident-addr @ cc-prep-ident-len @ cc-pp-emit-bytes exit,
  then,
  dup cc-macro-params cell[] @ 0< if,
    cc-pp-expand-object
  else,
    cc-prep-ident-addr @ cc-prep-ident-len @ rot    ( a u i )
    cc-pp-paren-ahead? if,
      nip nip cc-pp-expand-call
    else,
      drop cc-pp-emit-bytes
    then,
  then,
  cc-prep-in-file @ if, cc-pp-flush-nl then, ;
: cc-pp-ident
  cc-pp-location-line @ >r
  cc-prep-src-addr @ cc-prep-src-pos @ + cc-pp-location-at
  cc-pp-ident-work
  r> cc-pp-location-line ! ;

```

## Conditional groups and the walker

Each open conditional has a state: `cond-take` emits its group, `cond-seek` waits for a successful alternative, and `cond-done` ignores alternatives through the closing directive (`forth-bootstrap/cc/040-cc-prep.fth:1472`):

```forth file=cc/040-cc-prep.fth
\ ---------------------------------------------------------------------------
\ Conditional groups
\ ---------------------------------------------------------------------------
\ One cell per open #if, innermost last, saying what happens to the lines of
\ its current group:
\   cond-take  the group is compiled
\   cond-done  a group was already taken, or the whole #if sits inside a
\              dropped group: drop lines up to the #endif
\   cond-seek  no group taken yet: drop lines, but an #elif or #else may
\              take the next one

[lit] 0 constant cond-take
[lit] 1 constant cond-done
[lit] 2 constant cond-seek

[lit] 64 constant cc-pp-cond-cap
create cc-pp-cond  cc-pp-cond-cap [lit] 8 * allot
variable cc-pp-cond-depth

\ cc-pp-cond-top ( -- cell )  The innermost open #if's cell.
: cc-pp-cond-top  cc-pp-cond-depth @ 1- cc-pp-cond cell[] ;
```

The top state determines whether ordinary text is dropped. Skipping still consumes comments and literals whole, so punctuation inside them cannot invent a directive (`forth-bootstrap/cc/040-cc-prep.fth:1493`):

```forth file=cc/040-cc-prep.fth

\ cc-pp-skipping? ( -- f )  True while lines are being dropped.
: cc-pp-skipping?
  cc-pp-cond-depth @ if,
    cc-pp-cond-top @ cond-take <>
  else,
    [lit] 0
  then, ;

\ ---------------------------------------------------------------------------
\ The walker
\ ---------------------------------------------------------------------------

\ cc-pp-skip-char ( -- )  One byte of a dropped line.  A comment or literal
\ is stepped over whole (a '#' or quote inside it means nothing), and the
\ newlines inside it are owed.
: cc-pp-skip-char
  put-count cc-pp-put-mode !
  [char] / [char] * cc-pp-at-spliced? if, cc-pp-block-comment exit, then,
  [char] / [char] / cc-pp-at-spliced? if, cc-pp-line-comment  exit, then,
  cc-prep-peek dup [char] " = swap [char] ' = or if, cc-pp-literal exit, then,
  cc-prep-advance ;

```

File comments remain in the flattened text for Chapter 29's lexer. In replacement text they become separator blanks, with physical newlines counted as owed (`forth-bootstrap/cc/040-cc-prep.fth:1516`):

```forth file=cc/040-cc-prep.fth
\ cc-pp-comment ( -- )  pos at a comment.  A file's comments are copied (the
\ lexer skips them); in macro text a comment is one blank.
: cc-pp-comment
  cc-prep-in-file @ if,
    put-emit cc-pp-put-mode !
  else,
    put-count cc-pp-put-mode !
    bl cc-prep-emit-byte
  then,
  [char] / [char] * cc-pp-at-spliced? if,
    cc-pp-block-comment
  else,
    cc-pp-line-comment
  then,
  cc-prep-in-file @ cc-pp-location-enabled @ and if, cc-pp-flush-nl then, ;

```

### Safe source continuations

A source continuation is safe to replace with a newline only when that separator cannot change token boundaries. Lookahead finds the next byte, while the punctuation predicate recognizes tokens that cannot grow by joining (`forth-bootstrap/cc/040-cc-prep.fth:1532`):

```forth file=cc/040-cc-prep.fth
\ cc-pp-splice-next ( -- c )  The byte after the run of LF or CRLF
\ continuations at pos: nl for a CRLF line end or at EOR.  pos is kept.
: cc-pp-splice-next
  cc-prep-src-pos @ >r
  begin, cc-pp-line-continuation? while,
    cc-prep-advance
    cc-prep-peek [lit] 13 = if, cc-prep-advance then,
    cc-prep-advance
  repeat,
  cc-prep-eor? if, nl else,
    [lit] 13 nl cc-prep-at? if, nl else, cc-prep-peek then,
  then,
  r> cc-prep-src-pos ! ;

\ cc-pp-whole-punct? ( c -- f )  c is a punctuator that is always a whole
\ token, never the first byte of a longer one: , ; ( ) [ ] { } ~
: cc-pp-whole-punct?
  dup [lit] 44 = over [lit] 59 = or over [lit] 40 = or
  over [lit] 41 = or over [lit] 91 = or over [lit] 93 = or
  over [lit] 123 = or over [lit] 125 = or swap [lit] 126 = or ;

```

The safety check accepts boundaries beside whitespace, complete block comments or whole-token punctuation. It rejects continuations that would join identifier, number or multi-byte punctuation spelling (`forth-bootstrap/cc/040-cc-prep.fth:1553`):

```forth file=cc/040-cc-prep.fth
\ In source text a continuation becomes its newline, which is only safe
\ where a separator cannot change the tokens: at the start of the input,
\ before whitespace or EOR, after whitespace, a whole-token punctuator or
\ a complete block comment. It cannot join an identifier, number or
\ delimiter.
: cc-pp-file-splice-safe?
  cc-prep-src-pos @ 0= if, true exit, then,
  cc-pp-splice-next dup bl = over tab = or over nl = or
  over [lit] 11 = or swap [lit] 12 = or if, true exit, then,
  cc-prep-src-addr @ cc-prep-src-pos @ + 1- dup c@ space? if,
    drop true exit,
  then,
  dup c@ cc-pp-whole-punct? if, drop true exit, then,
  cc-prep-src-pos @ [lit] 2 < if, drop [lit] 0 exit, then,
  dup c@ [char] / = swap 1- c@ [char] * = and ;

```

The character dispatcher treats file newlines as line starts and replacement newlines as owed separators. A safe source continuation emits its physical newline without creating a new directive boundary (`forth-bootstrap/cc/040-cc-prep.fth:1569`):

```forth file=cc/040-cc-prep.fth
\ cc-pp-scan-char ( -- )  Deal with the byte at pos, and the construct it
\ starts.  A newline in macro text (an argument spread over lines) is a
\ blank, and the newline is owed.
: cc-pp-scan-char
  cc-prep-peek nl = if,
    cc-prep-advance
    cc-prep-in-file @ if,
      nl cc-prep-emit-byte  true cc-prep-at-line-start !
    else,
      bl cc-prep-emit-byte  [lit] 1 cc-pp-pending-nl +!
    then,
    exit,
  then,
  [lit] 0 cc-prep-at-line-start !
  cc-prep-in-file @ cc-pp-location-enabled @ and if,
    cc-pp-line-continuation? if,
      cc-pp-file-splice-safe? 0= if, [lit] 49 cc-die then,
      put-emit cc-pp-put-mode ! cc-pp-take-continuation exit,
    then,
  then,
```

After handling skipped groups, the dispatcher copies literals, walks comments, removes replacement continuations and delegates numbers and names. Remaining punctuation is copied directly (`forth-bootstrap/cc/040-cc-prep.fth:1589`):

```forth file=cc/040-cc-prep.fth
  cc-prep-in-file @ if,
    cc-pp-skipping? if, cc-pp-skip-char exit, then,
  then,
  cc-prep-peek dup [char] " = swap [char] ' = or if,
    put-emit cc-pp-put-mode ! cc-pp-literal
    cc-prep-in-file @ if, cc-pp-flush-nl then, exit,
  then,
  [char] / [char] * cc-pp-at-spliced?  [char] / [char] / cc-pp-at-spliced? or if,
    cc-pp-comment exit,
  then,
  backslash nl cc-prep-at?  cc-prep-in-file @ 0= and if,
    cc-prep-advance cc-prep-advance  [lit] 1 cc-pp-pending-nl +! exit,
  then,
  cc-prep-peek digit?       if, cc-pp-copy-number exit, then,
  cc-prep-peek ident-start? if, cc-pp-ident       exit, then,
  cc-prep-peek cc-prep-emit-byte  cc-prep-advance ;

```

### Finding directives

Directive-prefix whitespace has a stricter grammar in the location-enabled profile. A carriage return must belong to CRLF, while the other horizontal C whitespace forms can precede the directive (`forth-bootstrap/cc/040-cc-prep.fth:1606`):

```forth file=cc/040-cc-prep.fth
\ cc-prep-line-is-directive? ( -- f )  -1 iff the first non-blank byte on
\ the current line is '#'.  Does NOT advance pos.
variable cc-prep-isd-save-pos

\ SysV recognizes all C horizontal whitespace at directive boundaries.
\ Reuse the comment walker for lookahead and consumption. Prefix mode
\ permits inert block-comment splices; split delimiters and malformed
\ comments still fail49 before any directive can silently disappear.
: cc-prep-directive-blanks
  begin,
    cc-prep-peek [lit] 13 = if,
      cc-prep-peek2 nl <> if, [lit] 49 cc-die then, cc-prep-advance
    then,
    cc-prep-eor? 0= if,
      cc-prep-peek dup bl = over tab = or over [lit] 11 = or
      swap [lit] 12 = or
    else, [lit] 0 then,
  while, cc-prep-advance repeat, ;

```

Prefix scanning uses the shared comment walker both for lookahead and consumption. Save-switch-restore preserves the caller's disposal and line-control modes across that scan (`forth-bootstrap/cc/040-cc-prep.fth:1625`):

```forth file=cc/040-cc-prep.fth
: cc-prep-directive-prefix ( put-mode -- )
  cc-pp-put-mode @ >r cc-pp-put-mode !
  cc-pp-line-control @ >r [lit] 2 cc-pp-line-control !
  begin,
    cc-prep-directive-blanks
    begin, cc-pp-line-continuation? while,
      cc-pp-take-continuation cc-prep-directive-blanks
    repeat,
    [char] / [char] * cc-pp-at-spliced?
  while,
    cc-pp-block-comment
  repeat,
  [char] / [char] / cc-pp-at-spliced? if, cc-pp-line-comment then,
  r> cc-pp-line-control ! r> cc-pp-put-mode ! ;

```

Lookahead restores the source cursor after testing for `#`. It runs only at a line start, so a long indentation is not rescanned for every byte (`forth-bootstrap/cc/040-cc-prep.fth:1640`):

```forth file=cc/040-cc-prep.fth
: cc-prep-line-is-directive?
  cc-prep-src-pos @ cc-prep-isd-save-pos !
  cc-pp-location-enabled @ if,
    put-drop cc-prep-directive-prefix
  else, cc-prep-skip-blanks then,
  cc-prep-peek [char] # = >r
  cc-prep-isd-save-pos @ cc-prep-src-pos !
  r> ;

\ cc-prep-at-directive? ( -- f )  -1 iff pos is at a line start and the line
\ is a directive.  Looks ahead only at a line start, so a long line of
\ blanks is scanned once, not once per byte.
: cc-prep-at-directive?
  cc-prep-at-line-start @ 0= if, [lit] 0 exit, then,
  cc-prep-line-is-directive? ;

```

The main walker dispatches directives only in file regions and pays their owed newlines immediately afterward. Replacement regions always use ordinary character scanning (`forth-bootstrap/cc/040-cc-prep.fth:1656`):

```forth file=cc/040-cc-prep.fth
\ cc-pp-scan ( -- )  Walk the current region to its end.  In a file, a line
\ that starts with '#' is a directive; the newlines it owes are written
\ right after it.
: cc-pp-scan
  true cc-prep-at-line-start !
  begin,
    cc-prep-eor? 0=
  while,
    cc-prep-in-file @ if, cc-prep-at-directive? else, [lit] 0 then,
    if,
      cc-prep-handle-directive-fwd
      cc-pp-flush-nl
      [lit] 0 cc-prep-at-line-start !
    else,
      cc-pp-scan-char
    then,
  repeat, ;

' cc-pp-scan is cc-pp-scan-fwd

```

## `#if` and friends

The preprocessor expands a conditional expression, handling `defined` before its operand can expand, then passes the result to `cc-pp-eval`. Chapter 34 supplies the core constant-expression evaluator and Chapter 45 extends typed evaluation; this file defines only the interface (`forth-bootstrap/cc/040-cc-prep.fth:1676`):

```forth file=cc/040-cc-prep.fth
\ ===========================================================================
\ Directives
\ ===========================================================================

\ ---------------------------------------------------------------------------
\ #if, #ifdef, #ifndef, #elif, #else, #endif
\ ---------------------------------------------------------------------------

\ cc-pp-eval ( a u -- n )  The value of the constant expression a u, which
\ has no macros left in it.  100-cc-expr.fth fills it in: #if uses the
\ same grammar as array sizes and case labels, with intmax_t/uintmax_t
\ signedness and conversions in the LP64 profile.
defer cc-pp-eval

\ cc-pp-if-value ( -- f )  Expand the rest of the #if / #elif line into a
\ temp buffer, with `defined` answered first, and evaluate it.
: cc-pp-if-value
  cc-pp-scratch-top @ >r
  cc-pp-line-slice
  true cc-pp-in-if !
  cc-pp-temp-begin cc-pp-expand-text cc-pp-temp-end
  [lit] 0 cc-pp-in-if !
  cc-pp-eval 0= 0=
  r> cc-pp-scratch-top ! ;
```

Opening a conditional pushes either take or seek after checking depth. `#ifdef` needs only macro lookup; alternative and closing directives require an already open group (`forth-bootstrap/cc/040-cc-prep.fth:1700`):

```forth file=cc/040-cc-prep.fth

\ cc-pp-cond-push ( state -- )  Open an #if.  Dies with 38 past
\ cc-pp-cond-cap nested ones.
: cc-pp-cond-push
  cc-pp-cond-depth @ 1+ cc-pp-cond-cap [lit] 38 cc-check-cap
  cc-pp-cond-depth @ cc-pp-cond cell[] !
  [lit] 1 cc-pp-cond-depth +! ;

\ cc-pp-cond-open ( f -- )  Open an #if whose first group is taken iff f.
: cc-pp-cond-open
  if, cond-take else, cond-seek then, cc-pp-cond-push ;

\ cc-pp-defined-name? ( -- f )  #ifdef / #ifndef: is the next name a macro?
: cc-pp-defined-name?
  cc-pp-need-name
  cc-prep-ident-addr @ cc-prep-ident-len @ cc-macro-find 0< 0= ;

\ cc-pp-need-group ( -- )  #elif / #else / #endif with no #if open: die 41.
: cc-pp-need-group
  cc-pp-cond-depth @ 0= if, [lit] 41 cc-die then, ;
```

The conditional dispatcher recognizes stored directive names. An `#if` nested inside a dropped group pushes done without evaluating an expression that may be invalid in that configuration (`forth-bootstrap/cc/040-cc-prep.fth:1720`):

```forth file=cc/040-cc-prep.fth

create cc-pp-n-if      s, if
create cc-pp-n-ifdef   s, ifdef
create cc-pp-n-ifndef  s, ifndef
create cc-pp-n-elif    s, elif
create cc-pp-n-else    s, else
create cc-pp-n-endif   s, endif

\ cc-pp-cond-directive ( -- f )  If the directive just read is one of the
\ six conditionals, act on it and answer true.  Inside a dropped group an
\ #if is not evaluated: the whole #if is dropped.
: cc-pp-cond-directive
  cc-pp-n-if [lit] 2 cc-prep-ident= if,
    cc-pp-skipping? if,
      cond-done cc-pp-cond-push
    else,
      cc-pp-if-value cc-pp-cond-open
    then,
    true exit,
  then,
```

`#ifdef` and `#ifndef` use complementary name-existence tests when active. Inside skipped text, both preserve nesting by opening a done group (`forth-bootstrap/cc/040-cc-prep.fth:1740`):

```forth file=cc/040-cc-prep.fth
  cc-pp-n-ifdef [lit] 5 cc-prep-ident= if,
    cc-pp-skipping? if,
      cond-done cc-pp-cond-push
    else,
      cc-pp-defined-name? cc-pp-cond-open
    then,
    true exit,
  then,
  cc-pp-n-ifndef [lit] 6 cc-prep-ident= if,
    cc-pp-skipping? if,
      cond-done cc-pp-cond-push
    else,
      cc-pp-defined-name? 0= cc-pp-cond-open
    then,
    true exit,
  then,
```

A taken group becomes done at `#elif`; only seek evaluates another condition. `#else` takes a seeking group, and `#endif` pops the innermost state (`forth-bootstrap/cc/040-cc-prep.fth:1756`):

```forth file=cc/040-cc-prep.fth
  cc-pp-n-elif [lit] 4 cc-prep-ident= if,
    cc-pp-need-group
    cc-pp-cond-top @ cond-take = if, cond-done cc-pp-cond-top ! then,
    cc-pp-cond-top @ cond-seek = if,
      cc-pp-if-value if, cond-take cc-pp-cond-top ! then,
    then,
    true exit,
  then,
  cc-pp-n-else [lit] 4 cc-prep-ident= if,
    cc-pp-need-group
    cc-pp-cond-top @ cond-seek = if, cond-take else, cond-done then,
    cc-pp-cond-top !
    true exit,
  then,
  cc-pp-n-endif [lit] 5 cc-prep-ident= if,
    cc-pp-need-group
    [lit] 1 cc-pp-cond-depth -!
    true exit,
  then,
  [lit] 0 ;

```

## Recursive include processing

An include scan must return to the exact source address, length and position it interrupted. Depth-indexed save arrays keep nested includes from overwriting their callers' restore state (`forth-bootstrap/cc/040-cc-prep.fth:1777`):

```forth file=cc/040-cc-prep.fth
\ ---------------------------------------------------------------------------
\ #include
\ ---------------------------------------------------------------------------

\ State save / restore for recursive descent.
\ Arrays indexed by cc-prep-inc-depth (parallel to the include-pool slots),
\ so nested includes don't corrupt each other's restore state.
cc-prep-direct-depth constant cc-prep-save-count
create cc-prep-save-addr  cc-prep-save-count [lit] 8 * allot
create cc-prep-save-len   cc-prep-save-count [lit] 8 * allot
create cc-prep-save-pos   cc-prep-save-count [lit] 8 * allot

\ cc-prep-save-slot ( arr -- addr )  Compute the save-slot address for the
\ current include depth.  Arrays are indexed by cc-prep-inc-depth.
: cc-prep-save-slot  cc-prep-inc-depth @ swap cell[] ;

\ cc-prep-handle-include
\ Pre: pos points just past "include".  Skip blanks, read "..." or <...>,
\ then recurse on quoted names, and on angle names in direct mode.
\ At exit pos is at end-of-line (or EOR); newline is NOT consumed.
variable cc-prep-inc-end
variable cc-prep-inc-expanded

```

Literal include parsing selects quote or angle delimiters and records the name's slice. Computed quoted operands step over escaped bytes without decoding their backslashes into a different pathname (`forth-bootstrap/cc/040-cc-prep.fth:1800`):

```forth file=cc/040-cc-prep.fth
: cc-prep-include-literal
  cc-prep-skip-blanks
  [lit] 0 cc-prep-inc-mode !
  cc-prep-peek [char] " = if,
    [lit] 1 cc-prep-inc-mode ! [char] " cc-prep-inc-end !
  else,
    cc-prep-peek [char] < = if,
      [lit] 2 cc-prep-inc-mode ! [char] > cc-prep-inc-end !
    then,
  then,
  cc-prep-inc-mode @ if,
    cc-prep-advance
    cc-prep-src-addr @ cc-prep-src-pos @ + cc-prep-src-pos @
    begin,
      cc-prep-eor? 0= cc-prep-peek cc-prep-inc-end @ <> and
      cc-prep-peek nl <> and
    while,
      cc-prep-inc-expanded @ cc-prep-inc-mode @ [lit] 1 = and
      cc-prep-peek backslash = and if,
        cc-prep-advance
        cc-prep-eor? 0= cc-prep-peek nl <> and if, cc-prep-advance then,
      else, cc-prep-advance then,
    repeat,
```

Direct mode requires a nonempty, closed name. Expanded operands must contain only that header name; internal whitespace in computed angle names is rejected because this text engine cannot preserve its token-joining meaning (`forth-bootstrap/cc/040-cc-prep.fth:1823`):

```forth file=cc/040-cc-prep.fth
    cc-prep-src-pos @ swap -
    cc-prep-direct @ if,
      dup 0= cc-prep-peek cc-prep-inc-end @ <> or if, [lit] 30 cc-die then,
    then,
    cc-prep-peek cc-prep-inc-end @ = if, cc-prep-advance then,
    cc-prep-inc-expanded @ if,
      \ Macro expansion must yield exactly one header operand.
      cc-prep-skip-blanks cc-prep-eor? 0= if, [lit] 30 cc-die then,
      cc-prep-inc-mode @ [lit] 2 = if,
        \ Whitespace-sensitive angle token joining is not yet represented.
        \ Reject it explicitly instead of silently selecting another file.
        2dup begin, dup while,
          over c@ space? if, [lit] 30 cc-die then,
          swap 1+ swap 1-
        repeat, 2drop
      then,
    then,
    [lit] 0 cc-prep-inc-expanded !
```

Opening an include uses save-switch-restore for the region as well as the packed-pool top. When line mapping is enabled, entry and exit each add a record. Between them, the walker scans the included region before resuming the caller (`forth-bootstrap/cc/040-cc-prep.fth:1841`):

```forth file=cc/040-cc-prep.fth
    cc-prep-inc-mode @ [lit] 1 = cc-prep-direct @ or if,
      cc-prep-inc-top @ >r
      cc-prep-load-file
      cc-prep-src-addr @ cc-prep-save-addr cc-prep-save-slot !
      cc-prep-src-len  @ cc-prep-save-len  cc-prep-save-slot !
      cc-prep-src-pos  @ cc-prep-save-pos  cc-prep-save-slot !
      [lit] 1 cc-prep-inc-depth +!
      cc-prep-src-len ! cc-prep-src-addr ! [lit] 0 cc-prep-src-pos !
      cc-pp-location-enter
      [lit] 1 cc-pp-line-map-note
      cc-pp-scan
      [lit] 1 cc-prep-inc-depth -!
      cc-prep-save-addr cc-prep-save-slot @ cc-prep-src-addr !
      cc-prep-save-len  cc-prep-save-slot @ cc-prep-src-len  !
      cc-prep-save-pos  cc-prep-save-slot @ cc-prep-src-pos  !
      r> cc-prep-inc-top !
      cc-pp-map-resume cc-pp-location-cell @ cc-pp-line-map-note
    else, 2drop then,
  then, ;
```

### Computed include operands

An operand such as `#include EXTRA_MODES_FILE` needs expansion before it names a file. Direct mode builds that result in scratch, requires a quote or angle opener and invokes the same include parser while preserving the original file's search context (`forth-bootstrap/cc/040-cc-prep.fth:1860`):

```forth file=cc/040-cc-prep.fth

\ A computed operand is rescanned with the same macro engine as C text.
\ Preserve the original file region while parsing its expanded header token;
\ recursive include search and location state still belong to that file.
: cc-prep-handle-include
  cc-pp-line-map-on @ if,
    \ The directive's own line, where this file resumes after the header.
    cc-prep-src-addr @ cc-prep-src-pos @ + cc-pp-location-at
    cc-pp-location-line @ cc-pp-map-resume cc-pp-location-cell !
  then,
  [lit] 0 cc-prep-inc-expanded !
  cc-prep-skip-blanks
  cc-prep-peek [char] " = cc-prep-peek [char] < = or
  cc-prep-direct @ 0= or if, cc-prep-include-literal exit, then,
  cc-pp-scratch-top @ >r
  cc-pp-line-slice
  cc-pp-temp-begin cc-pp-expand-text cc-pp-temp-end
  cc-prep-src-addr @ >r cc-prep-src-len @ >r cc-prep-src-pos @ >r
  cc-prep-at-line-start @ >r
  cc-prep-src-len ! cc-prep-src-addr ! [lit] 0 cc-prep-src-pos !
  cc-prep-skip-blanks
  cc-prep-peek [char] " = cc-prep-peek [char] < = or 0= if,
    [lit] 30 cc-die
  then,
  true cc-prep-inc-expanded ! cc-prep-include-literal
  r> cc-prep-at-line-start !
  r> cc-prep-src-pos ! r> cc-prep-src-len ! r> cc-prep-src-addr !
  r> cc-pp-scratch-top ! ;
```

<details>
<summary>Line control: interpreting a source-supplied filename and line number</summary>

An included or generated source can change the location reported for
later tokens. The line-control parser updates that record while keeping
the physical input cursor separate. After this reference section, the
main walkthrough returns to installing macro definitions.

## Parsing C line control

Generated parser text can use `#line` to identify copied grammar actions. After macro expansion, the operand grammar accepts a positive decimal line and an optional ordinary filename string; it does not evaluate an expression (`forth-bootstrap/cc/040-cc-prep.fth:1888`):

```forth file=cc/040-cc-prep.fth

\ ---------------------------------------------------------------------------
\ #line: shared macro expansion followed by a bounded operand grammar
\ ---------------------------------------------------------------------------
\ Only the source-location-enabled target uses this directive. The parser
\ accepts decimal 1..2147483647 and an optional ordinary byte string.
\ Simple, octal and hex escapes are decoded; NUL, overflow, wide/Unicode
\ forms and names exceeding 1023 bytes fail49 rather than alter provenance.
variable cc-pp-line-number
variable cc-pp-line-name-size

: cc-pp-line-blanks
  begin, cc-prep-eor? 0= if,
    cc-prep-peek dup space? over [lit] 11 = or swap [lit] 12 = or
  else, [lit] 0 then, while, cc-prep-advance repeat, ;

: cc-pp-line-decimal
  cc-prep-peek digit? 0= if, [lit] 49 cc-die then,
  [lit] 0
  begin, cc-prep-peek digit? while,
    [lit] 10 * cc-prep-peek [char] 0 - +
    dup [lit] 2147483647 > if, [lit] 49 cc-die then,
    cc-prep-advance
  repeat,
  dup 0= if, [lit] 49 cc-die then, cc-pp-line-number ! ;

```

Filename escapes use local digit decoding. Hexadecimal escapes require a digit and reject overflow while accumulating, so malformed input cannot silently become a different filename (`forth-bootstrap/cc/040-cc-prep.fth:1914`):

```forth file=cc/040-cc-prep.fth
: cc-pp-line-hex ( c -- n|-1 )
  dup digit? if, [char] 0 - exit, then,
  dup [char] a >= over [char] f <= and if, [char] a - [lit] 10 + exit, then,
  dup [char] A >= over [char] F <= and if, [char] A - [lit] 10 + exit, then,
  drop true ;

: cc-pp-line-octal? ( c -- f )
  dup [char] 0 >= swap [char] 7 <= and ;

: cc-pp-line-escape ( -- byte )
  cc-prep-eor? if, [lit] 49 cc-die then,
  cc-prep-peek cc-prep-advance
  dup [char] x = if,
    drop cc-prep-peek cc-pp-line-hex 0< if, [lit] 49 cc-die then,
    [lit] 0
    begin, cc-prep-peek cc-pp-line-hex dup 0< 0= while,
      swap [lit] 16 * + dup [lit] 255 > if, [lit] 49 cc-die then,
      cc-prep-advance
    repeat, drop exit,
  then,
```

Octal and simple escapes complete the byte grammar. Unsupported escape letters are rejected rather than copied with a different meaning (`forth-bootstrap/cc/040-cc-prep.fth:1934`):

```forth file=cc/040-cc-prep.fth
  dup cc-pp-line-octal? if,
    [char] 0 - [lit] 1
    begin, dup [lit] 3 < cc-prep-peek cc-pp-line-octal? and while,
      swap [lit] 8 * cc-prep-peek [char] 0 - + swap 1+ cc-prep-advance
    repeat, drop exit,
  then,
  dup [char] a = if, drop [lit] 7 exit, then,
  dup [char] b = if, drop [lit] 8 exit, then,
  dup [char] f = if, drop [lit] 12 exit, then,
  dup [char] n = if, drop nl exit, then,
  dup [char] r = if, drop [lit] 13 exit, then,
  dup [char] t = if, drop tab exit, then,
  dup [char] v = if, drop [lit] 11 exit, then,
  dup backslash = over [char] " = or over [char] ' = or over [char] ? = or
  0= if, [lit] 49 cc-die then, ;

```

The filename parser requires a closing quote, rejects NUL and oversized byte values, and checks the decoded name's capacity before each store. Empty names are allowed (`forth-bootstrap/cc/040-cc-prep.fth:1950`):

```forth file=cc/040-cc-prep.fth
: cc-pp-line-filename
  cc-prep-peek [char] " <> if, [lit] 49 cc-die then,
  cc-prep-advance [lit] 0 cc-pp-line-name-size !
  begin,
    cc-prep-eor? cc-prep-peek nl = or if, [lit] 49 cc-die then,
    cc-prep-peek [char] " <>
  while,
    cc-prep-peek cc-prep-advance
    dup backslash = if, drop cc-pp-line-escape then,
    dup 0= over [lit] 255 > or if, [lit] 49 cc-die then,
    cc-pp-line-name-size @ 1+ cc-prep-path-cap 1- [lit] 49 cc-check-cap
    cc-pp-logical-name cc-pp-line-name-size @ + c!
    [lit] 1 cc-pp-line-name-size +!
  repeat,
  cc-prep-advance ;

```

### Applying a logical location

`cc-prep-handle-line` expands and validates the entire operand in a temporary region. It rejects extra tokens before restoring the source cursor and releasing the temporary scratch storage (`forth-bootstrap/cc/040-cc-prep.fth:1966`):

```forth file=cc/040-cc-prep.fth
: cc-prep-handle-line
  cc-pp-scratch-top @ >r
  true cc-pp-line-control ! cc-pp-line-slice
  cc-pp-temp-begin cc-pp-expand-text cc-pp-temp-end
  [lit] 0 cc-pp-line-control !
  cc-prep-src-addr @ >r cc-prep-src-len @ >r cc-prep-src-pos @ >r
  cc-prep-at-line-start @ >r
  cc-prep-src-len ! cc-prep-src-addr ! [lit] 0 cc-prep-src-pos !
  cc-pp-line-blanks cc-pp-line-decimal cc-pp-line-blanks
  true cc-pp-line-name-size !
  cc-prep-eor? 0= if, cc-pp-line-filename cc-pp-line-blanks then,
  cc-prep-eor? 0= if, [lit] 49 cc-die then,
  r> cc-prep-at-line-start !
  r> cc-prep-src-pos ! r> cc-prep-src-len ! r> cc-prep-src-addr !
  r> cc-pp-scratch-top !
```

The requested number applies to the following physical line. Updating an offset preserves the physical cursor used by argument prescan and leaves relative include lookup tied to the real pathname (`forth-bootstrap/cc/040-cc-prep.fth:1981`):

```forth file=cc/040-cc-prep.fth
  \ The terminating physical newline is still unread. Set the offset for
  \ the following line only after validating the entire expanded operand.
  cc-prep-src-addr @ cc-prep-src-pos @ + cc-pp-location-at
  cc-pp-line-number @ cc-pp-file-line cc-pp-location-cell @ 1+ -
  cc-pp-file-offset cc-pp-location-cell !
  cc-pp-line-name-size @ dup 0< if, drop else,
    cc-pp-file-name-len cc-pp-location-cell !
  then,
  cc-pp-line-number @ 1- cc-pp-line-map-note ;

```

</details>

## `#define` and `#undef`

We have followed a call using an already stored body. Now complete the
other half: how did `#define SQUARE(x) ((x) * (x))` create that body?
Definition processing recognizes `x` as a parameter and records its
index at both occurrences. It leaves the choice of argument text to the
later invocation, which is why one stored definition can serve many calls.

A function-like definition records parameter names while its body is encoded. Those names live only until body copying finishes; the stored macro body uses parameter markers instead (`forth-bootstrap/cc/040-cc-prep.fth:1991`):

```forth file=cc/040-cc-prep.fth
\ ---------------------------------------------------------------------------
\ #define and #undef
\ ---------------------------------------------------------------------------

\ A function-like macro's parameter names, while its body is copied:
\ legacy source slices or direct logical names in scratch, looked up
\ with cc-name-find. Direct scratch is released after copying the body.
[lit] 16 constant cc-pp-params-max
create cc-pp-param-addr  cc-pp-params-max [lit] 8 * allot
create cc-pp-param-len   cc-pp-params-max [lit] 8 * allot
variable cc-pp-param-count

\ cc-pp-read-params ( -- )  pos is just past the '(' of `#define NAME(`.
\ Read the parameter names through the ')'.  Anything but names, commas
\ and blanks before the ')' dies with 47, more than cc-pp-params-max
\ parameters with 48.
```

The legacy parameter reader records source slices separated by commas. `cc-pp-param?` resolves a body identifier against those names so later substitution need not search textual identifiers again (`forth-bootstrap/cc/040-cc-prep.fth:2026`):

```forth file=cc/040-cc-prep.fth
: cc-pp-read-params
  [lit] 0 cc-pp-param-count !
  begin,
    cc-prep-skip-blanks
    cc-prep-peek ident-start? if,
      cc-pp-param-count @ 1+ cc-pp-params-max [lit] 48 cc-check-cap
      cc-prep-read-ident
      cc-prep-ident-addr @ cc-pp-param-count @ cc-pp-param-addr cell[] !
      cc-prep-ident-len  @ cc-pp-param-count @ cc-pp-param-len  cell[] !
      [lit] 1 cc-pp-param-count +!
      cc-prep-skip-blanks
    then,
    cc-prep-peek [char] , =
  while,
    cc-prep-advance
  repeat,
  cc-pp-need-rparen ;

\ cc-pp-param? ( -- k | -1 )  Is the identifier just read parameter k?
: cc-pp-param?
  cc-prep-ident-addr @ cc-prep-ident-len @
  cc-pp-param-addr cc-pp-param-len cc-pp-param-count @ cc-name-find ;

```

### Logical parameter names

In the location-enabled parameter grammar, a continuation joins name bytes without introducing whitespace. Logical parameter names are built in a bounded temporary sink while their physical newlines become owed (`forth-bootstrap/cc/040-cc-prep.fth:2030`):

```forth file=cc/040-cc-prep.fth
\ Parameter-list phase two is local to the direct grammar: remove LF or
\ CRLF continuations, retaining their physical newlines as owed. Do not
\ turn a splice into whitespace: ab\<newline>cd is one parameter name.
: cc-pp-param-splices
  put-count cc-pp-put-mode !
  begin, cc-pp-line-continuation? while,
    cc-pp-take-continuation
  repeat, ;

: cc-pp-param-blanks
  begin,
    cc-prep-skip-blanks
    cc-pp-line-continuation?
  while, cc-pp-param-splices repeat, ;

\ Logical parameter names share one bounded temporary sink (code 37).
\ Its text survives through body encoding; the physical input is untouched.
: cc-pp-param-ident
  cc-pp-out @ cc-pp-out-pos @ + cc-prep-ident-addr !
  begin,
    cc-pp-param-splices
    cc-prep-peek ident-cont?
  while,
    cc-prep-peek cc-prep-emit-byte cc-prep-advance
  repeat,
  cc-pp-out @ cc-pp-out-pos @ + cc-prep-ident-addr @ - cc-prep-ident-len ! ;

```

The direct parameter reader accepts an empty list or distinct comma-separated identifiers. It rejects duplicates, missing names, trailing commas, comments and variadic forms; its logical-name storage survives until body encoding finishes (`forth-bootstrap/cc/040-cc-prep.fth:2057`):

```forth file=cc/040-cc-prep.fth
\ Direct lists are empty or comma-separated distinct identifiers. Reject
\ missing names, trailing commas and duplicates with 47; retain the existing
\ 16-name limit (48). Comments and variadic forms remain unsupported (47).
: cc-pp-read-direct-params
  [lit] 0 cc-pp-param-count !
  cc-pp-temp-begin cc-pp-param-blanks
  cc-prep-peek [char] ) = if,
    cc-prep-advance cc-pp-temp-end 2drop exit,
  then,
  begin,
    cc-prep-peek ident-start? 0= if, [lit] 47 cc-die then,
    cc-pp-param-count @ 1+ cc-pp-params-max [lit] 48 cc-check-cap
    cc-pp-param-ident
    cc-pp-param? 0< 0= if, [lit] 47 cc-die then,
    cc-prep-ident-addr @ cc-pp-param-count @ cc-pp-param-addr cell[] !
    cc-prep-ident-len @ cc-pp-param-count @ cc-pp-param-len cell[] !
    [lit] 1 cc-pp-param-count +!
    cc-pp-param-blanks
    cc-prep-peek [char] ) = if,
      cc-prep-advance cc-pp-temp-end 2drop exit,
    then,
    cc-prep-peek [char] , <> if, [lit] 47 cc-die then,
    cc-prep-advance cc-pp-param-blanks
  again, ;

```

### Encoding a replacement body

Direct body encoding gives stringification and pasting their own markers. A single `#` must name a parameter; `##` becomes a paste marker for substitution (`forth-bootstrap/cc/040-cc-prep.fth:2082`):

```forth file=cc/040-cc-prep.fth
\ cc-pp-copy-hash ( -- )  Encode #parameter and ## outside literals.
: cc-pp-copy-hash
  cc-prep-advance
  cc-prep-peek [char] # = if,
    [lit] 3 cc-prep-emit-byte cc-prep-advance
  else,
    cc-prep-skip-blanks
    cc-pp-need-name cc-pp-param?
    dup 0< if, [lit] 47 cc-die then,
    [lit] 2 cc-prep-emit-byte cc-prep-emit-byte
  then, ;

```

Body copying removes continuations and replaces comments with blanks while retaining their newline debt. Literal contents remain literal, so parameter-looking names inside quotes are never substituted (`forth-bootstrap/cc/040-cc-prep.fth:2094`):

```forth file=cc/040-cc-prep.fth
\ cc-pp-copy-body ( -- )  Copy the rest of the #define line to the sink (the
\ macro pool): a comment becomes one blank, a backslash-newline joins the
\ lines (the newline is owed), and a parameter becomes the marker 1, k.
: cc-pp-copy-body
  begin,
    cc-prep-eor? 0= cc-prep-peek nl <> and
  while,
    backslash nl cc-prep-at? if,
      cc-prep-advance cc-prep-advance  [lit] 1 cc-pp-pending-nl +!
    else,
    [char] / [char] * cc-pp-at-spliced?  [char] / [char] / cc-pp-at-spliced? or if,
      put-count cc-pp-put-mode !
      [char] / [char] * cc-pp-at-spliced? if,
        cc-pp-block-comment
      else,
        cc-pp-line-comment
      then,
      bl cc-prep-emit-byte
    else,
    cc-prep-peek dup [char] " = swap [char] ' = or if,
      put-emit cc-pp-put-mode !  cc-pp-literal
    else,
```

Outside literals, direct hash operators are encoded, numbers remain whole and recognized parameters become index markers. Other identifiers retain their spelling for lookup when the macro is used (`forth-bootstrap/cc/040-cc-prep.fth:2116`):

```forth file=cc/040-cc-prep.fth
    cc-prep-peek [char] # = cc-prep-direct @ and if,
      cc-pp-copy-hash
    else,
    cc-prep-peek digit? if,
      cc-pp-copy-number
    else,
    cc-prep-peek ident-start? if,
      cc-prep-read-ident
      cc-pp-param? dup 0< if,
        drop cc-prep-ident-addr @ cc-prep-ident-len @ cc-pp-emit-bytes
      else,
        [lit] 1 cc-prep-emit-byte  cc-prep-emit-byte
      then,
    else,
      cc-prep-peek cc-prep-emit-byte  cc-prep-advance
    then, then, then, then, then, then,
  repeat, ;

```

Trailing blanks need not occupy the macro pool. Trimming moves the sink's written length back only as far as this body's start (`forth-bootstrap/cc/040-cc-prep.fth:2134`):

```forth file=cc/040-cc-prep.fth
\ cc-pp-trim ( start -- start )  Drop the blanks that end the text written
\ to the sink since address start.
: cc-pp-trim
  begin,
    cc-pp-out @ cc-pp-out-pos @ +                  ( start end )
    2dup < if,
      1- c@ dup bl = swap tab = or
    else,
      drop [lit] 0
    then,
  while,
    [lit] 1 cc-pp-out-pos -!
  repeat, ;

```

### Installing and removing definitions

A definition is function-like only when its opening parenthesis is adjacent to the name. The location-enabled path can preserve that adjacency across a continuation, but rejects a split macro name (`forth-bootstrap/cc/040-cc-prep.fth:2148`):

```forth file=cc/040-cc-prep.fth
\ cc-prep-handle-define ( -- )  pos is just past "define".  `NAME(` with no
\ blank before the '(' makes a function-like macro.  The name and the body
\ go to the pool.  A #define with no name is dropped.
: cc-prep-handle-define
  cc-prep-skip-blanks
  cc-prep-peek ident-start? 0= if, exit, then,
  cc-prep-read-ident
  cc-prep-ident-addr @ cc-prep-ident-len @ cc-pp-pool-copy   ( na nu )
  cc-pp-scratch-top @ >r
  cc-pp-location-enabled @ cc-pp-line-continuation? and if,
    cc-pp-param-splices
    \ A join before '(' preserves adjacency; split macro names are outside
    \ this grammar and must not silently define the unjoined prefix.
    cc-prep-peek ident-cont? if, [lit] 47 cc-die then,
  then,
  cc-prep-peek lparen = if,
    cc-prep-advance
    cc-pp-location-enabled @ if, cc-pp-read-direct-params else, cc-pp-read-params then,
    cc-pp-param-count @
  else,
    [lit] 0 cc-pp-param-count !  true
  then,
```

After encoding, the name, body and parameter count become a table record and temporary parameter storage is released. `#undef` invalidates every matching definition, so an older shadowed record cannot reappear (`forth-bootstrap/cc/040-cc-prep.fth:2170`):

```forth file=cc/040-cc-prep.fth
  >r                                               ( na nu ; R: saved-scratch params )
  cc-pp-location-enabled @ if, cc-pp-param-blanks else, cc-prep-skip-blanks then,
  cc-macro-pool cc-macro-pool-pos @ +              ( na nu ba )
  cc-pp-to-pool  cc-pp-copy-body  cc-pp-trim  cc-pp-from-pool
  cc-macro-pool cc-macro-pool-pos @ + over -       ( na nu ba bu )
  r> cc-macro-record
  r> cc-pp-scratch-top ! ;

\ cc-prep-handle-undef ( -- )  pos is just past "undef".  Forget every
\ definition of the name (a zero length never matches).
: cc-prep-handle-undef
  cc-prep-skip-blanks
  cc-prep-peek ident-start? 0= if, exit, then,
  cc-prep-read-ident
  begin,
    cc-prep-ident-addr @ cc-prep-ident-len @ cc-macro-find
    dup 0< 0=
  while,
    [lit] 0 swap cc-macro-name-len cell[] !
  repeat,
  drop ;

```

## The dispatcher

The dispatcher consumes the prefix and reads the directive name. In the location-enabled profile it rejects GNU numeric line markers in active text and continuations that split directive names (`forth-bootstrap/cc/040-cc-prep.fth:2192`):

```forth file=cc/040-cc-prep.fth
\ ---------------------------------------------------------------------------
\ cc-prep-handle-directive  ( -- )
\ ---------------------------------------------------------------------------
\ Pre: pos is at the line's '#'.  Read the directive's name and dispatch.
\ In a dropped group only the conditionals count.  #error dies with 40.
\ Anything else is dropped.  Always ends at the end of the line.

create cc-prep-name-include  s, include
create cc-prep-name-define   s, define
create cc-prep-name-undef    s, undef
create cc-prep-name-error    s, error
create cc-prep-name-line     s, line

: cc-prep-handle-directive
  cc-pp-location-enabled @ if,
    put-count cc-prep-directive-prefix
  else, cc-prep-skip-blanks then,                 \ leading indent before '#'
  cc-prep-advance                                 \ consume '#'
  cc-pp-location-enabled @ if,
    put-count cc-prep-directive-prefix
  else, cc-prep-skip-blanks then,
  cc-pp-location-enabled @ cc-pp-skipping? 0= and if,
    cc-prep-peek digit? if, [lit] 49 cc-die then,
  then,
  cc-prep-peek ident-start? if,
    cc-prep-read-ident
    cc-pp-location-enabled @ cc-pp-line-continuation? and if,
      [lit] 49 cc-die
    then,
```

Conditionals are handled even while skipping, because they control nesting. Other directives act only in a kept group; `#error` stops preprocessing, and unrecognized directives are discarded through line end (`forth-bootstrap/cc/040-cc-prep.fth:2221`):

```forth file=cc/040-cc-prep.fth
    cc-pp-cond-directive if, cc-prep-skip-to-eol exit, then,
    cc-pp-skipping? 0= if,
      cc-pp-location-enabled @ if,
        cc-prep-name-line [lit] 4 cc-prep-ident= if,
          cc-prep-handle-line exit,
        then,
      then,
      cc-prep-name-include [lit] 7 cc-prep-ident= if,
        cc-prep-handle-include cc-prep-skip-to-eol exit,
      then,
      cc-prep-name-define [lit] 6 cc-prep-ident= if,
        cc-prep-handle-define cc-prep-skip-to-eol exit,
      then,
      cc-prep-name-undef [lit] 5 cc-prep-ident= if,
        cc-prep-handle-undef cc-prep-skip-to-eol exit,
      then,
      cc-prep-name-error [lit] 5 cc-prep-ident= if,
        [lit] 40 cc-die
      then,
    then,
  then,
  cc-prep-skip-to-eol ;

' cc-prep-handle-directive is cc-prep-handle-directive-fwd

```

## The built-in macros and the pass driver

Legacy mode supplies replacement text for names whose system headers it drops. These stored spellings are ordinary object-macro bodies, including the hexadecimal spelling for `EOF` (`forth-bootstrap/cc/040-cc-prep.fth:2246`):

```forth file=cc/040-cc-prep.fth
\ ===========================================================================
\ Built-in macros
\ ===========================================================================
\ What the dropped system headers would have defined and the subset's
\ programs use: <stdio.h>'s NULL, EOF, stdin/stdout/stderr (file
\ descriptors, see Appendix F), <stdlib.h>'s EXIT_SUCCESS/EXIT_FAILURE and
\ <fcntl.h>'s open(2) flags.

create cc-pp-t0      s, 0
create cc-pp-t1      s, 1
create cc-pp-t2      s, 2
create cc-pp-t64     s, 64
create cc-pp-t512    s, 512
create cc-pp-teof    s, 0xFFFFFFFFFFFFFFFF
```

The built-in name objects cover null and exit status, standard streams and open flags. They are separate from their replacement text so the same table-recording path can install them (`forth-bootstrap/cc/040-cc-prep.fth:2260`):

```forth file=cc/040-cc-prep.fth

create cc-builtin-name-NULL          s, NULL
create cc-builtin-name-EOF           s, EOF
create cc-builtin-name-EXIT_SUCCESS  s, EXIT_SUCCESS
create cc-builtin-name-EXIT_FAILURE  s, EXIT_FAILURE
create cc-builtin-name-stdin         s, stdin
create cc-builtin-name-stdout        s, stdout
create cc-builtin-name-stderr        s, stderr
create cc-builtin-name-O_RDONLY      s, O_RDONLY
create cc-builtin-name-O_WRONLY      s, O_WRONLY
create cc-builtin-name-O_CREAT       s, O_CREAT
create cc-builtin-name-O_TRUNC       s, O_TRUNC

```

`cc-prep-builtins` pairs each name with its body through `cc-macro-add`. User definitions can shadow these entries through the same lookup as any other macro (`forth-bootstrap/cc/040-cc-prep.fth:2273`):

```forth file=cc/040-cc-prep.fth
: cc-prep-builtins
  cc-builtin-name-NULL          [lit]  4  cc-pp-t0   [lit] 1  cc-macro-add
  cc-builtin-name-EOF           [lit]  3  cc-pp-teof [lit] 18 cc-macro-add
  cc-builtin-name-EXIT_SUCCESS  [lit] 12  cc-pp-t0   [lit] 1  cc-macro-add
  cc-builtin-name-EXIT_FAILURE  [lit] 12  cc-pp-t1   [lit] 1  cc-macro-add
  cc-builtin-name-stdin         [lit]  5  cc-pp-t0   [lit] 1  cc-macro-add
  cc-builtin-name-stdout        [lit]  6  cc-pp-t1   [lit] 1  cc-macro-add
  cc-builtin-name-stderr        [lit]  6  cc-pp-t2   [lit] 1  cc-macro-add
  cc-builtin-name-O_RDONLY      [lit]  8  cc-pp-t0   [lit] 1  cc-macro-add
  cc-builtin-name-O_WRONLY      [lit]  8  cc-pp-t1   [lit] 1  cc-macro-add
  cc-builtin-name-O_CREAT       [lit]  7  cc-pp-t64  [lit] 2  cc-macro-add
  cc-builtin-name-O_TRUNC       [lit]  7  cc-pp-t512 [lit] 3  cc-macro-add ;

```

### Dynamic built-ins

Location built-ins use special parameter tags so their values are computed at invocation. They remain real table entries for `defined`, replacement and `#undef`; the target hook is empty until a later layer selects target policy in Chapter 44 (`forth-bootstrap/cc/040-cc-prep.fth:2286`):

```forth file=cc/040-cc-prep.fth
\ ===========================================================================
\ cc-preprocess  ( -- )
\ ===========================================================================
\ Top-level driver.  Walks cc-in-buf and writes the result into cc-src-buf,
\ then rewinds the reader (cc-src-pos 0, cc-src-line 1) for the lexer.  An
\ #if still open at the end dies with 39.

\ Negative parameter tags below -1 identify dynamic object-like builtins.
\ They are real table entries: defined/#ifdef, replacement and undef work
\ through the same lookup as ordinary macros, without fixed line answers.
create cc-pp-name-line s, __LINE__
create cc-pp-name-file s, __FILE__
: cc-prep-location-builtins
  true cc-pp-location-enabled !
  cc-pp-name-line [lit] 8 [lit] 0 [lit] 0 [lit] 0 [lit] 2 - cc-macro-record
  cc-pp-name-file [lit] 8 [lit] 0 [lit] 0 [lit] 0 [lit] 3 - cc-macro-record ;

\ Optional target-owned predefined macros. The default preserves native output.
: cc-prep-target-default ;
defer cc-prep-target-fwd
' cc-prep-target-default is cc-prep-target-fwd

```

### The pass driver

`cc-preprocess` starts a fresh pass: it resets macro records, include and conditional depth, sink state, line debt and scratch storage, then selects the source buffer as output (`forth-bootstrap/cc/040-cc-prep.fth:2308`):

```forth file=cc/040-cc-prep.fth
: cc-preprocess
  cc-src-init
  [lit] 0 cc-macro-count !  cc-macro-hash-reset
  [lit] 0 cc-macro-pool-pos !
  [lit] 0 cc-prep-inc-depth !
  [lit] 0 cc-pp-cond-depth !
  [lit] 0 cc-pp-sink-depth !
  [lit] 0 cc-pp-pending-nl !
  [lit] 0 cc-pp-in-if ! [lit] 0 cc-pp-line-control !
  [lit] 0 cc-pp-line-map !
  cc-pp-scratch cc-pp-scratch-top !
  cc-src-buf cc-pp-out !  [lit] 0 cc-pp-out-pos !
  cc-src-cap cc-pp-out-cap !  [lit] 36 cc-pp-out-code !
  cc-pp-flags-init
```

The driver installs the selected built-ins, scans raw input and rejects an unclosed conditional. It publishes the sink length and rewinds source position and line state for Chapter 29's lexer (`forth-bootstrap/cc/040-cc-prep.fth:2322`):

```forth file=cc/040-cc-prep.fth
  cc-prep-direct @ 0= if, cc-prep-builtins then,
  [lit] 0 cc-pp-location-enabled ! [lit] 1 cc-pp-location-line !
  [lit] 0 cc-pp-location-rescan ! [lit] 0 cc-pp-location-depth !
  cc-prep-target-fwd
  [lit] 0 cc-prep-inc-top !
  cc-prep-source-path cc-prep-source-len @ cc-prep-file-paths cc-prep-copy-path
  cc-prep-source-len @ cc-prep-file-lens !
  cc-in-buf cc-prep-src-addr !
  cc-in-len @ cc-prep-src-len !
  [lit] 0 cc-prep-src-pos !
  cc-pp-location-enter
  [lit] 1 cc-pp-line-map-note
  true cc-prep-in-file !
  cc-pp-scan
  cc-pp-cond-depth @ if, [lit] 39 cc-die then,
  cc-pp-out-pos @ cc-src-len !
  [lit] 0 cc-src-pos !
  [lit] 1 cc-src-line ! ;
```

## Try it

Run this from the `forth-bootstrap` checkout root. The command loads the
complete Forth library and only the arena, I/O and preprocessor layers.
`dump-prep` loads the remaining stdin as C text, runs `cc-preprocess` and
prints the rewritten buffer. `#ifdef` uses macro lookup alone; `#if` is
excluded because its evaluator belongs to Chapter 34.

```sh
(
set -o pipefail
{
  cat forth/010-lib.fth cc/020-cc-arena.fth cc/030-cc-io.fth cc/040-cc-prep.fth || exit "$?"
  cat <<'FORTH' || exit "$?"
    : dump-prep
      cc-load-stdin cc-preprocess
      [lit] 0
      begin, dup cc-src-len @ < while,
        dup cc-src-buf + c@ emit
        [lit] 1 +
      repeat, drop
      bye ;
    dump-prep
FORTH
  cat <<'C' || exit "$?"
#define ROWS 4
#define SQUARE(x) ((x) * (x))
#ifdef ROWS
    int w[ROWS];
#else
    int w[1];
#endif
    if (t.stars == SQUARE(ROWS)) return t.stars;
C
} | ./seed-forth
)
```

Observed output, including its blank lines:

```text



    int w[ 4 ];



    if (t.stars ==  ((   4   ) * (   4   )) ) return t.stars;
```

The directives and inactive branch leave blank lines. `ROWS` expands inside
the array bound and again before substitution into `SQUARE`; separator
blanks keep the replacement's tokens distinct from their neighbours.

## Exercise

Hints and feedback are in [Appendix H](66-exercise-feedback.md#chapter-28-expansion-and-inactive-text).

**Trace (easy).** Follow `SQUARE(ROWS)` through argument expansion,
substitution and replacement rescanning. Account for each separator blank
around the expanded argument in the observed output.

**Verify (easy).** In the checkpoint input, change `#ifdef ROWS` to
`#ifdef ABSENT` and rerun. Check which array declaration remains and whether
the following statement retains its line position.
