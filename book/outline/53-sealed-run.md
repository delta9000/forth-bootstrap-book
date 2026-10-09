# The sealed host run

Part: 4

Scope: Audit the host run whose initial root contains only hex0-seed as an executable. Follow source pins, executable publication, and execve traces through the GCC fixed point.

Sources taught: `chain/plumbing-root.sh`; `MANIFEST.sha256`; `tools/fetch-archives.py` — TODO: these sources have no line ranges in INVENTORY.md; inventory them before drafting.

Prerequisites: [52 — GCC 4.0.4: stages C and D](52-gcc-4-fixed-point.md)

Checkpoint: `python3 tools/fetch-archives.py`; `sha256sum -c MANIFEST.sha256`; `sh chain/plumbing-root.sh` — requires bwrap, strace, and user namespaces; allow 20–40 minutes and inspect the trace and fixed-point report.

Reuses: None — new chapter.

TODO:

- TODO Inventory the sealed-run script and source-pin checks.
- TODO Explain the initial executable boundary and how to audit the resulting traces.
