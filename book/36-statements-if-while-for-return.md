# Chapter 36 — Statements and control flow

The expression compiler chooses the order of calculations. Statements
choose whether a calculation happens and whether it happens again. The
instruction emitters already supply jumps; now the parser must decide
where those jumps should land.

## Follow a loop before compiling it

Read the checkpoint's loop in ordinary C notation:

```c
sum = 0;
for (i = 0; i < 8; i = i + 1) {
    if (i == 2) continue;
    if (i == 5) break;
    sum = sum + i;
}
```

On paper, the loop adds 0, 1, 3, and 4, for a sum of 8. The skipped 2
still needs its increment: if `continue` went straight to the condition,
`i` would stay 2 forever. The `break` at 5 must instead bypass the step
and the condition. These are different jump destinations even though
both statements stop executing the current body.

There is a second ordering problem for the compiler. The source puts the
step before the body; the executable needs it afterward. Because this
compiler emits instructions as it parses, it must deliberately visit the
source in a different order.

| Compiler visit | What is emitted | What remains to remember |
|---|---|---|
| Parse initialization, then condition | Initialization followed by the loop test and a forward exit branch | Test address and the exit field to patch |
| Scan past the step | No step instructions yet | The source positions delimiting the step |
| Parse the body | Body instructions, including pending break/continue branches | The lexer position after the body |
| Rewind and parse the step | Step instructions after the body; continue branches target their start | Restore the lexer position after the body |
| Finish the loop | Backward jump to the test; patch the exit and break fields | Restore the enclosing loop and scope state |

This table traces the source algorithm below, not a second execution of
the loop. Runtime never rewinds the lexer: it follows the already emitted
jumps. Restoring the lexer is just as important as the rewind. Without
it, the compiler would resume reading near the loop header instead of at
the statement following the loop. A `continue` targets the emitted step;
a `break` targets the first instruction after the loop.

Both problems use the same tools: remember a location when it is known,
or leave a fixup when it is not. We will start with `if`, which needs one
forward destination, then grow that technique into nested loops and
switches. Each loop keeps its own pending jumps and patches them as their
destinations become known.

## The forward reference, compound blocks, and `if`

The dispatcher selects a parser from the leading token; parsers with bodies call the dispatcher again. `cc-parse-stmt-fwd` connects those recursive calls to the dispatcher after the handlers have been defined (`forth-bootstrap/cc/112-cc-stmt.fth:1`):

```forth file=cc/112-cc-stmt.fth
\ 112-cc-stmt.fth — statement parser for the C-subset compiler.
\
\ Parses compound blocks, if, while, for, do/while, switch, break, continue,
\ labels and goto, and expression statements.  Each emits jumps with rel32
\ placeholders and patches them once their targets are known.
\
\ Depends on 110-cc-decl.fth (local declarations, return) and everything it
\ depends on.

\ ===========================================================================
\ Statement dispatch
\ ===========================================================================
\ cc-parse-stmt is mutually recursive with every statement that has a body
\ (compound, if, while, for, do, switch), and those come first, so they call
\ it through this deferred word (010-lib.fth), filled in once it is defined.

defer cc-parse-stmt-fwd

```

A compound block repeats that recursive call until the closing brace.
Its scope controls which names lookup can find: closing the block removes
its local declarations from the symbol table. It does not reclaim their
core frame slots; Chapter 35's allocator keeps those reserved for the
function. This is a compiler-side scope change, not an emitted stack pop
(`forth-bootstrap/cc/112-cc-stmt.fth:19`):

```forth file=cc/112-cc-stmt.fth
\ cc-parse-compound ( -- )  '{' (stmt | decl)* '}'
\ Caller has already consumed '{'.  Pushes/pops a scope so locals declared
\ inside the block are discarded at end-of-block.
: cc-parse-compound
  cc-scope-push
  begin,
    cc-next-token-keep
    \ Stop on '}'.
    tok-kind @ tk-punct = tok-num @ [char] } = and 0=
  while,
    cc-putback-token
    cc-parse-stmt-fwd
  repeat,
  \ '}' was consumed by the loop test.
  cc-scope-pop ;

```

An `if` must skip code whose size is unknown. The rel32 placeholder (Chapter 31) stays on the data stack across the then-body parse; the source layout shows where each path will land (`forth-bootstrap/cc/112-cc-stmt.fth:35`):

```forth file=cc/112-cc-stmt.fth
\ cc-parse-if ( -- )  'if' already consumed.
\   if (expr) stmt
\   if (expr) stmt else stmt
\
\ Codegen:
\     <eval cond>
\     test rdi, rdi
\     jz   <else-or-end>            (rel32 fixup #1)
\     <then-body>
\     [if else:]
\     jmp  <end>                    (rel32 fixup #2)
\   else-or-end:
\     <else-body>
\   end:
: cc-parse-if
  lparen cc-expect-punct-c
  cc-parse-expr
  [char] ) cc-expect-punct-c

  cc-value-test-fwd
  cc-emit-jz-rel32-placeholder                    ( fixup-jz )

  cc-parse-stmt-fwd                             \ then-body

```

An `else` adds a jump over its own body before the false branch is patched. Without `else`, the lookahead token goes back and the false branch targets the end directly (`forth-bootstrap/cc/112-cc-stmt.fth:59`):

```forth file=cc/112-cc-stmt.fth
  \ Optional else.
  cc-next-token-keep
  tok-kind @ tk-kw = tok-kw-id @ kw-else = and if,
    \ jmp end ; patch jz to here ; else-body ; patch jmp to here.
    cc-emit-jmp-rel32-placeholder                 ( fixup-jz fixup-jmp )
    swap cc-patch-rel32-to-here                   ( fixup-jmp )
    cc-parse-stmt-fwd                           \ else-body
    cc-patch-rel32-to-here                        ( -- )
  else,
    cc-putback-token
    cc-patch-rel32-to-here                        ( -- )
  then, ;

```

## Loop helpers and absolute backward branches

The target supplied to these helpers is an absolute virtual address; the emitted instruction still uses a relative displacement. The handlers differ only in which branch opcode precedes that displacement.

| Input → result | Handler |
|---|---|
| Target → unconditional branch | `cc-emit-jmp-vaddr` |
| Target → branch when nonzero | `cc-emit-jnz-vaddr` |
| Target → branch when equal | `cc-emit-je-vaddr` |

The unconditional form subtracts the address after the displacement from the target (`forth-bootstrap/cc/112-cc-stmt.fth:72`):

```forth file=cc/112-cc-stmt.fth
\ ===========================================================================
\ Loop helpers
\ ===========================================================================
\ cc-emit-jmp-vaddr lives here (rather than in 090-cc-emit.fth) alongside the
\ loop constructs that call it.  cc-here-vaddr (080) loads before 090, so the
\ split is organizational, not a load-order dependency.

\ cc-emit-jmp-vaddr ( target-vaddr -- )  Emit `E9 <rel32>` to absolute target.
\ After emitting the E9 opcode, cc-out-pos points at the rel32 slot's first
\ byte; the address of the next instruction is cc-here-vaddr + 4.
: cc-emit-jmp-vaddr                               ( target-vaddr -- )
  [lit] 233 cc-emit-byte                          \ E9 opcode
  cc-here-vaddr [lit] 4 + -                       \ rel32
  cc-emit-4le ;

```

The conditional forms make the same subtraction after emitting their opcode prefixes (`forth-bootstrap/cc/112-cc-stmt.fth:87`):

```forth file=cc/112-cc-stmt.fth
\ cc-emit-jnz-vaddr ( target-vaddr -- )  Emit `0F 85 <rel32>` to absolute target.
\ After emitting `0F 85`, cc-out-pos points at the rel32 slot's first byte.
: cc-emit-jnz-vaddr                               ( target-vaddr -- )
  [lit]  15 cc-emit-byte                          \ 0F prefix
  [lit] 133 cc-emit-byte                          \ 85 opcode
  cc-here-vaddr [lit] 4 + -                       \ rel32
  cc-emit-4le ;

\ cc-emit-je-vaddr ( target-vaddr -- )  Emit `0F 84 <rel32>` to absolute
\ target.  Mirror of cc-emit-jnz-vaddr; used by switch dispatch.
: cc-emit-je-vaddr                                ( target-vaddr -- )
  [lit]  15 cc-emit-byte                          \ 0F prefix
  [lit] 132 cc-emit-byte                          \ 84 opcode
  cc-here-vaddr [lit] 4 + -                       \ rel32
  cc-emit-4le ;

```

## Break/continue fixup lists

A loop can contain many pending exits. Its list heads belong to the innermost construct, while outer heads wait on the return stack. The `cc-for-*` variables reserve the condition address, exit patch, and step source bounds; `cc-fixup-target-tmp` holds a walker’s destination (`forth-bootstrap/cc/112-cc-stmt.fth:103`):

```forth file=cc/112-cc-stmt.fth
\ ===========================================================================
\ Break / continue fixup-list infrastructure
\ ===========================================================================
\ Each loop maintains TWO linked lists of pending forward-jump fixups: one for
\ break-statements (target = end-of-loop), one for continue-statements (target =
\ continue-point — for-loop step, do-while cond test, while-loop top).
\
\ A node is two cells (16 bytes): { fixup-offset (8), next-pointer (8) }.  The
\ list head is just the variable cc-break-stack-head / cc-continue-stack-head.
\ "0" is the empty-list sentinel.
\
\ When entering a loop, save the outer head on the rstack and reset to 0.  When
\ leaving, walk the list patching each fixup's rel32 to a known target vaddr,
\ then restore the outer head.

variable cc-break-stack-head
variable cc-continue-stack-head
\ Temp slot for cc-walk-and-patch-to-vaddr (avoids deeper stack juggling).
variable cc-fixup-target-tmp
variable cc-for-top-vaddr
variable cc-for-end-fixup
variable cc-for-step-start
variable cc-for-step-end

```

`cc-add-break-fixup` and `cc-add-continue-fixup` select the appropriate head for the shared forward-call list insertion (Chapter 32) (`forth-bootstrap/cc/112-cc-stmt.fth:127`):

```forth file=cc/112-cc-stmt.fth
\ cc-add-fixup-to-list is now defined in 090-cc-emit.fth so 100-cc-expr.fth can
\ reference it from cc-parse-primary's forward-function-rvalue path.

: cc-add-break-fixup                              ( off -- )
  cc-break-stack-head cc-add-fixup-to-list ;

: cc-add-continue-fixup                           ( off -- )
  cc-continue-stack-head cc-add-fixup-to-list ;

```

A list may contain jumps scattered throughout the body. `cc-walk-and-patch-to-vaddr` follows its nodes and patches each displacement to the same destination (`forth-bootstrap/cc/112-cc-stmt.fth:139`):

```forth file=cc/112-cc-stmt.fth
\ cc-walk-and-patch-to-vaddr ( head-ptr target-vaddr -- )
\ Walk the linked list head-ptr, patching each fixup's rel32 to point at
\ target-vaddr.
: cc-walk-and-patch-to-vaddr                      ( head target -- )
  cc-fixup-target-tmp !                           ( head )
  begin,
    dup [lit] 0 <>
  while,
    \ Stack: ( node-ptr ).  Read the fixup-offset (node[0]).
    dup @                                         ( node off )
    \ rel32 = target - (cc-base-vaddr + off + 4)
    cc-fixup-target-tmp @                         ( node off target )
    over cc-base-vaddr + [lit] 4 + -              ( node off rel32 )
    \ Patch 4 bytes at off with rel32.
    over cc-out-patch-4le                         ( node off )
    drop                                          ( node )
    \ Advance to next node: head := node[8].
    [lit] 8 + @                                   ( next-node )
  repeat,
  drop ;
```

Some pending references load an address instead of branching to it. `cc-walk-and-patch-imm64-to-vaddr` writes the absolute target into each immediate (`forth-bootstrap/cc/112-cc-stmt.fth:161`):

```forth file=cc/112-cc-stmt.fth

\ cc-walk-and-patch-imm64-to-vaddr ( head target-vaddr -- )
\ Walk the linked list head, patching each fixup's 8-byte imm64 to the
\ absolute target vaddr.  Used for forward `movabs rdi, imm64` sites that
\ load a function's address as an rvalue before the function is defined.
: cc-walk-and-patch-imm64-to-vaddr                ( head target -- )
  cc-fixup-target-tmp !                           ( head )
  begin,
    dup [lit] 0 <>
  while,
    dup @                                         ( node off )
    cc-fixup-target-tmp @                         ( node off target )
    swap cc-out-patch-8le                         ( node )
    [lit] 8 + @                                   ( next-node )
  repeat,
  drop ;

```

At a construct’s closing address, `cc-walk-and-patch-fixups` supplies the current output position as the destination for every branch in the list (`forth-bootstrap/cc/112-cc-stmt.fth:174`):

```forth file=cc/112-cc-stmt.fth
\ cc-walk-and-patch-fixups ( head-ptr -- )  Patch each fixup to current cc-out-pos.
: cc-walk-and-patch-fixups                        ( head -- )
  cc-here-vaddr
  cc-walk-and-patch-to-vaddr ;

```

## `while`: condition as the continue target

The condition is the re-entry point of a `while`. Saving the outer heads and loop switch depth before clearing the heads keeps nested loops from collecting each other’s jumps (`forth-bootstrap/cc/112-cc-stmt.fth:178`):

```forth file=cc/112-cc-stmt.fth
\ cc-parse-while ( -- )  'while' already consumed.
\
\ Codegen:
\   <top:>           ; record vaddr; continue-target
\   <eval cond>      ; rdi = cond
\   test rdi, rdi
\   jz   <end>       ; rel32 placeholder
\   <body>           ; break/continue inside emit forward-fixed jmps
\   jmp  <top>       ; absolute via cc-emit-jmp-vaddr
\   <end:>           ; patch jz to here; break-target
\
\ The outer break/continue list heads are saved/restored on the rstack.
\ During the body, both heads are 0 (= empty list); break/continue stmts
\ inside add forward-jmp fixup nodes that we patch at end-of-loop.
: cc-parse-while
  \ Save outer break/continue list heads + loop switch-depth on rstack.
  cc-break-stack-head    @ >r
  cc-continue-stack-head @ >r
  cc-loop-switch-depth   @ >r
  [lit] 0 cc-break-stack-head    !
  [lit] 0 cc-continue-stack-head !
  cc-switch-depth @ cc-loop-switch-depth !

```

The condition emits a forward exit, while the known top address survives on the return stack across the body. A `continue` returns to that condition; the ordinary body exit uses the same destination (`forth-bootstrap/cc/112-cc-stmt.fth:201`):

```forth file=cc/112-cc-stmt.fth
  lparen cc-expect-punct-c
  cc-here-vaddr                                   ( top-vaddr )
  cc-parse-expr
  [char] ) cc-expect-punct-c
  cc-value-test-fwd
  cc-emit-jz-rel32-placeholder                    ( top fixup-end )

  \ Park top-vaddr on rstack so it survives the body parse.
  swap >r                                         ( fixup-end ; R: ... top )

  cc-parse-stmt-fwd                             \ body

  \ Continue target = top-vaddr.  Walk continue list (no-op if empty).
  cc-continue-stack-head @ r@ cc-walk-and-patch-to-vaddr

  \ Emit jmp top, then patch jz fixup.
  r> cc-emit-jmp-vaddr                            ( fixup-end )
  cc-patch-rel32-to-here

```

Every `break` lands after the backward jump. Restoring the enclosing state makes subsequent statements belong to the surrounding construct again (`forth-bootstrap/cc/112-cc-stmt.fth:220`):

```forth file=cc/112-cc-stmt.fth
  \ Break target = here.  Walk break list (no-op if empty).
  cc-break-stack-head @ cc-walk-and-patch-fixups

  \ Restore outer heads.
  r> cc-loop-switch-depth   !
  r> cc-continue-stack-head !
  r> cc-break-stack-head    ! ;

```

## `for` with step rewind

The step expression appears before the body in C but must execute after it. `cc-parse-for` therefore saves its scratch variables across nesting and gives the loop its own declaration scope; the layout below separates source order from execution order (`forth-bootstrap/cc/112-cc-stmt.fth:247`):

```forth file=cc/112-cc-stmt.fth
\ cc-parse-for ( -- )  'for' already consumed.
\
\ Grammar: 'for' '(' init? ';' cond? ';' step? ')' stmt
\
\ The step expression appears textually BEFORE the body but must execute
\ AFTER it.  We handle this by recording the source range of the step,
\ scanning past the close-paren, parsing the body, then rewinding the lexer
\ to re-parse the step in place after the body.
\
\ Codegen:
\   <init expr (if any)>
\   <top:>
\   <cond expr (if any, else mov rdi, 1)>
\   test rdi, rdi
\   jz   <end>
\   <body>
\   <step expr (if any)>
\   jmp  <top>
\   <end:>
: cc-parse-for
  cc-for-top-vaddr @ >r cc-for-end-fixup @ >r
  cc-for-step-start @ >r cc-for-step-end @ >r
  cc-scope-push
  lparen cc-expect-punct-c

```

The initializer runs before the new loop takes ownership of break and continue lists. An LP64 declaration goes through the native declaration hook supplied in Chapter 39; the core path accepts an expression (`forth-bootstrap/cc/112-cc-stmt.fth:253`):

```forth file=cc/112-cc-stmt.fth
  \ --- Init (optional); declaration scope ends with this loop. ---
  cc-next-token-keep
  [char] ; cc-tok-punct? 0= if,
    cc-target-lp64 @ if, cc-native-type-start-fwd else, [lit] 0 then, if,
      cc-native-decl-fwd
    else,
      cc-putback-token cc-parse-expr [char] ; cc-expect-punct-c
    then,
  then,

  \ Save outer break/continue heads + loop switch-depth on rstack (after
  \ init, since init runs outside the loop and shouldn't see this loop's
  \ break/continue).
  cc-break-stack-head    @ >r
  cc-continue-stack-head @ >r
  cc-loop-switch-depth   @ >r
  [lit] 0 cc-break-stack-head    !
  [lit] 0 cc-continue-stack-head !
  cc-switch-depth @ cc-loop-switch-depth !

```

An omitted condition must behave as true, including its expression metadata. The condition address and exit placeholder are saved in `cc-for-top-vaddr` and `cc-for-end-fixup` before scanning the step (`forth-bootstrap/cc/112-cc-stmt.fth:273`):

```forth file=cc/112-cc-stmt.fth
  \ Top of loop.
  cc-here-vaddr                                   ( top-vaddr )

  \ --- Cond (optional) ---
  cc-next-token-keep
  tok-kind @ tk-punct = tok-num @ [char] ; = and if,
    \ ';' — empty cond; synthesize an integer value, including its metadata.
    [lit] 1 cc-emit-mov-rdi-imm32 cc-mark-int-value
  else,
    cc-putback-token
    cc-parse-expr
    [char] ; cc-expect-punct-c
  then,

  cc-value-test-fwd
  cc-emit-jz-rel32-placeholder                    ( top fixup-end )
  cc-for-end-fixup !
  cc-for-top-vaddr !

```

The scanner consumes tokens until the matching closing parenthesis, counting nested parentheses. This is not expression compilation: it records `cc-for-step-start` and `cc-for-step-end` without emitting the step, and punctuation inside a string token cannot change the nesting count (`forth-bootstrap/cc/112-cc-stmt.fth:292`):

```forth file=cc/112-cc-stmt.fth
  \ --- Step source-range capture ---
  \ Before scanning forward we must clear any pending putback so the lexer's
  \ next read after we rewind re-tokenises from the new cc-src-pos.
  \ (No putback is in flight here — cc-expect-punct-c above consumed it — but
  \ the assertion is cheap.)
  [lit] 0 cc-tok-pending !
  cc-src-pos @ cc-for-step-start !
  \ Scan to the matching ')'.  Track depth starting at 1 (we're already
  \ inside the outer for-paren).
  [lit] 1                                         ( depth )
  begin,
    dup [lit] 0 >  cc-eof? 0= and
  while,
    cc-next-token-keep
    lparen cc-tok-punct? if, 1+ then,
    [char] ) cc-tok-punct? if, 1- then,
  repeat,
  drop                                            ( -- )
  \ cc-src-pos is now just past ')'.  step-end = position of ')'.
  cc-src-pos @ 1- cc-for-step-end !

```

After emitting the body, the continue list is patched to the start of the step. A lexer snapshot preserves the position after the body while a shortened source window exposes only the saved step; skipping whitespace and comments distinguishes an omitted step from an expression (`forth-bootstrap/cc/112-cc-stmt.fth:313`):

```forth file=cc/112-cc-stmt.fth
  \ --- Body ---
  cc-parse-stmt-fwd

  \ Continue target = HERE (just before step).  Walk continue list.
  cc-continue-stack-head @ cc-walk-and-patch-fixups

  \ --- Re-parse step at recorded range ---
  \ Save current lexer state, set pos := step-start, len := step-end (so the
  \ tokenizer naturally hits EOF at the close-paren).  After parsing, restore.
  cc-lex-state-size cc-alloc dup cc-lex-mark >r
  cc-src-len @ >r
  cc-for-step-end @ cc-src-len !
  cc-for-step-start @ cc-src-pos !
  \ Clear any pending putback before re-tokenising at the new position.
  [lit] 0 cc-tok-pending !
  \ Whitespace/comments alone do not make an omitted step an expression.
  cc-skip-ws-and-comments
  cc-src-pos @ cc-src-len @ < if,
    cc-parse-expr
  then,
  \ Restore lexer state.
  r> cc-src-len !
  r> cc-lex-reset
```

Restoring the lexer snapshot resumes parsing after the body. The backward jump returns to the condition, breaks bypass it, and both loop state and scratch variables return to their enclosing values (`forth-bootstrap/cc/112-cc-stmt.fth:336`):

```forth file=cc/112-cc-stmt.fth

  \ Emit jmp top.
  cc-for-top-vaddr @ cc-emit-jmp-vaddr

  \ Patch jz fixup to current position.
  cc-for-end-fixup @ cc-patch-rel32-to-here

  \ Break target = here.  Walk break list (no-op if empty).
  cc-break-stack-head @ cc-walk-and-patch-fixups

  \ Restore outer heads.
  r> cc-loop-switch-depth   !
  r> cc-continue-stack-head !
  r> cc-break-stack-head    !
  cc-scope-pop
  r> cc-for-step-end ! r> cc-for-step-start !
  r> cc-for-end-fixup ! r> cc-for-top-vaddr ! ;

```

The opening loop now has all its destinations. Its continue list lands
at the emitted increment, its break list lands after the loop, and the
restored lexer points at the next statement. Each saved position belongs
to one of those jobs; substituting another position can produce valid
machine code that runs the wrong loop.

## `do`/`while`

A `do` loop enters its body before testing. Its saved top is therefore the body address, while the continue target remains unknown until the body has been emitted (`forth-bootstrap/cc/112-cc-stmt.fth:354`):

```forth file=cc/112-cc-stmt.fth
\ ===========================================================================
\ do-while loop
\ ===========================================================================
\ Codegen:
\   <top:>           ; record vaddr (back-target for jnz)
\   <body>           ; break/continue inside emit forward-fixup jmps
\   <continue-here:> ; walk continue list, patch each to here
\   <eval cond>      ; rdi = cond
\   test rdi, rdi
\   jnz <top>        ; absolute backward branch
\   <break-here:>    ; walk break list, patch each to here
\
\ "do" has already been consumed.  Grammar:  do stmt while ( expr ) ;
: cc-parse-do-while
  \ Save outer break/continue heads + loop switch-depth.
  cc-break-stack-head    @ >r
  cc-continue-stack-head @ >r
  cc-loop-switch-depth   @ >r
  [lit] 0 cc-break-stack-head    !
  [lit] 0 cc-continue-stack-head !
  cc-switch-depth @ cc-loop-switch-depth !

  \ Record top-vaddr for the backward jnz.
  cc-here-vaddr >r                                ( ; R: ... top )

```

The continue list lands immediately before the trailing condition. A nonzero result jumps backward to the body; fall-through and breaks meet after that jump, before the outer state is restored (`forth-bootstrap/cc/112-cc-stmt.fth:379`):

```forth file=cc/112-cc-stmt.fth
  cc-parse-stmt-fwd                             \ body

  \ Continue target = HERE (just before cond test).
  cc-continue-stack-head @ cc-walk-and-patch-fixups

  \ Parse 'while ( expr ) ;'
  kw-while cc-expect-kw-id
  lparen cc-expect-punct-c
  cc-parse-expr
  [char] ) cc-expect-punct-c
  [char] ; cc-expect-punct-c

  cc-value-test-fwd
  r> cc-emit-jnz-vaddr                            \ jnz top

  \ Break target = here.
  cc-break-stack-head @ cc-walk-and-patch-fixups

  \ Restore outer heads.
  r> cc-loop-switch-depth   !
  r> cc-continue-stack-head !
  r> cc-break-stack-head    ! ;

```

## `switch` with deferred dispatch

A loop patches several jumps to a shared exit. A switch must additionally
remember several possible entry points, one for each case. The same
separation between source order and execution order helps here: discover
the case destinations first, then emit the code that chooses among them.

Case addresses become known while parsing the body. Emitting that body before the comparisons avoids holding its generated code elsewhere: the initial jump skips forward to dispatch, and dispatch jumps backward to the selected case (`forth-bootstrap/cc/112-cc-stmt.fth:402`):

```forth file=cc/112-cc-stmt.fth
\ ===========================================================================
\ switch / case / default
\ ===========================================================================
\ Codegen layout (single-pass with a deferred dispatch table):
\
\     <eval e>                  ; rdi = scrutinee
\     push rbx                  ; preserve outer rbx
\     mov  rbx, rdi             ; rbx = scrutinee for the rest of the switch
\     jmp  <dispatch>           ; rel32, patched after body parse
\   case-K1-body:               ; vaddr recorded in case-list
\     <stmts>
\     [break: jmp <end-A>]      ; (registered as a break fixup)
\     ... (falls through to next case-body if no break)
\   default-body:               ; (or absent)
\     <stmts>
\     jmp <end-A>               ; fall-through past last case (always emitted)
\   dispatch:
\     cmp rbx, K1; je case-K1-body
\     cmp rbx, K2; je case-K2-body
\     ...
\     [jmp default-body | jmp <end-A>]
\   end-A:                      ; break fixups + fall-through + no-default land here
\     pop rbx                   ; restore outer rbx
\   end:
\
```

`cc-switch-cases-head` links each constant to its body address; `cc-add-switch-case` prepends a node. `cc-switch-default-vaddr` records the fallback, and `cc-switch-type` retains the promoted controlling type. Reversed comparison order preserves valid C case selection, but this code does not diagnose duplicate cases (`forth-bootstrap/cc/112-cc-stmt.fth:439`):

```forth file=cc/112-cc-stmt.fth
\ The break list and the cc-switch-default-vaddr / cc-switch-cases-head state
\ are saved/restored on the rstack across recursion (nested switches and
\ switch-inside-loop and loop-inside-switch all work).

variable cc-switch-cases-head     \ linked list of { K (8), vaddr (8), next (8) }
variable cc-switch-default-vaddr  \ 0 if no default seen
variable cc-switch-type           \ LP64: promoted controlling type

\ cc-add-switch-case ( K body-vaddr -- )  Allocate a 24-byte node and prepend
\ it to cc-switch-cases-head.  The list is built in reverse source order;
\ this is fine because the dispatch table semantics are order-independent
\ (duplicate K is illegal C anyway).
: cc-add-switch-case                              ( K vaddr -- )
  [lit] 24 cc-alloc                               ( K vaddr node )
  >r                                              ( K vaddr ; R: node )
  r@ [lit] 8 + !                                  \ node[8] = vaddr
  r@ !                                            \ node[0] = K
  cc-switch-cases-head @ r@ [lit] 16 + !          \ node[16] = old head
  r> cc-switch-cases-head ! ;                     \ head := node

```

## Case labels and comparisons

A native case constant must have the same interpretation as the controlling value. For a controlling type of four bytes, `cc-switch-label` truncates and then sign-extends or zero-extends according to `cc-switch-type`; wider types and the core target leave the constant unchanged (`forth-bootstrap/cc/112-cc-stmt.fth:449`):

```forth file=cc/112-cc-stmt.fth
\ LP64 labels are converted to the promoted controlling type (C90 6.6.4.2),
\ so a 32-bit label is sign- or zero-extended exactly as the scrutinee is.
: cc-switch-label                                 ( K -- K' )
  cc-target-lp64 @ 0= if, exit, then,
  cc-switch-type @ ty-size [lit] 4 = if,
    [lit] 4294967295 and
    cc-switch-type @ ty-unsigned? 0= if,
      dup [lit] 2147483648 and if, [lit] 4294967296 - then,
    then,
  then, ;
```

The label handlers record destinations without emitting a branch, preserving fall-through between adjacent case bodies.

| Input → result | Handler |
|---|---|
| Constant followed by colon → case node | `cc-switch-case` |
| Colon → fallback address | `cc-switch-default` |

Both label paths bind the current output address, so a label costs no instruction bytes (`forth-bootstrap/cc/112-cc-stmt.fth:457`):

```forth file=cc/112-cc-stmt.fth

\ cc-switch-case ( -- )  `case` has been consumed inside an open switch.
\ This is the one entry point for every label, whether it sits at the top
\ of the switch body or nested in a statement within it (C90 6.6.4.2 lets
\ a label appear anywhere in the body): read the constant, convert it to
\ the promoted controlling type, require ':' (170), and record it here.
: cc-switch-case                                  ( -- )
  cc-parse-const cc-switch-label                  ( K )
  cc-next-token-keep
  [char] : cc-tok-punct? 0= if, [lit] 170 cc-die then,
  cc-here-vaddr cc-add-switch-case ;

\ cc-switch-default ( -- )  `default` has been consumed: require ':' and
\ record the current vaddr as the switch's default.
: cc-switch-default                               ( -- )
  [char] : cc-expect-punct-c
  cc-here-vaddr cc-switch-default-vaddr ! ;

```

A native case value outside the signed immediate range needs a register comparison. `cc-emit-switch-compare` loads that value into the otherwise free `rdi`; smaller values keep the immediate form (`forth-bootstrap/cc/112-cc-stmt.fth:478`):

```forth file=cc/112-cc-stmt.fth
\ A label outside signed-32 range needs all 64 bits: load it into rdi,
\ which is free during dispatch, and compare registers (48 39 FB is
\ cmp rbx, rdi).  Every other label keeps the imm32 form.
: cc-emit-switch-compare                          ( K -- )
  cc-target-lp64 @ if,
    dup [lit] 2147483648 + [lit] 4294967296 / if,
      cc-emit-movabs-rdi-imm64
      [lit] 72 cc-emit-byte [lit] 57 cc-emit-byte [lit] 251 cc-emit-byte
      exit,
    then,
  then,
  cc-emit-cmp-rbx-imm32 ;

```

Dispatch walks `cc-switch-cases-head`, compares the saved controlling value in `rbx`, and branches to the recorded body on equality (`forth-bootstrap/cc/112-cc-stmt.fth:488`):

```forth file=cc/112-cc-stmt.fth
\ cc-emit-switch-dispatch ( -- )  Walk cc-switch-cases-head, emitting
\ `cmp rbx, K; je <body-vaddr>` for each entry.  Order is reverse of source,
\ which is semantically irrelevant for switch/case.
: cc-emit-switch-dispatch                         ( -- )
  cc-switch-cases-head @                          ( node )
  begin,
    dup [lit] 0 <>
  while,
    dup @                                         ( node K )
    cc-emit-switch-compare                        \ cmp rbx, K
    dup [lit] 8 + @                               ( node body-vaddr )
    cc-emit-je-vaddr                              \ je <body-vaddr>
    [lit] 16 + @                                  \ next
  repeat,
  drop ;

```

## Building and leaving the switch body

A switch replaces the break list but leaves the loop’s continue list active. Saving its own cases, fallback, and type prevents a nested switch from overwriting the outer dispatch state (`forth-bootstrap/cc/112-cc-stmt.fth:504`):

```forth file=cc/112-cc-stmt.fth
\ cc-parse-switch ( -- )  'switch' already consumed by cc-parse-stmt.
\ Grammar:  switch ( expr ) { (case CONSTANT : | default : | stmt)* }
\ The body is a single compound statement; we parse it inline rather than
\ via cc-parse-compound so that case/default can be intercepted.
: cc-parse-switch
  \ Save outer state on rstack.
  cc-switch-cases-head    @ >r
  cc-switch-default-vaddr @ >r
  cc-break-stack-head     @ >r
  cc-switch-type          @ >r
  [lit] 0 cc-switch-cases-head    !
  [lit] 0 cc-switch-default-vaddr !
  [lit] 0 cc-break-stack-head     !

  \ '(' expr ')'
  lparen cc-expect-punct-c
  cc-parse-expr                                   \ rdi = scrutinee
  cc-last-expr-type @ cc-value-integer-use-fwd
  cc-last-expr-type @ cc-unary-type cc-switch-type !
  [char] ) cc-expect-punct-c

```

The controlling value moves into `rbx` after saving the enclosing value. The switch-depth increment records that saved register for exits that bypass the normal closing pop; the pending dispatch jump waits on the return stack (`forth-bootstrap/cc/112-cc-stmt.fth:525`):

```forth file=cc/112-cc-stmt.fth
  \ Save outer rbx, then move scrutinee into rbx.  Mark the switch open so
  \ return/continue/goto inside the body emit a balancing pop (see
  \ cc-emit-switch-unwind).
  cc-emit-push-rbx
  cc-emit-mov-rbx-rdi
  [lit] 1 cc-switch-depth +!

  \ Forward jmp to the dispatch table (emitted after the body).
  cc-emit-jmp-rel32-placeholder                   ( jmp-to-dispatch )
  >r

  \ '{' (case|default|stmt)* '}'
  [char] { cc-expect-punct-c
  cc-target-lp64 @ if, cc-scope-push then,

```

The body loop intercepts case and default labels and delegates ordinary statements. Under LP64 the dispatcher also accepts labels nested inside those statements, using the same recording words (`forth-bootstrap/cc/112-cc-stmt.fth:540`):

```forth file=cc/112-cc-stmt.fth
  begin,
    cc-next-token-keep
    \ Stop on '}'.
    tok-kind @ tk-punct = tok-num @ [char] } = and 0=
  while,
    \ Three sub-cases: 'case' CONSTANT ':', 'default' ':', or generic stmt.
    tok-kind @ tk-kw = tok-kw-id @ kw-case = and if,
      \ 'case' has been consumed; the label is a constant expression
      \ (cc-parse-const): a number, a character, an enum constant, -1 ...
      cc-switch-case
    else,
      tok-kind @ tk-kw = tok-kw-id @ kw-default = and if,
        \ 'default' has been consumed.
        cc-switch-default
      else,
        \ Generic statement — put back, parse it as one.
        cc-putback-token
        cc-parse-stmt-fwd
      then,
    then,
  repeat,
  \ '}' was consumed by the loop test.

```

Falling past the last case must skip dispatch, not run the comparisons again. That fall-through jump joins the break list, as does the no-match path when no default exists (`forth-bootstrap/cc/112-cc-stmt.fth:563`):

```forth file=cc/112-cc-stmt.fth
  \ Fall-through past the last case-body must skip the dispatch table and
  \ land at end-A.  Emit a jmp placeholder and register it in the break list
  \ so it gets patched together with the rest.
  cc-emit-jmp-rel32-placeholder
  cc-add-break-fixup

  \ Patch the initial jmp-to-dispatch to land here (start of dispatch table).
  r> cc-patch-rel32-to-here                       ( -- )

  \ Emit the dispatch chain.
  cc-emit-switch-dispatch

  \ After the dispatch chain: if there's a default, jump to it; otherwise
  \ register a final jmp to end-A (no case matched, no default).
  cc-switch-default-vaddr @ [lit] 0 <> if,
    cc-switch-default-vaddr @ cc-emit-jmp-vaddr
  else,
    cc-emit-jmp-rel32-placeholder
    cc-add-break-fixup
  then,

```

Breaks converge before `pop rbx`, so every ordinary switch exit restores the saved value. The remaining operations restore the enclosing compiler state and close the native scope (`forth-bootstrap/cc/112-cc-stmt.fth:584`):

```forth file=cc/112-cc-stmt.fth
  \ end-A: walk break list, patching each fixup to here.
  cc-break-stack-head @ cc-walk-and-patch-fixups

  \ Restore outer rbx; the switch is closed again.
  cc-emit-pop-rbx
  cc-switch-depth @ 1- cc-switch-depth !

  \ Restore outer state.
  r> cc-switch-type          !
  r> cc-break-stack-head     !
  r> cc-switch-default-vaddr !
  r> cc-switch-cases-head    !
  cc-target-lp64 @ if, cc-scope-pop then, ;

```

## Break and continue

`cc-parse-break-stmt` adds a pending exit to the innermost loop or switch. `cc-parse-continue-stmt` instead uses the loop’s list and applies the established switch-unwind contract to switches crossed on the way. These parsers assume valid nesting; no depth check rejects an out-of-context jump (`forth-bootstrap/cc/112-cc-stmt.fth:598`):

```forth file=cc/112-cc-stmt.fth
\ ===========================================================================
\ break / continue statements
\ ===========================================================================
\ Each emits a forward-jmp placeholder and prepends its rel32-fixup-offset to
\ the innermost loop's break or continue list.  The enclosing loop walks the
\ list at end-of-loop, patching each fixup's rel32 to the appropriate target.
\
\ cc-parse-break-stmt ( -- )  "break" already consumed by cc-parse-stmt.
\ NB: detecting "break outside any loop" requires a depth counter.  This
\ compiler assumes break/continue appear in valid loop or switch contexts.
: cc-parse-break-stmt
  [char] ; cc-expect-punct-c
  cc-emit-jmp-rel32-placeholder                   ( fixup-offset )
  cc-add-break-fixup ;

\ cc-parse-continue-stmt ( -- )  "continue" already consumed.
\ Unwind the scrutinee pushes of any switches between here and the loop
\ being continued before jumping out of them.
: cc-parse-continue-stmt
  [char] ; cc-expect-punct-c
  cc-switch-depth @ cc-loop-switch-depth @ - cc-emit-switch-unwind
  cc-emit-jmp-rel32-placeholder                   ( fixup-offset )
  cc-add-continue-fixup ;

```

## Labels and `goto`

A loop or switch supplies a destination from its enclosing syntax. A
`goto` names its destination instead, and that label may appear later in
the function. The parser therefore needs a per-function name table as well
as a pending-jump list.

The label table keeps names, addresses, pending jumps, and lexical switch
depths; `cc-label-cap` reads the active bound from `cc-label-limit`
(`forth-bootstrap/cc/112-cc-stmt.fth:638`):

```forth file=cc/112-cc-stmt.fth
\ ===========================================================================
\ Label table (per-function) + goto / label definition
\ ===========================================================================
\ Labels are function-local.  We use parallel arrays similar to cc-sym, sized
\ with a 64-label default and a measured direct-GCC workspace. The count resets on
\ function entry.
\
\ Each label tracks:
\   cc-label-name-addr [id] : pointer into cc-src-buf where name begins
\   cc-label-name-len  [id] : length
\   cc-label-vaddr     [id] : 0 if undefined, else absolute vaddr of the label
\   cc-label-fixup     [id] : head-pointer of forward-jmp fixup list (0 = none)

[lit] 64 constant cc-label-default-cap
variable cc-label-limit
cc-label-default-cap cc-label-limit !
: cc-label-cap ( -- entries ) cc-label-limit @ ;
```

Each column has a default allocation, a variable selecting its active buffer, and an accessor returning that buffer. The address and length columns identify the name; the remaining columns track resolution and switch state.

| Stored value → accessor | Default allocation | Buffer selector |
|---|---|---|
| Name address → `cc-label-name-addr` | `cc-label-default-name-addr` | `cc-label-name-addr-buffer` |
| Name length → `cc-label-name-len` | `cc-label-default-name-len` | `cc-label-name-len-buffer` |
| Target → `cc-label-vaddr` | `cc-label-default-vaddr` | `cc-label-vaddr-buffer` |
| Pending head → `cc-label-fixup` | `cc-label-default-fixup` | `cc-label-fixup-buffer` |
| Switch depth → `cc-label-switch-depth` | `cc-label-default-switch-depth` | `cc-label-switch-depth-buffer` |

The initial selectors point into the default workspace, whose columns share `cc-label-default-cap` (`forth-bootstrap/cc/112-cc-stmt.fth:639`):

```forth file=cc/112-cc-stmt.fth
create cc-label-default-name-addr cc-label-default-cap [lit] 8 * allot
variable cc-label-name-addr-buffer
cc-label-default-name-addr cc-label-name-addr-buffer !
: cc-label-name-addr ( -- address ) cc-label-name-addr-buffer @ ;
create cc-label-default-name-len cc-label-default-cap [lit] 8 * allot
variable cc-label-name-len-buffer
cc-label-default-name-len cc-label-name-len-buffer !
: cc-label-name-len ( -- address ) cc-label-name-len-buffer @ ;
create cc-label-default-vaddr cc-label-default-cap [lit] 8 * allot
variable cc-label-vaddr-buffer
cc-label-default-vaddr cc-label-vaddr-buffer !
: cc-label-vaddr ( -- address ) cc-label-vaddr-buffer @ ;
create cc-label-default-fixup cc-label-default-cap [lit] 8 * allot
variable cc-label-fixup-buffer
cc-label-default-fixup cc-label-fixup-buffer !
: cc-label-fixup ( -- address ) cc-label-fixup-buffer @ ;
create cc-label-default-switch-depth cc-label-default-cap [lit] 8 * allot
variable cc-label-switch-depth-buffer
cc-label-default-switch-depth cc-label-switch-depth-buffer !
: cc-label-switch-depth ( -- address ) cc-label-switch-depth-buffer @ ;
```

`cc-label-default-workspace` selects all default columns and their bound together. The separate `cc-label-direct-cap` and `cc-label-direct-base` reserve a larger workspace choice (`forth-bootstrap/cc/112-cc-stmt.fth:663`):

```forth file=cc/112-cc-stmt.fth
\ Original insn-recog.c has at most 739 labels in one function (recog_20).
\ Five disjoint, page-sized arrays support the fixed 1,024-label direct bound.
[lit] 1024 constant cc-label-direct-cap
variable cc-label-direct-base
: cc-label-default-workspace ( -- )
  cc-label-default-cap cc-label-limit !
  cc-label-default-name-addr cc-label-name-addr-buffer !
  cc-label-default-name-len cc-label-name-len-buffer !
  cc-label-default-vaddr cc-label-vaddr-buffer !
  cc-label-default-fixup cc-label-fixup-buffer !
  cc-label-default-switch-depth cc-label-switch-depth-buffer !
;
```

The source comment calls these arrays “page-sized.” Each actually holds
1,024 eight-byte cells: 8,192 bytes, or two 4 KiB pages. All five columns
occupy 40,960 bytes, matching the allocation below.

`cc-label-direct-workspace` maps storage only when its cached base is empty, then selects disjoint column regions and their common bound. Neither selector migrates live entries or resets `cc-label-count`; Chapter 37 resets the count for each function (`forth-bootstrap/cc/112-cc-stmt.fth:671`):

```forth file=cc/112-cc-stmt.fth
: cc-label-direct-workspace ( -- )
  cc-label-direct-base @ 0= if,
    cc-label-direct-cap [lit] 40 * [lit] 171 cc-workspace-map
    cc-label-direct-base !
  then,
  cc-label-direct-cap cc-label-limit !
  cc-label-direct-base @ cc-label-direct-cap [lit] 0 * + cc-label-name-addr-buffer !
  cc-label-direct-base @ cc-label-direct-cap [lit] 8 * + cc-label-name-len-buffer !
  cc-label-direct-base @ cc-label-direct-cap [lit] 16 * + cc-label-vaddr-buffer !
  cc-label-direct-base @ cc-label-direct-cap [lit] 24 * + cc-label-fixup-buffer !
  cc-label-direct-base @ cc-label-direct-cap [lit] 32 * + cc-label-switch-depth-buffer !
;
variable cc-label-count

```

## Finding and defining a label

`cc-label-vaddr-of` reads a target, `cc-label-set-vaddr` writes one, and `cc-label-fixups` returns the mutable head cell. `cc-label-find` searches the active name columns within `cc-label-count` (`forth-bootstrap/cc/112-cc-stmt.fth:685`):

```forth file=cc/112-cc-stmt.fth
\ Each table is indexed with cell[] (030).
: cc-label-vaddr-of   cc-label-vaddr cell[] @ ;              \ ( id -- vaddr )
: cc-label-set-vaddr  cc-label-vaddr cell[] ! ;              \ ( v id -- )
: cc-label-fixups     cc-label-fixup cell[] ;                \ ( id -- list-cell )

\ cc-label-find ( name-addr name-len -- id-or-neg1 )  Newest first, like
\ cc-sym-find; cc-name-find (030) does the walk.
: cc-label-find
  cc-label-name-addr cc-label-name-len cc-label-count @ cc-name-find ;

```

A newly created label is unresolved. `cc-label-create` checks capacity, stores its spelling, and clears target, pending head, and switch depth before advancing the count (`forth-bootstrap/cc/112-cc-stmt.fth:697`):

```forth file=cc/112-cc-stmt.fth
\ cc-label-create ( name-addr name-len -- id )  Append a new label entry.
\ Initial vaddr=0 (undefined), fixup=0 (no forward refs yet).
: cc-label-create                                 ( a u -- id )
  cc-label-count @ 1+ cc-label-cap [lit] 171 cc-check-cap
  cc-label-count @                                ( a u id )
  >r                                              \ R: id
  r@ cc-label-name-len  cell[] !                  \ store len
  r@ cc-label-name-addr cell[] !                  \ store addr
  [lit] 0 r@ cc-label-set-vaddr                   \ vaddr := 0
  [lit] 0 r@ cc-label-fixups !
  [lit] 0 r@ cc-label-switch-depth cell[] !                    \ fixup-list := 0
  [lit] 1 cc-label-count +!
  r> ;

```

Both a forward jump and a definition need the same entry. `cc-label-find-or-create` preserves an existing identity or appends a new one (`forth-bootstrap/cc/112-cc-stmt.fth:711`):

```forth file=cc/112-cc-stmt.fth
\ cc-label-find-or-create ( name-addr name-len -- id )
\ Look up by name; if not found, append a new entry.
: cc-label-find-or-create                         ( a u -- id )
  2dup cc-label-find                              ( a u id )
  dup [lit] 0 >= if,
    \ Found.  Discard name args, keep id.
    >r 2drop r>
  else,
    drop                                          ( a u )
    cc-label-create
  then, ;

```

Defining a label binds its address and lexical switch depth, rejecting a second definition. Core forward jumps are patched immediately; native jumps wait because each source may require a different switch-stack adjustment (`forth-bootstrap/cc/112-cc-stmt.fth:721`):

```forth file=cc/112-cc-stmt.fth
\ cc-define-label ( name-addr name-len -- )
\ Bind the label to the current cc-out-pos and resolve any forward refs.
\ Dies with code 172 on a duplicate definition.
: cc-define-label                                 ( a u -- )
  cc-label-find-or-create                         ( id )
  \ Reject duplicates.
  dup cc-label-vaddr-of [lit] 0 <> if,
    [lit] 172 cc-die
  then,
  \ Set vaddr.
  >r                                              ( ; R: id )
  cc-here-vaddr r@ cc-label-set-vaddr
  cc-switch-depth @ r@ cc-label-switch-depth cell[] !
  \ Native forward gotos use end-of-function switch-stack trampolines.
  cc-target-lp64 @ if, r> drop else,
    r> cc-label-fixups @ cc-walk-and-patch-fixups
  then, ;

```

## Native jump adjustments

A native jump leaving switches pops saved registers; a jump entering deeper lexical switch nesting reserves matching saved-register slots. `cc-native-goto-adjust` computes that difference without evaluating a skipped controlling expression (`forth-bootstrap/cc/112-cc-stmt.fth:745`):

```forth file=cc/112-cc-stmt.fth
\ cc-parse-goto-stmt ( -- )  "goto" already consumed.  Grammar:  goto IDENT ;
\
\ If the target label is already defined, emit an absolute backward jmp.
\ Otherwise emit a forward-jmp placeholder and prepend its rel32-fixup-offset
\ to the label's fixup list (resolved when the label is defined).
\ Adjust saved switch registers to the destination's lexical depth.
: cc-native-goto-adjust ( source-depth target-depth -- )
  - dup 0< if,
    [lit] 0 swap -
    begin, dup while, cc-emit-push-rbx 1- repeat, drop
  else, cc-emit-switch-unwind then, ;
```

`cc-native-goto-fixup` stores the source depth with the pending branch, allowing resolution to compare the jump’s origin with its eventual target (`forth-bootstrap/cc/112-cc-stmt.fth:750`):

```forth file=cc/112-cc-stmt.fth
: cc-native-goto-fixup ( label-id patch-offset -- )
  [lit] 24 cc-alloc >r r@ !
  cc-switch-depth @ r@ [lit] 8 + !
  dup cc-label-fixups @ r@ [lit] 16 + !
  r> swap cc-label-fixups ! ;
```

A forward native jump needs its own adjustment path. `cc-native-finish-gotos` patches each original branch to such a path and jumps onward to the defined label; it rejects unresolved targets (`forth-bootstrap/cc/112-cc-stmt.fth:755`):

```forth file=cc/112-cc-stmt.fth
: cc-native-finish-gotos
  [lit] 0
  begin, dup cc-label-count @ < while,
    dup cc-label-fixups @
    begin, dup while,
      over cc-label-vaddr-of 0= if, [lit] 174 cc-die then,
      dup @ cc-patch-rel32-to-here
      dup >r [lit] 8 + @ over cc-label-switch-depth cell[] @
      r> swap >r swap r>
      cc-native-goto-adjust
      over cc-label-vaddr-of cc-emit-jmp-vaddr
      [lit] 16 + @
    repeat, drop 1+
  repeat, drop ;

```

A known native target can receive its adjustment immediately. An unknown target instead enters the extended fixup list, preserving the depth at the jump site (`forth-bootstrap/cc/112-cc-stmt.fth:770`):

```forth file=cc/112-cc-stmt.fth
: cc-parse-goto-stmt
  cc-next-token-keep
  tok-kind @ tk-ident <> if,
    [lit] 173 cc-die
  then,
  tok-str-addr @ tok-str-len @ cc-label-find-or-create   ( id )
  cc-target-lp64 @ if,
    dup cc-label-vaddr-of if,
      cc-switch-depth @ over cc-label-switch-depth cell[] @
      cc-native-goto-adjust
      cc-label-vaddr-of cc-emit-jmp-vaddr
    else,
      cc-emit-jmp-rel32-placeholder cc-native-goto-fixup
    then,
    [char] ; cc-expect-punct-c exit,
  then,

```

The core path has a narrower contract: it unwinds every open switch and assumes the target lies outside all switches. A known label gets a direct branch; a forward label receives a shared-list placeholder. The restriction on jumping into a switch applies to this path, not the native path above (`forth-bootstrap/cc/112-cc-stmt.fth:787`):

```forth file=cc/112-cc-stmt.fth
  \ Unwind any open switch scrutinees before jumping (assumes the label is
  \ not inside any switch — a goto to a label inside any switch is unsupported).
  cc-switch-depth @ cc-emit-switch-unwind

  dup cc-label-vaddr-of                           ( id vaddr )
  dup [lit] 0 <> if,
    \ Backward jump to known target.
    cc-emit-jmp-vaddr                             ( id )
    drop                                          ( -- )
  else,
    drop                                          ( id )
    \ Forward ref: emit placeholder, prepend offset to label's fixup list.
    cc-emit-jmp-rel32-placeholder                 ( id fixup-offset )
    swap cc-label-fixups cc-add-fixup-to-list     ( -- )
  then,
  [char] ; cc-expect-punct-c ;

```

## The dispatcher

An identifier can begin either a label or an expression. `cc-peek-after-is-colon?` commits a following colon but restores the lexer state on a mismatch, so the identifier can still start an expression. The copied comment's instruction to “also consume” the colon is stale: success has already consumed it. Failure restores the prior current token and pending flag; it does not independently make IDENT pending. The caller must not advance a second time after success (`forth-bootstrap/cc/112-cc-stmt.fth:819`):

```forth file=cc/112-cc-stmt.fth
\ ===========================================================================
\ One-token lookahead used to detect "IDENT :" label definitions.
\ ===========================================================================
\ The putback layer (cc-tok-pending) only buffers one token.  To peek TWO
\ tokens ahead we mark the lexer state in cc-peek-mark, read one fresh token,
\ and either commit (if it confirms a label) or reset to the mark (if not).

\ cc-peek-after-is-colon? ( -- f )
\ Caller has already consumed one token (e.g. IDENT) into tok-* via
\ cc-next-token-keep.  This peeks the FOLLOWING token without consuming.
\ Returns -1 iff that token is the punctuation ':'.
\
\ If the answer is true, the caller should also consume the colon (it has
\ been read into tok-* and cc-tok-pending=0 — i.e. it's "current").
\ If false, this word restores everything so the IDENT remains pending.
: cc-peek-after-is-colon?
  cc-peek-mark cc-lex-mark
  cc-next-token
  tok-kind @ tk-punct = tok-num @ [char] : = and
  dup 0= if,
    \ Not a colon — rewind.
    cc-peek-mark cc-lex-reset
  then, ;

```

`cc-parse-expr-stmt` puts the leading token back and requires a terminating semicolon. `cc-parse-ident-stmt` first checks whether the identifier denotes a typedef, which selects declaration parsing before label lookahead (`forth-bootstrap/cc/112-cc-stmt.fth:828`):

```forth file=cc/112-cc-stmt.fth
\ cc-parse-expr-stmt ( -- )  An expression statement `e ;`.  The token
\ that starts it has been read, so it goes back first.
: cc-parse-expr-stmt
  cc-putback-token
  cc-parse-expr
  [char] ; cc-expect-punct-c ;

\ cc-parse-ident-stmt ( -- )  A statement that starts with an identifier:
\ a declaration if the name is a typedef, a label definition if a ':'
\ follows, an expression statement otherwise.
: cc-parse-ident-stmt
  tok-str-addr @ tok-str-len @ cc-sym-find        ( id | -1 )
  dup 0< 0= if,
    dup cc-sym-kind-of sk-typedef = if,
      \ Resolved typedef: the IDENT is consumed (tok-* still holds it);
      \ parse the declaration with the typedef's encoded base+ptr-depth.
      cc-sym-val-of                               ( ty )
      dup ty-base swap ty-ptr                     ( base ptr-depth )
      cc-parse-decl-with-base exit,
    then,
  then,
  drop
```

If lookahead confirms a label, its saved spelling is bound at the current address. The native path recursively parses the labeled statement; otherwise the identifier is returned to expression parsing (`forth-bootstrap/cc/112-cc-stmt.fth:850`):

```forth file=cc/112-cc-stmt.fth
  \ Not a typedef (or not found yet — it may be a forward label).
  tok-str-addr @ tok-str-len @                    ( a u )
  cc-peek-after-is-colon? if,
    cc-define-label
    cc-target-lp64 @ if, cc-parse-stmt-fwd then,
    exit,
  then,
  2drop
  cc-parse-expr-stmt ;

```

The final dispatch order gives special forms priority over the expression fallback. A leading `return` token selects the existing `cc-parse-return`, so the dispatcher reuses the return handling from Chapter 35.

| Input → parser |
|---|
| Native case/default → `cc-switch-case` / `cc-switch-default`, then a statement |
| Native type start → `cc-native-decl-fwd` (Chapter 39) |
| Empty statement → no emission |
| Basic type, enum, struct → declaration parser |
| Return → `cc-parse-return` |
| Conditional, loop, switch, break, continue, goto → corresponding handler |
| Opening brace → `cc-parse-compound` |
| Identifier → `cc-parse-ident-stmt` |
| Other token → `cc-parse-expr-stmt` |

Native case and default labels require an open switch even when nested inside another statement. Native declarations leave through their hook before the core cases are considered (`forth-bootstrap/cc/112-cc-stmt.fth:860`):

```forth file=cc/112-cc-stmt.fth
\ cc-parse-stmt ( -- )  Dispatch on the leading token: one line per kind of
\ statement, each returning with exit, once its parser has run.  Silently
\ skip any leading storage-class / type-qualifier keywords (static,
\ extern, const, volatile, ...).  A lone ';' is the empty statement, and
\ `enum TAG x;` declares an int.
: cc-parse-stmt
  cc-skip-storage-quals
  cc-next-token-keep
  cc-target-lp64 @ if,
    kw-case cc-tok-kw? if,
      cc-switch-depth @ 0= if, [lit] 170 cc-die then,
      cc-switch-case cc-parse-stmt-fwd exit,
    then,
    kw-default cc-tok-kw? if,
      cc-switch-depth @ 0= if, [lit] 170 cc-die then,
      cc-switch-default cc-parse-stmt-fwd exit,
    then,
    cc-native-type-start-fwd kw-typedef cc-tok-kw? or if,
      cc-native-decl-fwd exit,
    then,
  then,
```

Each matching core case calls its parser and exits the dispatcher. The final binding connects every earlier recursive body call to this completed selection logic (`forth-bootstrap/cc/112-cc-stmt.fth:881`):

```forth file=cc/112-cc-stmt.fth
  [char] ;    cc-tok-punct? if, exit, then,           \ the empty statement
  cc-tok-is-basic-type-kw? if, cc-parse-decl exit, then,
  kw-enum     cc-tok-kw? if,
    cc-skip-enum-tag  ty-int [lit] 0 cc-parse-decl-with-base exit,
  then,
  \ `struct TAG ... ;` at stmt scope is always a local declaration (a struct
  \ *definition* — `struct TAG { ... };` — is only allowed at top level).
  \ The 'struct' keyword is the current token and is already consumed;
  \ cc-parse-struct-local-decl reads from here.
  kw-struct   cc-tok-kw? if, cc-parse-struct-local-decl exit, then,
  kw-return   cc-tok-kw? if, cc-parse-return            exit, then,
  kw-if       cc-tok-kw? if, cc-parse-if                exit, then,
  kw-while    cc-tok-kw? if, cc-parse-while             exit, then,
  kw-for      cc-tok-kw? if, cc-parse-for               exit, then,
  kw-do       cc-tok-kw? if, cc-parse-do-while          exit, then,
  kw-switch   cc-tok-kw? if, cc-parse-switch            exit, then,
  kw-break    cc-tok-kw? if, cc-parse-break-stmt        exit, then,
  kw-continue cc-tok-kw? if, cc-parse-continue-stmt     exit, then,
  kw-goto     cc-tok-kw? if, cc-parse-goto-stmt         exit, then,
  [char] {    cc-tok-punct? if, cc-parse-compound       exit, then,
  tok-kind @ tk-ident = if, cc-parse-ident-stmt exit, then,
  cc-parse-expr-stmt ;

\ Fill in the forward reference now that cc-parse-stmt is defined.
' cc-parse-stmt is cc-parse-stmt-fwd
```

## Try it

Run from the `forth-bootstrap` checkout root with the seed built in Part 1. The driver loads through the statement layer, supplies a frame with `cc-emit-prologue`, and calls `cc-parse-stmt` directly. It compiles the loop described above into an ELF image in a fresh temporary directory. The final `sum;` leaves the value for the exit shim; no function parser or C return is needed. The empty comments separate type keywords from names inside the token copied by `s,`.

<!-- tryit: expect "driver exit: 0\nloop sum: 8 (exit status)" -->
```sh
(
set -o pipefail
probe_dir=$(mktemp -d /tmp/book-probe.XXXXXXXXXX) || exit "$?"
trap 'status=$?; rm -rf -- "$probe_dir" || status=1; exit "$status"' EXIT
compiler_status=0
{
  cat forth/010-lib.fth cc/020-cc-arena.fth cc/030-cc-io.fth \
      cc/040-cc-prep.fth cc/050-cc-lex.fth \
      cc/060-cc-types.fth cc/070-cc-sym.fth \
      cc/080-cc-elf.fth cc/090-cc-emit.fth cc/100-cc-expr.fth \
      cc/110-cc-decl.fth cc/112-cc-stmt.fth || exit "$?"
  cat <<'FORTH' || exit "$?"
cc-src-init
here dup cc-src-buffer !
s, {int/**/i;int/**/sum;sum=0;for(i=0;i<8;i=i+1){if(i==2)continue;if(i==5)break;sum=sum+i;}sum;}
here swap - cc-src-len !
[lit] 0 cc-src-pos ! [lit] 0 cc-tok-pending !
cc-out-init [lit] 0 cc-bss-size ! cc-emit-elf-header
cc-frame-slots [lit] 8 * cc-emit-prologue
cc-parse-stmt cc-emit-exit-shim
cc-finalize-elf
[lit] 1 cc-out-buf cc-out-pos @ write drop
bye
FORTH
} | ./seed-forth > "$probe_dir/loop" || compiler_status=$?
printf 'driver exit: %s\n' "$compiler_status" # prints 'driver exit: 0'
test "$compiler_status" -eq 0 || exit "$compiler_status"
chmod +x "$probe_dir/loop" || exit "$?"
program_status=0
"$probe_dir/loop" || program_status=$?
printf 'loop sum: %s (exit status)\n' "$program_status" # prints 'loop sum: 8 (exit status)'
test "$program_status" -eq 8
)
```

Observed output:

```text
driver exit: 0
loop sum: 8 (exit status)
```

The result exercises compound and expression statements, conditional jumps, the loop’s step rewind, and distinct break and continue destinations. Switches, labels, native paths, and return delegation are source walkthroughs here; this checkpoint does not execute them.

## Exercise

Hints and feedback are in [Appendix H](66-exercise-feedback.md#chapter-36-leaving-the-right-construct).

**Trace (easy).** Trace the checkpoint’s continue and break placeholders to their patch sites. Explain why exchanging the destinations would terminate the loop early or fail to leave it at the break.

**Modify (moderate).** Wrap the continue test in a switch on `i`, using a case for the skipped item. Keep the break test outside the switch. Predict the sum, then rerun the probe and trace which saved register must be restored before continuing.

Keep the source after `s,` a single Forth token. Use `/**/` wherever the
inserted C needs whitespace, including between `case` and its number.
If the driver fails before printing a loop sum, first check that the whole
C block reached the parser; that is different from a wrong jump target.
