"""Dialect, DOM-copy fidelity and palette checks; no browser QA is implied."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[2]
NODE = shutil.which("node")
SCRIPT = ROOT / "theme/forth-highlight.js"
RUNNER = ROOT / "tools/tests/forth_highlight_runner.js"


def run_highlighter(**request):
    request["script"] = str(SCRIPT)
    result = subprocess.run([NODE, str(RUNNER)], input=json.dumps(request),
                            text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


def significant(tokens):
    return [(t["kind"], t["text"]) for t in tokens if t["text"].strip(" \t\r\n")]


@unittest.skipUnless(NODE, "Node.js is needed to execute the Forth highlighter")
class ForthHighlightTests(unittest.TestCase):
    def tokens(self, source):
        tokens = run_highlighter(sources=[source])["tokens"][0]
        self.assertEqual("".join(t["text"] for t in tokens), source)
        return significant(tokens)

    def test_definition_names_include_punctuation_and_digits(self):
        for word in ("2^63", "0<", "1+", "c,", "cc-parse-if", "[char]", "123", "<tag>"):
            with self.subTest(word=word):
                self.assertEqual(self.tokens(f": {word} [lit] 1 ;")[1], ("definition", word))

    def test_control_words_are_exact_and_case_sensitive(self):
        words = "if, else, then, begin, while, repeat, until, again, exit, branch 0branch"
        self.assertTrue(all(kind == "control" for kind, _ in self.tokens(words)))
        words = "if then cc-if, cc-parse-while begin,x IF, 0branch-xt cc-return 123 2^63"
        self.assertTrue(all(kind == "" for kind, _ in self.tokens(words)))

    def test_only_unsigned_ascii_decimal_lit_operands_are_numbers(self):
        for word in ("0", "00", "18446744073709551615", "18446744073709551616"):
            self.assertEqual(self.tokens(f"[lit] {word}")[-1], ("number", word))
        for word in ("-1", "+1", "0x41", "$41", "%101", "1.0", "1_000", "1e2", "１２", "1+", "2dup"):
            self.assertEqual(self.tokens(f"[lit] {word}")[-1], ("", word))
            self.assertNotIn(("number", word), self.tokens(word))

    def test_comments_are_whole_tokens_not_substrings(self):
        self.assertEqual(self.tokens("\\note (x) word\\tail (x"), [("", "\\note"), ("", "(x)"), ("", "word\\tail"), ("", "(x")])
        self.assertEqual(self.tokens("( a ( b )dup"), [("comment", "( a ( b )"), ("builtin", "dup")])
        self.assertEqual(self.tokens("( no close\n[lit] 9"), [("comment", "( no close\n[lit] 9")])

    def test_comment_line_end_and_crlf_preserve_the_next_line(self):
        for source in ("\\\n[lit] 1", "\\\r\n[lit] 1", "\\ [lit] 99\n[lit] 1"):
            self.assertEqual(self.tokens(source)[-2:], [("meta", "[lit]"), ("number", "1")])
        self.assertEqual(self.tokens("\\ ends at EOF"), [("comment", "\\ ends at EOF")])

    def test_only_seed_whitespace_splits_words(self):
        self.assertEqual(self.tokens("dup\u00a0drop dup\vdrop dup\fdrop"),
                         [("", "dup\u00a0drop"), ("", "dup\vdrop"), ("", "dup\fdrop")])
        self.assertEqual(self.tokens("dup\0[lit] 1"), [("builtin", "dup"), ("", "\0[lit] 1")])

    def test_comments_do_not_consume_pending_operands(self):
        self.assertEqual(self.tokens("[lit] \\ skip\n( stack ) 42")[-1], ("number", "42"))
        self.assertEqual(self.tokens("char ( ignored ) \\ ignored\n;")[-1], ("string", ";"))

    def test_real_string_readers_override_all_payload_syntax(self):
        for reader in ("s,", "kw,", "char", "token"):
            for word in ("char", "if,", "0", "'", "<stdin>", '"hello"', "x\\y"):
                self.assertEqual(self.tokens(f"{reader} {word}")[-1], ("string", word))
        self.assertEqual(self.tokens("kw, char kw, void"),
                         [("builtin", "kw,"), ("string", "char"), ("builtin", "kw,"), ("string", "void")])

    def test_standard_forth_quoted_strings_and_base_switches_are_not_invented(self):
        self.assertTrue(all(kind == "" for kind, _ in self.tokens('s" hello" ." hi" c" x" hex decimal [ ]')))

    def test_tick_is_and_binop_operands_are_references(self):
        self.assertEqual(self.tokens("' if, is later")[-1], ("reference", "later"))
        self.assertIn(("reference", "if,"), self.tokens("' if,"))
        self.assertEqual(self.tokens("cc-binop, * +")[-2:], [("reference", "*"), ("reference", "+")])

    def test_compiled_readers_do_not_steal_the_next_source_word(self):
        source = ": constant : push-body, [lit] 0 state ! ; : char ' drop tib c@ ; : copy s, bytes, ;"
        tokens = self.tokens(source)
        self.assertNotIn(("definition", "push-body,"), tokens)
        self.assertNotIn(("reference", "drop"), tokens)
        self.assertNotIn(("string", "bytes,"), tokens)
        self.assertIn(("builtin", "drop"), tokens)

    def test_char_semicolon_does_not_end_a_definition(self):
        tokens = self.tokens(": punctuation [char] ; s, dup ; create data s, 0")
        self.assertIn(("string", ";"), tokens)
        self.assertIn(("builtin", "dup"), tokens)
        self.assertIn(("definition", "data"), tokens)
        self.assertEqual(tokens[-1], ("string", "0"))

    def test_body_excerpt_then_next_definition(self):
        tokens = self.tokens("  [lit] 1 + ;\n: next [lit] 2 ;")
        self.assertIn(("definition", "next"), tokens)
        self.assertEqual(sum(kind == "definition" for kind, _ in tokens), 1)

    def test_definers_and_native_code_names(self):
        for reader in ("create", "variable", "constant", "defer", "code:"):
            self.assertEqual(self.tokens(f"{reader} 0<")[-1], ("definition", "0<"))
        self.assertEqual(self.tokens("' - code: - [lit] 195 c,")[-2:], [("number", "195"), ("builtin", "c,")])

    def test_dom_is_safe_exact_and_idempotent(self):
        source = ': <script>alert(1)</script>\t[lit] 123\r\n create x s, <img/onerror=bad>\n\\ & < > "\n'
        block = run_highlighter(blocks=[{"text": source}])["blocks"][0]
        self.assertEqual(block["text"], source)
        self.assertTrue(block["idempotent"])
        self.assertNotIn("<script>", block["html"])
        self.assertNotIn("<img/", block["html"])
        self.assertIn("&lt;script&gt;", block["html"])

    def test_only_tagged_forth_fences_change(self):
        blocks = [{"text": ": x ;"}, {"text": ": x ;", "pre": False},
                  {"text": "int x = 1;", "classes": "language-c"},
                  {"text": "echo hello", "classes": "language-sh"},
                  {"text": ": x ;", "classes": "language-text"}]
        results = run_highlighter(blocks=blocks)["blocks"]
        self.assertFalse(results[0]["unchanged"])
        self.assertTrue(all(b["unchanged"] for b in results[1:]))

    def test_keyboard_scrolling_is_only_added_when_needed(self):
        result = run_highlighter(blocks=[{"text": ": wide ;", "overflow": True}, {"text": ": short ;"}], resize=True)
        # Resizing back to no overflow removes the extra tab stop and label.
        self.assertEqual(result["resizedAttrs"], [{}, {}])
        overflow = run_highlighter(blocks=[{"text": ": wide ;", "overflow": True}])["blocks"][0]
        self.assertEqual(overflow["attrs"]["tabindex"], "0")
        self.assertEqual(overflow["attrs"]["role"], "region")

    def test_revealed_or_sidebar_resized_listings_gain_keyboard_access(self):
        result = run_highlighter(blocks=[{"text": ": newly-visible ;"},
                                        {"text": "int x;", "classes": "language-c"}], reveal=True)
        self.assertEqual(result["resizedAttrs"][0]["tabindex"], "0")
        self.assertEqual(result["resizedAttrs"][0]["role"], "region")
        self.assertEqual(result["resizedAttrs"][1], {})

    def test_every_real_forth_fence_preserves_all_characters(self):
        sources = []
        for page in (ROOT / "book").glob("*.md"):
            sources.extend(re.findall(r"^```forth[^\n]*\n(.*?)^```\s*$", page.read_text(), re.M | re.S))
        self.assertGreater(len(sources), 1000)
        result = run_highlighter(blocks=[{"text": s} for s in sources])
        for source, block in zip(sources, result["blocks"], strict=True):
            self.assertEqual(block["text"], source)
            self.assertTrue(block["idempotent"])
        self.assertGreater(max(len(s) for s in sources), 10000)


class ForthPaletteTests(unittest.TestCase):
    def test_both_palettes_meet_small_text_contrast(self):
        css = (ROOT / "theme/forth-highlight.css").read_text()
        def luminance(color):
            rgb = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
            rgb = [n / 12.92 if n <= .04045 else ((n + .055) / 1.055) ** 2.4 for n in rgb]
            return sum(n * w for n, w in zip(rgb, (.2126, .7152, .0722)))
        palettes = re.findall(r"--forth-background: #[0-9a-f]+;.*?--forth-builtin: #[0-9a-f]+;", css, re.S)
        self.assertEqual(len(palettes), 2)
        for palette in palettes:
            colors = dict(re.findall(r"--forth-([\w-]+): (#[0-9a-f]+);", palette))
            background = luminance(colors.pop("background"))
            for name, color in colors.items():
                value = luminance(color)
                contrast = (max(value, background) + .05) / (min(value, background) + .05)
                self.assertGreaterEqual(contrast, 4.5, (name, color, contrast))
        self.assertIn(".light, .rust", css)
        self.assertIn(".coal, .navy, .ayu", css)
        self.assertIn("font-weight: 700", css)
        self.assertIn("font-style: italic", css)
        self.assertIn("@media print", css)
        self.assertIn("white-space: pre-wrap", css)

    def test_local_assets_are_added_without_replacing_mdbook(self):
        config = tomllib.loads((ROOT / "book.toml").read_text())["output"]["html"]
        self.assertIn("theme/forth-highlight.css", config["additional-css"])
        self.assertIn("theme/forth-highlight.js", config["additional-js"])
        self.assertLess(config["additional-js"].index("theme/forth-highlight.js"),
                        config["additional-js"].index("theme/reader.js"))
        self.assertFalse((ROOT / "theme/highlight.js").exists())
        self.assertFalse((ROOT / "theme/book.js").exists())


if __name__ == "__main__":
    unittest.main()
