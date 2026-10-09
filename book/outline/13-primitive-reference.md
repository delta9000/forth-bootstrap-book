# The 32 seed primitives: reference

Part: 1

Scope: Consolidate the instruction-level contracts into a compact primitive reference. Make this the lookup point for stack effects and primitive behavior used throughout the Forth library.

Sources taught: `seed/000-seed.hex0` — chunks `file-header-comment`, `elf-header`, `program-header`, `entry-point`, `sysvar-init`, `jmp-to-repl`, `dup`, `drop`, `swap`, `to-r`, `r-from`, `r-at`, `fetch`, `store`, `cfetch`, `cstore`, `plus`, `nand`, `zeq`, `divide`, `star`, `bye`, `emit`, `key`, `syscall6`, `find`, `here`, `comma`, `execute`, `read-word`, `read-char`, `report-token`, `state`, `latest`, `tick`, `colon`, `semicolon`, `compile-call`, `lit`, `bracket-lit`, `branch`, `zbranch`, `parse-decimal`, `repl` (names from INVENTORY.md).

Prerequisites: [04 — x86-64 encoding and the two-stack machine](04-x86-64-and-two-stacks.md); [12 — Decimal parsing and the REPL](12-repl.md)

Checkpoint: `seed/build.sh`; `echo 'bye' | ./seed-forth` — Part 1 checkpoint.

Reuses: [A1-32-seed-primitives.md](../A1-32-seed-primitives.md) — Reuse the primitive names, stack effects, and opcode reference.

TODO:

- TODO Reorganize the primitive table around the completed machine-code walkthrough.
