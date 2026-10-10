# Editorial notes

This page is for anyone changing the book. It covers how the book is tied
to the sources it teaches, how a chapter is laid out, and the checks every
change must pass.

## The book and its sources

The book quotes the `forth-bootstrap` repository, pinned as the
`forth-bootstrap` submodule of this repository. Two kinds of code fence
appear in chapters:

- A fence tagged `file=` or `chunk=` is part of the source. Read in book
  order, those fences reassemble the quoted files byte for byte. They are
  copied from the source and never retyped.
- An untagged fence is an excerpt. Its introduction cites
  `forth-bootstrap/<path>:<line>`, and the cited line must hold the first
  word the caption names.

When the source changes, move the submodule pin, then update every quoted
fence and citation that the change touches. Commit the book side
separately.

## Shape of a chapter

- The opening paragraph starts from something concrete: a byte sequence,
  a short program, a question. It states the new idea and the result the
  reader gains.
- The first section shows the shape of the code. Later sections grow it in
  fragments of about 5–30 lines, each with one job and one citation.
- A concept already taught is recalled in one clause, as "(Chapter N)", at
  most once per chapter. Chapter numbers have no leading zeros.
- A chapter ends with `## Try it`, the checkpoint, then `## Exercise`.
- A checkpoint runs a real command and shows its real output. A command
  that cannot run inside the checks (a long build, pinned archives, bwrap
  and strace, QEMU) is marked to be skipped. A comment above that marker
  gives the reason, and the prose tells the reader what the command needs
  and how long it takes.
- Output from a run that is too long to repeat is labelled as coming from
  a recorded run.

Each Part opens with a one-screen page that maps its chapters. The
[Glossary](62-glossary.md) gives one name per concept, and chapters use
that name.

## Checks

`./check.sh`, run from the repository root, must pass before every commit:

| Check | What it verifies |
|---|---|
| `tools/tangle.sh verify --strict` | every `file=` and `chunk=` fence reassembles its source file byte for byte |
| `tools/check-numbers.py` | every numeric claim with a citation matches the cited source |
| `tools/check-tryit.py` | every runnable Try it block runs and prints what the chapter says |
| `tools/gen-index.py --check` | the [word index](WORD-INDEX.md) is up to date |
| `tools/check-links.py` | every link and anchor resolves |

When a chapter is replaced, `tools/gen-index.py` may lose index targets
that pointed into the old file. Retarget those entries in its concept
list, then regenerate the index with `python3 tools/gen-index.py`.

## Working files

`book/outline/` holds one stub per chapter: its scope, sources,
prerequisites and checkpoint. `book/outline/LEDGER.md` lists each concept
with the chapter that teaches it. `tools/make-bundle.py NN` gathers a
chapter's stub, neighbours, ledger rows and sources into `book/bundles/NN/`
(not committed). `AGENTS.md` at the repository root sets out the chapter
rules in full.

The previous edition's writing protocol and learning-story plan are kept
under Retired for reference. Where they disagree with this page, this page
applies.
