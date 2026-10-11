# Chapter 56 — Epilogue: onward to GCC 15.2

The guest route now reaches GCC 10.5.0 and can build Linux. A concrete
next project is to use that compiler to build GCC 15.2.0 under K1 before
the handoff. We have a starting recipe: the older
[seed-forth](https://github.com/delta9000/seed-forth) project already made
that compiler climb on its own route. Its final stages stayed behind
when forth-bootstrap's direct route was extracted
(`forth-bootstrap/HISTORY.md:28`).

This is where following the book can become extending it. The work is to
carry those stages across without losing track of their inputs, builders
and checks. Forth-bootstrap has no GCC 15 guest checkpoint yet. We will
read the historical seed-forth snapshot
[0dd2b8815cae](https://github.com/delta9000/seed-forth/tree/0dd2b8815caeb5b9814567036f4ce101fdebeb21),
the extraction revision named in `forth-bootstrap/HISTORY.md:3–4`.
All `gcc64/` links below identify recipes or recorded results in that
snapshot, outside this book's submodule.

## The route that stayed behind

Start by finding where the routes meet. Seed-forth reaches gcc-A through
TinyCC, musl and binutils (`forth-bootstrap/HISTORY.md:28`). Our route
reaches it from the direct GCC 4.0.4, through the bridge stage in
Chapter 55 (`forth-bootstrap/chain/gcc64/run-gcc64.sh:267`). Both then
climb through the later GCC versions. We can preserve our beginning and
extend its end.

That choice is visible in the stage lists. Seed-forth defaults to
`stage0` through `stage12`; forth-bootstrap selects `bridge`, then
`stage6` through `stage10` (seed-forth's
[`gcc64/run-gcc64.sh:799–803`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/run-gcc64.sh#L799-L803);
`forth-bootstrap/chain/gcc64/run-gcc64.sh:452`). The missing continuation
is therefore small at the orchestration level:

| Step | Input → result | Source in seed-forth |
|---|---|---|
| `stage11` | GCC 10.5.0 → GCC 15.2.0 bootstrap, comparison and C/C++ tests | [`gcc64/run-gcc64.sh:697–712`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/run-gcc64.sh#L697-L712) |
| `stage12` | Installed compilers → compiled and executed test programs; final tool-path checks | [`gcc64/run-gcc64.sh:719–768`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/run-gcc64.sh#L719-L768) |

These are gcc64 stage names. Forth-bootstrap's `chain/ladder/stage12.sh` builds Linux; it is a different script with a different responsibility (Chapter 55). Reusing a number in a new integration must not silently replace the Linux build.

Seed-forth's README records a successful compiler comparison and the
tests it checked
([`gcc64/README.md:163–189`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/README.md#L163-L189)).
That gives us a working precedent and a set of observations to reproduce
under K1.

## Keep the build's actual boundary

The final compiler recipe uses the existing sysroot, its GMP, MPFR and MPC libraries, and the existing binutils. It selects C and C++, enables bootstrap, and disables several optional runtime libraries and compiler facilities (seed-forth's [`gcc64/build-gcc15.sh:18–29`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/build-gcc15.sh#L18-L29)). This is a particular compiler configuration. “GCC 15.2.0” alone does not specify what was built.

The decisive option is `--enable-bootstrap`. The preceding GCC 10.5.0
recipe uses `--disable-bootstrap`
([`gcc64/build-gcc10.sh:29`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/build-gcc10.sh#L29));
this final recipe instead builds with the supplied compiler, rebuilds
with its own outputs, and compares generations. We have met that idea
before in Chapter 52. Here GCC's own build performs the bootstrap, and
the caller requires `Comparison successful` in the log before continuing
to C and C++ tests
([`gcc64/run-gcc64.sh:704`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/run-gcc64.sh#L704)).
Preserve that stop condition when moving the recipe.

The recipe applies no GCC-source patches and configures without ISL or zstd (seed-forth's [`gcc64/build-gcc15.sh:3`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/build-gcc15.sh#L3), [`gcc64/build-gcc15.sh:29`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/build-gcc15.sh#L29)). That does not make the whole environment patch-free. The README identifies a musl declaration patch for the newer compiler's C23 dialect ([`gcc64/README.md:221`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/README.md#L221)). Integration must audit the surrounding sysroot and patches as well as copy the final recipe.

The sysroot libraries remain the earlier gcc-B's builds, and the final assembler and linker remain the earlier binutils build (seed-forth's [`gcc64/README.md:326–330`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/README.md#L326-L330)). A successful final compiler bootstrap therefore leaves those dependencies in place. Rebuilding the sysroot and binutils with the final compiler would be a separate extension with its own comparisons, not something this recipe already demonstrates.

## Bring inputs and work into K1

The archive to add is `gcc-15.2.0.tar.xz`, with the digest and acquisition URLs in seed-forth's [`gcc64/SOURCES:58`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/SOURCES#L58). The existing dependencies are also explicit there: musl, the GMP DFSG repack, MPFR, MPC and binutils ([`gcc64/SOURCES:35`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/SOURCES#L35), [`gcc64/SOURCES:43`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/SOURCES#L43), [`gcc64/SOURCES:45`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/SOURCES#L45), [`gcc64/SOURCES:47`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/SOURCES#L47), [`gcc64/SOURCES:49`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/SOURCES#L49)). A port should reconcile those pins with the inputs already used by forth-bootstrap before fetching anything new.

Forth-bootstrap's manifest already pins those arithmetic-library archives and the later binutils archive (`forth-bootstrap/MANIFEST.sha256:37`, `forth-bootstrap/MANIFEST.sha256:49`, `forth-bootstrap/MANIFEST.sha256:55`). Adding a source entry alone would be insufficient: the new archive also needs a `MANIFEST.sha256` entry. The fetcher reads gcc64's URLs but accepts cached or downloaded bytes against the manifest (`forth-bootstrap/tools/fetch-archives.py:81`, `forth-bootstrap/tools/fetch-archives.py:146`, `forth-bootstrap/tools/fetch-archives.py:181`). Both descriptions must agree.

The guest also needs the recipe and test sources. Its current Linux input list includes the earlier compiler recipes and libc/C++ tests; archive selection reads manifest paths (`forth-bootstrap/kernel/k1/direct_inputs.py:349`, `forth-bootstrap/kernel/k1/direct_inputs.py:415`). The proposed integration would add the final recipe and the verification workloads, extend stage selection and source selection, and arrange a guest invocation before results are exported. Host-only setup and build glue in seed-forth's script would need review against the tools available inside K1 ([`gcc64/README.md:237–257`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/README.md#L237-L257)). Copying the script is not evidence that those tools exist there.

Resource planning needs a guest measurement. Seed-forth records 4,851 seconds for the final bootstrap with `JOBS=4` on its historical host run ([`gcc64/README.md:141–144`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/README.md#L141-L144), [`gcc64/README.md:159`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/README.md#L159)). That timing does not establish K1's elapsed time, peak RAM or disk capacity. The port should measure those quantities while preserving room for sources, intermediate bootstrap trees, installed outputs and exported logs. There is no verified guest budget for this extension here.

## What would count as success

A proposed GCC extension should preserve separate evidence for each claim:

- Pinned inputs are present and verified before extraction, including the new archive and every dependency used.
- The final bootstrap completes its stage2 = stage3 compare, and the comparison log is exported.
- C and C++ workloads compile and run under the guest. Seed-forth's verification also checks the final sysroot, assembler, linker and verbose compiler program paths ([`gcc64/run-gcc64.sh:719–768`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/run-gcc64.sh#L719-L768)).
- The new outputs receive pins in forth-bootstrap's `HASHES`, with the build root and comparison scope stated. Seed-forth pins the final driver, compiler executables and runtime archives as path-dependent outputs ([`gcc64/HASHES:34`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/HASHES#L34), [`gcc64/HASHES:41–44`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/HASHES#L41-L44)). Its historical digests are reference evidence, not automatic pins for a different guest build.

The report should name the tests actually run and preserve their outputs.
Together, the stage comparison, output hashes and executed workloads
would turn the integration plan into a new checkpoint.

At the start of the book, the whole executable fit within a byte-by-byte
reading. The tools now exceed that scale, but each handoff still has a
source, a builder and a result we can inspect. Adding the next compiler
means making one more such handoff explicit. That is the method to carry
beyond this route.

## Try it

Forth-bootstrap has no GCC 15.2 checkpoint. The following command is quoted from seed-forth's README, for that repository only ([`gcc64/README.md:14`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/README.md#L14)). `DIR` denotes an existing build root from its TinyCC-based route, with the preceding compiler stages and pinned archive cache ready. It rebuilds the final compiler and runs verification, writing installations and logs under that root. Allow hours for preparation and build work; the recorded host timing is not a guest estimate.

<!-- check-tryit: the runner selects only shell blocks piped into ./seed-forth; this different-repository command requires seed-forth's TinyCC-based preceding stages, pinned archives, and hours of compiler build work. -->
<!-- tryit: skip -->
```sh
BUILDROOT=DIR gcc64/run-gcc64.sh stage11 stage12
```

No output is reproduced here. This command requires the historical
seed-forth environment; it is not a checkpoint for this checkout.

## Exercise

Hints and feedback are in [Appendix H](66-exercise-feedback.md#chapter-56-plan-a-port-without-inheriting-its-measurements).

**Modify (moderate).** Read seed-forth's final compiler recipe and stage verification. List the inputs an extension would inherit from forth-bootstrap's completed climb, then separate the files it would need to add from the measurements it would need to make. For each proposed success criterion, name the log or pinned artifact you would export from K1. Explain why importing seed-forth's output digests would not by itself verify the guest extension.
