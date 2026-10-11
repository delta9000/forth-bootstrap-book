#!/usr/bin/env bash
# tools/tangle.sh — literate-programming tangler for the seed-forth book.
#
# The book in book/*.md interleaves prose with fenced code blocks.  Blocks
# tagged with a "file=" attribute are part of the canonical source for
# that file; this script extracts them and verifies them against the
# checked-in source files.
#
# Block format:
#
#     ```forth file=forth/010-lib.fth
#     : over  >r dup r> swap ;
#     ```
#
# For seed/000-seed.hex0 (which is hand-assembled with strict byte offsets),
# named chunks let us teach by topic rather than by ELF offset:
#
#     ```hex0 file=seed/000-seed.hex0
#     <<elf-header>>
#     <<entry-point>>
#     <<sysvar-init>>
#     ```
#
#     ```hex0 chunk=elf-header
#     7F 45 4C 46         ; magic
#     ...
#     ```
#
# Commands:
#   extract OUTDIR  Tangle the chapters, in book/SUMMARY.md order, into
#                   OUTDIR/<target-file>.
#   verify          For each file mentioned in the book, every tangled
#                   line must appear in the source file in non-decreasing
#                   order.  Used while the book is in progress.
#   verify --strict Every required source in canonical-sources.txt must be
#                   covered by published chapters and equal source byte-for-byte.
#                   Audit explicit check-only exceptions without executing their tests.
#   status          Print canonical coverage and registered check-only checkpoints.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BOOK_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BOOK_DIR="$BOOK_ROOT/book"
# The sources the book quotes: a forth-bootstrap checkout (the submodule, or
# $FORTH_BOOTSTRAP).
REPO_ROOT="$(cd "${FORTH_BOOTSTRAP:-$BOOK_ROOT/forth-bootstrap}" && pwd)"
TANGLE_AWK="$SCRIPT_DIR/tangle.awk"
INVENTORY="$SCRIPT_DIR/canonical-sources.txt"
CHECK_ONLY_INVENTORY="$SCRIPT_DIR/check-only-sources.txt"
declare -a required_sources=() check_only_sources=()
declare -A source_roles=() check_only_tests=()

usage() {
    sed -n '2,/^$/p' "$0" | sed 's/^# \{0,1\}//'
    exit 2
}

# chapters: the book's top-level chapter files in reading order -- the
# order book/SUMMARY.md links them. Unpublished chapters never count toward
# canonical coverage. A file's fences are concatenated in this order, so a
# chapter that moves (a new number, a new part) keeps its place by its
# position in SUMMARY.md, not by its file name.
chapters() {
    local f seen=" "
    [ -f "$BOOK_DIR/SUMMARY.md" ] || {
        echo "tangle: missing book/SUMMARY.md" >&2; return 1;
    }
    while IFS= read -r f; do
        case $f in */*|*\ *) continue ;; esac
        [ -f "$BOOK_DIR/$f" ] || {
            echo "tangle: published chapter $f is missing" >&2; return 1;
        }
        case $seen in *" $f "*) continue ;; esac
        seen="$seen$f "
        printf '%s\n' "$BOOK_DIR/$f"
    done < <(grep -o '](\([^)#]*\.md\)' "$BOOK_DIR/SUMMARY.md" | sed 's/^](//')
}

cmd_extract() {
    local outdir="${1:-}"
    [ -n "$outdir" ] || { echo "extract: missing OUTDIR" >&2; exit 2; }
    mkdir -p "$outdir"
    local files=() chapter_list
    chapter_list=$(chapters) || return 1
    [ -n "$chapter_list" ] || {
        echo "tangle: SUMMARY.md has no published chapters" >&2; return 1;
    }
    mapfile -t files <<< "$chapter_list"
    awk -f "$TANGLE_AWK" -v OUTDIR="$outdir" "${files[@]}"
}

# Each numbered source has exactly one role: taught byte-for-byte, or an
# explicit check-only exception mapped to a checkpoint in the source checkout.
# This is a static contract audit. It never executes the registered checkpoints.
load_source_contract() {
    required_sources=()
    check_only_sources=()
    source_roles=()
    check_only_tests=()
    [ -s "$INVENTORY" ] || {
        echo "tangle: missing or empty required-source inventory $INVENTORY" >&2
        return 1
    }
    [ -f "$CHECK_ONLY_INVENTORY" ] || {
        echo "tangle: missing check-only inventory $CHECK_ONLY_INVENTORY" >&2
        return 1
    }

    local fail=0 line required checkpoint extra src
    while IFS= read -r line || [ -n "$line" ]; do
        case $line in ''|'#'*) continue ;; esac
        read -r required extra <<< "$line"
        if ! is_numbered_source "$required" || [ -n "$extra" ]; then
            echo "FAIL  $line  (invalid canonical source entry)" >&2
            fail=1
            continue
        fi
        if [ -n "${source_roles[$required]:-}" ]; then
            echo "FAIL  $required  (duplicate canonical source entry)" >&2
            fail=1
            continue
        fi
        source_roles[$required]=canonical
        required_sources+=("$required")
        if [ ! -f "$REPO_ROOT/$required" ]; then
            echo "FAIL  $required  (required source file is missing)" >&2
            fail=1
        fi
    done < "$INVENTORY"
    if [ "${#required_sources[@]}" = 0 ]; then
        echo "tangle: required-source inventory contains no source paths" >&2
        fail=1
    fi

    while IFS= read -r line || [ -n "$line" ]; do
        case $line in ''|'#'*) continue ;; esac
        read -r required checkpoint extra <<< "$line"
        if ! is_numbered_source "$required" || ! is_checkpoint_path "$checkpoint" || [ -n "$extra" ]; then
            echo "FAIL  $line  (invalid check-only entry; expected numbered-source tests/checkpoint-path)" >&2
            fail=1
            continue
        fi
        case ${source_roles[$required]:-} in
            canonical)
                echo "FAIL  $required  (source is both canonical and check-only)" >&2
                fail=1
                continue ;;
            check-only)
                echo "FAIL  $required  (duplicate check-only source entry)" >&2
                fail=1
                continue ;;
        esac
        source_roles[$required]=check-only
        check_only_sources+=("$required")
        check_only_tests[$required]=$checkpoint
        if [ ! -f "$REPO_ROOT/$required" ]; then
            echo "FAIL  $required  (check-only source file is missing)" >&2
            fail=1
        fi
        if [ ! -f "$REPO_ROOT/$checkpoint" ]; then
            echo "FAIL  $required  (check-only checkpoint is missing: $checkpoint)" >&2
            fail=1
        fi
    done < "$CHECK_ONLY_INVENTORY"

    # Unknown future numbered sources cannot silently escape the audit.
    for src in "$REPO_ROOT"/seed/[0-9]*.hex0 "$REPO_ROOT"/forth/[0-9]*.fth "$REPO_ROOT"/cc/[0-9]*.fth; do
        [ -f "$src" ] || continue
        required=${src#"$REPO_ROOT"/}
        if [ -z "${source_roles[$required]:-}" ]; then
            echo "FAIL  $required  (numbered source absent from canonical-sources.txt and check-only-sources.txt)" >&2
            fail=1
        fi
    done
    return "$fail"
}

is_numbered_source() {
    [[ $1 =~ ^(seed/[0-9][[:alnum:]_.-]*\.hex0|(forth|cc)/[0-9][[:alnum:]_.-]*\.fth)$ ]]
}

is_checkpoint_path() {
    [[ $1 == tests/* && $1 =~ ^[[:alnum:]_./-]+$ ]] || return 1
    case /$1/ in *//*|*/./*|*/../*) return 1 ;; esac
}

report_check_only() {
    local source=$1
    printf 'CHECK-ONLY  %s  (checkpoint %s registered; not executed)\n' "$source" "${check_only_tests[$source]}"
}

cmd_verify() {
    local strict=""
    if [ "${1:-}" = "--strict" ]; then strict=1; fi

    local tmpdir
    tmpdir="$(mktemp -d)"
    trap "rm -rf '$tmpdir'" EXIT

    cmd_extract "$tmpdir"

    local fail=0
    local any=0
    if [ -n "$strict" ]; then
        load_source_contract || return 1
        local required
        for required in "${required_sources[@]}"; do
            if [ ! -f "$tmpdir/$required" ]; then
                echo "FAIL  $required  (no published file= coverage for required source)" >&2
                fail=1
            fi
        done
        for required in "${check_only_sources[@]}"; do
            if [ -f "$tmpdir/$required" ]; then
                echo "FAIL  $required  (check-only source has published file= coverage; reconcile its inventory role)" >&2
                fail=1
            else
                report_check_only "$required"
            fi
        done
    fi
    for t in $(cd "$tmpdir" && find . -type f | sed 's|^\./||' | LC_ALL=C sort); do
        local base src
        base="$t"
        t="$tmpdir/$t"
        any=1
        src="$REPO_ROOT/$base"
        if [ -n "$strict" ] && [ "${source_roles[$base]:-}" = check-only ]; then
            # The role conflict was already reported above; do not call it OK.
            continue
        fi
        if [ ! -f "$src" ]; then
            echo "FAIL  $base  (no such source file in the repository)" >&2
            fail=1
            continue
        fi

        if [ -n "$strict" ]; then
            if diff -q "$src" "$t" >/dev/null 2>&1; then
                echo "OK    $base  (strict, byte-identical)"
            else
                echo "FAIL  $base  (book does not tangle to byte-identical source)" >&2
                diff -u "$src" "$t" | sed -n '1,40p' >&2 || true
                fail=1
            fi
        else
            if verify_in_order "$src" "$t"; then
                local nt ns
                nt=$(wc -l <"$t")
                ns=$(wc -l <"$src")
                printf 'OK    %-24s  %4d / %4d lines covered\n' "$base" "$nt" "$ns"
            else
                fail=1
            fi
        fi
    done

    if [ "$any" = 0 ]; then
        echo "tangle verify: no file= blocks found in $BOOK_DIR" >&2
        return 1
    fi
    if [ -n "$strict" ] && [ "$fail" = 0 ]; then
        printf 'tangle verify: %d canonical sources byte-identical; check-only registrations: %d (not executed)\n' \
            "${#required_sources[@]}" "${#check_only_sources[@]}"
    fi
    return $fail
}

verify_in_order() {
    local src="$1" tangled="$2"
    awk -v SRC="$src" -v TANGLED="$tangled" '
        BEGIN {
            n = 0
            while ((getline line < SRC) > 0) {
                n++
                src[n] = line
            }
            close(SRC)
            cur = 1
            tno = 0
            while ((getline tline < TANGLED) > 0) {
                tno++
                found = 0
                for (i = cur; i <= n; i++) {
                    if (src[i] == tline) {
                        cur = i + 1
                        found = 1
                        break
                    }
                }
                if (!found) {
                    printf "FAIL  %s  (tangled line %d not found in source at-or-after src:%d)\n", \
                        TANGLED, tno, cur > "/dev/stderr"
                    printf "         tangled: %s\n", tline > "/dev/stderr"
                    exit 1
                }
            }
            close(TANGLED)
            exit 0
        }
    '
}

cmd_status() {
    local tmpdir
    tmpdir="$(mktemp -d)"
    trap "rm -rf '$tmpdir'" EXIT
    cmd_extract "$tmpdir"
    load_source_contract || return 1

    printf '%-28s %10s %10s %8s\n' "file" "covered" "total" "%"
    printf '%-28s %10s %10s %8s\n' "----" "-------" "-----" "-"
    for src in "$REPO_ROOT"/seed/[0-9]*.hex0 "$REPO_ROOT"/forth/[0-9]*.fth "$REPO_ROOT"/cc/[0-9]*.fth; do
        [ -f "$src" ] || continue
        local base nt ns pct
        base="${src#"$REPO_ROOT"/}"
        if [ "${source_roles[$base]:-}" = check-only ]; then
            report_check_only "$base"
            continue
        fi
        ns=$(wc -l <"$src")
        if [ -f "$tmpdir/$base" ]; then
            nt=$(wc -l <"$tmpdir/$base")
        else
            nt=0
        fi
        if [ "$ns" -gt 0 ]; then
            pct=$(( 100 * nt / ns ))
        else
            pct=0
        fi
        printf '%-28s %10d %10d %7d%%\n' "$base" "$nt" "$ns" "$pct"
    done
}

case "${1:-}" in
    extract) shift; cmd_extract "$@" ;;
    verify)  shift; cmd_verify  "$@" ;;
    status)  shift; cmd_status  "$@" ;;
    -h|--help|"") usage ;;
    *) echo "unknown command: $1" >&2; usage ;;
esac
