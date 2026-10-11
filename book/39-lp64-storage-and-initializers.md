# Chapter 39 — LP64 storage and initializers

An eight-byte working slot tells us how the evaluator carries a value.
It does not tell us how to locate or store a field of
`struct Item { char tag; long value; }`. The `tag` object needs one byte;
`value` needs eight-byte alignment. How should the initializer `{3, 7}`
reach those two destinations without treating storage as a row of working
values?

The native layer answers with LP64 sizes, aligned field offsets, and a
recursive initializer. A descriptor says where each value belongs in the
object; the initializer walks that layout and emits the appropriate stores.

## Native declarations and aligned storage

A declaration context collects the base and declarator; a descriptor supplies size and alignment for allocation and initialization. The program layer provides a place to run static initialization before `main`; its private runtime provides the final Linux boundary. These are separate responsibilities, so LP64 layout does not imply a particular calling convention.

This target's LP64 layout gives `char`, `short`, and `int` storage widths of one, two, and four bytes, while `long` and pointers occupy eight. An expression register can hold a wider value than the object from which it came. Layout therefore uses object size and alignment, not stack-cell width.

Chapter 41 supplies the System V AMD64 calling convention, and Chapter 43 supplies the later runtime.

Keep that `Item` beside the walkthrough; it is the checkpoint's record.
Its layout answers where a store must land: `tag` starts at
offset 0, seven padding bytes precede `value` at offset 8, and the record
occupies 16 bytes. Its initializer `{3, 7}` answers what to store at those
two destinations. The padding contributes to the size but consumes no
initializer value. This layout follows by hand from the field-placement
rules below.

There is also a timing decision. For the native executable path used in
this chapter, file-scope initialization becomes callable generated code
queued to run before `main`. An automatic local's initialization stays
inline where the declaration executes. In both cases the Forth compiler
is emitting the stores; the resulting C program executes them later.
The object-output path introduced in the following chapters has its own
static-data construction and must not be inferred from this queue.

On a first pass, follow [field placement](#place-fields-at-aligned-offsets),
[object allocation](#allocate-an-object-and-keep-its-references-valid), and
[the initializer's destination](#walk-children-without-losing-the-destination)
through that example. Return to the declarator
context machinery when you need to explain how a nested type preserves
its enclosing declaration. The checkpoint checks the initialized contents
and size sum when `main` runs; the queue trace explains how the static
objects received their values before that point.

The declaration walker needs deep stack access, maximum selection, and record copying without tying those operations to a particular C type (`forth-bootstrap/cc/115-cc-native.fth:1`):

```forth file=cc/115-cc-native.fth
\ 115-cc-native.fth — opt-in LP64 bootstrap declaration parser.
\ The legacy M2-compatible parser remains the default. Native mode uses
\ LP64 object layout and a private, all-stack call ABI within its image.
\ That ABI is private: it binds only code compiled together into one image.

: cc-npick ( x_n ... x_0 n -- x_n ... x_0 x_n )
  dup 0= if, drop dup exit, then,
  1- swap >r cc-npick r> swap ;
: cc-nminus-rot rot rot ;
: cc-nmax 2dup < if, swap then, drop ;
: cc-ncopy ( src dst n -- )
  begin, dup while,
    1- >r over r@ + c@ over r@ + c! r>
  repeat, drop 2drop ;
```

## Keep each declaration in its own context

Consider an outer record with a `long` followed by an inner record. The
outer parser has already accumulated eight bytes when it starts reading
the inner members. The inner parser needs its own running size, current
name, base type and array bounds. Reusing the outer cells would make the
inner fields look like additional outer fields and lose the unfinished
outer declaration.

`cc-nctx` makes that suspended state explicit: save its pointer, select a
fresh context for the nested declaration, then restore the pointer before
placing the completed inner object. The descriptor is the durable result;
the context is the workspace used to obtain it. Their lifetimes differ.
The address map groups that workspace so switching contexts restores all
of the enclosing facts together (`forth-bootstrap/cc/115-cc-native.fth:15`):

```forth file=cc/115-cc-native.fth

variable cc-nctx
[lit] 240 constant cc-nctx-bytes
: nc-ty     cc-nctx @ ;
: nc-desc   cc-nctx @ [lit] 8 + ;
: nc-name   cc-nctx @ [lit] 16 + ;
: nc-nlen   cc-nctx @ [lit] 24 + ;
: nc-array  cc-nctx @ [lit] 32 + ;
: nc-inner  cc-nctx @ [lit] 40 + ;
: nc-func   cc-nctx @ [lit] 48 + ;
: nc-params cc-nctx @ [lit] 56 + ;
: nc-td     cc-nctx @ [lit] 120 + ;
: nc-static cc-nctx @ [lit] 128 + ;
: nc-top    cc-nctx @ [lit] 136 + ;
: nc-base   cc-nctx @ [lit] 144 + ;
: nc-sdesc  cc-nctx @ [lit] 152 + ;
: nc-id     cc-nctx @ [lit] 160 + ;
: nc-slot   cc-nctx @ [lit] 168 + ;
: nc-extern cc-nctx @ [lit] 176 + ;
: nc-bound-mask cc-nctx @ [lit] 184 + ;
: nc-base-array cc-nctx @ [lit] 192 + ;
: nc-base-inner cc-nctx @ [lit] 200 + ;
: nc-qualified cc-nctx @ [lit] 208 + ;
: nc-base-qualified cc-nctx @ [lit] 216 + ;
: nc-prefix-qualified cc-nctx @ [lit] 224 + ;
: nc-storage cc-nctx @ [lit] 232 + ;
```

Qualifier notes accumulate in the selected context, and a fresh context starts cleared through `cc-nzero` (`forth-bootstrap/cc/115-cc-native.fth:41`):

```forth file=cc/115-cc-native.fth
: cc-native-qual-note
  cc-nctx @ if, cc-qualifier-bit nc-qualified @ or nc-qualified ! then, ;
' cc-native-qual-note is cc-qual-note
\ cc-nzero ( a n -- )  Zero n bytes at a: rep stosb (code:, 020).
code: cc-nzero
  [lit] 72 c, [lit] 137 c, [lit] 249 c,                     \ mov rcx, rdi
  [lit] 72 c, [lit] 139 c, [lit] 125 c, [lit] 0 c,          \ mov rdi, [rbp]
  [lit] 49 c, [lit] 192 c,  [lit] 243 c, [lit] 170 c,       \ xor eax,eax  rep stosb
  [lit] 72 c, [lit] 139 c, [lit] 125 c, [lit] 8 c,          \ mov rdi, [rbp+8]
  [lit] 72 c, [lit] 131 c, [lit] 197 c, [lit] 16 c,  ret,   \ add rbp, 16
: cc-ncontext
  cc-nctx-bytes cc-alloc dup cc-nctx ! cc-nctx-bytes cc-nzero ;
: cc-nalign ( n alignment -- n' )
  dup [lit] 0 <= if, drop [lit] 1 then,
```

Object layout distinguishes an array or record descriptor from a scalar type before choosing size and alignment (`forth-bootstrap/cc/115-cc-native.fth:55`):

```forth file=cc/115-cc-native.fth
  dup >r 1- + r@ / r> * ;
: cc-nsize ( ty desc -- n )
  over ty-base ty-array = over [lit] 0 <> and if,
    over ty-ptr 0= if, nip cc-ad-size exit, then,
  then,
  over ty-base ty-struct = [lit] 2 cc-npick ty-ptr 0= and if,
    dup 0= if, [lit] 210 cc-die then, nip cc-sd-total-size
  else, drop ty-size then, ;
: cc-nalignment ( ty desc -- n )
  over ty-base ty-array = over [lit] 0 <> and if,
    over ty-ptr 0= if, nip cc-ad-align exit, then,
  then,
  over ty-base ty-struct = [lit] 2 cc-npick ty-ptr 0= and if,
    nip cc-sd-align
  else, drop ty-align then, ;

```

`cc-nsize` and `cc-nalignment` keep extent separate from alignment: a record’s extent can exceed every member’s alignment (Chapter 30).

## Recognize a native base

Tag lookup filters for tag symbols, while declaration lookahead also accepts typedef names and the extended scalar keywords (`forth-bootstrap/cc/115-cc-native.fth:71`):

```forth file=cc/115-cc-native.fth
\ Tags live in their own namespace, so typedef struct T T is unambiguous.
variable cc-ntag-a
variable cc-ntag-u
: cc-nfind-tag ( a u -- id|-1 )
  cc-ntag-u ! cc-ntag-a !
  cc-sym-count @
  begin, dup while,
    1-
    dup cc-sym-kind-of sk-struct = if,
      dup cc-sym-name-len cell[] @ cc-ntag-u @ = if,
        dup cc-sym-name-addr cell[] @ cc-ntag-a @ cc-ntag-u @ bytes-eq if,
          exit,
        then,
      then,
    then,
  repeat, drop true ;

: cc-native-type-start
  cc-tok-is-basic-type-kw? cc-qualifier? or
  kw-struct cc-tok-kw? or kw-union cc-tok-kw? or kw-enum cc-tok-kw? or
  kw-float cc-tok-kw? or kw-double cc-tok-kw? or kw-bool cc-tok-kw? or
  tok-kind @ tk-ident = if,
    tok-str-addr @ tok-str-len @ cc-sym-find
    dup 0< if, drop else, cc-sym-kind-of sk-typedef = or then,
  then, ;
' cc-native-type-start is cc-native-type-start-fwd
```

`cc-native-type-start` answers only whether declaration syntax may begin here; it does not promise that every recognized type is enabled in the selected profile.

Base parsing needs recursive aggregate dispatch and target decisions about typedef validity, omitted bases, and enum provenance (`forth-bootstrap/cc/115-cc-native.fth:97`):

```forth file=cc/115-cc-native.fth

: cc-ntypedef-check-noop ;
defer cc-ntypedef-check-fwd
' cc-ntypedef-check-noop is cc-ntypedef-check-fwd

\ A target may provide C90's omitted int base without changing native mode.
: cc-native-implicit-base-noop [lit] 0 ;
defer cc-native-implicit-base-fwd
' cc-native-implicit-base-noop is cc-native-implicit-base-fwd

defer cc-nbase-fwd

defer cc-naggregate-fwd

\ A target can retain enum provenance without changing its scalar encoding.
: cc-nenum-desc-default [lit] 0 ;
defer cc-nenum-desc-fwd
' cc-nenum-desc-default is cc-nenum-desc-fwd

```

The defaults add no typedef check, implicit base, or enum descriptor. Deferred words let a later target change these decisions without replacing the walker.

The native enum reader returns the scalar type together with the descriptor hook’s answer after optionally installing enumerators (`forth-bootstrap/cc/115-cc-native.fth:116`):

```forth file=cc/115-cc-native.fth
\ Read an enum type and optionally install its enumerators.
: cc-nenum
  cc-next-token-keep
  tok-kind @ tk-ident = if, cc-next-token-keep then,
  [char] { cc-tok-punct? if,
    [lit] 0
    begin,
      cc-next-token-keep
      [char] } cc-tok-punct? 0= while,
      tok-kind @ tk-ident <> if, [lit] 190 cc-die then,
      tok-str-addr @ tok-str-len @ rot
      cc-next-token-keep
      [char] = cc-tok-punct? if, drop cc-parse-const else, cc-putback-token then,
      dup >r sk-enum swap ty-int [lit] 0 ty-make swap cc-sym-add drop
      r> 1+
      cc-next-token-keep
      [char] , cc-tok-punct? 0= if,
        [char] } cc-tok-punct? 0= if, [lit] 192 cc-die then,
        cc-putback-token
      then,
    repeat,
    drop
  else, cc-putback-token then,
  ty-int [lit] 0 ty-make cc-nenum-desc-fwd ;

```

## Count type specifiers before choosing a type

A qualifier between type keywords must not end the base prematurely; the specifier reader skips it while retaining its flags (`forth-bootstrap/cc/115-cc-native.fth:141`):

```forth file=cc/115-cc-native.fth
\ A target may consume context-specific declaration specifiers around base
\ keywords. Native mode keeps its existing token and qualifier handling.
: cc-nbase-specifiers-default ;
defer cc-nbase-specifiers-fwd
' cc-nbase-specifiers-default is cc-nbase-specifiers-fwd

\ C90 lets qualifiers and target specifiers appear between type keywords:
\ `unsigned const char` and `long volatile int` name the same type as their
\ qualifier-first spellings. Read past them into the next type keyword.
\ Qualifiers keep their existing flag; they never change the base type.
: cc-nbase-next-specifier
  begin,
    cc-nbase-specifiers-fwd
    cc-qualifier? while, cc-qual-note cc-next-token-keep
  repeat, ;

```

`cc-nbase-specifiers-default` consumes nothing, reserving this position for target-specific specifiers without coupling qualifier placement to target policy.

Keyword counts preserve the whole spelling until the parser can decide what type it denotes (`forth-bootstrap/cc/115-cc-native.fth:157`):

```forth file=cc/115-cc-native.fth
\ Type keywords are counted per spelling: int .. signed use their keyword
\ numbers 0-6 as slots; float, double and _Bool have named slots after them.
\ A target may check the multiset; native mode keeps its permissive
\ keyword sequence.
[lit] 7 constant cc-nspec-float
[lit] 8 constant cc-nspec-double
[lit] 9 constant cc-nspec-bool
[lit] 10 constant cc-nspec-slots
create cc-nspec-counts cc-nspec-slots [lit] 8 * allot
: cc-nspec-count ( slot -- n ) cc-nspec-counts cell[] @ ;
: cc-nspec-keyword? ( -- flag )
  cc-tok-is-basic-type-kw? kw-float cc-tok-kw? or kw-double cc-tok-kw? or
  kw-bool cc-tok-kw? or ;
: cc-nspec-note
  cc-nspec-keyword? 0= if, exit, then,
  tok-kw-id @
  dup kw-float = if, drop cc-nspec-float then,
  dup kw-double = if, drop cc-nspec-double then,
  dup kw-bool = if, drop cc-nspec-bool then,
  cc-nspec-counts cell[] dup @ 1+ swap ! ;
: cc-nspec-check-default ;
defer cc-nspec-check-fwd
' cc-nspec-check-default is cc-nspec-check-fwd

```

`cc-nspec-counts` retains the keyword multiset, including floating and boolean specifiers. `cc-nspec-check-default` accepts it without further validation.

Choosing from the completed counts makes `unsigned long` and `long unsigned` independent of spelling order (`forth-bootstrap/cc/115-cc-native.fth:181`):

```forth file=cc/115-cc-native.fth
\ The base comes from the counted keywords. In native mode an invalid set
\ still selects one base: the first of void, _Bool, float, double, char,
\ short and long that occurs, otherwise int. Long double is double with a long.
\ Two longs name long long only under LP64; the legacy model has one long.
: cc-nspec-base ( -- base )
  kw-void cc-nspec-count if, ty-void exit, then,
  cc-nspec-bool cc-nspec-count if, ty-bool exit, then,
  cc-nspec-float cc-nspec-count if, ty-float exit, then,
  cc-nspec-double cc-nspec-count if,
    kw-long cc-nspec-count if, ty-ldouble else, ty-double then, exit,
  then,
  kw-char cc-nspec-count if, ty-char exit, then,
  kw-short cc-nspec-count if, ty-short exit, then,
  kw-long cc-nspec-count if,
    kw-long cc-nspec-count [lit] 1 > cc-target-lp64 @ and if,
      ty-llong
    else, ty-long then, exit,
  then,
  ty-int ;

\ A target may give a keyword-spelled scalar its own representation; the
\ SysV layer (121) makes long double an opaque sixteen-byte record.
: cc-nbase-scalar-default ( type descriptor -- type descriptor ) ;
defer cc-nbase-scalar-fwd
' cc-nbase-scalar-default is cc-nbase-scalar-fwd

```

`cc-nspec-base` selects `long long` when the counts contain repeated `long` under LP64. This permissive default is not full declaration validation. `cc-nbase-scalar-default` leaves the resulting type and descriptor untouched; the representation hook is used by the later target. Floating values are taught in Chapter 47 and extended floating values in Chapter 49.

## Finish the base without losing qualifiers

Aggregate, enum, typedef, and keyword bases enter through the same base-type dispatch (`forth-bootstrap/cc/115-cc-native.fth:207`):

```forth file=cc/115-cc-native.fth
\ The current token is a base type. Return encoded type and descriptor.
: cc-nbase-raw
  cc-nctx @ 0= if, cc-ncontext then,
  [lit] 0 nc-base-array ! [lit] 0 nc-base-inner !
  cc-nbase-next-specifier
  cc-native-implicit-base-fwd if, exit, then,
  kw-struct cc-tok-kw? kw-union cc-tok-kw? or if,
    cc-naggregate-fwd exit,
  then,
  kw-enum cc-tok-kw? if, cc-nenum exit, then,
  tok-kind @ tk-ident = if,
    tok-str-addr @ tok-str-len @ cc-sym-find
    dup 0< if, [lit] 194 cc-die then,
    dup cc-sym-kind-of sk-typedef <> if, [lit] 195 cc-die then,
    cc-ntypedef-check-fwd
    dup cc-sym-val-of swap cc-sym-struct-desc-of exit,
  then,
  \ Count every keyword first, so the spelling order cannot matter.
```

The keyword path applies unsignedness and the floating-type gate before its wrapper preserves the base qualifiers for each following declarator (`forth-bootstrap/cc/115-cc-native.fth:225`):

```forth file=cc/115-cc-native.fth
  cc-nspec-counts cc-nspec-slots [lit] 8 * cc-nzero
  begin,
    cc-nspec-note
    cc-next-token-keep cc-nbase-next-specifier
    cc-nspec-keyword?
  while, repeat,
  cc-putback-token cc-nspec-check-fwd
  cc-nspec-base kw-unsigned cc-nspec-count
  over ty-float = [lit] 2 cc-npick ty-double = or
  [lit] 2 cc-npick ty-ldouble = or cc-native-float-types-fwd 0= and if,
    [lit] 214 cc-die
  then,
  if,
    dup ty-char = if, drop ty-uchar else,
    dup ty-short = if, drop ty-ushort else,
    dup ty-long = if, drop ty-ulong else,
    dup ty-llong = if, drop ty-ullong else,
    drop ty-uint then, then, then, then,
  then,
  [lit] 0 ty-make [lit] 0 cc-nbase-scalar-fwd ;
\ A target may also read specifiers after a typedef name, tag or implicit
\ int, as in `struct S static s;`; native mode leaves them to the declarator.
: cc-nbase-trailing-default ;
defer cc-nbase-trailing-fwd
' cc-nbase-trailing-default is cc-nbase-trailing-fwd
 : cc-nbase
  cc-nctx @ 0= if, cc-ncontext then,
  nc-prefix-qualified @ nc-qualified ! [lit] 0 nc-prefix-qualified !
  cc-nbase-raw cc-nbase-trailing-fwd nc-qualified @ nc-base-qualified ! ;
' cc-nbase is cc-nbase-fwd

```

`cc-nbase-trailing-default` leaves trailing specifiers alone; its hook permits target handling after typedef, tag, or keyword bases. Binding `cc-nbase-fwd` after the qualifier wrapper ensures recursive members receive the same handling.

## Separate a declarator’s shape from its base

Callback parsing, name requirements, declarator validation, and extra array syntax have separate extension points (`forth-bootstrap/cc/115-cc-native.fth:256`):

```forth file=cc/115-cc-native.fth
\ The optional ABI layer records function-pointer signatures at this seam.
: cc-nfnptr-default ( extra-stars -- )
  drop cc-skip-fnptr-params ty-func [lit] 1 ty-make nc-ty ! ;
defer cc-nfnptr-fwd
' cc-nfnptr-default is cc-nfnptr-fwd
: cc-ndeclarator-check-noop ;
defer cc-ndeclarator-check-fwd
' cc-ndeclarator-check-noop is cc-ndeclarator-check-fwd

\ A named declarator is the bootstrap default. Prototype parameters may
\ opt into an abstract function-pointer declarator with no identifier.
: cc-nfnptr-name-default
  cc-expect-ident
  tok-str-addr @ nc-name ! tok-str-len @ nc-nlen ! ;
defer cc-nfnptr-name-fwd
' cc-nfnptr-name-default is cc-nfnptr-name-fwd

: cc-narray-extra-default ;
defer cc-narray-extra-fwd
' cc-narray-extra-default is cc-narray-extra-fwd

```

Array bounds belong to the object shape, whereas a function suffix saves parameter tokens for a possible definition (`forth-bootstrap/cc/115-cc-native.fth:277`):

```forth file=cc/115-cc-native.fth
\ Parse array suffixes with the current '[' already read. The count and
\ element type are independent, including arrays of function pointers.
: cc-narray-suffix
  [char] [ cc-tok-punct? if,
    cc-next-token-keep
    [char] ] cc-tok-punct? if, true nc-array ! else,
      [lit] 1 nc-bound-mask !
      cc-putback-token cc-parse-const nc-array ! [char] ] cc-expect-punct-c
    then,
    cc-next-token-keep
    [char] [ cc-tok-punct? if,
      [lit] 2 nc-bound-mask +!
      cc-parse-const nc-inner ! [char] ] cc-expect-punct-c
      cc-next-token-keep
    then,
    cc-narray-extra-fwd
  then, ;

: cc-nfunction-suffix
  \ An array may contain pointers to functions, never functions themselves.
  nc-array @ if, [lit] 238 cc-die then,
  true nc-func !
  nc-params cc-lex-mark
  cc-skip-fnptr-params
  cc-next-token-keep ;

```

`cc-narray-suffix` records bounds for later inference. `cc-nfunction-suffix` rejects arrays of functions and saves parameter tokens for a possible body. An array of pointers to functions follows the grouped path instead.

Parentheses around a name must preserve its array suffixes without accepting unsupported nested pointer groups (`forth-bootstrap/cc/115-cc-native.fth:303`):

```forth file=cc/115-cc-native.fth
\ A grouped declarator distinguishes (*f()) (function returning a pointer)
\ from (*f)() and (*f[N])() (a pointer or array of pointers to functions).
\ Stars inside the group belong to the object only when no outer function
\ suffix follows. General pointers to arrays still lack a representation.
: cc-npointer-array-default drop [lit] 238 cc-die ;
defer cc-npointer-array-fwd
' cc-npointer-array-default is cc-npointer-array-fwd
\ Parentheses around a starless direct declarator only group: (*(s[2]))()
\ declares what (*s[2])() does.  The name and its array suffixes are read
\ here; the outer group sees the token after the inner ')' as if it had
\ followed the name.  Pointer groups nested inside a group stay outside.
: cc-ngroup-name
  cc-next-token-keep
  lparen cc-tok-punct? 0= if, cc-putback-token cc-nfnptr-name-fwd exit, then,
  cc-next-token-keep
  [char] * cc-tok-punct? if, [lit] 238 cc-die then,
  tok-kind @ tk-ident <> if, [lit] 203 cc-die then,
  tok-str-addr @ tok-str-len @ cc-sym-find
  dup 0< 0= if,
    cc-sym-kind-of sk-typedef = if, [lit] 203 cc-die then,
  else, drop then,
  tok-str-addr @ nc-name ! tok-str-len @ nc-nlen !
  cc-next-token-keep
  cc-narray-suffix
  [char] ) cc-tok-punct? 0= if, [lit] 143 cc-die then,
  cc-next-token-keep
  [char] [ cc-tok-punct? nc-array @ and if, [lit] 238 cc-die then,
  cc-putback-token ;
```

`cc-ngroup-name` handles that limited grouping. `cc-npointer-array-default` rejects general pointer-to-array shapes; its deferred partner leaves room for another representation without silently flattening the shape.

## Resolve grouped declarators

A function suffix inside the group makes the grouped name a function returning the accumulated pointer type (`forth-bootstrap/cc/115-cc-native.fth:331`):

```forth file=cc/115-cc-native.fth
: cc-ngrouped-declarator
  cc-count-stars >r
  cc-ngroup-name
  cc-next-token-keep
  lparen cc-tok-punct? if,
    nc-nlen @ 0= if, [lit] 203 cc-die then,
    r> nc-ty +!
    cc-nfunction-suffix
    [char] ) cc-tok-punct? 0= if, [lit] 143 cc-die then,
    cc-next-token-keep
    lparen cc-tok-punct? [char] [ cc-tok-punct? or if, [lit] 238 cc-die then,
    exit,
  then,
  cc-narray-suffix
  \ A later grouped pointer/function constructor cannot replace ranked
  \ element metadata. Keep that complex declarator outside this profile.
  nc-array @ nc-ty @ ty-base ty-array = and
  nc-ty @ ty-ptr 0= and if, [lit] 238 cc-die then,
  [char] ) cc-tok-punct? 0= if, [lit] 143 cc-die then,
  cc-next-token-keep
```

A suffix outside the group instead selects a function pointer or delegates the pointer-to-array case (`forth-bootstrap/cc/115-cc-native.fth:351`):

```forth file=cc/115-cc-native.fth
  lparen cc-tok-punct? if,
    r@ 0= if,
      r> drop
      nc-array @ if, [lit] 238 cc-die then,
      cc-nfunction-suffix
    else,
      r> 1- cc-nfnptr-fwd
      cc-next-token-keep
      lparen cc-tok-punct? [char] [ cc-tok-punct? or if, [lit] 238 cc-die then,
    then,
  else,
    r@ [char] [ cc-tok-punct? and if,
      r> cc-npointer-array-fwd exit,
    then,
    nc-array @ [char] [ cc-tok-punct? and if, [lit] 238 cc-die then,
    r> nc-ty +!
  then, ;

```

The distinction is where the star belongs: in the return type or in the declared object. `cc-ngrouped-declarator` retains array metadata and rejects combinations its representation cannot preserve. Chapter 41 retains the shared call signature through the function-pointer hook.

Each declarator resets its name and dimensions before combining its own shape with the saved base (`forth-bootstrap/cc/115-cc-native.fth:369`):

```forth file=cc/115-cc-native.fth
\ Declarator after nc-base/nc-sdesc. Function parameter tokens are saved
\ so a definition can return and install parameter names after classification.
: cc-ndeclarator
  nc-base-qualified @ nc-qualified !
  cc-skip-qualifiers
  nc-qualified @ nc-base-qualified !
  nc-base @ cc-count-stars + nc-ty !
  nc-sdesc @ nc-desc !
  [lit] 0 nc-name ! [lit] 0 nc-nlen !
  [lit] 0 nc-array ! [lit] 0 nc-inner ! [lit] 0 nc-func !
  [lit] 0 nc-bound-mask !
  cc-next-token-keep
  lparen cc-tok-punct? if,
    cc-ngrouped-declarator
  else,
    tok-kind @ tk-ident = if,
      tok-str-addr @ nc-name ! tok-str-len @ nc-nlen !
      cc-next-token-keep
    then,
  then,
  cc-narray-suffix
  lparen cc-tok-punct? if, cc-nfunction-suffix then,
  cc-ndeclarator-check-fwd ;

```

`cc-ndeclarator` leaves the following token available to the caller. That caller can distinguish an initializer, a function body, another declarator, or the declaration terminator without reparsing the name.

## Place fields at aligned offsets

For `Item`, placing `tag` leaves the running extent at one byte. Before
placing `value`, round that extent up to its eight-byte alignment: the
next field begins at offset 8 and ends at offset 16. The record's maximum
member alignment is eight, so completion needs no further tail padding in
this example. These decisions use each field's object type, even though
both values can pass through the same eight-byte expression register.

Growing a field table changes record addresses, so qualifier entries must follow the moved records (`forth-bootstrap/cc/115-cc-native.fth:393`):

```forth file=cc/115-cc-native.fth
\ Field qualification (070) is keyed by record address, and a growing
\ field table (060) moves its records: re-key the entries that moved.
variable cc-nmove-old
variable cc-nmove-new
variable cc-nmove-bytes
: cc-nqualified-move ( old new bytes -- )
  cc-nmove-bytes ! cc-nmove-new ! cc-nmove-old !
  cc-qualified-fields @ begin, dup while,
    dup [lit] 8 + @ cc-nmove-old @ -             ( entry offset )
    dup 0< 0= over cc-nmove-bytes @ < and if,
      cc-nmove-new @ + over [lit] 8 + !
    else, drop then,
    @
  repeat, drop ;
' cc-nqualified-move is cc-sd-table-moved

```

`cc-nqualified-move` changes only qualifier keys inside the moved region.

A field’s offset comes from its alignment before its extent contributes to the containing record (`forth-bootstrap/cc/115-cc-native.fth:409`):

```forth file=cc/115-cc-native.fth
\ Add a field, including flattened anonymous aggregate members.
: cc-nadd-field ( desc -- )
  dup cc-sd-field-count over swap cc-sd-field-rec >r
  nc-qualified @ r@ cc-field-set-qualified
  nc-name @ r@ cc-sf-set-name-addr
  nc-nlen @ r@ cc-sf-set-name-len
  nc-ty @ r@ cc-sf-set-type
  nc-desc @ r@ cc-sf-set-desc
  nc-array @ r@ cc-sf-set-array-len
  nc-inner @ r@ cc-sf-set-array-inner
  nc-ty @ nc-desc @ cc-nalignment
  over cc-sd-align over < if, dup [lit] 2 cc-npick cc-sd-set-align then,
  over cc-sd-total-size swap cc-nalign
  over cc-sd-union? if, drop [lit] 0 then,
  dup r> cc-sf-set-offset
  nc-ty @ nc-desc @ cc-nsize
  nc-array @ [lit] 0 > if, nc-array @ * then,
  nc-inner @ [lit] 0 > if, nc-inner @ * then,
  + over cc-sd-total-size cc-nmax over cc-sd-set-total-size
  dup cc-sd-field-count 1+ swap cc-sd-set-field-count ;

```

`cc-nadd-field` copies the current declaration into the next field record. For a struct it rounds the running extent up; for a union it uses the shared beginning. It retains the maximum alignment and the maximum ending position, multiplying element extent by the recorded array bounds. Final tail padding belongs to aggregate completion, not to each field.

An anonymous aggregate exposes its child records at offsets relative to the containing object (`forth-bootstrap/cc/115-cc-native.fth:430`):

```forth file=cc/115-cc-native.fth
\ Anonymous aggregate promotion copies records and adds the enclosing offset.
: cc-npromote-fields ( child parent -- )
  dup cc-sd-field-count 1- over swap cc-sd-field-rec cc-sf-offset >r
  dup cc-sd-field-count 1- over cc-sd-set-field-count
  over cc-sd-field-count [lit] 0
  begin, 2dup > while,
    dup [lit] 4 cc-npick swap cc-sd-field-rec
    [lit] 3 cc-npick dup cc-sd-field-count swap over cc-sd-field-rec
    swap drop
    2dup swap cc-field-qualified nc-qualified @ or swap cc-field-set-qualified
    cc-sd-record-bytes cc-ncopy
    [lit] 2 cc-npick dup cc-sd-field-count cc-sd-field-rec
    dup cc-sf-offset r@ + swap cc-sf-set-offset
    [lit] 2 cc-npick dup cc-sd-field-count 1+ swap cc-sd-set-field-count
    1+
  repeat, 2drop 2drop r> drop ;

\ A target may add member syntax while retaining the shared declarator.
: cc-nmember-default ( desc -- )
  nc-func @ if, [lit] 238 cc-die then,
  dup cc-nadd-field
  nc-nlen @ 0= if, nc-desc @ swap cc-npromote-fields else, drop then, ;
defer cc-nmember-fwd
' cc-nmember-default is cc-nmember-fwd

```

`cc-npromote-fields` replaces the anonymous field entry with copied child records, adds the enclosing offset, and combines qualifiers. `cc-nmember-default` rejects function members and selects that promotion only for an unnamed member; `cc-nmember-fwd` is the point Chapter 48 extends for bitfields.

## Complete aggregates and type queries

Aggregate parsing uses a fresh declaration context for members and rounds the completed extent to the record alignment (`forth-bootstrap/cc/115-cc-native.fth:455`):

```forth file=cc/115-cc-native.fth
: cc-naggregate
  kw-union cc-tok-kw? >r
  cc-next-token-keep
  tok-kind @ tk-ident = if,
    tok-str-addr @ tok-str-len @ 2dup cc-nfind-tag
    dup 0< if,
      drop cc-sd-alloc dup >r
      sk-struct swap [lit] 0 swap cc-sym-add drop r>
    else, nip nip cc-sym-val-of then,
    cc-next-token-keep
  else, cc-sd-alloc then,
  r> over cc-sd-set-union
  [char] { cc-tok-punct? if,
    [lit] 1 over cc-sd-set-align
    cc-nctx @ >r cc-ncontext
    begin,
      cc-next-token-keep
      [char] } cc-tok-punct? 0= while,
      cc-nbase-fwd nc-sdesc ! nc-base !
      begin,
        cc-ndeclarator
        dup cc-nmember-fwd
        [char] , cc-tok-punct?
      while, repeat,
      [char] ; cc-tok-punct? 0= if, [lit] 58 cc-die then,
    repeat,
    dup cc-sd-total-size over cc-sd-align cc-nalign over cc-sd-set-total-size
    r> cc-nctx !
  else, cc-putback-token then,
  ty-struct [lit] 0 ty-make swap ;
' cc-naggregate is cc-naggregate-fwd

```

`cc-naggregate` adds union layout, aligned members, and tail padding to struct tag pre-registration (Chapter 35). Saving and restoring `cc-nctx` keeps recursive members from replacing the containing declarator; `cc-naggregate-fwd` closes the recursive dependency with base parsing.

A type query inside a declaration must leave the enclosing array shape and qualifiers intact (`forth-bootstrap/cc/115-cc-native.fth:487`):

```forth file=cc/115-cc-native.fth
\ Type queries preserve the enclosing declaration's array base shape.
: cc-native-type-shape-default + ;
defer cc-native-type-shape-fwd
' cc-native-type-shape-default is cc-native-type-shape-fwd
: cc-native-type-name
  cc-nctx @ 0= if, cc-ncontext then,
  nc-base-qualified @ >r nc-qualified @ >r
  nc-base-array @ >r nc-base-inner @ >r
  [lit] 0 cc-type-name-array ! [lit] 0 cc-type-name-inner !
  cc-nbase cc-cast-desc ! cc-skip-qualifiers cc-count-stars
  cc-native-type-shape-fwd
  nc-qualified @ cc-type-name-qualified !
  r> nc-base-inner ! r> nc-base-array !
  r> nc-qualified ! r> nc-base-qualified ! ;
' cc-native-type-name is cc-native-type-name-fwd

```

`cc-native-type-name` restores declaration state after parsing. Its default shape hook adds pointer depth; a later target can supply richer shapes. `cc-cast-desc` receives the result descriptor.

## Allocate an object and keep its references valid

The completed `Item` descriptor now requests a sixteen-byte object with
eight-byte alignment. Allocation must reserve that whole extent before
initialization starts. The base it chooses, together with the retained
field offsets 0 and 8, supplies the two destinations; the initializer
must not allocate a fresh working slot for each member.

Storage allocation needs the full object extent, and its symbol must retain the same shape used to compute it (`forth-bootstrap/cc/115-cc-native.fth:503`):

```forth file=cc/115-cc-native.fth
defer cc-native-function-fwd

: cc-nobject-size
  nc-ty @ nc-desc @ cc-nsize
  nc-array @ [lit] 0 > if, nc-array @ * then,
  nc-inner @ [lit] 0 > if, nc-inner @ * then, ;

: cc-ninstall-symbol ( kind slot -- id )
  >r >r nc-name @ nc-nlen @ r> nc-ty @ r> cc-sym-add
  nc-desc @ over cc-sym-set-struct-desc
  nc-array @ over cc-sym-set-array-len
  nc-inner @ over cc-sym-set-array-inner
  nc-qualified @ over cc-sym-qualified cell[] ! ;

: cc-ngstore ( value offset bytes -- )
  >r cc-globals-buf + r>
  begin, dup while,
    >r over [lit] 255 and over c!
    1+ swap [lit] 256 / swap r> 1-
  repeat, drop 2drop ;
```

`cc-ninstall-symbol` preserves the allocated object’s type, dimensions, and qualifiers. The scalar initializer uses `cc-ngstore` for direct byte stores.

A tentative object that gains an initializer must redirect existing address fixups to initialized storage (`forth-bootstrap/cc/115-cc-native.fth:523`):

```forth file=cc/115-cc-native.fth
: cc-nmove-tentative
  nc-slot @ cc-bss-flag >= if,
    cc-globals-pos @ nc-ty @ nc-desc @ cc-nalignment cc-nalign cc-globals-pos !
    cc-nobject-size cc-globals-alloc
    [lit] 0
    begin, dup cc-gfixup-count @ < while,
      dup cc-gfixup-slot cell[] @ nc-slot @ = if,
        over over cc-gfixup-slot cell[] !
      then, 1+
    repeat, drop
    dup nc-id @ cc-sym-val cell[] ! nc-slot !
  then, ;

```

The first initializer handles scalar values and reserves hooks for strings and aggregates (`forth-bootstrap/cc/115-cc-native.fth:536`):

```forth file=cc/115-cc-native.fth
: cc-native-init-noop ;
defer cc-native-init-prepare-fwd
defer cc-native-init-fwd
defer cc-native-init-entry-fwd
defer cc-native-init-finish-fwd
' cc-native-init-noop is cc-native-init-prepare-fwd
' cc-native-init-noop is cc-native-init-entry-fwd
' cc-native-init-noop is cc-native-init-finish-fwd
: cc-native-scalar-init
  nc-top @ nc-static @ or if,
    cc-nmove-tentative
    cc-parse-const nc-slot @ nc-ty @ ty-size cc-ngstore
  else,
    cc-parse-assign cc-emit-materialize
    nc-slot @ nc-ty @ cc-emit-store-local-typed
  then,
  cc-next-token-keep ;
' cc-native-scalar-init is cc-native-init-fwd

```

`cc-nmove-tentative` allocates an aligned destination, changes matching fixup slots, and updates both symbol and context. `cc-native-scalar-init` then writes a static constant into the global buffer or emits a typed local store. Empty prepare, entry, and finish hooks let the initializer layer replace this scalar path.

The object allocator distinguishes persistent storage from a function-local reservation before installing the symbol (`forth-bootstrap/cc/115-cc-native.fth:555`):

```forth file=cc/115-cc-native.fth
: cc-native-local-layout-default ( -- slots slot )
  cc-nobject-size [lit] 7 + [lit] 8 / dup cc-fn-local-count @ + 1- ;
defer cc-native-local-layout-fwd
' cc-native-local-layout-default is cc-native-local-layout-fwd

: cc-nobject
  [char] = cc-tok-punct? if, cc-native-init-prepare-fwd then,
  nc-name @ nc-nlen @ cc-sym-find nc-id !
  nc-top @ nc-static @ or if,
    nc-top @ 0= if, true nc-id ! then,
    nc-id @ 0< 0= if,
      nc-id @ cc-sym-kind-of sk-global = if,
        nc-id @ cc-sym-val-of nc-slot !
      else, true nc-id ! then,
    then,
    nc-id @ 0< if,
      [char] = cc-tok-punct? if,
        cc-globals-pos @ nc-ty @ nc-desc @ cc-nalignment cc-nalign cc-globals-pos !
        cc-nobject-size cc-globals-alloc
      else,
        cc-bss-pos @ nc-ty @ nc-desc @ cc-nalignment cc-nalign cc-bss-pos !
        cc-nobject-size cc-bss-alloc
      then,
      dup nc-slot ! sk-global swap cc-ninstall-symbol nc-id !
      cc-nobject-size nc-id @ cc-sym-set-object-size
    else,
```

`cc-native-local-layout-default` rounds object extent into stack slots and returns the slot at the object’s base. `cc-native-local-layout-fwd` reserves that choice for another calling convention. In `cc-nobject`, inference runs before allocation; initialized objects use the global buffer and tentative objects use BSS.

A larger later declaration must update pending references as well as the symbol’s new dimensions (`forth-bootstrap/cc/115-cc-native.fth:581`):

```forth file=cc/115-cc-native.fth
      cc-nobject-size nc-id @ cc-sym-object-size-of > if,
        cc-bss-pos @ nc-ty @ nc-desc @ cc-nalignment cc-nalign cc-bss-pos !
        cc-nobject-size cc-bss-alloc
        [lit] 0
        begin, dup cc-gfixup-count @ < while,
          dup cc-gfixup-slot cell[] @ nc-slot @ = if,
            over over cc-gfixup-slot cell[] !
          then, 1+
        repeat, drop
        dup nc-id @ cc-sym-val cell[] ! nc-slot !
        cc-nobject-size nc-id @ cc-sym-set-object-size
      then,
      nc-ty @ nc-id @ cc-sym-type cell[] !
      nc-desc @ nc-id @ cc-sym-set-struct-desc
      nc-array @ nc-id @ cc-sym-set-array-len
      nc-inner @ nc-id @ cc-sym-set-array-inner
    then,
  else,
    cc-native-local-layout-fwd dup nc-slot !
    sk-local swap cc-ninstall-symbol nc-id !
    cc-fn-add-slots
  then,
  [char] = cc-tok-punct? if, cc-native-init-fwd then, ;

defer cc-nobject-fwd
' cc-nobject is cc-nobject-fwd

```

The growth branch reserves a replacement BSS region and retargets matching fixups. The local branch uses the selected frame layout and advances the function’s slot count. Both paths reach initialization only after `nc-slot` identifies a destination.

## Dispatch the completed declaration

Storage-class parsing must know which context owns the base being read (`forth-bootstrap/cc/115-cc-native.fth:608`):

```forth file=cc/115-cc-native.fth
\ cc-nstorage-context is the declaration context whose own base may hold
\ storage-class keywords among its type specifiers (C90 6.5 sets no order);
\ a target reads them through cc-nbase-specifiers-fwd.  nc-storage starts
\ with the count already read before the base, including a leading typedef.
variable cc-nstorage-context
: cc-native-declaration ( top? -- )
  cc-nctx @ >r cc-ncontext nc-top !
  cc-prefix-qualified @ nc-prefix-qualified ! [lit] 0 cc-prefix-qualified !
  cc-decl-static @ nc-static ! cc-decl-extern @ nc-extern !
  cc-decl-storage @ nc-storage !
  kw-typedef cc-tok-kw? if,
    true nc-td ! [lit] 1 nc-storage +! cc-next-token-keep
  then,
  cc-nstorage-context @ >r cc-nctx @ cc-nstorage-context !
  cc-nbase nc-sdesc ! nc-base !
  r> cc-nstorage-context !
  cc-next-token-keep
  [char] ; cc-tok-punct? if, r> cc-nctx ! exit, then,
  cc-putback-token
```

`cc-native-declaration` saves the enclosing context and transfers prefix qualifiers and storage flags into a new one. `cc-nstorage-context` temporarily names that context while `cc-nbase` runs. A tag-only declaration can then finish without an object name.

The declarator’s classification decides whether to install a typedef, parse a function, or allocate an object (`forth-bootstrap/cc/115-cc-native.fth:627`):

```forth file=cc/115-cc-native.fth
  begin,
    cc-ndeclarator
    nc-nlen @ 0= if, [lit] 203 cc-die then,
    nc-td @ if,
      nc-name @ nc-nlen @ sk-typedef [lit] 0 nc-ty @ cc-sym-add
      nc-qualified @ over cc-sym-qualified cell[] !
      nc-desc @ over cc-sym-set-struct-desc
      nc-array @ over cc-sym-set-array-len
      nc-inner @ swap cc-sym-set-array-inner
    else,
      nc-func @ if,
        cc-native-function-fwd
        [char] } cc-tok-punct? if, r> cc-nctx ! exit, then,
      else, cc-nobject-fwd then,
    then,
    [char] , cc-tok-punct?
  while, repeat,
  [char] ; cc-tok-punct? 0= if, [lit] 205 cc-die then,
  r> cc-nctx ! ;
: cc-native-local-declaration [lit] 0 cc-native-declaration ;
' cc-native-local-declaration is cc-native-decl-fwd
```

Comma-separated names reuse the base but have independent declarators. `cc-native-local-declaration` binds the statement parser’s declaration hook. The surrounding context is restored after the declaration or a completed function body.

## Private stack calls and whole programs

The native program layer’s private all-stack ABI gives each argument a caller-owned eight-byte stack slot. This storage convention is distinct from LP64 object widths: a `char` object remains narrow even when its evaluated argument travels in a full slot. System V interoperability belongs to Chapter 41.

Parameter names must address incoming caller slots rather than consume new local storage (`forth-bootstrap/cc/117-cc-native-program.fth:1`):

```forth file=cc/117-cc-native-program.fth
\ 117-cc-native-program.fth — program and private stack ABI for native mode.
\ All linked code is generated together. No system libc or host object is used.
variable cc-native-param-count
variable cc-native-frame-patch

: cc-native-params
  [lit] 0 cc-native-param-count !
  begin,
    cc-next-token-keep
    [char] ) cc-tok-punct? if, exit, then,
    pt-ellipsis cc-tok-punct? if, [char] ) cc-expect-punct-c exit, then,
    kw-void cc-tok-kw? if,
      cc-peek-mark cc-lex-mark cc-next-token-keep
      [char] ) cc-tok-punct? if, exit, then,
      cc-peek-mark cc-lex-reset
    then,
    cc-nbase nc-sdesc ! nc-base !
    cc-ndeclarator
    nc-array @ if, [lit] 1 nc-ty +! [lit] 0 nc-array ! then,
    nc-ty @ dup ty-base ty-struct = swap ty-ptr 0= and if, [lit] 212 cc-die then,
    nc-nlen @ if,
      sk-local [lit] 0 cc-native-param-count @ [lit] 3 + -
      cc-ninstall-symbol drop
    then,
    [lit] 1 cc-native-param-count +!
    [char] , cc-tok-punct? 0= if,
      [char] ) cc-tok-punct? 0= if, [lit] 184 cc-die then,
      exit,
    then,
  again, ;
```

`cc-native-params` converts array parameters to pointers, rejects aggregate values, and installs named parameters with negative local-slot indices. Those indices address the incoming area above the frame pointer.

A function body supplies addresses for both earlier calls and earlier function-pointer references (`forth-bootstrap/cc/117-cc-native-program.fth:31`):

```forth file=cc/117-cc-native-program.fth

: cc-native-function
  nc-ty @ dup ty-base ty-struct = swap ty-ptr 0= and if, [lit] 212 cc-die then,
  nc-name @ nc-nlen @ cc-sym-find
  dup 0< 0= if,
    dup cc-sym-kind-of sk-func <> if, drop true then,
  then,
  dup 0< if,
    drop nc-name @ nc-nlen @ sk-func nc-ty @ [lit] 0 cc-sym-add
    nc-desc @ over cc-sym-set-struct-desc
  then,
  nc-id !
  nc-ty @ nc-id @ cc-sym-type cell[] !
  nc-desc @ nc-id @ cc-sym-set-struct-desc
  [char] { cc-tok-punct? 0= if, exit, then,
  nc-id @ cc-sym-val-of if, [lit] 211 cc-die then,
  cc-here-vaddr nc-id @ cc-sym-val cell[] !
  nc-id @ cc-sym-call-fixups @ cc-here-vaddr cc-walk-and-patch-to-vaddr
  [lit] 0 nc-id @ cc-sym-call-fixups !
  nc-id @ cc-sym-addr-fixups @ cc-here-vaddr cc-walk-and-patch-imm64-to-vaddr
  [lit] 0 nc-id @ cc-sym-addr-fixups !
  nc-name @ nc-nlen @ cc-is-main? if, cc-here-vaddr cc-main-vaddr ! then,
  nc-ty @ cc-native-return-type ! nc-desc @ cc-native-return-desc !
```

`cc-native-function` distinguishes a prototype from a body at the opening brace, rejects a second body, and resolves both kinds of pending reference. Aggregate returns are excluded from this private boundary; pointers to aggregates remain representable.

The required frame extent is known only after the body has declared its locals (`forth-bootstrap/cc/117-cc-native-program.fth:54`):

```forth file=cc/117-cc-native-program.fth
  nc-params cc-lex-reset
  cc-nctx @ >r cc-ncontext
  cc-scope-push
  [lit] 0 cc-fn-local-count !
  [lit] 0 cc-label-count !
  [lit] 0 cc-break-stack-head ! [lit] 0 cc-continue-stack-head !
  [lit] 0 cc-switch-depth ! [lit] 0 cc-loop-switch-depth !
  cc-native-params
  [char] { cc-expect-punct-c
  [lit] 0 cc-emit-prologue
  cc-out-pos @ [lit] 4 - cc-native-frame-patch !
  begin,
    cc-next-token-keep [char] } cc-tok-punct? 0= while,
    cc-putback-token cc-parse-stmt
  repeat,
  cc-emit-xor-rax-rax cc-emit-epilogue
  cc-native-finish-gotos
  cc-fn-local-count @ [lit] 8 * [lit] 16 cc-nalign
  cc-native-frame-patch @ cc-out-patch-4le
  cc-scope-pop r> cc-nctx ! ;
' cc-native-function is cc-native-function-fwd

```

The saved parameter tokens are replayed in a fresh context and scope. A placeholder prologue precedes the statements; the completed local count determines the frame size, rounded to sixteen-byte alignment.

Static initialization must precede the call to `main`, so entry emission reserves its call before parsing declarations (`forth-bootstrap/cc/117-cc-native-program.fth:76`):

```forth file=cc/117-cc-native-program.fth
: cc-native-entry
  cc-native-init-entry-fwd
  \ Kernel stack has argc,argv. Push arguments right-to-left for main.
  [lit] 72 cc-emit-byte [lit] 139 cc-emit-byte [lit] 60 cc-emit-byte [lit] 36 cc-emit-byte
  [lit] 72 cc-emit-byte [lit] 141 cc-emit-byte [lit] 116 cc-emit-byte [lit] 36 cc-emit-byte [lit] 8 cc-emit-byte
  [lit] 86 cc-emit-byte [lit] 87 cc-emit-byte
  cc-emit-call-rel32-placeholder cc-call-main-patch !
  cc-emit-mov-rdi-rax
  [lit] 184 cc-emit-byte [lit] 60 cc-emit-4le
  [lit] 15 cc-emit-byte [lit] 5 cc-emit-byte ;

: cc-native-runtime-noop ;
defer cc-native-runtime-fwd
' cc-native-runtime-noop is cc-native-runtime-fwd

: cc-native-program
  cc-native-entry
  cc-native-runtime-fwd
  begin,
    cc-skip-storage-quals cc-next-token-keep
    tok-kind @ tk-eof = 0= while,
    true cc-native-declaration
  repeat,
  cc-native-init-finish-fwd
  cc-check-fns-defined cc-patch-call-main ;
```

`cc-native-entry` delegates that reservation, obtains `argc` and `argv` from the kernel stack, pushes arguments in reverse order, and exits with the returned result. `cc-native-program` emits the selected runtime, parses top-level declarations, finishes initialization, and closes function references. The empty runtime hook lets the runtime file supply its implementation.

## Initializers reuse expression fixups

A static initializer can contain an address whose final value is unresolved. The native layer emits a small routine containing ordinary expression code and stores, then arranges to call it before `main`. This is static initializer lowering: runtime stores implement the accepted constant initialization language, without admitting arbitrary file-scope execution.

`cc-ni-frame` selects traversal state; `cc-ni-static` chooses persistent or local addressing.

Recursive initialization needs destination state independent of the declaration context (`forth-bootstrap/cc/118-cc-native-init.fth:1`):

```forth file=cc/118-cc-native-init.fth
\ 118-cc-native-init.fth — bounded C initializers for the native bootstrap.
\ Scalar stores, brace lists, nested arrays/aggregates and character strings
\ are lowered by the Forth compiler. Static expressions use the expression
\ parser's constant-category guard; they run once before main. This avoids
\ a second relocation engine: ordinary global/function fixups serve both
\ executable expressions and initializers. No host compiler is involved.
\ Designators and more than two array dimensions are outside this profile.

variable cc-ni-frame
variable cc-ni-static
variable cc-ni-head
variable cc-ni-tail
variable cc-ni-entry-patch

: ni-type   cc-ni-frame @ ;
: ni-desc   cc-ni-frame @ [lit] 8 + ;
: ni-array  cc-ni-frame @ [lit] 16 + ;
: ni-inner  cc-ni-frame @ [lit] 24 + ;
: ni-offset cc-ni-frame @ [lit] 32 + ;
: ni-index  cc-ni-frame @ [lit] 40 + ;
: ni-brace  cc-ni-frame @ [lit] 48 + ;
: ni-nested cc-ni-frame @ [lit] 56 + ;

```

Every leaf needs an address, while aggregate setup also needs byte-copy and zero-fill emission (`forth-bootstrap/cc/118-cc-native-init.fth:24`):

```forth file=cc/118-cc-native-init.fth
\ A target may represent a scalar as an opaque record (121: long double);
\ initializers treat it as one scalar leaf, never as a brace list.
: cc-ni-aggregate?
  ni-type @ ty-base ty-struct = ni-type @ ty-ptr 0= and
  ni-type @ ni-desc @ cc-opaque-scalar-fwd 0= and ;
: cc-ni-address ( offset -- )
  cc-ni-static @ if,
    nc-slot @ cc-emit-global-ref
  else, nc-slot @ cc-emit-lea-rdi-local then,
  dup if, cc-emit-add-rdi-imm32 else, drop then, ;
: cc-ni-count-rcx ( n -- )
  [lit] 185 cc-emit-byte cc-emit-4le ;
: cc-ni-mov-rsi-rdi
  [lit] 72 cc-emit-byte [lit] 137 cc-emit-byte [lit] 254 cc-emit-byte ;
: cc-ni-copy-bytes ( n -- )
  cc-ni-count-rcx [lit] 243 cc-emit-byte [lit] 164 cc-emit-byte ;
: cc-ni-zero-object
  [lit] 0 cc-ni-address
  cc-nobject-size cc-ni-count-rcx
  cc-emit-xor-rax-rax
  [lit] 243 cc-emit-byte [lit] 170 cc-emit-byte ;

```

`cc-ni-aggregate?` excludes an opaque scalar even if its representation uses a record descriptor. `cc-ni-address` chooses global-reference or local-address emission and adds the destination offset. `cc-ni-zero-object` clears omitted local elements.

An inferred character array must count decoded characters, not the source spelling of escape sequences (`forth-bootstrap/cc/118-cc-native-init.fth:46`):

```forth file=cc/118-cc-native-init.fth
\ The literal lexer retains escapes. Count exactly their decoded bytes.
: cc-ni-string-size ( a u -- n )
  [lit] 0 >r
  begin, dup [lit] 0 > while,
    over c@ backslash = over [lit] 1 > and if,
      over 1+ cc-decode-escape nip 1+
    else, [lit] 1 then,
    >r swap r@ + swap r> -
    r> 1+ >r
  repeat, 2drop r> ;

\ Before allocating an inferred array, count its outer brace elements.
\ Nested aggregates in inferred arrays require their own braces. Known-size
\ arrays additionally accept the ordinary brace-elided nested form.
variable cc-ni-scan-mark
variable cc-ni-scan-count
variable cc-ni-scan-depth
variable cc-ni-scan-have
variable cc-ni-scan-brace
```

`cc-ni-string-size` advances by each escape’s source length while counting its decoded byte.

## Infer extent before reserving storage

The inference pass recognizes a bare or braced string and includes its terminator in the inferred extent (`forth-bootstrap/cc/118-cc-native-init.fth:65`):

```forth file=cc/118-cc-native-init.fth
: cc-ni-infer
  nc-array @ [lit] 0 < 0= if, exit, then,
  cc-lex-state-size cc-alloc dup cc-ni-scan-mark ! cc-lex-mark
  cc-next-token-keep
  [lit] 0 cc-ni-scan-brace !
  nc-inner @ 0= nc-ty @ ty-ptr 0= and
  nc-ty @ ty-size [lit] 1 = and [char] { cc-tok-punct? and if,
    cc-lex-state-size cc-alloc dup >r cc-lex-mark
    cc-next-token-keep
    tok-kind @ tk-str = if,
      true cc-ni-scan-brace ! r> drop
    else, r> cc-lex-reset then,
  then,
  tok-kind @ tk-str = if,
    nc-ty @ ty-ptr if, [lit] 220 cc-die then,
    nc-ty @ ty-size [lit] 1 <> if, [lit] 220 cc-die then,
    [lit] 0
    begin, tok-kind @ tk-str = while,
      tok-str-addr @ tok-str-len @ cc-ni-string-size +
      cc-next-token-keep
    repeat, 1+ nc-array !
    cc-ni-scan-brace @ if,
      [char] , cc-tok-punct? if, cc-next-token-keep then,
      [char] } cc-tok-punct? 0= if, [lit] 223 cc-die then,
    then,
  else,
    [char] { cc-tok-punct? 0= if, [lit] 220 cc-die then,
```

For brace lists, only separators at the outer nesting level finish an element (`forth-bootstrap/cc/118-cc-native-init.fth:92`):

```forth file=cc/118-cc-native-init.fth
    [lit] 0 cc-ni-scan-count ! [lit] 0 cc-ni-scan-depth !
    [lit] 0 cc-ni-scan-have !
    begin,
      cc-next-token-keep
      tok-kind @ tk-eof = if, [lit] 221 cc-die then,
      [char] } cc-tok-punct? cc-ni-scan-depth @ 0= and if,
        cc-ni-scan-have @ if, [lit] 1 cc-ni-scan-count +! then,
        cc-ni-scan-count @ dup 0= if, [lit] 220 cc-die then, nc-array !
        cc-ni-scan-mark @ cc-lex-reset exit,
      then,
      [char] , cc-tok-punct? cc-ni-scan-depth @ 0= and if,
        cc-ni-scan-have @ 0= if, [lit] 221 cc-die then,
        [lit] 1 cc-ni-scan-count +! [lit] 0 cc-ni-scan-have !
      else,
        cc-ni-scan-have @ 0= if,
          nc-ty @ ty-base dup ty-struct = swap ty-array = or
          nc-ty @ ty-ptr 0= and nc-ty @ nc-desc @ cc-opaque-scalar-fwd 0= and if,
            [char] { cc-tok-punct? 0= if, [lit] 222 cc-die then,
          then,
          nc-inner @ if,
            [char] { cc-tok-punct? 0= if,
              tok-kind @ tk-str = nc-ty @ ty-ptr 0= and
              nc-ty @ ty-size [lit] 1 = and 0= if, [lit] 222 cc-die then,
            then,
```

`cc-ni-scan-have` distinguishes a real element from an empty position. For an inferred array of aggregates, the scanner requires braces around each aggregate so it can count outer objects before knowing their internal values.

Tracking nested delimiters prevents inner commas from enlarging the outer array (`forth-bootstrap/cc/118-cc-native-init.fth:116`):

```forth file=cc/118-cc-native-init.fth
          then,
        then,
        true cc-ni-scan-have !
        [char] { cc-tok-punct? lparen cc-tok-punct? or
        [char] [ cc-tok-punct? or if, [lit] 1 cc-ni-scan-depth +! then,
        [char] } cc-tok-punct? [char] ) cc-tok-punct? or
        [char] ] cc-tok-punct? or if, true cc-ni-scan-depth +! then,
        cc-ni-scan-depth @ [lit] 0 < if, [lit] 221 cc-die then,
      then,
    again,
  then,
  cc-ni-scan-mark @ cc-lex-reset ;
' cc-ni-infer is cc-native-init-prepare-fwd

defer cc-ni-value-fwd

```

`cc-ni-infer` restores the saved token state after computing `nc-array`; allocation sees the bound, and initialization sees the original input. Binding it to `cc-native-init-prepare-fwd` establishes that order.

## Initialize a string or scalar leaf

A string initializer needs literal bytes in the image and a copy into the destination object (`forth-bootstrap/cc/118-cc-native-init.fth:132`):

```forth file=cc/118-cc-native-init.fth
\ Emit one complete (possibly concatenated) character string and copy its
\ decoded bytes. C permits a fixed char[N] string of exactly N non-NUL bytes.
: cc-ni-string
  cc-emit-jmp-rel32-placeholder >r
  cc-here-vaddr cc-out-pos @
  begin, tok-kind @ tk-str = while,
    tok-str-addr @ tok-str-len @ cc-emit-string-bytes
    true cc-out-pos +!
    cc-next-token-keep
  repeat,
  cc-out-pos @ swap -
  dup ni-array @ > if, [lit] 223 cc-die then,
  [lit] 0 cc-emit-byte
  1+ dup ni-array @ > if, drop ni-array @ then,
  r> cc-patch-rel32-to-here
  swap cc-emit-movabs-rdi-imm64 cc-ni-mov-rsi-rdi
  ni-offset @ cc-ni-address cc-ni-copy-bytes ;

: cc-value-static-init-default drop ;
defer cc-value-static-init-fwd
' cc-value-static-init-default is cc-value-static-init-fwd

```

`cc-ni-string` jumps over the literal payload, concatenates adjacent tokens by replacing their intermediate terminators, and copies the decoded bytes. A fixed array may be exactly full without a terminator; a shorter string keeps its terminator. `cc-value-static-init-default` discards the requested type without adding target restrictions.

A scalar initializer saves the destination address before expression emission can replace the working register (`forth-bootstrap/cc/118-cc-native-init.fth:154`):

```forth file=cc/118-cc-native-init.fth
: cc-ni-scalar
  cc-ni-aggregate? cc-ni-static @ and if, [lit] 219 cc-die then,
  cc-ni-static @ if, ni-type @ cc-value-static-init-fwd then,
  ni-offset @ cc-ni-address cc-emit-push-rdi
  cc-putback-token cc-parse-assign
  cc-ni-aggregate? if,
    cc-last-expr-type @ ty-base ty-struct <>
    cc-last-expr-type @ ty-ptr [lit] 0 <> or
    cc-last-struct-desc @ ni-desc @ <> or if, [lit] 224 cc-die then,
    cc-ni-mov-rsi-rdi
    cc-emit-pop-rdi
    ni-type @ ni-desc @ cc-nsize cc-ni-copy-bytes
  else,
    cc-emit-materialize
    cc-last-expr-type @ cc-last-struct-desc @ ni-type @ ni-desc @ cc-value-shape-fwd
    cc-last-expr-type @ ni-type @ cc-value-init-fwd
    cc-emit-pop-rcx ni-type @ cc-emit-store-typed-via-rcx
  then,
  cc-next-token-keep ;

defer cc-ni-scalar-fwd
defer cc-ni-string-fwd
' cc-ni-scalar is cc-ni-scalar-fwd
' cc-ni-string is cc-ni-string-fwd
```

`cc-ni-scalar` performs shape and conversion checks before a typed store. A local aggregate copy instead requires matching descriptors and copies the aggregate extent. Static aggregate expression copies are rejected here.

## Walk children without losing the destination

For `struct Item item = {3, 7}`, the first child retains the object's base and adds
`tag`'s offset 0; the second adds `value`'s offset 8. Each child also
carries its own type, so the scalar path emits a one-byte store for 3 and
an eight-byte store for 7. The seven padding bytes are a gap between
addresses, not seven extra children to consume from the initializer.

Array children derive offsets from element stride, while record children use their field offsets (`forth-bootstrap/cc/118-cc-native-init.fth:178`):

```forth file=cc/118-cc-native-init.fth

: cc-ni-child-count
  ni-array @ if, ni-array @ exit, then,
  ni-desc @ cc-sd-union? if, [lit] 1 else, ni-desc @ cc-sd-field-count then, ;

: cc-ni-field-default ( rec -- handled? ) drop [lit] 0 ;
defer cc-ni-field-fwd
' cc-ni-field-default is cc-ni-field-fwd

: cc-ni-child
  ni-array @ if,
    ni-type @ ni-desc @ ni-inner @ [lit] 0
    ni-type @ ni-desc @ cc-nsize
    ni-inner @ if, ni-inner @ * then,
    ni-index @ * ni-offset @ + true cc-ni-value-fwd
  else,
    ni-desc @ ni-index @ cc-sd-field-rec
    dup cc-ni-field-fwd if, drop exit, then,
    dup cc-sf-type over cc-sf-desc
    [lit] 2 cc-npick cc-sf-array-len
    [lit] 3 cc-npick cc-sf-array-inner
    [lit] 4 cc-npick cc-sf-offset ni-offset @ +
    true cc-ni-value-fwd drop
  then, ;

```

`cc-ni-child-count` limits a union to its first member. `cc-ni-child` passes each child’s type, dimensions, and accumulated offset into recursive traversal. `cc-ni-field-default` reports that it did not handle a special field; `cc-ni-field-fwd` gives later field representations a place to intervene.

Brace elision requires the child walker to leave a separator for its enclosing list when its own destination is full (`forth-bootstrap/cc/118-cc-native-init.fth:203`):

```forth file=cc/118-cc-native-init.fth
: cc-ni-list
  [char] { cc-tok-punct? ni-brace !
  ni-brace @ if, cc-next-token-keep then,
  [lit] 0 ni-index !
  begin,
    [char] } cc-tok-punct? 0=
    ni-index @ cc-ni-child-count < and
  while,
    cc-ni-child [lit] 1 ni-index +!
    [char] , cc-tok-punct? if,
      ni-brace @ ni-index @ cc-ni-child-count < or if,
        cc-next-token-keep
      else, exit, then,
    else,
      ni-brace @ if,
        [char] } cc-tok-punct? 0= if, [lit] 225 cc-die then,
      else, exit, then,
    then,
  repeat,
  ni-brace @ if,
    [char] } cc-tok-punct? 0= if, [lit] 226 cc-die then,
    cc-next-token-keep
  then, ;

```

`cc-ni-list` tracks whether it consumed an opening brace. With explicit braces it requires the matching close; without them it returns as soon as the child sequence is complete. An explicit list that still has extra elements fails rather than writing beyond the object.

A character array needs lookahead to distinguish a braced string from an ordinary list of character values (`forth-bootstrap/cc/118-cc-native-init.fth:227`):

```forth file=cc/118-cc-native-init.fth
\ Character-array strings may optionally have a single pair of braces.
: cc-ni-char-array
  tok-kind @ tk-str = if, cc-ni-string-fwd exit, then,
  [char] { cc-tok-punct? if,
    cc-lex-state-size cc-alloc dup >r cc-lex-mark
    cc-next-token-keep
    tok-kind @ tk-str = if,
      r> drop cc-ni-string-fwd
      [char] , cc-tok-punct? if, cc-next-token-keep then,
      [char] } cc-tok-punct? 0= if, [lit] 223 cc-die then,
      cc-next-token-keep exit,
    then,
    r> cc-lex-reset
  then,
  [char] { cc-tok-punct? ni-nested @ or 0= if, [lit] 225 cc-die then,
  cc-ni-list ;

```

`cc-ni-char-array` commits to the string path only when it sees a string token. Otherwise it restores the token position and delegates to list traversal. The `ni-nested` flag permits the supported brace-elided nested case.

## Recurse through the initializer shape

Each recursive value saves the parent frame before unpacking its own array representation (`forth-bootstrap/cc/118-cc-native-init.fth:244`):

```forth file=cc/118-cc-native-init.fth
: cc-ni-value ( ty desc array inner offset nested? -- )
  cc-ni-frame @ >r
  [lit] 64 cc-alloc dup cc-ni-frame ! [lit] 64 cc-nzero
  ni-nested ! ni-offset ! ni-inner ! ni-array ! ni-desc ! ni-type !
  \ Re-enter the existing array traversal for a recursively typed element.
  ni-array @ 0= ni-type @ ty-base ty-array = and
  ni-type @ ty-ptr 0= and if,
    ni-desc @ dup cc-ad-type ni-type !
    dup cc-ad-count ni-array ! dup cc-ad-inner ni-inner !
    cc-ad-desc ni-desc !
  then,
  ni-array @ [lit] 0 > if,
    ni-inner @ 0= ni-type @ ty-ptr 0= and
    ni-type @ ty-size [lit] 1 = and if,
      cc-ni-char-array
    else,
      [char] { cc-tok-punct? ni-nested @ or 0= if, [lit] 225 cc-die then,
      cc-ni-list
    then,
  else,
    cc-ni-aggregate? if,
```

The remaining dispatch distinguishes aggregate lists, scalar braces, and scalar leaves before restoring the parent frame (`forth-bootstrap/cc/118-cc-native-init.fth:265`):

```forth file=cc/118-cc-native-init.fth
      [char] { cc-tok-punct? ni-nested @ or if,
        cc-ni-list
      else, cc-ni-scalar-fwd then,
    else,
      [char] { cc-tok-punct? if,
        cc-next-token-keep
        ni-type @ ni-desc @ [lit] 0 [lit] 0 ni-offset @ true cc-ni-value-fwd
        [char] , cc-tok-punct? if, cc-next-token-keep then,
        [char] } cc-tok-punct? 0= if, [lit] 227 cc-die then,
        cc-next-token-keep
      else, cc-ni-scalar-fwd then,
    then,
  then,
  r> cc-ni-frame ! ;
' cc-ni-value is cc-ni-value-fwd

```

Static routines need an ordered queue so program completion can emit their dispatcher (`forth-bootstrap/cc/118-cc-native-init.fth:281`):

```forth file=cc/118-cc-native-init.fth
: cc-ni-queue ( vaddr -- )
  [lit] 16 cc-alloc dup >r !
  [lit] 0 r@ [lit] 8 + !
  cc-ni-tail @ if, r@ cc-ni-tail @ [lit] 8 + ! else, r@ cc-ni-head ! then,
  r> cc-ni-tail ! ;
```

`cc-ni-value` always returns to its caller’s `cc-ni-frame`. An opaque scalar stays on the scalar path. `cc-ni-queue` appends a routine address to the pending list and handles its initially empty head. Designated initializers are outside this bounded parser; the accepted forms are positional lists, strings, and scalar expressions.

Persistent objects queue a routine, while local aggregates clear their destination before explicit values are stored (`forth-bootstrap/cc/118-cc-native-init.fth:286`):

```forth file=cc/118-cc-native-init.fth

: cc-native-initializer
  nc-top @ nc-static @ or cc-ni-static !
  cc-ni-static @ if,
    cc-emit-jmp-rel32-placeholder >r
    cc-here-vaddr cc-ni-queue
    true cc-native-static-init !
  else,
    nc-array @ nc-ty @ ty-base ty-struct = nc-ty @ ty-ptr 0= and or if,
      cc-ni-zero-object
    then,
  then,
  cc-next-token-keep
  nc-ty @ nc-desc @ nc-array @ nc-inner @ [lit] 0 [lit] 0 cc-ni-value
  cc-ni-static @ if,
    [lit] 0 cc-native-static-init !
    [lit] 195 cc-emit-byte
    r> cc-patch-rel32-to-here
  then, ;
' cc-native-initializer is cc-native-init-fwd
```

`cc-native-initializer` sets `cc-native-static-init` while compiling a static expression so the expression parser’s constant-category restrictions apply. It emits a jump around the routine, queues its address, emits its stores and return, then patches the jump. The queue changes when stores execute, not which C expressions are permitted.

The entry call can be resolved only after every static initializer routine has been queued (`forth-bootstrap/cc/118-cc-native-init.fth:306`):

```forth file=cc/118-cc-native-init.fth

: cc-ni-entry
  [lit] 0 cc-ni-head ! [lit] 0 cc-ni-tail !
  cc-emit-call-rel32-placeholder cc-ni-entry-patch ! ;
' cc-ni-entry is cc-native-init-entry-fwd

: cc-ni-finish
  cc-ni-entry-patch @ cc-patch-rel32-to-here
  cc-ni-head @
  begin, dup while,
    [lit] 232 cc-emit-byte
    dup @ cc-here-vaddr [lit] 4 + - cc-emit-4le
    [lit] 8 + @
  repeat, drop
  [lit] 195 cc-emit-byte ;
' cc-ni-finish is cc-native-init-finish-fwd
```

`cc-ni-entry` clears the queue and emits that call. `cc-ni-finish` patches it to a dispatcher that calls the queued routines in order and returns. The bindings replace the previously empty entry and finish hooks. Local initialization stays inline at the declaration.

## A finite Linux boundary

The private runtime is a set of emitted leaf functions, not a full C library. Each leaf obtains arguments from caller-owned stack slots and supplies the kernel operation named by its symbol. The source’s portable-libc comments describe the historical consumer; the later C runtime is taught in Chapter 43.

Runtime symbol registration uses stored C spellings so source calls can resolve to the emitted boundary (`forth-bootstrap/cc/119-cc-native-runtime.fth:1`):

```forth file=cc/119-cc-native-runtime.fth
\ 119-cc-native-runtime.fth — Linux AMD64 primitives for the native ABI.
\ Every argument occupies an eight-byte caller-owned stack slot. These
\ leaf functions have no frame: argument one is at rsp+8, not in rdi.
\ Portable libc supplies FILE, allocation, strings, stdio and formatting.
\ Only its kernel boundary is emitted here; no SysV libc shim is linked.

create cc-native-name-exit     s, exit
create cc-native-name-read     s, read
create cc-native-name-write    s, write
create cc-native-name-open     s, open
create cc-native-name-close    s, close
create cc-native-name-lseek    s, lseek
create cc-native-name-unlink   s, unlink
create cc-native-name-mkdir    s, mkdir
create cc-native-name-chmod    s, chmod
create cc-native-name-access   s, access
create cc-native-name-mprotect s, mprotect
create cc-native-name-time     s, time
create cc-native-name-gettimeofday s, gettimeofday

```

A kernel error must match the failure value expected by this boundary’s C caller (`forth-bootstrap/cc/119-cc-native-runtime.fth:21`):

```forth file=cc/119-cc-native-runtime.fth
\ cc-native-sysarg ( stack-byte-offset modrm -- )
\ MOV a full stack cell into a syscall argument register. Narrow C values
\ arrive extended by expression evaluation; pointers/size_t/off_t stay 64-bit.
: cc-native-sysarg
  [lit] 72 cc-emit-byte [lit] 139 cc-emit-byte
  cc-emit-byte [lit] 36 cc-emit-byte cc-emit-byte ;

\ cc-native-syscall ( syscall-number argument-count -- )
\ Linux returns -errno in rax. Portable libc tests fd == -1, so turn
\ [-4095,-1] into -1. This bootstrap boundary does not maintain errno.
\ An absent file therefore makes fopen fail
\ cleanly rather than allocating a FILE containing a negative errno.
: cc-native-syscall
  dup [lit] 0 > if, [lit] 8 [lit] 124 cc-native-sysarg then,
  dup [lit] 1 > if, [lit] 16 [lit] 116 cc-native-sysarg then,
  [lit] 2 > if, [lit] 24 [lit] 84 cc-native-sysarg then,
  [lit] 184 cc-emit-byte cc-emit-4le             \ mov eax, syscall-number
  [lit] 15 cc-emit-byte [lit] 5 cc-emit-byte     \ syscall
  [lit] 72 cc-emit-byte [lit] 61 cc-emit-byte
  [lit] 0 [lit] 4095 - cc-emit-4le              \ cmp rax, -4095
  [lit] 114 cc-emit-byte [lit] 7 cc-emit-byte    \ jb .ok (unsigned)
  [lit] 72 cc-emit-byte [lit] 199 cc-emit-byte [lit] 192 cc-emit-byte
  [lit] 0 1- cc-emit-4le                        \ mov rax, -1
  [lit] 195 cc-emit-byte ;                      \ .ok: ret
```

`cc-native-sysarg` emits a full-slot load into the selected syscall register. `cc-native-syscall` emits the operation, then maps the kernel error range from −4095 through −1 to −1. It does not maintain `errno`. The unsigned comparison leaves ordinary successful return values unchanged.

Registering return types before source prototypes prevents wide file positions and byte counts from being treated as `int` (`forth-bootstrap/cc/119-cc-native-runtime.fth:45`):

```forth file=cc/119-cc-native-runtime.fth

\ cc-native-primitive ( name-addr name-len return-base syscall argc -- )
\ Register the real return type before parsing source prototypes. In
\ particular read/write/lseek return signed LP64 long, never 32-bit int.
: cc-native-primitive
  >r >r [lit] 0 ty-make sk-func swap cc-here-vaddr cc-sym-add drop
  r> r> cc-native-syscall ;

```

The historical restricted profile keeps unavailable operation names beside their diagnostic state (`forth-bootstrap/cc/119-cc-native-runtime.fth:53`):

```forth file=cc/119-cc-native-runtime.fth
\ These three unavailable library paths are part of the measured seed-only
\ profile. Do not generalize this allow-list to arbitrary unresolved names.
\ Successful bootstrap builds must never execute one: each names the missing
\ operation on stderr and exits 125. Normal native mode does not define them.
create cc-native-name-localtime s, localtime
create cc-native-name-ldexp     s, ldexp
create cc-native-name-longjmp   s, longjmp
create cc-native-trap-prefix
  s, seed-forth [lit] 32 c, s, bootstrap: [lit] 32 c,
  s, unsupported [lit] 32 c,
here cc-native-trap-prefix - constant cc-native-trap-prefix-length
variable cc-native-trap-message
variable cc-native-trap-length
```

`cc-native-primitive` pairs registration with syscall emission. The unavailable names and diagnostic storage serve only the restricted historical profile.

## Reject execution of unavailable operations

An unavailable operation must fail visibly if control reaches it instead of returning a fabricated result (`forth-bootstrap/cc/119-cc-native-runtime.fth:66`):

```forth file=cc/119-cc-native-runtime.fth

: cc-native-emit-raw ( addr len -- )
  begin, dup while,
    over c@ cc-emit-byte swap 1+ swap 1-
  repeat, 2drop ;

: cc-native-unavailable ( name-addr name-len return-type -- )
  >r 2dup
  cc-here-vaddr cc-native-trap-message !
  cc-native-trap-prefix cc-native-trap-prefix-length cc-native-emit-raw
  cc-native-emit-raw [lit] 10 cc-emit-byte
  dup cc-native-trap-prefix-length 1+ + cc-native-trap-length !
  sk-func r> cc-here-vaddr cc-sym-add drop
  [lit] 184 cc-emit-byte [lit] 1 cc-emit-4le       \ mov eax, SYS_write
  [lit] 191 cc-emit-byte [lit] 2 cc-emit-4le       \ mov edi, stderr
  [lit] 72 cc-emit-byte [lit] 190 cc-emit-byte
  cc-native-trap-message @ cc-emit-8le            \ movabs rsi, message
  [lit] 186 cc-emit-byte cc-native-trap-length @ cc-emit-4le
  [lit] 15 cc-emit-byte [lit] 5 cc-emit-byte       \ syscall
  [lit] 184 cc-emit-byte [lit] 60 cc-emit-4le      \ mov eax, SYS_exit
  [lit] 191 cc-emit-byte [lit] 125 cc-emit-4le     \ mov edi, 125
  [lit] 15 cc-emit-byte [lit] 5 cc-emit-byte
  [lit] 15 cc-emit-byte [lit] 11 cc-emit-byte ;    \ ud2: never return

```

`cc-native-unavailable` emits the message followed by a function body that writes it to stderr and exits with status 125. The trailing invalid instruction prevents accidental fallthrough. This is the fail-closed bootstrap runtime: an accepted historical symbol does not imply an implemented operation.

The runtime installer keeps the supported syscall list separate from the conditional unavailable-operation list (`forth-bootstrap/cc/119-cc-native-runtime.fth:90`):

```forth file=cc/119-cc-native-runtime.fth
: cc-native-runtime
  cc-native-name-exit     [lit] 4 ty-void [lit] 60 [lit] 1 cc-native-primitive
  cc-native-name-read     [lit] 4 ty-long [lit] 0 [lit] 3 cc-native-primitive
  cc-native-name-write    [lit] 5 ty-long [lit] 1 [lit] 3 cc-native-primitive
  \ open's third stack slot contains mode for O_CREAT/O_TMPFILE. Linux
  \ ignores that slot for a two-argument open without those flags.
  cc-native-name-open     [lit] 4 ty-int [lit] 2 [lit] 3 cc-native-primitive
  cc-native-name-close    [lit] 5 ty-int [lit] 3 [lit] 1 cc-native-primitive
  cc-native-name-lseek    [lit] 5 ty-long [lit] 8 [lit] 3 cc-native-primitive
  cc-native-name-unlink   [lit] 6 ty-int [lit] 87 [lit] 1 cc-native-primitive
  cc-native-name-mkdir    [lit] 5 ty-int [lit] 83 [lit] 2 cc-native-primitive
  cc-native-name-chmod    [lit] 5 ty-int [lit] 90 [lit] 2 cc-native-primitive
  cc-native-name-access   [lit] 6 ty-int [lit] 21 [lit] 2 cc-native-primitive
  cc-native-name-mprotect [lit] 8 ty-int [lit] 10 [lit] 3 cc-native-primitive
  cc-native-name-time     [lit] 4 ty-long [lit] 201 [lit] 1 cc-native-primitive
  cc-native-name-gettimeofday [lit] 12 ty-int [lit] 96 [lit] 2 cc-native-primitive
  cc-bootstrap-floatbits @ if,
    cc-native-name-localtime [lit] 9 ty-struct [lit] 1 ty-make cc-native-unavailable
    cc-native-name-ldexp [lit] 5 ty-double [lit] 0 ty-make cc-native-unavailable
    cc-native-name-longjmp [lit] 7 ty-void [lit] 0 ty-make cc-native-unavailable
  then, ;
' cc-native-runtime is cc-native-runtime-fwd
```

`cc-native-runtime` registers the boundary and adds the unavailable bodies only when `cc-bootstrap-floatbits` is enabled. Normal native mode does not define those bodies. This bounded list is not permission to accept arbitrary unresolved names. Chapter 40 next changes output representation to objects and relocations.

## Try it

Run from the `forth-bootstrap` checkout root with the seed already built. The full loader includes the later extension layers. Its final line invokes the core entry, so `sed` removes that invocation while keeping its definitions; the small `storage-main` below selects the native program path. The load order and final-entry placement are specified in `forth-bootstrap/cc/compiler-layers.sh:2`. Compilation artifacts live in a `mktemp -d` directory, and the resulting program runs there. Do not run concurrently with another user of `/tmp/cc-out`. A checked move saves any existing output before compilation; cleanup restores it or reports the retained backup path if restoration fails.

<!-- tryit: expect "compiler exit: 0\nLP64\nprogram exit: 40" -->
```sh
(
set -o pipefail
probe_dir=$(mktemp -d /tmp/book-probe.XXXXXXXXXX) || exit "$?"
saved_output=0
if [ -e /tmp/cc-out ] || [ -L /tmp/cc-out ]; then
  if mv -T -- /tmp/cc-out "$probe_dir/saved-cc-out"; then
    saved_output=1
  else
    printf 'Backup failed; inspect /tmp/cc-out and %s\n' "$probe_dir" >&2
    exit 1
  fi
fi
cleanup() {
  status=$?
  trap - EXIT HUP INT TERM
  if ! rm -f -- /tmp/cc-out; then
    printf 'Cleanup failed; inspect /tmp/cc-out and %s\n' "$probe_dir" >&2
    exit 1
  fi
  if [ "$saved_output" -eq 1 ] &&
      ! mv -T -- "$probe_dir/saved-cc-out" /tmp/cc-out; then
    printf 'Restore failed; saved output retained at %s\n' "$probe_dir/saved-cc-out" >&2
    exit 1
  fi
  rm -rf -- "$probe_dir" || status=1
  exit "$status"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
layers=$(cc/compiler-layers.sh) || exit "$?"
cat forth/010-lib.fth $layers | sed '$d' > "$probe_dir/compiler.fth" || exit "$?"
cat >> "$probe_dir/compiler.fth" <<'FORTH' || exit "$?"
true cc-target-lp64 !
: storage-main
  cc-load-stdin cc-preprocess cc-out-init cc-globals-init
  cc-emit-elf-header cc-native-program cc-finalize-globals
  cc-finalize-elf cc-out-path cc-write-output bye ;
storage-main
FORTH
cat > "$probe_dir/storage.c" <<'C' || exit "$?"
long write(int fd, char *buf, long count);
struct Item { char tag; long value; } item = { 3, 7 };
char label[] = "LP64\n";
int main(void) {
  write(1, label, sizeof(label) - 1);
  return sizeof(long) + sizeof(label) + sizeof(item)
       + item.tag + item.value;
}
C
compiler_status=0
cat "$probe_dir/compiler.fth" "$probe_dir/storage.c" | ./seed-forth || compiler_status=$?
printf 'compiler exit: %s\n' "$compiler_status"
test "$compiler_status" -eq 0 || exit "$compiler_status"
mv -T -- /tmp/cc-out "$probe_dir/storage" || exit "$?"
chmod +x "$probe_dir/storage" || exit "$?"
program_status=0
(cd "$probe_dir" && ./storage) || program_status=$?
printf 'program exit: %s\n' "$program_status"
test "$program_status" -eq 40
)
```

Observed output:

```text
compiler exit: 0
LP64
program exit: 40
```

The printed bytes come from the initialized character array. The exit sum combines `sizeof(long)` = 8, `sizeof(label)` = 6, `sizeof(item)` = 16, and initialized fields 3 and 7. The record size includes the alignment gap before its `long` field. This exercises native declarations, inferred array extent, aligned record storage, queued static initialization, private entry, and the emitted `write` boundary.

## Exercise

Hints and feedback are in [Appendix H](66-exercise-feedback.md#chapter-39-object-layout-and-initializer-timing).

**Trace (easy).** Follow `cc-nadd-field` for `struct Item` in the checkpoint. Explain why the `long` member does not immediately follow the `char`, and where the final record extent is rounded.

**Verify (moderate).** Move `label` and `item` inside `main`, keeping their initializers. Predict whether the output and exit sum change. Run the modified checkpoint, then explain which initialization code stays inline instead of entering `cc-ni-queue`.

