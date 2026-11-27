"""Builds MoodyFin's Funnel Sans files for Kodi (run with fontTools installed):

    python build_fonts.py <FunnelSans[wght].ttf> <NotoSansSymbols2-Regular.ttf> <skin fonts folder>

- Kodi can't pick a weight from a variable font (it shows the default, 300), so this cuts static
  Regular/Medium/SemiBold/Bold (400/500/600/700) instances.
- Funnel Sans has no U+2605 BLACK STAR (used in "Sci-Fi • ★ 8.3"); it is copied in from Noto Sans Symbols 2.
Both fonts are SIL OFL 1.1 without Reserved Font Names, so modified copies may keep their names.
Sources: github.com/google/fonts ofl/funnelsans and ofl/notosanssymbols2.
"""
import sys

from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

STAR = 0x2605
WEIGHTS = [("Regular", 400), ("Medium", 500), ("SemiBold", 600), ("Bold", 700)]


def add_star(font, symbols):
    src_name = symbols.getBestCmap()[STAR]
    rec = DecomposingRecordingPen(symbols.getGlyphSet())
    symbols.getGlyphSet()[src_name].draw(rec)
    scale = font["head"].unitsPerEm / symbols["head"].unitsPerEm * 0.82  # a touch smaller than the cap height
    src_adv, _ = symbols["hmtx"][src_name]
    pen = TTGlyphPen(None)
    # scale, and lift it a little so it sits on the text's x-height centre
    rec.replay(TransformPen(pen, (scale, 0, 0, scale, 0, font["head"].unitsPerEm * 0.02)))
    glyph = pen.glyph()
    name = "uni2605"
    font["glyf"][name] = glyph
    if name not in font.getGlyphOrder():
        font.setGlyphOrder(font.getGlyphOrder() + [name])
    glyph.recalcBounds(font["glyf"])
    font["hmtx"][name] = (int(src_adv * scale), glyph.xMin if hasattr(glyph, "xMin") else 0)
    for table in font["cmap"].tables:
        if table.isUnicode():
            table.cmap[STAR] = name
    font["maxp"].numGlyphs = len(font.getGlyphOrder())


def main(vf_path, symbols_path, out_dir):
    symbols = TTFont(symbols_path)
    for style, weight in WEIGHTS:
        font = instantiateVariableFont(TTFont(vf_path), {"wght": weight}, updateFontNames=False)
        for rec in font["name"].names:
            if rec.nameID in (2, 17):
                rec.string = style
            elif rec.nameID == 4:
                rec.string = "Funnel Sans " + style
            elif rec.nameID == 6:
                rec.string = "FunnelSans-" + style
        add_star(font, symbols)
        if "post" in font:
            font["post"].formatType = 3.0  # no glyph names table to keep in sync
        out = "%s/FunnelSans-%s.ttf" % (out_dir, style)
        font.save(out)
        print("wrote", out)


if __name__ == "__main__":
    main(*sys.argv[1:4])
