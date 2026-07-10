#!/usr/bin/env python3
"""Turn all 10 frames of the official Party Parrot GIF into COLR glyphs."""

from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen
from collections import Counter

from PIL import Image
from fontTools.fontBuilder import FontBuilder
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).parent
OUT = ROOT / "fonts"
SOURCE = "https://cultofthepartyparrot.com/parrots/hd/partyparrot.gif"
PUA = 0xE000
SCALE = 7


def rect(pen, x1, y1, x2, y2):
    pen.moveTo((x1, y1)); pen.lineTo((x2, y1)); pen.lineTo((x2, y2))
    pen.lineTo((x1, y2)); pen.closePath()


def frame_layers(image, frame_index, palette, glyphs):
    """Create one glyph per color, merging horizontal pixels into exact runs."""
    raw = image.convert("RGBA")
    counts = Counter(pixel[:3] for pixel in raw.getdata() if pixel[3] >= 128)
    anchors = [rgb for rgb, _ in counts.most_common(3)]
    rgba = Image.new("RGBA", raw.size)
    mapped = []
    for pixel in raw.getdata():
        if pixel[3] < 128:
            mapped.append((0, 0, 0, 0)); continue
        rgb = min(anchors, key=lambda c: sum((c[i] - pixel[i]) ** 2 for i in range(3)))
        mapped.append((*rgb, 255))
    rgba.putdata(mapped)
    by_color = {}
    for y in range(128):
        x = 0
        while x < 128:
            color = rgba.getpixel((x, y))
            if color[3] == 0:
                x += 1; continue
            end = x + 1
            while end < 128 and rgba.getpixel((end, y)) == color:
                end += 1
            by_color.setdefault(color, []).append((x, y, end))
            x = end

    layers = []
    for layer_index, (color, runs) in enumerate(by_color.items()):
        name = f"frame{frame_index}.color{layer_index}"
        pen = TTGlyphPen(None)
        # Join identical horizontal runs on adjacent rows. This is pixel-exact,
        # but avoids antialias seams between hundreds of one-pixel rectangles.
        active = {}
        merged = []
        for x1, y, x2 in runs:
            key = (x1, x2)
            if key in active and active[key][1] == y:
                active[key] = (active[key][0], y + 1)
            else:
                if key in active:
                    merged.append((x1, active[key][0], x2, active[key][1]))
                active[key] = (y, y + 1)
        for (x1, x2), (y1, y2) in active.items():
            merged.append((x1, y1, x2, y2))
        for x1, y1, x2, y2 in merged:
            left = 52 + x1 * SCALE; right = 52 + x2 * SCALE
            top = 948 - y1 * SCALE; bottom = 948 - y2 * SCALE
            rect(pen, left, bottom, right, top)
        glyphs[name] = pen.glyph()
        if color not in palette:
            palette[color] = len(palette)
        layers.append((name, palette[color]))
    return layers


def main():
    OUT.mkdir(exist_ok=True)
    data = urlopen(Request(SOURCE, headers={"User-Agent": "Mozilla/5.0"})).read()
    gif = Image.open(BytesIO(data))
    if gif.size != (128, 128) or gif.n_frames != 10:
        raise ValueError(f"Unexpected official GIF: {gif.size}, {gif.n_frames} frames")

    empty = TTGlyphPen(None).glyph()
    ligature_chars = "party_o"
    text_glyphs = {character: f"text.{character if character != '_' else 'underscore'}" for character in ligature_chars}
    glyphs = {".notdef": empty, ".null": empty, "space": empty, **{name: empty for name in text_glyphs.values()}}
    palette = {}
    colr = {}
    base_names = []
    for frame in range(gif.n_frames):
        gif.seek(frame)
        base = f"parrot.frame{frame}"
        base_names.append(base); glyphs[base] = empty
        colr[base] = frame_layers(gif, frame, palette, glyphs)

    # COLR v0 compatibility: early Windows implementations require glyph ID 1
    # to be .null (OpenType COLR specification recommendation).
    order = [".notdef", ".null", "space"] + list(text_glyphs.values()) + base_names + [n for n in glyphs if n not in {".notdef", ".null", "space", *text_glyphs.values(), *base_names}]
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(order); fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics({name: (1000 if name != "space" else 360, 0) for name in order})
    cmap = {ord("P"): base_names[0], 0x1F99C: base_names[0], 32: "space"}
    cmap.update({ord(character): glyph for character, glyph in text_glyphs.items()})
    cmap.update({PUA + i: name for i, name in enumerate(base_names)})
    fb.setupCharacterMap(cmap)
    fb.setupHorizontalHeader(ascent=1000, descent=0)
    fb.setupOS2(sTypoAscender=1000, sTypoDescender=0, usWinAscent=1000, usWinDescent=0)
    fb.setupNameTable({"familyName": "Party Parrot Official", "styleName": "Regular",
                       "uniqueFontIdentifier": "PartyParrotOfficialFrames-1.0",
                       "fullName": "Party Parrot Official Frames", "psName": "PartyParrotOfficialFrames"})
    fb.setupPost(); fb.setupMaxp(); fb.setupCOLR(colr, version=0)
    colors = [None] * len(palette)
    for rgba, index in palette.items():
        colors[index] = tuple(channel / 255 for channel in rgba)
    fb.setupCPAL([colors])
    addOpenTypeFeaturesFromString(fb.font, f"""
        languagesystem DFLT dflt;
        feature liga {{
            sub {' '.join(text_glyphs[c] for c in 'party')} by {base_names[0]};
            sub {' '.join(text_glyphs[c] for c in 'parrot')} by {base_names[0]};
            sub {' '.join(text_glyphs[c] for c in 'party_parrot')} by {base_names[0]};
        }} liga;
    """)

    ttf = OUT / "party-parrot-official.ttf"; fb.save(ttf)
    web = TTFont(ttf); web.flavor = "woff2"; web.save(OUT / "party-parrot-official.woff2")
    print(f"Built {gif.n_frames} exact GIF-frame glyphs with {len(colors)} colors")


if __name__ == "__main__":
    main()
