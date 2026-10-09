# Owning the tools

Part: 4

Scope: Explain how seed-cc builds the shell and utilities needed to configure and build GCC. Follow configure under the chain’s own bash and extend the resulting GCC fixed point to the late tools.

Sources taught: `chain/plumbing/chain.kaem`; `chain/plumbing/stage1.kaem`; `chain/plumbing/stage2.kaem`; `chain/plumbing/lexers.kaem`; `chain/plumbing/bash.kaem`; `chain/gcc-direct/configure.sh`; `chain/gcc-direct/late-tools.sh` — TODO: these sources have no line ranges in INVENTORY.md; inventory them before drafting.

Prerequisites: [51 — GCC 4.0.4: stages C and D](51-gcc-4-fixed-point.md)

Checkpoint: The plumbing stages: `sh chain/plumbing-root.sh` builds them first, in the sealed root.  The late tools run only under K1 here (`kernel/k1/run-chain.sh --direct-linux`, `build-out/late/report.txt` on the output disk); TODO — a host-side late-tools checkpoint (seed-forth had `tools/late-root.sh`).

Reuses: None — new chapter.

TODO:

- TODO Inventory the plumbing recipes, configure runner, and late-tool build.
- TODO Trace the first kaem and shell construction and distinguish prerequisites from the later tool replacements.
