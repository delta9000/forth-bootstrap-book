# Linux 7.2.8 and kexec under QEMU

Part: 4

Scope: Carry the tools through the compiler ladder to GCC 10.5.0 and Linux 7.2.8 under K1. Follow output verification and kexec into the kernel produced by the run.

Sources taught: `kernel/k1/direct-linux.recipe`; `kernel/k1/direct_inputs.py`; `kernel/k1/run-chain.sh`; `chain/ladder/stage12.sh`; `chain/gcc64/run-gcc64.sh` — TODO: these sources have no line ranges in INVENTORY.md; inventory them before drafting.

Prerequisites: [54 — K0 and K1](54-k0-and-k1.md)

Checkpoint: `JOBS=2 kernel/k1/run-chain.sh --direct-linux` — requires pinned archives, QEMU with KVM, and 24 GiB free guest RAM; allow roughly 80–100 minutes. Expect the built Linux kernel’s init greeting after kexec.

Reuses: None — new chapter.

TODO:

- TODO Inventory the kernel route and compiler-ladder scripts.
- TODO Explain the handover, output hashes, and Linux init greeting as separate evidence.
