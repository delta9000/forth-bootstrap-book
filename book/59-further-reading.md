# Appendix E — Further reading

Which reference answers the question in front of you: what an instruction means, how to factor a Forth word, how to parse C, or what a bootstrap proves? The readings below pair those questions with language texts, interface specifications and related projects. Choose the group that matches the source you are reading.

## Part 1 — How do you read the seed's machine code?

Keep these references beside [Part 1 — asm](part-1-asm.md) when checking instruction encodings, executable headers and the Linux boundary.

- **Intel® 64 and IA-32 Architectures Software Developer's Manual** (Intel SDM).
  The instruction reference for checking encodings and register effects.
  Available from intel.com.

- **TIS, *Executable and Linkable Format (ELF) Specification***.
  A reference for ELF headers, segments and sections. The old reading list's
  location is `gabi.xinuos.com`; use it alongside the seed's ELF header and
  the compiler's object emission.

- **Linux man-pages, sections 2 (syscalls) and 5 (file formats: `elf`, `core`)**.
  Consult the syscall entries for argument contracts and error results,
  and `elf` for executable-format structures.

- **Richard W. M. Jones, "JONESFORTH"**.
  A commented x86-32 Forth in assembly. It offers a comparison for dictionary
  lookup, compilation and interpreter structure on a different x86 target.

- **Brad Rodriguez, "Moving Forth"**.
  A series on Forth implementation techniques, threading models and assembly
  primitives. Available at bradrodriguez.com/papers.

## Part 2 — How do you build and design with Forth words?

[Part 2 — Forth](part-2-forth.md) grows a library from the seed's primitives.
These readings offer broader language practice and other small implementations.

- **Leo Brodie, *Starting Forth***.
  An introduction to conventional Forth vocabulary and stack-based programming.
  Free online at forth.com.

- **Leo Brodie, *Thinking Forth***.
  A guide to factoring, decomposition and program design in Forth.

- **Elizabeth D. Rather, Donald R. Colburn, and Charles H. Moore, "The Evolution of Forth"**.
  An account of the language's history and the design forces behind it.

- **ANS Forth (ANSI X3.215-1994)**.
  The language standard is a reference for conventional word contracts.
  The seed implements a smaller language, not the standard as a whole.

- **gforth**.
  GNU Forth provides another implementation for exploring the language.
  Documentation at gnu.org/software/gforth.

- **Bill Muench and C. H. Ting, "eForth"**.
  A minimal portable Forth design for comparing the division between machine
  primitives and definitions written in Forth.

- **Cesar Blum, "sectorforth"**.
  A small x86 Forth built for a BIOS boot sector. Compare its environment
  and primitive choices with the Linux-hosted seed.

- **Koichi Nakamura, "planckforth"**.
  A Forth bootstrapped from a handwritten i386 ELF binary and a `bootstrap.fs`
  library. Compare how its library builds readable vocabulary on top of
  its initial primitive names.

## Part 3 — How do C syntax and interfaces become machine code?

Use these with [Part 3 — compiler](part-3-compiler.md). The compiler texts
address language translation; the ELF and ABI references address the output's
contract with other tools.

- **Niklaus Wirth, *Compiler Construction***.
  An account of grammars and a working compiler, using Oberon-0 rather than C.

- **Andrew Appel, *Modern Compiler Implementation in C***.
  A compiler text covering parsing and code generation in greater depth.

- **Jack Crenshaw, "Let's Build a Compiler"**.
  A step-by-step compiler construction series using Pascal. Search the title
  to locate the series.

- **Theodore Norvell, "Parsing Expressions by Recursive Descent"**.
  A comparison of expression-parsing approaches. Read it beside the
  precedence cascade in [Chapter 33](33-expressions-part-1.md).

- **Keith Clarke, "The top-down parsing of expressions"**.
  A technical note on precedence climbing, an alternative to spelling out
  a separate parser function for each precedence level.

- **Vaughan Pratt, "Top down operator precedence"**.
  Another approach to expression parsing, useful for comparing parser
  organization with the cascade.

- **System V Application Binary Interface, AMD64 Architecture Processor Supplement** ("psABI").
  The reference for calling conventions and object interfaces. Maintained
  at gitlab.com/x86-psABIs/x86-64-ABI. Read it alongside
  [System V calls](41-system-v-calls.md); the ELF specification listed under
  Part 1 also supports [Objects and relocations](40-objects-and-relocations.md).

## Part 4 — What makes a toolchain bootstrap trustworthy?

[Part 4 — bootstrap](part-4-bootstrap.md) raises questions about inherited
executables, rebuild comparisons and the boundary between tools and kernels.
For the book's GCC route, use [GCC stages C and D](52-gcc-4-fixed-point.md);
for kernel entry and handoff, use [K0 and K1](54-k0-and-k1.md) and
[Linux and kexec](55-linux-and-kexec.md).

- **Ken Thompson, "Reflections on Trusting Trust"**.
  The compiler-trust argument behind asking which executable built a tool,
  rather than examining its source alone.

- **bootstrappable.org**.
  A starting point for projects that reduce dependence on inherited binaries.

- **Jeremiah Orians et al., stage0 / stage0-posix / M2-Planet / mescc-tools** (github.com/oriansj).
  Related source-bootstrap tools. Use them to compare the assembler, linker
  and compiler boundaries with those in this book.

- **Janneke Nieuwenhuizen, GNU Mes** (gnu.org/software/mes).
  A Scheme/C interpreter used in the Guix Full Source Bootstrap route through
  TinyCC toward GCC. This is a related route, not this book's direct GCC route.

- **Live-bootstrap** (github.com/fosslinux/live-bootstrap).
  A source-bootstrap project for studying how a complete chain is assembled
  and made reproducible.

- **[seed-forth](https://github.com/delta9000/seed-forth)**.
  The earlier project retains routes discussed in
  [Appendix C](57-historical-reproducibility.md) and the GCC continuation
  discussed in the [epilogue](56-gcc-15-epilogue.md). Keep those historical
  results distinct from the current forth-bootstrap route.
