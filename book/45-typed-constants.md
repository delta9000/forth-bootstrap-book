# Chapter 45 — Typed constants

`static long x = sizeof(long) * 3 + (1 << 4);` asks the compiler to calculate a value before the program runs. A typed evaluator calculates it while preserving C conversions at each operator. Its typed constant record becomes either initializer bytes or a symbolic address for the linker.

## A value carries its type

Trace the checkpoint's `(0xffffffffU + 2U) < 2U` by hand in the selected
LP64 target. The `U` suffixes give the addition two 32-bit unsigned
operands. The host Forth cell can hold their mathematical sum, but the C
intermediate value must obey its narrower type:

| Step | Value | Representation |
|---|---|---|
| Add before narrowing | `0x100000001` | Working sum in a Forth cell |
| Normalize the addition | `1` | `unsigned int` |
| Compare `1 < 2U` | `1` | `int`, the comparison result |

Keeping the wider sum until the final initializer store would make the
comparison false. The type belongs to every intermediate result, so the
evaluator must normalize at the addition boundary. Read the conversion
helpers as part of evaluation, not merely as preparation for a memory store.

A record must therefore carry a type alongside its value. It also carries
a descriptor for a shaped type and a symbol for an unresolved address.
For the checkpoint's `&arr[2]`, the compiler can already calculate the
byte addend `2 * sizeof(int) = 8`; it cannot yet calculate `arr`'s final
address. The record keeps that symbol and addend together until the
initializer can request a relocation (Chapter 41). An absent symbol
instead makes the numeric value absolute.

Every fold consumes records and produces another record; no generated
machine code runs to calculate the result. The private pool bounds those
records, and its accessors expose the four fields without confusing the
record's own Forth address with the value it describes
(`forth-bootstrap/cc/125-cc-consteval.fth:1`):

```forth file=cc/125-cc-consteval.fth
\ 125-cc-consteval.fth — typed LP64 constants for the direct System V target.
\ Loading this layer preserves legacy and native-mode constant semantics.
\ A private value record carries value, type, descriptor and relocation ID.
\ The public integer API returns ( value type ); the static API returns all
\ four cells. No machine code is executed to obtain a constant value.
\ A binary32 or binary64 record holds its IEEE encoding as the value;
\ an extended constant holds a pointer to its significand/sign-exponent.
\ 128 supplies the exact rounding behind the cc-fp-*-fwd hooks.

[lit] 4096 constant cc-const-cap
create cc-const-values cc-const-cap [lit] 32 * allot
variable cc-const-used
: cc-const-type [lit] 8 + @ ;
: cc-const-desc [lit] 16 + @ ;
: cc-const-symbol [lit] 24 + @ ;
: cc-const-new ( value type descriptor symbol -- record )
  cc-const-used @ 1+ cc-const-cap [lit] 240 cc-check-cap
  cc-const-used @ [lit] 32 * cc-const-values + >r
  [lit] 1 cc-const-used +!
  r@ [lit] 24 + ! r@ [lit] 16 + ! r@ [lit] 8 + ! r@ ! r> ;
: cc-const-cells ( record -- value type descriptor symbol )
  dup @ swap dup cc-const-type swap dup cc-const-desc swap cc-const-symbol ;
```

The integer-only API needs a value free of a relocation symbol. `cc-const-int-type` supplies the result type for Boolean operations; `cc-const-integer?` excludes pointers, and `cc-const-check-integer` enforces both restrictions (`forth-bootstrap/cc/125-cc-consteval.fth:23`):

```forth file=cc/125-cc-consteval.fth
: cc-const-int-type ty-int [lit] 0 ty-make ;
: cc-const-integer? ( type -- flag )
  dup ty-ptr if, drop [lit] 0 exit, then,
  ty-base
  dup ty-char = over ty-uchar = or over ty-short = or
  over ty-ushort = or over ty-int = or over ty-uint = or
  over ty-long = or over ty-ulong = or
  over ty-llong = or over ty-ullong = or swap ty-bool = or ;
: cc-const-check-integer ( record -- )
  dup cc-const-symbol swap cc-const-type cc-const-integer? 0= or if,
    cc-const-unsupported
  then, ;

```

These helpers compute with the Forth machine's 64-bit cells. The library's
`<` tests the sign of a wrapping subtraction. That is not enough for
full-range constants: the smallest signed cell, −2^63, is less than 1,
but subtracting 1 wraps to the largest positive cell.

`cc-const-slt` and `cc-const-ult` first ask whether the operands' high bits
differ. If they do, signed comparison treats the operand with its high bit
set as smaller; unsigned comparison treats it as larger. If the high bits
match, their difference fits the signed cell range, so the existing
subtraction-based comparison is safe. This is why the two helpers select
opposite operands in their differing-high-bit branches.

`cc-const-format` returns the storage size; `cc-const-signed-min`
constructs the signed lower bound from that size
(`forth-bootstrap/cc/125-cc-consteval.fth:36`):

```forth file=cc/125-cc-consteval.fth
\ 010's subtraction comparison is sufficient for compiler offsets, but
\ constants may straddle the entire signed or unsigned 64-bit range.
: cc-const-slt ( a b -- flag )
  2dup cc-xor 0< if, drop 0< else, < then, ;
: cc-const-ult ( a b -- flag )
  2dup cc-xor 0< if, nip 0< else, < then, ;
: cc-const-format ( type -- format ) ty-size ;
: cc-const-signed-min ( type -- value )
  ty-size [lit] 8 * 1- cc-pow2 cc-negate ;

```

<span id="floating-constants-are-exact-records"></span>

## Floating constants retain their encodings

Floating values reserve the same record shape. `cc-const-float?` recognizes them only for the System V target; `cc-const-sign` locates their sign bit. A binary floating value carries encoded bits, while an extended value carries an encoding address. `cc-fp-decimal-fwd`, `cc-fp-integer-fwd`, `cc-fp-resize-fwd`, `cc-fp-arith-fwd`, and `cc-fp-truncate-fwd` reserve decimal parsing, integer conversion, resizing, arithmetic, and truncation; their defaults reject. `cc-f80-new` reserves construction from a significand and sign/exponent. Chapter 47 supplies numeric operations; Chapter 49 connects extended values to runtime storage (`forth-bootstrap/cc/125-cc-consteval.fth:46`):

```forth file=cc/125-cc-consteval.fth
\ Floating constants exist only for the System V target. A format is the
\ byte size: 4 for binary32, 8 for binary64, 16 for extended precision.
: cc-const-float? ( type -- flag )
  dup ty-ptr if, drop [lit] 0 exit, then,
  ty-base dup ty-float = over ty-double = or swap ty-ldouble = or cc-target-sysv @ and ;
: cc-const-sign ( type -- bit )
  dup ty-base ty-ldouble = if, drop [lit] 32768 exit, then,
  ty-size [lit] 4 = if, [lit] 2147483648 else, 2^63 then, ;
defer cc-f80-new ( significand sign-exponent -- bits )
defer cc-fp-decimal-fwd  ( address length format -- bits )
defer cc-fp-integer-fwd  ( value signed? format -- bits )
defer cc-fp-resize-fwd   ( bits from-format to-format -- bits )
defer cc-fp-arith-fwd    ( left right operator format -- bits )
defer cc-fp-truncate-fwd ( bits format -- magnitude negative? fits? )
' cc-const-unsupported is cc-fp-decimal-fwd
' cc-const-unsupported is cc-fp-integer-fwd
' cc-const-unsupported is cc-fp-resize-fwd
' cc-const-unsupported is cc-fp-arith-fwd
' cc-const-unsupported is cc-fp-truncate-fwd
```

A suffix chooses a format before decoding. `cc-const-float-spelling` removes the suffix, passes the remaining token spelling to `cc-fp-decimal-fwd`, and pairs the returned encoding with its type. Loading this file alone therefore does not enable floating literals (`forth-bootstrap/cc/125-cc-consteval.fth:67`):

```forth file=cc/125-cc-consteval.fth
\ A trailing f/F selects binary32; l/L selects extended precision.
\ The decoder checks the remaining spelling without a suffix.
: cc-const-float-spelling ( -- bits type )
  tok-str-addr @ tok-str-len @
  2dup + 1- c@ dup [char] f = swap [char] F = or if,
    1- [lit] 4 cc-fp-decimal-fwd ty-float
  else,
    2dup + 1- c@ dup [char] l = swap [char] L = or if,
      1- [lit] 16 cc-fp-decimal-fwd ty-ldouble
    else, [lit] 8 cc-fp-decimal-fwd ty-double then,
  then,
  [lit] 0 ty-make ;

```

## Keep the numeric boundary explicit

Unsigned wraparound must happen before the next operator, not just when an initializer is stored. `cc-const-convert` masks narrow values and sign-extends signed results; `cc-const-bool?` selects the separate nonzero test for `_Bool`. `cc-const-promote` updates a checked integer record through the existing promotion rule. `cc-const-scalar?` admits integers and pointers for the nonfloating cast path (`forth-bootstrap/cc/125-cc-consteval.fth:78`):

```forth file=cc/125-cc-consteval.fth
\ Narrowing keeps low bits, then sign extends signed integer targets.
\ / is the seed's unsigned division, so a bit-63-set value stays intact.
\ _Bool instead keeps whether the value is nonzero.
: cc-const-bool? ( type -- flag ) dup ty-ptr 0= swap ty-base ty-bool = and ;
: cc-const-convert ( value type -- value )
  dup cc-const-integer? 0= if, cc-const-unsupported then,
  dup cc-const-bool? if, drop if, [lit] 1 else, [lit] 0 then, exit, then,
  dup ty-size [lit] 8 = if, drop exit, then,
  dup ty-unsigned? >r ty-size [lit] 8 * cc-pow2
  dup 1- rot and swap
  r> 0= if,
    over over [lit] 2 / and if, - else, drop then,
  else, drop then, ;
: cc-const-promote ( record -- record )
  dup cc-const-check-integer
  dup cc-const-type cc-expr-promote over [lit] 8 + ! ;
: cc-const-scalar? ( type -- flag )
  dup ty-ptr if, drop true else, cc-const-integer? then, ;

```

Crossing the floating boundary changes representation. `cc-const-to-float` either resizes an encoding or converts an integer with its signedness. In the reverse direction, `cc-const-from-float` requests a truncated magnitude and sign, checks the destination range with unsigned comparisons, then applies the sign. A negative nonzero magnitude cannot become an unsigned result; signed destinations allow the extra negative endpoint. `cc-const-range` is the common failure (`forth-bootstrap/cc/125-cc-consteval.fth:97`):

```forth file=cc/125-cc-consteval.fth
\ Integer to floating rounds once; floating to integer truncates toward
\ zero and must fit the destination (242). Width changes round once too.
: cc-const-to-float ( value from to -- bits )
  over cc-const-float? if,
    cc-const-format swap cc-const-format swap 2dup = if, 2drop exit, then,
    cc-fp-resize-fwd exit,
  then,
  over cc-const-integer? 0= if, cc-const-unsupported then,
  cc-const-format swap ty-unsigned? 0= swap cc-fp-integer-fwd ;
: cc-const-range [lit] 242 cc-die ;
: cc-const-from-float ( bits from to -- value )
  dup cc-const-integer? 0= if, cc-const-unsupported then,
  >r cc-const-format cc-fp-truncate-fwd 0= if, cc-const-range then,
  r@ ty-unsigned? if,
    over 0= 0= and if, cc-const-range then,
    r@ ty-size [lit] 8 < if,
      dup r@ ty-size [lit] 8 * cc-pow2 cc-const-ult 0= if,
        cc-const-range
      then,
    then,
  else,
    r@ ty-size [lit] 8 * 1- cc-pow2 swap if,
      over cc-const-ult if, cc-const-range then, cc-negate
    else,
      over swap cc-const-ult 0= if, cc-const-range then,
    then,
  then, r> drop ;
```

Truth conversion must bypass truncation: a nonzero fraction is true. `cc-const-float-bool` ignores only the sign, making either signed zero false. `cc-const-change` chooses this path for floating-to-`_Bool`, otherwise dispatches to floating conversion or integer normalization. `cc-const-arithmetic?` admits either numeric family (`forth-bootstrap/cc/125-cc-consteval.fth:124`):

```forth file=cc/125-cc-consteval.fth
\ A floating value is nonzero, NaN included, when any bit but the sign is set.
: cc-const-float-bool ( bits from -- value )
  dup ty-base ty-ldouble = if,
    drop dup @ swap [lit] 8 + @ [lit] 32767 and or if, [lit] 1 else, [lit] 0 then, exit,
  then,
  ty-size [lit] 4 = if, [lit] 2147483647 else, [lit] 9223372036854775807 then,
  and if, [lit] 1 else, [lit] 0 then, ;
: cc-const-change ( value from to -- value )
  dup cc-const-float? if, cc-const-to-float exit, then,
  over cc-const-float? over cc-const-bool? and if, drop cc-const-float-bool exit, then,
  over cc-const-float? if, cc-const-from-float exit, then,
  nip cc-const-convert ;
: cc-const-arithmetic? ( type -- flag )
  dup cc-const-integer? swap cc-const-float? or ;

```

Casts must preserve the meaning of a symbol. `cc-const-cast` routes numeric conversions through `cc-const-change`, checks scalar compatibility otherwise, and refuses to narrow a symbolic value below pointer width. A symbolic pointer cast to `long` retains its symbol but changes subsequent addition to byte arithmetic. Absolute values can be normalized before the destination type and descriptor replace the old fields (`forth-bootstrap/cc/125-cc-consteval.fth:139`):

```forth file=cc/125-cc-consteval.fth
: cc-const-cast ( record type descriptor -- record )
  2dup cc-ld? if, swap drop ty-ldouble [lit] 0 ty-make swap then,
  >r >r
  dup cc-const-type cc-const-float? r@ cc-const-float? or if,
    dup cc-const-symbol if, cc-const-unsupported then,
    dup cc-const-type cc-const-arithmetic? r@ cc-const-arithmetic? and 0= if,
      cc-const-unsupported
    then,
    dup @ over cc-const-type r@ cc-const-change over !
    r> over [lit] 8 + ! r> over [lit] 16 + ! exit,
  then,
  dup cc-const-type cc-const-scalar? r@ cc-const-scalar? and 0= if,
    cc-const-unsupported
  then,
  dup cc-const-type r@ cc-cast-types-fwd
  dup cc-const-symbol if,
    r@ ty-size [lit] 8 <> if, cc-const-unsupported then,
  else,
    dup cc-const-type cc-const-integer? if,
      dup @ over cc-const-type cc-const-convert over !
    then,
    r@ ty-ptr 0= if, dup @ r@ cc-const-convert over ! then,
  then,
  r> over [lit] 8 + ! r> over [lit] 16 + ! ;

```

## Validate leaves before combining them

The lexer retains a spelling even if its accumulated value has wrapped. `cc-const-literal-check` validates it before trusting that value: `cc-const-literal-base` selects the radix, `cc-const-literal-value` tracks the checked accumulation, and `cc-const-literal-digit` records whether any digit occurred. Before multiplying, the loop subtracts the next digit from the maximum value and divides by the base. The accumulator must not exceed that bound. The suffix parser must accept the entire suffix; trailing identifier characters or a decimal point cause rejection (`forth-bootstrap/cc/125-cc-consteval.fth:170`):

```forth file=cc/125-cc-consteval.fth
\ The lexer retains the spelling but accumulates modulo2^64. Recheck the
\ digits before accepting that value, and reject floating or malformed
\ spellings instead of accepting their integer prefix as a constant.
variable cc-const-literal-base
variable cc-const-literal-value
variable cc-const-literal-digit
: cc-const-literal-check
  [lit] 10 cc-const-literal-base ! [lit] 0 cc-const-literal-value !
  [lit] 0 cc-const-literal-digit !
  tok-str-addr @ tok-str-len @
  over c@ [char] 0 = if,
    [lit] 8 cc-const-literal-base !
    over 1+ c@ dup [char] x = swap [char] X = or if,
      swap [lit] 2 + swap [lit] 2 - [lit] 16 cc-const-literal-base !
    then,
  then,
  dup 0= if, cc-const-unsupported then,
  begin, dup while,
    over c@ dup cc-hex-digit? if,
      cc-hex-digit-val
      dup cc-const-literal-base @ >= if, cc-const-unsupported then,
      true over - cc-const-literal-base @ /
      cc-const-literal-value @ cc-const-ult if, cc-const-unsupported then,
      cc-const-literal-value @ cc-const-literal-base @ * + cc-const-literal-value !
      true cc-const-literal-digit !
    else,
      \ The rest of the spelling must be exactly one suffix, read by the
      \ same parser that types the literal (060's cc-integer-suffix).
      \ Leave the last letter for the step below, which ends the loop.
      drop 2dup cc-integer-suffix 0= if, cc-const-unsupported then,
      + 1- [lit] 1                                  ( last 1 )
    then,
    swap 1+ swap 1-
  repeat, drop
  cc-const-literal-digit @ 0= if, cc-const-unsupported then,
  c@ dup ident-cont? swap [char] . = or if, cc-const-unsupported then, ;

```

`cc-const-unary-fwd` and `cc-const-conditional-fwd` provide the recursive parser entries. Conditions also need a shared conversion: `cc-const-truth` inspects a floating encoding or checks an integer record, while `cc-const-boolean` stores the C truth value and changes its type to `int`. A symbolic record cannot pass the integer truth test (`forth-bootstrap/cc/125-cc-consteval.fth:201`):

```forth file=cc/125-cc-consteval.fth
defer cc-const-unary-fwd
defer cc-const-conditional-fwd

\ A condition becomes int 0 or 1. Both floating zeros are false.
: cc-const-truth ( record -- flag )
  dup cc-const-type cc-const-float? if,
    dup @ swap cc-const-type cc-const-float-bool 0= 0= exit,
  then,
  dup cc-const-check-integer @ 0= 0= ;
: cc-const-boolean ( record -- record )
  dup cc-const-truth cc-flag over !
  cc-const-int-type over [lit] 8 + ! ;

```

`cc-const-operand` keeps each leaf typed. Numeric tokens undergo spelling validation, characters and enum members become integer records, and identifier or string callbacks return the object adapter’s cells. After an opening parenthesis, a type name selects a cast; otherwise the conditional parser handles a grouped expression. Array casts are rejected before the operand is parsed. Both recursive paths return a record rather than emitted target code (`forth-bootstrap/cc/125-cc-consteval.fth:214`):

```forth file=cc/125-cc-consteval.fth
: cc-const-operand ( -- record )
  cc-next-token-keep
  tok-kind @ tk-num = if,
    cc-const-literal-check
    tok-num @ cc-integer-literal-type [lit] 0 [lit] 0 cc-const-new exit,
  then,
  tok-kind @ tk-chr = if,
    tok-num @ cc-const-int-type [lit] 0 [lit] 0 cc-const-new exit,
  then,
  tok-kind @ tk-float = if,
    cc-const-float-spelling [lit] 0 [lit] 0 cc-const-new exit,
  then,
  tok-kind @ tk-ident = if,
    tok-str-addr @ tok-str-len @ cc-sym-find
    dup 0< 0= if,
      dup cc-sym-kind-of sk-enum = if,
        cc-sym-val-of cc-const-int-type [lit] 0 [lit] 0 cc-const-new exit,
      then,
    then, drop
    cc-const-ident-fwd cc-const-new exit,
  then,
  tok-kind @ tk-str = if, cc-const-string-fwd cc-const-new exit, then,
  lparen cc-tok-punct? if,
    cc-next-token-keep
    cc-type-start? if,
      cc-parse-type-name
      cc-type-name-qualified @ cc-const-qualified @ or cc-const-qualified !
      cc-type-name-array @ if, cc-const-unsupported then,
      >r cc-cast-desc @ >r
      [char] ) cc-expect-punct-c
      cc-const-unary-fwd
      r> r> swap cc-const-cast exit,
    then,
    cc-putback-token cc-const-conditional-fwd
    [char] ) cc-expect-punct-c exit,
  then,
  cc-const-unsupported ;

```

## Apply unary operators to records

`cc-const-unary` wraps `sizeof` in an unsigned-long record and delegates address leaves after `&`. Unary plus promotes integers but keeps floating types. Unary minus has separate halves: an encoding changes only its sign, whereas an integer needs overflow checking and width normalization in the continuation below (`forth-bootstrap/cc/125-cc-consteval.fth:252`):

```forth file=cc/125-cc-consteval.fth
: cc-const-unary ( -- record )
  cc-next-token-keep
  kw-sizeof cc-tok-kw? if,
    cc-native-sizeof ty-ulong [lit] 0 ty-make
    [lit] 0 [lit] 0 cc-const-new exit,
  then,
  [char] & cc-tok-punct? if,
    cc-const-address-fwd cc-const-new exit,
  then,
  [char] + cc-tok-punct? if,
    cc-const-unary dup cc-const-type cc-const-float? 0= if,
      cc-const-promote
    then, exit,
  then,
  [char] - cc-tok-punct? if,
    cc-const-unary dup cc-const-type cc-const-float? if,
      \ Negation flips only the sign, so -0.0 keeps its sign bit.
      dup cc-const-type ty-base ty-ldouble = if,
        dup @ dup @ swap [lit] 8 + @ [lit] 32768 cc-xor cc-f80-new over ! exit,
      then,
      dup @ over cc-const-type cc-const-sign cc-xor over ! exit,
    then,
```

The integer half rejects negation of the signed minimum unless arithmetic is being skipped. Complement promotes and normalizes; logical negation uses the shared truth conversion. Falling through puts the token back for operand parsing, and the final binding closes the recursive unary entry (`forth-bootstrap/cc/125-cc-consteval.fth:274`):

```forth file=cc/125-cc-consteval.fth
    cc-const-promote
    cc-cx-skip @ 0= if,
      dup cc-const-type ty-unsigned? 0= if,
        dup @ over cc-const-type cc-const-signed-min = if,
          [lit] 242 cc-die
        then,
      then,
      dup @ cc-negate over cc-const-type cc-const-convert over !
    then, exit,
  then,
  [char] ~ cc-tok-punct? if,
    cc-const-unary cc-const-promote
    dup @ cc-invert over cc-const-type cc-const-convert over ! exit,
  then,
  [char] ! cc-tok-punct? if,
    cc-const-unary cc-const-boolean
    dup @ 0= cc-flag over ! exit,
  then,
  cc-putback-token cc-const-operand ;
' cc-const-unary is cc-const-unary-fwd

```

## Carry an address without knowing its final location

Return to the checkpoint's `&arr[2]`: its record keeps `arr` as the symbol
and 8 as the byte addend. If the next operator adds 1 to that `int *`, the
addend becomes 12, because pointer arithmetic advances by `sizeof(int)`.
The symbol stays unchanged and no array element is read. The evaluator
can complete this part of the calculation even though only the linker
will know where `arr` lives.

Binary scratch state belongs to a completed pair of operands: `cc-const-left` and `cc-const-right` hold records, `cc-const-row` the operator, `cc-const-common` the working type, and `cc-const-a` and `cc-const-b` the converted values. Filling these only after recursion returns avoids overwriting an outer operation. `cc-const-op`, `cc-const-unsigned?`, and `cc-const-less` read that state. `cc-const-address?` recognizes both symbolic integers and pointer-typed constants (`forth-bootstrap/cc/125-cc-consteval.fth:295`):

```forth file=cc/125-cc-consteval.fth
\ Binary temporaries are filled only after both recursive operands return.
variable cc-const-left
variable cc-const-right
variable cc-const-row
variable cc-const-common
variable cc-const-a
variable cc-const-b

: cc-const-op cc-const-row @ bo-op + @ ;
: cc-const-unsigned? cc-const-common @ ty-unsigned? ;
: cc-const-less
  cc-const-unsigned? if, cc-const-ult else, cc-const-slt then, ;
: cc-const-address? ( record -- flag )
  dup cc-const-symbol swap cc-const-type ty-ptr or ;
```

Address arithmetic accepts an address plus an integer, or an address minus an integer. `cc-const-address-binary` rejects other operators and any pair of addresses, then puts the address on the left. Pointer arithmetic scales by the pointee size and descriptor; a symbolic integer uses the common integer type without scaling. The result overwrites only the addend, preserving the symbol for relocation. A skipped operation substitutes an irrelevant addend while retaining the record’s type (`forth-bootstrap/cc/125-cc-consteval.fth:309`):

```forth file=cc/125-cc-consteval.fth
: cc-const-address-binary ( -- record )
  cc-const-op [char] + = cc-const-op [char] - = or 0= if,
    cc-const-unsupported
  then,
  cc-const-left @ cc-const-address? if,
    cc-const-right @ cc-const-address? if, cc-const-unsupported then,
  else,
    cc-const-op [char] - = if, cc-const-unsupported then,
    cc-const-left @ cc-const-right @ cc-const-left ! cc-const-right !
  then,
  cc-const-right @ cc-const-check-integer
  cc-const-left @ cc-const-type dup ty-ptr if,
    dup ty-ptr [lit] 1 = if,
      dup ty-base dup ty-void = swap ty-func = or if,
        cc-const-unsupported
      then,
    then,
    cc-const-left @ cc-const-desc cc-expr-pointee-size
    cc-const-right @ @ *
  else,
    cc-const-right @ cc-const-type cc-expr-common-type
    dup ty-size [lit] 8 <> if, cc-const-unsupported then,
    dup cc-const-left @ [lit] 8 + !
    cc-const-right @ @ swap cc-const-convert
  then,
  cc-cx-skip @ if, drop [lit] 0 else,
    cc-const-op [char] - = if, cc-negate then,
    cc-const-left @ @ +
  then,
  cc-const-left @ ! cc-const-left @ ;
```

## Check arithmetic at the working width

The handlers share converted operands and return a normalized value.

| Input | Result handler | Check or rule |
|---|---|---|
| Sum or difference | `cc-const-add`, `cc-const-subtract` | Detect signed overflow, then check the destination width. |
| Product | `cc-const-multiply` | Bound operand magnitudes before multiplying. |
| Quotient or remainder | `cc-const-divide` | Reject a zero divisor and signed minimum divided by −1. |
| Shift | `cc-const-shift` | Validate the count against the promoted left width. |

Machine-cell overflow and narrow-type overflow are different failures. The sign tests cover the former; `cc-const-check-result` catches the latter when normalization would change a signed result. Unsigned results simply normalize (`forth-bootstrap/cc/125-cc-consteval.fth:339`):

```forth file=cc/125-cc-consteval.fth
: cc-const-check-result ( value -- value )
  cc-const-unsigned? 0= if,
    dup cc-const-common @ cc-const-convert over <> if, [lit] 242 cc-die then,
  then,
  cc-const-common @ cc-const-convert ;
: cc-const-add ( a b -- sum )
  2dup + >r
  cc-const-unsigned? 0= if,
    2dup cc-xor 0< 0= if,
      over r@ cc-xor 0< if, [lit] 242 cc-die then,
    then,
  then, 2drop r> cc-const-check-result ;
: cc-const-subtract ( a b -- difference )
  2dup - >r
  cc-const-unsigned? 0= if,
    2dup cc-xor 0< if,
      over r@ cc-xor 0< if, [lit] 242 cc-die then,
    then,
  then, 2drop r> cc-const-check-result ;
```

The product limit depends on its sign: a negative result may reach the signed minimum’s magnitude. Division selects unsigned operations or signed truncation toward zero after validating the divisor (`forth-bootstrap/cc/125-cc-consteval.fth:358`):

```forth file=cc/125-cc-consteval.fth
: cc-const-multiply ( a b -- product )
  cc-const-unsigned? 0= over 0= 0= and if,
    2dup cc-xor 0< >r
    cc-const-common @ cc-const-signed-min cc-abs
    r> 0= if, 1- then,
    over cc-abs / [lit] 2 cc-npick cc-abs cc-const-ult if,
      [lit] 242 cc-die
    then,
  then, * cc-const-check-result ;
: cc-const-divide ( a b -- value )
  cc-divisor
  cc-const-unsigned? if,
    cc-const-op [char] / = if, / else, 2dup / * - then,
  else,
    dup true = [lit] 2 cc-npick cc-const-common @ cc-const-signed-min = and if,
      [lit] 242 cc-die
    then,
    cc-const-op [char] / = if, cc-div else, cc-mod then,
  then, ;
```

With a valid count, `cc-const-shift` keeps low bits even for a negative or overflowing signed left operand; this is the evaluator’s deliberate extension. Right shift chooses zero fill or sign propagation. `cc-const-evaluate` dispatches the checked cases, converts comparisons to C flags, and uses the existing operator-table evaluator for the remaining operators (`forth-bootstrap/cc/125-cc-consteval.fth:377`):

```forth file=cc/125-cc-consteval.fth
\ A count outside the promoted width is 241. Within it, a left shift keeps
\ the low bits as two's complement, as GCC folds it even for a negative or
\ overflowing signed operand: TYPE_MINIMUM (t) is ~(t)0 << (bits - 1).
: cc-const-shift ( a b -- value )
  dup 0< over cc-const-common @ ty-size [lit] 8 * >= or if,
    [lit] 241 cc-die
  then,
  cc-const-op pt-shl = if,
    cc-shl
  else,
    cc-const-unsigned? if, cc-pow2 / else, cc-sar then,
  then, cc-const-common @ cc-const-convert ;
: cc-const-evaluate ( a b -- value )
  cc-const-op
  dup [char] + = if, drop cc-const-add exit, then,
  dup [char] - = if, drop cc-const-subtract exit, then,
  dup [char] * = if, drop cc-const-multiply exit, then,
  dup [char] / = over [char] % = or if, drop cc-const-divide exit, then,
  dup pt-shl = over pt-shr = or if, drop cc-const-shift exit, then,
  dup [char] < = if, drop cc-const-less cc-flag exit, then,
  dup [char] > = if, drop swap cc-const-less cc-flag exit, then,
  dup pt-le = if, drop swap cc-const-less 0= cc-flag exit, then,
  dup pt-ge = if, drop cc-const-less 0= cc-flag exit, then,
  drop cc-const-row @ bo-eval + @ execute ;

```

## Compare floating records without target execution

Floating operands first pass through `cc-const-float-operand`, which rejects symbols and converts to the selected type. `cc-const-float-key` maps ordinary encodings into signed ordering keys with a shared key for signed zeros. Extended encodings instead compare sign, exponent, then significand through `cc-const-extended-compare`; `cc-const-extended-nan?` identifies their unordered case. These helpers inspect encodings, leaving their construction to the later numeric layers (`forth-bootstrap/cc/125-cc-consteval.fth:402`):

```forth file=cc/125-cc-consteval.fth
\ Usual arithmetic conversions: double if either operand is double, else
\ float. Only + - * / and comparisons accept floating operands.
: cc-const-float-operand ( record -- value )
  dup cc-const-symbol if, cc-const-unsupported then,
  dup @ swap cc-const-type cc-const-common @ cc-const-change ;
: cc-const-float-key ( bits -- key )
  dup cc-const-common @ cc-const-sign and if,
    cc-const-common @ cc-const-sign 1- and cc-negate
  then, ;
: cc-const-extended-compare ( a b -- comparison )
  2dup @ swap @ or 0= if, 2drop [lit] 0 exit, then,
  2dup [lit] 8 + @ swap [lit] 8 + @
  2dup [lit] 32768 and swap [lit] 32768 and <> if,
    drop [lit] 32768 and if, 2drop [lit] 1 else, 2drop true then, exit,
  then, 2drop
  2dup @ swap @ or if,
    2dup [lit] 8 + @ [lit] 32767 and swap [lit] 8 + @ [lit] 32767 and
    2dup = if, 2drop 2dup @ swap @ 2dup = if, 2drop [lit] 0 else,
      cc-const-ult if, [lit] 1 else, true then, then,
    else, < if, [lit] 1 else, true then, then,
    >r over [lit] 8 + @ [lit] 32768 and if, r> cc-negate >r then, 2drop r>
  else, 2drop [lit] 0 then, ;
: cc-const-extended-nan? ( bits -- flag )
  dup [lit] 8 + @ [lit] 32767 and [lit] 32767 = swap @ 2^63 <> and ;
```

`cc-const-float-compare` accepts only comparison operators. Extended NaNs make only inequality true. Other extended values compare through the preceding helper; ordinary encodings compare through their keys. The explicit operator gate prevents bitwise operators from accidentally using this path (`forth-bootstrap/cc/125-cc-consteval.fth:426`):

```forth file=cc/125-cc-consteval.fth
: cc-const-float-compare ( a b -- flag )
  cc-const-op dup [char] < = over [char] > = or over pt-le = or over pt-ge = or
  over pt-eq-eq = or swap pt-bang-eq = or 0= if, cc-const-unsupported then,
  cc-const-common @ ty-base ty-ldouble = if,
    2dup cc-const-extended-nan? swap cc-const-extended-nan? or if,
      2drop cc-const-op pt-bang-eq = exit,
    then,
    cc-const-extended-compare [lit] 0 cc-const-op
    dup [char] < = if, drop < exit, then,
    dup [char] > = if, drop > exit, then,
    dup pt-le = if, drop <= exit, then,
    dup pt-ge = if, drop >= exit, then,
    dup pt-eq-eq = if, drop = exit, then,
    pt-bang-eq = if, <> exit, then, cc-const-unsupported
  then,
  cc-const-float-key swap cc-const-float-key swap
  cc-const-op
  dup [char] < = if, drop cc-const-slt exit, then,
  dup [char] > = if, drop swap cc-const-slt exit, then,
  dup pt-le = if, drop swap cc-const-slt 0= exit, then,
  dup pt-ge = if, drop cc-const-slt 0= exit, then,
  dup pt-eq-eq = if, drop = exit, then,
  pt-bang-eq = if, <> exit, then,
  cc-const-unsupported ;
```

`cc-const-float-binary` chooses extended precision ahead of double, and double ahead of float, then converts both operands. Arithmetic calls `cc-fp-arith-fwd`; comparisons return `int`. Skipped arithmetic bypasses the hook. The left record receives the result and its type, so later operators see the conversion already applied (`forth-bootstrap/cc/125-cc-consteval.fth:450`):

```forth file=cc/125-cc-consteval.fth
: cc-const-float-binary ( -- record )
  cc-const-left @ cc-const-type ty-base ty-ldouble =
  cc-const-right @ cc-const-type ty-base ty-ldouble = or if,
    ty-ldouble
  else,
  cc-const-left @ cc-const-type ty-base ty-double =
  cc-const-right @ cc-const-type ty-base ty-double = or if,
    ty-double else, ty-float then, then, [lit] 0 ty-make cc-const-common !
  cc-const-left @ cc-const-float-operand cc-const-a !
  cc-const-right @ cc-const-float-operand cc-const-b !
  cc-const-op dup [char] + = over [char] - = or
  over [char] * = or swap [char] / = or if,
    cc-cx-skip @ if, [lit] 0 else,
      cc-const-a @ cc-const-b @ cc-const-op
      cc-const-common @ cc-const-format cc-fp-arith-fwd
    then, cc-const-common @
  else,
    cc-cx-skip @ if, [lit] 0 else,
      cc-const-a @ cc-const-b @ cc-const-float-compare cc-flag
    then, cc-const-int-type
  then,
  cc-const-left @ [lit] 8 + ! cc-const-left @ ! cc-const-left @ ;

```

## Combine operands before releasing recursion

`cc-const-binary-apply` first routes addresses and floating values, then converts integers before evaluating. Shifts promote their operands independently; other integer operators use a common type. Comparison results change to `int`, and every result is normalized before replacing the left record. `cc-const-binary` recurses by precedence and fills the scratch state only when both operands have returned (`forth-bootstrap/cc/125-cc-consteval.fth:473`):

```forth file=cc/125-cc-consteval.fth
: cc-const-binary-apply ( left right row -- left )
  cc-const-row ! cc-const-right ! cc-const-left !
  cc-const-left @ cc-const-address? cc-const-right @ cc-const-address? or if,
    cc-const-address-binary exit,
  then,
  cc-const-left @ cc-const-type cc-const-float?
  cc-const-right @ cc-const-type cc-const-float? or if,
    cc-const-float-binary exit,
  then,
  cc-const-left @ cc-const-check-integer
  cc-const-right @ cc-const-check-integer
  cc-const-row @ bo-level + @ level-shift = if,
    cc-const-left @ cc-const-type cc-expr-promote
  else,
    cc-const-left @ cc-const-type cc-const-right @ cc-const-type cc-expr-common-type
  then, cc-const-common !
  cc-const-left @ @ cc-const-common @ cc-const-convert cc-const-a !
  cc-const-row @ bo-level + @ level-shift = if,
    cc-const-right @ @ cc-const-right @ cc-const-type cc-expr-promote cc-const-convert
  else,
    cc-const-right @ @ cc-const-common @ cc-const-convert
  then, cc-const-b !
  cc-cx-skip @ if, [lit] 0 else,
    cc-const-a @ cc-const-b @ cc-const-evaluate
  then,
  cc-const-row @ bo-level + @ dup level-rel = swap level-eq = or if,
    cc-const-int-type cc-const-common !
  then,
  cc-const-common @ cc-const-convert cc-const-left @ !
  cc-const-common @ cc-const-left @ [lit] 8 + ! cc-const-left @ ;
: cc-const-binary ( level -- record )
  dup 0= if, drop cc-const-unary exit, then,
  dup 1- cc-const-binary
  begin, over cc-binop? dup while,
    >r over 1- cc-const-binary r> cc-const-binary-apply
  repeat, drop cc-putback-token nip ;

```

## Parse dead arms while suppressing their effects

For a manual trace of `0 && (9 / 0)`, separate consuming tokens from
performing arithmetic. The left zero makes the right operand irrelevant
to the value, so the parser enables the skip state before visiting the
parenthesized expression. It still consumes `9`, `/`, `0`, and `)` and
builds a typed result, but bypasses the division calculation. After
restoring the prior skip state, the logical operator produces integer
zero. Replacing the leading zero with one selects the division and
reaches the zero-divisor check. An unselected operand must still have
valid syntax; skipping its calculation cannot repair a missing operand
or closing parenthesis.

Under the inherited skip state (Chapter 34), an unused operand still supplies a typed record. `cc-const-logical-and` and `cc-const-logical-or` save `cc-cx-skip`, enable it for an irrelevant right operand, and restore the outer state afterward. Binary arithmetic handlers consult that state before calculating; tokens and operand types still pass through the parser. Skipping arithmetic does not suppress every later numeric-conversion diagnostic. Each logical result reuses the left record as an `int` (`forth-bootstrap/cc/125-cc-consteval.fth:510`):

```forth file=cc/125-cc-consteval.fth
: cc-const-logical-and ( -- record )
  level-bit-or cc-const-binary
  begin, cc-next-token-keep pt-and-and cc-tok-punct? while,
    cc-const-boolean
    cc-cx-skip @ >r dup @ 0= if, true cc-cx-skip ! then,
    level-bit-or cc-const-binary
    r> cc-cx-skip ! cc-const-boolean
    @ 0= 0= over @ 0= 0= and cc-flag over !
    cc-const-int-type over [lit] 8 + !
  repeat, cc-putback-token ;
: cc-const-logical-or ( -- record )
  cc-const-logical-and
  begin, cc-next-token-keep pt-or-or cc-tok-punct? while,
    cc-const-boolean
    cc-cx-skip @ >r dup @ if, true cc-cx-skip ! then,
    cc-const-logical-and
    r> cc-cx-skip ! cc-const-boolean
    @ 0= 0= over @ 0= 0= or cc-flag over !
    cc-const-int-type over [lit] 8 + !
  repeat, cc-putback-token ;
```

A conditional’s unselected arm still affects its type. `cc-const-null?` recognizes an absolute integer zero, allowing `cc-const-select` to adopt the other arm’s pointer type and descriptor. Pointer arms must then be compatible. Numeric arms determine a common type before choosing a value; a selected symbol must remain pointer-width and nonfloating. The chosen absolute value passes through `cc-const-change` (`forth-bootstrap/cc/125-cc-consteval.fth:530`):

```forth file=cc/125-cc-consteval.fth
: cc-const-null? ( record -- flag )
  dup cc-const-type cc-const-integer? over cc-const-symbol 0= and swap @ 0= and ;
: cc-const-select ( condition yes no -- result )
  \ Two pointer arms need the same pointed-to type. A zero integer arm
  \ adopts the other pointer's type. Symbolic integer arms remain 64-bit.
  over cc-const-type ty-ptr over cc-const-type ty-ptr or if,
    over cc-const-null? if,
      dup cc-const-type [lit] 2 cc-npick [lit] 8 + !
      dup cc-const-desc [lit] 2 cc-npick [lit] 16 + !
    then,
    dup cc-const-null? if,
      over cc-const-type over [lit] 8 + !
      over cc-const-desc over [lit] 16 + !
    then,
    over cc-const-type [lit] 2 cc-npick cc-const-desc
    [lit] 2 cc-npick cc-const-type [lit] 3 cc-npick cc-const-desc
    cc-sysv-compatible-types 0= if, cc-const-unsupported then,
    rot @ if, drop else, nip then, exit,
  then,
  2dup cc-const-type ty-base ty-ldouble = swap cc-const-type ty-base ty-ldouble = or if,
    ty-ldouble [lit] 0 ty-make
  else, 2dup cc-const-type swap cc-const-type cc-expr-common-type then, >r
  rot @ if, drop else, nip then,
  dup cc-const-symbol if,
    r@ ty-size [lit] 8 <> r@ cc-const-float? or if, cc-const-unsupported then,
  else, dup @ over cc-const-type r@ cc-const-change over ! then,
  r> over [lit] 8 + ! ;
```

`cc-const-conditional` applies the skip state separately to each arm, keeping the saved outer state across nested conditionals. It calls `cc-const-select` only after parsing both arms. The final binding connects parenthesized expressions and casts back to this parser (`forth-bootstrap/cc/125-cc-consteval.fth:557`):

```forth file=cc/125-cc-consteval.fth
: cc-const-conditional ( -- record )
  cc-const-logical-or cc-next-token-keep
  [char] ? cc-tok-punct? if,
    cc-const-boolean
    cc-cx-skip @ >r
    dup @ 0= if, true cc-cx-skip ! then,
    cc-const-conditional r@ cc-cx-skip ! >r
    [char] : cc-expect-punct-c
    dup @ if, true cc-cx-skip ! then,
    cc-const-conditional r> swap cc-const-select
    r> cc-cx-skip !
  else, cc-putback-token then, ;
' cc-const-conditional is cc-const-conditional-fwd

```

## Return values to initializers

The address adapter needs this evaluator inside its own grammar. `cc-const-address-cast` preserves qualification information and returns cast cells; `cc-const-address-unary` returns unary cells; `cc-const-address-index` requires an integer subscript. They inherit the current skip state. The LP64 storage traversal already owns destination widths, so `cc-const-initial` changes representation only for floating values or `_Bool`; ordinary integers and pointers pass through unchanged (`forth-bootstrap/cc/125-cc-consteval.fth:571`):

```forth file=cc/125-cc-consteval.fth
\ The object adapter parses address operands without emitting or loading
\ target memory. These callbacks share this evaluator's casts, unary
\ precedence and integer checks, including the current dead-arm state.
: cc-const-address-cast ( type descriptor -- value type descriptor symbol )
  cc-type-name-qualified @ cc-const-qualified @ or cc-const-qualified !
  >r >r cc-const-unary r> r> cc-const-cast cc-const-cells ;
: cc-const-address-unary ( -- value type descriptor symbol )
  cc-const-unary cc-const-cells ;
: cc-const-address-index ( -- value )
  cc-const-conditional dup cc-const-check-integer @ ;
' cc-const-address-cast is cc-om-address-cast-fwd
\ Static leaves change representation only when a floating type or _Bool
\ is involved.
: cc-const-initial ( value source destination -- value )
  2dup cc-const-float? swap cc-const-float? or over cc-const-bool? or if,
    cc-const-change exit,
  then, 2drop ;
' cc-const-initial is cc-om-value-fwd
' cc-const-address-unary is cc-om-address-unary-fwd
' cc-const-address-index is cc-om-address-index-fwd

```

Public parsing must release temporary records without destroying outer operands. `cc-parse-static-const` saves the constant pool watermark, skip state, and qualification state, returns unpacked cells, then restores all three. `cc-parse-integer-const` further rejects symbols and noninteger types. Binding the static hook enables scalar initializers; `cc-parse-target-const` selects the typed integer API only for System V outside preprocessing, preserving the default parser elsewhere (`forth-bootstrap/cc/125-cc-consteval.fth:592`):

```forth file=cc/125-cc-consteval.fth
\ Each public parse restores its pool watermark. Nested sizeof array bounds
\ can therefore call the same API without corrupting their outer operands.
: cc-parse-static-const ( -- value type descriptor symbol )
  cc-const-used @ >r cc-cx-skip @ >r cc-const-qualified @ >r
  [lit] 0 cc-const-qualified !
  [lit] 0 cc-cx-skip !
  cc-const-conditional cc-const-cells
  r> cc-const-qualified ! r> cc-cx-skip ! r> cc-const-used ! ;
: cc-parse-integer-const ( -- value type )
  cc-parse-static-const
  swap drop if, cc-const-unsupported then,
  dup cc-const-integer? 0= if, cc-const-unsupported then, ;

' cc-parse-static-const is cc-parse-static-const-fwd
: cc-parse-target-const
  cc-target-sysv @ cc-cx-pp @ 0= and if,
    cc-parse-integer-const drop
  else, cc-parse-const-default then, ;
' cc-parse-target-const is cc-parse-const
```

The consumer in `forth-bootstrap/cc/123-cc-object-program.fth:232` calls that static hook. For an absolute result, it invokes `cc-om-value-fwd` and patches the destination-sized bytes; for a symbol, it records an address relocation with the returned addend. Thus the opening expression becomes the stored value of `x`, while `&arr[2]` keeps `arr` symbolic until linking. The evaluator computes neither a final load address nor runtime instructions.

## Try it

Run from the `forth-bootstrap` checkout root with the seed already built. The block loads compiler layers through this evaluator, writes a small `_start` object, then links each probe with the Forth linker. Each executable returns one initializer result; the shell prints and checks its exit status. All generated files stay in the temporary directory.

<!-- tryit: expect "x = 40\npointer = 29\nwrap = 0" -->
```sh
(
set -o pipefail
work=$(mktemp -d /tmp/book-probe.XXXXXXXXXX) || exit "$?"
trap 'status=$?; rm -rf -- "$work" || status=1; exit "$status"' EXIT
{
  cat forth/010-lib.fth cc/020-cc-arena.fth cc/030-cc-io.fth cc/081-cc-object.fth || exit "$?"
  printf 'create output-path s, %s/start.o [lit] 0 c,\n' "$work"
  cat <<'FORTH' || exit "$?"
cc-obj-init
[lit] 232 cc-obj-byte [lit] 0 cc-obj-4le
[lit] 137 cc-obj-byte [lit] 199 cc-obj-byte
[lit] 184 cc-obj-byte [lit] 60 cc-obj-4le
[lit] 15 cc-obj-byte [lit] 5 cc-obj-byte
create entry-name s, _start
create main-name s, main
entry-name [lit] 6 cc-obj-global cc-obj-func cc-obj-default cc-obj-text [lit] 0 [lit] 14 cc-obj-symbol drop
main-name [lit] 4 cc-obj-global cc-obj-func cc-obj-default cc-obj-undef [lit] 0 [lit] 0 cc-obj-symbol
>r cc-obj-text [lit] 1 cc-obj-plt32 r> [lit] 0 [lit] 4 - cc-obj-reloc
output-path cc-obj-write bye
FORTH
} | ./seed-forth || exit "$?"
for probe in x pointer wrap; do
  cat > "$work/probe.c" <<'C' || exit "$?"
static long x = sizeof(long) * 3 + (1 << 4);
static int arr[3] = {7, 11, 29};
static int *p = &arr[2];
static unsigned int wrapped = 0xffffffffU + 2U;
static int before_store = (0xffffffffU + 2U) < 2U;
C
  case "$probe" in
    x) expression=x; expected=40 ;;
    pointer) expression='*p'; expected=29 ;;
    wrap) expression='wrapped != 1U ? 101 : before_store != 1 ? 102 : 0'; expected=0 ;;
  esac
  printf 'int main(void) { return %s; }\n' "$expression" >> "$work/probe.c"
  {
    cat forth/010-lib.fth cc/0[2-9]*-cc-*.fth cc/1[01]*-cc-*.fth \
        cc/121-cc-sysv.fth cc/123-cc-object-program.fth \
        cc/124-cc-target.fth cc/125-cc-consteval.fth || exit "$?"
    printf 'create output-path s, %s/probe.o [lit] 0 c,\n' "$work"
    cat <<'FORTH' || exit "$?"
cc-sysv-object-enable
: object-main
  cc-load-stdin cc-preprocess cc-out-init cc-globals-init
  cc-sysv-object-program output-path cc-obj-write bye ;
object-main
FORTH
    cat "$work/probe.c" || exit "$?"
  } | ./seed-forth || exit "$?"
  {
    cat forth/010-lib.fth cc/020-cc-arena.fth cc/030-cc-io.fth cc/140-cc-link.fth || exit "$?"
    for name in start.o probe.o result; do
      printf 'create p-%s s, %s/%s [lit] 0 c,\n' "$name" "$work" "$name"
    done
    printf '%s\n' 'create entry-name s, _start' \
      'lnk-init p-start.o lnk-add-object p-probe.o lnk-add-object' \
      'entry-name [lit] 6 lnk-entry p-result lnk-link lnk-release bye'
  } | ./seed-forth || exit "$?"
  result=0
  "$work/result" || result=$?
  printf '%s = %s\n' "$probe" "$result"
  test "$result" -eq "$expected" || exit 1
done
) # prints "x = 40\npointer = 29\nwrap = 0"
```

Expected output (the wrap check returns zero on success):

```text
x = 40
pointer = 29
wrap = 0
```

The wrap probe checks both the stored value and `before_store`. The latter stores the result of comparing the unsigned sum with `2U`: normalization only at the final four-byte store of `wrapped` would fail this check. Status 101 identifies a wrong stored value; 102 identifies a wrong before-store comparison.

## Exercise

Hints and feedback are in [Appendix H](66-exercise-feedback.md#chapter-45-typed-intermediate-values-and-dead-arms).

**Trace (easy).** Follow `wrapped` through literal validation, common-type conversion, addition, and `cc-const-check-result`. Explain why delaying normalization until the final store would break a comparison of the sum with `2U`.

**Verify (moderate).** Give `x` the initializer
`1 ? (sizeof(long) * 3 + (1 << 4)) : (1 / 0)`, then make a second version
with condition `0`. Before running either, predict whether compilation
succeeds and what a successfully compiled program returns. Run both
versions and trace the parser state and arithmetic check responsible for
each outcome. Account for how the parser reaches the declaration's end
even when an arm does not supply its value.

Run each version as a fresh complete block and record its shell status
immediately afterward, for example with `status=$?`. Keep the existing
compiler-failure guards: if compilation rejects an initializer, the block
must stop before linking or running it, and its normal three result lines
will be absent. Compare the diagnostic and status with your prediction;
do not remove the guard to obtain a program result. Restore the successful
source before testing an unrelated change.
