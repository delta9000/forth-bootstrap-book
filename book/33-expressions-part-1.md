# Chapter 33 — Expressions: precedence

`2 + 3 * 4` needs the multiplication to finish before the addition can use its result. A precedence cascade makes that order emerge from parser calls, without building an expression tree. The resulting binary-expression compiler connects tokens to arithmetic, comparison, bitwise operations, and short-circuit branches.

## The shape of the cascade

Each level asks the next-tighter level for an operand, then consumes its own operators in a loop. Call order determines binding; the operator table selects the operation within a level. The root block places these levels between operand parsing and assignment (`forth-bootstrap/cc/100-cc-expr.fth:1`):

```forth file=cc/100-cc-expr.fth
<<expr-header>>
<<expr-fwd-refs>>
<<expr-tok-tests>>
<<expr-lvalue>>
<<expr-struct-field>>
<<expr-array-index>>
<<expr-call>>
<<expr-primary>>
<<expr-unary>>
<<expr-binops>>
<<expr-mul>>
<<expr-add>>
<<expr-shift>>
<<expr-rel>>
<<expr-eq>>
<<expr-bit>>
<<expr-log>>
<<expr-ternary>>
<<expr-assign>>
<<expr-top>>
```

This is the assembly recipe for the file, not its literal header. The operand and assignment chunks belong to Chapter 34; `expr-call` belongs to Chapter 37. Their names here establish placement, not ownership.

The grammar makes each binary operand a call to a tighter production (`forth-bootstrap/cc/100-cc-expr.fth:1`):

```forth chunk=expr-header
\ 100-cc-expr.fth — recursive-descent expression parser for the C subset.
\ Emits code that leaves the expression's value in rdi.  Uses 090-cc-emit.fth's
\ instruction encoders.
\
\ Expression grammar, loosest-binding first (one cc-parse-LEVEL word each):
\   expr    := assign                                 \ then materialize
\   assign  := ternary (ASSIGN-OP assign)?            \ = += -= *= /= %= <<= >>= &= |= ^=
\   ternary := log-or ('?' assign ':' assign)?
\   log-or  := log-and ('||' log-and)*
\   log-and := bit-or ('&&' bit-or)*
\   bit-or  := bit-xor ('|' bit-xor)*
\   bit-xor := bit-and ('^' bit-and)*
\   bit-and := eq ('&' eq)*
\   eq      := rel (('=='|'!=') rel)*
\   rel     := shift (('<'|'<='|'>'|'>=') shift)*
\   shift   := add (('<<'|'>>') add)*
\   add     := mul (('+'|'-') mul)*
\   mul     := unary (('*'|'/'|'%') unary)*
```

At the bottom, unary and primary parsing supply values; the dependency comment identifies the token interface used throughout (`forth-bootstrap/cc/100-cc-expr.fth:19`):

```forth chunk=expr-header
\   unary   := ('*'|'&'|'-'|'!'|'~'|'++'|'--') unary | 'sizeof' '(' ... ')'
\            | primary
\   primary := (NUMBER | CHAR | STRING | IDENT | IDENT '(' args ')'
\               | IDENT '[' expr ']' | '(' expr ')')
\              ('.' IDENT | '->' IDENT | '[' expr ']' | '++' | '--')*
\
\ Tokens come from the lexer's interface (050-cc-lex.fth): cc-next-token-keep
\ reads the next one, and cc-putback-token hands the current one back when a
\ parser has read one token too many.
\
\ Depends on 010-lib.fth, 030-cc-io.fth, 050-cc-lex.fth, 060-cc-types.fth, 070-cc-sym.fth,
\ 090-cc-emit.fth.

```

## One token of putback

After `cc-parse-mul` consumes `a * b`, it reads the following `+` and returns it through the lexer’s putback interface (Chapter 29). The additive parser can then consume that same operator. A level relinquishes a token whenever it cannot use it.

Token tests must check the kind as well as the payload, so a numeric value cannot be mistaken for punctuation (`forth-bootstrap/cc/100-cc-expr.fth:57`):

```forth chunk=expr-tok-tests
\ ===========================================================================
\ Token tests.  Is the current token this punctuation, or this keyword?
\ ===========================================================================

\ cc-tok-punct? ( code -- f )  True if the current token is punctuation code
\ (a character such as [char] ( or a pt-* constant such as pt-arrow).
: cc-tok-punct?  tok-kind @ tk-punct =  swap tok-num @ =  and ;

\ cc-tok-kw? ( id -- f )  True if the current token is the keyword id (kw-*).
: cc-tok-kw?  tok-kind @ tk-kw =  swap tok-kw-id @ =  and ;

```

`cc-tok-punct?` compares a character or `pt-*` code with `tok-num`; `cc-tok-kw?` compares a keyword ID with `tok-kw-id`. Both leave the token in place. They answer a question about the current token rather than consuming another one.

## Forward references for mutual recursion

Parentheses re-enter expression parsing, while a cast needs a type parser defined outside this file. The forward slots separate those call relationships from source order.

Declare the recursive entry points before their callers, together with the guard used when runtime lowering is forbidden (`forth-bootstrap/cc/100-cc-expr.fth:32`):

```forth chunk=expr-fwd-refs
\ ===========================================================================
\ Forward references.  The grammar is recursive: a primary's '(' expr ')'
\ and a call's arguments re-enter the whole grammar, and the ternary's arms
\ parse assignments.  cc-parse-expr and cc-parse-assign are defined near the
\ end of this file, so the words before them call these deferred words
\ (010-lib.fth), which the last lines of the file fill in.  A cast needs
\ the type parser of 110-cc-decl.fth, which fills in cc-try-cast-fwd.
\ ===========================================================================

defer cc-parse-expr-fwd                           \ runs cc-parse-expr
defer cc-parse-comma-fwd                          \ native comma expressions, no materialize
defer cc-parse-assign-fwd                         \ runs cc-parse-assign
defer cc-try-cast-fwd                             \ runs cc-try-cast (110)
defer cc-parse-unary-fwd                          \ runs cc-parse-unary
defer cc-sizeof-type-start-fwd                    \ current token starts a type?
defer cc-sizeof-type-fwd                          \ current type token -> ty desc
defer cc-parse-const-fwd                          \ constant expression evaluator
variable cc-expr-unevaluated
variable cc-native-static-init                    \ restrict runtime lowering to static constants

: cc-check-static-init
  cc-native-static-init @ cc-expr-unevaluated @ 0= and if,
    [lit] 219 cc-die
  then, ;

```

`cc-parse-expr-fwd`, `cc-parse-assign-fwd`, and `cc-parse-unary-fwd` reach their respective grammar entries. `cc-parse-comma-fwd` reaches comma expressions without forcing a value load. Chapter 34 supplies those parsers and the initial constant-expression target of `cc-parse-const-fwd`; Chapter 45 develops typed constants.

`cc-try-cast-fwd` delegates a possible cast. `cc-sizeof-type-start-fwd` asks whether the current token starts a type, and `cc-sizeof-type-fwd` obtains its type and descriptor. Chapter 35 supplies declaration-side type parsing.

`cc-native-static-init` requests the static-initializer restriction. `cc-expr-unevaluated` suspends evaluation while syntax is still parsed. `cc-check-static-init` rejects a runtime operation when the restriction is active and the expression is evaluated. Chapter 39 supplies the initializer context.

## The operator table

An operator has separate actions at compile time and at runtime. Its evaluator computes a Forth value; its emitter writes machine instructions. Keeping both in one row lets later constant parsing reuse the operator identities without executing generated code.

### Arithmetic helpers

The small handlers have these contracts:

| Input → result | Words |
|---|---|
| value → negation, complement, magnitude | `cc-negate`, `cc-invert`, `cc-abs` |
| pair of values → bitwise exclusive-or | `cc-xor` |
| Forth flag → C truth value | `cc-flag` |
| divisor → checked divisor | `cc-divisor` |
| dividend, divisor → signed quotient or remainder | `cc-div`, `cc-mod` |
| exponent → power of two | `cc-pow2` |
| value, count → left or arithmetic-right shift | `cc-shl`, `cc-sar` |
| pair of values → C comparison result | `cc-lt`, `cc-gt`, `cc-le`, `cc-ge`, `cc-eq`, `cc-ne` |

Constant arithmetic first needs signed and Boolean adapters around the available Forth operations (`forth-bootstrap/cc/100-cc-expr.fth:1579`):

```forth chunk=expr-binops
\ ===========================================================================
\ Arithmetic at compile time
\ ===========================================================================
\ A constant expression (an array size, a case label, an #if line) is
\ computed while compiling, so each operator also needs a Forth word that
\ does what its instructions do at run time, on two 64-bit values.  The
\ seed's / is unsigned and it has no shift or xor, so the signed
\ versions are built here.

: cc-negate  [lit] 0 swap - ;                     ( n -- -n )
: cc-invert  dup nand ;                           ( n -- ~n )
: cc-xor     2dup or >r and cc-invert r> and ;     ( a b -- a^b )
: cc-flag    0= 1+ ;                              \ ( f -- 1|0 ): C truth
: cc-abs     dup 0< if, cc-negate then, ;         ( n -- |n| )

```

Signed division operates on magnitudes, then restores the quotient’s sign or the dividend’s sign for the remainder (`forth-bootstrap/cc/100-cc-expr.fth:1594`):

```forth chunk=expr-binops
\ cc-divisor ( b -- b )  Die with 124 if a constant divisor is 0.
: cc-divisor  dup 0= if, [lit] 124 cc-die then, ;

\ cc-div ( a b -- q )  Signed division, truncating toward zero like idiv.
\ cc-mod ( a b -- r )  Its remainder, which takes the sign of a.
: cc-div
  cc-divisor
  2dup cc-xor 0< >r  cc-abs swap cc-abs swap /  r> if, cc-negate then, ;
: cc-mod
  cc-divisor
  over 0< >r  cc-abs swap cc-abs swap  2dup / * -  r> if, cc-negate then, ;

```

`cc-divisor` rejects a zero divisor before either calculation. `cc-div` uses the sign of the operands’ exclusive-or to decide whether to negate the quotient; `cc-mod` remembers only the dividend’s sign. These are the baseline evaluators, not the checked typed arithmetic developed in Chapter 45.

A power-of-two factor implements shifting; complementing a negative input before division and afterwards preserves arithmetic-right-shift behavior (`forth-bootstrap/cc/100-cc-expr.fth:1606`):

```forth chunk=expr-binops
\ cc-pow2 ( n -- 2^n )
: cc-pow2
  [lit] 1 swap
  begin, dup while, swap dup + swap 1- repeat,
  drop ;
\ cc-shl ( a n -- a<<n )   cc-sar ( a n -- a>>n ), the sign bit copied in.
: cc-shl  cc-pow2 * ;
: cc-sar
  over 0< if,
    swap cc-invert swap cc-pow2 / cc-invert
  else,
    cc-pow2 /
  then, ;

```

The comparison adapters return normalized C truth values (`forth-bootstrap/cc/100-cc-expr.fth:1620`):

```forth chunk=expr-binops
\ The comparisons answer C's 1 or 0.
: cc-lt  <  cc-flag ;
: cc-gt  >  cc-flag ;
: cc-le  <= cc-flag ;
: cc-ge  >= cc-flag ;
: cc-eq  =  cc-flag ;
: cc-ne  <> cc-flag ;

```

### Row layout and construction

The table describes membership, not the recursive call order. Changing a `level-*` label alone does not change which parser supplies an operand.

The row contract also reserves a compound-assignment key so Chapter 34 can reuse the operation (`forth-bootstrap/cc/100-cc-expr.fth:1628`):

```forth chunk=expr-binops
\ ===========================================================================
\ The binary-operator table
\ ===========================================================================
\ Eight levels of the grammar, mul down to bit-or, have one shape: parse an
\ operand at the next-tighter level, then, while the next token is one of
\ this level's operators, parse another operand and combine the two.  Only
\ the operators and the instructions that combine differ, so those live in
\ this table, one row of five cells per operator:
\
\   op        the operator's punct code (tok-num)
\   compound  the code of its compound assignment (`+` has `+=`); 0 if none
\   level     which level parses it (level-mul .. level-bit-or)
\   emitter   xt of the 090 word that emits rdi := rdi OP rcx
\   evaluator xt of the word above that computes a OP b now
\
\ Each level's parser looks its operators up by op; cc-parse-assign looks
\ `+=` and the rest up by compound, so `a + b` and `a += b` share an
\ emitter.  A row whose op is 0 ends the table.

```

Named fields let a consumer select the operator, its grammar level, or either execution token (`forth-bootstrap/cc/100-cc-expr.fth:1647`):

```forth chunk=expr-binops
[lit] 1 constant level-mul                        \ * / %
[lit] 2 constant level-add                        \ + -
[lit] 3 constant level-shift                      \ << >>
[lit] 4 constant level-rel                        \ < > <= >=
[lit] 5 constant level-eq                         \ == !=
[lit] 6 constant level-bit-and                    \ &
[lit] 7 constant level-bit-xor                    \ ^
[lit] 8 constant level-bit-or                     \ |

[lit]  0 constant bo-op                           \ byte offsets within a row
[lit]  8 constant bo-compound
[lit] 16 constant bo-level
[lit] 24 constant bo-emitter
[lit] 32 constant bo-eval
[lit] 40 constant bo-size

```

`level-mul`, `level-add`, `level-shift`, `level-rel`, and `level-eq` identify arithmetic and comparison groups. `level-bit-and`, `level-bit-xor`, and `level-bit-or` identify the bitwise groups.

`bo-op` addresses the punctuation key; `bo-compound` addresses its assignment twin. `bo-level` selects the owning group. `bo-emitter` and `bo-eval` select runtime emission and compile-time evaluation respectively. `bo-size` advances to the next row.

`cc-binop,` stores the supplied keys, then reads the emitter and evaluator names from the input to construct `cc-binops` (`forth-bootstrap/cc/100-cc-expr.fth:1663`):

```forth chunk=expr-binops
\ cc-binop, ( op compound level "emitter" "evaluator" -- )  Lay down one
\ row; the emitter's and the evaluator's names follow in the input.
: cc-binop,  rot , swap , ,  ' ,  ' , ;

create cc-binops
\ op          compound       level                  emitter                evaluator
char *      pt-star-eq     level-mul      cc-binop, cc-emit-imul-rdi-rcx   *
char /      pt-slash-eq    level-mul      cc-binop, cc-emit-idiv-quotient  cc-div
char %      pt-percent-eq  level-mul      cc-binop, cc-emit-idiv-remainder cc-mod
char +      pt-plus-eq     level-add      cc-binop, cc-emit-add-rdi-rcx    +
char -      pt-minus-eq    level-add      cc-binop, cc-emit-sub-rdi-rcx    -
pt-shl      pt-shl-eq      level-shift    cc-binop, cc-emit-shl-rdi-cl     cc-shl
pt-shr      pt-shr-eq      level-shift    cc-binop, cc-emit-sar-rdi-cl     cc-sar   \ signed
char <      [lit] 0        level-rel      cc-binop, cc-emit-cmp-lt         cc-lt
char >      [lit] 0        level-rel      cc-binop, cc-emit-cmp-gt         cc-gt
pt-le       [lit] 0        level-rel      cc-binop, cc-emit-cmp-le         cc-le
pt-ge       [lit] 0        level-rel      cc-binop, cc-emit-cmp-ge         cc-ge
pt-eq-eq    [lit] 0        level-eq       cc-binop, cc-emit-cmp-eq         cc-eq
pt-bang-eq  [lit] 0        level-eq       cc-binop, cc-emit-cmp-ne         cc-ne
char &      pt-amp-eq      level-bit-and  cc-binop, cc-emit-and-rdi-rcx    and
char ^      pt-caret-eq    level-bit-xor  cc-binop, cc-emit-xor-rdi-rcx    cc-xor
char |      pt-pipe-eq     level-bit-or   cc-binop, cc-emit-or-rdi-rcx     or
[lit] 0 ,                                         \ end of table

```

The final zero operator is a sentinel. The default division, comparison, and right-shift rows select signed emitters; the native dispatch below can replace that choice for unsigned operands.

### Finding an operator

A search takes a field as well as a key. Binary parsing searches by punctuation; assignment can search by the compound form.

`cc-binop-row` walks until either its selected field matches or the sentinel ends the search (`forth-bootstrap/cc/100-cc-expr.fth:1689`):

```forth chunk=expr-binops
\ cc-binop-row ( key field -- row | 0 )  The first row whose cell at byte
\ offset field holds key, or 0 when no row does.
: cc-binop-row
  >r cc-binops                                    ( key row ; R: field )
  begin,
    dup bo-op + @                                 \ stop at the end row
  while,
    2dup r@ + @ = if,                             ( key row )
      nip r> drop exit,                           \ found: answer the row
    then,
    bo-size +
  repeat,
  2drop r> drop [lit] 0 ;

```

`cc-binop?` admits a token only when its row belongs to the requested level (`forth-bootstrap/cc/100-cc-expr.fth:1704`):

```forth chunk=expr-binops
\ cc-binop? ( level -- row | 0 )  Read the next token.  If it is one of
\ this level's operators, answer its row; otherwise 0, and the caller
\ puts the token back.
: cc-binop?
  cc-next-token-keep
  tok-kind @ tk-punct <> if,
    drop [lit] 0 exit,                            \ not an operator at all
  then,
  tok-num @ bo-op cc-binop-row                    ( level row | level 0 )
  dup 0= if,
    nip exit,                                     \ no row: answer 0
  then,
  swap over bo-level + @ = if,                    ( row )
    exit,                                         \ ours: answer the row
  then,
  drop [lit] 0 ;                                  \ another level's operator

```

Failure leaves the token available for putback by the caller. Finding an operator in the table is insufficient: a multiplication parser must also reject an addition row.

### Preserving operand types

The native path needs facts about both operands after recursive parsing has finished. It carries the left facts across the right parse, then copies them into temporary cells for the operation. The type encodings themselves are unchanged (Chapter 30).

Keep the completed operands’ metadata separate from the parser’s current-expression state (`forth-bootstrap/cc/100-cc-expr.fth:1718`):

```forth chunk=expr-binops
\ Native arithmetic preserves type information and applies pointer scaling.
\ These temporary cells are only used after recursive operand parsing ends.
variable cc-expr-left-qualified
variable cc-expr-right-qualified
variable cc-expr-left-type
variable cc-expr-left-desc
variable cc-expr-right-type
variable cc-expr-right-desc
variable cc-expr-left-inner
variable cc-expr-left-null
variable cc-expr-right-null
variable cc-expr-right-inner
variable cc-expr-common
variable cc-expr-op-row

```

The `cc-expr-left-type` and `cc-expr-right-type` cells hold encoded types; their `-desc` partners hold descriptors. `cc-expr-left-inner` and `cc-expr-right-inner` retain array row widths. The `-null` pair records null-constant status, and the `-qualified` pair retains qualification. `cc-expr-common` holds the selected result/conversion type; `cc-expr-op-row` holds the operator row.

Promotion first widens small integer operands, while the equal-width long-long case preserves rank and signedness (`forth-bootstrap/cc/100-cc-expr.fth:1733`):

```forth chunk=expr-binops
: cc-expr-promote                                ( ty -- ty' )
  dup ty-ptr if, exit, then,
  dup ty-size [lit] 4 < if, drop ty-int [lit] 0 ty-make then, ;

\ Equal-size operands differ only in rank and signedness. Long long ranks
\ above every other eight-byte kind, so either long long operand makes the
\ result long long, unsigned when either operand is unsigned (C99 6.3.1.8).
: cc-expr-long-long-common                       ( left right -- ty )
  ty-unsigned? swap ty-unsigned? or if, ty-ullong else, ty-llong then,
  [lit] 0 ty-make ;

```

`cc-expr-promote` leaves pointers alone. `cc-expr-long-long-common` selects unsigned long long if either operand is unsigned, otherwise signed long long.

The default common-type policy promotes both operands, prefers a pointer or wider type, then resolves equal-width rank and unsignedness (`forth-bootstrap/cc/100-cc-expr.fth:1744`):

```forth chunk=expr-binops
: cc-expr-common-type-default                            ( left right -- ty )
  cc-expr-promote swap cc-expr-promote swap
  over ty-ptr if, drop exit, then,
  dup ty-ptr if, nip exit, then,
  2dup ty-size swap ty-size > if, nip exit, then,
  2dup ty-size swap ty-size < if, drop exit, then,
  over ty-long-long? over ty-long-long? or if,
    cc-expr-long-long-common exit,
  then,
  dup ty-unsigned? if, nip else, drop then, ;

defer cc-expr-common-type
' cc-expr-common-type-default is cc-expr-common-type

```

`cc-expr-common-type` is the replaceable entry point, initially bound to `cc-expr-common-type-default`. This describes the policy implemented here; it does not establish that every possible C operand pair is valid.

Snapshotting after recursion protects the left operand from the right parser’s updates (`forth-bootstrap/cc/100-cc-expr.fth:1758`):

```forth chunk=expr-binops
: cc-expr-save-types                             ( left-ty left-desc right-ty right-desc -- )
  cc-expr-right-desc ! cc-expr-right-type !
  cc-expr-left-desc ! cc-expr-left-type !
  cc-expr-left-type @ cc-expr-right-type @ cc-expr-common-type cc-expr-common ! ;

: cc-expr-save-native-types ( left-ty left-desc left-inner left-null qualified -- )
  cc-expr-left-qualified !
  cc-last-expr-qualified @ cc-expr-right-qualified !
  cc-expr-left-null ! cc-last-expr-null @ cc-expr-right-null !
  cc-expr-left-inner !
  cc-last-expr-array-inner @ cc-expr-right-inner !
  cc-last-expr-type @ cc-last-struct-desc @ cc-expr-save-types ;

```

`cc-expr-save-types` stores the type/descriptor pairs and computes their common type. `cc-expr-save-native-types` adds qualification, null status, and inner width, taking the left facts from its arguments and the right facts from the current-expression cells.

### Pointer steps and result descriptors

A pointer operation must retain both the pointed-to layout and the amount by which an integer offset advances it. These helpers choose that information from the saved operand facts.

`cc-expr-common-inner` keeps the chosen pointer’s row width, while `cc-expr-left-step` and `cc-expr-right-step` multiply pointee size by any saved inner width (`forth-bootstrap/cc/100-cc-expr.fth:1771`):

```forth chunk=expr-binops
: cc-expr-common-inner                           ( -- row-width )
  cc-expr-common @ ty-ptr if,
    cc-expr-left-type @ cc-expr-common @ = if,
      cc-expr-left-inner @
    else, cc-expr-right-inner @ then,
  else, [lit] 0 then, ;

: cc-expr-left-step
  cc-expr-left-type @ cc-expr-left-desc @ cc-expr-pointee-size
  cc-expr-left-inner @ if, cc-expr-left-inner @ * then, ;
: cc-expr-right-step
  cc-expr-right-type @ cc-expr-right-desc @ cc-expr-pointee-size
  cc-expr-right-inner @ if, cc-expr-right-inner @ * then, ;

```

`cc-expr-common-desc` preserves the matching descriptor for a struct, function, or array base and returns zero for other bases (`forth-bootstrap/cc/100-cc-expr.fth:1785`):

```forth chunk=expr-binops
: cc-expr-common-desc                            ( -- desc )
  cc-expr-common @ ty-base dup ty-struct = over ty-func = or swap ty-array = or if,
    cc-expr-left-type @ cc-expr-common @ = if,
      cc-expr-left-desc @
    else, cc-expr-right-desc @ then,
  else, [lit] 0 then, ;

```

### Selecting the native operation

Unsigned division, remainder, comparisons, and right shift need different instructions from the default table rows.

`cc-native-binop-emit-default` checks the common type before falling back to the row’s emitter (`forth-bootstrap/cc/100-cc-expr.fth:1792`):

```forth chunk=expr-binops
: cc-native-binop-emit-default                           ( -- )
  cc-expr-common @ ty-unsigned? if,
    cc-expr-op-row @ bo-op + @
    dup [char] / = if, drop cc-emit-udiv-quotient exit, then,
    dup [char] % = if, drop cc-emit-udiv-remainder exit, then,
    dup pt-shr = if, drop cc-emit-shr-rdi-cl exit, then,
    dup [char] < = if, drop cc-emit-cmp-ult exit, then,
    dup pt-le = if, drop cc-emit-cmp-ule exit, then,
    dup [char] > = if, drop cc-emit-cmp-ugt exit, then,
    dup pt-ge = if, drop cc-emit-cmp-uge exit, then,
    drop
  then,
  cc-expr-op-row @ bo-emitter + @ execute ;

defer cc-native-binop-emit
' cc-native-binop-emit-default is cc-native-binop-emit

```

The `cc-native-binop-emit` slot permits a later numeric layer to replace that dispatch. The table remains the default for operations whose instruction is unchanged by signedness.

Array-related policy has separate extension slots so binary, compound, and conditional expressions can share this machinery (`forth-bootstrap/cc/100-cc-expr.fth:1809`):

```forth chunk=expr-binops
: cc-array-binop-default ;
defer cc-array-binop-fwd
' cc-array-binop-default is cc-array-binop-fwd
: cc-array-compound-default ;
defer cc-array-compound-fwd
' cc-array-compound-default is cc-array-compound-fwd
: cc-array-ternary-default ;
defer cc-array-ternary-fwd
' cc-array-ternary-default is cc-array-ternary-fwd
```

`cc-array-binop-fwd`, `cc-array-compound-fwd`, and `cc-array-ternary-fwd` initially call the empty `cc-array-binop-default`, `cc-array-compound-default`, and `cc-array-ternary-default`. They perform no validation in this binding. The binary application calls its hook after saving operand facts; Chapter 34 owns the compound and conditional callers.

### Applying a typed operator

The native fold combines scaling, conversion, and emission after both operands have been parsed. Its stack comment omits the saved qualification argument consumed by `cc-expr-save-native-types`; the level parsers below supply that argument.

Save the row and operand facts, select the promoted left type for a shift, and scale an integer right operand when the left is a pointer (`forth-bootstrap/cc/100-cc-expr.fth:1818`):

```forth chunk=expr-binops
: cc-native-binop-apply                          ( left-ty left-desc left-inner left-null row -- )
  cc-expr-op-row !
  cc-emit-materialize
  cc-expr-save-native-types cc-array-binop-fwd
  cc-expr-op-row @ bo-level + @ level-shift = if,
    cc-expr-left-type @ cc-expr-promote cc-expr-common !
  then,
  cc-expr-op-row @ bo-level + @ level-add = if,
    cc-expr-left-type @ ty-ptr
    cc-expr-right-type @ ty-ptr 0= and if,
      cc-expr-left-step cc-emit-scale-rdi
    then,
  then,
  cc-emit-mov-rcx-rdi cc-emit-pop-rdi
```

After restoring the left value, pointer-on-the-right addition scales the integer left value before conversion and emission (`forth-bootstrap/cc/100-cc-expr.fth:1832`):

```forth chunk=expr-binops
  cc-expr-op-row @ bo-op + @ [char] + = if,
    cc-expr-left-type @ ty-ptr 0=
    cc-expr-right-type @ ty-ptr [lit] 0 <> and if,
      cc-expr-right-step cc-emit-scale-rdi
    then,
  then,
  cc-expr-left-type @ cc-expr-common @ cc-emit-convert-value
  cc-expr-right-type @ cc-expr-common @ cc-emit-convert-right
  cc-native-binop-emit
```

Pointer subtraction converts a byte difference to an element difference, while comparisons publish an integer result (`forth-bootstrap/cc/100-cc-expr.fth:1841`):

```forth chunk=expr-binops
  cc-expr-op-row @ bo-op + @ [char] - = if,
    cc-expr-left-type @ ty-ptr cc-expr-right-type @ ty-ptr and if,
      cc-expr-left-step
      dup [lit] 1 <> if,
        cc-emit-push-rdi cc-emit-mov-rdi-int
        cc-emit-mov-rcx-rdi cc-emit-pop-rdi cc-emit-idiv-quotient
      else, drop then,
      ty-long [lit] 0 ty-make cc-expr-common !
    then,
  then,
  cc-expr-op-row @ bo-level + @
  dup level-rel = swap level-eq = or if,
    ty-int [lit] 0 ty-make cc-expr-common !
  then,
  cc-expr-common @ cc-emit-convert-rdi
  cc-expr-common @ cc-expr-common-desc cc-mark-typed-value
  cc-expr-common @ ty-ptr if,
    cc-expr-left-qualified @ cc-expr-right-qualified @ or cc-last-expr-qualified !
  then,
  cc-expr-common-inner cc-last-expr-array-inner ! ;

```

The final marking preserves the selected descriptor, combines pointer qualification, and propagates the common inner width. Those facts let the enclosing expression consume the result without recovering its history.

The baseline `cc-binop-apply` needs only the saved left value, the current right value, and the row’s emitter (`forth-bootstrap/cc/100-cc-expr.fth:1865`):

```forth chunk=expr-binops
\ cc-binop-apply ( row -- )  The left operand is pushed and the right one
\ is in rdi.  Materialize the right, move it to rcx, pop the left into rdi,
\ emit the row's operation, and mark the result a plain value.
: cc-binop-apply
  cc-emit-materialize                             \ right must be a value
  cc-emit-mov-rcx-rdi                             \ rcx = right
  cc-emit-pop-rdi                                 \ rdi = left
  bo-emitter + @ execute                          \ rdi = left OP right
  cc-mark-not-lvalue ;

```

Its machine-code sequence moves the right value to `rcx`, restores the left into `rdi`, and emits `left OP right`. Materialization requests a value from a possibly pending address; marking clears assignability. Chapter 34 owns those mechanisms.

## The level template: `cc-parse-mul`

Call this repeated sequence the **binary fold**: parse left, preserve left, parse right, restore left, apply the operator. The Forth parser is executing during compilation; its emitted pushes and pops execute in the resulting program.

The multiplicative level repeats the binary fold while the lookahead row belongs to `level-mul` (`forth-bootstrap/cc/100-cc-expr.fth:1872`):

```forth chunk=expr-mul
\ ===========================================================================
\ cc-parse-mul: unary (('*'|'/'|'%') unary)*
\ ===========================================================================

: cc-parse-mul
  cc-parse-unary
  begin,
    level-mul cc-binop? dup                       ( row row | 0 0 )
  while,
    >r                                            ( ; R: row )
    cc-emit-materialize                           \ left must be a value
    cc-target-lp64 @ if,
      cc-last-expr-type @ cc-last-struct-desc @ cc-last-expr-array-inner @ cc-last-expr-null @ cc-last-expr-qualified @
    then,
    cc-emit-push-rdi                              \ save left
    cc-parse-unary                                \ rdi = right
    r> cc-target-lp64 @ if, cc-native-binop-apply else, cc-binop-apply then,
                                                  \ rdi = left OP right
  repeat,
  drop                                            \ cc-binop?'s 0
  cc-putback-token ;                              \ we read one too many

```

`cc-parse-unary` supplies an operand. `cc-binop? dup` keeps the row while the loop tests whether it exists. Inside the loop, `>r` protects that row across recursive parsing; `cc-emit-push-rdi` preserves the generated program’s left value.

With the native target enabled, the parser also saves the left operand’s metadata on the Forth data stack. After the right parse, it passes the restored row to the selected apply word. Another iteration uses the result as its left operand. On failure, `drop` removes the failed lookup result and putback returns the unaccepted token.

## `cc-parse-add`: just like `mul`, looser

Addition uses a complete multiplicative expression as each operand. That call boundary, rather than an arithmetic comparison of level numbers, makes multiplication bind tighter.

The additive binary fold changes the operand parser and the accepted row group (`forth-bootstrap/cc/100-cc-expr.fth:1894`):

```forth chunk=expr-add
\ ===========================================================================
\ cc-parse-add: mul (('+'|'-') mul)*
\ ===========================================================================

: cc-parse-add
  cc-parse-mul
  begin,
    level-add cc-binop? dup                       ( row row | 0 0 )
  while,
    >r                                            ( ; R: row )
    cc-emit-materialize                           \ left must be a value
    cc-target-lp64 @ if,
      cc-last-expr-type @ cc-last-struct-desc @ cc-last-expr-array-inner @ cc-last-expr-null @ cc-last-expr-qualified @
    then,
    cc-emit-push-rdi                              \ save left
    cc-parse-mul                                  \ rdi = right
    r> cc-target-lp64 @ if, cc-native-binop-apply else, cc-binop-apply then,
                                                  \ rdi = left OP right
  repeat,
  drop                                            \ cc-binop?'s 0
  cc-putback-token ;                              \ we read one too many

```

The loop also gives **left associativity**. For `a - b - c`, it emits the subtraction of `b` before it begins the next iteration for `c`, so the grouping is `(a - b) - c`. Recursing into the same level for the right operand would change that grouping.

## Shifts: between relational and additive

A shift’s operand parser consumes addition first, so `a + b << c` groups as `(a + b) << c`. The binary fold already places the right value in `rcx`, where the shift emitter needs its count.

The shift level delegates operands to addition and accepts the shift rows (`forth-bootstrap/cc/100-cc-expr.fth:1916`):

```forth chunk=expr-shift
\ ===========================================================================
\ cc-parse-shift: add (('<<'|'>>') add)*
\ ===========================================================================
\ C puts shift between relational and additive: `a + b << c` is
\ `(a + b) << c`.  Variable-count shifts take the count in rcx (CL).

: cc-parse-shift
  cc-parse-add
  begin,
    level-shift cc-binop? dup                     ( row row | 0 0 )
  while,
    >r                                            ( ; R: row )
    cc-emit-materialize                           \ left must be a value
    cc-target-lp64 @ if,
      cc-last-expr-type @ cc-last-struct-desc @ cc-last-expr-array-inner @ cc-last-expr-null @ cc-last-expr-qualified @
    then,
    cc-emit-push-rdi                              \ save left
    cc-parse-add                                  \ rdi = right
    r> cc-target-lp64 @ if, cc-native-binop-apply else, cc-binop-apply then,
                                                  \ rdi = left OP right
  repeat,
  drop                                            \ cc-binop?'s 0
  cc-putback-token ;                              \ we read one too many

```

## Relational and equality

The remaining ordinary folds differ by input level and accepted operators:

| Operand parser → result parser | Operators |
|---|---|
| `cc-parse-shift` → `cc-parse-rel` | `<`, `>`, `<=`, `>=` |
| `cc-parse-rel` → `cc-parse-eq` | `==`, `!=` |
| `cc-parse-eq` → `cc-parse-bit-and` | `&` |
| `cc-parse-bit-and` → `cc-parse-bit-xor` | `^` |
| `cc-parse-bit-xor` → `cc-parse-bit-or` | `\|` |

A relational operand contains any tighter shifts and arithmetic before the comparison emits (`forth-bootstrap/cc/100-cc-expr.fth:1940`):

```forth chunk=expr-rel
\ ===========================================================================
\ cc-parse-rel: shift (('<'|'<='|'>'|'>=') shift)*
\ ===========================================================================

: cc-parse-rel
  cc-parse-shift
  begin,
    level-rel cc-binop? dup                       ( row row | 0 0 )
  while,
    >r                                            ( ; R: row )
    cc-emit-materialize                           \ left must be a value
    cc-target-lp64 @ if,
      cc-last-expr-type @ cc-last-struct-desc @ cc-last-expr-array-inner @ cc-last-expr-null @ cc-last-expr-qualified @
    then,
    cc-emit-push-rdi                              \ save left
    cc-parse-shift                                \ rdi = right
    r> cc-target-lp64 @ if, cc-native-binop-apply else, cc-binop-apply then,
                                                  \ rdi = left OP right
  repeat,
  drop                                            \ cc-binop?'s 0
  cc-putback-token ;                              \ we read one too many

```

Equality accepts completed relational results as operands (`forth-bootstrap/cc/100-cc-expr.fth:1962`):

```forth chunk=expr-eq
\ ===========================================================================
\ cc-parse-eq: rel (('=='|'!=') rel)*
\ ===========================================================================

: cc-parse-eq
  cc-parse-rel
  begin,
    level-eq cc-binop? dup                        ( row row | 0 0 )
  while,
    >r                                            ( ; R: row )
    cc-emit-materialize                           \ left must be a value
    cc-target-lp64 @ if,
      cc-last-expr-type @ cc-last-struct-desc @ cc-last-expr-array-inner @ cc-last-expr-null @ cc-last-expr-qualified @
    then,
    cc-emit-push-rdi                              \ save left
    cc-parse-rel                                  \ rdi = right
    r> cc-target-lp64 @ if, cc-native-binop-apply else, cc-binop-apply then,
                                                  \ rdi = left OP right
  repeat,
  drop                                            \ cc-binop?'s 0
  cc-putback-token ;                              \ we read one too many

```

Thus `a < b == c < d` compares the results of the relational expressions. The comparison emitters supply C truth values; this layer selects their order.

## The bitwise trio

Bitwise operators also use the binary fold, without runtime short-circuiting.

Operator position distinguishes this binary `&` from the address-of operand handled in Chapter 34 (`forth-bootstrap/cc/100-cc-expr.fth:1984`):

```forth chunk=expr-bit
\ ===========================================================================
\ cc-parse-bit-and: eq ('&' eq)*
\ ===========================================================================
\ This '&' is the binary (infix) bitwise-and.  Unary '&' (address-of) is
\ cc-parse-unary's: operator position vs operand position tells them apart.

: cc-parse-bit-and
  cc-parse-eq
  begin,
    level-bit-and cc-binop? dup                   ( row row | 0 0 )
  while,
    >r                                            ( ; R: row )
    cc-emit-materialize                           \ left must be a value
    cc-target-lp64 @ if,
      cc-last-expr-type @ cc-last-struct-desc @ cc-last-expr-array-inner @ cc-last-expr-null @ cc-last-expr-qualified @
    then,
    cc-emit-push-rdi                              \ save left
    cc-parse-eq                                   \ rdi = right
    r> cc-target-lp64 @ if, cc-native-binop-apply else, cc-binop-apply then,
                                                  \ rdi = left OP right
  repeat,
  drop                                            \ cc-binop?'s 0
  cc-putback-token ;                              \ we read one too many

```

Exclusive-or accepts a complete bitwise-and operand (`forth-bootstrap/cc/100-cc-expr.fth:2008`):

```forth chunk=expr-bit
\ ===========================================================================
\ cc-parse-bit-xor: bit-and ('^' bit-and)*
\ ===========================================================================

: cc-parse-bit-xor
  cc-parse-bit-and
  begin,
    level-bit-xor cc-binop? dup                   ( row row | 0 0 )
  while,
    >r                                            ( ; R: row )
    cc-emit-materialize                           \ left must be a value
    cc-target-lp64 @ if,
      cc-last-expr-type @ cc-last-struct-desc @ cc-last-expr-array-inner @ cc-last-expr-null @ cc-last-expr-qualified @
    then,
    cc-emit-push-rdi                              \ save left
    cc-parse-bit-and                              \ rdi = right
    r> cc-target-lp64 @ if, cc-native-binop-apply else, cc-binop-apply then,
                                                  \ rdi = left OP right
  repeat,
  drop                                            \ cc-binop?'s 0
  cc-putback-token ;                              \ we read one too many

```

Bitwise-or accepts a complete exclusive-or operand (`forth-bootstrap/cc/100-cc-expr.fth:2030`):

```forth chunk=expr-bit
\ ===========================================================================
\ cc-parse-bit-or: bit-xor ('|' bit-xor)*
\ ===========================================================================

: cc-parse-bit-or
  cc-parse-bit-xor
  begin,
    level-bit-or cc-binop? dup                    ( row row | 0 0 )
  while,
    >r                                            ( ; R: row )
    cc-emit-materialize                           \ left must be a value
    cc-target-lp64 @ if,
      cc-last-expr-type @ cc-last-struct-desc @ cc-last-expr-array-inner @ cc-last-expr-null @ cc-last-expr-qualified @
    then,
    cc-emit-push-rdi                              \ save left
    cc-parse-bit-xor                              \ rdi = right
    r> cc-target-lp64 @ if, cc-native-binop-apply else, cc-binop-apply then,
                                                  \ rdi = left OP right
  repeat,
  drop                                            \ cc-binop?'s 0
  cc-putback-token ;                              \ we read one too many

```

## Short-circuit `&&` and `||`

A logical operator must sometimes skip its right operand at runtime. Both sides are still parsed and emitted. Conditional branches determine whether the resulting program executes the right side.

The conjunction sketch directs either false operand to a shared false-result path (`forth-bootstrap/cc/100-cc-expr.fth:2052`):

```forth chunk=expr-log
\ ===========================================================================
\ Short-circuit logical && and || — produce 1 or 0 (not the operand).
\ ===========================================================================
\ For `a && b`:
\   eval a; if zero, skip b and produce 0; else eval b; if zero, produce 0;
\   else produce 1.
\
\ Codegen sketch (with three rel32 fixups stashed on rstack):
\   <eval a>
\   test rdi,rdi
\   jz   .false_LHS
\   <eval b>
\   test rdi,rdi
\   jz   .false_RHS
\   mov rdi, 1
\   jmp  .end
\ .false_LHS:
\ .false_RHS:
\   mov rdi, 0
\ .end:
\
\ We push the three fixups onto rstack so the data stack stays clear for the
\ nested parse calls and any pending operator codes.

```

`cc-parse-log-and` emits those paths and patches the saved branch sites after their targets exist (`forth-bootstrap/cc/100-cc-expr.fth:2076`):

```forth chunk=expr-log
: cc-parse-log-and
  cc-parse-bit-or
  begin,
    cc-next-token-keep
    tok-kind @ tk-punct = tok-num @ pt-and-and = and
  while,
    cc-emit-materialize
    cc-value-test-fwd
    cc-emit-jz-rel32-placeholder >r               \ R: fixup-false-LHS
    cc-parse-bit-or
    cc-emit-materialize
    cc-value-test-fwd
    cc-emit-jz-rel32-placeholder >r               \ R: f-LHS f-RHS
    [lit] 1 cc-emit-mov-rdi-imm32
    cc-emit-jmp-rel32-placeholder >r              \ R: f-LHS f-RHS f-end
    \ False-target lands here for both fixups.
    r> r>                                         ( f-end f-RHS ; R: f-LHS )
    cc-patch-rel32-to-here                        \ patch f-RHS
    r>                                            ( f-end f-LHS )
    cc-patch-rel32-to-here                        \ patch f-LHS
    [lit] 0 cc-emit-mov-rdi-imm32
    cc-patch-rel32-to-here                        \ patch f-end
    cc-mark-int-value
  repeat,
  cc-putback-token ;

```

The return stack holds the left-false site, right-false site, and end-jump site in emission order. Patching pulls the end site aside, patches both false sites to the current position, emits the false result, then patches the end site. A nested right operand cannot consume the enclosing operation’s saved sites.

`cc-parse-log-or` reverses the deciding condition: either nonzero operand reaches the shared true-result path (`forth-bootstrap/cc/100-cc-expr.fth:2102`):

```forth chunk=expr-log
: cc-parse-log-or
  cc-parse-log-and
  begin,
    cc-next-token-keep
    tok-kind @ tk-punct = tok-num @ pt-or-or = and
  while,
    cc-emit-materialize
    cc-value-test-fwd
    cc-emit-jnz-rel32-placeholder >r              \ R: fixup-true-LHS
    cc-parse-log-and
    cc-emit-materialize
    cc-value-test-fwd
    cc-emit-jnz-rel32-placeholder >r              \ R: t-LHS t-RHS
    [lit] 0 cc-emit-mov-rdi-imm32
    cc-emit-jmp-rel32-placeholder >r              \ R: t-LHS t-RHS f-end
    \ True-target lands here for both fixups.
    r> r>                                         ( f-end t-RHS ; R: t-LHS )
    cc-patch-rel32-to-here
    r>                                            ( f-end t-LHS )
    cc-patch-rel32-to-here
    [lit] 1 cc-emit-mov-rdi-imm32
    cc-patch-rel32-to-here                        \ patch f-end
    cc-mark-int-value
  repeat,
  cc-putback-token ;

```

When neither operand decides early, conjunction produces true and disjunction produces false. `cc-mark-int-value` describes the joined result. Each loop then tests for another operator at its own level, and puts back the first token it cannot use.

## The cascade in motion

For `2 + 3 * 4`, follow the calls that actually emit an operation:

- The additive parser asks multiplication for its left operand. Multiplication obtains `2`, rejects `+`, and puts it back.
- Addition accepts `+`, emits a push of the left value, and calls multiplication for its right operand.
- That multiplication parses `3`, accepts `*`, saves its left value, and parses `4`. Its fold emits multiplication before returning.
- Addition receives the completed product, restores its own left value, and emits addition.

The machine stack preserves the outer left value while the inner fold uses its own saved operand. No expression tree is needed: the nested calls put multiplication’s instructions before addition’s instructions. The checkpoint makes the resulting value visible.

## Try it

Run from the `forth-bootstrap` checkout root. This driver loads through the expression file and calls `cc-parse-log-or` directly. It uses Chapter 34’s operand parsing from that same file as a black box; it loads no declaration, statement, function, or compiler-entry layer.

The driver points the lexer at the expression text, emits the cascade into an ELF image, and appends the exit shim. The shell runs that image from a fresh temporary directory and prints its exit status:

```sh
probe_dir=$(mktemp -d)
{
  cat forth/010-lib.fth cc/020-cc-arena.fth cc/030-cc-io.fth \
      cc/040-cc-prep.fth cc/050-cc-lex.fth \
      cc/060-cc-types.fth cc/070-cc-sym.fth \
      cc/080-cc-elf.fth cc/090-cc-emit.fth cc/100-cc-expr.fth
  cat <<'FORTH'
cc-src-init
here dup cc-src-buffer ! s, 2+3*4 here swap - cc-src-len !
[lit] 0 cc-src-pos ! [lit] 0 cc-tok-pending !
cc-out-init [lit] 0 cc-bss-size ! cc-emit-elf-header
cc-parse-log-or cc-emit-exit-shim
cc-finalize-elf
[lit] 1 cc-out-buf cc-out-pos @ write drop
bye
FORTH
} | ./seed-forth > "$probe_dir/expression"
printf 'driver exit: %s\n' "$?" # prints 'driver exit: 0'
chmod +x "$probe_dir/expression"
"$probe_dir/expression"
printf '2 + 3 * 4 = %s (exit status)\n' "$?" # prints '2 + 3 * 4 = 14 (exit status)'
rm -r "$probe_dir"
```

Observed output:

```text
driver exit: 0
2 + 3 * 4 = 14 (exit status)
```

This run exercises token handoff, the operator lookup, and nested multiplication/addition folds. It does not verify native pointer arithmetic, constant evaluation, or short-circuit execution.

## Exercise

**Trace — easy.** Follow `a - b - c` through `cc-parse-add`. Identify when each subtraction emits and which value becomes the next iteration’s left operand.

**Trace — moderate.** Follow `a && b || c`. Identify the branches that skip `b`, and explain why a false result from the conjunction must still allow `c` to run.
