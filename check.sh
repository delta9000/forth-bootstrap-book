#!/usr/bin/env bash
# check.sh -- the book's checks, against the forth-bootstrap sources it
# quotes (the forth-bootstrap submodule, or a checkout named by
# $FORTH_BOOTSTRAP).
#   tangle verify --strict  required published source coverage, byte for byte
#   check-numbers.py        recognized numeric forms and explicit citation bounds
#   check-tryit.py          selected seed-pipeline examples and recognized outputs
#   gen-index.py --check    book/WORD-INDEX.md is up to date
#   check-links.py          published local Markdown links/anchors resolve
# --static omits seed execution and numeric forms that need the built seed size.
# Neither mode repeats the long bootstrap/guest builds or certifies prose semantics.
set -euo pipefail
cd "$(dirname "$0")"
src=${FORTH_BOOTSTRAP:-forth-bootstrap}
mode=${1:-}
if [[ $# -gt 1 || ( -n "$mode" && "$mode" != --static ) ]]; then
    echo "usage: $0 [--static]" >&2
    exit 2
fi
[ -x "$src/seed/build.sh" ] || {
    echo "check: no forth-bootstrap checkout at $src (git submodule update --init --recursive)" >&2
    exit 1
}
python3 -m unittest discover -s tools/tests -v
tools/tangle.sh verify --strict
if [[ "$mode" == --static ]]; then
    python3 tools/check-numbers.py --citations-only
    echo "numeric byte/count checks and seed checkpoint execution: NOT RUN (--static)"
else
    "$src/seed/build.sh"                  # selected examples run its seed-forth
    python3 tools/check-numbers.py
    python3 tools/check-tryit.py
fi
python3 tools/gen-index.py --check
python3 tools/check-links.py
