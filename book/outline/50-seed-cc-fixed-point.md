# Building seed-cc and seed-ar

Part: 4

Scope: Follow the Forth-only construction of the C compiler driver and archiver. Plan the rebuild and byte comparison that establish the seed-cc fixed point, keeping that claim separate from Stage A.

Sources taught: `cc/driver/seed-cc-start.fth`; `cc/driver/seed-cc.c`; `cc/driver/seed-ar.c`; `cc/driver/seed-cc-boot/` — TODO: these sources have no line ranges in INVENTORY.md; inventory them before drafting.

Prerequisites: [49 — Aggregates and extended floating values](49-aggregate-abi.md)

Checkpoint: `./seed-forth < cc/driver/seed-cc-start.fth` builds seed-cc and seed-ar. `tests/cc/seed-cc-rebuild-check.sh` then constructs generation one and uses its seed-cc to build generation two, comparing both seed-cc and seed-ar byte for byte. The checkpoint and cleanup warnings are in Chapter 50.

Reuses: None — new chapter.

TODO:

- TODO Inventory the driver and Forth-only construction sources.
- NOTE (checked against source pin b25487ad4d62adb950c3372de43564dfcfabdd87): Chapter 50 documents the two-generation comparison in tests/cc/seed-cc-rebuild-check.sh. Building once is not that comparison. Keep this seed-tool result distinct from GCC stage D (Chapter 52) and the bzImage identities (Chapter 55).
