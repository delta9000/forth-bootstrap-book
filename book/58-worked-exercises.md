# Appendix D — Worked exercises

`?exit,` can turn a flag into an early return; `a - b - c` can expose a parser's grouping choice. These worked exercises from Parts 1–3 turn a source-reading question into a predicted result, then test that prediction. Each answer follows the same method: identify the question, sketch the answer, solve it, run a check, and explain why the result follows.

## D.1. Chapter 24 — Add the `?exit,` combinator

**Extend — moderate.** Build an immediate `?exit,` that compiles “return if the runtime flag is nonzero,” using the emission operations behind `if,`, `exit,`, and `then,`.

### What's asked

The target is a compile-time word with runtime effect `( flag -- )`. Its own execution must emit the conditional return into the definition under construction. Writing the immediate combinators directly inside its body would execute them while compiling `?exit,` itself.

### Shape of the answer

The definitions in [Chapter 24](24-lib-11-control-flow-combinators.md) supply the plan: emit a conditional branch with a reserved destination, append a return, then patch the destination past that return. The fixup stays inside `?exit,`; its caller need not carry it to a separate `then,`.

### Solution

Keep the destination unresolved until the return has been emitted. This exercise definition combines the operations in the library's conditional and patching definitions (`forth-bootstrap/forth/010-lib.fth:309`):

```forth
: ?exit,
  0branch-xt call, here [lit] 0 ,
  ret, here swap ! ;
immediate
```

The branch's zero path lands after the return. Its nonzero path reaches the return. The final `immediate` makes this emission happen while compiling the caller.

### Check

Run each check in this appendix from the `forth-bootstrap` checkout root at `./forth-bootstrap`, with the seed already built. This one loads the library, adds the exercise definition, and invokes a word that prints a dot only on the fall-through path:

```sh
{
  cat forth/010-lib.fth
  printf '%s\n' \
    ': ?exit, 0branch-xt call, here [lit] 0 , ret, here swap ! ; immediate' \
    ': dot-unless ?exit, [lit] 46 emit ;' \
    '[lit] 0 dot-unless [lit] 1 dot-unless [lit] 0 dot-unless'
} | ./seed-forth
```

The seed prints `..`.

### Why

The dots distinguish the paths: a zero flag skips the return and reaches `emit`; a nonzero flag returns before `emit`. The early return requires a balanced return stack (Chapter 24).

## D.2. Chapters 10 and 12 — Why does `ret` end a colon definition?

**Trace — easy.** Follow entry into a colon body and explain which address its terminating `ret` consumes.

### What's asked

A definition can call other words and still finish with the return appended by `;`. Identify the address left on the return stack when those nested calls have finished.

### Shape of the answer

Draw the control path into a word, through a nested word, and back to the interpreter. Label the return address at each boundary. The relevant source is the colon compiler in [Chapter 10](10-colon-compiler.md) and dispatch in [Chapter 12](12-repl.md).

### Solution

Follow the REPL's execution path (`forth-bootstrap/seed/000-seed.hex0:687`): it calls `execute_code`. The routine at `forth-bootstrap/seed/000-seed.hex0:392` moves the execution token into `rax`, removes it from the data stack, and jumps to it. The jump preserves the return address supplied by the REPL's call.

A call from another colon body reaches the word directly through an emitted call. In either case, the body has a return address for its caller. A nested call adds its own address and consumes it on return. After balanced nested operations, the outer address is exposed again.

The semicolon handler appends the return opcode and clears compilation state (`forth-bootstrap/seed/000-seed.hex0:543`). That appended instruction consumes the exposed address. `execute` needs no extra return after its jump.

### Check

Make the nested word print `A`, its caller print `B`, and the interpreter print `C` after the caller returns:

```sh
printf '%s\n' \
  ': inner [lit] 65 emit ;' \
  ': outer inner [lit] 66 emit ;' \
  'outer [lit] 67 emit' | ./seed-forth
```

The seed prints `ABC`.

### Why

`B` demonstrates return from `inner` into `outer`; `C` demonstrates return from `outer` to dispatch. An unmatched value saved on the return stack would hide the address the terminating instruction needs. The trace depends on balanced return-stack use, not on a separate frame teardown.

## D.3. Chapter 33 — Trace `cc-parse-add` on `a - b - c`

**Trace — moderate.** Identify when each subtraction is emitted and what becomes the next left operand.

### What's asked

The required grouping is `(a - b) - c`. Find the point where the parser commits to that grouping rather than parsing the entire remaining additive expression as the right operand.

### Shape of the answer

Use a row per successful pass through the additive loop. Track the saved left operand, the right operand, and the result available for the following pass. [Chapter 33](33-expressions-part-1.md) supplies the parser; this check uses its core mode.

### Solution

The right operand is parsed at multiplication precedence, so another subtraction remains for the next loop pass (`forth-bootstrap/cc/100-cc-expr.fth:1898`):

```forth
: cc-parse-add
  cc-parse-mul
  begin,
    level-add cc-binop? dup                       ( row row | 0 0 )
  while,
    >r                                            ( ; R: row )
    cc-emit-materialize                           \ left must be a value
    cc-target-lp64 @ if,
      cc-last-expr-type @ cc-last-struct-desc @ cc-last-expr-array-inner @ cc-last-expr-null @ cc-last-expr-qualified @
    then,
    cc-emit-push-rdi                              \ save left
    cc-parse-mul                                  \ rdi = right
    r> cc-target-lp64 @ if, cc-native-binop-apply else, cc-binop-apply then,
                                                  \ rdi = left OP right
  repeat,
  drop                                            \ cc-binop?'s 0
  cc-putback-token ;                              \ we read one too many
```

The LP64 branch preserves additional type information. It is inactive in this check. In core mode, `cc-binop-apply` materializes the right operand, emits its transfer to `rcx`, restores the left into `rdi`, and invokes the operator's emitter (`forth-bootstrap/cc/100-cc-expr.fth:1865`). These words emit instructions; they do not subtract the C operands while Forth is parsing.

| Pass | Saved left | Parsed right | Generated result |
|---|---|---|---|
| First subtraction | `a` | `b` | `a - b` |
| Next subtraction | `a - b` | `c` | `(a - b) - c` |

For a variable operand, the initial parse can leave an lvalue description. The materialization before saving the left ensures the generated program uses its value. After the final subtraction, the failed operator lookup ends the loop and the following token is put back.

### Where left-associativity comes from

Each pass completes its operation before accepting another additive operator. The right-hand call is `cc-parse-mul`, not `cc-parse-add`; it cannot absorb the next subtraction. The completed result therefore becomes the next pass's left operand.

### Check

Use local variables so the test exercises operand loads as well as subtraction. This driver follows the phase order of `cc-main`, but writes the finalized image to stdout instead of its fixed output path (`forth-bootstrap/cc/120-cc-main.fth:28`). The shell captures that image in a temporary directory and removes it after execution.

```sh
(
probe_dir=$(mktemp -d)
trap 'rm -r "$probe_dir"' EXIT
{
  cat forth/010-lib.fth cc/020-cc-arena.fth cc/030-cc-io.fth \
      cc/040-cc-prep.fth cc/050-cc-lex.fth \
      cc/060-cc-types.fth cc/070-cc-sym.fth \
      cc/080-cc-elf.fth cc/090-cc-emit.fth cc/100-cc-expr.fth \
      cc/110-cc-decl.fth cc/112-cc-stmt.fth \
      cc/114-cc-func.fth cc/116-cc-prog.fth
  cat <<'FORTH'
: exercise-main
  cc-load-stdin cc-preprocess
  cc-out-init cc-globals-init cc-emit-elf-header
  cc-parse-program cc-finalize-globals cc-finalize-elf
  [lit] 1 cc-out-buf cc-out-pos @ write drop bye ;
exercise-main
int main(void) { int a = 10; int b = 3; int c = 2; return a - b - c; }
FORTH
} | ./seed-forth > "$probe_dir/subtract"
printf 'compiler exit: %s\n' "$?"
chmod +x "$probe_dir/subtract"
"$probe_dir/subtract"
printf 'a - b - c: %s (exit status)\n' "$?"
)
```

Observed output:

```text
compiler exit: 0
a - b - c: 5 (exit status)
```

### Why

The returned value matches the loop trace: subtract `b` from `a`, then subtract `c` from that result. This run checks the core parser and emitted executable together. It does not test the LP64 branch.
