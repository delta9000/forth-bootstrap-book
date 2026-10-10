# GCC 4.0.4: stages C and D

Part: 4

Scope: Follow the compiler-proper build into stage C’s libgcc and musl and stage D’s repeated GCC rebuilds. Explain the installed-file comparison establishing stage 2 = 3 = 4, then the late tools (make 4.4.1, bash 5.2, coreutils 9.5 and the rest) that the fixed-point GCC builds, each with its own configure.

Sources taught: `chain/gcc-direct/census.sh`; `chain/gcc-direct/binutils.sh`; `chain/gcc-direct/stage-c.sh`; `chain/gcc-direct/stage-d.sh`; `chain/gcc-direct/chain.sh`; `chain/gcc-direct/late-tools.sh` — TODO: these sources have no line ranges in INVENTORY.md; inventory them before drafting.

Prerequisites: [51 — Owning the tools](51-owning-the-tools.md)

Checkpoint: `sh chain/plumbing-root.sh` (after `python3 tools/fetch-archives.py`): it runs the plumbing stages and then `chain/gcc-direct/chain.sh`, ending with `# Stage D: fixed point reached` (stage 2 = 3 = 4, 54 files, 0 differ) in `build-out/plumbing-root/build-out/chain/stage-d/report.txt`.

Reuses: [49-direct-gcc-cc1.md](../52-gcc-4-fixed-point.md) — Reuse the compiler census, source generators, cc1 linking, and execution checks as the entrance to stages C and D.

TODO:

- TODO Inventory stages C and D and the compiler census.
- TODO Extend chapter 49 through libgcc, musl, and the three-generation comparison.
- TODO Add the late tools after the fixed point; they run only under K1 here (`kernel/k1/run-chain.sh --direct-linux`, `build-out/late/report.txt` on the output disk), so a host-side late-tools checkpoint is still TODO.
