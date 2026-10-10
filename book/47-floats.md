# Chapter 47 — Floating values and exact literals

`double sum(void)` can add decimal literals and return their rounded sum. This chapter adds type-directed SSE operations that compute with those bits and return them in the right register, and an exact decimal decoder that produces them. The result is executable floating expressions with correctly rounded literal bits.

## Read the bits before rounding

The decoder must choose between representable values. First recover what
their encodings mean; if you can already derive the neighbours of `1.0`,
try the prediction below and continue to the payload path.

A binary floating payload has three fields, from most to least significant:
sign `s`, unsigned exponent field `E`, and unsigned fraction field `F`.
Here `p` counts **stored fraction bits**, and `B` is the exponent bias:

In the formulas below, `2^k` means two raised to the power `k`. This is
mathematical notation, not C's bitwise exclusive-or operator.

| Format in this compiler | Sign bits | Exponent bits | Fraction bits `p` | Bias `B` |
|---|---:|---:|---:|---:|
| binary32 (`float`) | 1 | 8 | 23 | 127 |
| binary64 (`double`) | 1 | 11 | 52 | 1023 |

These are the IEEE [single](https://docs.oracle.com/cd/E37069_01/html/E39019/z4000ac019178.html)
and [double](https://docs.oracle.com/cd/E37069_01/html/E39019/z4000ac019269.html)
layouts. The compiler selects their fraction widths, leading units `2^p`
and biases in `forth-bootstrap/cc/128-cc-float-literal.fth:278–291`.
The field cases explain why that leading unit is sometimes present:

- **Normal:** when `E` is neither zero nor all ones, the value is
  `(-1)^s * (1 + F/2^p) * 2^(E-B)`. The significand is the
  `1 + F/2^p` part. Its leading `1` is implicit, so `p` stored fraction
  bits give `p+1` significant bits. The integer significand used during
  rounding is `q = 2^p + F`.
- **Subnormal or zero:** when `E = 0`, the value is
  `(-1)^s * (F/2^p) * 2^(1-B)`, with no implicit `1`.
  Nonzero `F` encodes a subnormal, allowing smaller magnitudes below the
  smallest normal. `F = 0` encodes zero; the sign distinguishes `+0`
  from `-0`. Both are false in a C condition.
- **Nonfinite:** an all-ones exponent (`255` or `2047`) encodes infinity
  when `F = 0`, and NaN (not a number) otherwise.

Unpacking implements the normal/subnormal distinction at
`forth-bootstrap/cc/128-cc-float-literal.fth:403–412`; the zero test discards
the sign at `forth-bootstrap/cc/127-cc-binary64.fth:145–163`.
Recognizing the IEEE cases does not establish full compiler support:
scalar literal overflow is diagnosed, and the
[constant-operation limits](#change-a-constants-format) remain important.

### Derive unity and its neighbour

Work in binary64. For positive `1.0`, `s = 0`, `F = 0`, and the actual
exponent is zero, so `E = B = 1023 = 0x3ff`. Placing that exponent above
the 52 fraction bits gives `0x3ff0000000000000`. Increasing `F` to `1`
gives the next larger value, `1 + 2^-52`, encoded as
`0x3ff0000000000001`. These are whole-payload hexadecimal values, not a
memory byte listing.

Their exact midpoint is `1 + 2^-53`, which needs one more fraction bit
than binary64 stores. Round to nearest chooses the closer endpoint; at an
exact tie, **ties to even** chooses the endpoint whose integer significand
`q` is even. Here the choices have `q = 2^52` and `q = 2^52 + 1`, so
the midpoint rounds to `1.0`. This is a manual derivation, matching the
quotient parity test in `forth-bootstrap/cc/128-cc-float-literal.fth:252–269`.

**Predict a changed tie.** Move the interval up one step: its endpoints
are `1 + 2^-52` and `1 + 2 * 2^-52`. Which binary64 payload should their
exact midpoint, `1 + 3 * 2^-53`, round to? Decide before opening the
feedback; no compiler run is needed.

<details>
<summary>Hint</summary>

Write the two integer significands as `2^52 + F`. Which has a zero low bit?

</details>

<details>
<summary>Feedback and repair</summary>

The result is the upper endpoint, `0x3ff0000000000002`. The lower
significand is `2^52 + 1`, which is odd; the upper is `2^52 + 2`, which
is even. Ties to even does not mean always rounding down. If you chose
the lower endpoint, return to [unity and its neighbour](#derive-unity-and-its-neighbour)
and compare the two low bits before trying again. If the payload itself
was hard to form, revisit [the field layout](#read-the-bits-before-rounding).

</details>

The rest of the chapter first transports these payloads, then constructs
them from exact integer ratios. The ratio must retain enough information
to distinguish below, at, and above a midpoint before rounding once.

## Keep the payload, preserve the type

The path is spelling → payload in RDI → transient SSE operands → payload in RDI → storage or return. Binary64 occupies a full expression cell; binary32 uses its low half and stores only four bytes. Separate type and transport prevent a `float` store from overwriting its neighbour.

The predicates exclude pointers and enable floating values only in System V mode. `cc-fp-scalar-check` admits those values; `cc-fp-storage-type` presents binary32 to the existing memory emitter as `unsigned int`, without numerically converting it (`forth-bootstrap/cc/127-cc-binary64.fth:1`):
```forth file=cc/127-cc-binary64.fth
\ 127-cc-binary64.fth — binary32/binary64 scalar System V values.
\ Raw payloads occupy RDI/RCX and eight-byte expression/frame slots.
\ Binary32 storage is four bytes; arithmetic rounds at its own precision.
\ XMM0/XMM1 are transient arithmetic registers; XMM0 carries ABI results.
\ Long double uses X87 transport (121, 131) and computations (132).
\ Static floating initializers are exact compile-time constants (125, 128).
\ Native mode is not changed.

: cc-f64-type? ( type -- flag )
  dup ty-ptr 0= swap ty-base ty-double = and cc-target-sysv @ and ;
: cc-f32-type? ( type -- flag )
  dup ty-ptr 0= swap ty-base ty-float = and cc-target-sysv @ and ;
: cc-fp-type? ( type -- flag ) dup cc-f32-type? swap cc-f64-type? or ;
: cc-fp-scalar-check ( type -- )
  dup cc-fp-type? if, drop else, cc-sysv-check-scalar-default then, ;
' cc-fp-scalar-check is cc-sysv-check-scalar

\ The integer storage emitter sees binary32 as an unsigned four-byte
\ payload. This hook changes no expression type and does no conversion.
: cc-fp-storage-type ( type -- storage-type )
  cc-sysv-value-type-check
  dup cc-f32-type? if, drop ty-uint [lit] 0 ty-make then, ;
' cc-fp-storage-type is cc-emit-type-check-fwd

```
A literal must retain its whole spelling for validation. The scanner's start, previous character, floating-marker flag and hexadecimal flag describe that temporary scan; signs belong to a preprocessing number only after an exponent marker (`forth-bootstrap/cc/127-cc-binary64.fth:25`):
```forth file=cc/127-cc-binary64.fth
\ Scan a complete pp-number, retaining its spelling. Integer tokens return
\ to the original lexer unchanged; malformed floating forms reach128's
\ checked grammar instead of being split into plausible integer tokens.
variable cc-f64-scan-start
variable cc-f64-scan-prev
variable cc-f64-scan-seen
variable cc-f64-scan-hex
: cc-f64-number-char? ( char -- flag )
  dup ident-cont? over [char] . = or if, drop true exit, then,
  dup [char] + = swap [char] - = or
  cc-f64-scan-prev @ dup [char] e = over [char] E = or
  over [char] p = or swap [char] P = or and ;
```
`cc-f64-lex` either captures the complete candidate or rewinds for the integer lexer. A point or an appropriate exponent marker selects `tk-float`; malformed trailing characters stay attached so the decoder can reject the whole token (`forth-bootstrap/cc/127-cc-binary64.fth:37`):
```forth file=cc/127-cc-binary64.fth
: cc-f64-lex ( -- handled? )
  cc-target-sysv @ 0= cc-eof? or if, [lit] 0 exit, then,
  cc-peek-char digit? cc-peek-char-2 digit? swap [char] . = and or
  0= if, [lit] 0 exit, then,
  cc-src-pos @ cc-f64-scan-start !
  cc-peek-char-2 dup [char] x = swap [char] X = or
  swap [char] 0 = and cc-f64-scan-hex !
  [lit] 0 cc-f64-scan-prev ! [lit] 0 cc-f64-scan-seen !
  begin, cc-eof? 0= cc-peek-char cc-f64-number-char? and while,
    cc-next-char
    dup [char] . = if, true cc-f64-scan-seen ! then,
    cc-f64-scan-hex @ if,
      dup [char] p = over [char] P = or
    else, dup [char] e = over [char] E = or then,
    if, true cc-f64-scan-seen ! then,
    cc-f64-scan-prev !
  repeat,
  cc-f64-scan-seen @ 0= if,
    cc-f64-scan-start @ cc-src-pos ! [lit] 0 exit,
  then,
  cc-src-buf cc-f64-scan-start @ + tok-str-addr !
  cc-src-pos @ cc-f64-scan-start @ - tok-str-len !
  tk-float tok-kind ! [lit] 0 tok-num ! true ;
' cc-f64-lex is cc-sysv-lex-number-fwd
```
The runtime literal hook asks the typed spelling interface (Chapter 45) for bits and type, then emits the bits as an immediate. Its decimal conversion will use the same path as a static initializer (`forth-bootstrap/cc/127-cc-binary64.fth:61`):
```forth file=cc/127-cc-binary64.fth
: cc-f64-literal ( -- handled? )
  cc-target-sysv @ tok-kind @ tk-float = and 0= if, [lit] 0 exit, then,
  cc-const-float-spelling swap cc-emit-movabs-rdi-imm64
  [lit] 0 cc-mark-typed-value true ;
' cc-f64-literal is cc-value-literal-fwd

```

## Move into SSE only to compute

XMM0 and XMM1 belong to a separate bank of
[128-bit registers](https://www.intel.com/content/dam/support/us/en/documents/processors/pentium4/sb/25366521.pdf),
rather than being aliases of RDI and RCX. The scalar SSE/SSE2 instructions used here
operate on one binary32 value in the low 32 bits or one binary64 value in
the low 64 bits; the remaining bits are not extra precision for that value.

The register bridges copy payloads without converting them. RAX supplies an auxiliary operand for updates and unsigned conversion; ordinary binary expressions use RCX (`forth-bootstrap/cc/127-cc-binary64.fth:67`):
```forth file=cc/127-cc-binary64.fth
: cc-fp-xmm0-from-rdi
  [lit] 102 cc-emit-byte [lit] 72 cc-emit-byte
  [lit] 15 cc-emit-byte [lit] 110 cc-emit-byte [lit] 199 cc-emit-byte ;
: cc-fp-xmm1-from-rcx
  [lit] 102 cc-emit-byte [lit] 72 cc-emit-byte
  [lit] 15 cc-emit-byte [lit] 110 cc-emit-byte [lit] 201 cc-emit-byte ;
: cc-fp-xmm1-from-rax
  [lit] 102 cc-emit-byte [lit] 72 cc-emit-byte
  [lit] 15 cc-emit-byte [lit] 110 cc-emit-byte [lit] 200 cc-emit-byte ;
: cc-fp-rdi-from-xmm0
  [lit] 102 cc-emit-byte [lit] 72 cc-emit-byte
  [lit] 15 cc-emit-byte [lit] 126 cc-emit-byte [lit] 199 cc-emit-byte ;
```
`cc-fp-prefix` chooses scalar single or double precision; `cc-fp-signed-from-rdi` emits numeric integer conversion, `cc-fp-truncate-rdi` emits conversion toward zero, and `cc-fp-sse` supplies the shared binary-instruction shape. `cc-fp-change-check` admits floating updates (`forth-bootstrap/cc/127-cc-binary64.fth:79`):
```forth file=cc/127-cc-binary64.fth
: cc-fp-prefix ( type -- )
  cc-f32-type? if, [lit] 243 else, [lit] 242 then, cc-emit-byte ;
: cc-fp-signed-from-rdi ( type -- )
  cc-fp-prefix [lit] 72 cc-emit-byte
  [lit] 15 cc-emit-byte [lit] 42 cc-emit-byte [lit] 199 cc-emit-byte ;
: cc-fp-truncate-rdi ( type -- )
  cc-fp-prefix [lit] 72 cc-emit-byte
  [lit] 15 cc-emit-byte [lit] 44 cc-emit-byte [lit] 248 cc-emit-byte ;
: cc-fp-sse ( opcode type -- )
  cc-fp-prefix [lit] 15 cc-emit-byte cc-emit-byte [lit] 193 cc-emit-byte ;
\ Admit floating updates while retaining other targets' scalar-use checks.
: cc-fp-change-check
  cc-last-expr-type @ cc-fp-type? 0= if, cc-change-check-default then, ;
' cc-fp-change-check is cc-change-check-fwd

```
An increment needs a unit at the operand's width. `cc-fp-change-value` loads that unit into XMM1, adds or subtracts it, and returns the rounded payload to the shared lvalue path. That path retains the address and the old postfix value (`forth-bootstrap/cc/127-cc-binary64.fth:96`):
```forth file=cc/127-cc-binary64.fth
\ ++/-- use a same-width 1.0 and retain the operand's floating type.
\ RAX/XMM1 are scratch; the shared lvalue path owns address and old value.
: cc-fp-change-value
  cc-change-type @ cc-fp-type? 0= if, cc-change-value-default exit, then,
  cc-fp-xmm0-from-rdi
  [lit] 72 cc-emit-byte [lit] 184 cc-emit-byte
  cc-change-type @ cc-f32-type? if,
    [lit] 1065353216
  else, [lit] 4607182418800017408 then,
  cc-emit-8le cc-fp-xmm1-from-rax
  cc-change-delta @ [lit] 1 = if, [lit] 88 else, [lit] 92 then,
  cc-change-type @ cc-fp-sse cc-fp-rdi-from-xmm0
  cc-change-type @ cc-emit-convert-rdi ;
' cc-fp-change-value is cc-change-value-fwd

```

## Cross the unsigned boundary

A large unsigned integer cannot be handed directly to a signed SSE conversion. `cc-fp-u64-to-value` branches on the high bit, using `cc-fp-jcc` for the patch. In the high half it converts `(u >> 1) | (u & 1)` and doubles the result: the retained low bit preserves the rounding decision. This rounds directly at the destination precision under nearest-even SSE rounding (`forth-bootstrap/cc/127-cc-binary64.fth:109`):
```forth file=cc/127-cc-binary64.fth
: cc-fp-jcc ( opcode -- patch )
  [lit] 15 cc-emit-byte cc-emit-byte cc-out-pos @ [lit] 0 cc-emit-4le ;
: cc-fp-flip-sign ( type -- )
  [lit] 72 cc-emit-byte [lit] 15 cc-emit-byte [lit] 186 cc-emit-byte
  [lit] 255 cc-emit-byte
  cc-f32-type? if, [lit] 31 else, [lit] 63 then, cc-emit-byte ;
: cc-fp-u64-to-value ( type -- )
  >r
  cc-emit-test-rdi [lit] 137 cc-fp-jcc
  r> swap >r >r
  \ High unsigned half: round the sticky half, then double exactly.
  [lit] 72 cc-emit-byte [lit] 137 cc-emit-byte [lit] 248 cc-emit-byte
  [lit] 72 cc-emit-byte [lit] 209 cc-emit-byte [lit] 232 cc-emit-byte
  [lit] 131 cc-emit-byte [lit] 231 cc-emit-byte [lit] 1 cc-emit-byte
  [lit] 72 cc-emit-byte [lit] 9 cc-emit-byte [lit] 248 cc-emit-byte
  r@ cc-fp-prefix [lit] 72 cc-emit-byte
  [lit] 15 cc-emit-byte [lit] 42 cc-emit-byte [lit] 192 cc-emit-byte
  r@ cc-fp-prefix [lit] 15 cc-emit-byte
  [lit] 88 cc-emit-byte [lit] 192 cc-emit-byte
  r> cc-emit-jmp-rel32-placeholder r> cc-patch-rel32-to-here >r
  cc-fp-signed-from-rdi r> cc-patch-rel32-to-here ;
```
The reverse conversion splits at `2^63`. Below it, signed truncation suffices; above it, subtract the split, truncate, then restore the high bit. `cc-fp-double-to-u64` supports finite inputs whose truncated value is representable, without defining results for out-of-range C conversions (`forth-bootstrap/cc/127-cc-binary64.fth:130`):
```forth file=cc/127-cc-binary64.fth
: cc-fp-double-to-u64
  [lit] 72 cc-emit-byte [lit] 184 cc-emit-byte
  [lit] 4890909195324358656 cc-emit-8le cc-fp-xmm1-from-rax
  [lit] 102 cc-emit-byte [lit] 15 cc-emit-byte
  [lit] 46 cc-emit-byte [lit] 193 cc-emit-byte
  [lit] 130 cc-fp-jcc >r
  ty-double [lit] 0 ty-make dup >r
  [lit] 92 swap cc-fp-sse r@ cc-fp-truncate-rdi r> cc-fp-flip-sign
  cc-emit-jmp-rel32-placeholder r> cc-patch-rel32-to-here >r
  ty-double [lit] 0 ty-make cc-fp-truncate-rdi r> cc-patch-rel32-to-here ;

```

## Convert values, including truth values

A width change uses `cvtss2sd` or `cvtsd2ss`; an identical type emits nothing. Widening is exact, while narrowing rounds at binary32 precision. `cc-bool-type?` separately recognizes a scalar `_Bool` destination (`forth-bootstrap/cc/127-cc-binary64.fth:148`):
```forth file=cc/127-cc-binary64.fth
: cc-fp-width-convert ( source destination -- )
  2dup = if, 2drop exit, then,
  swap cc-fp-prefix [lit] 15 cc-emit-byte [lit] 90 cc-emit-byte
  [lit] 192 cc-emit-byte drop ;
\ C99 _Bool: any nonzero scalar converts to 1, and so does a NaN, which
\ compares unequal to zero. A floating value is zero exactly when its bits
\ without the sign are zero; an integer or pointer is tested at its width.
: cc-bool-type? ( type -- flag ) dup ty-ptr 0= swap ty-base ty-bool = and ;
```
Converting to `_Bool` must test before narrowing. `cc-bool-convert` discards a floating sign bit, making either signed zero false and every other payload true, including NaNs. Integer and pointer sources are tested at their declared width; `setne` followed by zero extension produces the canonical C result (`forth-bootstrap/cc/127-cc-binary64.fth:149`):
```forth file=cc/127-cc-binary64.fth
: cc-bool-convert ( source -- )
  dup cc-bool-type? if, drop exit, then,
  dup cc-fp-type? if,
    cc-f32-type? 0= if, [lit] 72 cc-emit-byte then,
    [lit] 209 cc-emit-byte [lit] 231 cc-emit-byte    \ shl edi/rdi, 1
  else,
    ty-size
    dup [lit] 2 = if, [lit] 102 cc-emit-byte then,
    dup [lit] 8 = if, [lit] 72 cc-emit-byte then,
    [lit] 1 = if, [lit] 64 cc-emit-byte [lit] 132 else, [lit] 133 then,
    cc-emit-byte [lit] 255 cc-emit-byte              \ test dil/di/edi/rdi
  then,
  [lit] 64 cc-emit-byte [lit] 15 cc-emit-byte
  [lit] 149 cc-emit-byte [lit] 199 cc-emit-byte    \ setne dil
  cc-emit-zx-byte-rdi ;
```
`cc-fp-convert` dispatches by both types. It normalizes an integer before conversion, selects the unsigned high-half path when needed, and widens binary32 exactly before reusing the binary64-to-unsigned routine. Non-arithmetic conversions are rejected except for discarding a value as `void` (`forth-bootstrap/cc/127-cc-binary64.fth:164`):
```forth file=cc/127-cc-binary64.fth
: cc-fp-convert ( source destination -- )
  dup cc-bool-type? if, drop cc-bool-convert exit, then,
  2dup cc-fp-type? swap cc-fp-type? or 0= if,
    cc-emit-convert-value-default exit,
  then,
  dup cc-fp-type? if,
    over cc-fp-type? if,
      cc-fp-xmm0-from-rdi 2dup cc-fp-width-convert
      cc-fp-rdi-from-xmm0 nip cc-emit-convert-rdi exit,
    then,
    over cc-const-integer? 0= if, [lit] 232 cc-die then,
    over cc-emit-convert-rdi
    over ty-unsigned? [lit] 2 cc-npick ty-size [lit] 8 = and if,
      dup cc-fp-u64-to-value
    else, dup cc-fp-signed-from-rdi then,
    cc-fp-rdi-from-xmm0 nip cc-emit-convert-rdi
  else,
    dup ty-base ty-void = over ty-ptr 0= and if, 2drop exit, then,
    dup cc-const-integer? 0= if, [lit] 232 cc-die then,
    cc-fp-xmm0-from-rdi
    dup ty-unsigned? over ty-size [lit] 8 = and if,
      swap ty-double [lit] 0 ty-make cc-fp-width-convert
      cc-fp-double-to-u64
    else, swap cc-fp-truncate-rdi then,
    cc-emit-convert-rdi
  then, ;
' cc-fp-convert is cc-emit-convert-value
```
Exchanging RDI with RCX lets `cc-fp-convert-right` reuse it; `cc-fp-initialize` invokes it only when floating types or a `_Bool` destination require it (`forth-bootstrap/cc/127-cc-binary64.fth:191`):
```forth file=cc/127-cc-binary64.fth
: cc-fp-convert-right ( source destination -- )
  2dup cc-fp-type? swap cc-fp-type? or 0= if,
    cc-emit-convert-right-default exit,
  then,
  [lit] 72 cc-emit-byte [lit] 135 cc-emit-byte [lit] 207 cc-emit-byte
  cc-fp-convert
  [lit] 72 cc-emit-byte [lit] 135 cc-emit-byte [lit] 207 cc-emit-byte ;
' cc-fp-convert-right is cc-emit-convert-right
: cc-fp-initialize ( source destination -- )
  2dup cc-fp-type? swap cc-fp-type? or over cc-bool-type? or if,
    cc-fp-convert
  else, 2drop then, ;
' cc-fp-initialize is cc-value-init-fwd
```

## Return a floating result

At a return boundary, a floating payload belongs in XMM0. `cc-fp-return` moves it there, and `cc-fp-result` retrieves it after a call; integer returns keep their existing route. These extend the call sequence (Chapter 41) (`forth-bootstrap/cc/127-cc-binary64.fth:204`):
```forth file=cc/127-cc-binary64.fth
: cc-fp-return
  cc-native-return-type @ cc-fp-type? if,
    cc-fp-xmm0-from-rdi
  else, cc-emit-mov-rax-rdi then, ;
' cc-fp-return is cc-value-return-fwd
: cc-fp-result ( type -- )
  dup cc-fp-type? if, cc-fp-rdi-from-xmm0 then, cc-emit-convert-rdi ;
' cc-fp-result is cc-sysv-result-value-fwd

```
The argument parser still calls the rejecting default scalar check at `forth-bootstrap/cc/121-cc-sysv.fth:1009`, even after this layer replaces the general scalar hook. Chapter 49 supplies the shared argument planner.

## Compute at the common precision

Mixed arithmetic needs a common precision. `cc-fp-common-type` chooses double if either floating operand is double, otherwise float; the other operand must be arithmetic. Integer-only expressions retain their existing rule (`forth-bootstrap/cc/127-cc-binary64.fth:213`):
```forth file=cc/127-cc-binary64.fth
: cc-fp-common-type ( left right -- type )
  2dup cc-fp-type? swap cc-fp-type? or if,
    over cc-fp-type? over cc-fp-type? and 0= if,
      over cc-fp-type? if, dup else, over then,
      cc-const-integer? 0= if, [lit] 232 cc-die then,
    then,
    cc-f64-type? swap cc-f64-type? or if, ty-double else, ty-float then,
    [lit] 0 ty-make
  else, cc-expr-common-type-default then, ;
' cc-fp-common-type is cc-expr-common-type
```
An unordered comparison sets flags that also resemble equality and less-than. `cc-fp-comparison-flags` masks those results with orderedness, or adds unorderedness for `!=`. Greater-than and greater-or-equal already exclude the unordered flag combination. `cc-fp-comparison` selects `ucomiss` or `ucomisd` (`forth-bootstrap/cc/127-cc-binary64.fth:223`):
```forth file=cc/127-cc-binary64.fth
: cc-fp-comparison-flags ( op -- )
  dup [char] > = if, drop [lit] 151 else,
  dup pt-ge = if, drop [lit] 147 else,
  dup [char] < = if, drop [lit] 146 else,
  dup pt-le = if, drop [lit] 150 else,
  dup pt-eq-eq = if, drop [lit] 148 else,
  pt-bang-eq = if, [lit] 149 else, [lit] 232 cc-die then,
  then, then, then, then, then,
  dup [lit] 15 cc-emit-byte cc-emit-byte [lit] 192 cc-emit-byte
  dup [lit] 146 = over [lit] 150 = or over [lit] 148 = or if,
    [lit] 15 cc-emit-byte [lit] 155 cc-emit-byte [lit] 194 cc-emit-byte
    [lit] 32 cc-emit-byte [lit] 208 cc-emit-byte
  then,
  [lit] 149 = if,
    [lit] 15 cc-emit-byte [lit] 154 cc-emit-byte [lit] 194 cc-emit-byte
    [lit] 8 cc-emit-byte [lit] 208 cc-emit-byte
  then,
  [lit] 15 cc-emit-byte [lit] 182 cc-emit-byte [lit] 248 cc-emit-byte ;
: cc-fp-comparison ( op -- )
  cc-expr-common @ cc-f64-type? if, [lit] 102 cc-emit-byte then, [lit] 15 cc-emit-byte
  [lit] 46 cc-emit-byte [lit] 193 cc-emit-byte
  cc-fp-comparison-flags ;
```
With converted operands in XMM0 and XMM1, `cc-fp-binop` chooses addition, subtraction, multiplication or division; other supported operators enter comparison. Each scalar arithmetic instruction rounds at the common precision, and its result returns immediately to RDI (`forth-bootstrap/cc/127-cc-binary64.fth:245`):
```forth file=cc/127-cc-binary64.fth
: cc-fp-binop
  cc-expr-left-type @ cc-fp-type? cc-expr-right-type @ cc-fp-type? or 0= if,
    cc-native-binop-emit-default exit,
  then,
  cc-fp-xmm0-from-rdi cc-fp-xmm1-from-rcx
  cc-expr-op-row @ bo-op + @
  dup [char] + = if, drop [lit] 88 else,
  dup [char] - = if, drop [lit] 92 else,
  dup [char] * = if, drop [lit] 89 else,
  dup [char] / = if, drop [lit] 94 else,
    cc-fp-comparison exit,
  then, then, then, then,
  cc-expr-common @ cc-fp-sse cc-fp-rdi-from-xmm0 ;
' cc-fp-binop is cc-native-binop-emit

```
Arithmetic and narrowing here assume the normal nearest-even SSE environment with gradual underflow. This layer emits no floating-environment controls.

## Test and reject by value category

A condition must recognize zero without changing the value. `cc-fp-test` shifts a scratch copy to discard the sign; `cc-fp-not` converts that test to C's logical result. This makes negative zero false while keeping NaNs true (`forth-bootstrap/cc/127-cc-binary64.fth:260`):
```forth file=cc/127-cc-binary64.fth
: cc-fp-test
  cc-last-expr-type @ cc-fp-type? if,
    \ Clear only the sign in a scratch value; both signed zeros are false.
    cc-last-expr-type @ cc-f64-type? if, [lit] 72 cc-emit-byte then,
    [lit] 137 cc-emit-byte [lit] 248 cc-emit-byte
    cc-last-expr-type @ cc-f64-type? if, [lit] 72 cc-emit-byte then,
    [lit] 209 cc-emit-byte [lit] 224 cc-emit-byte
    cc-last-expr-type @ cc-f64-type? if, [lit] 72 cc-emit-byte then,
    [lit] 133 cc-emit-byte [lit] 192 cc-emit-byte
  else, cc-emit-test-rdi then, ;
' cc-fp-test is cc-value-test-fwd
: cc-fp-not
  cc-last-expr-type @ cc-fp-type? if,
    cc-fp-test
    [lit] 15 cc-emit-byte [lit] 148 cc-emit-byte [lit] 192 cc-emit-byte
    [lit] 15 cc-emit-byte [lit] 182 cc-emit-byte [lit] 248 cc-emit-byte
  else, cc-emit-not-zero-flag then, ;
' cc-fp-not is cc-value-not-fwd
```
The remaining hooks distinguish payload operations from integer-only operations (`forth-bootstrap/cc/127-cc-binary64.fth:278`):

| Input operation | Result or handler |
|---|---|
| Unary minus | `cc-fp-negate` flips only the sign |
| Bitwise complement | `cc-fp-complement` rejects floating operands |
| Conditional expression | `cc-fp-ternary` leaves selected-arm conversion to the expression parser |
| Integer-only use or mapped-mode static initialization | `cc-fp-integer-use` rejects floating values |
```forth file=cc/127-cc-binary64.fth
: cc-fp-negate
  cc-last-expr-type @ cc-fp-type? if, cc-last-expr-type @ cc-fp-flip-sign else, cc-emit-neg-rdi then, ;
' cc-fp-negate is cc-value-negate-fwd
: cc-fp-complement
  cc-last-expr-type @ cc-fp-type? if, [lit] 232 cc-die then, cc-emit-not-rdi ;
' cc-fp-complement is cc-value-complement-fwd
\ Conditional arms use cc-fp-common-type and selected-arm conversions in100.
: cc-fp-ternary ;
' cc-fp-ternary is cc-value-ternary-fwd

: cc-fp-integer-use ( type -- )
  cc-fp-type? if, [lit] 232 cc-die then, ;
' cc-fp-integer-use is cc-value-integer-use-fwd
' cc-fp-integer-use is cc-value-static-init-fwd
```

## Build literal bits without floating arithmetic

The seed and the Forth layers have no floating-point words, and the decoder uses only integer Forth operations (`forth-bootstrap/cc/128-cc-float-literal.fth:2`). The bits of a literal therefore never depend on the host's FPU or C library: every machine produces the same encoding, as a reproducible bootstrap requires. The decoder does exact integer arithmetic and rounds once.

The literal `0.1` becomes an exact integer ratio, then rounds once to the requested format. The returned cell is either a scalar encoding or an address for an extended constant; Chapter 49 owns extended runtime operations (`forth-bootstrap/cc/128-cc-float-literal.fth:1`):
```forth file=cc/128-cc-float-literal.fth
\ 128-cc-float-literal.fth -- exact binary32/binary64/extended constants.
\ Only integer Forth operations participate in parsing or rounding. The
\ returned cell is an IEEE encoding or an extended-object address.
\ One exact ratio rounds literals and constant arithmetic for 125.
\ Requires 010 and 020; production loads it after the scalar value layer.
\ Hooks: cc-fp-decimal-fwd, cc-fp-integer-fwd, cc-fp-resize-fwd,
\ cc-fp-arith-fwd and cc-fp-truncate-fwd (all deferred words).

```
Invalid spelling and unrepresentable values have distinct diagnostics (`forth-bootstrap/cc/128-cc-float-literal.fth:9`):
```forth file=cc/128-cc-float-literal.fth
create cc-f64-error-prefix s, cc-f64-literal: bl c,
here cc-f64-error-prefix - constant cc-f64-error-prefix-len
create cc-f64-error-malformed s, malformed nl c,
here cc-f64-error-malformed - constant cc-f64-error-malformed-len
create cc-f64-error-suffix s, suffix-unsupported nl c,
here cc-f64-error-suffix - constant cc-f64-error-suffix-len
create cc-f64-error-hex s, hexfloat-unsupported nl c,
here cc-f64-error-hex - constant cc-f64-error-hex-len
create cc-f64-error-token s, token-limit nl c,
here cc-f64-error-token - constant cc-f64-error-token-len
create cc-f64-error-digits s, digit-limit nl c,
here cc-f64-error-digits - constant cc-f64-error-digits-len
create cc-f64-error-exponent s, exponent-limit nl c,
here cc-f64-error-exponent - constant cc-f64-error-exponent-len
create cc-f64-error-overflow s, overflow nl c,
here cc-f64-error-overflow - constant cc-f64-error-overflow-len
create cc-f64-error-workspace s, workspace-limit nl c,
here cc-f64-error-workspace - constant cc-f64-error-workspace-len
: cc-f64-fail ( address length -- )
  cc-f64-error-prefix cc-f64-error-prefix-len cc-err-write
  cc-err-write [lit] 248 die ;
: cc-f64-malformed
  cc-f64-error-malformed cc-f64-error-malformed-len cc-f64-fail ;
: cc-f64-overflow
  cc-f64-error-overflow cc-f64-error-overflow-len cc-f64-fail ;

```

## Keep every accepted digit

The exact ratio uses counted, little-endian limb buffers `cc-f64-n` and `cc-f64-d` (`forth-bootstrap/cc/128-cc-float-literal.fth:35`):
```forth file=cc/128-cc-float-literal.fth
\ Big integers are a used-limb count followed by 2048 little-endian limbs.
\ Each 32-bit limb occupies a cell, so multiply-by-ten plus carry fits
\ comfortably in an unsigned seed cell. Zero has no used limbs. Bytes
\ outside the used prefix are never read. Operations preserve this form.
[lit] 2048 constant cc-f64-limb-cap
[lit] 4294967296 constant cc-f64-radix
[lit] 4294967295 constant cc-f64-mask
[lit] 16392 constant cc-f64-big-size
create cc-f64-n cc-f64-big-size allot
create cc-f64-d cc-f64-big-size allot
variable cc-f64-bi-a
variable cc-f64-bi-b
variable cc-f64-bi-i
variable cc-f64-bi-m
variable cc-f64-bi-carry
: cc-f64-bi-cell ( big index -- address ) [lit] 1 + [lit] 8 * + ;
: cc-f64-bi-get ( big index -- limb )
  over @ over > if, cc-f64-bi-cell @ else, 2drop [lit] 0 then, ;
: cc-f64-bi-zero ( big -- ) [lit] 0 swap ! ;
```
Trimmed high zeros make length comparisons valid; checked appends bound the workspace (`forth-bootstrap/cc/128-cc-float-literal.fth:54`):
```forth file=cc/128-cc-float-literal.fth
: cc-f64-bi-trim ( big -- )
  begin, dup @ while,
    dup dup @ 1- cc-f64-bi-cell @ if, drop exit, then,
    [lit] 1 over -!
  repeat, drop ;
: cc-f64-bi-append ( limb big -- )
  dup @ cc-f64-limb-cap >= if,
    cc-f64-error-workspace cc-f64-error-workspace-len cc-f64-fail
  then,
  2dup dup @ cc-f64-bi-cell ! [lit] 1 swap +! drop ;
```
Each decimal digit extends the coefficient by multiply-and-add with carry (`forth-bootstrap/cc/128-cc-float-literal.fth:64`):
```forth file=cc/128-cc-float-literal.fth
: cc-f64-bi-muladd ( big multiplier carry -- )
  cc-f64-bi-carry ! cc-f64-bi-m ! cc-f64-bi-a !
  [lit] 0 cc-f64-bi-i !
  begin, cc-f64-bi-i @ cc-f64-bi-a @ @ < while,
    cc-f64-bi-a @ cc-f64-bi-i @ cc-f64-bi-cell
    dup @ cc-f64-bi-m @ * cc-f64-bi-carry @ +
    dup cc-f64-radix / cc-f64-bi-carry !
    cc-f64-mask and swap !
    [lit] 1 cc-f64-bi-i +!
  repeat,
  cc-f64-bi-carry @ if,
    cc-f64-bi-carry @ cc-f64-bi-a @ cc-f64-bi-append
  then, ;
```

## Compare exact magnitudes

The first unequal high limb decides an equal-length magnitude comparison (`forth-bootstrap/cc/128-cc-float-literal.fth:77`):
```forth file=cc/128-cc-float-literal.fth
: cc-f64-bi-compare ( a b -- comparison )
  cc-f64-bi-b ! cc-f64-bi-a !
  cc-f64-bi-a @ @ cc-f64-bi-b @ @ < if, true exit, then,
  cc-f64-bi-a @ @ cc-f64-bi-b @ @ > if, [lit] 1 exit, then,
  cc-f64-bi-a @ @ cc-f64-bi-i !
  begin, cc-f64-bi-i @ while,
    [lit] 1 cc-f64-bi-i -!
    cc-f64-bi-a @ cc-f64-bi-i @ cc-f64-bi-get
    cc-f64-bi-b @ cc-f64-bi-i @ cc-f64-bi-get
    2dup < if, 2drop true exit, then,
    > if, [lit] 1 exit, then,
  repeat, [lit] 0 ;
```
Exact remainder subtraction requires the left magnitude to be at least the right (`forth-bootstrap/cc/128-cc-float-literal.fth:89`):
```forth file=cc/128-cc-float-literal.fth
: cc-f64-bi-subtract ( a b -- )
  \ Caller proves a >= b. The signed temporary is in [-2^32, 2^32-1].
  cc-f64-bi-b ! cc-f64-bi-a !
  [lit] 0 cc-f64-bi-carry ! [lit] 0 cc-f64-bi-i !
  begin, cc-f64-bi-i @ cc-f64-bi-a @ @ < while,
    cc-f64-bi-a @ cc-f64-bi-i @ cc-f64-bi-get
    cc-f64-bi-b @ cc-f64-bi-i @ cc-f64-bi-get -
    cc-f64-bi-carry @ - dup 0< if,
      cc-f64-radix + [lit] 1 cc-f64-bi-carry !
    else, [lit] 0 cc-f64-bi-carry ! then,
    cc-f64-bi-a @ cc-f64-bi-i @ cc-f64-bi-cell !
    [lit] 1 cc-f64-bi-i +!
  repeat,
  cc-f64-bi-a @ cc-f64-bi-trim ;
```
Bit lengths estimate the exponent; checked scaling supplies powers of two and ten (`forth-bootstrap/cc/128-cc-float-literal.fth:103`):
```forth file=cc/128-cc-float-literal.fth
: cc-f64-bi-bits ( big -- bits )
  dup @ 0= if, drop [lit] 0 exit, then,
  dup @ 1- dup [lit] 32 * >r cc-f64-bi-get
  begin, dup while, [lit] 2 / r> 1+ >r repeat, drop r> ;
: cc-f64-bi-shift ( big count -- )
  begin, dup while,
    >r dup [lit] 2 [lit] 0 cc-f64-bi-muladd r> 1-
  repeat, 2drop ;
: cc-f64-bi-ten-power ( big count -- )
  begin, dup while,
    >r dup [lit] 10 [lit] 0 cc-f64-bi-muladd r> 1-
  repeat, 2drop ;

```

## Read the coefficient and exponent

Parser state keeps decimal position separate from binary normalization and rounding (`forth-bootstrap/cc/128-cc-float-literal.fth:116`):
```forth file=cc/128-cc-float-literal.fth
\ The grammar is ((digits '.' digits?) | ('.' digits) | digits)
\ followed by an optional e/E and signed decimal exponent. A point or
\ exponent is mandatory. A unary sign belongs to the expression parser.
\ Limit: 4096 token bytes; 768 digits from the first nonzero mantissa
\ digit through its last digit; exponent magnitude at most 1,000,000.
variable cc-f64-allow-hex
variable cc-f64-hex
variable cc-f64-p
variable cc-f64-left
variable cc-f64-point
variable cc-f64-any-digit
variable cc-f64-significant
variable cc-f64-format
variable cc-f64-fractional
variable cc-f64-exponent
variable cc-f64-exponent-negative
variable cc-f64-has-exponent
variable cc-f64-scale
variable cc-f64-order
variable cc-f64-e
variable cc-f64-q-carry
variable cc-f64-q
: cc-f64-peek ( -- character )
  cc-f64-left @ if, cc-f64-p @ c@ else, [lit] 0 then, ;
: cc-f64-advance
  [lit] 1 cc-f64-p +! [lit] 1 cc-f64-left -! ;
```
For `0.1`, the leading zero is skipped and the fractional digit becomes the coefficient; trailing zeros after a nonzero digit still count toward the limit (`forth-bootstrap/cc/128-cc-float-literal.fth:142`):
```forth file=cc/128-cc-float-literal.fth
: cc-f64-mantissa
  begin, cc-f64-left @ while,
    cc-f64-peek dup digit? if,
      [char] 0 - true cc-f64-any-digit !
      cc-f64-point @ if, [lit] 1 cc-f64-fractional +! then,
      dup cc-f64-significant @ or if,
        [lit] 1 cc-f64-significant +!
        cc-f64-significant @ [lit] 768 > if,
          cc-f64-error-digits cc-f64-error-digits-len cc-f64-fail
        then,
        cc-f64-n [lit] 10 rot cc-f64-bi-muladd
      else, drop then,
      cc-f64-advance
    else,
      [char] . = if,
        cc-f64-point @ if, cc-f64-malformed then,
        true cc-f64-point ! cc-f64-advance
      else, exit, then,
    then,
  repeat, ;
```
An exponent marker requires digits after its optional sign; `p/P` replaces `e/E` for hexadecimal input (`forth-bootstrap/cc/128-cc-float-literal.fth:162`):
```forth file=cc/128-cc-float-literal.fth
: cc-f64-read-exponent
  cc-f64-peek cc-f64-hex @ if,
    dup [char] p = swap [char] P = or
  else, dup [char] e = swap [char] E = or then, 0= if, exit, then,
  true cc-f64-has-exponent ! cc-f64-advance
  cc-f64-peek dup [char] - = if,
    true cc-f64-exponent-negative !
  then,
  dup [char] - = swap [char] + = or if, cc-f64-advance then,
  cc-f64-peek digit? 0= if, cc-f64-malformed then,
  begin, cc-f64-peek digit? while,
    cc-f64-exponent @ [lit] 10 * cc-f64-peek [char] 0 - +
    dup [lit] 1000000 > if,
      cc-f64-error-exponent cc-f64-error-exponent-len cc-f64-fail
    then, cc-f64-exponent ! cc-f64-advance
  repeat,
  cc-f64-exponent-negative @ if,
    [lit] 0 cc-f64-exponent @ - cc-f64-exponent !
  then, ;
```

## Validate the complete spelling

Extended hexadecimal mantissas accumulate in radix sixteen, counting fractional position in binary shifts (`forth-bootstrap/cc/128-cc-float-literal.fth:181`):
```forth file=cc/128-cc-float-literal.fth
: cc-f80-hex-digit? ( character -- flag )
  dup digit? if, drop true exit, then,
  dup [char] a >= over [char] f <= and if, drop true exit, then,
  dup [char] A >= swap [char] F <= and ;
: cc-f80-hex-value ( character -- digit )
  dup digit? if, [char] 0 - exit, then,
  dup [char] a >= if, [char] a else, [char] A then, - [lit] 10 + ;
: cc-f80-hex-mantissa
  cc-f64-advance cc-f64-advance
  begin, cc-f64-left @ while,
    cc-f64-peek dup cc-f80-hex-digit? if,
      cc-f80-hex-value true cc-f64-any-digit !
      cc-f64-point @ if, [lit] 4 cc-f64-fractional +! then,
      dup cc-f64-significant @ or if,
      [lit] 1 cc-f64-significant +!
      cc-f64-significant @ [lit] 768 > if,
        cc-f64-error-digits cc-f64-error-digits-len cc-f64-fail
      then,
      cc-f64-n [lit] 16 rot cc-f64-bi-muladd
      else, drop then, cc-f64-advance
    else,
      [char] . = if,
        cc-f64-point @ if, cc-f64-malformed then,
        true cc-f64-point ! cc-f64-advance
      else, exit, then,
    then,
  repeat, ;
```
Complete-spelling validation checks token limits and grammar even for zero or underflow; scalar hexadecimal input and leftover suffixes are rejected, while unary signs belong to the expression parser (`forth-bootstrap/cc/128-cc-float-literal.fth:208`):
```forth file=cc/128-cc-float-literal.fth
: cc-f64-spelling ( address length -- )
  dup [lit] 4096 > if,
    cc-f64-error-token cc-f64-error-token-len cc-f64-fail
  then,
  cc-f64-left ! cc-f64-p !
  [lit] 0 cc-f64-hex !
  cc-f64-left @ [lit] 2 >= if,
    cc-f64-p @ c@ [char] 0 =
    cc-f64-p @ 1+ c@ dup [char] x = swap [char] X = or and if,
      cc-f64-allow-hex @ 0= if,
        cc-f64-error-hex cc-f64-error-hex-len cc-f64-fail
      then, true cc-f64-hex !
    then,
  then,
  [lit] 0 cc-f64-point ! [lit] 0 cc-f64-any-digit !
  [lit] 0 cc-f64-significant ! [lit] 0 cc-f64-fractional !
  [lit] 0 cc-f64-exponent ! [lit] 0 cc-f64-exponent-negative !
  [lit] 0 cc-f64-has-exponent !
  cc-f64-n cc-f64-bi-zero cc-f64-d cc-f64-bi-zero
  [lit] 1 cc-f64-d cc-f64-bi-append
  cc-f64-hex @ if, cc-f80-hex-mantissa else, cc-f64-mantissa then,
  cc-f64-any-digit @ 0= if, cc-f64-malformed then,
  cc-f64-read-exponent
  cc-f64-hex @ cc-f64-has-exponent @ 0= and if, cc-f64-malformed then,
  cc-f64-left @ if,
    cc-f64-peek dup [char] f = over [char] F = or
    over [char] l = or swap [char] L = or if,
      cc-f64-error-suffix cc-f64-error-suffix-len cc-f64-fail
    then, cc-f64-malformed
  then,
  cc-f64-point @ cc-f64-has-exponent @ or 0= if, cc-f64-malformed then, ;
```

## Normalize, then settle the rounding tie

For `0.1`, normalization preserves `value = N/D * 2^e`, bringing `1/10` to `8/5 * 2^-4` without losing a digit (`forth-bootstrap/cc/128-cc-float-literal.fth:239`):
```forth file=cc/128-cc-float-literal.fth

\ Exact x = N/D * 2^e. Initial decimal order rejects obvious overflow
\ and zero before constructing powers. Extended precision also admits
\ decimal orders through 4932 and down to -4951. The checked 65536-bit
\ workspace covers their ratios and full-range constant sums.
: cc-f64-normalize
  cc-f64-n cc-f64-bi-bits cc-f64-d cc-f64-bi-bits - cc-f64-e !
  cc-f64-e @ 0< if,
    cc-f64-n [lit] 0 cc-f64-e @ - cc-f64-bi-shift
  else, cc-f64-d cc-f64-e @ cc-f64-bi-shift then,
  cc-f64-n cc-f64-d cc-f64-bi-compare 0< if,
    cc-f64-n [lit] 1 cc-f64-bi-shift [lit] 1 cc-f64-e -!
  then, ;
```
Repeated doubling and exact remainder comparison produce the binary64 quotient 7205759403792793 with remainder `3/5`; twice that remainder exceeds unity, so rounding increments the quotient (`forth-bootstrap/cc/128-cc-float-literal.fth:252`):
```forth file=cc/128-cc-float-literal.fth
: cc-f64-quotient ( fractional-bits -- )
  \ N/D is in [1,2). At every step q is the integer prefix and
  \ 0 <= N < D is the exact remainder; no sticky bit is approximated.
  [lit] 0 cc-f64-q-carry !
  [lit] 1 cc-f64-q ! cc-f64-n cc-f64-d cc-f64-bi-subtract
  begin, dup while,
    >r cc-f64-n [lit] 1 cc-f64-bi-shift
    cc-f64-q @ [lit] 2 * cc-f64-q !
    cc-f64-n cc-f64-d cc-f64-bi-compare 0< 0= if,
      cc-f64-n cc-f64-d cc-f64-bi-subtract [lit] 1 cc-f64-q +!
    then, r> 1-
  repeat, drop
  cc-f64-n [lit] 1 cc-f64-bi-shift
  cc-f64-n cc-f64-d cc-f64-bi-compare
  dup [lit] 0 > swap 0= cc-f64-q @ [lit] 1 and and or if,
    [lit] 1 cc-f64-q +!
    cc-f64-q @ 0= cc-f64-q-carry !
  then, ;
```
A halfway remainder increments only an odd retained quotient: round to nearest, ties to even, as in [the changed midpoint prediction](#derive-unity-and-its-neighbour). `cc-f64-q-carry` records a full-cell wrap.

## Select the destination before rounding

The destination record selects fraction width, leading unit, exponent limits and sign mask before rounding; a suffixed float rounds directly to binary32 to avoid double rounding near a midpoint (`forth-bootstrap/cc/128-cc-float-literal.fth:278`):
```forth file=cc/128-cc-float-literal.fth
\ A format names an encoding by its byte size: 8 selects binary64 and
\ 4 binary32, and 16 extended precision. One exact ratio serves all three
\ widths. Each caller selects its format before it rounds.
variable cc-f64-fraction
variable cc-f64-unit
variable cc-f64-emin
variable cc-f64-emax
variable cc-f64-sign
: cc-f64-use ( format -- )
  dup cc-f64-format !
  dup [lit] 16 = if,
    drop [lit] 63 cc-f64-fraction ! 2^63 cc-f64-unit !
    [lit] 16383 cc-f64-emax ! [lit] 0 [lit] 16382 - cc-f64-emin !
    [lit] 32768 cc-f64-sign ! exit,
  then,
  [lit] 4 = if,
    [lit] 23 [lit] 8388608 [lit] 127 [lit] 2147483648
  else,
    [lit] 52 [lit] 4503599627370496 [lit] 1023 2^63
  then,
  cc-f64-sign ! dup cc-f64-emax ! [lit] 1 swap - cc-f64-emin !
  cc-f64-unit ! cc-f64-fraction ! ;

```
Extended constants store an explicit significand and sign/exponent field, handling subnormals, carry and overflow to infinity (`forth-bootstrap/cc/128-cc-float-literal.fth:293`):
```forth file=cc/128-cc-float-literal.fth
: cc-f80-allocate ( significand sign-exponent -- bits )
  [lit] 16 cc-alloc dup >r [lit] 8 + ! r@ ! r> ;
: cc-f80-round ( -- bits )
  cc-f64-e @ [lit] 0 [lit] 16446 - < if, [lit] 0 [lit] 0 cc-f80-allocate exit, then,
  cc-f64-e @ [lit] 0 [lit] 16446 - = if,
    cc-f64-n cc-f64-d cc-f64-bi-compare 0= if, [lit] 0 else, [lit] 1 then,
    [lit] 0 cc-f80-allocate exit,
  then,
  cc-f64-e @ [lit] 0 [lit] 16382 - < if,
    cc-f64-e @ [lit] 16445 + cc-f64-quotient
    cc-f64-q @ dup 0< if, [lit] 1 else, [lit] 0 then, cc-f80-allocate exit,
  then,
  [lit] 63 cc-f64-quotient
  cc-f64-q-carry @ if, 2^63 cc-f64-q ! [lit] 1 cc-f64-e +! then,
  cc-f64-e @ [lit] 16383 > if, 2^63 [lit] 32767 cc-f80-allocate exit, then,
  cc-f64-q @ cc-f64-e @ [lit] 16383 + cc-f80-allocate ;
```
Scalar rounding reduces subnormal precision, increments the exponent on significand carry, and diagnoses overflow instead of returning infinity (`forth-bootstrap/cc/128-cc-float-literal.fth:310`):
```forth file=cc/128-cc-float-literal.fth
\ Round N/D * 2^e, with N/D in [1,2), once to the selected format.
: cc-f64-round ( -- bits )
  cc-f64-format @ [lit] 16 = if, cc-f80-round exit, then,
  cc-f64-emin @ cc-f64-fraction @ - 1- >r
  cc-f64-e @ r@ < if, r> drop [lit] 0 exit, then,
  cc-f64-e @ r> = if,
    \ Exactly half the minimum subnormal rounds to even zero.
    cc-f64-n cc-f64-d cc-f64-bi-compare 0= if,
      [lit] 0 else, [lit] 1 then, exit,
  then,
  cc-f64-e @ cc-f64-emin @ < if,
    cc-f64-e @ cc-f64-emin @ - cc-f64-fraction @ + cc-f64-quotient
    cc-f64-q @ exit,
  then,
  cc-f64-fraction @ cc-f64-quotient
  cc-f64-q @ cc-f64-unit @ [lit] 2 * = if,
    cc-f64-q @ [lit] 2 / cc-f64-q ! [lit] 1 cc-f64-e +!
  then,
  cc-f64-e @ cc-f64-emax @ > if, cc-f64-overflow then,
  cc-f64-e @ cc-f64-emax @ + cc-f64-unit @ *
  cc-f64-q @ cc-f64-unit @ - + ;

```
Exactly half the smallest subnormal rounds to even zero; a larger ratio at that exponent rounds to the minimum subnormal. Rounding the largest subnormal upward produces the smallest normal encoding.

## Finish the decimal ratio

For `0.1`, written exponent minus fractional digit count gives negative scale, so the decoder scales D to form `1/10` before normalization and rounding (`forth-bootstrap/cc/128-cc-float-literal.fth:331`):
```forth file=cc/128-cc-float-literal.fth
: cc-f64-decode ( address length -- bits )
  cc-f64-spelling
  cc-f64-n @ 0= if,
    cc-f64-format @ [lit] 16 = if, [lit] 0 [lit] 0 cc-f80-allocate else, [lit] 0 then, exit,
  then,
  cc-f64-hex @ if,
    cc-f64-normalize
    cc-f64-exponent @ cc-f64-fractional @ - cc-f64-e +! cc-f64-round exit,
  then,
  cc-f64-exponent @ cc-f64-fractional @ - cc-f64-scale !
  cc-f64-significant @ cc-f64-scale @ + 1- cc-f64-order !
  cc-f64-order @ cc-f64-format @ [lit] 16 = if, [lit] 4932 else, [lit] 308 then, > if,
    cc-f64-format @ [lit] 16 = if, 2^63 [lit] 32767 cc-f80-allocate exit, then,
    cc-f64-overflow
  then,
  cc-f64-order @ cc-f64-format @ [lit] 16 = if, [lit] 0 [lit] 4951 - else, [lit] 0 [lit] 324 - then, < if,
    cc-f64-format @ [lit] 16 = if, [lit] 0 [lit] 0 cc-f80-allocate else, [lit] 0 then, exit,
  then,
  cc-f64-scale @ 0< if,
    cc-f64-d [lit] 0 cc-f64-scale @ - cc-f64-bi-ten-power
  else, cc-f64-n cc-f64-scale @ cc-f64-bi-ten-power then,
  cc-f64-normalize cc-f64-round ;

: cc-f64-decimal ( address length format -- bits )
  dup [lit] 16 = cc-f64-allow-hex ! cc-f64-use cc-f64-decode ;
: cc-f64-parse ( address length -- bits ) [lit] 8 cc-f64-decimal ;

```
Decimal order is significant count plus scale minus one. Scalar orders above 308 fail and those below -324 return zero; boundary orders use exact conversion. These broad gates also bound binary32, whose narrower overflow is checked during rounding. `cc-f64-decimal` takes an explicit format; `cc-f64-parse` fixes binary64.

## Reuse the ratio for constant operations

Constant operations reuse the exact ratio, with limb copies and multiplication scratch space (`forth-bootstrap/cc/128-cc-float-literal.fth:358`):
```forth file=cc/128-cc-float-literal.fth
\ Constant arithmetic (125) uses the same ratio. An encoding splits into
\ a sign and integers M and E with magnitude M * 2^E. Each operation is
\ exact on those integers, so cc-f64-round is its only rounding step.
create cc-f64-t cc-f64-big-size allot
: cc-f64-bi-set ( value big -- )
  >r r@ cc-f64-bi-zero
  dup cc-f64-mask and r@ cc-f64-bi-append
  cc-f64-radix / r@ cc-f64-bi-append r> cc-f64-bi-trim ;
: cc-f64-bi-copy ( from to -- )
  cc-f64-bi-b ! cc-f64-bi-a ! [lit] 0 cc-f64-bi-i !
  begin, cc-f64-bi-i @ cc-f64-bi-a @ @ > 0= while,
    cc-f64-bi-a @ cc-f64-bi-i @ [lit] 8 * + @
    cc-f64-bi-b @ cc-f64-bi-i @ [lit] 8 * + !
    [lit] 1 cc-f64-bi-i +!
  repeat, ;
```
Magnitude addition retains the final carry even when it extends the destination (`forth-bootstrap/cc/128-cc-float-literal.fth:373`):
```forth file=cc/128-cc-float-literal.fth
: cc-f64-bi-add ( a b -- )
  cc-f64-bi-b ! cc-f64-bi-a !
  [lit] 0 cc-f64-bi-carry ! [lit] 0 cc-f64-bi-i !
  begin,
    cc-f64-bi-i @ cc-f64-bi-a @ @ < cc-f64-bi-i @ cc-f64-bi-b @ @ < or
  while,
    cc-f64-bi-a @ cc-f64-bi-i @ cc-f64-bi-get
    cc-f64-bi-b @ cc-f64-bi-i @ cc-f64-bi-get + cc-f64-bi-carry @ +
    dup cc-f64-radix / cc-f64-bi-carry ! cc-f64-mask and
    cc-f64-bi-i @ cc-f64-bi-a @ @ < if,
      cc-f64-bi-a @ cc-f64-bi-i @ cc-f64-bi-cell !
    else, cc-f64-bi-a @ cc-f64-bi-append then,
    [lit] 1 cc-f64-bi-i +!
  repeat,
  cc-f64-bi-carry @ if,
    cc-f64-bi-carry @ cc-f64-bi-a @ cc-f64-bi-append
  then, ;
```
`cc-f64-bi-times` splits a full-cell multiplier to keep limb products within a cell; `cc-f64-power` supplies powers for truncation (`forth-bootstrap/cc/128-cc-float-literal.fth:390`):
```forth file=cc/128-cc-float-literal.fth
\ Multiply by a full cell in two 32-bit halves: big*hi*2^32 + big*lo.
: cc-f64-bi-times ( big value -- )
  over cc-f64-t cc-f64-bi-copy
  cc-f64-t over cc-f64-radix / [lit] 0 cc-f64-bi-muladd
  cc-f64-t cc-f64-bi-trim cc-f64-t [lit] 32 cc-f64-bi-shift
  over swap cc-f64-mask and [lit] 0 cc-f64-bi-muladd
  dup cc-f64-bi-trim cc-f64-t cc-f64-bi-add ;
: cc-f64-power ( n -- 2^n )
  [lit] 1 swap begin, dup while, swap [lit] 2 * swap 1- repeat, drop ;

```

## Separate sign, significand and exponent

For finite binary32/binary64 values, the sign test and unpacker recover sign and magnitude `M * 2^e`, restoring the implicit unit only for normals. Here `M` is an integer significand; its scale is `e = E-B-p` for normals and `e = 1-B-p` for subnormals, using the stored field `E` from the opening layout (`forth-bootstrap/cc/128-cc-float-literal.fth:400`):
```forth file=cc/128-cc-float-literal.fth
: cc-f64-negative? ( bits -- flag )
  cc-f64-format @ [lit] 16 = if, [lit] 8 + @ then,
  cc-f64-sign @ and 0= 0= ;
\ A zero exponent field reads as field one without the hidden unit.
: cc-f64-unpack ( bits -- significand exponent )
  cc-f64-format @ [lit] 16 = if,
    dup @ swap [lit] 8 + @ [lit] 32767 and dup 0= if, drop [lit] 1 then,
    [lit] 16446 - exit,
  then,
  cc-f64-sign @ 1- and
  dup cc-f64-unit @ 1- and swap cc-f64-unit @ /
  dup if, swap cc-f64-unit @ + swap else, drop [lit] 1 then,
  cc-f64-emax @ - cc-f64-fraction @ - ;
```
Packing normalizes and rounds the exact ratio before attaching the sign, including for zero (`forth-bootstrap/cc/128-cc-float-literal.fth:413`):
```forth file=cc/128-cc-float-literal.fth
\ Round N/D * 2^exponent and apply the sign; zero keeps its sign.
: cc-f64-pack ( exponent negative? -- bits )
  >r cc-f64-n @ if,
    cc-f64-normalize cc-f64-e +! cc-f64-round
  else, drop cc-f64-format @ [lit] 16 = if, [lit] 0 [lit] 0 cc-f80-allocate else, [lit] 0 then, then,
  r> if,
    cc-f64-format @ [lit] 16 = if,
      dup [lit] 8 + dup @ [lit] 32768 or swap !
    else, cc-f64-sign @ or then,
  then, ;
: cc-f64-one-denominator [lit] 1 cc-f64-d cc-f64-bi-set ;

```
Integer conversion uses an unsigned magnitude over a unit denominator, preserving the minimum signed input’s magnitude (`forth-bootstrap/cc/128-cc-float-literal.fth:427`):
```forth file=cc/128-cc-float-literal.fth
\ An integer is its own ratio; the minimum signed value negates to its
\ unsigned magnitude.
: cc-f64-integer ( value signed? format -- bits )
  cc-f64-use
  over 0< and dup >r if, [lit] 0 swap - then,
  cc-f64-n cc-f64-bi-set cc-f64-one-denominator
  [lit] 0 r> cc-f64-pack ;
: cc-f64-third ( a b c -- a b c a ) >r over r> swap ;
variable cc-f80-resize-sign
variable cc-f80-resize-nan
```

## Change a constant's format

| Case | Handling |
|---|---|
| Finite resize | Unpack in the source format; pack in the destination. |
| Extended infinity or NaN resize | `cc-f80-resize-sign` preserves sign; `cc-f80-resize-nan` distinguishes quiet NaN from infinity. |
| Exceptional construction | `cc-f80-nan-signed`, `cc-f80-nan`, `cc-f80-inf`, `cc-f80-zero` allocate results; `cc-f80-a-inf` and `cc-f80-b-inf` recognize special exponents. |
| Invalid arithmetic | Zero/zero, infinity/infinity, infinity times zero, and oppositely signed infinity sums produce NaNs. |
| Other exceptional division | Division by zero produces infinity; finite divided by infinity produces zero. |

These branches handle extended exceptions, not general scalar nonfinite arithmetic.

Two bounded observations limit the finite-example story at this source
pin. In this chapter's object profile, `static int x = 1 ? 7 : (int)2147483648.0;`
raises error 242 despite the unused arm; dead integer division and an
in-range floating-cast control both return 7. Numeric cast conversion
therefore still performs its range check in that arm.

Resizing an extended NaN to binary64 also exposes a comparison difference:
constant equality of two such NaNs returned 1, while runtime equality of
the same initialized NaN returned 0. Finite controls agreed. These are
profile-specific observations, not a claim of general scalar nonfinite
support; [Appendix F](60-c-subset.md#observed-profile-boundaries) records the
limits and outstanding source work.

Format changes share the finite packing path and separate extended exceptional cases (`forth-bootstrap/cc/128-cc-float-literal.fth:435`):
```forth file=cc/128-cc-float-literal.fth
: cc-f64-resize ( bits from to -- bits )
  dup [lit] 16 = cc-f64-third [lit] 16 <> and if,
    >r dup >r cc-f64-use
    dup cc-f64-negative? cc-f80-resize-sign !
    dup cc-f64-sign @ 1- and cc-f64-unit @ /
    cc-f64-emax @ [lit] 2 * 1+ = if,
      cc-f64-unit @ 1- and 0= if, 2^63 else, [lit] 13835058055282163712 then,
      cc-f80-resize-sign @ if, [lit] 65535 else, [lit] 32767 then,
      r> drop r> drop cc-f80-allocate exit,
    then, r> r>
  then,
  over [lit] 16 = over [lit] 16 <> and if,
    cc-f64-third [lit] 8 + @ [lit] 32767 and [lit] 32767 = if,
      >r drop dup [lit] 8 + @ [lit] 32768 and cc-f80-resize-sign !
      @ 2^63 <> cc-f80-resize-nan ! r> dup cc-f64-use
      [lit] 4 = if,
        cc-f80-resize-nan @ if, [lit] 2143289344 else, [lit] 2139095040 then,
      else,
        cc-f80-resize-nan @ if, [lit] 9221120237041090560 else, [lit] 9218868437227405312 then,
      then,
      cc-f80-resize-sign @ if, cc-f64-sign @ or then, exit,
    then,
  then,
  >r cc-f64-use
  dup cc-f64-negative? swap cc-f64-unpack
  swap cc-f64-n cc-f64-bi-set cc-f64-one-denominator
  swap r> cc-f64-use cc-f64-pack ;
```

## Operate on exact pairs

Saved sign, significand and exponent pairs give a negative product or quotient when signs differ (`forth-bootstrap/cc/128-cc-float-literal.fth:469`):
```forth file=cc/128-cc-float-literal.fth

variable cc-f64-a-negative
variable cc-f64-a-m
variable cc-f64-a-e
variable cc-f64-b-negative
variable cc-f64-b-m
variable cc-f64-b-e
: cc-f64-operands ( left right -- )
  dup cc-f64-negative? cc-f64-b-negative !
  cc-f64-unpack cc-f64-b-e ! cc-f64-b-m !
  dup cc-f64-negative? cc-f64-a-negative !
  cc-f64-unpack cc-f64-a-e ! cc-f64-a-m ! ;
: cc-f64-sign-of-product ( -- negative? )
  cc-f64-a-negative @ cc-f64-b-negative @ <> ;
```
`cc-f64-product` adds exponents and quotients subtract them, then pack once; `cc-f64-ratio` rejects a zero divisor (`forth-bootstrap/cc/128-cc-float-literal.fth:476`):
```forth file=cc/128-cc-float-literal.fth
: cc-f64-product ( -- bits )
  cc-f64-a-m @ cc-f64-n cc-f64-bi-set cc-f64-n cc-f64-b-m @ cc-f64-bi-times
  cc-f64-one-denominator
  cc-f64-a-e @ cc-f64-b-e @ + cc-f64-sign-of-product cc-f64-pack ;
: cc-f64-ratio ( -- bits )
  cc-f64-b-m @ 0= if, [lit] 124 cc-die then,
  cc-f64-a-m @ cc-f64-n cc-f64-bi-set cc-f64-b-m @ cc-f64-d cc-f64-bi-set
  cc-f64-a-e @ cc-f64-b-e @ - cc-f64-sign-of-product cc-f64-pack ;
```
Addition aligns to the smaller exponent, adds equal-sign magnitudes or subtracts opposite-sign magnitudes, and keeps the larger magnitude’s sign; cancellation gives positive zero, while negative zero plus negative zero stays negative (`forth-bootstrap/cc/128-cc-float-literal.fth:486`):
```forth file=cc/128-cc-float-literal.fth
\ Align both magnitudes to the smaller exponent; D holds the right one.
\ Exact cancellation is +0 under round to nearest; -0 + -0 stays -0.
: cc-f64-sum ( -- bits )
  cc-f64-a-e @ cc-f64-b-e @ 2dup > if, swap then, drop >r
  cc-f64-a-m @ cc-f64-n cc-f64-bi-set cc-f64-n cc-f64-a-e @ r@ - cc-f64-bi-shift
  cc-f64-b-m @ cc-f64-d cc-f64-bi-set cc-f64-d cc-f64-b-e @ r@ - cc-f64-bi-shift
  cc-f64-a-negative @ cc-f64-b-negative @ = if,
    cc-f64-n cc-f64-d cc-f64-bi-add cc-f64-a-negative @
  else,
    cc-f64-n cc-f64-d cc-f64-bi-compare dup 0= if,
      drop cc-f64-n cc-f64-bi-zero [lit] 0
    else, 0< if,
      cc-f64-d cc-f64-n cc-f64-bi-subtract cc-f64-d cc-f64-n cc-f64-bi-copy
      cc-f64-b-negative @
    else,
      cc-f64-n cc-f64-d cc-f64-bi-subtract cc-f64-a-negative @
    then, then,
  then,
  cc-f64-one-denominator r> swap cc-f64-pack ;
```

## Handle extended exceptional constants

Extended constructors supply the signed exceptional results used by the handlers (`forth-bootstrap/cc/128-cc-float-literal.fth:503`):
```forth file=cc/128-cc-float-literal.fth
\ Extended nonfinite constant results use canonical quiet NaNs, as GCC's
\ constant folder does; finite arithmetic still rounds one exact ratio.
: cc-f80-nan-signed ( negative? -- bits )
  if, [lit] 65535 else, [lit] 32767 then,
  [lit] 13835058055282163712 swap cc-f80-allocate ;
: cc-f80-nan [lit] 0 cc-f80-nan-signed ;
: cc-f80-inf ( negative? -- bits )
  if, [lit] 65535 else, [lit] 32767 then, 2^63 swap cc-f80-allocate ;
: cc-f80-zero ( negative? -- bits )
  if, [lit] 32768 else, [lit] 0 then, [lit] 0 swap cc-f80-allocate ;
: cc-f80-a-inf cc-f64-a-e @ [lit] 16321 = ;
: cc-f80-b-inf cc-f64-b-e @ [lit] 16321 = ;
```
Exceptional arithmetic selects a result before the finite ratio path (`forth-bootstrap/cc/128-cc-float-literal.fth:515`):
```forth file=cc/128-cc-float-literal.fth
: cc-f80-special-arith ( operator -- bits handled? )
  dup [char] / = if,
    drop cc-f80-a-inf cc-f80-b-inf and
    cc-f64-a-m @ cc-f64-b-m @ or 0= or if,
      cc-f64-sign-of-product cc-f80-nan-signed true exit, then,
    cc-f80-a-inf cc-f64-b-m @ 0= or if,
      cc-f64-sign-of-product cc-f80-inf true exit,
    then,
    cc-f80-b-inf if, cc-f64-sign-of-product cc-f80-zero true exit, then,
    [lit] 0 [lit] 0 exit,
  then,
  dup [char] * = if,
    drop cc-f80-a-inf cc-f64-b-m @ 0= and
    cc-f80-b-inf cc-f64-a-m @ 0= and or if,
      cc-f64-sign-of-product cc-f80-nan-signed true exit, then,
    cc-f80-a-inf cc-f80-b-inf or if,
      cc-f64-sign-of-product cc-f80-inf true exit,
    then, [lit] 0 [lit] 0 exit,
  then, drop
  cc-f80-a-inf cc-f80-b-inf and
  cc-f64-a-negative @ cc-f64-b-negative @ <> and if,
    cc-f80-nan true exit,
  then,
  cc-f80-a-inf if, cc-f64-a-negative @ cc-f80-inf true exit, then,
  cc-f80-b-inf if, cc-f64-b-negative @ cc-f80-inf true exit, then,
  [lit] 0 [lit] 0 ;
```
The dispatcher propagates extended NaNs first and reverses the right sign for subtraction (`forth-bootstrap/cc/128-cc-float-literal.fth:541`):
```forth file=cc/128-cc-float-literal.fth
: cc-f64-arith ( left right operator format -- bits )
  cc-f64-use >r cc-f64-operands r>
  cc-f64-format @ [lit] 16 = if,
    cc-f80-a-inf cc-f64-a-m @ 2^63 <> and if,
      drop cc-f64-a-negative @ cc-f80-nan-signed exit,
    then,
    cc-f80-b-inf cc-f64-b-m @ 2^63 <> and if,
      drop cc-f64-b-negative @ cc-f80-nan-signed exit,
    then,
  then,
  dup [char] - = if, cc-f64-b-negative @ 0= cc-f64-b-negative ! then,
  cc-f64-format @ [lit] 16 = if,
    dup cc-f80-special-arith if, nip exit, then, drop
  then,
  dup [char] * = if, drop cc-f64-product exit, then,
  dup [char] / = if, drop cc-f64-ratio exit, then,
  drop cc-f64-sum ;
```

## Truncate a constant without executing it

Truncation returns magnitude, sign and cell-fit status, leaving destination range checks to the caller; the bindings connect these operations to Chapter 45’s typed constant evaluator (`forth-bootstrap/cc/128-cc-float-literal.fth:560`):
```forth file=cc/128-cc-float-literal.fth
\ Truncate toward zero. fits? is false when the magnitude needs more
\ than 64 bits; the caller applies the destination type's range.
: cc-f64-truncate ( bits format -- magnitude negative? fits? )
  cc-f64-use dup cc-f64-negative? >r cc-f64-unpack
  dup 0< if,
    [lit] 0 swap - dup [lit] 64 < if,
      cc-f64-power /
    else, 2drop [lit] 0 then,
    r> true exit,
  then,
  dup [lit] 63 > if, 2drop [lit] 0 r> [lit] 0 exit, then,
  cc-f64-power 2dup * dup >r swap / = r> swap r> swap ;

' cc-f64-decimal is cc-fp-decimal-fwd
' cc-f64-integer is cc-fp-integer-fwd
' cc-f64-resize is cc-fp-resize-fwd
' cc-f64-arith is cc-fp-arith-fwd
' cc-f64-truncate is cc-fp-truncate-fwd
```

## Try it

Run from the `forth-bootstrap` checkout root with the seed already built. The block compiles layers through this chapter, emits a small `_start` object and links with the Forth linker. The shell prints and checks each executable's result from its process status.

The boundary literal lies just above the midpoint between unity and the next binary64 value. Its union view checks that exact decimal conversion chooses the upper encoding. The other probes exercise `sum`'s XMM0 return, runtime addition, comparison and truncating conversion.

<!-- tryit: expect "(int)((0.1 + 0.2) * 100) = 30\n0.1 + 0.2 > 0.3 = 1\nboundary bits == 0x3ff0000000000001 = 1" -->
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
for probe in 0 1 2; do
printf '#define PROBE %s\n' "$probe" > "$work/probe.c"
cat >> "$work/probe.c" <<'C' || exit "$?"
double sum(void) {
    double a = 0.1;
    double b = 0.2;
    return a + b;
}
int main(void) {
    double x = sum();
    union { double d; unsigned long bits; } boundary;
    boundary.d = 1.00000000000000011102230246251565404236316680908203126;
#if PROBE == 0
    return (int)(x * 100.0);
#elif PROBE == 1
    return x > 0.3;
#else
    return boundary.bits == 4607182418800017409UL;
#endif
}
C
{
  cat forth/010-lib.fth cc/0[2-9]*-cc-*.fth cc/1[01]*-cc-*.fth \
      cc/121-cc-sysv.fth cc/123-cc-object-program.fth \
      cc/124-cc-target.fth cc/125-cc-consteval.fth cc/126-cc-varargs.fth \
      cc/127-cc-binary64.fth cc/128-cc-float-literal.fth || exit "$?"
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
case "$probe" in
  0) printf '(int)((0.1 + 0.2) * 100) = %s\n' "$result"
     test "$result" -eq 30 || exit 1 ;;
  1) printf '0.1 + 0.2 > 0.3 = %s\n' "$result"
     test "$result" -eq 1 || exit 1 ;;
  2) printf 'boundary bits == 0x3ff0000000000001 = %s\n' "$result"
     test "$result" -eq 1 || exit 1 ;;
esac
done
)
# prints "(int)((0.1 + 0.2) * 100) = 30\n0.1 + 0.2 > 0.3 = 1\nboundary bits == 0x3ff0000000000001 = 1"
```

Observed output:

```text
(int)((0.1 + 0.2) * 100) = 30
0.1 + 0.2 > 0.3 = 1
boundary bits == 0x3ff0000000000001 = 1
```

## Exercise

Hints and feedback are in [Appendix H](66-exercise-feedback.md#chapter-47-exact-halfway-rounding).

**Trace — easy.** In `cc-f64-quotient`, follow an exact halfway remainder with an odd retained quotient, then with an even quotient. Explain why only the odd case increments.

**Verify — moderate.** Replace the checkpoint's boundary literal with `1.00000000000000011102230246251565404236316680908203125`, the exact midpoint. Change the C bit comparison to the encoding of unity (`4607182418800017408UL`). Also change the shell's printed bit-pattern label and expected-output comment to `0x3ff0000000000000`. Predict the Boolean result, then run it; the shell should still expect 1 for a true comparison.
