#!/usr/bin/env bash
# check.sh -- the book's checks, against the forth-bootstrap sources it
# quotes (the forth-bootstrap submodule, or a checkout named by
# $FORTH_BOOTSTRAP).
#   tangle verify --strict  every file= block is its source file, byte for byte
#   check-numbers.py        every numeric claim in the prose matches the source
#   check-tryit.py          every "Try it" shell block runs and prints what it says
#   gen-index.py --check    book/WORD-INDEX.md is up to date
#   check-links.py          every link and anchor resolves
set -euo pipefail
cd "$(dirname "$0")"
src=${FORTH_BOOTSTRAP:-forth-bootstrap}
[ -x "$src/seed/build.sh" ] || {
    echo "check: no forth-bootstrap checkout at $src (git submodule update --init --recursive)" >&2
    exit 1
}
"$src/seed/build.sh" > /dev/null          # the Try-it blocks run its seed-forth
tools/tangle.sh verify --strict > /dev/null && echo "tangle --strict: OK"
python3 tools/check-numbers.py | tail -1
python3 tools/check-tryit.py | tail -1
python3 tools/gen-index.py --check
python3 tools/check-links.py | tail -1
