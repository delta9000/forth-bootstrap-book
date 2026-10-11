# Assembler regression check

<a id="chapter-26--the-m1-assembler-and-hex2-linker"></a>
<a id="appendix-i--the-m1-assembler-and-hex2-linker"></a>

The standalone M1/hex2 assembler remains a regression check in the pinned
source repository. It is outside the book's teaching route: continue from
[Chapter 25](25-lib-12-defining-words-and-bytes-eq.md) to
[Part 3](part-3-compiler.md). The C compiler emits executable and object
bytes directly; its loader does not include `forth/130-asm.fth`
(`forth-bootstrap/cc/compiler-layers.sh:2–11`).

The source's quick-check suite still runs `tests/asm/hi-check.sh`
(`forth-bootstrap/check-all.sh:64`). It loads the seed, library, and
assembler, assembles a small program, and checks three results: `hi`, exit
status 42, and a 160-byte executable. This is a smoke test of that input,
not a general assembler-conformance claim.

[Stage A](38-main-and-bootstrap-chain.md#stage-a-the-parity-proof) is a
separate compiler regression: it compares M1 text emitted by Forth-built
and GCC-built M2-Planet without assembling that text
(`forth-bootstrap/tests/cc/stage-a-check.sh:3–13`). The direct bootstrap
still uses kaem and the mescc-tools-extra utilities
([Chapter 51](51-owning-the-tools.md)); their role is unchanged.

## Run the check

<a id="try-it"></a>

From the book root, after the [seed setup](01-reading-the-book.md#try-it-establish-the-setup),
run `python3 tools/book-lab.py run 26.1`. The retained selector is a
compatibility ID for this check, not a chapter on the reading route.
The lab companion checks its stdout against `hi`, `exit: 42`, and `160`.
To run the source repository's own test instead, use
`./tests/asm/hi-check.sh` from the `forth-bootstrap` checkout.

The exact lab below also runs from that checkout with `seed-forth` built.
It writes only to a fresh temporary directory, removes it on exit, and
checks the generated program's intentional status 42. The printed byte
count and output are checked by the lab companion and book check harness.

<details>
<summary>Regression input and shell wrapper (lab 26.1)</summary>

<!-- tryit: expect "hi\nexit: 42\n160" -->
```sh
(
set -o pipefail
d=$(mktemp -d /tmp/book-probe.XXXXXXXXXX) || exit "$?"
trap 'status=$?; rm -rf -- "$d" || status=1; exit "$status"' EXIT
cat > "$d/hi.M1" <<'M1' || exit "$?"
DEFINE mov_eax, B8
DEFINE mov_edi, BF
DEFINE mov_esi, BE
DEFINE mov_edx, BA
DEFINE jmp8 EB
DEFINE syscall 0F05

:ELF_base                                   # the file loads at 0x600000
'7F454C46 02 01 01 03 00 00000000000000'    # e_ident
'0200 3E00 01000000'                        # ET_EXEC, AMD64, version 1
&_start '00000000'                          # e_entry
%ELF_phdr>ELF_base '00000000'               # e_phoff
'0000000000000000 00000000'                 # e_shoff, e_flags
'4000 3800 0100 0000 0000 0000'             # sizes; one program header
:ELF_phdr
'01000000 07000000 0000000000000000'        # PT_LOAD, RWX, offset 0
&ELF_base '00000000' &ELF_base '00000000'   # vaddr, paddr
%ELF_end>ELF_base '00000000'                # filesz
%ELF_end>ELF_base '00000000'                # memsz
'0100000000000000'                          # align

:_start
    mov_eax, %1  mov_edi, %1                # write(1,
    mov_esi, &msg  mov_edx, %3              #   msg, 3)
    syscall
    jmp8 !done                              # hop over the data
:msg "hi
"
:done
    mov_eax, %60  mov_edi, %42  syscall     # exit(42)
:ELF_end
M1
{ cat forth/010-lib.fth forth/130-asm.fth || exit "$?"
  echo "create out s, $d/hi [lit] 0 c,  out asm-out-name !"
  echo asm-main; cat "$d/hi.M1"; } | ./seed-forth || exit "$?"
chmod +x "$d/hi" || exit "$?"
status=0
"$d/hi" || status=$?             # prints "hi"
printf 'exit: %s\n' "$status"  # prints "exit: 42"
test "$status" -eq 42 || exit 1
wc -c < "$d/hi"             # prints: 160
)
```

</details>

## Source and history

This page replaces the former Chapter 26 / Appendix I walkthrough; its
URL and check selector remain available for existing links. Assembler
section-by-section teaching, exercises, and canonical source listings
have been removed. The implementation and test remain unchanged in
[forth-bootstrap at the pinned revision](https://github.com/delta9000/forth-bootstrap/blob/b25487ad4d62adb950c3372de43564dfcfabdd87/forth/130-asm.fth).
That MIT-licensed source retains its attribution and history.

Book source reconstruction covers the 34 files explicitly listed in
`tools/canonical-sources.txt`. The assembler is separately recorded in
`tools/check-only-sources.txt`; it is checked as a program, not reconstructed
from book listings. See the [editorial notes](65-editorial-notes.md) for
what each validation step establishes.
