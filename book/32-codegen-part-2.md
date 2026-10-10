# Chapter 32 — Calls, shims, and globals

A program can print `**` by calling a `putchar` shim whose location is still unknown when the calls are emitted. A fixup list preserves those call sites until the target exists; the same separation between emitting bytes and resolving addresses supports strings and globals. The checkpoint builds and runs that program directly from emitter words.

## `movabs rdi, imm64` and the forward-call fixup list

The emitter has this shape: write an instruction with a placeholder → remember its output offset → patch it when the target is known. Call displacements use the existing patch operation (Chapter 31); absolute addresses need a full-width immediate field.

`cc-emit-movabs-rdi-imm64` loads an address without a signed-immediate range check by writing the full value after `48 BF`. The opcode arithmetic is `B8 + 7 = BF`; the source comment's `B7` is a typo, while emitted decimal 191 is correct (`forth-bootstrap/cc/090-cc-emit.fth:451`):

```forth file=cc/090-cc-emit.fth
\ ===========================================================================
\ movabs rdi, imm64 — used for loading string-literal addresses.
\ ===========================================================================
\ Encoding: 48 BF <imm64-LE>  (10 bytes total).

: cc-emit-movabs-rdi-imm64                        ( v -- )
  [lit]  72 cc-emit-byte                          \ REX.W
  [lit] 191 cc-emit-byte                          \ B7 + rdi (7) = BF
  cc-emit-8le ;

```

Integer literals benefit from the compact form when it is safe. `cc-emit-mov-rdi-int` assumes the legacy literal domain in its default branch; it does not correctly classify every possible 64-bit input pattern. Its LP64 path uses unsigned division to select the wide form at or above `2^31`, so a set high bit cannot masquerade as a small magnitude (`forth-bootstrap/cc/090-cc-emit.fth:464`):

```forth file=cc/090-cc-emit.fth
\ cc-emit-mov-rdi-int ( v -- )  Load an integer literal into rdi using the
\ shortest correct encoding.  `mov rdi, imm32` (7 bytes) sign-extends its
\ 32-bit field, so it only represents values in signed-32 range; a wider
\ constant (e.g. 0x80000000 or 2^32) would be sign-extended or truncated.
\ For those, fall back to the 10-byte `movabs rdi, imm64`.  C literals are
\ always non-negative here (a leading `-` is unary minus, applied later), so
\ only the upper bound needs checking — which keeps every in-range constant
\ on the exact imm32 bytes it emitted before.
: cc-emit-mov-rdi-int                             ( v -- )
  cc-target-lp64 @ if,
    \ Unsigned magnitude also catches literals with bit 63 set.
    dup [lit] 2147483648 / if,
      cc-emit-movabs-rdi-imm64
    else, cc-emit-mov-rdi-imm32 then,
    exit,
  then,
  dup [lit] 2147483647 > if,
    cc-emit-movabs-rdi-imm64
  else,
    cc-emit-mov-rdi-imm32
  then, ;

```

For the helper-level input `0x8000000100000000`, the distinction is concrete.
The table derives the encoding by hand. Compiled, `0x8000000100000000 != 0`
returns 0, confirming the value loss, while `2147483648 > 0` returns 1.
Arbitrary 64-bit literals are therefore not part of the core contract:

| Branch | Width decision | Emitted value |
|---|---|---|
| Default/core | `>` inspects the sign of wrapping `0x7fffffff - v = 0x7fffffff7fffffff`, so it returns false | Seven-byte immediate form writes the low 32 bits, zero, and loads zero |
| LP64 | Unsigned `v / 2147483648` is nonzero | Ten-byte `movabs` retains all 64 bits |

Thus “shortest correct encoding” in the copied comment is too broad for
arbitrary inputs to the default helper. The small literal checkpoint still
passes. Keep this restricted default path distinct from the LP64 selector;
[Appendix F](60-c-subset.md#observed-profile-boundaries) scopes the probes.

Taking an undefined function’s address needs `cc-emit-movabs-rdi-imm64-placeholder`: the same instruction shape with an empty immediate. The returned offset identifies the value field to overwrite, not the instruction’s beginning (`forth-bootstrap/cc/090-cc-emit.fth:485`):

```forth file=cc/090-cc-emit.fth
\ cc-emit-movabs-rdi-imm64-placeholder ( -- patch-offset )
\ Emits `48 BF 00 00 00 00 00 00 00 00`; returns the imm64 file-offset.
\ Used when a forward-declared function's name is taken as an rvalue
\ (function-pointer load) before its definition is reached.  Caller threads
\ patch-offset onto the prototype symbol's cc-sym-addr-fixups list; the
\ list is walked and each 8-byte imm64 is patched to the function's real
\ vaddr when cc-parse-function processes its definition.
: cc-emit-movabs-rdi-imm64-placeholder
  [lit]  72 cc-emit-byte
  [lit] 191 cc-emit-byte
  cc-out-pos @
  [lit] 0 cc-emit-8le ;

```

Several references to a target need several remembered sites. `cc-add-fixup-to-list` allocates a node containing the patch offset followed by the old head, then installs the node as the new head (`forth-bootstrap/cc/090-cc-emit.fth:495`):

```forth file=cc/090-cc-emit.fth
\ cc-add-fixup-to-list ( fixup-offset list-var -- )  Allocate a 16-byte node
\ and prepend it to the linked list rooted at list-var.  Defined here so
\ 100-cc-expr.fth (loaded before 112-cc-stmt.fth) can reference it from the
\ forward-function-rvalue path in cc-parse-primary.
: cc-add-fixup-to-list                            ( off var -- )
  [lit] 16 cc-alloc                               ( off var node )
  >r                                              ( off var ; R: node )
  swap r@ !                                       ( var ; R: node )
  dup @ r@ [lit] 8 + !                            ( var ; R: node )
  r> swap ! ;                                     ( -- )

```

The caller passes the address of the list head. After a prepend, following the new node’s link reaches every earlier site. Call lists and function-address lists use the same node shape, but their eventual patches differ: a displacement for a call, an absolute address for a function pointer. Chapter 37 connects both lists to function definitions; Chapter 36 reuses the list operation for pending statement jumps.

## String-literal bytes with C-escape decoding

A string token carries a source slice, so emitting it must consume source characters as well as produce output bytes. `cc-emit-string-bytes` delegates escape interpretation to `cc-decode-escape` (Chapter 29), then advances by the decoder’s consumed length plus the backslash (`forth-bootstrap/cc/090-cc-emit.fth:511`):

```forth file=cc/090-cc-emit.fth
\ ===========================================================================
\ String-literal byte emission with C-escape decoding.
\ ===========================================================================
\ Walks ( src-addr src-len ) and copies bytes into cc-out-buf, decoding each
\ escape with cc-decode-escape (050), the same table character literals
\ use.  Appends a trailing NUL byte.
\
\ Stack convention inside the loop: ( src len ).

: cc-emit-string-bytes                            ( src-addr src-len -- )
  begin,
    dup [lit] 0 >
  while,
    over c@ backslash = if,
      dup [lit] 2 >= if,
        \ Have at least one more byte for the escape.
        over 1+ cc-decode-escape                  ( src len byte n )
        swap cc-emit-byte 1+                      ( src len k )
        \ Advance src by k (the backslash and the escape), len by -k.
        >r swap r@ + swap r> -
```

Ordinary characters and a lone trailing backslash take the literal-copy path; after the slice is exhausted, a NUL terminator makes the emitted bytes usable as a C string (`forth-bootstrap/cc/090-cc-emit.fth:522`):

```forth file=cc/090-cc-emit.fth
      else,
        \ Trailing backslash with no follow-up char: emit literally.
        over c@ cc-emit-byte
        swap 1+ swap 1-
      then,
    else,
      over c@ cc-emit-byte
      swap 1+ swap 1-
    then,
  repeat,
  drop drop
  [lit] 0 cc-emit-byte ;                          \ trailing NUL terminator

```

The source cursor and remaining length move together. An escape can consume more source bytes than it emits, so advancing by a fixed pair would be wrong. This word emits data only: Chapter 34 supplies the surrounding expression code that keeps execution out of the bytes and loads their address.

## The libc shims: write/read/open/close/mmap

A shim is executable code emitted into the output buffer. These shims accept arguments in the registers named by their comments and return through `rax`; they do not use the Forth data stack. Chapter 37 owns their registration and placement, and Chapter 41 develops the later System V call machinery.

A pushed argument can double as a temporary byte buffer. The `putchar` layout uses that stack-buffer pattern to give `write` an address (`forth-bootstrap/cc/090-cc-emit.fth:535`):

```forth file=cc/090-cc-emit.fth
\ ===========================================================================
\ Built-in libc shims (putchar, exit, getchar) emitted at the start of
\ the code segment so user code can call them via the standard call path.
\ ===========================================================================
\
\ All three shims follow SYS-V x86-64 calling convention: the first arg is in
\ rdi, the return value comes back in rax, and the call site converts rax to
\ rdi via cc-emit-mov-rdi-rax (already done by cc-parse-call).
\
\ NOTE on stack: each shim is entered with rsp ≡ 8 mod 16 (caller pushed the
\ return address from a 16-aligned base).  putchar and getchar each do one
\ `push` before the syscall, restoring rsp ≡ 0 mod 16.  Linux syscalls don't
\ care about ABI alignment, so this keeps the shim prologues uniform.

\ -- putchar(int c): write the low byte of rdi to fd 1.  29 bytes.
\
\   push rdi             57
\   mov rax, 1           48 C7 C0 01 00 00 00     (write syscall #)
\   mov rdi, 1           48 C7 C7 01 00 00 00     (fd = stdout)
\   mov rsi, rsp         48 89 E6                 (buffer = pushed qword's first byte)
\   mov rdx, 1           48 C7 C2 01 00 00 00     (count = 1)
\   syscall              0F 05
\   pop rdi              5F                       (restore rsp)
\   ret                  C3
```

The emitter turns the layout into bytes, restores the stack after the syscall, and leaves the kernel’s write result in `rax` (`forth-bootstrap/cc/090-cc-emit.fth:559`):

```forth file=cc/090-cc-emit.fth
: cc-emit-putchar-shim
  [lit]  87 cc-emit-byte                          \ push rdi
  [lit]  72 cc-emit-byte [lit] 199 cc-emit-byte [lit] 192 cc-emit-byte
  [lit]   1 cc-emit-4le                           \ mov rax, 1
  [lit]  72 cc-emit-byte [lit] 199 cc-emit-byte [lit] 199 cc-emit-byte
  [lit]   1 cc-emit-4le                           \ mov rdi, 1
  [lit]  72 cc-emit-byte [lit] 137 cc-emit-byte [lit] 230 cc-emit-byte
                                                  \ mov rsi, rsp
  [lit]  72 cc-emit-byte [lit] 199 cc-emit-byte [lit] 194 cc-emit-byte
  [lit]   1 cc-emit-4le                           \ mov rdx, 1
  [lit]  15 cc-emit-byte [lit]   5 cc-emit-byte   \ syscall
  [lit]  95 cc-emit-byte                          \ pop rdi
  [lit] 195 cc-emit-byte ;                        \ ret

```

Process termination needs only the status already in `rdi`; the trailing return instruction is unreachable after a successful exit syscall (`forth-bootstrap/cc/090-cc-emit.fth:573`):

```forth file=cc/090-cc-emit.fth
\ -- exit(int n): syscall 60 with rdi = n.  10 bytes.
\
\   mov rax, 60          48 C7 C0 3C 00 00 00
\   syscall              0F 05
\   ret                  C3                        (unreachable but tidy)
: cc-emit-exit-shim
  [lit]  72 cc-emit-byte [lit] 199 cc-emit-byte [lit] 192 cc-emit-byte
  [lit]  60 cc-emit-4le                           \ mov rax, 60
  [lit]  15 cc-emit-byte [lit]   5 cc-emit-byte   \ syscall
  [lit] 195 cc-emit-byte ;                        \ ret

```

Input uses the stack-buffer pattern too, but EOF must become a sentinel rather than a character (`forth-bootstrap/cc/090-cc-emit.fth:584`):

```forth file=cc/090-cc-emit.fth
\ -- getchar(void): read 1 byte from fd 0; return -1 on EOF.  48 bytes.
\
\   push rdi             57                          (reserve 8B scratch on stack)
\   mov rax, 0           48 C7 C0 00 00 00 00        (read syscall #)
\   mov rdi, 0           48 C7 C7 00 00 00 00        (fd = stdin)
\   mov rsi, rsp         48 89 E6
\   mov rdx, 1           48 C7 C2 01 00 00 00
\   syscall              0F 05
\   test rax, rax        48 85 C0
\   jnz .have            75 09                       (skip 9 bytes -> movzx)
\   mov rax, -1          48 C7 C0 FF FF FF FF
\   jmp .done            EB 05                       (skip 5 bytes -> pop rdi)
\ .have:
\   movzx rax, byte [rsp] 48 0F B6 04 24
\ .done:
\   pop rdi              5F
\   ret                  C3
```

`cc-emit-getchar-shim` tests for a zero read result and substitutes minus one; a nonzero result selects the scratch byte. A negative read error also takes that byte path, so this is not complete error handling (`forth-bootstrap/cc/090-cc-emit.fth:601`):

```forth file=cc/090-cc-emit.fth
: cc-emit-getchar-shim
  [lit]  87 cc-emit-byte                          \ push rdi
  [lit]  72 cc-emit-byte [lit] 199 cc-emit-byte [lit] 192 cc-emit-byte
  [lit]   0 cc-emit-4le                           \ mov rax, 0
  [lit]  72 cc-emit-byte [lit] 199 cc-emit-byte [lit] 199 cc-emit-byte
  [lit]   0 cc-emit-4le                           \ mov rdi, 0
  [lit]  72 cc-emit-byte [lit] 137 cc-emit-byte [lit] 230 cc-emit-byte
                                                  \ mov rsi, rsp
  [lit]  72 cc-emit-byte [lit] 199 cc-emit-byte [lit] 194 cc-emit-byte
  [lit]   1 cc-emit-4le                           \ mov rdx, 1
  [lit]  15 cc-emit-byte [lit]   5 cc-emit-byte   \ syscall
  [lit]  72 cc-emit-byte [lit] 133 cc-emit-byte [lit] 192 cc-emit-byte
                                                  \ test rax, rax
  [lit] 117 cc-emit-byte [lit]   9 cc-emit-byte   \ jnz +9 (skip mov+jmp)
  [lit]  72 cc-emit-byte [lit] 199 cc-emit-byte [lit] 192 cc-emit-byte
  [lit] 255 cc-emit-byte [lit] 255 cc-emit-byte
  [lit] 255 cc-emit-byte [lit] 255 cc-emit-byte   \ mov rax, -1 (sign-extended imm32 = FFFFFFFF)
  [lit] 235 cc-emit-byte [lit]   5 cc-emit-byte   \ jmp +5 (skip movzx)
  [lit]  72 cc-emit-byte [lit]  15 cc-emit-byte
  [lit] 182 cc-emit-byte [lit]   4 cc-emit-byte
  [lit]  36 cc-emit-byte                          \ movzx rax, byte [rsp]
  [lit]  95 cc-emit-byte                          \ pop rdi
  [lit] 195 cc-emit-byte ;                        \ ret

```

## Stream shims

Here `FILE *` is represented by a file descriptor, not a stream object. The interfaces expose the following behavior:

| Emitter | Input → result |
|---|---|
| `cc-emit-fputs-shim` | string, descriptor → raw write result |
| `cc-emit-fputc-shim` | character, descriptor → character byte |
| `cc-emit-fopen-shim` | path, mode → descriptor, or zero on error |
| `cc-emit-fclose-shim` | descriptor → zero |
| `cc-emit-fwrite-shim` | buffer, size, count, descriptor → bytes written |
| `cc-emit-fread-shim` | buffer, size, count, descriptor → elements read on a positive read |

Writing a NUL-terminated string first requires its byte count; the layout scans to the terminator before arranging the write arguments (`forth-bootstrap/cc/090-cc-emit.fth:625`):

```forth file=cc/090-cc-emit.fth
\ ===========================================================================
\ Libc shims: fputs, fputc, fopen, fclose, fwrite, fread, calloc,
\ free.  All follow SYS-V x86-64 ABI.  Symbol registration and
\ vaddr assignment happen in cc-emit-shims (116-cc-prog.fth).
\ ===========================================================================

\ -- fputs(char *s, FILE *fp) -> non-negative on success.  33 bytes.
\
\   push rdi           57                    (save str)
\   push rsi           56                    (save fd)
\   xor rdx, rdx       48 31 D2              (length counter)
\ .loop:
\   movzx ecx, [rdi+rdx]  0F B6 0C 17       SIB: idx=rdx(2) base=rdi(7)
\   test cl, cl            84 C9
\   jz +5  (.done)         74 05
\   inc rdx                48 FF C2
\   jmp .loop              EB F3             (disp = -13)
\ .done:
\   mov rax, 1         48 C7 C0 01 00 00 00  (write)
\   mov rsi, rdi       48 89 FE              (buf = str)
\   pop rdi            5F                    (fd = saved rsi slot)
\   pop rcx            59                    (discard saved str)
\   syscall            0F 05
\   ret                C3
```

The emitted scan leaves its length in `rdx`, then recovers the saved descriptor into `rdi` before the syscall (`forth-bootstrap/cc/090-cc-emit.fth:649`):

```forth file=cc/090-cc-emit.fth
: cc-emit-fputs-shim
  [lit]  87 cc-emit-byte                          \ push rdi
  [lit]  86 cc-emit-byte                          \ push rsi
  [lit]  72 cc-emit-byte [lit]  49 cc-emit-byte
  [lit] 210 cc-emit-byte                          \ xor rdx, rdx
  [lit]  15 cc-emit-byte [lit] 182 cc-emit-byte
  [lit]  12 cc-emit-byte [lit]  23 cc-emit-byte   \ movzx ecx, [rdi+rdx]
  [lit] 132 cc-emit-byte [lit] 201 cc-emit-byte   \ test cl, cl
  [lit] 116 cc-emit-byte [lit]   5 cc-emit-byte   \ jz +5
  [lit]  72 cc-emit-byte [lit] 255 cc-emit-byte
  [lit] 194 cc-emit-byte                          \ inc rdx
  [lit] 235 cc-emit-byte [lit] 243 cc-emit-byte   \ jmp .loop  (disp = -13)
  [lit]  72 cc-emit-byte [lit] 199 cc-emit-byte
  [lit] 192 cc-emit-byte [lit]   1 cc-emit-4le    \ mov rax, 1
  [lit]  72 cc-emit-byte [lit] 137 cc-emit-byte
  [lit] 254 cc-emit-byte                          \ mov rsi, rdi  (buf)
  [lit]  95 cc-emit-byte                          \ pop rdi  (fd)
  [lit]  89 cc-emit-byte                          \ pop rcx  (discard str)
  [lit]  15 cc-emit-byte [lit]   5 cc-emit-byte   \ syscall
  [lit] 195 cc-emit-byte ;                        \ ret

```

A single-character stream write avoids the scan by using the stack-buffer pattern. Its return path reloads the character even if the syscall failed (`forth-bootstrap/cc/090-cc-emit.fth:670`):

```forth file=cc/090-cc-emit.fth
\ -- fputc(int c, FILE *fp) -> c on success.  30 bytes.
\
\   push rdi           57                    (char onto stack = write buffer)
\   mov rax, 1         48 C7 C0 01 00 00 00
\   mov rdi, rsi       48 89 F7              (fd = arg2)
\   mov rsi, rsp       48 89 E6              (buf = stack)
\   mov rdx, 1         48 C7 C2 01 00 00 00
\   syscall            0F 05
\   movzx eax, [rsp]   0F B6 04 24           (return char)
\   pop rcx            59
\   ret                C3
: cc-emit-fputc-shim
  [lit]  87 cc-emit-byte                          \ push rdi
  [lit]  72 cc-emit-byte [lit] 199 cc-emit-byte
  [lit] 192 cc-emit-byte [lit]   1 cc-emit-4le    \ mov rax, 1
  [lit]  72 cc-emit-byte [lit] 137 cc-emit-byte
  [lit] 247 cc-emit-byte                          \ mov rdi, rsi  (fd)
  [lit]  72 cc-emit-byte [lit] 137 cc-emit-byte
  [lit] 230 cc-emit-byte                          \ mov rsi, rsp  (buf)
  [lit]  72 cc-emit-byte [lit] 199 cc-emit-byte
  [lit] 194 cc-emit-byte [lit]   1 cc-emit-4le    \ mov rdx, 1
  [lit]  15 cc-emit-byte [lit]   5 cc-emit-byte   \ syscall
  [lit]  15 cc-emit-byte [lit] 182 cc-emit-byte
  [lit]   4 cc-emit-byte [lit]  36 cc-emit-byte   \ movzx eax, [rsp]
  [lit]  89 cc-emit-byte                          \ pop rcx
  [lit] 195 cc-emit-byte ;                        \ ret

```

Opening a stream interprets only the first mode character: `w` selects truncation, `a` selects append, and every other character leaves read-only flags (`forth-bootstrap/cc/090-cc-emit.fth:697`):

```forth file=cc/090-cc-emit.fth
\ -- fopen(char *path, char *mode) -> fd on success, 0 on error.  51 bytes.
\
\   push rdi           57
\   movzx eax, [rsi]   0F B6 06              (first char of mode)
\   xor esi, esi       31 F6                 (flags = O_RDONLY = 0)
\   cmp eax, 119       83 F8 77              ('w')
\   jne +7  (.try_a)   75 07
\   mov esi, 0x241     BE 41 02 00 00        (O_WRONLY|O_CREAT|O_TRUNC)
\   jmp +10  (.open)   EB 0A
\ .try_a:
\   cmp eax, 97        83 F8 61              ('a')
\   jne +5  (.open)    75 05
\   mov esi, 0x441     BE 41 04 00 00        (O_WRONLY|O_CREAT|O_APPEND)
\ .open:
\   pop rdi            5F
\   mov rax, 2         48 C7 C0 02 00 00 00  (open syscall)
\   mov edx, 420       BA A4 01 00 00        (mode 0644)
\   syscall            0F 05
\   test rax, rax      48 85 C0
\   jns +2  (.ok)      79 02
\   xor eax, eax       31 C0                 (return NULL on error)
\ .ok:
\   ret                C3
```

The mode-selection branches join at `open`; a negative result is replaced with zero. A successful descriptor zero is therefore indistinguishable from the error result (`forth-bootstrap/cc/090-cc-emit.fth:720`):

```forth file=cc/090-cc-emit.fth
: cc-emit-fopen-shim
  [lit]  87 cc-emit-byte                          \ push rdi
  [lit]  15 cc-emit-byte [lit] 182 cc-emit-byte
  [lit]   6 cc-emit-byte                          \ movzx eax, [rsi]
  [lit]  49 cc-emit-byte [lit] 246 cc-emit-byte   \ xor esi, esi
  [lit] 131 cc-emit-byte [lit] 248 cc-emit-byte
  [char] w  cc-emit-byte                          \ cmp eax, 'w'
  [lit] 117 cc-emit-byte [lit]   7 cc-emit-byte   \ jne +7
  [lit] 190 cc-emit-byte [lit] 577 cc-emit-4le    \ mov esi, 0x241
  [lit] 235 cc-emit-byte [lit]  10 cc-emit-byte   \ jmp +10
  [lit] 131 cc-emit-byte [lit] 248 cc-emit-byte
  [char] a  cc-emit-byte                          \ cmp eax, 'a'
  [lit] 117 cc-emit-byte [lit]   5 cc-emit-byte   \ jne +5
  [lit] 190 cc-emit-byte [lit] 1089 cc-emit-4le   \ mov esi, 0x441
  [lit]  95 cc-emit-byte                          \ pop rdi
  [lit]  72 cc-emit-byte [lit] 199 cc-emit-byte
  [lit] 192 cc-emit-byte [lit]   2 cc-emit-4le    \ mov rax, 2
  [lit] 186 cc-emit-byte [lit] 420 cc-emit-4le    \ mov edx, 0644
  [lit]  15 cc-emit-byte [lit]   5 cc-emit-byte   \ syscall
  [lit]  72 cc-emit-byte [lit] 133 cc-emit-byte
  [lit] 192 cc-emit-byte                          \ test rax, rax
  [lit] 121 cc-emit-byte [lit]   2 cc-emit-byte   \ jns +2
  [lit]  49 cc-emit-byte [lit] 192 cc-emit-byte   \ xor eax, eax
  [lit] 195 cc-emit-byte ;                        \ ret

```

Closing discards the syscall result and returns zero unconditionally, which explains the restricted result contract in the table (`forth-bootstrap/cc/090-cc-emit.fth:745`):

```forth file=cc/090-cc-emit.fth
\ -- fclose(FILE *fp) -> 0.  12 bytes.
\
\   mov rax, 3    48 C7 C0 03 00 00 00  (close syscall)
\   syscall       0F 05
\   xor eax, eax  31 C0
\   ret           C3
: cc-emit-fclose-shim
  [lit]  72 cc-emit-byte [lit] 199 cc-emit-byte
  [lit] 192 cc-emit-byte [lit]   3 cc-emit-4le    \ mov rax, 3
  [lit]  15 cc-emit-byte [lit]   5 cc-emit-byte   \ syscall
  [lit]  49 cc-emit-byte [lit] 192 cc-emit-byte   \ xor eax, eax
  [lit] 195 cc-emit-byte ;                        \ ret

```

## Block transfers

Block output multiplies element size by count to obtain a byte count and moves the descriptor from `rcx` before `syscall` can clobber it (`forth-bootstrap/cc/090-cc-emit.fth:758`):

```forth file=cc/090-cc-emit.fth
\ -- fwrite(void *ptr, size_t sz, size_t n, FILE *fp) -> bytes written.  20 bytes.
\
\   imul rdx, rsi  48 0F AF D6   (total = n * sz;  rdx=n, rsi=sz)
\   mov rsi, rdi   48 89 FE      (buf = ptr)
\   mov rdi, rcx   48 89 CF      (fd = arg4)
\   mov rax, 1     48 C7 C0 01 00 00 00
\   syscall        0F 05
\   ret            C3
: cc-emit-fwrite-shim
  [lit]  72 cc-emit-byte [lit]  15 cc-emit-byte
  [lit] 175 cc-emit-byte [lit] 214 cc-emit-byte   \ imul rdx, rsi
  [lit]  72 cc-emit-byte [lit] 137 cc-emit-byte
  [lit] 254 cc-emit-byte                          \ mov rsi, rdi  (buf)
  [lit]  72 cc-emit-byte [lit] 137 cc-emit-byte
  [lit] 207 cc-emit-byte                          \ mov rdi, rcx  (fd)
  [lit]  72 cc-emit-byte [lit] 199 cc-emit-byte
  [lit] 192 cc-emit-byte [lit]   1 cc-emit-4le    \ mov rax, 1
  [lit]  15 cc-emit-byte [lit]   5 cc-emit-byte   \ syscall
  [lit] 195 cc-emit-byte ;                        \ ret

```

Block input must preserve the element size across the syscall so it can convert a positive byte count back to an element count (`forth-bootstrap/cc/090-cc-emit.fth:778`):

```forth file=cc/090-cc-emit.fth
\ -- fread(void *ptr, size_t sz, size_t n, FILE *fp) -> elements read.  30 bytes.
\
\   push rsi         56               (save sz)
\   imul rsi, rdx    48 0F AF F2      (total = sz * n)
\   mov rdx, rsi     48 89 F2         (count)
\   mov rsi, rdi     48 89 FE         (buf = ptr)
\   mov rdi, rcx     48 89 CF         (fd = arg4)
\   xor eax, eax     31 C0            (read = 0)
\   syscall          0F 05
\   pop rcx          59               (restore sz)
\   test rax, rax    48 85 C0
\   jle +5  (.done)  7E 05
\   xor edx, edx     31 D2            (clear for div)
\   div rcx          48 F7 F1         (rax = bytes_read / sz)
\ .done:
\   ret              C3
```

Saving the size on the stack protects it until division. Nonpositive read results bypass that division, including raw negative errors (`forth-bootstrap/cc/090-cc-emit.fth:794`):

```forth file=cc/090-cc-emit.fth
: cc-emit-fread-shim
  [lit]  86 cc-emit-byte                          \ push rsi
  [lit]  72 cc-emit-byte [lit]  15 cc-emit-byte
  [lit] 175 cc-emit-byte [lit] 242 cc-emit-byte   \ imul rsi, rdx
  [lit]  72 cc-emit-byte [lit] 137 cc-emit-byte
  [lit] 242 cc-emit-byte                          \ mov rdx, rsi  (count)
  [lit]  72 cc-emit-byte [lit] 137 cc-emit-byte
  [lit] 254 cc-emit-byte                          \ mov rsi, rdi  (buf)
  [lit]  72 cc-emit-byte [lit] 137 cc-emit-byte
  [lit] 207 cc-emit-byte                          \ mov rdi, rcx  (fd)
  [lit]  49 cc-emit-byte [lit] 192 cc-emit-byte   \ xor eax, eax
  [lit]  15 cc-emit-byte [lit]   5 cc-emit-byte   \ syscall
  [lit]  89 cc-emit-byte                          \ pop rcx  (sz)
  [lit]  72 cc-emit-byte [lit] 133 cc-emit-byte
  [lit] 192 cc-emit-byte                          \ test rax, rax
  [lit] 126 cc-emit-byte [lit]   5 cc-emit-byte   \ jle +5
  [lit]  49 cc-emit-byte [lit] 210 cc-emit-byte   \ xor edx, edx
  [lit]  72 cc-emit-byte [lit] 247 cc-emit-byte
  [lit] 241 cc-emit-byte                          \ div rcx
  [lit] 195 cc-emit-byte ;                        \ ret

```

## Allocation with inline state

The generated `calloc` keeps its allocation state beside its machine code. The layout locates `heap_base` and `heap_pos` after the return instruction and accesses them relative to the next instruction address (`forth-bootstrap/cc/090-cc-emit.fth:815`):

```forth file=cc/090-cc-emit.fth
\ -- calloc(size_t n, size_t sz) -> zeroed memory or NULL.  113 bytes.
\
\ Bump allocator backed by a single 256 MB mmap.  heap_base and heap_pos
\ are stored as inline 8-byte data slots immediately after the ret.
\ All RIP-relative displacements are fixed because the shim is a closed
\ region; the offsets below are exact (verified by hand):
\
\   heap_base @ shim_offset 97  (rip+0x58 from @2, rip+0x2A from @48)
\   heap_pos  @ shim_offset 105 (rip+0x2B from @55, rip+0x16 from @76,
\                                 rip+0x09 from @89)
\
\   push rdi                    57
\   push rsi                    56
\   mov rax, [rip+0x58]         48 8B 05 58 00 00 00  (heap_base)
\   test rax, rax               48 85 C0
\   jnz +48  (.have_heap)       75 30
\   xor edi, edi                31 FF
\   mov esi, 0x10000000         BE 00 00 00 10
\   mov edx, 3                  BA 03 00 00 00   (PROT_READ|PROT_WRITE)
\   mov r10d, 0x22              41 BA 22 00 00 00  (MAP_PRIVATE|MAP_ANONYMOUS)
\   mov r8d, -1                 41 B8 FF FF FF FF  (no fd)
\   xor r9d, r9d                45 31 C9           (offset=0)
\   mov eax, 9                  B8 09 00 00 00     (mmap)
\   syscall                     0F 05
\   mov [rip+0x2A], rax         48 89 05 2A 00 00 00  (heap_base)
\   mov [rip+0x2B], rax         48 89 05 2B 00 00 00  (heap_pos)
```

Once a mapping exists, allocation rounds the request, returns the current position, and stores the advanced position (`forth-bootstrap/cc/090-cc-emit.fth:841`):

```forth file=cc/090-cc-emit.fth
\ .have_heap:
\   pop rsi                     5E
\   pop rdi                     5F
\   imul rdi, rsi               48 0F AF FE   (total = n*sz)
\   add rdi, 7                  48 83 C7 07   (align8)
\   and rdi, -8                 48 83 E7 F8
\   mov rax, [rip+0x16]         48 8B 05 16 00 00 00  (heap_pos = cur)
\   mov rcx, rax                48 89 C1
\   add rcx, rdi                48 01 F9      (new_pos = cur + size)
\   mov [rip+0x09], rcx         48 89 0D 09 00 00 00  (heap_pos = new_pos)
\   ret                         C3
\   heap_base: 8 zero bytes     (mmap is zero-filled by Linux)
\   heap_pos:  8 zero bytes
```

`cc-emit-calloc-shim` skips mapping when `heap_base` is nonzero; otherwise the emitted syscall requests writable anonymous memory and saves its result in both inline slots (`forth-bootstrap/cc/090-cc-emit.fth:854`):

```forth file=cc/090-cc-emit.fth
: cc-emit-calloc-shim
  [lit]  87 cc-emit-byte                          \ push rdi
  [lit]  86 cc-emit-byte                          \ push rsi
  [lit]  72 cc-emit-byte [lit] 139 cc-emit-byte
  [lit]   5 cc-emit-byte [lit]  88 cc-emit-4le    \ mov rax, [rip+0x58]
  [lit]  72 cc-emit-byte [lit] 133 cc-emit-byte
  [lit] 192 cc-emit-byte                          \ test rax, rax
  [lit] 117 cc-emit-byte [lit]  48 cc-emit-byte   \ jnz +48 (.have_heap)
  [lit]  49 cc-emit-byte [lit] 255 cc-emit-byte   \ xor edi, edi
  [lit] 190 cc-emit-byte [lit] 268435456 cc-emit-4le  \ mov esi, 0x10000000 (256 MB heap)
  [lit] 186 cc-emit-byte [lit]   3 cc-emit-4le    \ mov edx, 3
  [lit]  65 cc-emit-byte [lit] 186 cc-emit-byte
  [lit]  34 cc-emit-4le                           \ mov r10d, 0x22
  [lit]  65 cc-emit-byte [lit] 184 cc-emit-byte
  [lit] 255 cc-emit-byte [lit] 255 cc-emit-byte
  [lit] 255 cc-emit-byte [lit] 255 cc-emit-byte   \ mov r8d, -1  (4 explicit bytes)
  [lit]  69 cc-emit-byte [lit]  49 cc-emit-byte
  [lit] 201 cc-emit-byte                          \ xor r9d, r9d
  [lit] 184 cc-emit-byte [lit]   9 cc-emit-4le    \ mov eax, 9
  [lit]  15 cc-emit-byte [lit]   5 cc-emit-byte   \ syscall
  [lit]  72 cc-emit-byte [lit] 137 cc-emit-byte
  [lit]   5 cc-emit-byte [lit]  42 cc-emit-4le    \ mov [rip+0x2A], rax (heap_base)
  [lit]  72 cc-emit-byte [lit] 137 cc-emit-byte
  [lit]   5 cc-emit-byte [lit]  43 cc-emit-4le    \ mov [rip+0x2B], rax (heap_pos)
```

Subsequent calls use the saved position. Fresh anonymous pages supply the zero bytes, while the return instruction prevents execution from falling into the state slots (`forth-bootstrap/cc/090-cc-emit.fth:878`):

```forth file=cc/090-cc-emit.fth
  [lit]  94 cc-emit-byte                          \ pop rsi
  [lit]  95 cc-emit-byte                          \ pop rdi
  [lit]  72 cc-emit-byte [lit]  15 cc-emit-byte
  [lit] 175 cc-emit-byte [lit] 254 cc-emit-byte   \ imul rdi, rsi
  [lit]  72 cc-emit-byte [lit] 131 cc-emit-byte
  [lit] 199 cc-emit-byte [lit]   7 cc-emit-byte   \ add rdi, 7
  [lit]  72 cc-emit-byte [lit] 131 cc-emit-byte
  [lit] 231 cc-emit-byte [lit] 248 cc-emit-byte   \ and rdi, -8
  [lit]  72 cc-emit-byte [lit] 139 cc-emit-byte
  [lit]   5 cc-emit-byte [lit]  22 cc-emit-4le    \ mov rax, [rip+0x16] (heap_pos)
  [lit]  72 cc-emit-byte [lit] 137 cc-emit-byte
  [lit] 193 cc-emit-byte                          \ mov rcx, rax
  [lit]  72 cc-emit-byte [lit]   1 cc-emit-byte
  [lit] 249 cc-emit-byte                          \ add rcx, rdi
  [lit]  72 cc-emit-byte [lit] 137 cc-emit-byte
  [lit]  13 cc-emit-byte [lit]   9 cc-emit-4le    \ mov [rip+0x09], rcx (heap_pos)
  [lit] 195 cc-emit-byte                          \ ret
  [lit]   0 cc-emit-8le                           \ heap_base = 0
  [lit]   0 cc-emit-8le ;                         \ heap_pos  = 0
```

The fixed displacements depend on distances within the shim. Adding bytes before the whole shim moves accesses and slots together; adding bytes between an access and its slot changes that displacement. Despite the header comment’s “or NULL,” this body checks neither mapping failure nor heap exhaustion, and it does not check multiplication overflow.

`cc-emit-free-shim` leaves the bump position untouched, so allocations are never reused (`forth-bootstrap/cc/090-cc-emit.fth:899`):

```forth file=cc/090-cc-emit.fth

\ -- free(void *p) -> void.  1 byte.  No-op: bump allocator never frees.
: cc-emit-free-shim
  [lit] 195 cc-emit-byte ;                        \ ret

```

## Descriptor calls and allocation wrappers

| Emitter | Input → result |
|---|---|
| `cc-emit-syscall-shim` | syscall number at emission → wrapper mapping negative results to minus one |
| `cc-emit-malloc-shim` | `calloc` address at emission → allocation wrapper |

Descriptor calls already have their arguments in the needed registers, so the shared body adds only the syscall number and error normalization. Its length is 20 bytes: `5 + 2 + 3 + 2 + 7 + 1` for the six displayed instructions. The copied comment's 22-byte total is stale; `jns +7` still skips exactly the seven-byte failure-value load (`forth-bootstrap/cc/090-cc-emit.fth:902`):

```forth file=cc/090-cc-emit.fth
\ ===========================================================================
\ Libc shims: the POSIX calls open, read, write, close; malloc, and the
\ string functions strlen, memcpy, strrchr.
\ ===========================================================================

\ -- open / read / write / close: the arguments are already where the
\ syscall wants them (rdi, rsi, rdx), so each is the syscall plus C's
\ error convention: a negative result (Linux's -errno) becomes -1.  22 bytes.
\
\   mov eax, N          B8 <N>
\   syscall             0F 05
\   test rax, rax       48 85 C0
\   jns +7  (.ok)       79 07
\   mov rax, -1         48 C7 C0 FF FF FF FF
\ .ok:
\   ret                 C3
: cc-emit-syscall-shim                            ( n -- )
  [lit] 184 cc-emit-byte cc-emit-4le              \ mov eax, n
  [lit]  15 cc-emit-byte [lit]   5 cc-emit-byte   \ syscall
  [lit]  72 cc-emit-byte [lit] 133 cc-emit-byte
  [lit] 192 cc-emit-byte                          \ test rax, rax
  [lit] 121 cc-emit-byte [lit]   7 cc-emit-byte   \ jns +7
  [lit]  72 cc-emit-byte [lit] 199 cc-emit-byte [lit] 192 cc-emit-byte
  [lit] 255 cc-emit-byte [lit] 255 cc-emit-byte
  [lit] 255 cc-emit-byte [lit] 255 cc-emit-byte   \ mov rax, -1
  [lit] 195 cc-emit-byte ;                        \ ret
```

The allocation wrapper sets the element size and jumps to `calloc`, preserving the original caller’s return address (`forth-bootstrap/cc/090-cc-emit.fth:928`):

```forth file=cc/090-cc-emit.fth

\ -- malloc(size_t n) -> calloc(n, 1).  12 bytes.
\
\   mov rsi, 1          48 C7 C6 01 00 00 00
\   jmp calloc          E9 <rel32>
: cc-emit-malloc-shim                             ( calloc-vaddr -- )
  [lit]  72 cc-emit-byte [lit] 199 cc-emit-byte
  [lit] 198 cc-emit-byte [lit]   1 cc-emit-4le    \ mov rsi, 1
  [lit] 233 cc-emit-byte
  cc-here-vaddr [lit] 4 + - cc-emit-4le ;         \ jmp calloc

```

## Scanning and copying strings

| Emitter | Input → result |
|---|---|
| `cc-emit-strlen-shim` | string → length before NUL |
| `cc-emit-memcpy-shim` | destination, source, count → original destination |
| `cc-emit-strrchr-shim` | string, character → last matching address or NULL |

A terminator scan can return its index directly: `strlen` keeps the count in `rax`, with no syscall or frame (`forth-bootstrap/cc/090-cc-emit.fth:939`):

```forth file=cc/090-cc-emit.fth
\ -- strlen(char *s) -> length.  14 bytes.
\
\   xor eax, eax             31 C0
\ .loop:
\   cmp byte [rdi+rax], 0    80 3C 07 00
\   je +5  (.done)           74 05
\   inc rax                  48 FF C0
\   jmp .loop                EB F5
\ .done:
\   ret                      C3
: cc-emit-strlen-shim
  [lit]  49 cc-emit-byte [lit] 192 cc-emit-byte   \ xor eax, eax
  [lit] 128 cc-emit-byte [lit]  60 cc-emit-byte
  [lit]   7 cc-emit-byte [lit]   0 cc-emit-byte   \ cmp byte [rdi+rax], 0
  [lit] 116 cc-emit-byte [lit]   5 cc-emit-byte   \ je +5
  [lit]  72 cc-emit-byte [lit] 255 cc-emit-byte
  [lit] 192 cc-emit-byte                          \ inc rax
  [lit] 235 cc-emit-byte [lit] 245 cc-emit-byte   \ jmp .loop  (disp = -11)
  [lit] 195 cc-emit-byte ;                        \ ret

```

`memcpy` saves the original destination before `rep movsb` advances the pointers; the count moves into `rcx` for that instruction (`forth-bootstrap/cc/090-cc-emit.fth:959`):

```forth file=cc/090-cc-emit.fth
\ -- memcpy(void *d, void *s, size_t n) -> d.  9 bytes.
\
\   mov rax, rdi     48 89 F8
\   mov rcx, rdx     48 89 D1
\   rep movsb        F3 A4           (rdi = d, rsi = s already)
\   ret              C3
: cc-emit-memcpy-shim
  [lit]  72 cc-emit-byte [lit] 137 cc-emit-byte
  [lit] 248 cc-emit-byte                          \ mov rax, rdi
  [lit]  72 cc-emit-byte [lit] 137 cc-emit-byte
  [lit] 209 cc-emit-byte                          \ mov rcx, rdx
  [lit] 243 cc-emit-byte [lit] 164 cc-emit-byte   \ rep movsb
  [lit] 195 cc-emit-byte ;                        \ ret

```

Finding the last matching character requires retaining a candidate while continuing the scan. The comparison precedes the terminator test so searching for NUL can succeed (`forth-bootstrap/cc/090-cc-emit.fth:973`):

```forth file=cc/090-cc-emit.fth
\ -- strrchr(char *s, int c) -> pointer to the last c in s (the NUL
\ counts, so c = 0 finds the end), or NULL.  23 bytes.
\
\   xor eax, eax               31 C0
\ .loop:
\   movzx ecx, byte [rdi]      0F B6 0F
\   cmp cl, sil                40 38 F1
\   jne +3  (.skip)            75 03
\   mov rax, rdi               48 89 F8
\ .skip:
\   test cl, cl                84 C9
\   je +5  (.done)             74 05
\   inc rdi                    48 FF C7
\   jmp .loop                  EB EC
\ .done:
\   ret                        C3
```

On a match, the current address replaces the candidate in `rax`; otherwise it survives the next iteration (`forth-bootstrap/cc/090-cc-emit.fth:989`):

```forth file=cc/090-cc-emit.fth
: cc-emit-strrchr-shim
  [lit]  49 cc-emit-byte [lit] 192 cc-emit-byte   \ xor eax, eax
  [lit]  15 cc-emit-byte [lit] 182 cc-emit-byte
  [lit]  15 cc-emit-byte                          \ movzx ecx, byte [rdi]
  [lit]  64 cc-emit-byte [lit]  56 cc-emit-byte
  [lit] 241 cc-emit-byte                          \ cmp cl, sil
  [lit] 117 cc-emit-byte [lit]   3 cc-emit-byte   \ jne +3
  [lit]  72 cc-emit-byte [lit] 137 cc-emit-byte
  [lit] 248 cc-emit-byte                          \ mov rax, rdi
  [lit] 132 cc-emit-byte [lit] 201 cc-emit-byte   \ test cl, cl
  [lit] 116 cc-emit-byte [lit]   5 cc-emit-byte   \ je +5
  [lit]  72 cc-emit-byte [lit] 255 cc-emit-byte
  [lit] 199 cc-emit-byte                          \ inc rdi
  [lit] 235 cc-emit-byte [lit] 236 cc-emit-byte   \ jmp .loop  (disp = -20)
  [lit] 195 cc-emit-byte ;                        \ ret

```

## Bitwise, shifts, inc/dec, and unary `!`

The register operations retain the accumulator interface. Their differences fit in a table:

| Emitter | Input → result |
|---|---|
| `cc-emit-shl-rdi-cl` | `rdi`, count in `cl` → left shift |
| `cc-emit-sar-rdi-cl` | `rdi`, count in `cl` → sign-propagating right shift |
| `cc-emit-and-rdi-rcx` | `rdi`, `rcx` → bitwise AND |
| `cc-emit-or-rdi-rcx` | `rdi`, `rcx` → bitwise OR |
| `cc-emit-xor-rdi-rcx` | `rdi`, `rcx` → bitwise XOR |
| `cc-emit-not-rdi` | `rdi` → bitwise complement |
| `cc-emit-neg-rdi` | `rdi` → arithmetic negation |

Variable shifts take their count from `cl`, which is already part of the right-operand register; the arithmetic right shift propagates the sign bit (`forth-bootstrap/cc/090-cc-emit.fth:1005`):

```forth file=cc/090-cc-emit.fth
\ ===========================================================================
\ Shifts, bitwise ops, inc/dec/neg/not on rdi
\ ===========================================================================
\ Variable-count shifts use rcx (specifically CL).  The binary-op pattern
\ leaves rdi=left and rcx=right (already in rcx because of mov rcx,rdi+pop).
\
\ shl rdi, cl: 48 D3 E7   (D3 /4, mod=11 rm=rdi=7 -> 11_100_111=0xE7)
: cc-emit-shl-rdi-cl
  [lit]  72 cc-emit-byte
  [lit] 211 cc-emit-byte
  [lit] 231 cc-emit-byte ;

\ sar rdi, cl (arithmetic right shift, signed): 48 D3 FF  (D3 /7 -> 11_111_111=0xFF)
: cc-emit-sar-rdi-cl
  [lit]  72 cc-emit-byte
  [lit] 211 cc-emit-byte
  [lit] 255 cc-emit-byte ;

```

The bitwise binary operations share operand selection, leaving only the operation byte to vary (`forth-bootstrap/cc/090-cc-emit.fth:1023`):

```forth file=cc/090-cc-emit.fth
\ and rdi, rcx: 48 21 CF  (21 /r, mod=11 reg=rcx=1 rm=rdi=7 -> 11_001_111=0xCF)
: cc-emit-and-rdi-rcx
  [lit]  72 cc-emit-byte
  [lit]  33 cc-emit-byte
  [lit] 207 cc-emit-byte ;

\ or rdi, rcx: 48 09 CF
: cc-emit-or-rdi-rcx
  [lit]  72 cc-emit-byte
  [lit]   9 cc-emit-byte
  [lit] 207 cc-emit-byte ;

\ xor rdi, rcx: 48 31 CF
: cc-emit-xor-rdi-rcx
  [lit]  72 cc-emit-byte
  [lit]  49 cc-emit-byte
  [lit] 207 cc-emit-byte ;

```

Complement and negation select different operations within the same instruction family; neither implements C’s logical `!` (`forth-bootstrap/cc/090-cc-emit.fth:1041`):

```forth file=cc/090-cc-emit.fth
\ not rdi: 48 F7 D7  (F7 /2 = NOT, mod=11 rm=rdi=7 -> 11_010_111=0xD7)
: cc-emit-not-rdi
  [lit]  72 cc-emit-byte
  [lit] 247 cc-emit-byte
  [lit] 215 cc-emit-byte ;

\ neg rdi: 48 F7 DF  (F7 /3 = NEG, mod=11 rm=rdi=7 -> 11_011_111=0xDF)
: cc-emit-neg-rdi
  [lit]  72 cc-emit-byte
  [lit] 247 cc-emit-byte
  [lit] 223 cc-emit-byte ;

```

## Updating memory without losing the expression value

Post-increment must retain the old value while changing storage. `cc-emit-inc-mem-local` and `cc-emit-dec-mem-local` update the addressed slot without changing `rdi` (`forth-bootstrap/cc/090-cc-emit.fth:1053`):

```forth file=cc/090-cc-emit.fth
\ inc qword [rbp + disp]: 48 FF 45 <disp8>  (or 48 FF 85 <disp32>)
\ ModR/M(mod=01, reg=/0=INC, rm=rbp=5) = 01_000_101 = 0x45.  Increments the
\ local slot in place without disturbing rdi/rcx (used by post-increment).
: cc-emit-inc-mem-local                           ( slot -- )
  [lit]  72 cc-emit-byte
  [lit] 255 cc-emit-byte
  [lit]  69 cc-emit-local-ea ;

\ dec qword [rbp + disp]: 48 FF 4D <disp8>  (or 48 FF 8D <disp32>)
\ ModR/M(mod=01, reg=/1=DEC, rm=rbp=5) = 01_001_101 = 0x4D.
: cc-emit-dec-mem-local                           ( slot -- )
  [lit]  72 cc-emit-byte
  [lit] 255 cc-emit-byte
  [lit]  77 cc-emit-local-ea ;

```

For an indirect operand, `rcx` retains the address while `cc-emit-load-via-rcx` retrieves the old value. `cc-emit-inc-via-rcx` and `cc-emit-dec-via-rcx` select byte or qword storage from `byte?` (`forth-bootstrap/cc/090-cc-emit.fth:1068`):

```forth file=cc/090-cc-emit.fth
\ The same through the address in rcx, for a ++ / -- whose operand is a
\ pointer target, an element or a field (rcx holds its address).
\ byte? picks the one-byte form (a char).
\   inc qword [rcx]  48 FF 01      inc byte [rcx]  FE 01
\   dec qword [rcx]  48 FF 09      dec byte [rcx]  FE 09
: cc-emit-inc-via-rcx                             ( byte? -- )
  0= if, [lit] 72 cc-emit-byte [lit] 255 else, [lit] 254 then,
  cc-emit-byte  [lit] 1 cc-emit-byte ;
: cc-emit-dec-via-rcx                             ( byte? -- )
  0= if, [lit] 72 cc-emit-byte [lit] 255 else, [lit] 254 then,
  cc-emit-byte  [lit] 9 cc-emit-byte ;

\ mov rdi, [rcx]  48 8B 39   /  movzx rdi, byte [rcx]  48 0F B6 39
: cc-emit-load-via-rcx                            ( byte? -- )
  [lit] 72 cc-emit-byte
  if, [lit] 15 cc-emit-byte [lit] 182 else, [lit] 139 then,
  cc-emit-byte  [lit] 57 cc-emit-byte ;

```

`cc-emit-not-zero-flag` replaces the accumulator with the C truth value for logical negation. Clearing `rax` before testing lets `sete al` supply the whole result without stale high bits (`forth-bootstrap/cc/090-cc-emit.fth:1088`):

```forth file=cc/090-cc-emit.fth
\ cc-emit-not-zero-flag.  Canonicalize rdi to 0/1 = (rdi == 0).
\ Pattern: xor rax,rax; test rdi,rdi; sete al; mov rdi,rax.  Used by unary '!'.
: cc-emit-not-zero-flag
  [lit]  72 cc-emit-byte [lit]  49 cc-emit-byte [lit] 192 cc-emit-byte
                                                  \ xor rax,rax
  [lit]  72 cc-emit-byte [lit] 133 cc-emit-byte [lit] 255 cc-emit-byte
                                                  \ test rdi,rdi
  [lit]  15 cc-emit-byte [lit] 148 cc-emit-byte [lit] 192 cc-emit-byte
                                                  \ sete al
  [lit]  72 cc-emit-byte [lit] 137 cc-emit-byte [lit] 199 cc-emit-byte ;
                                                  \ mov rdi,rax

```

Chapter 34 chooses when to load, update, and preserve an expression’s value. These helpers provide the operations without making that parser decision.

## File-scope globals and deferred vaddr fixups

A global reference needs both a storage slot and a future address. The source’s layout contract distinguishes file-backed data from zero-filled storage and records each use until placement is known (`forth-bootstrap/cc/090-cc-emit.fth:1098`):

```forth file=cc/090-cc-emit.fth
\ ===========================================================================
\ File-scope global variables.
\ ===========================================================================
\ Globals live in two areas placed after the code, in the same PT_LOAD
\ segment:
\   data  scalars, and whatever has an initializer.  Built in
\         cc-globals-buf during parsing (initializer bytes are written
\         straight in; the rest stays zero) and appended to the output
\         file.
\   bss   arrays.  They start zeroed, so they take no room in the file:
\         the segment's p_memsz simply extends past its p_filesz, and
\         the kernel zero-fills the difference.
\ Each global gets a SLOT: its offset in the data area, or cc-bss-flag
\ plus its offset in the bss.
\
\ At codegen time, an IDENT referring to a sk-global emits
\     movabs rdi, <imm64 placeholder = 0>          ; 10 bytes
\ and records (patch-offset-in-cc-out-buf, slot) into the cc-gfixup arrays.
\
\ At cc-finalize-globals (called after parsing, before cc-finalize-elf):
\   1. cc-globals-base-vaddr := cc-here-vaddr (080); the bss starts at
\      the first 8-aligned address after the data.
\   2. Append cc-globals-buf bytes to cc-out-buf.
\   3. For each fixup, compute the slot's vaddr and patch the placeholder
\      imm64 in cc-out-buf at the recorded patch-offset.

```

`cc-globals-buf` stores initialized bytes under `cc-globals-cap`, with `cc-globals-pos` as its cursor. BSS needs only `cc-bss-pos` and `cc-bss-cap`; adding `cc-bss-flag` to its offsets makes those slots distinguishable from data offsets (`forth-bootstrap/cc/090-cc-emit.fth:1124`):

```forth file=cc/090-cc-emit.fth
[lit] 65536 constant cc-globals-cap                \ data area: 64 KiB
create cc-globals-buf  cc-globals-cap allot
variable cc-globals-pos

[lit] 268435456 constant cc-bss-cap                \ bss: 256 MiB
variable cc-bss-pos
[lit] 1099511627776 constant cc-bss-flag           \ 2^40: "this slot is in the bss"

```

Global-address fixups use two parallel columns, an output patch position and a storage slot. They live either in default dictionary arrays or in a larger mapped workspace; callers always go through the active pointers, so the choice is made once:

| Name | Role |
|---|---|
| `cc-gfixup-default-cap` | capacity of the default columns |
| `cc-gfixup-default-out-pos`, `cc-gfixup-default-slot` | default column buffers |
| `cc-gfixup-limit`, `cc-gfixup-out-pos-buffer`, `cc-gfixup-slot-buffer` | active capacity and column pointers |
| `cc-gfixup-cap`, `cc-gfixup-out-pos`, `cc-gfixup-slot` | accessors through the active pointers |
| `cc-gfixup-direct-cap`, `cc-gfixup-direct-base` | capacity and cached mapping of the larger workspace |
| `cc-gfixup-direct-workspace`, `cc-gfixup-default-workspace` | workspace selectors |
| `cc-gfixup-count` | occupied rows |

The default columns and accessors come first (`forth-bootstrap/cc/090-cc-emit.fth:1132`):

```forth file=cc/090-cc-emit.fth
\ Capacity for deferred global-vaddr fixups (each use of a global's name
\ is one).  M2-Planet's source has about 1,600.
[lit] 16384 constant cc-gfixup-default-cap
variable cc-gfixup-limit
cc-gfixup-default-cap cc-gfixup-limit !
: cc-gfixup-cap ( -- entries ) cc-gfixup-limit @ ;
create cc-gfixup-default-out-pos cc-gfixup-default-cap [lit] 8 * allot
variable cc-gfixup-out-pos-buffer
cc-gfixup-default-out-pos cc-gfixup-out-pos-buffer !
: cc-gfixup-out-pos ( -- address ) cc-gfixup-out-pos-buffer @ ;
create cc-gfixup-default-slot cc-gfixup-default-cap [lit] 8 * allot
variable cc-gfixup-slot-buffer
cc-gfixup-default-slot cc-gfixup-slot-buffer !
: cc-gfixup-slot ( -- address ) cc-gfixup-slot-buffer @ ;
```

The direct workspace, the selectors, the count and the base-vaddr variables that await placement follow (`forth-bootstrap/cc/090-cc-emit.fth:1146`):

```forth file=cc/090-cc-emit.fth
\ Complete original insn-attrtab.c needs 17,502 deferred global references.
\ Round the direct bound up to a 512-entry quantum; keep the default intact.
\ Both columns select one fixed, disjoint pair of mapped arrays.
[lit] 17920 constant cc-gfixup-direct-cap
variable cc-gfixup-direct-base
: cc-gfixup-default-workspace ( -- )
  cc-gfixup-default-cap cc-gfixup-limit !
  cc-gfixup-default-out-pos cc-gfixup-out-pos-buffer !
  cc-gfixup-default-slot cc-gfixup-slot-buffer ! ;
: cc-gfixup-direct-workspace ( -- )
  cc-gfixup-direct-base @ 0= if,
    cc-gfixup-direct-cap [lit] 16 * [lit] 81 cc-workspace-map
    cc-gfixup-direct-base !
  then,
  cc-gfixup-direct-cap cc-gfixup-limit !
  cc-gfixup-direct-base @ cc-gfixup-out-pos-buffer !
  cc-gfixup-direct-base @ cc-gfixup-direct-cap [lit] 8 * + cc-gfixup-slot-buffer ! ;
variable cc-gfixup-count

variable cc-globals-base-vaddr                   \ set by cc-finalize-globals
variable cc-bss-base-vaddr                       \ set by cc-finalize-globals

```

The capacity comments mention historical consumers. They explain sizing decisions, not a current handoff route. Chapter 37 owns global placement and fixup traversal; the emitter’s contract is to preserve the slot and patch position until then.

## Reserving slots and recording uses

A new compilation must not inherit initialized bytes or pending uses. `cc-globals-init` resets the cursors and fixup count, clears the data base, and zeroes the data buffer (`forth-bootstrap/cc/090-cc-emit.fth:1169`):

```forth file=cc/090-cc-emit.fth
\ cc-globals-init ( -- )  Reset globals + fixup state at the start of compile.
: cc-globals-init
  [lit] 0 cc-globals-pos !
  [lit] 0 cc-bss-pos !
  [lit] 0 cc-gfixup-count !
  [lit] 0 cc-globals-base-vaddr !
  \ Zero the globals buffer so uninitialized globals are guaranteed zero
  \ even if a previous run left bytes in there.  Loop walks i = 0..cap-1.
  [lit] 0
  begin, dup cc-globals-cap < while,
    [lit] 0 over cc-globals-buf + c!
    1+
  repeat, drop ;

```

| Allocator | Requested bytes → returned slot |
|---|---|
| `cc-globals-alloc` | data reservation → old data cursor |
| `cc-bss-alloc` | zero-filled reservation → old BSS cursor plus `cc-bss-flag` |

Both reservations check capacity before advancing their cursor; only the returned slot’s tag distinguishes the storage areas (`forth-bootstrap/cc/090-cc-emit.fth:1182`):

```forth file=cc/090-cc-emit.fth
\ cc-globals-alloc ( bytes -- slot )  Reserve `bytes` bytes of the data
\ area; return the offset of the first reserved byte.  Dies with 80 if
\ cc-globals-buf would overflow.
: cc-globals-alloc                                 ( bytes -- slot )
  dup cc-globals-pos @ + cc-globals-cap [lit] 80 cc-check-cap
  cc-globals-pos @                                 ( bytes slot )
  swap                                              ( slot bytes )
  cc-globals-pos +! ;

\ cc-bss-alloc ( bytes -- slot )  Reserve `bytes` zeroed bytes in the bss;
\ return the slot (cc-bss-flag + offset).  Dies with 82 past cc-bss-cap.
: cc-bss-alloc                                     ( bytes -- slot )
  dup cc-bss-pos @ + cc-bss-cap [lit] 82 cc-check-cap
  cc-bss-pos @ cc-bss-flag +                       ( bytes slot )
  swap cc-bss-pos +! ;

```

An initializer writes into the data buffer at its allocated offset. `cc-globals-store-8le` serializes a full cell there; it does not accept a tagged BSS slot (`forth-bootstrap/cc/090-cc-emit.fth:1200`):

```forth file=cc/090-cc-emit.fth
\ cc-globals-store-8le ( v slot -- )  Write `v` as 8-byte LE into globals-buf
\ at the given slot offset.
: cc-globals-store-8le                             ( v slot -- )
  cc-globals-buf +                                 ( v addr )
  >r                                                ( v ; R: addr )
  dup r@                       c!
  [lit] 256 / dup r@ 1+ c!
  [lit] 256 / dup r@ [lit] 2 + c!
  [lit] 256 / dup r@ [lit] 3 + c!
  [lit] 256 / dup r@ [lit] 4 + c!
  [lit] 256 / dup r@ [lit] 5 + c!
  [lit] 256 / dup r@ [lit] 6 + c!
  [lit] 256 /     r> [lit] 7 + c! ;

```

A reference adds one row to the active fixup columns. `cc-gfixup-add` checks the next count before writing either column, then advances the count (`forth-bootstrap/cc/090-cc-emit.fth:1214`):

```forth file=cc/090-cc-emit.fth
\ cc-gfixup-add ( patch-offset slot -- )  Record a deferred global-vaddr fixup.
\ Indexes its two parallel arrays with cell[] (030-cc-io.fth).
: cc-gfixup-add                                    ( patch-off slot -- )
  cc-gfixup-count @ 1+ cc-gfixup-cap [lit] 81 cc-check-cap
  cc-gfixup-count @                                 ( patch-off slot i )
  >r                                                \ park i on rstack
  r@ cc-gfixup-slot     cell[] !                   \ store slot
  r@ cc-gfixup-out-pos  cell[] !                   \ store patch-off
  r> drop
  [lit] 1 cc-gfixup-count +! ;

```

`cc-emit-global-ref` joins emission to bookkeeping: its empty absolute-address field is paired with the caller’s slot, so later placement can recover both what to patch and where. As in the earlier wide-immediate helper, the opcode is `B8 + 7 = BF`, despite the copied `B7` annotation (`forth-bootstrap/cc/090-cc-emit.fth:1227`):

```forth file=cc/090-cc-emit.fth
\ cc-emit-global-ref ( slot -- )  Emit `movabs rdi, <vaddr placeholder>` and
\ record a deferred fixup so the imm64 will be patched to the slot's
\ address once globals are placed.  Used by the sk-global IDENT path in
\ cc-parse-primary.
: cc-emit-global-ref                                ( slot -- )
  [lit]  72 cc-emit-byte                            \ REX.W (0x48)
  [lit] 191 cc-emit-byte                            \ B7 + 7 = BF (movabs rdi)
  cc-out-pos @                                      ( slot patch-off )
  [lit] 0 cc-emit-8le                               \ imm64 placeholder
  swap cc-gfixup-add ;
```

For a data slot, the eventual address is `cc-globals-base-vaddr + slot`. For a BSS slot it is `cc-bss-base-vaddr + slot - cc-bss-flag`. Emission records these inputs without predicting how much code will precede the storage.

## LP64 integer encoders

Typed emission separates storage width from register value. The initial `cc-emit-type-check-fwd` target, `cc-emit-type-check-noop`, leaves the type untouched so integer encoders can proceed; the deferred hook allows a later layer to enforce more restrictions (`forth-bootstrap/cc/090-cc-emit.fth:1244`):

```forth file=cc/090-cc-emit.fth

\ ===========================================================================
\ Opt-in LP64 integer encoders.
\ ===========================================================================
\ The original words above stay byte-identical.  The typed wrappers retain
\ their legacy encodings while cc-target-lp64 is 0.  Scalar floating types
\ have storage sizes in 060, but these words implement integer operations.
\ A typed store writes only the destination width; use convert-rdi first
\ when the assignment expression must retain a correctly converted result.

\ cc-emit-load-typed-via-rdi ( ty -- )  rdi := *(T *)rdi.
: cc-emit-type-check-noop ;
defer cc-emit-type-check-fwd
' cc-emit-type-check-noop is cc-emit-type-check-fwd

```

`cc-emit-load-typed-via-rdi` selects both width and extension: signed narrow loads propagate the sign, unsigned loads clear the high bits, and a full-width load needs no extension (`forth-bootstrap/cc/090-cc-emit.fth:1248`):

```forth file=cc/090-cc-emit.fth
: cc-emit-load-typed-via-rdi
  cc-emit-type-check-fwd
  dup ty-size [lit] 1 = if,
    ty-unsigned? if, cc-emit-load-byte-via-rdi else,
      [lit] 72 cc-emit-byte [lit] 15 cc-emit-byte
      [lit] 190 cc-emit-byte [lit] 63 cc-emit-byte  \ movsx rdi, byte [rdi]
    then, exit,
  then,
  dup ty-size [lit] 2 = if,
    [lit] 72 cc-emit-byte [lit] 15 cc-emit-byte
    ty-unsigned? if, [lit] 183 else, [lit] 191 then, cc-emit-byte
    [lit] 63 cc-emit-byte exit,                    \ movzx/movsx rdi, word [rdi]
  then,
  dup ty-size [lit] 4 = if,
    ty-unsigned? if,
      [lit] 139 cc-emit-byte [lit] 63 cc-emit-byte  \ mov edi, [rdi]
    else,
      [lit] 72 cc-emit-byte [lit] 99 cc-emit-byte
      [lit] 63 cc-emit-byte                       \ movsxd rdi, dword [rdi]
    then, exit,
  then,
  drop cc-emit-load-via-rdi ;

```

`cc-emit-store-typed-via-rcx` writes only the destination width and preserves `rdi`. It therefore cannot by itself make the retained assignment value match a narrowed destination (`forth-bootstrap/cc/090-cc-emit.fth:1272`):

```forth file=cc/090-cc-emit.fth
\ cc-emit-store-typed-via-rcx ( ty -- )  *(T *)rcx := rdi.
: cc-emit-store-typed-via-rcx
  cc-emit-type-check-fwd
  ty-size
  dup [lit] 1 = if, drop cc-emit-store-byte-via-rcx exit, then,
  dup [lit] 2 = if,
    drop [lit] 102 cc-emit-byte [lit] 137 cc-emit-byte
    [lit] 57 cc-emit-byte exit,                    \ mov word [rcx], di
  then,
  [lit] 4 = if,
    [lit] 137 cc-emit-byte [lit] 57 cc-emit-byte    \ mov dword [rcx], edi
  else, cc-emit-store-via-rcx then, ;

```

`cc-emit-convert-rdi` supplies that missing conversion by narrowing the register value and extending it according to destination signedness. A full-width destination requires no emitted instruction (`forth-bootstrap/cc/090-cc-emit.fth:1285`):

```forth file=cc/090-cc-emit.fth
\ cc-emit-convert-rdi ( ty -- )  Truncate/sign-extend the integer in rdi.
: cc-emit-convert-rdi
  cc-emit-type-check-fwd
  dup ty-size [lit] 1 = if,
    ty-unsigned? if, cc-emit-zx-byte-rdi else,
      [lit] 72 cc-emit-byte [lit] 15 cc-emit-byte
      [lit] 190 cc-emit-byte [lit] 255 cc-emit-byte \ movsx rdi, dil
    then, exit,
  then,
  dup ty-size [lit] 2 = if,
    [lit] 72 cc-emit-byte [lit] 15 cc-emit-byte
    ty-unsigned? if, [lit] 183 else, [lit] 191 then, cc-emit-byte
    [lit] 255 cc-emit-byte exit,                   \ movzx/movsx rdi, di
  then,
  dup ty-size [lit] 4 = if,
    ty-unsigned? if,
      [lit] 137 cc-emit-byte [lit] 255 cc-emit-byte \ mov edi, edi
    else,
      [lit] 72 cc-emit-byte [lit] 99 cc-emit-byte
      [lit] 255 cc-emit-byte                      \ movsxd rdi, edi
    then, exit,
  then,
  drop ;

```

## Conversion hooks and typed locals

Width and signedness conversion do not cover every scalar rule. In
particular, `_Bool` must turn any nonzero value into 1 rather than truncate
it to one byte. Chapter 47 supplies that nonzero test through the later
value-conversion hook.

`cc-emit-convert-value` leaves room for later value representations. Its initial target, `cc-emit-convert-value-default`, discards the source type and converts `rdi` using the destination type (`forth-bootstrap/cc/090-cc-emit.fth:1309`):

```forth file=cc/090-cc-emit.fth
\ Conversions with source type preserve the integer emitter by default.
: cc-emit-convert-value-default ( source destination -- ) nip cc-emit-convert-rdi ;
defer cc-emit-convert-value
' cc-emit-convert-value-default is cc-emit-convert-value

```

The right operand needs the same normalization independently. `cc-emit-convert-rcx` applies the destination width and signedness to `rcx` without replacing the left operand (`forth-bootstrap/cc/090-cc-emit.fth:1314`):

```forth file=cc/090-cc-emit.fth
\ cc-emit-convert-rcx ( ty -- )  Same conversion for the right operand.
: cc-emit-convert-rcx
  cc-emit-type-check-fwd
  dup ty-size [lit] 1 = if,
    [lit] 72 cc-emit-byte [lit] 15 cc-emit-byte
    ty-unsigned? if, [lit] 182 else, [lit] 190 then, cc-emit-byte
    [lit] 201 cc-emit-byte exit,                   \ movzx/movsx rcx, cl
  then,
  dup ty-size [lit] 2 = if,
    [lit] 72 cc-emit-byte [lit] 15 cc-emit-byte
    ty-unsigned? if, [lit] 183 else, [lit] 191 then, cc-emit-byte
    [lit] 201 cc-emit-byte exit,                   \ movzx/movsx rcx, cx
  then,
  dup ty-size [lit] 4 = if,
    ty-unsigned? if,
      [lit] 137 cc-emit-byte [lit] 201 cc-emit-byte \ mov ecx, ecx
    else,
      [lit] 72 cc-emit-byte [lit] 99 cc-emit-byte
      [lit] 201 cc-emit-byte                      \ movsxd rcx, ecx
    then, exit,
  then,
  drop ;

```

`cc-emit-convert-right` initially targets `cc-emit-convert-right-default`, which discards the source type before converting `rcx`. `cc-emit-load-local-typed` selects typed memory access under `cc-target-lp64` and keeps the legacy local load otherwise (`forth-bootstrap/cc/090-cc-emit.fth:1336`):

```forth file=cc/090-cc-emit.fth
: cc-emit-convert-right-default ( source destination -- ) nip cc-emit-convert-rcx ;
defer cc-emit-convert-right
' cc-emit-convert-right-default is cc-emit-convert-right

\ cc-emit-load-local-typed ( slot ty -- )  LP64 memory width, legacy qword.
: cc-emit-load-local-typed
  cc-target-lp64 @ if,
    swap cc-emit-lea-rdi-local cc-emit-load-typed-via-rdi
  else, drop cc-emit-load-local then, ;

```

`cc-emit-store-local-typed` similarly selects a narrow memory instruction only in LP64 mode, preserving the register value and delegating displacement selection to the existing local-address helper (`forth-bootstrap/cc/090-cc-emit.fth:1347`):

```forth file=cc/090-cc-emit.fth
\ cc-emit-store-local-typed ( slot ty -- )  rdi is preserved.
: cc-emit-store-local-typed
  cc-emit-type-check-fwd
  cc-target-lp64 @ 0= if, drop cc-emit-store-local exit, then,
  ty-size
  dup [lit] 1 = if,
    drop [lit] 64 cc-emit-byte [lit] 136 cc-emit-byte
    [lit] 125 cc-emit-local-ea exit,               \ mov byte [rbp+disp], dil
  then,
  dup [lit] 2 = if,
    drop [lit] 102 cc-emit-byte [lit] 137 cc-emit-byte
    [lit] 125 cc-emit-local-ea exit,               \ mov word [rbp+disp], di
  then,
  [lit] 4 = if,
    [lit] 137 cc-emit-byte [lit] 125 cc-emit-local-ea
  else, cc-emit-store-local then, ;

```

These are integer encoders even when a type record can describe a floating value. Chapter 39 develops LP64 storage and initializers; Chapter 47 supplies floating-value operations.

## Unsigned arithmetic results

Operands must already have their common integer type before these operations run:

| Emitter | Converted operands → result in `rdi` |
|---|---|
| `cc-emit-udiv-quotient` | dividend, divisor → unsigned quotient |
| `cc-emit-udiv-remainder` | dividend, divisor → unsigned remainder |
| `cc-emit-cmp-ult` | left, right → unsigned less-than truth value |
| `cc-emit-cmp-uge` | left, right → unsigned greater-or-equal truth value |
| `cc-emit-cmp-ule` | left, right → unsigned less-or-equal truth value |
| `cc-emit-cmp-ugt` | left, right → unsigned greater-than truth value |
| `cc-emit-shr-rdi-cl` | value, count → zero-filling right shift |

Unsigned division clears the high dividend instead of sign-extending it, then selects either quotient or remainder for the accumulator (`forth-bootstrap/cc/090-cc-emit.fth:1363`):

```forth file=cc/090-cc-emit.fth
\ Unsigned division clears rdx, then DIV rcx uses the full rdx:rax dividend.
\ Both operands must already have been converted to the common C type.
: cc-emit-udiv-quotient
  cc-emit-mov-rax-rdi
  [lit] 49 cc-emit-byte [lit] 210 cc-emit-byte      \ xor edx, edx
  [lit] 72 cc-emit-byte [lit] 247 cc-emit-byte [lit] 241 cc-emit-byte
  cc-emit-mov-rdi-rax ;                            \ div rcx; mov rdi, rax

: cc-emit-udiv-remainder
  cc-emit-mov-rax-rdi
  [lit] 49 cc-emit-byte [lit] 210 cc-emit-byte
  [lit] 72 cc-emit-byte [lit] 247 cc-emit-byte [lit] 241 cc-emit-byte
  [lit] 72 cc-emit-byte [lit] 137 cc-emit-byte [lit] 215 cc-emit-byte ;

```

Unsigned comparisons reuse the comparison emitter with unsigned condition codes; logical right shift fills with zeros where the earlier arithmetic shift copied the sign (`forth-bootstrap/cc/090-cc-emit.fth:1377`):

```forth file=cc/090-cc-emit.fth
: cc-emit-cmp-ult [lit] 146 cc-emit-cmp-set ;       \ setB
: cc-emit-cmp-uge [lit] 147 cc-emit-cmp-set ;       \ setAE
: cc-emit-cmp-ule [lit] 150 cc-emit-cmp-set ;       \ setBE
: cc-emit-cmp-ugt [lit] 151 cc-emit-cmp-set ;       \ setA

\ Logical (unsigned) right shift: shr rdi, cl = 48 D3 EF.
: cc-emit-shr-rdi-cl
  [lit] 72 cc-emit-byte [lit] 211 cc-emit-byte [lit] 239 cc-emit-byte ;
```

## Try it

Run from the `forth-bootstrap` checkout root. This driver loads the library and compiler layers through all of `090-cc-emit.fth`, emits into the output buffer, and finalizes the ELF header. It uses no C parser.

Each call placeholder is prepended to `calls`. After emitting the program’s exit path, `patch-calls` walks the list and targets the current output position, where `cc-emit-putchar-shim` is about to emit its body. The program calls that body to print `**`, then exits before it can fall through into the shim.

The shell captures the executable in a fresh temporary directory, runs it, and removes the directory:

<!-- tryit: expect "driver exit: 0\n**\nprogram exit: 0" -->
```sh
(
set -o pipefail
probe_dir=$(mktemp -d /tmp/book-probe.XXXXXXXXXX) || exit "$?"
trap 'status=$?; rm -rf -- "$probe_dir" || status=1; exit "$status"' EXIT
compiler_status=0
{
  cat forth/010-lib.fth cc/020-cc-arena.fth cc/030-cc-io.fth \
      cc/040-cc-prep.fth cc/050-cc-lex.fth \
      cc/060-cc-types.fth cc/070-cc-sym.fth \
      cc/080-cc-elf.fth cc/090-cc-emit.fth || exit "$?"
  cat <<'FORTH' || exit "$?"
variable calls
: patch-calls
  calls @ begin, dup while,
    dup @ cc-patch-rel32-to-here
    [lit] 8 + @
  repeat, drop ;
cc-out-init [lit] 0 cc-bss-size ! cc-emit-elf-header
[lit] 0 calls !
[lit] 42 cc-emit-mov-rdi-int
cc-emit-call-rel32-placeholder calls cc-add-fixup-to-list
[lit] 42 cc-emit-mov-rdi-int
cc-emit-call-rel32-placeholder calls cc-add-fixup-to-list
[lit] 0 cc-emit-mov-rdi-int cc-emit-exit-shim
patch-calls cc-emit-putchar-shim
cc-finalize-elf
[lit] 1 cc-out-buf cc-out-pos @ write drop
bye
FORTH
} | ./seed-forth > "$probe_dir/stars" || compiler_status=$?
printf 'driver exit: %s\n' "$compiler_status" # prints 'driver exit: 0'
test "$compiler_status" -eq 0 || exit "$compiler_status"
chmod +x "$probe_dir/stars" || exit "$?"
program_status=0
"$probe_dir/stars" || program_status=$? # prints '**'
printf '\nprogram exit: %s\n' "$program_status" # prints '\nprogram exit: 0'
test "$program_status" -eq 0
)
```

Observed output:

```text
driver exit: 0
**
program exit: 0
```

This exercises multiple forward-call nodes, list traversal, integer emission, and the output and exit shims. It does not test every shim, string decoding, global fixups, or the typed encoders.

## Exercise

Hints and feedback are in [Appendix H](66-exercise-feedback.md#chapter-32-fixup-lists-and-shim-limits).

**Trace — easy.** Name the head and next node after each call is recorded in the checkpoint. Explain why walking the list in reverse emission order still patches both calls to the same shim.

**Trace — moderate.** Follow `fopen` for mode strings `rb` and `r+`. Identify the byte it examines and explain which requested behavior the shim ignores.

