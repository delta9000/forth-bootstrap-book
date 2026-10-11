# x86-64 encoding and the two-stack machine

Part: 1

Scope: Teach the logical data stack, register/memory distinction, ModRM, REX, and rel32 needed to decode the seed. Introduce the syscall register convention in Chapter 8, when it is used. Establish the data stack, return stack, register assignments, and instruction-byte reading method before the ELF walkthrough.

Sources taught: None directly: its examples are instructions from `seed/000-seed.hex0`, whose chunks are taught in stubs 05-12.

Prerequisites: [03 — What builds the seed?](03-where-this-fits.md)

Checkpoint: Inspect and decode the seed entry jump, then compare its target with objdump.

Reuses: None — new chapter.

The worked dup transition connects logical values to storage before decoding its store. The two-stack diagram distinguishes the cached register from memory cells.
