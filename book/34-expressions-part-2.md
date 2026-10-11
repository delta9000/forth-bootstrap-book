# Chapter 34 — Expressions: operands and assignment

An expression can identify a place to store a value. In `*p = 7`, the
compiler must preserve the address held in `p` until it can write 7 there.
In `*p + 7`, it must instead read through that address before adding. The
same operand starts both expressions; what follows determines whether we
need its location or its contents.

We will keep that choice open. An **lvalue** denotes an object; obtaining
the stored value is a separate step called **materialization**. The parser
emits code for the operand and records how that result may be used.

Consider `*p += q` by hand, with valid core integer storage: `p` holds
address `A`, the integer at `A` is 10, and `q` is 3. The generated program
must preserve `A`, obtain the old 10, add 3, and store 13 back at `A`.
The assignment expression also supplies 13 to its caller. Loading 10 and
forgetting `A` would make the addition possible and the store impossible.

There is a matching problem inside the compiler. Parsing `q` overwrites
the shared record describing the current expression. We must save the
left side's destination information before making that recursive call.
First we will build this record, then follow assignment through both the
compiler and the program it emits. The remaining operand forms fit into
that same contract.

## Lvalue tracking

Primary and unary parsing supply operands to the binary cascade
(Chapter 33); ternary and assignment consume its results. Each parser
leaves instructions that produce a result in `rdi`, together with compiler
metadata describing that result. A pending dereference means `rdi` will
hold an address when the program runs. Materializing it emits the load.
This is what lets `p[i]` serve either side of an assignment.

The source’s introductory comment gives the core delayed-load contract; its “four facts” description predates the additional metadata below
(`forth-bootstrap/cc/100-cc-expr.fth:68`):
```forth chunk=expr-lvalue
\ ===========================================================================
\ Lvalue tracking for assignment, address-of, and dereference.
\ ===========================================================================
\ Every parse function leaves a value in rdi and four facts about it here.
\ The cc-mark words below write the kind and slot and clear the struct
\ descriptor and the type, which the parser sets afterwards when it knows
\ them; cc-emit-materialize is the only other writer of the kind.
\
\   cc-last-lvalue-kind  what rdi holds — one of the lv-* constants:
\       lv-value      a value; not assignable
\       lv-local      a local's value, already loaded; the local is
\                     cc-last-ident-slot, so `x = ...` stores back there
\       lv-deref      the ADDRESS of a qword that has not been loaded yet
\       lv-deref-byte the ADDRESS of a single byte (a char) not loaded yet
\     A consumer that wants the value calls cc-emit-materialize, which loads
\     through a pending address; assignment instead stores through it.
\   cc-last-ident-slot   slot index of an lv-local (-1 otherwise).
\   cc-last-struct-desc  struct descriptor of a struct or struct-pointer
\                        value (0 if none), for a following '.' / '->'.
\   cc-last-expr-type    encoded C type (ty-base + ptr-depth) of the value,
\                        0 if unknown.  A following '[' or unary '*' reads it
\                        to pick byte or qword stride and width.
\
\ A binary operator's result is a plain value: it marks lv-value, which
\ clears all four.  cc-parse-assign reads kind and slot once, right after
\ parsing the left side, and keeps them on the data stack while the right
\ side's parse overwrites them.

```

`lv-temporary` prevents a temporary record or member from becoming a store destination. `cc-mark` resets the entire expression record: kind, local slot, qualification, field record, descriptor, type, null-constant status, and array dimensions
(`forth-bootstrap/cc/100-cc-expr.fth:96`):
```forth chunk=expr-lvalue
[lit] 0 constant lv-value
[lit] 1 constant lv-local
[lit] 2 constant lv-deref
[lit] 3 constant lv-deref-byte
[lit] 4 constant lv-temporary                     \ non-lvalue record or materialized member

variable cc-last-lvalue-kind                       \ lv-value .. lv-deref-byte
variable cc-last-ident-slot
variable cc-last-expr-qualified
variable cc-last-field-rec                         \ 0 or aggregate field metadata
variable cc-last-struct-desc
variable cc-last-expr-type
variable cc-last-expr-null
variable cc-last-expr-array-len                    \ undecayed array length for sizeof
variable cc-last-expr-array-inner                  \ row width for a two-dimensional array

\ cc-mark ( slot kind -- )  Record kind and slot; clear desc and type.
: cc-mark
  cc-last-lvalue-kind !
  cc-last-ident-slot !
  [lit] 0 cc-last-expr-qualified !
  [lit] 0 cc-last-field-rec !
  [lit] 0 cc-last-struct-desc !
  [lit] 0 cc-last-expr-type !
  [lit] 0 cc-last-expr-null !
  [lit] 0 cc-last-expr-array-len !
  [lit] 0 cc-last-expr-array-inner ! ;

```

The kind is an implementation category, not a complete C type: `lv-local` already holds a loaded value but retains its store slot; a pending dereference holds an address. Array length and inner width preserve shape for `sizeof`, while null-constant status distinguishes a recognized null constant from an arbitrary runtime value.

### Marking a result

These small handlers give each producer a common vocabulary for the result it leaves:

| Input | Result or predicate |
|---|---|
| Plain value | `cc-mark-not-lvalue` selects `lv-value` |
| Local slot | `cc-mark-local-lvalue` selects `lv-local` |
| Byte-width flag | `cc-mark-deref` selects `lv-deref-byte` or `lv-deref` |
| Current kind | `cc-deref-pending?` recognizes an address awaiting a load |
| Encoded type | `cc-char-ptr?` recognizes a pointer directly to `char` |

The wrappers separate marking from the tests that consumers need
(`forth-bootstrap/cc/100-cc-expr.fth:124`):
```forth chunk=expr-lvalue
\ cc-mark-not-lvalue ( -- )  rdi holds a plain value.
: cc-mark-not-lvalue     true lv-value cc-mark ;

\ cc-mark-local-lvalue ( slot -- )  rdi holds the loaded value of local slot.
: cc-mark-local-lvalue   lv-local cc-mark ;

\ cc-mark-deref ( byte? -- )  rdi holds an address not yet loaded; byte? is
\ true when it addresses a single byte (`s[i]` or `*s` with s a char*).
: cc-mark-deref
  if, lv-deref-byte else, lv-deref then,
  true swap cc-mark ;

\ cc-deref-pending? ( -- f )  True if rdi holds an address not yet loaded.
: cc-deref-pending?
  cc-last-lvalue-kind @ lv-deref =
  cc-last-lvalue-kind @ lv-deref-byte = or ;

\ cc-char-ptr? ( ty -- f )  True iff ty is char* (a subscript or '*' on it
\ reaches a single byte).
: cc-char-ptr?
  dup ty-base ty-char = swap ty-ptr [lit] 1 = and ;

```

`cc-expr-symbol-desc` selects descriptors for records, arrays, and functions (Chapter 30). The size helpers distinguish object size from pointee size, including the native byte stride for `void *`
(`forth-bootstrap/cc/100-cc-expr.fth:146`):
```forth chunk=expr-lvalue
\ Native expression metadata uses the existing encoded type plus descriptor.
\ A plain aggregate is represented by its address, never by its first word.
: cc-expr-symbol-desc                             ( id -- desc )
  dup cc-sym-type-of ty-base dup ty-struct = over ty-array = or swap ty-func = or if,
    cc-sym-struct-desc-of
  else, drop [lit] 0 then, ;

: cc-expr-type-size                               ( ty desc -- bytes )
  over ty-base ty-array = if,
    over ty-ptr if, drop ty-size else, nip cc-ad-size then, exit,
  then,
  over ty-base ty-struct = over [lit] 0 <> and
  [lit] 0 = if, drop ty-size exit, then,
  over ty-ptr if, drop ty-size else, nip cc-sd-total-size then, ;

: cc-expr-pointee-type                            ( ty -- ty' )
  dup ty-ptr if, [lit] 1 - then, ;

: cc-expr-pointee-size                            ( ty desc -- bytes )
  \ GNU C treats void-pointer arithmetic as byte arithmetic. Keep this
  \ separate from ty-size(void), which is also used by sizeof.
  cc-target-lp64 @ if,
    over ty-base ty-void = if,
      over ty-ptr [lit] 1 = if, 2drop [lit] 1 exit, then,
    then,
  then,
  swap cc-expr-pointee-type swap cc-expr-type-size ;

```

Typed results restore their type after marking, and `cc-unary-type` promotes narrow integers while preserving pointer types
(`forth-bootstrap/cc/100-cc-expr.fth:174`):
```forth chunk=expr-lvalue
: cc-mark-int-value                               ( -- )
  cc-mark-not-lvalue
  cc-target-lp64 @ if, ty-int [lit] 0 ty-make cc-last-expr-type ! then, ;

: cc-unary-type                                  ( ty -- promoted-ty )
  dup ty-ptr if, exit, then,
  dup ty-size [lit] 4 < if, drop ty-int [lit] 0 ty-make then, ;

: cc-mark-typed-value                             ( ty desc -- )
  cc-mark-not-lvalue
  cc-last-struct-desc ! cc-last-expr-type ! ;

```

<details>
<summary>Value hooks used by later numeric and aggregate types</summary>

Ordinary core integers use the existing emitters. These bindings leave
places for floating values, bitfields, and aggregates to supply other
operations without changing the expression grammar.

### Value-operation hooks

A hook lets a later target replace a value operation without replacing the parser. The bindings here are the defaults, not the later implementations:

| Hook family | Default result |
|---|---|
| `cc-value-literal-fwd` | Declines a special literal |
| `cc-value-test-fwd`, `cc-value-not-fwd`, `cc-value-negate-fwd`, `cc-value-complement-fwd` | Existing integer emitters |
| `cc-value-plus-fwd`, `cc-value-ternary-fwd` | No extra operation |
| `cc-value-ternary-split-fwd`, `cc-aggregate-ternary-fwd` | Decline special branch joining |
| `cc-value-integer-use-fwd`, `cc-value-shape-fwd`, `cc-value-init-fwd` | Consume checking arguments without further action |
| `cc-opaque-scalar-fwd` | Declines scalar treatment of an aggregate-shaped type |

Literal dispatch and scalar operations initially use the existing encoders; conditional hooks leave branch joining to the ordinary parser
(`forth-bootstrap/cc/100-cc-expr.fth:186`):
```forth chunk=expr-lvalue
\ Typed value operations share the historical encoders until a target binds them.
: cc-value-literal-default [lit] 0 ;
defer cc-value-literal-fwd
' cc-value-literal-default is cc-value-literal-fwd
defer cc-value-test-fwd
' cc-emit-test-rdi is cc-value-test-fwd
defer cc-value-not-fwd
' cc-emit-not-zero-flag is cc-value-not-fwd
defer cc-value-negate-fwd
' cc-emit-neg-rdi is cc-value-negate-fwd
defer cc-value-complement-fwd
' cc-emit-not-rdi is cc-value-complement-fwd
\ Unary plus has no opcode, but its operand still has type constraints.
: cc-value-plus-default ;
defer cc-value-plus-fwd
' cc-value-plus-default is cc-value-plus-fwd
: cc-value-ternary-noop ;
defer cc-value-ternary-fwd
' cc-value-ternary-noop is cc-value-ternary-fwd
: cc-value-ternary-split-default [lit] 0 ;
defer cc-value-ternary-split-fwd
' cc-value-ternary-split-default is cc-value-ternary-split-fwd
```

The remaining defaults establish checking and aggregate contracts; Chapters 47–49 supply specialized value handling
(`forth-bootstrap/cc/100-cc-expr.fth:208`):
```forth chunk=expr-lvalue
\ A record conditional consumes saved left metadata and the true-arm fixup,
\ patches the join and publishes its value. Scalars leave both in place.
: cc-aggregate-ternary-default [lit] 0 ;
defer cc-aggregate-ternary-fwd
' cc-aggregate-ternary-default is cc-aggregate-ternary-fwd
\ Integer-only consumers have a distinct check from scalar load/store support.
: cc-value-integer-use-default drop ;
defer cc-value-integer-use-fwd
' cc-value-integer-use-default is cc-value-integer-use-fwd
: cc-value-shape-default ( source descriptor destination descriptor -- ) 2drop 2drop ;
defer cc-value-shape-fwd
' cc-value-shape-default is cc-value-shape-fwd
: cc-value-init-default ( source destination -- ) 2drop ;
defer cc-value-init-fwd
' cc-value-init-default is cc-value-init-fwd

: cc-opaque-scalar-default ( type descriptor -- flag ) 2drop [lit] 0 ;
defer cc-opaque-scalar-fwd
' cc-opaque-scalar-default is cc-opaque-scalar-fwd

```

</details>

### Choosing address or value

`cc-mark-typed-deref` preserves addresses for arrays, functions, and ordinary records, but marks scalar storage for a later load
(`forth-bootstrap/cc/100-cc-expr.fth:228`):
```forth chunk=expr-lvalue
: cc-mark-typed-deref                             ( ty desc -- )
  over ty-base ty-array = if,
    over ty-ptr 0= if,
      nip dup cc-ad-count >r dup cc-ad-inner >r
      dup cc-ad-type [lit] 1 + swap cc-ad-desc cc-mark-typed-value
      r> cc-last-expr-array-inner ! r> cc-last-expr-array-len ! exit,
    then,
  then,
  over ty-base ty-func = if,
    over ty-ptr 0= if, cc-mark-typed-value exit, then,
  then,
  over ty-base ty-struct = over [lit] 0 <> and
  if,
    over ty-ptr 0= if,
      2dup cc-opaque-scalar-fwd 0= if, cc-mark-typed-value exit, then,
    then,
  then,
  over ty-size [lit] 1 = cc-mark-deref
  cc-last-struct-desc ! cc-last-expr-type ! ;

```

Indexing and pointer updates need byte offsets, so `cc-emit-scale-rdi` and `cc-emit-scale-rcx` multiply an index by its stride
(`forth-bootstrap/cc/100-cc-expr.fth:248`):
```forth chunk=expr-lvalue
: cc-emit-scale-rdi                               ( bytes -- )
  dup [lit] 1 = if, drop exit, then,
  dup [lit] 8 = if, drop cc-emit-shl-rdi-3 exit, then,
  [lit] 72 cc-emit-byte [lit] 105 cc-emit-byte [lit] 255 cc-emit-byte
  cc-emit-4le ;                                   \ imul rdi,rdi,imm32

: cc-emit-scale-rcx                               ( bytes -- )
  dup [lit] 1 = if, drop exit, then,
  [lit] 72 cc-emit-byte [lit] 105 cc-emit-byte [lit] 201 cc-emit-byte
  cc-emit-4le ;                                   \ imul rcx,rcx,imm32

```

Field operations follow a shared contract. A load or store consumes the field type and record; a value-type query returns the type of the loaded value; a use check consumes the record. The defaults use ordinary typed storage and ignore field-specific metadata. Chapter 48 supplies bitfield behavior.

The field bindings isolate storage policy from expression parsing
(`forth-bootstrap/cc/100-cc-expr.fth:259`):
```forth chunk=expr-lvalue
\ cc-emit-materialize ( -- )  If rdi holds an address not yet loaded, load
\ through it (one byte or eight) so rdi holds the value, and mark it a plain
\ value.  The struct descriptor and type describe the value either way, so
\ they are kept.  A no-op for lv-value and lv-local.
\ Record members can override scalar storage without changing ordinary lvalues.
: cc-field-load-default ( ty rec -- ) drop cc-emit-load-typed-via-rdi ;
: cc-field-store-default ( ty rec -- ) drop cc-emit-store-typed-via-rcx ;
: cc-field-value-type-default ( ty rec -- ty ) drop ;
: cc-field-use-default ( rec -- ) drop ;
defer cc-field-load-fwd
defer cc-field-store-fwd
defer cc-field-value-type-fwd
defer cc-field-use-fwd
' cc-field-load-default is cc-field-load-fwd
' cc-field-store-default is cc-field-store-fwd
' cc-field-value-type-default is cc-field-value-type-fwd
' cc-field-use-default is cc-field-use-fwd

```

`cc-emit-materialize` first offers array decay to its hook, then loads only a pending dereference; it changes the kind and slot while retaining the value’s descriptive metadata
(`forth-bootstrap/cc/100-cc-expr.fth:277`):
```forth chunk=expr-lvalue
: cc-array-decay-default ;
defer cc-array-decay-fwd
' cc-array-decay-default is cc-array-decay-fwd
: cc-emit-materialize
  cc-array-decay-fwd
  cc-deref-pending? if,
    cc-target-lp64 @ if,
      cc-check-static-init
      cc-last-expr-type @ cc-last-field-rec @ cc-field-load-fwd
      cc-last-expr-type @ cc-last-field-rec @ cc-field-value-type-fwd cc-last-expr-type !
    else,
      cc-last-lvalue-kind @ lv-deref-byte = if,
        cc-emit-load-byte-via-rdi
      else,
        cc-emit-load-via-rdi
      then,
    then,
    true cc-last-ident-slot !
    lv-value cc-last-lvalue-kind !
  then, ;

```

## Assignment: snapshot, recurse, store

The left operand parser has done its job: it has identified a destination.
For now, take the operand and ternary parsers as tools that produce the
record just described. Assignment protects that record while asking for
the right side. The detailed trace shows exactly what must be saved and
which stack owns it.

### A two-stack assignment trace

Return to the opening example in the core profile, with valid eight-byte integer storage: `p` holds
address `A`, memory at `A` holds 10, and local `q` holds 3 in slot `s`.
This is a manual trace of `*p += q`, not a new runnable checkpoint.
Compiler stacks exist while Forth emits code; the program-stack column
describes what that code does later. Stack top is on the right. Only the
cells owned by this assignment are shown; return addresses and surrounding
frames are omitted. Let `K` mean `lv-deref` and `OP` mean the `+=` token.

| Transition | Compiler data stack | Compiler return stack | Generated program stack | Generated registers and metadata |
|---|---|---|---|---|
| Parse `*p`, then snapshot left side | `K -1` | empty | empty | `rdi=A`; kind K, no local slot, type core int |
| Recognize `+=`; preserve destination and old contents | empty, after `OP K >r >r` | `K OP` | `A 10` | Push A, load eight bytes through A, push 10; compiler metadata still describes the left side |
| Parse and materialize `q` | empty after recursion | `K OP` | `A 10` | `rdi=3`; globals now describe local q: kind `lv-local`, slot s, type core int |
| Recover old value and apply saved operator | empty after the emitter consumes OP | `K` | `A` | Move 3 to `rcx`, pop 10 to `rdi`, emit addition: `rdi=13` |
| Recover destination, store and finish | empty | empty | empty | Pop A to `rcx`; saved K selects an eight-byte store; memory[A]=13, `rdi=13`; mark result `lv-value` |

The slot `s` now recorded in the compiler globals describes `q`; it is
never used as the destination. The saved address supplies that destination, while the saved kind selects
the store width. The old value and address are runtime values; K and OP
are compiler decisions. Mixing these two timelines is the common error
this trace is meant to catch.

For a byte target, the saved kind instead selects a byte load/store. For
native typed assignment, the snapshot must additionally retain destination
type, descriptor, field record and qualification; its conversion and
field-aware hooks cannot be replaced by the core width rule above.

### Recognizing an assignment

An assignment must remember its destination while recursively parsing its source; `cc-assign-op?` recognizes either plain assignment or a compound operator’s table entry
(`forth-bootstrap/cc/100-cc-expr.fth:2200`):
```forth chunk=expr-assign
\ ===========================================================================
\ cc-parse-assign: ternary (ASSIGN-OP assign)?
\ ===========================================================================
\ Right-recursive.  After parsing the LHS via cc-parse-ternary, snapshot
\ cc-last-ident-slot on the data stack BEFORE recursing into the RHS (which
\ would otherwise overwrite it).
\
\ We test the next token without immediately committing: if it's '=', we use
\ the snapshot to emit a store; otherwise we put the token back and discard
\ the snapshot.
\
\ NOTE: assignment is right-associative, so the RHS recurses through
\ cc-parse-assign (not cc-parse-eq) — chained `a = b = 1` works.

\ cc-assign-op? ( -- f )  After cc-next-token-keep, returns -1 if the
\ current token is '=' or the compound form of an operator in the table
\ ('+=' '-=' '*=' '/=' '%=' '<<=' '>>=' '&=' '|=' '^=').
: cc-assign-op?
  tok-kind @ tk-punct = if,
    tok-num @ [char] = =
    tok-num @ bo-compound cc-binop-row 0= 0= or
  else,
    [lit] 0
  then, ;

```

Compound assignment reads the old value at the destination’s width, then `cc-apply-compound-op` invokes the corresponding binary emitter
(`forth-bootstrap/cc/100-cc-expr.fth:2225`):
```forth chunk=expr-assign
\ cc-emit-load-via-rdi-or-byte ( byte? -- )  rdi := the byte or the qword
\ at the address in rdi.
: cc-emit-load-via-rdi-or-byte
  if, cc-emit-load-byte-via-rdi else, cc-emit-load-via-rdi then, ;

\ cc-apply-compound-op ( op -- )  After rdi=LHS-value, rcx=RHS-value: apply
\ the compound-assign op to rdi with the emitter of its row in the operator
\ table.  Consumes op.  Plain '=' must be filtered by the caller.
: cc-apply-compound-op
  bo-compound cc-binop-row                        ( row | 0 )
  dup 0= if,
    [lit] 118 cc-die                              \ not a compound operator
  then,
  bo-emitter + @ execute ;

```

<details>
<summary>Native assignment: preserve type, field, and qualification metadata</summary>

The core path below saves a kind and slot. Native stores also need the
destination's type and field rules after the right side has been parsed.
This snapshot extends the same lifetime discipline to that larger record.

### Native destination snapshots

`cc-parse-native-assign` rejects temporary destinations and converts a local slot to an address, giving locals and pending dereferences a shared store path
(`forth-bootstrap/cc/100-cc-expr.fth:2240`):
```forth chunk=expr-assign
variable cc-assign-qualified
variable cc-assign-type
variable cc-assign-desc
variable cc-assign-op
variable cc-assign-field

: cc-aggregate-assignment-default ;
defer cc-aggregate-assignment-fwd
' cc-aggregate-assignment-default is cc-aggregate-assignment-fwd
\ A target may give compound assignment to a record type its own diagnostic.
: cc-aggregate-compound-default ( type descriptor -- ) 2drop ;
defer cc-aggregate-compound-fwd
' cc-aggregate-compound-default is cc-aggregate-compound-fwd

\ One native store path handles locals, globals, fields and dereferences.
\ Snapshots live on the return stack across the recursive RHS parse.
: cc-parse-native-assign                          ( kind slot -- )
  over lv-temporary = if, [lit] 120 cc-die then,
  cc-check-static-init
  over lv-local = if,
    nip cc-emit-lea-rdi-local
  else,
    drop dup lv-deref = swap lv-deref-byte = or
    cc-last-expr-type @ ty-base ty-struct =
    cc-last-expr-type @ ty-ptr 0= and or
    0= if, [lit] 120 cc-die then,
  then,
```

The `cc-assign-*` globals are scratch cells used after recursion. Qualification, field record, type, descriptor, and operator stay on the return stack until the right side finishes; putting them in those globals earlier would let a nested assignment overwrite them. The aggregate-assignment default does nothing, and the aggregate-compound default consumes its type arguments before the caller rejects the operation.

The generated program saves its destination address and, for compound assignment, its old value; the compiler separately saves metadata across the recursive parse
(`forth-bootstrap/cc/100-cc-expr.fth:2267`):
```forth chunk=expr-assign
  cc-last-expr-qualified @ >r
  cc-last-field-rec @ >r
  cc-last-expr-type @ >r cc-last-struct-desc @ >r tok-num @ >r
  cc-emit-push-rdi
  r@ [char] = <> if,
    cc-last-expr-type @ cc-last-field-rec @ cc-field-load-fwd
    cc-emit-push-rdi
  then,
  cc-parse-assign-fwd cc-emit-materialize
  r> cc-assign-op ! r> cc-assign-desc ! r> cc-assign-type !
  r> cc-assign-field ! r> cc-assign-qualified !
  cc-assign-op @ [char] = = if,
    cc-last-expr-type @ cc-last-struct-desc @
    cc-assign-type @ cc-assign-desc @ cc-value-shape-fwd
  then,
```

An ordinary record assignment copies the object’s bytes and returns its destination address as the expression result; aggregate hooks allow target-specific validation
(`forth-bootstrap/cc/100-cc-expr.fth:2282`):
```forth chunk=expr-assign
  cc-assign-type @ ty-base ty-struct = cc-assign-type @ ty-ptr 0= and
  cc-assign-type @ cc-assign-desc @ cc-opaque-scalar-fwd 0= and if,
    cc-assign-op @ [char] = <> if,
      cc-assign-type @ cc-assign-desc @ cc-aggregate-compound-fwd
      [lit] 120 cc-die
    then,
    cc-aggregate-assignment-fwd
    [lit] 72 cc-emit-byte [lit] 137 cc-emit-byte [lit] 254 cc-emit-byte
    cc-emit-pop-rdi cc-emit-push-rdi               \ rsi=source; rdi=destination
    [lit] 72 cc-emit-byte [lit] 199 cc-emit-byte [lit] 193 cc-emit-byte
    cc-assign-type @ cc-assign-desc @ cc-expr-type-size cc-emit-4le
    [lit] 243 cc-emit-byte [lit] 164 cc-emit-byte  \ rep movsb
    cc-emit-pop-rdi
    cc-assign-type @ cc-assign-desc @ cc-mark-typed-value
    cc-assign-qualified @ cc-last-expr-qualified ! exit,
  then,
```

Native compound assignment converts operands for the operation, scales pointer changes, and converts the result back to the destination type before the field-aware store
(`forth-bootstrap/cc/100-cc-expr.fth:2298`):
```forth chunk=expr-assign
  cc-assign-op @ [char] = <> if,
    cc-assign-type @ cc-assign-field @ cc-field-value-type-fwd cc-assign-desc @
    cc-last-expr-type @ cc-last-struct-desc @ cc-expr-save-types
    cc-assign-op @ bo-compound cc-binop-row cc-expr-op-row !
    cc-array-compound-fwd cc-array-binop-fwd
    cc-expr-op-row @ bo-level + @ level-shift = if,
      cc-expr-left-type @ cc-expr-promote cc-expr-common !
    then,
    cc-assign-type @ ty-ptr if,
      cc-expr-op-row @ bo-level + @ level-add = if,
        cc-assign-type @ cc-assign-desc @ cc-expr-pointee-size cc-emit-scale-rdi
      then,
    then,
    cc-emit-mov-rcx-rdi cc-emit-pop-rdi
    cc-expr-left-type @ cc-expr-common @ cc-emit-convert-value
    cc-expr-right-type @ cc-expr-common @ cc-emit-convert-right
    cc-native-binop-emit cc-expr-common @ cc-last-expr-type !
  then,
  cc-last-expr-type @ cc-assign-type @ cc-emit-convert-value
  cc-emit-pop-rcx
  cc-assign-type @ cc-assign-field @ cc-field-store-fwd
  cc-assign-type @ cc-assign-field @ cc-field-value-type-fwd
  cc-assign-desc @ cc-mark-typed-value
  cc-assign-qualified @ cc-last-expr-qualified ! ;

```

</details>

### Legacy locals and pointer targets

`cc-parse-assign` snapshots kind and slot before looking for an assignment operator; a legacy local saves its old value only when the operator needs it
(`forth-bootstrap/cc/100-cc-expr.fth:2323`):
```forth chunk=expr-assign
: cc-parse-assign
  cc-parse-ternary
  \ Snapshot lvalue state BEFORE the recursive RHS parse can clobber it.
  cc-last-lvalue-kind @                           ( kind )
  cc-last-ident-slot @                            ( kind slot )
  cc-next-token-keep
  cc-assign-op? if,
    cc-target-lp64 @ if, cc-parse-native-assign exit, then,
    \ Some assignment operator confirmed.  Dispatch on lvalue kind.
    \ Stack layout: ( kind slot ).  lv-local -> store to the slot;
    \ lv-deref / lv-deref-byte -> store through the address in rdi;
    \ lv-value -> not an lvalue (error).
    over lv-local = if,
      \ ---- Local lvalue (lv-local) ---------------------------------------
      \ The LHS load was already emitted by cc-parse-primary; we'll just
      \ overwrite the local slot with the RHS / RHS-folded value.
      nip                                         ( slot )
      tok-num @                                   ( slot op )
      swap >r                                     \ stash slot ( op ; R: slot )
      \ For compound assignment, save current LHS value before parsing RHS.
      dup [char] = = 0= if,
        cc-emit-push-rdi
      then,
      >r                                          \ stash op ( ; R: slot op )
      cc-parse-assign
      cc-emit-materialize                         \ ensure rdi holds a value
```

The local path folds and stores into its saved slot, while a compound dereference saves both the destination address and its old contents
(`forth-bootstrap/cc/100-cc-expr.fth:2349`):
```forth chunk=expr-assign
      r> r>                                       ( op slot )
      swap                                        ( slot op )
      dup [char] = = if,
        drop                                      ( slot )
      else,
        cc-emit-mov-rcx-rdi                       \ rcx = RHS
        cc-emit-pop-rdi                           \ rdi = LHS (saved earlier)
        cc-apply-compound-op                      \ rdi := rdi <op> rcx
      then,
      cc-emit-store-local                         \ [rbp - 8*(slot+1)] := rdi
      cc-mark-not-lvalue
    else,
      over dup lv-deref = swap lv-deref-byte = or if,
        \ ---- Dereference lvalue (lv-deref / lv-deref-byte) ---------------
        \ rdi already holds the destination address (no load was emitted by
        \ cc-parse-unary).
        drop                                      ( kind )
        tok-num @ [char] = <> if,
          \ Compound: load the old value through the address, combine,
          \ store back through the same address.
          tok-num @ swap                          ( op kind )
          cc-emit-push-rdi                        \ save dest address
          dup lv-deref-byte = cc-emit-load-via-rdi-or-byte
          cc-emit-push-rdi                        \ save old value
          >r >r                                   ( ; R: kind op )
```

After recursion, compound assignment combines the saved value with the right side and stores through the saved address; plain assignment needs only that address
(`forth-bootstrap/cc/100-cc-expr.fth:2374`):
```forth chunk=expr-assign
          cc-parse-assign
          cc-emit-materialize
          cc-emit-mov-rcx-rdi                     \ rcx := RHS
          cc-emit-pop-rdi                         \ rdi := old value
          r> cc-apply-compound-op                 \ rdi := old OP RHS
          cc-emit-pop-rcx                         \ rcx := dest address
          r> lv-deref-byte = if,
            cc-emit-store-byte-via-rcx
          else,
            cc-emit-store-via-rcx
          then,
          cc-mark-not-lvalue exit,
        then,
        >r                                        \ R: kind
        cc-emit-push-rdi                          \ save dest address
        cc-parse-assign
        cc-emit-materialize                       \ rdi holds RHS value
        cc-emit-mov-rcx-rdi                       \ rcx := RHS
        cc-emit-pop-rdi                           \ rdi := dest address
        \ End-of-sequence wants rdi=value, rcx=address.  We currently have
        \ rcx=value, rdi=address.  Swap via push/pop:
        \    push rdi ; mov rdi, rcx ; pop rcx
        cc-emit-push-rdi                          \ push address
        \ mov rdi, rcx: 48 89 CF (mod=11 reg=rcx=1 rm=rdi=7 -> 11_001_111=0xCF)
```

The final store puts the value in `rdi` and the address in `rcx`, selecting byte or qword width from the saved kind; a non-assignment token discards the unused snapshot
(`forth-bootstrap/cc/100-cc-expr.fth:2398`):
```forth chunk=expr-assign
        [lit]  72 cc-emit-byte
        [lit] 137 cc-emit-byte
        [lit] 207 cc-emit-byte
        cc-emit-pop-rcx                           \ rcx := address
        r> lv-deref-byte = if,
          cc-emit-store-byte-via-rcx              \ [rcx] := dil  (1 byte)
        else,
          cc-emit-store-via-rcx                   \ [rcx] := rdi  (8 bytes)
        then,
        cc-mark-not-lvalue
      else,
        \ Not an lvalue at all.
        2drop
        [lit] 120 cc-die
      then,
    then,
  else,
    2drop                                         \ discard kind/slot snapshot
    cc-putback-token
  then, ;

```

## Struct-field lookup

Assignment can now consume a destination without losing it. We can turn
back to the operand forms that supply one: fields, subscripts, names, and
unary dereferences. Each must leave both the right runtime result and the
metadata needed by its next consumer.

A field lookup must return both an offset and enough metadata for the next postfix operation; the `cc-ff-*` cells hold the search name, descriptor, and matched results
(`forth-bootstrap/cc/100-cc-expr.fth:298`):
```forth chunk=expr-struct-field
\ ===========================================================================
\ Struct-field name lookup.
\ ===========================================================================
\ Walks the descriptor's field array and returns the first matching field's
\ byte offset, leaving its pointee desc and encoded type in cc-ff-result-desc
\ and cc-ff-result-type for the caller.  Dies with code 90 if no field
\ matches (compile-time error: field not found).  Uses globals to stash the
\ needle so the loop body has predictable stack effect.

variable cc-ff-needle-addr
variable cc-ff-needle-len
variable cc-ff-desc
variable cc-ff-result-desc                           \ matched field's pointee desc (0 if not a struct ptr)
variable cc-ff-result-type                           \ matched field's encoded type (ty-base + ptr-depth)
variable cc-ff-result-array                          \ matched field's inline array length
variable cc-ff-result-record

\ cc-find-field ( name-addr name-len desc -- offset )
: cc-find-field
  cc-ff-desc           !
  cc-ff-needle-len     !
  cc-ff-needle-addr    !
  \ Loop i = 0..field-count-1.
  cc-ff-desc @ cc-sd-field-count                    ( count )
  [lit] 0                                            ( count i )
```

`cc-find-field` compares each field name, publishes its descriptor, type, array length, and record, then removes the loop state before returning the offset
(`forth-bootstrap/cc/100-cc-expr.fth:323`):
```forth chunk=expr-struct-field
  begin,
    over over >                                      ( count i count>i? )
  while,
    \ Compare names at field i.
    cc-ff-desc @ over cc-sd-field-rec                ( count i rec )
    dup cc-sf-name-len cc-ff-needle-len @ = if,
      dup cc-sf-name-addr                           ( count i rec entry-addr )
      cc-ff-needle-addr @ swap                      ( count i rec needle entry )
      cc-ff-needle-len  @                           ( count i rec needle entry u )
      bytes-eq if,                                  ( count i rec )
        dup cc-ff-result-record !
        dup cc-sf-desc cc-ff-result-desc !
        dup cc-sf-type cc-ff-result-type !
        cc-target-lp64 @ if,
          dup cc-sf-array-len cc-ff-result-array !
        else, [lit] 0 cc-ff-result-array ! then,
        cc-sf-offset nip nip exit,                  ( offset )
      then,
    then,
    drop                                            ( count i )
    1+                                              ( count i+1 )
  repeat,
  [lit] 90 cc-die ;

```

## Array indexing helper

A named subscript starts with a symbol, so the legacy helper distinguishes inline storage from a stored pointer before calculating the element address
(`forth-bootstrap/cc/100-cc-expr.fth:347`):
```forth chunk=expr-array-index
\ ===========================================================================
\ cc-parse-array-index — handle `arr[expr]`.
\ ===========================================================================
\ Called from cc-parse-primary AFTER finding an IDENT that resolves to a
\ local-array symbol, local pointer, global array, or global pointer, AND
\ after peeking the next token and seeing '['.  At entry the symbol id is
\ on TOS and the '[' token has been read into tok-* (so the next
\ cc-next-token-keep will advance past it).
\
\ The base is loaded into rdi by one of four paths:
\   inline local array  (sk-local,  len>0)  lea  rdi, [rbp+disp]      \ &arr[0]
\   local pointer       (sk-local,  len=0)  mov  rdi, [rbp+disp]      \ value of p
\   inline global array (sk-global, len>0)  movabs rdi, &globals[off]
\   global pointer      (sk-global, len=0)  movabs rdi, &globals[off]; mov rdi, [rdi]
\
\ Then `arr[i]` becomes:
\     push rdi
\     <eval i>                                 ; rdi = i
\     (shl  rdi, 3)                            ; iff element size is 8
\     pop  rcx
\     add  rdi, rcx                            ; rdi = element address
\
\ Element size is 1 for raw char data (so `argv[i]` and `int arr[N]` work
\ together); 8 for everything else (pointers, ints, struct-pointer slots).
\ The char-step decision is based on the symbol's type after one indexing
\ step yields a single char:
\   inline array of T:  step=1 iff base==ty-char AND ptr-depth==0
\   pointer-to-T:       step=1 iff base==ty-char AND ptr-depth==1
```

`cc-parse-array-index` accepts a local or global symbol and selects its base-loading path
(`forth-bootstrap/cc/100-cc-expr.fth:375`):
```forth chunk=expr-array-index
\
\ This word then marks the result a pending deref (lv-deref) so the consumer
\ either does the load (rvalue use, via cc-emit-materialize) or treats rdi
\ as the destination address (lvalue use in assignment, the deref path).
: cc-parse-array-index                            ( id -- )
  \ Accept sk-local or sk-global.
  dup cc-sym-kind-of sk-local =
  over cc-sym-kind-of sk-global = or 0= if,
    drop
    [lit] 91 cc-die
  then,

  \ Emit base address into rdi.
  dup cc-sym-kind-of sk-global = if,
    dup cc-sym-val-of cc-emit-global-ref          \ rdi = &globals[off]
    dup cc-sym-array-len-of [lit] 0 = if,
      cc-emit-load-via-rdi                        \ pointer global: load slot value
    then,
  else,
    dup cc-sym-array-len-of [lit] 0 > if,
      dup cc-sym-val-of cc-emit-lea-rdi-local     \ inline array: address of slot
    else,
      dup cc-sym-val-of cc-emit-load-local        \ pointer local: load slot value
    then,
  then,

```

The element type survives recursive index parsing on the compiler’s return stack; an array consumes its array dimension, while a pointer loses a pointer level
(`forth-bootstrap/cc/100-cc-expr.fth:401`):
```forth chunk=expr-array-index
  \ Element type of arr[i] plus a byte-step flag, both stashed on the rstack
  \ so they survive the index-expression parse.  An inline array (len>0)
  \ keeps the symbol's type — the subscript consumes the array dimension, not
  \ a pointer level; a pointer (len==0) drops one pointer level.  The step
  \ is one byte iff the element is a plain char, so a chained `[j]` (e.g.
  \ char* v[]; v[i][j]) reads cc-last-expr-type and picks byte stride/deref.
  dup cc-sym-array-len-of [lit] 0 > if,
    cc-sym-type-of                                ( elem-ty )         \ array: keep type
  else,
    cc-sym-type-of                                ( ty )
    dup ty-base swap ty-ptr 1- ty-make            ( elem-ty )         \ ptr: depth-1
  then,
  dup >r                                          ( elem-ty ; R: elem-ty )
  dup ty-base ty-char = swap ty-ptr [lit] 0 = and ( char-step? ; R: elem-ty )
  >r                                              ( ; R: elem-ty char-step? )

```

Generated code saves the base, evaluates and scales the index, then forms an address and marks the resulting element as a pending dereference
(`forth-bootstrap/cc/100-cc-expr.fth:417`):
```forth chunk=expr-array-index
  cc-emit-push-rdi

  \ Parse the index expression.  cc-parse-expr-fwd ends with a materialize
  \ so rdi holds an actual integer.
  cc-parse-expr-fwd

  r@ 0= if,
    cc-emit-shl-rdi-3                             \ rdi *= 8 (non-char step)
  then,

  \ Pop the base, add to scaled index.
  cc-emit-pop-rcx
  cc-emit-add-rdi-rcx

  \ Expect ']'.
  cc-next-token-keep
  tok-kind @ tk-punct <> tok-num @ [char] ] <> or if,
    [lit] 92 cc-die
  then,

  \ rdi now holds the element address; mark it a pending deref so the
  \ consumer either loads or stores depending on context.  A char-step
  \ element (flag still on rstack) is a byte-wide deref, so the eventual
  \ load/store is 1 byte, not 8.  The mark zeroes cc-last-expr-type, so
  \ republish the element type afterwards for any chained postfix `[j]`.
  r> cc-mark-deref
  r> cc-last-expr-type ! ;

```

## Primary expressions

A primary starts with an operand, then lets suffixes refine its result.
We will read the dispatch loop first so each handler has a place in that
process. The source itself assembles the handlers before the loop that
calls them
(`forth-bootstrap/cc/100-cc-expr.fth:674`):
```forth chunk=expr-primary
<<expr-primary-literals>>
<<expr-primary-fn-rvalue>>
<<expr-primary-global>>
<<expr-primary-local>>
<<expr-primary-ident>>
<<expr-primary-paren>>
<<expr-primary-operand>>
<<expr-primary-postfix-incdec>>
<<expr-primary-postfix-index>>
<<expr-primary-postfix-field>>
<<expr-primary-postfix>>
```

### The top: operand, then postfix loop

A primary can grow into a chain such as `head->next->s[i]`; `cc-postfix-op?` and the loop keep consuming suffixes, including native indirect calls
(`forth-bootstrap/cc/100-cc-expr.fth:1182`):
```forth chunk=expr-primary-postfix
\ cc-postfix-op? ( -- f )  True if the current token is a postfix operator.
: cc-postfix-op?
  [char] . cc-tok-punct?
  pt-arrow cc-tok-punct? or
  pt-plus-plus cc-tok-punct? or
  pt-minus-minus cc-tok-punct? or
  [char] [ cc-tok-punct? or
  cc-target-lp64 @ if, lparen cc-tok-punct? or then, ;

\ cc-parse-postfix-ops ( -- )  Zero or more postfix operators applied to
\ the operand just parsed.
: cc-parse-postfix-ops
  begin,
    cc-next-token-keep
    cc-postfix-op?
  while,
    tok-num @                                     ( op )
    dup pt-plus-plus = over pt-minus-minus = or if,
      cc-parse-postfix-inc-dec
    else,
      dup [char] [ = if,
        drop cc-parse-postfix-index
      else,
        dup lparen = cc-target-lp64 @ and if,
          drop cc-native-indirect-fwd
        else,
          cc-parse-postfix-field
        then,
      then,
    then,
```

The first non-postfix token belongs to the enclosing expression, and each new primary begins with cleared lvalue metadata
(`forth-bootstrap/cc/100-cc-expr.fth:1212`):
```forth chunk=expr-primary-postfix
  repeat,
  cc-putback-token ;                              \ not a postfix operator

\ cc-parse-primary ( -- )  An operand, then zero or more postfix operators.
: cc-parse-primary
  cc-mark-not-lvalue                              \ default: not an lvalue
  cc-parse-operand cc-parse-postfix-ops ;

```

`cc-parse-operand` dispatches literals, names, and parentheses; a numeric zero records null-constant status, and a string publishes a character-pointer type
(`forth-bootstrap/cc/100-cc-expr.fth:947`):
```forth chunk=expr-primary-operand
\ cc-parse-operand ( -- )  Read one token and compile the operand it starts:
\ a literal, a name, a cast or a parenthesised expression.
: cc-parse-operand
  cc-next-token-keep
  cc-value-literal-fwd if, exit, then,
  tok-kind @ tk-num = if,
    cc-target-lp64 @ if,
      cc-integer-literal-type cc-last-expr-type !
    then,
    tok-num @ 0= cc-last-expr-null !
    tok-num @ cc-emit-mov-rdi-int exit,           \ widen to imm64 if out of imm32 range
  then,
  tok-kind @ tk-chr = if,
    \ Character literal — value is in tok-num just like a number.
    cc-target-lp64 @ if, ty-int [lit] 0 ty-make cc-last-expr-type ! then,
    tok-num @ 0= cc-last-expr-null !
    tok-num @ cc-emit-mov-rdi-imm32 exit,
  then,
  tok-kind @ tk-str   = if,
    \ A string literal is a char*: "abc"[1] is one byte.
    cc-parse-string-literal
    ty-char [lit] 1 ty-make cc-last-expr-type ! exit,
  then,
  tok-kind @ tk-ident = if, cc-parse-ident          exit, then,
  lparen cc-tok-punct? if,
    cc-try-cast-fwd if, exit, then,              \ '(' TYPE ')' operand
    cc-parse-paren exit,
  then,
  [lit] 97 cc-die ;

```

### String literals

Inline string data needs a jump around it so execution reaches the instruction that loads its address
(`forth-bootstrap/cc/100-cc-expr.fth:674`):
```forth chunk=expr-primary-literals
\ ===========================================================================
\ cc-parse-primary: the operand, then its postfix operators
\ ===========================================================================
\ A primary is an operand (a literal, a name, or a parenthesised expression)
\ followed by any number of postfix operators ('.' '->' '[' '++' '--').
\ Each word below handles one form and returns with exit, as soon as it has
\ compiled it.  Each failure dies through cc-die (020-cc-arena.fth) with its
\ own code; Appendix G of the book lists them.

\ cc-parse-string-literal ( -- )  The current token is a string literal.
\ We emit the bytes inline in the code stream and jump over them, then load
\ their absolute vaddr into rdi:
\     jmp +N            E9 <rel32>          (5 bytes; rel32 patched)
\     <decoded string bytes + NUL>
\   skip:
\     movabs rdi, vaddr 48 BF <imm64>       (10 bytes)
\ Native strings concatenate adjacent tokens after escape decoding. Each
\ piece's temporary terminator is removed; exactly one final NUL remains.
\ Output positions count decoded bytes, including any explicit embedded NUL.
```

`cc-parse-native-string-literal` joins adjacent decoded tokens, retains their combined array length, and becomes the default native string hook
(`forth-bootstrap/cc/100-cc-expr.fth:693`):
```forth chunk=expr-primary-literals
: cc-parse-native-string-literal
  cc-emit-jmp-rel32-placeholder
  cc-here-vaddr swap                              ( str-vaddr fixup-off )
  cc-out-pos @ >r
  begin,
    tok-str-addr @ tok-str-len @ cc-emit-string-bytes
    [lit] 1 cc-out-pos -!
    cc-next-token-keep
    tok-kind @ tk-str <>
  until,
  cc-putback-token
  [lit] 0 cc-emit-byte
  cc-out-pos @ r> - cc-last-expr-array-len !
  cc-patch-rel32-to-here
  cc-emit-movabs-rdi-imm64 ;

defer cc-native-string-fwd
' cc-parse-native-string-literal is cc-native-string-fwd

```

The legacy string path handles the current token, patches the jump over its bytes, and loads their address
(`forth-bootstrap/cc/100-cc-expr.fth:712`):
```forth chunk=expr-primary-literals
: cc-parse-string-literal
  cc-target-lp64 @ if, cc-native-string-fwd exit, then,
  cc-emit-jmp-rel32-placeholder                   ( fixup-off )
  \ Capture the vaddr where the string bytes will start (= current emit
  \ position, NOT the rel32 fixup, so we keep it on the stack under the
  \ fixup).
  cc-here-vaddr                                   ( fixup-off str-vaddr )
  swap                                            ( str-vaddr fixup-off )
  \ Copy decoded string bytes (with NUL terminator).
  tok-str-addr @ tok-str-len @ cc-emit-string-bytes
  \ Patch the jmp's rel32 to land here (right after the string bytes).
  cc-patch-rel32-to-here                          ( str-vaddr )
  \ Emit the movabs rdi, str-vaddr.
  cc-emit-movabs-rdi-imm64 ;

```

### Identifiers, calls, and subscripts

| Identifier hook | Default result |
|---|---|
| `cc-native-intrinsic-fwd` | `cc-native-intrinsic-noop` declines to consume an intrinsic |
| `cc-native-unknown-ident-fwd` | `cc-native-unknown-ident-default` keeps the missing-name sentinel |
| `cc-native-call-qualified-fwd` | `cc-native-call-qualified-default` returns an unqualified result |

These defaults keep name lookup usable without a target-specific intrinsic or call policy
(`forth-bootstrap/cc/100-cc-expr.fth:870`):
```forth chunk=expr-primary-ident
\ cc-parse-ident ( -- )  The current token is an identifier.  Look it up,
\ then peek one token to tell a call, a subscript and a plain reference
\ apart.
\ Optional target intrinsics consume the complete call when handled.
: cc-native-intrinsic-noop [lit] 0 ;
defer cc-native-intrinsic-fwd
' cc-native-intrinsic-noop is cc-native-intrinsic-fwd

: cc-native-unknown-ident-default true ;
defer cc-native-unknown-ident-fwd
' cc-native-unknown-ident-default is cc-native-unknown-ident-fwd

: cc-native-call-qualified-default drop [lit] 0 ;
defer cc-native-call-qualified-fwd
' cc-native-call-qualified-default is cc-native-call-qualified-fwd

```

`cc-parse-ident` resolves enums before suffix dispatch, while a following parenthesis sends callable symbols toward the call parser
(`forth-bootstrap/cc/100-cc-expr.fth:886`):
```forth chunk=expr-primary-ident
: cc-parse-ident
  cc-native-intrinsic-fwd if, exit, then,
  tok-str-addr @ tok-str-len @ cc-sym-find        ( id | -1 )
  dup 0< if, drop cc-native-unknown-ident-fwd then,
  dup 0< if,
    drop
    [lit] 93 cc-die
  then,
  \ Enum constants resolve to their integer value (mov rdi, imm32).
  \ Handle this BEFORE the suffix peek so RED, GREEN etc. work in any
  \ expression context — they're never callable / indexable / assignable.
  dup cc-sym-kind-of sk-enum = if,
    cc-sym-val-of cc-emit-mov-rdi-imm32
    cc-mark-int-value exit,
  then,
  cc-next-token-keep                              \ peek the suffix
  lparen cc-tok-punct? if,
    \ Function call.  The id must refer either to an sk-func (direct call)
    \ or to an sk-local function pointer (indirect call).
    dup cc-sym-kind-of sk-func <> cc-target-lp64 @ 0= and if,
      dup cc-sym-kind-of sk-local =
      over cc-sym-type-of ty-base ty-func = and 0= if,
        drop
        [lit] 94 cc-die
      then,
    then,
```

Call results recover their saved metadata; a legacy named subscript uses the helper above, and a plain reference dispatches by symbol kind
(`forth-bootstrap/cc/100-cc-expr.fth:912`):
```forth chunk=expr-primary-ident
    \ cc-parse-call (above) consumes the '(' (already peeked), parses the
    \ args, emits the call, and leaves the return value in rdi.
    cc-target-lp64 @ if,
      dup cc-native-call-qualified-fwd >r
      dup cc-native-call-result-fwd swap >r >r
      cc-parse-call
      r> r> swap cc-mark-typed-value
      r> cc-last-expr-qualified ! exit,
    then,
    cc-parse-call
    cc-mark-not-lvalue exit,
  then,
  [char] [ cc-tok-punct? if,
    \ Array index.  '[' has been read into tok-*; cc-parse-array-index
    \ consumes through ']'.
    cc-target-lp64 @ 0= if, cc-parse-array-index exit, then,
  then,
  \ A plain reference.  Put back the peeked token.
  cc-putback-token
  dup cc-sym-kind-of sk-func   = if, cc-parse-func-ref   exit, then,
  dup cc-sym-kind-of sk-global = if, cc-parse-global-ref exit, then,
  dup cc-sym-kind-of sk-local  = if, cc-parse-local-ref  exit, then,
  drop
  [lit] 95 cc-die ;

```

Chapter 37 builds `cc-parse-call` and the function machinery. This dispatcher only chooses that path and records the expression result.

### A function name as a value

A function used as an operand needs its address, so `cc-parse-func-ref` emits an immediate or records a pending address fixup; an unevaluated expression does not retain that fixup
(`forth-bootstrap/cc/100-cc-expr.fth:727`):
```forth chunk=expr-primary-fn-rvalue
\ cc-parse-func-ref ( id -- )  A function name as a value — `op = square;`.
\ Load the function's absolute vaddr into rdi via movabs.  Result is not an
\ lvalue.  When val == 0 the function is still a forward prototype; emit a
\ 10-byte movabs placeholder and thread the imm64 patch-offset onto its
\ cc-sym-addr-fixups list so cc-parse-function can patch it once the real
\ vaddr is known.  Without this, M2-Planet code like
\ `common_recursion(expression)` (where `expression` is forward-declared)
\ loads 0 into rdi and crashes at the indirect call.
: cc-parse-func-ref
  dup cc-native-function-desc-fwd >r
  dup cc-sym-val-of [lit] 0 = if,
    cc-emit-movabs-rdi-imm64-placeholder          ( id patch-off )
    cc-expr-unevaluated @ if,
      2drop
    else,
      swap cc-sym-addr-fixups                     ( patch-off list-cell )
      cc-add-fixup-to-list
    then,
  else,
    cc-sym-val-of cc-emit-movabs-rdi-imm64
  then,
  cc-target-lp64 @ if,
    ty-func [lit] 1 ty-make r> cc-mark-typed-value
  else, r> drop cc-mark-not-lvalue then, ;

```

### Globals

The native global path preserves qualification and array shape across marking, leaving scalar storage for a delayed load
(`forth-bootstrap/cc/100-cc-expr.fth:752`):
```forth chunk=expr-primary-global
\ cc-parse-global-ref ( id -- )  A file-scope global.  Emit movabs rdi,
\ <vaddr-placeholder> with a deferred fixup.  Scalar globals are
\ deref-pending lvalues (lv-deref); array globals decay to their address
\ (lv-value).
\
\ The type decides which extra fact the symbol carries (070):
\   ty-struct base -> cc-sym-struct-desc-of (NOT an array length).
\   any other      -> cc-sym-array-len-of (>0 for arrays, 0 otherwise).
: cc-parse-global-ref
  cc-target-lp64 @ if,
    dup cc-sym-qualified cell[] @ >r
    dup cc-sym-array-inner-of >r
    dup cc-sym-val-of cc-emit-global-ref
    dup cc-sym-type-of
    over cc-expr-symbol-desc
    rot cc-sym-array-len-of dup if,                ( ty desc n )
      >r swap [lit] 1 + swap cc-mark-typed-value
      r> cc-last-expr-array-len !
    else,
      drop cc-mark-typed-deref
    then,
    r> cc-last-expr-array-inner !
    r> cc-last-expr-qualified !
    exit,
  then,
```

Legacy global references select a descriptor-bearing address, an array address, or a pending scalar dereference according to the symbol
(`forth-bootstrap/cc/100-cc-expr.fth:777`):
```forth chunk=expr-primary-global
  dup cc-sym-type-of ty-base ty-struct = if,
    \ Struct or struct-pointer global.  Treat like a scalar (deref-pending
    \ lvalue) so assignment works; record the descriptor for any postfix
    \ '.' / '->'.
    dup cc-sym-val-of cc-emit-global-ref
    [lit] 0 cc-mark-deref
    cc-sym-struct-desc-of cc-last-struct-desc ! exit,
  then,
  dup cc-sym-array-len-of [lit] 0 > if,
    \ Global array: rdi := &globals[slot]; not an lvalue.
    cc-sym-val-of cc-emit-global-ref
    cc-mark-not-lvalue exit,
  then,
  \ Global scalar: rdi := &globals[slot]; mark deref-pending so the consumer
  \ either loads (rvalue) or stores via that address (assignment's deref
  \ path).  Record the scalar's type (across the mark, which clears it) so a
  \ following unary '*' knows whether this is a char* (1-byte deref) or a
  \ wider pointer.
  dup cc-sym-type-of >r
  cc-sym-val-of cc-emit-global-ref
  [lit] 0 cc-mark-deref
  r> cc-last-expr-type ! ;

```

### Locals

Native inline objects use their local address; `cc-native-local-load-fwd` reserves the ordinary typed load for scalar locals
(`forth-bootstrap/cc/100-cc-expr.fth:800`):
```forth chunk=expr-primary-local
\ cc-parse-local-ref ( id -- )  A local: struct, struct pointer, array or
\ scalar, told apart by its type.
defer cc-native-local-load-fwd
' cc-emit-load-local-typed is cc-native-local-load-fwd

: cc-parse-local-ref
  cc-target-lp64 @ if,
    dup cc-sym-qualified cell[] @ >r
    cc-check-static-init
    dup cc-sym-array-inner-of >r
    dup cc-sym-array-len-of
    over cc-sym-type-of ty-base ty-struct =
    over [lit] 0 <> or if,                        ( id n )
      over cc-sym-type-of ty-ptr 0= over [lit] 0 <> or if,
        >r dup cc-sym-val-of cc-emit-lea-rdi-local
        dup cc-sym-type-of swap cc-expr-symbol-desc
        r@ if, swap [lit] 1 + swap then,
        cc-mark-typed-value
        cc-last-expr-type @ cc-last-struct-desc @ cc-opaque-scalar-fwd if,
          lv-deref cc-last-lvalue-kind !
        then,
        r> cc-last-expr-array-len !
        r> cc-last-expr-array-inner ! r> cc-last-expr-qualified ! exit,
      then,
    then,
```

A scalar local keeps its slot after loading, whereas the legacy record path keeps the object’s address and descriptor for member selection
(`forth-bootstrap/cc/100-cc-expr.fth:825`):
```forth chunk=expr-primary-local
    drop
    dup cc-sym-val-of dup cc-mark-local-lvalue
    over cc-sym-type-of cc-native-local-load-fwd
    dup cc-sym-type-of cc-last-expr-type !
    cc-expr-symbol-desc cc-last-struct-desc !
    r> cc-last-expr-array-inner ! r> cc-last-expr-qualified ! exit,
  then,
  dup cc-sym-type-of ty-base ty-struct =
  over cc-sym-type-of ty-ptr [lit] 0 = and if,
    \ struct T x;  Emit lea on the first-element slot so rdi holds the
    \ address of the struct.  Then record the descriptor for any following
    \ '.field'.  This is NOT a normal lvalue (you can't assign to a whole
    \ struct); '.field' will mark a deref.
    dup cc-sym-struct-desc-of                     \ descriptor pointer
    swap cc-sym-val-of                            \ slot of field 0 (deepest)
    cc-emit-lea-rdi-local
    cc-mark-not-lvalue
    cc-last-struct-desc ! exit,
  then,
```

Legacy record pointers retain a store slot, arrays supply their address, and plain scalars republish their type after marking
(`forth-bootstrap/cc/100-cc-expr.fth:844`):
```forth chunk=expr-primary-local
  dup cc-sym-type-of ty-base ty-struct = if,
    \ struct T* p;  Load the pointer value; treat as an lvalue local
    \ (lv-local) so plain `p = q;` still works, AND record the descriptor
    \ for '->field'.
    dup cc-sym-struct-desc-of                     \ descriptor pointer
    swap cc-sym-val-of                            \ slot index
    dup cc-mark-local-lvalue
    cc-emit-load-local
    cc-last-struct-desc ! exit,
  then,
  dup cc-sym-array-len-of [lit] 0 > if,
    \ An array decays to &arr[0] — emit lea, not load.  The result is a
    \ pointer value (not an lvalue).
    cc-sym-val-of                                 \ slot of arr[0]
    cc-emit-lea-rdi-local
    cc-mark-not-lvalue exit,
  then,
  \ Plain scalar local.  Save its type across the mark (which clears
  \ cc-last-expr-type) so a following unary '*' can tell a char* (1-byte
  \ deref) from a wider pointer.
  dup cc-sym-type-of >r
  cc-sym-val-of                                   \ slot index
  dup cc-mark-local-lvalue                        \ lv-local, remember slot
  cc-emit-load-local
  r> cc-last-expr-type ! ;

```

These words consume existing symbols. Chapter 35 builds declarations and allocates their storage; the expression checkpoint below needs neither.

### Parentheses

Grouping must preserve a potential destination: `cc-parse-paren` leaves the inner metadata intact, so `(*p)++` and `(x) = y` retain their lvalue meaning
(`forth-bootstrap/cc/100-cc-expr.fth:937`):
```forth chunk=expr-primary-paren
\ cc-parse-paren ( -- )  '(' expr ')'.  Parentheses only group: the inner
\ expression's lvalue kind, slot, type and struct descriptor are left as
\ its parse set them, so `(*p)++`, `(x) = 1` and `(p)->f` work.
: cc-parse-paren
  cc-target-lp64 @ if, cc-parse-comma-fwd else, cc-parse-assign-fwd then,
  cc-next-token-keep
  [char] ) cc-tok-punct? 0= if,
    [lit] 96 cc-die
  then, ;

```

The operand dispatcher asks `cc-try-cast-fwd` before taking this grouping path. Chapter 35 supplies cast recognition. An isolated expression driver must bind that hook even when its input contains no cast.

## The postfix operators

### Increment and decrement

Mutation adds a second question to the destination contract: which value
should the expression supply afterward? Both `++x` and `x++` change the
same object. Prefix supplies the changed value; postfix must preserve the
old value while performing the store. The native path shares one updater
and makes that choice explicit.

The `cc-change-*` cells record the operand metadata, direction, and prefix/postfix choice; the default check validates integer use, and the default update scales pointers before converting back to the stored type
(`forth-bootstrap/cc/100-cc-expr.fth:977`):
```forth chunk=expr-primary-postfix-incdec
variable cc-change-qualified
variable cc-change-type
variable cc-change-desc
variable cc-change-field
variable cc-change-postfix
variable cc-change-delta

\ Validate before inspecting lvalue form: long double uses an address value.
: cc-change-check-default cc-last-expr-type @ cc-value-integer-use-fwd ;
defer cc-change-check-fwd
' cc-change-check-default is cc-change-check-fwd

\ Update RDI's value; the shared caller saves the address and old payload.
: cc-change-value-default
  cc-change-type @ ty-ptr if,
    cc-change-type @ cc-change-desc @ cc-expr-pointee-size
  else, [lit] 1 then,
  cc-change-delta @ * cc-emit-add-rdi-imm32
  \ The sum has the promoted type; converting it, not truncating it, lets a
  \ _Bool's b++ and b-- produce 1 and !b as C requires.
  cc-change-type @ dup cc-unary-type swap cc-emit-convert-value ;
defer cc-change-value-fwd
' cc-change-value-default is cc-change-value-fwd

```

`cc-native-inc-dec` saves the destination, optionally saves the old payload, stores the changed value, and restores the old payload only for postfix use
(`forth-bootstrap/cc/100-cc-expr.fth:1001`):
```forth chunk=expr-primary-postfix-incdec
\ cc-native-inc-dec ( delta postfix? -- )  Mutate one typed lvalue.
: cc-native-inc-dec
  cc-check-static-init cc-change-check-fwd
  cc-change-postfix ! cc-change-delta !
  cc-last-expr-qualified @ cc-change-qualified !
  cc-last-expr-type @ cc-change-type !
  cc-last-struct-desc @ cc-change-desc !
  cc-last-field-rec @ cc-change-field !
  cc-last-lvalue-kind @ lv-local = if,
    cc-last-ident-slot @ cc-emit-lea-rdi-local
  else,
    cc-deref-pending? 0= if, [lit] 113 cc-die then,
  then,
  cc-emit-push-rdi
  cc-change-type @ cc-change-field @ cc-field-load-fwd
  cc-change-postfix @ if, cc-emit-push-rdi then,
  cc-change-value-fwd
  cc-change-postfix @ if, cc-emit-pop-rdx then,
  cc-emit-pop-rcx
  cc-change-type @ cc-change-field @ cc-field-store-fwd
  cc-change-postfix @ if,
    [lit] 72 cc-emit-byte [lit] 137 cc-emit-byte [lit] 215 cc-emit-byte
  then,                                           \ mov rdi,rdx (old value)
  cc-change-type @ cc-change-field @ cc-field-value-type-fwd
  cc-change-desc @ cc-mark-typed-value
  cc-change-qualified @ cc-last-expr-qualified ! ;

```

Legacy postfix mutation of a local updates its slot while leaving the already-loaded old value in `rdi`
(`forth-bootstrap/cc/100-cc-expr.fth:1028`):
```forth chunk=expr-primary-postfix-incdec
\ cc-parse-postfix-inc-dec ( op -- )  Postfix '++' / '--' on an lvalue.
\ For a local, the operand parse already loaded the old value into rdi and
\ recorded the slot (lv-local): bump the slot in place.  For a pointer
\ target, element or field, rdi holds its address (lv-deref /
\ lv-deref-byte): load the old value through it and bump the memory in
\ place.  Either way rdi keeps the old value, which is not an lvalue but
\ keeps the operand's type, so `*s++` on a char* loads one byte.
: cc-parse-postfix-inc-dec
  cc-target-lp64 @ if,
    pt-plus-plus = if, [lit] 1 else, [lit] 0 [lit] 1 - then,
    true cc-native-inc-dec exit,
  then,
  cc-last-expr-type @ >r                          ( op ; R: ty )
  cc-last-lvalue-kind @ lv-local = if,
    pt-plus-plus = if,
      cc-last-ident-slot @ cc-emit-inc-mem-local
    else,
      cc-last-ident-slot @ cc-emit-dec-mem-local
    then,
  else,
```

For a pending dereference, the address moves to `rcx` before the old value is loaded and memory is changed; the result retains its type but loses assignability
(`forth-bootstrap/cc/100-cc-expr.fth:1048`):
```forth chunk=expr-primary-postfix-incdec
    cc-deref-pending? 0= if,
      drop
      [lit] 98 cc-die
    then,
    cc-last-lvalue-kind @ lv-deref-byte =         ( op byte? )
    cc-emit-mov-rcx-rdi                           \ rcx := address
    dup cc-emit-load-via-rcx                      \ rdi := old value
    swap pt-plus-plus = if,
      cc-emit-inc-via-rcx
    else,
      cc-emit-dec-via-rcx
    then,
  then,
  cc-mark-not-lvalue
  r> cc-last-expr-type ! ;

```

### Subscripts after a value

`cc-index-base-fwd` and `cc-member-base-fwd` initially share the empty `cc-postfix-base-default`, reserving a target check before suffix processing
(`forth-bootstrap/cc/100-cc-expr.fth:1064`):
```forth chunk=expr-primary-postfix-index
\ cc-parse-postfix-index ( -- )  Postfix '[' INDEX ']' applied to whatever
\ value the primary has produced so far (typically after a chain of '.' /
\ '->').  Materialize so rdi holds the actual pointer value (not a
\ deref-pending address), push it, parse the index, scale, add, mark deref.
\ Stride is 1 (byte) iff the subscripted value is a char pointer (e.g.
\ `head->s[i]` where s is char*) — M2-Planet's tokenizer compares
\ `global_token->s[0]` against digit/letter sets, which only works when each
\ byte is loaded individually.  Everything else (int*, struct*, untyped)
\ uses qword stride and qword deref.
: cc-postfix-base-default ;
defer cc-index-base-fwd
defer cc-member-base-fwd
' cc-postfix-base-default is cc-index-base-fwd
' cc-postfix-base-default is cc-member-base-fwd
```

Native indexing preserves qualification and row width while parsing the index, then marks either a remaining row or the selected element
(`forth-bootstrap/cc/100-cc-expr.fth:1078`):
```forth chunk=expr-primary-postfix-index
: cc-parse-postfix-index
  cc-index-base-fwd
  cc-target-lp64 @ if,
    cc-last-expr-qualified @ >r
    \ An inline matrix already denotes its storage. Subscript it without
    \ manufacturing a pointer-to-row, which would discard qualification.
    cc-last-expr-array-len @ 0= if, cc-emit-materialize then,
    cc-last-expr-type @ cc-last-struct-desc @      ( ty desc )
    cc-last-expr-array-inner @ >r
    cc-emit-push-rdi
    cc-parse-expr-fwd
    cc-last-expr-type @ cc-value-integer-use-fwd
    2dup cc-expr-pointee-size
    r@ if, r@ * then,
    cc-emit-scale-rdi
    cc-emit-pop-rcx cc-emit-add-rdi-rcx
    cc-next-token-keep
    [char] ] cc-tok-punct? 0= if, [lit] 99 cc-die then,
    r@ if,
      cc-mark-typed-value
      r> cc-last-expr-array-len !
    else,
      r> drop swap cc-expr-pointee-type swap cc-mark-typed-deref
    then,
    r> cc-last-expr-qualified !
    exit,
  then,
```

The legacy path materializes a pointer before saving it, uses `cc-char-ptr?` for byte stride, and republishes the pointee type for another suffix
(`forth-bootstrap/cc/100-cc-expr.fth:1105`):
```forth chunk=expr-primary-postfix-index
  \ Keep the subscripted value's type on the rstack: the index parse
  \ overwrites cc-last-expr-type.
  cc-emit-materialize
  cc-last-expr-type @ >r                          \ R: pre-subscript ty
  cc-emit-push-rdi
  cc-parse-expr-fwd
  r@ cc-char-ptr? 0= if,
    cc-emit-shl-rdi-3                             \ char*: byte offset, no shift
  then,
  cc-emit-pop-rcx
  cc-emit-add-rdi-rcx
  cc-next-token-keep
  [char] ] cc-tok-punct? 0= if,
    [lit] 99 cc-die
  then,
  \ Mark deref: byte-width iff we just subscripted a char*.  The post-step
  \ expression type drops one level of indirection — record it so chained
  \ `[i][j]` (char**) and following postfix ops can see the right type.
  r@ cc-char-ptr? cc-mark-deref
  r@ ty-ptr [lit] 0 > if,
    r@ ty-base r@ ty-ptr 1- ty-make cc-last-expr-type !
  then,
  r> drop ;

```

For `v[i][j]` with `v` pointing to character pointers, the first result denotes a pointer slot. The next subscript materializes that slot to get the character pointer. Its final pending dereference therefore has byte width.

### Fields after a value

`->` needs the stored pointer value, whereas `.` uses an object address directly; both add the offset returned by `cc-find-field`
(`forth-bootstrap/cc/100-cc-expr.fth:1129`):
```forth chunk=expr-primary-postfix-field
\ cc-parse-postfix-field ( op -- )  '.' or '->' followed by a field name.
: cc-parse-postfix-field
  cc-member-base-fwd
  cc-target-lp64 @ if,
    dup [char] . = cc-last-lvalue-kind @ lv-temporary = and >r
  then,
  cc-last-struct-desc @ [lit] 0 = if,
    [lit] 100 cc-die
  then,
  \ '->': rdi must hold the pointer's value.  A struct-pointer local is
  \ already loaded (lv-local, materialize is a no-op); a struct-pointer
  \ global or field is still an address (lv-deref), so load it.
  \ '.': rdi holds the struct's base address (lv-value); no load.
  \ Materialize keeps cc-last-struct-desc, which the lookup reads.
  pt-arrow = if,
    cc-emit-materialize
  then,
  cc-next-token-keep
  tok-kind @ tk-ident <> if,
    [lit] 101 cc-die
  then,
  tok-str-addr @ tok-str-len @ cc-last-struct-desc @
  cc-find-field                                   ( offset )
  cc-emit-add-rdi-imm32
```

The selected field republishes its type and descriptor for chaining; native handling also combines qualification, retains array shape, and prevents a temporary record’s member from becoming assignable
(`forth-bootstrap/cc/100-cc-expr.fth:1153`):
```forth chunk=expr-primary-postfix-field
  cc-target-lp64 @ if,
    cc-last-expr-qualified @ >r
    cc-ff-result-type @ cc-ff-result-desc @
    cc-ff-result-array @ if,
      swap [lit] 1 + swap cc-mark-typed-value
      cc-ff-result-array @ cc-last-expr-array-len !
      cc-ff-result-record @ cc-sf-array-inner cc-last-expr-array-inner !
    else, cc-mark-typed-deref then,
    cc-ff-result-record @ cc-last-field-rec !
    cc-ff-result-record @ cc-field-qualified r> or cc-last-expr-qualified !
    \ A scalar member of a non-lvalue record is a value too. Arrays retain
    \ their normal decay into the independent temporary's inline storage.
    r> if,
      cc-last-expr-array-len @ 0= if, cc-emit-materialize then,
      lv-temporary cc-last-lvalue-kind !
    then,
    exit,
  then,
  [lit] 0 cc-mark-deref
  \ Propagate the field's pointee descriptor so chained '->' / '.' (e.g.
  \ `head->next->prev`) can resolve subsequent field lookups.  Stays 0
  \ when the field isn't a struct pointer.
  cc-ff-result-desc @ cc-last-struct-desc !
  \ Record the field's type so a following postfix '[' can detect
  \ char-pointer subscripts (e.g. `head->s[0]`) and emit byte stride/load
  \ instead of qword.  cc-mark-deref cleared this slot above, so set it
  \ after the mark.
  cc-ff-result-type @ cc-last-expr-type ! ;

```

## `cc-parse-unary`: prefix operators

A recursive unary operand supports chains such as `**p`; the header describes the legacy address-of restriction, while the native branch below accepts general addressable operands
(`forth-bootstrap/cc/100-cc-expr.fth:1220`):
```forth chunk=expr-unary
\ ===========================================================================
\ cc-parse-unary: ('&' unary | '*' unary | primary)
\ ===========================================================================
\ Disambiguation: at unary position, '*' is dereference and '&' is address-of;
\ at binary position (handled by cc-parse-mul) '*' means multiply.
\
\ The address-of operand is restricted to a simple local IDENT; it emits
\ `lea rdi, [rbp - 8*(slot+1)]`.  More complex address expressions such as
\ `&*p` or `&arr[i]` are not implemented.
\
\ For dereference, the operand is parsed as a (recursive) unary expression so
\ `**p` works.  We materialize the operand (turning any pending deref into a
\ loaded value) so rdi holds the *address* that the outer '*' should target,
\ then mark it lv-deref — leaving the load for the consumer.

```

### Measuring an operand

`sizeof` asks about the operand's storage rather than its contents. For
an array, that means retaining its shape instead of treating it as a
pointer. For a native expression operand, it also means learning the type
without leaving code that evaluates the expression at runtime.

The legacy `sizeof` dispatcher keeps its answer in `cc-sizeof-bytes`, so each branch can update the same cell
(`forth-bootstrap/cc/100-cc-expr.fth:1235`):
```forth chunk=expr-unary
\ cc-parse-sizeof — `sizeof '(' (type-spec | EXPR) ')'`.
\ Called with the `sizeof` keyword token already consumed.
\
\ Type-spec forms:
\   sizeof(int)            sizeof(char)        sizeof(void)
\   sizeof(int*)           sizeof(int**)       ...
\   sizeof(struct TAG)
\   sizeof(typedef-name)
\
\ EXPR forms supported here are bare identifiers:
\   sizeof(scalar-local)   -> sizeof(scalar-type)
\   sizeof(array-local)    -> N * 8                            (no decay)
\   sizeof(struct-local)   -> descriptor->total-size
\
\ Always emits `mov rdi, imm32` with the size in bytes; result is not an lvalue.
\
\ Implementation note: this routine stages the computed byte count in
\ cc-sizeof-bytes so the deeply-nested if/else dispatch needn't preserve
\ a value on the data stack across the recursive '*'-counting / lookup paths.
\ Pointer modifiers '*+' are accepted on every type-spec branch (struct,
\ typedef, primitive).
variable cc-sizeof-bytes

```

Pointer modifiers replace the staged size, and `cc-native-sizeof-expr-size` measures preserved array shape; the separate type-name path can replace `cc-sizeof-type-size-fwd`
(`forth-bootstrap/cc/100-cc-expr.fth:1258`):
```forth chunk=expr-unary
\ cc-sizeof-count-stars-add ( -- )  Read zero-or-more '*' tokens.  Each star
\ overrides the result with 8 (a pointer is always 8 bytes regardless of
\ pointee).  The first non-'*' token is left current for the caller.
: cc-sizeof-count-stars-add
  begin,
    cc-next-token-keep
    tok-kind @ tk-punct = tok-num @ [char] * = and
  while,
    [lit] 8 cc-sizeof-bytes !
  repeat, ;

\ Native sizeof parses its operand without retaining any emitted code or
\ relocations. An array's length/row metadata prevents its normal decay.
: cc-native-sizeof-expr-size                     ( -- bytes )
  cc-last-field-rec @ cc-field-use-fwd
  cc-last-expr-type @ cc-last-struct-desc @
  cc-last-expr-array-len @ if,
    cc-expr-pointee-size cc-last-expr-array-len @ *
    cc-last-expr-array-inner @ if, cc-last-expr-array-inner @ * then,
  else, cc-expr-type-size then, ;

defer cc-sizeof-type-size-fwd
' cc-expr-type-size is cc-sizeof-type-size-fwd

```

`cc-native-sizeof` parses an unevaluated operand, then restores the output cursor and global-fixup count so the tentative code is discarded
(`forth-bootstrap/cc/100-cc-expr.fth:1282`):
```forth chunk=expr-unary
: cc-native-sizeof                              ( -- bytes )
  cc-out-pos @ >r cc-gfixup-count @ >r
  cc-expr-unevaluated @ >r true cc-expr-unevaluated !
  cc-next-token-keep
  lparen cc-tok-punct? if,
    cc-next-token-keep
    cc-sizeof-type-start-fwd if,
      cc-sizeof-type-fwd cc-sizeof-type-size-fwd
      cc-next-token-keep
      begin, [char] [ cc-tok-punct? while,
        cc-parse-const-fwd *
        cc-next-token-keep
        [char] ] cc-tok-punct? 0= if, [lit] 110 cc-die then,
        cc-next-token-keep
      repeat,
      [char] ) cc-tok-punct? 0= if, [lit] 110 cc-die then,
    else,
      \ `(expr)` is only the primary of a unary operand: postfix operators
      \ after it still apply, so `sizeof (a)[0]` is sizeof ((a)[0]).
      cc-putback-token cc-mark-not-lvalue
      cc-parse-paren cc-parse-postfix-ops
      cc-native-sizeof-expr-size
    then,
  else,
    cc-putback-token cc-parse-unary-fwd
    cc-native-sizeof-expr-size
  then,
  r> cc-expr-unevaluated ! r> cc-gfixup-count ! r> cc-out-pos ! ;
```

A parenthesized expression can have a suffix outside its closing parenthesis: `sizeof (a)[i]` measures the subscripted operand. The native path therefore runs the postfix loop before measuring it. Type-name recognition comes from Chapter 35.

`cc-parse-sizeof` chooses the native path first; its legacy record-type case obtains the descriptor’s total size
(`forth-bootstrap/cc/100-cc-expr.fth:1310`):
```forth chunk=expr-unary

: cc-parse-sizeof
  cc-target-lp64 @ if,
    cc-native-sizeof cc-emit-mov-rdi-int
    ty-ulong [lit] 0 ty-make [lit] 0 cc-mark-typed-value exit,
  then,
  \ Expect '('.  We inline the check because cc-expect-punct-c lives in
  \ 110-cc-decl.fth (loaded AFTER 100-cc-expr.fth) and isn't visible yet.
  cc-next-token-keep
  tok-kind @ tk-punct <> tok-num @ lparen <> or if,
    [lit] 102 cc-die
  then,
  cc-next-token-keep
  tok-kind @ tk-kw = if,
    tok-kw-id @ kw-struct = if,
      \ struct TAG — look up descriptor.
      cc-next-token-keep
      tok-kind @ tk-ident <> if,
        [lit] 103 cc-die
      then,
      tok-str-addr @ tok-str-len @ cc-sym-find-tag
      dup 0< if,
        [lit] 104 cc-die
      then,
      dup cc-sym-kind-of sk-struct <> if,
        [lit] 105 cc-die
      then,
      cc-sym-val-of cc-sd-total-size cc-sizeof-bytes !
      cc-sizeof-count-stars-add
    else,
```

Primitive and typedef operands select a base size before pointer modifiers override it
(`forth-bootstrap/cc/100-cc-expr.fth:1340`):
```forth chunk=expr-unary
      tok-kw-id @ kw-int = if,
        [lit] 8 cc-sizeof-bytes !
      else,
        tok-kw-id @ kw-char = if,
          [lit] 1 cc-sizeof-bytes !
        else,
          tok-kw-id @ kw-void = if,
            [lit] 0 cc-sizeof-bytes !
          else,
            [lit] 106 cc-die
          then,
        then,
      then,
      cc-sizeof-count-stars-add
    then,
  else,
    tok-kind @ tk-ident = if,
      tok-str-addr @ tok-str-len @ cc-sym-find
      dup 0< if,
        [lit] 107 cc-die
      then,
      dup cc-sym-kind-of sk-typedef = if,
        \ Typedef name -> compute base size, then any extra stars override to 8.
        cc-sym-val-of ty-size cc-sizeof-bytes !
        cc-sizeof-count-stars-add
      else,
```

A legacy local operand is measured as a record, pointer, array, or scalar; unsupported names fail instead of being evaluated
(`forth-bootstrap/cc/100-cc-expr.fth:1366`):
```forth chunk=expr-unary
        dup cc-sym-kind-of sk-local = if,
          \ Local — branch on struct vs array vs scalar.
          dup cc-sym-type-of ty-base ty-struct = if,
            dup cc-sym-type-of ty-ptr [lit] 0 = if,
              \ struct T x; — total-size of the descriptor.
              cc-sym-struct-desc-of cc-sd-total-size cc-sizeof-bytes !
            else,
              \ struct T* p; — 8 bytes.
              drop [lit] 8 cc-sizeof-bytes !
            then,
          else,
            dup cc-sym-array-len-of [lit] 0 > if,
              \ Array — N * 8 (this subset assumes int elements here).
              cc-sym-array-len-of [lit] 8 * cc-sizeof-bytes !
            else,
              \ Scalar.
              cc-sym-type-of ty-size cc-sizeof-bytes !
            then,
          then,
          cc-next-token-keep                       \ should land on ')'
        else,
          drop
          [lit] 108 cc-die
        then,
      then,
    else,
      [lit] 109 cc-die
    then,
  then,
```

The size becomes an immediate result after the closing parenthesis; the following `cc-name-alone?` helper preserves lexer state while detecting a suffix
(`forth-bootstrap/cc/100-cc-expr.fth:1395`):
```forth chunk=expr-unary
  \ Current token must be ')'.
  tok-kind @ tk-punct <> tok-num @ [char] ) <> or if,
    [lit] 110 cc-die
  then,
  cc-sizeof-bytes @ cc-emit-mov-rdi-imm32
  cc-mark-not-lvalue ;

\ cc-name-alone? ( -- f )  The current token is a name; true unless a
\ postfix operator or a call follows it (`--b->n` bumps the field, not b).
\ Restores the lexer state.
: cc-name-alone?
  cc-peek-mark cc-lex-mark
  cc-next-token
  cc-postfix-op? lparen cc-tok-punct? or 0=
  cc-peek-mark cc-lex-reset ;

```

### Prefix mutation

Prefix mutation uses the same native updater with postfix disabled; the legacy fast path applies only when the local name has no suffix
(`forth-bootstrap/cc/100-cc-expr.fth:1411`):
```forth chunk=expr-unary
\ cc-parse-prefix-inc-dec ( delta -- )  delta = 1 (for ++) else dec.
\ Called with the '++' / '--' punct ALREADY consumed.  A plain local (a
\ name with no postfix operator after it) is bumped in its slot:
\   inc/dec qword [rbp+disp]    ; bump slot in-place
\   mov rdi, [rbp+disp]         ; load new value
\ Any other operand is parsed as a unary expression, which must leave the
\ address of a pointer target, element or field (else die 113); that is
\ bumped through rcx and the new value loaded.  The result is not an
\ lvalue; it keeps the operand's type.
: cc-parse-prefix-inc-dec                         ( delta -- )
  cc-target-lp64 @ if,
    cc-parse-unary-fwd
    0= if, [lit] 0 [lit] 1 - else, [lit] 1 then,
    [lit] 0 cc-native-inc-dec exit,
  then,
  cc-next-token-keep
  tok-kind @ tk-ident = if,
    tok-str-addr @ tok-str-len @ cc-sym-find      ( delta id )
    dup 0< 0= if, dup cc-sym-kind-of sk-local = else, [lit] 0 then,
    cc-name-alone? and if,
```

A bare local is changed before loading its result; other operands must yield a pending address, which is changed before being read
(`forth-bootstrap/cc/100-cc-expr.fth:1431`):
```forth chunk=expr-unary
      dup cc-sym-type-of >r
      cc-sym-val-of                               ( delta slot ; R: ty )
      swap                                        ( slot delta )
      [lit] 1 = if,
        dup cc-emit-inc-mem-local
      else,
        dup cc-emit-dec-mem-local
      then,
      cc-emit-load-local                          \ rdi := updated value
      cc-mark-not-lvalue
      r> cc-last-expr-type ! exit,
    then,
    drop
  then,
  cc-putback-token
  cc-parse-unary-fwd
  cc-deref-pending? 0= if,
    [lit] 113 cc-die
  then,
  cc-last-expr-type @ >r                          ( delta ; R: ty )
  cc-last-lvalue-kind @ lv-deref-byte =  swap     ( byte? delta )
  cc-emit-mov-rcx-rdi                             \ rcx := address
  [lit] 1 = if,
    dup cc-emit-inc-via-rcx
  else,
    dup cc-emit-dec-via-rcx
  then,
  cc-emit-load-via-rcx                            \ rdi := updated value
  cc-mark-not-lvalue
  r> cc-last-expr-type ! ;
```

That lookahead matters in `--b->n`: the destination is the member, not the local holding `b`. Both prefix and postfix return values, so another increment or decrement cannot use their result as a destination.

### Taking an address

`cc-array-address-default` discards shape arguments and adds indirection; the native `&` path first checks that its operand denotes addressable storage
(`forth-bootstrap/cc/100-cc-expr.fth:1461`):
```forth chunk=expr-unary

: cc-array-address-default ( type descriptor count inner -- type descriptor )
  2drop swap [lit] 1 + swap ;
defer cc-array-address-fwd
' cc-array-address-default is cc-array-address-fwd

: cc-parse-unary
  cc-next-token-keep
  kw-sizeof cc-tok-kw? if,
    \ sizeof(TYPE).  The `sizeof` keyword is the current token; we just
    \ leave it as "consumed" (no putback) and dispatch into cc-parse-sizeof.
    cc-parse-sizeof exit,
  then,
  [char] & cc-tok-punct? if,
    cc-target-lp64 @ if,
      cc-parse-unary
      cc-last-lvalue-kind @ lv-temporary = if, [lit] 116 cc-die then,
      cc-last-field-rec @ cc-field-use-fwd
      cc-last-lvalue-kind @ lv-local = if,
        cc-last-ident-slot @ cc-emit-lea-rdi-local
      else,
        cc-deref-pending? cc-last-struct-desc @ [lit] 0 <> or
        cc-last-expr-array-len @ [lit] 0 <> or
        cc-last-expr-type @ ty-base ty-func = or
        0= if, [lit] 116 cc-die then,
      then,
```

Array address formation can replace the default hook, while other native operands preserve qualification; legacy `&` accepts only a local name
(`forth-bootstrap/cc/100-cc-expr.fth:1487`):
```forth chunk=expr-unary
      cc-last-expr-array-len @ if,
        cc-last-expr-type @ cc-last-struct-desc @
        cc-last-expr-array-len @ cc-last-expr-array-inner @ cc-array-address-fwd
      else,
        cc-last-expr-type @
        dup ty-func [lit] 1 ty-make = cc-last-lvalue-kind @ lv-value = and
        0= if, [lit] 1 + then, cc-last-struct-desc @
      then,
      cc-last-expr-qualified @ >r cc-mark-typed-value
      r> cc-last-expr-qualified ! exit,
    then,
    \ '&' = address-of.  Operand must be a simple local IDENT.
    cc-next-token-keep
    tok-kind @ tk-ident <> if,
      [lit] 114 cc-die
    then,
    tok-str-addr @ tok-str-len @ cc-sym-find
    dup 0< if,
      drop
      [lit] 115 cc-die
    then,
    dup cc-sym-kind-of sk-local <> if,
      drop
      [lit] 116 cc-die
    then,
    cc-sym-val-of                                 \ slot
    cc-emit-lea-rdi-local
    cc-mark-not-lvalue exit,                      \ &x is a value, not an lvalue
  then,
```

### Dereferencing and transforming a value

Unary `*` materializes its pointer operand, then marks the pointed-to storage for a delayed load; preserving the pointee type keeps chained dereferences correctly sized
(`forth-bootstrap/cc/100-cc-expr.fth:1516`):
```forth chunk=expr-unary
  [char] * cc-tok-punct? if,
    \ '*' = dereference.  A char* operand (ty-char, ptr-depth 1) derefs to a
    \ single byte; int*, T**, etc. deref to a qword.  The operand's type sits
    \ in cc-last-expr-type when it came from a scalar variable (recorded in
    \ cc-parse-primary), so `*p = c` on a char* emits a 1-byte store instead
    \ of clobbering 8 bytes.  The mark clears the type; keep it on the stack.
    cc-parse-unary
    cc-emit-materialize                           \ operand is now a value (an address)
    cc-target-lp64 @ if,
      cc-last-expr-qualified @ >r
      cc-last-expr-type @ cc-expr-pointee-type
      cc-last-struct-desc @ cc-mark-typed-deref
      r> cc-last-expr-qualified ! exit,
    then,
    cc-last-expr-type @                           ( ty ; 0 if untracked )
    dup cc-char-ptr? cc-mark-deref                \ defer the load; *char* is 1 byte
    dup ty-ptr [lit] 0 > if,                      \ record pointee type for chained ops
      dup ty-base swap ty-ptr 1- ty-make cc-last-expr-type !
    else,
      drop
    then,
    exit,
  then,
```

| Prefix input | Result handler |
|---|---|
| `++`, `--` | `cc-parse-prefix-inc-dec`, returning the changed value |
| `-` | Negation, with native promotion and conversion |
| `!` | `cc-value-not-fwd`, returning an integer truth value |
| `~` | Complement, with native promotion and conversion |
| Native `+` | `cc-value-plus-fwd`, followed by promotion |
| No prefix | Put back the token and parse a primary |

The value-transforming cases consume their recursive operand before marking the result
(`forth-bootstrap/cc/100-cc-expr.fth:1539`):
```forth chunk=expr-unary
  \ Prefix '++' / '--'.  Bump the operand in place, leave the new value in
  \ rdi.  cc-parse-prefix-inc-dec takes 1 for ++, anything else for --.
  pt-plus-plus   cc-tok-punct? if, [lit] 1 cc-parse-prefix-inc-dec exit, then,
  pt-minus-minus cc-tok-punct? if, [lit] 0 cc-parse-prefix-inc-dec exit, then,
  \ '-', '!' and '~' parse their operand, materialize it, and emit one
  \ operation on rdi ('!' gives rdi := (rdi == 0)).
  [char] - cc-tok-punct? if,
    cc-parse-unary cc-emit-materialize
    cc-target-lp64 @ if,
      cc-last-expr-type @ cc-unary-type
      cc-value-negate-fwd dup cc-emit-convert-rdi
      cc-last-struct-desc @ cc-mark-typed-value exit,
    then,
    cc-emit-neg-rdi cc-mark-not-lvalue exit,
  then,
  [char] ! cc-tok-punct? if,
    cc-parse-unary cc-emit-materialize
    cc-value-not-fwd cc-mark-int-value exit,
  then,
```

Complement and native unary plus complete the dispatch; the fallback lets primary parsing see the untouched token
(`forth-bootstrap/cc/100-cc-expr.fth:1558`):
```forth chunk=expr-unary
  [char] ~ cc-tok-punct? if,
    cc-parse-unary cc-emit-materialize
    cc-target-lp64 @ if,
      cc-last-expr-type @ cc-unary-type
      cc-value-complement-fwd dup cc-emit-convert-rdi
      [lit] 0 cc-mark-typed-value exit,
    then,
    cc-emit-not-rdi cc-mark-not-lvalue exit,
  then,
  cc-target-lp64 @ if,
    [char] + cc-tok-punct? if,
      cc-parse-unary cc-emit-materialize
      cc-value-plus-fwd
      cc-last-expr-type @ cc-unary-type dup cc-emit-convert-rdi
      cc-last-struct-desc @ cc-mark-typed-value exit,
    then,
  then,
  \ Not a unary operator — putback so primary sees the same token.
  cc-putback-token
  cc-parse-primary ;

```

## Ternary

`cc-parse-ternary` turns the condition into a branch around the true arm.
In the checkpoint's `(-3 < 0) ? 7 : 9`, that branch selects which value
the program produces at runtime
(`forth-bootstrap/cc/100-cc-expr.fth:2128`):
```forth chunk=expr-ternary
\ ===========================================================================
\ Ternary  cond '?' then ':' else
\ ===========================================================================
\ Right-associative; the two arms recurse through cc-parse-assign so that
\ chained `a ? b : c ? d : e` parses as `a ? b : (c ? d : e)` and lower-
\ precedence comma-free assignment lives inside an arm.
\
\ Codegen:
\   <eval cond>
\   test rdi,rdi
\   jz   .else
\   <eval then-arm>
\   jmp  .end
\ .else:
\   <eval else-arm>
\ .end:

: cc-parse-ternary
  cc-parse-log-or
  cc-next-token-keep
  tok-kind @ tk-punct = tok-num @ [char] ? = and if,
    \ '?' — consume and emit branch.
    cc-emit-materialize
    cc-value-test-fwd
    cc-emit-jz-rel32-placeholder >r               \ R: f-else
    cc-target-lp64 @ if, cc-parse-comma-fwd else, cc-parse-assign-fwd then,
                                                  \ then-arm (right-assoc)
    cc-emit-materialize
```

The true arm jumps past the false arm; after the colon, the false-branch fixup can be patched to the current position
(`forth-bootstrap/cc/100-cc-expr.fth:2156`):
```forth chunk=expr-ternary
    cc-target-lp64 @ if,
      cc-last-expr-type @ cc-last-struct-desc @ cc-last-expr-array-inner @ cc-last-expr-null @ cc-last-expr-qualified @
    then,
    cc-emit-jmp-rel32-placeholder >r              \ R: f-else f-end
    \ Expect ':' — inline check (cc-expect-punct-c lives in 110-cc-decl.fth).
    cc-next-token-keep
    tok-kind @ tk-punct <> tok-num @ [char] : <> or if,
      [lit] 117 cc-die
    then,
    \ Pop fixups: top of rstack is f-end, second is f-else.
    r> r>                                         ( f-end f-else )
    cc-patch-rel32-to-here                        \ patch f-else
    >r
    cc-parse-assign-fwd                         \ else-arm
    cc-emit-materialize
```

Native joining waits until both arm types are known, allowing separate conversions or an aggregate hook; the legacy join simply publishes a value
(`forth-bootstrap/cc/100-cc-expr.fth:2171`):
```forth chunk=expr-ternary
    cc-target-lp64 @ if,
      r> cc-aggregate-ternary-fwd 0= if,
        \ The true arm jumps past the false arm and its conversion. Only
        \ after both types are known can either selected value be converted.
        cc-value-ternary-split-fwd if,
          >r cc-expr-save-native-types cc-array-ternary-fwd cc-value-ternary-fwd
          cc-expr-right-type @ cc-expr-common @ cc-emit-convert-value
          cc-emit-jmp-rel32-placeholder r> cc-patch-rel32-to-here >r
          cc-expr-left-type @ cc-expr-common @ cc-emit-convert-value
          r> cc-patch-rel32-to-here
        else,
          cc-patch-rel32-to-here
          cc-expr-save-native-types cc-array-ternary-fwd cc-value-ternary-fwd
          cc-expr-common @ cc-emit-convert-rdi
        then,
        cc-expr-common @ cc-expr-common-desc cc-mark-typed-value
        cc-expr-common @ ty-ptr if,
          cc-expr-left-qualified @ cc-expr-right-qualified @ or cc-last-expr-qualified !
        then,
        cc-expr-common-inner cc-last-expr-array-inner !
      then,
    else,
      r> cc-patch-rel32-to-here
      cc-mark-not-lvalue
    then,
  else,
    cc-putback-token
  then, ;

```

Both arms are compiled, but execution follows only the selected arm. The false arm recurses through assignment, which also makes nested conditionals associate to the right. This grammar accepts a bare assignment in the false arm; that is broader than C’s conditional-expression grammar. Chapter 41 supplies native join policy, and Chapter 49 supplies aggregate joins.

## The top-level driver

`cc-parse-comma` sequences native comma operands, and `cc-parse-expr` materializes the final result for its caller
(`forth-bootstrap/cc/100-cc-expr.fth:2419`):
```forth chunk=expr-top
\ ===========================================================================
\ cc-parse-expr: top-level entry
\ ===========================================================================

\ cc-parse-expr always ends with a materialize so any consumer (return,
\ if/while cond, expression-statement, function-call argument, decl
\ initializer, ...) receives an actual value in rdi rather than a pending
\ deref-address.
: cc-parse-comma
  cc-parse-assign
  cc-target-lp64 @ if,
    begin,
      cc-next-token-keep [char] , cc-tok-punct?
    while,
      cc-check-static-init
      cc-emit-materialize cc-parse-assign
      [lit] 0 cc-last-expr-null !               \ comma results are not constants
    repeat,
    cc-putback-token
  then, ;

: cc-parse-expr
  cc-parse-comma
  cc-emit-materialize ;

```

Parentheses call an entry that preserves lvalues; ordinary value consumers use `cc-parse-expr`. That distinction prevents grouping from accidentally turning a destination into a read.

Preserving `(x)` does not make `(0, x)` assignable in C, but the LP64
comma path also keeps the final operand's lvalue state, so
`int main(void) { int x=0; (0,x)=1; return x; }` compiles and returns 1.
In ISO C a comma result is not an lvalue; treat this as a dialect quirk,
not a feature. The core profile has no comma operator at all. See
[Appendix F](60-c-subset.md#observed-profile-boundaries).

## Constant expressions

An array bound must be known when the compiler reserves storage; a case
label must be known when it builds dispatch. Neither can wait for the
generated program to run. Constant parsing reuses the operator table and
precedence levels but computes a Forth value instead of emitting a runtime
calculation.

`cc-cx-pp`, `cc-cx-skip`, and `cc-cx-unsigned` track preprocessing mode,
dead arms, and signedness
(`forth-bootstrap/cc/100-cc-expr.fth:2444`):
```forth chunk=expr-top
\ ===========================================================================
\ Constant expressions
\ ===========================================================================
\ An array size, a case label, an enum value, a global's initializer and an
\ #if line need a value while compiling, not code.  cc-parse-const reads
\ the grammar of cc-parse-ternary and computes it with the operator
\ table's evaluator column instead of emitting instructions.  An operand
\ is a number, a character, an enum constant or a parenthesised constant
\ expression.  On an #if line (cc-cx-pp true) any identifier the
\ preprocessor left is 0, as C says.  Errors: 125 for a name that isn't
\ an enum constant, 126 for a token that can't start an operand, 127 for
\ a missing ')', 128 for a '?' without its ':'.

variable cc-cx-pp
variable cc-cx-skip                              \ true in an unevaluated constant arm
variable cc-cx-unsigned                          \ signedness of the current value
: cc-cx-typed?  cc-cx-pp @ cc-target-lp64 @ and ;

\ Comparisons must also work across opposite signs, where 010's < wraps.
: cc-cx-lt ( a b -- flag )
  2dup cc-xor 0< if, drop 0< else, < then, ;
: cc-cx-ult ( a b -- flag )
  2dup cc-xor 0< if, swap drop 0< else, < then, ;

```

`cc-cx-typed?` enables signedness tracking for native preprocessor expressions. `cc-cx-lt` and `cc-cx-ult` inspect opposite sign bits before using the ordinary comparison, avoiding subtraction wraparound across that boundary.

`cc-cx-eval` saves the operator and comparison category, suppresses dead-arm evaluation, and chooses signed or unsigned relational comparison
(`forth-bootstrap/cc/100-cc-expr.fth:2468`):
```forth chunk=expr-top
\ cc-cx-eval ( a b row left-unsigned -- v )  The recursive caller
\ saved the left flag; the right flag is current. Shifts use only the
\ left type. All other arithmetic uses uintmax_t if either is unsigned.
variable cc-cx-op
variable cc-cx-comparison
: cc-cx-eval
  over bo-level + @ level-shift = if,
    cc-cx-unsigned !
  else, cc-cx-unsigned @ or cc-cx-unsigned ! then,
  dup bo-op + @ cc-cx-op !
  dup bo-level + @ dup level-rel = swap level-eq = or cc-cx-comparison !
  cc-cx-skip @ if,
    drop 2drop [lit] 0
  else,
    cc-cx-comparison @ if,
      cc-cx-op @ [char] < = if, drop cc-cx-unsigned @ if, cc-cx-ult else, cc-cx-lt then, cc-flag else,
      cc-cx-op @ [char] > = if, drop swap cc-cx-unsigned @ if, cc-cx-ult else, cc-cx-lt then, cc-flag else,
      cc-cx-op @ pt-le = if, drop swap cc-cx-unsigned @ if, cc-cx-ult else, cc-cx-lt then, 0= cc-flag else,
      cc-cx-op @ pt-ge = if, drop cc-cx-unsigned @ if, cc-cx-ult else, cc-cx-lt then, 0= cc-flag else,
        bo-eval + @ execute
      then, then, then, then,
```

Unsigned division, remainder, and right shift need separate evaluators; symbolic constant hooks initially bind to `cc-const-unsupported` and fail if used before their later implementations
(`forth-bootstrap/cc/100-cc-expr.fth:2489`):
```forth chunk=expr-top
    else,
      cc-cx-unsigned @ if,
        cc-cx-op @ [char] / = if, drop cc-divisor / else,
        cc-cx-op @ [char] % = if, drop cc-divisor 2dup / * - else,
        cc-cx-op @ pt-shr = if, drop cc-pow2 / else,
          bo-eval + @ execute
        then, then, then,
      else, bo-eval + @ execute then,
    then,
  then,
  cc-cx-comparison @ if, [lit] 0 cc-cx-unsigned ! then, ;

\ The object target supplies symbolic leaves; other targets never enter
\ them. The typed evaluator binds the parser after all compiler layers load.
: cc-const-unsupported [lit] 240 cc-die ;
defer cc-parse-static-const-fwd
defer cc-const-ident-fwd
defer cc-const-address-fwd
defer cc-const-string-fwd
' cc-const-unsupported is cc-parse-static-const-fwd
' cc-const-unsupported is cc-const-ident-fwd
' cc-const-unsupported is cc-const-address-fwd
' cc-const-unsupported is cc-const-string-fwd

```

Chapter 45 builds the typed static evaluator. The `cc-parse-static-const-fwd`, `cc-const-ident-fwd`, `cc-const-address-fwd`, and `cc-const-string-fwd` declarations here reserve its entry and symbolic-leaf contracts.

### Constant operands and folds

`cc-cx-operand` accepts numbers, characters, enums, and grouped constants; preprocessing mode treats remaining names as zero
(`forth-bootstrap/cc/100-cc-expr.fth:2513`):
```forth chunk=expr-top
\ cc-cx-operand ( -- v )  Under LP64 a number's suffix is checked by
\ the same parser that types runtime literals (060), so #if 1LLL is 240.
: cc-cx-operand
  [lit] 0 cc-cx-unsigned !
  cc-next-token-keep
  tok-kind @ tk-num = cc-target-lp64 @ and if, cc-integer-literal-check then,
  tok-kind @ tk-num = if,
    cc-cx-typed? if,
      cc-literal-unsigned @ tok-num @ 0< or cc-cx-unsigned !
    then,
    tok-num @ exit,
  then,
  tok-kind @ tk-chr = if, tok-num @ exit, then,
  tok-kind @ tk-ident = if,
    cc-cx-pp @ if, [lit] 0 exit, then,
    tok-str-addr @ tok-str-len @ cc-sym-find                ( id )
    dup 0< 0= if, dup cc-sym-kind-of sk-enum = else, [lit] 0 then,
    0= if, [lit] 125 cc-die then,
    cc-sym-val-of exit,
  then,
  lparen cc-tok-punct? if,
    cc-parse-const-fwd
    cc-next-token-keep
    [char] ) cc-tok-punct? 0= if, [lit] 127 cc-die then,
    exit,
  then,
  [lit] 126 cc-die ;

```

Constant unary operators compute directly on the Forth value, with logical negation clearing unsignedness
(`forth-bootstrap/cc/100-cc-expr.fth:2541`):
```forth chunk=expr-top
\ cc-cx-unary ( -- v )  '-' '+' '!' '~' then an operand.
: cc-cx-unary
  cc-next-token-keep
  cc-target-lp64 @ if,
    kw-sizeof cc-tok-kw? if, cc-native-sizeof exit, then,
  then,
  [char] - cc-tok-punct? if, cc-cx-unary cc-negate       exit, then,
  [char] + cc-tok-punct? if, cc-cx-unary                 exit, then,
  [char] ! cc-tok-punct? if, cc-cx-unary 0= cc-flag [lit] 0 cc-cx-unsigned ! exit, then,
  [char] ~ cc-tok-punct? if, cc-cx-unary cc-invert       exit, then,
  cc-putback-token
  cc-cx-operand ;

```

`cc-cx-binary` recurses by precedence level and executes the operator table’s evaluator column; skipped arms still consume and check their operands
(`forth-bootstrap/cc/100-cc-expr.fth:2554`):
```forth chunk=expr-top
\ cc-cx-binary ( level -- v )  One level of the operator table: operands
\ from the level below, combined by this level's evaluators.  Level 0 is
\ the unary operators.
: cc-cx-binary
  dup 0= if, drop cc-cx-unary exit, then,
  dup 1- cc-cx-binary                               ( level v )
  begin,
    over cc-binop? dup                              ( level v row row | .. 0 0 )
  while,
    >r cc-cx-unsigned @ >r
    over 1- cc-cx-binary                            ( level v w ; R: row left-u )
    r> r> swap                                     ( level v w row left-u )
    cc-cx-typed? if, cc-cx-eval else,
    drop cc-cx-skip @ if,
      \ Still consume/check every operand, but do not execute a dead arm.
      drop 2drop [lit] 0
    else,
      bo-eval + @ execute
    then, then,                                    ( level v' )
  repeat,
  drop cc-putback-token nip ;

```

### Unevaluated constant arms

The constant parser must check an unselected branch’s syntax without calculating its value. Its logical handlers preserve an outer skip flag so a nested expression cannot accidentally re-enable evaluation:

| Input condition | Handler action |
|---|---|
| False left operand of `&&` | `cc-cx-and` skips evaluation of the right operand |
| True left operand of `\|\|` | `cc-cx-or` skips evaluation of the right operand |
| Conditional test | `cc-parse-const-default` skips the unselected arm |

Logical conjunction and disjunction restore the enclosing skip state after parsing each right operand
(`forth-bootstrap/cc/100-cc-expr.fth:2576`):
```forth chunk=expr-top
\ cc-cx-and ( -- v )   cc-cx-or ( -- v )   && and ||, answering 1 or 0.
: cc-cx-and
  level-bit-or cc-cx-binary
  begin,
    cc-next-token-keep pt-and-and cc-tok-punct?
  while,
    cc-cx-skip @ >r
    dup 0= if, true cc-cx-skip ! then,
    level-bit-or cc-cx-binary
    r> cc-cx-skip !
    0= 0= swap 0= 0= and cc-flag [lit] 0 cc-cx-unsigned !
  repeat,
  cc-putback-token ;

: cc-cx-or
  cc-cx-and
  begin,
    cc-next-token-keep pt-or-or cc-tok-punct?
  while,
    cc-cx-skip @ >r
    dup if, true cc-cx-skip ! then,
    cc-cx-and
    r> cc-cx-skip !
    0= 0= swap 0= 0= or cc-flag [lit] 0 cc-cx-unsigned !
  repeat,
  cc-putback-token ;

```

A constant conditional parses both arms, selects a payload, combines their unsignedness, and installs the default constant parser behind its deferred entry
(`forth-bootstrap/cc/100-cc-expr.fth:2603`):
```forth chunk=expr-top
\ cc-parse-const ( -- v )  cond ? a : b, or just cond.
: cc-parse-const-default
  cc-cx-or
  cc-next-token-keep
  [char] ? cc-tok-punct? if,
    cc-cx-skip @ >r                                 ( c ; R: outer-skip )
    dup 0= if, true cc-cx-skip ! then,
    cc-parse-const-default                                  ( c a ; R: outer-skip )
    r@ cc-cx-skip !
    cc-cx-unsigned @ >r
    >r                                              ( c ; R: outer-skip a-u a )
    cc-next-token-keep
    [char] : cc-tok-punct? 0= if, [lit] 128 cc-die then,
    dup if, true cc-cx-skip ! then,
    cc-parse-const-default                                  ( c b ; R: outer-skip a-u a )
    swap if, drop r> else, r> drop then,
    r> cc-cx-unsigned @ or cc-cx-unsigned !
    r> cc-cx-skip !
  else,
    cc-putback-token
  then, ;

defer cc-parse-const
' cc-parse-const-default is cc-parse-const

' cc-parse-const is cc-parse-const-fwd

```

### Evaluating preprocessor text

`cc-pp-eval-text` saves lexer state in `cc-cx-save`, redirects source offsets to the expanded expression, requires end-of-input, and restores the caller’s state before the final parser bindings are installed
(`forth-bootstrap/cc/100-cc-expr.fth:2630`):
```forth chunk=expr-top
\ cc-pp-eval-text ( a u -- n )  #if's evaluator (cc-pp-eval, 040): lex
\ the expanded line a u by pointing the reader at it. Its source-relative
\ offsets can be negative when cc-src-buf is mapped; both endpoints use
\ the same base, so signed range checks and address addition still agree.  The lexer's state and cc-src-len are
\ put back afterwards; anything left after the expression dies with 129.
create cc-cx-save  cc-lex-state-size allot

: cc-pp-eval-text
  cc-cx-save cc-lex-mark
  cc-src-len @ >r
  over + cc-src-buf - cc-src-len !                  ( a )
  cc-src-buf - cc-src-pos !
  [lit] 0 cc-tok-pending !
  true cc-cx-pp !
  [lit] 0 cc-cx-skip !
  cc-parse-const
  cc-next-token-keep  tok-kind @ tk-eof <> if, [lit] 129 cc-die then,
  [lit] 0 cc-cx-pp !
  r> cc-src-len !
  cc-cx-save cc-lex-reset ;

' cc-pp-eval-text is cc-pp-eval

\ Fill in the forward references declared at the top of the file.
' cc-parse-expr   is cc-parse-expr-fwd
' cc-parse-comma  is cc-parse-comma-fwd
' cc-parse-assign is cc-parse-assign-fwd
' cc-parse-unary  is cc-parse-unary-fwd
```

## Try it

Run from the `forth-bootstrap` checkout root with the seed built in Part 1.
The driver loads through `cc/100-cc-expr.fth` and compiles
`(-3 < 0) ? 7 : 9` into an ELF image in a fresh temporary directory.
This checks grouping, unary negation, comparison, and the conditional
join without requiring names or storage declarations. The assignment
trace above explains how those additional operands retain a destination;
Chapter 35 supplies the declarations that make them available in C.

The cast hook is declared without a binding at `forth-bootstrap/cc/100-cc-expr.fth:44`. `probe-no-cast` supplies a false result without consuming input, allowing parentheses to mean grouping in this driver. It does not implement casts. Locals and their declarations are outside this checkpoint.

<!-- tryit: expect "driver exit: 0\n(-3 < 0) ? 7 : 9 = 7 (exit status)" -->
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
      cc/080-cc-elf.fth cc/090-cc-emit.fth cc/100-cc-expr.fth || exit "$?"
  cat <<'FORTH' || exit "$?"
: probe-no-cast [lit] 0 ;
' probe-no-cast is cc-try-cast-fwd
cc-src-init
here dup cc-src-buffer ! s, (-3<0)?7:9 here swap - cc-src-len !
[lit] 0 cc-src-pos ! [lit] 0 cc-tok-pending !
cc-out-init [lit] 0 cc-bss-size ! cc-emit-elf-header
cc-parse-expr cc-emit-exit-shim
cc-finalize-elf
[lit] 1 cc-out-buf cc-out-pos @ write drop
bye
FORTH
} | ./seed-forth > "$probe_dir/expression" || compiler_status=$?
printf 'driver exit: %s\n' "$compiler_status" # prints 'driver exit: 0'
test "$compiler_status" -eq 0 || exit "$compiler_status"
chmod +x "$probe_dir/expression" || exit "$?"
program_status=0
"$probe_dir/expression" || program_status=$?
printf '(-3 < 0) ? 7 : 9 = %s (exit status)\n' "$program_status" # prints '(-3 < 0) ? 7 : 9 = 7 (exit status)'
test "$program_status" -eq 7
)
```

Observed output:

```text
driver exit: 0
(-3 < 0) ? 7 : 9 = 7 (exit status)
```

This run exercises operand dispatch, grouping, unary negation, comparison, ternary selection, and final materialization. It does not exercise storage mutation or the native target hooks.

## Exercise

Hints and feedback are in [Appendix H](66-exercise-feedback.md#chapter-34-an-address-through-parentheses).

**Trace (easy).** Follow `(*p)++` with `p` a character pointer. Identify where the pointer is loaded, where the target remains an address, and why parentheses preserve that address for the postfix handler.

**Verify (easy).** Change the checkpoint’s comparison from `<` to `>`.
Predict which ternary branch executes and the resulting program status.
Update both the printed expression and the final `test "$program_status"`
assertion to match that prediction, then run it. Keep the compiler-status
check at zero: successful compilation and the generated program's answer
are separate results.

