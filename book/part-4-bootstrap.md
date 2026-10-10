# Part 4 — bootstrap

Part 4 turns the compiler into a toolchain and then uses the toolchain to
build everything else. By the end, a run that starts from `hex0-seed` and
the pinned source archives has rebuilt GCC 4.0.4 until it reproduces
itself. It has also climbed to GCC 10.5.0 and booted Linux 7.2.8 inside
QEMU, under kernels that the route built itself.

Most checkpoints in this Part are long builds. Each one says what it
needs: pinned archives, bwrap and strace, or QEMU with KVM. Where a run
is too long to repeat, the chapter shows the output of a recorded run and
labels it as recorded.

- [Chapter 50](50-seed-cc-fixed-point.md) builds `seed-cc` and `seed-ar`,
  the command-line driver and archiver around the Forth compiler, from the
  seed alone.
- [Chapter 51](51-owning-the-tools.md) uses them to build kaem, make, the
  parser generators and bash 2.05b, and so owns the tools that run GCC's
  build.
- [Chapter 52](52-gcc-4-fixed-point.md) builds binutils and GCC 4.0.4. It
  then rebuilds GCC until the installed files of stages 2, 3 and 4 agree,
  and builds the late tools with that compiler.
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
