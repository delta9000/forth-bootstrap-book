# Chapter 48 — Record bitfields

Setting `flags.low` must leave `flags.delta` negative and `flags.high` unchanged. An ordinary integer store cannot isolate adjacent bitfields: each needs a width and a position within its storage unit. Allocation records that slice, and every store must preserve the rest of the unit.

## Describe a slice of a native object

The declaration determines a unit offset, bit shift and width; loads and stores use those three facts to isolate the field. In the LP64 native object storage (Chapter 39), a bitfield's byte offset names its containing unit. Chapter 49 extends that storage layout to record arguments and returns.

Work through the checkpoint's three fields before reading their metadata.
In this implementation, `unsigned low : 3`, `signed delta : 5`, and
`unsigned high : 4` occupy bits 0–2, 3–7, and 8–11 of one four-byte int
unit. The initializer `{5, -3, 9}` gives the low twelve bits
`1001 11101 101`, or `0x9ED`: the five-bit representation of -3 is 29.
This is a manual bit calculation; it makes no claim about the unused
upper bits of the unit.

Changing `low` to 2 must clear only mask `0x7` and insert `0x2`. The low
twelve bits become `0x9EA`; the other bits retain their previous values.
Reading `delta` then shifts by three and masks five bits, obtaining 29.
Because that field is signed and its top bit is set, sign extension
interprets it as `29 - 32 = -3`. A plain unsigned extraction would report
29; a whole-unit store of 2 would erase both neighbours. The layout,
extraction, and preserving-store words below each supply one part of
this calculation.

`cc-bf-record-bytes` expands compiler field metadata to 72 bytes only in explicit System V mode. `cc-bf-die` writes `cc-bf-error-prefix` and exits with 248 (`forth-bootstrap/cc/129-cc-bitfield.fth:1`):
```forth file=cc/129-cc-bitfield.fth
\ 129-cc-bitfield.fth -- AMD64 little-endian integer record bitfields.
\ Only the explicit SysV target changes descriptor or member semantics.
\ Named int/unsigned/long/unsigned long fields use their natural 4/8-byte
\ allocation units; a _Bool field is at most one bit in a one-byte unit. Stores preserve every bit outside the destination.
\ Volatile accesses use ordinary unit loads and RMW stores; no atomicity
\ or inter-thread synchronization is provided, and compound updates can
\ perform an operand load plus the preserving RMW load.
create cc-bf-error-prefix s, bitfield: bl c,
: cc-bf-die cc-bf-error-prefix [lit] 10 cc-err-write [lit] 248 cc-die ;
: cc-bf-record-bytes
  cc-target-sysv @ if, [lit] 72 else, cc-sd-record-bytes-default then, ;
' cc-bf-record-bytes is cc-sd-record-bytes

```

Accessors separate layout metadata from the scalar type:

| Input | Result or destination |
|---|---|
| Field record → `cc-bf-array-inner` | Retained inner array bound at offset 64 in System V mode; default elsewhere. |
| Bound, field record → `cc-bf-set-array-inner` | Same target-selected slot. |
| Descriptor → `cc-sd-bit-end` | Address of the bit cursor at offset 32. |
| Field record → `cc-sf-bit-width`, `cc-sf-bit-shift` | Width at offset 48, shift at offset 56. |
| Field record → `cc-bf?` | Nonzero width only for a non-null record in System V mode. |

Ordinary members retain zero width, and array metadata survives the enlarged field record (`forth-bootstrap/cc/129-cc-bitfield.fth:14`):
```forth file=cc/129-cc-bitfield.fth
\ The final SysV field cell retains the second fixed array dimension.
\ Bitfield slots stay at 48/56; anonymous promotion copies the entire record.
: cc-bf-array-inner ( rec -- n )
  cc-target-sysv @ if, [lit] 64 + @ else, cc-sf-array-inner-default then, ;
: cc-bf-set-array-inner ( n rec -- )
  cc-target-sysv @ if, [lit] 64 + ! else, cc-sf-set-array-inner-default then, ;
' cc-bf-array-inner is cc-sf-array-inner
' cc-bf-set-array-inner is cc-sf-set-array-inner

: cc-sd-bit-end [lit] 32 + ;
: cc-sf-bit-width [lit] 48 + @ ;
: cc-sf-bit-shift [lit] 56 + @ ;
: cc-bf? ( rec -- flag )
  cc-target-sysv @ over [lit] 0 <> and if, cc-sf-bit-width else, drop [lit] 0 then, ;
```

## Admit only implemented field types

`cc-bf-enum-desc` supplies the `cc-bf-enum-origin` marker so typedefs preserve enum provenance. `cc-bf-type?` admits only non-pointer int, long, long long, their unsigned forms, and `_Bool` (`forth-bootstrap/cc/129-cc-bitfield.fth:28`):
```forth file=cc/129-cc-bitfield.fth
\ Enum representation is a separate capability. Preserve provenance through
\ typedefs so enum fields cannot silently acquire signed-int bit semantics.
create cc-bf-enum-origin [lit] 0 ,
: cc-bf-enum-desc
  cc-target-sysv @ if, cc-bf-enum-origin else, [lit] 0 then, ;
' cc-bf-enum-desc is cc-nenum-desc-fwd

: cc-bf-type? ( ty -- flag )
  dup ty-ptr if, drop [lit] 0 exit, then,
  ty-base dup ty-int = over ty-uint = or over ty-long = or over ty-ulong = or
  over ty-llong = or over ty-ullong = or swap ty-bool = or ;

```

`cc-bf-add` saves the descriptor in `cc-bf-desc` and bit width and unit size in `cc-bf-width` and `cc-bf-unit`; `cc-bf-position` tracks the cursor and `cc-bf-record` the named member. Validation precedes placement (`forth-bootstrap/cc/129-cc-bitfield.fth:45`):
```forth file=cc/129-cc-bitfield.fth
variable cc-bf-desc
variable cc-bf-width
variable cc-bf-unit
variable cc-bf-position
variable cc-bf-record
: cc-bf-add ( desc -- )
  cc-bf-desc !
  nc-desc @ cc-bf-enum-origin = if, cc-bf-die then,
  nc-ty @ cc-bf-type? 0= nc-array @ [lit] 0 <> or
  nc-inner @ [lit] 0 <> or nc-func @ [lit] 0 <> or if, cc-bf-die then,
  cc-parse-const cc-bf-width !
  nc-ty @ ty-size [lit] 8 * cc-bf-unit !
  cc-bf-width @ [lit] 0 < cc-bf-width @ cc-bf-unit @ > or if, cc-bf-die then,
  cc-bf-width @ [lit] 32 > cc-bf-width @ [lit] 64 < and if, cc-bf-die then,
  nc-ty @ ty-base ty-bool = cc-bf-width @ [lit] 1 > and if, cc-bf-die then,
  cc-bf-width @ 0= nc-nlen @ [lit] 0 <> and if, cc-bf-die then,
```

Int fields admit widths 1–32; long and long long admit 1–32 or 64. Widths 33–63 are rejected, even when they fit the underlying type. `_Bool` admits width 1. Zero width is allowed only without a name; negative widths and widths beyond the unit fail. Enum provenance, pointers, arrays, function declarators, char, short and floating base types are rejected.

## Allocate within the containing unit

The checkpoint fits every field in one unit. The boundary case explains
why allocation tracks a bit cursor as well as a byte offset. Two unsigned
int fields of widths 31 and 2 cannot share a four-byte unit: after the first
field, only one bit remains. The second field starts at bit 32, giving it
byte offset 4 and shift 0. The first unit's spare bit remains unused; the
field is not split across two loads. This manual layout follows the
containment test below.

A struct continues at its bit cursor; a union starts at zero. Zero width
aligns the cursor without creating a member (`forth-bootstrap/cc/129-cc-bitfield.fth:56`):
```forth file=cc/129-cc-bitfield.fth
  cc-bf-desc @ cc-sd-union? if, [lit] 0 else, cc-bf-desc @ cc-sd-bit-end @ then,
  cc-bf-position !
  cc-bf-width @ 0= if,
    cc-bf-position @ cc-bf-unit @ cc-nalign cc-bf-position !
  else,
    cc-bf-position @ cc-bf-unit @ cc-mod cc-bf-width @ + cc-bf-unit @ > if,
      cc-bf-position @ cc-bf-unit @ cc-nalign cc-bf-position !
    then,
    nc-nlen @ if,
      cc-bf-desc @ cc-sd-field-count cc-bf-desc @ swap cc-sd-field-rec cc-bf-record !
      nc-name @ cc-bf-record @ cc-sf-set-name-addr
      nc-nlen @ cc-bf-record @ cc-sf-set-name-len
      nc-ty @ cc-bf-record @ cc-sf-set-type
      cc-bf-position @ cc-bf-unit @ / cc-bf-unit @ * [lit] 8 /
      cc-bf-record @ cc-sf-set-offset
      cc-bf-width @ cc-bf-record @ [lit] 48 + !
      cc-bf-position @ cc-bf-unit @ cc-mod cc-bf-record @ [lit] 56 + !
      cc-bf-desc @ dup cc-sd-field-count 1+ swap cc-sd-set-field-count
      cc-bf-desc @ cc-sd-align nc-ty @ ty-align cc-nmax cc-bf-desc @ cc-sd-set-align
    then,
    cc-bf-width @ cc-bf-position +!
  then,
  cc-bf-position @ [lit] 7 + [lit] 8 /
  cc-bf-desc @ cc-sd-total-size cc-nmax cc-bf-desc @ cc-sd-set-total-size
  cc-bf-position @ cc-bf-desc @ cc-sd-bit-end !
  cc-next-token-keep ;
```

The byte offset rounds down to the unit start; the shift is the remainder, counted from the least significant bit. Units occupy four bytes for int, eight for long and long long, one for `_Bool`. A type change recalculates containment without necessarily starting a fresh unit.

Only named fields enter the member list and raise aggregate alignment. Unnamed fields consume no initializer element; nonzero widths still consume bits. The size update rounds the bit end up to a byte and keeps the maximum, including for unions.

In `cc-bf-member`, a colon selects bit allocation; ordinary aligned members reset the cursor to their byte end. `cc-bf-layout-check` includes tail alignment when checking the object limit, failing with 245 (`forth-bootstrap/cc/129-cc-bitfield.fth:82`):
```forth file=cc/129-cc-bitfield.fth
\ Products are checked by the declarator; sums and final tail padding
\ must also fit, including when a bitfield follows a maximal matrix.
: cc-bf-layout-check ( desc -- )
  dup cc-sd-total-size swap cc-sd-align cc-nalign
  cc-sysv-object-size-limit > if, [lit] 245 cc-die then, ;
: cc-bf-member ( desc -- )
  cc-target-sysv @ 0= if, cc-nmember-default exit, then,
  [char] : cc-tok-punct? if, dup >r cc-bf-add r> cc-bf-layout-check exit, then,
  \ An incomplete outer dimension cannot describe an inline matrix.
  nc-inner @ nc-array @ [lit] 0 <= and if, [lit] 238 cc-die then,
  dup >r cc-nmember-default
  r@ cc-bf-layout-check
  r@ cc-sd-total-size [lit] 8 * r> cc-sd-bit-end ! ;
' cc-bf-member is cc-nmember-fwd

```

An inner array bound with a missing or nonpositive outer bound fails with 238.

## Extract a value with its own sign

`cc-bf-load` loads the unit and shifts the field down. `cc-bf-truncate` removes bits above its width; `cc-bf-shift-rdi` omits zero-count shifts (`forth-bootstrap/cc/129-cc-bitfield.fth:97`):
```forth file=cc/129-cc-bitfield.fth
: cc-bf-shift-rdi ( count opcode -- )
  over if,
    [lit] 72 cc-emit-byte [lit] 193 cc-emit-byte cc-emit-byte cc-emit-byte
  else, 2drop then, ;
: cc-bf-truncate ( rec -- )
  dup cc-sf-bit-width [lit] 64 swap - [lit] 231 cc-bf-shift-rdi
  dup cc-sf-bit-width [lit] 64 swap -
  swap cc-sf-type ty-unsigned? if, [lit] 239 else, [lit] 255 then, cc-bf-shift-rdi ;
: cc-bf-load ( ty rec -- )
  dup cc-bf? 0= if, cc-field-load-default exit, then,
  swap cc-emit-load-typed-via-rdi
  dup cc-sf-bit-shift [lit] 239 cc-bf-shift-rdi
  cc-bf-truncate ;
' cc-bf-load is cc-field-load-fwd

```

Truncation shifts left by 64 minus the width, placing the field's sign bit at the top of RDI. Shifting back logically produces an unsigned value; shifting back arithmetically extends a signed field's sign. A full-width field needs neither shift.

## Replace bits without replacing neighbours

`cc-bf-store` retains the truncated assignment result in RDI and builds the positioned payload in R8 using `cc-bf-shift-r8`. `cc-bf-mask` supplies the low-width mask, with an all-bits-set case for width 64 (`forth-bootstrap/cc/129-cc-bitfield.fth:112`):
```forth file=cc/129-cc-bitfield.fth
: cc-bf-mask ( width -- mask )
  dup [lit] 64 = if, drop true else, [lit] 1 swap cc-shl 1- then, ;
: cc-bf-shift-r8 ( count opcode -- )
  over if,
    [lit] 73 cc-emit-byte [lit] 193 cc-emit-byte cc-emit-byte cc-emit-byte
  else, 2drop then, ;
: cc-bf-store ( ty rec -- )
  dup cc-bf? 0= if, cc-field-store-default exit, then,
  nip dup cc-bf-truncate
  [lit] 73 cc-emit-byte [lit] 137 cc-emit-byte [lit] 248 cc-emit-byte \ mov r8,rdi
  dup cc-sf-bit-width [lit] 64 swap - [lit] 224 cc-bf-shift-r8
  dup cc-sf-bit-width [lit] 64 swap - [lit] 232 cc-bf-shift-r8
  dup cc-sf-bit-shift [lit] 224 cc-bf-shift-r8
  dup cc-sf-type ty-size [lit] 8 = if, [lit] 72 cc-emit-byte then,
  dup cc-sf-type ty-size [lit] 1 = if,
    [lit] 15 cc-emit-byte [lit] 182 cc-emit-byte [lit] 1 cc-emit-byte \ movzx eax,byte [rcx]
  else, [lit] 139 cc-emit-byte [lit] 1 cc-emit-byte then, \ mov eax/rax,[rcx]
  [lit] 73 cc-emit-byte [lit] 185 cc-emit-byte \ movabs r9,preserving mask
  dup cc-sf-bit-width cc-bf-mask over cc-sf-bit-shift cc-shl dup nand cc-emit-8le
  [lit] 76 cc-emit-byte [lit] 33 cc-emit-byte [lit] 200 cc-emit-byte \ and rax,r9
  [lit] 76 cc-emit-byte [lit] 9 cc-emit-byte [lit] 192 cc-emit-byte  \ or rax,r8
  cc-sf-type ty-size
  dup [lit] 8 = if, [lit] 72 cc-emit-byte then,
  [lit] 1 = if, [lit] 136 else, [lit] 137 then,
  cc-emit-byte [lit] 1 cc-emit-byte ; \ mov [rcx],al/eax/rax
' cc-bf-store is cc-field-store-fwd

```

With address in RCX, the emitted operation is `new_unit = (old_unit & ~positioned_mask) | positioned_value`. R8's logical truncation removes any sign extension before positioning; R9 holds the complement mask. The final write uses the declared unit size, including a byte write for `_Bool`.

This is a read-modify-write sequence, not an atomic operation. Volatile fields use the same ordinary unit accesses; a compound update can load its operand and then load the unit again for the preserving store. No inter-thread synchronization is provided.

## Choose the expression type

Storage width also constrains promotion: `cc-bf-value-type` maps fields narrower than 32 bits to int, maps width 32 to int or unsigned int according to signedness, and leaves full-width types intact. `cc-bf-use` rejects a bitfield when the caller requires an ordinary object (`forth-bootstrap/cc/129-cc-bitfield.fth:139`):
```forth file=cc/129-cc-bitfield.fth
: cc-bf-value-type ( ty rec -- promoted-ty )
  dup cc-bf? if,
    cc-sf-bit-width dup [lit] 32 < if,
      drop drop ty-int [lit] 0 ty-make
    else,
      [lit] 32 = if,
        ty-unsigned? if, ty-uint else, ty-int then, [lit] 0 ty-make
      then,
    then,
  else, drop then, ;
' cc-bf-value-type is cc-field-value-type-fwd
: cc-bf-use ( rec -- )
  cc-bf? if, cc-bf-die then, ;
' cc-bf-use is cc-field-use-fwd

```

A narrow unsigned field therefore promotes to signed int: its entire range fits.

## Initialize the same slice

Static initialization merges a constant into object data instead of emitting a store instruction. `cc-bf-init-record` retains the member and `cc-bf-init-offset` its output position; `cc-bf-static-initializer` rejects relocatable values and uses typed constant conversion (Chapter 45) for floating inputs or a `_Bool` destination (`forth-bootstrap/cc/129-cc-bitfield.fth:158`):
```forth file=cc/129-cc-bitfield.fth
\ Initializer records contain only named members; unnamed and zero-width
\ declarations affect layout but consume no initializer element.
variable cc-bf-init-record
variable cc-bf-init-offset
: cc-bf-static-initializer ( rec -- )
  cc-bf-init-record !
  cc-putback-token cc-parse-static-const-fwd
  if, cc-bf-die then, drop
  dup cc-const-float? cc-bf-init-record @ cc-sf-type cc-const-bool? or if,
    cc-bf-init-record @ cc-sf-type cc-const-change
  else, drop then,
  cc-bf-init-record @ cc-sf-bit-width cc-bf-mask and
  cc-bf-init-record @ cc-sf-bit-shift cc-shl
  nc-slot @ om-offset @ ni-offset @ + cc-bf-init-record @ cc-sf-offset + cc-bf-init-offset !
  cc-obj-data cc-obj-base cc-bf-init-offset @ + @
  cc-bf-init-record @ cc-sf-bit-width cc-bf-mask
  cc-bf-init-record @ cc-sf-bit-shift cc-shl dup nand and or
  cc-obj-data cc-bf-init-offset @ cc-bf-init-record @ cc-sf-type ty-size cc-obj-patch ;

```

`cc-obj-patch` writes the unit's byte count after merging, preserving initialized neighbours.

Automatic initialization takes the other branch of `cc-bf-initializer`: compute the member address, parse and convert the expression, then invoke the preserving store. The wrapper returns false for an ordinary member and accepts optional braces around a bitfield value (`forth-bootstrap/cc/129-cc-bitfield.fth:173`):
```forth file=cc/129-cc-bitfield.fth
: cc-bf-initializer ( rec -- handled? )
  dup cc-bf? 0= if, drop [lit] 0 exit, then,
  >r
  [char] { cc-tok-punct? dup >r if, cc-next-token-keep then,
  r> r> swap >r >r
  cc-sysv-object-mode @ cc-ni-static @ and if,
    r> cc-bf-static-initializer
  else,
    r@ cc-sf-offset ni-offset @ + cc-ni-address cc-emit-push-rdi
    cc-putback-token cc-parse-assign cc-emit-materialize
    cc-last-expr-type @ r@ cc-sf-type cc-value-init-fwd
    cc-emit-pop-rcx r@ cc-sf-type r> cc-field-store-fwd
  then,
  cc-next-token-keep
  r> if,
    [char] , cc-tok-punct? if, cc-next-token-keep then,
    [char] } cc-tok-punct? 0= if, [lit] 227 cc-die then,
    cc-next-token-keep
  then,
  true ;
' cc-bf-initializer is cc-ni-field-fwd
```

## Try it

Run from the `forth-bootstrap` checkout root with the seed already built. The block compiles through `cc/129-cc-bitfield.fth` and uses the Forth linker with a small `_start`. Each probe returns its value through the process status; the shell decodes the signed result.

The fields share an int unit without crossing its boundary. Each probe checks both initializer paths, then changes `low` and checks its neighbours.

<!-- tryit: expect "low = 2\ndelta = -3\nhigh = 9\nsizeof(struct Flags) = 4" -->
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
for probe in 0 1 2 3; do
printf '#define PROBE %s\n' "$probe" > "$work/probe.c"
cat >> "$work/probe.c" <<'C' || exit "$?"
struct Flags { unsigned low : 3; signed delta : 5; unsigned high : 4; };
static struct Flags initial = {5, -3, 9};
int main(void) {
    struct Flags flags = {5, -3, 9};
    if (initial.low != 5 || initial.delta != -3 || initial.high != 9) return 100;
    if (flags.low != 5 || flags.delta != -3 || flags.high != 9) return 101;
    flags.low = 2;
    if (flags.low != 2 || flags.delta != -3 || flags.delta >= 0 || flags.high != 9)
        return 102;
    if (PROBE == 0) return flags.low;
    if (PROBE == 1) return flags.delta;
    if (PROBE == 2) return flags.high;
    return sizeof(struct Flags);
}
C
{
  cat forth/010-lib.fth cc/0[2-9]*-cc-*.fth cc/1[01]*-cc-*.fth \
      cc/121-cc-sysv.fth cc/123-cc-object-program.fth \
      cc/124-cc-target.fth cc/125-cc-consteval.fth cc/126-cc-varargs.fth \
      cc/127-cc-binary64.fth cc/128-cc-float-literal.fth cc/129-cc-bitfield.fth || exit "$?"
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
  for name in start.o probe.o result; do printf 'create p-%s s, %s/%s [lit] 0 c,\n' "$name" "$work" "$name"; done
  printf '%s\n' 'create entry-name s, _start' \
    'lnk-init p-start.o lnk-add-object p-probe.o lnk-add-object entry-name [lit] 6 lnk-entry p-result lnk-link lnk-release bye'
} | ./seed-forth || exit "$?"
result=0
"$work/result" || result=$?
case "$probe" in
  0) label=low; expected=2 ;;
  1) label=delta; expected=-3; result=$((result >= 128 ? result - 256 : result)) ;;
  2) label=high; expected=9 ;;
  3) label='sizeof(struct Flags)'; expected=4 ;;
esac
printf '%s = %s\n' "$label" "$result"
test "$result" -eq "$expected" || exit 1
done
)
# prints "low = 2\ndelta = -3\nhigh = 9\nsizeof(struct Flags) = 4"
```

Observed output:
```text
low = 2
delta = -3
high = 9
sizeof(struct Flags) = 4
```

## Exercise

Hints and feedback are in [Appendix H](66-exercise-feedback.md#chapter-48-preserve-neighboring-fields).

**Trace (easy).** Follow `cc-bf-add` for the checkpoint's members. Derive each shift, the containing byte offset, and the final aligned size. Then explain why changing `low` cannot erase `delta`'s sign bit.

**Verify (moderate).** After the existing initialization and `flags.low = 2` guards, but before the `PROBE` returns, store `-4` into `flags.delta`. This value fits the signed five-bit field. Add a check that `low` is still 2, `delta` is now −4, and `high` is still 9. Change the shell's expected delta value to −4 and rerun all four probes; the raw status 252 is decoded by the wrapper to −4. Keep the earlier guards unchanged so they still check the original initialization and low-field store.


Repeat independently with a different representable negative value. Predict the unit bits and the returned status before running it, then check that both neighboring fields are still unchanged.
