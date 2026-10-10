# Chapter 51 — Owning the tools

A build recipe needs programs that create directories, unpack sources, generate parsers, and interpret shell commands. The plumbing recipes turn C sources and fixed configuration answers into the tools that will run GCC's build.

## Start with a recipe runner

The construction has this shape: seed-cc → kaem → file utilities and make → text and archive tools → parser generators → bash → configure. The driver and archiver are already built (Chapter 50). The stage controller orders the recipes before handing control to the new bash (`forth-bootstrap/chain/plumbing/chain.kaem:13`):

```sh
./build-out/plumbing/bin/kaem --verbose --strict --file chain/plumbing/stage1.kaem
./build-out/plumbing/bin/kaem --verbose --strict --file chain/plumbing/stage2.kaem
./build-out/plumbing/bin/kaem --verbose --strict --file chain/plumbing/lexers.kaem
./build-out/plumbing/bin/kaem --verbose --strict --file chain/plumbing/bash.kaem
./build-out/plumbing/bin/bash chain/gcc-direct/chain.sh -j 6
```

These are source excerpts, not commands to paste individually. The recipes depend on pinned archives and earlier stages; the full run is described below. The GCC construction after the handoff belongs to Chapter 52.

Kaem occupies the gap before a conventional shell exists. Its C sources can be compiled by seed-cc, so the first recipe runner does not depend on bash. The sealed launcher supplies the source list directly (`forth-bootstrap/chain/plumbing-root.sh:72`):

```sh
enter 3 /build-out/seed-cc/seed-cc -static vendor/mescc-tools/Kaem/kaem.c \
  vendor/mescc-tools/Kaem/variable.c vendor/mescc-tools/Kaem/kaem_globals.c \
  vendor/stage0-posix/mescc-tools-extra/M2libc/bootstrappable.c \
  -o build-out/plumbing/bin/kaem > "$T/entry3.log" 2>&1
status=0
```

`enter` executes the compiler inside the prepared root through bwrap under strace, with the environment cleared and `PATH` set to `/bin` (`forth-bootstrap/chain/plumbing-root.sh:60`). The short checkpoint at the end uses the same compiler arguments in the checkout, with a temporary output path. It tests construction and execution of kaem; it does not establish the sealed-run claim.

Directory creation must precede installing tools into the new directory. The recipe writes a temporary `mkdir` into the existing build directory, then uses it to make the destination (`forth-bootstrap/chain/plumbing/stage1.kaem:16`):

```sh
CC=./build-out/seed-cc/seed-cc
X=vendor/stage0-posix/mescc-tools-extra
B=build-out/plumbing
BIN=./build-out/plumbing/bin

# mkdir first, into a directory that already exists.
${CC} -static ${X}/mkdir.c ${X}/M2libc/bootstrappable.c -o build-out/plumbing-mkdir
./build-out/plumbing-mkdir -p ${BIN} ${B}/src

${CC} -static ${X}/mkdir.c ${X}/M2libc/bootstrappable.c -o ${BIN}/mkdir
```

The rest of that recipe compiles `sha256sum`, `unbz2`, `ungz`, `untar`, `cp`, `chmod`, and `rm`, each with `bootstrappable.c` (`forth-bootstrap/chain/plumbing/stage1.kaem:26`). These small utilities supply the operations needed to unpack and prepare larger packages.

## Build make before using Makefiles

A Makefile cannot build its own interpreter. The initial make construction therefore uses an explicit sequence of compiler commands. Archive verification precedes extraction, and the supplied header replaces configure (`forth-bootstrap/chain/plumbing/stage1.kaem:34`):

```sh
# Every input is checked before it is used.
${BIN}/sha256sum --check chain/plumbing/SOURCES

# GNU make 3.82: unpack, configure by header, compile, link.
cd ${B}/src
../bin/unbz2 --file ../../plumbing-inputs/make-3.82.tar.bz2 --output make-3.82.tar
../bin/untar --file make-3.82.tar
../bin/rm make-3.82.tar
cd make-3.82
../../bin/cp ../../../../chain/plumbing/make-3.82/config.h config.h

M=../../../seed-cc/seed-cc
${M} -c -DHAVE_CONFIG_H -I. -Iglob ar.c
${M} -c -DHAVE_CONFIG_H -I. -Iglob arscan.c
${M} -c -DHAVE_CONFIG_H -I. -Iglob commands.c
```

The subsequent commands compile the remaining objects and link `../../bin/make`, then return to the checkout root to print its version (`forth-bootstrap/chain/plumbing/stage1.kaem:49`). This builds make 3.82, the version named by the archive above.

A **fixed configuration** records the capabilities the package may use without executing a probe script. The make header selects waiting and jobserver support so parallel and recursive builds retain their intended behaviour (`forth-bootstrap/chain/plumbing/make-3.82/config.h:17`):

```c
/* waitpid and a jobserver pipe, as configure finds them on Linux.  Without
   HAVE_WAITPID, make falls back to counting SIGCHLDs and in practice runs
   one job at a time even with -j; without MAKE_JOBSERVER, recursive makes
   would ignore -j.  */
#define HAVE_SYS_WAIT_H 1
#define HAVE_WAITPID 1
#define MAKE_JOBSERVER 1
```

A configuration answer affects control flow in the package itself. Leaving these features disabled would select fallback scheduling, even though the runtime provides the needed operations. Fixed configuration must describe that runtime, not the machine on which a reader happens to inspect the source.

## Give make commands it can execute directly

The next stage repeats unpack → configure by header → make → install. The table follows the recipe's execution order.

| Input | Installed result | Recipe source |
|---|---|---|
| sed 4.0.9 | `sed` | `forth-bootstrap/chain/plumbing/stage2.kaem:30` |
| gzip 1.2.4 | `gzip`, `gunzip`, `zcat` | `forth-bootstrap/chain/plumbing/stage2.kaem:41` |
| patch 2.5.9 | `patch` | `forth-bootstrap/chain/plumbing/stage2.kaem:55` |
| diffutils 2.7 | `cmp`, `diff`, `diff3`, `sdiff` | `forth-bootstrap/chain/plumbing/stage2.kaem:66` |
| grep 2.4 | `grep`, `egrep`, `fgrep` | `forth-bootstrap/chain/plumbing/stage2.kaem:83` |
| gawk 3.0.4 | `gawk`, `awk` | `forth-bootstrap/chain/plumbing/stage2.kaem:98` |
| tar 1.12 | `tar` | `forth-bootstrap/chain/plumbing/stage2.kaem:111` |
| coreutils 5.0 | file and text utilities, including replacements for the initial file tools | `forth-bootstrap/chain/plumbing/stage2.kaem:122` |

The sed portion shows the repeated operation: extraction tools come from the previous stage, while make receives the repository's explicit recipe (`forth-bootstrap/chain/plumbing/stage2.kaem:31`):

```sh
../bin/ungz --file ../../plumbing-inputs/sed-4.0.9.tar.gz --output sed-4.0.9.tar
../bin/untar --file sed-4.0.9.tar
../bin/rm sed-4.0.9.tar
cd sed-4.0.9
../../bin/cp ${P}/sed-4.0.9/config.h config.h
${MK} -j4 -f ${P}/sed-4.0.9/Makefile
../../bin/cp sed/sed ../../bin/sed
../../bin/chmod 755 ../../bin/sed
cd ..
```

Make can execute a plain recipe command directly. Shell metacharacters would force it to invoke a shell that has not been built. The package Makefiles therefore use **direct recipes**: a compile, archive, link, or copy command without shell interpretation. The sed rules show that constraint in their object-to-program path (`forth-bootstrap/chain/plumbing/sed-4.0.9/Makefile:24`):

```make
$(LIB_OBJ) $(SED_OBJ): config.h lib/regex.h

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

lib/libsed.a: $(LIB_OBJ)
	$(AR) cr $@ $(LIB_OBJ)

sed/sed: $(SED_OBJ) lib/libsed.a
	$(CC) -static -o $@ $(SED_OBJ) lib/libsed.a
```

The link follows lazy member selection (Chapter 42). A direct recipe also avoids pipelines and compound commands: separate dependency rules express the work instead.

Quoted path definitions would complicate command execution. Fixed configuration puts such strings in C headers, where quoting has C semantics. Diffutils records the program paths it will use there (`forth-bootstrap/chain/plumbing/diffutils-2.7/config.h:1`):

```c
/* config.h for GNU diffutils 2.7 built by seed-cc against runtime/gcc-seed.
   No configure script runs.  Each answer below is true for this runtime.
   The program paths Makefile.in passes as quoted -D options are here too,
   so that make runs every compile without a shell; they are the values a
   build with prefix /usr gives, as in live-bootstrap.  */

#define NULL_DEVICE "/dev/null"
#define PR_PROGRAM "/bin/pr"
#define DIFF_PROGRAM "/usr/bin/diff"
#define DEFAULT_EDITOR_PROGRAM "ed"
```

Those paths are part of the package's behaviour. In an ordinary checkout, `/usr/bin/diff` can reach a host program; the README explicitly warns about this (`forth-bootstrap/chain/plumbing/README.md:102`). In the sealed root, `/bin` and `/usr/bin` point at the plumbing output directory (`forth-bootstrap/chain/plumbing-root.sh:54`). Reading a Makefile is therefore insufficient evidence that a later invocation stays inside the chain: the filesystem bindings matter too.

Gzip is the fixed-configuration exception: its unquoted capability options live in its Makefile rather than a `config.h` (`forth-bootstrap/chain/plumbing/gzip-1.2.4/Makefile:1`). The other packages follow the header approach. Their recipes make undeclared function calls errors; the headers supply missing declarations through real runtime headers, as explained in `forth-bootstrap/chain/plumbing/README.md:79`.

Patch precedes coreutils because coreutils source preparation uses the newly built patch. The recipe applies `canonicalize-realloc.diff` before compilation, then uses the new `ginstall` to replace the initial `cp`, `rm`, `mkdir`, and `chmod` (`forth-bootstrap/chain/plumbing/stage2.kaem:122`). The README explains the source fix: a pointer into a buffer must survive a realloc that moves the buffer (`forth-bootstrap/chain/plumbing/README.md:89`). This is a source correction, separate from fixed configuration.

## Generate the generators' inputs

The parser-generator recipe builds oyacc 6.6, then Heirloom lex 070527, then flex 2.5.11 (`forth-bootstrap/chain/plumbing/README.md:133`). A parser generator translates a grammar into C parser code; a scanner generator translates token rules into C scanner code. The ordering solves a dependency problem: lex needs a parser, and flex needs both a parser and a scanner before flex itself can run.

Oyacc is compiled from its object list. Heirloom's parser is then generated by that oyacc; its scanner support library is archived by seed-ar. Both actions remain direct recipes (`forth-bootstrap/chain/plumbing/heirloom-lex-070527/Makefile:7`):

```make
all: $(BIN)/lex libl.a
parser.c: parser.y
	$(BIN)/oyacc parser.y
	$(BIN)/cp y.tab.c parser.c
$(BIN)/lex: $(OBJECTS)
	$(CC) -static -o $@ $(OBJECTS)
libl.a: $(LIBOBJECTS)
	$(AR) rcs $@ $(LIBOBJECTS)
main-unit.o: main-unit.c main.c config.h
```

Heirloom's configuration header is generated by `lexer-prepare lexconfig`, rather than copied from a package directory (`forth-bootstrap/chain/plumbing/lexers.kaem:29`). It records where the lex form files remain in the unpacked source tree; those files must remain available when using lex (`forth-bootstrap/chain/plumbing/README.md:157`).

Flex's preparation removes shipped generated C so the generators just built must supply it. The seed-cc-built `lexer-prepare` also applies the pinned patches and constructs the skeleton (`forth-bootstrap/chain/plumbing/lexers.kaem:35`):

```sh
cd ../../${F}
../../bin/lexer-prepare patch ${R}/patches/scan_l.patch
../../bin/lexer-prepare patch ${R}/patches/yyin.patch
../../bin/cp ${R}/files/scan.lex.l scan.lex.l
# No shipped generated C can enter the bootstrap.
../../bin/lexer-prepare ungenerated
../../bin/lexer-prepare skeleton flex.skl skel.c
../../bin/cp ../../../../chain/plumbing/flex-2.5.11/config.h config.h
../../bin/cp ../../../../chain/plumbing/flex-2.5.11/Makefile Makefile
cd ../../../..
${BIN}/sha256sum --check chain/plumbing/lexers.PREPARED
```

The prepared-input hash check occurs before make, and the generated-output hash check follows it (`forth-bootstrap/chain/plumbing/lexers.kaem:45`). These checks cover different boundaries: the source transformations and the generated artifacts.

The Makefile first uses oyacc on `parse.y` (`forth-bootstrap/chain/plumbing/flex-2.5.11/Makefile:10`). For the scanner, Heirloom lex processes a temporary scanner description. That scanner allows `flex-tmp` to be built, which processes the original patched `scan.l`; the final flex links the resulting scanner (`forth-bootstrap/chain/plumbing/flex-2.5.11/Makefile:15`):

```make
scan-ascii.l: scan.lex.l
	$(PREP) ascii scan.lex.l scan-ascii.l
heirloom-scan.c: scan-ascii.l parse.h
	$(BIN)/lex -Y../heirloom-devtools-070527/lex scan-ascii.l
	$(BIN)/cp lex.yy.c heirloom-scan.c
scan-tmp.c: heirloom-scan.c
	$(PREP) scanner heirloom-scan.c scan-tmp.c
flex-tmp: $(OBJECTS) $(LIBL)
	$(CC) -static -o $@ $(OBJECTS) $(LIBL)
scan.c: flex-tmp scan.l
	./flex-tmp scan.l
	$(BIN)/cp lex.yy.c scan.c
$(BIN)/flex: $(FINAL) $(LIBL)
	$(CC) -static -o $@ $(FINAL) $(LIBL)
```

The temporary scanner bootstrap breaks the dependency cycle. It need only let the intermediate flex process its own scanner input; the final executable uses `scan.o` instead of `scan-tmp.o`.

This regeneration requirement is local to the generator construction. It does not mean every earlier package regenerates every parser: gawk's recipe explicitly uses the shipped `awktab.c` (`forth-bootstrap/chain/plumbing/gawk-3.0.4/Makefile:1`).

## Build the shell last

Bash 2.05b can be built once make, patch, and oyacc exist. Its recipe copies fixed configuration and explicit Makefiles, deletes the shipped parser, and applies the reviewed patch (`forth-bootstrap/chain/plumbing/bash.kaem:24`):

```sh
../../bin/cp ${R}/config.h config.h
../../bin/cp ${R}/Makefile Makefile
../../bin/cp ${R}/common.mk common.mk
../../bin/cp ${R}/builtins.mk builtins/Makefile
../../bin/cp ${R}/empty.h include/version.h
../../bin/cp ${R}/empty.h include/pipesize.h
../../bin/rm y.tab.c y.tab.h parser-built
../../bin/patch -p1 -i ${R}/missing-defines.patch
```

The shell's builtins are generated and archived before the final build. The parser generator is selected explicitly, and the same executable is installed under both shell names (`forth-bootstrap/chain/plumbing/bash.kaem:33`):

```sh
../../bin/make prefix=/usr mkbuiltins
cd builtins
../../../bin/make prefix=/usr libbuiltins.a
cd ..
../../bin/make prefix=/usr YACC=../../bin/oyacc
../../bin/cp bash ../../bin/bash
../../bin/cp bash ../../bin/sh

cd ../../../..
./build-out/plumbing/bin/bash --version
```

The Makefile's `y.tab.c: parse.y` rule invokes `$(YACC) -d`; it does not accept the deleted parser as an input (`forth-bootstrap/chain/plumbing/bash-2.05b/Makefile:87`). The common settings name seed-cc and seed-ar, so generating bash's helper programs does not introduce another compiler (`forth-bootstrap/chain/plumbing/bash-2.05b/common.mk:6`).

The initial shell is deliberately bounded. The shared chain scripts are written for this bash without arrays, brace expansion, pipefail, or `+=` (`forth-bootstrap/chain/gcc-direct/chain-lib.sh:3`). Later replacements belong to Chapter 52.

## Let configure discover capabilities

Fixed configuration made a shell possible. With that shell available, upstream configure scripts can perform their own probes. The runner first removes cached answer variables so the caller's environment cannot decide the results (`forth-bootstrap/chain/gcc-direct/configure.sh:85`):

```sh
# No cached configure answer may leak in from the caller's environment.
for name in $(env | sed -n 's/^\([A-Za-z_][A-Za-z_0-9]*\)=.*/\1/p'); do
  case $name in
    *_cv_*|ac_cv*|gcc_cv*|gt_cv*) unset "$name" ;;
  esac
done
```

Configure must use the chain's compiler and shell even when it searches for familiar tool names. The runner prepends a guard directory and selects the compiler through environment variables (`forth-bootstrap/chain/gcc-direct/configure.sh:92`):

```sh
G=$work/guard
PATH=$G:$PATH
CONFIG_SITE=/dev/null CONFIG_SHELL=$BASH
CC=$SEED_CC CPP="$SEED_CC -E" CC_FOR_BUILD=$SEED_CC
CXX=$G/c++ CXXCPP=$G/cpp
CFLAGS= CPPFLAGS= LDFLAGS= LIBS= CFLAGS_FOR_BUILD= CXXFLAGS=
AS=$G/as LD=$G/ld AR=$G/ar RANLIB=$G/ranlib NM=$G/nm
AS_FOR_TARGET=$G/as LD_FOR_TARGET=$G/ld
export PATH CONFIG_SITE CONFIG_SHELL CC CPP CC_FOR_BUILD CXX CXXCPP CFLAGS CPPFLAGS LDFLAGS LIBS
export CFLAGS_FOR_BUILD CXXFLAGS AS LD AR RANLIB NM AS_FOR_TARGET LD_FOR_TARGET
if [ $package = binutils ]; then CXX=no; fi
if [ -n "$forth_ar" ]; then AR=$SEED_AR RANLIB="$SEED_AR s"; fi
```

The guards log attempts to execute target tools and fail, rather than falling through to a host installation (`forth-bootstrap/chain/gcc-direct/configure.sh:76`). `--forth-ar` deliberately replaces the archive guards with seed-ar. The `--with-binutils` option later permits the chain's built target tools (`forth-bootstrap/chain/gcc-direct/configure.sh:104`); their construction belongs to Chapter 52.

The actual configure invocation names bash explicitly, and captures its exit status and log (`forth-bootstrap/chain/gcc-direct/configure.sh:141`):

```sh
if [ -n "$sysroot" ]; then set -- "$@" --with-sysroot=$sysroot; fi
echo "$BASH $configure $*" > "$work/configure-command.txt"
echo "$work"
status=0
(cd "$build" && "$BASH" "$configure" "$@") > "$work/configure.log" 2>&1 || status=$?
attempts=0
if [ -f "$work/host-tool-attempts.log" ]; then attempts=$(wc -l < "$work/host-tool-attempts.log"); fi
```

`CONFIG_SHELL` directs subsidiary shell invocations; `"$BASH"` chooses the interpreter for this invocation itself. The runner records the environment for later make runs (`forth-bootstrap/chain/gcc-direct/configure.sh:125`). It labels its report provisional, requiring a probe and generated-header audit (`forth-bootstrap/chain/gcc-direct/configure.sh:148`). A successful configure exit is not proof that every selected capability is correct.

## The full plumbing run

From the forth-bootstrap checkout root, the full route is `sh chain/plumbing-root.sh`, after caching pinned inputs with `python3 tools/fetch-archives.py`. The fetcher's manifest and hash checks are described in `forth-bootstrap/tools/fetch-archives.py:2`. This is not an automatic Try it: it requires pinned archives, bwrap and strace, and continues through the long GCC build. The launcher checks those tools and stages the archives (`forth-bootstrap/chain/plumbing-root.sh:34`). It executes the plumbing controller inside the sealed root (`forth-bootstrap/chain/plumbing-root.sh:77`), which continues beyond bash through the GCC stages.

It is a long run; the project's recorded runs are in `forth-bootstrap/README.md:237`. Its plumbing outputs lie under `build-out/plumbing-root/build-out/plumbing/bin/`, following the launcher's default root and the recipes' output paths (`forth-bootstrap/chain/plumbing-root.sh:31`). Chapter 53 audits the sealed host run.

## Try it

Run from the forth-bootstrap checkout root, with the previously built seed-cc and the seed already available. This compiles kaem with the source list used by the launcher, changing only its output destination (`forth-bootstrap/chain/plumbing-root.sh:72`). Then kaem expands a variable and executes a tiny script.

It needs `build-out/seed-cc/seed-cc` from Chapter 50 and leaves its temporary directory for inspection. The surrounding shell supplies `mktemp` and `printf`, so this is not a sealed execution audit.

<!-- check-tryit: its scratch checkout has neither build-out/seed-cc nor vendor/; run directly. -->
<!-- tryit: skip -->
```sh
(
work=$(mktemp -d) || exit
./build-out/seed-cc/seed-cc -static vendor/mescc-tools/Kaem/kaem.c \
  vendor/mescc-tools/Kaem/variable.c vendor/mescc-tools/Kaem/kaem_globals.c \
  vendor/stage0-posix/mescc-tools-extra/M2libc/bootstrappable.c \
  -o "$work/kaem" || exit
printf '%s\n' 'MESSAGE=hello-from-kaem' 'echo ${MESSAGE}' > "$work/tiny.kaem"
"$work/kaem" --strict --file "$work/tiny.kaem"
)
```

Observed output:

```text
hello-from-kaem
```

## Exercise

**Trace (easy).** Follow the scanner targets in the flex Makefile. Which target first executes a flex built by this recipe? Explain why removing Heirloom lex would leave that target unreachable, even though seed-cc can compile all the C objects.

