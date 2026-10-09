# Decimal parsing and the REPL

Part: 1

Scope: Follow decimal conversion and the loop that chooses lookup, literal compilation, or execution. Close the seed walkthrough by building and starting the complete 1,772-byte program.

Sources taught: `seed/000-seed.hex0` — chunks `parse-decimal`, `repl` (names from INVENTORY.md).

Prerequisites: [11 — Branches and inline cells](11-branches.md)

Checkpoint: `seed/build.sh`; `echo 'bye' | ./seed-forth` — build the 1,772-byte seed and confirm that its REPL accepts `bye`.

Reuses: [20-number-parser-and-repl.md](../20-number-parser-and-repl.md) — Reuse the source walkthrough: Follow decimal conversion and the loop that chooses lookup, literal compilation, or execution.

TODO:

- TODO Write the seed build and REPL checkpoint with expected size and exit behavior.
- TODO Rewrite the running byte-count table for the new chapter numbering (old rows 13/14 now unchecked).
