"""Text/structure contracts for diagrams; these do not replace rendered QA."""

from html.parser import HTMLParser
import importlib.util
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
BOOK = ROOT / "book"
SVG = "{http://www.w3.org/2000/svg}"
GRAPHICS = {
    "28": ("macro-scratch-lifetime", "generate_macro.py", "scratch"),
    "37": ("scope-storage", "draw_scope_storage.py", "slot"),
    "50": ("process-handoff", "generate_process.py", "wait"),
}


class Figure(HTMLParser):
    def __init__(self, markup):
        super().__init__()
        self.nodes = []
        self.stack = []
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        node = dict(tag=tag, attrs=dict(attrs), text="", parents=self.stack[:])
        self.nodes.append(node)
        if tag not in ("br", "img", "hr", "input", "link", "meta"):
            self.stack.append(node)

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1]["tag"] == tag:
            self.stack.pop()

    def handle_data(self, data):
        for node in self.stack:
            node["text"] += data

    def by_class(self, name):
        return [n for n in self.nodes if name in n["attrs"].get("class", "").split()]


def figures(chapter="*"):
    for path in sorted(BOOK.glob(f"{chapter}-*.md")):
        for markup in re.findall(r"<figure\b.*?</figure>", path.read_text(), re.S):
            yield Figure(markup)


class DiagramTests(unittest.TestCase):
    def test_all_mechanisms_have_named_text_captions(self):
        diagrams = list(figures())
        self.assertEqual(len(diagrams), 9)
        for diagram in diagrams:
            with self.subTest(caption=diagram.nodes[0]["attrs"].get("aria-labelledby")):
                caption_id = diagram.nodes[0]["attrs"]["aria-labelledby"]
                captions = [n for n in diagram.nodes if n["tag"] == "figcaption"
                            and n["attrs"].get("id") == caption_id]
                self.assertEqual(len(captions), 1)
                self.assertTrue(captions[0]["text"].strip())

    def test_svg_figures_have_local_images_descriptive_alt_and_fullsize_links(self):
        for chapter, (name, _, keyword) in GRAPHICS.items():
            with self.subTest(chapter=chapter):
                diagram, = figures(chapter)
                self.assertEqual(len(diagram.by_class("mechanism-graphic")), 1)
                viewport, = diagram.by_class("mechanism-graphic-viewport")
                self.assertEqual(viewport["attrs"]["tabindex"], "0")
                self.assertEqual(viewport["attrs"]["role"], "region")
                self.assertIn("scroll", viewport["attrs"]["aria-label"])
                image, = [n for n in diagram.nodes if n["tag"] == "img"]
                relative = f"images/mechanisms/{name}.svg"
                self.assertEqual(image["attrs"]["src"], relative)
                self.assertTrue((BOOK / relative).is_file())
                self.assertIn(keyword, image["attrs"]["alt"].lower())
                self.assertGreater(len(image["attrs"]["alt"].split()), 25)
                link, = diagram.by_class("mechanism-graphic-fullsize")
                self.assertEqual(link["attrs"]["href"], relative)
                self.assertIn("full-size", link["text"])
                root = ET.parse(BOOK / relative).getroot()
                dimensions = [float(v) for v in root.attrib["viewBox"].split()]
                self.assertEqual(int(image["attrs"]["width"]), dimensions[2])
                self.assertEqual(int(image["attrs"]["height"]), dimensions[3])
                caption, = [n for n in diagram.nodes if n["tag"] == "figcaption"]
                self.assertIn(keyword, caption["text"].lower())

    def test_svg_assets_are_valid_self_contained_and_have_text_equivalents(self):
        for name, _, _ in GRAPHICS.values():
            with self.subTest(figure=name):
                root = ET.parse(BOOK / f"images/mechanisms/{name}.svg").getroot()
                self.assertEqual(root.tag, SVG + "svg")
                for tag in ("title", "desc"):
                    nodes = root.findall(SVG + tag)
                    self.assertEqual(len(nodes), 1)
                    self.assertTrue(nodes[0].text.strip())
                self.assertTrue(root.findall(".//" + SVG + "text"))
                ids = [n.attrib["id"] for n in root.iter() if "id" in n.attrib]
                self.assertEqual(len(ids), len(set(ids)))
                for node in root.iter():
                    self.assertNotIn(node.tag, (SVG + "script", SVG + "foreignObject"))
                    for attr, value in node.attrib.items():
                        if attr.split("}")[-1] == "href":
                            self.assertTrue(value.startswith("#"), value)
                            self.assertIn(value[1:], ids)
                        for reference in re.findall(r"url\(([^)]+)\)", value):
                            self.assertTrue(reference.startswith("#"), reference)
                            self.assertIn(reference[1:], ids)
                for value in root.attrib.get("aria-labelledby", "").split():
                    self.assertIn(value, ids)

    def test_scope_answer_stays_inside_feedback_after_prediction(self):
        text = (BOOK / "37-functions-and-scope.md").read_text()
        image = text.index('src="images/mechanisms/scope-storage.svg"')
        opening = text.rfind("<details>", 0, image)
        self.assertGreater(opening, text.rfind("</details>", 0, image))
        self.assertIn("Feedback: reusable symbol rows, unreused core slots",
                      text[opening:image])
        self.assertGreater(opening, text.index("**Trace (moderate).**"))
        closing = text.index("</details>", image)
        self.assertLess(closing, text.index("**Trace (moderate), changed case.**"))
        self.assertLess(text.index("</figure>", image), closing)

    def reproduce(self, name, generator):
        with tempfile.TemporaryDirectory(prefix="book-figure-test-") as directory:
            output = Path(directory) / "figure.svg"
            subprocess.run([sys.executable, str(ROOT / "tools/figures" / generator),
                            str(output)], cwd=directory, check=True, capture_output=True)
            self.assertEqual(output.read_bytes(),
                             (BOOK / f"images/mechanisms/{name}.svg").read_bytes())

    def test_standard_library_macro_generator_is_reproducible(self):
        self.reproduce(*GRAPHICS["28"][:2])

    @unittest.skipUnless(importlib.util.find_spec("svgwrite"),
                         "optional svgwrite drawing dependency is not installed")
    def test_svgwrite_generators_are_reproducible(self):
        for chapter in ("37", "50"):
            with self.subTest(chapter=chapter):
                self.reproduce(*GRAPHICS[chapter][:2])

    def test_cached_register_is_outside_data_memory_rows(self):
        diagram = next(figures("04"))
        register, = diagram.by_class("stack-register")
        memory, = diagram.by_class("stack-memory")
        self.assertIn("CPU register", register["text"])
        self.assertIn("rdi", register["text"])
        self.assertIn("c · cached top", register["text"])
        self.assertNotIn(memory, register["parents"])
        rows = [n for n in diagram.by_class("memory-cell") if memory in n["parents"]]
        self.assertEqual([n["text"] for n in rows],
                         ["[rbp]b · second item", "[rbp + 8]a · older item"])
        self.assertNotIn("memory-cell", register["attrs"]["class"].split())

    def test_each_alias_contains_its_own_physical_destination(self):
        diagram = next(figures("54"))
        aliases, = diagram.by_class("diagram-aliases")
        routes = [n for n in diagram.nodes if n["parents"]
                  and n["parents"][-1] is aliases]
        self.assertEqual(len(routes), 2)
        for route, virtual in zip(routes, ("0x201234", "0xFFFF800000201234")):
            self.assertIn(virtual, route["text"])
            endpoints = [n for n in diagram.by_class("diagram-endpoint")
                         if route in n["parents"]]
            self.assertEqual(len(endpoints), 1)
            self.assertIn("Translates to", endpoints[0]["text"])
            self.assertIn("Physical byte 0x201234", endpoints[0]["text"])

    def test_alias_summary_keeps_identity_and_access_qualifications(self):
        diagram = next(figures("54"))
        result, = diagram.by_class("diagram-result")
        self.assertIn("supervisor-only", result["text"])
        self.assertIn("one physical byte, not two copies", result["text"])


if __name__ == "__main__":
    unittest.main()
