# Linker and archives

Part: 3

Scope: Resolve symbols and relocations into executables using the Forth ELF linker. Extend the same model to indexed archives and selection of needed members.

Sources taught: `cc/140-cc-link.fth 1-613`; `cc/141-archive.fth 1-413`

Prerequisites: [41 — System V calls and separate compilation](41-system-v-calls.md)

Checkpoint: TODO — no chapter-specific checkpoint exists.

Reuses: [37-direct-gcc-linker.md](../42-linker-and-archives.md) — Reuse symbol resolution, relocation application, BSS layout, and executable publication; [44-direct-gcc-archives.md](../42-linker-and-archives.md) — Reuse archive indexing, deterministic construction, and lazy member selection.

TODO:

- TODO Merge archive indexing and member selection with the linker’s resolution narrative.
