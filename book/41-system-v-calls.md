# Chapter 41 — System V calls and separate compilation

With `base` holding 14, the checkpoint's call to `add(&base, 1, 2, 3, 4, 5, 6, 7)` crosses from one C object into another and returns `42`. Separate compilation requires the caller and callee to agree without seeing each other’s bodies. The System V target gives the compiler that agreement for integer and pointer values, then carries unresolved calls into relocatable objects.

## Trace the call before tracing its parser

To follow the trace, recall the eight-byte stack cells, `call`'s pushed
return address, and the `push rbp; mov rbp,rsp` frame setup. We use the explicit
scalar System V target. The core six-register path of Chapter 37 and the
private LP64 all-stack path of Chapter 39 are different contracts; merely
loading the System V definitions selects neither the new layout nor its
alignment rule.

| Source argument | Caller location immediately before `call` | Callee location after frame setup |
|---|---|---|
| `&base` | RDI | Spilled from RDI into its local parameter slot |
| `1, 2, 3, 4, 5` | RSI, RDX, RCX, R8, R9 | Spilled into their corresponding parameter slots |
| `6` | `[rsp + 0]` | `[rbp + 16]` |
| `7` | `[rsp + 8]` | `[rbp + 24]` |

Argument evaluation first uses temporary staging cells. The emitter then
allocates and aligns a separate outgoing block, copies the two stack
arguments into its first 16 bytes, and loads the six registers. Padding
lies beyond those arguments; it cannot precede the value 6 and shift its
ABI position. At this moment `rsp mod 16 = 0`. `call` pushes eight bytes,
so that seventh argument is now at entry `rsp + 8`; pushing the old RBP
and adopting the new frame pointer puts saved RBP at +0, return address at +8, and that
argument at +16. These offsets follow from the two pushes, not from the
callee's local-frame size.

If the final argument itself is a call, earlier outer arguments remain
live. The call record saves that surviving span in fixed-frame storage
before preparing the inner outgoing block, then restores it afterward.
The detailed [live-value machinery](#keep-expression-temporaries-alive)
implements this lifetime boundary.

The source walkthrough is long because it also retains C declaration
shapes. For a first pass, keep the same `add` call and follow four stops:

1. [Retain its signature](#one-signature-two-places-to-use-it): what must
   the caller know without seeing the body?
2. [Stage its arguments](#keep-expression-temporaries-alive): where can
   eight completed values wait while the call is prepared?
3. [Receive them in the callee](#preserve-the-callers-register-values):
   how do register and stack arguments become the body's parameter objects?
4. [Finish the caller's object](#finish-the-translation-unit): what remains
   to be done when `add` is still in another file?

Those stops trace one complete boundary. Then return to the intervening
declaration, compatibility, and symbolic-address sections to see how the
compiler preserves it for richer source forms.

## One signature, two places to use it

The implementation has three parts: retain a signature, lower both sides of a call from it, and export code with unresolved references. `cc-sysv-enable` selects this target explicitly; loading its definitions preserves the private all-stack target (Chapter 39). The signature describes C types, while the call emitter decides where their values travel.

For `add`, retain a `long` result and eight fixed parameters: one
`long *`, followed by seven `long` values, with no variadic tail. The
caller's prototype omits parameter names; the definition names them
`base`, then `a` through `g`. Names let the body refer to its parameters,
but their types and order are what let the two files agree. The signature
contains neither the address of `add` nor an assignment of registers.

Target state and a tagged signature table keep that choice separate from loading the module (`forth-bootstrap/cc/121-cc-sysv.fth:1`):

```forth file=cc/121-cc-sysv.fth
\ 121-cc-sysv.fth — explicit scalar System V AMD64 target.
\ Loading this file changes no target. cc-sysv-enable opts in to LP64 and
\ INTEGER-class calls; floating and aggregate values fail closed.
variable cc-target-sysv
[lit] 0 cc-target-sysv !
[lit] 64 constant cc-sysv-arg-cap
[lit] 1398362966 constant cc-sysv-signature-tag
create cc-sysv-signatures cc-sym-cap [lit] 8 * allot

```

A function named `stat` must remain visible beside `struct stat`; ordinary lookup skips tags, while tag lookup keeps its own path (`forth-bootstrap/cc/121-cc-sysv.fth:10`):

```forth file=cc/121-cc-sysv.fth
\ An ordinary identifier never resolves to a struct/union tag. The walk
\ along the name's bucket (070), newest first, still chooses the innermost
\ ordinary declaration; member names live in their aggregate descriptors
\ and enumerators remain ordinary names.
: cc-sysv-find-ordinary ( a u -- id|-1 )
  cc-target-sysv @ 0= if, cc-sym-find-default exit, then,
  cc-nf-u ! cc-nf-a !
  cc-nf-a @ cc-nf-u @ cc-name-hash cc-sym-bucket cell[] @ 1-     ( id )
  begin, dup 0< 0= while,
    dup cc-sym-count @ < over cc-sym-kind-of sk-struct <> and if,
      dup cc-sym-name-len cell[] @ cc-nf-u @ = if,
        dup cc-sym-name-addr cell[] @ cc-nf-a @ cc-nf-u @ bytes-eq if,
          exit,
        then,
      then,
    then,
    cc-sym-hnext cell[] @
  repeat, ;
: cc-sysv-find-tag ( a u -- id|-1 )
  cc-target-sysv @ if, cc-nfind-tag else, cc-sym-find-default then, ;
' cc-sysv-find-ordinary is cc-sym-find
' cc-sysv-find-tag is cc-sym-find-tag

```

The lexer also accepts source spellings needed by this target: `cc-sysv-extension?` recognizes the complete `__extension__` token, `cc-sysv-skip-extensions` skips it, and `cc-sysv-lex-extra` delegates number scanning through `cc-sysv-lex-number-fwd` (`forth-bootstrap/cc/121-cc-sysv.fth:33`):

```forth file=cc/121-cc-sysv.fth
\ GNU C's __extension__ only silences pedantic diagnostics, which this
\ compiler never issues. The SysV lexer drops the reserved word between
\ tokens, so it may precede declarations, members and operands alike;
\ the preprocessed text keeps it. Number scanning (127) plugs in behind.
create cc-sysv-extension-name s, __extension__
: cc-sysv-extension? ( -- flag )
  cc-src-pos @ [lit] 13 + dup cc-src-len @ > if, drop [lit] 0 exit, then,
  dup cc-src-len @ < if,
    cc-src-buf + c@ ident-cont? if, [lit] 0 exit, then,
  else, drop then,
  cc-src-buf cc-src-pos @ + cc-sysv-extension-name [lit] 13 bytes-eq ;
: cc-sysv-skip-extensions
  begin,
    cc-target-sysv @ cc-eof? 0= and if, cc-sysv-extension? else, [lit] 0 then,
  while,
    cc-src-pos @ [lit] 13 + cc-src-pos ! cc-skip-ws-and-comments
  repeat, ;
defer cc-sysv-lex-number-fwd
' cc-lex-extra-default is cc-sysv-lex-number-fwd
: cc-sysv-lex-extra ( -- handled? )
  cc-sysv-skip-extensions cc-sysv-lex-number-fwd ;
' cc-sysv-lex-extra is cc-lex-extra-fwd

```

| Signature input | Result |
|---|---|
| Signature → `cc-sysv-sig-return`, `cc-sysv-sig-desc` | Result type and descriptor |
| Signature → `cc-sysv-sig-count`, `cc-sysv-sig-varargs` | Fixed count and prototype flags |
| Signature and index → `cc-sysv-sig-param`, `cc-sysv-sig-name` | Parameter type pair and optional name record |
| Signature → `cc-sysv-prototype?`, `cc-sysv-known-params?` | Whether callers or definitions supply parameter information |

The same accessors serve calls and definitions; a signature check rejects missing metadata, and the default executable boundary accepts scalar integers and pointers (`forth-bootstrap/cc/121-cc-sysv.fth:56`):

```forth file=cc/121-cc-sysv.fth
\ Signature: tag, return type, return descriptor, count, variadic flag,
\ then 64 (type, descriptor) pairs and 64 (name, length, declared) records.
\ Flags: 1 variadic, 2 unspecified prototype, 4 identifier-list definition.
\ Function-pointer descriptors are tagged; names are compile-time metadata.
: cc-sysv-sig-return [lit] 8 + @ ;
: cc-sysv-sig-desc [lit] 16 + @ ;
: cc-sysv-sig-count [lit] 24 + @ ;
: cc-sysv-sig-varargs [lit] 32 + @ ;
: cc-sysv-sig-param [lit] 16 * [lit] 40 + + ;
: cc-sysv-sig-name [lit] 24 * [lit] 1064 + + ;
: cc-sysv-prototype? cc-sysv-sig-varargs [lit] 2 and 0= ;
: cc-sysv-known-params?
  dup cc-sysv-prototype? swap cc-sysv-sig-varargs [lit] 4 and or ;
: cc-sysv-check-signature
  dup 0= if, [lit] 230 cc-die then,
  dup @ cc-sysv-signature-tag <> if, [lit] 230 cc-die then, ;
: cc-sysv-check-scalar-default ( ty -- )
  dup [lit] 256 / [lit] 255 and if, [lit] 231 cc-die then,
  dup ty-ptr if, drop exit, then,
  ty-base
  dup ty-struct = over ty-float = or over ty-double = or
  over ty-ldouble = or swap ty-func = or if, [lit] 232 cc-die then, ;
defer cc-sysv-check-scalar
' cc-sysv-check-scalar-default is cc-sysv-check-scalar

```

The accessors above are enough to describe the opening call. Follow that
signature into [argument staging](#keep-expression-temporaries-alive) for
the first-pass trace. The next sections preserve additional type shapes
and declaration rules before call emission uses the completed signature.

## Preserve array shape in signatures

Compare `long *p` with `long (*row)[3]`. Both values occupy one eight-byte
pointer, but `p + 1` advances eight bytes while `row + 1` advances 24.
The latter points to one whole row of three longs. For a valid matrix,
`row[1][2]` first advances one row and then two elements: `24 + 16 = 40`
bytes from the original address. These are manual consequences of LP64
layout, before any instruction selection.

A parameter written `long row[][3]` adjusts to that pointer-to-row type;
only the outer array becomes a pointer. Erasing the inner bound would make
the declaration look like a plain pointer and generate the wrong stride.
An encoded pointer depth cannot retain the distinction by itself. The
descriptor must carry the pointee's shape through typedefs, parameter
adjustment and abstract type names.

Size multiplication checks the bound before computing a product; typedef lookup also carries the declaration’s array shape and qualifiers forward (`forth-bootstrap/cc/121-cc-sysv.fth:81`):

```forth file=cc/121-cc-sysv.fth
\ Bound object-size arithmetic before multiplying. Explicit bounds are
\ distinct from the unsized-array sentinel inherited from the native parser.
[lit] 1073741824 constant cc-sysv-object-size-limit
: cc-sysv-size-product ( size count -- size' )
  dup 0< if, [lit] 245 cc-die then,
  over 0= if, [lit] 238 cc-die then,
  over cc-sysv-object-size-limit swap / over < if, [lit] 245 cc-die then, * ;
: cc-sysv-object-size
  nc-ty @ nc-desc @ cc-nsize
  nc-array @ [lit] 0 > if, nc-array @ cc-sysv-size-product then,
  nc-inner @ [lit] 0 > if, nc-inner @ cc-sysv-size-product then, ;
: cc-sysv-typedef-check
  cc-target-sysv @ if,
    dup cc-sym-qualified cell[] @ nc-qualified @ or nc-qualified !
    dup cc-sym-array-len-of nc-base-array !
    dup cc-sym-array-inner-of nc-base-inner !
  then, ;
' cc-sysv-typedef-check is cc-ntypedef-check-fwd
\ Preserve array typedef shape through aliases and ordinary declarations.
\ Two bounded dimensions can also be retained behind pointer constructors.
```

`cc-sysv-array-node` turns legacy matrix metadata into recursive element nodes, so equivalent row types do not depend on declarator spelling (`forth-bootstrap/cc/121-cc-sysv.fth:106`):

```forth file=cc/121-cc-sysv.fth
[lit] 64 constant cc-sysv-array-rank-limit
: cc-sysv-array-rank ( type descriptor -- dimensions )
  over ty-base ty-array = [lit] 2 cc-npick ty-ptr 0= and if,
    nip dup cc-ad-type swap cc-ad-desc cc-sysv-array-rank 1+
  else, 2drop [lit] 0 then, ;
: cc-sysv-array-node ( type descriptor count inner -- descriptor )
  [lit] 56 cc-alloc >r [lit] 0 r@ [lit] 48 + !
  r@ [lit] 24 + ! r@ [lit] 16 + ! r@ [lit] 8 + ! r@ !
  \ Canonical nodes hold one dimension, including legacy matrix pointers.
  \ Equivalent row shapes must not depend on how the declarator was spelled.
  r@ cc-ad-inner if,
    r@ cc-ad-type r@ cc-ad-desc r@ cc-ad-inner [lit] 0
    cc-sysv-array-node r@ [lit] 8 + !
    ty-array [lit] 0 ty-make r@ ! [lit] 0 r@ [lit] 24 + !
  then,
  r@ cc-ad-type r@ cc-ad-desc cc-sysv-array-rank
  cc-sysv-array-rank-limit >= if, [lit] 238 cc-die then,
  r@ cc-ad-count [lit] 0 <= if, [lit] 238 cc-die then,
  r@ cc-ad-type ty-ptr 0= if,
    r@ cc-ad-type ty-base dup ty-void = swap ty-func = or if, [lit] 238 cc-die then,
  then,
  r@ cc-ad-type r@ cc-ad-desc cc-expr-type-size
  r@ cc-ad-count cc-sysv-size-product
  r@ cc-ad-inner if, r@ cc-ad-inner cc-sysv-size-product then,
  r@ [lit] 32 + !
  r@ cc-ad-type r@ cc-ad-desc cc-nalignment r@ [lit] 40 + ! r> ;
```

Shared typedef nodes cannot be modified in place: qualification creates a copy, and additional suffixes recursively construct bounded element types (`forth-bootstrap/cc/121-cc-sysv.fth:127`):

```forth file=cc/121-cc-sysv.fth
\ A new node may be born qualified. An existing one may be shared by a
\ typedef or declaration, so qualifying it builds a qualified copy.  The
\ cell holds the row's qualifier set (110's cc-qualifier-bit), never a
\ flag: a const row and a volatile row are different types.
: cc-sysv-qualified-node ( type descriptor count inner set -- descriptor )
  >r cc-sysv-array-node r> over [lit] 48 + ! ;
: cc-sysv-qualify-node ( descriptor set -- descriptor )
  over cc-ad-qualified or
  over cc-ad-qualified over = if, drop exit, then,
  >r dup cc-ad-type over cc-ad-desc [lit] 2 cc-npick cc-ad-count
  [lit] 3 cc-npick cc-ad-inner r> cc-sysv-qualified-node nip ;
\ Additional fixed suffixes form real element-array types. The old outer
\ metadata stays intact for one/two dimensions and for the native target.
\ Depth is bounded independently of the checked 1 GiB size product.
: cc-sysv-array-tail ( depth -- descriptor )
  dup cc-sysv-array-rank-limit > if, [lit] 238 cc-die then,
  cc-parse-const dup [lit] 0 <= if, [lit] 238 cc-die then, >r
  [char] ] cc-expect-punct-c cc-next-token-keep
  [char] [ cc-tok-punct? if,
    1+ cc-sysv-array-tail ty-array [lit] 0 ty-make swap
  else, drop nc-ty @ nc-desc @ then,
  r> [lit] 0 cc-sysv-array-node ;
: cc-sysv-array-extra
  cc-target-sysv @ [char] [ cc-tok-punct? and if,
    nc-base-array @ if, [lit] 238 cc-die then,
    nc-inner @ [lit] 0 <= if, [lit] 238 cc-die then,
    [lit] 3 cc-sysv-array-tail
    ty-array [lit] 0 ty-make swap nc-inner @ [lit] 0
    cc-sysv-array-node nc-desc ! ty-array [lit] 0 ty-make nc-ty !
    [lit] 0 nc-inner ! nc-bound-mask @ [lit] 1 and nc-bound-mask !
  then, ;
' cc-sysv-array-extra is cc-narray-extra-fwd
```

Decay keeps the qualifier on the pointed-to row; `cc-sysv-array-decay` handles both an existing element node and the legacy inner-count form (`forth-bootstrap/cc/121-cc-sysv.fth:164`):

```forth file=cc/121-cc-sysv.fth
\ A qualified array decays like any other (C90 6.2.2.1): the qualifier moves
\ onto the pointed-to type. A matrix's row node records it, and the value
\ keeps the expression's qualified flag, so `const T t[2][3]` gives a
\ pointer to qualified rows. A ranked array already points at its element
\ node; a qualified one points at a qualified copy.
: cc-sysv-array-decay
  cc-target-sysv @ cc-last-expr-array-len @ 0= 0= and
  cc-last-expr-type @ ty-base ty-array = and if,
    cc-last-struct-desc @ cc-last-expr-qualified @ cc-sysv-qualify-node
    cc-last-struct-desc !
  then,
  cc-target-sysv @ cc-last-expr-array-inner @ 0= 0= and if,
    cc-last-expr-qualified @ >r
    cc-last-expr-type @ [lit] 1 - cc-last-struct-desc @
    cc-last-expr-array-inner @ [lit] 0 r@ cc-sysv-qualified-node
    ty-array [lit] 1 ty-make swap cc-mark-typed-value
    r> cc-last-expr-qualified !
  then, ;
' cc-sysv-array-decay is cc-array-decay-fwd
```

## Carry array shape through declarations

Grouped array pointers take the base type’s qualifiers, while address-of constructs a descriptor for the entire array (`forth-bootstrap/cc/121-cc-sysv.fth:178`):

```forth file=cc/121-cc-sysv.fth
\ Declared array pointers take the base type's qualifiers: in
\ `const long (*p)[3]` the rows are qualified, in `long (*const p)[3]` only p.
: cc-sysv-grouped-array ( stars -- )
  cc-target-sysv @ 0= if, cc-npointer-array-default exit, then,
  nc-array @ nc-inner @ or nc-base-array @ or if, [lit] 238 cc-die then,
  >r cc-narray-suffix
  nc-bound-mask @ [lit] 2 and nc-inner @ [lit] 0 <= and if, [lit] 238 cc-die then,
  nc-ty @ nc-desc @ nc-array @ nc-inner @ nc-base-qualified @
  cc-sysv-qualified-node nc-desc !
  ty-array r> ty-make nc-ty !
  [lit] 0 nc-array ! [lit] 0 nc-inner ! [lit] 0 nc-bound-mask ! ;
' cc-sysv-grouped-array is cc-npointer-array-fwd
: cc-sysv-array-address ( type descriptor count inner -- type descriptor )
  cc-target-sysv @ 0= if, cc-array-address-default exit, then,
  >r >r swap [lit] 1 - swap r> r> cc-last-expr-qualified @
  cc-sysv-qualified-node ty-array [lit] 1 ty-make swap ;
' cc-sysv-array-address is cc-array-address-fwd
```

An inherited array alias either stays an object shape or moves behind a pointer constructor; `cc-sysv-type-shape` makes the same distinction for type names (`forth-bootstrap/cc/121-cc-sysv.fth:212`):

```forth file=cc/121-cc-sysv.fth
: cc-sysv-inherit-array
  nc-base-array @ if,
    nc-ty @ nc-base @ <> if,
      nc-base @ nc-sdesc @ nc-base-array @ nc-base-inner @
      nc-base-qualified @ cc-sysv-qualified-node nc-desc !
      ty-array nc-ty @ nc-base @ - ty-make nc-ty ! exit,
    then,
    nc-func @ if, [lit] 238 cc-die then,
    nc-array @ if,
      nc-inner @ nc-base-inner @ or nc-base-array @ [lit] 0 < or if,
        [lit] 238 cc-die
      then,
      nc-base-array @ nc-inner !
    else,
      nc-base-array @ nc-array ! nc-base-inner @ nc-inner !
    then,
  then, ;
: cc-sysv-type-shape ( base-type stars -- type )
  cc-target-sysv @ 0= if, + exit, then,
  dup 0= 0= nc-base-array @ 0= 0= and if,
    >r cc-cast-desc @ nc-base-array @ nc-base-inner @
    nc-base-qualified @ cc-sysv-qualified-node cc-cast-desc !
    ty-array r> ty-make exit,
  then,
  nc-base-array @ cc-type-name-array ! nc-base-inner @ cc-type-name-inner ! + ;
' cc-sysv-type-shape is cc-native-type-shape-fwd
```

`sizeof` retains the complete array extent, while indexing and member access reject a base whose pointer or record shape cannot support the operation (`forth-bootstrap/cc/121-cc-sysv.fth:221`):

```forth file=cc/121-cc-sysv.fth
: cc-sysv-sizeof-type ( type descriptor -- bytes )
  cc-expr-type-size
  cc-target-sysv @ if,
    cc-type-name-array @ if,
      cc-type-name-array @ [lit] 0 < if, [lit] 238 cc-die then,
      cc-type-name-array @ cc-sysv-size-product
      cc-type-name-inner @ if, cc-type-name-inner @ cc-sysv-size-product then,
    then,
  then, ;
' cc-sysv-sizeof-type is cc-sizeof-type-size-fwd
\ Array expressions carry a pointer-shaped type before decay. A whole
\ matrix is not a record, and another subscript needs a pointer operand.
: cc-sysv-index-base
  cc-target-sysv @ if,
    cc-last-expr-type @ ty-ptr 0= if, [lit] 238 cc-die then,
  then, ;
' cc-sysv-index-base is cc-index-base-fwd
: cc-sysv-member-base ( op -- op )
  cc-target-sysv @ if,
    cc-last-expr-type @ ty-base ty-struct <> if, [lit] 238 cc-die then,
    dup [char] . = if,
      cc-last-expr-array-len @ cc-last-expr-type @ ty-ptr or if, [lit] 238 cc-die then,
    else,
      cc-last-expr-type @ ty-ptr [lit] 1 <>
      cc-last-expr-array-inner @ or if, [lit] 238 cc-die then,
    then,
  then, ;
' cc-sysv-member-base is cc-member-base-fwd

```

## Retain layouts without promising value operations

A declaration may name a type whose executable call boundary is unsupported. Taking an address must preserve its layout without first trying to load its value.

`cc-ld-desc` caches a shared opaque long-double descriptor; `cc-ld?` recognizes it, `cc-ld-mismatch` rejects cross-type transport, and `cc-ld-die` emits `cc-ld-error-prefix` before failing (`forth-bootstrap/cc/121-cc-sysv.fth:250`):

```forth file=cc/121-cc-sysv.fth
\ Real layouts are retained even when floating/aggregate value operations
\ are unsupported. Taking an address must not read that value first.
: cc-sysv-float-types cc-target-sysv @ cc-bootstrap-floatbits @ or ;
' cc-sysv-float-types is cc-native-float-types-fwd

\ Long double is the x87 80-bit extended format in sixteen bytes, aligned
\ to sixteen. The transport representation is an opaque record:
\ the value is an opaque record with one shared, memberless descriptor, so
\ it travels by address as records do and every spelling has one identity.
\ Layer 132 adds x87 computations and exact constants to this transport.
variable cc-ld-desc
[lit] 0 cc-ld-desc !
: cc-ld-descriptor ( -- descriptor )
  cc-ld-desc @ dup if, exit, then, drop
  cc-sd-alloc [lit] 16 over cc-sd-set-total-size
  [lit] 16 over cc-sd-set-align dup cc-ld-desc ! ;
: cc-ld? ( type descriptor -- flag )
  dup 0= if, 2drop [lit] 0 exit, then,
  cc-ld-desc @ = swap ty-struct [lit] 0 ty-make = and ;
create cc-ld-error-prefix s, long-double: bl c,
: cc-ld-die cc-ld-error-prefix [lit] 13 cc-err-write [lit] 249 cc-die ;
\ ( t1 d1 t2 d2 -- )  A value crossing between long double and another
\ type would need an x87 conversion.
: cc-ld-mismatch
  cc-ld? >r cc-ld? r> <> if, cc-ld-die then, ;
: cc-sysv-scalar-base ( type descriptor -- type descriptor )
  cc-target-sysv @ 0= if, exit, then,
  over ty-ldouble [lit] 0 ty-make = if,
    2drop ty-struct [lit] 0 ty-make cc-ld-descriptor
  then, ;
' cc-sysv-scalar-base is cc-nbase-scalar-fwd
' cc-ld? is cc-opaque-scalar-fwd
```

Local scalar references become deferred lvalues, so address-taking avoids an unsupported load; `cc-sysv-local-layout` reserves storage with the type’s actual alignment (`forth-bootstrap/cc/121-cc-sysv.fth:293`):

```forth file=cc/121-cc-sysv.fth
: cc-sysv-value-type-check ( type -- type )
  cc-target-sysv @ cc-expr-unevaluated @ 0= and if,
    dup cc-sysv-check-scalar
  then, ;
' cc-sysv-value-type-check is cc-emit-type-check-fwd
: cc-sysv-local-load ( slot type -- )
  cc-target-sysv @ if,
    drop cc-emit-lea-rdi-local
    true cc-last-ident-slot ! lv-deref cc-last-lvalue-kind !
  else, cc-emit-load-local-typed then, ;
' cc-sysv-local-load is cc-native-local-load-fwd
: cc-sysv-local-layout ( -- slots slot )
  cc-target-sysv @ 0= if, cc-native-local-layout-default exit, then,
  cc-sysv-object-size dup 0= if, [lit] 238 cc-die then,
  cc-fn-local-count @ [lit] 8 * +
  nc-ty @ nc-desc @ cc-nalignment [lit] 8 cc-nmax cc-nalign
  [lit] 8 / dup cc-fn-local-count @ - swap 1- ;
' cc-sysv-local-layout is cc-native-local-layout-fwd

```

Long-double arithmetic and its call classification belong to Chapter 49. Binary floating value operations belong to Chapter 47; these hooks preserve storage identity until those layers install their policies.

## Read a function declaration once

An omitted file-scope base becomes `int` unless the identifier is a typedef; a function’s saved suffix is then reparsed through `cc-sysv-declarator-signature` (`forth-bootstrap/cc/121-cc-sysv.fth:320`):

```forth file=cc/121-cc-sysv.fth
\ C90 permits an omitted int at file scope. A typedef name still starts
\ an explicit type; other identifiers remain pending for the declarator.
: cc-sysv-implicit-base ( -- type descriptor true | false )
  cc-target-sysv @ nc-top @ and 0= if, [lit] 0 exit, then,
  tok-kind @ tk-ident <> if, [lit] 0 exit, then,
  tok-str-addr @ tok-str-len @ cc-sym-find
  dup 0< 0= if,
    dup cc-sym-kind-of sk-typedef = if, drop [lit] 0 exit, then,
  then, drop
  cc-putback-token ty-int [lit] 0 ty-make [lit] 0 true ;
' cc-sysv-implicit-base is cc-native-implicit-base-fwd

: cc-sysv-implicit-declarator-noop ;
defer cc-sysv-implicit-declarator-fwd
' cc-sysv-implicit-declarator-noop is cc-sysv-implicit-declarator-fwd

defer cc-sysv-signature-fwd
\ A function declarator's signature: its saved suffix reparsed, or the one
\ a function typedef supplied, which nc-func then holds in place of true.
: cc-sysv-declarator-signature ( -- signature )
  nc-func @ true <> if, nc-func @ exit, then,
  cc-lex-state-size cc-alloc dup cc-lex-mark >r
  nc-params cc-lex-reset
  nc-ty @ nc-desc @ cc-sysv-signature-fwd
  r> cc-lex-reset ;
\ `typedef int F (char *);` names a function type: base ty-func with no
\ star, its signature as descriptor, so `F *p` is a function pointer. A
\ declarator of that type with no star declares a function, `F g;`.
```

A function typedef stores a signature without a pointer star; using that typedef as a declaration recovers its result type, after which the common declarator check enforces shape bounds (`forth-bootstrap/cc/121-cc-sysv.fth:329`):

```forth file=cc/121-cc-sysv.fth
: cc-sysv-function-typedef
  nc-func @ nc-ty @ ty-func [lit] 0 ty-make = and if, [lit] 238 cc-die then,
  nc-td @ nc-func @ and if,
    cc-sysv-declarator-signature
    dup cc-sysv-sig-varargs [lit] 4 and if, [lit] 233 cc-die then,
    nc-desc ! ty-func [lit] 0 ty-make nc-ty ! [lit] 0 nc-func !
  then,
  nc-ty @ ty-func [lit] 0 ty-make = if,
    nc-array @ nc-inner @ or if, [lit] 238 cc-die then,
    nc-td @ 0= if,
      nc-desc @ dup nc-func ! dup cc-sysv-sig-return nc-ty !
      cc-sysv-sig-desc nc-desc !
    then,
  then, ;
: cc-sysv-check-declarator
  cc-target-sysv @ if,
    cc-sysv-function-typedef
    cc-sysv-implicit-declarator-fwd
    cc-sysv-inherit-array
    nc-ty @ nc-desc @ cc-sysv-array-rank
    nc-array @ if, 1+ then, nc-inner @ if, 1+ then,
    cc-sysv-array-rank-limit > if, [lit] 238 cc-die then,
    nc-ty @ [lit] 256 / [lit] 255 and if, [lit] 231 cc-die then,
    nc-bound-mask @ [lit] 1 and if,
      nc-array @ [lit] 0 <= if, [lit] 238 cc-die then,
    then,
    nc-bound-mask @ [lit] 2 and if,
      nc-inner @ [lit] 0 <= if, [lit] 238 cc-die then,
    then,
    nc-array @ [lit] 0 > nc-inner @ [lit] 0 > or if,
      cc-sysv-object-size drop
    then,
  then, ;
' cc-sysv-check-declarator is cc-ndeclarator-check-fwd

```

Array parameters adjust to pointers to their elements, and function-pointer declarations retain a signature independently of whether a parameter name is present (`forth-bootstrap/cc/121-cc-sysv.fth:364`):

```forth file=cc/121-cc-sysv.fth
: cc-sysv-adjust-array-parameter
  nc-array @ if,
    \ Ranked element nodes also construct a pointer-to-array at adjustment.
    nc-ty @ ty-base ty-array = nc-ty @ ty-ptr 0= and if,
      nc-desc @ nc-base-qualified @ cc-sysv-qualify-node nc-desc !
    then,
    nc-inner @ if,
      nc-ty @ nc-desc @ nc-inner @ [lit] 0 nc-base-qualified @
      cc-sysv-qualified-node nc-desc !
      ty-array [lit] 1 ty-make nc-ty !
      [lit] 0 nc-array ! [lit] 0 nc-inner ! exit,
    then,
    [lit] 1 nc-ty +! [lit] 0 nc-array !
  then, ;

\ Parameter signatures carry types independently of optional source names.
: cc-sysv-fnptr-name
  cc-target-sysv @ 0= if, cc-nfnptr-name-default exit, then,
  cc-next-token-keep
  tok-kind @ tk-ident = if,
    tok-str-addr @ nc-name ! tok-str-len @ nc-nlen !
  else, cc-putback-token then, ;
' cc-sysv-fnptr-name is cc-nfnptr-name-fwd

: cc-sysv-fnptr
  cc-target-sysv @ 0= if, cc-nfnptr-default exit, then,
  1+ dup [lit] 255 > if, [lit] 231 cc-die then, >r
  nc-base-array @ if,
    nc-ty @ nc-base @ = if, [lit] 238 cc-die then,
    cc-sysv-inherit-array
    [lit] 0 nc-base-array ! [lit] 0 nc-base-inner !
  then,
  nc-ty @ nc-desc @ cc-sysv-signature-fwd nc-desc !
  ty-func r> ty-make nc-ty ! ;
' cc-sysv-fnptr is cc-nfnptr-fwd

```

Identifier-list definitions first save names in source order with provisional `int` types; `cc-sysv-find-parameter` later locates the name being refined (`forth-bootstrap/cc/121-cc-sysv.fth:400`):

```forth file=cc/121-cc-sysv.fth
: cc-sysv-find-parameter ( sig name length -- index|-1 )
  [lit] 0 begin, [lit] 3 cc-npick cc-sysv-sig-count over > while,
    [lit] 3 cc-npick over cc-sysv-sig-name
    dup [lit] 8 + @ [lit] 3 cc-npick = if,
      @ [lit] 3 cc-npick [lit] 3 cc-npick bytes-eq if,
        >r drop 2drop r> exit,
      then,
    else, drop then,
    1+
  repeat, drop drop 2drop true ;
: cc-sysv-identifier-list ( sig -- sig )
  dup cc-sysv-sig-count if, [lit] 233 cc-die then,
  [lit] 6 over [lit] 32 + !
  begin,
    tok-kind @ tk-ident <> if, [lit] 233 cc-die then,
    dup cc-sysv-sig-count cc-sysv-arg-cap >= if, [lit] 234 cc-die then,
    dup tok-str-addr @ tok-str-len @ cc-sysv-find-parameter 0< 0= if,
      [lit] 233 cc-die
    then,
    dup dup cc-sysv-sig-count cc-sysv-sig-name
    tok-str-addr @ over ! tok-str-len @ swap [lit] 8 + !
    dup dup cc-sysv-sig-count cc-sysv-sig-param
    ty-int [lit] 0 ty-make swap !
    [lit] 1 over [lit] 24 + +!
    cc-next-token-keep [char] , cc-tok-punct? if,
      cc-next-token-keep
    else,
      [char] ) cc-tok-punct? 0= if, [lit] 233 cc-die then, exit,
    then,
  again, ;
```

## Keep declaration policy out of the ABI

Storage keywords and accepted source spellings are parser policy. They do not change the register assignment of an integer or pointer argument.

The declaration context counts storage classes wherever they appear among type keywords, rejecting repeated or conflicting choices (`forth-bootstrap/cc/121-cc-sysv.fth:430`):

```forth file=cc/121-cc-sysv.fth
\ C90 parameter declarations allow one register specifier, interleaved
\ with type keywords and qualifiers. Keep this policy in the parameter's
\ own declaration context: an aggregate member uses a different context.
\ Qualifiers retain the shared parser's existing representation; the base
\ type, signedness, pointer depth and descriptor still come from cc-nbase.
variable cc-sysv-parameter-context
variable cc-sysv-parameter-register
\ A file- or block-scope declaration's own base (cc-nstorage-context, 115)
\ also reads storage-class keywords between its type keywords and
\ qualifiers: `int static x`, `long static int y`, `char const static *p`,
\ `unsigned extern long z`, `int typedef T`.  They set the same nc-static,
\ nc-extern and nc-td cells as a leading keyword.  One storage class per
\ declaration, wherever it is written; a second is 233.  So is one in a
\ member or a type name, neither of which declares storage.
: cc-sysv-storage-note
  [lit] 1 nc-storage +! nc-storage @ [lit] 1 > if, [lit] 233 cc-die then, ;
: cc-sysv-storage-specifier? ( -- flag )
  kw-static cc-tok-kw? if, cc-sysv-storage-note true nc-static ! true exit, then,
  kw-extern cc-tok-kw? if, cc-sysv-storage-note true nc-extern ! true exit, then,
  kw-typedef cc-tok-kw? if, cc-sysv-storage-note true nc-td ! true exit, then,
  kw-auto cc-tok-kw? kw-register cc-tok-kw? or if,
    cc-sysv-storage-note true exit,
  then,
  kw-inline cc-tok-kw? ;
: cc-sysv-declaration-specifiers
  nc-storage @ [lit] 1 > if, [lit] 233 cc-die then,
  begin, cc-sysv-storage-specifier? while, cc-next-token-keep repeat, ;
: cc-sysv-storage-keyword? ( -- flag )
  kw-static cc-tok-kw? kw-extern cc-tok-kw? or kw-typedef cc-tok-kw? or
  kw-auto cc-tok-kw? or kw-register cc-tok-kw? or ;
```

Parameter context admits `register` and qualifiers while excluding other storage classes; `cc-sysv-base-trailing` applies the same policy after a typedef name or tag (`forth-bootstrap/cc/121-cc-sysv.fth:478`):

```forth file=cc/121-cc-sysv.fth
: cc-sysv-parameter-specifiers
  cc-target-sysv @ 0= if, exit, then,
  cc-nctx @ cc-nstorage-context @ = if, cc-sysv-declaration-specifiers exit, then,
  cc-nctx @ cc-sysv-parameter-context @ <> if,
    cc-sysv-storage-keyword? if, [lit] 233 cc-die then, exit,
  then,
  begin,
    kw-static cc-tok-kw? kw-extern cc-tok-kw? or
    kw-auto cc-tok-kw? or kw-typedef cc-tok-kw? or
    kw-inline cc-tok-kw? or if, [lit] 233 cc-die then,
    kw-register cc-tok-kw? if,
      cc-sysv-parameter-register @ if, [lit] 233 cc-die then,
      true cc-sysv-parameter-register ! true
    else, cc-qualifier? dup if, cc-qual-note then, then,
  while, cc-next-token-keep repeat, ;
' cc-sysv-parameter-specifiers is cc-nbase-specifiers-fwd
\ After a typedef name, tag or implicit int, the same specifiers and
\ qualifiers may follow before the declarator: `struct S static s`.
: cc-sysv-base-trailing
  cc-target-sysv @ 0= if, exit, then,
  cc-next-token-keep cc-nbase-next-specifier cc-putback-token ;
' cc-sysv-base-trailing is cc-nbase-trailing-fwd
```

`cc-sysv-spec-total`, `cc-sysv-spec-only`, and `cc-sysv-spec-fail` accumulate invalid keyword combinations before `cc-sysv-spec-check` reports them (`forth-bootstrap/cc/121-cc-sysv.fth:482`):

```forth file=cc/121-cc-sysv.fth
\ C90 constrains the multiset of type keywords, whatever their order and
\ any qualifiers between them. Only long may repeat (long long); one sign;
\ void and float stand alone; double admits one long; char admits a sign;
\ short admits int and a sign. Every declaration context rejects with 233.
variable cc-sysv-spec-bad
: cc-sysv-spec-fail ( flag -- ) cc-sysv-spec-bad @ or cc-sysv-spec-bad ! ;
: cc-sysv-spec-total ( -- n )
  [lit] 0 [lit] 0
  begin, dup cc-nspec-slots < while, dup cc-nspec-count rot + swap 1+ repeat, drop ;
\ Fail when any keyword outside the named slots' total is present.
: cc-sysv-spec-only ( allowed -- ) cc-sysv-spec-total swap - [lit] 0 > cc-sysv-spec-fail ;
: cc-sysv-spec-check
  cc-target-sysv @ 0= if, exit, then,
  [lit] 0 cc-sysv-spec-bad !
  [lit] 0
  begin, dup cc-nspec-slots < while,
    dup cc-nspec-count over kw-long = if, [lit] 2 else, [lit] 1 then, >
    cc-sysv-spec-fail 1+
  repeat, drop
  kw-unsigned cc-nspec-count kw-signed cc-nspec-count + dup >r
  [lit] 1 > cc-sysv-spec-fail
  kw-void cc-nspec-count if, kw-void cc-nspec-count cc-sysv-spec-only then,
  cc-nspec-bool cc-nspec-count if,
    cc-nspec-bool cc-nspec-count cc-sysv-spec-only
  then,
  cc-nspec-float cc-nspec-count if,
    cc-nspec-float cc-nspec-count cc-sysv-spec-only
  then,
  cc-nspec-double cc-nspec-count if,
    kw-long cc-nspec-count [lit] 1 > cc-sysv-spec-fail
    cc-nspec-double cc-nspec-count kw-long cc-nspec-count + cc-sysv-spec-only
  then,
  kw-char cc-nspec-count if, kw-char cc-nspec-count r@ + cc-sysv-spec-only then,
  kw-short cc-nspec-count if,
    kw-short cc-nspec-count kw-int cc-nspec-count + r@ + cc-sysv-spec-only
  then,
  r> drop
  cc-sysv-spec-bad @ if, [lit] 233 cc-die then, ;
' cc-sysv-spec-check is cc-nspec-check-fwd
```

Nested parameter parsing saves the outer context, and a function-declared parameter adjusts through the same signature parser as an explicit function pointer (`forth-bootstrap/cc/121-cc-sysv.fth:521`):

```forth file=cc/121-cc-sysv.fth
: cc-sysv-parameter-base ( -- type descriptor )
  cc-sysv-parameter-context @ >r cc-sysv-parameter-register @ >r
  cc-nctx @ cc-sysv-parameter-context !
  [lit] 0 cc-sysv-parameter-register !
  cc-nbase
  \ Aggregate, enum and typedef bases return before trailing specifiers.
  cc-next-token-keep cc-sysv-parameter-specifiers cc-putback-token
  r> cc-sysv-parameter-register ! r> cc-sysv-parameter-context ! ;

\ C adjusts a function-declared parameter to a pointer to that function.
\ Reparse its saved suffix through the same recursive signature parser as
\ an explicit (*callback) declarator, then restore the enclosing delimiter.
: cc-sysv-adjust-function-parameter
  nc-func @ if,
    cc-sysv-declarator-signature nc-desc !
    ty-func [lit] 1 ty-make nc-ty ! [lit] 0 nc-func !
  then, ;

```

## Distinguish prototypes from unspecified lists

In this source dialect, `f()` leaves argument types unspecified; `f(void)` requires no arguments. A definition with an identifier list supplies names that subsequent declarations refine. Keeping those states distinct prevents a later declaration with unspecified parameters from erasing a useful prototype.

Signature construction records the result and opens a fresh declaration context before distinguishing empty, variadic, void, and identifier-list endings (`forth-bootstrap/cc/121-cc-sysv.fth:539`):

```forth file=cc/121-cc-sysv.fth
: cc-sysv-signature ( return-type return-desc -- signature )
  [lit] 2600 cc-alloc dup >r [lit] 2600 cc-nzero
  r@ [lit] 16 + ! r@ [lit] 8 + !
  cc-sysv-signature-tag r@ !
  nc-qualified @ r@ cc-field-set-qualified
  cc-nctx @ >r cc-ncontext
  begin,
    cc-next-token-keep
    [char] ) cc-tok-punct? if,
      r> cc-nctx ! r>
      dup cc-sysv-sig-count if, [lit] 233 cc-die then,
      [lit] 2 over [lit] 32 + ! exit,
    then,
    pt-ellipsis cc-tok-punct? if,
      r> cc-nctx ! r>
      dup cc-sysv-sig-count 0= if, [lit] 233 cc-die then,
      [lit] 1 over [lit] 32 + ! [char] ) cc-expect-punct-c exit,
    then,
    kw-void cc-tok-kw? if,
      cc-peek-mark cc-lex-mark cc-next-token-keep
      [char] ) cc-tok-punct? if,
        r> cc-nctx ! r> dup cc-sysv-sig-count if, [lit] 233 cc-die then, exit,
      then,
      cc-peek-mark cc-lex-reset
    then,
    tok-kind @ tk-ident = cc-native-type-start 0= and if,
      r> cc-nctx ! r> cc-sysv-identifier-list exit,
    then,
```

Each typed parameter is adjusted, checked for a duplicate name, and stored with its descriptor and qualification before the parser advances (`forth-bootstrap/cc/121-cc-sysv.fth:567`):

```forth file=cc/121-cc-sysv.fth
    cc-sysv-parameter-base nc-sdesc ! nc-base ! cc-ndeclarator
    cc-sysv-adjust-function-parameter
    cc-sysv-adjust-array-parameter
    nc-ty @ ty-size 0= if, [lit] 233 cc-die then,
    r> r> dup >r swap >r
    nc-nlen @ if,
      dup nc-name @ nc-nlen @ cc-sysv-find-parameter 0< 0= if,
        [lit] 233 cc-die
      then,
    then,
    dup cc-sysv-sig-count dup cc-sysv-arg-cap >= if, [lit] 234 cc-die then,
    over swap cc-sysv-sig-param
    nc-qualified @ over cc-field-set-qualified
    nc-ty @ over ! nc-desc @ swap [lit] 8 + !
    dup dup cc-sysv-sig-count cc-sysv-sig-name
    nc-name @ over ! nc-nlen @ over [lit] 8 + !
    true swap [lit] 16 + !
    [lit] 1 swap [lit] 24 + +!
    [char] , cc-tok-punct? 0= if,
      [char] ) cc-tok-punct? 0= if, [lit] 184 cc-die then,
      r> cc-nctx ! r> exit,
    then,
  again, ;
' cc-sysv-signature is cc-sysv-signature-fwd

```

Abstract grouped type names preserve every pointer star and reuse the array or function descriptor constructor selected by their suffix (`forth-bootstrap/cc/121-cc-sysv.fth:592`):

```forth file=cc/121-cc-sysv.fth
\ Grouped object-pointer type names add their stars to the base type.
\ Abstract function-pointer type names reuse the declaration signature parser.
\ Each grouped star is retained in the type word beside its signature.
\ Depth one is a function pointer; greater depths point to pointer objects.
\ The operand address is unchanged; loads occur when those objects are read.
: cc-sysv-type-name-raw
  cc-native-type-name
  cc-type-name-qualified @ nc-qualified !
  cc-target-sysv @ 0= if, exit, then,
  cc-next-token-keep
  lparen cc-tok-punct? if,
    [char] * cc-expect-punct-c
    cc-skip-qualifiers cc-count-stars 1+
    dup [lit] 255 > if, [lit] 231 cc-die then, >r
    [char] ) cc-expect-punct-c cc-next-token-keep
    [char] [ cc-tok-punct? if,
      cc-type-name-array @ if, [lit] 238 cc-die then,
      cc-type-name-qualified @ cc-nctx @ >r cc-ncontext >r
      cc-narray-suffix
      nc-bound-mask @ [lit] 2 and nc-inner @ [lit] 0 <= and if, [lit] 238 cc-die then,
      cc-cast-desc @ nc-array @ nc-inner @ r> cc-sysv-qualified-node
      cc-cast-desc !
      r> cc-nctx ! ty-array r> ty-make cc-putback-token
    else,
      lparen cc-tok-punct? if,
        cc-type-name-array @ if, [lit] 238 cc-die then,
        cc-cast-desc @ cc-sysv-signature cc-cast-desc !
        ty-func r> ty-make
      else,
        r@ over ty-ptr + [lit] 255 > if, [lit] 231 cc-die then,
        cc-type-name-array @ if,
          cc-cast-desc @ cc-type-name-array @ cc-type-name-inner @
          cc-type-name-qualified @ cc-sysv-qualified-node cc-cast-desc !
          [lit] 0 cc-type-name-array ! [lit] 0 cc-type-name-inner !
          ty-array [lit] 0 ty-make
        then,
        r> + cc-putback-token
      then,
    then,
  else, cc-putback-token then, ;
```

A type name temporarily clears storage-declaration context and restores surrounding qualifier state, preventing a nested cast from changing its enclosing declaration (`forth-bootstrap/cc/121-cc-sysv.fth:632`):

```forth file=cc/121-cc-sysv.fth
\ A type name shares its enclosing declaration's context but is never a
\ declaration: a storage class inside one, as in an enumerator's
\ sizeof (int static), is 233 (cc-sysv-parameter-specifiers).
: cc-sysv-type-name
  cc-nctx @ 0= if, cc-ncontext then,
  cc-nstorage-context @ >r [lit] 0 cc-nstorage-context !
  nc-qualified @ >r nc-base-qualified @ >r nc-prefix-qualified @ >r
  [lit] 0 nc-prefix-qualified ! cc-sysv-type-name-raw
  nc-qualified @ cc-type-name-qualified !
  r> nc-prefix-qualified ! r> nc-base-qualified ! r> nc-qualified !
  r> cc-nstorage-context ! ;
' cc-sysv-type-name is cc-native-type-name-fwd

```

## Separate address representation from callability

An explicit function-pointer cast changes the selected signature without moving the address. A later indirect call must still use a signature compatible with the actual definition. A pointer to a stored function pointer requires a load before it is callable.

`cc-sysv-cast-types` allows the target’s bit-preserving pointer representation casts and rejects integer destinations too narrow to retain a function address, except for a Boolean test (`forth-bootstrap/cc/121-cc-sysv.fth:664`):

```forth file=cc/121-cc-sysv.fth
\ C permits function-pointer conversions and a round trip back to the
\ original signature. A call still uses its actual selected signature and
\ the normal ABI class checks. Only explicit casts cross to object pointers.
: cc-sysv-function-pointer? ( type -- flag )
  dup ty-base ty-func = swap ty-ptr [lit] 1 = and ;
: cc-sysv-integral? ( type -- flag )
  dup ty-ptr if, drop [lit] 0 exit, then,
  ty-base
  dup ty-char = over ty-uchar = or over ty-short = or
  over ty-ushort = or over ty-int = or over ty-uint = or
  over ty-long = or over ty-ulong = or
  over ty-llong = or over ty-ullong = or swap ty-bool = or ;
\ Explicit LP64 integer/function-pointer representation conversions use
\ all 64 bits. Only pointer-width integral destinations preserve a function
\ address, but any function pointer converts to _Bool by testing it.
\ Explicit function/object pointer casts keep all 64 bits too, as
\ POSIX dlsym and GCC allow; any other function-pointer partner rejects.
\ The policy is pure so constant and runtime casts share it.
\ This permits signal sentinels and address round trips, not arbitrary calls.
: cc-sysv-cast-types ( source destination -- )
  cc-target-sysv @ 0= if, 2drop exit, then,
  dup ty-void [lit] 0 ty-make = if, 2drop exit, then,
  over cc-sysv-integral? over cc-sysv-function-pointer? and if,
    2drop exit,
  then,
  over cc-sysv-function-pointer? over cc-sysv-integral? and if,
    dup ty-base ty-bool <> swap ty-size [lit] 8 <> and if, [lit] 230 cc-die then,
    drop exit,
  then,
  over cc-sysv-function-pointer? over cc-sysv-function-pointer? = if,
    2drop exit,
  then,
  ty-ptr 0= swap ty-ptr 0= or if, [lit] 230 cc-die then, ;
' cc-sysv-cast-types is cc-cast-types-fwd
```

Runtime integer casts normalize width and signedness before conversion; `cc-sysv-cast-null` separately tracks whether a cast preserves null-pointer-constant status (`forth-bootstrap/cc/121-cc-sysv.fth:692`):

```forth file=cc/121-cc-sysv.fth
\ Normalize an integral operand before replacing its type with a pointer:
\ signed narrow values extend their sign and unsigned ones extend zero.
: cc-sysv-cast-value ( source destination -- )
  cc-target-sysv @ if,
    over cc-sysv-integral? over cc-sysv-function-pointer? and if,
      over cc-emit-convert-rdi
    then,
  then,
  cc-emit-convert-value ;
' cc-sysv-cast-value is cc-cast-value-fwd
\ Qualified void pointees do not form null pointer constants. The flattened
\ qualifier flag also conservatively excludes top-level-qualified void*.
\ Read the cast target's saved flag, never metadata left by a nested cast.
: cc-sysv-cast-null ( source destination null qualified -- null )
  swap >r >r
  dup cc-sysv-integral? swap ty-void [lit] 1 ty-make = r> 0= and or
  swap cc-sysv-integral? and r> and cc-target-sysv @ and ;
' cc-sysv-cast-null is cc-cast-null-fwd
: cc-sysv-ternary-split cc-target-sysv @ ;
' cc-sysv-ternary-split is cc-value-ternary-split-fwd


```

## Compare the shape behind a pointer


`cc-sysv-compatible-types` recursively compares function signatures and array elements, while record pointers retain descriptor identity (`forth-bootstrap/cc/121-cc-sysv.fth:715`):

```forth file=cc/121-cc-sysv.fth
\ Type identity is checked at redeclarations. Struct pointers retain tag
\ identity; function-pointer signatures compare recursively by shape.
\ A row reached through a pointer carries its qualifier set on its node;
\ a nested array element's rows share the outer node's set, so only
\ pointer-to-row types have a set of their own to compare.
: cc-sysv-row-set ( type descriptor -- set )
  over ty-base ty-array = [lit] 2 cc-npick ty-ptr 0= 0= and over 0= 0= and if,
    nip cc-ad-qualified exit,
  then, 2drop [lit] 0 ;
\ cc-sysv-compatible-types compares shape, and below the outermost level,
\ qualifier sets exactly: `const long (*a[2])[3]` and `long (*b[2])[3]` are
\ incompatible.  The outermost row's set is left to the caller, since an
\ assignment may add a qualifier there (cc-sysv-row-qualifier-check).
defer cc-sysv-compatible-signatures-fwd
: cc-sysv-compatible-types ( ty1 desc1 ty2 desc2 -- flag )
  >r swap >r
  2dup <> if, 2drop r> drop r> drop [lit] 0 exit, then,
  drop ty-base
  dup ty-func = if,
    drop r> r> cc-sysv-compatible-signatures-fwd exit,
  then,
  dup ty-array = if,
    drop r> r>
    2dup 0= swap 0= or if, [lit] 237 cc-die then,
    2dup cc-ad-count swap cc-ad-count <> if, 2drop [lit] 0 exit, then,
    2dup cc-ad-inner swap cc-ad-inner <> if, 2drop [lit] 0 exit, then,
    dup cc-ad-type swap cc-ad-desc >r >r
    dup cc-ad-type swap cc-ad-desc r> r>
    [lit] 3 cc-npick [lit] 3 cc-npick cc-sysv-row-set
    [lit] 2 cc-npick [lit] 2 cc-npick cc-sysv-row-set <> if,
      2drop 2drop [lit] 0 exit,
    then,
    cc-sysv-compatible-types exit,
  then,
  ty-struct = if, r> r> = else, r> drop r> drop true then, ;
```

Redeclarations require equal row qualifier sets through `cc-sysv-same-types`; an implicit value conversion may add an outer row qualifier but cannot discard one (`forth-bootstrap/cc/121-cc-sysv.fth:739`):

```forth file=cc/121-cc-sysv.fth
\ cc-sysv-same-types also requires equal outermost row sets: redeclared
\ objects and prototype parameters and results must match exactly, so
\ `extern const long (*p)[3]; extern volatile long (*p)[3];` is 237.
: cc-sysv-same-types ( ty1 desc1 ty2 desc2 -- flag )
  [lit] 3 cc-npick [lit] 3 cc-npick cc-sysv-row-set
  [lit] 2 cc-npick [lit] 2 cc-npick cc-sysv-row-set <> if,
    2drop 2drop [lit] 0 exit,
  then,
  cc-sysv-compatible-types ;
\ Implicit conversion may add a row qualifier but never discard one:
\ `long (*p)[3] = t` with `const long t[2][3]` needs an explicit cast
\ (238), and so does `const long (*q)[3] = v` from volatile rows.  Below
\ the first pointer the sets must be equal (C90 6.3.16.1: the pointed-to
\ types must be compatible), so `const long (**q)[3] = &p` from
\ `long (*p)[3]` is 237.
: cc-sysv-row-qualifier-check ( source descriptor destination descriptor -- same )
  [lit] 3 cc-npick ty-base ty-array = [lit] 2 cc-npick ty-base ty-array = and
  [lit] 3 cc-npick 0= 0= and over 0= 0= and if,
    [lit] 3 cc-npick [lit] 3 cc-npick cc-sysv-row-set
    [lit] 2 cc-npick [lit] 2 cc-npick cc-sysv-row-set
    [lit] 3 cc-npick ty-ptr [lit] 1 > if,
      <> if, [lit] 237 cc-die then,
    else,
      cc-invert and if, [lit] 238 cc-die then,
    then,
  then, ;
```

`cc-sysv-value-shape` applies that distinction at value boundaries, handling Boolean conversion, null constants, and the permitted generic-pointer cases first (`forth-bootstrap/cc/121-cc-sysv.fth:762`):

```forth file=cc/121-cc-sysv.fth
: cc-sysv-value-shape ( source descriptor destination descriptor -- )
  cc-target-sysv @ 0= if, 2drop 2drop exit, then,
  \ Every scalar, a function or array pointer included, converts to _Bool.
  over dup ty-ptr 0= swap ty-base ty-bool = and if, 2drop 2drop exit, then,
  [lit] 3 cc-npick ty-base ty-array = [lit] 2 cc-npick ty-base ty-array = or
  [lit] 4 cc-npick ty-base ty-func = [lit] 3 cc-npick ty-base ty-func = or or if,
    [lit] 3 cc-npick ty-ptr 0= [lit] 2 cc-npick ty-ptr 0= or if,
      cc-last-expr-null @ 0= if, [lit] 237 cc-die then,
      2drop 2drop exit,
    then,
    [lit] 3 cc-npick ty-void [lit] 1 ty-make =
    [lit] 2 cc-npick ty-void [lit] 1 ty-make = or if, 2drop 2drop exit, then,
    [lit] 3 cc-npick [lit] 3 cc-npick [lit] 3 cc-npick [lit] 3 cc-npick
    cc-sysv-compatible-types 0= if, [lit] 237 cc-die then,
    cc-sysv-row-qualifier-check 2drop 2drop
  else, 2drop 2drop then, ;
' cc-sysv-value-shape is cc-value-shape-fwd
```

## Check array-pointer operators

Array-pointer arithmetic permits compatible pointer comparisons and subtraction, or integral stepping; `cc-sysv-array-pair-check` keeps unrelated row shapes from mixing (`forth-bootstrap/cc/121-cc-sysv.fth:783`):

```forth file=cc/121-cc-sysv.fth
: cc-sysv-array-operands?
  cc-target-sysv @ if,
    cc-expr-left-type @ ty-base ty-array = cc-expr-right-type @ ty-base ty-array = or
  else, [lit] 0 then, ;
: cc-sysv-array-pair-check
  cc-expr-left-type @ cc-expr-left-desc @ cc-expr-right-type @ cc-expr-right-desc @
  cc-sysv-compatible-types 0= if, [lit] 237 cc-die then, ;
: cc-sysv-array-binop
  cc-sysv-array-operands? 0= if, exit, then,
  cc-expr-left-type @ ty-ptr cc-expr-right-type @ ty-ptr and if,
    cc-expr-op-row @ bo-op + @ [char] - =
    cc-expr-op-row @ bo-level + @ dup level-rel = swap level-eq = or or
    0= if, [lit] 237 cc-die then,
    cc-sysv-array-pair-check exit,
  then,
  cc-expr-op-row @ bo-level + @ level-add = if,
    cc-expr-left-type @ ty-ptr if,
      cc-expr-right-type @ cc-sysv-integral? 0= if, [lit] 237 cc-die then,
    else,
      cc-expr-op-row @ bo-op + @ [char] + <>
      cc-expr-left-type @ cc-sysv-integral? 0= or if, [lit] 237 cc-die then,
    then, exit,
  then,
  cc-expr-op-row @ bo-level + @ level-eq = if,
    cc-expr-left-type @ ty-ptr if, cc-expr-right-null @ else, cc-expr-left-null @ then,
    if, exit, then,
  then,
  [lit] 237 cc-die ;
' cc-sysv-array-binop is cc-array-binop-fwd
```

Compound stepping requires an integral increment, and a conditional combines compatible row qualifiers while distinguishing a null constant from a pointer variable (`forth-bootstrap/cc/121-cc-sysv.fth:808`):

```forth file=cc/121-cc-sysv.fth
: cc-sysv-array-compound
  cc-sysv-array-operands? if,
    cc-expr-left-type @ ty-ptr 0= cc-expr-right-type @ cc-sysv-integral? 0= or
    if, [lit] 237 cc-die then,
  then, ;
' cc-sysv-array-compound is cc-array-compound-fwd
: cc-sysv-array-ternary
  cc-target-sysv @ 0= if, exit, then,
  cc-expr-left-type @ ty-void [lit] 0 ty-make =
  cc-expr-right-type @ ty-void [lit] 0 ty-make = or if,
    cc-expr-left-type @ cc-expr-right-type @ <> if, [lit] 237 cc-die then,
    ty-void [lit] 0 ty-make cc-expr-common ! exit,
  then,
  cc-expr-left-type @ ty-ptr cc-expr-right-type @ ty-ptr or 0= if, exit, then,
  \ A null pointer constant adopts the other arm's pointer type. A void*
  \ variable, including one whose runtime value is zero, is not such a constant.
  cc-expr-left-null @ cc-expr-right-type @ ty-ptr and if,
    cc-expr-right-type @ cc-expr-common ! exit,
  then,
  cc-expr-right-null @ cc-expr-left-type @ ty-ptr and if,
    cc-expr-left-type @ cc-expr-common ! exit,
  then,
  cc-expr-left-type @ ty-ptr 0= cc-expr-right-type @ ty-ptr 0= or
  if, [lit] 237 cc-die then,
  cc-expr-left-type @ ty-void [lit] 1 ty-make =
  cc-expr-right-type @ ty-void [lit] 1 ty-make = or if,
    cc-expr-left-type @ cc-sysv-function-pointer?
    cc-expr-right-type @ cc-sysv-function-pointer? or if, [lit] 237 cc-die then,
    ty-void [lit] 1 ty-make cc-expr-common ! exit,
  then,
  cc-sysv-array-pair-check
  \ Either arm's row qualifier qualifies the result, which takes the left
  \ arm's node.
  cc-expr-left-type @ ty-base ty-array = if,
    cc-expr-left-desc @ cc-expr-right-desc @ cc-ad-qualified
    cc-sysv-qualify-node cc-expr-left-desc !
  then, ;
' cc-sysv-array-ternary is cc-array-ternary-fwd
```

Row qualifiers are descriptor sets. Scalar pointer qualification remains less precise: this representation does not consistently distinguish qualification of a scalar pointee from qualification of the pointer itself.

## Compare declarations before emitting calls


`cc-sysv-default-type` models default promotions even for declaration-only types; `cc-sysv-comparison-param` uses them when an identifier-list definition meets a prototype (`forth-bootstrap/cc/121-cc-sysv.fth:846`):

```forth file=cc/121-cc-sysv.fth
: cc-sysv-signature-result dup cc-sysv-sig-return swap cc-sysv-sig-desc ;
: cc-sysv-parameter-type cc-sysv-sig-param dup @ swap [lit] 8 + @ ;
\ Default promotions matter to prototype compatibility even for types
\ whose executable calling convention is deliberately unsupported.
: cc-sysv-default-type ( type -- promoted-type )
  dup ty-ptr 0= over ty-base ty-float = and if,
    drop ty-double [lit] 0 ty-make
  else, cc-unary-type then, ;
: cc-sysv-comparison-param ( sig index -- type desc )
  over cc-sysv-prototype? >r cc-sysv-parameter-type
  r> 0= if, swap cc-sysv-default-type swap then, ;
: cc-sysv-default-compatible? ( sig -- flag )
  dup cc-sysv-sig-varargs [lit] 1 and if, drop [lit] 0 exit, then,
  [lit] 0 begin, over cc-sysv-sig-count over > while,
    2dup cc-sysv-sig-param @ dup cc-sysv-default-type <> if,
      2drop [lit] 0 exit,
    then, 1+
  repeat, 2drop true ;
```

Signature compatibility checks the result first, then the known parameter counts, variadic state, and recursively compatible promoted parameter types (`forth-bootstrap/cc/121-cc-sysv.fth:864`):

```forth file=cc/121-cc-sysv.fth
: cc-sysv-compatible-signatures ( sig1 sig2 -- flag )
  2dup cc-sysv-check-signature drop cc-sysv-check-signature drop
  2dup >r cc-sysv-signature-result r> cc-sysv-signature-result
  cc-sysv-same-types 0= if, 2drop [lit] 0 exit, then,
  over cc-sysv-known-params? 0= if,
    nip dup cc-sysv-prototype? if, cc-sysv-default-compatible?
    else, drop true then, exit,
  then,
  dup cc-sysv-known-params? 0= if,
    drop dup cc-sysv-prototype? if, cc-sysv-default-compatible?
    else, drop true then, exit,
  then,
  2dup cc-sysv-sig-count swap cc-sysv-sig-count <> if, 2drop [lit] 0 exit, then,
  2dup cc-sysv-sig-varargs [lit] 1 and
  swap cc-sysv-sig-varargs [lit] 1 and <> if, 2drop [lit] 0 exit, then,
  [lit] 0 begin, over cc-sysv-sig-count over > while,
    [lit] 2 cc-npick over cc-sysv-comparison-param
    [lit] 3 cc-npick [lit] 3 cc-npick cc-sysv-comparison-param
    cc-sysv-same-types 0= if, drop 2drop [lit] 0 exit, then,
    1+
  repeat, drop 2drop true ;
' cc-sysv-compatible-signatures is cc-sysv-compatible-signatures-fwd

```

## Keep an external identity after a block ends

An undeclared call uses the source dialect’s implicit `extern int` declaration. Its name has block scope, but its pending calls must survive after the parser reuses that block’s symbol slots. A persistent translation-unit record separates those lifetimes.

`cc-sysv-implicit-find` and `cc-sysv-implicit-symbol` locate that record; call and address fixup accessors redirect to its persistent cells (`forth-bootstrap/cc/121-cc-sysv.fth:887`):

```forth file=cc/121-cc-sysv.fth
\ C90 implicit externs keep scoped visibility but persistent declaration
\ identity and fixups: a block's symbol IDs may be reused after it exits.
\ Record: next, name, length, unspecified-int signature, calls, addresses.
variable cc-sysv-implicit-head
variable cc-sysv-implicit-count
: cc-sysv-implicit-find ( name length -- record|0 )
  cc-nf-u ! cc-nf-a ! cc-sysv-implicit-head @
  begin, dup while,
    dup [lit] 16 + @ cc-nf-u @ = if,
      dup [lit] 8 + @ cc-nf-a @ cc-nf-u @ bytes-eq if, exit, then,
    then, @
  repeat, ;
: cc-sysv-implicit-symbol ( id -- record|0 )
  dup cc-sym-kind-of sk-func <> if, drop [lit] 0 exit, then,
  dup cc-sym-name-addr cell[] @ swap cc-sym-name-len cell[] @ cc-sysv-implicit-find ;
: cc-sysv-call-fixups ( id -- cell )
  cc-target-sysv @ if,
    dup cc-sysv-implicit-symbol dup if, nip [lit] 32 + exit, then, drop
  then, cc-sym-call-fixups-default ;
: cc-sysv-address-fixups ( id -- cell )
  cc-target-sysv @ if,
    dup cc-sysv-implicit-symbol dup if, nip [lit] 40 + exit, then, drop
  then, cc-sym-addr-fixups-default ;
' cc-sysv-call-fixups is cc-sym-call-fixups
' cc-sysv-address-fixups is cc-sym-addr-fixups
: cc-sysv-implicit-record ( name length -- record )
```

Creating an implicit record installs an unspecified `int` signature; `cc-sysv-implicit-error` can instead request rejection, with message pieces retained for the diagnostic (`forth-bootstrap/cc/121-cc-sysv.fth:913`):

```forth file=cc/121-cc-sysv.fth
  2dup cc-sysv-implicit-find dup if, nip nip exit, then, drop
  cc-sysv-implicit-count @ 1+ cc-sym-cap [lit] 60 cc-check-cap
  [lit] 1 cc-sysv-implicit-count +!
  [lit] 48 cc-alloc dup >r [lit] 48 cc-nzero
  r@ [lit] 16 + ! r@ [lit] 8 + !
  cc-sysv-implicit-head @ r@ ! r@ cc-sysv-implicit-head !
  [lit] 2600 cc-alloc dup [lit] 2600 cc-nzero
  cc-sysv-signature-tag over !
  ty-int [lit] 0 ty-make over [lit] 8 + !
  [lit] 2 over [lit] 32 + ! r@ [lit] 24 + ! r> ;
: cc-sysv-implicit-declared-noop drop ;
defer cc-sysv-implicit-declared-fwd
' cc-sysv-implicit-declared-noop is cc-sysv-implicit-declared-fwd
\ C90 accepts a call to an undeclared function as `extern int f ();`. On
\ LP64 that truncates a pointer or double result, so a driver may set this
\ flag (GCC's -Werror=implicit-function-declaration) to make it error 228.
variable cc-sysv-implicit-error
[lit] 0 cc-sysv-implicit-error !
create cc-sysv-implicit-message                  \ "implicit declaration of function '"
  s, implicit bl c, s, declaration bl c, s, of bl c, s, function bl c, [lit] 39 c,
create cc-sysv-implicit-close [lit] 39 c, [lit] 58 c, bl c,       \ "': "
create cc-sysv-implicit-at s, ' bl c, s, at bl c,     \ "' at "
\ Name the source file and line through the preprocessor's line map, then
\ the usual flattened line: "... function 'f' at a.c:11: cc: line 29: ...".
```

The diagnostic reports mapped source locations when available, and `cc-sysv-unknown-ident` creates a function only when the next token is a call delimiter (`forth-bootstrap/cc/121-cc-sysv.fth:947`):

```forth file=cc/121-cc-sysv.fth
: cc-sysv-implicit-die
  cc-sysv-implicit-message [lit] 34 cc-err-write
  tok-str-addr @ tok-str-len @ cc-err-write
  cc-src-line @ cc-pp-line-map-find if,
    cc-sysv-implicit-at [lit] 5 cc-err-write
    >r cc-err-write cc-sysv-implicit-close [lit] 1 + [lit] 1 cc-err-write
    r> cc-err-dec cc-sysv-implicit-close [lit] 1 + [lit] 2 cc-err-write
  else,
    cc-sysv-implicit-close [lit] 3 cc-err-write
  then, [lit] 228 cc-die ;
: cc-sysv-unknown-ident ( -- id|-1 )
  cc-target-sysv @ 0= if, true exit, then,
  cc-peek-mark cc-lex-mark cc-next-token-keep
  lparen cc-tok-punct? cc-peek-mark cc-lex-reset 0= if, true exit, then,
  cc-sysv-implicit-error @ if, cc-sysv-implicit-die then,
  tok-str-addr @ tok-str-len @ cc-sysv-implicit-record >r
  tok-str-addr @ tok-str-len @ sk-func ty-int [lit] 0 ty-make [lit] 0 cc-sym-add
  r> [lit] 24 + @ over cc-sysv-signatures cell[] !
  dup cc-sysv-implicit-declared-fwd ;
' cc-sysv-unknown-ident is cc-native-unknown-ident-fwd
```

A later declaration must agree with the persistent signature and external linkage; standalone program completion rejects fixups still lacking a definition (`forth-bootstrap/cc/121-cc-sysv.fth:957`):

```forth file=cc/121-cc-sysv.fth
: cc-sysv-check-implicit-signature ( signature -- )
  nc-name @ nc-nlen @ cc-sysv-implicit-find dup if,
    nc-static @ if, [lit] 237 cc-die then,
    [lit] 24 + @ cc-sysv-compatible-signatures 0= if, [lit] 237 cc-die then,
  else, 2drop then, ;
\ A file-scope object cannot replace an earlier implicit external function;
\ a typedef or a block-local object has no conflicting external linkage.
: cc-sysv-implicit-declarator
  nc-top @ nc-func @ 0= and nc-td @ 0= and if,
    nc-name @ nc-nlen @ cc-sysv-implicit-find if, [lit] 237 cc-die then,
  then, ;
' cc-sysv-implicit-declarator is cc-sysv-implicit-declarator-fwd
: cc-sysv-check-implicit-defined
  cc-sysv-implicit-head @ begin, dup while,
    dup [lit] 32 + @ over [lit] 40 + @ or if, [lit] 206 cc-die then, @
  repeat, drop ;

```

## Recover a call’s result type

| Symbol input | Result |
|---|---|
| `cc-sysv-symbol-signature` | Validated function or function-pointer signature |
| `cc-sysv-call-qualified` | Qualification of the declared result |
| `cc-sysv-function-desc` | Descriptor used for a function address |
| `cc-sysv-call-result` | Result type and descriptor used by an expression |

These symbol adapters expose the retained signature to existing expression hooks and preserve their native defaults (`forth-bootstrap/cc/121-cc-sysv.fth:974`):

```forth file=cc/121-cc-sysv.fth
: cc-sysv-symbol-signature ( id -- signature )
  dup cc-sym-kind-of sk-func = if,
    cc-sysv-signatures cell[] @
  else,
    dup cc-sym-type-of cc-sysv-function-pointer? 0= if, [lit] 230 cc-die then,
    cc-sym-struct-desc-of
  then, cc-sysv-check-signature ;
: cc-sysv-call-qualified
  cc-target-sysv @ if, cc-sysv-symbol-signature cc-field-qualified
  else, drop [lit] 0 then, ;
' cc-sysv-call-qualified is cc-native-call-qualified-fwd

: cc-sysv-function-desc
  cc-target-sysv @ if, cc-sysv-symbol-signature
  else, cc-native-function-desc then, ;
' cc-sysv-function-desc is cc-native-function-desc-fwd
: cc-sysv-call-result
  cc-target-sysv @ if,
    cc-sysv-symbol-signature dup cc-sysv-sig-return swap cc-sysv-sig-desc
  else, cc-native-call-result then, ;
' cc-sysv-call-result is cc-native-call-result-fwd

```

## Keep expression temporaries alive

Arguments are evaluated before the register/stack split. Staging them keeps nested calls from destroying earlier arguments and gives the final call sequence a stable source vector.

Return to `add(&base, 1, 2, 3, 4, 5, 6, 7)`. The prototype converts each
integer literal to `long` before saving it. Once the vector has been
reversed into parameter order, it holds `&base` followed by 1 through 7.
These eight temporary cells are the source of the outgoing values; they
are not yet the callee's stack arguments. `cc-sysv-prepare-call` will copy
6 and 7 into a separate outgoing block and load the other six values into
registers, producing the layout in the opening table.

`cc-sysv-parse-args` converts fixed arguments to their prototype types, promotes unspecified arguments, checks arity, and reverses the staged vector into parameter order (`forth-bootstrap/cc/121-cc-sysv.fth:1001`):

```forth file=cc/121-cc-sysv.fth
\ Stage each argument in an eight-byte temporary, converting fixed arguments
\ to the prototype's actual width before the register/stack split.
: cc-sysv-argument-check-default ( signature index -- ) 2drop ;
defer cc-sysv-argument-check-fwd
' cc-sysv-argument-check-default is cc-sysv-argument-check-fwd
: cc-sysv-parse-args ( signature -- count )
  [lit] 0 cc-next-token-keep
  [char] ) cc-tok-punct? 0= if,
    cc-putback-token
    begin,
      dup cc-sysv-arg-cap >= if, [lit] 234 cc-die then,
      cc-parse-assign-fwd cc-emit-materialize
      2dup cc-sysv-argument-check-fwd
      cc-expr-unevaluated @ 0= if, cc-last-expr-type @ cc-sysv-check-scalar-default then,
      over cc-sysv-sig-count over > [lit] 2 cc-npick cc-sysv-prototype? and if,
        2dup cc-sysv-sig-param @
        cc-expr-unevaluated @ 0= if, dup cc-sysv-check-scalar-default then,
        cc-last-expr-type @ swap cc-emit-convert-value
      else,
        over cc-sysv-sig-varargs [lit] 3 and 0= if, [lit] 235 cc-die then,
        cc-last-expr-type @ cc-unary-type cc-emit-convert-rdi
      then,
      cc-emit-push-rdi 1+
      cc-next-token-keep [char] , cc-tok-punct? 0=
    until,
    [char] ) cc-tok-punct? 0= if, [lit] 121 cc-die then,
  then,
  over cc-sysv-prototype? if,
    over cc-sysv-sig-count over > if, [lit] 235 cc-die then,
  then,
  nip dup cc-native-reverse-args ;

```

Push/pop hooks count live expression cells; staged loads map the first six integer-class arguments to `rdi`, `rsi`, `rdx`, `rcx`, `r8`, and `r9`, while later arguments need outgoing stack slots (`forth-bootstrap/cc/121-cc-sysv.fth:1028`):

```forth file=cc/121-cc-sysv.fth
\ Count actual expression/argument pushes, separately from lexical switch
\ saves. A call snapshots the complete surviving span, including outer-call
\ arguments and switch RBX saves; its own argument vector is transient.
variable cc-sysv-stack-depth
: cc-sysv-track-push
  cc-target-sysv @ if, [lit] 1 cc-sysv-stack-depth +! then, ;
: cc-sysv-track-pop
  cc-target-sysv @ if,
    cc-sysv-stack-depth @ 0= if, [lit] 239 cc-die then,
    [lit] 1 cc-sysv-stack-depth -!
  then, ;
' cc-sysv-track-push is cc-emit-track-push-fwd
' cc-sysv-track-pop is cc-emit-track-pop-fwd

: cc-sysv-stack-count [lit] 6 - dup 0< if, drop [lit] 0 then, ;
: cc-sysv-load-staged ( index modrm -- )
  cc-emit-byte [lit] 8 * cc-emit-4le ;
: cc-sysv-load-gp ( index -- )
  dup [lit] 4 < if, [lit] 73 else, [lit] 77 then, cc-emit-byte
  [lit] 139 cc-emit-byte
  dup [lit] 0 = if, [lit] 187 else,
  dup [lit] 1 = if, [lit] 179 else,
  dup [lit] 2 = if, [lit] 147 else,
  dup [lit] 3 = if, [lit] 139 else,
  dup [lit] 4 = if, [lit] 131 else, [lit] 139
  then, then, then, then, then, cc-sysv-load-staged ;
: cc-sysv-store-outgoing ( offset -- )
  [lit] 72 cc-emit-byte [lit] 137 cc-emit-byte
  [lit] 132 cc-emit-byte [lit] 36 cc-emit-byte cc-emit-4le ;
```

A call record describes the original stack pointer, surviving span, and staged span; saving and restoring the surviving cells uses persistent local slots rather than the outgoing call area (`forth-bootstrap/cc/121-cc-sysv.fth:1057`):

```forth file=cc/121-cc-sysv.fth
\ Call record: RSP frame slot, surviving cell count, staged cell count.
: cc-sysv-save-live ( record -- )
  >r
  [lit] 72 cc-emit-byte [lit] 137 cc-emit-byte
  r@ @ [lit] 101 cc-emit-local-ea                \ mov [rbp+slot],rsp
  [lit] 0 begin, dup r@ [lit] 8 + @ < while,
    [lit] 72 cc-emit-byte [lit] 139 cc-emit-byte
    [lit] 188 cc-emit-byte [lit] 36 cc-emit-byte
    dup r@ [lit] 16 + @ + [lit] 8 * cc-emit-4le
    dup r@ @ + 1+ cc-emit-store-local
    1+
  repeat, drop r> drop ;
: cc-sysv-restore-live ( record -- )
  >r
  [lit] 72 cc-emit-byte [lit] 139 cc-emit-byte
  r@ @ [lit] 101 cc-emit-local-ea                \ mov rsp,[rbp+slot]
  [lit] 0 begin, dup r@ [lit] 8 + @ < while,
    dup r@ @ + 1+ cc-emit-load-local
    [lit] 72 cc-emit-byte [lit] 137 cc-emit-byte
    [lit] 188 cc-emit-byte [lit] 36 cc-emit-byte
    dup r@ [lit] 16 + @ + [lit] 8 * cc-emit-4le
    1+
  repeat, drop r> drop ;
```

Saving only `rsp` would not preserve operands across a second return from a function such as `setjmp`: intervening calls could overwrite an operand before the pointer was restored. The saved span includes outer argument staging and switch saves, but excludes this call’s disposable argument vector. This scheme assumes fixed frames.

`cc-sysv-prepare-call` snapshots that span, points `r11` at the staged vector, reserves stack-argument space plus padding, and rounds `rsp` down to a multiple of sixteen before copying arguments (`forth-bootstrap/cc/121-cc-sysv.fth:1080`):

```forth file=cc/121-cc-sysv.fth
: cc-sysv-prepare-call ( count indirect? -- record )
  >r dup r> if, 1+ then,
  [lit] 24 cc-alloc dup >r [lit] 16 + !
  cc-sysv-stack-depth @ r@ [lit] 16 + @ -
  dup 0< if, [lit] 239 cc-die then,
  cc-switch-depth @ + dup r@ [lit] 8 + !
  cc-expr-unevaluated @ if,
    drop [lit] 0 r@ ! [lit] 0 r@ [lit] 8 + !
  else,
    cc-fn-local-count @ r@ ! 1+ cc-fn-add-slots
  then,
  r@ cc-sysv-save-live
  \ Align a fresh outgoing block below every staged and surviving value.
  [lit] 73 cc-emit-byte [lit] 137 cc-emit-byte [lit] 227 cc-emit-byte
  [lit] 72 cc-emit-byte [lit] 129 cc-emit-byte [lit] 236 cc-emit-byte
  dup cc-sysv-stack-count [lit] 8 * [lit] 15 + cc-emit-4le
  [lit] 72 cc-emit-byte [lit] 131 cc-emit-byte
  [lit] 228 cc-emit-byte [lit] 240 cc-emit-byte
  [lit] 6 begin, 2dup > while,
    [lit] 73 cc-emit-byte [lit] 139 cc-emit-byte
    dup [lit] 131 cc-sysv-load-staged
    dup [lit] 6 - [lit] 8 * cc-sysv-store-outgoing
    1+
  repeat, drop
  [lit] 0 begin, 2dup > over [lit] 6 < and while,
    dup cc-sysv-load-gp 1+
  repeat, 2drop r> ;
```

The seventh argument occupies the outgoing block’s first slot. After `call` pushes its return address, that argument sits just above the return address in the callee. Padding is above the copied argument block, so it never separates the return address from the first stack argument.

Call completion restores the saved span and discards staging before moving `rax` into the expression register; indirect targets use `r10`, leaving `al` free to report zero vector arguments (`forth-bootstrap/cc/121-cc-sysv.fth:1107`):

```forth file=cc/121-cc-sysv.fth
: cc-sysv-finish-call ( count indirect? record -- )
  >r 2drop r@ cc-sysv-restore-live
  r@ [lit] 16 + @ dup cc-sysv-stack-depth @ swap - cc-sysv-stack-depth !
  cc-native-drop-args r> drop
  cc-emit-mov-rdi-rax ;
: cc-sysv-zero-vector-count
  [lit] 49 cc-emit-byte [lit] 192 cc-emit-byte ;
: cc-sysv-call-staged-target ( count -- )
  \ r10 is independent of AL, which reports zero vector arguments.
  [lit] 77 cc-emit-byte [lit] 139 cc-emit-byte
  [lit] 147 cc-sysv-load-staged
  cc-sysv-zero-vector-count
  [lit] 65 cc-emit-byte [lit] 255 cc-emit-byte [lit] 210 cc-emit-byte ;
defer cc-sysv-result-value-fwd
' cc-emit-convert-rdi is cc-sysv-result-value-fwd

```

## Emit direct and indirect calls

The argument locations are now settled, but `caller.c` still cannot name
an instruction address for `add`. Its direct call therefore reserves a
relative-displacement field and attaches that field to `add`'s fixup list.
Staging answers how to send the values; the fixup records where control
must eventually go. Object completion will turn that obligation into a
[relocation request](#finish-the-translation-unit).

A direct call either reaches a known address or joins a fixup list; a named function-pointer object instead stages its loaded target before evaluating arguments (`forth-bootstrap/cc/121-cc-sysv.fth:1123`):

```forth file=cc/121-cc-sysv.fth
: cc-sysv-call ( id -- )
  cc-target-sysv @ 0= if, cc-parse-native-call exit, then,
  cc-check-static-init
  dup cc-sysv-symbol-signature >r
  dup cc-sym-kind-of sk-func <> if,
    dup cc-sym-kind-of sk-local = if,
      cc-sym-val-of cc-emit-load-local
    else, cc-sym-val-of cc-emit-global-ref cc-emit-load-via-rdi then,
    cc-emit-push-rdi
    r@ cc-sysv-parse-args dup true cc-sysv-prepare-call >r
    dup cc-sysv-call-staged-target true r> cc-sysv-finish-call
  else,
    r@ cc-sysv-parse-args dup [lit] 0 cc-sysv-prepare-call >r >r
    cc-sysv-zero-vector-count
    dup cc-sym-val-of 0= if,
      cc-emit-call-rel32-placeholder
      cc-expr-unevaluated @ if, 2drop
      else, swap cc-sym-call-fixups cc-add-fixup-to-list then,
    else, cc-sym-val-of cc-emit-call-vaddr then,
    r> [lit] 0 r> cc-sysv-finish-call
  then,
  r> cc-sysv-sig-return cc-sysv-result-value-fwd ;
' cc-sysv-call is cc-native-call-fwd
```

An arbitrary callable expression uses the same staging and recovery, normalizes the returned integer to its declared width, then attaches the signature’s result descriptor and qualifiers (`forth-bootstrap/cc/121-cc-sysv.fth:1146`):

```forth file=cc/121-cc-sysv.fth
: cc-sysv-check-callable ( type -- )
  dup ty-base ty-func <> swap ty-ptr [lit] 1 > or if, [lit] 230 cc-die then, ;
: cc-sysv-indirect-call
  cc-target-sysv @ 0= if, cc-parse-indirect-call exit, then,
  cc-check-static-init
  cc-last-expr-type @ cc-sysv-check-callable
  cc-last-struct-desc @ cc-sysv-check-signature >r
  cc-emit-materialize cc-emit-push-rdi
  r@ cc-sysv-parse-args dup true cc-sysv-prepare-call >r
  dup cc-sysv-call-staged-target true r> cc-sysv-finish-call
  r@ cc-sysv-sig-return dup cc-sysv-result-value-fwd
  r> dup cc-field-qualified >r cc-sysv-sig-desc cc-mark-typed-value
  r> cc-last-expr-qualified ! ;
' cc-sysv-indirect-call is cc-native-indirect-fwd

```

<span id="save-the-registers-the-caller-owns"></span>

## Preserve the caller's register values

The core prologue already preserves `rbp` (Chapter 31). This target also preserves `rbx`, the expression backend’s other used callee-saved register. Incoming arguments are copied into typed local slots so body expressions no longer depend on argument registers.

In the separately compiled `add` definition, the parameter emitter uses
the same signature to recover `base` from RDI and `a` through `e` from the
next five GP registers. It recovers `f` and `g` from `[rbp + 16]` and
`[rbp + 24]`, then copies them into local parameter slots too. The body
dereferences its `base` pointer to obtain 14 and adds the seven local
parameters: `14 + 1 + 2 + 3 + 4 + 5 + 6 + 7 = 42`. It returns a `long`
in RAX; the caller's result hook moves that value back into its expression
register. Neither side needed the other's source.

The first local slot holds saved `rbx`; `cc-sysv-store-gp` dispatches register arguments to the matching local-store emitter (`forth-bootstrap/cc/121-cc-sysv.fth:1172`):

```forth file=cc/121-cc-sysv.fth
\ RBX is the only callee-saved expression register. RBP is saved by090;
\ R12..R15 are never touched. Reserve local slot0 before any parameters.
: cc-sysv-restore-callee
  cc-target-sysv @ if,
    [lit] 72 cc-emit-byte [lit] 139 cc-emit-byte
    [lit] 93 cc-emit-byte [lit] 248 cc-emit-byte
  then, ;
' cc-sysv-restore-callee is cc-emit-restore-callee-fwd
: cc-sysv-save-callee
  [lit] 72 cc-emit-byte [lit] 137 cc-emit-byte
  [lit] 93 cc-emit-byte [lit] 248 cc-emit-byte ;
: cc-sysv-store-gp ( index -- )
  dup 1+ swap
  dup [lit] 0 = if, drop cc-emit-store-local exit, then,
  dup [lit] 1 = if, drop cc-emit-store-local-from-rsi exit, then,
  dup [lit] 2 = if, drop cc-emit-store-local-from-rdx exit, then,
  dup [lit] 3 = if, drop cc-emit-store-local-from-rcx exit, then,
  dup [lit] 4 = if, drop cc-emit-store-local-from-r8 exit, then,
  drop cc-emit-store-local-from-r9 ;
```

Identifier-list declarations refine saved names without changing their order; `cc-sysv-abi-type-fwd` is the boundary check before installing an executable parameter (`forth-bootstrap/cc/121-cc-sysv.fth:1180`):

```forth file=cc/121-cc-sysv.fth
\ K&R declarations refine the identifier list by name, preserving order.
\ Undeclared parameters keep C90's implicit int. Only register storage is
\ permitted here; a declaration outside the identifier list is an error.
: cc-sysv-abi-type-default ( type descriptor -- ) drop cc-sysv-check-scalar-default ;
defer cc-sysv-abi-type-fwd
' cc-sysv-abi-type-default is cc-sysv-abi-type-fwd
: cc-sysv-old-parameters ( sig -- )
  cc-nctx @ >r cc-ncontext
  begin, [char] { cc-tok-punct? 0= while,
    cc-sysv-parameter-base nc-sdesc ! nc-base !
    begin,
      cc-ndeclarator
      cc-sysv-adjust-function-parameter
      cc-sysv-adjust-array-parameter
      nc-ty @ nc-desc @ cc-sysv-abi-type-fwd
      nc-ty @ ty-size 0= if, [lit] 233 cc-die then,
      dup nc-name @ nc-nlen @ cc-sysv-find-parameter
      dup 0< if, [lit] 233 cc-die then,
      2dup cc-sysv-sig-name dup [lit] 16 + @ if, [lit] 233 cc-die then,
      true swap [lit] 16 + !
      over swap cc-sysv-sig-param
      nc-qualified @ over cc-field-set-qualified
    nc-ty @ over ! nc-desc @ swap [lit] 8 + !
      [char] , cc-tok-punct?
    while, repeat,
    [char] ; cc-tok-punct? 0= if, [lit] 233 cc-die then,
    cc-next-token-keep
  repeat, drop r> cc-nctx ! ;
```

`cc-sysv-params` installs finalized parameter metadata, while the default variadic-definition hooks reject a body that would need a register save area (`forth-bootstrap/cc/121-cc-sysv.fth:1208`):

```forth file=cc/121-cc-sysv.fth
: cc-sysv-params ( sig -- )
  dup cc-sysv-sig-count cc-native-param-count !
  [lit] 0 begin, over cc-sysv-sig-count over > while,
    2dup cc-sysv-sig-name dup @ nc-name ! [lit] 8 + @ nc-nlen !
    nc-nlen @ 0= if, [lit] 233 cc-die then,
    2dup cc-sysv-sig-param cc-field-qualified nc-qualified !
    2dup cc-sysv-parameter-type nc-desc ! nc-ty !
    nc-ty @ cc-sysv-check-scalar-default
    [lit] 0 nc-array ! [lit] 0 nc-inner !
    sk-local over 1+ cc-ninstall-symbol drop
    [lit] 1 cc-fn-add-slots 1+
  repeat, 2drop ;

\ Later target layers may implement variadic definitions; the default
\ remains a checked rejection until their register-save machinery exists.
: cc-sysv-varargs-prepare-default ( signature -- )
  cc-sysv-sig-varargs [lit] 1 and if, [lit] 236 cc-die then, ;
: cc-sysv-varargs-save-default ;
defer cc-sysv-varargs-prepare-fwd
defer cc-sysv-varargs-save-fwd
' cc-sysv-varargs-prepare-default is cc-sysv-varargs-prepare-fwd
' cc-sysv-varargs-save-default is cc-sysv-varargs-save-fwd

```

Register arguments and incoming stack arguments converge on local slots through `cc-sysv-store-params-default`; the return hook independently validates the result class (`forth-bootstrap/cc/121-cc-sysv.fth:1233`):

```forth file=cc/121-cc-sysv.fth
defer cc-sysv-params-fwd
' cc-sysv-params is cc-sysv-params-fwd
: cc-sysv-store-params-default
  [lit] 0 begin, dup cc-native-param-count @ < while,
    dup [lit] 6 < if, dup cc-sysv-store-gp else,
      [lit] 0 over [lit] 3 - - cc-emit-load-local
      dup 1+ cc-emit-store-local
    then, 1+
  repeat, drop ;
defer cc-sysv-store-params-fwd
' cc-sysv-store-params-default is cc-sysv-store-params-fwd
: cc-sysv-return-check-default ( type descriptor -- ) drop cc-sysv-check-scalar ;
defer cc-sysv-return-check-fwd
' cc-sysv-return-check-default is cc-sysv-return-check-fwd

```

Chapter 46 supplies variadic definitions. Integer-only variadic calls can already report an empty vector-register argument set; that does not supply a variadic callee’s argument cursor.

This completes the value path for `add`. On the first-pass route, continue
to [object completion](#finish-the-translation-unit) to settle what the
caller can export before the call has a destination. The intervening
sections implement function-body setup and the persistent object records
used there.

## Build the body from its retained signature

A block-scope function declaration checks a visible function or creates a scoped symbol backed by the persistent external record; `cc-sysv-function-signature` holds the selected signature (`forth-bootstrap/cc/121-cc-sysv.fth:1246`):

```forth file=cc/121-cc-sysv.fth
variable cc-sysv-frame-patch
variable cc-sysv-function-signature
\ A block-scope function declarator names the one external function. With
\ none visible, a scoped symbol shares the implicit records' persistent
\ signature and fixups; a visible function stays the target after checks.
: cc-sysv-block-function
  nc-static @ nc-storage @ nc-extern @ 0= and or if, [lit] 233 cc-die then,
  [char] { cc-tok-punct? if, [lit] 238 cc-die then,
  cc-sysv-declarator-signature cc-sysv-function-signature !
  cc-sysv-function-signature @ cc-sysv-sig-varargs [lit] 4 and if,
    [lit] 233 cc-die
  then,
  cc-sysv-function-signature @ cc-sysv-check-implicit-signature
  nc-name @ nc-nlen @ cc-sym-find
  dup 0< 0= if,
    dup cc-sym-kind-of sk-func = if,
      cc-sysv-symbol-signature cc-sysv-function-signature @
      cc-sysv-compatible-signatures 0= if, [lit] 237 cc-die then, exit,
    then,
  then, drop
  nc-name @ nc-nlen @ cc-sysv-implicit-record [lit] 24 + >r
  r@ @ cc-sysv-prototype? cc-sysv-function-signature @ cc-sysv-prototype? 0= and
  0= if, cc-sysv-function-signature @ r@ ! then,
  nc-name @ nc-nlen @ sk-func nc-ty @ [lit] 0 cc-sym-add
  nc-desc @ over cc-sym-set-struct-desc
  r> @ over cc-sysv-signatures cell[] !
  cc-sysv-implicit-declared-fwd ;
```

File-scope processing refines identifier-list definitions and checks prior declarations, retaining an existing prototype when a later declaration leaves parameters unspecified (`forth-bootstrap/cc/121-cc-sysv.fth:1273`):

```forth file=cc/121-cc-sysv.fth
: cc-sysv-function
  cc-target-sysv @ 0= if, cc-native-function exit, then,
  nc-top @ 0= if, cc-sysv-block-function exit, then,
  \ A function type from a typedef declares; C defines only with a suffix.
  nc-func @ true <> [char] { cc-tok-punct? and if, [lit] 238 cc-die then,
  cc-sysv-declarator-signature cc-sysv-function-signature !
  \ A definition's empty parentheses are an empty identifier list: zero
  \ parameters, which a prior prototype must also have (C90 6.5.4.3).
  [char] { cc-tok-punct? cc-sysv-function-signature @ cc-sysv-sig-varargs [lit] 2 = and if,
    [lit] 6 cc-sysv-function-signature @ [lit] 32 + !
  then,
  cc-sysv-function-signature @ cc-sysv-sig-varargs [lit] 4 and if,
    cc-sysv-function-signature @ cc-sysv-old-parameters
  then,
  cc-sysv-function-signature @ cc-sysv-check-implicit-signature
  nc-name @ nc-nlen @ cc-sym-find
  dup 0< 0= if,
    dup cc-sym-kind-of sk-func <> if, [lit] 237 cc-die then,
    dup cc-sysv-symbol-signature cc-sysv-function-signature @
    cc-sysv-compatible-signatures 0= if, [lit] 237 cc-die then,
  then,
  dup 0< if,
    drop nc-name @ nc-nlen @ sk-func nc-ty @ [lit] 0 cc-sym-add
    nc-desc @ over cc-sym-set-struct-desc
    [lit] 0 over cc-sysv-signatures cell[] !
  then,
  nc-id !
  nc-id @ cc-sysv-signatures cell[] @ dup if,
    cc-sysv-prototype? cc-sysv-function-signature @ cc-sysv-prototype? 0= and
  else, drop [lit] 0 then, 0= if,
    cc-sysv-function-signature @ nc-id @ cc-sysv-signatures cell[] !
  then,
  nc-ty @ nc-id @ cc-sym-type cell[] !
  nc-desc @ nc-id @ cc-sym-set-struct-desc
  [char] { cc-tok-punct? 0= if, exit, then,
```

A definition resolves pending addresses, creates parameter locals, saves incoming registers, and parses the body; `cc-sysv-frame-patch` delays the frame allocation size until all call-save slots are known (`forth-bootstrap/cc/121-cc-sysv.fth:1308`):

```forth file=cc/121-cc-sysv.fth
  nc-ty @ nc-desc @ cc-sysv-return-check-fwd
  nc-id @ cc-sym-val-of if, [lit] 211 cc-die then,
  cc-here-vaddr nc-id @ cc-sym-val cell[] !
  nc-id @ cc-sym-call-fixups @ cc-here-vaddr cc-walk-and-patch-to-vaddr
  [lit] 0 nc-id @ cc-sym-call-fixups !
  nc-id @ cc-sym-addr-fixups @ cc-here-vaddr cc-walk-and-patch-imm64-to-vaddr
  [lit] 0 nc-id @ cc-sym-addr-fixups !
  nc-name @ nc-nlen @ cc-is-main? if, cc-here-vaddr cc-main-vaddr ! then,
  nc-ty @ cc-native-return-type ! nc-desc @ cc-native-return-desc !
  cc-nctx @ >r cc-ncontext cc-scope-push
  [lit] 1 cc-fn-local-count ! [lit] 0 cc-label-count !
  [lit] 0 cc-sysv-stack-depth !
  [lit] 0 cc-break-stack-head ! [lit] 0 cc-continue-stack-head !
  [lit] 0 cc-switch-depth ! [lit] 0 cc-loop-switch-depth !
  cc-sysv-function-signature @ cc-sysv-params-fwd
  cc-sysv-function-signature @ cc-sysv-varargs-prepare-fwd
  [lit] 0 cc-emit-prologue
  cc-out-pos @ [lit] 4 - cc-sysv-frame-patch ! cc-sysv-save-callee
  cc-sysv-varargs-save-fwd
  cc-sysv-store-params-fwd
  begin,
    cc-next-token-keep [char] } cc-tok-punct? 0= while,
    cc-putback-token cc-parse-stmt
  repeat,
  cc-sysv-stack-depth @ if, [lit] 239 cc-die then,
  cc-emit-xor-rax-rax cc-emit-epilogue cc-native-finish-gotos
  cc-fn-local-count @ [lit] 8 * [lit] 16 cc-nalign
  cc-sysv-frame-patch @ cc-out-patch-4le
  cc-scope-pop r> cc-nctx ! ;
' cc-sysv-function is cc-native-function-fwd

```

`cc-sysv-enable` resets per-translation-unit identities and selects LP64 scalar calls; the standalone entry passes the process arguments to `main`, while object mode will omit that entry (`forth-bootstrap/cc/121-cc-sysv.fth:1339`):

```forth file=cc/121-cc-sysv.fth
: cc-sysv-enable
  [lit] 0 cc-qualified-fields ! [lit] 0 cc-ld-desc !
  [lit] 0 cc-sysv-implicit-head ! [lit] 0 cc-sysv-implicit-count !
  true cc-target-sysv ! true cc-target-lp64 ! true cc-prep-direct !
  [lit] 0 cc-bootstrap-floatbits ! ;
: cc-sysv-translation-unit
  begin,
    cc-skip-storage-quals cc-next-token-keep tok-kind @ tk-eof = 0= while,
    true cc-native-declaration
  repeat, ;
: cc-sysv-entry
  cc-native-init-entry-fwd
  [lit] 72 cc-emit-byte [lit] 139 cc-emit-byte [lit] 60 cc-emit-byte [lit] 36 cc-emit-byte
  [lit] 72 cc-emit-byte [lit] 141 cc-emit-byte [lit] 116 cc-emit-byte [lit] 36 cc-emit-byte [lit] 8 cc-emit-byte
  cc-sysv-zero-vector-count cc-emit-call-rel32-placeholder cc-call-main-patch !
  cc-emit-mov-rdi-rax [lit] 184 cc-emit-byte [lit] 60 cc-emit-4le
  [lit] 15 cc-emit-byte [lit] 5 cc-emit-byte ;
: cc-sysv-program
  cc-sysv-entry cc-sysv-translation-unit
  cc-native-init-finish-fwd cc-sysv-check-implicit-defined
  cc-check-fns-defined cc-patch-call-main ;
```

## Carry code and storage into a relocatable object

The object adapter keeps the same parser and call lowering. It omits a process entry and records unresolved targets for the linker. Relative calls already resolved within the text remain valid when caller and callee move together.

`cc-sysv-object-mode` selects the adapter, and its stable-record workspace can use either the default buffer or an explicitly mapped larger buffer (`forth-bootstrap/cc/123-cc-object-program.fth:1`):

```forth file=cc/123-cc-object-program.fth
\ 123-cc-object-program.fth — shared scalar C parser to ELF64 ET_REL.
\ Stable object records outlive parser scopes: static locals never inherit
\ an unrelated object when cc-sym IDs are reused. All relocations name these
\ records until081 assigns its own stable symbol IDs at serialization.
variable cc-sysv-object-mode
[lit] 0 cc-sysv-object-mode !
[lit] 4096 constant cc-om-default-cap
create cc-om-default-records cc-om-default-cap [lit] 128 * allot
variable cc-om-limit
variable cc-om-buffer
cc-om-default-cap cc-om-limit !
cc-om-default-records cc-om-buffer !
: cc-om-cap ( -- entries ) cc-om-limit @ ;
: cc-om-records ( -- address ) cc-om-buffer @ ;
\ Complete original insn-output.c needs 10,559 stable records; round to 10,752.
\ Keep the default table and opt in explicitly to a fixed mapped table.
[lit] 10752 constant cc-om-direct-cap
variable cc-om-direct-base
: cc-om-default-workspace ( -- )
  cc-om-default-records cc-om-buffer ! cc-om-default-cap cc-om-limit ! ;
: cc-om-direct-workspace ( -- )
  cc-om-direct-base @ 0= if,
    cc-om-direct-cap [lit] 128 * [lit] 245 cc-workspace-map
    cc-om-direct-base !
  then,
  cc-om-direct-base @ cc-om-buffer ! cc-om-direct-cap cc-om-limit ! ;
```

The source comment’s capacity measurement is historical; this checkpoint does not repeat it. The records outlive parser symbol IDs, and the accessors below expose their persistent fields.

| Record input | Field accessors |
|---|---|
| Identity and binding | `om-name`, `om-nlen`, `om-bind`, `om-kind` |
| Storage location and extent | `om-section`, `om-offset`, `om-size`, `om-align` |
| C declaration shape | `om-type`, `om-desc`, `om-array`, `om-inner` |
| Publication state | `om-flags`, `om-output`, `om-symbol` |

`cc-om-count` tracks allocated records, and `cc-om-record` checks an ID before converting it into a record address (`forth-bootstrap/cc/123-cc-object-program.fth:29`):

```forth file=cc/123-cc-object-program.fth
variable cc-om-count
\ Reject invalid IDs before subtraction or multiplication in either workspace.
: cc-om-record ( id -- address )
  dup [lit] 1 < if, [lit] 245 cc-die then,
  dup cc-om-cap [lit] 245 cc-check-cap
  1- [lit] 128 * cc-om-records + ;
: om-name cc-om-record ;
: om-nlen cc-om-record [lit] 8 + ;
: om-bind cc-om-record [lit] 16 + ;
: om-kind cc-om-record [lit] 24 + ;
: om-section cc-om-record [lit] 32 + ;
: om-offset cc-om-record [lit] 40 + ;
: om-size cc-om-record [lit] 48 + ;
: om-align cc-om-record [lit] 56 + ;
: om-type cc-om-record [lit] 64 + ;
: om-desc cc-om-record [lit] 72 + ;
: om-array cc-om-record [lit] 80 + ;
: om-inner cc-om-record [lit] 88 + ;
: om-flags cc-om-record [lit] 96 + ;
: om-output cc-om-record [lit] 104 + ;
: om-symbol cc-om-record [lit] 112 + ;
```

`cc-om-bucket` and `cc-om-hnext` index names; reset clears buckets, link prepends a record, and new-record construction zeroes state before setting binding and kind (`forth-bootstrap/cc/123-cc-object-program.fth:48`):

```forth file=cc/123-cc-object-program.fth
\ Lookup by name goes through a hash table (cc-name-hash, 030):
\ cc-om-bucket holds the newest record whose name hashes there (0 for
\ none), and cc-om-hnext the next older record in the same bucket.
create cc-om-bucket  cc-name-buckets [lit] 8 * allot
create cc-om-hnext   cc-om-direct-cap 1+ [lit] 8 * allot
: cc-om-hash-reset ( -- )
  [lit] 0 begin, dup cc-name-buckets < while,
    [lit] 0 over cc-om-bucket cell[] !  1+
  repeat, drop ;
: cc-om-link ( id -- )
  dup om-name @ over om-nlen @ cc-name-hash cc-om-bucket cell[]   ( id b )
  2dup @ swap cc-om-hnext cell[] !
  ! ;
\ Flags:1 extern-only,2 tentative,4 initialized,8 block static,
\ 16 referenced,32 anonymous. A later definition replaces extern-only.
: cc-om-flag ( flag record -- ) om-flags dup @ rot or swap ! ;
: cc-om-new ( name length binding kind -- record )
  cc-om-count @ 1+ cc-om-cap [lit] 245 cc-check-cap
  [lit] 1 cc-om-count +! cc-om-count @ >r
  r@ cc-om-record [lit] 128 cc-nzero
  r@ om-kind ! r@ om-bind ! r@ om-nlen ! r@ om-name !
  r@ cc-om-link
  [lit] 1 r@ om-align ! r> ;
```

Lookup uses `cc-om-find-name` and `cc-om-find-length` as scratch state and selects the oldest ordinary external identity, excluding block statics and anonymous records (`forth-bootstrap/cc/123-cc-object-program.fth:71`):

```forth file=cc/123-cc-object-program.fth
variable cc-om-find-name
variable cc-om-find-length
\ The oldest record of that name that is neither a block static nor
\ anonymous: the walk along the name's bucket runs newest first, so the
\ last match it meets is the one.
: cc-om-find ( name length -- record|0 )
  cc-om-find-length ! cc-om-find-name !
  [lit] 0                                                ( found )
  cc-om-find-name @ cc-om-find-length @ cc-name-hash cc-om-bucket cell[] @
  begin, dup while,                                      ( found id )
    dup om-flags @ [lit] 40 and 0= if,
      dup om-nlen @ cc-om-find-length @ = if,
        dup om-name @ cc-om-find-name @ cc-om-find-length @ bytes-eq if,
          nip dup
        then,
      then,
    then, cc-om-hnext cell[] @
  repeat, drop ;
: cc-om-from-symbol ( symbol -- record )
  dup cc-sym-kind-of sk-global = if, cc-sym-val-of exit, then,
  dup cc-sym-name-addr cell[] @ swap cc-sym-name-len cell[] @ cc-om-find
  dup 0= if, [lit] 238 cc-die then, ;

```

## Turn references into relocation requests


`om-implicit` preserves the external declaration record, while `cc-om-reloc` queues a relocation against an object record; address emission reserves an absolute field without guessing its final address (`forth-bootstrap/cc/123-cc-object-program.fth:94`):

```forth file=cc/123-cc-object-program.fth
\ The unused final record cell retains an implicit declaration's stable
\ identity even after its block-scoped parser symbol has disappeared.
: om-implicit cc-om-record [lit] 120 + ;
: cc-sysv-object-implicit ( id -- )
  cc-sysv-object-mode @ 0= if, drop exit, then,
  dup cc-sym-name-addr cell[] @ over cc-sym-name-len cell[] @ cc-om-find
  dup 0= if,
    drop dup cc-sym-name-addr cell[] @ over cc-sym-name-len cell[] @
    cc-obj-global cc-obj-func cc-om-new
  then,
  dup om-kind @ cc-obj-func <> if, [lit] 237 cc-die then,
  swap cc-sysv-implicit-symbol swap om-implicit ! ;
' cc-sysv-object-implicit is cc-sysv-implicit-declared-fwd

variable cc-om-relocations
: cc-om-reloc ( section offset kind record addend -- )
  [lit] 48 cc-alloc >r
  r@ [lit] 40 + ! dup [lit] 16 swap cc-om-flag
  r@ [lit] 32 + ! r@ [lit] 24 + ! r@ [lit] 16 + ! r@ [lit] 8 + !
  cc-om-relocations @ r@ ! r> cc-om-relocations ! ;
: cc-om-reference ( record -- )
  >r cc-obj-text cc-out-pos @ [lit] 2 + cc-obj-r64 r> [lit] 0 cc-om-reloc
  [lit] 0 cc-emit-movabs-rdi-imm64 ;
: cc-sysv-object-function-desc
  cc-sysv-object-mode @ cc-expr-unevaluated @ 0= and if,
    dup cc-om-from-symbol >r
    cc-obj-text cc-out-pos @ [lit] 2 + cc-obj-r64 r> [lit] 0 cc-om-reloc
  then, cc-sysv-function-desc ;
' cc-sysv-object-function-desc is cc-native-function-desc-fwd

```

`cc-om-string-piece` decodes bytes into read-only storage, `cc-om-string` creates an anonymous `.Lstring` record, and the expression hook emits a reference to it (`forth-bootstrap/cc/123-cc-object-program.fth:124`):

```forth file=cc/123-cc-object-program.fth
create cc-om-string-name s, .Lstring
: cc-om-string-piece ( address length -- )
  begin, dup while,
    over c@ backslash = over [lit] 1 > and if,
      over 1+ cc-decode-escape swap cc-obj-byte 1+
      >r swap r@ + swap r> -
    else,
      over c@ cc-obj-byte swap 1+ swap 1-
    then,
  repeat, 2drop ;
: cc-om-string ( -- record )
  cc-obj-current @ >r cc-obj-rodata cc-obj-use
  cc-om-string-name [lit] 8 cc-obj-local cc-obj-object cc-om-new
  [lit] 32 over om-flags ! cc-obj-rodata over om-section !
  cc-obj-here over om-offset !
  begin, tok-kind @ tk-str = while,
    tok-str-addr @ tok-str-len @ cc-om-string-piece cc-next-token-keep
  repeat,
  [lit] 0 cc-obj-byte
  cc-obj-here over om-offset @ - over om-size !
  r> cc-obj-use ;
: cc-sysv-object-string
  cc-sysv-object-mode @ cc-expr-unevaluated @ 0= and if,
    cc-om-string dup om-size @ cc-last-expr-array-len !
    cc-putback-token cc-om-reference
  else, cc-parse-native-string-literal then, ;
' cc-sysv-object-string is cc-native-string-fwd
```

The function adapter wraps ordinary lowering and measures the emitted text span, recording a local binding for a static function and leaving a mere declaration undefined (`forth-bootstrap/cc/123-cc-object-program.fth:151`):

```forth file=cc/123-cc-object-program.fth

: cc-sysv-object-function
  cc-sysv-object-mode @ 0= nc-top @ 0= or if, cc-sysv-function exit, then,
  nc-name @ nc-nlen @ cc-om-find
  dup 0= if,
    drop nc-name @ nc-nlen @ cc-obj-global cc-obj-func cc-om-new
  else,
    dup om-kind @ cc-obj-func <> if, [lit] 237 cc-die then,
  then,
  nc-static @ if, cc-obj-local over om-bind ! then,
  >r cc-out-pos @ >r cc-sysv-function
  nc-id @ r> r> rot over om-symbol !
  >r cc-out-pos @ over - dup if,
    r@ om-size ! r@ om-offset ! cc-obj-text r@ om-section !
  else, 2drop then, r> drop ;
' cc-sysv-object-function is cc-native-function-fwd
```

## Complete storage declarations before export

Repeated object declarations must agree on type and array shape; size updates complete tentative arrays, and parser symbols are installed with the stable record as their value (`forth-bootstrap/cc/123-cc-object-program.fth:167`):

```forth file=cc/123-cc-object-program.fth

: cc-om-compatible-object ( record -- )
  dup om-kind @ cc-obj-object <> if, [lit] 237 cc-die then,
  dup om-type @ over om-desc @ nc-ty @ nc-desc @
  cc-sysv-same-types 0= if, [lit] 237 cc-die then,
  dup om-array @ 0= nc-array @ 0= <> if, [lit] 237 cc-die then,
  dup om-array @ [lit] 0 > nc-array @ [lit] 0 > and if,
    dup om-array @ nc-array @ <> if, [lit] 237 cc-die then,
  then,
  dup om-inner @ nc-inner @ <> if, [lit] 237 cc-die then, drop ;
: cc-om-size-from-declaration ( record -- )
  nc-ty @ over om-type ! nc-desc @ over om-desc !
  nc-array @ [lit] 0 < over om-array @ [lit] 0 > and if,
    dup om-array @ nc-array !
  then,
  nc-array @ over om-array ! nc-inner @ over om-inner !
  cc-sysv-object-size over om-size !
  nc-ty @ nc-desc @ cc-nalignment swap om-align ! ;
: cc-om-install-object ( record -- )
  dup nc-slot !
  nc-top @ if, nc-name @ nc-nlen @ cc-sym-find else, true then,
  dup 0< if,
    drop sk-global over cc-ninstall-symbol
  else,
    dup cc-sym-kind-of sk-global <> if, [lit] 237 cc-die then,
    nc-qualified @ over cc-sym-qualified cell[] !
    nc-ty @ over cc-sym-type cell[] !
    nc-desc @ over cc-sym-set-struct-desc
    nc-array @ over cc-sym-set-array-len nc-inner @ over cc-sym-set-array-inner
    over over cc-sym-val cell[] !
  then,
  dup nc-id ! cc-sysv-object-size swap cc-sym-set-object-size drop ;
```

A block static gets its own record even when names repeat; initialized storage reserves aligned data bytes, while extern-only and tentative declarations retain distinct flags (`forth-bootstrap/cc/123-cc-object-program.fth:199`):

```forth file=cc/123-cc-object-program.fth
: cc-om-initializer
  true cc-ni-static ! cc-next-token-keep
  nc-ty @ nc-desc @ nc-array @ nc-inner @ [lit] 0 [lit] 0 cc-ni-value ;
: cc-sysv-object-declaration
  cc-sysv-object-mode @ 0= if, cc-nobject exit, then,
  nc-top @ 0= nc-extern @ 0= and nc-array @ [lit] 0 < and
  [char] = cc-tok-punct? 0= and if, [lit] 238 cc-die then,
  nc-top @ nc-static @ or nc-extern @ or 0= if, cc-nobject exit, then,
  [char] = cc-tok-punct? if, cc-native-init-prepare-fwd then,
  nc-top @ 0= nc-static @ and if, [lit] 0
  else, nc-name @ nc-nlen @ cc-om-find then,
  dup if, dup cc-om-compatible-object else,
    drop nc-name @ nc-nlen @ cc-obj-global cc-obj-object cc-om-new
    nc-top @ 0= nc-static @ and if, [lit] 8 over cc-om-flag then,
  then,
  nc-static @ if, cc-obj-local over om-bind ! then,
  dup cc-om-size-from-declaration dup cc-om-install-object
  [char] = cc-tok-punct? if,
    dup om-flags @ [lit] 4 and if, [lit] 237 cc-die then,
    cc-obj-current @ >r cc-obj-data cc-obj-use
    dup om-align @ cc-obj-align dup om-size @ cc-obj-reserve over om-offset !
    cc-obj-data over om-section ! [lit] 4 over cc-om-flag
    r> cc-obj-use drop cc-om-initializer
  else,
    nc-extern @ if, [lit] 1 else, [lit] 2 then, swap cc-om-flag
  then, ;
' cc-sysv-object-declaration is cc-nobject-fwd

```

Static scalar leaves either patch absolute bytes or queue a symbolic pointer relocation; `cc-om-value-fwd` keeps a conversion seam for Chapter 45’s typed constant evaluator (`forth-bootstrap/cc/123-cc-object-program.fth:227`):

```forth file=cc/123-cc-object-program.fth
\ Reuse118's recursive aggregate/array traversal; only static leaves differ.
\ A floating leaf is converted at compile time (125); others keep their bits.
: cc-om-value-default ( value source destination -- value ) 2drop ;
defer cc-om-value-fwd
' cc-om-value-default is cc-om-value-fwd
: cc-om-scalar-initializer
  cc-sysv-object-mode @ cc-ni-static @ and 0= if, cc-ni-scalar exit, then,
  cc-ni-aggregate? if, [lit] 219 cc-die then,
  ni-type @ cc-sysv-check-scalar
  cc-putback-token cc-parse-static-const-fwd
  dup 0= [lit] 4 cc-npick 0= and cc-last-expr-null !
  >r 2dup ni-type @ ni-desc @ cc-value-shape-fwd r>
  dup if,
    ni-type @ ty-size [lit] 8 <> if, [lit] 238 cc-die then,
    ni-type @ dup ty-ptr 0= swap ty-base ty-double = and if, [lit] 232 cc-die then,
    >r 2drop
    cc-obj-data nc-slot @ om-offset @ ni-offset @ + cc-obj-r64 r> [lit] 4 cc-npick cc-om-reloc
    drop
  else,
    drop drop ni-type @ cc-om-value-fwd
    cc-obj-data nc-slot @ om-offset @ ni-offset @ +
    ni-type @ ty-size cc-obj-patch
  then,
  cc-next-token-keep ;
' cc-om-scalar-initializer is cc-ni-scalar-fwd
```

A string initializer copies decoded bytes into the destination array, using object-data patches for static storage and emitted copies for automatic storage (`forth-bootstrap/cc/123-cc-object-program.fth:252`):

```forth file=cc/123-cc-object-program.fth
: cc-om-string-initializer
  cc-sysv-object-mode @ 0= if, cc-ni-string exit, then,
  cc-om-string
  dup om-size @ 1- ni-array @ > if, [lit] 223 cc-die then,
  dup om-size @ ni-array @ cc-nmax drop
  dup om-size @ ni-array @ > if, ni-array @ else, dup om-size @ then,
  cc-ni-static @ if,
    [lit] 0 begin, 2dup > while,
      [lit] 2 cc-npick om-offset @ over + cc-obj-rodata cc-obj-base + c@
      cc-obj-data nc-slot @ om-offset @ ni-offset @ + [lit] 3 cc-npick +
      [lit] 1 cc-obj-patch 1+
    repeat, 2drop drop
  else,
    swap cc-om-reference cc-ni-mov-rsi-rdi
    ni-offset @ cc-ni-address cc-ni-copy-bytes
  then, ;
' cc-om-string-initializer is cc-ni-string-fwd
```

The recursive initializer traversal is reused unchanged. At this layer the static-expression hook still rejects every static scalar expression; Chapter 45 installs its evaluator. The checkpoint therefore assigns its local value in executable code.

## Represent an address without loading it

Function, array, and string constants carry a record plus an addend; `cc-om-const-ident` retains row shape, while a skipped string expression consumes tokens without allocating storage (`forth-bootstrap/cc/123-cc-object-program.fth:272`):

```forth file=cc/123-cc-object-program.fth

\ Symbolic constant leaves feed125's typed expression grammar. Record IDs
\ are never addresses; arithmetic only changes an explicit RELA addend.
: cc-om-const-ident
  cc-sysv-object-mode @ 0= if, cc-const-unsupported then,
  tok-str-addr @ tok-str-len @ cc-sym-find
  dup 0< if, cc-const-unsupported then,
  dup cc-sym-kind-of sk-func = if,
    dup cc-sysv-symbol-signature >r cc-om-from-symbol >r
    [lit] 0 ty-func [lit] 1 ty-make r> r> swap exit,
  then,
  dup cc-sym-kind-of sk-global <> if, cc-const-unsupported then,
  dup cc-sym-array-len-of 0= if, cc-const-unsupported then,
  dup cc-om-from-symbol >r
  dup cc-sym-array-inner-of if,
    dup cc-sym-type-of over cc-expr-symbol-desc
    [lit] 2 cc-npick cc-sym-array-inner-of [lit] 0
    [lit] 4 cc-npick cc-sym-qualified cell[] @ cc-sysv-qualified-node
    nip ty-array [lit] 1 ty-make swap
  else,
    dup cc-sym-type-of 1+ swap
    dup cc-sym-qualified cell[] @ >r cc-expr-symbol-desc
    over ty-base ty-array = if, r@ cc-sysv-qualify-node then, r> drop
  then, [lit] 0 rot rot r> ;
: cc-om-const-string
  cc-sysv-object-mode @ 0= if, cc-const-unsupported then,
  cc-cx-skip @ if,
    begin, cc-next-token-keep tok-kind @ tk-str <> until,
    [lit] 0
  else, cc-om-string then,
  >r cc-putback-token [lit] 0 ty-char [lit] 1 ty-make [lit] 0 r> ;
```

| Address-frame input | Field accessors |
|---|---|
| Symbolic address | `oa-value` for the addend; `oa-record` for identity |
| Type shape | `oa-type`, `oa-desc`, `oa-array`, `oa-inner` |
| Expression category | `oa-lvalue`, `oa-qualified` |

`cc-om-address-frame` parks the current operand, and `cc-const-qualified` transfers qualification into it; cast, unary, and index hooks reject until a constant-expression layer supplies them (`forth-bootstrap/cc/123-cc-object-program.fth:300`):

```forth file=cc/123-cc-object-program.fth
\ An address operand carries an lvalue category separately from its type.
\ Parentheses preserve it; casts produce values. Arrow and subscripting may
\ consume a constant pointer value, but must never load a pointer object.
variable cc-const-qualified
variable cc-om-address-frame
: oa-value cc-om-address-frame @ ;
: oa-type cc-om-address-frame @ [lit] 8 + ;
: oa-desc cc-om-address-frame @ [lit] 16 + ;
: oa-record cc-om-address-frame @ [lit] 24 + ;
: oa-array cc-om-address-frame @ [lit] 32 + ;
: oa-inner cc-om-address-frame @ [lit] 40 + ;
: oa-lvalue cc-om-address-frame @ [lit] 48 + ;
: oa-qualified cc-om-address-frame @ [lit] 56 + ;
defer cc-om-address-cast-fwd
defer cc-om-address-unary-fwd
defer cc-om-address-index-fwd
' cc-const-unsupported is cc-om-address-cast-fwd
' cc-const-unsupported is cc-om-address-unary-fwd
' cc-const-unsupported is cc-om-address-index-fwd
: cc-om-address-value ( value type descriptor symbol -- )
  oa-record ! oa-desc ! oa-type ! oa-value !
  [lit] 0 oa-array ! [lit] 0 oa-inner ! [lit] 0 oa-lvalue !
  cc-const-qualified @ oa-qualified ! ;
```

An identifier becomes an addressable operand; array descent unwraps its element descriptor, while dereference accepts a constant pointer value but refuses to load a pointer object (`forth-bootstrap/cc/123-cc-object-program.fth:323`):

```forth file=cc/123-cc-object-program.fth
: cc-om-address-ident
  tok-str-addr @ tok-str-len @ cc-sym-find
  dup 0< if, cc-const-unsupported then,
  dup cc-sym-qualified cell[] @ oa-qualified !
  dup cc-sym-kind-of sk-func = if,
    dup cc-sysv-symbol-signature oa-desc ! cc-om-from-symbol oa-record !
    ty-func [lit] 0 ty-make oa-type !
  else,
    dup cc-sym-kind-of sk-global <> if, cc-const-unsupported then,
    dup cc-om-from-symbol oa-record ! dup cc-sym-type-of oa-type !
    dup cc-expr-symbol-desc oa-desc !
    dup cc-sym-array-len-of oa-array ! cc-sym-array-inner-of oa-inner !
  then,
  true oa-lvalue ! ;
: cc-om-address-array
  oa-array @ 0= oa-type @ ty-base ty-array = and
  oa-type @ ty-ptr 0= and if,
    oa-desc @ dup cc-ad-type oa-type !
    dup cc-ad-count oa-array ! dup cc-ad-inner oa-inner !
    cc-ad-desc oa-desc !
  then, ;
: cc-om-address-deref
  oa-lvalue @ oa-type @ ty-ptr 0= or if, cc-const-unsupported then,
  oa-type @ 1- oa-type ! true oa-lvalue !
  oa-type @ ty-base ty-array = oa-type @ ty-ptr 0= and if,
    oa-desc @ dup cc-ad-type oa-type !
    dup cc-ad-count oa-array ! dup cc-ad-inner oa-inner !
    cc-ad-desc oa-desc ! exit,
  then,
  oa-type @ ty-ptr 0= oa-type @ ty-base ty-void = and if,
    cc-const-unsupported
  then, ;
```

## Compose symbolic address selections

Member selection adds a field offset and qualification; indexing scales an evaluated constant index by the element extent, preserving symbolic identity (`forth-bootstrap/cc/123-cc-object-program.fth:355`):

```forth file=cc/123-cc-object-program.fth
: cc-om-address-member
  oa-lvalue @ 0= oa-array @ or oa-type @ ty-ptr or if,
    cc-const-unsupported
  then,
  oa-type @ ty-base ty-struct <> oa-desc @ 0= or if,
    cc-const-unsupported
  then,
  cc-expect-ident
  tok-str-addr @ tok-str-len @ oa-desc @ cc-find-field oa-value +!
  cc-ff-result-record @ cc-field-qualified oa-qualified @ or oa-qualified !
  cc-ff-result-record @ cc-field-use-fwd
  cc-ff-result-type @ oa-type ! cc-ff-result-desc @ oa-desc !
  cc-ff-result-array @ oa-array !
  cc-ff-result-record @ cc-sf-array-inner oa-inner ! ;
: cc-om-address-index
  oa-array @ if,
    cc-om-address-index-fwd
    dup 0< over oa-array @ > or if, cc-const-unsupported then,
    oa-type @ oa-desc @ cc-nsize
    oa-inner @ if, oa-inner @ * then, * oa-value +!
    oa-inner @ oa-array ! [lit] 0 oa-inner ! cc-om-address-array
  else,
    oa-type @ oa-desc @ cc-expr-pointee-size >r
    cc-om-address-deref
    oa-type @ ty-ptr 0= oa-type @ ty-base ty-func = and if,
      cc-const-unsupported
    then,
    cc-om-address-index-fwd r> * oa-value +!
  then,
  [char] ] cc-expect-punct-c ;
```

The address-operand parser distinguishes identifiers, parenthesized lvalues, casts, and unary dereference; casts replace the operand category with a value (`forth-bootstrap/cc/123-cc-object-program.fth:385`):

```forth file=cc/123-cc-object-program.fth
: cc-om-address-operand
  cc-next-token-keep
  tok-kind @ tk-ident = if,
    cc-om-address-ident
  else,
    lparen cc-tok-punct? if,
      cc-next-token-keep
      cc-type-start? if,
        cc-parse-type-name
        cc-type-name-array @ if, cc-const-unsupported then,
        cc-type-name-qualified @ >r
        cc-cast-desc @ >r >r [char] ) cc-expect-punct-c
        r> r> cc-om-address-cast-fwd cc-om-address-value
        r> oa-qualified ! exit,
      then,
      cc-putback-token cc-om-address-operand [char] ) cc-expect-punct-c
    else,
      [char] * cc-tok-punct? if,
        cc-om-address-unary-fwd cc-om-address-value cc-om-address-deref exit,
      then,
      cc-const-unsupported
    then,
  then,
```

Postfix selection composes those operations, and `cc-om-const-address` returns the resulting addend, pointer type, descriptor, and record before restoring the outer address frame (`forth-bootstrap/cc/123-cc-object-program.fth:422`):

```forth file=cc/123-cc-object-program.fth
  begin,
    cc-next-token-keep
    [char] [ cc-tok-punct? if,
      cc-om-address-index
    else,
      [char] . cc-tok-punct? if,
        cc-om-address-member
      else,
        pt-arrow cc-tok-punct? if,
          cc-om-address-deref cc-om-address-member
        else, cc-putback-token exit, then,
      then,
    then,
  again, ;
: cc-om-const-address
  cc-sysv-object-mode @ 0= if, cc-const-unsupported then,
  cc-om-address-frame @ >r
  [lit] 64 cc-alloc dup cc-om-address-frame ! [lit] 64 cc-nzero
  cc-om-address-operand
  oa-lvalue @ 0= if, cc-const-unsupported then,
  oa-value @
  oa-array @ if,
    oa-type @ oa-desc @ oa-array @ oa-inner @ oa-qualified @
    cc-sysv-qualified-node
    ty-array [lit] 1 ty-make swap
  else, oa-type @ 1+ oa-desc @ then,
  oa-record @
  r> cc-om-address-frame ! ;
' cc-om-const-ident is cc-const-ident-fwd
' cc-om-const-address is cc-const-address-fwd
' cc-om-const-string is cc-const-string-fwd
```

## Finish the translation unit

Return to `caller.o`. Its call already knows how to pass eight values and
receive one `long`, but `add` still has no definition in this translation
unit. `cc-om-function-calls` turns its pending call field into a
`cc-obj-plt32` relocation with addend −4. Export gives `add` an undefined
function symbol; the relocation names that symbol through the writer's
stable handle. In `add.o`, the separately compiled definition supplies a
symbol located in its text section.

The two objects thus agree on value transport before either has a final
load address. Linking selects `add`'s definition, places its text, and
fills the caller's displacement field. Chapter 42 derives that last
calculation; this chapter's checkpoint delegates it to the host linker.
The signature, staging cells, and relocation have different jobs: C type
agreement, temporary value storage, and an unfinished control-flow target.

Tentative objects receive BSS storage before export; `cc-om-export-needed?` retains defined or referenced records, and unresolved function calls become PLT-relative relocations with the call-field adjustment (`forth-bootstrap/cc/123-cc-object-program.fth:452`):

```forth file=cc/123-cc-object-program.fth

: cc-om-finalize-storage ( record -- )
  dup om-kind @ cc-obj-object = over om-section @ 0= and if,
    dup om-flags @ [lit] 2 and if,
      cc-obj-bss cc-obj-use dup om-align @ cc-obj-align
      dup om-size @ cc-obj-reserve over om-offset ! cc-obj-bss over om-section !
    then,
  then, drop ;
: cc-om-export ( record -- )
  dup >r om-name @ r@ om-nlen @ r@ om-bind @ r@ om-kind @ cc-obj-default
  r@ om-section @ r@ om-offset @
  r@ om-section @ if, r@ om-size @ else, [lit] 0 then,
  cc-obj-symbol r> om-output ! ;
: cc-om-export-needed? ( record -- flag )
  dup om-section @ swap om-flags @ [lit] 16 and or ;
: cc-om-function-calls ( record -- )
  dup om-kind @ cc-obj-func <> if, drop exit, then,
  dup om-implicit @ dup if, [lit] 32 + @
  else, drop dup om-symbol @ cc-sym-call-fixups @ then,
  begin, dup while,
    cc-obj-text over @ cc-obj-plt32 [lit] 4 cc-npick [lit] 0 [lit] 4 - cc-om-reloc
    [lit] 8 + @
  repeat, 2drop ;
```

`cc-sysv-object-enable` clears adapter state; `cc-sysv-object-program` collects text, storage, calls, and global references, then translates record identities to writer symbol handles (`forth-bootstrap/cc/123-cc-object-program.fth:462`):

```forth file=cc/123-cc-object-program.fth
: cc-sysv-object-enable
  cc-sysv-enable true cc-sysv-object-mode !
  [lit] 0 cc-om-count ! [lit] 0 cc-om-relocations ! cc-om-hash-reset ;
: cc-sysv-object-program
  cc-obj-init cc-sysv-translation-unit
  cc-ni-head @ if, [lit] 238 cc-die then,
  cc-obj-text cc-obj-use cc-out-buf cc-out-pos @ cc-obj-bytes
  [lit] 1 begin, dup cc-om-count @ <= while,
    dup cc-om-finalize-storage dup cc-om-function-calls 1+
  repeat, drop
  [lit] 0 begin, dup cc-gfixup-count @ < while,
    cc-obj-text over cc-gfixup-out-pos cell[] @ cc-obj-r64
    [lit] 3 cc-npick cc-gfixup-slot cell[] @ [lit] 0 cc-om-reloc 1+
  repeat, drop
  [lit] 1 begin, dup cc-om-count @ <= while,
    dup cc-om-export-needed? if, dup cc-om-export then, 1+
  repeat, drop
  cc-om-relocations @ begin, dup while,
    dup [lit] 8 + @ over [lit] 16 + @ [lit] 2 cc-npick [lit] 24 + @
    [lit] 3 cc-npick [lit] 32 + @ om-output @ [lit] 4 cc-npick [lit] 40 + @
    cc-obj-reloc @
  repeat, drop ;
```

Absolute address fields make this a static executable path rather than position-independent code generation. Chapter 42 supplies the Forth linker that resolves these objects; this chapter’s checkpoint uses the host linker.

## Try it

Run from the `forth-bootstrap` checkout root with the seed already built. This block loads the Forth library, the compiler layers before `cc/120-cc-main.fth`, and this chapter’s target and adapter. Each seed process compiles one C unit. All generated files live in a `mktemp -d` directory. `gcc` is used only as a linker, adding host startup and library support; it compiles neither C file.

```sh
(
set -o pipefail
work=$(mktemp -d /tmp/book-probe.XXXXXXXXXX) || exit "$?"
trap 'status=$?; rm -rf -- "$work" || status=1; exit "$status"' EXIT
cat > "$work/add.c" <<'C' || exit "$?"
long add(long *base, long a, long b, long c, long d,
         long e, long f, long g) {
    return *base + a + b + c + d + e + f + g;
}
C
cat > "$work/caller.c" <<'C' || exit "$?"
extern long add(long *, long, long, long, long, long, long, long);
int main(void) {
    long base;
    base = 14;
    return add(&base, 1, 2, 3, 4, 5, 6, 7);
}
C
for unit in add caller; do
  {
    cat forth/010-lib.fth cc/0[2-9]*-cc-*.fth cc/1[01]*-cc-*.fth \
        cc/121-cc-sysv.fth cc/123-cc-object-program.fth || exit "$?"
    printf 'create output-path s, %s/%s.o [lit] 0 c,\n' "$work" "$unit"
    cat <<'FORTH' || exit "$?"
cc-sysv-object-enable
: object-main
  cc-load-stdin cc-preprocess cc-out-init cc-globals-init
  cc-sysv-object-program output-path cc-obj-write bye ;
object-main
FORTH
    cat "$work/$unit.c" || exit "$?"
  } | ./seed-forth || exit "$?"
done
gcc -no-pie -Wl,-z,noexecstack "$work/caller.o" "$work/add.o" -o "$work/call" || exit "$?"
result=0
"$work/call" || result=$?
printf 'separate call returned %s\n' "$result"
test "$result" -eq 42
)
```

Observed output:

```text
separate call returned 42
```

The pointer and the first integer arguments travel in registers; `f` and `g` travel on the stack. The callee dereferences the pointer, adds the arguments, and returns the result through `rax`. The shell prints the program’s exit status.

## Exercise

Hints and feedback are in [Appendix H](66-exercise-feedback.md#chapter-41-stack-arguments-and-nested-lifetimes).

**Trace (easy).** Follow `f` and `g` from `cc-sysv-parse-args` through `cc-sysv-prepare-call` into `cc-sysv-store-params-default`. Draw the caller’s outgoing block and the callee’s frame, including the return address and saved `rbp`. Explain why alignment padding cannot move either argument’s expected location.

**Verify (moderate).** Replace only the checkpoint call's final argument
with another `add(&base, 1, 2, 3, 4, 5, 6, 7)` call. Predict the exit status
and update the final `test "$result"` assertion before running it. Identify
which outer staged values must survive the inner call and where the
emitted code preserves them.
