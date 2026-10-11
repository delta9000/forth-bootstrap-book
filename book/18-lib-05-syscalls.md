# Chapter 18 — Linux syscall wrappers

`open`, `read`, `write`, `close`, and `die` give Linux operations names
and argument lists a Forth caller can use directly. Calling them through
the generic bridge still requires unused argument slots and a syscall
number; each wrapper supplies those details. The returning wrappers leave
the kernel's result directly on the caller's stack.

## A sidebar on the syscall ABI

Recall Chapter 4's Linux syscall register convention and Chapter 8's
`syscall6` operand order, padding, and raw result; the contract is collected
in [Chapter 13](13-primitive-reference.md#the-table).
The wrapper skeleton is **caller arguments → padding → syscall number →
`syscall6`**. Call this the *pad-and-call* pattern. The wrapper fixes the
operation while preserving the caller's argument order.

## `open`: a path, flags, and mode

Push `path flags mode`, in the order of the C arguments. `path` points to
a NUL-terminated pathname; `flags` selects the operation, and `mode`
supplies permissions when creating a file. Even when creation is not
requested, the caller must supply the mode slot.

The library's syscall header and first wrapper in
`forth-bootstrap/forth/010-lib.fth:47` show where the caller's operands
end and the pad-and-call pattern begins:

```forth file=forth/010-lib.fth
\ ===== Linux syscall wrappers (via syscall6 primitive) =====
\ syscall6 ( a b c d e f n -- rax )  loads a..f into rdi/rsi/rdx/r10/r8/r9
\ and n into rax.  We pad with zeros for unused argument slots.
\
\ Linux x86-64 syscall numbers:
\   read=0  write=1  open=2  close=3  exit=60  brk=12  mmap=9

\ open  ( path flags mode -- fd )    SYS_open=2
: open   [lit] 0 [lit] 0 [lit] 0 [lit]  2 syscall6 ;

```

`open` leaves its three inputs in place, appends three padding zeros,
and selects syscall number `2`. Trace the boundary without expanding the
register bridge:

| Point | Stack |
|---|---|
| wrapper entry | `path flags mode` |
| padding appended | `path flags mode 0 0 0` |
| number appended | `path flags mode 0 0 0 2` |
| call returns | `fd-or-error` |

The zeros belong after `mode`. Putting them before `path` would change
which values the kernel receives as the real arguments. Omitting them
would let the bridge consume unrelated stack values.

The source comment names the successful result `fd`. An error is a raw
negative result in that same slot. Unlike a C library interface, this
wrapper does not replace it with a common failure sentinel or store an
error number elsewhere. The caller must distinguish an error from a
usable descriptor before passing the result to another wrapper.

## `read` and `write`: a symmetric pair

A buffer transfer needs a descriptor, an address, and a requested byte
count. Direction is the only difference in the pad-and-call bodies in
`forth-bootstrap/forth/010-lib.fth:57`:

```forth file=forth/010-lib.fth
\ read  ( fd buf count -- n )        SYS_read=0
: read   [lit] 0 [lit] 0 [lit] 0 [lit]  0 syscall6 ;

\ write ( fd buf count -- n )        SYS_write=1
: write  [lit] 0 [lit] 0 [lit] 0 [lit]  1 syscall6 ;

```

Both callers push `fd buf count`. `read` fills the buffer; `write`
copies bytes from it. Each appends three padding zeros. The final
literal selects `read` with `0` or `write` with `1`.

On success, `n` is the number of bytes actually transferred. It can be
smaller than `count`; a read returning zero indicates end of input when
a nonempty read was requested. Neither wrapper retries a short transfer.
A negative result reports an error, so it must not be reused as a buffer
length. Buffered I/O belongs to Chapter 27.

## `close` and `die`: one real argument

A descriptor close and a process exit each take a single input.
The one-argument form of pad-and-call in
`forth-bootstrap/forth/010-lib.fth:63` fills the remaining slots the
same way for both operations:

```forth file=forth/010-lib.fth
\ close ( fd -- err )                SYS_close=3
\ Pads 5 zero args + syscall #.
: close  [lit] 0 [lit] 0 [lit] 0 [lit] 0 [lit] 0 [lit]  3 syscall6 ;

\ die ( n -- )  Exit with status n via SYS_exit=60.
\ Used by the C compiler's error paths instead of inlining the full syscall.
: die  [lit] 0 [lit] 0 [lit] 0 [lit] 0 [lit] 0 [lit] 60 syscall6 ;

```

### `close`: release a descriptor

For `close`, pad-and-call appends five zeros and syscall number `3`.
The caller supplies `fd` alone and receives `err`: zero on success,
or a raw negative error. Closing a descriptor does not end the Forth
process; execution continues with that result on the stack.

### `die`: exit unconditionally

`die` uses the same five-zero padding as `close`, followed by syscall
number `60`. Its argument is an exit status, not a condition to test.
Calling it ends execution unconditionally, even when the status is zero.
There is no result for the next Forth word to consume, and no following
word runs. A caller that wants to report an error must do so before
calling `die`.

## Try it

Run this from the `forth-bootstrap` checkout at `./forth-bootstrap`,
using the seed built in Part 1. `head -n 70` loads the library header
and definitions through `die`, stopping before character classification.
The command writes to stdout and creates no files.

`c,` (Chapter 15) builds the payload at `here`.
The first input line writes `OK` and a newline to stdout, descriptor `1`,
then prints the returned byte count, `3`. The next lines exercise errors:
`open` receives an empty pathname and returns `-2`; `read` and `close`
receive the invalid descriptor `-1` and return `-9`. Adding each error's
magnitude and testing for zero prints `0` for a match or `1` for a
mismatch. Subtraction (Chapter 17) builds that invalid descriptor
without a signed literal.

<!-- tryit: expect "OK\n3\n000\nexit status: 0" -->
```sh
{ head -n 70 forth/010-lib.fth
  printf '%s\n' \
    '[lit] 1 here [lit] 79 c, [lit] 75 c, [lit] 10 c, [lit] 3 write [lit] 48 + emit [lit] 10 emit' \
    'here [lit] 0 c, [lit] 0 [lit] 0 open [lit] 2 + 0= [lit] 49 + emit' \
    '[lit] 0 [lit] 1 - here [lit] 1 read [lit] 9 + 0= [lit] 49 + emit' \
    '[lit] 0 [lit] 1 - close [lit] 9 + 0= [lit] 49 + emit [lit] 10 emit' \
    '[lit] 0 die [lit] 88 emit'
} | ./seed-forth
# prints "OK\n3\n000"
printf 'exit status: %s\n' "$?"
# prints "exit status: 0"
```

Observed output:

```text
OK
3
000
exit status: 0
```

The final input line calls `die` with status zero. The following `emit`
would print `X`; its absence checks that execution stopped.

## Exercise

**Trace (easy).** Start with `saved fd` and trace `close` through its
padding and syscall number. Show the stack just before `syscall6` and
just after it returns. Which value survives beneath the result? Explain
what would go wrong if the wrapper omitted a padding zero.
