# The seed-cc fixed point

Part: 4

Scope: Follow the Forth-only construction of the C compiler driver and archiver. Plan the rebuild and byte comparison that establish the seed-cc fixed point, keeping that claim separate from Stage A.

Sources taught: `cc/driver/seed-cc-start.fth`; `cc/driver/seed-cc.c`; `cc/driver/seed-ar.c`; `cc/driver/seed-cc-boot/` — TODO: these sources have no line ranges in INVENTORY.md; inventory them before drafting.

Prerequisites: [49 — Aggregates and extended floating values](49-aggregate-abi.md)

Checkpoint: `./seed-forth < cc/driver/seed-cc-start.fth` builds seed-cc and seed-ar. TODO — provide a verified rebuild-and-compare checkpoint for the seed-cc fixed point.

Reuses: None — new chapter.

TODO:

- TODO Inventory the driver and Forth-only construction sources.
- TODO Document the seed-cc rebuild inputs and exact byte-comparison procedure; the construction command alone is not a fixed-point proof.
