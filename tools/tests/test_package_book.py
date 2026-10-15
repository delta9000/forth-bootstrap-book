"""Offline publication checks against tiny real Git/mdBook-shaped fixtures."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile

SPEC = importlib.util.spec_from_file_location(
    "package_book", Path(__file__).resolve().parents[1] / "package-book.py")
pkg = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pkg)


class PackageBookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="book-package-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / "dist/book.zip"
        self.write(".gitignore", "docs/\ndist/\n")
        self.write("book.toml", '[book]\nsrc="book"\n[build]\nbuild-dir="docs"\n'
                   '[output.html]\nadditional-css=["theme/reader.css"]\n'
                   'additional-js=["theme/reader.js"]\n')
        self.write("book/SUMMARY.md", "# Summary\n\n- [Intro](intro.md)\n")
        self.write("book/intro.md", "# Intro\n\nA reading edition.\n")
        self.write("theme/reader.css", "body { color: black }\n")
        self.write("theme/reader.js", "/* custom reader */\n")
        for name in pkg.LICENSES:
            self.write(name, f"License text for {name}\n")
        self.page = ('<!DOCTYPE html><html><head>'
                     '<link rel="stylesheet" href="theme/reader-123.css">'
                     '<script src="book-456.js"></script>'
                     '<script src="theme/reader-789.js"></script>'
                     '<script>window.path_to_searchindex_js="searchindex-abc.js";</script>'
                     '</head><body><a href="intro.html#intro">Intro</a></body></html>')
        for name in ("intro.html", "index.html", "toc.html", "404.html", "print.html"):
            self.write("docs/" + name, self.page)
        self.write("docs/theme/reader-123.css", (self.root / "theme/reader.css").read_text())
        self.write("docs/theme/reader-789.js", (self.root / "theme/reader.js").read_text())
        self.write("docs/book-456.js", "/* mdBook core */\n")
        self.write("docs/searchindex-abc.js", "{}\n")
        self.write("docs/bundles/private.fth", "DO NOT DISTRIBUTE\n")
        self.write("docs/outline/old.html", "Unpublished\n")
        self.write("forth-bootstrap/source.fth", "seed source\n")
        self.git(self.root / "forth-bootstrap", "init", "-q")
        self.git(self.root / "forth-bootstrap", "add", "source.fth")
        self.git(self.root / "forth-bootstrap", "commit", "-qm", "source fixture")
        pin = self.git(self.root / "forth-bootstrap", "rev-parse", "HEAD").strip()
        self.git(self.root, "init", "-q")
        self.git(self.root, "add", ".gitignore", "book.toml", "book", "theme", *pkg.LICENSES)
        self.git(self.root, "update-index", "--add", "--cacheinfo", f"160000,{pin},forth-bootstrap")
        self.git(self.root, "commit", "-qm", "book fixture")
        self.fresh()

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def git(self, root, *args):
        return subprocess.check_output(
            ["git", "-C", str(root), "-c", "user.name=Book Test", "-c",
             "user.email=book-test@example.invalid", "-c", "commit.gpgsign=false", *args],
            text=True, stderr=subprocess.PIPE)

    def fresh(self):
        for name in ("book.toml", "book/SUMMARY.md", "book/intro.md",
                     "theme/reader.css", "theme/reader.js", *pkg.LICENSES):
            os.utime(self.root / name, ns=(1_000_000_000, 1_000_000_000))
        for path in (self.root / "docs").rglob("*"):
            if path.is_file():
                os.utime(path, ns=(2_000_000_000, 2_000_000_000))

    def build(self):
        return pkg.package(self.root, self.output)

    def add_svg_figure(self, name="scope-storage"):
        relative = f"images/mechanisms/{name}.svg"
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 80">'
               f'<title>{name}</title><text x="10" y="40">Mechanism</text></svg>\n')
        self.write("book/" + relative, svg)
        self.write("docs/" + relative, svg)
        figure = (f'<figure><img src="{relative}" alt="Mechanism diagram">'
                  '<figcaption>How the mechanism works.</figcaption></figure>')
        chapter = self.root / "book/intro.md"
        chapter.write_text(chapter.read_text() + "\n" + figure + "\n")
        for name in ("intro.html", "index.html", "print.html"):
            page = self.root / "docs" / name
            page.write_text(page.read_text().replace("</body>", figure + "</body>"))
        self.fresh()
        return relative

    def test_archive_is_reproducible_self_identifying_and_excludes_working_files(self):
        count, manifest = self.build()
        first = self.output.read_bytes()
        self.build()
        self.assertEqual(first, self.output.read_bytes())
        self.assertFalse(manifest["book"]["dirty"])
        self.assertEqual(manifest["forth_bootstrap"]["pinned_commit"],
                         manifest["forth_bootstrap"]["checkout_commit"])
        with zipfile.ZipFile(self.output) as archive:
            self.assertEqual(len(archive.infolist()), count)
            self.assertEqual(archive.namelist(), sorted(archive.namelist()))
            self.assertNotIn("forth-bootstrap-book/bundles/private.fth", archive.namelist())
            self.assertNotIn("forth-bootstrap-book/outline/old.html", archive.namelist())
            for info in archive.infolist():
                self.assertTrue(info.filename.startswith("forth-bootstrap-book/"))
                self.assertEqual(info.date_time, pkg.FIXED_DATE)
            for name, digest in manifest["files"].items():
                self.assertEqual(pkg.sha256(archive.read("forth-bootstrap-book/" + name)), digest)
            recorded = json.loads(archive.read("forth-bootstrap-book/MANIFEST.json"))
            self.assertEqual(recorded, manifest)
            self.assertIn("theme/reader-789.js", manifest["files"])

    def test_dirty_manuscript_is_identified_by_content_and_not_only_commit(self):
        _, before = self.build()
        self.write("book/intro.md", "# Intro\n\nAn edited working edition.\n")
        self.fresh()
        _, after = self.build()
        self.assertTrue(after["book"]["dirty"])
        self.assertEqual(before["book"]["commit"], after["book"]["commit"])
        self.assertNotEqual(before["manuscript_inputs_sha256"], after["manuscript_inputs_sha256"])

    def test_missing_published_page_fails_before_replacing_existing_archive(self):
        self.output.parent.mkdir()
        self.output.write_bytes(b"keep this prior archive")
        (self.root / "docs/intro.html").unlink()
        with self.assertRaisesRegex(pkg.PackageError, "missing required file"):
            self.build()
        self.assertEqual(self.output.read_bytes(), b"keep this prior archive")

    def test_missing_dynamic_search_index_fails(self):
        (self.root / "docs/searchindex-abc.js").unlink()
        with self.assertRaisesRegex(pkg.PackageError, "missing required file"):
            self.build()

    def test_svg_figures_are_offline_payloads_and_manuscript_inputs(self):
        figures = [self.add_svg_figure(name) for name in
                   ("scope-storage", "macro-scratch-lifetime", "process-handoff")]
        self.write("docs/images/mechanisms/unpublished.svg", "not linked")
        _, manifest = self.build()
        first = self.output.read_bytes()
        self.build()
        self.assertEqual(first, self.output.read_bytes())
        with zipfile.ZipFile(self.output) as archive:
            for relative in figures:
                with self.subTest(relative=relative):
                    source = (self.root / "book" / relative).read_bytes()
                    self.assertEqual(archive.read("forth-bootstrap-book/" + relative), source)
                    self.assertEqual(manifest["files"][relative], pkg.sha256(source))
                    self.assertEqual(manifest["manuscript_inputs"]["book/" + relative],
                                     pkg.sha256(source))
            self.assertNotIn("images/mechanisms/unpublished.svg", manifest["files"])

    def test_missing_linked_svg_fails_before_replacing_existing_archive(self):
        relative = self.add_svg_figure()
        self.build()
        previous = self.output.read_bytes()
        (self.root / "docs" / relative).unlink()
        with self.assertRaisesRegex(pkg.PackageError, "missing required file"):
            self.build()
        self.assertEqual(self.output.read_bytes(), previous)

    def test_source_svg_change_is_detected_with_preserved_timestamps(self):
        relative = self.add_svg_figure()
        source = self.root / "book" / relative
        original_time = source.stat().st_mtime_ns
        source.write_text(source.read_text().replace("Mechanism", "Changed mechanism"))
        os.utime(source, ns=(original_time, original_time))
        self.fresh()
        with self.assertRaisesRegex(pkg.PackageError, "stale rendered manuscript asset"):
            self.build()

    def test_changed_svg_updates_manuscript_digest(self):
        relative = self.add_svg_figure()
        _, before = self.build()
        source = self.root / "book" / relative
        changed = source.read_text().replace("Mechanism", "Changed mechanism")
        self.write("book/" + relative, changed)
        self.write("docs/" + relative, changed)
        self.fresh()
        _, after = self.build()
        self.assertEqual(before["book"]["commit"], after["book"]["commit"])
        self.assertNotEqual(before["manuscript_inputs_sha256"], after["manuscript_inputs_sha256"])
        self.assertNotEqual(before["manuscript_inputs"]["book/" + relative],
                            after["manuscript_inputs"]["book/" + relative])

    def test_source_svg_symlinks_are_rejected(self):
        relative = self.add_svg_figure()
        source = self.root / "book" / relative
        source.unlink()
        source.symlink_to(self.root / "LICENSE")
        with self.assertRaisesRegex(pkg.PackageError, "symlink"):
            self.build()

    def test_css_dependencies_and_font_notices_are_included(self):
        css = '@font-face { src: url("../fonts/font.woff2") }\n'
        self.write("theme/reader.css", css)
        self.write("docs/theme/reader-123.css", css)
        self.write("docs/fonts/font.woff2", "font fixture")
        self.write("docs/fonts/OPEN-SANS-LICENSE.txt", "open sans notice")
        self.write("docs/fonts/SOURCE-CODE-PRO-LICENSE.txt", "source code pro notice")
        self.fresh()
        _, manifest = self.build()
        self.assertIn("fonts/font.woff2", manifest["files"])
        self.assertIn("fonts/OPEN-SANS-LICENSE.txt", manifest["files"])
        (self.root / "docs/fonts/font.woff2").unlink()
        with self.assertRaisesRegex(pkg.PackageError, "missing required file"):
            self.build()

    def test_newer_manuscript_and_configuration_each_require_rebuild(self):
        for name in ("book/intro.md", "book.toml"):
            with self.subTest(name=name):
                self.fresh()
                os.utime(self.root / name, ns=(3_000_000_000, 3_000_000_000))
                with self.assertRaisesRegex(pkg.PackageError, "stale render"):
                    self.build()

    def test_custom_assets_require_equal_rendered_contents(self):
        self.write("docs/theme/reader-789.js", "old custom reader")
        self.fresh()
        with self.assertRaisesRegex(pkg.PackageError, "missing or stale rendered custom asset"):
            self.build()

    def test_custom_book_js_cannot_silently_replace_mdbook_core(self):
        self.write("docs/book-456.js", (self.root / "theme/reader.js").read_text())
        self.fresh()
        with self.assertRaisesRegex(pkg.PackageError, "replaced mdBook's core"):
            self.build()

    def test_rendered_file_symlinks_are_rejected(self):
        (self.root / "docs/book-456.js").unlink()
        (self.root / "docs/book-456.js").symlink_to(self.root / "theme/reader.js")
        with self.assertRaisesRegex(pkg.PackageError, "symlink"):
            self.build()

    def test_rendered_directory_symlinks_are_rejected(self):
        (self.root / "docs/theme").rename(self.root / "rendered-theme")
        (self.root / "docs/theme").symlink_to(self.root / "rendered-theme", target_is_directory=True)
        with self.assertRaisesRegex(pkg.PackageError, "symlink"):
            self.build()

    def test_local_links_cannot_escape_archive_root(self):
        self.write("docs/index.html", self.page.replace("intro.html#intro", "../LICENSE"))
        self.fresh()
        with self.assertRaisesRegex(pkg.PackageError, "escapes package"):
            self.build()
        for target in ("%2e%2e/secret", "/absolute.css", "..\\secret"):
            with self.subTest(target=target), self.assertRaises(pkg.PackageError):
                pkg.local_target("index.html", target)

    def test_remote_references_are_allowed_but_remote_resources_are_not(self):
        self.write("docs/index.html", self.page.replace("intro.html#intro", "https://example.com/"))
        self.fresh()
        self.build()
        self.write("docs/index.html", self.page.replace("book-456.js", "https://example.com/script.js"))
        self.fresh()
        with self.assertRaisesRegex(pkg.PackageError, "external resource"):
            self.build()

    def test_output_cannot_be_inside_render_or_follow_symlink(self):
        with self.assertRaisesRegex(pkg.PackageError, "outside render"):
            pkg.package(self.root, self.root / "docs/output.zip")
        self.output.parent.mkdir()
        self.output.symlink_to(self.root / "LICENSE")
        with self.assertRaisesRegex(pkg.PackageError, "symlink"):
            self.build()
        self.assertEqual((self.root / "LICENSE").read_text(), "License text for LICENSE\n")

    def test_source_checkout_must_match_indexed_pin(self):
        self.write("forth-bootstrap/source.fth", "a different source revision")
        self.git(self.root / "forth-bootstrap", "add", "source.fth")
        self.git(self.root / "forth-bootstrap", "commit", "-qm", "advance source")
        with self.assertRaisesRegex(pkg.PackageError, "differs from its indexed pin"):
            self.build()

    def test_changed_tracked_source_is_visible_in_manifest(self):
        self.write("forth-bootstrap/source.fth", "uncommitted source change")
        _, manifest = self.build()
        self.assertTrue(manifest["forth_bootstrap"]["tracked_dirty"])
        self.assertTrue(manifest["book"]["dirty"])


if __name__ == "__main__":
    unittest.main()
