# Chapter 8 — The seed’s Linux boundary

When `hello` from Chapter 1 reaches its first `emit`, `rdi` holds 72,
the byte for `H`. Linux needs that same register to hold 1, the descriptor
for standard output. Simply assigning the descriptor would lose the
character. The boundary word must first put the byte somewhere Linux
can read it, then arrange the call, then recover the Forth stack.

## The Linux register boundary

A **system call**, or **syscall**, asks the Linux kernel to perform an
operation such as writing bytes or ending the process. The processor's
`syscall` instruction enters the kernel; this is a different boundary
from calling a Forth word and returning with `ret`.

A **file descriptor** is a small integer identifying one of a process's
open I/O channels. The standard descriptors are 0 for input (**stdin**),
1 for output (**stdout**), and 2 for error output (**stderr**). A shell
pipe connects the seed's stdin to the program on its left; stdin need
not be a keyboard, and stdout need not be a screen.

The Linux syscall register convention temporarily gives registers a different job. The syscall number goes in `rax` and arguments go, in order, in `rdi`, `rsi`, `rdx`, `r10`, `r8`, and `r9`. The result comes back in `rax`; `syscall` clobbers `rcx` and `r11`. The argument register after `rdx` is `r10`, not the C function-call convention's `rcx`.

Follow each word through its preparation, kernel request, and final effect:

| Word | Prepare | Ask Linux | Finish |
|---|---|---|---|
| `bye` | Select a successful exit | Terminate | Does not return |
| `emit` | Copy the character into scratch storage | Write the byte | Consume the character |
| `key` | Preserve the previous top | Read into scratch storage | Supply the byte or an end-of-input marker |
| `syscall6` | Transfer the caller’s operands to registers | Perform the selected call | Replace the operands with its result |

The listings retain their dictionary headers so the source can be reconstructed. Chapter 9 explains those headers; follow the instructions after each `_code` comment here.

## `bye`: leave the process

Termination needs no stack recovery, so `bye` provides the smallest complete boundary crossing in `forth-bootstrap/seed/000-seed.hex0:251`.

```hex0 chunk=bye
;; --- bye @ 0x22D --- header
12 02 40 00 00 00 00 00                   ; link  = 0x400212 (*)
00                                        ; flags = 0
03                                        ; nlen  = 3
62 79 65                                  ; name  = "bye"
;; ----- bye_code @ 0x23A  ( -- ) exit(0); never returns -----
B8 3C 00 00 00                            ; mov eax, 60        ; SYS_exit
BF 00 00 00 00                            ; mov edi, 0         ; status 0
0F 05                                     ; syscall

```

The constants select syscall `60`, `exit`, with status `0`. The incoming Forth top is overwritten without being saved. There is no `ret`: successful termination leaves no Forth caller to resume. Unlike a C function returning to its caller, `bye` ends the process regardless of what remains on either Forth stack.

## `emit`: consume a character

Linux’s write operation needs a buffer address, so `emit` first copies the character out of `rdi` in `forth-bootstrap/seed/000-seed.hex0:261`.

```hex0 chunk=emit
;; --- emit @ 0x246 --- header
2D 02 40 00 00 00 00 00                   ; link  = 0x40022D (bye)
00                                        ; flags = 0
04                                        ; nlen  = 4
65 6D 69 74                               ; name  = "emit"
;; ----- emit_code @ 0x254  ( c -- ) write one byte to stdout -----
48 C7 C0 00 20 41 00                      ; mov rax, 0x412000  ; scratch byte
40 88 38                                  ; mov [rax], dil     ; store TOS's low byte there
B8 01 00 00 00                            ; mov eax, 1         ; SYS_write
BF 01 00 00 00                            ; mov edi, 1         ; fd 1 (stdout)
48 BE 00 20 41 00 00 00 00 00             ; mov rsi, 0x412000  ; buf (movabs)
BA 01 00 00 00                            ; mov edx, 1         ; count 1
0F 05                                     ; syscall            ; clobbers rcx, r11
48 8B 7D 00                               ; mov rdi, [rbp]
48 83 C5 08                               ; add rbp, 8
C3                                        ; ret

```

The I/O scratch byte is at `0x412000` (Chapter 5). `mov [rax], dil` puts the character there before `mov edi, 1` replaces `rdi`'s contents with stdout’s file descriptor. Only the low byte is written; the rest of the Forth cell does not reach the output stream.

The syscall requests `write(1, scratch, 1)`: stdout, the scratch address, and a single byte. After it returns, the tail uses the `drop` pattern from Chapter 6 to consume the character. The kernel’s result in `rax` is discarded, so `emit` supplies neither a byte count nor an error indication to its caller.

Call this **prepare–call–recover**: prepare the kernel’s operands, make the call, then recover the Forth stack in the shape promised by the word. Recovery does not necessarily mean restoring the old top. For `emit`, it means exposing the value underneath the consumed character.

## `key`: preserve the old top and add input

Input must leave earlier stack values intact, so `key` saves the old top before borrowing `rdi` for stdin in `forth-bootstrap/seed/000-seed.hex0:278`.

```hex0 chunk=key
;; --- key @ 0x282 --- header
46 02 40 00 00 00 00 00                   ; link  = 0x400246 (emit)
00                                        ; flags = 0
03                                        ; nlen  = 3
6B 65 79                                  ; name  = "key"
;; ----- key_code @ 0x28F  ( -- c ) read one byte from stdin; 0 at EOF -----
48 83 ED 08                               ; sub rbp, 8
48 89 7D 00                               ; mov [rbp], rdi
B8 00 00 00 00                            ; mov eax, 0         ; SYS_read
BF 00 00 00 00                            ; mov edi, 0         ; fd 0 (stdin)
48 C7 C6 00 20 41 00                      ; mov rsi, 0x412000  ; buf = scratch byte
BA 01 00 00 00                            ; mov edx, 1         ; count 1
0F 05                                     ; syscall
48 85 C0                                  ; test rax, rax      ; 0 bytes read = EOF
74 06                                     ; jz .eof  (rel8 = 0x2BA - 0x2B4)
48 0F B6 3E                               ; movzx rdi, byte [rsi] ; TOS = the byte
EB 03                                     ; jmp .done  (rel8 = 0x2BD - 0x2BA)
;; .eof:
48 31 FF                                  ; xor rdi, rdi       ; TOS = 0
;; .done:
C3                                        ; ret

```

Unlike `emit`, this word produces a value without consuming a caller operand. Its opening prepares `read(0, scratch, 1)`.

**End of file**, or **EOF**, means that the input has ended. It is not
an extra byte sent after the last character. For this one-byte request,
Linux reports EOF by returning a byte count of zero; `key` must choose a
Forth value to represent that condition.

After the call, `test rax, rax` distinguishes EOF from a nonzero return. A zero result takes `.eof`, where `xor rdi, rdi` supplies the sentinel `0`. Otherwise, the byte at the buffer address becomes the new top through `movzx`, just as in `c@` from Chapter 6. Neither path needs to change `rsp`; the final `ret` uses the waiting return address.

This is prepare–call–recover with a new top rather than a consumed one. The recovery has a limitation: an input NUL (byte zero) and EOF both produce `0`. There is also no separate error branch. A negative read result takes the buffer-load path and can expose the scratch byte’s previous contents. The primitive is a minimal byte interface, not a checked read operation.

Chapter 9 follows the token reader’s use of `key`; Chapter 12 follows the REPL’s decision to stop.

## `syscall6`: let the caller choose

The fixed I/O words choose their own operands; `syscall6` instead transfers the caller’s stack operands into kernel registers in `forth-bootstrap/seed/000-seed.hex0:300`.

```hex0 chunk=syscall6
;; --- syscall6 @ 0x2BE --- header
82 02 40 00 00 00 00 00                   ; link  = 0x400282 (key)
00                                        ; flags = 0
08                                        ; nlen  = 8
73 79 73 63 61 6C 6C 36                   ; name  = "syscall6"
;; ----- syscall6_code @ 0x2D0  ( a b c d e f n -- rax ) -----
;; Linux x86-64: rax=n, rdi=a, rsi=b, rdx=c, r10=d, r8=e, r9=f.
;; Pops the six arguments; the new TOS is the syscall's return value.
48 89 F8                                  ; mov rax, rdi       ; rax = n (syscall number)
4C 8B 4D 00                               ; mov r9, [rbp]      ; f
4C 8B 45 08                               ; mov r8, [rbp+8]    ; e
4C 8B 55 10                               ; mov r10, [rbp+16]  ; d
48 8B 55 18                               ; mov rdx, [rbp+24]  ; c
48 8B 75 20                               ; mov rsi, [rbp+32]  ; b
48 8B 7D 28                               ; mov rdi, [rbp+40]  ; a
0F 05                                     ; syscall            ; clobbers rcx, r11 (unused)
48 83 C5 30                               ; add rbp, 48        ; pop the 6 argument cells
48 89 C7                                  ; mov rdi, rax       ; TOS = result
C3                                        ; ret

```

At entry, the syscall number `n` occupies `rdi`. Saving it in `rax` must precede loading argument `a` into `rdi`. The other arguments are read directly from their stack slots:

| Forth operand | Entry location | Kernel destination |
|---|---|---|
| `n` | `rdi` | `rax` |
| `f` | `[rbp]` | `r9` |
| `e` | `[rbp+8]` | `r8` |
| `d` | `[rbp+16]` | `r10` |
| `c` | `[rbp+24]` | `rdx` |
| `b` | `[rbp+32]` | `rsi` |
| `a` | `[rbp+40]` | `rdi` |

The deepest argument is loaded last. These loads leave the memory slots untouched, and `rbp` remains available throughout the call. The syscall’s clobbers, listed above, do not destroy any state this primitive needs for recovery.

On return, `add rbp, 48` releases the six argument cells. Moving `rax` into `rdi` replaces the syscall number with the kernel’s result. This is prepare–call–recover again, but the result is passed through without interpretation. Every call supplies all six argument cells because the primitive loads and removes them unconditionally. Supply zero in unused positions.

Chapter 18 builds readable Linux syscall wrappers on this bridge. Here the distinction is already useful: `emit` hides the write result, while `syscall6` lets the caller inspect it. If the selected operation terminates the process, the recovery instructions are never reached.

## Try it

Run the checkpoint from the `forth-bootstrap` checkout (`cd forth-bootstrap` from the book repository). `./seed/build.sh` builds the complete seed. We use its existing command reader as a tool; Chapter 9 explains token reading and Chapter 12 explains the REPL.

This works because the reader stops at the space after `key`, so `key` itself reads the very next byte of input, which is the character typed straight after it. The first input stream gives `key` an `A`, emits it, then reads and emits a newline before `bye`. The second uses `[lit]`, the interface introduced in Chapter 1, to supply `( 42 0 0 0 0 0 60 )` explicitly: status 42, five unused zero arguments, then syscall number 60. Its implementation comes in Chapter 10. Keeping the operands visible lets us check the six-argument contract without encoding numbers as input characters.

```sh
./seed/build.sh
printf 'key Aemit key \nemit bye\n' | ./seed-forth
# prints "A"
status=0
printf '%s\n' '[lit] 42 [lit] 0 [lit] 0 [lit] 0 [lit] 0 [lit] 0 [lit] 60 syscall6' | ./seed-forth || status=$?
printf 'syscall6 exit status: %s\n' "$status"
# prints "syscall6 exit status: 42"
```

Observed output:

```text
Built seed-forth (1772 bytes) using vendor/stage0-posix/bootstrap-seeds/POSIX/AMD64/hex0-seed
A
syscall6 exit status: 42
```

## Exercise

**Trace (easy).** Follow `syscall6` with an older value below `a`. Mark where `n` is saved, which instruction releases the argument cells, and where the older value sits when the result becomes the cached top. Then explain what would break if the first `mov rax, rdi` were moved after the load of `a`.

<details>
<summary>Check the six-argument trace</summary>

Write the incoming stack as `older a b c d e f n`, top at the right,
and name the initial `rbp` value `p`. `n` is cached in `rdi`; memory
holds `f` at `[p]`, through `a` at `[p+40]`, then `older` at `[p+48]`.
The first `mov rax, rdi` saves `n` before `rdi` is reused for `a`.
On a returning syscall, `add rbp, 48` advances to the older value's
slot. `mov rdi, rax` caches the result, leaving `older` at the new
`[rbp]`, beneath it. No reload or extra pop is needed.

Moving the first instruction after the load of `a` would instead put
`a` in `rax`: Linux would receive the first argument as the syscall
number. This is a paper trace, not a safe mutation to try with arbitrary
system-call operands. The checkpoint's exit syscall never returns, so
it does not exercise the recovery tail.

</details>
