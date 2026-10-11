# Chapter 38 — Compiler entry and Stage A

`int main(void) { putchar(42); return 0; }` becomes an executable that prints `*`. The remaining job is to give the compiler layers an entry word that takes over stdin and carries compilation through to a file. `cc-main` supplies that entry; Stage A then tests the resulting compiler on M2-Planet against a GCC-built reference.

## `cc-main`: nine words and a `bye`

The entry file has a simple shape: a fixed output path, a definition that sequences the compilation phases, and a call that starts it. Loading this file is the boundary between defining the compiler in Forth and feeding it C.

The header records the core load order so that the executing entry comes after its dependencies (`forth-bootstrap/cc/120-cc-main.fth:1`):

```forth file=cc/120-cc-main.fth
\ 120-cc-main.fth — main entry for the C-subset compiler.
\
\ Reads C source from stdin; emits ELF executable to /tmp/cc-out.
\
\ Load order (strict — do not rearrange):
\   010-lib.fth        — primitives, syscalls, control-flow, defining words
\   020-cc-arena.fth   — bump allocator (must load before 030-cc-io.fth)
\   030-cc-io.fth      — source buffer, output buffer, file I/O
\   040-cc-prep.fth    — preprocessor (#include, #define, #if; expands macros)
\   050-cc-lex.fth     — tokenizer (reads what 040-cc-prep.fth wrote)
\   060-cc-types.fth   — type encoding (int, char, pointer, struct)
\   070-cc-sym.fth     — symbol table (parallel arrays, scope stack)
\   080-cc-elf.fth     — ELF header emission
\   090-cc-emit.fth    — x86-64 instruction encoders (codegen backend)
\   100-cc-expr.fth    — expression parser (depends on 090-cc-emit.fth)
\   110-cc-decl.fth    — declaration parser (depends on 100-cc-expr.fth)
\   112-cc-stmt.fth    — statement parser
\   114-cc-func.fth    — function definitions
\   116-cc-prog.fth    — file-scope forms, entry stub, top-level driver
\   120-cc-main.fth    — entry point: cc-main

```

The output needs a name before the entry can write it. `cc-out-path` supplies the address of the NUL-terminated `/tmp/cc-out` string; its payload occupies 12 bytes (`forth-bootstrap/cc/120-cc-main.fth:22`):

```forth file=cc/120-cc-main.fth
\ Pre-baked output path: "/tmp/cc-out\0"
create cc-out-path
[lit]  47 c, [lit] 116 c, [lit] 109 c, [lit] 112 c,    \ /tmp
[lit]  47 c, [lit]  99 c, [lit]  99 c, [lit]  45 c,    \ /cc-
[lit] 111 c, [lit] 117 c, [lit] 116 c, [lit]   0 c,    \ out\0

```

This fixed destination is the compiler's output interface. There is no output-name argument to `cc-main`. Its writer accepts this address (Chapter 27), so another compilation replaces the file. The checkpoint saves an existing file before running and restores it afterward.

## The nine steps

Each phase must leave its result ready for the next. In particular, parsing must finish before global placement, and global placement must finish before the ELF header sizes are patched. The program parser already owns entry generation and function checks (Chapter 37); `cc-main` owns the order around it.

| Step | Phase | Result passed onward |
|---|---|---|
| 1 | `cc-load-stdin` | The remaining input is available as C source. |
| 2 | `cc-preprocess` | The parser's source buffer is ready. |
| 3 | `cc-out-init` | The output cursor is reset. |
| 4 | `cc-globals-init` | Global storage and fixup state are reset. |
| 5 | `cc-emit-elf-header` | Output begins with the executable header. |
| 6 | `cc-parse-program` | Program code is emitted and function references checked. |
| 7 | `cc-finalize-globals` | Global storage is placed and its references resolved. |
| 8 | `cc-finalize-elf` | Header sizes describe the completed image. |
| 9 | `cc-write-output` | The image is written to `cc-out-path`. |

The definition puts those phase calls in order, then exits; the bare call below it starts compilation as soon as the file loads (`forth-bootstrap/cc/120-cc-main.fth:28`):

```forth file=cc/120-cc-main.fth
: cc-main
  cc-load-stdin
  cc-preprocess
  cc-out-init
  cc-globals-init
  cc-emit-elf-header
  cc-parse-program
  cc-finalize-globals
  cc-finalize-elf
  cc-out-path cc-write-output
  bye ;

cc-main
```

“Nine words” counts the phase operations: `cc-out-path` supplies an operand to the last operation, and `bye` ends the process. C `main` is inside the generated executable; Forth `cc-main` runs while producing that executable.

The input handoff determines where this file belongs. Anything appended after its final call is compiler input, even if it looks like another Forth definition. The loader helper therefore places this file last, after any optional extensions, as specified in `forth-bootstrap/cc/compiler-layers.sh:2`.

## Stage A: the parity proof

So far we have chosen small C programs whose answers we can predict.
M2-Planet is a different kind of test: a real compiler, large enough to
exercise many of the paths we have just built. We need a comparison that
does not require predicting its entire output by hand.

A star on the terminal checks the entry path. Stage-A parity asks a larger, precise question: does M2-Planet built by the Forth compiler emit byte-identical M1 output to M2-Planet built by GCC when both compile the same M2-Planet source set for amd64?

The test constructs the comparison in `forth-bootstrap/tests/cc/stage-a-check.sh:41`:

- Build a fresh reference executable, `m2-ref`, using host GCC.
- Build `cc-out-v1` by feeding the compiler vocabulary and an M2-Planet monolith to the seed.
- Run both executables on the same source list with the same architecture and include-expansion options.
- Compare `self-v1-amd64.M1` and `self-ref-amd64.M1` with `cmp`.

The monolith builder prepares the C input and feeds it after the Forth vocabulary (`forth-bootstrap/tests/cc/build-m2planet-monolith.sh:71`). Stage A invokes that builder with `CC_OUT` pointing into its build directory. The builder tries a private `/tmp` and falls back to the shared `/tmp/cc-out` when namespaces are unavailable (`forth-bootstrap/tests/cc/build-m2planet-monolith.sh:42`). The checkpoint preserves that shared path around Stage A too.

The comparison spans two compilation steps. The Forth compiler and GCC first
produce two M2-Planet executables; each executable then produces an M1
file. Those final files are what `cmp` compares. Different machine code
in the two executables is compatible with identical assembly output.

A match gives evidence that the Forth-built M2-Planet behaves like the
reference on this source set and these options. It does not establish a
fixed point or remove the host GCC dependency: GCC supplied the reference
(`forth-bootstrap/tests/cc/stage-a-check.sh:4`). We can use the result to
justify the next experiment without asking it to prove the entire chain.

## The wider chain

A bootstrap chain is a sequence in which tools built from source provide the means to build the next tools. Stage A is a comparison alongside that construction, not the downstream route itself. The current route in `forth-bootstrap/README.md:14` proceeds through `seed-cc`, the build tools, GCC, and Linux; the README distinguishes the host and kernel runs in `forth-bootstrap/README.md:81`.

Part 4 follows that route: Chapter 50 builds `seed-cc`, Chapter 51 builds the tools, and Chapter 52 follows GCC. Chapter 53 audits the sealed host run; Chapter 54 introduces K0 and K1; Chapter 55 carries the chain to Linux. Stage A closes the core compiler sequence without claiming those later results.

Before taking that route, the compiler needs a more precise account of
storage. Consider `struct Item { char tag; long value; }` initialized with
`{3, 7}`. Where must each store land, and how much room belongs between
the fields? An eight-byte working register cannot answer those questions:
the objects have their own sizes and alignment. [Chapter 39](39-lp64-storage-and-initializers.md)
uses this record to connect LP64 field layout to initialization, beginning
the extensions needed by the larger sources ahead.

## Try it

Run both checkpoints from the `forth-bootstrap` checkout root, with the seed already built in Part 1. Do not run either checkpoint concurrently with another user of `/tmp/cc-out`. Each saves that path before starting, restores it on exit, and retains the backup directory if restoration fails. The first loads the complete Forth library and the core compiler, then appends the opening C example. `cc/compiler-layers.sh` is the full loader, including the extension layers of Chapters 39–49; this demo loads only the core.

<!-- tryit: expect "compiler exit: 0\n*\nprogram exit: 0" -->
```sh
(
set -o pipefail
probe_dir=$(mktemp -d /tmp/book-probe.XXXXXXXXXX) || exit "$?"
saved_output=0
if [ -e /tmp/cc-out ] || [ -L /tmp/cc-out ]; then
  if mv -T -- /tmp/cc-out "$probe_dir/saved-cc-out"; then
    saved_output=1
  else
    printf 'Backup failed; inspect /tmp/cc-out and %s\n' "$probe_dir" >&2
    exit 1
  fi
fi
cleanup() {
  status=$?
  trap - EXIT HUP INT TERM
  if ! rm -f -- /tmp/cc-out; then
    printf 'Cleanup failed; inspect /tmp/cc-out and %s\n' "$probe_dir" >&2
    exit 1
  fi
  if [ "$saved_output" -eq 1 ] &&
      ! mv -T -- "$probe_dir/saved-cc-out" /tmp/cc-out; then
    printf 'Restore failed; saved output retained at %s\n' "$probe_dir/saved-cc-out" >&2
    exit 1
  fi
  rm -rf -- "$probe_dir" || status=1
  exit "$status"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
compiler_status=0
{
  cat forth/010-lib.fth cc/020-cc-arena.fth cc/030-cc-io.fth \
      cc/040-cc-prep.fth cc/050-cc-lex.fth \
      cc/060-cc-types.fth cc/070-cc-sym.fth \
      cc/080-cc-elf.fth cc/090-cc-emit.fth cc/100-cc-expr.fth \
      cc/110-cc-decl.fth cc/112-cc-stmt.fth \
      cc/114-cc-func.fth cc/116-cc-prog.fth cc/120-cc-main.fth || exit "$?"
  printf '%s\n' 'int main(void) { putchar(42); return 0; }'
} | ./seed-forth || compiler_status=$?
printf 'compiler exit: %s\n' "$compiler_status"
test "$compiler_status" -eq 0 || exit "$compiler_status"
mv -T -- /tmp/cc-out "$probe_dir/program" || exit "$?"
chmod +x "$probe_dir/program" || exit "$?"
program_status=0
"$probe_dir/program" || program_status=$?
printf '\nprogram exit: %s\n' "$program_status"
test "$program_status" -eq 0
)
```

Observed output:

```text
compiler exit: 0
*
program exit: 0
```

The program emits the star; the shell adds the newline before its exit-status report. This exercises `cc-main` and its fixed output destination without loading later compiler layers.

For the parity check, host GCC and the initialized vendor sources are required. The reference builder checks for M2-Planet, its M2libc, and mescc-tools sources (`forth-bootstrap/tests/cc/build-gcc-refs.sh:29`). A fresh temporary `BUILDROOT` keeps the artifacts together; the script runs in seconds. This is the repository's prescribed test, with its normal loader.

```sh
(
set -o pipefail
probe_dir=$(mktemp -d /tmp/book-probe.XXXXXXXXXX) || exit "$?"
saved_output=0
keep_work=0 # Set to 1 to keep the Stage A files for the exercise.
if [ -e /tmp/cc-out ] || [ -L /tmp/cc-out ]; then
  if mv -T -- /tmp/cc-out "$probe_dir/saved-cc-out"; then
    saved_output=1
  else
    printf 'Backup failed; inspect /tmp/cc-out and %s\n' "$probe_dir" >&2
    exit 1
  fi
fi
cleanup() {
  status=$?
  trap - EXIT HUP INT TERM
  if ! rm -f -- /tmp/cc-out; then
    printf 'Cleanup failed; inspect /tmp/cc-out and %s\n' "$probe_dir" >&2
    exit 1
  fi
  if [ "$saved_output" -eq 1 ] &&
      ! mv -T -- "$probe_dir/saved-cc-out" /tmp/cc-out; then
    printf 'Restore failed; saved output retained at %s\n' "$probe_dir/saved-cc-out" >&2
    exit 1
  fi
  if [ "$keep_work" -eq 1 ]; then
    printf 'Stage A files retained at %s\n' "$probe_dir"
  else
    rm -rf -- "$probe_dir" || status=1
  fi
  exit "$status"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
stage_status=0
CC=gcc BUILDROOT="$probe_dir/stage-a" tests/cc/stage-a-check.sh || stage_status=$?
printf 'stage-a exit: %s\n' "$stage_status"
if [ "$stage_status" -ne 0 ]; then keep_work=1; fi
exit "$stage_status"
)
```

Observed final lines from this run:

```text
stage-a-check: self-v1-amd64.M1 == self-ref-amd64.M1 (2367260 bytes)
stage-a-check: PASS
stage-a exit: 0
```

## Exercise

Hints and feedback are in [Appendix H](66-exercise-feedback.md#chapter-38-handoff-and-stage-a-evidence).

**Trace (easy).** In the first checkpoint, identify the exact Forth token that changes the meaning of the remaining stdin from Forth definitions to C source. Explain what would happen if another Forth definition were appended after that token.

**Verify (moderate).** Set `keep_work=1` in the Stage A checkpoint to retain its build directory while still restoring `/tmp/cc-out`. Use the printed directory path to repeat the script's `cmp` on the emitted M1 files. Explain why that equality does not require the compiler executables themselves to be identical.
