"""Writes MoodyFin's hover card includes (the Jellyfin theme's hover preview) into skin.moodyfin/xml/Includes_MoodyFin.xml,
between <!-- MFPopup:begin --> and <!-- MFPopup:end -->.

A Kodi list clips whatever its items draw outside their slot, so the card is a control of its own, placed after the
list (same left/top as the list) and moved over the focused poster with one conditional slide per visible position:
  MFPopupRow / MFPopupRowTop10  (horizontal lists)  x from Container(list).Position
  MFPopupGrid                   (poster panel)      x from Container(list).Column, y from Container(list).Row
It shows after a second without a key press (System.IdleTime(1)) plus a 0.2 s fade, for movies and shows.

The card follows the Jellyfin theme's web-src/js/35-hover-preview.js: #18181b, radius 12, 16:9 backdrop fading into the card,
logo (max 62 % wide, 64 tall) or the title in Bebas 30 px; then (the Jellyfin theme's 38 px buttons left out: a remote
can't reach them without breaking the row's left/right)
rating (accent) . year . length . age rating in SemiBold 13 px at 90 % white, genres in Medium 13 px at 72 % white,
padding 12 / 14. Theme px are about skin units here (their posters ~188 px, ours 190); text is a px or two larger
for a TV (fonts mf_heading32, mf_card_meta 15, mf_card_genre 15, mf_card_badge 12).

    python build_popup.py
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
INCLUDES = os.path.join(HERE, "..", "skin.moodyfin", "xml", "Includes_MoodyFin.xml")

ITEM_W = 206        # poster slot (190 poster + 16 gap); cards sit 4 px in
POSTER_W, POSTER_H = 190, 285
CARD_W = 336
IMG_H = CARD_W * 9 // 16            # 189
META_Y = IMG_H + 14                 # rating . year . length . age (no buttons: a remote can't reach them)
GENRE_Y = META_Y + 22 + 8           # genres
CARD_H = GENRE_Y + 22 + 14
ROW_H = 390         # poster grid row height
GRID_MAX_Y = 530    # lowest the card goes in the grid (relative to the panel's top), so it stays on screen
SLOTS = 12          # positions / columns handled
GRID_ROWS = 4


def card_x(n):
    return n * ITEM_W + 4 + POSTER_W // 2 - CARD_W // 2


def card_y():
    return 4 + POSTER_H // 2 - CARD_H // 2


def slide(x, y, cond):
    return ('\t\t\t\t<animation effect="slide" end="%d,%d" time="0" condition="%s">Conditional</animation>\n'
            % (x, y, cond))


def meta_label(label, visible=None, color="E6FFFFFF"):
    vis = "\n\t\t\t\t\t<visible>%s</visible>" % visible if visible else ""
    return """				<control type="label">
					<width>auto</width><height>22</height>
					<aligny>center</aligny>
					<font>mf_card_meta</font>
					<textcolor>%s</textcolor>
					<label>%s</label>%s
				</control>
""" % (color, label, vis)


def body():
    L = "Container($PARAM[list]).ListItem"
    v = {"w": CARD_W, "h": CARD_H, "img": IMG_H, "g0": IMG_H - IMG_H * 65 // 100, "g1": IMG_H * 65 // 100 + 1,
         "ly": IMG_H - 64 - 12, "lw": CARD_W * 62 // 100, "ty": IMG_H - 74 - 10, "tw": CARD_W - 28,
         "my": META_Y, "gy": GENRE_Y, "L": L}
    meta = (meta_label("$INFO[%s.Rating,★ ,]" % L, color="mf_accent")
            + meta_label("$INFO[%s.Year]" % L)
            + meta_label("$INFO[%s.Property(mf.runtime)]" % L, "!String.IsEmpty(%s.Property(mf.runtime))" % L)
            + meta_label("$INFO[%s.Duration(mins),, min]" % L,
                         "String.IsEmpty(%s.Property(mf.runtime)) + String.IsEqual(%s.DBType,movie)" % (L, L))
            + meta_label("$INFO[%s.Property(TotalSeasons),, Seasons]" % L,
                         "String.IsEqual(%s.DBType,tvshow) + Integer.IsGreater(%s.Property(TotalSeasons),1)" % (L, L))
            + meta_label("1 Season",
                         "String.IsEqual(%s.DBType,tvshow) + String.IsEqual(%s.Property(TotalSeasons),1)" % (L, L)))
    v["meta"] = meta
    return """	<!-- hover card body (the Jellyfin theme's hover preview); param list = the list whose focused item it shows -->
	<include name="MFPopupBody">
		<param name="list" />
		<definition>
			<control type="image">
				<width>%(w)d</width><height>%(h)d</height>
				<texture border="12" colordiffuse="FF18181B">moodyfin/shapes/rr12.png</texture>
			</control>
			<control type="image">
				<width>%(w)d</width><height>%(img)d</height>
				<aspectratio>stretch</aspectratio>
				<texture background="true" diffuse="moodyfin/masks/pop.png">$INFO[%(L)s.Art(landscape)]</texture>
				<visible>String.IsEmpty(%(L)s.Art(fanart))</visible>
			</control>
			<control type="image">
				<width>%(w)d</width><height>%(img)d</height>
				<aspectratio aligny="top">scale</aspectratio>
				<texture background="true" diffuse="moodyfin/masks/pop.png">$INFO[%(L)s.Art(poster)]</texture>
				<visible>String.IsEmpty(%(L)s.Art(fanart)) + String.IsEmpty(%(L)s.Art(landscape))</visible>
			</control>
			<control type="image">
				<width>%(w)d</width><height>%(img)d</height>
				<aspectratio>stretch</aspectratio>
				<texture background="true" diffuse="moodyfin/masks/pop.png">$INFO[%(L)s.Art(fanart)]</texture>
			</control>
			<control type="image">
				<top>%(g0)d</top><width>%(w)d</width><height>%(g1)d</height>
				<texture colordiffuse="FF18181B">moodyfin/shapes/grad_down.png</texture>
			</control>
			<control type="image">
				<width>%(w)d</width><height>%(h)d</height>
				<texture border="14" colordiffuse="14FFFFFF">moodyfin/shapes/rr12_line.png</texture>
			</control>
			<control type="image">
				<left>14</left><top>%(ly)d</top><width>%(lw)d</width><height>64</height>
				<aspectratio align="left" aligny="bottom">keep</aspectratio>
				<texture background="true">$INFO[%(L)s.Art(clearlogo)]</texture>
			</control>
			<control type="label">
				<left>14</left><top>%(ty)d</top><width>%(tw)d</width><height>74</height>
				<aligny>bottom</aligny>
				<wrapmultiline>true</wrapmultiline>
				<font>mf_heading32</font>
				<textcolor>FFFFFFFF</textcolor>
				<label>$INFO[%(L)s.Label]</label>
				<visible>String.IsEmpty(%(L)s.Art(clearlogo))</visible>
			</control>
			<!-- 5.7   2026   1h 36m   [R]   (shows: N Seasons) -->
			<control type="grouplist">
				<left>14</left><top>%(my)d</top><width>%(tw)d</width><height>22</height>
				<orientation>horizontal</orientation>
				<itemgap>10</itemgap>
				<usecontrolwidth>true</usecontrolwidth>
%(meta)s				<control type="button">
					<top>2</top><width>auto</width><height>18</height>
					<label>$INFO[%(L)s.Mpaa]</label>
					<font>mf_card_badge</font>
					<textoffsetx>5</textoffsetx>
					<aligny>center</aligny>
					<disabledcolor>E6FFFFFF</disabledcolor>
					<texturenofocus border="4" colordiffuse="B3FFFFFF">moodyfin/shapes/rr6_line.png</texturenofocus>
					<enable>false</enable>
					<visible>!String.IsEmpty(%(L)s.Mpaa)</visible>
				</control>
			</control>
			<!-- Comedy . Romance -->
			<control type="label">
				<left>14</left><top>%(gy)d</top><width>%(tw)d</width><height>22</height>
				<aligny>center</aligny>
				<font>mf_card_genre</font>
				<textcolor>B8FFFFFF</textcolor>
				<label>$INFO[%(L)s.Property(mf.genredots)]</label>
				<visible>!String.IsEmpty(%(L)s.Property(mf.genredots))</visible>
			</control>
			<control type="label">
				<left>14</left><top>%(gy)d</top><width>%(tw)d</width><height>22</height>
				<aligny>center</aligny>
				<font>mf_card_genre</font>
				<textcolor>B8FFFFFF</textcolor>
				<label>$INFO[%(L)s.Genre]</label>
				<visible>String.IsEmpty(%(L)s.Property(mf.genredots))</visible>
			</control>
		</definition>
	</include>
""" % v


def visible(lst):
    return ("Control.HasFocus(%s) + System.IdleTime(1) + !Container(%s).Scrolling + "
            "[String.IsEqual(Container(%s).ListItem.DBType,movie) | String.IsEqual(Container(%s).ListItem.DBType,tvshow)]"
            % (lst, lst, lst, lst))


def head(name, comment):
    return """	<!-- %s -->
	<include name="%s">
		<param name="list" />
		<definition>
			<control type="group">
				<top>%d</top><width>%d</width><height>%d</height>
				<visible>%s</visible>
				<animation effect="fade" start="0" end="100" time="200">Visible</animation>
				<animation effect="zoom" start="92" end="100" center="auto" time="200" tween="cubic" easing="out">Visible</animation>
""" % (comment, name, card_y(), CARD_W, CARD_H, visible("$PARAM[list]"))


TAIL = """				<include content="MFPopupBody"><param name="list" value="$PARAM[list]" /></include>
			</control>
		</definition>
	</include>
"""


def row_include(name, maxx):
    """Hover card for a horizontal list; maxx = furthest right the card may go, relative to the list."""
    out = [head(name, "hover card over a horizontal poster list; place it right after the list, with its left/top")]
    for n in range(SLOTS):
        out.append(slide(min(max(-40, card_x(n)), maxx), 0, "Integer.IsEqual(Container($PARAM[list]).Position,%d)" % n))
    out.append(TAIL)
    return "".join(out)


def grid_include():
    out = [head("MFPopupGrid", "hover card over the poster panel; place it right after the panel, with its left/top")]
    for n in range(SLOTS):
        out.append(slide(min(max(-40, card_x(n)), 1468), 0, "Integer.IsEqual(Container($PARAM[list]).Column,%d)" % n))
    for r in range(1, GRID_ROWS):
        out.append(slide(0, min(r * ROW_H, GRID_MAX_Y), "Integer.IsEqual(Container($PARAM[list]).Row,%d)" % r))
    out.append(TAIL)
    return "".join(out)


def main():
    block = ("\t<!-- MFPopup:begin (written by tools/build_popup.py) -->\n"
             + body() + row_include("MFPopupRow", 1468) + row_include("MFPopupRowTop10", 1056) + grid_include() +
             "\t<!-- MFPopup:end -->\n")
    with open(INCLUDES, encoding="utf-8") as f:
        s = f.read()
    if "<!-- MFPopup:begin" in s:
        s = re.sub(r"\t<!-- MFPopup:begin.*?<!-- MFPopup:end -->\n", lambda m: block, s, flags=re.S)
    else:
        s = s.rstrip()
        assert s.endswith("</includes>")
        s = s[:-len("</includes>")] + block + "</includes>\n"
    with open(INCLUDES, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
    print("wrote MFPopupBody, MFPopupRow, MFPopupRowTop10, MFPopupGrid (card %dx%d)" % (CARD_W, CARD_H))


if __name__ == "__main__":
    main()
