#!/usr/bin/env python3
"""Turn all 10 Party Parrot GIF frames into a linked COLR font family."""

from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen
from collections import Counter
from string import ascii_letters, digits, punctuation
from zipfile import ZIP_DEFLATED, ZipFile

from PIL import Image
from fontTools.fontBuilder import FontBuilder
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).parent
OUT = ROOT / "fonts"
SOURCE = "https://cultofthepartyparrot.com/parrots/hd/partyparrot.gif"
NOTO_SOURCE = "https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/Variable/TTF/Subset/NotoSansJP-VF.ttf"
NOTO_LICENSE = "https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/LICENSE"
PUA = 0xE000
SCALE = 7
FAMILY = "Party Parrot Frames"
HIRAGANA = "ぁあぃいぅうぇえぉおかがきぎくぐけげこござしじすずせぜそぞただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろゎわゐゑをんゔゕゖ"
KATAKANA = "ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポマミムメモャヤュユョヨラリルレロヮワヰヱヲンヴヵヶ"
JP_SYMBOLS = "、。・ー「」『』【】（）［］｛｝！？：；〜…‥〒※☆★○●◎々〆〄"
STYLES = (
    ("Regular", 0, 400, False, False, "regular"),
    ("Bold", 2, 700, True, False, "bold"),
    ("Italic", 7, 400, False, True, "italic"),
    ("Bold Italic", 5, 700, True, True, "bold-italic"),
)


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


def label_glyph(character, noto):
    pen = TTGlyphPen(None)
    source_name = noto.getBestCmap().get(ord(character))
    if source_name is None:
        return pen.glyph(), 0
    glyph_set = noto.getGlyphSet(location={"wght": 700})
    bounds_pen = BoundsPen(glyph_set)
    glyph_set[source_name].draw(bounds_pen)
    if bounds_pen.bounds is None:
        return pen.glyph(), 0
    x_min, y_min, x_max, y_max = bounds_pen.bounds
    scale = min(185 / max(1, x_max - x_min), 185 / max(1, y_max - y_min))
    # The character becomes the parrot's wing: embedded in the lower torso and
    # visually connected to the original black wing stroke.
    x = 385 - (x_min + x_max) * scale / 2
    y = 290 - (y_min + y_max) * scale / 2
    transformed = TransformPen(Cu2QuPen(pen, max_err=0.4, reverse_direction=False),
                               (scale, 0, 0, scale, x, y))
    recording = DecomposingRecordingPen(glyph_set)
    glyph_set[source_name].draw(recording)
    recording.replay(transformed)
    return pen.glyph(), round(x + x_min * scale)


def character_frame(character):
    lower = character.lower()
    if "a" <= lower <= "z":
        return (ord(lower) - ord("a")) % 10
    japanese = HIRAGANA + KATAKANA + JP_SYMBOLS
    if character in japanese:
        return japanese.index(character) % 10
    if character.isdigit():
        return int(character) % 10
    return ord(character) % 10


def build_sources(gif, noto):
    empty = TTGlyphPen(None).glyph()
    preview_chars = ascii_letters + digits + punctuation + HIRAGANA + KATAKANA + JP_SYMBOLS
    text_glyphs = {character: f"text.u{ord(character):04X}" for character in preview_chars}
    label_glyphs = {character: f"label.u{ord(character):04X}" for character in preview_chars}
    label_data = {character: label_glyph(character, noto) for character in preview_chars}
    glyphs = {".notdef": empty, ".null": empty, "space": empty,
              **{name: empty for name in text_glyphs.values()},
              **{name: label_data[character][0] for character, name in label_glyphs.items()}}
    label_lsbs = {name: label_data[character][1] for character, name in label_glyphs.items()}
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
    order = [".notdef", ".null", "space"] + list(text_glyphs.values()) + list(label_glyphs.values()) + base_names + [n for n in glyphs if n not in {".notdef", ".null", "space", *text_glyphs.values(), *label_glyphs.values(), *base_names}]
    black = min(palette, key=lambda color: sum(color[:3]))
    colors = [None] * len(palette)
    for rgba, index in palette.items():
        colors[index] = tuple(channel / 255 for channel in rgba)
    return glyphs, text_glyphs, label_glyphs, label_lsbs, base_names, colr, order, colors, palette[black]


def build_style(style_name, preview_frame, weight, bold, italic, suffix, sources):
    glyphs, text_glyphs, label_glyphs, label_lsbs, base_names, frame_colr, order, colors, black_index = sources
    colr = dict(frame_colr)
    for character, glyph in text_glyphs.items():
        frame = (character_frame(character) + preview_frame) % len(base_names)
        layers = frame_colr[base_names[frame]]
        # A black character-shaped wing becomes part of the body marking rather
        # than a white label floating over the illustration.
        colr[glyph] = layers + [(label_glyphs[character], black_index)]
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(order); fb.setupGlyf(glyphs)
    metrics = {name: (1000 if name != "space" else 360, label_lsbs.get(name, 0)) for name in order}
    fb.setupHorizontalMetrics(metrics)
    cmap = {0x1F99C: base_names[preview_frame], 32: "space"}
    cmap.update({ord(character): glyph for character, glyph in text_glyphs.items()})
    cmap.update({PUA + i: name for i, name in enumerate(base_names)})
    fb.setupCharacterMap(cmap)
    fb.setupHorizontalHeader(ascent=1000, descent=0)
    fs_selection = (0x20 if bold else 0) | (0x01 if italic else 0) | (0x40 if not bold and not italic else 0)
    fb.setupOS2(sTypoAscender=1000, sTypoDescender=0, usWinAscent=1000, usWinDescent=0,
                usWeightClass=weight, fsSelection=fs_selection)
    ps_style = style_name.replace(" ", "")
    fb.setupNameTable({"familyName": FAMILY, "styleName": style_name,
                       "uniqueFontIdentifier": f"PartyParrotFrames-{ps_style}-1.0",
                       "fullName": f"{FAMILY} {style_name}", "psName": f"PartyParrotFrames-{ps_style}",
                       "licenseDescription": "This font includes modified Noto Sans JP outlines under the SIL Open Font License 1.1. See the bundled notices.",
                       "licenseInfoURL": "https://openfontlicense.org"})
    fb.setupPost(italicAngle=-12 if italic else 0); fb.setupMaxp(); fb.setupCOLR(colr, version=0)
    fb.font["head"].macStyle = (1 if bold else 0) | (2 if italic else 0)
    fb.setupCPAL([colors])
    addOpenTypeFeaturesFromString(fb.font, f"""
        languagesystem DFLT dflt;
        feature liga {{
            sub {' '.join(text_glyphs[c] for c in 'party')} by {base_names[preview_frame]};
            sub {' '.join(text_glyphs[c] for c in 'parrot')} by {base_names[preview_frame]};
            sub {' '.join(text_glyphs[c] for c in 'party_parrot')} by {base_names[preview_frame]};
        }} liga;
    """)

    ttf = OUT / f"party-parrot-frames-{suffix}.ttf"; fb.save(ttf)
    web = TTFont(ttf); web.flavor = "woff2"; web.save(OUT / f"party-parrot-frames-{suffix}.woff2")
    return ttf


def main():
    OUT.mkdir(exist_ok=True)
    data = urlopen(Request(SOURCE, headers={"User-Agent": "Mozilla/5.0"})).read()
    noto_data = urlopen(Request(NOTO_SOURCE, headers={"User-Agent": "Mozilla/5.0"})).read()
    noto_license = urlopen(Request(NOTO_LICENSE, headers={"User-Agent": "Mozilla/5.0"})).read()
    gif = Image.open(BytesIO(data))
    if gif.size != (128, 128) or gif.n_frames != 10:
        raise ValueError(f"Unexpected source GIF: {gif.size}, {gif.n_frames} frames")
    sources = build_sources(gif, TTFont(BytesIO(noto_data)))
    ttfs = [build_style(*style, sources) for style in STYLES]
    with ZipFile(OUT / "party-parrot-frames-family.zip", "w", ZIP_DEFLATED) as archive:
        for ttf in ttfs:
            archive.write(ttf, ttf.name)
        archive.write(ROOT / "PARTY_PARROT_LICENSE.md", "THIRD_PARTY_NOTICES.md")
        archive.writestr("OFL-1.1.txt", noto_license)
    print(f"Built {len(ttfs)} linked styles from {gif.n_frames} GIF frames")


if __name__ == "__main__":
    main()
