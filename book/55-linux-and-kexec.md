# Chapter 55 — Linux 7.2.8 and kexec under QEMU

The recorded guest run ends with a greeting:
`init: hello from a Linux kernel built from hex0 and seed-forth`.
By then, K1 has built its successor and handed the same QEMU machine to
it. Linux has started and loaded the small program that prints the line
(`forth-bootstrap/results/k1-2026-10-08/serial.log:1330`).

Getting from a kernel *file* to that greeting is the last problem in the
route. We must build the compiler selected by the Linux recipe, produce
the kernel and its first program, preserve the build results, and enter
Linux with the machine state it expects. Once control passes to Linux,
K1 will no longer be there to finish the work.

## A greeting from the new kernel

The final program is short enough to understand before following the
build. This statically linked init mounts proc, prints its greeting, and
reads `/proc/version`. The second message therefore comes from the
running kernel (`forth-bootstrap/chain/ladder/init.c:19`):

```c
    mount("proc", "/proc", "proc", 0, 0);
    printf("init: hello from a Linux kernel built from hex0 and seed-forth\n");
    fd = open("/proc/version", O_RDONLY);
    if (fd >= 0) {
        n = read(fd, buf, sizeof buf - 1);
        if (n > 0) {
            buf[n] = 0;
            printf("init: %s", buf);
        }
        close(fd);
    }
```

Init then flushes output and uses QEMU's debug-exit device. The wrapper
checks that exit status and the serial markers for the build, handover
and init (`forth-bootstrap/chain/ladder/init.c:30`,
`forth-bootstrap/kernel/k1/run-chain.sh:59`). These give the long build
an observable destination: a program running under the kernel the guest
just built. The compiler comparisons and archive checks establish the
earlier steps; this greeting checks that control reached the new system.

## Extend the guest recipe

The smoke route in Chapter 54 showed that K1 can run the compiler,
archiver and recipe runner. The full route uses those tools to rebuild
the plumbing and GCC chain under K1. For `--direct-linux`, the host image
writer appends `direct-linux.recipe` to `direct.recipe`, rather than to
the shorter smoke recipe (`forth-bootstrap/kernel/k1/mkdisk.py:50`).
Unpacking, patching and compilation remain in the guest
(`forth-bootstrap/kernel/k1/run-chain.sh:6`).

The appended recipe prepares the direct GCC and late tools, installs
those tools as the guest system, climbs to the final compiler, builds
Linux, then exports the results and hands over. Each invocation uses an
explicit executable path because the runner starts it with an empty
environment. The final commands are in `direct-linux.recipe`
(`forth-bootstrap/kernel/k1/direct-linux.recipe:9`):

```text
run 0 - /dev/console /dev/console /build-out/plumbing/bin/bash kernel/k1/direct-full.sh JOBS=2
say "k1: GCC 4.0.4 fixed point and late tools built under K1"
run 0 - /dev/console /dev/console /build-out/late/usr/bin/bash /chain/ladder/stage10-direct.sh
run 0 - /dev/console /dev/console /usr/bin/env JOBS=2 /usr/bin/bash /chain/ladder/stage11.sh
run 0 - /dev/console /dev/console /usr/bin/env JOBS=2 /usr/bin/bash /chain/ladder/stage12.sh
run 0 - /dev/console /dev/console /usr/bin/bash /chain/ladder/finish.sh
```

The runner waits for success before advancing to the next command (`forth-bootstrap/kernel/tools/amd64-runner.c:555`). The compiler and late tools (Chapter 52) become available to the longer guest route (`forth-bootstrap/kernel/k1/direct-full.sh:28`).

Shell scripts need conventional paths even though their tools came from the bootstrap. `direct-full.sh` supplies those paths inside K1's root, rather than borrowing a host installation (`forth-bootstrap/kernel/k1/direct-full.sh:12`):

```text
# The recipe runner starts programs with an empty environment.
PATH=/build-out/plumbing/bin
export PATH
jobs=${1#JOBS=}
jobs=${jobs:-2}
cd /
[ -e /bin ] || ln -s build-out/plumbing/bin /bin
mkdir -p /usr
[ -e /usr/bin ] || ln -s ../build-out/plumbing/bin /usr/bin
```

That script checks the stage-D report before building the late tools, then removes source and build trees that the remaining route does not read (`forth-bootstrap/kernel/k1/direct-full.sh:29`). `stage10-direct.sh` replaces the plumbing links with directories containing the late tools and makes `/bin/sh` point to their bash (`forth-bootstrap/chain/ladder/stage10-direct.sh:11`). Thus later scripts' system paths still name programs built inside K1.

## Carry inputs, check bytes

The input disk must contain future sources before the guest begins. `direct_inputs.py` separates the existing starting tree from the Linux extension. The extension adds the GCC scripts, patches, `SOURCES`, `HASHES`, the ladder scripts and init sources (`forth-bootstrap/kernel/k1/direct_inputs.py:349`). Its archive selection is based on paths in `MANIFEST.sha256`, not a scan of everything lying in the host build directory (`forth-bootstrap/kernel/k1/direct_inputs.py:415`).

The inventory extends the image only when Linux is selected, in `direct_inputs.py` (`forth-bootstrap/kernel/k1/direct_inputs.py:430`):

```python
def k1_tree(smoke, linux=False):
    tree = _files(SMOKE)
    if not smoke:
        tree.update(_files(DIRECT))
        tree.update(_archives(("build-out/plumbing-inputs/", "build-out/lexer-inputs/")))
    if linux:
        # direct-full.sh links the chain's gcc and musl archives to their
        # build-out/distfiles copies; chain.SOURCES' plain binutils tar is the
        # one input that is not a release archive as published.
        tree.update(_files(LINUX))
        tree.update(_archives(("build-out/distfiles/", "build-out/stage-b-inputs/")))
    return tree
```

`_files` rejects absent files and symlinks; it checks availability and file type, not their digests (`forth-bootstrap/kernel/k1/direct_inputs.py:404`). The host image writer copies this inventory onto hda, marking hex0-seed as the initial tree's only executable (`forth-bootstrap/kernel/k1/mkdisk.py:23`).

An archive can be present on hda and still contain the wrong bytes. The
inventory checks availability; digest checks establish whether those
bytes match the pinned input.

On the host, `tools/fetch-archives.py` checks cached and downloaded archives
against `MANIFEST.sha256` (`forth-bootstrap/tools/fetch-archives.py:146`,
`forth-bootstrap/tools/fetch-archives.py:181`). Inside the guest, the
compiler climb's `need` checks cached inputs against `chain/gcc64/SOURCES`
before using them (`forth-bootstrap/chain/gcc64/run-gcc64.sh:182`). The
Linux recipe checks against `MANIFEST.sha256` instead. Its `unpack`
function puts that check before extraction
(`forth-bootstrap/chain/ladder/stage12.sh:27`):

```text
unpack() {
    local want
    want=$(sed -n "s|^\([0-9a-f]\{64\}\)  build-out/distfiles/$2\$|\1|p" /MANIFEST.sha256)
    [ -n "$want" ] || fail "no pin for $2 in /MANIFEST.sha256"
    echo "$want  $D/$2" | sha256sum -c --quiet || fail "sha256 $2"
    rm -rf "$S/$1" "$S/$1.tmp"
    mkdir -p "$S/$1.tmp"
    tar -xf "$D/$2" -C "$S/$1.tmp"
    mv "$S/$1.tmp"/* "$S/$1"
```

At this point the sources are available and identified. The next task is
to turn the completed GCC 4.0.4 toolchain into the compiler used by the
Linux recipe.

## Climb to the Linux compiler

`stage11.sh` selects the completed direct compiler and the bootstrap parser generators. It fixes the build root at `/build-out/g64`, uses the already supplied archive cache, and starts the compiler stages under the guest's installed bash (`forth-bootstrap/chain/ladder/stage11.sh:9`):

```text
B=/build-out/g64
mkdir -p $B $B/src
chmod 755 /chain/gcc64/*.sh            # copied into the root as plain files
export GCC64_DIRECT=/build-out/chain/stage-d GCC64_OYACC=/build-out/plumbing/bin/oyacc \
    GCC64_FLEX=/build-out/plumbing/bin/flex
[ $# -gt 0 ] || set -- bridge stage6 stage7 stage8 stage9 stage10
GCC64_CACHE=/build-out/distfiles BUILDROOT=$B JOBS=${JOBS:-16} \
    bash /chain/gcc64/run-gcc64.sh "$@" || {
```

The stage names belong to gcc64's script; they are distinct from the ladder script names. Read the build as a sequence of builder → output relationships:

| Step | Builder → output | Source |
|---|---|---|
| Bridge | Direct GCC 4.0.4 → binutils 2.30 and GCC 4.0.4, named gcc-A | `forth-bootstrap/chain/gcc64/run-gcc64.sh:267` |
| `stage6` | gcc-A → gcc-B; gcc-B → gcc-C; compare B with C | `forth-bootstrap/chain/gcc64/run-gcc64.sh:308` |
| `stage7` | gcc-B → musl, GMP, MPFR and MPC; run their checks | `forth-bootstrap/chain/gcc64/run-gcc64.sh:330` |
| `stage8` | gcc-B → GCC 4.7.4 with C and C++ | `forth-bootstrap/chain/gcc64/run-gcc64.sh:367` |
| `stage9` | GCC 4.7.4 → binutils 2.41 | `forth-bootstrap/chain/gcc64/run-gcc64.sh:387` |
| `stage10` | GCC 4.7.4 with binutils 2.41 → GCC 10.5.0 | `forth-bootstrap/chain/gcc64/run-gcc64.sh:404` |

The final step explicitly selects the newer assembler and linker before invoking `build-gcc10.sh`; it also compiles and runs C and C++ test programs (`forth-bootstrap/chain/gcc64/run-gcc64.sh:409`). Those tests check behavior on their workloads. The B/C comparison checks repeatability of the selected rebuilt artifacts, rather than general compiler correctness (`forth-bootstrap/chain/gcc64/run-gcc64.sh:312`).

Output pins ask another question: did this run produce the recorded bytes? `chain/gcc64/HASHES` gives each artifact a digest and a scope. `any` applies regardless of the build root; `root` applies at its declared `/build-out/g64` because configured paths are embedded in the files (`forth-bootstrap/chain/gcc64/HASHES:2`).

The comparison records actual hashes even when a path-dependent pin cannot be enforced, in `run-gcc64.sh` (`forth-bootstrap/chain/gcc64/run-gcc64.sh:431`):

```text
    root=$(sed -n 's/^root //p' "$GCC64/HASHES")
    while read -r h f scope; do
        case $h in ''|'#'*|root) continue ;; esac
        [ -f "$W/$f" ] || continue
        got=$(sha "$W/$f"); echo "$got  $f" >> "$LOG/hashes.txt"
        if [ "$scope" = root ] && [ "$W" != "$root" ]; then
            n_skip=$((n_skip+1))
        elif [ "$got" = "$h" ]; then
            n_ok=$((n_ok+1))
        else
            n_bad=$((n_bad+1)); echo "$me: $f is $got, not the pinned $h ($scope)" >&2
        fi
    done < "$GCC64/HASHES"
```

A missing artifact is skipped, so a partial invocation cannot establish
that the entire pin set exists. An artifact that differs from an applicable pin fails
unless explicit repinning mode is enabled
(`forth-bootstrap/chain/gcc64/run-gcc64.sh:444`). The recorded full guest
run matched all 31 pins (`forth-bootstrap/README.md:239`). That identifies
the selected compiler and library outputs. The kernel image is still
ahead of us.

## Build a kernel with its own init

`stage12.sh` puts the GCC 10.5.0 and binutils 2.41 directories first on PATH. Its build-time support libraries are zlib and libelf for objtool; the directory named `host` holds tools and libraries used during the build inside the chain root, not programs supplied by the outer QEMU host (`forth-bootstrap/chain/ladder/stage12.sh:1`, `forth-bootstrap/chain/ladder/stage12.sh:45`).

Linux needs a first process independent of K1's recipe runner. The build compiles `chain/ladder/init.c` statically and describes its placement in an embedded initramfs, in `stage12.sh` (`forth-bootstrap/chain/ladder/stage12.sh:76`):

```text
# The initramfs: /init from chain/ladder/init.c, static against gcc-10's musl.
gcc -static -O2 -o $O/init /chain/ladder/init.c || fail "init"
printf 'dir /dev 755 0 0\nnod /dev/console 600 0 0 c 5 1\ndir /proc 755 0 0\nfile /init %s 755 0 0\n' \
    $O/init > $O/initramfs.list
```

The initramfs supplies `/init` and the console node. It travels inside bzImage, so this route does not need an external initrd file.

The kernel source is Linux 7.2.8, unpacked after manifest verification (`forth-bootstrap/chain/ladder/stage12.sh:82`). The kernel configuration enables executable loading, the serial console and the embedded filesystem, then produces bzImage. Fixed build metadata keeps the timestamp and builder names controlled, in `stage12.sh` (`forth-bootstrap/chain/ladder/stage12.sh:88`):

```text
    K="make KBUILD_BUILD_TIMESTAMP=@0 KBUILD_BUILD_USER=chain KBUILD_BUILD_HOST=chain-root"
    {
        $K tinyconfig &&
        ./scripts/config -e 64BIT -e PRINTK -e TTY -e SERIAL_8250 -e SERIAL_8250_CONSOLE \
            -e BINFMT_ELF -e BINFMT_SCRIPT -e BLK_DEV_INITRD -e PROC_FS -e SYSFS \
            -e EARLY_PRINTK -e RD_GZIP -e KERNEL_GZIP -d KERNEL_XZ \
            -e X86_IOPL_IOPERM \
            -e CMDLINE_BOOL --set-str CMDLINE "console=ttyS0 panic=-1" \
            --set-str INITRAMFS_SOURCE "$O/initramfs.list" &&
        $K olddefconfig &&
        $K headers &&                     # asm/ and linux/ for host tools; headers_install
        cp -r usr/include/. $P/include/ &&  # would copy them with rsync
        $K -j"${JOBS:-16}" bzImage
    } > "$LOG/linux.log" 2>&1 || fail "linux (see $LOG/linux.log)"
    cp arch/x86/boot/bzImage $O/bzImage
    cp .config $O/config
    touch "$LOG/linux.done"
```

The resulting image and configuration live under `/build-out/linux`; the build logs remain under `/build-out/s12-logs` (`forth-bootstrap/chain/ladder/stage12.sh:12`). The script prints an image digest, but the gcc64 pin list is a different artifact set: it ends at the compiler and supporting libraries, not bzImage (`forth-bootstrap/chain/gcc64/HASHES:10`).

## Preserve results before handing over

The kernel image exists in K1's RAM filesystem. Starting Linux will make
that filesystem unavailable to the new system, so “boot, then save the
logs” is the wrong order. `finish.sh` first selects the Linux output,
Linux build logs and gcc64 logs, plus the earlier reports when present
(`forth-bootstrap/chain/ladder/finish.sh:8`). It writes them to the output
disk before preparing the handoff (`forth-bootstrap/chain/ladder/finish.sh:14`):

```text
tar -cf /dev/hdb "$@"
echo "finish: results written to hdb"
mkdir -p /boot
cp /build-out/linux/bzImage /boot/bzImage
printf 'console=ttyS0 panic=-1' > /boot/cmdline
gcc -static -O2 -o /build-out/kexec /chain/ladder/kexec.c
echo "finish: K1 hands the machine to the Linux kernel it built"
exec /build-out/kexec
```

The hdb tar preserves the image, configuration, pin report and build logs for inspection from the host. It does not export the whole RAM root or all installed compilers. The result marker follows a successful tar command; it is evidence of export, not an independent readback or integrity comparison (`forth-bootstrap/chain/ladder/finish.sh:4`). The host wrapper attaches this disk as `out.img` and preserves the serial stream in `serial.log` (`forth-bootstrap/kernel/k1/run-chain.sh:50`).

The small `kexec` program issues the reboot syscall with the KEXEC command. K1 dispatches that command directly to `boot_linux`, naming `/boot/bzImage`, an optional external initrd and the command-line file (`forth-bootstrap/chain/ladder/kexec.c:7`, `forth-bootstrap/kernel/k1/sys.c:1139`). This is a kexec-style handover: the running kernel loads its successor and transfers control without returning through firmware.

## Prepare the Linux entry state

A bzImage is not an ELF program for K1's process loader. `boot_linux` reads the setup header, checks its signature and accepts only a protocol with the required long-mode entry. It finds the protected-mode payload after the setup area, in `linux.c` (`forth-bootstrap/kernel/k1/linux.c:41`):

```c
    if ((r = namei(root, kernel, 1, &kip)))
        return r;
    if (inode_read(kip, 0, hdr, sizeof hdr) != sizeof hdr || memcmp(hdr + 0x202, "HdrS", 4))
        return -ENOEXEC;
    if (*(u16 *)(hdr + 0x206) < 0x20C || !(hdr[0x236] & 1))
        return -ENOEXEC;                /* needs the 64-bit entry (XLF_KERNEL_64) */
    setup_sects = hdr[0x1F1] ? hdr[0x1F1] : 4;
    pm_off = (setup_sects + 1) * 512;
    init_size = *(u32 *)(hdr + 0x260);
    /* the protected-mode kernel, with room to decompress in place */
    size = kip->size - pm_off;
    if (init_size < size)
        init_size = size;
```

The loader reserves enough contiguous physical memory for decompression, respecting the header's alignment and preferred-address requirements before copying the payload (`forth-bootstrap/kernel/k1/linux.c:55`). The reserve is based on `init_size`, not just the compressed file's length.

Linux boot parameters describe the machine it inherits. K1 allocates and clears `boot_params` and command-line storage, copies the image's setup header, records physical pointers for the command line and any external initrd, and copies the firmware e820 memory map (`forth-bootstrap/kernel/k1/linux.c:71`). The embedded initramfs is already part of the loaded image; absence of an external initrd is consistent with this build.

The final preparation keeps the current K1 stack addressable while adding
the identity mapping required by the entry code. The call in `linux.c`
passes physical addresses for the page tables and boot parameters
(`forth-bootstrap/kernel/k1/linux.c:97`):

```c
    /* identity map of the first 512 GiB, plus the direct map so this code
     * keeps its stack until the jump */
    pml4 = P2V(palloc_contig(PAGE, PAGE, 16UL << 20));
    pdpt = P2V(palloc_contig(PAGE, PAGE, 16UL << 20));
    memset(pml4, 0, PAGE);
    for (i = 0; i < 512; i++)
        pdpt[i] = i << 30 | 0x83;
    pml4[0] = V2P(pdpt) | 3;
    extern u64 *kpml4;
    for (i = 256; i < 512; i++)
        pml4[i] = kpml4[i];
    kprintf("k1: booting Linux (protocol %x, load %lx, init_size %lx, initrd %lu bytes)\n",
            *(u16 *)(hdr + 0x206), load, init_size, rdsize);
    linux_jump(V2P(pml4), V2P(bp), load + 0x200);
```

`linux_jump` disables interrupts, installs the new page tables and jumps
through the entry argument while leaving the boot-parameter argument in
`rsi` (`forth-bootstrap/kernel/k1/k1-asm.fth:229`). Linux receives the
machine state required by its boot protocol. The preceding
`k1: booting Linux` marker shows that preparation reached the call to
`linux_jump`; subsequent Linux output shows that the successor executed.

**Predict before continuing.** Suppose the loop copying `pml4[256]` through `pml4[511]` were removed, leaving only the identity map. After CR3 changes, `rsp` still holds a high direct-map address for K1's kernel stack. If the handoff code now needed to read a saved value from that stack, would the identity map make the read safe? Explain which address would be translated.

<details>
<summary>Check the stack prediction</summary>

No. The read would use the unchanged high virtual address in `rsp`; it would not automatically subtract `KBASE`. With no corresponding upper PML4 entry, that address would cause a page fault even though the physical bytes still exist and have a low identity-mapped alias. K1 allocates the process's kernel stack through the direct map (`forth-bootstrap/kernel/k1/proc.c:23`, `forth-bootstrap/kernel/k1/mm.c:149`). Preserving the upper entries keeps that stack address usable across the switch.

This is a conditional prediction, not a claim that removing the loop necessarily faults at the CR3 instruction: the pinned `linux_jump` touches no stack between loading CR3 and its register-indirect jump (`forth-bootstrap/kernel/k1/k1-asm.fth:232`). If you expected the identity map to repair `rsp`, revisit [the two-address trace in Chapter 54](54-k0-and-k1.md#two-virtual-addresses-one-physical-byte), then explain why mapping the physical stack bytes is different from preserving the virtual address already in use.

</details>

After the jump, Linux starts the init we read at the beginning of the
chapter. A kernel banner shows that Linux executed; the init lines show
that it also loaded and ran the program carried in its initramfs. We have
followed the path from source bytes to a file, from that file to machine
state, and from that state to a running system.

## Try it

Run from the forth-bootstrap checkout root. Have the pinned archives in place using `tools/fetch-archives.py`, QEMU with KVM, and room on the host for a 24 GiB guest plus QEMU's own overhead. The recorded run took 1 h 38 min with `JOBS=2` and that guest memory; K1 has one CPU, so the build runs slower than on a many-core host (`forth-bootstrap/README.md:182`, `forth-bootstrap/README.md:239`). The wrapper defaults to that guest memory for `--direct-linux` (`forth-bootstrap/kernel/k1/run-chain.sh:28`).

The command recreates the input and output images under `build-out/k1-direct-linux` and writes `serial.log` there. Preserve earlier results before starting; the output disk is replaced (`forth-bootstrap/kernel/k1/run-chain.sh:28`, `forth-bootstrap/kernel/k1/run-chain.sh:38`).

<!-- check-tryit: the runner only executes selected seed-forth pipe examples in a scratch tree; this guest needs pinned archives, kernel/ and vendor/, QEMU with KVM, 24 GiB guest RAM and over an hour. -->
<!-- tryit: skip -->
```sh
JOBS=2 kernel/k1/run-chain.sh --direct-linux
```

Recorded output from the completed run of 2026-10-08 (`forth-bootstrap/README.md:231`), marker lines in order with the tool output between them omitted. Only the prefix of the K0 handover line is shown:

```text
k0: K1 built by seed Forth
k1: starting
k1: seed-forth built by hex0-seed
k1: seed-cc and seed-ar built by seed Forth
k1: seed-cc, seed-ar and kaem work; starting the plumbing stages
k1: PASS (direct route under K1: seed to bash 2.05b)
k1: GCC chain (binutils, stage C, stage D) under K1
k1: GCC 4.0.4 fixed point under K1; building the late tools
k1: late tools built by the stage-D GCC
k1: GCC 4.0.4 fixed point and late tools built under K1
stage10: environment ready (direct route: tools built by the stage-D GCC)
```

The compiler climb's markers, without the log's elapsed-time prefixes:

```text
gcc-A -O2 libc-test: PASSED: 0 failures
gcc-B -O2 libc-test: PASSED: 0 failures
gcc-4.7.4: PASSED: 0 failures; PASSED: C++ test, 0 failures
gcc-10.5.0: PASSED: 0 failures; PASSED: C++ test, 0 failures
all requested stages passed
gcc (GCC) 10.5.0
GNU ld (GNU Binutils) 2.41
stage12: zlib-1.3.1
stage12: elfutils-0.192 libelf
finish: results written to hdb
finish: K1 hands the machine to the Linux kernel it built
```

The K1 jump marker begins `k1: booting Linux`. After it, the recorded Linux boot line and init lines read:

```text
Linux version 7.2.8 (chain@chain-root) (gcc (GCC) 10.5.0, GNU ld (GNU Binutils) 2.41) #1 PREEMPT @0
init: hello from a Linux kernel built from hex0 and seed-forth
init: Linux version 7.2.8 (chain@chain-root) (gcc (GCC) 10.5.0, GNU ld (GNU Binutils) 2.41) #1 PREEMPT @0
```

The order of those messages now has a reason. The build identifies its
compiler outputs, preserves its results, prepares the handover, and then
gives way to Linux and init. Each later line depends on work we can locate
in the preceding recipes. The greeting finishes the execution story;
the saved reports let us inspect how the system that printed it was built.

## Exercise

Hints and feedback are in [Appendix H](66-exercise-feedback.md#chapter-55-producing-bytes-versus-transferring-control).

**Trace (moderate).** Follow bzImage from `stage12.sh` through `finish.sh`, the reboot handler and `boot_linux`. Identify which step copies file bytes, which reserves decompression space, which constructs boot parameters and which transfers control. Explain why an embedded initramfs can coexist with no external initrd.

**Verify (easy).** Classify these observations: an archive passes SHA-256 checking; a gcc64 artifact matches a pin; `finish` reports an export; Linux prints its version; init prints the greeting. For each, name one failure it rules out and one failure it leaves possible. Use the cited sources and recorded excerpts without starting a build.
