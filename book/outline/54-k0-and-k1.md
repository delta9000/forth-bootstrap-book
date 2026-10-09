# K0 and K1

Part: 4

Scope: Read the tiny K0 entry and the C kernel K1 that seed Forth builds. Explain the recipe runner, disk inputs, and transition to running the bootstrap tools under K1 in QEMU.

Sources taught: `kernel/k0/k0.hex0`; `kernel/k0/k0.asm`; `kernel/k1/k1.h`; `kernel/tools/k1-direct-start.fth`; `kernel/tools/k1-direct.recipe`; `kernel/k1/run-chain.sh` — TODO: these sources have no line ranges in INVENTORY.md; inventory them before drafting.

Prerequisites: [53 — The sealed host run](53-sealed-run.md)

Checkpoint: `sh kernel/k1/tests/direct-build-check.sh`; `kernel/k1/run-chain.sh --direct-smoke` — requires strace and GNU as for the build check, and QEMU for the smoke run.

Reuses: None — new chapter.

TODO:

- TODO Inventory K0, K1, and the direct build recipes.
- TODO Trace K0 to K1 and show the seed-cc, seed-ar, and kaem smoke-run evidence.
