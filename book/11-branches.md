# Chapter 11 — Branches and inline cells

`0branch` is how compiled code chooses: it jumps when the top of the stack is zero and falls through otherwise. A branch takes its destination from an
inline cell. By the end, you can trace `branch` and `0branch` through both
stacks and run a definition that takes or declines a branch.

## The compiled shape

Recall the inline-cell convention from Chapter 10 (The colon compiler).
For a branch, the cell holds an absolute destination address. The runtime
shape follows the entry contract in `forth-bootstrap/seed/000-seed.hex0:607`:

```text
caller body:
    CALL branch or 0branch
slot:
    destination address
fall-through:
    next instruction
```

Call the cell's address `slot` and its contents `target`. At primitive
entry, the return address is `slot`. The unconditional branch selects
`target`; the conditional branch selects either `target` or `slot + 8`.
The destination cell is data, so neither path may execute it as instructions.
The destination is an address, not a distance: a backward branch and a
forward branch need the same runtime code.

<a id="branch"></a>

## `branch_code`: replace the return address

The unconditional form needs no data-stack operand. Its dictionary header
and complete body are in `forth-bootstrap/seed/000-seed.hex0:602`:

```hex0 chunk=branch
;; --- branch @ 0x601 --- header
B2 05 40 00 00 00 00 00                   ; link  = 0x4005B2 ([lit])
00                                        ; flags = 0
06                                        ; nlen  = 6
62 72 61 6E 63 68                         ; name  = "branch"
;; ----- branch_code @ 0x611  ( -- ) jump to the address in the inline cell -----
58                                        ; pop rax            ; rax = the cell's address
48 8B 00                                  ; mov rax, [rax]     ; rax = the target
50                                        ; push rax
C3                                        ; ret                ; 'return' to the target

```

`58` pops `slot` into `rax`. The load `48 8B 00` replaces that address
with the cell's contents, `target`. Finally, `50 C3` pushes `target` and
executes `ret`, transferring control there. No instruction changes `rdi`
or `rbp`, so the data stack is unchanged.

The dereference is essential. Returning to `slot` would execute the
address bytes as machine instructions. Loading `[rax]` selects the code
those bytes name.

<a id="0branch"></a>

## `zbranch_code`: consume the flag and choose

A conditional branch must remove its flag whichever path it takes. The
body saves the flag before selecting the destination
(`forth-bootstrap/seed/000-seed.hex0:613`):

```hex0 chunk=zbranch
;; --- 0branch @ 0x617 --- header
01 06 40 00 00 00 00 00                   ; link  = 0x400601 (branch)
00                                        ; flags = 0
07                                        ; nlen  = 7
30 62 72 61 6E 63 68                      ; name  = "0branch"
;; ----- zbranch_code @ 0x628  ( flag -- ) jump to the inline cell's target if flag = 0 -----
48 89 FA                                  ; mov rdx, rdi       ; rdx = flag
48 8B 7D 00                               ; mov rdi, [rbp]
48 83 C5 08                               ; add rbp, 8
58                                        ; pop rax            ; rax = the cell's address
48 85 D2                                  ; test rdx, rdx
75 05                                     ; jnz .skip  (rel8 = 0x63E - 0x639)
48 8B 00                                  ; mov rax, [rax]     ; flag = 0: rax = the target
EB 04                                     ; jmp .push  (rel8 = 0x642 - 0x63E)
;; .skip:
48 83 C0 08                               ; add rax, 8         ; flag != 0: step past the cell
;; .push:
50                                        ; push rax
C3                                        ; ret

```

The opening `mov rdx, rdi` preserves the flag while the following load and
`add rbp, 8` consume it. `pop rax` then obtains `slot`. Thus the data
stack has already lost its flag before the conditional jump runs.

`48 85 D2` tests `rdx` against itself without changing it. A zero flag
sets ZF; a nonzero flag clears ZF. The following `75 05` is `jnz .skip`,
so a nonzero flag takes the native jump to `.skip`. That is the
*fall-through* case for the Forth branch: `add rax, 8` selects the
instruction after the destination cell.

For a zero flag, execution instead reaches `mov rax, [rax]`, selecting
`target`. The `EB 04` jump bypasses `.skip`, preserving that selection.
Both paths meet at `.push` and use the same `push rax; ret` ending.
A nonzero flag need not have any particular bit pattern; the test only
distinguishes zero from nonzero.

| Forth operation | Selected instruction address | Data-stack effect |
|---|---|---|
| `branch` | `target` | `( -- )` |
| `0branch`, zero flag | `target` | `( flag -- )` |
| `0branch`, nonzero flag | `slot + 8` | `( flag -- )` |

## The consumed-slot property

The **consumed-slot property** means the branch removes the return address
that points at inline data. The cell remains in memory for subsequent
executions; consuming the slot does not erase it.

Suppose `caller-return` is the return address beneath `slot`. Just before
the primitive's final `ret`, the top of the return stack is the selected
address, with `caller-return` beneath it. After `ret`, the selected
address is the instruction pointer and `caller-return` is the return-stack
top. Neither `slot` nor the selected address remains as an extra stack
entry. This distinction matters when the destination eventually returns:
it must reach the caller, not revisit the destination cell. The
destination may be another word's entry point, provided that word can use
the existing data stack and return to the enclosing definition's caller.

Chapter 24 (Control-flow combinators) emits and patches branches to build
structured conditionals and loops. Its runtime reference points are
[unconditional branch](#branch) and [branch on zero](#0branch). The
consumed-slot property is the contract those combinators depend on.

## Try it

Use an already defined word as the destination so its address is known
before the branch is compiled. The checkpoint helper `target,` reads that
word's name and appends its address; recall `'` and `,` from Chapter 9
(The dictionary and token reader). Recall the IMMEDIATE flag from
Chapter 10: the store at header offset `8` marks `target,` so it runs
while `choose` and `jump` are being compiled. It emits only the cell;
the preceding `branch` or `0branch` supplies the call.

`yes` prints `Y` and returns. A zero flag makes `choose` transfer to
`yes`; a nonzero flag continues after the cell and prints `N`. `jump`
always transfers to `yes`, bypassing the code that would print `X`.
The letters `A`, `B`, and `C` sit beneath the test operands and are
printed after each call. They expose an accidental extra data-stack pop
or an unconsumed flag as well as checking that control returns.

Run the following from the `forth-bootstrap` checkout at
`./forth-bootstrap`. The build command creates `seed-forth`
(`forth-bootstrap/seed/build.sh:27`); the input then exercises the branch
bodies decoded above.

```sh
./seed/build.sh > /dev/null
cat <<'EOF' | ./seed-forth
: target, ' , ;
[lit] 1 latest @ [lit] 8 + c!
: yes [lit] 89 emit ;
: choose 0branch target, yes [lit] 78 emit ;
: jump branch target, yes [lit] 88 emit ;
[lit] 65 [lit] 0 choose emit
[lit] 66 [lit] 1 choose emit
[lit] 67 jump emit
[lit] 10 emit bye
EOF
# prints "YANBYC"
```

Observed output:

```text
YANBYC
```

## Exercises

- **Trace — easy.** Start with `caller-return` beneath `slot` on the return
  stack. Follow a zero flag and then a nonzero flag through `zbranch_code`.
  Record `rax`, the return-stack top, and the instruction pointer just
  before and just after the final `ret`.
- **Verify — easy.** In the checkpoint, replace the nonzero flag with
  `[lit] 89`. Predict the output before running it. Explain why the flag
  itself is never printed.
