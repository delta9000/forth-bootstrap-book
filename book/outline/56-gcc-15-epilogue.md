# Epilogue: onward to GCC 15.2

Part: 4

Scope: Sketch the work needed to continue beyond the demonstrated GCC 10.5.0 and Linux route to GCC 15.2. Distinguish this planned extension from the checkpoints the current repository provides.

Sources taught: None inventoried for GCC 15.2. `chain/gcc64/run-gcc64.sh` is the existing ladder context; TODO — add its ranges to INVENTORY.md and identify sources for the extension.

Prerequisites: [55 — Linux 7.2.8 and kexec under QEMU](55-linux-and-kexec.md)

Checkpoint: TODO — forth-bootstrap has no verified GCC 15.2 checkpoint for this outline.

Reuses: None — new chapter.

TODO:

- TODO Specify the GCC 15.2 route, dependencies, and success criteria as future work.
- TODO Inventory any implementation before presenting the extension as executable.
- NOTE (checked against the code 2026-10-10): the gcc64 climb to GCC 15.2.0 was carried out in the older seed-forth project (forth-bootstrap/HISTORY.md:23-25) and stayed there; it is not unexplored future work. Frame this epilogue as a route that exists elsewhere and what bringing it into forth-bootstrap would take.
- NOTE: link seed-forth's gcc64 as https://github.com/delta9000/seed-forth, never a local path. The GCC 15.2.0 diverse-double-compiling result (1,043 files) is not recorded in forth-bootstrap's HISTORY.md or README.md (checked 2026-10-10), so leave it out; if it is ever cited, binutils and the musl sysroot were shared and are not covered.
