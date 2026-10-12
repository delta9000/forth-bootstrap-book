"""Execute focused reader-script contracts; no browser or visual QA is implied."""

import json
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]
NODE = shutil.which("node")


@unittest.skipUnless(NODE, "Node.js is needed to execute reader.js")
class ReaderInterfaceTests(unittest.TestCase):
    def test_listing_arrows_keep_native_defaults_and_do_not_reach_document(self):
        result = subprocess.run(
            [NODE, str(ROOT / "tools/tests/reader_keyboard_runner.js")],
            input=json.dumps({"script": str(ROOT / "theme/reader.js")}),
            text=True, capture_output=True, check=True,
        )
        checked = json.loads(result.stdout)
        self.assertGreater(checked["cases"], 100)
        self.assertFalse(checked["actualMdBook"])

    def search_description(self, description, *, field=True, header=True):
        """Supply only the search DOM; the manuscript enhancement exits early."""
        fixture = {
            "description": description,
            "field": field,
            "header": header,
            "script": str(ROOT / "theme/reader.js"),
        }
        result = subprocess.run(
            [NODE, "-e", """
const fs = require("node:fs");
const vm = require("node:vm");
const fixture = JSON.parse(fs.readFileSync(0, "utf8"));
const field = {
    attrs: {"aria-describedby": fixture.description},
    writes: 0,
    getAttribute(name) { return this.attrs[name] ?? null; },
    setAttribute(name, value) { this.attrs[name] = value; this.writes++; }
};
const header = {id: "mdbook-searchresults-header"};
const document = {
    getElementById(id) {
        if (id === "mdbook-searchbar") return fixture.field ? field : null;
        if (id === header.id) return fixture.header ? header : null;
        return null;
    },
    querySelector() { return null; }
};
vm.runInNewContext(fs.readFileSync(fixture.script, "utf8"), {document});
process.stdout.write(JSON.stringify({
    description: field.attrs["aria-describedby"], writes: field.writes
}));
"""], input=json.dumps(fixture), text=True, capture_output=True, check=True,
        )
        return json.loads(result.stdout)

    def test_pinned_template_description_resolves_to_the_results_header(self):
        self.assertEqual(self.search_description("searchresults-header"), {
            "description": "mdbook-searchresults-header", "writes": 1,
        })

    def test_newer_or_custom_template_descriptions_are_preserved(self):
        for description in ("mdbook-searchresults-header", "custom-help", None):
            with self.subTest(description=description):
                self.assertEqual(self.search_description(description), {
                    "description": description, "writes": 0,
                })

    def test_missing_search_controls_do_not_create_a_dangling_reference(self):
        for field, header in ((False, True), (True, False), (False, False)):
            with self.subTest(field=field, header=header):
                self.assertEqual(self.search_description(
                    "searchresults-header", field=field, header=header), {
                    "description": "searchresults-header", "writes": 0,
                })


if __name__ == "__main__":
    unittest.main()
