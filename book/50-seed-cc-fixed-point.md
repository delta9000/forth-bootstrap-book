# Chapter 50 — Building seed-cc and seed-ar

The next build recipe wants to say `seed-cc -c source.c` and receive an
object file. Part 3 gave us every operation behind that command, but its
checkpoints still assembled compiler input streams by hand. A **driver**
can do that bookkeeping for every source file: interpret the options,
arrange the input stream, run the compiler, and publish the result.

Our driver is a C program. To build its first executable, we need those
same operations before the driver exists. A Forth controller supplies
them once; the resulting `seed-cc` can then build the next copy of itself
and its companion archiver, `seed-ar`. Comparing the copies checks whether
the two ways of arranging the build agree. The compiler underneath both
remains the Forth implementation running inside `seed-forth`.

## From a filename to an object

Follow the proposed command `seed-cc -c source.c -o source.o` by hand.
The driver reads the C file and gathers the compiler layers. It places a
small Forth driver after those layers and the C text after that driver.
The final Forth call starts C parsing, just as in the earlier checkpoints.
The child seed writes an object in the private workspace; after successful
compilation, `seed-cc` publishes the requested `source.o`
(`forth-bootstrap/cc/driver/seed-cc.c:577`,
`forth-bootstrap/cc/driver/seed-cc.c:659`).

The command-line modes choose how far that work goes. `parse` defines
these choices (`forth-bootstrap/cc/driver/seed-cc.c:169`):

| Input | Result |
|---|---|
| no mode flag | Compile C inputs and link a program |
| `-c` | Publish objects without linking |
| `-E` | Publish preprocessed text |
| `-o PATH` | Select the output destination |
| `-I PATH` | Add an include search directory |
| `-D NAME=VALUE`, `-U NAME` | Supply preprocessor directives |
| `-L PATH`, `-l NAME` | Search for library inputs while linking |
| `-nostdinc`, `-nostdlib` | Omit the default include directory or runtime |

Conflicting modes and unsupported options fail. `-static`, `-O0` and `-g0` describe the output
already produced; they do not enable additional passes. This is enough of
a command interface for the recipes in Chapter 51. First we must construct
the program that implements it.

## Build a driver without running a driver

The Forth controller starts with the existing seed and the source files.
It compiles the runtime and tool C sources, emits the Forth runtime
objects, archives the runtime, then links each tool. Every compilation
and link starts a child `seed-forth`; the new tool executables are needed
only after this construction finishes.

Directory traversal supplies the inputs rather than a handwritten list. `layer?` accepts numbered compiler layers, excluding `120-cc-main.fth` and `140-cc-link.fth`; `source?` accepts runtime C sources except `math.c`. The controller sorts both lists by filename before using them. The linker has its own smaller layer list (`forth-bootstrap/cc/driver/seed-cc-start.fth:188–199`, `forth-bootstrap/cc/driver/seed-cc-start.fth:220–247`, `forth-bootstrap/cc/driver/seed-cc-start.fth:272–279`).

Each translation unit gets its own input stream and a fresh `seed-forth`
process. `run-seed` executes the seed again, which resets compiler globals
and arena state; merely changing the input file would not provide that
isolation (`forth-bootstrap/cc/driver/seed-cc-start.fth:281`).
`compile-unit` assembles the stream and starts that process
(`forth-bootstrap/cc/driver/seed-cc-start.fth:309`):
```forth
: compile-unit
 unit-driver ! dup unit-name ! source-path
 new-input compiler-layers unit-driver @ append-file srcbuf append-file end-input
 run-seed
 unit-name @ object-path
 unit-object pathbuf rename if, [lit] 115 die then, ;
```

`compiler-layers` appends the library and the sorted compiler layers.
The fixed driver comes next, followed by one C source. The child seed
writes `unit.o`; the controller renames it before compiling another unit.
Runtime C uses `runtime-unit.fth`, while the tool sources use
`tools-unit.fth`.

The tool driver selects object compilation (Chapter 41) and provides the runtime include directory; its final call consumes the C text that follows it (`forth-bootstrap/cc/driver/seed-cc-boot/tools-unit.fth:5`):
```forth
cc-sysv-object-enable
[lit] 22020096 cc-arena-map
cc-io-direct-workspace cc-prep-direct-workspace
cc-om-direct-workspace cc-label-direct-workspace
cc-obj-direct-workspace cc-gfixup-direct-workspace
create driver-output s, build-out/seed-cc/boot/unit.o [lit] 0 c,
create driver-source s, cc/driver/unit.c [lit] 0 c,
driver-source [lit] 16 cc-prep-source-name
create driver-inc-0 s, chain/runtime/gcc-seed/include [lit] 0 c,
driver-inc-0 [lit] 30 cc-prep-add-include
: driver-main cc-load-stdin cc-preprocess cc-out-init cc-globals-init
cc-sysv-object-program driver-output cc-obj-write bye ;
driver-main
```

The child reads that assembled input through standard input, so no shell or compiler executable must interpret the build recipe (`forth-bootstrap/cc/driver/seed-cc-start.fth:281`):
```forth
: run-seed
 fork dup 0< if, [lit] 109 die then,
 dup 0= if,
   drop
   input-path [lit] 0 [lit] 0 open dup 0< if, [lit] 110 die then,
   dup [lit] 0 dup2 0< if, [lit] 111 die then,
   close drop
   seed-path seed-argv exec drop [lit] 112 die
 then,
 pid !
 pid @ status wait4 pid @ <> if, [lit] 113 die then,
 status @ if, [lit] 114 die then, ;
```

The parent waits for the child and stops on a failing status. This is the
whole execution loop behind the first driver: fork, redirect, exec the
seed, and wait. The surrounding shell launches the controller, but the
controller constructs both tools without executing Python or a C driver.

## Put startup before the archive

C runtime objects come first in `libseed.a`, in sorted source order. The Forth-generated members follow as `syscall.o`, `errno.o`, `frame.o`, `sigreturn.o`, `setjmp.o`, and `longjmp.o`. `start.o` is emitted alongside them but kept outside the archive. The controller expresses that order directly (`forth-bootstrap/cc/driver/seed-cc-start.fth:321`):
```forth
: make-archive
 new-input linker-layers archive-head append-file
 [lit] 0 cursor !
 begin, cursor @ source-count @ < while,
   source-table cursor @ [lit] 8 * + @ object-path member-line
   cursor @ 1+ cursor !
 repeat,
 sysrt-list cursor !
 begin, cursor @ @ while,
   cursor @ @ member-path member-line
   cursor @ [lit] 8 + cursor !
 repeat,
 archive-tail append-file end-input run-seed ;
```

`member-line` writes an `arc-add-object` command for the current path. `archive-head.fth` starts the archive; `archive-tail.fth` writes it. These steps load the library, arena, I/O, linker and archive layers, without loading the C parser.

Startup must be added as an ordinary object. Archive extraction responds
to unresolved symbol references (Chapter 42), and no input here asks for
`_start`. `lnk-entry` records that name for the final entry lookup; it does
not create a reference that would extract startup from an archive
(`forth-bootstrap/cc/140-cc-link.fth:161`). The explicit startup object
therefore supplies `_start`, the program object supplies `main`, and the
runtime archive satisfies their unresolved library references
(`forth-bootstrap/cc/driver/seed-cc-boot/link-seed-cc.fth:3`):
```forth
lnk-init
create driver-obj-0 s, build-out/seed-cc/boot/start.o [lit] 0 c,
driver-obj-0 lnk-add-object
create driver-obj-1 s, build-out/seed-cc/boot/seed-cc.o [lit] 0 c,
driver-obj-1 lnk-add-object
create driver-obj-2 s, build-out/seed-cc/boot/libseed.a [lit] 0 c,
driver-obj-2 lnk-add-archive
create driver-entry s, _start
driver-entry [lit] 6 lnk-entry
create driver-output s, build-out/seed-cc/seed-cc [lit] 0 c,
driver-output lnk-link bye
```

`link-seed-ar.fth` uses the same order with `seed-ar.o` and the archiver output path. The construction writes both executables under `build-out/seed-cc/`, with input streams, objects and the archive in `build-out/seed-cc/boot/`.

## Let C assemble the next Forth stream

We now have a runnable `seed-cc`. Its central job is the stream assembly
we followed at the start of the chapter. The C function `forth` joins
captured layer bytes, generated driver text and source bytes in that
order (`forth-bootstrap/cc/driver/seed-cc.c:577`):
```c
/* Run the seed on the named modules, the driver text and SOURCE. */
static void forth(struct names *modules, const struct buf *driver, const char *source, unsigned long nsource)
{
    struct buf program, out, err;
    unsigned long i;
    long status;
    b_init(&program);
    for (i = 0; i < modules->count; i = i + 1) {
        struct buf *m = input_data(modules->items[i]);
        if (i)
            b_chr(&program, '\n');
        b_add(&program, m->data, m->len);
    }
    b_chr(&program, '\n');
    b_add(&program, driver->data, driver->len);
    b_add(&program, source, nsource);
    status = st_run_seed(tc.work, tc.seed, &program, &out, &err);
    b_free(&program);
```

`compile_unit` generates the same kind of setup as the fixed bootstrap driver, adding the requested includes and macro directives. Its ordinary object path ends by invoking the Forth compiler, while preprocessing mode writes the preprocessed buffer instead (`forth-bootstrap/cc/driver/seed-cc.c:659`):
```c
    } else {
        b_str(&d, ": driver-main cc-load-stdin cc-preprocess cc-out-init cc-globals-init\n");
        b_str(&d, "cc-sysv-object-program driver-output cc-obj-write bye ;\n");
    }
    b_str(&d, "driver-main\n");
    forth(&tc.compiler, &d, source, nsource);
    b_free(&d);
}
```

The driver captures its compiler inputs and checks for changes during capture.
It verifies the seed executable against its hex source, then builds a
private workspace containing the captured seed and runtime inputs
(`forth-bootstrap/cc/driver/seed-cc.c:476`). These checks establish which
compiler inputs the command used. Comparing successive builds of `seed-cc` is a
separate step.

## Preserve the link and archive policy

The C driver preserves the bootstrap's eager startup and trailing runtime archive when linking ordinary user inputs (`forth-bootstrap/cc/driver/seed-cc.c:1253`):
```c
        char *program = st_cat3(work, "/", "program");
        if (!o.nostdlib) {
            struct names runtime, ordered;
            runtime_objects(&runtime);
            memset(&ordered, 0, sizeof ordered);
            for (i = 0; i < runtime.count; i = i + 1)
                if (strcmp(st_pname(runtime.items[i]), "start.o") == 0)
                    n_add(&ordered, runtime.items[i]);
            for (i = 0; i < objects.count; i = i + 1)
                n_add(&ordered, objects.items[i]);
            n_add(&ordered, runtime_archive(&runtime, "libseed.a"));
            objects = ordered;
        }
        link_objects(&objects, program);
        memset(&results, 0, sizeof results);
```

`runtime_object_names` keeps sorted C objects before the Forth objects, and `runtime_archive` skips `start.o` (`forth-bootstrap/cc/driver/seed-cc.c:699`, `forth-bootstrap/cc/driver/seed-cc.c:923`). The ordering is shared by construction and later driver use.

`seed-ar` is also an adapter. It accepts archive creation and update flags, replaces matching members by basename, appends new members, or validates an existing index. Forth still writes the archive. The adapter runs the assembled archive commands and publishes only after success (`forth-bootstrap/cc/driver/seed-ar.c:338`):
```c
    if (create)
        b_str(&code, "archive-output arc-write\n");
    b_str(&code, "bye\n");
    status = st_run_seed(work, seed, &code, &out, &err);
    if (out.len)
        st_write_all(2, out.data, out.len);
    if (err.len)
        st_write_all(2, err.data, err.len);
    if (status || out.len)
        st_finish(status > 0 ? (int)status : 1);
    if (create) {
        st_read_file(private_output, &result);
        publish(output, &result, update);
    }
```

## Rebuild the driver with itself

The first construction used fixed Forth drivers. The second can ask the
new C driver to compile the same tool sources. If it changes an include,
compiler stream, runtime order or link, the resulting bytes may expose
the difference. The rebuild check puts the second generation at the same
directory depth so the driver still finds its source tree from its own
path (`forth-bootstrap/tests/cc/seed-cc-rebuild-check.sh:15`):
```sh
./seed-forth < cc/driver/seed-cc-start.fth
G1=build-out/seed-cc
G2=build-out/seed-cc-gen2
rm -rf "$G2"
mkdir -p "$G2"
"$G1/seed-cc" -static cc/driver/seed-cc.c -o "$G2/seed-cc"
"$G1/seed-cc" -static cc/driver/seed-ar.c -o "$G2/seed-ar"
```

Equal bytes show that the two construction paths agree on these driver
and archiver executables. The Forth compiler still performs both builds;
the result is a fixed point of the tools around it. Chapter 52 will cross
a larger boundary, from a Forth-built GCC to generations built by GCC.

## Try it

Run from the `forth-bootstrap` checkout root, using the seed built in Part 1. The construction writes `seed-cc` and `seed-ar` into `build-out/seed-cc/` and takes a few seconds. The new driver then compiles a small program; the working directory stays at the checkout root so the driver can locate its source tree, while the test source and executable live in a temporary directory.

<!-- check-tryit: its private /tmp hides the scratch checkout from the built driver; run directly. -->
<!-- tryit: skip -->
```sh
(
set -o pipefail
work=$(mktemp -d /tmp/book-probe.XXXXXXXXXX) || exit
trap 'rm -rf "$work"' EXIT
cat cc/driver/seed-cc-start.fth | ./seed-forth > "$work/build.log" 2>&1 || exit
wc -c build-out/seed-cc/seed-cc build-out/seed-cc/seed-ar || exit
cat > "$work/hello.c" <<'C' || exit
#include <stdio.h>
int main(void) {
    printf("hello from seed-cc\n");
    return 0;
}
C
./build-out/seed-cc/seed-cc "$work/hello.c" -o "$work/hello" || exit
"$work/hello"
)
```

Recorded checkpoint output:

```text
160136 build-out/seed-cc/seed-cc
 98624 build-out/seed-cc/seed-ar
258760 total
hello from seed-cc
```

The construction log is empty on success; both artifacts are static x86-64 ELF executables.

The rebuild check takes a few seconds more and is a step of `./check-all.sh`:

<!-- check-tryit: its private /tmp hides the scratch checkout from the built driver; run directly. -->
<!-- tryit: skip -->
```sh
tests/cc/seed-cc-rebuild-check.sh
```

Recorded rebuild-check output:

```text
seed-cc-rebuild-check: PASS (generation 2 seed-cc and seed-ar equal generation 1: 160136 and 98624 bytes)
```

## Exercise

Hints and feedback are in [Appendix H](66-exercise-feedback.md#chapter-50-which-stream-contains-c).

**Trace (easy).** Follow `compile-unit`, `make-archive` and `link-program`. Identify which child input streams contain C source and which contain only Forth. Explain why placing `start.o` inside `libseed.a` would change the linker's initial unresolved symbols.
