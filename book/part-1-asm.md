# Part 1 — asm

When we called `hello`, the seed had to remember its name, find its
instructions, and send three bytes to Linux. Part 1 follows those actions
inside the program we have already built. By the end, you can trace a line
of input through the seed and say which instructions run.

We begin with the values a word works on: where are they kept, and how
does one instruction change them? Chapter 4 builds that model before
teaching the byte encodings. Chapter 5 then shows how Linux loads the
file and prepares its starting state. With those pieces in place, the
individual Forth words have somewhere to run.

The source is the commented hexadecimal in `seed/000-seed.hex0`. We will
read the existing seed rather than implement a second one. Its 32
**primitives** are built-in words; a **dictionary** associates names with
code; and its read–evaluate–print loop, or **REPL**, repeatedly reads and
handles input. Each gets a worked explanation when we reach it.

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
