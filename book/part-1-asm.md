# Part 1 — asm

The whole starting program is a 1,772-byte x86-64 executable, written as
commented hexadecimal in `seed/000-seed.hex0` and assembled by the 229-byte
`hex0-seed`. Part 1 reads those bytes until every one of them is accounted
for. When it ends, you can build the seed, trace a line of input through it,
and say which instructions run.

No new code is written here. The seed is a Forth with two stacks, a
dictionary of 32 primitives, a token reader, a colon compiler and a REPL.
Each chapter decodes one layer of it against the machine and the Linux
interface.

- [Chapter 4](04-x86-64-and-two-stacks.md) teaches how to decode x86-64
  instructions by hand, and sets out the seed's register and stack
  conventions.
- [Chapter 5](05-elf-and-entry.md) reads the ELF header, the program header
  and the entry code. Together they fix the memory map that every later
  chapter uses.
- [Chapters 6](06-stack-primitives.md) and [7](07-arithmetic-and-logic.md)
  decode the stack, memory and arithmetic primitives as register and memory
  changes.
- [Chapter 8](08-seed-io.md) crosses into Linux: `emit`, `key`, `bye` and
  the generic `syscall6`.
- [Chapters 9](09-dictionary.md) and [10](10-colon-compiler.md) follow a
  name through the dictionary and compile new words as native calls.
- [Chapter 11](11-branches.md) adds branches that take their destination from
  an inline cell.
- [Chapter 12](12-repl.md) joins the parts into the REPL and builds the
  complete seed.
- [Chapter 13](13-primitive-reference.md) is the reference table to keep
  open while reading Part 2.

The checkpoints inspect the built seed or pipe a few words into
`./seed-forth`. Each states the particular bytes, output, or exit behavior
it checks.

Before moving on, return to `hello` from Chapter 1: where is its name
stored, what bytes are compiled for its body, and how does its `emit`
reach Linux? Chapters 9, 10 and 8 supply those three links. Part 2 can
then use a primitive's stack contract without decoding its instructions
again.
