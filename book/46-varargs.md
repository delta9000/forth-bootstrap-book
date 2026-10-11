# Chapter 46 — System V varargs

`sum(8, 1L, 2L, 3L, 4L, 5L, 6L, 7L, 8L)` must find arguments that have no parameter names. A saved register area and a movable `va_list` cursor supply the missing access. The resulting variadic function retrieves values across the register/stack boundary and returns their sum.

## Preserve arguments for later retrieval

A variadic definition needs three additions: save incoming registers, validate a `va_list`, and emit the cursor operations requested by C intrinsics. The System V call sequence already supplies the arguments (Chapter 41); this layer replaces the hook that rejects variadic definitions. `cc-va-signature` retains the definition's signature even if a block-scope declaration changes parser state. `cc-va-register-slot` identifies the save area's base local slot.

First place the opening call's arguments. Named parameter `n=8` uses
RDI. Values 1 through 5 use the other five integer argument registers;
values 6 through 8 arrive on the stack. Saving the registers gives
`va_arg` stable memory to read after the function starts using those
registers for its own work.

The list is a position in these saved arguments. It does not contain the
argument values, a count of remaining values, or their types. `n` supplies
the loop bound in this example, and each `va_arg(ap, long)` supplies the
type to retrieve. Asking for the wrong type cannot be repaired by
inspecting the bytes. The chapter's validation checks the list's layout
and supported operations, not agreement with every caller's unnamed
argument list.

For the integer-only checkpoint, let `R` be the register-save base and
`O` the address of the first unnamed stack argument. This manual trace
starts just after `va_start`:

| Next value | Address returned | `gp_offset` afterward | Overflow pointer afterward |
|---|---|---:|---|
| 1 | `R + 8` | 16 | `O` |
| 2 through 5 | `R + 16` through `R + 40` | 48 after value 5 | `O` |
| 6 | `O` | 48 | `O + 8` |
| 7 | `O + 8` | 48 | `O + 16` |
| 8 | `O + 16` | 48 | `O + 24` |

The initial GP offset is 8 because the named parameter already used RDI.
Once the offset reaches 48, there is no seventh saved GP register to
read: retrieval switches to the overflow pointer. Only the selected
cursor advances. This is why the two pointers and offsets in a list must
survive independently, even though the C loop asks for one value at a
time. The helpers below implement those two paths and then extend the
same choice to the floating and extended formats.

Bad intrinsic operands need a recognizable diagnostic: `cc-va-error-prefix` stores `varargs: `, and `cc-va-die` writes it before the ordinary compiler error (`forth-bootstrap/cc/126-cc-varargs.fth:6`):

```forth file=cc/126-cc-varargs.fth
\ 126-cc-varargs.fth — INTEGER/binary64/X87 System V AMD64 variadic callees.
\ va_list is the real 24-byte record array[1], declared by stdarg.h.
\ Six GP and eight XMM slots belong to each invocation below named parameters.
\ Binary64 retrieval consumes XMM or overflow slots; 131 supplies named ABI offsets.
create cc-va-error-prefix s, varargs: bl c,
: cc-va-die cc-va-error-prefix [lit] 9 cc-err-write cc-die ;

variable cc-va-signature
variable cc-va-register-slot

```

Each invocation needs its own saved arguments. `cc-va-prepare` pads an odd local count, reserves 22 slots, and records the lowest-address slot; `cc-va-save-xmm` emits an uninterpreted `movups` store at an offset from that base (`forth-bootstrap/cc/126-cc-varargs.fth:11`):

```forth file=cc/126-cc-varargs.fth
: cc-va-prepare ( signature -- )
  dup cc-va-signature !
  cc-sysv-sig-varargs [lit] 1 and if,
    cc-fn-local-count @ [lit] 1 and if, [lit] 1 cc-fn-add-slots then,
    cc-fn-local-count @ [lit] 21 + cc-va-register-slot !
    [lit] 22 cc-fn-add-slots
  then, ;
: cc-va-save-xmm ( index -- )
  [lit] 15 cc-emit-byte [lit] 17 cc-emit-byte
  dup [lit] 8 * [lit] 133 + cc-emit-byte \ movups [rbp+disp32], xmmN
  [lit] 16 * [lit] 48 +
  cc-va-register-slot @ 1+ [lit] 8 * - cc-emit-4le ;
```

The reserved area is 176 bytes: 48 for GP registers and 128 for XMM registers. Memory offsets increase while local slot numbers decrease. Padding keeps the base aligned to 16 bytes. These are frame locals, so recursive invocations do not share argument storage.

The function-entry hook runs before parameter storage (`forth-bootstrap/cc/121-cc-sysv.fth:1326`).

Saving must precede parameter copies that can overwrite incoming registers. `cc-va-save-registers` stores RDI through R9, then XMM0 through XMM7 (`forth-bootstrap/cc/126-cc-varargs.fth:23`):

```forth file=cc/126-cc-varargs.fth
: cc-va-save-registers
  cc-va-signature @ cc-sysv-sig-varargs [lit] 1 and if,
    cc-va-register-slot @ dup cc-emit-store-local
    1- dup cc-emit-store-local-from-rsi
    1- dup cc-emit-store-local-from-rdx
    1- dup cc-emit-store-local-from-rcx
    1- dup cc-emit-store-local-from-r8
    1- cc-emit-store-local-from-r9
    [lit] 0 begin, dup [lit] 8 < while,
      dup cc-va-save-xmm 1+
    repeat, drop
  then, ;

```

The XMM saves are unconditional. They preserve possible floating arguments without branching on the caller's AL count or interpreting the values. Floating expressions themselves belong to Chapter 47.

## Validate the list's identity

The public `va_list` is an array of one record. Its local object contains the cursor; passing it as a parameter passes a pointer to that record, so the callee can advance the original list. Replacing the typedef with a pointer would lose local storage. Passing a record value would instead lose the shared cursor.

The record layout is fixed:

| Field | Byte offset | Contents |
|---|---:|---|
| `gp_offset` | 0 | Unsigned offset of the next GP save slot |
| `fp_offset` | 4 | Unsigned offset of the next XMM save slot |
| `overflow_arg_area` | 8 | Pointer to the next stack argument |
| `reg_save_area` | 16 | Pointer to saved RDI |

The offsets occupy four bytes each; the pointers occupy eight. The record occupies 24 bytes and has eight-byte alignment.

The intrinsics require the reserved `va_list` descriptor as well as the right layout. `cc-va-tag-name` identifies its tag; `cc-va-descriptor` checks its size, alignment, field count and nonunion shape, while `cc-va-field` checks each scalar field's offset and type (`forth-bootstrap/cc/126-cc-varargs.fth:36`):

```forth file=cc/126-cc-varargs.fth
create cc-va-tag-name s, __seed_va_list_tag
: cc-va-field ( descriptor index offset type -- )
  >r >r cc-sd-field-rec
  dup cc-sf-offset r> <> if, [lit] 246 cc-va-die then,
  dup cc-sf-type r> <> if, [lit] 246 cc-va-die then,
  cc-sf-array-len if, [lit] 246 cc-va-die then, ;
: cc-va-descriptor ( -- descriptor )
  cc-va-tag-name [lit] 18 cc-nfind-tag
  dup 0< if, [lit] 246 cc-va-die then, cc-sym-val-of
  dup cc-sd-total-size [lit] 24 <> if, [lit] 246 cc-va-die then,
  dup cc-sd-align [lit] 8 <> if, [lit] 246 cc-va-die then,
  dup cc-sd-field-count [lit] 4 <> if, [lit] 246 cc-va-die then,
  dup cc-sd-union? if, [lit] 246 cc-va-die then,
  dup [lit] 0 [lit] 0 ty-uint [lit] 0 ty-make cc-va-field
  dup [lit] 1 [lit] 4 ty-uint [lit] 0 ty-make cc-va-field
  dup [lit] 2 [lit] 8 ty-void [lit] 1 ty-make cc-va-field
  dup [lit] 3 [lit] 16 ty-void [lit] 1 ty-make cc-va-field ;
```

An intrinsic needs a checked address before it can touch the cursor. `cc-va-operand` parses its expression once, requires a pointer to that descriptor, rejects an inner array dimension, and materializes the address. `cc-va-expect` checks punctuation; `cc-va-void-result` marks a completed operation as void (`forth-bootstrap/cc/126-cc-varargs.fth:53`):

```forth file=cc/126-cc-varargs.fth
: cc-va-expect ( punctuation -- )
  cc-next-token-keep cc-tok-punct? 0= if, [lit] 246 cc-va-die then, ;
: cc-va-operand
  cc-parse-assign-fwd
  cc-last-expr-type @ ty-struct [lit] 1 ty-make <> if,
    [lit] 246 cc-va-die
  then,
  cc-last-struct-desc @ cc-va-descriptor <> if, [lit] 246 cc-va-die then,
  cc-last-expr-array-inner @ if, [lit] 246 cc-va-die then,
  cc-emit-materialize ;
: cc-va-void-result
  [lit] 0 cc-emit-mov-rdi-int
  ty-void [lit] 0 ty-make [lit] 0 cc-mark-typed-value ;

```

The diagnostic code for a malformed list or invocation is 246. Shape checks and descriptor identity serve different purposes: a matching layout alone does not make an unrelated structure a `va_list`.

## Start after the named parameters

Initializing a cursor must leave its address in RDI. `cc-va-store-u32` writes an offset field directly; `cc-va-store-frame-address` computes a frame-relative pointer in RAX and stores it into the list (`forth-bootstrap/cc/126-cc-varargs.fth:67`):

```forth file=cc/126-cc-varargs.fth
\ rdi addresses the list. These helpers do not move that address.
: cc-va-store-u32 ( value displacement -- )
  [lit] 199 cc-emit-byte
  dup if, [lit] 71 cc-emit-byte cc-emit-byte
  else, drop [lit] 7 cc-emit-byte then,
  cc-emit-4le ;
: cc-va-store-frame-address ( frame-offset list-offset -- )
  >r [lit] 72 cc-emit-byte [lit] 141 cc-emit-byte
  [lit] 133 cc-emit-byte cc-emit-4le       \ lea rax, [rbp+disp32]
  [lit] 72 cc-emit-byte [lit] 137 cc-emit-byte
  [lit] 71 cc-emit-byte r> cc-emit-byte ; \ mov [rdi+disp8], rax
```

The last named argument is a parameter identity, not a value to evaluate. `cc-va-last-named` checks the variadic signature, spelling, local-symbol kind and frame slot. `cc-va-last-slot-default` supplies the slot through `cc-va-last-slot-fwd`; Chapter 49 replaces that default for its entry plan (`forth-bootstrap/cc/126-cc-varargs.fth:78`):

```forth file=cc/126-cc-varargs.fth
\ The last named parameter's frame slot; 131 supplies it from its entry plan,
\ where a sixteen-byte long double parameter occupies two slots.
: cc-va-last-slot-default ( -- slot ) cc-va-signature @ cc-sysv-sig-count ;
defer cc-va-last-slot-fwd
' cc-va-last-slot-default is cc-va-last-slot-fwd
: cc-va-last-named
  cc-va-signature @ dup 0= if, [lit] 246 cc-va-die then,
  dup cc-sysv-sig-varargs [lit] 1 and 0= if, [lit] 246 cc-va-die then,
  dup cc-sysv-sig-count 1- cc-sysv-sig-name
  cc-next-token-keep
  tok-kind @ tk-ident <> if, [lit] 246 cc-va-die then,
  dup [lit] 8 + @ tok-str-len @ <> if, [lit] 246 cc-va-die then,
  @ tok-str-addr @ tok-str-len @ bytes-eq 0= if, [lit] 246 cc-va-die then,
  tok-str-addr @ tok-str-len @ cc-sym-find
  dup 0< if, [lit] 246 cc-va-die then,
  dup cc-sym-kind-of sk-local <> if, [lit] 246 cc-va-die then,
  cc-sym-val-of cc-va-last-slot-fwd <> if,
    [lit] 246 cc-va-die
  then, ;
```

Checking the slot also rejects a local variable that shadows the parameter. Assigning a new value to the actual parameter does not change where unnamed arguments begin.

The initial cursor must skip the named arguments. `cc-va-layout-default` returns the GP offset, FP offset and frame-relative overflow address through `cc-va-layout-fwd`; `cc-va-start` writes those fields and the register-save pointer (`forth-bootstrap/cc/126-cc-varargs.fth:97`):

```forth file=cc/126-cc-varargs.fth
: cc-va-layout-default ( -- gp-offset fp-offset overflow-offset )
  cc-va-signature @ cc-sysv-sig-count dup [lit] 6 > if,
    drop [lit] 6
  then, [lit] 8 * [lit] 48
  cc-va-signature @ cc-sysv-sig-count cc-sysv-stack-count [lit] 8 * [lit] 16 + ;
defer cc-va-layout-fwd
' cc-va-layout-default is cc-va-layout-fwd
: cc-va-start
  cc-va-operand [char] , cc-va-expect
  cc-va-last-named [char] ) cc-va-expect
  cc-va-layout-fwd >r swap [lit] 0 cc-va-store-u32
  [lit] 4 cc-va-store-u32 r> [lit] 8 cc-va-store-frame-address
  [lit] 0 cc-va-register-slot @ 1+ [lit] 8 * -
  [lit] 16 cc-va-store-frame-address
  cc-va-void-result ;

```

With INTEGER named parameters, the GP offset is eight times the named count, capped at 48. The FP offset starts at 48. The overflow pointer starts at `rbp + 16`, plus eight bytes for each named stack argument. Chapter 49 replaces `cc-va-layout-fwd` with the shared argument plan for mixed named types.

For `sum`, `n` consumes the first GP register. The list starts at GP offset 8 and retrieves five unnamed values from saved registers before using the stack. A later `va_start` can reset the same list from the invocation's saved arguments.

## Advance the appropriate cursor

Retrieval first selects an address; loading the requested type comes afterward. The INTEGER class covers integers and pointers; the X87 path handles extended floating values. The selectors differ where the ABI requires it:

| Requested class → selector | Register path | Overflow path |
|---|---|---|
| INTEGER → `cc-va-next-address` | Below 48: take GP slot, advance by 8 | Take stack slot, advance by 8 |
| `double` → `cc-va-next-double-address` | Below 176: take XMM slot, advance by 16 | Take stack slot, advance by 8 |
| X87 → `cc-va-next-x87-address` | None | Align to 16, take object, advance by 16 |

Each selector replaces the list address in RDI with the argument address. Register exhaustion is independent for GP and XMM; overflow accesses share a pointer and follow argument order.

The INTEGER path branches on `gp_offset`, leaving the old slot available while it advances the stored cursor (`forth-bootstrap/cc/126-cc-varargs.fth:113`):

```forth file=cc/126-cc-varargs.fth
\ Choose the next eight-byte INTEGER slot, updating only that list's cursor.
\ The caller then loads the requested four- or eight-byte value from rdi.
: cc-va-next-address
  [lit] 139 cc-emit-byte [lit] 7 cc-emit-byte         \ mov eax, [rdi]
  [lit] 131 cc-emit-byte [lit] 248 cc-emit-byte [lit] 48 cc-emit-byte
  [lit] 15 cc-emit-byte [lit] 131 cc-emit-byte        \ jae overflow
  cc-out-pos @ [lit] 0 cc-emit-4le >r
  [lit] 72 cc-emit-byte [lit] 139 cc-emit-byte
  [lit] 79 cc-emit-byte [lit] 16 cc-emit-byte         \ mov rcx, [rdi+16]
  [lit] 72 cc-emit-byte [lit] 1 cc-emit-byte [lit] 193 cc-emit-byte
  [lit] 131 cc-emit-byte [lit] 7 cc-emit-byte [lit] 8 cc-emit-byte
  [lit] 72 cc-emit-byte [lit] 137 cc-emit-byte [lit] 207 cc-emit-byte
  cc-emit-jmp-rel32-placeholder r> cc-patch-rel32-to-here >r
  [lit] 72 cc-emit-byte [lit] 139 cc-emit-byte
  [lit] 71 cc-emit-byte [lit] 8 cc-emit-byte          \ mov rax, [rdi+8]
  [lit] 72 cc-emit-byte [lit] 141 cc-emit-byte
  [lit] 72 cc-emit-byte [lit] 8 cc-emit-byte          \ lea rcx, [rax+8]
  [lit] 72 cc-emit-byte [lit] 137 cc-emit-byte
  [lit] 79 cc-emit-byte [lit] 8 cc-emit-byte          \ mov [rdi+8], rcx
  cc-emit-mov-rdi-rax r> cc-patch-rel32-to-here ;
```

An XMM slot carries its double payload in the low eight bytes. The full immediate comparison against 176 avoids treating that threshold as a negative signed byte (`forth-bootstrap/cc/126-cc-varargs.fth:133`):

```forth file=cc/126-cc-varargs.fth
\ Choose the next SSE slot for double, preserving gp_offset. Only the low
\ eight bytes of each sixteen-byte XMM save slot are the binary64 payload.
\ A stack double requires eight-byte alignment, already maintained by every
\ supported INTEGER/double overflow access and the incoming ABI stack area.
: cc-va-next-double-address
  [lit] 139 cc-emit-byte [lit] 71 cc-emit-byte [lit] 4 cc-emit-byte
  [lit] 61 cc-emit-byte [lit] 176 cc-emit-4le        \ cmp eax, 176
  [lit] 15 cc-emit-byte [lit] 131 cc-emit-byte        \ jae overflow
  cc-out-pos @ [lit] 0 cc-emit-4le >r
  [lit] 72 cc-emit-byte [lit] 139 cc-emit-byte
  [lit] 79 cc-emit-byte [lit] 16 cc-emit-byte         \ mov rcx, [rdi+16]
  [lit] 72 cc-emit-byte [lit] 1 cc-emit-byte [lit] 193 cc-emit-byte
  [lit] 131 cc-emit-byte [lit] 71 cc-emit-byte
  [lit] 4 cc-emit-byte [lit] 16 cc-emit-byte         \ add dword [rdi+4],16
  [lit] 72 cc-emit-byte [lit] 137 cc-emit-byte [lit] 207 cc-emit-byte
  cc-emit-jmp-rel32-placeholder r> cc-patch-rel32-to-here >r
  [lit] 72 cc-emit-byte [lit] 139 cc-emit-byte
  [lit] 71 cc-emit-byte [lit] 8 cc-emit-byte          \ mov rax, [rdi+8]
  [lit] 72 cc-emit-byte [lit] 141 cc-emit-byte
  [lit] 72 cc-emit-byte [lit] 8 cc-emit-byte          \ lea rcx, [rax+8]
  [lit] 72 cc-emit-byte [lit] 137 cc-emit-byte
  [lit] 79 cc-emit-byte [lit] 8 cc-emit-byte          \ mov [rdi+8], rcx
  cc-emit-mov-rdi-rax r> cc-patch-rel32-to-here ;
```

The X87 selector rounds the overflow pointer upward before advancing it, and returns an object address without moving either register cursor (`forth-bootstrap/cc/126-cc-varargs.fth:156`):

```forth file=cc/126-cc-varargs.fth
\ Long double is class X87: always in the overflow area, aligned to sixteen
\ and sixteen bytes long, never in a register save slot. The result is the
\ object's address, as for every long double value (121).
: cc-va-next-x87-address
  [lit] 72 cc-emit-byte [lit] 139 cc-emit-byte
  [lit] 71 cc-emit-byte [lit] 8 cc-emit-byte          \ mov rax, [rdi+8]
  [lit] 72 cc-emit-byte [lit] 131 cc-emit-byte
  [lit] 192 cc-emit-byte [lit] 15 cc-emit-byte        \ add rax, 15
  [lit] 72 cc-emit-byte [lit] 131 cc-emit-byte
  [lit] 224 cc-emit-byte [lit] 240 cc-emit-byte       \ and rax, -16
  [lit] 72 cc-emit-byte [lit] 141 cc-emit-byte
  [lit] 72 cc-emit-byte [lit] 16 cc-emit-byte         \ lea rcx, [rax+16]
  [lit] 72 cc-emit-byte [lit] 137 cc-emit-byte
  [lit] 79 cc-emit-byte [lit] 8 cc-emit-byte          \ mov [rdi+8], rcx
  cc-emit-mov-rdi-rax ;
```

These selectors preserve the incoming representation. Chapter 47 supplies floating computation; Chapter 49 supplies extended-value operations and aggregate classification.

## Fetch a value of the requested type

A slot must not be consumed under an unsupported type. `cc-va-check-result-type` admits pointers, promoted integer types, double and the recognized extended type; `cc-va-record-default` rejects records through `cc-va-record-fwd` until Chapter 49 supplies their retrieval (`forth-bootstrap/cc/126-cc-varargs.fth:171`):

```forth file=cc/126-cc-varargs.fth
: cc-va-check-result-type ( type -- )
  dup [lit] 256 / [lit] 255 and if, [lit] 247 cc-va-die then,
  dup cc-cast-desc @ cc-ld? if, drop exit, then,
  dup ty-ptr if, drop exit, then,
  ty-base dup ty-int = over ty-uint = or
  over ty-long = or over ty-ulong = or over ty-llong = or over ty-ullong = or
  swap ty-double = or 0= if, [lit] 247 cc-va-die then, ;
\ A record argument's ABI class lives in 131, which supplies its retrieval.
: cc-va-record-default ( type descriptor -- ) 2drop [lit] 247 cc-va-die ;
defer cc-va-record-fwd
' cc-va-record-default is cc-va-record-fwd
```

The result-type error is 247. A promoted `char` or `short` must be requested as `int`; `float` must be requested as `double`. The integer whitelist prevents a narrow request from disguising the caller's promotion. A pointer to a floating object still uses the INTEGER path.

`va_arg` includes a type name where an ordinary call has an expression. `cc-va-arg` parses that type, rejects array requests, delegates records, and selects the address helper before applying a typed load (`forth-bootstrap/cc/126-cc-varargs.fth:182`):

```forth file=cc/126-cc-varargs.fth
: cc-va-arg
  cc-va-operand [char] , cc-va-expect
  cc-next-token-keep cc-native-type-name-fwd
  cc-type-name-array @ cc-type-name-inner @ or if, [lit] 247 cc-va-die then,
  dup ty-ptr 0= over ty-base ty-struct = and over cc-cast-desc @ cc-ld? 0= and if,
    cc-cast-desc @ [char] ) cc-va-expect cc-va-record-fwd exit,
  then,
  dup cc-va-check-result-type cc-cast-desc @ >r >r
  [char] ) cc-va-expect
  r> r> 2dup >r >r cc-ld? if,
    cc-va-next-x87-address r> r> cc-mark-typed-value exit,
  then,
  r@ ty-double [lit] 0 ty-make = if,
    cc-va-next-double-address
  else, cc-va-next-address then,
  r@ cc-emit-load-typed-via-rdi
  r> r> cc-mark-typed-value ;
```

The typed load preserves the requested width and signedness: an `int` does not expose the unused upper part of its GP slot. The extended-value path instead marks the address as its typed result. The array checks prevent requesting `va_list` itself from decaying into an accidental scalar fetch.

## Copy a cursor without copying arguments

A second traversal needs independent cursor fields. `cc-va-copy-word` emits a cell transfer; `cc-va-copy` saves the destination across evaluation of the source and copies the record. `cc-va-end` evaluates and validates its operand, then returns void (`forth-bootstrap/cc/126-cc-varargs.fth:199`):

```forth file=cc/126-cc-varargs.fth
: cc-va-copy-word ( displacement -- )
  [lit] 72 cc-emit-byte [lit] 139 cc-emit-byte
  [lit] 71 cc-emit-byte dup cc-emit-byte             \ mov rax, [rdi+disp8]
  [lit] 72 cc-emit-byte [lit] 137 cc-emit-byte
  [lit] 65 cc-emit-byte cc-emit-byte ;               \ mov [rcx+disp8], rax
: cc-va-copy
  cc-va-operand cc-emit-push-rdi [char] , cc-va-expect
  cc-va-operand [char] ) cc-va-expect cc-emit-pop-rcx
  [lit] 0 cc-va-copy-word [lit] 8 cc-va-copy-word [lit] 16 cc-va-copy-word
  cc-va-void-result ;
: cc-va-end
  cc-va-operand [char] ) cc-va-expect cc-va-void-result ;

```

Both operands of `va_copy` are evaluated once. The copied pointers still refer to the original invocation's arguments, while changes to either list's offsets or overflow pointer remain private. `va_end` has no runtime resource to release here. It does not make an expired list safe: neither an ended list nor a list whose owning invocation has returned may be reused for retrieval.

## Recognize the C spellings

The target header maps the public operations to builtins (`forth-bootstrap/chain/runtime/gcc-seed/include/stdarg.h:13`). Name recognition connects them to these handlers:

| C input → stored builtin name | Handler result |
|---|---|
| `va_start` → `cc-va-start-name` | `cc-va-start`: initialized cursor, void |
| `va_arg` → `cc-va-arg-name` | `cc-va-arg`: next typed value |
| `va_copy` → `cc-va-copy-name` | `cc-va-copy`: independent cursor, void |
| `va_end` → `cc-va-end-name` | `cc-va-end`: checked operand, void |

`cc-va-name?` compares token length before bytes so only the complete reserved spelling matches (`forth-bootstrap/cc/126-cc-varargs.fth:216`):

```forth file=cc/126-cc-varargs.fth
create cc-va-start-name s, __builtin_va_start
create cc-va-arg-name s, __builtin_va_arg
create cc-va-copy-name s, __builtin_va_copy
create cc-va-end-name s, __builtin_va_end
: cc-va-name? ( name length -- flag )
  dup tok-str-len @ <> if, 2drop [lit] 0 exit, then,
  tok-str-addr @ swap bytes-eq ;
```

`cc-va-intrinsic` gates dispatch on the System V target, checks the expression context and opening parenthesis, then invokes the selected handler. The final bindings install register preparation, register saving and intrinsic parsing (`forth-bootstrap/cc/126-cc-varargs.fth:219`):

```forth file=cc/126-cc-varargs.fth
: cc-va-intrinsic ( -- handled? )
  cc-target-sysv @ 0= if, [lit] 0 exit, then,
  cc-va-start-name [lit] 18 cc-va-name? if, [lit] 1 else,
  cc-va-arg-name [lit] 16 cc-va-name? if, [lit] 2 else,
  cc-va-copy-name [lit] 17 cc-va-name? if, [lit] 3 else,
  cc-va-end-name [lit] 16 cc-va-name? if, [lit] 4 else,
    [lit] 0 exit,
  then, then, then, then,
  cc-check-static-init lparen cc-va-expect
  dup [lit] 1 = if, drop cc-va-start else,
  dup [lit] 2 = if, drop cc-va-arg else,
  [lit] 3 = if, cc-va-copy else, cc-va-end then, then, then,
  true ;
' cc-va-prepare is cc-sysv-varargs-prepare-fwd
' cc-va-save-registers is cc-sysv-varargs-save-fwd
' cc-va-intrinsic is cc-native-intrinsic-fwd
```

The runtime formatter needs this argument cursor (Chapter 43). `printf` can initialize a list and hand it to a `v` formatter; each conversion then fetches the type implied by the format. A copied list permits another traversal without consuming the first cursor. Floating formatting also needs the remaining numeric layers. Chapter 50 assembles the complete runtime once those are available.

## Try it

Run from the `forth-bootstrap` checkout root with the seed already built. This block loads compiler layers through varargs and uses the target `stdarg.h` include directory. It compiles `sum` and its caller to an object, emits a small `_start` object, and links them with the Forth linker. The entry returns `main`'s result as the process status; the shell prints and checks it. Generated files stay in the temporary directory.

<!-- tryit: expect "sum = 36" -->
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
includes=chain/runtime/gcc-seed/include
cat > "$work/probe.c" <<'C' || exit "$?"
#include <stdarg.h>
long sum(int n, ...) {
    va_list ap;
    long total = 0;
    int i;
    va_start(ap, n);
    for (i = 0; i < n; i++) total += va_arg(ap, long);
    va_end(ap);
    return total;
}
int main(void) { return sum(8, 1L, 2L, 3L, 4L, 5L, 6L, 7L, 8L); }
C
{
  cat forth/010-lib.fth cc/0[2-9]*-cc-*.fth cc/1[01]*-cc-*.fth \
      cc/121-cc-sysv.fth cc/123-cc-object-program.fth \
      cc/124-cc-target.fth cc/125-cc-consteval.fth cc/126-cc-varargs.fth || exit "$?"
  printf 'create output-path s, %s/probe.o [lit] 0 c,\n' "$work"
  printf 'create include-path s, %s [lit] 0 c,\n' "$includes"
  printf 'include-path [lit] %s cc-prep-add-include\n' "${#includes}"
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
printf 'sum = %s\n' "$result"
test "$result" -eq 36 || exit 1
) # prints "sum = 36"
```

Observed output:

```text
sum = 36
```

The final three values come from the stack, so the result exercises both branches of `cc-va-next-address`.

## Exercise

Hints and feedback are in [Appendix H](66-exercise-feedback.md#chapter-46-a-varargs-cursor-crosses-banks).

**Trace (easy).** Follow `gp_offset` and `overflow_arg_area` through every iteration of `sum`. Identify the first iteration that leaves `gp_offset` unchanged.

**Modify (moderate).** After retrieving the first stack argument (value 6), use `va_copy` to copy the list. Sum the remaining arguments through the copy and then independently through the original, starting each suffix total at zero. Predict both suffix totals before running. Check their equality in C, return the original full total on success so the shell still expects 36, and call `va_end` on both lists.

