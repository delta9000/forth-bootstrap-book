# Expressions: precedence

Part: 3

Scope: Follow the precedence cascade and binary operator folding. Connect token consumption, type decisions, and emitted operations.

Sources taught: `cc/100-cc-expr.fth`, assembled from chunks: the root block (lines 1-20) and `expr-header`, `expr-tok-tests`, `expr-fwd-refs`, `expr-binops`, `expr-mul`, `expr-add`, `expr-shift`, `expr-rel`, `expr-eq`, `expr-bit`, `expr-log` (INVENTORY.md, "Chunks by chapter").

Prerequisites: [32 — Calls, shims, and globals](32-codegen-part-2.md)

Checkpoint: TODO — the cumulative core checkpoint is Stage A at the end of the core compiler sequence.

Reuses: [27-expressions-part-1.md](../33-expressions-part-1.md) — Reuse the source walkthrough: Follow the precedence cascade and binary operator folding.

TODO:

- TODO Adjust the chapter’s prerequisites and cross-references to the four-part order.
- TODO Record the expression chunks and their source ranges in the inventory before splitting coverage.
