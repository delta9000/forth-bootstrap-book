# Part 4 — bootstrap

We can compile a C program. Now try to build a compiler that comes with
Makefiles, generated parsers, shell scripts and a C library. Each tool
the build expects becomes another program we must first construct.
Part 4 solves those dependencies until GCC can rebuild itself, then
repeats the route under kernels we build on the way to Linux.

Chapters 50–53 construct and audit the toolchain on the host kernel.
Chapters 54–55 move construction into QEMU: K0 starts the seed, the seed
builds K1, and the long guest route rebuilds the tools under K1 before
climbing to GCC 10.5.0 and booting Linux 7.2.8.

These are related build routes, not one uninterrupted run. The guest
starts with a host-prepared boot image containing the initial seed;
Chapter 54 identifies that handoff. The later compilers and tools are
then built inside the guest from the supplied sources.

This Part mixes short tool builds and trace checks with sustained
bootstrap runs. Chapters 50–51 build small tools; Chapter 53 can check
pins and a synthetic trace without rebuilding GCC. The full host and
Linux routes in Chapters 52 and 55 need more time and resources. Each
checkpoint states its prerequisites, and output from an earlier run is
labelled as recorded.

- [Chapter 50](50-seed-cc-fixed-point.md) builds `seed-cc` and `seed-ar`,
  the command-line driver and archiver around the Forth compiler, from the
  seed alone.
- [Chapter 51](51-owning-the-tools.md) uses them to build kaem, the file
  utilities from mescc-tools-extra, make, the parser generators and bash
  2.05b, and so owns the tools that run GCC's build.
- [Chapter 52](52-gcc-4-fixed-point.md) builds binutils and GCC 4.0.4. It
  then rebuilds GCC until the installed files of stages 2, 3 and 4 agree,
  and follows the late-tool recipe that the guest route runs with that
  compiler.
- [Chapter 53](53-sealed-run.md) audits that run. It starts in a root whose
  only executable is `hex0-seed`, and every `execve` is traced.
- [Chapter 54](54-k0-and-k1.md) moves the route off the host kernel. QEMU
  boots K0, seed Forth builds the C kernel K1, and K1 runs the tools.
- [Chapter 55](55-linux-and-kexec.md) climbs to GCC 10.5.0 under K1,
  builds Linux 7.2.8, writes the results to disk and hands the machine
  over to the new kernel.
- [Chapter 56](56-gcc-15-epilogue.md) closes the book with GCC 15.2. That
  climb exists in the older seed-forth project, and the chapter sets out
  what bringing it into forth-bootstrap would take.

Follow the builder as well as the product. At one handoff, seed-cc
produces GCC; at the next, GCC becomes the builder. At another, the seed
builds a kernel that will run the next compiler. Keeping those roles
visible is the key to understanding how the route grows.

## Choose your route through this Part

- **Inspect only:** read the handoffs, then complete the
  [evidence checkpoint below](#short-checkpoint-build-an-evidence-ledger).
  No compiler build or QEMU installation is needed.
- **Run short checks:** use the driver checkpoint in
  [Chapter 50](50-seed-cc-fixed-point.md#try-it) and the pin/trace checks in
  [Chapter 53](53-sealed-run.md#try-it). Follow each chapter's prerequisites;
  these do not reproduce the long routes.
- **Build the route:** follow the host prerequisites in
  [Chapter 52](52-gcc-4-fixed-point.md#try-it), or the separate guest route in
  [Chapters 54](54-k0-and-k1.md#try-it) and
  [55](55-linux-and-kexec.md#try-it). The recorded Linux run used a 24 GiB
  guest and took 98 minutes. Those are observations, not a minimum RAM
  requirement or a promised runtime. Preserve earlier output before rerunning.

Whichever route you choose, aim to identify each builder and execution
environment, explain what each equality compares, and trace the kernel
image through export, boot and init execution.

## Short checkpoint: build an evidence ledger

Return here after Chapters 52–55. You can complete this checkpoint on
paper: it tests the claims you can justify, without a fresh bootstrap.
For each item below, write **artifact or event; builder; execution
environment; comparison or observation; result; evidence still missing**.
Use “not established by this item” where necessary rather than inventing
an attribution. Label your entries **recorded** or **synthetic**. A fresh
reading of a report is not a fresh run of the reported build.

1. **Recorded guest report.** Stage D reports `Stage 2 vs stage 3: 54
   files, 0 differ.` Its next lines identify stage2's builder as Stage C's
   installed GCC and stage3's builder as stage2's installed GCC
   (`forth-bootstrap/results/k1-2026-10-08/stage-d-report.txt:4–7`).
   State the comparison rule from
   [Chapter 52](52-gcc-4-fixed-point.md#compare-installations-not-build-debris).
   Would two archives that differ only in header timestamps necessarily
   fail that rule?
2. **Synthetic trace.** Process 101 successfully executes `/hex0-seed`;
   process 102 begins an unfinished exec of the built bash; process 103's
   `/usr/bin/arch` exec fails with `ENOENT`; process 102 resumes with result
   zero. This is the sample in
   [Chapter 53](53-sealed-run.md#read-successes-separately-from-attempts),
   not a retained guest trace. Count completed successes, completed
   failures and pending calls. Repeat after deleting the resumed line.
3. **Recorded guest pins.** The serial log reports `pins: 31 as pinned,
   0 differ, 0 path-dependent and not comparable here`
   (`forth-bootstrap/results/k1-2026-10-08/serial.log:1202`). Contrast this
   output comparison with an input archive's successful SHA-256 check
   against `MANIFEST.sha256`. Which would identify bzImage?
4. **Recorded handoff.** The same serial log reports
   `finish: results written to hdb`, then a Linux version banner, then
   `init: hello from a Linux kernel built from hex0 and seed-forth`
   (`forth-bootstrap/results/k1-2026-10-08/serial.log:1209–1331`). Give each
   observation its own ledger entry. Which entry would you add after
   [reading the output disk on the host](55-linux-and-kexec.md#read-back-the-output-disk)?

<details>
<summary>Hint: choose the question before choosing the evidence</summary>

Ask whether you are checking source identity, repeatability, an attempted
or completed execution, preservation of bytes, or execution after a
handoff. Those questions need different observations. Separate the guest
building the image from the host later reading its exported copy.

</details>

<details>
<summary>Check your ledger</summary>

1. The recorded K1 run compares selected installed files from successive
   GCC builders, not every build-tree byte. Ordinary files compare by
   bytes; readable archives with simple, unique member names compare
   ordered names and each member’s bytes, excluding archive-header metadata.
   The name-based comparator does not establish that rule for duplicate
   member names. Different timestamps alone need
   not fail. This establishes the reported fixed point under that rule,
   not correctness for all C programs or a fresh reproduction by you.
2. The full synthetic trace has **two successes, one failure, zero
   pending calls**. Removing the resumed line leaves **one success, one
   failure, one pending call**. Bash's outcome becomes unknown; `arch`
   still did not execute in that attempt. These records do not establish
   how the executable bytes were built or audit the real route.
3. The 31 matches concern gcc64 compiler/library outputs in the recorded
   guest build and its declared build-root scope. An input hash instead
   identifies source-archive bytes against an expected digest. Neither
   identifies bzImage: it is outside gcc64's pin set. Neither proves
   general compiler correctness. See Chapter 55's separate image digest.
4. The export marker follows a successful tar command under K1; it does
   not independently read the disk back. The Linux banner records
   successor-kernel execution; init's greeting records execution of the
   embedded program under Linux. Host readback adds independently read
   archive members and their digests, with an explicit reference for any
   comparison. It does not itself boot those bytes. Keep fresh readback
   separate from the recorded boot, even if their hashes match.

If you treated all four items as one “PASS”, revisit the relevant
chapter and rewrite only that row with a narrower claim. Then try this
change: a fresh run exports readable files but never prints a Linux
banner. You can claim export/readback, but cannot promote it to evidence
of Linux or init execution. Locate the handoff boundary next.

</details>
