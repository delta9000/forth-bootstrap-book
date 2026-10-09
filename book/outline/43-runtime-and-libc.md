# Runtime, libc, streams, and formatting

Part: 3

Scope: Teach process entry and the raw syscall boundary before the bounded C library. Connect allocation, memory, strings, streams, and formatting to the programs they support.

Sources taught: `cc/122-cc-sysv-runtime.fth` 1-187. `chain/runtime/gcc-seed/` supplies libc and stdio; TODO — INVENTORY.md has no line spans for these C sources.

Prerequisites: [42 — Linker and archives](42-linker-and-archives.md)

Checkpoint: TODO — no chapter-specific checkpoint exists.

Reuses: [38-direct-gcc-runtime.md](../38-direct-gcc-runtime.md) — Reuse process entry, syscall wrappers, and errno storage; [39-direct-gcc-libc.md](../39-direct-gcc-libc.md) — Reuse source-built allocation, memory, and string operations; [43-direct-gcc-stdio.md](../43-direct-gcc-stdio.md) — Reuse streams, file operations, and bounded formatting.

TODO:

- TODO Combine runtime, libc, and stdio around their shared contracts.
- TODO Inventory the C runtime sources and assign line ranges before drafting.
