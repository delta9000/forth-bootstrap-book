# Chapter 44 — Target headers

A target header contract tells C source which declarations it can select before compilation. A header chooses its dialect from the macros the compiler predefines. Here the compiler publishes its target identity and a bounded ANSI declaration policy, then a C probe checks those promises.

## Names describe the selected target

The layer has a simple shape: store the macro spellings, install their replacements when System V mode is selected, and attach that installer to the preprocessor hook. Macro lookup and conditional inclusion already provide the consumer side (Chapter 28).

The stored names map to this advertised interface. Values come from the installer in `forth-bootstrap/cc/124-cc-target.fth:14`; the replacement strings are defined in `forth-bootstrap/cc/040-cc-prep.fth:2254`.

| Forth name | C macro → replacement | Meaning |
|---|---|---|
| `cc-target-name-stdc` | `__STDC__` → `1` | Select ANSI-style declarations. |
| `cc-target-name-hosted` | `__STDC_HOSTED__` → `0` | Do not promise a complete hosted C environment. |
| `cc-target-name-seed` | `__SEED_FORTH__` → `1` | Identify this compiler. |
| `cc-target-name-linux` | `__linux__` → `1` | Advertise Linux. |
| `cc-target-name-amd64` | `__x86_64__` → `1` | Advertise AMD64. |
| `cc-target-name-lp64` | `__LP64__` → `1` | Advertise the LP64 data model. |

These are stored spellings, not switches that implement the named features. The names occupy the opening of `forth-bootstrap/cc/124-cc-target.fth:1`:

```forth file=cc/124-cc-target.fth
\ 124-cc-target.fth -- explicit predefined macros for the SysV C90-oriented mode.
\ The legacy/native route keeps its existing macro policy. No GCC identity
\ or C99/C11 language version is advertised. See book Ch 40 for the boundary.
create cc-target-name-stdc       s, __STDC__
create cc-target-name-hosted     s, __STDC_HOSTED__
create cc-target-name-seed       s, __SEED_FORTH__
create cc-target-name-linux      s, __linux__
create cc-target-name-amd64      s, __x86_64__
create cc-target-name-lp64       s, __LP64__

```

The comment's “book Ch 40” refers to this chapter in the old numbering.

The LP64 promise rests on the storage model already implemented (Chapter 39). The runtime agrees: its `stddef.h` uses `unsigned long` for `size_t` and `long` for `ptrdiff_t` (`forth-bootstrap/chain/runtime/gcc-seed/include/stddef.h:3`). Defining a macro alone would not make those declarations match generated code.

## Install facts before scanning source

The names need values in each fresh macro table. `cc-preprocess` clears that table before calling the target hook, then scans the source (`forth-bootstrap/cc/040-cc-prep.fth:2308`). Installing entries there avoids injecting synthetic source lines.

`cc-target-predefines` gates the policy on `cc-target-sysv`; its final binding makes the preprocessor call this installer (`forth-bootstrap/cc/124-cc-target.fth:11`):

```forth file=cc/124-cc-target.fth
: cc-target-predefines
  cc-target-sysv @ if,
    cc-prep-location-builtins
    cc-target-name-stdc   [lit] 8  cc-pp-t1 [lit] 1 cc-macro-add
    cc-target-name-hosted [lit] 15 cc-pp-t0 [lit] 1 cc-macro-add
    cc-target-name-seed   [lit] 14 cc-pp-t1 [lit] 1 cc-macro-add
    cc-target-name-linux  [lit] 9  cc-pp-t1 [lit] 1 cc-macro-add
    cc-target-name-amd64  [lit] 10 cc-pp-t1 [lit] 1 cc-macro-add
    cc-target-name-lp64   [lit] 8  cc-pp-t1 [lit] 1 cc-macro-add
  then, ;
' cc-target-predefines is cc-prep-target-fwd
```

Each `cc-macro-add` receives the stored name and its length, followed by the replacement text and its length. `cc-pp-t1` supplies the text `1`; `cc-pp-t0` supplies `0`. The hosted entry is deliberately different from the identity entries. With System V mode disabled, this word adds nothing.

The call to `cc-prep-location-builtins` also enables `__FILE__` and `__LINE__`. They are dynamic macro-table entries rather than fixed target constants (`forth-bootstrap/cc/040-cc-prep.fth:2298`). Their expansion machinery is unchanged.

## A declaration policy has limits

`__STDC__` lets a historical header choose its ANSI branch: prototypes and qualified declarations instead of a traditional interface. The source calls this policy C90-oriented and explicitly withholds GCC identity and a C99/C11 version claim (`forth-bootstrap/cc/124-cc-target.fth:1`). Neither `__GNUC__` nor `__STDC_VERSION__` is installed. The preprocessor's other built-in installers add library constants and source locations, not those identities (`forth-bootstrap/cc/040-cc-prep.fth:2273`).

A header must not infer complete language or library conformance from this branch selection. Advertising GCC would invite headers to select GCC-specific facilities; advertising a later C version would make another unsupported promise. Even an accepted declaration cannot supply a missing implementation. The runtime's public headers intentionally expose only implemented interfaces (`forth-bootstrap/chain/runtime/gcc-seed/README.md:3`). Its `features.h` likewise withholds `__GLIBC__` and feature-test machinery (`forth-bootstrap/chain/runtime/gcc-seed/include/features.h:3`).

The contract therefore joins header selection to implemented semantics. A build that needs a particular function or extension must still test that facility with the compiler and runtime it will use.

## Try it

Run from the `forth-bootstrap` checkout root at `./forth-bootstrap`, with the seed already built. The full loader includes later extension definitions; this probe uses only preprocessing, integer sizes, and the System V program entry taught so far. The loader places the executing main last (`forth-bootstrap/cc/compiler-layers.sh:2`), so `sed` removes that invocation before appending `target-main`.

`cc-sysv-enable` selects the target before preprocessing; `cc-sysv-program` emits the executable's entry and translation unit (`forth-bootstrap/cc/121-cc-sysv.fth:1339`). The temporary directory holds the generated inputs and executable, and the exit trap restores any saved `/tmp/cc-out`.

The C program rejects missing or incorrect target macros and unexpected GCC or language-version identities. It also checks that the advertised data model agrees with `sizeof`. A successful return means all checks passed.

```sh
(
probe_dir=$(mktemp -d)
if [ -e /tmp/cc-out ] || [ -L /tmp/cc-out ]; then
  mv /tmp/cc-out "$probe_dir/saved-cc-out"
fi
trap 'rm -f /tmp/cc-out; if [ -e "$probe_dir/saved-cc-out" ] || [ -L "$probe_dir/saved-cc-out" ]; then mv "$probe_dir/saved-cc-out" /tmp/cc-out; fi; rm -r "$probe_dir"' EXIT
cat forth/010-lib.fth $(cc/compiler-layers.sh) | sed '$d' > "$probe_dir/compiler.fth"
cat >> "$probe_dir/compiler.fth" <<'FORTH'
cc-sysv-enable
: target-main
  cc-load-stdin cc-preprocess cc-out-init cc-globals-init
  cc-emit-elf-header cc-sysv-program cc-finalize-globals
  cc-finalize-elf cc-out-path cc-write-output bye ;
target-main
FORTH
cat > "$probe_dir/target.c" <<'C'
int main(void) {
#if !defined(__STDC__) || !defined(__STDC_HOSTED__) || !defined(__SEED_FORTH__)
  return 1;
#elif __STDC__ != 1 || __STDC_HOSTED__ != 0 || __SEED_FORTH__ != 1
  return 2;
#elif !defined(__linux__) || !defined(__x86_64__) || !defined(__LP64__)
  return 3;
#elif __linux__ != 1 || __x86_64__ != 1 || __LP64__ != 1
  return 4;
#endif
#ifdef __GNUC__
  return 5;
#endif
#ifdef __STDC_VERSION__
  return 6;
#endif
#if !defined(__FILE__) || !defined(__LINE__)
  return 7;
#endif
  return sizeof(int) != 4 || sizeof(long) != 8 || sizeof(void *) != 8;
}
C
(cat "$probe_dir/compiler.fth" "$probe_dir/target.c" | ./seed-forth)
compiler_status=$?
printf 'compiler exit: %s\n' "$compiler_status"
if [ "$compiler_status" != 0 ]; then exit "$compiler_status"; fi
mv /tmp/cc-out "$probe_dir/target"
chmod +x "$probe_dir/target"
(cd "$probe_dir" && ./target)
program_status=$?
printf 'target contract exit: %s\n' "$program_status"
exit "$program_status"
)
```

Observed output:

```text
compiler exit: 0
target contract exit: 0
```

## Exercise

**Trace — easy.** Follow `cc-target-name-hosted` from its stored spelling to its `cc-macro-add` call. Why would replacing `#if __STDC_HOSTED__` with `#ifdef __STDC_HOSTED__` select a different branch? Identify the checkpoint condition that distinguishes absence from a false value.
