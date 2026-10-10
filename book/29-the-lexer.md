# Chapter 29 — The lexer

`int w[4];` becomes a keyword, an identifier, punctuation and a number when the lexer reads it. A parser needs these units before it can recognise C syntax. The lexer supplies them through `cc-next-token`, with token values and reversible lookahead for its callers.

## Token kinds and punctuation IDs

The code has this shape:

```text
cc-src-buf → skip whitespace/comments → classify leading byte
                                       ↓
                        number / name / string / char / punctuation
                                       ↓
                                   tok-* cells
                                       ↓
                          putback or save/restore for lookahead
```

The token kind tells the caller how to interpret the result; `tk-float` reserves a kind for the floating-literal work in Chapter 47 (`forth-bootstrap/cc/050-cc-lex.fth:1`):

```forth file=cc/050-cc-lex.fth
\ 050-cc-lex.fth — C tokenizer (one-token lookahead) for the C-subset compiler.
\ Reads bytes from cc-src-buf via cc-peek-char/cc-next-char/cc-eof? (030-cc-io.fth).
\ Stores the current token in 5 cells of the lexer's state block
\ (020-cc-arena.fth): tok-kind, tok-num, tok-str-addr, tok-str-len, tok-kw-id.
\ The parser drives the lexer through the interface at the end of this file:
\ cc-next-token-keep / cc-putback-token, and cc-lex-mark / cc-lex-reset.
\
\ Depends on 010-lib.fth (control-flow combinators, classifiers, bytes-eq, etc.),
\ 020-cc-arena.fth (cc-lex-state and its cells), 030-cc-io.fth (cc-src-buf,
\ cc-peek-char, cc-next-char, cc-eof?, ident-start?, ident-cont?).

\ ===========================================================================
\ Token kinds and punctuation IDs
\ ===========================================================================

[lit] 0 constant tk-eof
[lit] 1 constant tk-ident
[lit] 2 constant tk-num
[lit] 3 constant tk-str
[lit] 4 constant tk-chr
[lit] 5 constant tk-punct
[lit] 6 constant tk-kw
[lit] 7 constant tk-float

```

The `tok-*` cells belong to the lexer state block (Chapter 27). `tok-kind` selects the payload: `tok-num` holds an integer, character value or punctuation code; `tok-str-addr` and `tok-str-len` describe a source slice; `tok-kw-id` identifies a keyword. Only the fields belonging to the current kind are meaningful. Identifiers and string bodies remain in the source buffer instead of being copied.

Single-character punctuation uses its ASCII byte as `tok-num`. Multi-character punctuation needs distinct IDs outside the byte range; the comments pair each `pt-*` name with its spelling (`forth-bootstrap/cc/050-cc-lex.fth:25`):

```forth file=cc/050-cc-lex.fth
\ Multi-char punctuation codes start at 256 to avoid clash with single-byte
\ ASCII codes used directly for one-char punct (e.g. '(' = 40).
[lit] 256 constant pt-eq-eq         \ ==
[lit] 257 constant pt-bang-eq       \ !=
[lit] 258 constant pt-le            \ <=
[lit] 259 constant pt-ge            \ >=
[lit] 260 constant pt-and-and       \ &&
[lit] 261 constant pt-or-or         \ ||
[lit] 262 constant pt-arrow         \ ->
[lit] 263 constant pt-plus-plus     \ ++
[lit] 264 constant pt-minus-minus   \ --
[lit] 265 constant pt-shl           \ <<
[lit] 266 constant pt-shr           \ >>
[lit] 267 constant pt-plus-eq       \ +=
[lit] 268 constant pt-minus-eq      \ -=
[lit] 269 constant pt-star-eq       \ *=
[lit] 270 constant pt-slash-eq      \ /=
[lit] 271 constant pt-percent-eq    \ %=
[lit] 272 constant pt-amp-eq        \ &=
[lit] 273 constant pt-pipe-eq       \ |=
[lit] 274 constant pt-caret-eq      \ ^=
[lit] 275 constant pt-shl-eq        \ <<=
[lit] 276 constant pt-shr-eq        \ >>=
[lit] 277 constant pt-ellipsis      \ ...

```

## The keyword table

Keyword recognition needs spellings as well as IDs. Each `kw,` appends a length byte and the name bytes to `kw-table`, so the next entry can be found without a separate pointer table (`forth-bootstrap/cc/050-cc-lex.fth:50`):

```forth file=cc/050-cc-lex.fth
\ ===========================================================================
\ Keyword table + IDs
\ ===========================================================================
\ Flat byte array: each entry is [length-byte][name-bytes]; terminator is a
\ length-byte of 0.  Defined here (before cc-check-keyword) so the latter can
\ reference kw-table directly.

\ kw, ( "name" -- )  lay down one entry: the length byte, then the bytes.
: kw,  token dup c, bytes, ;

create kw-table
kw, int
kw, char
kw, void
kw, short
kw, long
kw, unsigned
kw, signed
kw, const
kw, volatile
kw, static
kw, extern
kw, auto
kw, register
kw, restrict
kw, struct
kw, enum
kw, typedef
kw, sizeof
```

The remaining entries use the same counted-name layout; a zero length ends the search (`forth-bootstrap/cc/050-cc-lex.fth:79`):

```forth file=cc/050-cc-lex.fth
kw, if
kw, else
kw, while
kw, for
kw, do
kw, return
kw, break
kw, continue
kw, goto
kw, switch
kw, case
kw, default
kw, union
kw, float
kw, double
kw, inline
kw, _Bool
[lit] 0 c,                                      \ terminator

```

The `kw-*` constants mirror declaration order, beginning with `kw-int`. Reordering table entries without changing these constants would give recognised words the wrong meaning (`forth-bootstrap/cc/050-cc-lex.fth:98`):

```forth file=cc/050-cc-lex.fth
\ Keyword IDs in declaration order.
[lit]  0 constant kw-int
[lit]  1 constant kw-char
[lit]  2 constant kw-void
[lit]  3 constant kw-short
[lit]  4 constant kw-long
[lit]  5 constant kw-unsigned
[lit]  6 constant kw-signed
[lit]  7 constant kw-const
[lit]  8 constant kw-volatile
[lit]  9 constant kw-static
[lit] 10 constant kw-extern
[lit] 11 constant kw-auto
[lit] 12 constant kw-register
[lit] 13 constant kw-restrict
[lit] 14 constant kw-struct
[lit] 15 constant kw-enum
[lit] 16 constant kw-typedef
```

Control-flow names and the remaining type names continue that ordering; `_Bool` is named `kw-bool` in Forth (`forth-bootstrap/cc/050-cc-lex.fth:116`):

```forth file=cc/050-cc-lex.fth
[lit] 17 constant kw-sizeof
[lit] 18 constant kw-if
[lit] 19 constant kw-else
[lit] 20 constant kw-while
[lit] 21 constant kw-for
[lit] 22 constant kw-do
[lit] 23 constant kw-return
[lit] 24 constant kw-break
[lit] 25 constant kw-continue
[lit] 26 constant kw-goto
[lit] 27 constant kw-switch
[lit] 28 constant kw-case
[lit] 29 constant kw-default
[lit] 30 constant kw-union
[lit] 31 constant kw-float
[lit] 32 constant kw-double
[lit] 33 constant kw-inline
[lit] 34 constant kw-bool

```

Recognising a prefix must not consume it prematurely. `cc-peek-char-2` returns the current and following bytes without advancing, supplying zero when the following byte is outside the source (`forth-bootstrap/cc/050-cc-lex.fth:141`):

```forth file=cc/050-cc-lex.fth
\ ===========================================================================
\ Helper: 2-byte peek
\ ===========================================================================

\ cc-peek-char-2 ( -- c1 c2 )  Returns the byte at pos and the byte at pos+1
\ without advancing.  Returns 0 for c2 at EOF.  c1 is also 0 at EOF.
: cc-peek-char-2
  cc-peek-char                                  ( c1 )
  cc-src-pos @ 1+                               ( c1 next-pos )
  dup cc-src-len @ < if,
    cc-src-buf swap + c@                        ( c1 c2 )
  else,
    drop [lit] 0                                ( c1 0 )
  then, ;

```

A name becomes a keyword only after both its length and bytes match an entry. `cc-check-keyword` carries `( ptr id )` through the table and otherwise leaves an ordinary identifier (`forth-bootstrap/cc/050-cc-lex.fth:158`):

```forth file=cc/050-cc-lex.fth
\ ===========================================================================
\ cc-check-keyword
\ ===========================================================================

\ cc-check-keyword ( -- )  After cc-lex-ident-or-kw has set tok-str-addr/len,
\ this walks kw-table; on a match it sets tok-kind=tk-kw + tok-kw-id and
\ returns at once, otherwise tok-kind=tk-ident.  Loop invariant on the data
\ stack: ( ptr id ).
: cc-check-keyword
  kw-table                                      \ ptr
  [lit] 0                                       \ id
  begin,
    over c@ [lit] 0 >                           \ entry length non-zero?
  while,
    over c@ tok-str-len @ = if,                 \ same length?
      \ Stack here: ( ptr id ).  bytes-eq wants ( a1 a2 u ) where
      \ a1 = tok-str-addr, a2 = ptr+1 (skipping length byte), u = tok-str-len.
      over 1+  tok-str-addr @  swap  tok-str-len @  bytes-eq if,
        tok-kw-id !  drop                       \ matched: record the id
        tk-kw tok-kind !  exit,
      then,
    then,
    \ Advance: ( ptr id ) -> ( ptr+len+1 id+1 )
    swap dup c@ 1+ + swap 1+
  repeat,
  2drop                                         \ discard ptr and id
  tk-ident tok-kind ! ;

```

The advance step changes `( ptr id )` to `( ptr+len+1 id+1 )`: the length byte locates the next entry while the counter tracks its ID. On a match, storing the ID and dropping the pointer leaves no search state behind. A name such as `integer` cannot match `int`, because their lengths differ.

## Whitespace and comments

A line comment ends before the newline. Leaving that byte for the outer whitespace loop keeps the comment reader concerned only with finding its boundary (`forth-bootstrap/cc/050-cc-lex.fth:178`):

```forth file=cc/050-cc-lex.fth
\ ===========================================================================
\ Whitespace and comment skipping
\ ===========================================================================

\ cc-skip-line-comment ( -- )  Caller has already consumed the //.  Skip
\ to (but do not consume) the next newline; the outer ws-skip will eat it.
: cc-skip-line-comment
  begin,
    cc-eof? 0=
    cc-peek-char nl <> and
  while,
    cc-next-char drop
  repeat, ;

```

A block comment must swallow its closing `*/`, since those bytes must not become punctuation tokens. At end-of-input this helper simply stops (`forth-bootstrap/cc/050-cc-lex.fth:192`):

```forth file=cc/050-cc-lex.fth
\ cc-skip-block-comment ( -- )  Caller has already consumed the /*.  Skip
\ to and including the closing */, or to EOF.
: cc-skip-block-comment
  begin,
    cc-eof? 0=
  while,
    cc-next-char [char] * = if,                 \ saw '*'
      cc-peek-char [char] / = if,               \ followed by '/'
        cc-next-char drop exit,                 \ consume '/': done
      then,
    then,
  repeat, ;

```

Whitespace and comments can alternate, so the outer loop keeps trying after either. `cc-cspace?` includes vertical tab and form feed; a slash that starts neither comment is left for punctuation (`forth-bootstrap/cc/050-cc-lex.fth:207`):

```forth file=cc/050-cc-lex.fth
\ cc-skip-ws-and-comments ( -- )  Skip whitespace, // line-comments, and
\ /* block comments.  Returns at the first non-whitespace, non-comment byte.
: cc-cspace? dup space? over [lit] 11 = or swap [lit] 12 = or ;

: cc-skip-ws-and-comments
  begin,
    cc-eof? 0=
  while,
    cc-peek-char dup cc-cspace? if,
      drop cc-next-char drop
    else,
      [char] / <> if, exit, then,               \ stop: not ws or comment
      cc-peek-char-2 nip [char] / = if,         \ // ?
        cc-next-char drop  cc-next-char drop
        cc-skip-line-comment
      else,
        cc-peek-char-2 nip [char] * = if,       \ /* ?
          cc-next-char drop  cc-next-char drop
          cc-skip-block-comment
        else,
          exit,                                 \ stop: bare '/'
        then,
      then,
    then,
  repeat, ;

```

`cc-skip-ws-and-comments` consumes comment openers before calling the helpers. A bare slash returns immediately without advancing, preserving division and compound assignment for the token reader. These routines do not report unterminated block comments.

## Number, identifier, string, char

### Digit recognition and accumulation

Numeric readers need predicates for their own digit sets. `cc-hex-digit?` accepts decimal digits and hex letters in either case; `cc-octal-digit?` accepts only octal digits (`forth-bootstrap/cc/050-cc-lex.fth:231`):

```forth file=cc/050-cc-lex.fth
\ ===========================================================================
\ Number / identifier / string / char lexers
\ ===========================================================================

\ Hex digit helpers (Task D: 0xFF hex literals).
\ cc-hex-digit? ( c -- f )  -1 if c is 0-9, a-f, A-F.
: cc-hex-digit?
  dup digit? if,
    drop true
  else,
    dup alpha-lower? if,
      [char] a - [lit] 6 / 0=                     \ 'a'..'f' -> 0..5 -> /6=0
    else,
      dup alpha-upper? if,
        [char] A - [lit] 6 / 0=                   \ 'A'..'F'
      else,
        drop [lit] 0
      then,
    then,
  then, ;

\ cc-octal-digit? ( c -- f )  True for '0'..'7'.
: cc-octal-digit?  [char] 0 - [lit] 8 / 0= ;

```

After a hexadecimal byte has passed that predicate, `cc-hex-digit-val` converts it to the value used by the accumulator (`forth-bootstrap/cc/050-cc-lex.fth:256`):

```forth file=cc/050-cc-lex.fth
\ cc-hex-digit-val ( c -- v )  Convert hex digit char to 0..15.
: cc-hex-digit-val
  dup digit? if,
    [char] 0 -
  else,
    dup alpha-lower? if,
      [char] a - [lit] 10 +                       \ 'a' -> 10
    else,
      [char] A - [lit] 10 +                       \ 'A' -> 10
    then,
  then, ;

```

The decimal reader establishes the recurring *multiply–add* pattern: multiply the accumulated value by the base, add the next digit, and consume that byte (`forth-bootstrap/cc/050-cc-lex.fth:267`):

```forth file=cc/050-cc-lex.fth
\ cc-lex-number-dec ( -- )  Read decimal digits into tok-num.
: cc-lex-number-dec
  [lit] 0
  begin,
    cc-eof? 0=
    cc-peek-char digit? and
  while,
    [lit] 10 *
    cc-peek-char [char] 0 - +
    cc-next-char drop
  repeat,
  tok-num !
  tk-num tok-kind ! ;

```

Hexadecimal input uses the same multiply–add loop after its prefix has been consumed, with the hexadecimal predicate and conversion (`forth-bootstrap/cc/050-cc-lex.fth:281`):

```forth file=cc/050-cc-lex.fth
\ cc-lex-number-hex ( -- )  '0x' already consumed; read hex digits into tok-num.
: cc-lex-number-hex
  [lit] 0
  begin,
    cc-eof? 0=
    cc-peek-char cc-hex-digit? and
  while,
    [lit] 16 *
    cc-peek-char cc-hex-digit-val +
    cc-next-char drop
  repeat,
  tok-num !
  tk-num tok-kind ! ;

```

Octal input also uses multiply–add, with the leading zero already consumed; the first byte outside its digit set remains unread (`forth-bootstrap/cc/050-cc-lex.fth:295`):

```forth file=cc/050-cc-lex.fth
\ cc-lex-number-oct ( -- )  A leading '0' already consumed; read octal
\ digits into tok-num (C's 010 is eight).
: cc-lex-number-oct
  [lit] 0
  begin,
    cc-eof? 0=
    cc-peek-char cc-octal-digit? and
  while,
    [lit] 8 *
    cc-peek-char [char] 0 - +
    cc-next-char drop
  repeat,
  tok-num !
  tk-num tok-kind ! ;

```

### Choosing the base and retaining the spelling

The prefix decides which numeric reader runs. `cc-lex-number` saves the start address, chooses hex for `0x` or `0X`, octal for a leading zero followed by a digit, and decimal otherwise (`forth-bootstrap/cc/050-cc-lex.fth:314`):

```forth file=cc/050-cc-lex.fth
\ cc-lex-number ( -- )  Hex if it starts 0x or 0X, octal if it starts with
\ 0 and another digit, else decimal.  The full spelling, including a
\ u/U/l/L suffix, is retained in tok-str-addr/len for type classification.
\ tok-num still contains the unsigned 64-bit bit pattern, in both targets.
: cc-lex-number
  cc-src-buf cc-src-pos @ + >r                    \ numeric token start
  cc-peek-char-2                                  ( c1 c2 )
  over [char] 0 = if,                             \ c1 == '0' ?
    dup [char] x = over [char] X = or if,         \ c2 == 'x' or 'X' ?
      2drop
      cc-next-char drop                           \ consume '0'
      cc-next-char drop                           \ consume 'x'/'X'
      cc-lex-number-hex
    else,
      digit? if,                                  \ c2 a digit: octal
        drop
        cc-next-char drop                         \ consume '0'
        cc-lex-number-oct
      else,
        drop cc-lex-number-dec
      then,
    then,
  else,
    2drop
    cc-lex-number-dec
  then,
```

Suffix letters belong to the numeric token even though they do not change its accumulated value. This tail consumes them and retains the complete source spelling for type classification in Chapter 30 (`forth-bootstrap/cc/050-cc-lex.fth:336`):

```forth file=cc/050-cc-lex.fth
  begin,
    cc-peek-char dup [char] u = over [char] U = or
    over [char] l = or  swap [char] L = or
  while,
    cc-next-char drop
  repeat,
  cc-src-buf cc-src-pos @ + r@ - tok-str-len !
  r> tok-str-addr ! ;

```

The accumulator wraps with cell arithmetic. The spelling preserves information the value alone loses, including the base and suffix. This scanner accepts repeated suffix letters and does not diagnose missing hexadecimal digits or invalid octal digits; it is not a complete validator of C integer literals.

### Names and quoted bodies

An identifier is a source slice followed by a keyword lookup. The leading-byte dispatcher has already checked `ident-start?`, so `cc-lex-ident-or-kw` only needs `ident-cont?` while extending the name (`forth-bootstrap/cc/050-cc-lex.fth:348`):

```forth file=cc/050-cc-lex.fth
\ cc-lex-ident-or-kw ( -- )  Read [a-zA-Z_][a-zA-Z0-9_]* and check the
\ keyword table.  Sets tok-str-addr/len, then dispatches kind.  Macros are
\ already expanded (040-cc-prep.fth), so an identifier is just a name.
: cc-lex-ident-or-kw
  cc-src-buf cc-src-pos @ +                     \ start address
  [lit] 0                                       ( start len )
  begin,
    cc-eof? 0=
    cc-peek-char ident-cont? and
  while,
    cc-next-char drop
    1+
  repeat,
  tok-str-len !  tok-str-addr !
  cc-check-keyword ;

```

Names arrive after preprocessing (Chapter 28); this word does not expand macros. An unmatched name remains `tk-ident`. Resolving what it denotes belongs to the symbol work in Chapter 30.

A backslash protects the following byte from ending the string body, even when that byte is a quote. `cc-lex-string` keeps the backslash and following byte together, recording the body without its surrounding quotes (`forth-bootstrap/cc/050-cc-lex.fth:365`):

```forth file=cc/050-cc-lex.fth
\ cc-lex-string ( -- )  Read "..." preserving escape sequences as literal
\ bytes (a \" inside the body is two bytes long; the closing quote is the
\ unescaped ").  Stores the slice as offset+len into cc-src-buf for later
\ string-pool insertion or escape decoding.
: cc-lex-string
  cc-next-char drop                             \ consume opening "
  cc-src-buf cc-src-pos @ +                     \ start address
  [lit] 0                                       ( start len )
  begin,
    cc-eof? 0=
    cc-peek-char [char] " <> and
  while,
    cc-peek-char backslash = if,                \ backslash: keep both bytes
      cc-next-char drop
      1+
      cc-eof? 0= if,
        cc-next-char drop
        1+
      then,
    else,
      cc-next-char drop
      1+
    then,
  repeat,
  cc-eof? 0= if, cc-next-char drop then,        \ consume closing "
  tok-str-len !  tok-str-addr !
  tk-str tok-kind ! ;

```

The slice holds an address and length, despite the header comment saying “offset+len”. Escapes remain spelled as source bytes. Chapter 32 handles their decoding during string emission. Reaching EOF also ends this reader; it does not reject a missing closing quote.

### Escape values and character tokens

Character literals need a value immediately. `cc-decode-escape` returns that byte and the source length after the backslash; `cc-esc-a` holds the starting address, `cc-esc-v` the accumulator, and `cc-esc-n` the consumed length. Its hex branch counts the `x` before scanning digits (`forth-bootstrap/cc/050-cc-lex.fth:399`):

```forth file=cc/050-cc-lex.fth
\ cc-decode-escape ( a -- byte n )  a is the address of what follows a
\ backslash; answer the byte the escape stands for and how many bytes the
\ escape takes after the backslash.  \n \t \r \a \b \f \v are the usual
\ control characters; \ooo (one to three octal digits, so \0 too) and
\ \xhh... (hex digits) give a byte by value; any other \c (including \\
\ \' \") stands for c itself.  The one table for both character literals
\ (cc-lex-char) and string literals (cc-emit-string-bytes, 090).
variable cc-esc-a
variable cc-esc-v
variable cc-esc-n
: cc-decode-escape
  dup cc-esc-a !  c@
  dup [char] x = if,
    drop  [lit] 0 cc-esc-v !  [lit] 1 cc-esc-n !
    begin,
      cc-esc-a @ cc-esc-n @ + c@  dup cc-hex-digit?
    while,
      cc-hex-digit-val  cc-esc-v @ [lit] 16 * +  cc-esc-v !
      [lit] 1 cc-esc-n +!
    repeat,
    drop  cc-esc-v @ [lit] 255 and  cc-esc-n @ exit,
  then,
```

The octal branch limits the digit count and masks the result to a byte, as the hex branch does. Named control escapes return their control byte; any unrecognised escape returns the escaped character itself (`forth-bootstrap/cc/050-cc-lex.fth:411`):

```forth file=cc/050-cc-lex.fth
  dup cc-octal-digit? if,
    drop  [lit] 0 cc-esc-v !  [lit] 0 cc-esc-n !
    begin,
      cc-esc-a @ cc-esc-n @ + c@
      dup cc-octal-digit?  cc-esc-n @ [lit] 3 < and
    while,
      [char] 0 -  cc-esc-v @ [lit] 8 * +  cc-esc-v !
      [lit] 1 cc-esc-n +!
    repeat,
    drop  cc-esc-v @ [lit] 255 and  cc-esc-n @ exit,
  then,
  dup [char] n = if, drop nl       [lit] 1 exit, then,
  dup [char] t = if, drop tab      [lit] 1 exit, then,
  dup [char] r = if, drop [lit] 13 [lit] 1 exit, then,
  dup [char] a = if, drop [lit]  7 [lit] 1 exit, then,
  dup [char] b = if, drop [lit]  8 [lit] 1 exit, then,
  dup [char] f = if, drop [lit] 12 [lit] 1 exit, then,
  dup [char] v = if, drop [lit] 11 [lit] 1 exit, then,
  [lit] 1 ;

```

The character reader advances by the decoder's returned length, then stores the byte in `tok-num` with kind `tk-chr`. Without a backslash it takes the literal byte directly (`forth-bootstrap/cc/050-cc-lex.fth:431`):

```forth file=cc/050-cc-lex.fth
\ cc-lex-char ( -- )  Read 'c' or '\c'.  Stores the byte value in tok-num.
: cc-lex-char
  cc-next-char drop                             \ consume opening '
  cc-peek-char backslash = if,                  \ escape
    cc-next-char drop                           \ consume backslash
    cc-src-buf cc-src-pos @ + cc-decode-escape  ( byte n )
    begin, dup while, cc-next-char drop 1- repeat,
    drop
  else,
    cc-next-char                                \ literal char
  then,
  tok-num !
  cc-eof? 0= if, cc-next-char drop then,        \ consume closing '
  tk-chr tok-kind ! ;

```

The final advance assumes the following byte is the closing quote; it does not test that assumption. Unlike a string token, a character token carries a decoded value rather than a body slice.

## Punctuation: a fan-out

### Longest matches

An ambiguous punctuation prefix follows a *consume–peek–commit* pattern: the dispatcher consumes the first byte, the handler peeks at the remainder, and only a matching continuation is consumed. Equality establishes the pattern (`forth-bootstrap/cc/050-cc-lex.fth:446`):

```forth file=cc/050-cc-lex.fth
\ ===========================================================================
\ Punctuation: per-first-char handlers + dispatch
\ ===========================================================================
\ Each handler is entered after the first char has already been read.  It
\ checks for any multi-char follow-on, then stores the punct code in tok-num
\ and sets tok-kind to tk-punct.

: cc-punct-eq                                   \ '='  '=='
  cc-peek-char [char] = = if,
    cc-next-char drop  pt-eq-eq tok-num !
  else,
    [char] = tok-num !
  then,
  tk-punct tok-kind ! ;

```

The bang handler uses consume–peek–commit for `!` and `!=`, storing either the original byte or the named compound ID (`forth-bootstrap/cc/050-cc-lex.fth:461`):

```forth file=cc/050-cc-lex.fth
: cc-punct-bang                                 \ '!'  '!='
  cc-peek-char [char] = = if,
    cc-next-char drop  pt-bang-eq tok-num !
  else,
    [char] ! tok-num !
  then,
  tk-punct tok-kind ! ;

```

A less-than prefix has a deeper choice: `<=`, a shift, or a bare `<`. After consuming the second `<`, the handler must still check for the assignment suffix (`forth-bootstrap/cc/050-cc-lex.fth:469`):

```forth file=cc/050-cc-lex.fth
: cc-punct-lt                                   \ '<' '<=' '<<' '<<='
  cc-peek-char [char] = = if,
    cc-next-char drop  pt-le tok-num !
  else,
    cc-peek-char [char] < = if,
      cc-next-char drop
      cc-peek-char [char] = = if,
        cc-next-char drop  pt-shl-eq tok-num !
      else,
        pt-shl tok-num !
      then,
    else,
      [char] < tok-num !
    then,
  then,
  tk-punct tok-kind ! ;

```

The greater-than handler mirrors those choices for comparisons and right shifts (`forth-bootstrap/cc/050-cc-lex.fth:486`):

```forth file=cc/050-cc-lex.fth
: cc-punct-gt                                   \ '>' '>=' '>>' '>>='
  cc-peek-char [char] = = if,
    cc-next-char drop  pt-ge tok-num !
  else,
    cc-peek-char [char] > = if,
      cc-next-char drop
      cc-peek-char [char] = = if,
        cc-next-char drop  pt-shr-eq tok-num !
      else,
        pt-shr tok-num !
      then,
    else,
      [char] > tok-num !
    then,
  then,
  tk-punct tok-kind ! ;

```

### Repeated prefixes and assignment

Four handlers can see their first byte doubled or followed by `=`; minus also has the arrow. Each checks the doubled form before the assignment form:

| First byte | Bare | Doubled | With `=` | Other |
|---|---|---|---|---|
| `&` | `&` | `pt-and-and` | `pt-amp-eq` | |
| `\|` | `\|` | `pt-or-or` | `pt-pipe-eq` | |
| `+` | `+` | `pt-plus-plus` | `pt-plus-eq` | |
| `-` | `-` | `pt-minus-minus` | `pt-minus-eq` | `pt-arrow` for `->` |

The handlers follow in that order (`forth-bootstrap/cc/050-cc-lex.fth:503`):

```forth file=cc/050-cc-lex.fth
: cc-punct-amp                                  \ '&' '&&' '&='
  cc-peek-char [char] & = if,
    cc-next-char drop  pt-and-and tok-num !
  else,
    cc-peek-char [char] = = if,
      cc-next-char drop  pt-amp-eq tok-num !
    else,
      [char] & tok-num !
    then,
  then,
  tk-punct tok-kind ! ;

```

```forth file=cc/050-cc-lex.fth
: cc-punct-pipe                                 \ '|' '||' '|='
  cc-peek-char [char] | = if,
    cc-next-char drop  pt-or-or tok-num !
  else,
    cc-peek-char [char] = = if,
      cc-next-char drop  pt-pipe-eq tok-num !
    else,
      [char] | tok-num !
    then,
  then,
  tk-punct tok-kind ! ;

```

```forth file=cc/050-cc-lex.fth
: cc-punct-plus                                 \ '+' '++' '+='
  cc-peek-char [char] + = if,
    cc-next-char drop  pt-plus-plus tok-num !
  else,
    cc-peek-char [char] = = if,
      cc-next-char drop  pt-plus-eq tok-num !
    else,
      [char] + tok-num !
    then,
  then,
  tk-punct tok-kind ! ;

```

```forth file=cc/050-cc-lex.fth
: cc-punct-minus                                \ '-' '--' '-=' '->'
  cc-peek-char [char] - = if,
    cc-next-char drop  pt-minus-minus tok-num !
  else,
    cc-peek-char [char] = = if,
      cc-next-char drop  pt-minus-eq tok-num !
    else,
      cc-peek-char [char] > = if,
        cc-next-char drop  pt-arrow tok-num !
      else,
        [char] - tok-num !
      then,
    then,
  then,
  tk-punct tok-kind ! ;

```

### Assignment-only continuations

Four more handlers only distinguish the bare byte from its `=` form. Slash arrives here after comment skipping, so `/=` is its only compound:

| First byte | Bare | With `=` |
|---|---|---|
| `*` | `*` | `pt-star-eq` |
| `/` | `/` | `pt-slash-eq` |
| `%` | `%` | `pt-percent-eq` |
| `^` | `^` | `pt-caret-eq` |

They follow in that order (`forth-bootstrap/cc/050-cc-lex.fth:555`):

```forth file=cc/050-cc-lex.fth
: cc-punct-star                                 \ '*' '*='
  cc-peek-char [char] = = if,
    cc-next-char drop  pt-star-eq tok-num !
  else,
    [char] * tok-num !
  then,
  tk-punct tok-kind ! ;

```

```forth file=cc/050-cc-lex.fth
: cc-punct-slash                                \ '/' '/=' (// and /* handled earlier)
  cc-peek-char [char] = = if,
    cc-next-char drop  pt-slash-eq tok-num !
  else,
    [char] / tok-num !
  then,
  tk-punct tok-kind ! ;

```

```forth file=cc/050-cc-lex.fth
: cc-punct-percent                              \ '%' '%='
  cc-peek-char [char] = = if,
    cc-next-char drop  pt-percent-eq tok-num !
  else,
    [char] % tok-num !
  then,
  tk-punct tok-kind ! ;

```

```forth file=cc/050-cc-lex.fth
: cc-punct-caret                                \ '^' '^='
  cc-peek-char [char] = = if,
    cc-next-char drop  pt-caret-eq tok-num !
  else,
    [char] ^ tok-num !
  then,
  tk-punct tok-kind ! ;

```

### Dots and dispatch

An ellipsis requires all its dots. `cc-punct-dot` peeks far enough to commit only to `...`; for `..` it returns a bare dot and leaves the next dot unread (`forth-bootstrap/cc/050-cc-lex.fth:587`):

```forth file=cc/050-cc-lex.fth
: cc-punct-dot                                  \ '.' '...'
  cc-peek-char [char] . = if,
    cc-peek-char-2 nip [char] . = if,
      cc-next-char drop  cc-next-char drop
      pt-ellipsis tok-num !
    else,
      [char] . tok-num !
    then,
  else,
    [char] . tok-num !
  then,
  tk-punct tok-kind ! ;

```

The dispatch chain consumes the first byte and selects its handler. Anything without a handler falls through to a punctuation token whose code is that byte (`forth-bootstrap/cc/050-cc-lex.fth:600`):

```forth file=cc/050-cc-lex.fth
\ cc-lex-punct ( -- )  Consume the next char and dispatch to a per-char
\ handler.  Single-char punctuation (; { } ( ) [ ] , ? : ~) falls through
\ to the default arm, which stores the byte itself as the punct code.
: cc-lex-punct
  cc-next-char                                  ( first-char )
  dup [char] = = if, drop cc-punct-eq      else,
  dup [char] ! = if, drop cc-punct-bang    else,
  dup [char] < = if, drop cc-punct-lt      else,
  dup [char] > = if, drop cc-punct-gt      else,
  dup [char] & = if, drop cc-punct-amp     else,
  dup [char] | = if, drop cc-punct-pipe    else,
  dup [char] + = if, drop cc-punct-plus    else,
  dup [char] - = if, drop cc-punct-minus   else,
  dup [char] * = if, drop cc-punct-star    else,
  dup [char] / = if, drop cc-punct-slash   else,
  dup [char] % = if, drop cc-punct-percent else,
  dup [char] ^ = if, drop cc-punct-caret   else,
  dup [char] . = if, drop cc-punct-dot     else,
    \ Default: single-char punct.
    tok-num ! tk-punct tok-kind !
  then, then, then, then, then, then, then,
  then, then, then, then, then, then, ;

```

That fallback covers delimiters such as parentheses and semicolons, but it is not a validity check. An otherwise unrecognised source byte also takes the fallback.

## The top-level driver

An extension gets first refusal before ordinary token classification. `cc-lex-extra-fwd` initially calls `cc-lex-extra-default`, whose false result declines the token (`forth-bootstrap/cc/050-cc-lex.fth:628`):

```forth file=cc/050-cc-lex.fth
\ ===========================================================================
\ Top-level: cc-next-token
\ ===========================================================================

\ cc-next-token ( -- )  Skip ws/comments, dispatch on the first byte.
: cc-lex-extra-default [lit] 0 ;
defer cc-lex-extra-fwd
' cc-lex-extra-default is cc-lex-extra-fwd

```

After skipping whitespace and comments, `cc-next-token` returns immediately if the extension claims a token. Otherwise it reports EOF or dispatches by the leading byte (`forth-bootstrap/cc/050-cc-lex.fth:632`):

```forth file=cc/050-cc-lex.fth
: cc-next-token
  cc-skip-ws-and-comments
  cc-lex-extra-fwd if, exit, then,
  cc-eof? if,
    tk-eof tok-kind !
  else,
    cc-peek-char
    dup digit?       if, drop cc-lex-number          else,
    dup [char] " =   if, drop cc-lex-string          else,
    dup [char] ' =   if, drop cc-lex-char            else,
    dup ident-start? if, drop cc-lex-ident-or-kw     else,
      drop cc-lex-punct
    then, then, then, then,
  then, ;

```

An extension that returns true must have supplied the token state. With the default installed, digits select numbers, quotes select strings or characters, identifier starts select names, and the remaining bytes select punctuation. The extension mechanism leaves room for Chapter 47; this layer does not produce floating tokens itself.

## The parser's interface: putback, mark and reset

A caller that has read too far can offer the current token again. `cc-putback-token` sets a pending flag; `cc-next-token-keep` clears it and returns the unchanged token instead of reading (`forth-bootstrap/cc/050-cc-lex.fth:647`):

```forth file=cc/050-cc-lex.fth
\ ===========================================================================
\ The parser's interface: putback, mark and reset
\ ===========================================================================
\ The lexer reads one token at a time with no built-in peek.  A parser that
\ has read one token too many puts it back: cc-putback-token sets
\ cc-tok-pending, and the next cc-next-token-keep returns the same tok-*
\ state without advancing.

\ cc-next-token-keep ( -- )  Advance to the next token unless one is pending.
: cc-next-token-keep
  cc-tok-pending @ if,
    [lit] 0 cc-tok-pending !
  else,
    cc-next-token
  then, ;

\ cc-putback-token ( -- )  Mark the current tok-* as still-pending so the
\ next cc-next-token-keep returns it without advancing.
: cc-putback-token
  true cc-tok-pending ! ;

```

Putback does not rewind the source cursor or keep a token history. Calling it repeatedly still marks only the current token. Mixing direct calls to `cc-next-token` with a pending token bypasses that promise; callers using putback must advance through `cc-next-token-keep`.

Longer lookahead needs to save the entire lexer state. `cc-lex-copy` copies cells from the end of the block toward its beginning, including the cursor, line, token payload and pending flag (`forth-bootstrap/cc/050-cc-lex.fth:674`):

```forth file=cc/050-cc-lex.fth
\ To look further ahead, a parser marks the whole lexer state (reader
\ cursor, line, current token, putback flag: the cc-lex-state block),
\ reads as many tokens as it likes, and resets to the mark.  A mark is any
\ cc-lex-state-size bytes of storage.

\ cc-lex-copy ( src dst -- )  Copy one lexer-state block, last cell first.
: cc-lex-copy
  cc-lex-state-size
  begin, dup while,
    [lit] 8 -                                   ( src dst off )
    >r  over r@ + @  over r@ + !  r>
  repeat,
  drop 2drop ;

```

Mark copies state into a buffer; reset copies it back. `cc-peek-mark` provides shared storage for lookahead that only reads tokens and cannot nest another use of the same buffer (`forth-bootstrap/cc/050-cc-lex.fth:682`):

```forth file=cc/050-cc-lex.fth
\ cc-lex-mark ( buf -- )  Save the lexer state into buf.
: cc-lex-mark   cc-lex-state swap cc-lex-copy ;

\ cc-lex-reset ( buf -- )  Restore the lexer state saved by cc-lex-mark.
: cc-lex-reset  cc-lex-state cc-lex-copy ;

\ cc-peek-mark is the one mark every lookahead in the parser uses.  Between
\ marking and resetting, each of them only reads tokens, so no lookahead
\ can start while another is in progress and one buffer serves them all.
create cc-peek-mark  cc-lex-state-size allot
```

For example, save a mark while an identifier is current, read the following punctuation, then reset: the identifier payload and the cursor after it both return. The next advance reads the same punctuation again. A nested lookahead would need a separate mark buffer. Copying lexer state does not copy the source bytes, so the source must remain unchanged during the lookahead.

## Try it

Run these from the `forth-bootstrap` checkout root. First, watch the opening example become tokens. The driver loads the library and the layers through the lexer, reads `int w[4];` from stdin through the preprocessor (Chapter 28), and prints one line per token: its kind, then the keyword ID, identifier length, punctuation byte or number value.

```sh
{ cat forth/010-lib.fth cc/020-cc-arena.fth cc/030-cc-io.fth cc/040-cc-prep.fth cc/050-cc-lex.fth
  cat <<'FORTH'
: digit.  [lit] 48 + emit ;
: lex-dump
  cc-load-stdin cc-preprocess  [lit] 0 cc-src-pos !  [lit] 1 cc-src-line !
  begin, cc-next-token tok-kind @ dup while,
    dup digit. bl emit
    dup tk-kw    = if, tok-kw-id @ digit. then,
    dup tk-ident = if, tok-str-len @ digit. then,
    dup tk-punct = if, tok-num @ emit then,
        tk-num   = if, tok-num @ digit. then,
    nl emit
  repeat, drop bye ;
lex-dump
FORTH
  printf 'int w[4];\n'
} | ./seed-forth
```

Observed output:

```text
6 0
1 1
5 [
2 4
5 ]
5 ;
```

Kind 6 is `tk-kw` with `kw-int` (0); kind 1 is an identifier of length 1; kind 5 is punctuation carrying its byte; kind 2 is a number with value 4. `tk-eof` (0) ends the loop.

Then run the lexer layer test selected by `forth-bootstrap/test.sh:124`, the coverage check for this layer:

```sh
cat forth/010-lib.fth cc/020-cc-arena.fth cc/030-cc-io.fth \
    cc/040-cc-prep.fth cc/050-cc-lex.fth cc/test-050-cc-lex.fth | ./seed-forth
printf 'exit status: %s\n' "$?"
```

Observed output:

```text
exit status: 0
```

The test itself is silent. In `forth-bootstrap/cc/test-050-cc-lex.fth:1`, each assertion contributes to a Boolean accumulator, and the final `0= die` turns success into a successful process exit. It writes source bytes directly into `cc-src-buf`, so loading the preprocessor here does not test macro expansion.

The assertions check keyword IDs for `int` and `return`; identifier kinds, lengths and selected bytes; ordinary delimiters and `<=`, `&&`, `>>=`; decimal, octal and hexadecimal values; suffix consumption; a string slice; character values and newline, hex and octal escapes; comment skipping; and EOF. They do not cover every keyword or punctuation handler, numeric spelling metadata, malformed literals, overflow, the extension hook, or putback and mark/reset. A passing smoke test establishes those selected cases, not full C lexical conformance.

## Exercise

**Trace — easy.** Follow `cc-punct-dot` on `..` and on `...`, beginning just after the dispatcher consumes the first dot. For each input, identify the branch taken, the punctuation code stored, and the unread suffix. Explain why consuming the next dot before checking the following byte would break the shorter case.

**Verify — medium.** Add a local lexer probe that marks an identifier, reads the following punctuation, resets, and reads again. Check the token payload, source cursor and pending flag as well as the kind. Repeat with a token pending at the moment of the mark.

