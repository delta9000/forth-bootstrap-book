#!/usr/bin/env python3
"""List, inspect, or run one short checkpoint from the published book.

    python3 tools/book-lab.py list [CHAPTER]
    python3 tools/book-lab.py show CHAPTER.BLOCK
    python3 tools/book-lab.py run CHAPTER.BLOCK [--timeout SECONDS]

Selectors count sh/bash/shell fences in each published numbered chapter,
including excluded fences. Untagged transcripts and canonical source fences
are never executable labs. Commands are read from the book on every call.

Run executes the exact fence in a clean, noninteractive Bash from the source
checkout ($FORTH_BOOTSTRAP or ./forth-bootstrap), without injecting shell
options or rewriting paths. It is not a sandbox: the block's documented
effects and cleanup apply. Run only one lab at a time. Chapters 50 onward,
explicit skips, loops, Stage A, full builds, and context-dependent commands
are listed but cannot be run here. There is deliberately no run-all/force.

The exit status and explicit `tryit: expect` UTF-8 output metadata are checked.
Trailing newlines are ignored, as in check-tryit.py. Other expectations in
prose, comments, or observed-output transcripts remain for the reader to
compare. A passing exit status with no metadata does not check stdout.
"""

import argparse
import glob
import importlib.util
import math
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys


SPEC = importlib.util.spec_from_file_location(
    "check_tryit", Path(__file__).with_name("check-tryit.py"))
TRYIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TRYIT)

HOST_TOOLS = ("basename", "cat", "chmod", "cp", "dd", "file", "gcc", "head",
              "mktemp", "mv", "objdump", "od", "readelf", "rm", "sed",
              "sort", "tail", "timeout", "wc", "xxd")
LONG_COMMAND = re.compile(
    r"\b(?:stage-[a-z]-check|bootstrap|build-full|build-gcc-refs)\.sh\b"
    r"|(?:^|[\s;&|])(?:\./)?(?:tests/|test\.sh\b|chain/[^\s]*\.sh\b)"
    r"|(?:^|[\s;&|])(?:make|gforth|git|qemu-system-\S+)\b")
ROOT_COMMAND = re.compile(r"\bcd\s+(?:\"|')?(?:\./)?forth-bootstrap\b"
                          r"|\btools/[\w-]+\.(?:py|sh)\b")


def inventory():
    """Follow SUMMARY, so retired chapters cannot become accidental labs."""
    labs = []
    seen = set()
    for filename in TRYIT.published_files():
        match = re.match(r"(\d+)-", Path(filename).name)
        if not match:
            continue
        chapter = int(match[1])
        if chapter in seen:
            raise ValueError(f"two published chapters have number {chapter}")
        seen.add(chapter)
        blocks = [block for block in TRYIT.find_blocks(filename, include_omitted=True)
                  if block["tag"] in {"sh", "bash", "shell"}]
        for index, block in enumerate(blocks, 1):
            labs.append(dict(block, selector=f"{chapter}.{index}", chapter=chapter,
                             filename=filename))
    return labs


def code(lab):
    return "\n".join(lab["body"]) + "\n"


def location(lab):
    return f"{os.path.relpath(lab['filename'], TRYIT.BOOK_ROOT)}:{lab['line']}"


def exclusion(lab):
    if lab.get("metadata_error"):
        return lab["metadata_error"]
    if lab["marker"] == "skip":
        return "explicit tryit: skip marker; follow the chapter manually"
    if lab["marker"] == "loops" or TRYIT.LOOP_RE.search(code(lab) + lab["para"]):
        return "documented loop; requires an interactive/manual run"
    if not 1 <= lab["chapter"] <= 49:
        return "outside the short-lab scope (chapters 1–49); follow the chapter manually"
    if LONG_COMMAND.search(code(lab)):
        return "Stage A, external build, test suite, or bootstrap build; run manually"
    if ROOT_COMMAND.search(code(lab)):
        return "uses the book root; labs run from forth-bootstrap (see the chapter)"
    if not re.search(r"(?:\./)?seed-forth\b|(?:\./)?seed/build\.sh\b", code(lab)):
        return "not a self-contained seed checkpoint"
    # Current published labs supply stdin in their source. A naked seed would
    # otherwise look successful when this tool closes its noninteractive stdin.
    for line in lab["body"]:
        command = TRYIT.split_comment(line)[0].strip()
        if re.fullmatch(r"(?:timeout\s+\S+\s+)?\./seed-forth", command):
            return "interactive seed invocation; run manually"
    return None


def prerequisites(lab, source):
    """Return readable prerequisites and current problems without mutating."""
    shell = "\n".join(TRYIT.split_comment(line)[0] for line in lab["body"])
    commands = [tool for tool in HOST_TOOLS
                if re.search(r"(?:^\s*|[;&|({]\s*|\b(?:if|then|do)\s+)"
                             + re.escape(tool) + r"(?:\s|$)", shell, re.M)]
    needs = ["Linux x86-64", "initialized source checkout", "built seed-forth", "bash"] + commands
    problems = []
    if platform.system() != "Linux" or platform.machine().lower() not in ("x86_64", "amd64"):
        problems.append("needs Linux x86-64; use a Linux x86-64 VM or emulation")
    if not (source / "seed/000-seed.hex0").is_file():
        problems.append(f"source checkout missing at {source}; run git submodule update --init --recursive from the book root")
    if not os.access(source / "seed-forth", os.X_OK):
        problems.append(f"seed-forth is not built at {source}; run ./seed/build.sh from that source checkout")
    for tool in ["bash"] + commands:
        if not shutil.which(tool):
            problems.append(f"missing host tool: {tool}")
    paths = sorted(set(re.findall(r"\b(?:seed|forth|cc|chain|vendor)/[\w./*?\[\]-]+", shell)))
    for relative in paths:
        if not glob.glob(str(source / relative)):
            problems.append(f"missing source prerequisite: {relative}; initialize the checkout and its submodules")
    return needs, problems


def stop_process_group(proc, first_signal=signal.SIGTERM):
    """Allow the fence's traps to run, then reap/kill remaining descendants."""
    try:
        os.killpg(proc.pid, first_signal)
    except ProcessLookupError:
        pass
    try:
        return proc.communicate(timeout=2)
    except subprocess.TimeoutExpired:
        pass
    finally:
        # The shell may exit while a child retains an output pipe or ignores
        # TERM. A new session gives this run its own process group.
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    return proc.communicate()


def run(lab, source, timeout):
    reason = exclusion(lab)
    if reason:
        print(f"book-lab: excluded {lab['selector']}: {reason}", file=sys.stderr)
        return 2
    _, problems = prerequisites(lab, source)
    if problems:
        for problem in problems:
            print(f"book-lab: {problem}", file=sys.stderr)
        return 2
    env = {key: value for key, value in os.environ.items()
           if key not in ("BASH_ENV", "ENV", "SHELLOPTS", "BASHOPTS")}
    print(f"book-lab: running {lab['selector']} ({location(lab)}) in {source}", file=sys.stderr)
    proc = subprocess.Popen(["bash", "--noprofile", "--norc", "-c", code(lab)],
                            cwd=source, env=env, stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            start_new_session=True)
    stopped = None
    try:
        output, errors = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        stopped = 124
        output, errors = stop_process_group(proc)
    except KeyboardInterrupt:
        stopped = 130
        output, errors = stop_process_group(proc, signal.SIGINT)
    sys.stdout.buffer.write(output)
    sys.stdout.buffer.flush()
    sys.stderr.buffer.write(errors)
    sys.stderr.buffer.flush()
    if stopped:
        reason = f"timed out after {timeout:g}s" if stopped == 124 else "interrupted"
        print(f"book-lab: FAIL {lab['selector']}: {reason}", file=sys.stderr)
        return stopped
    if proc.returncode:
        print(f"book-lab: FAIL {lab['selector']}: shell exited {proc.returncode}", file=sys.stderr)
        return proc.returncode if proc.returncode > 0 else 128 - proc.returncode
    if lab["expected"] is not None:
        if not TRYIT.metadata_matches(output, lab["expected"]):
            print(f"book-lab: FAIL {lab['selector']}: expected UTF-8 stdout {lab['expected']!r}; got {output!r}", file=sys.stderr)
            return 1
        checked = "stdout matches expected metadata"
    else:
        checked = "no expected-output metadata; compare the chapter's output"
    print(f"book-lab: PASS {lab['selector']}: shell exited 0; {checked}", file=sys.stderr)
    return 0


def positive_seconds(value):
    seconds = float(value)
    if not math.isfinite(seconds) or seconds <= 0:
        raise argparse.ArgumentTypeError("timeout must be a finite positive number")
    return seconds


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    listing = commands.add_parser("list", help="list published shell fences, prerequisites and exclusions")
    listing.add_argument("chapter", type=int, nargs="?")
    showing = commands.add_parser("show", help="print the exact shell fence, including excluded fences")
    showing.add_argument("selector", help="CHAPTER.BLOCK, for example 26.1")
    running = commands.add_parser("run", help="run one short checkpoint from the source root")
    running.add_argument("selector", help="CHAPTER.BLOCK, for example 26.1")
    running.add_argument("--timeout", type=positive_seconds, default=30, metavar="SECONDS")
    args = parser.parse_args(argv)
    try:
        labs = inventory()
        source = Path(TRYIT.ROOT).resolve()
        if args.command == "list":
            selected = [lab for lab in labs if args.chapter is None or lab["chapter"] == args.chapter]
            if not selected:
                parser.error("no published shell checkpoints for that chapter")
            for lab in selected:
                reason = exclusion(lab)
                needs, problems = prerequisites(lab, source) if not reason else ([], [])
                state = "EXCLUDED" if reason else "BLOCKED" if problems else "READY"
                print(f"{lab['selector']:<6} {state:<8} {location(lab)}")
                print("       " + (reason or "requires: " + ", ".join(needs)))
                for problem in problems:
                    print("       " + problem)
            return 0
        if not re.fullmatch(r"[1-9]\d*\.[1-9]\d*", args.selector):
            parser.error("selector must be CHAPTER.BLOCK, for example 26.1")
        lab = next((lab for lab in labs if lab["selector"] == args.selector), None)
        if lab is None:
            parser.error(f"unknown checkpoint {args.selector}; use list to see selectors")
        if args.command == "show":
            sys.stdout.write(code(lab))
            return 0
        return run(lab, source, args.timeout)
    except (OSError, ValueError) as error:
        print(f"book-lab: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
