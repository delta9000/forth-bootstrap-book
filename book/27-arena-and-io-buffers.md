# Chapter 27 — Arena and I/O buffers

The compiler's first data structures are storage regions for source text, unfinished output and records whose sizes emerge during parsing. Giving each responsibility a bounded region makes its lifetime explicit before there is a C parser to use it. The result is an allocator, a source reader and an output buffer that later compiler layers can share.

## Part 3: from storage to a C compiler

The code has this shape:

```text
020-cc-arena: native Forth replacements → lexer state → diagnostics → arena
030-cc-io:    raw input → source buffer → character reader
             output buffer → append or patch → file
             shared name helpers and workspace selection
```

Chapter 27 establishes storage. Chapters 28–30 build preprocessing, lexing,
types and symbols; Chapters 31–32 supply executable emission. Chapters
33–37 connect expressions, declarations, statements and functions, and
Chapter 38 joins the core compiler and checks Stage A. Chapters 39–42
extend storage and introduce objects, the System V interface and linking.
Chapters 43–49 add the runtime, target headers, typed constants, varargs,
floating values, bitfields and aggregate calling rules.

The compiler uses the Forth library from Chapters 14–25. Its storage layer
also replaces expensive Forth operations before the later layers are read.

Variable-size records need a different home from fixed tables (`forth-bootstrap/cc/020-cc-arena.fth:1`):

```forth file=cc/020-cc-arena.fth
\ 020-cc-arena.fth — the compiler's ground floor: the lexer's state block,
\ how the compiler fails (cc-die, cc-check-cap), and a bump allocator for
\ variable-size data (struct descriptors, call/goto fixup lists, switch-case
\ lists — anything that doesn't fit a fixed slot in a parallel array).  Most
\ compiler state lives in fixed-size buffers (parallel arrays declared with
\ `create NAME N allot`); this arena handles the rest.
\
\ Depends on 010-lib.fth: constant, variable, create, allot, s,, char, [lit],
\ if,/then,, begin,/until,, swap, dup, over, nip, drop, >r, r>, +, -, /, *,
\ >, !, @, c!, c,, write, die.

```

## Redirecting existing Forth words

Previously compiled callers already contain execution tokens. `code:`
creates a fresh header and returns to interpretation so emitters can fill
its body. `native!` redirects an old address to the new body; `code-start`
remembers that destination while the body is emitted (`forth-bootstrap/cc/020-cc-arena.fth:12`):

```forth file=cc/020-cc-arena.fth
\ ----- The compiler's arithmetic in machine code -----
\ 010-lib.fth builds - from nand and +, and the sign test 0< from the
\ unsigned / (a 64-bit divide per comparison).  The compiler runs them
\ hundreds of millions of times, so here they become x86 code with the
\ same answers: < is still (a - b)'s sign bit, wrapping as before.  Each
\ native word gets a fresh header (code:), and native! turns the first
\ definition into a jump to it, so every word compiled earlier, in
\ 010-lib.fth too, runs the new code.  TOS is in rdi and the data stack
\ grows down from rbp, as in the seed's +.
: code:  : [lit] 0 state ! ;             \ header only; c, lays the body
: native!  ( old new -- )                \ old's first bytes: JMP rel32 new
  over [lit] 5 + -  swap                 \ rel32 first: old may be - itself
  here >r  here-addr !  [lit] 233 c, ,4
  r> here-addr ! ;
variable code-start
```

The displacement is calculated before the old body is overwritten. This
ordering matters when the old body is subtraction itself. Saving and
restoring HERE lets the patch change old code without moving the end of
the dictionary. The source's performance claims are not measurements made
by this checkpoint.

The subtraction body loads the left operand into `rax`, consumes its stack
slot and subtracts `rdi`. `mov-rax-[rbp],`, `add-rbp-8,`,
`sub-rax-rdi,` and `mov-rdi-rax,` name those instruction pieces;
`sar63,` selects the register whose sign is spread into a flag (`forth-bootstrap/cc/020-cc-arena.fth:27`):

```forth file=cc/020-cc-arena.fth
: mov-rax-[rbp],  [lit] 72 c, [lit] 139 c, [lit] 69 c, [lit] 0 c, ;
: add-rbp-8,      [lit] 72 c, [lit] 131 c, [lit] 197 c, [lit] 8 c, ;
: sub-rax-rdi,    [lit] 72 c, [lit] 41 c, [lit] 248 c, ;
: mov-rdi-rax,    [lit] 72 c, [lit] 137 c, [lit] 199 c, ;
: sar63,  ( modrm -- )  [lit] 72 c, [lit] 193 c, c, [lit] 63 c, ;
' - code: -  here code-start !            \ ( a b -- a-b )
  mov-rax-[rbp], add-rbp-8, sub-rax-rdi, mov-rdi-rax, ret,
  code-start @ native!
' 0< code: 0<  here code-start !          \ ( n -- f )  sar rdi, 63
  [lit] 255 sar63, ret,
  code-start @ native!
' < code: <  here code-start !            \ ( a b -- f )  sign of a - b
  mov-rax-[rbp], add-rbp-8, sub-rax-rdi, [lit] 248 sar63, mov-rdi-rax, ret,
  code-start @ native!
```

`0<` shifts `rdi`; `<` shifts the subtraction result in `rax`. The latter
preserves the library comparison's signed-overflow domain (Chapter 20). It does
not replace subtraction with an overflow-aware signed comparison.

Equality uses the subtraction's zero flag, then `sete`, zero-extension and
negation produce the Forth result. Increment and decrement need only their
native arithmetic instruction and a return (`forth-bootstrap/cc/020-cc-arena.fth:41`):

```forth file=cc/020-cc-arena.fth
' = code: =  here code-start !            \ ( a b -- f )  a - b = 0
  mov-rax-[rbp], add-rbp-8, sub-rax-rdi,
  [lit] 15 c, [lit] 148 c, [lit] 192 c,   \ sete al
  [lit] 72 c, [lit] 15 c, [lit] 182 c, [lit] 248 c,   \ movzx rdi, al
  [lit] 72 c, [lit] 247 c, [lit] 223 c,   \ neg rdi
  ret,
  code-start @ native!
' 1+ code: 1+  here code-start !          \ add rdi, 1
  [lit] 72 c, [lit] 131 c, [lit] 199 c, [lit] 1 c, ret,
  code-start @ native!
' 1- code: 1-  here code-start !          \ sub rdi, 1
  [lit] 72 c, [lit] 131 c, [lit] 239 c, [lit] 1 c, ret,
  code-start @ native!

```

## Handing buffered input to the compiler

Reading Forth source ahead can also consume the beginning of the C input.
`key-buffer` owns the bytes, `key-pos` names the next unread position and
`key-len` records the valid end. `movabs-rsi,` and `movabs-rdx,` embed the
addresses used by the reader (`forth-bootstrap/cc/020-cc-arena.fth:55`):

```forth file=cc/020-cc-arena.fth
\ The seed's key reads stdin one byte per read syscall, and the compiler
\ arrives through key: about 500 KB of Forth source on every run.  key-fill
\ below is key with a 64 KiB buffer; native! sends the seed's key, which its
\ reader calls directly, there too.  The C source that follows the Forth
\ text on stdin is then partly in the buffer: key-drain hands it over to
\ cc-read-all (030).
[lit] 4096 constant key-buffer-size
create key-buffer key-buffer-size allot
variable key-pos
variable key-len
: movabs-rsi,  [lit] 72 c, [lit] 190 c, ,8 ;
: movabs-rdx,  [lit] 72 c, [lit] 186 c, ,8 ;
```

The definition sets `key-buffer-size` to 4096 bytes. The preceding comment's
“64 KiB” is stale; the syscall below uses the constant.

`key-fill` serves a buffered byte when the position is below the length.
Otherwise it refills from stdin, resets the position and returns the first
byte; a nonpositive read returns zero. Patching the original `key` also
redirects the seed's reader (`forth-bootstrap/cc/020-cc-arena.fth:67`):

```forth file=cc/020-cc-arena.fth
' key code: key-fill  here code-start !   \ ( -- c ), 0 at end of input
  [lit] 72 c, [lit] 131 c, [lit] 237 c, [lit] 8 c,     \ sub rbp, 8
  [lit] 72 c, [lit] 137 c, [lit] 125 c, [lit] 0 c,     \ mov [rbp], rdi
  key-pos movabs-rsi,  [lit] 72 c, [lit] 139 c, [lit] 6 c,   \ mov rax, [rsi]
  key-len movabs-rdx,  [lit] 72 c, [lit] 59 c, [lit] 2 c,    \ cmp rax, [rdx]
  [lit] 114 c, [lit] 41 c,                             \ jb .have
  [lit] 49 c, [lit] 192 c,  [lit] 49 c, [lit] 255 c,   \ xor eax,eax  xor edi,edi
  key-buffer movabs-rsi,                               \ read(0, buffer,
  [lit] 186 c, key-buffer-size ,4  [lit] 15 c, [lit] 5 c,   \ size): syscall
  [lit] 72 c, [lit] 133 c, [lit] 192 c,                \ test rax, rax
  [lit] 126 c, [lit] 46 c,                             \ jle .eof
  key-len movabs-rdx,  [lit] 72 c, [lit] 137 c, [lit] 2 c,   \ mov [rdx], rax
  [lit] 49 c, [lit] 192 c,                             \ xor eax, eax
  key-buffer movabs-rsi,                               \ .have:
  [lit] 15 c, [lit] 182 c, [lit] 60 c, [lit] 6 c,      \ movzx edi, byte [rsi+rax]
  [lit] 72 c, [lit] 255 c, [lit] 192 c,                \ inc rax
  key-pos movabs-rdx,  [lit] 72 c, [lit] 137 c, [lit] 2 c,   \ mov [rdx], rax
  ret,
  [lit] 49 c, [lit] 255 c, ret,                        \ .eof: xor edi,edi
  code-start @ native!
```

`key-drain` transfers unread bytes to another buffer without another syscall.
Its scratch variables `kd-buf`, `kd-cap` and `kd-n` hold the destination,
maximum transfer and count copied. The loop stops at either bound (`forth-bootstrap/cc/020-cc-arena.fth:87`):

```forth file=cc/020-cc-arena.fth
\ key-drain ( buf cap -- n )  Move up to cap bytes that key-fill has read
\ but not handed out to buf; answer how many.
variable kd-buf
variable kd-cap
variable kd-n
: key-drain
  kd-cap ! kd-buf !  [lit] 0 kd-n !
  begin, kd-n @ kd-cap @ <  key-pos @ key-len @ <  and while,
    key-buffer key-pos @ + c@  kd-buf @ kd-n @ + c!
    [lit] 1 key-pos +!  [lit] 1 kd-n +!
  repeat,
  kd-n @ ;

```

This handoff prevents `cc-read-all` from losing C bytes already fetched
while the Forth definitions were being loaded. A destination too small to
accept all pending bytes leaves the remaining bytes in `key-buffer`.

## Compiling literals and branches directly

New definitions can contain instructions directly in place of calls to
small helpers. The replacement `[lit]` first delegates to `seed-lit`, then
uses `here-8` to retrieve the value and `here-13` to rewind over the old
encoding before emitting `push-imm64,` (Chapter 23) (`forth-bootstrap/cc/020-cc-arena.fth:100`):

```forth file=cc/020-cc-arena.fth
\ ----- A light optimizing compile -----
\ The seed compiles every word as a CALL.  For literals and branches that
\ CALL goes to lit, branch or 0branch, which pop and rewrite their own
\ return address, so the processor mispredicts the return each time.  From
\ here on [lit] lays an inline push, the control-flow words lay test and
\ jump instructions, and the commonest primitives are copied in place of
\ the CALL.  Each new word acts only while compiling (state @); run from
\ the interpreter it does what the old one did.  Words already compiled,
\ 010-lib.fth's included, keep their CALLs.
\ [lit] first: the seed's [lit] compiles CALL lit and the value's cell (13
\ bytes); take the value back out and lay the 18-byte push instead.
' [lit] constant seed-lit
: here-8   here [lit] 8 - ;
: here-13  here [lit] 13 - ;
: [lit]
  seed-lit execute
  state @ if,
    here-8 @  here-13 here-addr !  push-imm64,
  then, ;
immediate
```

Branch replacements keep the existing control-word interface but use
relative displacement fields. `flag-test,` consumes the condition into
`rax`; `jz-fwd,` and `jmp-fwd,` leave a field to patch with `rel32!`.
`jz-back,` and `jmp-back,` calculate an already-known destination (`forth-bootstrap/cc/020-cc-arena.fth:120`):

```forth file=cc/020-cc-arena.fth
\ Branches: if, while, and until, pop the flag and jz rel32; else, repeat,
\ and again, jmp rel32.  A forward fixup is the address of the rel32 field.
: rel32!  ( target fixup -- )
  dup [lit] 4 + rot swap -  swap
  here >r  here-addr ! ,4  r> here-addr ! ;
: flag-test,                                  \ rax = flag, popped; test it
  [lit] 72 c, [lit] 137 c, [lit] 248 c,                     \ mov rax, rdi
  [lit] 72 c, [lit] 139 c, [lit] 125 c, [lit] 0 c,          \ mov rdi, [rbp]
  add-rbp-8,  [lit] 72 c, [lit] 133 c, [lit] 192 c, ;       \ test rax, rax
: jz-fwd,    flag-test, [lit] 15 c, [lit] 132 c, here [lit] 0 ,4 ;
: jmp-fwd,   [lit] 233 c, here [lit] 0 ,4 ;
: jz-back,   flag-test, [lit] 15 c, [lit] 132 c, here [lit] 4 + - ,4 ;
: jmp-back,  [lit] 233 c, here [lit] 4 + - ,4 ;
: if,      jz-fwd, ;                        immediate
: then,    here swap rel32! ;               immediate
: else,    jmp-fwd, swap here swap rel32! ; immediate
: begin,   here ;                           immediate
: while,   jz-fwd, ;                        immediate
: repeat,  swap jmp-back, here swap rel32! ; immediate
: until,   jz-back, ;                       immediate
: again,   jmp-back, ;                      immediate
```

The immediate control words below the emitters select those operations:
`if,` and `while,` reserve conditional fields; `then,` resolves one;
`else,` reserves the onward jump before resolving the conditional field.
`begin,` retains HERE, while `repeat,`, `until,` and `again,` use backward
jumps. Only the generated representation changes.

## Inline primitives with an interpretation fallback

Each replacement uses the same dispatch: emit instructions while compiling,
execute a saved implementation while interpreting. `push-tos,` and
`pop-tos,` supply the stack movement. `compiling?` captures the old fetch
before `@` is replaced, avoiding a call from the new fetch to itself (`forth-bootstrap/cc/020-cc-arena.fth:141`):

```forth file=cc/020-cc-arena.fth
\ Primitives copied in place of the CALL: the seed's bodies without their
\ ret, with the return-stack words' own return address left out.
: push-tos,  [lit] 72 c, [lit] 131 c, [lit] 237 c, [lit] 8 c,      \ sub rbp, 8
             [lit] 72 c, [lit] 137 c, [lit] 125 c, [lit] 0 c, ;    \ mov [rbp], rdi
: pop-tos,   [lit] 72 c, [lit] 139 c, [lit] 125 c, [lit] 0 c, add-rbp-8, ;
\ A word can see its own name while it is being defined, so the new @ must
\ not read state with @: compiling? was compiled with the seed's.
: compiling?  state @ ;
' dup constant seed-dup     : dup   compiling? if, push-tos, else, seed-dup execute then, ; immediate
' drop constant seed-drop   : drop  compiling? if, pop-tos, else, seed-drop execute then, ; immediate
' swap constant seed-swap
: swap  compiling? if,
    [lit] 72 c, [lit] 135 c, [lit] 125 c, [lit] 0 c,      \ xchg rdi, [rbp]
  else, seed-swap execute then, ; immediate
' over constant seed-over
: over  compiling? if,
    push-tos, [lit] 72 c, [lit] 139 c, [lit] 125 c, [lit] 8 c,   \ mov rdi, [rbp+8]
  else, seed-over execute then, ; immediate
```

`seed-dup`, `seed-drop`, `seed-swap` and `seed-over` retain the previous
execution tokens. The inline `swap` uses `xchg`; inline `over` loads the
older item after making room. Call these paired paths **inline/fallback compilation**.

Memory operations use inline/fallback compilation without changing their stack effects.
`seed-fetch`, `seed-cfetch`, `seed-store` and `seed-cstore` preserve the
interpretation paths; the store bodies consume both address and value (`forth-bootstrap/cc/020-cc-arena.fth:159`):

```forth file=cc/020-cc-arena.fth
' @ constant seed-fetch
: @  compiling? if, [lit] 72 c, [lit] 139 c, [lit] 63 c,    \ mov rdi, [rdi]
  else, seed-fetch execute then, ; immediate
' c@ constant seed-cfetch
: c@  compiling? if, [lit] 72 c, [lit] 15 c, [lit] 182 c, [lit] 63 c,   \ movzx rdi, byte [rdi]
  else, seed-cfetch execute then, ; immediate
' ! constant seed-store
: !  compiling? if,
    mov-rax-[rbp], [lit] 72 c, [lit] 137 c, [lit] 7 c,    \ mov [rdi], rax
    add-rbp-8, pop-tos,
  else, seed-store execute then, ; immediate
' c! constant seed-cstore
: c!  compiling? if,
    mov-rax-[rbp], [lit] 136 c, [lit] 7 c,                \ mov [rdi], al
    add-rbp-8, pop-tos,
  else, seed-cstore execute then, ; immediate
```

Arithmetic uses the same inline/fallback compilation. `seed-plus` retains
addition, while `native-minus`, `native-1+` and `native-1-` retain the
native bodies just installed (`forth-bootstrap/cc/020-cc-arena.fth:175`):

```forth file=cc/020-cc-arena.fth
' + constant seed-plus
: +  compiling? if,
    [lit] 72 c, [lit] 3 c, [lit] 125 c, [lit] 0 c, add-rbp-8,   \ add rdi, [rbp]
  else, seed-plus execute then, ; immediate
' - constant native-minus
: -  compiling? if,
    mov-rax-[rbp], add-rbp-8, sub-rax-rdi, mov-rdi-rax,
  else, native-minus execute then, ; immediate
' 1+ constant native-1+
: 1+  compiling? if, [lit] 72 c, [lit] 131 c, [lit] 199 c, [lit] 1 c,
  else, native-1+ execute then, ; immediate
' 1- constant native-1-
: 1-  compiling? if, [lit] 72 c, [lit] 131 c, [lit] 239 c, [lit] 1 c,
  else, native-1- execute then, ; immediate
```

## Keeping return-stack operations frame-free

A fallback call would add a return address that the return-stack operation
could mistake for data. `jmp-xt,` instead emits a tail jump.
`seed->r`, `seed-r>` and `seed-r@` hold the targets; their
`jmp-seed->r,`, `jmp-seed-r>,` and `jmp-seed-r@,` helpers lay those jumps
into the interpretation arms (`forth-bootstrap/cc/020-cc-arena.fth:189`):

```forth file=cc/020-cc-arena.fth
\ The return stack is the x86 stack, so inline >r, r> and r@ are push,
\ pop and a load from [rsp].  Interpreted, they must not add a call frame
\ of their own, so they end in a jump to the seed's word (jmp-xt,).
: jmp-xt,  ( xt -- )  [lit] 233 c, here [lit] 4 + - ,4 ;
' >r constant seed->r
' r> constant seed-r>
' r@ constant seed-r@
: jmp-seed->r,  seed->r jmp-xt, ; immediate
: jmp-seed-r>,  seed-r> jmp-xt, ; immediate
: jmp-seed-r@,  seed-r@ jmp-xt, ; immediate
: >r  compiling? if, [lit] 87 c, pop-tos, exit, then, jmp-seed->r, ; immediate  \ push rdi
: r>  compiling? if, push-tos, [lit] 95 c, exit, then, jmp-seed-r>, ; immediate \ pop rdi
: r@  compiling? if, push-tos, [lit] 72 c, [lit] 139 c, [lit] 60 c, [lit] 36 c, exit, then,
  jmp-seed-r@, ; immediate                                                    \ mov rdi, [rsp]

```

The compilation arms emit `push`, `pop` or a load from `rsp` into the
caller's body. Their `exit,` finishes emission before control reaches the
tail-jump arm. The interpreted operation therefore reaches the seed body
with the return-stack arrangement that body expects.

## Inlining arithmetic and predicates

Multiplication and division retain `seed-star` and `seed-slash` for
interpretation. The inline division clears `rdx` before unsigned `div`;
the multiplication transfers its result from `rax` back to `rdi` (`forth-bootstrap/cc/020-cc-arena.fth:204`):

```forth file=cc/020-cc-arena.fth
\ More primitives copied in: *, /, 0=, nand, and, or.
' * constant seed-star
: *  compiling? if,
    [lit] 72 c, [lit] 137 c, [lit] 248 c,                          \ mov rax, rdi
    [lit] 72 c, [lit] 15 c, [lit] 175 c, [lit] 69 c, [lit] 0 c,    \ imul rax, [rbp]
    add-rbp-8, mov-rdi-rax,
  else, seed-star execute then, ; immediate
' / constant seed-slash
: /  compiling? if,
    mov-rax-[rbp], [lit] 72 c, [lit] 49 c, [lit] 210 c,           \ xor rdx, rdx
    [lit] 72 c, [lit] 247 c, [lit] 247 c,                          \ div rdi
    add-rbp-8, mov-rdi-rax,
  else, seed-slash execute then, ; immediate
```

`0=,` emits the complete zero-test body, with `seed-0=` as its fallback.
`and,` and `or,` provide reusable binary emitters; `seed-nand` preserves
NAND, while `native-and` and `native-or` preserve the newly installed
standalone Boolean bodies (`forth-bootstrap/cc/020-cc-arena.fth:217`):

```forth file=cc/020-cc-arena.fth
: 0=,  [lit] 72 c, [lit] 133 c, [lit] 255 c,                      \ test rdi, rdi
       [lit] 64 c, [lit] 15 c, [lit] 148 c, [lit] 199 c,          \ sete dil
       [lit] 72 c, [lit] 15 c, [lit] 182 c, [lit] 255 c,          \ movzx rdi, dil
       [lit] 72 c, [lit] 247 c, [lit] 223 c, ;                    \ neg rdi
' 0= constant seed-0=
: 0=  compiling? if, 0=, else, seed-0= execute then, ; immediate
: and,  [lit] 72 c, [lit] 35 c, [lit] 125 c, [lit] 0 c, add-rbp-8, ;   \ and rdi, [rbp]
: or,   [lit] 72 c, [lit] 11 c, [lit] 125 c, [lit] 0 c, add-rbp-8, ;   \ or rdi, [rbp]
' nand constant seed-nand
: nand  compiling? if, and, [lit] 72 c, [lit] 247 c, [lit] 215 c,      \ not rdi
  else, seed-nand execute then, ; immediate
' and code: and  here code-start !  and, ret,  code-start @ native!
' and constant native-and
: and  compiling? if, and, else, native-and execute then, ; immediate
' or code: or  here code-start !  or, ret,  code-start @ native!
' or constant native-or
: or  compiling? if, or, else, native-or execute then, ; immediate
```

Character predicates get native range checks through `in-range,`: subtract
the lower bound, compare unsigned against the count, and use `sbb` to
materialize the carry flag. `native-over` also replaces the earlier
fallback with a standalone native body (`forth-bootstrap/cc/020-cc-arena.fth:234`):

```forth file=cc/020-cc-arena.fth
\ 010-lib.fth's character tests subtract and divide; as x86 they are an
\ unsigned compare: sub rdi, low; cmp rdi, count; sbb rdi, rdi (-1 below).
: in-range,  ( low count -- )
  [lit] 72 c, [lit] 131 c, [lit] 239 c, swap c,                  \ sub rdi, low
  [lit] 72 c, [lit] 131 c, [lit] 255 c, c,                       \ cmp rdi, count
  [lit] 72 c, [lit] 25 c, [lit] 255 c, ret, ;                    \ sbb rdi, rdi
' digit? code: digit?  here code-start !  [lit] 48 [lit] 10 in-range,  code-start @ native!
' alpha-lower? code: alpha-lower?  here code-start !  [lit] 97 [lit] 26 in-range,  code-start @ native!
' alpha-upper? code: alpha-upper?  here code-start !  [lit] 65 [lit] 26 in-range,  code-start @ native!
\ The rest of 010-lib.fth's hot words, compiled again from the same text
\ so the copies above take effect, and the old bodies sent to the new ones.
' over code: over  here code-start !
  push-tos, [lit] 72 c, [lit] 139 c, [lit] 125 c, [lit] 8 c, ret,  code-start @ native!
' over constant native-over
: over  compiling? if, push-tos, [lit] 72 c, [lit] 139 c, [lit] 125 c, [lit] 8 c,
  else, native-over execute then, ; immediate
```

## Recompiling library clients of the new emitters

Existing compound words need fresh bodies to benefit from inline emission.
The definitions of `alpha?`, `space?`, `true`, the derived comparisons,
`nip`, `rot`, `2dup`, `2drop`, `+!` and `-!` keep their established contracts;
each saved old address is redirected after recompilation (`forth-bootstrap/cc/020-cc-arena.fth:250`):

```forth file=cc/020-cc-arena.fth
' alpha? : alpha?  dup alpha-lower? swap alpha-upper? or ;  ' alpha? native!
' space? : space?  dup [lit] 32 - 0= over [lit]  9 - 0= or
          over [lit] 10 - 0= or  swap [lit] 13 - 0= or ;  ' space? native!
' true : true  [lit] 0 0= ;  ' true native!
' <> : <>  = 0= ;  ' <> native!
' > : >   swap < ;  ' > native!
' <= : <=  > 0= ;  ' <= native!
' >= : >=  < 0= ;  ' >= native!
' nip : nip   swap drop ;  ' nip native!
' rot : rot   >r swap r> swap ;  ' rot native!
' 2dup : 2dup  over over ;  ' 2dup native!
' 2drop : 2drop drop drop ;  ' 2drop native!
' +! : +!  swap over @ + swap ! ;  ' +! native!
' -! : -!  swap over @ swap - swap ! ;  ' -! native!
```

`bytes-eq` is recompiled for the same reason. Its early mismatch path and
empty-range path remain intact; `native!` makes earlier callers reach the
new body too (`forth-bootstrap/cc/020-cc-arena.fth:264`):

```forth file=cc/020-cc-arena.fth
' bytes-eq : bytes-eq
  begin,
    dup [lit] 0 >
  while,
    >r
    over c@ over c@ <> if,
      r> drop 2drop [lit] 0 exit,
    then,
    1+ swap 1+ swap
    r> 1-
  repeat,
  drop 2drop true ;  ' bytes-eq native!

```

## Comparison emitters and immediate data words

`pop-sub,` supplies the common subtraction, and `flag-al,` converts a
byte-sized condition result into the Forth flag. `native-=`, `forth-<>`,
`native-<` and `forth->=` retain the corresponding fallback bodies (`forth-bootstrap/cc/020-cc-arena.fth:277`):

```forth file=cc/020-cc-arena.fth
\ Comparisons copied in place (same answers as 010-lib.fth's).
: pop-sub,  mov-rax-[rbp], add-rbp-8, sub-rax-rdi, ;          \ rax = a - b
: flag-al,  [lit] 72 c, [lit] 15 c, [lit] 182 c, [lit] 248 c, \ movzx rdi, al
            [lit] 72 c, [lit] 247 c, [lit] 223 c, ;           \ neg rdi
' = constant native-=
: =   compiling? if, pop-sub, [lit] 15 c, [lit] 148 c, [lit] 192 c, flag-al,  \ sete al
  else, native-= execute then, ; immediate
' <> constant forth-<>
: <>  compiling? if, pop-sub, [lit] 15 c, [lit] 149 c, [lit] 192 c, flag-al,  \ setne al
  else, forth-<> execute then, ; immediate
' < constant native-<
: <   compiling? if, pop-sub, [lit] 248 sar63, mov-rdi-rax,
  else, native-< execute then, ; immediate
' >= constant forth->=
: >=  compiling? if, pop-sub, [lit] 248 sar63,
    [lit] 72 c, [lit] 247 c, [lit] 208 c, mov-rdi-rax,        \ not rax
  else, forth->= execute then, ; immediate
```

Reversing the subtraction avoids emitting a separate swap for `>` and
`<=`. `pop-rsub,` leaves that result in `rdi`; `forth->`, `forth-<=` and
`native-0<` complete the fallback set (`forth-bootstrap/cc/020-cc-arena.fth:294`):

```forth file=cc/020-cc-arena.fth
: pop-rsub,  mov-rax-[rbp], add-rbp-8,
             [lit] 72 c, [lit] 41 c, [lit] 199 c, ;           \ sub rdi, rax: b - a
' > constant forth->
: >   compiling? if, pop-rsub, [lit] 255 sar63,
  else, forth-> execute then, ; immediate
' <= constant forth-<=
: <=  compiling? if, pop-rsub, [lit] 255 sar63,
    [lit] 72 c, [lit] 247 c, [lit] 215 c,                     \ not rdi
  else, forth-<= execute then, ; immediate
' 0< constant native-0<
: 0<  compiling? if, [lit] 255 sar63, else, native-0< execute then, ; immediate
```

A constant or data address can also be embedded directly in its caller.
`push-or-compile` leaves its value alone during interpretation and emits
it during compilation. `poc-xt` lets the defining words append a call to
that decision (`forth-bootstrap/cc/020-cc-arena.fth:305`):

```forth file=cc/020-cc-arena.fth
\ Constants and variables: a word made by constant, create or variable from
\ here on is immediate.  Compiling, it lays an inline push of its value
\ rather than a CALL; interpreted, it pushes the value as before.  Its body
\ is the 18-byte push, a CALL to push-or-compile, then ret (24 bytes).
: push-or-compile  ( v -- v | )  compiling? if, push-imm64, then, ;
' push-or-compile constant poc-xt
: constant  : push-imm64, poc-xt call, ret, [lit] 0 state ! immediate ;
: create  : here [lit] 24 + push-imm64, poc-xt call, ret, [lit] 0 state ! immediate ;
: variable  create [lit] 0 , ;

```

The new `constant`, `create` and `variable` make immediate words. A
created word's data begins after its push, call and return, so the address
calculation must use this new body size. `variable` still supplies an
initialized cell after that body.

## Indexing the growing Forth dictionary

A separate hash index narrows Forth name lookup to a bucket.
`fh-buckets` addresses the bucket array, `fh-pool` the node area,
`fh-pos` its used length and `fh-latest` the last indexed header.
`fh-a` and `fh-u` retain the current query; `fh-hash` selects its bucket
(`forth-bootstrap/cc/020-cc-arena.fth:315`):

```forth file=cc/020-cc-arena.fth
\ The seed's find walks every header from LATEST, and about a third of each
\ run went there while the compiler's own source was read.  fh-find answers
\ the same (the newest entry of that name, its header left in LAST_FOUND)
\ from a hash table it brings up to date first: headers are only ever added
\ at LATEST, so the ones newer than the last indexed are new.  Nodes
\ { next, header } live in a 2 MiB anonymous mapping, after 4096 buckets.
variable fh-buckets
variable fh-pool
variable fh-pos
variable fh-latest
variable fh-a
variable fh-u
[lit] 0 [lit] 2097152 [lit] 3 [lit] 34 true [lit] 0 [lit] 9 syscall6
dup fh-buckets !  [lit] 32768 + fh-pool !
: fh-hash  ( a u -- bucket )
  [lit] 5381 >r
  begin, dup while,
    over c@ r> [lit] 33 * + >r
    1- swap 1+ swap
  repeat, 2drop
  r> [lit] 4095 and ;
```

The hash starts at 5381 and updates by multiplying by 33 and adding the
next byte. Masking the result selects a bucket. The initial mapping call
has no failure check here, and the node pool has no capacity guard; these
are limits of this implementation, not guarantees supplied by `cc-alloc`.

Inserting a node at the bucket head makes insertion order significant.
`fh-insert` stores the previous head and the dictionary header in the node.
`fh-index` recurses to the last indexed header before inserting on return,
so the newer headers finish nearer the head (`forth-bootstrap/cc/020-cc-arena.fth:336`):

```forth file=cc/020-cc-arena.fth
: fh-insert  ( header -- )
  dup [lit] 10 + over [lit] 9 + c@ fh-hash [lit] 8 * fh-buckets @ +
  fh-pool @ fh-pos @ +
  over @ over !
  rot over [lit] 8 + !
  swap !
  [lit] 16 fh-pos +! ;
: fh-index  ( header -- )  \ every header newer than fh-latest, oldest first
  dup fh-latest @ = over 0= or if, drop exit, then,
  dup @ fh-index fh-insert ;
```

`fh-find` refreshes that index before searching. A matching length and
byte range yield the execution token, and the matching header is stored
in LAST_FOUND so the seed can still inspect its flags. Exhausting the
chain leaves zero (`forth-bootstrap/cc/020-cc-arena.fth:346`):

```forth file=cc/020-cc-arena.fth
: fh-find  ( c-addr u -- xt | 0 )
  fh-u ! fh-a !
  latest @ fh-latest @ <> if, latest @ fh-index  latest @ fh-latest ! then,
  fh-a @ fh-u @ fh-hash [lit] 8 * fh-buckets @ + @
  begin, dup while,
    dup [lit] 8 + @
    dup [lit] 9 + c@ fh-u @ = if,
      dup [lit] 10 + fh-a @ fh-u @ bytes-eq if,
        nip dup latest [lit] 16 + !                    \ LAST_FOUND
        [lit] 10 + fh-u @ + exit,
      then,
    then,
    drop @
  repeat, ;
' find ' fh-find native!

```

The final patch redirects the original `find`. This index accelerates
Forth dictionary lookup while the compiler is loaded; it is separate from
the compiler's C name tables introduced below.

## The lexer's state block

Look-ahead must restore the current token as well as the character cursor.
`cc-lex-state-size` bounds a contiguous `cc-lex-state` block whose field
names are addresses, so existing fetch and store words can access them (`forth-bootstrap/cc/020-cc-arena.fth:362`):

```forth file=cc/020-cc-arena.fth
\ ----- The lexer's state: one block -----
\ Everything the source reader (030) and the lexer (050) change as they move
\ through the program lives in this one 8-cell block, so a parser that wants
\ to look ahead can copy the block away and later copy it back
\ (cc-lex-mark / cc-lex-reset, 050).  Each name below is the address of its
\ cell, used exactly like a variable.  The block comes first because cc-die
\ reports the current line from it.
[lit] 64 constant cc-lex-state-size
create cc-lex-state  cc-lex-state-size allot
cc-lex-state             constant cc-src-pos     \ reader: offset of the next byte
cc-lex-state [lit]  8 +  constant cc-src-line    \ reader: 1-based line number
cc-lex-state [lit] 16 +  constant tok-kind       \ lexer: tk-* of the current token
cc-lex-state [lit] 24 +  constant tok-num        \ lexer: number / char / punct code
cc-lex-state [lit] 32 +  constant tok-str-addr   \ lexer: identifier or string bytes
cc-lex-state [lit] 40 +  constant tok-str-len    \ lexer: ... and their length
cc-lex-state [lit] 48 +  constant tok-kw-id      \ lexer: kw-* when tok-kind = tk-kw
cc-lex-state [lit] 56 +  constant cc-tok-pending \ lexer: -1 = current token put back

```

| Field | Role |
|---|---|
| `cc-src-pos` | Offset of the next source byte |
| `cc-src-line` | Current source line |
| `tok-kind` | Current token category |
| `tok-num` | Numeric, character or punctuation value |
| `tok-str-addr` | Address of token text |
| `tok-str-len` | Length of token text |
| `tok-kw-id` | Keyword identity |
| `cc-tok-pending` | Whether the current token has been put back |

Copying this block preserves the moving reader and token state together.
The source bytes stay in their own buffer, so a saved text address remains
meaningful. Chapter 29 builds the mark/reset operations and token meanings;
this layout only reserves their state. The line cell also gives failures
a location before the lexer is present.

## Failing: `cc-die`

Diagnostics must go to stderr without consuming the output buffer.
`cc-err-write` selects that descriptor; `cc-err-dec` fills `cc-err-digits`
backwards as it extracts decimal digits, then writes only the filled tail (`forth-bootstrap/cc/020-cc-arena.fth:380`):

```forth file=cc/020-cc-arena.fth
\ ----- Failing: cc-die -----
\ cc-err-write ( a u -- )  Write u bytes at a to stderr (fd 2).
: cc-err-write  >r >r [lit] 2 r> r> write drop ;

\ cc-err-dec ( u -- )  Write u in decimal to stderr.  Digits come out lowest
\ first, so they fill cc-err-digits from its end backwards.
create cc-err-digits  [lit] 20 allot             \ 2^64 has 20 digits
: cc-err-dec
  cc-err-digits [lit] 20 +                       ( u p )
  begin,
    1-  over [lit] 10 / [lit] 10 * >r  over r> - ( u p digit )
    [char] 0 +  over c!                          ( u p )
    swap [lit] 10 / swap                         ( u/10 p )
    over 0=
  until,
  nip  cc-err-digits [lit] 20 + over -  cc-err-write ;

```

The loop executes before testing whether the quotient is exhausted, so a
zero value still contributes a digit. The scratch area belongs to the
printer and does not allocate from the arena.

`cc-die-where`, `cc-die-what` and `cc-die-end` hold the location prefix,
error separator and newline. `cc-die` combines them with the current line
and the caller's code, then exits with that same code. `cc-check-cap`
connects the existing prospective-size guard to this diagnostic (`forth-bootstrap/cc/020-cc-arena.fth:397`):

```forth file=cc/020-cc-arena.fth
create cc-die-where  s, cc: bl c, s, line bl c,       \ "cc: line "  9 bytes
create cc-die-what   char : c, bl c, s, error bl c,   \ ": error "   8 bytes
create cc-die-end    nl c,                            \ "\n"         1 byte

\ cc-die ( code -- )  Every compiler failure ends here: write
\ "cc: line N: error CODE" to stderr and exit with status CODE.  N is the
\ reader's line in the preprocessed source, where #include'd files are
\ already spliced in (Appendix G).
: cc-die
  cc-die-where [lit] 9 cc-err-write
  cc-src-line @ cc-err-dec
  cc-die-what [lit] 8 cc-err-write
  dup cc-err-dec
  cc-die-end [lit] 1 cc-err-write
  die ;

\ cc-check-cap ( n cap code -- )  Die with code unless n <= cap.  n is how
\ full a buffer or table will be once the write about to happen is done.
: cc-check-cap
  >r > if, r> cc-die then,
  r> drop ;

```

The error-code convention keeps failure selection with the caller and
formatting with `cc-die`. In these files, allocation uses code 10, raw
input uses 20, output capacity uses 21 and output open failure uses 22.
`cc-check-cap` accepts equality with the limit and consumes its arguments
on success. It does not initialize the line cell: the input initializer
does that. After preprocessing, the location refers to the flattened
source, not an original include-file location.

## The arena

Records that survive until compilation ends can share a region with a
single moving allocation pointer. `cc-arena-cap` and `cc-arena-base`
describe the default slab; `cc-arena-start` and `cc-arena-limit` select
the active region, and `cc-arena-ptr` marks its unused tail (`forth-bootstrap/cc/020-cc-arena.fth:419`):

```forth file=cc/020-cc-arena.fth
\ ----- Storage -----
\ The buffer lives in the dictionary alongside the cc-arena-base header (it's
\ what `create` builds: a header + data area; allot extends the data area).
\ Sized to fit within 000-seed.hex0's mapped segment with room for the compiler
\ dictionary, struct descriptors, labels, and string overflow.
[lit] 32768 constant cc-arena-cap
create cc-arena-base  cc-arena-cap allot
variable cc-arena-ptr
\ Initialize the bump pointer to the base of the buffer.
cc-arena-base cc-arena-ptr !
variable cc-arena-start
variable cc-arena-limit
cc-arena-base cc-arena-start !
cc-arena-cap cc-arena-limit !
\ Opt-in workspace for larger translation units; the seed itself is unchanged.
: cc-arena-map ( bytes -- )
  dup cc-arena-limit !
  [lit] 0 swap [lit] 3 [lit] 34 true [lit] 0 [lit] 9 syscall6
  dup 0< if, [lit] 10 cc-die then,
  dup cc-arena-start ! cc-arena-ptr ! ;

```

`cc-arena-map` installs an anonymous read/write mapping as the active
region and resets the pointer to its start. A negative mapping result
uses the allocation error code. The word does not copy old records, free
a previous mapping or validate the requested size before the syscall;
selecting storage belongs before allocating records into it.

`cc-alloc` rounds the requested length, saves the old pointer as its answer,
and checks the proposed new pointer against the active region before
committing it (`forth-bootstrap/cc/020-cc-arena.fth:440`):

```forth file=cc/020-cc-arena.fth
\ ----- cc-alloc -----
\ cc-alloc ( n -- addr )  Bump n bytes (rounded up to an 8-byte boundary)
\ off the arena and return the start address of the allocation.  On exhaustion
\ the compiler dies with code 10.
\
\ Stack trace:
\   ( n )
\   align up to 8:  (n+7)/8*8
\   ( n' )
\   cc-arena-ptr @ swap over +     ( old-top new-top )
\   dup cc-arena-start @ -         ( old-top new-top used )
\   cc-arena-limit @ 10 cc-check-cap  ( old-top new-top )
\   cc-arena-ptr !                 ( old-top )
: cc-alloc                                       ( n -- addr )
  [lit] 7 + [lit] 8 / [lit] 8 *                  \ align up to 8 bytes
  cc-arena-ptr @ swap over +                     ( old-top new-top )
  dup cc-arena-start @ -  cc-arena-limit @ [lit] 10 cc-check-cap
  cc-arena-ptr ! ;                               ( -- old-top )
```

For the checkpoint's initial request of 16 bytes, let the old pointer be
`p`. Rounding leaves that length unchanged, the prospective pointer is
`p + 16`, and the checked usage is `p + 16 - cc-arena-start @`. Success
stores `p + 16` but returns `p`; the following allocation starts at that
stored pointer.

This is an *arena*: allocation advances a pointer and there is no
individual release operation. Records remain available as long as the
region does. Chapter 30 uses this facility for type records, Chapter 32
for call fixups and Chapter 36 for control-flow records.

The rounded length is a multiple of 8; that preserves the base address's
alignment rather than independently aligning the returned address. A
zero-length request can return the current pointer without advancing it.
Callers must supply valid nonnegative sizes whose rounding and pointer
arithmetic do not overflow. The comment's stack trace names the default
base and capacity, but the executable definition checks the selected
`cc-arena-start` and `cc-arena-limit`.

## The input and source buffers and the reader

Raw text, preprocessed text and emitted bytes have different lifetimes and
writers. The I/O file states that separation before declaring storage (`forth-bootstrap/cc/030-cc-io.fth:1`):

```forth file=cc/030-cc-io.fth
\ 030-cc-io.fth — Input and source buffers, output-buffer emitter, file I/O
\ wrappers, and a few helpers shared by the preprocessor, lexer and symbol
\ table.  Loaded after 010-lib.fth and 020-cc-arena.fth.
\
\ Four responsibilities:
\   A. Slurp stdin into the 1 MiB cc-in-buf.  The preprocessor (040) turns
\      it into the 2 MiB cc-src-buf, which the lexer walks via peek/next.
\   B. Accumulate the output ELF into cc-out-buf via emit-byte / 4le / 8le
\      with patch-byte / patch-4le for back-fixups.
\   C. Write cc-out-buf to a path via 010-lib.fth's open/write/close.
\   D. Shared helpers: identifier classifiers, cell[], cc-name-find.
\
\ Depends on 010-lib.fth: constant, variable, create, allot, [lit], if,/then,/else,,
\   begin,/while,/repeat,, exit,, +, -, /, =, >, >=, 0=, 0<, +!, !, @, c!, c@,
\   drop, dup, over, swap, >r, r@, r>, read, write, open, close, bytes-eq;
\   020-cc-arena.fth: cc-src-pos, cc-src-line, cc-die, cc-check-cap.

```

Large dictionary allocations must clear the VM's reserved pages.
`skip-vm-pages` precedes the raw buffer. `cc-in-default-cap` sizes
`cc-in-default-buf`; `cc-in-buffer` and `cc-in-limit` select its current
address and capacity, exposed by `cc-in-buf` and `cc-in-cap`.
`cc-in-len` records the valid byte count (`forth-bootstrap/cc/030-cc-io.fth:18`):

```forth file=cc/030-cc-io.fth
\ ===========================================================================
\ A. Input buffer, source buffer + reader
\ ===========================================================================

\ Skip past the VM's fixed pages (data stack 0x410000..0x411000, I/O scratch
\ 0x412000, token buffer 0x412800, sysvars 0x413000..0x414000) so the
\ megabyte buffers do not overlap runtime VM state.  At 030-cc-io.fth load
\ time HERE is well below 0x410000, so this is a forward bump to 0x414000.
skip-vm-pages                                     \ HERE = 0x414000

\ cc-in-buf holds stdin exactly as read; nothing but the preprocessor reads it.
[lit] 1048576 constant cc-in-default-cap
create cc-in-default-buf cc-in-default-cap allot
variable cc-in-buffer
variable cc-in-limit
cc-in-default-buf cc-in-buffer !
cc-in-default-cap cc-in-limit !
: cc-in-buf ( -- address ) cc-in-buffer @ ;
: cc-in-cap ( -- bytes ) cc-in-limit @ ;
variable cc-in-len

```

Preprocessing needs an independent destination because expansion can
outgrow the input. `cc-src-default-cap` sizes `cc-src-default-buf`, while
`cc-src-buffer` and `cc-src-limit` feed the public `cc-src-buf` and
`cc-src-cap` accessors. `cc-src-len` bounds valid text; `cc-src-init`
empties it and resets the reader's position and line (`forth-bootstrap/cc/030-cc-io.fth:39`):

```forth file=cc/030-cc-io.fth
\ cc-src-buf holds the preprocessed source the lexer reads: #include'd files
\ spliced in, directives blanked. The default is twice the raw capacity;
\ direct GCC selects separately measured limits. The reader's cursor is in the lexer's
\ state block (020-cc-arena.fth).
[lit] 2097152 constant cc-src-default-cap
create cc-src-default-buf cc-src-default-cap allot
variable cc-src-buffer
variable cc-src-limit
cc-src-default-buf cc-src-buffer !
cc-src-default-cap cc-src-limit !
: cc-src-buf ( -- address ) cc-src-buffer @ ;
: cc-src-cap ( -- bytes ) cc-src-limit @ ;
variable cc-src-len

\ cc-src-init ( -- )  Empty the source buffer and rewind the reader.
: cc-src-init
  [lit] 0 cc-src-len !
  [lit] 0 cc-src-pos !
  [lit] 1 cc-src-line ! ;

```

Chapter 28 supplies the transformation from `cc-in-buf` to `cc-src-buf`.
Keeping both buffers alive lets that transformation retain slices of raw
text while it appends expanded text elsewhere.

## Reading to a bounded end

`cc-read-all` accepts a descriptor, destination, capacity and failure code.
The `cc-ra-fd`, `cc-ra-buf`, `cc-ra-cap` and `cc-ra-code` cells retain those
arguments; `cc-ra-n` accumulates the length. Stdin first receives the
pending `key-drain` bytes before the ordinary read loop starts (`forth-bootstrap/cc/030-cc-io.fth:59`):

```forth file=cc/030-cc-io.fth
\ cc-read-all ( fd buf cap code -- n )  Read fd to end of file into buf and
\ return the byte count.  Each read asks for all the room left.  A buffer
\ that fills up dies with code: a full buffer and a longer file look the
\ same, so the data must leave at least one byte of buf unused.
variable cc-ra-fd
variable cc-ra-buf
variable cc-ra-cap
variable cc-ra-code
variable cc-ra-n
: cc-read-all
  cc-ra-code ! cc-ra-cap ! cc-ra-buf ! cc-ra-fd !
  [lit] 0 cc-ra-n !
  cc-ra-fd @ 0= if,                    \ stdin: first what key-fill holds (020)
    cc-ra-buf @ cc-ra-cap @ key-drain cc-ra-n !
    cc-ra-n @ 1+ cc-ra-cap @ cc-ra-code @ cc-check-cap
  then,
  begin,
    cc-ra-fd @  cc-ra-buf @ cc-ra-n @ +  cc-ra-cap @ cc-ra-n @ -  read
    dup [lit] 0 >
  while,
    cc-ra-n +!
    cc-ra-n @ 1+ cc-ra-cap @ cc-ra-code @ cc-check-cap   \ full: die
  repeat,
  drop cc-ra-n @ ;

```

Each read requests the remaining space. A positive result extends the
length; checking the length plus one reserves room to distinguish a full
buffer from end-of-file. Thus an input exactly filling the capacity is
rejected. A nonpositive result ends the loop: this implementation treats
a negative read error like EOF rather than diagnosing it separately.

`cc-load-stdin` resets the source reader before loading raw input, so an
input-capacity failure has an initialized line. `cc-eof?` compares the
source position with its length; `cc-peek-char` uses that verdict to avoid
reading outside valid source text (`forth-bootstrap/cc/030-cc-io.fth:84`):

```forth file=cc/030-cc-io.fth
\ cc-load-stdin ( -- )  Read all of fd 0 into cc-in-buf; die 20 if it fills.
\ Rewinds the reader first, so an error here reports line 1.
: cc-load-stdin
  cc-src-init
  [lit] 0 cc-in-buf cc-in-cap [lit] 20 cc-read-all  cc-in-len ! ;

\ cc-eof? ( -- f )  -1 if pos has reached len; 0 otherwise.
: cc-eof?  cc-src-pos @ cc-src-len @ >= ;

\ cc-peek-char ( -- c )  Returns byte at the current position; 0 at EOF.
\ Both arms of if,/else, produce exactly one value, so stack stays balanced.
: cc-peek-char
  cc-eof? if,
    [lit] 0
  else,
    cc-src-buf cc-src-pos @ + c@
  then, ;
```

Consuming a byte belongs in `cc-next-char`, which adds newline accounting
to `cc-peek-char` for the lexer in Chapter 29
(`forth-bootstrap/cc/030-cc-io.fth:101`):

```forth file=cc/030-cc-io.fth

\ cc-next-char ( -- c )  Returns current byte and advances pos.
\ Tracks line number when consuming '\n' (10).
: cc-next-char
  cc-peek-char
  [lit] 1 cc-src-pos +!
  dup nl = if,
    [lit] 1 cc-src-line +!
  then, ;

```

`cc-next-char` advances the position even when peek returned the EOF
sentinel. Callers that need to stop at the end must test `cc-eof?`;
repeated calls do not pin the cursor at the length.

## The output buffer

Emission needs its own active address, capacity and cursor.
`cc-out-default-cap` sizes `cc-out-default-buf`; `cc-out-buffer` and
`cc-out-limit` feed `cc-out-buf` and `cc-out-cap`. `cc-out-pos` is the
append offset, and `cc-out-init` resets it without clearing the storage
(`forth-bootstrap/cc/030-cc-io.fth:111`):

```forth file=cc/030-cc-io.fth
\ ===========================================================================
\ B. Output buffer + ELF-aware emit helpers
\ ===========================================================================

\ 1 MiB output cap — fits any reasonable ELF the C-subset compiler emits.
[lit] 1048576 constant cc-out-default-cap
create cc-out-default-buf cc-out-default-cap allot
variable cc-out-buffer
variable cc-out-limit
cc-out-default-buf cc-out-buffer !
cc-out-default-cap cc-out-limit !
: cc-out-buf ( -- address ) cc-out-buffer @ ;
: cc-out-cap ( -- bytes ) cc-out-limit @ ;
variable cc-out-pos

\ cc-out-init ( -- )
: cc-out-init  [lit] 0 cc-out-pos ! ;

```

Appending through `cc-emit-byte` checks the prospective position before
writing. `cc-emit-4le` and `cc-emit-8le` direct the established low-byte
emission sequence into this buffer instead of the Forth dictionary (`forth-bootstrap/cc/030-cc-io.fth:129`):

```forth file=cc/030-cc-io.fth
\ cc-emit-byte ( b -- )  Append a byte at cc-out-buf[cc-out-pos++]; die 21
\ if the buffer is full.
: cc-emit-byte
  cc-out-pos @ 1+ cc-out-cap [lit] 21 cc-check-cap
  cc-out-buf cc-out-pos @ + c!
  [lit] 1 cc-out-pos +! ;

\ cc-emit-4le ( v -- )  Emit low 4 bytes of v in little-endian.
: cc-emit-4le
  dup cc-emit-byte                              \ byte 0
  [lit] 256 / dup cc-emit-byte                  \ byte 1
  [lit] 256 / dup cc-emit-byte                  \ byte 2
  [lit] 256 / cc-emit-byte ;                    \ byte 3

\ cc-emit-8le ( v -- )  Emit all 8 bytes of v in little-endian.
\ Reuses cc-emit-4le for both halves; shifts by 32 between halves.
: cc-emit-8le
  dup cc-emit-4le                                              \ low 4 bytes
  [lit] 256 / [lit] 256 / [lit] 256 / [lit] 256 /              \ shift right 32
  cc-emit-4le ;                                                \ high 4 bytes

```

Capacity is checked per byte. If a multi-byte append runs out of room,
the earlier bytes of that value have already been stored, but the process
exits instead of returning a partially successful append.

## Back-patching output offsets

An unresolved output field needs an offset that remains valid while the
buffer grows. `cc-out-patch-byte` writes at that offset without advancing
`cc-out-pos`; `cc-out-patch-4le` keeps the starting offset while placing
the successive bytes (`forth-bootstrap/cc/030-cc-io.fth:150`):

```forth file=cc/030-cc-io.fth
\ cc-out-patch-byte ( v offset -- )  Overwrite cc-out-buf[offset] with low byte of v.
: cc-out-patch-byte  cc-out-buf + c! ;

\ cc-out-patch-4le ( v offset -- )  Overwrite 4 bytes at offset (LE).
\ Stash offset on the return stack so we can compute offset+1, +2, +3.
: cc-out-patch-4le
  >r                                                  ( v       ; R: offset )
  dup r@                       cc-out-patch-byte      ( v       ; R: offset )
  [lit] 256 / dup r@ 1+ cc-out-patch-byte             ( v>>8    ; R: offset )
  [lit] 256 / dup r@ [lit] 2 + cc-out-patch-byte      ( v>>16   ; R: offset )
  [lit] 256 /     r> [lit] 3 + cc-out-patch-byte ;    ( v>>24>>8 popped )

```

`cc-out-patch-8le` extends the same operation to a full cell, consuming the
saved offset on its final byte store (`forth-bootstrap/cc/030-cc-io.fth:162`):

```forth file=cc/030-cc-io.fth
\ cc-out-patch-8le ( v offset -- )  Overwrite 8 bytes at offset (LE).
: cc-out-patch-8le
  >r                                                  ( v       ; R: offset )
  dup r@                       cc-out-patch-byte      ( v       ; R: offset )
  [lit] 256 / dup r@ 1+ cc-out-patch-byte
  [lit] 256 / dup r@ [lit] 2 + cc-out-patch-byte
  [lit] 256 / dup r@ [lit] 3 + cc-out-patch-byte
  [lit] 256 / dup r@ [lit] 4 + cc-out-patch-byte
  [lit] 256 / dup r@ [lit] 5 + cc-out-patch-byte
  [lit] 256 / dup r@ [lit] 6 + cc-out-patch-byte
  [lit] 256 /     r> [lit] 7 + cc-out-patch-byte ;

```

These patchers neither reserve bytes nor check bounds. Their caller must
have emitted the field already and must supply an offset covering a valid
range. Chapter 31 uses this interface for executable fields; Chapter 32
extends its use to call and global fixups. Output back-patching here addresses
output-buffer offsets, independent of dictionary HERE.

## Writing the file

A completed output prefix can be written through `cc-write-output`.
The caller supplies a NUL-terminated path; the wrapper opens with create
and truncate flags, rejects a negative descriptor, writes the used prefix
and closes the descriptor (`forth-bootstrap/cc/030-cc-io.fth:174`):

```forth file=cc/030-cc-io.fth
\ ===========================================================================
\ C. Output file write
\ ===========================================================================
\ Open flags (Linux x86-64 asm-generic):
\   O_WRONLY=1, O_CREAT=64, O_TRUNC=512  →  bitwise OR = 577.
\ Mode 0o755 = decimal 493.
\
\ 010-lib.fth's `open` already takes ( path flags mode -- fd ) — its signature
\ matches what we need, so no open3 wrapper is required here.

\ cc-write-output ( path-addr -- )  path-addr must point at NUL-terminated bytes.
\ Opens path with O_WRONLY|O_CREAT|O_TRUNC, mode 0755; writes
\ cc-out-buf[0..cc-out-pos@] to it; closes.  On open failure (fd < 0),
\ dies with code 22.
: cc-write-output
  [lit] 577 [lit] 493 open                        ( fd )
  dup 0< if,
    drop
    [lit] 22 cc-die
  then,
  >r                                              ( ; R: fd )
  r@ cc-out-buf cc-out-pos @ write drop           \ write all bytes
  r> close drop ;

```

The wrapper discards both the write result and the close result. It does
not retry a short write or report those errors, so a successful open alone
does not establish that the whole file reached disk. Chapter 38 connects
this operation to the compiler entry point.

## Shared helpers for C names

Identifier spelling and table addressing recur across compiler layers.
`ident-start?` accepts a letter or underscore; `ident-cont?` also accepts a
digit. `cell[]` converts an entry index and an array base into the address
of the corresponding cell (`forth-bootstrap/cc/030-cc-io.fth:198`):

```forth file=cc/030-cc-io.fth
\ ===========================================================================
\ D. Helpers shared by the preprocessor, lexer and symbol table
\ ===========================================================================

\ ident-start? ( c -- f )  letter or '_'.
: ident-start?
  dup alpha?  swap [char] _ = or ;

\ ident-cont? ( c -- f )  ident-start? or digit.
: ident-cont?
  dup ident-start?  swap digit? or ;

\ cell[] ( i arr -- addr )  Address of cell i of an array of 8-byte cells —
\ how every parallel-array table (macros, symbols, ...) is indexed.
: cell[]  swap [lit] 8 * + ;

```

`cc-name-find` applies newest-first slice lookup to parallel address and
length arrays. `cc-nf-a` and `cc-nf-u` retain the query;
`cc-nf-addrs` and `cc-nf-lens` retain the arrays while the entry index
counts down (`forth-bootstrap/cc/030-cc-io.fth:214`):

```forth file=cc/030-cc-io.fth
\ cc-name-find ( a u addrs lens count -- i | -1 )  Look the name a u up in
\ a table kept as two parallel arrays, addrs (where each name's bytes are)
\ and lens (how many), of count entries.  Walks from the newest entry to the
\ oldest and returns the first match, so a later entry hides an earlier one
\ of the same name.  The loop index runs down to -1, so "not found" is
\ simply the final index.  The needle waits in globals so the loop body can
\ reach it without deep stack juggling.
variable cc-nf-a
variable cc-nf-u
variable cc-nf-addrs
variable cc-nf-lens
: cc-name-find
  >r  cc-nf-lens ! cc-nf-addrs ! cc-nf-u ! cc-nf-a !
  r> 1-                                          ( i = count-1 )
  begin,
    dup 0< 0=
  while,
    dup cc-nf-lens @ cell[] @  cc-nf-u @ = if,   \ same length?
      dup cc-nf-addrs @ cell[] @  cc-nf-a @  cc-nf-u @
      bytes-eq if, exit, then,                   \ found: return i
    then,
    1-                                           \ i--
  repeat, ;                                      \ not found: i = -1

```

A match returns the index directly from the loop. Falling past the first
entry leaves -1, including when the count was initially zero. The scratch
cells make this a non-reentrant helper. The caller owns both arrays and
the name bytes they reference.

Larger tables can use `cc-name-hash` to restrict comparisons to a bucket.
It uses the same hash recurrence as `fh-hash`, with `cc-name-buckets`
setting the mask (`forth-bootstrap/cc/030-cc-io.fth:238`):

```forth file=cc/030-cc-io.fth
\ cc-name-hash ( a u -- h )  djb2 over the name, as the linker hashes
\ symbols (140-cc-link.fth), masked to cc-name-buckets.  The macro and
\ symbol tables (040, 070) keep, per hash, their newest entry in a bucket
\ and link the older ones behind it, so a lookup compares only the names
\ that share its hash.
[lit] 4096 constant cc-name-buckets
: cc-name-hash
  [lit] 5381 >r
  begin, dup while,
    over c@ r> [lit] 33 * + >r
    1- swap 1+ swap
  repeat, 2drop
  r> cc-name-buckets 1- and ;

```

Equal hashes do not establish equal names; a bucket still needs length
and byte comparisons. Chapters 28 and 30 build the macro and symbol table
users. Chapter 29 consumes the identifier classifiers. This file supplies
helpers, not those tables' insertion and scope rules.

## Selecting a larger workspace

The public buffer accessors allow a different storage profile without
changing the reader and emitter interfaces. `cc-in-direct-cap`,
`cc-src-direct-cap` and `cc-out-direct-cap` bound the alternate slices;
`cc-io-direct-base` caches the mapping address (`forth-bootstrap/cc/030-cc-io.fth:252`):

```forth file=cc/030-cc-io.fth
\ Direct GCC source workspace is opt-in; default buffers stay dictionary-backed.
\ Measured raw/expanded/output maxima are 2,782,995/5,415,887/3,901,856 bytes.
\ Raw and output round to whole MiB. Expanded text splices in every included
\ byte, so it and the direct include pool (040) share one bound: the measured
\ maximum (binutils i386-opc.c) plus 25%, rounded up to whole MiB. 3/7/4 MiB.
[lit] 3145728 constant cc-in-direct-cap
[lit] 7340032 constant cc-src-direct-cap
[lit] 4194304 constant cc-out-direct-cap
variable cc-io-direct-base

```

The historical size measurements in the comment were not rerun for this
chapter. The constants specify a fixed profile, not automatic growth in
response to input.

`cc-workspace-round` rejects invalid sizes before rounding to page units.
`cc-workspace-syscall` requests anonymous read/write storage through
`cc-workspace-syscall-fwd`, whose deferred target can be substituted.
`cc-workspace-map` rejects a nonpositive result using the caller's code
(`forth-bootstrap/cc/030-cc-io.fth:262`):

```forth file=cc/030-cc-io.fth
\ Round before mmap only after rejecting zero, negative and overflowing sizes.
\ Requests are policy constants at callers; this helper never grows a buffer.
: cc-workspace-round ( bytes code -- page-bytes )
  >r dup [lit] 0 <= if, r@ cc-die then,
  dup [lit] 9223372036854771712 > if, r@ cc-die then,
  [lit] 4095 + [lit] 4096 / [lit] 4096 * r> drop ;
: cc-workspace-syscall ( page-bytes -- address )
  [lit] 0 swap [lit] 3 [lit] 34 true [lit] 0 [lit] 9 syscall6 ;
defer cc-workspace-syscall-fwd
' cc-workspace-syscall is cc-workspace-syscall-fwd
: cc-workspace-map ( bytes code -- address )
  >r r@ cc-workspace-round cc-workspace-syscall-fwd
  dup [lit] 0 <= if, r@ cc-die then, r> drop ;
```

`cc-io-direct-workspace` maps the combined capacity only when its cached
base is empty, then places the source slice after input and output after
source. `cc-io-default-workspace` restores the dictionary-backed addresses
and limits (`forth-bootstrap/cc/030-cc-io.fth:275`):

```forth file=cc/030-cc-io.fth
: cc-io-default-workspace ( -- )
  cc-in-default-buf cc-in-buffer ! cc-in-default-cap cc-in-limit !
  cc-src-default-buf cc-src-buffer ! cc-src-default-cap cc-src-limit !
  cc-out-default-buf cc-out-buffer ! cc-out-default-cap cc-out-limit ! ;
: cc-io-direct-workspace ( -- )
  cc-io-direct-base @ 0= if,
    cc-in-direct-cap cc-src-direct-cap + cc-out-direct-cap + [lit] 20 cc-workspace-map
    cc-io-direct-base !
  then,
  cc-io-direct-base @ cc-in-buffer ! cc-in-direct-cap cc-in-limit !
  cc-io-direct-base @ cc-in-direct-cap + cc-src-buffer !
  cc-src-direct-cap cc-src-limit !
  cc-src-buf cc-src-direct-cap + cc-out-buffer ! cc-out-direct-cap cc-out-limit ! ;
```

Neither selector resets lengths or cursors, copies contents, nor releases
the cached mapping. Select the profile before loading a new input and use
the ordinary initializers. The later bootstrap drivers choose their
profiles in Chapters 50–52; their execution is outside this checkpoint.

## Why one big buffer instead of streaming?

One buffer per responsibility gives the preprocessor stable raw text, the
lexer stable source slices and the emitter writable output fields. Random
access is explicit: the reader carries a position, and the patchers accept
offsets. Streaming would need additional machinery to retain text for
look-ahead and to revisit unfinished output.

The price is a fixed memory budget and whole-input residency. Capacity
checks bound ordinary appends; they do not turn unchecked patches, invalid
allocation requests or ignored I/O errors into safe operations. Each
interface still has a caller contract.

## Try it

Run these commands from the `forth-bootstrap` checkout root. They use the
layer inputs selected in `forth-bootstrap/test.sh:114` and
`forth-bootstrap/test.sh:119`, without loading later compiler layers.

The arena assertions in `forth-bootstrap/cc/test-020-cc-arena.fth:9` check
distinct allocations at the requested spacing, preservation of a stored
value, and matching, mismatching and empty byte comparisons. Despite its
alignment comment, the test does not check the base address modulo a cell.

The I/O assertions in `forth-bootstrap/cc/test-030-cc-io.fth:10` fill source
text directly and check peek, consumption, newline accounting and EOF.
They also check append positions, byte order for both wide emitters, and
byte and short-field patching. They do not exercise stdin loading, file
writing, mapped workspace selection or the full-cell patcher.

```sh
cat forth/010-lib.fth cc/020-cc-arena.fth cc/test-020-cc-arena.fth | ./seed-forth
printf 'arena exit: %s\n' "$?"
cat forth/010-lib.fth cc/020-cc-arena.fth cc/030-cc-io.fth cc/test-030-cc-io.fth | ./seed-forth
printf 'io exit: %s\n' "$?"
```

Observed output:

```text
arena exit: 0
io exit: 0
```

The tests themselves are silent. Their final `0= die` converts the
accumulated assertion flag into the exit status printed by the shell.

## Exercise

**Trace — easy.** Follow the arena test's first allocation through
`cc-alloc`. Identify the value returned, the pointer stored, and the value
passed as the prospective size to `cc-check-cap`. Then explain why
rounding the request preserves the base's alignment without proving that
the base itself is aligned.

**Verify — moderate.** Extend the I/O test locally to patch a full cell
through `cc-out-patch-8le`. Check every resulting byte and check that
`cc-out-pos` is unchanged. Use only the library and layers loaded above.

