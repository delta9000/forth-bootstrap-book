# Chapter 37 — Functions and translation units

`main` calls `add` before its definition, and `add` reads the global
`bias`. To compile the checkpoint's program, we must keep some names
available across function bodies while containing parameters and local
names within their scopes. We must also remember a call whose destination
has not been emitted yet.

The statement parser can already compile each body. This chapter connects
those bodies and supplies the entry stub that starts the program.

## Setup

Here is the checkpoint's source in reading order:

```c
int bias = 3;
int add(int n);
int main(void) { return add(4); }
int add(int n) { return n + bias; }
```

`int add(int n);` is a **prototype**: a declaration describing a function's
result and parameter types, with no body to execute. The later definition
adds that body. The name `n` is a **parameter**, the local object that
receives a call's value; `4` in `add(4)` is the **argument** supplied by
this caller.

The prototype lets the compiler accept the call before it has seen `add`'s
body. It cannot supply the body's address. That is the problem a fixup list
solves; the declaration and the later definition must meet at the same
pending references.

A **translation unit** is the source given to one compilation after
preprocessing, including any text brought in by headers. Here it contains
all four forms above. Later separate compilation will let another unit
supply a missing function body; this core executable path still needs all
referenced bodies before finalization.

The call parser compiles an expression; the function parser supplies its enclosing scope and frame; the top-level parser selects declarations until end of input. `cc-parse-program` places the entry stub before those bodies and resolves the remaining destinations afterward.

The checkpoint contains four file-scope forms. They arrive in source
order, but that is not the order in which the resulting program runs:

| Source form | What compilation learns or records | What remains unresolved |
|---|---|---|
| `int bias = 3;` | Reserve a data slot and store the initial bytes | The slot's final program address |
| `int add(int n);` | Register a callable name with no body address | Calls or address uses that later need that body |
| `int main(void) { return add(4); }` | Record `main`'s address and emit its call | The call field belongs to the earlier `add` entry's fixup list |
| `int add(int n) { return n + bias; }` | Register the body address; resolve earlier calls; emit a reference to `bias` | The global-address field, until data placement |

The entry stub was emitted before these forms. After finalization, Linux
enters that stub, the stub calls `main`, `main` calls `add`, and the returned
7 travels back to the stub's exit syscall. A prototype contributes compiler
state without contributing a body to run. A global definition contributes
data whose position can wait until every body has been emitted.

Read the call and function paths with those two pending references in
mind: one waits for a function definition, the other for the end of code.
The enum, typedef and top-level dispatch sections cover the other
file-scope forms.

A function name must remain available while parameter tokens replace the current token. `cc-fn-name-addr` and `cc-fn-name-len` preserve it; `cc-fn-param-count` counts incoming parameters, and `cc-fn-prior-sym-id` keeps the earlier prototype available for patching (`forth-bootstrap/cc/114-cc-func.fth:1`):

```forth file=cc/114-cc-func.fth
\ 114-cc-func.fth — function definitions for the C-subset compiler.
\
\ Parses a parameter list, spills the register arguments into the frame, and
\ compiles one `T NAME(params) { body }` between a prologue and an epilogue.
\
\ Depends on 112-cc-stmt.fth (the body's statements) and everything it
\ depends on.

\ ===========================================================================
\ Function parsing: multiple functions, params, SYS-V calling convention
\ ===========================================================================
\ The current-function bookkeeping uses two globals so the name token's bytes
\ aren't lost when subsequent tokens are read for the parameter list.
variable cc-fn-name-addr
variable cc-fn-name-len
variable cc-fn-param-count                        \ # params in current function
variable cc-fn-prior-sym-id                       \ prior sk-func id for fwd-fixup walk; -1 if none

```

The entry call needs to distinguish `main` from other functions. `cc-main-name-bytes` supplies its spelling to `cc-is-main?`; the body loop uses `cc-block-end?` to recognize its closing brace (`forth-bootstrap/cc/114-cc-func.fth:19`):

```forth file=cc/114-cc-func.fth
\ Pre-baked literal "main" for cc-is-main? — laid out as 4 raw bytes (no length
\ prefix here, because cc-is-main? only consumes 4 bytes).
create cc-main-name-bytes  s, main

\ cc-is-main? ( name-addr name-len -- f )  -1 if (addr, len) names "main".
: cc-is-main?                                     ( addr len -- f )
  dup [lit] 4 = if,
    drop                                          ( addr )
    cc-main-name-bytes swap [lit] 4 bytes-eq
  else,
    drop drop [lit] 0
  then, ;

\ cc-block-end? ( -- f )  After cc-next-token-keep, returns -1 if current
\ token is '}'.  Helper used by the function body loop.
: cc-block-end?
  tok-kind @ tk-punct =
  tok-num @ [char] } = and ;

```

## The call codegen

A call must protect earlier argument values while later arguments are
evaluated. As in Chapter 34's assignment trace, there are two lifetimes to
keep separate: the compiler saves a callee identity and argument count,
while the emitted program saves argument values. The register convention
is already established (Chapter 31); here the parser turns an argument
list into the required transfers.

A known function address needs no pending symbol lookup. `cc-emit-call-vaddr` converts that destination into the displacement carried by the emitted call (`forth-bootstrap/cc/100-cc-expr.fth:453`):

```forth chunk=expr-call
\ ===========================================================================
\ Function calls: `NAME ( args )`.  cc-parse-primary calls cc-parse-call
\ once it has seen an identifier followed by '('.
\ ===========================================================================

\ cc-emit-call-vaddr ( target-vaddr -- )  Emit `call <abs-target>` (5 bytes).
\ rel32 = target_vaddr - (callsite_after_E8 + 4) = target - (callsite_vaddr+5)
\ where callsite_vaddr = cc-here-vaddr at the moment of E8.
: cc-emit-call-vaddr
  [lit] 232 cc-emit-byte                          \ E8 opcode
  \ At this point cc-out-pos@ points at the rel32 slot's first byte.
  \ rel32 = target - (cc-here-vaddr + 4)
  cc-here-vaddr [lit] 4 + -                       ( rel32 )
  cc-emit-4le ;

```

Arguments are evaluated left to right and pushed in that order. `cc-emit-pops-for-args` walks their indices backward, asking `cc-emit-pop-by-arg-index` for each destination, so the last value pushed reaches the last argument register (`forth-bootstrap/cc/100-cc-expr.fth:460`):

```forth chunk=expr-call
\ cc-emit-pop-by-arg-index ( arg-index -- )  Emit a pop into the SYS-V arg
\ register corresponding to arg-index (0=rdi, 1=rsi, 2=rdx, 3=rcx, 4=r8, 5=r9).
\ Caller is responsible for not asking past 5.
: cc-emit-pop-by-arg-index
  dup [lit] 0 = if, drop cc-emit-pop-rdi else,
  dup [lit] 1 = if, drop cc-emit-pop-rsi else,
  dup [lit] 2 = if, drop cc-emit-pop-rdx else,
  dup [lit] 3 = if, drop cc-emit-pop-rcx else,
  dup [lit] 4 = if, drop cc-emit-pop-r8  else,
                    drop cc-emit-pop-r9
  then, then, then, then, then, ;

\ cc-emit-pops-for-args ( n -- )  Pop n values off the stack into the first n
\ SYS-V arg registers, in REVERSE order (so the last-pushed value lands in the
\ n-th argument register).  After this, args 1..n live in rdi/rsi/rdx/rcx/r8/r9.
\
\ Walks i = n-1 down to 0, emitting pop-into-reg(i) at each step.  Loop drives
\ a counter on the data stack.
: cc-emit-pops-for-args                           ( n -- )
  1-                                              ( i = n-1 )
  begin,
    dup [lit] 0 >=
  while,
    dup cc-emit-pop-by-arg-index
    1-
  repeat,
  drop ;

```

<details>
<summary>Native call defaults and indirect targets</summary>

The core call walkthrough continues below. These intervening definitions
provide a different argument path for native compilation and the hooks
that the System V layer will replace.

### The native-call hooks

The same source chunk contains the default native-call path. Its helpers remain dormant in the core checkpoint; Chapter 39 introduces the native whole-program profile, and Chapter 41 replaces these defaults for System V interoperability.

The native path leaves arguments on the machine stack. `cc-native-swap-args` exchanges slots through scratch registers; `cc-native-reverse-args` uses it on opposite ends until the first argument is nearest the return address (`forth-bootstrap/cc/100-cc-expr.fth:488`):

```forth chunk=expr-call
\ The native bootstrap image uses an internal all-stack call ABI.
\ Arguments occupy eight-byte slots; arg 0 is nearest the return address.
: cc-native-swap-args                            ( off1 off2 -- )
  >r
  dup [lit] 72 cc-emit-byte [lit] 139 cc-emit-byte
  [lit] 132 cc-emit-byte [lit] 36 cc-emit-byte cc-emit-4le
  r@ [lit] 72 cc-emit-byte [lit] 139 cc-emit-byte
  [lit] 140 cc-emit-byte [lit] 36 cc-emit-byte cc-emit-4le
  [lit] 72 cc-emit-byte [lit] 137 cc-emit-byte
  [lit] 140 cc-emit-byte [lit] 36 cc-emit-byte cc-emit-4le
  r> [lit] 72 cc-emit-byte [lit] 137 cc-emit-byte
  [lit] 132 cc-emit-byte [lit] 36 cc-emit-byte cc-emit-4le ;

: cc-native-reverse-args                         ( n -- )
  [lit] 0
  begin, over [lit] 2 / over > while,
    dup [lit] 8 * >r
    over 1- over - [lit] 8 * r> swap cc-native-swap-args
    1+
  repeat, 2drop ;

```

A saved indirect target sits beyond the argument slots. `cc-native-load-call-target` retrieves it without removing arguments; `cc-native-drop-args` later advances the stack past the consumed slots (`forth-bootstrap/cc/100-cc-expr.fth:509`):

```forth chunk=expr-call
: cc-native-drop-args                            ( n -- )
  dup if,
    [lit] 72 cc-emit-byte [lit] 129 cc-emit-byte [lit] 196 cc-emit-byte
    [lit] 8 * cc-emit-4le
  else, drop then, ;

: cc-native-load-call-target                     ( n -- )
  [lit] 72 cc-emit-byte [lit] 139 cc-emit-byte
  [lit] 132 cc-emit-byte [lit] 36 cc-emit-byte
  [lit] 8 * cc-emit-4le ;                         \ mov rax,[rsp+n*8]

```

Each native argument must be a materialized scalar value. `cc-native-parse-args` uses the assignment parser so commas remain separators, rejects struct values, pushes each result, and reverses the completed list (`forth-bootstrap/cc/100-cc-expr.fth:520`):

```forth chunk=expr-call
: cc-native-parse-args                           ( -- n )
  [lit] 0
  cc-next-token-keep
  [char] ) cc-tok-punct? if, exit, then,
  cc-putback-token
  begin,
    cc-parse-assign-fwd cc-emit-materialize
    cc-last-expr-type @ dup ty-base ty-struct = swap ty-ptr 0= and if,
      [lit] 212 cc-die
    then,
    cc-emit-push-rdi 1+
    cc-next-token-keep [char] , cc-tok-punct? 0=
  until,
  [char] ) cc-tok-punct? 0= if, [lit] 121 cc-die then,
  dup cc-native-reverse-args ;

```

### Dispatching native calls

A named native callee can be a function symbol or a pointer stored in a local or global. `cc-parse-native-call` preserves pointer targets before parsing arguments; direct forward calls attach a fixup unless the expression is unevaluated (`forth-bootstrap/cc/100-cc-expr.fth:536`):

```forth chunk=expr-call
: cc-parse-native-call                           ( id -- )
  cc-check-static-init
  dup cc-sym-kind-of sk-func <> if,
    dup cc-sym-kind-of sk-local = if,
      cc-sym-val-of cc-emit-load-local
    else,
      cc-sym-val-of cc-emit-global-ref cc-emit-load-via-rdi
    then,
    cc-emit-push-rdi
    cc-native-parse-args
    dup cc-native-load-call-target cc-emit-call-rax
    1+ cc-native-drop-args
  else,
    cc-native-parse-args >r
    dup cc-sym-val-of [lit] 0 = if,
      cc-emit-call-rel32-placeholder
      cc-expr-unevaluated @ if,
        2drop
      else, swap cc-sym-call-fixups cc-add-fixup-to-list then,
    else,
      cc-sym-val-of cc-emit-call-vaddr
    then,
    r> cc-native-drop-args
  then,
  cc-emit-mov-rdi-rax ;

```

An expression can also supply the callee directly. `cc-parse-indirect-call` saves that value and marks an integer result. `cc-native-call-fwd` and `cc-native-indirect-fwd` bind these defaults. `cc-native-call-result-fwd` initially calls `cc-native-call-result` for the symbol type and descriptor; `cc-native-function-desc-fwd` initially calls `cc-native-function-desc`, which supplies no descriptor (`forth-bootstrap/cc/100-cc-expr.fth:562`):

```forth chunk=expr-call
: cc-parse-indirect-call                         ( -- )
  cc-check-static-init
  cc-emit-materialize cc-emit-push-rdi
  cc-native-parse-args
  dup cc-native-load-call-target cc-emit-call-rax
  1+ cc-native-drop-args
  cc-emit-mov-rdi-rax
  ty-int [lit] 0 ty-make [lit] 0 cc-mark-typed-value ;

\ Optional ABI hooks preserve the native default until an explicit opt-in.
defer cc-native-call-fwd
defer cc-native-indirect-fwd
' cc-parse-native-call is cc-native-call-fwd
' cc-parse-indirect-call is cc-native-indirect-fwd
: cc-native-call-result ( id -- ty desc )
  dup cc-sym-kind-of sk-func = if, dup cc-sym-type-of
  else, ty-int [lit] 0 ty-make then,
  swap cc-expr-symbol-desc ;
defer cc-native-call-result-fwd
' cc-native-call-result is cc-native-call-result-fwd
: cc-native-function-desc drop [lit] 0 ;
defer cc-native-function-desc-fwd
' cc-native-function-desc is cc-native-function-desc-fwd

```

</details>

### Parsing a core call

The opening parenthesis has already been consumed when `cc-parse-call` receives the callee symbol. It delegates native mode through `cc-native-call-fwd`; the core path starts an argument count and handles an empty list (`forth-bootstrap/cc/100-cc-expr.fth:595`):

```forth chunk=expr-call
\ cc-parse-call ( id -- )  Parse a comma-separated argument list — the leading
\ '(' has ALREADY been consumed by cc-parse-primary (it was the lookahead
\ token that triggered dispatch here).  Evaluate each arg left-to-right
\ (each result pushed onto the stack), then emit the SYS-V argument-register
\ loads, the call, and post-call rdi <- rax move so the caller sees the
\ return value in rdi.
\
\ Stack at entry: ( id ).  The id is the symbol-table id of the callee.
\ Stack at exit:  ( ).
: cc-parse-call
  cc-target-lp64 @ if, cc-native-call-fwd exit, then,
  \ Parse the argument list.  Stack underneath: ( id ).  We thread an
  \ argument count below the id.  Initial state: ( id 0 ).
  [lit] 0                                         ( id arg-count )

  \ Empty arg list?
  cc-next-token-keep
  tok-kind @ tk-punct = tok-num @ [char] ) = and if,
    \ ')' — empty arg list, leave count = 0.
  else,
    cc-putback-token
```

While parsing a nonempty list, the callee id and count stay on the compiler stack. Each emitted push protects an argument value from the code for the next expression; the closing token must be a parenthesis (`forth-bootstrap/cc/100-cc-expr.fth:607`):

```forth chunk=expr-call
    \ Loop: parse one arg, push, increment count; continue while next is ','.
    begin,                                        ( id arg-count )
      cc-parse-expr-fwd                           \ rdi := arg value
      cc-emit-push-rdi
      1+                                          \ count++
      cc-next-token-keep
      tok-kind @ tk-punct = tok-num @ [char] , = and 0=
    until,                                        \ until the next is not ','
    cc-putback-token
    \ The token AFTER the last arg should be ')'.  Consume it.
    cc-next-token-keep
    tok-kind @ tk-punct = tok-num @ [char] ) = and 0= if,
      [lit] 121 cc-die
    then,
  then,

  ( id arg-count )

```

The core path rejects more than six arguments before selecting registers.
Balanced pushes and pops do not guarantee alignment at every nested call.
For core `f(1, g())`, start with a 16-byte-aligned stack: `rsp mod 16 = 0`.
Saving argument 1 changes the remainder to 8. The empty inner `g()` has no
argument pushes to undo, so its `call` executes with `rsp mod 16 = 8`,
violating the System V requirement of zero immediately before the call.
The return address then puts the callee at `rsp mod 16 = 0` instead of the
required 8. This is a source-derived limitation of this core path, not an
observed crash. Chapter 41's explicit System V
target protects live values and aligns a fresh outgoing block; the copied
comment below must not be read as that later guarantee
(`forth-bootstrap/cc/100-cc-expr.fth:625`):

```forth chunk=expr-call
  \ The SYS-V register path supports up to 6 args.  Reject excess.
  dup [lit] 6 > if,
    [lit] 122 cc-die
  then,

  \ NOTE on alignment: argument values are pushed while parsing, then popped
  \ into registers before the call.  The pops restore rsp to its pre-argument
  \ value, which our prologue keeps 16-aligned.  Nested calls happen during
  \ expression parsing before these argument pushes are popped, so they have
  \ their own balanced call sequence.

  \ Pop arg-count values off the stack into the arg registers.
  dup cc-emit-pops-for-args                       ( id arg-count )
  drop                                            ( id )

  \ Dispatch on symbol kind.
  \   sk-func, val != 0 -> direct call: E8 <rel32> to absolute vaddr.
  \   sk-func, val == 0 -> forward call: emit placeholder, register fixup
  \                        on this prototype's call-fixups list.  When the
  \                        function is later defined, cc-parse-function walks
  \                        the list and patches each rel32.
  \   sk-local + ty-func -> indirect call: load fp slot into rax, call rax.
  \                        rdi/rsi/... already hold args; rax is free.
```

A function with an address gets a direct call; an unresolved prototype receives a forward-call fixup (Chapter 32). A local function pointer instead loads the target into `rax`. After either call, the result moves into the expression result register (`forth-bootstrap/cc/100-cc-expr.fth:648`):

```forth chunk=expr-call
  dup cc-sym-kind-of sk-func = if,
    dup cc-sym-val-of [lit] 0 = if,
      \ Forward call.  Emit E8 + 4-byte placeholder; thread the slot offset
      \ onto the prototype's call-fixups list.
      cc-emit-call-rel32-placeholder              ( id patch-off )
      swap cc-sym-call-fixups                     ( patch-off list-cell )
      cc-add-fixup-to-list
    else,
      cc-sym-val-of                               ( target-vaddr )
      cc-emit-call-vaddr
    then,
  else,
    dup cc-sym-kind-of sk-local =
    over cc-sym-type-of ty-base ty-func = and if,
      cc-sym-val-of                               ( slot )
      cc-emit-load-local-into-rax                 \ rax := fp value
      cc-emit-call-rax
    else,
      drop
      [lit] 123 cc-die
    then,
  then,

  \ Move return value into rdi (so the caller's expression machinery picks it up).
  cc-emit-mov-rdi-rax ;

```

## Parameter lists and the spill

Follow `add(4)` across the boundary. The caller puts 4 in the first
argument register, `rdi`. The function registers `n` as its first local
and emits a store from that register into the local slot. The expression
`n + bias` can then use the ordinary local-load machinery. Giving a
parameter an addressable home also makes `&n` possible; keeping only its
incoming register would not.

The parameter parser must allocate storage before the body uses a parameter name. `cc-parse-param-list-loop` starts by selecting the base type; a struct parameter carries its descriptor into registration (`forth-bootstrap/cc/114-cc-func.fth:45`):

```forth file=cc/114-cc-func.fth
\ ===========================================================================
\ Parameter-list parsing + spill
\ ===========================================================================

\ cc-parse-param-list-loop ( -- )  Parse one or more parameters separated by
\ ','.  T may be int / char / void / long / short / struct TAG / enum TAG /
\ typedef-name, with '*' modifiers.  Consumes the closing ')'.
: cc-parse-param-list-loop
  begin,
    \ Base type.  Both branches leave ( base ptr-depth-so-far ); the kw path
    \ starts ptr-depth at 0; the typedef path inherits the typedef's encoded
    \ ptr-depth (so FUNCTION = void (*)() stays a function pointer in params).
    \ Qualifiers before the type (`const int size`) are skipped.
    cc-skip-qualifiers
    cc-next-token-keep
    tok-kind @ tk-kw = if,
      tok-kw-id @ kw-struct = if,
        cc-lookup-struct-tag cc-pending-struct-desc !
        ty-struct [lit] 0
      else,
```

Character pointers must preserve their base type for later indexing. Other basic keyword spellings collapse to the core integer representation, and an enum tag is consumed without changing that representation (`forth-bootstrap/cc/114-cc-func.fth:58`):

```forth file=cc/114-cc-func.fth
        \ int/char/void/long/short/unsigned/signed — char is distinguished so
        \ `char* s` params get ty-char + ptr-depth, which the array-index path
        \ needs to emit byte stride / byte load for `s[i]`.  Others collapse
        \ to ty-int.
        [lit] 0 cc-pending-struct-desc !
        tok-kw-id @ kw-enum = if, cc-skip-enum-tag then,
        tok-kw-id @ kw-char = if,
          ty-char
        else,
          ty-int
        then,
        cc-tok-is-basic-type-kw? if, cc-more-type-kws then,
        [lit] 0
      then,
    else,
```

A typedef parameter inherits both its base and pointer depth. The identifier branch rejects unknown names and non-typedef symbols before adding any explicit pointer stars (`forth-bootstrap/cc/114-cc-func.fth:73`):

```forth file=cc/114-cc-func.fth
      tok-kind @ tk-ident = if,
        \ Typedef-name (e.g. FILE, FUNCTION).  Look up and unpack its encoded
        \ base+ptr-depth so function-pointer typedefs survive into param type.
        tok-str-addr @ tok-str-len @ cc-sym-find   ( id )
        dup 0< if,
          [lit] 180 cc-die
        then,
        dup cc-sym-kind-of sk-typedef <> if,
          [lit] 181 cc-die
        then,
        [lit] 0 cc-pending-struct-desc !
        cc-sym-val-of                              ( ty )
        dup ty-base swap ty-ptr                    ( base ptr-depth )
      else,
        [lit] 182 cc-die
        ty-int [lit] 0                            \ unreachable
      then,
    then,
    ( base ptr-depth )
    cc-count-stars                                ( base ptr-depth extra )
    +                                              ( base total-ptr )
    ty-make                                       ( ty )
```

Each parameter name receives the next local slot and its pending struct descriptor. Both the local count and `cc-fn-param-count` advance; a comma repeats the parse, while the end of the list must be a closing parenthesis (`forth-bootstrap/cc/114-cc-func.fth:95`):

```forth file=cc/114-cc-func.fth
    \ Expect IDENT.
    cc-next-token-keep
    tok-kind @ tk-ident <> if,
      [lit] 183 cc-die
    then,
    \ Add as a local: name in tok-str-addr/len, kind=sk-local, type=ty,
    \ val=current local count (= slot).  Stack on entry: ( ty ).
    tok-str-addr @ tok-str-len @                  ( ty a u )
    rot                                            ( a u ty )
    sk-local swap                                  ( a u sk-local ty )
    cc-fn-local-count @                            ( a u kind ty slot )
    cc-sym-add                                    ( id )
    cc-pending-struct-desc @ swap cc-sym-set-struct-desc
    [lit] 1 cc-fn-add-slots
    [lit] 1 cc-fn-param-count +!
    \ Continue if next is ','.
    cc-next-token-keep
    tok-kind @ tk-punct = tok-num @ [char] , = and 0=
  until,
  cc-putback-token
  \ Now consume the closing ')'.
  cc-next-token-keep
  tok-kind @ tk-punct = tok-num @ [char] ) = and 0= if,
    [lit] 184 cc-die
  then, ;

```

An empty parameter list needs no local symbols. `cc-parse-param-list` accepts both `()` and `(void)`; the lookahead distinguishes the latter from a named parameter whose type begins with `void` (`forth-bootstrap/cc/114-cc-func.fth:124`):

```forth file=cc/114-cc-func.fth
\ cc-parse-param-list ( -- )  Parse a possibly-empty comma-separated list of
\ parameters.  Caller has NOT yet consumed any tokens.  When this returns the
\ closing ')' has been consumed.  Each parameter becomes an sk-local symbol.
: cc-parse-param-list
  [lit] 0 cc-fn-param-count !
  cc-next-token-keep
  tok-kind @ tk-punct = tok-num @ [char] ) = and if,
    \ ')' — empty list, done.
  else,
    \ Special case: `(void)` = no params.  Peek for kw-void followed by ')'.
    tok-kind @ tk-kw = tok-kw-id @ kw-void = and if,
      cc-peek-mark cc-lex-mark
      cc-next-token                               \ advance past void; tok-* := next
      tok-kind @ tk-punct = tok-num @ [char] ) = and >r
      cc-peek-mark cc-lex-reset
      r> if,
        \ It IS '(void)'.  void is already consumed; now consume ')'.
        cc-next-token
      else,
        cc-putback-token
        cc-parse-param-list-loop
      then,
    else,
      cc-putback-token
      cc-parse-param-list-loop
    then,
  then, ;

```

### Making parameters addressable

`cc-emit-spill-params` copies incoming registers into their assigned local slots. Parameters and body locals share the fixed 256-byte frame: 32 eight-byte slots, charged through the existing slot allocator. The spill has paths for the six register parameters; it does not implement stack parameters (`forth-bootstrap/cc/114-cc-func.fth:152`):

```forth file=cc/114-cc-func.fth
\ cc-emit-spill-params ( -- )  In the function prologue, spill the SYS-V
\ argument registers (rdi/rsi/rdx/rcx/r8/r9) into the local slots reserved
\ for them by cc-parse-param-list (slots 0..cc-fn-param-count-1).
: cc-emit-spill-params
  cc-fn-param-count @ [lit] 1 >= if,
    [lit] 0 cc-emit-store-local
  then,
  cc-fn-param-count @ [lit] 2 >= if,
    [lit] 1 cc-emit-store-local-from-rsi
  then,
  cc-fn-param-count @ [lit] 3 >= if,
    [lit] 2 cc-emit-store-local-from-rdx
  then,
  cc-fn-param-count @ [lit] 4 >= if,
    [lit] 3 cc-emit-store-local-from-rcx
  then,
  cc-fn-param-count @ [lit] 5 >= if,
    [lit] 4 cc-emit-store-local-from-r8
  then,
  cc-fn-param-count @ [lit] 6 >= if,
    [lit] 5 cc-emit-store-local-from-r9
  then, ;

```

The core compiler returns a single register-sized value regardless of the declared spelling. `cc-parse-fn-return-type` therefore consumes storage qualifiers, a type or tag, and pointer stars without retaining a return descriptor (`forth-bootstrap/cc/114-cc-func.fth:181`):

```forth file=cc/114-cc-func.fth
\ ===========================================================================
\ cc-parse-fn-return-type ( -- )
\ Consume the function's return type, which may be:
\   - int / char / void, after any storage classes and qualifiers
\   - struct TAG       (tag ident consumed)
\   - enum TAG         (tag ident consumed)
\   - typedef-name     (any non-keyword ident — FILE, etc.)
\ Followed by zero or more '*' modifiers.  Codegen treats every return as a
\ single rax-sized value, so the type is not recorded — it's just consumed.
: cc-parse-fn-return-type
  cc-skip-storage-quals
  cc-next-token-keep
  tok-kind @ tk-kw = if,
    tok-kw-id @ kw-struct = if,
      cc-next-token-keep
      tok-kind @ tk-ident <> if,
        [lit] 185 cc-die
      then,
    then,
    tok-kw-id @ kw-enum = if, cc-skip-enum-tag then,
    cc-tok-is-basic-type-kw? if, [lit] 0 cc-more-type-kws drop then,
  else,
    tok-kind @ tk-ident <> if,
      [lit] 186 cc-die
    then,
  then,
  cc-count-stars drop ;

```

## Function definitions

The function parser must publish a callable name before entering its body. The source layout puts registration ahead of the parameter scope, then encloses statement parsing between prologue and epilogue (`forth-bootstrap/cc/114-cc-func.fth:200`):

```forth file=cc/114-cc-func.fth
\ cc-parse-function — one user-defined `T NAME(params) { body }`.  T may be
\ int / char / void / struct TAG / typedef-name, optionally followed by '*'s.
\ ===========================================================================
\ Layout:
\   1. Consume return type, NAME, '('.
\   2. Capture the function's start vaddr (cc-here-vaddr) and
\      register it in the symbol table BEFORE parsing params/body — this lets
\      the body call this function recursively, and is also needed before any
\      forward-call patch.
\   3. If the name is "main", record cc-main-vaddr for the entry stub.
\   4. Push a fresh scope.  Reset local counter.
\   5. Parse the parameter list — each param becomes a local in slots 0..N-1.
\   6. Consume `{`.
\   7. Emit prologue (cc-frame-slots * 8 = 256-byte frame, room for 32
\      locals incl. params).
\   8. Spill arg registers into their slots.
\   9. Loop: parse statements until `}`.
\  10. Emit implicit return (xor rax,rax + epilogue) — wasted bytes if the
\      function already ended with a `return`, but harmless.
\  11. Pop scope.
: cc-parse-function
  cc-parse-fn-return-type
  \ Function name.
  cc-next-token-keep
  tok-kind @ tk-ident <> if,
    [lit] 187 cc-die
  then,
  tok-str-addr @ cc-fn-name-addr !
  tok-str-len  @ cc-fn-name-len  !
```

Before adding the definition, the function parser saves any previous symbol for the name. The new function entry remains outside the scope that will be popped at function end, making recursive calls and calls from later functions possible (`forth-bootstrap/cc/114-cc-func.fth:229`):

```forth file=cc/114-cc-func.fth

  lparen cc-expect-punct-c

  \ Capture any prior sk-func entry for this name BEFORE adding our own,
  \ so we can walk its forward-call fixup list and patch each call site.
  \ cc-sym-find returns the newest match; if a prototype was registered
  \ earlier (cc-register-fn-proto), that's what we get.  -1 means none.
  cc-fn-name-addr @ cc-fn-name-len @ cc-sym-find
  cc-fn-prior-sym-id !

  \ Register the function in the symbol table BEFORE pushing the per-function
  \ scope, so the entry survives cc-scope-pop at function-end and remains
  \ visible to subsequent function bodies.  Its vaddr is the address of the
  \ next byte we'll emit (the prologue's first byte, which we haven't emitted
  \ yet — but we will, immediately after the param list and the spill).
  cc-fn-name-addr @ cc-fn-name-len @
  sk-func
  ty-int [lit] 0 ty-make
  cc-here-vaddr                                   ( a u kind ty vaddr )
  cc-sym-add drop

```

Earlier references still belong to the prior prototype. Its call and address lists are patched to the new body address and cleared, so the final undefined-function check does not mistake resolved references for missing definitions (`forth-bootstrap/cc/114-cc-func.fth:250`):

```forth file=cc/114-cc-func.fth
  \ Patch any forward-call fixups registered against the prior prototype.
  \ The fixup list head lives in that entry's call-fixups cell.  After
  \ patching we zero the head so a repeat definition doesn't double-patch.
  \ Its addr-fixups cell holds a parallel list for `movabs rdi, imm64` rvalue
  \ sites (function-pointer references that appear before the definition).
  cc-fn-prior-sym-id @ [lit] 0 >= if,
    cc-fn-prior-sym-id @ cc-sym-kind-of sk-func = if,
      cc-fn-prior-sym-id @ cc-sym-call-fixups @
      cc-here-vaddr
      cc-walk-and-patch-to-vaddr
      [lit] 0 cc-fn-prior-sym-id @ cc-sym-call-fixups !
      cc-fn-prior-sym-id @ cc-sym-addr-fixups @
      cc-here-vaddr
      cc-walk-and-patch-imm64-to-vaddr
      [lit] 0 cc-fn-prior-sym-id @ cc-sym-addr-fixups !
    then,
  then,

```

### Entering and leaving the body

For `add`, the pending call from `main` is now resolved. Next we must make
`n` visible inside the body without letting it remain visible to the next
function. The function entry sits outside the new scope; the parameter
and body locals sit inside it. Closing that scope will remove `n` while
leaving `add` and the earlier global `bias` available.

A definition of `main` supplies the entry stub destination. The parser then resets local and control-flow state before pushing the scope that contains parameters and body declarations (`forth-bootstrap/cc/114-cc-func.fth:268`):

```forth file=cc/114-cc-func.fth
  \ If this is main, also record the vaddr for the entry-stub patch.
  cc-fn-name-addr @ cc-fn-name-len @ cc-is-main? if,
    cc-here-vaddr cc-main-vaddr !
  then,

  \ Reset locals; push scope (so params + body locals are popped together).
  [lit] 0 cc-fn-local-count !
  \ Reset per-function label table, break/continue stacks, switch depths.
  [lit] 0 cc-label-count !
  [lit] 0 cc-break-stack-head    !
  [lit] 0 cc-continue-stack-head !
  [lit] 0 cc-switch-depth        !
  [lit] 0 cc-loop-switch-depth   !
  cc-scope-push

```

With parameters registered, the parser reserves the frame and emits their spill before reading statements. The closing brace ends the body loop; an implicit zero return handles fall-through, and scope exit discards the function’s local names (`forth-bootstrap/cc/114-cc-func.fth:283`):

```forth file=cc/114-cc-func.fth
  \ Parameter list (consumes through ')').
  cc-parse-param-list

  [char] { cc-expect-punct-c

  \ Prologue.
  cc-frame-slots [lit] 8 * cc-emit-prologue

  \ Spill SYS-V argument registers into local slots 0..N-1.
  cc-emit-spill-params

  \ Body: stmt* until '}'.
  begin,
    cc-next-token-keep
    cc-block-end? 0=
  while,
    cc-putback-token
    cc-parse-stmt
  repeat,
  \ '}' was consumed by the loop test.

  \ Implicit return: if the body already ended with `return`, this is a few
  \ bytes of unreachable epilogue — harmless.  If it didn't, the function
  \ falls through to here and we need to terminate properly.
  cc-emit-xor-rax-rax                             \ rax := 0 (default return)
  cc-emit-epilogue

  cc-scope-pop ;
```

## Enums and typedefs

File-scope parsing produces more than function bodies: some declarations only introduce names. The program layer’s header places those declarations between runtime setup and final entry patching; `cc-enum-next-val` holds the next enumerator value (`forth-bootstrap/cc/116-cc-prog.fth:1`):

```forth file=cc/116-cc-prog.fth
\ 116-cc-prog.fth — file-scope forms and the top-level driver for the C-subset
\ compiler.
\
\ Parses enums, typedefs, prototypes, and global variables, skips the forms
\ it has no code for, and compiles a whole translation unit (cc-parse-program).
\
\ The compiled output begins with a 26-byte entry stub at vaddr 0x400078:
\     mov rdi, [rsp]   ; 48 8B 3C 24             (4 bytes, argc)
\     lea rsi, [rsp+8] ; 48 8D 74 24 08          (5 bytes, argv)
\     call <main>      ; E8 <rel32>             (5 bytes)
\     mov rdi, rax     ; 48 89 C7                (3 bytes)
\     mov rax, 60      ; 48 C7 C0 3C 00 00 00    (7 bytes)
\     syscall          ; 0F 05                    (2 bytes)
\
\ Then come the shims, declarations, and function bodies.  main returns its
\ value in rax (SYS-V); the stub moves it to rdi and exits.  The call's rel32
\ is patched after main's vaddr is known.
\
\ Depends on 114-cc-func.fth and everything it depends on.

\ ===========================================================================
\ Enum and typedef definitions (file-scope only).
\ ===========================================================================
\ Enum:  `enum [TAG] { NAME (= CONSTANT)?, NAME, ... };`
\ Typedef: `typedef BASE '*'* NAME ;`   (BASE = int / char / void / struct TAG)
\
\ Both register their introduced names in the symbol table so later code can
\ reference them via the standard cc-sym-find path.

variable cc-enum-next-val
```

An enum tag does not itself become a value. `cc-parse-enum-def` discards the optional tag, starts the value counter at zero, and saves each enumerator’s name before reading its initializer (`forth-bootstrap/cc/116-cc-prog.fth:37`):

```forth file=cc/116-cc-prog.fth

\ cc-parse-enum-def ( -- )  'enum' keyword has been consumed by the dispatcher.
\ Parses an optional tag, then `{ enumerator-list };`.
\ Each enumerator becomes an sk-enum entry whose val is the enumerator's
\ integer value (0-based by default, restart-from-N after `= N`, where N
\ is a constant expression, which may use the enumerators before it).
: cc-parse-enum-def
  \ Optional tag — discard.
  cc-next-token-keep
  tok-kind @ tk-ident = if,
    \ Tag IDENT — ignore.
  else,
    cc-putback-token
  then,

  [char] { cc-expect-punct-c

  [lit] 0 cc-enum-next-val !

  \ Enumerator loop.  Each pass ends with a continue (-1) / stop (0) flag.
  begin,
    cc-next-token-keep
    tok-kind @ tk-ident <> if,
      [lit] 190 cc-die
    then,
    tok-str-addr @ tok-str-len @                  ( a u )
```

An explicit constant replaces the pending enumerator value. Registering the name as `sk-enum` before advancing the counter lets later enumerators refer to earlier ones (`forth-bootstrap/cc/116-cc-prog.fth:57`):

```forth file=cc/116-cc-prog.fth

    \ Optional `= CONSTANT` (cc-parse-const).
    cc-next-token-keep
    tok-kind @ tk-punct = tok-num @ [char] = = and if,
      cc-parse-const cc-enum-next-val !
    else,
      cc-putback-token
    then,

    \ Add to symbol table as sk-enum.  ( a u kind type val )
    sk-enum
    [lit] 0                                       \ type unused
    cc-enum-next-val @                            \ val
    cc-sym-add drop

    [lit] 1 cc-enum-next-val +!

```

A trailing comma must not demand another identifier. The separator logic leaves the closing brace for the common terminator path and rejects other punctuation (`forth-bootstrap/cc/116-cc-prog.fth:74`):

```forth file=cc/116-cc-prog.fth
    \ Separator: ',' continues, '}' terminates.  A trailing ',' before '}'
    \ is allowed: peek the next token; if it's '}', stop.
    cc-next-token-keep
    tok-kind @ tk-punct = tok-num @ [char] , = and if,
      \ Peek to allow trailing comma.
      cc-next-token-keep
      tok-kind @ tk-punct = tok-num @ [char] } = and if,
        cc-putback-token                           \ leave '}' for the close
        [lit] 0                                    \ stop
      else,
        cc-putback-token                           \ not '}', let next iter read
        true                                       \ continue
      then,
    else,
      tok-kind @ tk-punct = tok-num @ [char] } = and if,
        cc-putback-token                           \ leave '}' for the close
        [lit] 0                                    \ stop
      else,
        [lit] 192 cc-die
      then,
    then,
    0=
  until,

  [char] } cc-expect-punct-c
  [char] ; cc-expect-punct-c ;

```

### Recording type aliases

A typedef stores an encoded type as its symbol payload and emits no target code. `cc-td-ty` carries the base through `cc-parse-typedef`; the keyword cases select that base before parsing the new name (`forth-bootstrap/cc/116-cc-prog.fth:110`):

```forth file=cc/116-cc-prog.fth
\ cc-parse-typedef ( -- )  'typedef' has been consumed by the dispatcher.
\ Grammar: typedef BASE '*'* NAME ';'
\ Supported bases: int / char / void / struct TAG / enum TAG / another
\ typedef.
\ Registers NAME as sk-typedef with val = encoded type word.
\
\ Uses cc-td-ty to stage the type so the data stack stays shallow across
\ keyword / pointer / IDENT parsing — easier than r-stack juggling.
variable cc-td-ty
: cc-parse-typedef
  cc-next-token-keep
  \ Parse base type into cc-td-ty.
  tok-kind @ tk-kw = if,
    tok-kw-id @ kw-int = if,
      ty-int [lit] 0 ty-make cc-td-ty !
    else, tok-kw-id @ kw-char = if,
      ty-char [lit] 0 ty-make cc-td-ty !
    else, tok-kw-id @ kw-void = if,
      ty-void [lit] 0 ty-make cc-td-ty !
    else, tok-kw-id @ kw-struct = if,
      cc-lookup-struct-tag drop
      ty-struct [lit] 0 ty-make cc-td-ty !
    else, tok-kw-id @ kw-enum = if,
      cc-skip-enum-tag
      ty-int [lit] 0 ty-make cc-td-ty !
    else,
      [lit] 193 cc-die
    then, then, then, then, then,
  else,
```

An alias can reuse a prior typedef. The identifier branch checks the symbol kind, copies its encoded type, and adds explicit pointer stars to the staged value (`forth-bootstrap/cc/116-cc-prog.fth:130`):

```forth file=cc/116-cc-prog.fth
    tok-kind @ tk-ident = if,
      tok-str-addr @ tok-str-len @ cc-sym-find
      dup 0< if,
        [lit] 194 cc-die
      then,
      dup cc-sym-kind-of sk-typedef <> if,
        [lit] 195 cc-die
      then,
      cc-sym-val-of cc-td-ty !
    else,
      [lit] 196 cc-die
    then,
  then,

  \ Add pointer stars onto whatever base we got.
  cc-count-stars                                   ( extra-stars )
  cc-td-ty @ +                                     ( final-ty )
  cc-td-ty !

```

A parenthesis after the base selects the function-pointer typedef form. This branch captures the pointer’s name before skipping its parameter signature; it does not retain a checked callable signature. The copied parse-through-only comment understates current behavior: a parameter declared through this alias retains the function-pointer base, and the core call path can call such a local indirectly. That is still different from checking its argument/result signature (`forth-bootstrap/cc/116-cc-prog.fth:149`):

```forth file=cc/116-cc-prog.fth
  \ Distinguish:
  \   typedef BASE *... NAME ';'                  (simple alias)
  \   typedef BASE (*NAME) ( params ) ';'         (function-pointer typedef)
  \ M2-Planet's gcc_req.h uses the fn-ptr form for `typedef void (*FUNCTION)(void);`.
  \ The return type and parameter types are parsed-and-discarded; NAME is
  \ registered as a pointer-to-function (ty-func, depth 1), matching how
  \ encodes inline `int (*op)(int)` locals — sufficient for parse-through
  \ without enabling actual indirect call via a typedef'd name yet.
  cc-next-token-keep
  tok-kind @ tk-punct = tok-num @ lparen = and if,
    \ '(' — function-pointer typedef.  Consume one or more '*'s, then IDENT,
    \ then ')'.  Then consume the parameter list parens (balanced).
    cc-count-stars drop                            \ at least one star expected
    cc-next-token-keep
    tok-kind @ tk-ident <> if,
      [lit] 197 cc-die
    then,
    tok-str-addr @ tok-str-len @                   ( a u )
    [char] ) cc-expect-punct-c
    lparen cc-expect-punct-c                       \ '(' of param list
```

Balanced parentheses delimit the skipped signature. The resulting alias records a pointer-to-function type; the plain-name branch instead records `cc-td-ty`, and both require a terminating semicolon (`forth-bootstrap/cc/116-cc-prog.fth:169`):

```forth file=cc/116-cc-prog.fth
    \ Skip tokens paren-balanced until matching ')'.  Depth starts at 1.
    [lit] 1
    begin,
      dup [lit] 0 >
    while,
      cc-next-token-keep
      tok-kind @ tk-punct = if,
        tok-num @ lparen = if, 1+ else,
        tok-num @ [char] ) = if, 1- else,
        then, then,
      then,
    repeat,
    drop                                           ( a u )
    sk-typedef [lit] 0                             ( a u kind type )
    ty-func [lit] 1 ty-make                        ( a u kind type val )
    cc-sym-add drop
  else,
    \ Plain IDENT (the new typedef name) — putback first since we just peeked.
    tok-kind @ tk-ident <> if,
      [lit] 198 cc-die
    then,
    tok-str-addr @ tok-str-len @                   ( a u )
    sk-typedef [lit] 0 cc-td-ty @                  ( a u kind type val )
    cc-sym-add drop
  then,

  [char] ; cc-expect-punct-c ;

```

The typedef signature loop above has no EOF branch. Given the truncated
input `typedef int (*F)(int`, it sees end of input at depth 1 on every
pass and never finishes, while the balanced declaration compiles normally.
The function-pointer parameter helper in Chapter 35 checks for EOF and
reports a diagnostic instead. [Appendix F](60-c-subset.md#observed-profile-boundaries)
lists this with the compiler's other known limits.

## Top-level elision

A declaration’s first type token cannot distinguish a variable, prototype, and function body. The classifier scans ahead to make that choice. The historical comment below predates global support: variables are parsed and allocated by the code that follows, rather than elided (`forth-bootstrap/cc/116-cc-prog.fth:197`):

```forth file=cc/116-cc-prog.fth
\ ---------------------------------------------------------------------------
\ Top-level forward-decl / file-scope-var elision.
\ ---------------------------------------------------------------------------
\ Our compiler only knows how to emit code for `int NAME(params) { body }`
\ function definitions.  When parsing real-world C headers we encounter a
\ profusion of other top-level forms:
\
\   void f(args);             /* forward fn decl, non-int return type */
\   char* f(args);            /* forward fn decl, pointer return type */
\   struct T* f(args);        /* forward fn decl, struct-ptr return type */
\   int f(args);              /* forward fn decl, int return type (no body) */
\   extern int g;             /* file-scope variable */
\   struct T* g_list;         /* file-scope variable */
\
\ None of these need to GENERATE anything in our target (the body is missing
\ for forward decls; file-scope vars aren't yet supported).  But they DO need
\ to PARSE without exploding so the headers can flow through.
\
\ Strategy: at top level, when we see a type-introducing keyword (int / char /
\ void / struct / typedef-name) that isn't a struct/enum/typedef DEFINITION,
\ cc-top-classify peeks ahead, paren-balanced, to the first ';' or '{' at
\ depth 0 and sorts the declaration into one of three classes:
\   - '{' first               → top-fndef: a function definition.
\   - ';' first, a '(' before → top-proto: a prototype; register the name.
\     (Only a '(' ahead of any '=' or '[' counts.)
\   - ';' first, no '('       → top-var: a file-scope variable.
\ The peek marks the lexer state in cc-peek-mark and resets to it, so the
\ parser that handles the class starts from the declaration's first token.

```

`top-var`, `top-proto`, and `top-fndef` name the possible outcomes. `cc-top-depth` tracks parentheses; `cc-top-var-seen` remembers an initializer or array declarator so its parentheses cannot turn a variable into a prototype (`forth-bootstrap/cc/116-cc-prog.fth:226`):

```forth file=cc/116-cc-prog.fth
[lit] 0 constant top-var
[lit] 1 constant top-proto
[lit] 2 constant top-fndef

variable cc-top-depth                             \ paren depth while scanning
variable cc-top-var-seen                          \ an '=' or '[' came first

\ cc-top-classify ( -- class )  Scan forward to the first ';' or '{' at paren
\ depth 0 (or EOF), noting whether a '(' came first — before any '=' or
\ '[' at depth 0, since `int x = (1);` and `int a[(2)];` are variables.
\ Always restores the lexer state; each of the three exits resets it, then
\ returns the class.
: cc-top-classify
  cc-peek-mark cc-lex-mark
  [lit] 0 cc-top-depth !
  [lit] 0 cc-top-var-seen !
  top-var                                         ( class )
  begin,
    cc-next-token-keep
    tok-kind @ tk-eof = if,
      cc-peek-mark cc-lex-reset exit,             \ EOF: no body
    then,
    tok-kind @ tk-punct = if,
      cc-top-depth @ [lit] 0 = if,
        tok-num @ [char] = =  tok-num @ [char] [ = or if,
          true cc-top-var-seen !
        then,
      then,
```

An opening parenthesis suggests a prototype only before a variable marker. A top-level brace selects a definition; a semicolon ends the classification. Every exit restores the lexer state so the chosen parser starts at the original token (`forth-bootstrap/cc/116-cc-prog.fth:254`):

```forth file=cc/116-cc-prog.fth
      tok-num @ lparen = if,
        cc-top-var-seen @ 0= if,
          drop top-proto                          \ a '(' before the end
        then,
        [lit] 1 cc-top-depth +!
      then,
      tok-num @ [char] ) = if, [lit] 1 cc-top-depth -! then,
      cc-top-depth @ [lit] 0 = if,
        tok-num @ [char] ; = if,
          cc-peek-mark cc-lex-reset exit,         \ ';' first: a declaration
        then,
        tok-num @ [char] { = if,
          drop top-fndef
          cc-peek-mark cc-lex-reset exit,         \ '{' first: a definition
        then,
      then,
    then,
  again, ;

```

### Keeping prototypes useful

A prototype contributes a name without a body. `cc-top-skip-to-semi` consumes the remaining signature with balanced parentheses, stopping at its semicolon or end of input (`forth-bootstrap/cc/116-cc-prog.fth:277`):

```forth file=cc/116-cc-prog.fth
\ cc-top-skip-to-semi ( -- )
\ Consume tokens through and including the next top-level ';'.  Paren-balanced
\ so commas / parens inside parameter lists don't fool us.  If we run into
\ EOF first, we exit cleanly so the outer loop also exits.
: cc-top-skip-to-semi
  [lit] 0 cc-top-depth !
  begin,
    cc-next-token-keep
    tok-kind @ tk-eof = if, exit, then,
    tok-kind @ tk-punct = if,
      tok-num @ lparen = if, [lit] 1 cc-top-depth +! then,
      tok-num @ [char] ) = if, [lit] 1 cc-top-depth -! then,
      tok-num @ [char] ; =  cc-top-depth @ [lit] 0 =  and if, exit, then,
    then,
  again, ;

```

Re-registering a prototype after its definition would hide the body behind an unresolved entry. `cc-register-fn-proto` first extracts the name, then checks whether it already denotes a function (`forth-bootstrap/cc/116-cc-prog.fth:304`):

```forth file=cc/116-cc-prog.fth
\ cc-register-fn-proto ( -- )  Parse `T '*'* NAME (...);` and register NAME
\ as sk-func with vaddr=0 so call sites resolve.  When the actual definition
\ is later parsed, cc-parse-function adds a newer sk-func entry; cc-sym-find
\ (newest-first) returns the definition for backward calls.  Forward calls
\ (call to fn before its def) are patched through the symbol's fixup list.
\ Caller has put-back the first token of the prototype.  Consumes through ';'.
\
\ Idempotency: real-world headers often re-declare the same prototype across
\ TUs (e.g. M2-Planet has `struct token_list* read_all_tokens(...)` in both
\ cc_macro.c and cc.c, with the definition in cc_reader.c sandwiched in
\ between).  Concatenated into our monolith the post-definition prototype
\ would register a new sk-func with val=0, and because cc-sym-find returns
\ the newest match, every later call site emits a forward-call placeholder
\ against a stale entry whose fixups are never patched.  Skip the re-add if
\ the name is already an sk-func.
: cc-register-fn-proto
  cc-parse-fn-return-type
  cc-next-token-keep
  tok-kind @ tk-ident <> if,
    [lit] 199 cc-die
  then,
  tok-str-addr @ tok-str-len @                    ( a u )
```

An existing function entry is kept intact. Only a new name, or a name whose current symbol has another kind, receives an unresolved `sk-func`; all paths consume the remainder of the declaration (`forth-bootstrap/cc/116-cc-prog.fth:311`):

```forth file=cc/116-cc-prog.fth
  2dup cc-sym-find                                ( a u id-or-neg1 )
  dup [lit] 0 >= if,
    cc-sym-kind-of sk-func = if,
      \ Already registered as a function — drop the leftover ( a u ).
      2drop
      cc-top-skip-to-semi
    else,
      sk-func ty-int [lit] 0 ty-make [lit] 0      ( a u kind ty val=0 )
      cc-sym-add drop
      cc-top-skip-to-semi
    then,
  else,
    drop                                          ( a u )
    sk-func ty-int [lit] 0 ty-make [lit] 0        ( a u kind ty val=0 )
    cc-sym-add drop
    cc-top-skip-to-semi
  then, ;

```

## File-scope globals

A global declaration has a shared base type and a separate declarator for each name. Scalars reserve initialized data storage; arrays reserve BSS storage. Repeated scalar declarations must reuse the same slot so earlier compiled accesses see a later initializer (`forth-bootstrap/cc/116-cc-prog.fth:329`):

```forth file=cc/116-cc-prog.fth
\ ===========================================================================
\ File-scope global variable declaration.
\ ===========================================================================
\ Parses ONE top-level declaration: a base type, then one or more
\ declarators separated by ',', then ';'.  A declarator is
\
\    '*'* name                      a scalar
\    '*'* name '=' CONSTANT         a scalar with an initializer
\    '*'* name '[' SIZE ']'         an array
\
\ where the base type is int/char/void/long/short/etc., `struct TAG`,
\ `enum TAG` or a typedef-name, and SIZE and CONSTANT are constant
\ expressions (cc-parse-const).  The base type is consumed by the caller
\ (cc-parse-function-list) — when we get here the lookahead has been put
\ back so cc-next-token-keep yields the type keyword again.
\
\ A scalar takes a data slot (8 bytes — a struct VALUE gets its full
\ descriptor size rounded up to 8), and its initializer is written into
\ the data area so the runtime image already contains the value.  An array
\ takes N*8 bytes of the bss.  A second declaration of a global that
\ already exists — `extern int g;` early on, `int g = 3;` later — names
\ the same slot, so both see one variable and the initializer lands in
\ it.  Function-pointer, aggregate, and struct initializers are not
\ implemented.
\
\ Errors die through cc-die with codes 202..205 (Appendix G).

```

The staging variables keep the base in `cc-gdecl-base`, the name slice in `cc-gdecl-name-a`/`cc-gdecl-name-u`, the slot in `cc-gdecl-slot`, the descriptor in `cc-gdecl-desc`, and pointer depth in `cc-gdecl-ptr-depth`. `cc-gdecl-scalar-bytes` reserves a full rounded descriptor size for a struct value; allocating only a scalar slot would let later fields overwrite the next global (`forth-bootstrap/cc/116-cc-prog.fth:369`):

```forth file=cc/116-cc-prog.fth
variable cc-gdecl-base
variable cc-gdecl-name-a
variable cc-gdecl-name-u
variable cc-gdecl-slot
variable cc-gdecl-desc
variable cc-gdecl-ptr-depth

\ cc-gdecl-scalar-bytes ( -- n )  Byte size of one non-array global slot.
\ A struct VALUE (ty-struct base, zero pointer depth, descriptor known)
\ needs its full descriptor size, rounded up to a multiple of 8 — a flat 8
\ would let stores past the first field clobber the next global.  Everything
\ else — ints, chars, pointers, struct pointers, opaque struct refs — is one
\ 8-byte slot.
: cc-gdecl-scalar-bytes                           ( -- n )
  cc-gdecl-base @ ty-struct =
  cc-gdecl-ptr-depth @ [lit] 0 = and
  cc-gdecl-desc @ [lit] 0 <> and if,
    cc-gdecl-desc @ cc-sd-total-size [lit] 7 + [lit] 8 / [lit] 8 *
  else,
    [lit] 8
  then, ;

```

Registration and reuse answer different questions. `cc-gdecl-add` creates an `sk-global` with the staged type and slot; `cc-gdecl-declared` returns an existing global ID or a negative result (`forth-bootstrap/cc/116-cc-prog.fth:378`):

```forth file=cc/116-cc-prog.fth
\ cc-gdecl-add ( -- id )  Register the declarator's name as an sk-global
\ in cc-gdecl-slot.
: cc-gdecl-add
  cc-gdecl-name-a @ cc-gdecl-name-u @               ( a u )
  sk-global                                          ( a u kind )
  cc-gdecl-base @ cc-gdecl-ptr-depth @ ty-make      ( a u kind type )
  cc-gdecl-slot @                                    ( a u kind type val )
  cc-sym-add ;

\ cc-gdecl-declared ( -- id | -1 )  The global this name already is, if
\ it is one.
: cc-gdecl-declared
  cc-gdecl-name-a @ cc-gdecl-name-u @ cc-sym-find
  dup 0< 0= if,
    dup cc-sym-kind-of sk-global <> if, drop true then,
  then, ;

```

An array declarator needs its bound before storage can be reserved. `cc-gdecl-declarator` saves the name, evaluates the bound, allocates BSS space, and records the element count on the symbol (`forth-bootstrap/cc/116-cc-prog.fth:397`):

```forth file=cc/116-cc-prog.fth
\ cc-gdecl-declarator ( -- )  One declarator; ends with the token after it
\ read (the caller wants ',' or ';').
: cc-gdecl-declarator
  cc-count-stars cc-gdecl-ptr-depth !
  cc-next-token-keep
  tok-kind @ tk-ident <> if,
    [lit] 203 cc-die
  then,
  tok-str-addr @ cc-gdecl-name-a !
  tok-str-len  @ cc-gdecl-name-u !
  cc-next-token-keep
  [char] [ cc-tok-punct? if,
    \ Array form: 'T name [ N ]', in the bss.  The symbol records the
    \ element count as its array length, so codegen can tell array decay
    \ from scalar deref.
    cc-parse-const                                   ( n )
    [char] ] cc-expect-punct-c
    dup [lit] 8 * cc-bss-alloc cc-gdecl-slot !
    cc-gdecl-add cc-sym-set-array-len
    cc-next-token-keep exit,
  then,
```

A scalar declarator first asks whether its slot already exists. New storage uses the computed size; an existing symbol supplies its old slot. An initializer writes the constant into that chosen slot (`forth-bootstrap/cc/116-cc-prog.fth:416`):

```forth file=cc/116-cc-prog.fth
  \ Scalar: a new data slot, or the one an earlier declaration made.
  cc-gdecl-declared dup 0< if,
    drop
    cc-gdecl-scalar-bytes cc-globals-alloc cc-gdecl-slot !
    cc-gdecl-desc @ cc-gdecl-add cc-sym-set-struct-desc
  else,
    cc-sym-val-of cc-gdecl-slot !
  then,
  [char] = cc-tok-punct? if,
    cc-parse-const cc-gdecl-slot @ cc-globals-store-8le
    cc-next-token-keep
  then, ;

```

### Choosing a global’s base type

`cc-parse-global-decl` starts with integer storage and no descriptor. A struct base uses soft tag lookup, allowing a pointer to an opaque struct whose definition is absent (`forth-bootstrap/cc/116-cc-prog.fth:432`):

```forth file=cc/116-cc-prog.fth
\ cc-parse-global-decl ( -- )  Caller has already done cc-skip-storage-quals;
\ the next token is the base-type keyword OR a typedef-name IDENT.  Consumes
\ through ';'.
: cc-parse-global-decl                            ( -- )
  [lit] 0 cc-gdecl-desc !
  ty-int cc-gdecl-base !
  \ Read base type.
  cc-next-token-keep
  tok-kind @ tk-kw = if,
    tok-kw-id @ kw-struct = if,
      \ Support struct TAG as base type.  Soft lookup: descriptor pointer
      \ if the struct is defined, 0 otherwise.  cc_globals.c declares
      \ `struct type* foo;` without a `struct type {...}` in scope — that's
      \ an opaque-pointer pattern we still need to parse.
      ty-struct cc-gdecl-base !
      cc-lookup-struct-tag-soft cc-gdecl-desc !
    else,
```

The keyword path keeps `char` distinct for pointer indexing. Enum tags and further basic type keywords are consumed before the declarators (`forth-bootstrap/cc/116-cc-prog.fth:446`):

```forth file=cc/116-cc-prog.fth
      \ Distinguish `char` from other primitives so `char* foo;` records
      \ ty-char in the symbol table.  Without this, `char* hold_string;`
      \ looks identical to `int* foo;` and the array-index path uses qword
      \ stride/load on its bytes — corrupting tokenizer scratch buffers in
      \ M2-Planet's preprocessor.  int/void/long/short/enum TAG all
      \ collapse to ty-int (storage is 8 bytes regardless; only the
      \ byte-stride dispatch cares).
      tok-kw-id @ kw-char = if, ty-char cc-gdecl-base ! then,
      tok-kw-id @ kw-enum = if, cc-skip-enum-tag then,
      cc-tok-is-basic-type-kw? if,
        cc-gdecl-base @ cc-more-type-kws cc-gdecl-base !
      then,
    then,
  else,
```

The identifier path merely accepts a type-like name and retains the default integer base; unlike parameter parsing, it does not unpack an arbitrary typedef’s encoded type. The declarator loop then handles each comma-separated name (`forth-bootstrap/cc/116-cc-prog.fth:460`):

```forth file=cc/116-cc-prog.fth
    \ Typedef-name IDENT (FILE, uint8_t, ...).  We don't need to verify it
    \ actually resolves to a known typedef — the caller already determined
    \ this is a declaration via cc-top-classify.
    tok-kind @ tk-ident <> if,
      [lit] 202 cc-die
    then,
  then,
  cc-skip-qualifiers
  begin,
    cc-gdecl-declarator
    [char] , cc-tok-punct?
  while,
  repeat,
  [char] ; cc-tok-punct? 0= if,
    [lit] 205 cc-die
  then, ;

```

### Placing data after code

Global addresses become final only after all function and shim bytes exist. `cc-finalize-globals` appends initialized data, aligns the BSS start when needed, and reports the BSS extent to ELF finalization (`forth-bootstrap/cc/116-cc-prog.fth:489`):

```forth file=cc/116-cc-prog.fth
\ cc-finalize-globals ( -- )  After the entire program has been parsed and
\ all functions emitted, append cc-globals-buf to cc-out-buf, place the bss
\ after it, and patch every recorded fixup to point at the now-known global
\ vaddrs.
\
\ cc-globals-base-vaddr is set to cc-base-vaddr + (cc-out-pos at the moment
\ globals are appended).  The bss starts at the next 8-aligned vaddr (the
\ file is padded with zeros to reach it), and cc-bss-size tells
\ cc-finalize-elf how much memory it adds.  Then each fixup's imm64
\ placeholder is overwritten with the slot's vaddr: cc-globals-base-vaddr
\ + slot for a data slot, cc-bss-base-vaddr + (slot - cc-bss-flag) for a
\ bss one.
: cc-finalize-globals
  cc-here-vaddr cc-globals-base-vaddr !
  \ Append cc-globals-pos bytes from cc-globals-buf to cc-out-buf.
  [lit] 0
  begin, dup cc-globals-pos @ < while,
    dup cc-globals-buf + c@ cc-emit-byte
    1+
  repeat, drop
  \ Align the bss, if there is one.
  cc-bss-pos @ if,
    begin, cc-out-pos @ [lit] 7 and while, [lit] 0 cc-emit-byte repeat,
  then,
  cc-here-vaddr cc-bss-base-vaddr !
  cc-bss-pos @ cc-bss-size !
```

The fixup walk selects the data base or BSS base from the slot encoding. Each absolute address replaces its recorded output placeholder, so an earlier access to `bias` reaches the data appended after the functions (`forth-bootstrap/cc/116-cc-prog.fth:503`):

```forth file=cc/116-cc-prog.fth
  \ Patch each fixup.  i walks 0..cc-gfixup-count-1.
  [lit] 0
  begin, dup cc-gfixup-count @ < while,
    dup cc-gfixup-slot     cell[] @                \ slot
    dup cc-bss-flag < if,
      cc-globals-base-vaddr @ +                     \ vaddr = base + slot
    else,
      cc-bss-flag - cc-bss-base-vaddr @ +           \ vaddr = bss base + offset
    then,
    over cc-gfixup-out-pos cell[] @                \ patch-offset
    cc-out-patch-8le
    1+
  repeat, drop ;

```

### Selecting each file-scope form

Definitions need priority over declarations that merely use a tag. These lookaheads leave token state intact for the selected parser.

| Input → result |
|---|
| `struct TAG {` → `cc-struct-def-ahead?` succeeds |
| `enum {` or `enum TAG {` → `cc-enum-def-ahead?` succeeds |
| Other type use → `cc-top-classify` chooses the declaration parser |

The distinction depends on the tokens after the keyword, not on the keyword alone (`forth-bootstrap/cc/116-cc-prog.fth:517`):

```forth file=cc/116-cc-prog.fth
\ cc-struct-def-ahead? ( -- f )  The current token is `struct`.  True iff
\ the next two are TAG '{' — a struct definition, not a declaration that
\ uses the type.  Restores the lexer state.
: cc-struct-def-ahead?
  cc-peek-mark cc-lex-mark
  cc-next-token                                   \ the tag IDENT
  cc-next-token                                   \ what follows it
  tok-kind @ tk-punct = tok-num @ [char] { = and
  cc-peek-mark cc-lex-reset ;

\ cc-enum-def-ahead? ( -- f )  The current token is `enum`.  True iff an
\ enumerator list follows: '{', or TAG '{'.  Otherwise the enum only names
\ a type (`enum BINDING f(...)`).  Restores the lexer state.
: cc-enum-def-ahead?
  cc-peek-mark cc-lex-mark
  cc-next-token
  tok-kind @ tk-ident = if, cc-next-token then,
  tok-kind @ tk-punct = tok-num @ [char] { = and
  cc-peek-mark cc-lex-reset ;

```

`cc-parse-top-decl` sends enum, typedef, and struct definitions to their own parsers first. Remaining forms go through classification and then the function, prototype, or global parser (`forth-bootstrap/cc/116-cc-prog.fth:543`):

```forth file=cc/116-cc-prog.fth
\ cc-parse-top-decl ( -- )  The current token starts a top-level item.
\ Definitions of a struct, enum or typedef have their own parsers; anything
\ else is a function definition, a prototype or a file-scope variable, and
\ cc-top-classify says which.  A `struct TAG` that isn't followed by '{'
\ (`struct TAG* f(...)`, `struct TAG* g;`) is one of those three, and so
\ is an `enum TAG` without an enumerator list.
: cc-parse-top-decl
  tok-kind @ tk-kw = if,
    tok-kw-id @ kw-enum    = if,
      cc-enum-def-ahead? if, cc-parse-enum-def exit, then,
    then,
    tok-kw-id @ kw-typedef = if, cc-parse-typedef  exit, then,
    tok-kw-id @ kw-struct  = if,
      cc-struct-def-ahead? if, cc-parse-struct-def exit, then,
    then,
  then,
  \ int/char/void/struct T/typedef-name: put the type back for the parser.
  cc-putback-token
  cc-top-classify
  dup top-fndef = if, drop cc-parse-function     exit, then,
      top-proto = if,      cc-register-fn-proto  exit, then,
  cc-parse-global-decl ;

```

Despite its name, `cc-parse-function-list` consumes every supported file-scope form. It skips storage qualifiers, stops at end of input, and otherwise asks the dispatcher to consume the next item (`forth-bootstrap/cc/116-cc-prog.fth:562`):

```forth file=cc/116-cc-prog.fth
\ cc-parse-function-list ( -- )  Loop over top-level declarations until EOF.
\ See the long comment above for the elision rules.
: cc-parse-function-list
  begin,
    cc-skip-storage-quals
    cc-next-token-keep
    tok-kind @ tk-eof = 0=
  while,
    cc-parse-top-decl
  repeat, ;

```

## The entry stub and the top-level driver

Linux enters the executable before any C function has run. `cc-emit-entry-stub` obtains `argc` and `argv` from the initial stack and prepares the call to `main`; its destination will be supplied after parsing (`forth-bootstrap/cc/116-cc-prog.fth:585`):

```forth file=cc/116-cc-prog.fth
\ ===========================================================================
\ Entry-stub emission and rel32 patching.
\ ===========================================================================

\ cc-emit-entry-stub ( -- )  Emit at vaddr cc-entry-vaddr (0x400078):
\     mov  rdi, [rsp]      48 8B 3C 24      ; argc (kernel puts it at [rsp])
\     lea  rsi, [rsp+8]    48 8D 74 24 08   ; argv = &argv[0]
\     call <main>          E8 <rel32>
\     mov  rdi, rax        48 89 C7         ; main's return -> exit code
\     mov  rax, 60         48 C7 C0 3C 00 00 00
\     syscall              0F 05
\ Records the file-offset of the rel32 in cc-call-main-patch.
\ Stack alignment: kernel hands us rsp 16-aligned and we don't touch it before
\ `call`, so main enters 8-mod-16 as SysV requires.
: cc-emit-entry-stub
  \ mov rdi, [rsp]   — argc
  [lit]  72 cc-emit-byte
  [lit] 139 cc-emit-byte
  [lit]  60 cc-emit-byte
  [lit]  36 cc-emit-byte

  \ lea rsi, [rsp+8] — argv
  [lit]  72 cc-emit-byte
  [lit] 141 cc-emit-byte
  [lit] 116 cc-emit-byte
  [lit]  36 cc-emit-byte
  [lit]   8 cc-emit-byte

```

The stub keeps the call displacement’s file offset in `cc-call-main-patch`, then turns `main`’s return value into the process exit status. `cc-patch-call-main` fills that saved displacement after the definition has set `cc-main-vaddr` (`forth-bootstrap/cc/116-cc-prog.fth:618`):

```forth file=cc/116-cc-prog.fth
  [lit] 232 cc-emit-byte                          \ E8
  cc-out-pos @ cc-call-main-patch !               \ remember rel32 file-offset
  [lit] 0 cc-emit-4le                             \ rel32 placeholder

  [lit]  72 cc-emit-byte
  [lit] 137 cc-emit-byte
  [lit] 199 cc-emit-byte                          \ mov rdi, rax

  [lit]  72 cc-emit-byte
  [lit] 199 cc-emit-byte
  [lit] 192 cc-emit-byte
  [lit]  60 cc-emit-4le                           \ mov rax, 60

  [lit]  15 cc-emit-byte
  [lit]   5 cc-emit-byte ;                        \ syscall

\ cc-patch-call-main ( -- )  Compute and store the call's rel32.
\ rel32 = main_vaddr - vaddr_of_next_instr
\       = main_vaddr - (cc-base-vaddr + cc-call-main-patch + 4)
: cc-patch-call-main
  cc-main-vaddr @
  cc-base-vaddr cc-call-main-patch @ + [lit] 4 + -
  cc-call-main-patch @
  cc-out-patch-4le ;

```

### Registering the built-in shims

Calls to built-ins should use ordinary function lookup. The `cc-name-*` byte strings supply spellings for symbol registration; this first group names the eagerly emitted routines and the external `memset` prototype (`forth-bootstrap/cc/116-cc-prog.fth:624`):

```forth file=cc/116-cc-prog.fth
\ ===========================================================================
\ Top-level driver
\ ===========================================================================

\ ===========================================================================
\ Built-in libc shim emission + symtab registration.
\ ===========================================================================
\ The shims (putchar, exit, getchar) live at the very start of the code
\ segment, immediately after the 26-byte entry stub.  Registering them in
\ the symbol table BEFORE parsing user functions means cc-parse-call's
\ name-lookup path finds them just like any user-defined function.

\ Pre-baked name strings (raw bytes, no length prefix; the length is supplied
\ explicitly to cc-sym-add).
create cc-name-putchar  s, putchar
create cc-name-exit     s, exit
create cc-name-getchar  s, getchar
create cc-name-fputs    s, fputs
create cc-name-fopen    s, fopen
create cc-name-fclose   s, fclose
create cc-name-fputc    s, fputc
create cc-name-fread    s, fread
create cc-name-fwrite   s, fwrite
create cc-name-calloc   s, calloc
create cc-name-memset   s, memset
create cc-name-free     s, free
```

The remaining names identify routines eligible for late emission. `cc-emit-shims` demonstrates the eager rule with `putchar`: register the current address, then emit the body at that address (`forth-bootstrap/cc/116-cc-prog.fth:661`):

```forth file=cc/116-cc-prog.fth
create cc-name-open     s, open
create cc-name-read     s, read
create cc-name-write    s, write
create cc-name-close    s, close
create cc-name-malloc   s, malloc
create cc-name-strlen   s, strlen
create cc-name-memcpy   s, memcpy
create cc-name-strrchr  s, strrchr

\ cc-emit-shims ( -- )  Emit each shim's body and register it in the symbol
\ table as sk-func with val = its absolute vaddr.
: cc-emit-shims
  \ putchar
  cc-name-putchar [lit] 7
  sk-func
  ty-int [lit] 0 ty-make
  cc-here-vaddr                                   ( a u kind ty vaddr )
  cc-sym-add drop
  cc-emit-putchar-shim

```

The rest of the eager registrations use the same sequence. Their result types are the core compiler’s symbol types, not a complete libc interface.

| Input name → registered result type |
|---|
| `exit`, `free` → `ty-void` |
| `getchar`, `fputs`, `fputc` → `ty-int` |
| `fopen`, `fclose`, `fwrite`, `fread`, `calloc` → `ty-int` |

The exit and character-output registrations reuse the eager sequence (`forth-bootstrap/cc/116-cc-prog.fth:670`):

```forth file=cc/116-cc-prog.fth
  \ exit
  cc-name-exit [lit] 4
  sk-func
  ty-void [lit] 0 ty-make
  cc-here-vaddr
  cc-sym-add drop
  cc-emit-exit-shim

  \ getchar
  cc-name-getchar [lit] 7
  sk-func
  ty-int [lit] 0 ty-make
  cc-here-vaddr
  cc-sym-add drop
  cc-emit-getchar-shim

  \ fputs
  cc-name-fputs [lit] 5
  sk-func ty-int [lit] 0 ty-make
  cc-here-vaddr
  cc-sym-add drop
  cc-emit-fputs-shim

  \ fputc
  cc-name-fputc [lit] 5
  sk-func ty-int [lit] 0 ty-make
  cc-here-vaddr
  cc-sym-add drop
  cc-emit-fputc-shim
```

The stream registrations likewise publish each address immediately before its body (`forth-bootstrap/cc/116-cc-prog.fth:699`):

```forth file=cc/116-cc-prog.fth

  \ fopen
  cc-name-fopen [lit] 5
  sk-func ty-int [lit] 0 ty-make
  cc-here-vaddr
  cc-sym-add drop
  cc-emit-fopen-shim

  \ fclose
  cc-name-fclose [lit] 6
  sk-func ty-int [lit] 0 ty-make
  cc-here-vaddr
  cc-sym-add drop
  cc-emit-fclose-shim

  \ fwrite
  cc-name-fwrite [lit] 6
  sk-func ty-int [lit] 0 ty-make
  cc-here-vaddr
  cc-sym-add drop
  cc-emit-fwrite-shim

  \ fread
  cc-name-fread [lit] 5
  sk-func ty-int [lit] 0 ty-make
  cc-here-vaddr
  cc-sym-add drop
  cc-emit-fread-shim
```

The allocator registrations complete the eager group; `free` uses the existing no-op emitter (`forth-bootstrap/cc/116-cc-prog.fth:727`):

```forth file=cc/116-cc-prog.fth

  \ calloc
  cc-name-calloc [lit] 6
  sk-func ty-int [lit] 0 ty-make
  cc-here-vaddr
  cc-sym-add drop
  cc-emit-calloc-shim

  \ free (no-op bump allocator)
  cc-name-free [lit] 4
  sk-func ty-void [lit] 0 ty-make
  cc-here-vaddr
  cc-sym-add drop
  cc-emit-free-shim ;

```

### Emitting a shim only when referenced

A late shim initially looks like an unresolved prototype. A user definition can satisfy its references before the fallback body is needed.

| Requested body → emitter |
|---|
| `open`, `read`, `write`, `close` → corresponding `cc-emit-*-shim` syscall wrapper |
| `malloc` → `cc-emit-malloc-late`, using the registered `calloc` address |
| `strlen`, `memcpy`, `strrchr` → their existing emitters |

The small wrappers adapt those requests to the existing syscall and allocation emitters (`forth-bootstrap/cc/116-cc-prog.fth:742`):

```forth file=cc/116-cc-prog.fth
\ ===========================================================================
\ Shims emitted only when used: malloc, open, read, write, close, strlen,
\ memcpy, strrchr.
\ ===========================================================================
\ These are registered like prototypes (sk-func, vaddr 0) before the
\ program is parsed, so a call to one is a forward call whose fixup waits
\ on the symbol (cc-parse-call).  If the program defines the function
\ itself, its definition takes the fixups as for any prototype.  After the
\ program, cc-emit-late-shims emits the body of each one still waiting and
\ patches its callers, so a program that uses none of them is not a byte
\ longer.
\
\ One row per shim: name, name length, emitter xt, and the symbol id
\ (filled in by cc-register-late-shims).  A 0 name ends the table.

: cc-emit-open-shim   [lit] 2 cc-emit-syscall-shim ;
: cc-emit-read-shim   [lit] 0 cc-emit-syscall-shim ;
: cc-emit-write-shim  [lit] 1 cc-emit-syscall-shim ;
: cc-emit-close-shim  [lit] 3 cc-emit-syscall-shim ;
\ malloc jumps into the calloc shim, the first sk-func named calloc.
: cc-emit-malloc-late
  cc-name-calloc [lit] 6 cc-sym-find cc-sym-val-of cc-emit-malloc-shim ;

```

`cc-late-shims` associates each spelling with an emitter and a symbol-id field. `cc-register-late-shims` creates unresolved function entries and fills those id fields so the later pass can find their references (`forth-bootstrap/cc/116-cc-prog.fth:777`):

```forth file=cc/116-cc-prog.fth
create cc-late-shims
cc-name-malloc  , [lit] 6 , ' cc-emit-malloc-late  , [lit] 0 ,
cc-name-open    , [lit] 4 , ' cc-emit-open-shim    , [lit] 0 ,
cc-name-read    , [lit] 4 , ' cc-emit-read-shim    , [lit] 0 ,
cc-name-write   , [lit] 5 , ' cc-emit-write-shim   , [lit] 0 ,
cc-name-close   , [lit] 5 , ' cc-emit-close-shim   , [lit] 0 ,
cc-name-strlen  , [lit] 6 , ' cc-emit-strlen-shim  , [lit] 0 ,
cc-name-memcpy  , [lit] 6 , ' cc-emit-memcpy-shim  , [lit] 0 ,
cc-name-strrchr , [lit] 7 , ' cc-emit-strrchr-shim , [lit] 0 ,
[lit] 0 ,

\ cc-register-late-shims ( -- )  Add each as a prototype; keep its id.
: cc-register-late-shims
  cc-late-shims
  begin, dup @ while,
    dup @  over [lit] 8 + @                       ( row a u )
    sk-func ty-int [lit] 0 ty-make [lit] 0 cc-sym-add
    over [lit] 24 + !
    [lit] 32 +
  repeat,
  drop ;

```

Pending calls or address loads make a late shim necessary. `cc-emit-late-shims` assigns its address, resolves both lists, clears them, and invokes its emitter; an entry with no pending references contributes no body (`forth-bootstrap/cc/116-cc-prog.fth:789`):

```forth file=cc/116-cc-prog.fth
\ cc-emit-late-shims ( -- )  Emit each shim that has callers still waiting,
\ and point them at it.
: cc-emit-late-shims
  cc-late-shims
  begin, dup @ while,
    dup [lit] 24 + @                               ( row id )
    dup cc-sym-call-fixups @  over cc-sym-addr-fixups @  or if,
      cc-here-vaddr over cc-sym-val cell[] !
      dup cc-sym-call-fixups @ cc-here-vaddr cc-walk-and-patch-to-vaddr
      dup cc-sym-addr-fixups @ cc-here-vaddr cc-walk-and-patch-imm64-to-vaddr
      [lit] 0 over cc-sym-call-fixups !
      [lit] 0 over cc-sym-addr-fixups !
      over [lit] 16 + @ execute
    then,
    drop
    [lit] 32 +
  repeat,
  drop ;

```

### Names without emitted bodies

`cc-emit-external-protos` registers `memset` without supplying an implementation. The following `cc-name-*` constants spell `FILE`, the fixed-width integer names, `size_t`, `ssize_t`, and `intptr_t` for built-in typedef registration (`forth-bootstrap/cc/116-cc-prog.fth:812`):

```forth file=cc/116-cc-prog.fth
\ ===========================================================================
\ M2 test-suite external prototype.  The M2 monolith itself does not call
\ memset, but the published parity script compares selected upstream tests
\ where memset is declared by an elided system header.
\ ===========================================================================

: cc-emit-external-protos
  cc-name-memset  [lit] 6  sk-func ty-int [lit] 0 ty-make  [lit] 0 cc-sym-add drop ;

\ Built-in typedefs for opaque libc/stdint names.  All map to ty-int so the
\ parser will accept `FILE* p;`, `uint8_t x;`, etc. — codegen still treats
\ them as 8-byte slots regardless of the C-visible width.
create cc-name-FILE      s, FILE
create cc-name-int8_t    s, int8_t
create cc-name-int16_t   s, int16_t
create cc-name-int32_t   s, int32_t
create cc-name-int64_t   s, int64_t
create cc-name-uint8_t   s, uint8_t
create cc-name-uint16_t  s, uint16_t
create cc-name-uint32_t  s, uint32_t
create cc-name-uint64_t  s, uint64_t
create cc-name-size_t    s, size_t
create cc-name-ssize_t   s, ssize_t
create cc-name-intptr_t  s, intptr_t

```

`cc-emit-libc-typedefs` maps every listed alias to the core integer type, including `FILE`. These names let declarations parse; they do not promise the C widths suggested by their spelling. Chapter 39 supplies native storage rules (`forth-bootstrap/cc/116-cc-prog.fth:834`):

```forth file=cc/116-cc-prog.fth
\ cc-emit-libc-typedefs ( -- )  Register the typedef names above so headers
\ that say `FILE* fp;` or `uint8_t b;` parse as types.  All map to ty-int
\ encoded as the sk-typedef's val field (matching cc-parse-typedef's layout).
: cc-emit-libc-typedefs
  cc-name-FILE     [lit] 4  sk-typedef [lit] 0  ty-int [lit] 0 ty-make  cc-sym-add drop
  cc-name-int8_t   [lit] 6  sk-typedef [lit] 0  ty-int [lit] 0 ty-make  cc-sym-add drop
  cc-name-int16_t  [lit] 7  sk-typedef [lit] 0  ty-int [lit] 0 ty-make  cc-sym-add drop
  cc-name-int32_t  [lit] 7  sk-typedef [lit] 0  ty-int [lit] 0 ty-make  cc-sym-add drop
  cc-name-int64_t  [lit] 7  sk-typedef [lit] 0  ty-int [lit] 0 ty-make  cc-sym-add drop
  cc-name-uint8_t  [lit] 7  sk-typedef [lit] 0  ty-int [lit] 0 ty-make  cc-sym-add drop
  cc-name-uint16_t [lit] 8  sk-typedef [lit] 0  ty-int [lit] 0 ty-make  cc-sym-add drop
  cc-name-uint32_t [lit] 8  sk-typedef [lit] 0  ty-int [lit] 0 ty-make  cc-sym-add drop
  cc-name-uint64_t [lit] 8  sk-typedef [lit] 0  ty-int [lit] 0 ty-make  cc-sym-add drop
  cc-name-size_t   [lit] 6  sk-typedef [lit] 0  ty-int [lit] 0 ty-make  cc-sym-add drop
  cc-name-ssize_t  [lit] 7  sk-typedef [lit] 0  ty-int [lit] 0 ty-make  cc-sym-add drop
  cc-name-intptr_t [lit] 8  sk-typedef [lit] 0  ty-int [lit] 0 ty-make  cc-sym-add drop ;

```

### Closing the translation unit

Return to the two pending references in the opening program. The
function definition has supplied `add`'s destination. Before placing the
data for `bias`, the driver must finish any late shim bodies and check
that no used function still lacks a destination. Only then is the end of
code fixed and the global-address patching described above ready to run.

An unused prototype is harmless; a used function with unresolved references is not. `cc-check-fns-defined` rejects remaining call or address fixups and then requires a definition of `main`, preventing executable output with unresolved destinations (`forth-bootstrap/cc/116-cc-prog.fth:855`):

```forth file=cc/116-cc-prog.fth
\ cc-check-fns-defined ( -- )  After the whole program: a function that was
\ called or used as a value but never defined still has pending call or
\ address fixups — each would run a rel32 of 0 (falling through to the next
\ instruction) or load address 0.  Die 206 instead.  Then die 207 if there
\ is no main for the entry stub to call.  memset is registered above with
\ no body, so a program that uses it dies here too: this compiler has no
\ memset to link.
: cc-check-fns-defined
  [lit] 0                                         ( id )
  begin, dup cc-sym-count @ < while,
    dup cc-sym-kind-of sk-func = if,
      dup cc-sym-call-fixups @  over cc-sym-addr-fixups @  or if,
        cc-target-lp64 @ if,
          dup cc-sym-name-addr cell[] @ over cc-sym-name-len cell[] @ cc-err-write
          cc-die-end [lit] 1 cc-err-write
        then,
        [lit] 206 cc-die
      then,
    then,
    1+
  repeat, drop
  cc-main-vaddr @ 0= if, [lit] 207 cc-die then, ;

```

The ordering in `cc-parse-program` makes built-ins visible before user parsing, emits needed late bodies before checking references, and patches entry last. Global placement and ELF finalization follow this word; Chapter 38 packages the compiler entry and its Stage A checkpoint (`forth-bootstrap/cc/116-cc-prog.fth:875`):

```forth file=cc/116-cc-prog.fth
\ cc-parse-program ( -- )  Emit entry stub, emit libc shims, register the
\ late shims, the one external prototype and built-in typedefs, parse all
\ functions, emit the late shims that were called, check every used
\ function got a body, patch entry stub.
: cc-parse-program
  cc-emit-entry-stub
  cc-emit-shims
  cc-register-late-shims
  cc-emit-external-protos
  cc-emit-libc-typedefs
  cc-parse-function-list
  cc-emit-late-shims
  cc-check-fns-defined
  cc-patch-call-main ;
```

## Try it

Run from the `forth-bootstrap` checkout root with the seed built in Part 1. This driver loads through `cc/116-cc-prog.fth` and places the opening example in the source buffer: `bias` is initialized, `main` calls the declared `add`, and the later definition returns its parameter plus `bias`. Empty C comments keep type keywords separate from names inside the token copied by `s,`.

<!-- tryit: expect "compiler exit: 0\nprogram exit: 7" -->
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
      cc/110-cc-decl.fth cc/112-cc-stmt.fth \
      cc/114-cc-func.fth cc/116-cc-prog.fth || exit "$?"
  cat <<'FORTH' || exit "$?"
cc-src-init
here dup cc-src-buffer !
s, int/**/bias=3;int/**/add(int/**/n);int/**/main(void){return/**/add(4);}int/**/add(int/**/n){return/**/n+bias;}
here swap - cc-src-len !
[lit] 0 cc-src-pos ! [lit] 0 cc-tok-pending !
cc-out-init [lit] 0 cc-bss-size ! cc-emit-elf-header
cc-parse-program cc-finalize-globals cc-finalize-elf
[lit] 1 cc-out-buf cc-out-pos @ write drop
bye
FORTH
} | ./seed-forth > "$probe_dir/program" || compiler_status=$?
printf 'compiler exit: %s\n' "$compiler_status" # prints 'compiler exit: 0'
test "$compiler_status" -eq 0 || exit "$compiler_status"
chmod +x "$probe_dir/program" || exit "$?"
program_status=0
(cd "$probe_dir" && ./program) || program_status=$?
printf 'program exit: %s\n' "$program_status" # prints 'program exit: 7'
test "$program_status" -eq 7
)
```

Observed output:

```text
compiler exit: 0
program exit: 7
```

The executable runs from the temporary directory and returns the helper’s result through the entry stub. This checks core parameter spilling, a forward call, global placement, and whole-program finalization. Native calls, enum and typedef parsing, repeated global declarations, and late-shim emission are source walkthroughs here; this checkpoint does not execute those paths.

## Exercise

Hints and feedback are in [Appendix H](66-exercise-feedback.md#chapter-37-resolving-a-function).

**Trace (easy).** Follow the checkpoint’s `add` symbol from prototype registration through the call in `main` to its definition. Identify which entry holds the pending call, when its list is cleared, and why the definition survives the end of its local scope.

**Modify (moderate).** Move the definition of `add` before `main`, keeping the prototype. Predict which call-emission branch changes, then rerun the checkpoint and compare the exit status.

