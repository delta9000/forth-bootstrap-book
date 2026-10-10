# Bounded compiler observations

These are observations collected on 2026-10-10 while repairing the book,
against source commit `b25487ad4d62adb950c3372de43564dfcfabdd87`.
**The source compiler is unchanged by this book PR.** These cases document
current boundaries and proposed upstream regression work, not fixed bugs
or a C-conformance certificate. They are not required-to-pass CI tests:
a future source correction must not be forced to retain a bad behavior.

## Preserved evidence and execution boundary

- [Exact C inputs](cases/) retain all 14 cases and their control programs.
- [Observed statuses and streams](observed.json) record compile, link and
  execution separately. Missing stages were not run; core compiler stdout
  contains ELF bytes rather than a text transcript.
- [Console transcript](transcript.txt) records the pin, private `/tmp` type
  (`tmpfs`), and the concise outcomes.
- [The executed runner](executed-runner.sh.txt) preserves the exact layer
  lists, generated Forth entry words, commands and timeout values as text.
  Its original scratch paths are retained. It is an evidence file, not a
  directly portable or standalone safe launcher.

All 436 tracked ordinary source files present in the probe copy were later
compared byte-for-byte with the pinned source checkout: zero differences.

The run used an isolated source copy on Linux x86-64 and a private `/tmp`
mount, so the native profile's fixed `/tmp/cc-out` did not touch an existing
host output. The outer namespace-creation command was not retained in this
packet; the transcript does record its resulting tmpfs. To repeat the
cases, adapt the runner's two absolute checkout/scratch references only
inside a disposable Linux environment with private `/tmp`, and keep the
pin, layer lists and programs unchanged. Do not paste the whole runner
into an ordinary source checkout. This packet does not claim a second
reproduction of the observations.

The exact inner compile commands are:

- Core: `timeout --kill-after=1s 3s ./seed-forth < "$d/input.fth" > "$d/program" 2> "$d/compiler.stderr"`
- Native and object: `timeout --kill-after=1s 10s ./seed-forth < "$d/input.fth" > "$d/compiler.stdout" 2> "$d/compiler.stderr"`
- Object link: `timeout --kill-after=1s 10s ./seed-forth < "$d/link.fth" > "$d/link.stdout" 2> "$d/link.stderr"`
- Program: `timeout --kill-after=1s 3s "$d/program" > "$d/program.stdout" 2> "$d/program.stderr"`

## Profiles

1. **Core:** Chapter 37's layers through `116-cc-prog.fth`, its explicit
   source-buffer setup and ELF-to-stdout driver. `/**/` separates C tokens
   while keeping the source a single `s,` token. No LP64 target enable.
2. **Native/private LP64:** Chapter 39's complete ordered layer list without
   the final executing core main, `true cc-target-lp64 !`, and a custom
   entry calling `cc-native-program`. This does not enable System V.
3. **Chapter 47 object:** The chapter's layers through `128-cc-float-literal.fth`,
   explicitly excluding later 129/131/132, followed by
   `cc-sysv-object-enable`. A small Forth-built `_start` and the Forth linker
   turn each object into the program whose exit value is observed. No host
   C compiler supplied code.

The runner text contains complete drivers. The C files alone do not select
these profiles, and loading later definitions alone does not select a target.

## Outcomes and dispositions

| Case and control | Observed outcome | Interpretation / next upstream check |
|---|---|---|
| Core valid typedef; truncated `typedef int (*F)(int` | Valid case compiles and returns 7; truncated case reaches 3-second timeout, status 124, zero output bytes | Clear bounded termination failure. Static loop inspection explains repeated EOF with nonzero depth. Fix EOF handling upstream; require a finite diagnostic in a future test. A timeout is evidence of this bounded run, not a mathematical proof of nontermination. |
| Core `2147483648 > 0`; `0x8000000100000000 != 0` | Return values 1 and 0 | The first threshold works. The higher accepted literal exposes the default emitter's restricted value domain; do not infer correct arbitrary 64-bit literal handling. |
| Native `(x) = 1`; `(0, x) = 1` | Both compile and return x=1 | Parentheses correctly preserve x, but comma also preserves assignability. This is a dialect/policy discrepancy with ordinary C; intended acceptance needs an upstream decision. Core comma is disabled. |
| Dead integer division; dead in-range float cast | Both compile/link and return 7 | Controls confirm selected-arm behavior for these inputs. |
| Dead `(int)2147483648.0`; the same selected cast | Both stop compilation with `cc: line 1: error 242` | Numeric conversion checks the range even in the unselected arm in this profile. Narrow the book's suppression claim; separate the desired diagnostic policy from a claim of general C conformance. |
| Finite constant equality; finite runtime equality | Both compile/link and return 1 | Finite control paths agree for one-half. |
| Resized NaN constant equality; runtime equality of the same initialized NaN | Both compile/link; return 1 and 0 respectively | Concrete constant/runtime inconsistency outside the scalar finite-arithmetic contract. Keep nonfinite support bounded and decide the desired semantics upstream before broadening the book's promise. |

Except for the two range-diagnostic cases, compiler/linker text streams are
empty; all generated program text streams are empty. Status 124 is GNU
`timeout`'s observation; statuses 1 and 7 are deliberate program values,
not wrapper failures. A successful finite control or matching result does
not clear other inputs or profiles. No full compiler bootstrap, GCC chain
or QEMU/Linux run was performed for this packet.
