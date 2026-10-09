# ELF, entry, and the memory map

Part: 1

Scope: Read the ELF headers and startup instructions that make the seed executable. Locate the stacks, dictionary, and mutable system variables in the memory map.

Sources taught: `seed/000-seed.hex0` — chunks `file-header-comment`, `elf-header`, `program-header`, `entry-point`, `sysvar-init`, `jmp-to-repl` (names from INVENTORY.md).

Prerequisites: [04 — x86-64 encoding and the two-stack machine](04-x86-64-and-two-stacks.md)

Checkpoint: TODO — use the complete-seed build and REPL checkpoint at the end of this walkthrough.

Reuses: [13-elf-and-entry.md](../13-elf-and-entry.md) — Reuse the source walkthrough: Read the ELF headers and startup instructions that make the seed executable; [A2-memory-map.md](../A2-memory-map.md) — Reuse the seed address map; move compiler-region details to the relevant Part 3 chapters.

TODO:

- TODO Move the seed memory map here and defer compiler-specific addresses to Part 3.
