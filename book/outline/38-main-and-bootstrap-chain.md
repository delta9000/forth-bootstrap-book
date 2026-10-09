# Compiler entry and Stage A

Part: 3

Scope: Join the compiler layers through the main entry point. Use Stage A’s byte-identical M1 output as the checkpoint for the core compiler.

Sources taught: `cc/120-cc-main.fth 1-40`

Prerequisites: [37 — Functions and translation units](37-functions-and-scope.md)

Checkpoint: `tests/cc/stage-a-check.sh` — requires host GCC for the reference; compare the emitted M1 for M2-Planet byte for byte.

Reuses: [32-main-and-bootstrap-chain.md](../32-main-and-bootstrap-chain.md) — Reuse the source walkthrough: Join the compiler layers through the main entry point.

TODO:

- TODO Adjust the chapter’s prerequisites and cross-references to the four-part order.
