# Chapter 52 — GCC 4.0.4: stages C and D

Stage D's report opens with one line: `# Stage D: fixed point reached`. Behind it, GCC 4.0.4 built by seed-cc builds GCC, that GCC builds GCC again, and the last two installations agree file for file. The route runs from the plumbing tools of Chapter 51 to that line, and on to the tools the stable compiler builds next.

## Put the output tools before the compiler

The construction has this shape: seed-cc → binutils → GCC compiler proper and driver → libgcc and musl → repeated GCC builds. The controller keeps the plumbing tools (Chapter 51) as its command environment, then runs the stages in dependency order (`forth-bootstrap/chain/gcc-direct/chain.sh:28`):

```sh
BIN=$ROOT/build-out/plumbing/bin
PATH=$BIN
export PATH
out=${out:-$ROOT/build-out/chain}
mkdir -p "$out"
out=$(absdir "$out")
started=$(date +%s)
if grep -qx 'built: 6 of 6' "$out/binutils/stage-b/report.txt" 2>/dev/null; then
  note "binutils: already built in $out/binutils"
else
  note "binutils"
  "$BASH" "$ROOT/chain/gcc-direct/binutils.sh" "$out/binutils" --oyacc "$BIN/oyacc" --flex "$BIN/flex" -j "$jobs"
fi
note "stage C"
"$BASH" "$ROOT/chain/gcc-direct/stage-c.sh" "$out/stage-c" --binutils "$out/binutils" \
  --oyacc "$BIN/oyacc" --flex "$BIN/flex" -j "$jobs" --resume
note "stage D"
"$BASH" "$ROOT/chain/gcc-direct/stage-d.sh" "$out/stage-d" --stage-c "$out/stage-c" \
  --oyacc "$BIN/oyacc" --flex "$BIN/flex" -j "$jobs"
```

`chain.sh` stops after Stage D; the late tools at the end of this chapter run from the K1 route.

GCC's `cc1` is the compiler proper: it translates C into assembly. The driver coordinates that translation with assembly and linking. Before either can build a replacement compiler, GCC's assembly output needs an assembler, and its objects need a linker. The seed-built binutils supplies that boundary; Stage C checks its tools against the Stage B report before copying them into its toolchain directory (`forth-bootstrap/chain/gcc-direct/stage-c.sh:110`).

Binutils uses the pinned source and regenerates its shipped parsers and scanners, so the build depends on the chain's generators rather than accepting generated C from the release (`forth-bootstrap/chain/gcc-direct/binutils.sh:64`):

```sh
note "unpacking $BINUTILS_TAR"
source=$work/src/binutils-2.30
untar "$BINUTILS_TAR" "$source" binutils-2.30
: > "$work/generated-removed.txt"
for name in $GENERATED; do
  [ -f "$source/$name" ] || die "listed generated file is absent: $name"
  echo "$(sha "$source/$name") $name" >> "$work/generated-removed.txt"
  rm "$source/$name"
done

note "configuring: $work"
status=0
"$BASH" "$ROOT/chain/gcc-direct/configure.sh" --package binutils --forth-ar --source "$source" --work "$work" \
  > "$work.configure.out" 2>&1 || status=$?
```

The `GENERATED` list identifies the files removed; handwritten support headers stay. Configuration uses the established runner. The build names both spellings of the parser and scanner variables and removes warning flags that seed-cc cannot accept (`forth-bootstrap/chain/gcc-direct/binutils.sh:81`):

```sh
  . "$work/configure-env.sh"
  overrides="CFLAGS= LDFLAGS= WARN_CFLAGS= WARN_WRITE_STRINGS= YACC=$oyacc BISON=$oyacc LEX=$flex FLEX=$flex"
  note "building with $jobs jobs; log: $work/make.log"
  status=0
  (cd "$work/build/top" && make -k -j "$jobs" $overrides all-gas all-ld all-binutils) > "$work/make.log" 2>&1 || status=$?
  note "make exit $status"
  steps="$steps; make $status"
  for directory in gas ld binutils; do
    if [ ! -f "$work/build/top/$directory/Makefile" ]; then
      note "$directory not configured; skipped"
      steps="$steps; make-$directory skipped"
      continue
    fi
    status=0
    (cd "$work/build/top/$directory" && make -k -j "$jobs" $overrides) > "$work/make-$directory.log" 2>&1 || status=$?
    note "make $directory exit $status"
    steps="$steps; make-$directory $status"
  done
```

The top-level make can fail because recursive make drops the warning overrides. The direct directory builds retain them. The report requires those builds and configuration to succeed, and records each executable's hash; building an executable is distinct from proving its behaviour (`forth-bootstrap/chain/gcc-direct/binutils.sh:122`).

## Let the Makefile select cc1

A compiler census asks the configured Makefile which objects belong to the compiler, rather than maintaining a second source list. First the census builds libiberty. Then it adds a tiny print target to the existing Makefile, preserving the upstream selection and dependencies (`forth-bootstrap/chain/gcc-direct/census.sh:58`):

```sh
started=$(date +%s)
(. "$work/libiberty/configure-env.sh"
 cd "$work/libiberty/build/libiberty"
 run "$log" make -j "$jobs" CFLAGS= LDFLAGS= libiberty.a)

gcc_build=$work/gcc/build/gcc
# Ask the configured Makefile itself which objects cc1 is linked from.
printf 'print-cc1-objects:\n\t@echo $(sort $(C_OBJS) main.o $(OBJS))\n' > "$out/print-cc1-objects.mk"
objects=$(. "$work/gcc/configure-env.sh"; cd "$gcc_build" && make -s -f Makefile -f "$out/print-cc1-objects.mk" print-cc1-objects) \
  || die "could not list cc1 objects"
echo $objects | tr ' ' '\n' > "$out/objects.txt"
count=$(wc -l < "$out/objects.txt" | tr -d ' ')
note "$count cc1 objects; make log: $log"
```

`C_OBJS` selects the C front end; `OBJS` supplies the shared compiler machinery. Sorting the expansion removes duplicate object names. The count comes from this configuration, not a constant in the script.

Generated compiler source belongs to the same dependency graph. The original Makefiles build and execute source generators with seed-cc, then compile their products with the real per-object flags (`forth-bootstrap/chain/gcc-direct/census.sh:12`). A generator is a build-time program whose output becomes another compilation input. Merely supplying a header would bypass that program and its builder.

The census requests every selected object with `make -k`, so independent units can still compile after a failure. Its override string names oyacc and flex and makes undeclared calls compilation errors (`forth-bootstrap/chain/gcc-direct/census.sh:53`):

```sh
# census_overrides WORK OYACC FLEX: the gcc make overrides (stage-c.sh too).
libiberty=$work/libiberty/build/libiberty/libiberty.a
libcpp=$work/libcpp/build/libcpp/libcpp.a
GCC_OVERRIDES="CFLAGS=-Werror=implicit-function-declaration LDFLAGS= BISON=$oyacc FLEX=$flex LIBIBERTY=$libiberty BUILD_LIBIBERTY=$libiberty CPPLIB=$libcpp"

```

An undeclared C function can acquire an integer return type at its call site. That can destroy a pointer result even when linking finds a definition. Rejecting the call catches the type error before the link hides the missing declaration.

With `--link`, libcpp is archived and the upstream `cc1` target performs the final link. Libcpp's hardcoded archiver must be replaced explicitly (`forth-bootstrap/chain/gcc-direct/census.sh:80`):

```sh
linked=
if [ -n "$link" ]; then
  # libcpp's 4.0.4 Makefile hardcodes `AR = ar` with `cru`; the archive is
  # removed just before, so `rc` with seed-ar is the same request.
  (. "$work/libcpp/configure-env.sh"
   cd "$work/libcpp/build/libcpp"
   run "$log" make -j "$jobs" CFLAGS= LDFLAGS= "AR=$AR" ARFLAGS=rc libcpp.a) || status=1
  (. "$work/gcc/configure-env.sh"
   cd "$gcc_build"
   run "$log" make $GCC_OVERRIDES cc1) || status=1
  if [ -f "$gcc_build/cc1" ]; then linked=1; fi
fi
```

The configured seed-cc performs this link with its Forth linker, using the established archive contract (Chapter 42). The census records built and missing objects and the linked compiler's identity. Its own report limits the conclusion to compilation and linking; it makes no execution or bootstrap claim (`forth-bootstrap/chain/gcc-direct/census.sh:105`). Stage C supplies the execution boundary.

## Cross from the builder's runtime to the target runtime

Stage C installs musl's headers before configuring GCC. The headers describe the target environment even though seed-cc builds the compiler executable. GCC configuration receives both the binutils directory and a sysroot, the directory tree containing its target headers and libraries (`forth-bootstrap/chain/gcc-direct/stage-c.sh:157`):

```sh
step_headers() {
  mkdir -p "$work/musl-headers"
  (cd "$work/musl-headers" && run "$out/headers.log" make -f "$musl_source/Makefile" "srcdir=$musl_source" \
     ARCH=x86_64 prefix=/usr "DESTDIR=$sysroot" install-headers)
  result headers "$(files "$sysroot/usr/include" | wc -l | tr -d ' ')"
}

step_configure() {
  local component
  for component in libiberty libcpp gcc; do
    if [ $component = gcc ]; then
      run "$out/configure.log" "$BASH" "$ROOT/chain/gcc-direct/configure.sh" --component gcc --forth-ar \
        --source "$gcc_source" --work "$work/gcc" --with-binutils "$toolchain" --with-sysroot "$sysroot"
    else
      run "$out/configure.log" "$BASH" "$ROOT/chain/gcc-direct/configure.sh" --component $component --forth-ar \
        --source "$gcc_source" --work "$work/$component"
    fi
  done
```

The input step unpacks GCC 4.0.4 and musl 1.1.24, applies the checked alloca adapter, and patches collect2 (`forth-bootstrap/chain/gcc-direct/stage-c.sh:126`). The adapter checks the source and patch hashes before application and the result afterward (`forth-bootstrap/chain/gcc-direct/stage-c.sh:143`). The collect2 correction prevents a failed link probe using `/dev/null` as its output from unlinking that device (`forth-bootstrap/chain/gcc-direct/stage-c.sh:131`).

After the census links `cc1`, GCC's Makefile builds `xgcc`, `cpp`, `collect2`, and `specs` (`forth-bootstrap/chain/gcc-direct/stage-c.sh:178`). `xgcc` is the build-tree driver. The next compilation changes builder: libgcc is compiled by this GCC, rather than seed-cc. Libgcc supplies target support routines that generated code calls when an operation needs a helper.

Recursive target-library builds discard command-line overrides. Stage C therefore creates the combined-tree library links and binutils links that the Makefile's defaults expect (`forth-bootstrap/chain/gcc-direct/stage-c.sh:195`). Its target archiver must handle the GNU assembler's objects. The target-library request and recorded products are explicit (`forth-bootstrap/chain/gcc-direct/stage-c.sh:217`):

```sh
  (target_env; cd "$gcc_build" && run "$out/libgcc.log" make -j "$jobs" $OVERRIDES stmp-multilib)
  for name in libgcc.a libgcov.a crtbegin.o crtend.o crtbeginS.o crtendS.o crtbeginT.o; do
    result $name "$(sha "$gcc_build/$name")"
  done
}
```

Fixincludes is disabled and `gsyslimits.h` supplies `syslimits.h`; musl's headers do not need rewriting (`forth-bootstrap/chain/gcc-direct/stage-c.sh:189`). The install step then installs GCC before musl uses it (`forth-bootstrap/chain/gcc-direct/stage-c.sh:223`).

Musl's own configure and Makefile build the target C library with the installed GCC, then place it in the sysroot (`forth-bootstrap/chain/gcc-direct/stage-c.sh:231`):

```sh
step_musl() {
  local name
  mkdir -p "$work/musl-build"
  (target_env
   unset CPP CXX CXXCPP CC_FOR_BUILD AS LD NM
   CC=$gcc CFLAGS= CPPFLAGS= LDFLAGS= AR=$toolchain/ar RANLIB=$toolchain/ranlib
   export CC CFLAGS CPPFLAGS LDFLAGS AR RANLIB
   cd "$work/musl-build"
   run "$out/musl.log" "$BASH" "$musl_source/configure" --target=x86_64 --host=x86_64 \
     --disable-shared --prefix=/usr --syslibdir=/lib
   run "$out/musl.log" make -j "$jobs" CROSS_COMPILE= "AR=$AR" "RANLIB=$RANLIB"
   run "$out/musl.log" make CROSS_COMPILE= "AR=$AR" "RANLIB=$RANLIB" "DESTDIR=$sysroot" install)
  for name in libc.a crt1.o crti.o crtn.o; do result $name "$(sha "$sysroot/usr/lib/$name")"; done
}
```

The compiler executable uses the builder's runtime; the programs it emits use the target runtime selected through the sysroot. That distinction breaks the apparent cycle: headers can be installed before libc is compiled.

Stage C's final check compiles and statically links `stage-c-hello.c` with the installed GCC, runs it, compares stdout with its expected file, and requires `nm` to find libgcc's `__divti3` (`forth-bootstrap/chain/gcc-direct/stage-c.sh:246`). Those checks exercise the output path across GCC, binutils, libgcc, and musl.

## Rebuild across the compiler boundary

Stage D uses the completed Stage C toolchain and sysroot. Each generation starts from a fresh C-only source tree. It extends GCC's parser-generator allocation exemption to oyacc's `YYBYACC` marker and applies the collect2 patch (`forth-bootstrap/chain/gcc-direct/stage-d.sh:72`).

The build routine puts the same binutils first in `PATH`, so configure's assembler probes see the same tools. It configures libiberty, libcpp, and GCC separately, using the chosen compiler and a common prefix (`forth-bootstrap/chain/gcc-direct/stage-d.sh:99`):

```sh
  (PATH=$tools:$PATH
   CC=$compiler CPP="$compiler -E" CFLAGS=-O2 LDFLAGS=-static AR=$tools/ar RANLIB=$tools/ranlib
   BISON=$oyacc YACC=$oyacc FLEX=$flex LEX=$flex CONFIG_SHELL=$BASH
   export PATH CC CPP CFLAGS LDFLAGS AR RANLIB BISON YACC FLEX LEX CONFIG_SHELL
   for component in libiberty libcpp gcc; do
     mkdir -p "$source/build/$component"
     (cd "$source/build/$component" && run "$log" "$BASH" ../../$component/configure "--prefix=$prefix" \
        "--build=$TRIPLE" "--host=$TRIPLE" "--target=$TRIPLE" --disable-shared --disable-nls \
        --disable-multilib --enable-languages=c "--with-sysroot=$sysroot" "--with-as=$tools/as" \
        "--with-ld=$tools/ld" --program-transform-name=)
   done
```

The source path, build path, and configured prefix stay the same between generations; otherwise embedded paths could create differences unrelated to code generation (`forth-bootstrap/chain/gcc-direct/stage-d.sh:20`). `DESTDIR` relocates the later installations without changing that configured prefix (`forth-bootstrap/chain/gcc-direct/stage-d.sh:119`).

The compiler ancestry is the reason for the repeated builds. Stage 2 is built by the seed-cc-built Stage C GCC. Stage 3 is built by Stage 2, and Stage 4 by Stage 3. Comparing only Stage C with Stage 2 would compare executables produced by different compiler implementations. The later pair tests reproduction by GCC-built GCC; the earlier pair tests whether that stable result already appeared at the first GCC-produced generation (`forth-bootstrap/chain/gcc-direct/stage-d.sh:169`):

```sh
: > "$work/steps.txt"
build stage2 "$stage_c/gcc/install/bin/gcc"
build stage3 "$prefix/bin/gcc" "$work/stage3"
stage3=$work/stage3$prefix
build stage4 "$stage3/bin/gcc" "$work/stage4"
stage4=$work/stage4$prefix

passed=yes
fixed=$(compare "$stage3" "$stage4" stage3-vs-stage4) || passed=
second=$(compare "$prefix" "$stage3" stage2-vs-stage3) || passed=
```

Here a **fixed point** means agreement of the installed results across both comparisons. It does not prove every accepted C program correct. A reproducible compiler can reproduce its own mistakes.

## Compare installations, not build debris

The shared `files` helper enumerates regular files relative to an installation root. It follows symlinks to files, but does not descend through symlinks to directories (`forth-bootstrap/chain/gcc-direct/chain-lib.sh:93`):

```sh
files() {
  (cd "$1" && files_walk .) | sed 's|^\./||'
}
files_walk() {
  local entry
  for entry in "$1"/* "$1"/.[!.]* "$1"/..?*; do
    if [ -d "$entry" ] && [ ! -L "$entry" ]; then
      files_walk "$entry"
    elif [ -f "$entry" ]; then
      echo "$entry"
    fi
  done
}
```

Thus the comparison covers all installed regular files selected by this traversal, including installed tools, libraries, headers, and support files. It does not compare the entire build tree, directory metadata, or symlink text.

Stage D sorts those relative paths and compares each common file. Ordinary files must match byte for byte. An archive that differs as a whole receives a member comparison instead (`forth-bootstrap/chain/gcc-direct/stage-d.sh:147`):

```sh
compare() {
  local a=$1 b=$2 label=$3 name differ=0 total
  files "$a" | sort > "$work/$label.first"
  files "$b" | sort > "$work/$label.second"
  total=$(wc -l < "$work/$label.first" | tr -d ' ')
  : > "$work/$label.differ"
  for name in $(comm -12 "$work/$label.first" "$work/$label.second"); do
    cmp -s "$a/$name" "$b/$name" && continue
    case $name in *.a) same_archive "$a/$name" "$b/$name" && continue ;; esac
    echo "$name" >> "$work/$label.differ"
  done
```

The script also reports paths present in only one tree. Its success condition requires identical path lists as well as no differing contents (`forth-bootstrap/chain/gcc-direct/stage-d.sh:158`). A missing installed file cannot disappear from the verdict merely because the common files match.

Archive member timestamps can vary without changing the objects the linker reads. The fallback therefore compares member names in order, then each member's bytes (`forth-bootstrap/chain/gcc-direct/stage-d.sh:132`):

```sh
same_archive() {
  local member
  "$tools/ar" t "$1" > "$work/cmp.a.list" && "$tools/ar" t "$2" > "$work/cmp.b.list" || return 1
  cmp -s "$work/cmp.a.list" "$work/cmp.b.list" || return 1
  for member in $(cat "$work/cmp.a.list"); do
    "$tools/ar" p "$1" "$member" > "$work/cmp.a.member"
    "$tools/ar" p "$2" "$member" > "$work/cmp.b.member"
    cmp -s "$work/cmp.a.member" "$work/cmp.b.member" || return 1
  done
}
```

This is narrower than raw archive equality and stronger than comparing an unordered set of objects. A changed member order fails too. The report prints its fixed-point verdict only when both installation comparisons pass (`forth-bootstrap/chain/gcc-direct/stage-d.sh:180`).

## Build the late tools with the stable compiler

The demonstrated late-tools run belongs to K1. Its full-route script checks the Stage D verdict before invoking `late-tools.sh` (`forth-bootstrap/kernel/k1/direct-full.sh:28`). The recipe used by `kernel/k1/run-chain.sh --direct-linux` executes that script under K1 (`forth-bootstrap/kernel/k1/direct-linux.recipe:1`). Chapters 54 and 55 build that environment.

Late tools use the Stage D `prefix` compiler with Stage C's binutils and musl. Plumbing programs stay first in the search path; newly installed programs fill capabilities absent from the plumbing set (`forth-bootstrap/chain/gcc-direct/late-tools.sh:45`):

```sh
P=$out/usr
TOOLS=$chain/stage-c/toolchain
CC=$chain/stage-d/prefix/bin/gcc
require_tool bash "$BIN/bash"
require_tool gcc "$CC"
require_tool as "$TOOLS/as"

PATH=$BIN:$TOOLS:$P/bin
```

Configure always runs under the plumbing bash. When `/bin/sh` is that bash, as it is under K1, the script names it `/bin/sh`, so installed scripts such as `zgrep` start with `#!/bin/sh` rather than a path into `build-out/plumbing` (`forth-bootstrap/chain/gcc-direct/late-tools.sh:313`).

Building a new make or bash does not immediately replace the tools interpreting this build. The initial bash and make continue to run the package builds, with static linking and the fixed-point compiler selected in the environment (`forth-bootstrap/chain/gcc-direct/late-tools.sh:62`).

The package sequence is recorded directly in the recipe:

| Inputs, in recipe order | Result | Source |
|---|---|---|
| make 4.4.1, sed 4.9, grep 3.11, gzip 1.13, xz 5.6.3 | build, text, and decompression tools | `forth-bootstrap/chain/gcc-direct/late-tools.sh:169` |
| bzip2 1.0.8 | compressor built with its own Makefile | `forth-bootstrap/chain/gcc-direct/late-tools.sh:174` |
| tar 1.35, gawk 5.3.1, patch 2.7.6, coreutils 9.5, bash 5.2.37 | archive, text, file, and shell tools | `forth-bootstrap/chain/gcc-direct/late-tools.sh:187` |
| diffutils 3.10, findutils 4.10.0, m4 1.4.19, bison 3.8.2, flex 2.6.4, bc 1.07.1 | comparison, search, macro, parser, scanner, and calculation tools | `forth-bootstrap/chain/gcc-direct/late-tools.sh:192` |

Each GNU package runs its own configure, followed by make and install; bzip2 is the explicit make-only exception. Package-specific configure arguments disable optional dependencies and choose supported features (`forth-bootstrap/chain/gcc-direct/late-tools.sh:116`). The common build path records each command and its output (`forth-bootstrap/chain/gcc-direct/late-tools.sh:151`):

```sh
  t0=$(date +%s)
  cd "$out/src/$name"
  lrun "$log" "$CONFIG_SHELL" ./configure "--build=$BUILD" "--prefix=$P" --disable-nls \
    --disable-dependency-tracking $(configure_args "$name")
  t1=$(date +%s)
  if [ -n "$mk" ]; then
    lrun "$log" make -j "$jobs" HELP2MAN=true MAKEINFO=true "$mk"
    lrun "$log" make install HELP2MAN=true MAKEINFO=true "$mk"
  else
    lrun "$log" make -j "$jobs" HELP2MAN=true MAKEINFO=true
    lrun "$log" make install HELP2MAN=true MAKEINFO=true
  fi
```

The report is written to `build-out/late/report.txt` by the default output path and report writer (`forth-bootstrap/chain/gcc-direct/late-tools.sh:199`). K1's finish script includes that report and the late-tools logs in the archive written to the output disk (`forth-bootstrap/chain/ladder/finish.sh:7`). A host-side late-tools checkpoint remains open.

## Try it

Run from the forth-bootstrap checkout root. Fetching verifies the pinned archives before use (`forth-bootstrap/tools/fetch-archives.py:2`). The full checkpoint requires those archives, bwrap, strace, and working user namespaces; the launcher executes the plumbing controller inside its prepared root (`forth-bootstrap/chain/plumbing-root.sh:60`). Allow a sustained build: the recorded host run took 18 minutes (`forth-bootstrap/README.md:162`). Chapter 53 audits that root and its execution traces.

<!-- check-tryit: the scratch checkout lacks chain/, pinned archives, and build-out/; this sustained build also requires bwrap, strace, and user namespaces. -->
<!-- tryit: skip -->
```sh
python3 tools/fetch-archives.py
sh chain/plumbing-root.sh
```

The resulting report is `build-out/plumbing-root/build-out/chain/stage-d/report.txt`, following the launcher's default root and the controller's default output directory (`forth-bootstrap/chain/plumbing-root.sh:31`). Its opening lines from a recorded run:

```text
# Stage D: fixed point reached

Stage 3 vs stage 4: 54 files, 0 differ.
Stage 2 vs stage 3: 54 files, 0 differ.
```

The recorded run likewise reports stage 2 = 3 = 4, with 54 files in each installation and no differences (`forth-bootstrap/README.md:162`). These counts describe that run, not a fixed size every configuration must produce.

## Exercise

**Trace (easy).** Follow `compare` and `same_archive` in Stage D. Predict the verdict for each change: an installed header disappears, an archive timestamp changes, an archive member changes position, or a member's object bytes change. Identify the condition that accepts or rejects each case.
