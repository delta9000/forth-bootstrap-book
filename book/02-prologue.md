# Chapter 2 — Prologue: Seventeen hundred and seventy-two bytes

A file small enough to inspect byte by byte can start a chain that builds Linux. The file is `seed-forth`: a 1,772-byte Forth executable for x86-64 Linux, represented as annotated hexadecimal in `seed/000-seed.hex0`. The checkpoint below builds it and puts its size and opening bytes in front of you.

The seed can read Forth source that extends its own capabilities. That is the opening a bootstrap needs: enough machinery to build the next tool from source, then use that tool to build another. The destination is concrete. The project's Results section reports Linux 7.2.8 booted by kexec and a kernel image of 1,278,976 bytes (`forth-bootstrap/README.md:164–165`).

Starting small makes a particular kind of understanding possible. You can account for each byte of the seed and connect its behavior to the source it consumes. As the tools grow, the question changes from “what does this byte do?” to “which program built this artifact, and what did that program depend on?” Smallness makes the first audit manageable; it does not establish correctness by itself or remove the machine and operating system beneath this checkpoint.

Chapter 1 gives the route through the book. Follow that map from the seed's instructions to the tools it makes possible, carrying the same question about dependencies across each handoff.

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

**Verify — easy.** Compare the byte groups printed by `od` with the opening data at `forth-bootstrap/seed/000-seed.hex0:21`. Check their order without interpreting the header fields; Chapter 5 explains those fields. What does agreement on the opening bytes leave unchecked about the rest of the file?
