# Chapter 56 — Epilogue: onward to GCC 15.2

GCC 15.2.0 already stands at the end of a bootstrap route in [seed-forth](https://github.com/delta9000/seed-forth). The climb stayed in that older project when forth-bootstrap's direct route to Linux was extracted (`forth-bootstrap/HISTORY.md:28`). Bringing it across would produce a new guest checkpoint; the existing sources give us a concrete integration plan, not a command that works here.

This chapter reads the historical seed-forth snapshot [0dd2b8815cae](https://github.com/delta9000/seed-forth/tree/0dd2b8815caeb5b9814567036f4ce101fdebeb21), the extraction revision named in `forth-bootstrap/HISTORY.md:3–4`. All `gcc64/` links below belong to that snapshot, outside this book's submodule. The line links identify inspected recipes and recorded results; no fresh GCC 15 build is reported here.

## The route that stayed behind

The scripts have different shapes. Seed-forth's default stage list runs from `stage0` through `stage12`; forth-bootstrap selects `bridge`, then `stage6` through `stage10` (seed-forth's [`gcc64/run-gcc64.sh:799–803`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/run-gcc64.sh#L799-L803); `forth-bootstrap/chain/gcc64/run-gcc64.sh:452`). Seed-forth reaches gcc-A through TinyCC, musl and binutils (`forth-bootstrap/HISTORY.md:28`). Forth-bootstrap reaches it from the direct GCC 4.0.4 of Chapter 52, through the bridge stage of Chapter 55 (`forth-bootstrap/chain/gcc64/run-gcc64.sh:267`).

That distinction must survive an extension: importing the final compiler build does not require changing the route's beginning.

The continuation in seed-forth is small at the orchestration level:

| Step | Input → result | Source in seed-forth |
|---|---|---|
| `stage11` | GCC 10.5.0 → GCC 15.2.0 bootstrap, comparison and C/C++ tests | [`gcc64/run-gcc64.sh:697–712`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/run-gcc64.sh#L697-L712) |
| `stage12` | Installed compilers → compiled and executed test programs; final tool-path checks | [`gcc64/run-gcc64.sh:719–768`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/run-gcc64.sh#L719-L768) |

These are gcc64 stage names. Forth-bootstrap's `chain/ladder/stage12.sh` builds Linux; it is a different script with a different responsibility (Chapter 55). Reusing a number in a new integration must not silently replace the Linux build.

Seed-forth's README records a successful compiler comparison and the tests it checked ([`gcc64/README.md:163–189`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/README.md#L163-L189)). Those results belong to that run. Its timing record also predates the default stage-zero migration to direct TinyCC; the README explicitly separates the recorded control run from the current starting route ([`gcc64/README.md:141–144`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/README.md#L141-L144)). The extension has precedent, but its evidence belongs to that route and that run.

## Keep the build's actual boundary

The final compiler recipe uses the existing sysroot, its GMP, MPFR and MPC libraries, and the existing binutils. It selects C and C++, enables bootstrap, and disables several optional runtime libraries and compiler facilities (seed-forth's [`gcc64/build-gcc15.sh:18–29`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/build-gcc15.sh#L18-L29)). This is a particular compiler configuration. “GCC 15.2.0” alone does not specify what was built.

The important change from the preceding recipe is `--enable-bootstrap`: seed-forth's GCC 10.5.0 recipe uses `--disable-bootstrap` ([`gcc64/build-gcc10.sh:29`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/build-gcc10.sh#L29)). The final recipe builds with the supplied compiler and then rebuilds with its own outputs. Its caller requires the log to contain `Comparison successful` before proceeding to the C and C++ tests ([`gcc64/run-gcc64.sh:704`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/run-gcc64.sh#L704)). A port should retain that failure condition, rather than treating an installed `gcc` as sufficient evidence.

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

The report should name the tests actually run and preserve their outputs. Matching compiler stages, matching recorded hashes and executing workloads answer different questions. An extension earns its checkpoint through those observations; a version string is only identification.

## Try it

Forth-bootstrap has no GCC 15.2 checkpoint. The following command is quoted from seed-forth's README, for that repository only ([`gcc64/README.md:14`](https://github.com/delta9000/seed-forth/blob/0dd2b8815caeb5b9814567036f4ce101fdebeb21/gcc64/README.md#L14)). `DIR` denotes an existing build root from its TinyCC-based route, with the preceding compiler stages and pinned archive cache ready. It rebuilds the final compiler and runs verification, writing installations and logs under that root. Allow hours for preparation and build work; the recorded host timing is not a guest estimate.

<!-- check-tryit: the runner selects only shell blocks piped into ./seed-forth; this different-repository command requires seed-forth's TinyCC-based preceding stages, pinned archives, and hours of compiler build work. -->
<!-- tryit: skip -->
```sh
BUILDROOT=DIR gcc64/run-gcc64.sh stage11 stage12
```

This book shows no output for it: the command belongs to seed-forth, and forth-bootstrap has not run it.

## Exercise

Hints and feedback are in [Appendix H](66-exercise-feedback.md#chapter-56-plan-a-port-without-inheriting-its-measurements).

**Modify (moderate).** Read seed-forth's final compiler recipe and stage verification. List the inputs an extension would inherit from forth-bootstrap's completed climb, then separate the files it would need to add from the measurements it would need to make. For each proposed success criterion, name the log or pinned artifact you would export from K1. Explain why importing seed-forth's output digests would not by itself verify the guest extension.
