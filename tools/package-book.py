#!/usr/bin/env python3
"""Package an existing mdBook render without bundling development directories.

Run after `mdbook build`: python3 tools/package-book.py [--output PATH]
The ZIP has fixed metadata, hashes every payload, records dirty provenance,
and checks freshness conservatively using source/output modification times.
It does not run mdBook or certify the book's independent verification suite.
"""

import argparse
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import stat
import subprocess
import tempfile
import tomllib
from urllib.parse import unquote, urlsplit
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FIXED_DATE = (1980, 1, 1, 0, 0, 0)
ARCHIVE_ROOT = "forth-bootstrap-book"
LICENSES = ("LICENSE", "LICENSE-CC-BY-4.0")
ASSET_SUFFIXES = {".css", ".js", ".png", ".svg", ".jpg", ".jpeg", ".gif", ".webp",
                  ".ico", ".woff", ".woff2", ".ttf", ".otf", ".eot", ".txt"}
LINK = re.compile(r"\]\(<?([^\s)>]+)>?(?:\s+[^)]*)?\)")
CSS_URL = re.compile(r"url\(\s*['\"]?([^'\"\s)]+)['\"]?\s*\)", re.I)
CSS_IMPORT = re.compile(r"@import\s+['\"]([^'\"]+)['\"]", re.I)
SEARCH_INDEX = re.compile(r"path_to_searchindex_js\s*=\s*['\"]([^'\"]+)['\"]")


class PackageError(ValueError):
    pass


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def local_target(origin, target):
    """Resolve a local URL without allowing an archive-root escape."""
    url = urlsplit(target)
    if url.scheme or url.netloc or not url.path:
        return None
    path = unquote(url.path)
    if path.startswith("/") or "\\" in path or "\0" in path:
        raise PackageError(f"non-portable local URL in {origin}: {target}")
    joined = posixpath.normpath(posixpath.join(posixpath.dirname(origin), path))
    if joined == ".." or joined.startswith("../") or joined == ".":
        raise PackageError(f"path escapes package in {origin}: {target}")
    return joined


def checked_path(base, relative):
    path = PurePosixPath(relative)
    if path.is_absolute() or any(p in ("..", ".") for p in path.parts) or "\\" in relative:
        raise PackageError(f"unsafe path: {relative}")
    candidate = base
    for ancestor in (candidate, *candidate.parents):
        if ancestor.is_symlink():
            raise PackageError(f"symlink is not a package input: {ancestor}")
    for part in path.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise PackageError(f"symlink is not a package input: {candidate}")
    if not candidate.is_file():
        raise PackageError(f"missing required file: {candidate}")
    if not stat.S_ISREG(candidate.stat().st_mode):
        raise PackageError(f"not a regular file: {candidate}")
    return candidate


class PageLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.targets = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "base":
            raise PackageError("HTML <base> cannot be used in this offline package")
        for name in ("href", "src", "poster"):
            target = attrs.get(name)
            if not target:
                continue
            url = urlsplit(target)
            resource = name != "href" or tag != "a"
            if resource and (url.netloc or url.scheme not in ("", "data")):
                raise PackageError(f"external resource prevents offline use: {target}")
            self.targets.append(target)
        if attrs.get("srcset"):
            raise PackageError("srcset requires explicit packaging support before publication")

    handle_startendtag = handle_starttag


def git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if result.returncode:
        raise PackageError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.rstrip("\n")


def provenance(root):
    indexed = git(root, "ls-files", "--stage", "--", "forth-bootstrap").split()
    if len(indexed) != 4 or indexed[0] != "160000" or indexed[2] != "0":
        raise PackageError("forth-bootstrap must be a pinned, conflict-free submodule")
    pin = indexed[1]
    source_root = root / "forth-bootstrap"
    if source_root.is_symlink():
        raise PackageError("forth-bootstrap checkout must not be a symlink")
    head = git(source_root, "rev-parse", "HEAD")
    if head != pin:
        raise PackageError("forth-bootstrap checkout differs from its indexed pin")
    book_status = git(root, "status", "--porcelain=v1", "--untracked-files=all")
    source_status = git(source_root, "status", "--porcelain=v1", "--untracked-files=no")
    return {
        "book": {"commit": git(root, "rev-parse", "HEAD"),
                 "dirty": bool(book_status), "status": book_status.splitlines()},
        "forth_bootstrap": {"pinned_commit": pin, "checkout_commit": head,
                            "tracked_dirty": bool(source_status),
                            "tracked_status": source_status.splitlines(),
                            "untracked_build_files": "not inspected or packaged"},
    }


def collect(root):
    """Collect only published pages and the resources they need."""
    config_path = checked_path(root, "book.toml")
    config = tomllib.loads(config_path.read_text())
    source_name = config.get("book", {}).get("src", "src")
    build_name = config.get("build", {}).get("build-dir", "book")
    for directory in (source_name, build_name):
        if (not isinstance(directory, str) or PurePosixPath(directory).is_absolute()
                or ".." in PurePosixPath(directory).parts or "\\" in directory):
            raise PackageError(f"unsafe configured directory: {directory}")
        if (root / directory).is_symlink():
            raise PackageError(f"symlink directory is not supported: {directory}")
    source = root / source_name
    build = root / build_name
    summary = checked_path(source, "SUMMARY.md")
    inputs = {"book.toml": config_path, f"{source_name}/SUMMARY.md": summary}
    pages = {}
    for target in LINK.findall(summary.read_text()):
        relative = local_target("SUMMARY.md", target)
        if relative is None or not relative.endswith(".md"):
            raise PackageError(f"SUMMARY must name local Markdown chapters: {target}")
        chapter = checked_path(source, relative)
        inputs[f"{source_name}/{relative}"] = chapter
        pages[str(PurePosixPath(relative).with_suffix(".html"))] = chapter
    if not pages:
        raise PackageError("SUMMARY has no published chapters")
    html_config = config.get("output", {}).get("html", {})
    custom = html_config.get("additional-css", []) + html_config.get("additional-js", [])
    for relative in custom:
        inputs[relative] = checked_path(root, relative)
    for relative in LICENSES:
        inputs[relative] = checked_path(root, relative)
    # Templates and other theme inputs can affect every rendered chapter.
    theme = root / "theme"
    if theme.is_symlink():
        raise PackageError("theme must not be a symlink")
    if theme.exists():
        for path in sorted(theme.rglob("*")):
            if path.is_symlink():
                raise PackageError(f"symlink theme input: {path}")
            if path.is_file():
                relative = path.relative_to(root).as_posix()
                inputs[relative] = checked_path(root, relative)
    global_inputs = [config_path, summary] + [p for name, p in inputs.items()
                                             if name.startswith("theme/") or name in custom]
    input_hashes = {name: sha256(path.read_bytes()) for name, path in sorted(inputs.items())}
    global_time = max(p.stat().st_mtime_ns for p in global_inputs)
    # mdBook's hosting-only 404 page has an absolute site-url <base>, so it
    # deliberately does not belong to the portable reading edition.
    required = set(pages) | {"index.html", "toc.html"}
    if html_config.get("print", {}).get("enable", True):
        required.add("print.html")
    newest_chapter = max(p.stat().st_mtime_ns for p in pages.values())
    for relative in sorted(required):
        page = checked_path(build, relative)
        needed = max(global_time, pages[relative].stat().st_mtime_ns if relative in pages
                     else newest_chapter)
        if page.stat().st_mtime_ns < needed:
            raise PackageError(f"stale render: {relative}; run mdbook build after editing")
    payload, pending = {}, set(required)
    while pending:
        relative = min(pending)
        pending.remove(relative)
        if relative in payload:
            continue
        suffix = PurePosixPath(relative).suffix.lower()
        if suffix == ".html" and relative not in required:
            raise PackageError(f"link reaches unpublished HTML: {relative}")
        if suffix != ".html" and suffix not in ASSET_SUFFIXES:
            raise PackageError(f"unsupported linked resource: {relative}")
        data = checked_path(build, relative).read_bytes()
        # mdBook copies manuscript assets at the same relative paths. Compare
        # their bytes, rather than trusting mtimes, and include them in source
        # provenance just like chapters and custom theme assets.
        source_asset = source / relative
        if suffix != ".html" and (source_asset.exists() or source_asset.is_symlink()):
            source_asset = checked_path(source, relative)
            expected = source_asset.read_bytes()
            if data != expected:
                raise PackageError(f"stale rendered manuscript asset: {relative}; run mdbook build")
            input_name = f"{source_name}/{relative}"
            inputs[input_name] = source_asset
            input_hashes[input_name] = sha256(expected)
        payload[relative] = data
        targets = []
        if suffix == ".html":
            text = data.decode("utf-8")
            parser = PageLinks()
            parser.feed(text)
            targets = parser.targets + SEARCH_INDEX.findall(text)
        elif suffix == ".css":
            text = data.decode("utf-8")
            targets = CSS_URL.findall(text) + CSS_IMPORT.findall(text)
            for target in targets:
                url = urlsplit(target)
                if url.netloc or url.scheme not in ("", "data"):
                    raise PackageError(f"external CSS resource prevents offline use: {target}")
        for target in targets:
            resolved = local_target(relative, target)
            if resolved is not None:
                pending.add(resolved)
    for relative in custom:
        expected = inputs[relative].read_bytes()
        p = PurePosixPath(relative)
        candidates = [name for name in payload if PurePosixPath(name).parent == p.parent
                      and (name == relative or
                           (PurePosixPath(name).name.startswith(p.stem + "-")
                            and PurePosixPath(name).suffix == p.suffix))]
        if not any(payload[name] == expected for name in candidates):
            raise PackageError(f"missing or stale rendered custom asset: {relative}")
    # A custom theme/book.js can replace mdBook's own book.js during rendering.
    # Catch that collision instead of shipping a reader without its core controls.
    core_scripts = [name for name in payload if re.fullmatch(r"book(?:-[\w]+)?\.js", name)]
    if len(core_scripts) != 1:
        raise PackageError("render must reference exactly one mdBook core book.js script")
    for relative in custom:
        if relative.endswith(".js") and payload[core_scripts[0]] == inputs[relative].read_bytes():
            raise PackageError("custom JavaScript replaced mdBook's core; rename the custom book.js")
    # mdBook's bundled font notices are not linked by their CSS, but must travel.
    if any(name.endswith((".woff", ".woff2", ".ttf", ".otf")) for name in payload):
        for notice in ("fonts/OPEN-SANS-LICENSE.txt", "fonts/SOURCE-CODE-PRO-LICENSE.txt"):
            payload[notice] = checked_path(build, notice).read_bytes()
    for relative in LICENSES:
        if relative in payload:
            raise PackageError(f"reserved package filename: {relative}")
        payload[relative] = inputs[relative].read_bytes()
    return payload, inputs, input_hashes, build, source


README = """forth-bootstrap — offline reading edition

Extract the entire ZIP, then open forth-bootstrap-book/index.html in a
browser. Keep the asset folders alongside the HTML pages. If your browser restricts local-file
scripts or search, run this from the extracted forth-bootstrap-book directory:

    python3 -m http.server 8000 --bind 127.0.0.1

Then open http://127.0.0.1:8000/ . Stop the server with Ctrl-C.
print.html is the continuous reading/printing edition. Links to external
references still need a network connection. The source repository, vendored
tools and runnable lab checkout are not included.

Copyright (c) 2026 Ben Sandbrook. Prose is CC BY 4.0; book code listings are
MIT. See LICENSE, LICENSE-CC-BY-4.0 and LICENSE.html. Bundled font notices
are in fonts/; other renderer asset notices remain in their original files.

MANIFEST.json records the book commit, whether the working tree was dirty,
the indexed forth-bootstrap pin, and SHA-256 hashes of manuscript/build
inputs and every package payload except the manifest itself. A dirty book
is a working edition, not a claim that the commit alone reproduces its text.
The manuscript digest covers the listed paths and their contents; timestamps
and machine-specific absolute paths are not part of that digest.

Packaging checks required pages, local referenced assets, manuscript and custom
asset contents, and source/output modification times. The timestamp check catches
ordinary stale renders; it cannot prove freshness after timestamps have
been preserved or rewritten. Package hashes identify the HTML actually
included. Packaging does not rerun source fidelity, link-anchor, numeric,
checkpoint, toolchain, or QEMU checks. Consult the edition's validation
record separately; do not infer those results from this archive's presence.

ZIP timestamps are fixed at 1980-01-01 for reproducibility, not build dates.
"""


def package(root, output):
    root, output = Path(root).absolute(), Path(output).absolute()
    # Reject output symlinks and symlink parents before creating directories.
    for path in (output, *output.parents):
        if path.is_symlink():
            raise PackageError(f"output path contains a symlink: {path}")
    payload, inputs, input_hashes, build, source = collect(root)
    if any(output.is_relative_to(p) for p in (build, source, root / "theme", root / "forth-bootstrap")):
        raise PackageError("output must be outside render, manuscript, theme and submodule directories")
    if output in inputs.values() or output.suffix.lower() != ".zip":
        raise PackageError("output must be a separate .zip file")
    info = provenance(root)
    if "README.txt" in payload or "MANIFEST.json" in payload:
        raise PackageError("README.txt and MANIFEST.json are reserved package filenames")
    payload["README.txt"] = README.encode()
    manifest = {"format_version": 1, **info,
                "manuscript_inputs_sha256": sha256(json_bytes(input_hashes)),
                "manuscript_inputs": input_hashes,
                "verification": {"packaging": "required pages, local assets, manuscript/custom asset contents, mtime freshness",
                                 "book_checks": "not run by packaging",
                                 "freshness_limit": "mtime checks cannot prove a content-to-render correspondence"},
                "files": {name: sha256(data) for name, data in sorted(payload.items())}}
    payload["MANIFEST.json"] = json_bytes(manifest)
    # A manuscript edited during collection must not acquire mismatched provenance.
    if input_hashes != {name: sha256(path.read_bytes()) for name, path in sorted(inputs.items())}:
        raise PackageError("manuscript inputs changed while packaging; rebuild and retry")
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".book-package-", suffix=".zip", dir=output.parent)
    try:
        with os.fdopen(fd, "w+b") as stream:
            with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
                for name, data in sorted(payload.items()):
                    entry = zipfile.ZipInfo(f"{ARCHIVE_ROOT}/{name}", date_time=FIXED_DATE)
                    entry.compress_type = zipfile.ZIP_DEFLATED
                    entry.create_system = 3
                    entry.external_attr = (stat.S_IFREG | 0o644) << 16
                    archive.writestr(entry, data, compresslevel=9)
        os.replace(temporary, output)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return len(payload), manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist/forth-bootstrap-book.zip")
    args = parser.parse_args(argv)
    try:
        count, manifest = package(ROOT, args.output)
    except (PackageError, OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        parser.exit(1, f"package-book: {exc}\n")
    state = "working edition (dirty tree)" if manifest["book"]["dirty"] else "clean tree"
    print(f"Packaged {count} files: {args.output} ({state})")
    print(f"Manuscript SHA-256: {manifest['manuscript_inputs_sha256']}")


if __name__ == "__main__":
    main()
