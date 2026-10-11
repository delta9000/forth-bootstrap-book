"""Text/structure contracts for diagrams; these do not replace rendered QA."""

from html.parser import HTMLParser
from pathlib import Path
import re
import unittest


BOOK = Path(__file__).resolve().parents[2] / "book"


class Figure(HTMLParser):
    def __init__(self, markup):
        super().__init__()
        self.nodes = []
        self.stack = []
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        node = dict(tag=tag, attrs=dict(attrs), text="", parents=self.stack[:])
        self.nodes.append(node)
        if tag != "br":
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
        self.assertEqual(len(diagrams), 6)
        for diagram in diagrams:
            with self.subTest(caption=diagram.nodes[0]["attrs"].get("aria-labelledby")):
                caption_id = diagram.nodes[0]["attrs"]["aria-labelledby"]
                captions = [n for n in diagram.nodes if n["tag"] == "figcaption"
                            and n["attrs"].get("id") == caption_id]
                self.assertEqual(len(captions), 1)
                self.assertTrue(captions[0]["text"].strip())

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
