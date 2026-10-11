# Appendix C — Historical reproducibility routes

A reproducibility result belongs to a particular route, input set and comparison. Forth-bootstrap keeps the direct route to Linux; the earlier project's other routes remain historical evidence (`forth-bootstrap/HISTORY.md:8`). This appendix separates the checks available here from the results retained elsewhere, so a matching artifact has a precise meaning.

## The projects around the seed

The bootstrappable-builds community supplies much of the surrounding work.
The project's credits name Jeremiah Orians' stage0-posix, mescc-tools,
M2-Planet and M2libc, alongside live-bootstrap
(`forth-bootstrap/CREDITS.md:42`). Their connections to this checkout are
concrete:

| Project | Connection to forth-bootstrap | Source |
| --- | --- | --- |
| stage0-posix | Supplies the starting `hex0-seed` binary and the mescc-tools-extra utility sources. | `forth-bootstrap/CREDITS.md:12–13` |
| mescc-tools | Supplies kaem, the shell source used by the route. | `forth-bootstrap/CREDITS.md:14` |
| M2-Planet | Supplies the C compiler source used for the Stage A comparison. | `forth-bootstrap/CREDITS.md:15` |
| live-bootstrap | Supplies patches and much of the ordering followed by the GCC climb. | `forth-bootstrap/CREDITS.md:16–17`, `forth-bootstrap/CREDITS.md:44` |

These are different kinds of dependency. An inherited executable is already
machine code when the route begins. Inherited source requires a builder.
A borrowed patch or build order carries knowledge about how to make
upstream packages work together. Keep those distinctions when reading a claim
that a project builds “from source.”

## How the route changed

forth-bootstrap began as route D of the older **seed-forth project**, then
moved into its own repository (`forth-bootstrap/HISTORY.md:3`). Distinguish
that project name from the executable named `seed-forth`, which remains in
this checkout (`forth-bootstrap/README.md:16`).

The older project explored several onward routes. Its history records a
route to self-hosted M2-Planet and a handoff into stage0-posix's recipes;
it also records direct TinyCC and pnut routes. Those routes stayed in the
older project when forth-bootstrap split off
(`forth-bootstrap/HISTORY.md:19–34`). Their reproducibility accounts below are historical records, rather than
the operating instructions for this checkout.

The current route has a different center: the Forth C compiler leads to
`seed-cc`, the tools it builds, and GCC. That is the route identified as D
in the project history (`forth-bootstrap/HISTORY.md:7–10`). The plumbing
recipe orders the tool-building stages before invoking the GCC chain
(`forth-bootstrap/chain/plumbing/chain.kaem:12–16`). Chapter 50 follows
`seed-cc`; Chapter 51 follows those tools; Chapter 52 follows the GCC rebuilds.

What sets this route apart is its middle. After the 229-byte `hex0-seed`
assembles the Forth seed, a C compiler written in that Forth builds the
driver, shell and first Unix tools, and those build GCC 4.0.4, then GCC
10.5.0, then Linux 7.2.8, with no compiler brought in from outside
(`forth-bootstrap/README.md:3–7`). The project history calls it the route
that reaches Linux with no other compiler at all
(`forth-bootstrap/HISTORY.md:7–8`).

M2-Planet still has a role here as a comparison target. Stage A compares
assembly emitted by a Forth-built M2-Planet with assembly emitted by a
GCC-built reference on the same M2-Planet source. The script compares those
outputs, not the compiler executables themselves
(`forth-bootstrap/tests/cc/stage-a-check.sh:57–76`). Chapter 38 returns to
that check. Agreement on this input is a bounded result, not a claim about
every C program.

## What forth-bootstrap checks today

The quick-check entry point is `check-all.sh`. Its header names the checks,
their prerequisites and the longer runs that require an explicit opt-in
(`forth-bootstrap/check-all.sh:4`). Each check supports a specific claim:

| Check | What it tests | Source |
|---|---|---|
| Seed | Assemble the annotated hex source into `seed-forth` | `forth-bootstrap/check-all.sh:5` |
| Tests | Exercise seed primitives, the Forth library and the first compiler layers | `forth-bootstrap/check-all.sh:7` |
| Assembler | Assemble and link a small M1 program, then check its execution | `forth-bootstrap/check-all.sh:9` |
| Driver rebuild | Build `seed-cc` and `seed-ar` with seed Forth, then rebuild both with that compiler and compare bytes | `forth-bootstrap/check-all.sh:11` |
| Pins | Check archive-pin agreement with `MANIFEST.sha256` | `forth-bootstrap/check-all.sh:13` |
| Stage A | Compare M2-Planet's emitted M1 against a GCC-built reference | `forth-bootstrap/check-all.sh:14` |
| K1 build | Check the seed-built kernel, object agreement with seed-cc and assembly agreement with GNU as | `forth-bootstrap/check-all.sh:16` |

Stage A is taught in [Chapter 38](38-main-and-bootstrap-chain.md). The driver rebuild belongs to [Chapter 50](50-seed-cc-fixed-point.md); the kernel construction belongs to [Chapter 54](54-k0-and-k1.md).

The default run includes the rows above. Missing GCC skips Stage A; missing `strace`, GNU `as` or Python skips the K1 build check. A missing Python also skips the pins check. The console distinguishes `OK`, `SKIP` and `FAIL`, and each executed step writes its output to a separate log under `TMPDIR`, defaulting to `/tmp` (`forth-bootstrap/check-all.sh:30`; `forth-bootstrap/check-all.sh:62`). A skip means the check supplied no result. It cannot be counted as agreement.

The sealed chain and guest executions are separate choices. `CHECK_CHAIN=1` adds the host chain to the GCC fixed point; `CHECK_K1=smoke` adds the guest smoke run; `CHECK_K1=linux` adds the guest Linux route (`forth-bootstrap/check-all.sh:21`). The fixed-point comparison is taught in [Chapter 52](52-gcc-4-fixed-point.md), the sealed host run in [Chapter 53](53-sealed-run.md), and the Linux handoff in [Chapter 55](55-linux-and-kexec.md). Passing the quick checks alone does not execute these opt-in branches (`forth-bootstrap/check-all.sh:81`).

Host reference tools have a different role from tools in the bootstrap lineage. The README assigns host GCC, GNU as and NASM to comparisons, and says their output is not used by the route. It separately lists the host kernel and isolation tools for the sealed run, and QEMU, KVM and the CPU for the guest run (`forth-bootstrap/README.md:89`). “No outside compiler” describes the construction route; it does not mean every verification task avoids a reference compiler.

### Recorded results

The following are repository records, not fresh executions of the sealed chain or guest route. The README dates each row of its Results table and keeps the reports in `results/` (`forth-bootstrap/README.md:231`).

| Recorded item | Result in the README | Source |
|---|---|---|
| Seed | `seed-forth`: 1,772 bytes | `forth-bootstrap/README.md:236` |
| Quick checks (2026-10-10) | 7 OK; Stage A compared 2,367,260 bytes of identical M1 | `forth-bootstrap/README.md:236` |
| Sealed host chain | 18 minutes wall clock; stage D reported stage 2 = 3 = 4, with 54 files each and 0 differing | `forth-bootstrap/README.md:237` |
| K1 | 221,672 bytes, built from seed Forth with its seed-built recipe runner and no inherited compiler | `forth-bootstrap/README.md:238`; `forth-bootstrap/kernel/k1/tests/direct-build-check.sh:4–6` |
| Guest Linux route | 1 h 38 min; stage D fixed point, late tools, all 31 gcc64 pins matched, Linux 7.2.8 booted by kexec | `forth-bootstrap/README.md:239` |
| Linux image | bzImage: 1,278,976 bytes | `forth-bootstrap/README.md:240` |

HISTORY records agreement with seed-forth's earlier run of the same route: the Linux image, gcc64 pins, stage D report and late-tool program hashes. It records differences in K1, seed-cc and seed-ar, with their causes (`forth-bootstrap/HISTORY.md:13`). Agreement is artifact-specific. It does not imply that every executable copied between projects must have the same digest.

## Routes retained in seed-forth

[seed-forth](https://github.com/delta9000/seed-forth) retains the alternatives listed in HISTORY. Forth-bootstrap extracted its direct route; the other successes remain attached to the earlier project's sources and recipes (`forth-bootstrap/HISTORY.md:3`; `forth-bootstrap/HISTORY.md:19`). A route recorded there is not an extra mode of the quick-check script here.

| Historical route | What HISTORY preserves | Source |
|---|---|---|
| Direct TinyCC | Seed Forth compiles TinyCC; repeated TinyCC builds agree; the ladder continues through the small kernels to Linux | `forth-bootstrap/HISTORY.md:21–25` |
| pnut | Seed Forth builds unmodified pnut for i386 and amd64, and pnut self-hosts | `forth-bootstrap/HISTORY.md:26` |
| gcc64 continuation | The TinyCC-based beginning and the later GCC 15.2.0 bootstrap remain in the earlier project | `forth-bootstrap/HISTORY.md:28` |
| M2-Planet and handoff | `bootstrap.sh` reaches self-hosted M2-Planet; `handoff.sh` feeds the Forth route into stage0-posix's recipes and reproduces their answer binaries | `forth-bootstrap/HISTORY.md:31` |

The TinyCC record says its repeated builds match the result reached through pnut. The same history records its Linux route passing under QEMU/KVM (`forth-bootstrap/HISTORY.md:22`). Those are useful cross-route observations, but neither turns TinyCC into a required intermediate compiler in forth-bootstrap's direct route (`forth-bootstrap/HISTORY.md:8`).

The gcc64 continuation belongs to [Chapter 56](56-gcc-15-epilogue.md). HISTORY records its final compiler bootstrap reaching stage2 = stage3, with artifact pins kept in the earlier project's `gcc64/HASHES` (`forth-bootstrap/HISTORY.md:29`). That record does not supply a completed forth-bootstrap guest extension.

### The GCC-free build

A GCC-free build reaches its target without an inherited GCC compiler building its tools. It can still be compared against a reference built with GCC. The distinction is visible in the Stage A header: this check uses host GCC for the reference, while assigning the earlier GCC-free self-host and other comparisons to seed-forth (`forth-bootstrap/tests/cc/stage-a-check.sh:4`).

For the historical M2-Planet route, HISTORY records `bootstrap.sh` reaching v2 = v3, followed by a handoff reproducing all 19 amd64 and all 19 x86 stage0-posix answer binaries (`forth-bootstrap/HISTORY.md:31`). Keep that result under its historical script names. Forth-bootstrap's current replacement is the direct chain and its sealed or guest execution, whose trust boundaries are documented separately (`forth-bootstrap/README.md:85`).

### Diverse double-compiling

Diverse double-compiling asks whether differently rooted compiler lineages can compile the same source through comparable rebuilds and reach the same result. The diversity matters because a self-consistent rebuild alone can preserve a defect inherited from its starting compiler. Agreement becomes stronger evidence when the routes do not inherit the same compiler machinery.

The historical handoff provides a related, narrower record: the Forth-fed
stage0-posix recipes reproduced the published answer binaries
(`forth-bootstrap/HISTORY.md:31`). That record establishes the reported
agreement. It does not document which tools the rebuilds shared, or
provide the detailed lineage comparison needed to assess a diverse
double-compiling argument.

Stage A also uses different compiler origins, but its actual comparison is emitted M1 on M2-Planet's self-compilation input. Its header explicitly excludes the subsequent M2-Planet self-hosting stages (`forth-bootstrap/tests/cc/stage-a-check.sh:7`; `forth-bootstrap/tests/cc/stage-a-check.sh:12`). Read the comparison that the script performs, rather than inferring a larger proof from the presence of a reference compiler.

## What byte-identical means, and what it proves

Byte-identical means that the compared files contain exactly the same bytes. The comparison point matters: Stage A compares emitted M1, rather than the differently built compiler executables (Chapter 38). Its `cmp` rejects a difference in those output files (`forth-bootstrap/tests/cc/stage-a-check.sh:73`). No claim about every possible C input follows from that particular comparison.

The driver rebuild compares the executable files for seed-cc and seed-ar directly (`forth-bootstrap/tests/cc/seed-cc-rebuild-check.sh:23`). Stage D's comparison has a documented archive exception: archive member names, order and bytes can agree even when the archive containers differ (Chapter 52). The implementation falls back to that member comparison after a whole-file comparison fails (`forth-bootstrap/chain/gcc-direct/stage-d.sh:133`; `forth-bootstrap/chain/gcc-direct/stage-d.sh:154`). “Fixed point” must be interpreted using that comparator, not as an unstated promise about every container byte.

The combined evidence supports construction, agreement and execution claims within named boundaries. The README records a sealed host root starting from hex0-seed, a compiler fixed point and a guest-built Linux kernel that boots (`forth-bootstrap/README.md:237`; `forth-bootstrap/README.md:239`). The source and archive assumptions remain explicit: repository sources, pinned upstream archives and vendor sources are inputs the route trusts (`forth-bootstrap/README.md:85`).

These results do not establish that the sources are correct for all inputs, or that the execution environment is uncompromised. The trust list retains the host kernel for the host route and QEMU, KVM and the CPU for the guest route (`forth-bootstrap/README.md:89`). Reproducing an artifact narrows uncertainty about its provenance; it does not remove the assumptions under which its builder ran.

## Exercise

**Trace (easy).** Choose a row from the recorded Results table above. Identify its comparison point, its execution boundary and the source that records the outcome. Then find its corresponding quick check or opt-in branch in `check-all.sh`. Explain why an `OK` from a different branch would not establish the same claim.
