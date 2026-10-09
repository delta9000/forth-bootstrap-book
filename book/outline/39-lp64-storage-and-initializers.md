# LP64 storage and initializers

Part: 3

Scope: Extend the core storage model to LP64 widths, alignment, native objects, and initializers. Mine the storage implementation from the retired TinyCC chapter while removing TinyCC as a route.

Sources taught: `cc/115-cc-native.fth 1-647`; `cc/117-cc-native-program.fth 1-100`; `cc/118-cc-native-init.fth 1-321`; `cc/119-cc-native-runtime.fth 1-111`

Prerequisites: [38 — Compiler entry and Stage A](38-main-and-bootstrap-chain.md)

Checkpoint: TODO — no chapter-specific checkpoint exists.

Reuses: [34-direct-tinycc.md](../34-direct-tinycc.md) — Mine only LP64 storage, layout, and initializers; the old TinyCC route remains in Retired.

TODO:

- TODO Extract LP64 layout and initializer material from chapter 34 and remove TinyCC route instructions.
- TODO Separate storage and initializer coverage from legacy calls and runtime material in the inventoried spans.
