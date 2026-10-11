# Assembler regression check

Part: checks and references

Scope: Document the standalone assembler's regression role and how to run its retained smoke check. This is not a teaching chapter or a prerequisite of the compiler/GCC route.

Sources taught: None.

Check source: `forth/130-asm.fth` remains in the pinned source checkout and is excluded from book source reconstruction.

Prerequisites: The seed setup in [01 — Your first word](01-reading-the-book.md).

Checkpoint: Lab selector 26.1 and upstream `tests/asm/hi-check.sh` check `hi`, exit 42, and 160 bytes. Stage A separately compares M1 text without assembling it.

Reuses: [Assembler regression check](../26-m1-and-hex2.md) — Keep the stable URL and runnable wrapper. Do not restore the retired walkthrough, source listing, or exercise sequence.
