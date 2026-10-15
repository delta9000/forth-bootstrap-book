"""Source-color contrast checks for the three flat, self-contained SVG figures.

This is deliberately not a general SVG renderer or a WCAG certification. The
reviewed labels each sit on one surface: their baseline anchor identifies it.
Resolve that surface in paint order, checking every paint in a hatched pattern
and compositing opacity. Rendered review still checks label extents/occlusion.
Reject unsupported styling rather than silently ignoring it. No font, image,
browser, or optional drawing package is needed by the normal test suite.
"""

from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
FIGURES = ROOT / "book/images/mechanisms"
SVG = "{http://www.w3.org/2000/svg}"
NAMES = ("macro-scratch-lifetime", "scope-storage", "process-handoff")


def rgb(value):
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise AssertionError(f"Unsupported paint: {value}")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (1, 3, 5))


def composite(foreground, background, opacity):
    assert 0 <= opacity <= 1
    return tuple(f * opacity + b * (1 - opacity)
                 for f, b in zip(foreground, background))


def luminance(color):
    # WCAG's sRGB transfer function, not gamma-encoded RGB brightness.
    channels = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
                for c in color]
    return sum(c * weight for c, weight in zip(channels, (0.2126, 0.7152, 0.0722)))


def contrast(first, second):
    low, high = sorted((luminance(first), luminance(second)))
    return (high + 0.05) / (low + 0.05)


def alpha(node, paint):
    return float(node.get("opacity", "1")) * float(node.get(f"{paint}-opacity", "1"))


def polygon_contains(points, x, y):
    inside = False
    for (ax, ay), (bx, by) in zip(points, points[1:] + points[:1]):
        if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay):
            inside = not inside
    return inside


def path_points(value):
    # Filled paths in these figures are straight-sided files and arrowheads.
    tokens = re.findall(r"[A-Za-z]|[-+]?(?:\d*\.\d+|\d+)", value)
    points, current, command = [], (0., 0.), None
    while tokens:
        if tokens[0].isalpha():
            command = tokens.pop(0)
        if command in ("Z", "z"):
            break
        assert command in ("M", "m", "L", "l", "H", "h", "V", "v"), value
        x, y = current
        if command.upper() in ("M", "L"):
            nx, ny = float(tokens.pop(0)), float(tokens.pop(0))
            current = (x + nx, y + ny) if command.islower() else (nx, ny)
        elif command.upper() == "H":
            nx = float(tokens.pop(0))
            current = (x + nx if command.islower() else nx, y)
        else:
            ny = float(tokens.pop(0))
            current = (x, y + ny if command.islower() else ny)
        points.append(current)
    return points


def contains(node, x, y):
    tag = node.tag.removeprefix(SVG)
    if tag == "rect":
        left, top = float(node.get("x", 0)), float(node.get("y", 0))
        # Label anchors are safely inside the rounded corners, checked visually.
        return left <= x <= left + float(node.get("width")) and top <= y <= top + float(node.get("height"))
    if tag == "circle":
        return (x - float(node.get("cx"))) ** 2 + (y - float(node.get("cy"))) ** 2 <= float(node.get("r")) ** 2
    if tag == "polygon":
        values = [float(n) for n in re.findall(r"[-+]?(?:\d*\.\d+|\d+)", node.get("points"))]
        return polygon_contains(list(zip(values[::2], values[1::2])), x, y)
    if tag == "path":
        return polygon_contains(path_points(node.get("d")), x, y)
    raise AssertionError(f"Unsupported filled shape: {tag}")


class Scene:
    def __init__(self, root):
        self.root = root
        self.patterns = {n.get("id"): n for n in root.findall(f".//{SVG}pattern")}
        # Fail closed if generators start using inherited/CSS paints/transforms.
        for node in root.iter():
            assert not ({"style", "class", "transform", "filter", "mask", "clip-path",
                         "display", "visibility"} & node.attrib.keys())
            assert node.tag not in (SVG + "g", SVG + "style", SVG + "tspan", SVG + "use")
            if node.tag in (SVG + "svg", SVG + "defs", SVG + "pattern", SVG + "marker"):
                assert alpha(node, "fill") == alpha(node, "stroke") == 1
        self.nodes = [n for n in root if n.tag not in (SVG + "defs", SVG + "title", SVG + "desc")]
        paper = self.nodes[0]
        assert paper.tag == SVG + "rect" and alpha(paper, "fill") == 1
        assert float(paper.get("x", 0)) == float(paper.get("y", 0)) == 0
        _, _, width, height = map(float, root.get("viewBox").split())
        assert float(paper.get("width")) == width and float(paper.get("height")) == height
        self.paper = rgb(paper.get("fill"))

    def paints(self, value):
        if not value.startswith("url("):
            return {rgb(value)}
        match = re.fullmatch(r"url\(#([^)]+)\)", value)
        assert match and match[1] in self.patterns, value
        pattern = self.patterns[match[1]]
        base = pattern[0]
        assert base.tag == SVG + "rect" and alpha(base, "fill") == 1
        background = rgb(base.get("fill"))
        result = {background}
        for child in pattern:
            for paint in ("fill", "stroke"):
                color = child.get(paint, "none")
                if color != "none":
                    result.add(composite(rgb(color), background, alpha(child, paint)))
        return result

    def text_contrasts(self):
        previous = []
        for node in self.nodes:
            if node.tag == SVG + "text":
                # Just inside the start/end anchor, halfway up the lower case.
                offset = {"start": 1, "middle": 0, "end": -1}[node.get("text-anchor", "start")]
                x = float(node.get("x")) + offset
                y = float(node.get("y")) - 0.4 * float(node.get("font-size"))
                backgrounds = {self.paper}
                for shape in previous:
                    fill = shape.get("fill", "none")
                    if fill != "none" and contains(shape, x, y):
                        backgrounds = {composite(p, b, alpha(shape, "fill"))
                                       for p in self.paints(fill) for b in backgrounds}
                foreground = rgb(node.get("fill"))
                for background in backgrounds:
                    effective = composite(foreground, background, alpha(node, "fill"))
                    yield "".join(node.itertext()), contrast(effective, background)
            else:
                previous.append(node)

    def graphic_contrasts(self):
        # Conservative contract: every visible stroke / dark glyph against ALL
        # used light surface paints, even pairs that are not adjacent. Pattern
        # hatching is redundant with labels and history marks; it is a surface
        # paint here, not an essential glyph. Text against it is still checked.
        backgrounds = {self.paper}
        foregrounds = set()
        for node in self.nodes:
            if node.tag == SVG + "text":
                continue
            fill = node.get("fill", "none")
            if fill != "none":
                for color in self.paints(fill):
                    if luminance(color) > 0.5:
                        backgrounds.add(composite(color, self.paper, alpha(node, "fill")))
                    else:
                        foregrounds.add((color, alpha(node, "fill")))
            stroke = node.get("stroke", "none")
            if stroke != "none" and float(node.get("stroke-width", "1")) > 0:
                foregrounds.add((rgb(stroke), alpha(node, "stroke")))
        # Marker arrowheads are paints too; inspect their actual SVG definitions.
        for marker in self.root.findall(f".//{SVG}marker"):
            for node in marker:
                foregrounds.add((rgb(node.get("fill")), alpha(node, "fill")))
        for color, opacity in foregrounds:
            for background in backgrounds:
                yield contrast(composite(color, background, opacity), background)


class FigureContrastTests(unittest.TestCase):
    def test_wcag_reference_ratios_and_srgb_breakpoint(self):
        self.assertEqual(contrast(rgb("#000000"), rgb("#FFFFFF")), 21)
        self.assertAlmostEqual(contrast(rgb("#777777"), rgb("#FFFFFF")), 4.478089453577214)
        self.assertLess(contrast(rgb("#777777"), rgb("#FFFFFF")), 4.5)
        self.assertAlmostEqual(luminance((0.04045,) * 3), 0.04045 / 12.92)

    def test_all_actual_svg_text_paints_clear_4_5(self):
        for name in NAMES:
            root = ET.parse(FIGURES / f"{name}.svg").getroot()
            results = list(Scene(root).text_contrasts())
            self.assertGreaterEqual(len(results), len(root.findall(SVG + "text")))
            for label, ratio in results:
                with self.subTest(figure=name, label=label, ratio=ratio):
                    self.assertGreaterEqual(ratio, 4.5)

    def test_actual_graphic_paints_clear_3(self):
        for name in NAMES:
            ratios = list(Scene(ET.parse(FIGURES / f"{name}.svg").getroot()).graphic_contrasts())
            with self.subTest(figure=name):
                self.assertTrue(ratios)
                self.assertGreaterEqual(min(ratios), 3)

    def test_audit_detects_tinted_pattern_and_opacity_regressions(self):
        root = ET.parse(FIGURES / "macro-scratch-lifetime.svg").getroot()
        labels = root.findall(SVG + "text")
        kept = next(n for n in labels if n.text == "kept for scan")
        kept.set("fill", "#D16B26")
        self.assertLess(dict(Scene(root).text_contrasts())["kept for scan"], 3)
        reusable = next(n for n in labels if n.text == "reusable")
        reusable.set("fill", "#637585")
        ratios = [r for text, r in Scene(root).text_contrasts() if text == "reusable"]
        self.assertLess(min(ratios), 3.4)  # The hatch stroke, not merely paper.
        root = ET.parse(FIGURES / "process-handoff.svg").getroot()
        old_program = next(n for n in root.findall(SVG + "text")
                           if n.text == "controller" and n.get("y") == "904")
        old_program.set("opacity", "0.52")
        self.assertLess(min(r for text, r in Scene(root).text_contrasts()
                            if text == "controller"), 4.5)

    def test_scope_guides_are_behind_the_reserved_frame_label(self):
        nodes = list(ET.parse(FIGURES / "scope-storage.svg").getroot())
        label = next(n for n in nodes if n.tag == SVG + "text"
                     and n.text == "256 bytes reserved throughout")
        band = next(n for n in nodes if n.tag == SVG + "rect"
                    and n.get("x") == "150" and n.get("y") == "960")
        guides = [n for n in nodes if n.tag == SVG + "line"
                  and n.get("x1") == n.get("x2") and n.get("y1") == "942"]
        self.assertEqual(len(guides), 2)
        for guide in guides:
            self.assertLess(nodes.index(guide), nodes.index(band))
        self.assertLess(nodes.index(band), nodes.index(label))

    def test_audit_rejects_unhandled_inherited_styling(self):
        for attribute, value in (("opacity", "0.5"), ("fill-opacity", "0.5"),
                                 ("style", "opacity: 0.5"), ("visibility", "hidden")):
            root = ET.parse(FIGURES / "macro-scratch-lifetime.svg").getroot()
            root.set(attribute, value)
            with self.subTest(attribute=attribute), self.assertRaises(AssertionError):
                Scene(root)


if __name__ == "__main__":
    unittest.main()
