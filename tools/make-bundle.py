#!/usr/bin/env python3
"""Build the writing bundle for one chapter of the outline.

    python3 tools/make-bundle.py NN        (from the repository root)

Writes book/bundles/NN/ (gitignored), everything a chapter writer reads
(see AGENTS.md):

  stub.md      the chapter's outline stub, book/outline/NN-*.md
  spine.md     every stub in reading order, two or three lines each
  ledger.md    a copy of book/outline/LEDGER.md
  prereqs.md   for each prerequisite chapter: the closing paragraph of its
               written chapter if one exists (book/NN-*.md under the new
               numbering is not used yet), else of its stub's Scope
  old/         the existing chapters the stub reuses (its Reuses links)
  source/      the forth-bootstrap files the stub names (from the pinned
               submodule), and source/chunks/NAME.md: each chunk the
               chapter owns, as the exact fenced block from the old book
  owns.txt     the file= fences and chunk= names this chapter owns: those
               INVENTORY.md lists for the old chapters it reuses
"""
import glob, os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK = os.path.join(ROOT, "book")
OUTLINE = os.path.join(BOOK, "outline")
SRC = os.environ.get("FORTH_BOOTSTRAP") or os.path.join(ROOT, "forth-bootstrap")


def stub_path(nn):
    found = glob.glob(os.path.join(OUTLINE, f"{nn}-*.md"))
    if len(found) != 1:
        sys.exit(f"make-bundle: no single stub book/outline/{nn}-*.md")
    return found[0]


def field(text, name):
    """The text of a 'Name: ...' field, up to the next field or heading."""
    m = re.search(rf"^{name}:[ \t]*(.*?)(?=^\w[\w ]*:[ \t]|^#|\Z)", text, re.M | re.S)
    return m.group(1).strip() if m else ""


def stubs():
    for p in sorted(glob.glob(os.path.join(OUTLINE, "[0-9][0-9]-*.md"))):
        yield os.path.basename(p)[:2], p, open(p).read()


def spine():
    out = ["# Spine: every chapter of the book in reading order", ""]
    for nn, p, t in stubs():
        title = t.splitlines()[0].lstrip("# ").strip()
        part = field(t, "Part")
        scope = re.split(r"(?<=\.)\s", field(t, "Scope"), maxsplit=1)[0]
        out.append(f"- **{nn} {title}** (Part {part}): {scope}")
        src = field(t, "Sources taught")
        if src and not src.startswith("None"):
            out.append(f"  Sources: {src[:200]}{'...' if len(src) > 200 else ''}")
    return "\n".join(out) + "\n"


def owned(reused):
    """file= spans and chunk names INVENTORY.md lists for the reused chapters."""
    inv = open(os.path.join(OUTLINE, "INVENTORY.md")).read()
    fences, chunks = [], []
    for old in reused:
        m = re.search(rf"^\| {re.escape(old)} \|[^|]*\|[^|]*\|([^|]*)\|", inv, re.M)
        if m and m.group(1).strip():
            fences += [s.strip() for s in m.group(1).split(";") if s.strip()]
        m = re.search(rf"^- {re.escape(old)}: (.*)$", inv, re.M)
        if m:
            for group in m.group(1).split("; "):
                f, names = group.split(": ", 1)
                chunks += [(f, n.strip()) for n in names.split(",")]
    return fences, list(dict.fromkeys(chunks))


def chunk_blocks(reused, names):
    """name -> the exact fenced chunk blocks (all definitions) from the old chapters."""
    blocks = {}
    for old in reused:
        lines = open(os.path.join(BOOK, old)).read().split("\n")
        i = 0
        while i < len(lines):
            m = re.match(r"^```[A-Za-z0-9_-]*\s+chunk=(\S+)", lines[i])
            if m:
                j = i + 1
                while not lines[j].startswith("```"):
                    j += 1
                if m.group(1) in names:
                    blocks.setdefault(m.group(1), []).append(
                        f"<!-- from {old}, line {i + 1} -->\n" + "\n".join(lines[i:j + 1]))
                i = j
            i += 1
    return blocks


def main():
    if len(sys.argv) != 2 or not re.fullmatch(r"\d\d", sys.argv[1]):
        sys.exit("usage: tools/make-bundle.py NN")
    nn = sys.argv[1]
    sp = stub_path(nn)
    text = open(sp).read()
    out = os.path.join(BOOK, "bundles", nn)
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(os.path.join(out, "old"))
    os.makedirs(os.path.join(out, "source", "chunks"))
    shutil.copy(sp, os.path.join(out, "stub.md"))
    open(os.path.join(out, "spine.md"), "w").write(spine())
    shutil.copy(os.path.join(OUTLINE, "LEDGER.md"), os.path.join(out, "ledger.md"))

    pre = ["# Prerequisites: what the reader can already do", ""]
    for pnn in re.findall(r"\]\((\d\d)-[^)]*\.md\)", field(text, "Prerequisites")):
        _, pp, pt = next(s for s in stubs() if s[0] == pnn)
        paras = [x for x in field(pt, "Scope").split("\n\n") if x.strip()]
        pre += [f"## {pnn} {pt.splitlines()[0].lstrip('# ').strip()} (from its stub)", "",
                paras[-1] if paras else "(no scope)", ""]
    open(os.path.join(out, "prereqs.md"), "w").write("\n".join(pre))

    reused = list(dict.fromkeys(re.findall(r"\]\(\.\./([^)#]+\.md)\)", field(text, "Reuses"))))
    for old in reused:
        shutil.copy(os.path.join(BOOK, old), os.path.join(out, "old", old))

    paths = sorted(set(re.findall(r"`([\w./-]+/[\w.*-]+)`", field(text, "Sources taught"))))
    copied = []
    for rel in paths:
        for f in sorted(glob.glob(os.path.join(SRC, rel))):
            dest = os.path.join(out, "source", os.path.relpath(f, SRC))
            if os.path.isdir(f):
                shutil.copytree(f, dest, dirs_exist_ok=True)
            else:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy(f, dest)
            copied.append(os.path.relpath(f, SRC))

    fences, chunks = owned(reused)
    blocks = chunk_blocks(reused, {n for _, n in chunks})
    for name, bs in blocks.items():
        open(os.path.join(out, "source", "chunks", f"{name}.md"), "w").write("\n\n".join(bs) + "\n")
    own = [f"# Fences and chunks chapter {nn} owns (from book/outline/INVENTORY.md,",
           "# for the old chapters it reuses).  Claim nothing else.", ""]
    own += [f"file= {f}" for f in fences] or ["# file= fences: none"]
    own += [f"chunk= {n}  ({f})" for f, n in chunks] or ["# chunk= blocks: none"]
    open(os.path.join(out, "owns.txt"), "w").write("\n".join(own) + "\n")
    print(f"make-bundle: book/bundles/{nn}: stub, spine, ledger, prereqs, {len(reused)} old "
          f"chapter(s), {len(copied)} source path(s), {len(blocks)} chunk(s), "
          f"{len(fences)} fence span(s)")


main()
