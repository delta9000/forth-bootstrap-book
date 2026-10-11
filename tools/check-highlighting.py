#!/usr/bin/env python3
"""Check the actual mdBook assets/order and every rendered Forth listing.

Executes mdBook's bundled syntax-highlighting section and our additional script
in a minimal DOM harness. Checks byte-for-byte text preservation, repeatability,
non-Forth isolation and source/render coverage. This is not browser/layout QA.
"""
import argparse
from collections import Counter
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


class RenderedCode(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.scripts = []
        self.styles = []
        self.blocks = []
        self.pre = 0
        self.current = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script" and attrs.get("src"):
            self.scripts.append(attrs["src"])
        if tag == "link" and attrs.get("rel") == "stylesheet":
            self.styles.append(attrs.get("href", ""))
        if tag == "pre":
            self.pre += 1
        if tag == "code" and self.pre:
            self.current = {"classes": attrs.get("class", ""), "text": ""}

    def handle_data(self, text):
        if self.current is not None:
            self.current["text"] += text

    def handle_endtag(self, tag):
        if tag == "code" and self.current is not None:
            self.blocks.append(self.current)
            self.current = None
        if tag == "pre":
            self.pre -= 1


def check(render):
    node = shutil.which("node")
    if not node:
        raise ValueError("Node.js is required to validate syntax highlighting")
    spec = importlib.util.spec_from_file_location("highlight_source", ROOT / "tools/check-tryit.py")
    source = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(source)
    pages = [Path(p) for p in source.published_files()]
    expected = []
    primary = []
    blocks = []
    highlighters = set()
    cores = set()
    for page in [p.with_suffix(".html").name for p in pages] + ["index.html", "print.html"]:
        path = render / page
        parser = RenderedCode()
        parser.feed(path.read_text())
        def asset(pattern, items):
            matches = [p for p in items if re.fullmatch(pattern, p)]
            if len(matches) != 1:
                raise ValueError(f"{page}: expected one {pattern}, found {matches}")
            target = matches[0]
            if urlsplit(target).scheme or target.startswith("/") or ".." in Path(target).parts:
                raise ValueError(f"{page}: nonlocal syntax asset {target}")
            if not (render / target).is_file():
                raise ValueError(f"{page}: missing asset {target}")
            return target
        hljs = asset(r"highlight-[a-f0-9]+\.js", parser.scripts)
        core = asset(r"book-[a-f0-9]+\.js", parser.scripts)
        custom = asset(r"theme/forth-highlight-[a-f0-9]+\.js", parser.scripts)
        reader = asset(r"theme/reader-[a-f0-9]+\.js", parser.scripts)
        stylesheet = asset(r"theme/forth-highlight-[a-f0-9]+\.css", parser.styles)
        if not [parser.scripts.index(x) for x in (hljs, core, custom, reader)] == sorted(parser.scripts.index(x) for x in (hljs, core, custom, reader)):
            raise ValueError(f"{page}: highlighting scripts are out of order")
        for actual, original in ((custom, "forth-highlight.js"), (stylesheet, "forth-highlight.css")):
            if (render / actual).read_bytes() != (ROOT / "theme" / original).read_bytes():
                raise ValueError(f"{page}: stale syntax asset {actual}")
        highlighters.add(hljs)
        cores.add(core)
        if page not in ("index.html", "print.html"):
            primary.extend(b["text"] for b in parser.blocks if "language-forth" in b["classes"].split())
        blocks.extend(parser.blocks)
    for page in pages:
        expected.extend(re.findall(r"^```forth[^\n]*\n(.*?)^```\s*$", page.read_text(), re.M | re.S))
    if Counter(primary) != Counter(expected):
        raise ValueError("Forth fence text/coverage differs between published source and HTML")
    if len(highlighters) != 1 or len(cores) != 1:
        raise ValueError("render mixes different versions of mdBook assets")
    # Include deliberate tabs/CRLF, inline Forth and injection-shaped text next
    # to the actual pages, with the bundled highlighter active first.
    probes = [
        {"classes": "language-forth", "text": ': <script>\t[lit] 42\r\n ;\n'},
        {"classes": "language-forth", "text": ': inline ;', "pre": False},
        {"classes": "language-c", "text": 'int main(void) { return 0; }\n'},
        {"classes": "language-sh", "text": 'printf "%s\\n" hello\n'},
    ]
    blocks.extend(probes)
    result = subprocess.run([node, str(ROOT / "tools/tests/forth_highlight_runner.js")],
        input=json.dumps({"script": str(ROOT / "theme/forth-highlight.js"),
                          "bundled": str(render / next(iter(highlighters))),
                          "book": str(render / next(iter(cores))),
                          "blocks": blocks, "summary": True}),
        capture_output=True, text=True, check=True)
    results = json.loads(result.stdout)
    forth = others = spans = 0
    for block, checked in zip(blocks, results["blocks"], strict=True):
        if not checked["textPreserved"] or not checked["idempotent"]:
            raise ValueError("DOM highlighter changed text or produced non-idempotent markup")
        if "language-forth" in block["classes"].split() and block.get("pre", True):
            forth += 1
            spans += checked["spans"]
        else:
            others += 1
            if not checked["unchanged"]:
                raise ValueError("Forth highlighter changed another language or inline code")
    if spans == 0:
        raise ValueError("No syntax spans were produced")
    print(f"highlighting: {len(expected)} published Forth fences match HTML; "
          f"{forth} DOM listings checked including print/index and probes; "
          f"{others} other/inline blocks unchanged; {spans} syntax spans")
    print(f"highlighting: mdBook bundled hljs {results['bundledVersion']}, "
          "local assets/load order, exact copied text and repeat highlighting PASS")
    print("highlighting: browser pixels, mobile layout, printed pages and screen-reader use NOT CHECKED")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, default=ROOT / "docs")
    args = parser.parse_args()
    try:
        check(args.html.resolve())
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"highlighting: {error}", file=sys.stderr)
        sys.exit(1)
