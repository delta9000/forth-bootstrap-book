# Owning the tools

Part: 4

Scope: Follow seed-cc as it builds every tool the GCC build needs, in the order the plumbing recipes run: kaem and the stage0-posix utilities, make 3.82, the stage-2 tools (sed, grep, gawk, coreutils, tar, gzip, patch, diffutils), the parser generators (oyacc, Heirloom lex, flex 2.5.11) and bash 2.05b. Then show configure scripts running under that bash, so no host shell or tool takes part in what follows.

Sources taught: `chain/plumbing/chain.kaem`; `chain/plumbing/stage1.kaem`; `chain/plumbing/stage2.kaem`; `chain/plumbing/lexers.kaem`; `chain/plumbing/bash.kaem`; `chain/plumbing/*/` (each package's Makefile and config.h); `chain/gcc-direct/configure.sh` — TODO: these sources have no line ranges in INVENTORY.md; inventory them before drafting.

Prerequisites: [50 — Building seed-cc and seed-ar](50-seed-cc-fixed-point.md)

Checkpoint: `sh chain/plumbing-root.sh` runs the plumbing stages first, in the sealed root, and leaves the tools in `build-out/plumbing-root/build-out/plumbing/bin/` (bash 2.05b among them); under K1, `kernel/k1/run-chain.sh --direct` stops at bash 2.05b. TODO — a host option to stop after the plumbing stages.

Reuses: None — new chapter. Mines `chain/plumbing/README.md` in forth-bootstrap.

TODO:

- TODO Inventory the plumbing recipes, the package Makefiles and config.h files, and the configure runner.
- TODO Trace the first kaem and shell construction, stage by stage.
- TODO Explain configure under the chain's own bash (`chain/gcc-direct/configure.sh`) as the bridge to the GCC chapter.
