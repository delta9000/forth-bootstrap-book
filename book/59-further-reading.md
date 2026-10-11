# Appendix E — Further reading

Which reference answers the question in front of you: what an instruction means, how to factor a Forth word, how to parse C, or what a bootstrap proves? The readings below pair those questions with language texts, interface specifications and related projects. Choose the group that matches the source you are reading.

## Part 1 — How do you read the seed's machine code?

Keep these references beside [Part 1 — asm](part-1-asm.md) when checking instruction encodings, executable headers and the Linux boundary.

- **Intel, [*Intel® 64 and IA-32 Architectures Software Developer's Manual*](https://www.intel.com/content/www/us/en/support/articles/000006715/processors.html)** (Intel SDM).
  The instruction reference for checking encodings and register effects.

- **[*ELF Object File Format*](https://gabi.xinuos.com/elf.pdf)**, the ELF portion of the System V generic ABI.
  The reference for headers, segments and sections. Use it alongside the
  seed's ELF header and the compiler's object emission; the AMD64 supplement
  below supplies processor-specific rules.

- **[Linux man-pages](https://man7.org/linux/man-pages/), sections 2 (syscalls) and 5 (file formats: `elf`, `core`)**.
  Consult the syscall entries for argument contracts and error results,
  and `elf` for executable-format structures.

- **Richard W. M. Jones, ["JONESFORTH"](https://rwmj.wordpress.com/2010/08/07/jonesforth-git-repository/)**.
  A commented x86-32 Forth in assembly. It offers a comparison for dictionary
  lookup, compilation and interpreter structure on a different x86 target.

- **Brad Rodriguez, ["Moving Forth"](https://www.bradrodriguez.com/papers/moving1.htm)**.
  A series on Forth implementation techniques, threading models and assembly
  primitives. The link starts with Part 1, on threading techniques.

## Part 2 — How do you build and design with Forth words?

[Part 2 — Forth](part-2-forth.md) grows a library from the seed's primitives.
These readings offer broader language practice and other small implementations.

- **Leo Brodie, [*Starting Forth*](https://www.forth.com/starting-forth/)**.
  An introduction to conventional Forth vocabulary and stack-based programming.

- **Leo Brodie, [*Thinking Forth*](https://thinking-forth.sourceforge.net/)**.
  A guide to factoring, decomposition and program design in Forth.

- **Elizabeth D. Rather, Donald R. Colburn, and Charles H. Moore, ["The Evolution of Forth"](https://www.forth.com/resources/forth-programming-language/)**.
  An account of the language's history and the design forces behind it.

- **[Forth 2012 Standard](https://forth-standard.org/standard/intro)**.
  The successor to ANS Forth (ANSI X3.215-1994) provides conventional word
  contracts and portability rules. The seed implements a smaller language,
  not the standard as a whole.

- **[Gforth](https://www.gnu.org/software/gforth/)**.
  GNU Forth provides another implementation for exploring the language,
  with a manual and tutorial linked from the project page.

- **Bill Muench and C. H. Ting, eForth; C. H. Ting, [*eForth and Zen*](https://www.forth.org/OffeteStore/1013_eForthAndZen.pdf)**.
  A minimal portable Forth design for comparing the division between machine
  primitives and definitions written in Forth. The linked book is Ting's
  account, preserved in the Forth Interest Group's Offete Publications archive.

- **Cesar Blum, [sectorforth](https://github.com/cesarblum/sectorforth)**.
  A small x86 Forth built for a BIOS boot sector. Compare its environment
  and primitive choices with the Linux-hosted seed.

- **Koichi Nakamura, [planckforth](https://github.com/nineties/planckforth)**.
  A Forth bootstrapped from a handwritten i386 ELF binary and a `bootstrap.fs`
  library. Compare how its library builds readable vocabulary on top of
  its initial primitive names.

## Part 3 — How do C syntax and interfaces become machine code?

Use these with [Part 3 — compiler](part-3-compiler.md). The compiler texts
address language translation; the ELF and ABI references address the output's
contract with other tools.

- **Niklaus Wirth, [*Compiler Construction*](https://people.inf.ethz.ch/wirth/CompilerConstruction/)**.
  An account of grammars and a working compiler, using Oberon-0 rather than C.

- **Andrew W. Appel with Maia Ginsburg, [*Modern Compiler Implementation in C*](https://www.cs.princeton.edu/~appel/modern/c/)**.
  A compiler text covering parsing and code generation in greater depth.

- **Jack Crenshaw, "Let's Build a Compiler"**.
  A step-by-step compiler construction series originally using Pascal.
  Marcel Hendrix's [iForth adaptation](https://iforth.nl/crenshaw/tiny.html)
  preserves the progression while translating the examples to Forth; it is
  an adaptation, not the original Pascal edition.

- **Theodore Norvell, ["Parsing Expressions by Recursive Descent"](https://www.engr.mun.ca/~theo/Misc/exp_parsing.htm)**.
  A comparison of expression-parsing approaches. Read it beside the
  precedence cascade in [Chapter 33](33-expressions-part-1.md).

- **Keith Clarke, ["The top-down parsing of expressions"](https://www.antlr.org/papers/Clarke-expr-parsing-1986.pdf)**.
  A technical note on precedence climbing, an alternative to spelling out
  a separate parser function for each precedence level. The scanned report
  is hosted by the ANTLR project.

- **Vaughan R. Pratt, ["Top down operator precedence"](https://doi.org/10.1145/512927.512931)** (1973).
  Another approach to expression parsing, useful for comparing parser
  organization with the cascade.

- **[*System V Application Binary Interface, AMD64 Architecture Processor Supplement*](https://gitlab.com/x86-psABIs/x86-64-ABI)** (psABI).
  The maintained reference for calling conventions and object interfaces. Read it alongside
  [System V calls](41-system-v-calls.md); the ELF specification listed under
  Part 1 also supports [Objects and relocations](40-objects-and-relocations.md).

## Part 4 — What makes a toolchain bootstrap trustworthy?

[Part 4 — bootstrap](part-4-bootstrap.md) raises questions about inherited
executables, rebuild comparisons and the boundary between tools and kernels.
For the book's GCC route, use [GCC stages C and D](52-gcc-4-fixed-point.md);
for kernel entry and handoff, use [K0 and K1](54-k0-and-k1.md) and
[Linux and kexec](55-linux-and-kexec.md).

- **Ken Thompson, ["Reflections on Trusting Trust"](https://doi.org/10.1145/358198.358210)** (1984).
  The compiler-trust argument behind asking which executable built a tool,
  rather than examining its source alone.

- **[Bootstrappable builds](https://www.bootstrappable.org/)**.
  A starting point for projects that reduce dependence on inherited binaries.

- **Jeremiah Orians et al., [stage0](https://github.com/oriansj/stage0),
  [stage0-posix](https://github.com/oriansj/stage0-posix),
  [M2-Planet](https://github.com/oriansj/M2-Planet), and
  [mescc-tools](https://github.com/oriansj/mescc-tools)**.
  Related source-bootstrap tools. Use them to compare the assembler, linker
  and compiler boundaries with those in this book.

- **Janneke Nieuwenhuizen et al., [GNU Mes](https://www.gnu.org/software/mes/)**.
  A Scheme interpreter and C compiler used in the Guix Full Source Bootstrap route through
  TinyCC toward GCC. This is a related route, not this book's direct GCC route.

- **[Live-bootstrap](https://github.com/fosslinux/live-bootstrap)**.
  A source-bootstrap project for studying how a complete chain is assembled
  and made reproducible.

