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
- An untagged fence may be a source excerpt, a runnable example, a
  schematic trace or recorded output. Identify which it is. Source excerpts
  cite `forth-bootstrap/<path>:<line>`; point at the named mechanism, which
  may intentionally lie inside a larger excerpt. Bounds checking cannot
  decide whether that mechanism supports the caption.

The explicit book-taught scope is the 34 files listed in
`tools/canonical-sources.txt`. It covers the seed, Forth library and
numbered compiler layers, not every file in the upstream repository.
`forth/130-asm.fth` stays in the pinned upstream checkout but is excluded
from source tangling and teaching coverage. The
[assembler regression check](26-m1-and-hex2.md#run-the-check) exercises
that separate program without reproducing its implementation.

When the source changes, move the submodule pin, then update every quoted
fence and citation that the change touches. Commit the book side
separately.

Appendix lettering starts at C to preserve references in the quoted
source. The former primitive-reference and memory-map appendices are now
Chapters 13 and 5. The assembler regression check is unnumbered back
matter after Appendix H. Its filename and lab selector retain 26 for
compatibility, so the main chapter sequence goes from 25 to 27.

## Shape of a chapter

- The opening paragraph starts from something concrete: a byte sequence,
  a short program, a question. It states the new idea and the result the
  reader gains.
- Establish a worked mental model before the implementation needs it:
  follow one expression, allocation, call, or artifact through the mechanism.
  Name the state each step must preserve and explain the consequence of
  losing it. Let that example determine the order of the explanation.
- Grow the implementation in fragments of about 5–30 lines, each with one
  job and one citation. A caption should explain the need or a consequential
  choice; avoid translating each code line into a sentence.
- Source order and reading order can differ. Independent named chunks may
  move while their assembly recipe preserves the compiled order; successive
  fragments of the same `file=` or `chunk=` must retain their byte order.
  Verify reconstruction after every rearrangement.
- Keep the central mechanism visible. Supporting encodings, extension hooks,
  and repeated cases may use an expandable implementation section with a
  specific summary. Teach its interface before the fold. All source within
  the declared coverage scope remains present; links must reveal their
  destinations, and printing must include the complete manuscript.
- A concept already taught is recalled in one clause, as "(Chapter N)", at
  most once per chapter. Chapter numbers have no leading zeros.
- A chapter ends with `## Try it`, the checkpoint, then `## Exercise`.
- Label exercises consistently as `Trace`, `Verify`, `Modify` or `Extend`,
  followed by the difficulty: for example, `**Trace (easy).**`.
  Use `easy`, `moderate` or `hard` for difficulty.
- A checkpoint names its prerequisites and comparison. Distinguish newly
  observed output, output from a recorded run, and a manual prediction. A
  command outside the seed-example harness (a long build, pinned archives,
  bwrap and strace, QEMU) is marked to be skipped. A comment above that marker
  gives the reason, and the prose tells the reader what the command needs
  and how long it takes.
- Output from a run that is too long to repeat is labelled as coming from
  a recorded run.

Each Part opens with a one-screen page that maps its chapters. The
[Glossary](62-glossary.md) gives one name per concept, and chapters use
that name.

At a difficult transition, name the action the reader needs to perform,
not merely the earlier chapter number. Teach an unfamiliar representation
before asking for a prediction; keep feedback separate from the attempt
and link a specific repair. An optional expandable bridge can keep a part
map short for experienced readers. The
[capability checks](63-concepts.md#capability-checks-at-the-transitions)
are examples, not a template required in every chapter. A successful build
is not a substitute for explaining its mechanism.

## Checks

`./check.sh`, run from the repository root, must pass before publication.
CI runs the same checks on every pull request, builds with mdBook 0.5.4 and
checks the rendered links. The authoring checks require Python 3.11 or
newer, including the packaging regression fixtures. When Node.js is
available, the suite also executes focused reader-interface tests; without
it, those cases report `SKIP`. They check script behavior, not browser
layout or screen-reader output. Only `main` deploys.

| Check | What it verifies |
|---|---|
| `python3 -m unittest discover -s tools/tests -v` | Regression fixtures for the checker and checkpoint failure paths |
| `tools/tangle.sh verify --strict` | Published fences reconstruct the 34 book-taught files in `tools/canonical-sources.txt`, byte for byte; missing coverage fails |
| `tools/check-numbers.py` | Recognized numeric/count forms and selected named Forth citations; all explicit `forth-bootstrap/PATH:LINE` citations have existing files and sensible in-bounds positions |
| `tools/check-tryit.py` | Selected shell fences that pipe into the seed execute in scratch space, subject to reported skips; only recognized expectations are asserted |
| `tools/gen-index.py --check` | Published name/concept targets exist and the [word index](WORD-INDEX.md) matches the generator |
| `tools/check-links.py` | Published local Markdown links and derived anchors resolve; external URLs are not fetched |
| `tools/check-links.py --html docs` after `mdbook build` | Published rendered pages exist and linked fragments are present in their actual HTML |

The reader's [lab companion](labs.md) uses `tools/book-lab.py` to list,
show, or run one published shell block. Selectors count tagged shell
fences in chapter order, including excluded ones. Run the affected lab
after changing a checkpoint. A successful run checks shell status and,
when present, explicit UTF-8 `tryit: expect` metadata; other transcript
comparisons remain manual. The runner preserves each block's shell
semantics and runs without isolation. Long builds and context-dependent
blocks remain excluded.

`./check.sh --static` runs regression, source-coverage, citation-bounds,
index and Markdown-link checks without executing the seed. It explicitly
omits runtime checks and numeric forms that require the built seed size.
The full check requires the pinned source/vendor checkout and runs the
vendored hex0 assembler and generated seed.

A passing run does not prove every prose number, the semantic correctness
of every citation, every printed transcript, or compiler conformance. The
seed harness selects pipeline-to-seed fences and documents its recognized
expectation syntax in `tools/check-tryit.py`; direct driver, toolchain and
QEMU commands need their own execution evidence. Record the source pin,
command, environment, status and compared artifacts when running those
checks. A skip or an unselected block provides no runtime result.

Keep source-comment corrections outside canonical fences while the source
pin is unchanged. Update the pin and the entire affected explanation,
trace, exercise and reference together when an upstream change is intended.

When a chapter is replaced, `tools/gen-index.py` may lose index targets
that pointed into the old file. Retarget those entries in its concept
list, then regenerate the index with `python3 tools/gen-index.py`.

## Working files

`book/outline/` holds one stub per chapter: its scope, sources,
prerequisites and checkpoint. `book/outline/LEDGER.md` lists each concept
with the chapter that teaches it. `tools/make-bundle.py NN` gathers a
chapter's stub, neighbours, ledger rows and sources into `book/bundles/NN/`
(not committed).

The previous edition's `book/WRITING.md`, `book/LEARNING_STORY_PLAN.md`
and `book/34-direct-tinycc.md` are retired and excluded from
`SUMMARY.md`. They are source-history material, not current authoring
instructions or learner-validation evidence. This page applies to the
published edition.

## The reading edition

`theme/reader.css` supplies screen and print typography.
`theme/reader.js` adds source captions and chapter navigation without
changing copied code or source anchors. The manuscript remains readable
without JavaScript. Keep these asset names distinct from mdBook's reserved
theme filenames, especially `book.js`, which would replace its core
search and navigation script.

Mechanism diagrams use native HTML text and the `.mechanism` styles. Keep
each figure tied to a worked example and state what its arrows mean.
Distinguish memory order, execution order, construction ancestry and value
transport; these are different relationships. Reflow labels on narrow
screens rather than shrinking them. Captions must retain the key inference
without color, and diagrams must remain readable without JavaScript.

After changes to the reading interface, inspect a long source chapter at
desktop and phone widths, in light and dark themes. Open the in-chapter
contents, follow a checkpoint link, try search, and check print styling.
Code and wide tables may scroll within their own regions; the page itself
must not require horizontal scrolling.

Build and check the rendered edition before packaging it:

```sh
mdbook build
python3 tools/check-links.py --html docs
python3 tools/package-book.py
```

The packager requires Python 3.11 or newer. The resulting
`dist/forth-bootstrap-book.zip` is an offline reading copy.
Its manifest records the source revision and working-tree content so an
uncommitted manuscript is not presented as an exact committed release.
Only published pages and required assets belong in that package; scratch
bundles and editorial working files do not. Packaging does not rerun the
compiler or kernel builds, and its hashes establish artifact identity,
not the correctness of the book's technical claims.


## Evidence to preserve for long runs

The committed historical reports are selected observations. In particular,
the host record contains counts and summaries, not the raw `execveN.txt`
streams needed to repeat the original join and path classification.

For a new long run, preserve a small manifest alongside its logs:

- Exact book, source and recursive vendor commit identities
- Input-manifest digest and the result of verifying the required inputs
- Command, target/profile, working root, machine/tool versions and resources
- Exit statuses and comparison scope, including skips and archive exceptions
- Raw trace/serial logs, generated reports and hashes of exported evidence

A useful manifest links those files to one run; it cannot reconstruct
missing historical raw records. Keep previous work and evidence outside
paths a launcher recreates, and inspect its cleanup policy before rerunning.
