# Chapter 2 — Prologue: Seventeen hundred and seventy-two bytes

The `hello` you defined in Chapter 1 was not present when the seed
started. The seed read its name, wrote a body of machine instructions,
and called that body. A program of 1,772 bytes had become a little more
capable without changing its original executable.

That is enough to begin a source bootstrap. Feed the seed definitions
for memory management, loops, and byte writers; then feed it definitions
for reading and compiling C. The C compiler can build the tools needed
to build another C compiler. Each step gives us a larger tool whose
construction we can trace back to the smaller one.

The starting file is `seed-forth`, an x86-64 Linux executable represented
as annotated hexadecimal in `seed/000-seed.hex0`. The hexadecimal
assembler that builds it is smaller still. Chapter 3 identifies that
inherited program; Chapters 4–12 account for the Forth seed's bytes.
Our first task is to explain how those bytes turn an input definition
into instructions that run.

The small size makes that task tractable. It also makes the limits
visible: 1,772 is the size of the executable, not the whole environment
it depends on. Its calls still enter Linux, and its instructions still
run on a processor. As the tools grow, our question changes from
“what does this byte do?” to “which program built this artifact?”
Part 4 follows that question through rebuilding GCC and into a guest
that builds and boots Linux. Chapter 55 examines the final kernel
handoff and its recorded evidence.

For now, put the first artifact in front of you. The checkpoint measures
the seed and exposes its opening bytes. In Chapter 5, those same bytes
become a loading recipe rather than a string of hexadecimal digits.

## Try it: inspect the seed

Recall the checkpoint working directory from Chapter 1: the `forth-bootstrap` checkout, located at `./forth-bootstrap` within the book checkout. Run the commands below there. The build script writes `seed-forth` and reports its size (`forth-bootstrap/seed/build.sh:27`). `wc -c` counts the file's bytes. `od` displays its first four bytes: `-An` suppresses addresses, `-tx1` prints individual bytes in hexadecimal, and `-N4` limits the read to four bytes.

```sh
./seed/build.sh
wc -c seed-forth
od -An -tx1 -N4 seed-forth
```

Observed output:

```text
Built seed-forth (1772 bytes) using vendor/stage0-posix/bootstrap-seeds/POSIX/AMD64/hex0-seed
1772 seed-forth
 7f 45 4c 46
```

## Exercise

**Verify (easy).** Compare the byte groups printed by `od` with the opening data at `forth-bootstrap/seed/000-seed.hex0:21`. Check their order without interpreting the header fields; Chapter 5 explains those fields. What does agreement on the opening bytes leave unchecked about the rest of the file?
