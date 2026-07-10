#!/usr/bin/env python3
"""Build a tiny variable font whose custom ANIM axis deforms every glyph."""

from math import sin, pi
from pathlib import Path

from fontTools.designspaceLib import AxisDescriptor, DesignSpaceDocument, SourceDescriptor
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.varLib import build as build_variable

ROOT = Path(__file__).parent
BUILD = ROOT / "build"
OUT = ROOT / "fonts"

# Seven-segment approximations. The deliberately mechanical alphabet makes the
# outline interpolation obvious and keeps every master perfectly compatible.
SEGMENTS = {
    "A": "abcefg", "B": "cdefg", "C": "adef", "D": "bcdeg",
    "E": "adefg", "F": "aefg", "G": "acdef", "H": "bcefg",
    "I": "bc", "J": "bcde", "K": "efg", "L": "def", "M": "abcef",
    "N": "abcef", "O": "abcdef", "P": "abefg", "Q": "abcdefg",
    "R": "abcefg", "S": "acdfg", "T": "deg", "U": "bcdef",
    "V": "bcdef", "W": "bcdef", "X": "bcefg", "Y": "bcdfg",
    "Z": "abdeg", "0": "abcdef", "1": "bc", "2": "abdeg",
    "3": "abcdg", "4": "bcfg", "5": "acdfg", "6": "acdefg",
    "7": "abc", "8": "abcdefg", "9": "abcdfg",
}

# x, y, width, height in font units.
BOXES = {
    "a": (150, 800, 500, 110), "b": (650, 470, 110, 330),
    "c": (650, 140, 110, 330), "d": (150, 30, 500, 110),
    "e": (40, 140, 110, 330), "f": (40, 470, 110, 330),
    "g": (150, 415, 500, 110),
}


def rect(pen, x, y, w, h):
    pen.moveTo((x, y)); pen.lineTo((x + w, y)); pen.lineTo((x + w, y + h))
    pen.lineTo((x, y + h)); pen.closePath()


def glyph_for(char, location):
    pen = TTGlyphPen(None)
    if char == "space":
        return pen.glyph()
    index = ord(char) if len(char) == 1 else 0
    t = location / 100.0
    for i, segment in enumerate("abcdefg"):
        x, y, w, h = BOXES[segment]
        active = segment in SEGMENTS.get(char, "abcdefg")
        # Inactive segments collapse to a 14-unit notch. They remain present so
        # all glyphs and all masters retain identical contour topology.
        if not active:
            w, h = (14, h) if w > h else (w, 14)
        wave = sin(t * 2 * pi + i * 0.88 + index * 0.21)
        dx = round(wave * (22 + i * 2))
        dy = round(sin(t * 2 * pi + i * 0.61 + index * 0.13) * 34)
        swell = round((wave + 1) * 10)
        rect(pen, x + dx - swell // 2, y + dy - swell // 2,
             max(8, w + swell), max(8, h + swell))
    return pen.glyph()


def make_master(path, location):
    glyph_order = [".notdef", "space"] + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    glyphs = {name: glyph_for(name if name != ".notdef" else "?", location) for name in glyph_order}
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics({name: (820 if name != "space" else 360, 20) for name in glyph_order})
    cmap = {ord(c): c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"}
    cmap.update({ord(c.lower()): c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"})
    cmap[32] = "space"
    fb.setupCharacterMap(cmap)
    fb.setupHorizontalHeader(ascent=950, descent=-100)
    fb.setupOS2(sTypoAscender=950, sTypoDescender=-100, usWinAscent=950, usWinDescent=100)
    fb.setupNameTable({"familyName": "Kinetic Seven", "styleName": "Regular",
                       "uniqueFontIdentifier": f"KineticSeven-{location}",
                       "fullName": "Kinetic Seven Regular", "psName": "KineticSeven-Regular"})
    fb.setupPost()
    fb.setupMaxp()
    fb.save(path)


def main():
    BUILD.mkdir(exist_ok=True); OUT.mkdir(exist_ok=True)
    locations = (0, 25, 50, 75, 100)
    masters = []
    for location in locations:
        path = BUILD / f"master-{location}.ttf"
        make_master(path, location)
        masters.append(path)

    designspace = DesignSpaceDocument()
    axis = AxisDescriptor()
    axis.name, axis.tag = "Animation", "ANIM"
    axis.minimum, axis.default, axis.maximum = 0, 0, 100
    designspace.addAxis(axis)
    for location, path in zip(locations, masters):
        source = SourceDescriptor()
        source.name = f"frame-{location}"
        source.path = str(path)
        source.location = {"Animation": location}
        source.copyInfo = source.copyLib = source.copyFeatures = location == 0
        designspace.addSource(source)
    ds_path = BUILD / "kinetic-seven.designspace"
    designspace.write(ds_path)

    variable, _, _ = build_variable(ds_path)
    ttf = OUT / "kinetic-seven-variable.ttf"
    variable.save(ttf)
    webfont = TTFont(ttf)
    webfont.flavor = "woff2"
    webfont.save(OUT / "kinetic-seven-variable.woff2")
    print(f"Built {ttf} and WOFF2 webfont")


if __name__ == "__main__":
    main()
