# Appendix I: the M1 assembler and hex2 linker (optional)

Part: back matter

Scope: Teach a standalone application of the completed Forth library. Follow macro expansion, two-pass label resolution, and output bytes in the M1/hex2 assembler. The direct C compiler and GCC route do not consume this assembler; the walkthrough is optional after Chapter 25.

Sources taught: `forth/130-asm.fth 1-785`

Prerequisites: [25 — Defining words and byte equality](25-lib-12-defining-words-and-bytes-eq.md)

Checkpoint: The appendix's self-contained seed checkpoint assembles a program that prints `hi`, exits 42, and occupies 160 bytes. The source repository keeps the corresponding `tests/asm/hi-check.sh` in its quick checks. Stage A separately compares M1 output and does not assemble it.

Reuses: [Appendix I](../26-m1-and-hex2.md) — Preserve the complete walkthrough, canonical source, existing URL and section anchors. The numeric filename and lab selector 26.1 remain compatibility identifiers, not reading-order requirements.
