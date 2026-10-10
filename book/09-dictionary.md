# Chapter 9 — The dictionary and token reader

When the seed reads the name `dup`, it walks a linked list of word headers until a name matches, then runs the code behind it. The dictionary puts a linked header before each word's instructions, and the token reader supplies the names to search for. Together they let you trace that search, execute its result, and use the allocation cursor to store a cell.

## The header layout

A dictionary entry has this shape: **link → flags → name length → name bytes → code**. The arrows here mean consecutive fields in memory. The link itself points to an older entry; the last link is zero. Recall the system-variable cells from Chapter 5: `LATEST` supplies the head of this chain.

The search uses **newest-first lookup**. It starts at `LATEST`, compares a name, and follows the link on a mismatch. If names repeat, the newest matching entry wins. Chapter 10 builds new entries.

The header for `find` shows these fields before any instructions (`forth-bootstrap/seed/000-seed.hex0:320`).

```hex0 chunk=find
;; --- find @ 0x2F5 --- header
BE 02 40 00 00 00 00 00                   ; link  = 0x4002BE (syscall6)
00                                        ; flags = 0
04                                        ; nlen  = 4
66 69 6E 64                               ; name  = "find"
```

The link occupies a cell. The flags byte is at offset 8, the name-length byte at offset 9, and the name starts at offset 10. Here the name length is 4. The instructions start immediately after `find`'s name; there is no separate code-pointer field.

That address is the **execution token**, abbreviated **xt**. For a header at address `h` with name length `n`, its xt is `h + 10 + n`. A header address identifies the metadata; an xt identifies the instructions. Confusing them would make the processor execute a link as machine code.

## `find_code`: compare, follow, return

`find` consumes `( c-addr u )`, the address and length of a name, and returns an xt or zero. It compares lengths before touching the name bytes. `u` arrives in `rdi`, with `c-addr` underneath it.

A length mismatch rules out an entry without comparing bytes. `find_code` loads the chain head and checks each candidate length (`forth-bootstrap/seed/000-seed.hex0:325`).

```hex0 chunk=find
;; ----- find_code @ 0x303  ( c-addr u -- xt | 0 ) -----
;; Walks the chain from LATEST.  On a hit, stores the entry's address in
;; LAST_FOUND (the REPL reads its flags byte) and returns the xt: the
;; first byte after the name, which is where the word's code starts.
48 8B 75 00                               ; mov rsi, [rbp]     ; rsi = c-addr
48 83 C5 08                               ; add rbp, 8         ; pop it; rdi = u
48 8B 0C 25 08 30 41 00                   ; mov rcx, [LATEST]  ; rcx = newest entry
;; .next:
48 85 C9                                  ; test rcx, rcx
74 3D                                     ; jz .miss  (rel8 = 0x355 - 0x318)      ; link 0: end of chain
48 0F B6 41 09                            ; movzx rax, byte [rcx+9] ; nlen
48 39 F8                                  ; cmp rax, rdi
75 2E                                     ; jne .skip  (rel8 = 0x350 - 0x322)     ; lengths differ
48 89 FA                                  ; mov rdx, rdi       ; rdx = bytes left to compare
4C 8D 41 0A                               ; lea r8, [rcx+10]   ; r8 = entry's name
49 89 F1                                  ; mov r9, rsi        ; r9 = token
```

`rsi` keeps the caller's name address while `rcx` walks the dictionary. A zero `rcx` means the chain has ended. For equal lengths, `rdx` becomes the remaining count, `r8` points into the entry's name, and `r9` points into the caller's name.

Equal lengths leave the bytes to check. The inner loop advances both name pointers together (`forth-bootstrap/seed/000-seed.hex0:341`).

```hex0 chunk=find
;; .bcmp:
48 85 D2                                  ; test rdx, rdx
74 13                                     ; jz .hit  (rel8 = 0x344 - 0x331)       ; every byte matched
41 8A 00                                  ; mov al, [r8]
41 3A 01                                  ; cmp al, [r9]
75 17                                     ; jne .skip  (rel8 = 0x350 - 0x339)
49 FF C0                                  ; inc r8
49 FF C1                                  ; inc r9
48 FF CA                                  ; dec rdx
EB E8                                     ; jmp .bcmp  (rel8 = 0x32C - 0x344)
```

A differing byte takes the same `.skip` path as a differing length. When the count reaches zero, `r8` has crossed the entire name and points directly at the code. No terminating NUL byte is needed or compared.

Newest-first lookup has three exits: return the code address, follow an older link, or report a miss (`forth-bootstrap/seed/000-seed.hex0:351`).

```hex0 chunk=find
;; .hit:
48 89 0C 25 18 30 41 00                   ; mov [LAST_FOUND], rcx
4C 89 C7                                  ; mov rdi, r8        ; xt = byte after the name
C3                                        ; ret
;; .skip:
48 8B 09                                  ; mov rcx, [rcx]     ; follow the link
EB BE                                     ; jmp .next  (rel8 = 0x313 - 0x355)
;; .miss:
48 31 FF                                  ; xor rdi, rdi       ; not found: 0
C3                                        ; ret

```

On a hit, `LAST_FOUND` retains the header address while the stack receives the xt. Those addresses serve different purposes: the header gives access to flags, and the xt can be executed. On a miss, `find` returns zero and leaves `LAST_FOUND` unchanged; a caller must not treat that old header as a new match.

Trace a search for `find` itself. Entries with other lengths take `.skip`. At its own header, the byte loop compares `f`, `i`, `n`, and `d`; its final `r8` points past the `d`, at `find_code`. A same-length name differing at any position still takes `.skip` and continues toward older entries.

## `here_code` and `comma_code`: append a cell

`here` returns the allocation cursor's value: the address where the next write belongs.

The load in `here_code` pushes the contents of `HERE` (`forth-bootstrap/seed/000-seed.hex0:362`).

```hex0 chunk=here
;; --- here @ 0x359 --- header
F5 02 40 00 00 00 00 00                   ; link  = 0x4002F5 (find)
00                                        ; flags = 0
04                                        ; nlen  = 4
68 65 72 65                               ; name  = "here"
;; ----- here_code @ 0x367  ( -- addr ) the value of HERE -----
48 83 ED 08                               ; sub rbp, 8
48 89 7D 00                               ; mov [rbp], rdi
48 8B 3C 25 10 30 41 00                   ; mov rdi, [HERE]
C3                                        ; ret

```

Reading `here` does not reserve space. The comma word, `,`, consumes a value and appends it at that address.

An append must also advance the cursor. `comma_code` stores the value and writes the updated address back to `HERE` (`forth-bootstrap/seed/000-seed.hex0:373`).

```hex0 chunk=comma
;; --- , @ 0x378 --- header
59 03 40 00 00 00 00 00                   ; link  = 0x400359 (here)
00                                        ; flags = 0
01                                        ; nlen  = 1
2C                                        ; name  = ","
;; ----- comma_code @ 0x383  ( v -- ) store a cell at HERE, HERE += 8 -----
48 8B 04 25 10 30 41 00                   ; mov rax, [HERE]
48 89 38                                  ; mov [rax], rdi     ; *HERE = v
48 83 C0 08                               ; add rax, 8
48 89 04 25 10 30 41 00                   ; mov [HERE], rax
48 8B 7D 00                               ; mov rdi, [rbp]
48 83 C5 08                               ; add rbp, 8
C3                                        ; ret

```

The destination advances by 8 bytes, one cell from Chapter 4. The final load and stack adjustment consume the stored value. This is an append operation, not a dictionary insertion: it does not supply a name or change `LATEST`. Chapter 10 uses the growing allocation area for definitions, and Chapter 15 builds further emission words.

## `execute`: enter the code address

An xt is useful independently of its name. `execute` consumes `( xt -- )` and enters that address with the remaining data stack available to the selected word.

The selected word needs its operands on top of the stack. `execute_code` saves the xt, then removes it from the data stack (`forth-bootstrap/seed/000-seed.hex0:387`).

```hex0 chunk=execute
;; --- execute @ 0x3A3 --- header
78 03 40 00 00 00 00 00                   ; link  = 0x400378 (,)
00                                        ; flags = 0
07                                        ; nlen  = 7
65 78 65 63 75 74 65                      ; name  = "execute"
;; ----- execute_code @ 0x3B4  ( xt -- ) tail-jump to xt -----
48 89 F8                                  ; mov rax, rdi       ; rax = xt
48 8B 7D 00                               ; mov rdi, [rbp]
48 83 C5 08                               ; add rbp, 8
FF E0                                     ; jmp rax            ; xt's ret returns to our caller

```

The final instruction is an indirect tail jump. It leaves the caller's return address on the return stack, so the selected word's `ret` returns directly to that caller. `execute` has no instruction to resume afterward. It does not check the address: zero from a failed lookup is not an executable token.

## `read_word`, the token reader

The reader's path is **skip whitespace → collect bytes → recognize comments → return the token**. `read_word` is an internal routine, not a named dictionary entry. Its `( -- c-addr u )` result fits `find`'s input exactly. The address refers to the shared token buffer from Chapter 5, so reading another token overwrites the old bytes.

Leading whitespace contributes no token bytes. `read_word` clears its length and skips it (`forth-bootstrap/seed/000-seed.hex0:398`).

```hex0 chunk=read-word
;; ----- read_word @ 0x3C1  ( -- c-addr u ) next token from stdin; u = 0 at EOF -----
;; Not a dictionary word.  Skips whitespace, then copies bytes to the
;; token buffer (TIB, 0x412800) until whitespace or EOF.  The length is
;; kept in rbx, which syscalls preserve and nothing else in the seed
;; writes, so report_token can still find it after find or [lit] fails.
;; A token that is exactly \ skips to the end of the line, and one that
;; is exactly ( skips past the next ); either way reading starts over.
;; A token longer than 255 bytes (too long for nlen) is fatal.
31 DB                                     ; xor ebx, ebx       ; rbx = length = 0
;; .skip_ws:
E8 6E 00 00 00                            ; call read_char  (rel32 = 0x436 - 0x3C8)
74 F9                                     ; je .skip_ws  (rel8 = 0x3C3 - 0x3CA)   ; whitespace: keep skipping
85 D2                                     ; test edx, edx
74 4F                                     ; jz .done  (rel8 = 0x41D - 0x3CE)      ; EOF before a token: u = 0
```

The helper `read_char` returns a byte in `rdx` and a whitespace verdict in the zero flag. An immediate `je` uses that verdict. The separate `test edx, edx` detects end of input; before any token bytes, it leads to a zero-length result.

`rbx` holds the length across helper calls. That length also survives a failed lookup for use in error reporting.

A token must fit the header's name-length field. The collection loop checks the count after each stored byte (`forth-bootstrap/seed/000-seed.hex0:412`).

```hex0 chunk=read-word
;; .store:
88 93 00 28 41 00                         ; mov [rbx+0x412800], dl ; TIB[len] = byte
FF C3                                     ; inc ebx
84 FF                                     ; test bh, bh        ; length >= 256?
0F 85 99 00 00 00                         ; jnz fatal_token  (rel32 = 0x477 - 0x3DE) ; too long: report and exit
E8 53 00 00 00                            ; call read_char  (rel32 = 0x436 - 0x3E3)
74 04                                     ; je .end  (rel8 = 0x3E9 - 0x3E5)       ; whitespace ends the token
85 D2                                     ; test edx, edx
75 E5                                     ; jnz .store  (rel8 = 0x3CE - 0x3E9)    ; not EOF: keep the byte
```

`bh` becomes nonzero when the count reaches 256, so the reader accepts at most 255 bytes. It stores the byte that crosses the limit before entering `fatal_token`. A delimiter ends collection without becoming part of the name. EOF after some bytes also completes that token.

## Comments are recognized as tokens

A comment opener must stand alone. A token beginning with `(` or `\` is not enough; the entire token must be that single character.

The completed-token check tests the length before looking for an opening character (`forth-bootstrap/seed/000-seed.hex0:421`).

```hex0 chunk=read-word
;; .end:
;; The token is complete; dl holds the byte that ended it (0 = EOF).
83 FB 01                                  ; cmp ebx, 1
75 2F                                     ; jne .done  (rel8 = 0x41D - 0x3EE)     ; comment markers are 1 byte long
8A 04 25 00 28 41 00                      ; mov al, [0x412800]
3C 5C                                     ; cmp al, 0x5C       ; '\'
74 14                                     ; je .line_comment  (rel8 = 0x40D - 0x3F9)
3C 28                                     ; cmp al, 0x28       ; '('
75 20                                     ; jne .done  (rel8 = 0x41D - 0x3FD)
```

For example, `(note` is an ordinary name, whereas `( note )` begins a comment. The opening marker has already consumed its following delimiter. Parenthesized comments do not nest.

The parenthesized-comment loop discards bytes through the next closing parenthesis (`forth-bootstrap/seed/000-seed.hex0:430`).

```hex0 chunk=read-word
;; .paren_comment:
E8 34 00 00 00                            ; call read_char  (rel32 = 0x436 - 0x402)
85 D2                                     ; test edx, edx
74 BB                                     ; jz read_word  (rel8 = 0x3C1 - 0x406)  ; EOF: start over (and return u = 0)
80 FA 29                                  ; cmp dl, 0x29       ; ')'
75 F2                                     ; jne .paren_comment  (rel8 = 0x3FD - 0x40B)
EB B4                                     ; jmp read_word  (rel8 = 0x3C1 - 0x40D) ; comment over: read the next token
```

The jump back to `read_word` resets the token length and starts another search for input. EOF takes the same restart path, which then returns an empty token.

A line-comment opener may have already consumed a newline. Checking the existing `dl` before reading again keeps the next line out of the comment (`forth-bootstrap/seed/000-seed.hex0:437`).

```hex0 chunk=read-word
;; .line_comment:
80 FA 0A                                  ; cmp dl, 0x0A       ; reached the newline?
74 AF                                     ; je read_word  (rel8 = 0x3C1 - 0x412)  ; comment over: read the next token
85 D2                                     ; test edx, edx
74 AB                                     ; jz read_word  (rel8 = 0x3C1 - 0x416)  ; EOF: start over (and return u = 0)
E8 1B 00 00 00                            ; call read_char  (rel32 = 0x436 - 0x41B)
EB F0                                     ; jmp .line_comment  (rel8 = 0x40D - 0x41D)
```

This is why a line containing only `\` still ends its comment at that line's boundary. Both comment paths discard their contents and restart token reading.

Every completed name takes the shared return path, which pushes the buffer address followed by the length (`forth-bootstrap/seed/000-seed.hex0:444`).

```hex0 chunk=read-word
;; .done:
48 83 ED 08                               ; sub rbp, 8
48 89 7D 00                               ; mov [rbp], rdi
BF 00 28 41 00                            ; mov edi, 0x412800  ; push c-addr = TIB
48 83 ED 08                               ; sub rbp, 8
48 89 7D 00                               ; mov [rbp], rdi
48 89 DF                                  ; mov rdi, rbx       ; push u
C3                                        ; ret

```

At return, the length is in `rdi`, and the address is underneath it. Comment text never reaches the caller as a name.

## `read_char`: a byte and a verdict

Recall `key` from Chapter 8. The token reader needs its byte in a register without leaving a new item on the data stack.

`read_char` moves the result off the stack and compares it against the accepted whitespace characters (`forth-bootstrap/seed/000-seed.hex0:453`).

```hex0 chunk=read-char
;; ----- read_char @ 0x436  ( -- ) rdx = next input byte (0 at EOF); ZF=1 iff whitespace -----
E8 54 FE FF FF                            ; call key_code  (rel32 = 0x28F - 0x43B) ; ( -- c )
48 89 FA                                  ; mov rdx, rdi       ; rdx = c
48 8B 7D 00                               ; mov rdi, [rbp]
48 83 C5 08                               ; add rbp, 8
80 FA 20                                  ; cmp dl, 0x20       ; space
74 0D                                     ; je .ret  (rel8 = 0x458 - 0x44B)
80 FA 09                                  ; cmp dl, 0x09       ; tab
74 08                                     ; je .ret  (rel8 = 0x458 - 0x450)
80 FA 0A                                  ; cmp dl, 0x0A       ; newline
74 03                                     ; je .ret  (rel8 = 0x458 - 0x455)
80 FA 0D                                  ; cmp dl, 0x0D       ; carriage return
;; .ret:
C3                                        ; ret                ; ret leaves the flags alone

```

Space, tab, newline, and carriage return set the zero flag. The matching branch reaches `ret` without changing that flag. A nonmatching byte leaves it clear after the final comparison. This flag is part of the helper's return contract, so its caller must branch before another instruction overwrites it.

EOF is zero, which matches none of those characters. The reader also treats an input NUL as end of input, because `key` returns the same value for it.

## `report_token` and `fatal_token`: failing out loud

The reader retains both the token bytes and their length. A diagnostic can use them even after `find` has consumed the address-length pair.

The diagnostic prints the failed token. `report_token` appends a question mark and newline, then writes the buffer (`forth-bootstrap/seed/000-seed.hex0:468`).

```hex0 chunk=report-token
;; ----- report_token @ 0x459  ( -- ) write the last token and '?' newline to stdout -----
;; Uses rbx (the token length).  Clobbers rdi, so callers drop or exit.
66 C7 83 00 28 41 00 3F 0A                ; mov word [rbx+0x412800], 0x0A3F ; append '?' and newline
8D 53 02                                  ; lea edx, [rbx+2]   ; count = len + 2
BE 00 28 41 00                            ; mov esi, 0x412800  ; buf = TIB
B8 01 00 00 00                            ; mov eax, 1         ; SYS_write
BF 01 00 00 00                            ; mov edi, 1         ; fd 1 (stdout)
0F 05                                     ; syscall
C3                                        ; ret

```

Recall the Linux call convention from Chapter 4 and output calls from Chapter 8. This helper writes to stdout and clobbers `rdi`; it does not restore the Forth stack top. Its caller must account for that before continuing.

An overlong token cannot be returned as a name. `fatal_token` reports the retained bytes and exits (`forth-bootstrap/seed/000-seed.hex0:478`).

```hex0 chunk=report-token
;; ----- fatal_token @ 0x477  ( -- ) report the last token, then exit(2) -----
E8 DD FF FF FF                            ; call report_token  (rel32 = 0x459 - 0x47C)
B8 3C 00 00 00                            ; mov eax, 60        ; SYS_exit
BF 02 00 00 00                            ; mov edi, 2         ; status 2: bad input
0F 05                                     ; syscall

```

The exit status is 2. Unlike an ordinary `find` miss, which just returns zero, exceeding the reader's limit terminates the process. Chapter 12 traces the REPL's use of token reading, lookup, and diagnostics.

## `state` and `latest`: addresses of system variables

Recall `@` and `!` from Chapter 6. They need a cell's address to read or change its value.

`state_code` exposes the mode cell by pushing the address of `STATE` (`forth-bootstrap/seed/000-seed.hex0:484`).

```hex0 chunk=state
;; --- state @ 0x488 --- header
A3 03 40 00 00 00 00 00                   ; link  = 0x4003A3 (execute)
00                                        ; flags = 0
05                                        ; nlen  = 5
73 74 61 74 65                            ; name  = "state"
;; ----- state_code @ 0x497  ( -- addr ) address of the STATE sysvar -----
48 83 ED 08                               ; sub rbp, 8
48 89 7D 00                               ; mov [rbp], rdi
48 BF 00 30 41 00 00 00 00 00             ; mov rdi, 0x413000  ; &STATE (movabs)
C3                                        ; ret

```

`state @` reads the mode; `state` alone leaves its address. Chapter 10 handles changes for compilation, and Chapter 12 uses the mode in the REPL.

The dictionary head is accessible the same way: `latest_code` pushes the address of `LATEST` (`forth-bootstrap/seed/000-seed.hex0:495`).

```hex0 chunk=latest
;; --- latest @ 0x4AA --- header
88 04 40 00 00 00 00 00                   ; link  = 0x400488 (state)
00                                        ; flags = 0
06                                        ; nlen  = 6
6C 61 74 65 73 74                         ; name  = "latest"
;; ----- latest_code @ 0x4BA  ( -- addr ) address of the LATEST sysvar -----
48 83 ED 08                               ; sub rbp, 8
48 89 7D 00                               ; mov [rbp], rdi
48 BF 08 30 41 00 00 00 00 00             ; mov rdi, 0x413008  ; &LATEST (movabs)
C3                                        ; ret

```

`latest @` yields the newest header address. By contrast, `here` already fetches its system-variable cell. Adding `@` after `here` would read the allocation area itself.

## `tick_code`: read a name and find its xt

The word `'`, pronounced *tick*, connects the reader to lookup. It consumes the next input token as a name and leaves the corresponding xt, or zero if no entry matches.

The stack contracts fit without rearrangement. `tick_code` calls the reader and tail-jumps to `find_code` (`forth-bootstrap/seed/000-seed.hex0:506`).

```hex0 chunk=tick
;; --- ' @ 0x4CD --- header
AA 04 40 00 00 00 00 00                   ; link  = 0x4004AA (latest)
00                                        ; flags = 0
01                                        ; nlen  = 1
27                                        ; name  = "'"
;; ----- tick_code @ 0x4D8  ( -- xt | 0 ) read the next token and find it -----
E8 E4 FE FF FF                            ; call read_word  (rel32 = 0x3C1 - 0x4DD) ; ( -- c-addr u )
E9 21 FE FF FF                            ; jmp find_code  (rel32 = 0x303 - 0x4E2) ; ( c-addr u -- xt | 0 ), tail call

```

The reader produces `( c-addr u )`; lookup consumes that pair. The tail jump lets `find` return directly to tick's caller. Thus `' dup` obtains the code address without executing `dup`. Comments between tick and the name are skipped by the same reader.

## Try it

From the book repository, run `cd forth-bootstrap`, then build the complete seed:

```sh
./seed/build.sh
```

The build run printed:

```text
Built seed-forth (1772 bytes) using vendor/stage0-posix/bootstrap-seeds/POSIX/AMD64/hex0-seed
```

Stay in that directory for the checkpoint. The byte `0x48` begins `dup_code`: it is the REX.W prefix of the first instruction, `sub rbp, 8` (Chapter 6; `forth-bootstrap/seed/000-seed.hex0:82`). Recall `c@` from Chapter 6 and `emit` from Chapter 8: reading and emitting that byte prints `H`. This gives a visible value without numeric-input words from later chapters.

The first input line uses tick to skip a parenthesized comment, find `dup`, and call `emit` through `execute`. The next looks up a missing name. Adding its zero result leaves the known byte unchanged. The third stores that byte as a cell at `here` and reads it back. The last pair of lines uses tick to skip a line comment before finding `dup`.

```sh
printf '%s\n' "' ( skipped ) dup c@ ' emit execute" \
  "' absent ' dup c@ + emit" \
  "here dup ' dup c@ , @ emit" \
  "' \ skipped" \
  "dup c@ emit bye" | ./seed-forth
# prints "HHHH"
```

Observed output, with no trailing newline:

```text
HHHH
```

## Exercises

- **Trace — easy.** Trace a lookup with a matching length but a different final byte. Which registers still identify the original input when `.skip` follows the next link?
- **Trace — easy.** Compare the inputs `' (skipped` and `' ( skipped ) dup`. Which name does tick pass to lookup in each case, and which result is safe to pass to `execute`?
- **Trace — medium.** In the checkpoint's allocation command, track the saved address through `,` and `@`. Why does the store change `HERE` without adding a searchable word?
