# Chapter 49 — Aggregates and extended floating values

A function that accepts `struct Pair` by value must receive the pair's bytes, and its caller must recover the bytes of the returned pair. The compiler represents a record expression by an address, so a call needs a classification and a transport plan between that address and the System V boundary. The completed layer passes records and scalar floating arguments, returns records, and computes with extended floating values.

## Classify the object before moving it

The path is expression address → classification → private argument copy → registers or outgoing stack → callee local object. Return transport follows the same classification in reverse. This extends the scalar boundary of Chapter 41 and closes Chapter 47's floating-argument deferral, where this transport was rejected with error 232. Bitfield members contribute their containing integer types without changing their layout (Chapter 48).

The implementation is a bounded classifier, not the full mixed-class System V algorithm. Nested records, unions, fixed arrays, pointers and supported integer members are admitted. Records containing `float` or `double` members, vector classes, empty records and over-aligned records are rejected. A pointer is classified without inspecting its pointee. Packed attributes are outside the parser's dialect.

The target gate keeps this value contract in explicit System V mode, so the private all-stack target is unaffected; every refused shape exits with error 232 (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:1`):
```forth file=cc/131-cc-aggregate-abi.fth
\ 131-cc-aggregate-abi.fth -- shared INTEGER/binary32/binary64/X87/MEMORY SysV ABI.
\ Record expressions carry addresses. The ABI transports object bytes, never
\ that address: up to two INTEGER eightbytes, otherwise a private stack copy.
\ Long double (121) is X87: a sixteen-aligned stack copy, returned in st(0).
\ Records cross prototyped, unprototyped and variadic calls alike, and
\ va_arg retrieves them. Floating members and vector classes are not implemented.
create cc-ag-error-prefix s, aggregate-abi: bl c,
: cc-ag-die cc-ag-error-prefix [lit] 15 cc-err-write [lit] 232 cc-die ;
: cc-ag-type? ( type -- flag )
  dup ty-ptr 0= swap ty-base ty-struct = and cc-target-sysv @ and ;

```
`cc-ag-walk` visits every leaf, noting long-double and other leaves separately, because an X87 object may contain nothing else. Ranked arrays recurse on their real element, and scalar floating leaves inside records fail instead of silently becoming INTEGER (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:19`):
```forth file=cc/131-cc-aggregate-abi.fth
\ Validate each nested member, including members of unions and arrays.
\ A descriptor with an unaligned member is MEMORY; the current parser emits
\ natural layouts, but the classifier does not rely on this coincidence.
\ The walk notes whether it met a long double leaf and any other leaf.
variable cc-ag-x87
variable cc-ag-other
defer cc-ag-walk-fwd
: cc-ag-walk ( type descriptor offset -- unaligned? )
  >r
  \ A ranked field must validate its real element, including floating leaves.
  over ty-base ty-array = [lit] 2 cc-npick ty-ptr 0= and if,
    nip dup cc-ad-type swap cc-ad-desc r> cc-ag-walk-fwd exit,
  then,
  2dup cc-ld? if,
    2drop true cc-ag-x87 ! r> [lit] 16 cc-mod 0= 0= exit,
  then,
  over cc-ag-type? 0= if,
    true cc-ag-other !
    drop dup ty-ptr 0= if,
      dup ty-base dup ty-float = over ty-double = or
      swap ty-ldouble = or if, cc-ag-die then,
    then,
    dup cc-sysv-check-scalar-default ty-align r> swap cc-mod 0= 0= exit,
  then,
```
Every field of a record or union must validate, even when the final object will travel in memory. The walk combines member alignment failures and rejects missing descriptors, empty objects, excessive alignment and negative array bounds (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:36`):
```forth file=cc/131-cc-aggregate-abi.fth
  nip dup 0= if, cc-ag-die then,
  dup cc-sd-total-size 0= if, cc-ag-die then,
  dup cc-sd-align dup [lit] 16 > if, cc-ag-die then,
  r@ swap cc-mod 0= 0= swap
  [lit] 0 begin, over cc-sd-field-count over > while,
    2dup cc-sd-field-rec
    dup cc-sf-array-len [lit] 0 < if, cc-ag-die then,
    dup cc-sf-type over cc-sf-desc
    [lit] 2 cc-npick cc-sf-offset r@ + cc-ag-walk-fwd
    >r drop rot r> or rot rot 1+
  repeat, 2drop r> drop ;
' cc-ag-walk is cc-ag-walk-fwd
```
`cc-ag-class` returns zero for MEMORY, one or two for INTEGER eightbytes, three for scalar SSE, and four for X87. A non-X87 record larger than sixteen bytes or with an unaligned member is MEMORY; otherwise its size rounds up to eightbytes. An X87 object must be exactly sixteen bytes, aligned, and contain no other leaf anywhere in the object. `cc-ag-abi-type` and `cc-ag-return-check` validate without retaining the class (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:48`):
```forth file=cc/131-cc-aggregate-abi.fth
\ Class is zero for MEMORY, one/two INTEGER eightbytes, three for scalar SSE
\ and four for X87: sixteen bytes holding only long double leaves, which an
\ argument passes like MEMORY and a result returns in st(0). Any other leaf
\ sharing an eightbyte with X87 makes the whole object MEMORY.
: cc-ag-class ( type descriptor -- class )
  over cc-fp-type? if, 2drop [lit] 3 exit, then,
  over cc-ag-type? 0= if, cc-sysv-abi-type-default [lit] 1 exit, then,
  [lit] 0 cc-ag-x87 ! [lit] 0 cc-ag-other !
  2dup [lit] 0 cc-ag-walk >r nip cc-sd-total-size
  dup cc-sysv-object-size-limit > if, cc-ag-die then,
  cc-ag-x87 @ if,
    [lit] 16 = cc-ag-other @ 0= and r> 0= and if, [lit] 4 else, [lit] 0 then,
    exit,
  then,
  dup [lit] 16 > r> or if, drop [lit] 0 else, [lit] 7 + [lit] 8 / then, ;
: cc-ag-abi-type ( type descriptor -- ) cc-ag-class drop ;
' cc-ag-abi-type is cc-sysv-abi-type-fwd
: cc-ag-return-check ( type descriptor -- )
  over cc-ag-type? if, cc-ag-abi-type else, cc-sysv-return-check-default then, ;
' cc-ag-return-check is cc-sysv-return-check-fwd

```
Member access must preserve a record address, while assignment must preserve descriptor identity; `cc-ag-field-load` and `cc-ag-assignment` enforce those separate obligations (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:69`):
```forth file=cc/131-cc-aggregate-abi.fth
\ Materializing a record does not fetch its first word. Assignment and
\ initialization consume the address and perform the existing byte copy.
: cc-ag-field-load ( type field -- )
  over cc-ag-type? if, 2drop else, cc-bf-load then, ;
' cc-ag-field-load is cc-field-load-fwd
: cc-ag-assignment
  cc-target-sysv @ if,
    cc-last-expr-type @ cc-assign-type @ <>
    cc-last-struct-desc @ cc-assign-desc @ <> or if, cc-ag-die then,
  then, ;
' cc-ag-assignment is cc-aggregate-assignment-fwd

```
## Give arguments explicit locations

A **call transport plan** separates source argument order from register order. The caller and callee use the same plan, including a hidden result pointer before visible arguments for MEMORY returns.

A plan holds the signature, a separate count for each register class (GP and SSE), the outgoing stack size and the result slot; it also remembers an indirect target and the live state that must survive the call. Each argument records its type, its class and its location: a first register, or a stack offset and frame slot.

`cc-ag-plan` selects the current call transport plan; `cc-ag-frame` reserves rounded storage without growing an unevaluated expression frame (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:104`):
```forth file=cc/131-cc-aggregate-abi.fth
\ A plan owns explicit argument locations. Nothing relies on the argument
\ index also being a register index. Each record is type, descriptor, byte
\ size, class, first GP register (-1 for stack), stack offset and frame slot.
variable cc-ag-plan
: ag-signature cc-ag-plan @ ;
: ag-count cc-ag-plan @ [lit] 8 + ;
: ag-gp cc-ag-plan @ [lit] 16 + ;
: ag-stack cc-ag-plan @ [lit] 24 + ;
: ag-result cc-ag-plan @ [lit] 32 + ;
: ag-return-class cc-ag-plan @ [lit] 40 + ;
: ag-return-size cc-ag-plan @ [lit] 48 + ;
: ag-indirect cc-ag-plan @ [lit] 56 + ;
: ag-live cc-ag-plan @ [lit] 64 + ;
: ag-target cc-ag-plan @ [lit] 72 + ;
: ag-fp cc-ag-plan @ [lit] 80 + ;
: ag-arg ( index -- record ) [lit] 64 * [lit] 96 + cc-ag-plan @ + ;
: ag-type @ ;
: ag-desc [lit] 8 + @ ;
: ag-size [lit] 16 + @ ;
: ag-class [lit] 24 + @ ;
: ag-register [lit] 32 + @ ;
: ag-offset [lit] 40 + @ ;
: ag-slot [lit] 48 + @ ;
: cc-ag-frame ( bytes -- slot )
  [lit] 7 + [lit] 8 / dup cc-fn-local-count @ + 1-
  swap cc-expr-unevaluated @ if, drop else, cc-fn-add-slots then, ;
```
A fixed prototype reserves only its declared argument capacity; unspecified and variadic signatures reserve the bounded capacity. `cc-ag-new-plan` starts GP allocation after the hidden MEMORY result pointer. `cc-ag-check-entry` rejects K&R float parameters because their promoted entry type needs a conversion this path does not implement (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:107`):
```forth file=cc/131-cc-aggregate-abi.fth
: cc-ag-new-plan ( signature -- )
  dup cc-sysv-sig-varargs [lit] 3 and if,
    cc-sysv-arg-cap
  else, dup cc-sysv-sig-count then,
  [lit] 64 * [lit] 96 + dup cc-alloc dup cc-ag-plan ! swap cc-nzero
  ag-signature ! true ag-result ! true ag-return-class !
  ag-signature @ cc-sysv-sig-return cc-ag-type? if,
    ag-signature @ cc-sysv-signature-result cc-ag-class ag-return-class !
    ag-signature @ cc-sysv-sig-desc cc-sd-total-size ag-return-size !
    ag-return-class @ 0= if, [lit] 1 ag-gp ! then,
  then, ;
\ Records and long double have one ABI in every prototype form: default
\ promotions leave them unchanged, so prototyped, variadic and unprototyped
\ calls, and every definition form, classify them alike.
: cc-ag-check-entry ( signature -- )
  \ K&R float parameters arrive as promoted doubles, but the local declared
  \ type is float. Reject until entry conversion has its own transport type.
  dup cc-sysv-sig-varargs [lit] 4 and if,
    [lit] 0 begin, over cc-sysv-sig-count over > while,
      2dup cc-sysv-sig-param @ cc-f32-type? if, cc-ag-die then, 1+
    repeat, drop
  then,
  drop ;
```
`cc-ag-locate` allocates a whole INTEGER record only if all of its registers fit. Otherwise it leaves the GP count untouched, so a later scalar may use the remaining register. SSE exhaustion is independent; MEMORY and X87 always use stack storage aligned to the object alignment or eight bytes, whichever is greater. INTEGER uses at most six GP registers; SSE uses at most eight XMM registers. Stack sizes round up to eight bytes (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:130`):
```forth file=cc/131-cc-aggregate-abi.fth
: cc-ag-locate ( type descriptor index -- )
  ag-arg >r
  2dup cc-ag-class r@ [lit] 24 + !
  2dup cc-nsize dup [lit] 0 <= if, cc-ag-die then, r@ [lit] 16 + !
  r@ [lit] 8 + ! r@ !
  r@ ag-class [lit] 3 = if,
    ag-fp @ [lit] 8 < if,
      ag-fp @ r@ [lit] 32 + ! [lit] 1 ag-fp +!
    else, true r@ [lit] 32 + ! then,
  else,
    r@ ag-class dup 0= over [lit] 4 = or over ag-gp @ + [lit] 6 > or if,
      drop true r@ [lit] 32 + !
    else, ag-gp @ r@ [lit] 32 + ! ag-gp +! then,
  then,
  \ Stack copies keep their own alignment, at least eight: X87 takes sixteen.
  r@ ag-register [lit] 0 < if,
    ag-stack @ r@ ag-type r@ ag-desc cc-nalignment [lit] 8 cc-nmax cc-nalign
    dup ag-stack ! r@ [lit] 40 + !
    r@ ag-size [lit] 8 cc-nalign ag-stack +!
  then,
  r@ ag-size cc-ag-frame r> [lit] 48 + ! ;

```
## Freeze each argument before the next expression

A **fixed-frame snapshot** owns the bytes of a completed argument. Later argument expressions, nested calls and changes to the original object cannot change those bytes. A result object receives its own storage too.

| Input | Result or destination |
|---|---|
| Slot, GP register → `cc-ag-store-gp` | Spill the incoming register. |
| Slot, GP register → `cc-ag-load-gp` | Load the outgoing register. |
| Slot, XMM register, opcode → `cc-ag-xmm-local` | Shared memory operand encoder. |
| Slot, XMM register → `cc-ag-store-xmm`, `cc-ag-load-xmm` | Spill or reload the scalar floating payload. |
| Size, slot → `cc-ag-copy-to-slot` | Copy the addressed object's exact byte size. |

GP moves follow the System V register sequence, with distinct encodings for the extended registers (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:152`):
```forth file=cc/131-cc-aggregate-abi.fth
\ Register numbers are the psABI sequence RDI, RSI, RDX, RCX, R8, R9.
: cc-ag-store-gp ( slot register -- )
  dup [lit] 0 = if, drop cc-emit-store-local exit, then,
  dup [lit] 1 = if, drop cc-emit-store-local-from-rsi exit, then,
  dup [lit] 2 = if, drop cc-emit-store-local-from-rdx exit, then,
  dup [lit] 3 = if, drop cc-emit-store-local-from-rcx exit, then,
  dup [lit] 4 = if, drop cc-emit-store-local-from-r8 exit, then,
  drop cc-emit-store-local-from-r9 ;
: cc-ag-load-gp ( slot register -- )
  dup [lit] 4 < if, [lit] 72 else, [lit] 76 then, cc-emit-byte
  [lit] 139 cc-emit-byte
  dup [lit] 0 = if, drop [lit] 125 else,
  dup [lit] 1 = if, drop [lit] 117 else,
  dup [lit] 2 = if, drop [lit] 85 else,
  dup [lit] 3 = if, drop [lit] 77 else,
  [lit] 4 = if, [lit] 69 else, [lit] 77
  then, then, then, then, then, cc-emit-local-ea ;
```
SSE payloads and object copies use private frame storage, so scalar C object widths need not match the register move width (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:169`):
```forth file=cc/131-cc-aggregate-abi.fth
\ Scalar SSE arguments use only the low eight bytes of XMM0..XMM7.
: cc-ag-xmm-local ( slot register opcode -- )
  [lit] 242 cc-emit-byte [lit] 15 cc-emit-byte cc-emit-byte
  [lit] 8 * [lit] 69 + cc-emit-local-ea ;
: cc-ag-store-xmm [lit] 17 cc-ag-xmm-local ;
: cc-ag-load-xmm [lit] 16 cc-ag-xmm-local ;
: cc-ag-copy-to-slot ( size slot -- )
  cc-ni-mov-rsi-rdi cc-emit-lea-rdi-local cc-ni-copy-bytes ;

```
`cc-ag-parse-arguments` chooses a declared parameter type when a prototype supplies one. Otherwise default promotions preserve records and long double, promote scalar float, and normalize narrow integers before location planning (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:180`):
```forth file=cc/131-cc-aggregate-abi.fth
\ Each argument is frozen in the fixed frame when its expression finishes.
\ Nested calls and alloca may move RSP without moving these object copies.
: cc-ag-parse-arguments
  cc-next-token-keep [char] ) cc-tok-punct? if,
    ag-signature @ cc-sysv-sig-count if, [lit] 235 cc-die then, exit,
  then, cc-putback-token
  begin,
    ag-count @ cc-sysv-arg-cap >= if, [lit] 234 cc-die then,
    cc-parse-assign-fwd cc-emit-materialize
    ag-count @ ag-signature @ cc-sysv-sig-count <
    ag-signature @ cc-sysv-prototype? and if,
      ag-signature @ ag-count @ cc-sysv-parameter-type
    else,
      ag-signature @ cc-sysv-sig-varargs [lit] 3 and 0= if, [lit] 235 cc-die then,
      \ Default promotions leave records and long double unchanged.
      cc-last-expr-type @ cc-last-struct-desc @
      2dup cc-ld? [lit] 2 cc-npick cc-ag-type? or 0= if,
        drop dup cc-sysv-check-scalar cc-sysv-default-type cc-last-struct-desc @
      then,
    then,
    2dup >r >r cc-last-expr-type @ cc-last-struct-desc @ r> r> cc-value-shape-fwd
    ag-count @ cc-ag-locate
```
A record is descriptor-checked and copied into its fixed-frame snapshot; a scalar is converted and saved. The parser then checks separators and the prototype argument count (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:200`):
```forth file=cc/131-cc-aggregate-abi.fth
    ag-count @ ag-arg >r
    r@ ag-type cc-ag-type? if,
      cc-last-expr-type @ r@ ag-type cc-emit-convert-value
      r@ ag-type r@ ag-desc cc-ld? if,
        r@ ag-type cc-last-expr-type ! r@ ag-desc cc-last-struct-desc !
      then,
      cc-last-expr-type @ r@ ag-type <>
      cc-last-struct-desc @ r@ ag-desc <> or if, cc-ag-die then,
      r@ ag-size r@ ag-slot cc-ag-copy-to-slot
    else,
      cc-last-expr-type @ cc-sysv-check-scalar
      cc-last-expr-type @ r@ ag-type cc-emit-convert-value
      r@ ag-slot cc-emit-store-local
    then, r> drop
    [lit] 1 ag-count +!
    cc-next-token-keep [char] , cc-tok-punct? 0=
  until,
  [char] ) cc-tok-punct? 0= if, [lit] 121 cc-die then,
  ag-signature @ cc-sysv-prototype? if,
    ag-count @ ag-signature @ cc-sysv-sig-count < if, [lit] 235 cc-die then,
  then, ;
```
## Prepare the boundary in a safe order

`cc-ag-prepare-call` saves live state and aligns the outgoing area to sixteen bytes. Stack copies precede register loads because the copy instruction uses GP argument registers (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:221`):
```forth file=cc/131-cc-aggregate-abi.fth
: cc-ag-prepare-call
  [lit] 24 cc-alloc dup ag-live ! [lit] 24 cc-nzero
  cc-sysv-stack-depth @ cc-switch-depth @ + dup ag-live @ [lit] 8 + !
  cc-expr-unevaluated @ if,
    drop [lit] 0 ag-live @ [lit] 8 + !
  else,
    cc-fn-local-count @ ag-live @ ! 1+ cc-fn-add-slots
  then,
  ag-live @ cc-sysv-save-live
  [lit] 72 cc-emit-byte [lit] 129 cc-emit-byte [lit] 236 cc-emit-byte
  ag-stack @ [lit] 15 + cc-emit-4le
  [lit] 72 cc-emit-byte [lit] 131 cc-emit-byte
  [lit] 228 cc-emit-byte [lit] 240 cc-emit-byte
  \ Stack copies precede register loads because REP MOVSB uses GP arguments.
  [lit] 0 begin, dup ag-count @ < while,
    dup ag-arg dup ag-register [lit] 0 < if,
      dup ag-slot cc-emit-lea-rdi-local cc-ni-mov-rsi-rdi
      [lit] 72 cc-emit-byte [lit] 141 cc-emit-byte
      [lit] 188 cc-emit-byte [lit] 36 cc-emit-byte dup ag-offset cc-emit-4le
      dup ag-size cc-ni-copy-bytes
```
The hidden result address is installed before visible GP arguments, while scalar SSE loads use their independent bank (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:241`):
```forth file=cc/131-cc-aggregate-abi.fth
    then, drop 1+
  repeat, drop
  ag-return-class @ 0= if, ag-result @ cc-emit-lea-rdi-local then,
  [lit] 0 begin, dup ag-count @ < while,
    dup ag-arg dup ag-register [lit] 0 >= if,
      dup ag-class [lit] 3 = if,
        dup ag-slot over ag-register cc-ag-load-xmm
      else,
        [lit] 0 begin, over ag-class over > while,
          over ag-slot over - [lit] 2 cc-npick ag-register [lit] 2 cc-npick + cc-ag-load-gp
          1+
        repeat, drop
      then,
    then, drop 1+
  repeat, drop ;
```
`cc-ag-result` captures INTEGER return registers or pops an X87 result into the caller's private object before restoring live state. MEMORY already occupies the caller buffer; scalar results follow their existing value hook (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:256`):
```forth file=cc/131-cc-aggregate-abi.fth
: cc-ag-result
  ag-return-class @ [lit] 4 = if,
    [lit] 219 cc-emit-byte ag-result @ [lit] 125 cc-emit-local-ea \ fstp tbyte
    ag-live @ cc-sysv-restore-live ag-result @ cc-emit-lea-rdi-local exit,
  then,
  ag-return-class @ [lit] 0 >= if,
    ag-return-class @ if,
      [lit] 72 cc-emit-byte [lit] 137 cc-emit-byte
      ag-result @ [lit] 69 cc-emit-local-ea
      ag-return-class @ [lit] 2 = if,
        ag-result @ 1- cc-emit-store-local-from-rdx
      then,
    then,
    ag-live @ cc-sysv-restore-live
    ag-result @ cc-emit-lea-rdi-local
  else,
    ag-live @ cc-sysv-restore-live cc-emit-mov-rdi-rax
    ag-signature @ cc-sysv-sig-return cc-sysv-result-value-fwd
  then, ;
```
`cc-ag-emit-call` writes the actual used SSE-register count into EAX for the unnamed-argument contract, then chooses a saved indirect target or a direct symbol fixup (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:275`):
```forth file=cc/131-cc-aggregate-abi.fth
: cc-ag-emit-call
  cc-ag-parse-arguments cc-ag-prepare-call
  [lit] 184 cc-emit-byte ag-fp @ cc-emit-4le
  ag-indirect @ if,
    [lit] 76 cc-emit-byte [lit] 139 cc-emit-byte
    ag-target @ [lit] 85 cc-emit-local-ea \ mov r10,[rbp+slot]
    [lit] 65 cc-emit-byte [lit] 255 cc-emit-byte [lit] 210 cc-emit-byte
  else,
    ag-target @ dup cc-sym-val-of 0= if,
      cc-emit-call-rel32-placeholder
      cc-expr-unevaluated @ if, 2drop
      else, swap cc-sym-call-fixups cc-add-fixup-to-list then,
    else, cc-sym-val-of cc-emit-call-vaddr then,
  then, cc-ag-result ;
```
`cc-ag-call-begin` allocates the result storage, and `cc-ag-call` saves the enclosing call transport plan, because an argument expression may itself contain a call that would otherwise overwrite it (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:289`):
```forth file=cc/131-cc-aggregate-abi.fth
: cc-ag-call-begin ( signature -- )
  dup cc-ag-check-entry cc-ag-new-plan
  ag-return-class @ [lit] 0 >= if,
    ag-return-size @ cc-ag-frame ag-result !
  then, ;
: cc-ag-save-target
  true ag-indirect ! [lit] 8 cc-ag-frame dup ag-target ! cc-emit-store-local ;
: cc-ag-call ( id -- )
  cc-target-sysv @ 0= cc-expr-unevaluated @ or if, cc-sysv-call exit, then,
  dup cc-sysv-symbol-signature
  cc-check-static-init cc-ag-plan @ >r cc-ag-call-begin
  dup cc-sym-kind-of sk-func = if, ag-target ! else,
    dup cc-sym-kind-of sk-local = if, cc-sym-val-of cc-emit-load-local
    else, cc-sym-val-of cc-emit-global-ref cc-emit-load-via-rdi then,
    cc-ag-save-target
  then,
  cc-ag-emit-call r> cc-ag-plan ! ;
' cc-ag-call is cc-native-call-fwd
```
An expression-valued function pointer needs callable and signature checks before materialization; `cc-ag-indirect-call` restores result metadata and the enclosing plan after the call (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:307`):
```forth file=cc/131-cc-aggregate-abi.fth
: cc-ag-indirect-call
  cc-target-sysv @ 0= cc-expr-unevaluated @ or if, cc-sysv-indirect-call exit, then,
  cc-last-expr-type @ cc-sysv-check-callable
  cc-last-struct-desc @ cc-sysv-check-signature
  cc-check-static-init cc-ag-plan @ >r cc-ag-call-begin
  cc-emit-materialize cc-ag-save-target cc-ag-emit-call
  ag-signature @ cc-sysv-signature-result cc-mark-typed-value
  ag-signature @ cc-field-qualified cc-last-expr-qualified !
  r> cc-ag-plan ! ;
' cc-ag-indirect-call is cc-native-indirect-fwd

```
## Reconstruct callee objects and return bytes

`cc-ag-parameters` installs each named parameter as an independent local object, so the callee can modify its copy without touching the caller's (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:320`):
```forth file=cc/131-cc-aggregate-abi.fth
variable cc-ag-function-plan
variable cc-ag-sret-slot
: cc-ag-parameters ( signature -- )
  [lit] 0 cc-ag-function-plan !
  dup cc-ag-check-entry cc-ag-plan @ >r cc-ag-new-plan
  cc-ag-plan @ cc-ag-function-plan !
  ag-return-class @ 0= if, [lit] 8 cc-ag-frame cc-ag-sret-slot ! then,
  ag-signature @ cc-sysv-sig-count cc-native-param-count !
  [lit] 0 begin, dup cc-native-param-count @ < while,
    ag-signature @ over cc-sysv-sig-param cc-field-qualified nc-qualified !
    ag-signature @ over cc-sysv-parameter-type [lit] 2 cc-npick cc-ag-locate
    ag-signature @ over cc-sysv-sig-name
    dup @ nc-name ! [lit] 8 + @ nc-nlen !
    nc-nlen @ 0= if, [lit] 233 cc-die then,
    dup ag-arg dup ag-type nc-ty ! dup ag-desc nc-desc !
    [lit] 0 nc-array ! [lit] 0 nc-inner !
    ag-slot sk-local swap cc-ninstall-symbol drop 1+
  repeat, drop r> cc-ag-plan ! ;
' cc-ag-parameters is cc-sysv-params-fwd
```
`cc-ag-store-parameters` spills every register parameter before copying any incoming stack object, because a copy could destroy a register that has not yet been saved (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:337`):
```forth file=cc/131-cc-aggregate-abi.fth
: cc-ag-store-parameters
  cc-ag-function-plan @ 0= if, cc-sysv-store-params-default exit, then,
  cc-ag-plan @ >r cc-ag-function-plan @ cc-ag-plan !
  ag-return-class @ 0= if, cc-ag-sret-slot @ cc-emit-store-local then,
  \ Spill all register parameters before a stack copy clobbers any register.
  [lit] 0 begin, dup cc-native-param-count @ < while,
    dup ag-arg dup ag-register [lit] 0 >= if,
      dup ag-class [lit] 3 = if,
        dup ag-slot over ag-register cc-ag-store-xmm
      else,
        [lit] 0 begin, over ag-class over > while,
          over ag-slot over - [lit] 2 cc-npick ag-register [lit] 2 cc-npick + cc-ag-store-gp
          1+
        repeat, drop
      then,
    then, drop 1+
  repeat, drop
  [lit] 0 begin, dup cc-native-param-count @ < while,
    dup ag-arg dup ag-register [lit] 0 < if,
      [lit] 72 cc-emit-byte [lit] 141 cc-emit-byte
      [lit] 181 cc-emit-byte dup ag-offset [lit] 16 + cc-emit-4le
      dup ag-slot cc-emit-lea-rdi-local dup ag-size cc-ni-copy-bytes
    then, drop 1+
  repeat, drop r> cc-ag-plan ! ;
' cc-ag-store-parameters is cc-sysv-store-params-fwd

```
`cc-ag-convert` permits a record discard to void but does not reinterpret record addresses as scalars. Scalar initializer paths use `cc-ag-initialize` to reject that mistake before storing (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:363`):
```forth file=cc/131-cc-aggregate-abi.fth
\ Return expressions keep their descriptor until the full object is copied.
\ MEMORY returns use the caller's separate result object and return its
\ address in RAX. Small returns are staged to avoid reading beyond the source.
: cc-ag-convert ( source destination -- )
  over cc-ag-type? over ty-void [lit] 0 ty-make = and if, 2drop exit, then,
  2dup cc-ag-type? swap cc-ag-type? or if,
    2dup <> if, cc-ag-die then, 2drop
  else, cc-fp-convert then, ;
' cc-ag-convert is cc-emit-convert-value
\ Scalar initializer paths retain their source type before storing bytes.
: cc-ag-initialize ( source destination -- )
  over cc-ag-type? over cc-ag-type? or if, cc-ag-die then,
  cc-fp-initialize ;
' cc-ag-initialize is cc-value-init-fwd
```
`cc-ag-return` checks value shape and descriptor identity. MEMORY copies into the saved caller buffer and returns its address in RAX; INTEGER returns stage the exact source bytes before wider register loads, avoiding a read beyond a short source object. X87 returns load the significant bytes into `st(0)` (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:377`):
```forth file=cc/131-cc-aggregate-abi.fth
: cc-ag-return
  cc-last-expr-type @ cc-last-struct-desc @
  cc-native-return-type @ cc-native-return-desc @ cc-value-shape-fwd
  cc-last-expr-type @ cc-ag-type?
  cc-native-return-type @ ty-void [lit] 0 ty-make = and if, cc-ag-die then,
  cc-native-return-type @ cc-ag-type? 0= if, cc-fp-return exit, then,
  cc-native-return-type @ cc-native-return-desc @ cc-ld? if,
    [lit] 219 cc-emit-byte [lit] 47 cc-emit-byte exit, then,
  cc-last-expr-type @ cc-native-return-type @ <>
  cc-last-struct-desc @ cc-native-return-desc @ <> or if, cc-ag-die then,
  cc-native-return-type @ cc-native-return-desc @ cc-ag-class
  dup [lit] 4 = if, drop [lit] 219 cc-emit-byte [lit] 47 cc-emit-byte exit, then, \ fld tbyte [rdi]
  dup 0= if,
    drop cc-ni-mov-rsi-rdi cc-ag-sret-slot @ cc-emit-load-local
    cc-emit-mov-rax-rdi
    cc-native-return-desc @ cc-sd-total-size cc-ni-copy-bytes
  else,
    >r cc-native-return-desc @ cc-sd-total-size dup cc-ag-frame >r
    r@ cc-ag-copy-to-slot
    [lit] 72 cc-emit-byte [lit] 139 cc-emit-byte r@ [lit] 69 cc-emit-local-ea
    r> r> [lit] 2 = if,
      1- [lit] 72 cc-emit-byte [lit] 139 cc-emit-byte [lit] 85 cc-emit-local-ea
    else, drop then,
  then, ;
' cc-ag-return is cc-value-return-fwd

```
## Keep record addresses out of scalar operations

These handlers protect the address representation. They are transport defaults; the extended arithmetic layer replaces the long-double cases while ordinary records keep their constraints.

| Input | Result or destination |
|---|---|
| Type → `cc-ag-scalar-use` | Reject an actual record in a scalar operation. |
| Type, descriptor → `cc-ld-scalar-use` | Also reject transport-only long double. |
| Current expression → `cc-ag-last-use`, `cc-ag-plus` | Apply those operand checks. |
| Operand types → `cc-ag-common-type` | Check both descriptors before scalar common-type selection. |
| Current expression → `cc-ag-test`, `cc-ag-not`, `cc-ag-negate`, `cc-ag-complement` | Check before the corresponding scalar operation. |
| Type → `cc-ag-integer-use` | Check before an integer-only use. |

The scalar guards run even when expression evaluation is suppressed, so an address cannot acquire arithmetic meaning through `sizeof` (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:403`):
```forth file=cc/131-cc-aggregate-abi.fth
\ An address representation is not permission to use a record as a scalar.
\ Explicit record casts remain outside this value contract. Long double
\ shares the representation; 132 replaces the scalar computation hooks.
: cc-ag-scalar-use ( type -- ) dup cc-ag-type? if, cc-ag-die then, drop ;
: cc-ld-scalar-use ( type descriptor -- )
  over swap cc-ld? if, cc-ld-die then, cc-ag-scalar-use ;
: cc-ag-last-use cc-last-expr-type @ cc-last-struct-desc @ cc-ld-scalar-use ;
: cc-ag-plus cc-ag-last-use ;
' cc-ag-plus is cc-value-plus-fwd
: cc-ag-common-type ( left right -- type )
  over cc-expr-left-desc @ cc-ld-scalar-use
  dup cc-expr-right-desc @ cc-ld-scalar-use cc-fp-common-type ;
' cc-ag-common-type is cc-expr-common-type
: cc-ag-test cc-ag-last-use cc-fp-test ;
: cc-ag-not cc-ag-last-use cc-fp-not ;
: cc-ag-negate cc-ag-last-use cc-fp-negate ;
: cc-ag-complement cc-ag-last-use cc-fp-complement ;
: cc-ag-integer-use
  dup cc-last-struct-desc @ cc-ld-scalar-use cc-fp-integer-use ;
' cc-ag-test is cc-value-test-fwd
' cc-ag-not is cc-value-not-fwd
' cc-ag-negate is cc-value-negate-fwd
' cc-ag-complement is cc-value-complement-fwd
' cc-ag-integer-use is cc-value-integer-use-fwd

```
`cc-ag-ternary` descriptor-checks the selected record and takes a fixed-frame snapshot at the branch join. Its temporary status prevents assignment or address-taking; unevaluated selection checks identity without copying (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:432`):
```forth file=cc/131-cc-aggregate-abi.fth
\ The join sees the selected arm's address. Freeze its complete object into
\ a fresh fixed-frame slot before any later expression can change an arm.
\ Every syntactic conditional owns storage, including nested conditionals;
\ sizeof checks identity but allocates no frame and emits no copy.
: cc-ag-ternary ( left-type left-desc inner null qualified true-fixup -- handled? )
  [lit] 5 cc-npick cc-ag-type? cc-last-expr-type @ cc-ag-type? or 0= if,
    [lit] 0 exit,
  then,
  cc-patch-rel32-to-here
  drop 2drop
  2dup cc-last-expr-type @ cc-last-struct-desc @ cc-ld-mismatch
  over cc-last-expr-type @ <> over cc-last-struct-desc @ <> or if, cc-ag-die then,
  dup 0= if, cc-ag-die then,
  cc-expr-unevaluated @ 0= if,
    cc-check-static-init
    dup cc-sd-total-size dup [lit] 0 <= over cc-sysv-object-size-limit > or if, cc-ag-die then,
    dup cc-ag-frame dup >r cc-ag-copy-to-slot r> cc-emit-lea-rdi-local
  then,
  cc-mark-typed-value lv-temporary cc-last-lvalue-kind ! true ;
' cc-ag-ternary is cc-aggregate-ternary-fwd


```
`cc-ag-argument-check` enforces prototype record identity independently of emitted call code, preserving type constraints in unevaluated calls (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:453`):
```forth file=cc/131-cc-aggregate-abi.fth
\ C type constraints apply inside sizeof even when no ABI code is emitted.
\ Leave the old scalar grammar and the metadata-only fallback intact; check
\ only the aggregate identities introduced by this layer's value contract.
: cc-ag-argument-check ( signature index -- )
  over cc-sysv-sig-count over > [lit] 2 cc-npick cc-sysv-prototype? and if,
    cc-sysv-parameter-type
    2dup >r >r cc-last-expr-type @ cc-last-struct-desc @ r> r> cc-value-shape-fwd
    over cc-ag-type? cc-last-expr-type @ cc-ag-type? or
    [lit] 2 cc-npick [lit] 2 cc-npick cc-ld?
    cc-last-expr-type @ cc-last-struct-desc @ cc-ld? or 0= and if,
      cc-last-expr-type @ cc-last-struct-desc @
      cc-sysv-compatible-types 0= if, cc-ag-die then,
    else, 2drop then,
  else, 2drop then, ;
' cc-ag-argument-check is cc-sysv-argument-check-fwd

```
`cc-ag-cast-types` shares the runtime and constant cast policy so a cast cannot relabel a small object address as a larger record. A void discard remains valid (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:469`):
```forth file=cc/131-cc-aggregate-abi.fth
\ A cast must never relabel a smaller object's address as a larger record.
\ Runtime and constant cast parsers share this pure policy hook. Valid
\ descriptor-checked assignments and returns bypass explicit cast parsing.
: cc-ag-cast-types ( source destination -- )
  dup ty-void [lit] 0 ty-make = if, cc-sysv-cast-types exit, then,
  \ A long double cast to its own type moves nothing; any other needs x87.
  over cc-last-struct-desc @ cc-ld? over cc-cast-desc @ cc-ld?
  2dup and if, 2drop 2drop exit, then,
  or if, cc-ld-die then,
  over cc-ag-type? over cc-ag-type? or if, cc-ag-die then,
  cc-sysv-cast-types ;
' cc-ag-cast-types is cc-cast-types-fwd

```
## Retrieve the same classes through varargs

The variadic cursor machinery (Chapter 46) receives the named arguments' actual consumption from the call transport plan. Records keep their classification in unnamed and unprototyped calls.

`cc-ag-va-layout` derives GP, SSE and overflow offsets from the function plan; `cc-ag-va-last-slot` locates the last named parameter without confusing argument order with register order (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:479`):
```forth file=cc/131-cc-aggregate-abi.fth
\ va_start uses the same named-argument plan as callee entry. GP and SSE
\ exhaustion are independent; overflow begins after all named stack bytes.
: cc-ag-va-layout ( -- gp-offset fp-offset overflow-offset )
  cc-ag-plan @ >r cc-ag-function-plan @ cc-ag-plan !
  ag-gp @ [lit] 8 * ag-fp @ [lit] 16 * [lit] 48 +
  ag-stack @ [lit] 16 + r> cc-ag-plan ! ;
' cc-ag-va-layout is cc-va-layout-fwd
: cc-ag-va-last-slot ( -- slot )
  cc-ag-plan @ >r cc-ag-function-plan @ cc-ag-plan !
  ag-signature @ cc-sysv-sig-count 1- ag-arg ag-slot r> cc-ag-plan ! ;
' cc-ag-va-last-slot is cc-va-last-slot-fwd
\ va_arg of a record: an INTEGER record whose eightbytes all fit in the
\ remaining GP save slots is read there, where they are consecutive; any
\ other record comes from the overflow area, aligned as the caller stored
\ it. The value is the record's address, like every record value.
```
`cc-ag-va-record` first checks whether every INTEGER eightbyte fits in the remaining GP save slots. A successful retrieval advances the GP cursor over the entire record (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:494`):
```forth file=cc/131-cc-aggregate-abi.fth
: cc-ag-va-record ( type descriptor -- )
  2dup cc-ag-class >r
  r@ [lit] 1 = r@ [lit] 2 = or if,
    [lit] 139 cc-emit-byte [lit] 7 cc-emit-byte         \ mov eax, [rdi]
    [lit] 131 cc-emit-byte [lit] 248 cc-emit-byte
    [lit] 49 r@ [lit] 8 * - cc-emit-byte                \ cmp eax, 49-8n
    [lit] 15 cc-emit-byte [lit] 131 cc-emit-byte        \ jae overflow
    cc-out-pos @ [lit] 0 cc-emit-4le >r
    [lit] 72 cc-emit-byte [lit] 139 cc-emit-byte
    [lit] 79 cc-emit-byte [lit] 16 cc-emit-byte         \ mov rcx, [rdi+16]
    [lit] 72 cc-emit-byte [lit] 1 cc-emit-byte [lit] 193 cc-emit-byte
    [lit] 131 cc-emit-byte [lit] 7 cc-emit-byte
    r> r@ [lit] 8 * cc-emit-byte >r                     \ add dword [rdi], 8n
    [lit] 72 cc-emit-byte [lit] 137 cc-emit-byte [lit] 207 cc-emit-byte
    cc-emit-jmp-rel32-placeholder r> cc-patch-rel32-to-here >r
  else, [lit] 0 >r then,
  [lit] 72 cc-emit-byte [lit] 139 cc-emit-byte
```
The overflow path aligns the cursor for the object, advances by rounded size, and returns an address. A failed register fit leaves the GP cursor untouched, matching caller allocation (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:511`):
```forth file=cc/131-cc-aggregate-abi.fth
  [lit] 71 cc-emit-byte [lit] 8 cc-emit-byte            \ mov rax, [rdi+8]
  2dup cc-nalignment [lit] 8 > if,
    [lit] 72 cc-emit-byte [lit] 131 cc-emit-byte
    [lit] 192 cc-emit-byte [lit] 15 cc-emit-byte        \ add rax, 15
    [lit] 72 cc-emit-byte [lit] 131 cc-emit-byte
    [lit] 224 cc-emit-byte [lit] 240 cc-emit-byte       \ and rax, -16
  then,
  [lit] 72 cc-emit-byte [lit] 141 cc-emit-byte [lit] 136 cc-emit-byte
  2dup cc-nsize [lit] 8 cc-nalign cc-emit-4le           \ lea rcx, [rax+size]
  [lit] 72 cc-emit-byte [lit] 137 cc-emit-byte
  [lit] 79 cc-emit-byte [lit] 8 cc-emit-byte            \ mov [rdi+8], rcx
  cc-emit-mov-rdi-rax
  r> dup if, cc-patch-rel32-to-here else, drop then, r> drop
  cc-mark-typed-value ;
' cc-ag-va-record is cc-va-record-fwd

```
Long double shares record storage but has its own descriptor identity, so the value-shape check tests that identity before any copy; computation stays rejected until the next layer replaces these transport defaults (`forth-bootstrap/cc/131-cc-aggregate-abi.fth:527`):
```forth file=cc/131-cc-aggregate-abi.fth
\ Transport-only defaults, replaced by 132 for scalar computations and
\ exact static initialization. Other records retain their copy contract.
: cc-ld-value-shape ( source descriptor destination descriptor -- )
  [lit] 3 cc-npick [lit] 3 cc-npick [lit] 3 cc-npick [lit] 3 cc-npick
  cc-ld-mismatch cc-sysv-value-shape ;
' cc-ld-value-shape is cc-value-shape-fwd
: cc-ld-ni-scalar
  ni-type @ ni-desc @ cc-ld? 0= if, cc-om-scalar-initializer exit, then,
  cc-ni-static @ if, cc-ld-die then,
  ni-offset @ cc-ni-address cc-emit-push-rdi
  cc-putback-token cc-parse-assign
  cc-last-expr-type @ cc-last-struct-desc @ ni-type @ ni-desc @ cc-ld-mismatch
  cc-ni-mov-rsi-rdi cc-emit-pop-rdi [lit] 16 cc-ni-copy-bytes
  cc-next-token-keep ;
' cc-ld-ni-scalar is cc-ni-scalar-fwd
' cc-ld-mismatch is cc-return-shape-fwd
: cc-ld-compound ( type descriptor -- ) cc-ld? if, cc-ld-die then, ;
' cc-ld-compound is cc-aggregate-compound-fwd
```
## Compute with extended values without retaining x87 state

Long double stores ten significant bytes in a sixteen-byte object with sixteen-byte alignment. The classifier treats its shared opaque descriptor as an X87 leaf: arguments travel on the stack, while results travel through `st(0)`. A pure long-double wrapper may use that return class; a union with an integer alternative is MEMORY because the walk sees another leaf.

A fixed-frame snapshot also bounds numeric lifetimes. Each x87 computation ends with a memory result and an empty x87 stack. The type-code test alone cannot distinguish an actual record from long double; descriptor shape checks must precede conversions.

| Input | Result or destination |
|---|---|
| Type → `cc-x87-type?` | System V opaque-record type-code test. |
| Current expression → `cc-x87-last?` | Descriptor-aware long-double test. |
| Opcode, ModRM → `cc-x87-op` | Instruction bytes. |
| Current object → `cc-x87-load`, `cc-x87-save` | Load extended data or pop it into a new frame object. |
| Opcode, ModRM → `cc-x87-stage` | Stage a scalar payload for a memory instruction. |
| Exponent → `cc-x87-power` | Exact extended power used by unsigned conversion. |

The load/save helpers keep numeric results in private storage; powers are constructed exactly rather than rounded through double (`forth-bootstrap/cc/132-cc-long-double.fth:1`):
```forth file=cc/132-cc-long-double.fth
\ 132-cc-long-double.fth -- x87 scalar computations on address values.
\ Every result is popped into a private sixteen-byte frame object. No x87
\ value survives a call, expression boundary or branch. Record ABI is 131.
\ Type-only conversion sites are preceded by descriptor shape checks.
\ Actual records use whole-object copies and never scalar conversions.
' cc-f80-allocate is cc-f80-new
: cc-x87-type? ( type -- flag )
  ty-struct [lit] 0 ty-make = cc-target-sysv @ and ;
: cc-x87-last? cc-last-expr-type @ cc-last-struct-desc @ cc-ld? ;
: cc-x87-op ( opcode modrm -- ) swap cc-emit-byte cc-emit-byte ;
: cc-x87-load [lit] 219 [lit] 47 cc-x87-op ; \ fld tbyte [rdi]
: cc-x87-save
  [lit] 16 cc-ag-frame cc-emit-lea-rdi-local
  [lit] 219 [lit] 63 cc-x87-op ;              \ fstp tbyte [rdi]
: cc-x87-stage ( opcode modrm -- )
  [lit] 8 cc-ag-frame dup cc-emit-store-local cc-emit-lea-rdi-local cc-x87-op ;
: cc-x87-power ( exponent -- )
  \ Exact power of two in extended format, constructed in a frame object.
  [lit] 16383 + >r 2^63 cc-emit-movabs-rdi-imm64
  [lit] 16 cc-ag-frame dup >r cc-emit-store-local
  r@ 1- r> r> cc-emit-mov-rdi-int
  >r cc-emit-store-local r> cc-emit-lea-rdi-local cc-x87-load ;
```
`cc-x87-truncate` saves and restores the caller's control word around integer conversion. `cc-x87-to-u64` splits the unsigned range at its high bit so signed truncation can handle either half (`forth-bootstrap/cc/132-cc-long-double.fth:23`):
```forth file=cc/132-cc-long-double.fth
: cc-x87-truncate
  \ Save caller's control word, select truncation, fistp, then restore it.
  [lit] 16 cc-ag-frame dup >r cc-emit-lea-rdi-local
  [lit] 217 [lit] 63 cc-x87-op                \ fnstcw [rdi]
  [lit] 15 [lit] 183 cc-x87-op [lit] 7 cc-emit-byte
  [lit] 128 [lit] 204 cc-x87-op [lit] 12 cc-emit-byte \ or ah,12
  [lit] 102 [lit] 137 cc-x87-op [lit] 71 cc-emit-byte [lit] 2 cc-emit-byte
  [lit] 217 [lit] 111 cc-x87-op [lit] 2 cc-emit-byte \ fldcw [rdi+2]
  [lit] 223 [lit] 127 cc-x87-op [lit] 8 cc-emit-byte \ fistp qword [rdi+8]
  [lit] 217 [lit] 47 cc-x87-op                \ fldcw [rdi]
  r> 1- cc-emit-load-local ;
: cc-x87-to-u64
  [lit] 63 cc-x87-power                     \ st0=2^63, st1=x
  [lit] 223 [lit] 233 cc-x87-op              \ fucomip st0,st1
  [lit] 135 cc-fp-jcc >r                    \ ja: x < 2^63
  [lit] 63 cc-x87-power
  [lit] 222 [lit] 233 cc-x87-op              \ fsubp st1,st0
  cc-x87-truncate ty-ulong [lit] 0 ty-make cc-fp-flip-sign
  cc-emit-jmp-rel32-placeholder r> cc-patch-rel32-to-here >r
  cc-x87-truncate r> cc-patch-rel32-to-here ;
```
`cc-x87-convert` loads float or double at its own width. Integer inputs normalize first; a high unsigned input is loaded as signed and corrected with an exact power (`forth-bootstrap/cc/132-cc-long-double.fth:43`):
```forth file=cc/132-cc-long-double.fth
: cc-x87-convert ( source destination -- )
  2dup cc-x87-type? swap cc-x87-type? or 0= if, cc-fp-convert exit, then,
  2dup = if, 2drop exit, then,
  dup cc-x87-type? if,
    over cc-fp-type? if,
      over cc-f32-type? if, [lit] 217 else, [lit] 221 then,
      [lit] 7 cc-x87-stage
    else,
      over cc-const-integer? 0= if, cc-ld-die then,
      over cc-emit-convert-rdi
      over ty-unsigned? [lit] 2 cc-npick ty-size [lit] 8 = and if,
        cc-emit-test-rdi [lit] 137 cc-fp-jcc >r
        [lit] 223 [lit] 47 cc-x87-stage
        [lit] 64 cc-x87-power [lit] 222 [lit] 193 cc-x87-op
        cc-emit-jmp-rel32-placeholder r> cc-patch-rel32-to-here >r
        [lit] 223 [lit] 47 cc-x87-stage r> cc-patch-rel32-to-here
      else, [lit] 223 [lit] 47 cc-x87-stage then,
    then,
    2drop cc-x87-save
  else,
```
Conversion out stores directly at the destination floating precision, compares with zero for Boolean conversion, or truncates for integers. Nonfinite and out-of-range integer conversions have no defined C result (`forth-bootstrap/cc/132-cc-long-double.fth:63`):
```forth file=cc/132-cc-long-double.fth
    dup ty-void [lit] 0 ty-make = if, 2drop exit, then,
    cc-x87-load
    dup cc-fp-type? if,
      [lit] 8 cc-ag-frame dup >r cc-emit-lea-rdi-local
      dup cc-f32-type? if, [lit] 217 else, [lit] 221 then,
      [lit] 31 cc-x87-op r> cc-emit-load-local
    else,
      dup cc-bool-type? if,
        [lit] 217 [lit] 238 cc-x87-op        \ fldz
        [lit] 223 [lit] 233 cc-x87-op
        [lit] 221 [lit] 216 cc-x87-op        \ fstp st0
        [lit] 15 [lit] 149 cc-x87-op [lit] 192 cc-emit-byte
        [lit] 15 [lit] 154 cc-x87-op [lit] 194 cc-emit-byte
        [lit] 8 [lit] 208 cc-x87-op
        [lit] 15 [lit] 182 cc-x87-op [lit] 248 cc-emit-byte
      else,
        dup cc-const-integer? 0= if, cc-ld-die then,
        dup ty-unsigned? over ty-size [lit] 8 = and if,
          cc-x87-to-u64 else, cc-x87-truncate then,
      then,
    then, nip cc-emit-convert-rdi
  then, ;
' cc-x87-convert is cc-emit-convert-value
```
## Select arithmetic only for numeric descriptors

`cc-x87-initialize` keeps actual records out of scalar stores, while `cc-x87-right` preserves the left operand during conversion of the right (`forth-bootstrap/cc/132-cc-long-double.fth:86`):
```forth file=cc/132-cc-long-double.fth
\ Initializers store integers at their destination width without a separate
\ conversion. Preserve that byte sequence unless an x87 value participates.
\ The shared record type code is insufficient: bitfield leaves do not run
\ a descriptor shape check, so reject actual records here as before 132.
: cc-x87-initialize ( source destination -- )
  over cc-ag-type? if,
    over cc-last-struct-desc @ cc-ld? 0= if, cc-ag-die then,
  then,
  2dup cc-x87-type? swap cc-x87-type? or if,
    cc-x87-convert
  else, cc-ag-initialize then, ;
' cc-x87-initialize is cc-value-init-fwd
: cc-x87-right
  2dup cc-x87-type? swap cc-x87-type? or 0= if, cc-fp-convert-right exit, then,
  cc-emit-push-rdi
  [lit] 72 [lit] 137 cc-x87-op [lit] 207 cc-emit-byte
  cc-x87-convert cc-emit-mov-rcx-rdi cc-emit-pop-rdi ;
' cc-x87-right is cc-emit-convert-right
```
`cc-x87-arithmetic?` accepts integers, scalar floating types and descriptor-identified long double. `cc-x87-common` chooses extended computation only after both operands pass that check (`forth-bootstrap/cc/132-cc-long-double.fth:104`):
```forth file=cc/132-cc-long-double.fth
: cc-x87-arithmetic? ( type descriptor -- flag )
  2dup cc-ld? >r drop dup cc-const-integer? swap cc-fp-type? or r> or ;
: cc-x87-common ( left right -- type )
  over cc-expr-left-desc @ cc-ld? over cc-expr-right-desc @ cc-ld? or if,
    over cc-expr-left-desc @ cc-x87-arithmetic?
    over cc-expr-right-desc @ cc-x87-arithmetic? and 0= if, cc-ld-die then,
    2dup cc-x87-type? swap cc-x87-type? or if,
      2drop ty-struct [lit] 0 ty-make exit,
    then,
  then, cc-ag-common-type ;
' cc-x87-common is cc-expr-common-type
```
`cc-x87-binop-check` limits extended operands to arithmetic and comparisons; integer-only operators remain rejected (`forth-bootstrap/cc/132-cc-long-double.fth:115`):
```forth file=cc/132-cc-long-double.fth
: cc-x87-binop-check
  cc-expr-left-type @ cc-expr-left-desc @ cc-ld?
  cc-expr-right-type @ cc-expr-right-desc @ cc-ld? or if,
    cc-expr-op-row @ bo-op + @
    dup [char] + = over [char] - = or over [char] * = or over [char] / = or
    over [char] < = or over [char] > = or over pt-le = or over pt-ge = or
    over pt-eq-eq = or swap pt-bang-eq = or 0= if, cc-ld-die then,
  then, cc-sysv-array-binop ;
' cc-x87-binop-check is cc-array-binop-fwd
```
`cc-x87-binop` loads right then left so subtraction and division preserve operand order. Arithmetic pops into private storage; comparisons pop both operands and reuse unordered flag handling (`forth-bootstrap/cc/132-cc-long-double.fth:124`):
```forth file=cc/132-cc-long-double.fth
: cc-x87-binop
  cc-expr-common @ cc-x87-type? 0= if, cc-fp-binop exit, then,
  [lit] 219 [lit] 41 cc-x87-op cc-x87-load \ right then left
  cc-expr-op-row @ bo-op + @
  dup [char] + = if, drop [lit] 193 else,
  dup [char] - = if, drop [lit] 225 else,
  dup [char] * = if, drop [lit] 201 else,
  dup [char] / = if, drop [lit] 241 else,
    \ Reuse IEEE unordered comparison handling after x87 sets EFLAGS.
    [lit] 223 [lit] 233 cc-x87-op [lit] 221 [lit] 216 cc-x87-op
    dup [char] < = over [char] > = or over pt-le = or over pt-ge = or
    over pt-eq-eq = or over pt-bang-eq = or 0= if, cc-ld-die then,
    cc-fp-comparison-flags exit,
  then, then, then, then,
  [lit] 222 swap cc-x87-op cc-x87-save ;
' cc-x87-binop is cc-native-binop-emit
```
## Freeze loads and updates

| Input | Result or destination |
|---|---|
| Current expression → `cc-x87-test`, `cc-x87-not` | Boolean test or its negation. |
| Current expression → `cc-x87-negate`, `cc-x87-plus` | Extended sign change or accepted unary plus. |
| Current expression → `cc-x87-change-check` | Admit extended updates, delegate other checks. |
| Update metadata → `cc-x87-change` | Increment or decrement with an exact unit. |
| Type, field → `cc-x87-field-load`, `cc-x87-field-store` | Snapshot extended data or store its significant bytes. |

Boolean conversion treats signed zeros as false and unordered values as true; unary minus loads, changes sign and saves a fresh object. `cc-x87-plus` accepts a long-double operand without changing it (`forth-bootstrap/cc/132-cc-long-double.fth:151`):
```forth file=cc/132-cc-long-double.fth
: cc-x87-test
  cc-x87-last? if,
    cc-last-expr-type @ ty-bool [lit] 0 ty-make cc-x87-convert cc-emit-test-rdi
  else, cc-ag-test then, ;
: cc-x87-not
  cc-x87-last? if,
    cc-x87-test cc-emit-not-zero-flag
  else, cc-ag-not then, ;
: cc-x87-negate
  cc-x87-last? if, cc-x87-load [lit] 217 [lit] 224 cc-x87-op cc-x87-save
  else, cc-ag-negate then, ;
: cc-x87-plus cc-x87-last? 0= if, cc-ag-plus then, ;
' cc-x87-test is cc-value-test-fwd
' cc-x87-not is cc-value-not-fwd
' cc-x87-negate is cc-value-negate-fwd
' cc-x87-plus is cc-value-plus-fwd
```
`cc-x87-change-check` delegates non-extended checks; `cc-x87-change` increments or decrements with an exact unit. Field loads take a fixed-frame snapshot before later side effects, and field stores write the ten significant bytes (`forth-bootstrap/cc/132-cc-long-double.fth:156`):
```forth file=cc/132-cc-long-double.fth
: cc-x87-change-check cc-x87-last? 0= if, cc-fp-change-check then, ;
: cc-x87-change
  cc-change-type @ cc-change-desc @ cc-ld? if,
    cc-x87-load [lit] 217 [lit] 232 cc-x87-op \ fld1
    cc-change-delta @ [lit] 1 = if, [lit] 193 else, [lit] 233 then,
    [lit] 222 swap cc-x87-op cc-x87-save
  else, cc-fp-change-value then, ;
' cc-x87-change-check is cc-change-check-fwd
' cc-x87-change is cc-change-value-fwd
: cc-x87-field-load ( type field -- )
  over cc-last-struct-desc @ cc-ld? if,
    2drop [lit] 16 cc-ag-frame dup >r [lit] 16 swap cc-ag-copy-to-slot r> cc-emit-lea-rdi-local
  else, cc-ag-field-load then, ;
: cc-x87-field-store ( type field -- )
  over cc-x87-type? if,
    2drop cc-x87-load [lit] 219 [lit] 57 cc-x87-op \ fstp tbyte [rcx]
  else, cc-bf-store then, ;
' cc-x87-field-load is cc-field-load-fwd
' cc-x87-field-store is cc-field-store-fwd
```
## Check shapes before casts and initialization

`cc-x87-shape` admits only arithmetic partners for long double, so casts and conditionals reuse one rule instead of each deciding which operands may meet (`forth-bootstrap/cc/132-cc-long-double.fth:175`):
```forth file=cc/132-cc-long-double.fth
: cc-x87-shape ( source descriptor destination descriptor -- )
  [lit] 3 cc-npick [lit] 3 cc-npick cc-ld? [lit] 2 cc-npick [lit] 2 cc-npick cc-ld? or if,
    2dup cc-x87-arithmetic? [lit] 4 cc-npick [lit] 4 cc-npick cc-x87-arithmetic? and 0= if,
      cc-ld-die
    then,
  else,
    [lit] 3 cc-npick cc-ag-type? [lit] 2 cc-npick cc-ag-type? <> if, cc-ag-die then,
  then, cc-sysv-value-shape ;
' cc-x87-shape is cc-value-shape-fwd
' cc-x87-shape is cc-return-shape-fwd
: cc-x87-cast ( source destination -- )
  dup ty-void [lit] 0 ty-make = if, cc-ag-cast-types exit, then,
  over cc-last-struct-desc @ cc-ld? over cc-cast-desc @ cc-ld? or if,
    over cc-last-struct-desc @ [lit] 2 cc-npick cc-cast-desc @ cc-x87-shape
    2drop exit,
  then, cc-ag-cast-types ;
' cc-x87-cast is cc-cast-types-fwd
: cc-x87-ternary ( left-type left-desc inner null qualified patch -- handled? )
  [lit] 5 cc-npick [lit] 5 cc-npick cc-ld? cc-x87-last? or if,
    [lit] 0 exit,
  then, cc-ag-ternary ;
' cc-x87-ternary is cc-aggregate-ternary-fwd
: cc-x87-scalar-check ( type -- )
  dup cc-x87-type? if, drop else, cc-fp-scalar-check then, ;
' cc-x87-scalar-check is cc-sysv-check-scalar
```
`cc-x87-ni-scalar` converts runtime initializers before copying the object. `cc-x87-literal` materializes the already-parsed extended significand and exponent into a frame object; it does not repeat literal rounding (`forth-bootstrap/cc/132-cc-long-double.fth:200`):
```forth file=cc/132-cc-long-double.fth
: cc-x87-ni-scalar
  ni-type @ ni-desc @ cc-ld? 0= if, cc-om-scalar-initializer exit, then,
  cc-ni-static @ if, cc-ld-die then,
  ni-offset @ cc-ni-address cc-emit-push-rdi
  cc-putback-token cc-parse-assign cc-emit-materialize
  cc-last-expr-type @ cc-last-struct-desc @ ni-type @ ni-desc @ cc-value-shape-fwd
  cc-last-expr-type @ ni-type @ cc-x87-convert
  cc-ni-mov-rsi-rdi cc-emit-pop-rdi [lit] 16 cc-ni-copy-bytes
  cc-next-token-keep ;
' cc-x87-ni-scalar is cc-ni-scalar-fwd
: cc-x87-literal
  cc-target-sysv @ tok-kind @ tk-float = and 0= if, [lit] 0 exit, then,
  cc-const-float-spelling
  dup ty-base ty-ldouble = if,
    drop dup @ cc-emit-movabs-rdi-imm64
    [lit] 16 cc-ag-frame dup >r cc-emit-store-local
    [lit] 8 + @ cc-emit-movabs-rdi-imm64 r@ 1- cc-emit-store-local
    r> cc-emit-lea-rdi-local
    ty-struct [lit] 0 ty-make cc-ld-descriptor cc-mark-typed-value
  else, swap cc-emit-movabs-rdi-imm64 [lit] 0 cc-mark-typed-value then,
  true ;
' cc-x87-literal is cc-value-literal-fwd
```
`cc-x87-initializer` uses the constant evaluator's representation to patch object data or emit typed stores; its runtime branch delegates to the converted-copy initializer (`forth-bootstrap/cc/132-cc-long-double.fth:222`):
```forth file=cc/132-cc-long-double.fth
: cc-x87-initializer
  ni-type @ ni-desc @ cc-ld? 0= if, cc-om-scalar-initializer exit, then,
  cc-ni-static @ if,
    cc-putback-token cc-parse-static-const-fwd
    if, cc-const-unsupported then, drop
    ty-ldouble [lit] 0 ty-make cc-const-change
    cc-sysv-object-mode @ if,
      dup @ cc-obj-data nc-slot @ om-offset @ ni-offset @ + [lit] 8 cc-obj-patch
      [lit] 8 + @ cc-obj-data nc-slot @ om-offset @ ni-offset @ + [lit] 8 +
      [lit] 8 cc-obj-patch
    else,
      dup @ >r ni-offset @ cc-ni-address cc-emit-mov-rcx-rdi
      r> cc-emit-movabs-rdi-imm64 ty-ulong [lit] 0 ty-make cc-emit-store-typed-via-rcx
      [lit] 8 + @ >r ni-offset @ [lit] 8 + cc-ni-address cc-emit-mov-rcx-rdi
      r> cc-emit-movabs-rdi-imm64 ty-ulong [lit] 0 ty-make cc-emit-store-typed-via-rcx
    then, cc-next-token-keep exit,
  then, cc-x87-ni-scalar ;
' cc-x87-initializer is cc-ni-scalar-fwd
```
## Try it

Run from the `forth-bootstrap` checkout root with the seed already built. The block loads the compiler through these aggregate and extended computation layers, compiles caller and callee separately, and links them with the Forth linker and a small `_start`. The shell displays each returned integer through the process status.

`shift` receives the INTEGER pair and an SSE double, changes its local copy, and returns the pair by value. The original object stays intact. `extended` exercises stack-passed long double and x87 multiplication. Records with double members remain unsupported; scalar SSE transport does not imply an SSE aggregate classifier.

<!-- tryit: expect "returned left = 23\nreturned right = 32\noriginal left = 20\nextended result = 8" -->
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
[lit] 137 cc-obj-byte [lit] 199 cc-obj-byte  [lit] 184 cc-obj-byte [lit] 60 cc-obj-4le
[lit] 15 cc-obj-byte [lit] 5 cc-obj-byte
create entry-name s, _start  create main-name s, main
entry-name [lit] 6 cc-obj-global cc-obj-func cc-obj-default cc-obj-text [lit] 0 [lit] 14 cc-obj-symbol drop
main-name [lit] 4 cc-obj-global cc-obj-func cc-obj-default cc-obj-undef [lit] 0 [lit] 0 cc-obj-symbol
>r cc-obj-text [lit] 1 cc-obj-plt32 r> [lit] 0 [lit] 4 - cc-obj-reloc
output-path cc-obj-write bye
FORTH
} | ./seed-forth || exit "$?"
cat > "$work/peer.c" <<'C' || exit "$?"
struct Pair { long left; long right; };
struct Pair shift(struct Pair p, double delta) {
    p.left += (long)delta;
    p.right += 2;
    return p;
}
long extended(long double x) { return (long)(x * 2.0L); }
C
for probe in 0 1 2 3; do
printf '#define PROBE %s\n' "$probe" > "$work/probe.c"
cat >> "$work/probe.c" <<'C' || exit "$?"
struct Pair { long left; long right; };
struct Pair shift(struct Pair, double);
long extended(long double);
int main(void) {
    struct Pair original = {20, 30};
    struct Pair answer = shift(original, 3.0);
    if (original.left != 20 || original.right != 30) return 100;
    if (PROBE == 0) return answer.left;
    if (PROBE == 1) return answer.right;
    if (PROBE == 2) return original.left;
    return extended(4.0L);
}
C
for unit in peer probe; do
{
  cat forth/010-lib.fth cc/0[2-9]*-cc-*.fth cc/1[01]*-cc-*.fth \
      cc/121-cc-sysv.fth cc/123-cc-object-program.fth \
      cc/124-cc-target.fth cc/125-cc-consteval.fth cc/126-cc-varargs.fth \
      cc/127-cc-binary64.fth cc/128-cc-float-literal.fth cc/129-cc-bitfield.fth \
      cc/131-cc-aggregate-abi.fth cc/132-cc-long-double.fth || exit "$?"
  printf 'create output-path s, %s [lit] 0 c,\n' "$work/$unit.o"
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
{
  cat forth/010-lib.fth cc/020-cc-arena.fth cc/030-cc-io.fth cc/140-cc-link.fth || exit "$?"
  for name in start.o peer.o probe.o result; do printf 'create p-%s s, %s/%s [lit] 0 c,\n' "$name" "$work" "$name"; done
  printf '%s\n' 'create entry-name s, _start' \
    'lnk-init p-start.o lnk-add-object p-peer.o lnk-add-object p-probe.o lnk-add-object entry-name [lit] 6 lnk-entry p-result lnk-link lnk-release bye'
} | ./seed-forth || exit "$?"
result=0
"$work/result" || result=$?
case "$probe" in
  0) label='returned left'; expected=23 ;;
  1) label='returned right'; expected=32 ;;
  2) label='original left'; expected=20 ;;
  3) label='extended result'; expected=8 ;;
esac
printf '%s = %s\n' "$label" "$result"
test "$result" -eq "$expected" || exit 1
done
)
# prints "returned left = 23\nreturned right = 32\noriginal left = 20\nextended result = 8"
```
Observed output:
```text
returned left = 23
returned right = 32
original left = 20
extended result = 8
```
## Exercise

Hints and feedback are in [Appendix H](66-exercise-feedback.md#chapter-49-whole-record-decisions).

**Trace — easy.** Follow the call plan for `shift`: locate the pair, the double and the result object. Explain which copy keeps `original` unchanged.

**Verify — moderate.** Add integer parameters before the pair until it no longer fits in GP registers. Add an integer after it and explain why that later argument can still use a register. Compile the two units again and check the returned members.
