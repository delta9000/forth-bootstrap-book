# Chapter 53 — The sealed host run

Which programs actually executed on the way to the fixed point? A compiler report alone cannot answer that question. The sealed run supplies an initial executable inventory and an execution trace, so you can audit the ancestry of the programs behind the report.

## Establish the executable boundary

The launcher has a simple shape: prepare a root, enter it under tracing, then reduce the traces to successful and failed paths. Its `ROOT` argument defaults to `build-out/plumbing-root`; the companion trace directory is `ROOT.trace/` (`forth-bootstrap/chain/plumbing-root.sh:31`). The sealed executable boundary leaves the host kernel in place.

The host copies tracked files, including submodules, rather than carrying an existing build tree into the root. It then supplies the pinned input archives by hard link, falling back to a copy (`forth-bootstrap/chain/plumbing-root.sh:39`):

```text
git ls-files -z --recurse-submodules | tar --null -T - -cf - | tar -xf - -C "$R"
mkdir -p "$R/build-out/plumbing-inputs" "$R/build-out/lexer-inputs/archives" \
  "$R/build-out/direct-gcc-inputs" "$R/build-out/stage-b-inputs" "$R/build-out/stage-c-inputs" \
  "$R/build-out/plumbing/bin" "$R/tmp" "$R/dev" "$R/proc" "$R/usr"
for f in build-out/plumbing-inputs/*.tar.* build-out/lexer-inputs/archives/*; do
  ln "$(readlink -f "$f")" "$R/$f" 2>/dev/null || cp "$(readlink -f "$f")" "$R/$f"
done
for f in direct-gcc-inputs/gcc-4.0.4-git-944765863e.tar stage-b-inputs/binutils-2.30.tar \
         stage-c-inputs/musl-1.1.24.tar.gz; do
  ln "$(readlink -f "build-out/$f")" "$R/build-out/$f" 2>/dev/null || cp "$(readlink -f "build-out/$f")" "$R/build-out/$f"
done
```

These inputs include the plumbing archives, lexer archives, GCC source, binutils tar, and musl archive. Hard linking saves a copy; it does not verify a digest. The source-pin checks below establish which bytes those archive paths should contain.

Permissions make the starting condition testable. The host clears execute bits on regular files while retaining directory traversal, then publishes a separate executable copy of hex0-seed (`forth-bootstrap/chain/plumbing-root.sh:50`):

```text
chmod -R a-x+X "$R"
cp "$HEX0" "$R/hex0-seed"
chmod 755 "$R/hex0-seed"
: > "$R/dev/null"
ln -s build-out/plumbing/bin "$R/bin"
ln -s ../build-out/plumbing/bin "$R/usr/bin"
inventory=$(find "$R" -type f -perm /111 | sed "s|^$R/||")
[ "$inventory" = hex0-seed ] || { echo "plumbing-root: unexpected executables: $inventory" >&2; exit 1; }
echo "plumbing-root: initial executable inventory: hex0-seed only ($(find "$R" -type f | wc -l) files)"
```

In `a-x+X`, the removal happens before the conditional addition. Directories regain search permission; regular files do not regain execution permission. The inventory must contain exactly `hex0-seed`, or the launcher stops. Source scripts remain readable, so a newly built interpreter can later read them.

The host also creates the `/bin` and `/usr/bin` links shown above. Both lead into the root's plumbing output directory, rather than to host tools (`forth-bootstrap/chain/plumbing-root.sh:54`). Once the chain's bash exists there, `/bin/sh` denotes that bash, including for scripts with a `#!/bin/sh` interpreter line (`forth-bootstrap/chain/plumbing-root.sh:25`).

## Trace every entry

The host keeps strace outside the root so the observer does not become another starting executable. Each invocation traces bwrap and its descendants; bwrap binds the prepared root as `/`, binds the host's null device, creates proc, and clears the environment before starting the requested program (`forth-bootstrap/chain/plumbing-root.sh:60`):

```text
# enter N CMD...: run CMD inside the root, tracing execve into $T/execveN.txt.
enter() {
  n=$1
  shift
  strace -f -qq --seccomp-bpf -e trace=execve -o "$T/execve$n.txt" \
    bwrap --unshare-user --bind "$REPO/$R" / --dev-bind /dev/null /dev/null --proc /proc \
      --chdir / --clearenv --setenv PATH /bin --setenv HOME / --setenv LC_ALL C "$@"
}
```

`-f` follows child processes. `-e trace=execve` records attempts to replace a process image, including attempts that fail. The environment supplies `/bin` as the initial search path, with `/` as the working directory. The root has access to the host kernel through this user namespace; the launcher does not boot another kernel (`forth-bootstrap/chain/plumbing-root.sh:65`).

The entry order exposes each executable handoff. These are the launcher's entries, not separate host builds (`forth-bootstrap/chain/plumbing-root.sh:69`):

| Entry | Program inside the root | Responsibility |
|---|---|---|
| First | `/hex0-seed` | Write `/seed-forth` from the seed source |
| Second | `/seed-forth` | Read the driver start file to build seed-cc and seed-ar |
| Third | `/build-out/seed-cc/seed-cc` | Build kaem from C source |
| Fourth | `/build-out/plumbing/bin/kaem` | Interpret the plumbing recipe and start the GCC chain |

```text
enter 1 /hex0-seed /seed/000-seed.hex0 /seed-forth > "$T/entry1.log" 2>&1
chmod 755 "$R/seed-forth"
enter 2 /seed-forth < "$R/cc/driver/seed-cc-start.fth" > "$T/entry2.log" 2>&1
enter 3 /build-out/seed-cc/seed-cc -static vendor/mescc-tools/Kaem/kaem.c \
  vendor/mescc-tools/Kaem/variable.c vendor/mescc-tools/Kaem/kaem_globals.c \
  vendor/stage0-posix/mescc-tools-extra/M2libc/bootstrappable.c \
  -o build-out/plumbing/bin/kaem > "$T/entry3.log" 2>&1
status=0
enter 4 /build-out/plumbing/bin/kaem --verbose --strict --file chain/plumbing/chain.kaem > "$T/entry4.log" 2>&1 || status=$?
echo "plumbing-root: entry 4 exit $status after $(( $(date +%s) - start )) s"
```

The `chmod` between the first and second entries is a host action. Hex0-seed writes seed-forth without its execute bit, and the host grants that bit before re-entry (`forth-bootstrap/chain/plumbing-root.sh:24`). Granting permission is different from supplying another program's bytes.

The final recipe builds the plumbing tools and bash, then uses that bash to run the GCC controller inside the root (`forth-bootstrap/chain/plumbing/chain.kaem:13`). The fixed-point comparison is already established (Chapter 52). Here the question is whether an unexpected executable participated in reaching it.

## Read successes separately from attempts

A trace line can stop at `<unfinished ...>` when strace switches to another process before reporting the syscall result. The later `<... execve resumed>` line carries that result, but not the path. Joining by process ID prevents a failed interrupted lookup from being counted as an execution (`forth-bootstrap/chain/plumbing-root.sh:80`):

```text
# Summary.  strace -f splits an execve that another process interrupts into
# an "<unfinished ...>" line holding the path and a "resumed" line holding the
# result; join them by pid, then count each path executed.
cat "$T"/execve[1-4].txt | awk '
/execve\(/ && /<unfinished/ { match($0, /execve\("[^"]*"/); p[$1] = substr($0, RSTART + 8, RLENGTH - 9); next }
/<\.\.\. execve resumed>/ { path = p[$1]; delete p[$1]; r = $0; sub(/.*= /, "", r); print (r ~ /^0/ ? "ok " : "fail ") path; next }
/execve\(/ { match($0, /execve\("[^"]*"/); path = substr($0, RSTART + 8, RLENGTH - 9); r = $0; sub(/.*= /, "", r); print (r ~ /^0/ ? "ok " : "fail ") path }
' > "$T/execve-joined.txt"
sed -n 's/^ok //p' "$T/execve-joined.txt" | sort | uniq -c | sort -rn > "$T/execve-programs.txt"
sed -n 's/^fail //p' "$T/execve-joined.txt" | sort | uniq -c | sort -rn > "$T/execve-failed.txt"
```

The awk array remembers the path under `$1`, the process ID. A resumed record consumes that saved path. A complete record needs no saved state. Both forms become `ok PATH` when the result starts with zero and `fail PATH` otherwise.

`execve-joined.txt` preserves the classified events in trace order. `execve-programs.txt` groups only successes by the literal path and sorts by frequency; `execve-failed.txt` does the same for failures. Different spellings of the same program can occupy different rows, so a distinct-path count is not a count of distinct executable contents.

The first rows of `execve-programs.txt` from a recorded run:

```text
  12292 //build-out/plumbing/bin/cat
   8620 //build-out/plumbing/bin/sed
   8278 //build-out/plumbing/bin/rm
   4739 //build-out/plumbing/bin/bash
   3706 //build-out/chain/stage-c/toolchain/as
```

Audit every successful path against the entry and construction history. `/hex0-seed` is the permitted starting program. A host bwrap path is the wrapper entering the root. Other successes must resolve to artifacts the chain produced there, or to scripts interpreted by its built shell. Paths such as `/bin/sh`, relative paths, `..`, and the doubled slashes above require resolving their spelling against the root and the invoking process's working directory. The mount and link setup supplies that boundary (`forth-bootstrap/chain/plumbing-root.sh:54`). A name containing `build-out` alone is not evidence of ancestry: check its producer and the raw `execveN.txt` record when its identity is unclear.

Failures are evidence of attempts, not of inherited executables running. The initial search path points into the root's own tool directory, and the root receives no host `/usr/bin` tree (`forth-bootstrap/chain/plumbing-root.sh:65`). Programs searching for an unavailable command can therefore leave failed paths. For example, the recorded raw trace contains this unsuccessful lookup:

```text
907338 execve("/usr/bin/arch", ["/usr/bin/arch", "-k"], 0x7885e961f7e0 /* 31 vars */) = -1 ENOENT (No such file or directory)
```

The recorded `execve-failed.txt` also lists `/usr/convex/getsysinfo` and `/bin/universe`. A failed probe of an absent system utility is expected in this sparse root; it does not show that utility executing. Consult the raw result before treating every failure as absence: the summary classifies all nonzero results as `fail`, even though its final message calls them “failed lookups of absent programs.” Permission and format errors need separate investigation.

The final count line reports successful calls, host entries, distinct successful spellings, and failed attempts (`forth-bootstrap/chain/plumbing-root.sh:90`):

```text
ok=$(grep -c '^ok ' "$T/execve-joined.txt" || true)
hosts=$(grep -c '^ok /usr/bin/bwrap$' "$T/execve-joined.txt" || true)
echo "plumbing-root: $ok successful execve calls ($hosts of them the host's bwrap entering the root), $(wc -l < "$T/execve-programs.txt") distinct paths; $(grep -c '^fail ' "$T/execve-joined.txt" || true) failed lookups of absent programs"
```

The host-entry counter recognizes the literal `/usr/bin/bwrap`. If bwrap is installed elsewhere, its successful path still appears in the trace, but this counter will miss it. Inspect the successful list rather than treating that count alone as the audit verdict.

README records one run taking 18 minutes, with about 63,000 programs run and 2,581 distinct paths (`forth-bootstrap/README.md:237`). Those are recorded observations, not a duration or count promised for another machine. The launcher also returns the final entry's exit status after writing the summaries (`forth-bootstrap/chain/plumbing-root.sh:94`); trace completeness and build success both matter.

## Bind the archive names to bytes

The trace answers which paths ran. Source pins answer which archive bytes were supplied. The manifest's header distinguishes whole-cache checking from agreement with each stage's pin file (`forth-bootstrap/MANIFEST.sha256:1`):

```text
# MANIFEST.sha256 -- every archive the route reads, with its sha256.
# Check the whole cache from the repository root with
#     sha256sum -c MANIFEST.sha256
# (add --ignore-missing to check a partial one).  Each stage also checks its
# own inputs before unpacking them, against the file named in its group
# below; tools/check-pins.py proves those files agree with this one.
# build-out/stage-b-inputs/binutils-2.30.tar is the plain tar inside
# binutils-2.30.tar.xz (xz -dc), since the chain's tools read no xz; the
# others are the release archives as published (see each SOURCES file).
```

A digest pin fixes content independently of a download location. It does not establish that the upstream source is correct. The plain binutils tar has its own pin because decompression changes the archive bytes being checked.

The fetcher reads every non-comment manifest row as a digest and destination path. Without path arguments it fetches all manifest entries, including archives for later layers; with path arguments it rejects names absent from the manifest (`forth-bootstrap/tools/fetch-archives.py:124`). Its release URL map and `chain/gcc64/SOURCES` supply locations, including git exports and members extracted from downloaded archives (`forth-bootstrap/tools/fetch-archives.py:79`). For a git export it checks the fetched commit before creating the tar (`forth-bootstrap/tools/fetch-archives.py:90`).

Derived inputs follow their source archives: binutils is decompressed with xz, and the direct GCC and stage-C musl archives are copied from their distfiles counterparts (`forth-bootstrap/tools/fetch-archives.py:64`). Destinations are the manifest's `build-out/` paths. An existing file is retained only when its digest matches (`forth-bootstrap/tools/fetch-archives.py:144`):

```text
    for path in order:
        dest = pathlib.Path(path)
        if dest.is_file() and sha(dest) == manifest[path]:
            print(f"ok      {path}")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        name = dest.name
        with tempfile.TemporaryDirectory(dir=dest.parent) as tmp:
            tmp = pathlib.Path(tmp)
            out = tmp / name
```

Downloads and derived files stay in a temporary directory until their final digest agrees. This prevents a bad transfer from being published at the pinned destination (`forth-bootstrap/tools/fetch-archives.py:181`):

```text
            got = sha(out)
            if got != manifest[path]:
                print(f"FAIL    {path}: sha256 {got}, pinned {manifest[path]}")
                bad += 1
                continue
            os.replace(out, dest)
            print(f"fetched {path}")
    if bad:
        sys.exit(f"fetch-archives: {bad} archive(s) missing or wrong")
    print(f"fetch-archives: all {len(wanted)} archives in place, sha256 as pinned")
```

`check-pins.py` checks the declarations rather than hashing downloaded files. It maps the plumbing, lexer, chain, late-tool, and gcc64 pins to manifest paths; the stage12 unpack list contributes paths whose digest is read from the manifest itself (`forth-bootstrap/tools/check-pins.py:28`). It rejects missing entries, disagreeing digests, and manifest entries owned by no stage (`forth-bootstrap/tools/check-pins.py:39`):

```text
    bad = 0
    for f, path, sha in pins:
        if path not in manifest:
            print(f"check-pins: {f}: {path} is not in MANIFEST.sha256"); bad += 1
        elif sha is not None and manifest[path] != sha:
            print(f"check-pins: {f}: {path} is {sha}, MANIFEST.sha256 says {manifest[path]}"); bad += 1
    for path in sorted(set(manifest) - {p for _, p, _ in pins}):
        print(f"check-pins: MANIFEST.sha256: {path} is pinned by no stage"); bad += 1
    if bad:
        sys.exit(1)
    print(f"check-pins: {len(pins)} stage pins agree with the {len(manifest)} entries of MANIFEST.sha256")
```

Thus this check works before fetching archives. Checking archive pin agreement and checking archive contents are separate operations.

## Try it

Run these commands from the forth-bootstrap checkout root. Pin agreement needs only the checkout:

<!-- check-tryit: the runner selects only blocks piping into ./seed-forth and does not copy tools/, MANIFEST.sha256, or the pin files; run directly in the checkout. -->
<!-- tryit: skip -->
```sh
python3 tools/check-pins.py
```

```text
check-pins: 45 stage pins agree with the 45 entries of MANIFEST.sha256
```

Exercise the trace join without a long build. The following synthetic sample interleaves an unfinished successful call with an absent-program lookup. The awk rules are copied from the launcher (`forth-bootstrap/chain/plumbing-root.sh:84`). The temporary directory is removed when the subshell exits.

<!-- check-tryit: the runner selects only blocks piping into ./seed-forth; this host awk audit runs directly and needs no seed input. -->
<!-- tryit: skip -->
```sh
(
audit_dir=$(mktemp -d) || exit
trap 'rm -rf "$audit_dir"' EXIT
cat > "$audit_dir/sample.txt" <<'TRACE'
101 execve("/hex0-seed", ["/hex0-seed"], 0x0) = 0
102 execve("/build-out/plumbing/bin/bash", ["bash"], 0x0 <unfinished ...>
103 execve("/usr/bin/arch", ["arch"], 0x0) = -1 ENOENT (No such file or directory)
102 <... execve resumed>) = 0
TRACE
awk '
/execve\(/ && /<unfinished/ { match($0, /execve\("[^"]*"/); p[$1] = substr($0, RSTART + 8, RLENGTH - 9); next }
/<\.\.\. execve resumed>/ { path = p[$1]; delete p[$1]; r = $0; sub(/.*= /, "", r); print (r ~ /^0/ ? "ok " : "fail ") path; next }
/execve\(/ { match($0, /execve\("[^"]*"/); path = substr($0, RSTART + 8, RLENGTH - 9); r = $0; sub(/.*= /, "", r); print (r ~ /^0/ ? "ok " : "fail ") path }
' "$audit_dir/sample.txt"
)
```

Observed output:

```text
ok /hex0-seed
fail /usr/bin/arch
ok /build-out/plumbing/bin/bash
```

For a full audit, fetching needs network access and the fetcher's curl, git, and xz tools (`forth-bootstrap/tools/fetch-archives.py:17`). Whole-cache hashing needs the fetched archives. The launcher additionally needs bwrap, strace, and working user namespaces (`forth-bootstrap/chain/plumbing-root.sh:6`). Its default root and trace directories are removed before preparation, so preserve any previous evidence first (`forth-bootstrap/chain/plumbing-root.sh:37`).

<!-- check-tryit: requires network, pinned archives, bwrap/strace and user namespaces; a sustained build exceeds the runner timeout and its scratch checkout omits chain/ and tools/. -->
<!-- tryit: skip -->
```sh
python3 tools/fetch-archives.py
sha256sum -c MANIFEST.sha256
sh chain/plumbing-root.sh
```

Allow a sustained build: 18 minutes on a 24-thread host (`forth-bootstrap/check-all.sh:24`), longer with fewer. Inspect `build-out/plumbing-root.trace/execve-programs.txt` and `execve-failed.txt`, then resolve each unexplained success using the raw traces and its producing recipe. The report from Chapter 52 establishes the build result; the audit establishes which executable paths participated.

## Exercise

**Trace (easy).** Change the resumed result in the synthetic sample from success to `-1 ENOENT`. Predict the output before running the modified checkpoint. Explain why counting only lines containing `execve(` would misclassify or lose the interrupted call's result.

**Verify (moderate).** With a completed root and its traces, choose a successful path outside the plumbing bin directory. Identify the recipe that produced it and resolve its path inside the prepared root. Explain why a row in the failed list cannot serve as evidence that the named program ran.
