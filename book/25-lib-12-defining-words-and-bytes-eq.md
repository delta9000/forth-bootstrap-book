# Chapter 25 — Defining words and byte equality

A named buffer gives a program somewhere to keep bytes between calls. A
defining word makes a name return a storage address; related words fill
that storage and choose what a name executes. The completed library
supplies buffers, variables, deferred calls, and byte comparisons.

## `allot` and `skip-vm-pages`: making room

The defining words share a shape: build a named runtime body, then place
its data directly after the code. Reserving space for that data is the
smallest piece of the construction. The opening comment leads into that
reservation operation in `forth-bootstrap/forth/010-lib.fth:374`:

```forth file=forth/010-lib.fth
\ ===== Defining-words: allot / create / variable =====
\ These let Forth code build variables and arbitrary data structures
\ without escaping back into 000-seed.hex0.  Like constant, create calls
\ the seed's `:` primitive to tokenize the next input word and build a
\ dictionary header (link, flags=0, name-len, name bytes), lays down the
\ 19-byte push body, and resets STATE=0 (since `:` left it at 1).

\ allot ( n -- )  Bump HERE by n bytes (no initialization).
\ Used after `create` to grow an array, or stand-alone for scratch buffers.
: allot  here-addr @ + here-addr ! ;

```

`allot ( n -- )` adds the requested byte count to HERE and stores the
result back. It writes no payload and performs no bounds check. With a
nonnegative count, the interval from the old HERE to the new HERE is
reserved for the caller; its contents still need initialization.

A large reservation must also avoid the seed's fixed working memory.
The library supplies an explicit cursor move in
`forth-bootstrap/forth/010-lib.fth:385`:

```forth file=forth/010-lib.fth
\ skip-vm-pages ( -- )  Jump HERE to the first page above the seed's fixed VM
\ pages: data stack (below 0x411000), I/O scratch byte (0x412000), token
\ buffer (0x412800) and the sysvar page, which starts at STATE's cell.  So
\ HERE becomes STATE + 4096 = 0x414000.  030-cc-io.fth and 130-asm.fth call
\ it before creating their megabyte buffers, which then cannot overlap VM
\ state.  HERE must still be below the data stack (0x410000) when it runs.
: skip-vm-pages  state [lit] 4096 + here-addr ! ;

```

`skip-vm-pages` sets HERE to the address of `STATE` plus a page. It neither
copies existing definitions nor allocates another mapping. It moves the
allocation cursor within the seed's existing memory so subsequent data
can grow above the fixed VM pages.

The source requires calling it while HERE is still below the data stack.
It is an explicit transition, not a guard inside `allot`: reserving a large
buffer first would defeat its purpose. Calling it again after allocating
above the VM pages would rewind HERE over that later allocation. The
checkpoint makes the transition before creating its buffers.

## `create`'s runtime body and `variable`'s cell

A buffer name should return the address where its payload begins.
`create` computes that address before emitting the body that will return
it, in `forth-bootstrap/forth/010-lib.fth:393`:

```forth file=forth/010-lib.fth
\ create ( "name" -- )  Define name as a word that pushes the address of
\ the data area immediately following its body.  Caller fills the data
\ area via `,` / `c,` / `allot`.  HERE is at the start of the body when
\ push-body, runs, and the body is 19 bytes, so the data area starts at
\ HERE + 19.
: create  : here [lit] 19 + push-body, [lit] 0 state ! ;
```

Let `B` be HERE after the inner `:` has consumed the new name. The existing
`push-body,` template (Chapter 23) occupies 19 bytes, so `B + 19` is the
future data address. That address becomes the value embedded in the
runtime body. Resetting `STATE` completes the definition.

After `create buf`, executing `buf` leaves that data address on the stack.
`create` itself reserves no payload. Follow it immediately with `allot`
or data writers, before another definition claims the same space. In the
checkpoint, `create buf` followed by `[lit] 3 allot` reserves the bytes
that later receive `A`, `B`, and `C`.

A mutable scalar needs initialized storage as well as a name. The small
wrapper in `forth-bootstrap/forth/010-lib.fth:399` supplies it:

```forth file=forth/010-lib.fth

\ variable ( "name" -- )  Define name as a word that pushes the address of
\ an 8-byte cell, initialized to 0: a create whose data area is one cell.
: variable  create [lit] 0 , ;

```

`variable counter` delegates name reading to `create`, then appends a zero
cell at the new word's data address. Executing `counter` supplies an
address for either fetching or storing; it does not fetch the current
value. The checkpoint first checks the initial zero, then stores and
reads back a character.

The distinction is in the payload: `create` leaves its size and contents
to the caller; `variable` chooses a zero-initialized cell. Neither creates
a separate heap object.

## `defer` and `is`: a name now, a meaning later

Suppose `twice` must call `greet` before the implementation of `greet`
exists. `defer greet` gives the caller a stable entry point. The entry
point reads its current target from a writable cell, much like calling
through a function pointer in C.

The target cell needs a known position relative to that entry point.
The layout and its saved helper addresses appear in
`forth-bootstrap/forth/010-lib.fth:404`:

```forth file=forth/010-lib.fth
\ ===== Deferred words: defer / is =====
\ A word can only call words that already exist, but two words that call
\ each other (a statement parser and the if-statement parser inside it)
\ cannot both come first.  defer names a word now and says what it does
\ later: its body calls whatever xt sits in a cell after its code, and is
\ fills that cell once the real word exists.
\
\ A deferred word's body is 29 bytes of code, then the cell:
\   <18 bytes>   push-imm64, of the cell's address   ; rdi = &cell
\   E8 <rel32>   call @                              ; rdi = the xt
\   E8 <rel32>   call execute                        ; run it
\   C3           ret
\   <8 bytes>    the cell (0 until is fills it)
' @       constant fetch-xt
' execute constant execute-xt
[lit] 29 constant defer-code-size

```

`fetch-xt` holds the execution token of `@`; `execute-xt` holds the token
of `execute`. These are the helper calls the wrapper will emit, independent
of the eventual target stored in its cell. `defer-code-size` records the
cell's offset from the start of the wrapper.

The size follows the emitted layout: an 18-byte push of the cell address,
a 5-byte fetch call, a 5-byte execute call, and a 1-byte return put the
cell at offset 29. Both the constructor and the setter use that same
offset. Changing the wrapper would require changing it too.

The constructor must emit a fetch of the target, rather than embed the
target itself, so later assignments remain visible. That construction is
in `forth-bootstrap/forth/010-lib.fth:421`:

```forth file=forth/010-lib.fth
\ defer ( "name" -- )  Define name as a word that runs the xt in its cell.
: defer
  : here defer-code-size + push-imm64,           \ rdi = address of the cell
  fetch-xt call,  execute-xt call,  ret,
  [lit] 0 ,  [lit] 0 state ! ;
```

For a wrapper beginning at `B`, `push-imm64,` embeds `B + defer-code-size`.
At runtime the wrapper pushes this cell address, fetches the target xt,
and executes it. When the target returns, the wrapper's trailing return
passes control back to its caller. Any arguments and results belong to
the target's stack contract.

The appended cell initially contains zero. Bind the deferred word before
calling it: this implementation has no unbound-target check. Its final
store to `STATE` completes the definition without making the cell part
of the executable body.

Assignment must locate the cell from the deferred name, even after other
definitions have moved HERE. The setter in
`forth-bootstrap/forth/010-lib.fth:426` uses the wrapper's entry point:

```forth file=forth/010-lib.fth

\ is ( xt "name" -- )  Make the deferred word name run xt from now on.
\ ' finds name's code; its cell sits defer-code-size bytes further on.
: is  ' defer-code-size + ! ;

```

In `' say-a is greet`, the stack entering `is` holds `xt-say-a`.
The tick inside `is` reads `greet`, giving
`xt-say-a xt-greet`; adding `defer-code-size` produces
`xt-say-a target-cell`, ready for the store.

Existing calls still address `greet`, so rebinding that cell also changes
what already-compiled callers do. In the checkpoint, `twice` is compiled
before either implementation is assigned, then follows both assignments
without being rebuilt. `is` assumes its name identifies a deferred word;
it does not validate that layout. Replacements must also honor the stack
contract their callers expect.

## `s,`: names as data

A name used as data needs an address and a length, independently of whether
it names a dictionary entry. `token` obtains that pair by reading into the
token buffer and recovering the length. Its implementation is in
`forth-bootstrap/forth/010-lib.fth:431`:

```forth file=forth/010-lib.fth
\ token ( "tok" -- a u )  read the next token; leave its address in the TIB
\ and its length.  The seed keeps the length in a register Forth cannot
\ see, so we blank the TIB's 256 bytes first and then count the token's
\ bytes up to the first blank (a token is at most 255 bytes).
: token
  tib [lit] 256 + tib                            ( end p )
  begin, 2dup > while, bl over c! 1+ repeat,     \ fill the TIB with blanks
  2drop  ' drop                                  \ read the token into it
  tib [lit] 0                                    ( a 0 )
  begin, 2dup + c@ bl <> while, 1+ repeat, ;     ( a u )

```

The first loop blanks the buffer. Its state is `end p`: each iteration
writes a blank at `p` and advances `p` until it reaches `end`.
The subsequent tick reads the token; `drop` discards the lookup result,
so the token need not be a defined word.

The final loop carries `a u`, where `a` stays at the buffer start and `u`
grows while the byte at `a + u` is not blank. Preblanking makes the first
unused position a sentinel even when an earlier token was longer. The
source's buffer size and token limit leave room for that sentinel.

The returned address points into shared scratch storage. Another token
read can overwrite those bytes, so a name that must survive needs copying
before control returns to the input loop.

Copying an address-length pair into dictionary storage is the job of
`bytes,` in `forth-bootstrap/forth/010-lib.fth:442`:

```forth file=forth/010-lib.fth
\ bytes, ( a u -- )  copy u bytes from a to HERE, advancing HERE.
: bytes,
  begin, dup while,
    over c@ c,  1- swap 1+ swap
  repeat,
  2drop ;
```

Each iteration transforms `a u` into `a+1 u-1`, with the byte formerly
at `a` appended to HERE. The loop ends with the advanced address and the
exhausted count, which `2drop` removes. An initially zero count copies
nothing. The caller supplies a valid source range and a nonnegative count.

Reading and copying must happen within the same operation to preserve the
scratch-buffer contents. The composition in
`forth-bootstrap/forth/010-lib.fth:448` does exactly that:

```forth file=forth/010-lib.fth

\ s, ( "tok" -- )  copy the next token's bytes to HERE: `create name s, text`
\ lays down the string "text" without a terminator or a length.
: s,  token bytes, ;

```

`create name-a s, maple` gives `name-a` a data area containing `maple`.
Here “names as data” means raw bytes whose count the caller tracks.
`s,` stores neither a length prefix nor a terminator. A later comparison must receive the
length separately. Whitespace separates tokens, so this word is not a
reader for quoted strings containing spaces.

The checkpoint also makes `name-b` by copying from `name-a` with `bytes,`.
That source is persistent dictionary storage, so it does not have the
token buffer's lifetime constraint.

## `bytes-eq`: stop at the first mismatch

Equality can reject a candidate as soon as a byte differs. The library's
last definition, in `forth-bootstrap/forth/010-lib.fth:453`, carries the
remaining count alongside the current addresses:

```forth file=forth/010-lib.fth
\ ===== bytes-eq =====
\ bytes-eq ( a1 a2 u -- f )  -1 if first u bytes at a1 match those at a2; 0 else.
\ Used by symbol-table name comparison and keyword recognition in the C
\ compiler.  Stops at the first mismatch: exit, returns 0 from inside the
\ loop, after r> drop has taken the parked count off the return stack.
: bytes-eq
  begin,
    dup [lit] 0 >
  while,
    >r                                           ( a1 a2  R: u )
    over c@ over c@ <> if,                       ( a1 a2 )
      r> drop 2drop [lit] 0 exit,                \ mismatch: answer 0
    then,
    1+ swap 1+ swap                              ( a1+1 a2+1 )
    r> 1-                                        ( a1+1 a2+1 u-1 )
  repeat,
  drop 2drop true ;                              \ all u bytes matched
```

`bytes-eq ( a1 a2 u -- f )` compares exactly the requested prefix, provided
`u` is nonnegative and both ranges are readable. It returns true when
all requested bytes match, false at the first mismatch. It does not
compare stored lengths or search for a terminator. To compare whole names,
the caller must establish equal lengths before comparing their bytes.

At the top of each iteration, the already-consumed prefixes match and
`a1 a2 u` describes what remains. Parking `u` exposes the addresses for
the byte comparison:

| Point in the body | Data stack | Saved count |
| --- | --- | --- |
| After `>r` | `a1 a2` | `u` |
| After the byte fetches | `a1 a2 byte-a byte-b` | `u` |
| After the conditional test | `a1 a2` | `u` |
| Equal path, after address advances | `a1+1 a2+1` | `u` |
| After `r> 1-` | `a1+1 a2+1 u-1` | removed |

The mismatch path must satisfy `exit,`'s clean-return-stack rule
(Chapter 24). Its `r> drop` removes the saved count before the early
return; `2drop` discards the addresses. That path leaves only the false
result above the caller's original stack.

The exhausted-count path has no saved count to recover. It drops the
count and addresses and returns true. In particular, a zero-length
comparison succeeds without fetching either address. The checkpoint
separates whole-range equality, a mismatch, an empty comparison, and a
matching prefix of otherwise different names.

Chapter 26 uses this vocabulary to build the M1 assembler and hex2 linker.

## Try it

Run this from the `forth-bootstrap` checkout at `./forth-bootstrap`, using
the seed built in Part 1. `head -n 469` loads the complete library through
`bytes-eq`, with no assembler or compiler layers.

<!-- tryit: expect "1\nABC\n1B\nAABB\n1011\n5" -->
```sh
{ head -n 469 forth/010-lib.fth
  printf '%s\n' \
    ': flag if, [char] 1 emit else, [char] 0 emit then, ;' \
    'skip-vm-pages here state [lit] 4096 + = flag nl emit' \
    'create buf [lit] 3 allot' \
    'char A buf c! char B buf 1+ c! char C buf [lit] 2 + c!' \
    'buf c@ emit buf 1+ c@ emit buf [lit] 2 + c@ emit nl emit' \
    'variable counter counter @ 0= flag' \
    'char B counter ! counter @ emit nl emit' \
    'defer greet : twice greet greet ;' \
    ": say-a [char] A emit ; ' say-a is greet twice" \
    ": say-b [char] B emit ; ' say-b is greet twice nl emit" \
    'create name-a s, maple' \
    'create name-b name-a [lit] 5 bytes,' \
    'create name-c s, mapXe' \
    'name-a name-b [lit] 5 bytes-eq flag' \
    'name-a name-c [lit] 5 bytes-eq flag' \
    'name-a name-c [lit] 0 bytes-eq flag' \
    'name-a name-c [lit] 3 bytes-eq flag nl emit' \
    ': token-length token nip ;' \
    'token-length maple [lit] 48 + emit nl emit' \
    'bye'
} | ./seed-forth
# prints "1\nABC\n1B\nAABB\n1011\n5"
```

Observed output:

```text
1
ABC
1B
AABB
1011
5
```

The first line checks the cursor destination chosen by `skip-vm-pages`.
`ABC` checks storage reserved by `create` and `allot`; `1B` checks the
variable's initial value and subsequent store. `AABB` shows an existing
caller following both deferred assignments. `1011` records equal ranges,
a mismatch, an empty comparison, and an equal prefix. The final line is
the token length recovered from `maple`.

## Exercise

**Trace (easy).** Follow `name-a name-c [lit] 5 bytes-eq` from the
checkpoint. At the mismatch, write down the data stack and the saved
count. Explain which item the emitted return would use as its destination
if `r> drop` were omitted.

**Modify (moderate).** Change `mapXe` to `Xaple`, then to `maplX`.
Predict which flags change and how far each comparison reads, then run
the checkpoint to check the flags.

<details>
<summary>Hint: include the parked count in the return-stack picture</summary>

The mismatch is at zero-based byte index 3. Two bytes remain in the
requested range, including that mismatching byte. Separate that saved
count from the caller's return address before following the early exit.

</details>

<details>
<summary>Check cleanup and the changed strings</summary>

After `if,` consumes the mismatch flag, the data stack is `S a+3 c+3`
and the saved count is `2` above the caller's continuation. `r> drop`
removes the count, `2drop` removes the pointers, and zero becomes the
result. Omitting `r> drop` makes the early `ret` take address `2`.

The four predicted flags are `1011` for `mapXe`, `1010` for `Xaple`,
and `1011` for `maplX`. In the length-five a/c comparison, they inspect
four, one, and five byte pairs respectively. The zero-length comparison
reads none; the length-three comparison reads three pairs except for
`Xaple`, which stops at its first pair. Equal printed flags need not
mean equal work. Recheck both stack cleanup and read distance when
moving a mismatch.

</details>
