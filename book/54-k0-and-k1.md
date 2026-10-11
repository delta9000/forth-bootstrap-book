# Chapter 54 — K0 and K1

Every `write`, `mmap`, fork and exec in the bootstrap has so far reached
the host's Linux kernel. The compiler and its tools have an ancestry we
can follow, but they still depend on that ready-made operating
environment. To build in a guest, we must supply the services ourselves.

That creates another starting problem: a kernel is a program we want to
compile, yet the compiler needs a kernel on which to run. K0 is the small
first answer, assembled from hex0 on the host. It can run the seed long
enough to build K1 in the guest. K1 then supplies the processes, memory
and files needed by the larger tools
(`forth-bootstrap/kernel/k1/run-chain.sh:2`).

## Prepare the handoffs

Follow the first seed across the boundary. It is the host-built
`seed-forth` from Chapter 1, copied into K0's boot image. Its job under
K0 is to build the next kernel. After the handoff, K1 starts a new
construction from hex0-seed in an imported tree:

| Where execution happens | Builder already available | What it produces |
|---|---|---|
| Host | hex0-seed and image-preparation tools | K0 and a boot image containing the existing seed-forth |
| K0 inside QEMU | That seed-forth, then its new recipe runner | The K1 executable |
| K1 inside the same QEMU machine | The retained runner and imported hex0-seed | A fresh seed-forth, seed-cc, seed-ar and kaem |

The two seed constructions serve different purposes. The copied seed
gets us far enough to build K1; the fresh seed starts the tool route
under K1. The wrapper keeps image preparation on the host and these
compiler invocations in the guest
(`forth-bootstrap/kernel/k1/run-chain.sh:2`).

The host prepares separate images because K0 needs a memory image to start, while K1 reads a disk archive. These lines in `run-chain.sh` assemble K0, prepare the boot image and select the input-image arguments (`forth-bootstrap/kernel/k1/run-chain.sh:31`):

```text
HEX0=${HEX0:-vendor/stage0-posix/bootstrap-seeds/POSIX/AMD64/hex0-seed}
mkdir -p build-out/k1 "$D"
"$HEX0" kernel/k0/k0.hex0 build-out/k1/k0.bin
python3 kernel/k1/mkboot.py build-out/k1/boot.img
set -- "$D/in.img" "$mode"
```

The following image-writing steps create the input disk and an empty
output disk (`forth-bootstrap/kernel/k1/run-chain.sh:37`). `mkboot.py`
supplies the Forth and C sources needed to build K1, with seed-forth
reading `k1-direct-start.fth`. It appends the boot recipe to the build
recipe so that construction and entry happen in order
(`forth-bootstrap/kernel/k1/mkboot.py:4`).

The host Python steps prepare descriptors, page tables and argv as well
as copying source bytes and the existing seed executable
(`forth-bootstrap/kernel/k0/mkfs.py:27`,
`forth-bootstrap/kernel/k0/mkfs.py:64–72`). They compile no guest C or
Forth program. The wrapper does not build or verify that first seed, so
build it from the pinned hex0 source before preparing these images.
The later serial line `seed-forth built by hex0-seed` belongs to the
fresh construction under K1. Unpacking, patching and compiler construction
then take place in the guest (`forth-bootstrap/kernel/k1/run-chain.sh:6`).

QEMU receives K0 as its kernel, K0's file image through the loader, and the input and output images as IDE drives. Keeping the serial log on the host preserves evidence across the kernel handoff (`forth-bootstrap/kernel/k1/run-chain.sh:50`):

```text
"${QEMU:-qemu-system-x86_64}" "$@" $accel -m "$memory" -display none -monitor none \
    -serial file:"$D/serial.log" -no-reboot \
    -device isa-debug-exit,iobase=0xf4,iosize=0x01 \
    -kernel build-out/k1/k0.bin \
    -device loader,file=build-out/k1/boot.img,addr=0x50000000,force-raw=on \
    -drive file="$D/in.img",format=raw,if=ide,index=0 \
    -drive file="$D/out.img",format=raw,if=ide,index=1
```

## K0 supplies just enough execution

K0 needs to run a narrow pattern: start a compiler child, wait for it,
then use its output in the next step. Its serialized fork runs the child
to completion before restoring the saved parent. The runner's fork,
redirect, exec and immediate wait fit that pattern, so this first kernel
can build its replacement without a general scheduler
(`forth-bootstrap/kernel/k0/k0.asm:12`).

`k0.hex0` holds the bytes assembled by hex0-seed; `k0.asm` gives the
readable instructions and design notes
(`forth-bootstrap/kernel/k0/k0.hex0:19`). K0 enters long mode with an
identity map and runs programs with kernel privilege, without interrupts.
It provides no protected user processes (`forth-bootstrap/kernel/k0/k0.asm:3`).

The initial program comes from the boot image's argument block. After installing the syscall entry address, K0 loads that program through its own `execve` handler (`forth-bootstrap/kernel/k0/k0.asm:95`):

```asm
        inc ecx                         ; LSTAR
        mov eax, syscall_entry
        cdq
        wrmsr
        mov edi, INIT + 16
        mov esi, INIT
        call sys_execve
        jmp ret_user
```

For this image the program is seed-forth and its input is the launcher (`forth-bootstrap/kernel/k1/mkboot.py:18`). K0 supplies the handlers behind the library's syscall wrappers (Chapter 18).

The object writer and linker also need calls that K0 lacks. The build loads `k0-syscalls.fth` after the library: it retries `stat` through `lstat`, synthesizes distinct `fstat` identities, treats `munmap` as success without reclaiming memory, and supplies a fixed `getpid` result. These K0 syscall fallbacks activate only after ENOSYS (`forth-bootstrap/kernel/k1/boot/k0-syscalls.fth:1`). They satisfy this build's checks; they do not give K0 general file metadata or memory reclamation.

## Build the replacement with seed Forth

The launcher first builds `amd64-runner`, then replaces itself with that runner to interpret `k1-direct.recipe`. The same launcher can run on the host kernel or under K0 (`forth-bootstrap/kernel/tools/k1-direct-start.fth:3`). The runner is a narrow C program built by the Forth compiler, with explicit executable paths and no shell or PATH search (`forth-bootstrap/kernel/tools/amd64-runner.c:1`).

Its recipe operations separate preparing bytes from starting a program (`forth-bootstrap/kernel/tools/amd64-runner.c:882`, `forth-bootstrap/kernel/tools/amd64-runner.c:939`):

| Operation | Input → result |
|---|---|
| `cat` | Named files → one compiler input stream |
| `run` | Expected status, input, output, error, executable and arguments → checked child execution |
| `same` | Two files → byte comparison |
| `rename` | Temporary object → named object for linking |

Each translation unit gets a fresh seed invocation. In `k1-direct.recipe`, the compiler stream already exists before the unit driver and C source are appended (`forth-bootstrap/kernel/tools/k1-direct.recipe:16`):

```text
cat ${K}/main.input ${K}/compiler.fth ${ROOT}/kernel/k1/boot/unit.fth ${ROOT}/kernel/k1/main.c
run 0 ${K}/main.input ${K}/main.out ${K}/main.err ${ROOT}/seed-forth
same ${K}/empty ${K}/main.out
rename ${K}/unit.o ${K}/main.o
cat ${K}/mm.input ${K}/compiler.fth ${ROOT}/kernel/k1/boot/unit.fth ${ROOT}/kernel/k1/mm.c
run 0 ${K}/mm.input ${K}/mm.out ${K}/mm.err ${ROOT}/seed-forth
same ${K}/empty ${K}/mm.out
rename ${K}/unit.o ${K}/mm.o
```

The recipe repeats this arrangement for the filesystem, processes,
syscall dispatcher, disk driver and Linux handoff source. Chapter 55
follows that last component. Privileged instructions live in
`k1-asm.fth`; the object writer turns its instruction bytes, labels and
relocations into the assembly object
(`forth-bootstrap/kernel/tools/k1-direct.recipe:24`).

The final build steps use the Forth linker rather than a host linker (`forth-bootstrap/kernel/tools/k1-direct.recipe:44`):

```text
cat ${K}/asm.input ${ROOT}/forth/010-lib.fth ${ROOT}/kernel/k1/boot/k0-syscalls.fth ${ROOT}/cc/020-cc-arena.fth ${ROOT}/cc/030-cc-io.fth ${ROOT}/cc/081-cc-object.fth ${ROOT}/kernel/tools/obj-asm.fth ${ROOT}/kernel/k1/k1-asm.fth ${ROOT}/kernel/k1/boot/asm.fth
run 0 ${K}/asm.input ${K}/asm.out ${K}/asm.err ${ROOT}/seed-forth
same ${K}/empty ${K}/asm.out
cat ${K}/link.input ${ROOT}/forth/010-lib.fth ${ROOT}/kernel/k1/boot/k0-syscalls.fth ${ROOT}/cc/020-cc-arena.fth ${ROOT}/cc/030-cc-io.fth ${ROOT}/cc/140-cc-link.fth ${ROOT}/kernel/k1/boot/link.fth
run 0 ${K}/link.input ${K}/link.out ${K}/link.err ${ROOT}/seed-forth
same ${K}/empty ${K}/link.out
chmod ${K}/k1
```

`run` forks, redirects the child's streams, executes with an empty environment, waits and checks the requested exit status (`forth-bootstrap/kernel/tools/amd64-runner.c:507`). In the fragment, a silent successful compilation must also pass `same` against the empty file. The kernel output gets its execute permission only after linking.

K0's appended boot recipe then runs that executable. K1 takes over the machine and never returns to the waiting K0 runner (`forth-bootstrap/kernel/tools/k1-direct-boot.recipe:1`). K0 starts K1 with the same program loader that started seed-forth.

## K1 provides the tools' operating environment

The later tools need more than K0's serial child execution. Make can
have children waiting on pipes while other children run; separate programs
need separate address spaces. K1 runs user processes through
SYSCALL/SYSRET, blocks them on waits and pipes, and preempts user code on
timer ticks (`forth-bootstrap/kernel/k1/README.md:145`). Its memory setup
is the first part of that separation we will follow.

K1 divides the implementation among `main.c` for boot and traps, `mm.c`
for memory, `fs.c` for files, `proc.c` for processes, `sys.c` for syscall
dispatch and `ata.c` for disks. Assembly routines handle privileged machine
operations (`forth-bootstrap/kernel/k1/README.md:215`).

### Two virtual addresses, one physical byte

An instruction uses a **virtual address**; paging translates it to a **physical address** and checks whether the access is allowed. K1 needs both an identity map, where the two addresses are equal, and a direct map, where adding a fixed base gives the kernel another address for the same physical memory. The direct-map arithmetic and allocation page size are explicit in `k1.h` (`forth-bootstrap/kernel/k1/k1.h:20`):

```c
#define NULL ((void *)0)
#define PAGE 4096UL
#define KBASE 0xFFFF800000000000UL /* direct map of physical memory */
#define P2V(p) ((void *)((u64)(p) + KBASE))
#define V2P(v) ((u64)(v) - KBASE)
#define ALIGNUP(x, a) (((x) + (a) - 1) & ~((a) - 1))
#define ALIGNDN(x, a) ((x) & ~((a) - 1))
```

`P2V(0x201234)` gives `0xFFFF800000201234`; `V2P` subtracts `KBASE` to recover `0x201234`. These macros only calculate addresses. The page tables must make both this high address and the low identity address `0x201234` reach the same physical byte.

For the listing below, read **PML4** (page-map level 4) as the root table, **PDPT** (page-directory-pointer table) as the next table, and **PD** as a page directory. An entry either stores the physical address of the next table or ends the walk at a **leaf**, giving the physical base of a mapped region. In these entries, `3` sets present and writable; `0x83` also sets the large-page bit. A large leaf at PDPT level covers 1 GiB; at PD level it covers 2 MiB. Thus the allocator's `PAGE = 4096` does not make every mapping 4 KiB. The hardware formats are specified in [Intel's system programming manual, §4.5](https://cdrdv2-public.intel.com/819714/253668-sdm-vol-3a.pdf); K1 names these flag bits in `mm.c` (`forth-bootstrap/kernel/k1/mm.c:195`).

Here is a manual translation trace through the tables this code constructs, not an executed memory read (`forth-bootstrap/kernel/k1/main.c:314`):

<figure class="mechanism" aria-labelledby="alias-caption">
<div class="mechanism-title">Two routes to the same physical byte</div>
<div class="diagram-routes diagram-aliases">
<div><span class="diagram-label">Low identity address</span><strong><code>0x201234</code></strong><span class="diagram-route">pml4[0] → pdpt_low[0] → pd_low[1]</span><span>2 MiB leaf: base 0x200000 + offset 0x1234</span></div>
<div><span class="diagram-label">High direct-map address</span><strong><code>0xFFFF800000201234</code></strong><span class="diagram-route">pml4[256] → pdpt_dm[0]</span><span>1 GiB leaf: base 0 + offset 0x201234</span></div>
</div>
<div class="diagram-merge" aria-hidden="true">↓ &nbsp; ↓</div>
<div class="diagram-result diagram-accent"><strong>Physical byte 0x201234</strong><br>One location in RAM, accessible through either virtual address.</div>
<figcaption id="alias-caption">These are two distinct page-table walks. P2V and V2P only perform address arithmetic; the mappings make the aliases work. The different leaf sizes explain why the high route stops one level earlier.</figcaption>
</figure>

Both flag values leave the user-access bit (`4`) clear. These mappings are **supervisor-only**: K1's privileged kernel code can use them; a restricted user process cannot read or write them merely by choosing the same address. Sharing the upper map therefore does not grant user access ([Intel, §4.6](https://cdrdv2-public.intel.com/819714/253668-sdm-vol-3a.pdf)).

`load_cr3` selects the root by loading its **physical** address into the CPU's CR3 register, an operation reserved for privileged code (`forth-bootstrap/kernel/k1/k1-asm.fth:87`). Here the table pointers still use K0's identity mapping, so their numeric values already are physical addresses. Loading CR3 changes translation, not the addresses held in registers or the bytes in RAM. This small model omits translation caches, detailed address-bit selection and fault handling; it is enough to follow which addresses survive a handoff.

The low mapping reserves space for K1 itself rather than user images (`forth-bootstrap/kernel/k1/main.c:314`):

```c
    memset(pml4, 0, 4 * 4096);
    for (i = 0; i < 512; i++)
        pdpt_dm[i] = i << 30 | 0x83;            /* 1 GiB pages: all RAM at KBASE */
    pd_low[0] = 0x000000 | 0x83;                /* 0-4 MiB: K1's image, kernel only */
    pd_low[1] = 0x200000 | 0x83;
    pdpt_low[0] = (u64)pd_low | 3;
    pml4[0] = (u64)pdpt_low | 3;
    pml4[256] = (u64)pdpt_dm | 3;
    load_cr3((u64)pml4);
    kpml4 = (u64 *)P2V(pml4);
    kpd_low = (u64 *)P2V(pd_low);
```

The build check rejects a K1 image extending beyond that mapping (`forth-bootstrap/kernel/k1/tests/direct-build-check.sh:59`). User processes receive their own page tables, while the upper direct map remains shared (`forth-bootstrap/kernel/k1/mm.c:202`). `struct mm` tracks the break and the next downward mmap placement separately, so heap growth and mapped regions can be checked for overlap (`forth-bootstrap/kernel/k1/k1.h:161`). Physical memory comes from QEMU's e820 map; mapped user regions acquire zeroed pages on demand. Fork copies present pages. Guest RAM must accommodate both the file system and process memory (`forth-bootstrap/kernel/k1/README.md:130`).

The tool-facing services include file and directory operations,
fork/exec/wait, pipes, memory mapping, clocks and signals. Console, null,
zero and random devices support the runtime; `/proc/self/exe` lets
seed-cc locate its source tree (`forth-bootstrap/kernel/k1/README.md:154`).

The header bounds each process's descriptor array with `NFD`, and its signal tables with `NSIG` (`forth-bootstrap/kernel/k1/k1.h:177`). Compatibility also has behavioral limits: static ELF is supported, but an ELF requiring an interpreter is rejected; file-backed mappings are private copies; threads and sockets are unavailable. Unlisted syscalls return ENOSYS (`forth-bootstrap/kernel/k1/README.md:176`, `forth-bootstrap/kernel/k1/README.md:195`). These are workload contracts, not a complete Linux implementation.

## Import the new root and retain the builder

K1's input image stores names, modes and file contents. The host marks hex0-seed as the starting tree's only executable (`forth-bootstrap/kernel/k1/mkdisk.py:23`). The archive carries a magic signature, record headers and aligned payloads; K1's disk importer recreates directories and copies regular-file contents into RAM (`forth-bootstrap/kernel/k1/ata.c:161`). The imported files live in RAM; subsequent writes change that RAM tree.

Boot establishes storage before selecting the initial process. K0's files move under `/k0/` when a disk tree exists, preserving the runner and the sources that built K1 (`forth-bootstrap/kernel/k1/main.c:490`):

```c
    phys_init();
    fs_init();
    ata_init();
    /* With a starting tree on hda, it is / and K0's files (which built
     * this K1) move to /k0; without one, K0's files are /. */
    fs_import_k0(disk_import() ? "k0/" : "");
```

The disk image's `/k1.args` names `/k0/build-out/amd64-runner`, `--recipe` and `/k1.recipe`. K1 reads those arguments and starts init with them (`forth-bootstrap/kernel/k1/mkdisk.py:64`, `forth-bootstrap/kernel/k1/main.c:497`). Thus the builder crosses the handoff as a file, then runs as a K1 user process.

The input drive is hda. The output drive is exposed as `/dev/hdb` for
explicit writes; files created in the RAM root do not automatically
appear on that disk. The longer route writes a tar archive to hdb
(`forth-bootstrap/kernel/k1/README.md:161`). Chapter 55 follows that
export and the handover to Linux through `--direct-linux`.

The smoke recipe starts construction again inside K1, from hex0-seed. Its initial steps publish seed-forth and build the compiler driver and archiver (`forth-bootstrap/kernel/k1/direct-smoke.recipe:7`):

```text
run 0 - /dev/console /dev/console /hex0-seed /seed/000-seed.hex0 /seed-forth
chmod /seed-forth
say "k1: seed-forth built by hex0-seed"
run 0 /cc/driver/seed-cc-start.fth /dev/console /dev/console /seed-forth
say "k1: seed-cc and seed-ar built by seed Forth"
mkdir /build-out/plumbing
mkdir /build-out/plumbing/bin
mkdir /build-out/k1-smoke
```

Next seed-cc builds kaem, and kaem runs the smoke recipe under K1 (`forth-bootstrap/kernel/k1/direct-smoke.recipe:15`). Kaem's role is already established (Chapter 51). The boundary test compiles a C object, archives it with seed-ar and links the executable from that archive, so execution exercises the built tools together (`forth-bootstrap/kernel/k1/direct-smoke.kaem:12`):

```text
CC=./build-out/seed-cc/seed-cc
AR=./build-out/seed-cc/seed-ar
X=vendor/stage0-posix/mescc-tools-extra
O=build-out/k1-smoke

# A program from an archive: compile, archive, link with -L and -l.
${CC} -c -Werror=implicit-function-declaration kernel/k1/tests/direct-smoke.c -o ${O}/direct-smoke.o
${AR} rcs ${O}/libsmoke.a ${O}/direct-smoke.o
${CC} -static -L${O} -lsmoke -o ${O}/direct-smoke
```

The resulting program tests the runtime's operating-system calls, then the recipe builds and runs the stage0-posix mkdir and sha256sum tools (`forth-bootstrap/kernel/k1/direct-smoke.kaem:22`). A passing guest marker therefore covers compilation, archive selection, program loading and execution under the kernel that seed Forth built.

## Try it

Run both checkpoints from the forth-bootstrap checkout root, after Chapter 1's seed build. The guest-image preparation needs Python 3 and an existing, current `seed-forth`; it does not refresh that binary for you. The build check needs GNU as for the assembly comparison and strace for the execution audit. It replaces `build-out/k1-direct`, writes the trace at `build-out/k1-direct.trace`, and compares the C objects with seed-cc output (`forth-bootstrap/kernel/k1/tests/direct-build-check.sh:26`). On the recorded host it took about nine seconds.

<!-- check-tryit: the runner selects seed-forth pipe blocks and omits kernel/ and vendor/; this host audit also needs strace and GNU as. -->
<!-- tryit: skip -->
```sh
sh kernel/k1/tests/direct-build-check.sh
```

Recorded build-check output, with the build banner, digest and timing lines omitted:

```text
direct-build-check: recipe lists all 29 compiler layers
direct-build-check: 12 execve calls, all the seed or the runner
direct-build-check: the seven C objects equal seed-cc -nostdinc -c's
asm-check: k1-asm.fth's bytes equal as on its comments: 801 text bytes, 384 data bytes, 32 globals, 55 relocations
direct-build-check: K1 is 221672 bytes, image 0x200000-0x283d48, entry 0x201000
```

The guest checkpoint needs QEMU and uses KVM when `/dev/kvm` is writable. It recreates the disk images under `build-out/k1-direct-smoke` and records the console in `serial.log`; preserve earlier outputs before running it (`forth-bootstrap/kernel/k1/run-chain.sh:26`). On the recorded host it took about seventeen seconds with KVM.

<!-- check-tryit: the scratch runner omits kernel/ and vendor/ and cannot launch this QEMU guest; QEMU and preferably KVM are host prerequisites. -->
<!-- tryit: skip -->
```sh
kernel/k1/run-chain.sh --direct-smoke
```

Recorded host output:

```text
build-out/k1/boot.img: 51 files, 7 dirs, 1393136 bytes
build-out/k1-direct-smoke/in.img: 214 files, 1 MiB
run-chain: qemu exit 1 (expected 1)
run-chain: PASS (--direct-smoke)
```

The serial log's K0 handoff marker starts with `k0: K1 built by seed Forth`. These complete lines follow it; intervening recipe echoes and individual check lines are omitted:

```text
k1: starting
k1: hda: 1 MiB
k1: hdb: 4096 MiB
k1: imported 214 files, 1 MiB from hda
k1: imported 93 files, 8163 KiB from K0 into /k0/
k1: seed-forth built by hex0-seed
k1: seed-cc and seed-ar built by seed Forth
k1: kaem built by seed-cc
direct-smoke: all 26 checks passed
k1: PASS (seed-cc, seed-ar and kaem work under the K1 that seed Forth built)
k1: init exited with status 0
```

The host audit checks which executables performed the build and compares
the resulting objects. The guest run checks the handoff and smoke
workload. QEMU encodes the guest's exit through its debug-exit device;
the wrapper checks both that status and the guest markers
(`forth-bootstrap/kernel/k1/run-chain.sh:59`).

## Exercise

Hints and feedback are in [Appendix H](66-exercise-feedback.md#chapter-54-carrying-a-generated-runner-into-k1).

**Trace (easy).** Follow `/k0/build-out/amd64-runner` from the Forth launcher's output path through K1's imports to `/k1.args`. Identify which image supplies the runner, which supplies its recipe, and why importing only hda would leave the initial executable unavailable.

**Verify (moderate).** Run the smoke checkpoint and locate the compilation, archive creation and link commands in `serial.log`. Match each to `direct-smoke.kaem`, then distinguish the program's check summary from K1's final PASS marker and the host wrapper's PASS.

