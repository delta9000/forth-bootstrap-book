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

Follow the builder as well as the product. At one handoff, seed-cc
produces GCC; at the next, GCC becomes the builder. At another, the seed
builds a kernel that will run the next compiler. Keeping those roles
visible is the key to understanding how the route grows.
