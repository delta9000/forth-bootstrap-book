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
are examples, not a template required in every chapter. The outline's
reading-order chain is not evidence that a learner has acquired each skill,
and a successful build is not a substitute for explaining its mechanism.

## Checks

`./check.sh`, run from the repository root, must pass before publication.
The PR workflow runs the same checks, builds with mdBook 0.5.4 and checks the
rendered result. Only pushes to `main` or a manual run on `main` can proceed
to the deployment job; a PR validation never deploys.

| Check | What it verifies |
|---|---|
| `python3 -m unittest discover -s tools/tests -v` | Regression fixtures for the checker and checkpoint failure paths |
| `tools/tangle.sh verify --strict` | Published fences reconstruct every required file in `tools/canonical-sources.txt`, byte for byte; missing coverage fails |
| `tools/check-numbers.py` | Recognized numeric/count forms and selected named Forth citations; all explicit `forth-bootstrap/PATH:LINE` citations have existing files and sensible in-bounds positions |
| `tools/check-tryit.py` | Selected shell fences that pipe into the seed execute in scratch space, subject to reported skips; only recognized expectations are asserted |
| `tools/gen-index.py --check` | Published name/concept targets exist and the [word index](WORD-INDEX.md) matches the generator |
| `tools/check-links.py` | Published local Markdown links and derived anchors resolve; external URLs are not fetched |
| `tools/check-links.py --html docs` after `mdbook build` | Published rendered pages exist and linked fragments are present in their actual HTML |

`./check.sh --static` runs regression, source-coverage, citation-bounds,
index and Markdown-link checks without executing the seed. It explicitly
omits runtime checks and numeric forms that require the built seed size.
The full check requires the pinned source/vendor checkout and runs the
vendored hex0 assembler and generated seed. Keep its full output when
reviewing a change; a final success line alone loses skip and assertion counts.

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


## Evidence to preserve for long runs

The committed historical reports are selected observations. In particular,
the host record contains counts and summaries, not the raw `execveN.txt`
streams needed to repeat the original join and path classification. Do not
relabel a synthetic trace exercise or a summary read as a repeated audit.

For a new long run, preserve a small manifest alongside its logs:

- Exact book, source and recursive vendor commit identities
- Input-manifest digest and the result of verifying the required inputs
- Command, target/profile, working root, machine/tool versions and resources
- Exit statuses and comparison scope, including skips and archive exceptions
- Raw trace/serial logs, generated reports and hashes of exported evidence

A useful manifest links those files to one run; it cannot reconstruct
missing historical raw records. Keep previous work and evidence outside
paths a launcher recreates, and inspect its cleanup policy before rerunning.
