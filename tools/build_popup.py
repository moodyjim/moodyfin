"""Writes MoodyFin's hover card includes (the Jellyfin theme's title popup) into skin.moodyfin/xml/Includes_MoodyFin.xml,
between <!-- MFPopup:begin --> and <!-- MFPopup:end -->.

A Kodi list clips whatever its items draw outside their slot, so the card is a control of its own, placed after the
list (same left/top as the list) and moved over the focused poster with one conditional slide per visible position:
  MFPopupRow  (horizontal lists)  x from Container(list).Position
  MFPopupGrid (poster panel)      x from Container(list).Column, y from Container(list).Row
It shows after a second without a key press (System.IdleTime(1)) plus a 0.2 s fade, for movies and shows.

    python build_popup.py
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
INCLUDES = os.path.join(HERE, "..", "skin.moodyfin", "xml", "Includes_MoodyFin.xml")

ITEM_W = 206        # poster slot (190 poster + 16 gap); cards sit 4 px in
POSTER_W, POSTER_H = 190, 285
CARD_W, CARD_H = 360, 344
ROW_H = 390         # poster grid row height
SLOTS = 12          # positions / columns handled
GRID_ROWS = 4


def card_x(n):
    return n * ITEM_W + 4 + POSTER_W // 2 - CARD_W // 2


def slide(x, y, cond):
    return ('\t\t\t\t<animation effect="slide" end="%d,%d" time="0" condition="%s">Conditional</animation>\n'
            % (x, y, cond))


def body():
    return '''	<!-- hover card body; param list = the list whose focused item it shows -->
	<include name="MFPopupBody">
		<param name="list" />
		<definition>
			<control type="image">
				<width>%(w)d</width><height>%(h)d</height>
				<texture border="12" colordiffuse="F7141518">moodyfin/shapes/rr12.png</texture>
			</control>
			<control type="image">
				<width>%(w)d</width><height>202</height>
				<aspectratio>stretch</aspectratio>
				<texture background="true" diffuse="moodyfin/masks/pop.png">$INFO[Container($PARAM[list]).ListItem.Art(fanart)]</texture>
			</control>
			<control type="image">
				<top>82</top><width>%(w)d</width><height>122</height>
				<texture colordiffuse="F2141518">moodyfin/shapes/grad_down.png</texture>
			</control>
			<control type="image">
				<width>%(w)d</width><height>%(h)d</height>
				<texture border="14" colordiffuse="1FFFFFFF">moodyfin/shapes/rr12_line.png</texture>
			</control>
			<control type="image">
				<left>16</left><top>104</top><width>250</width><height>88</height>
				<aspectratio align="left" aligny="bottom">keep</aspectratio>
				<texture background="true">$INFO[Container($PARAM[list]).ListItem.Art(clearlogo)]</texture>
			</control>
			<control type="label">
				<left>16</left><top>130</top><width>328</width><height>64</height>
				<aligny>bottom</aligny>
				<font>mf_heading48</font>
				<textcolor>mf_text</textcolor>
				<label>$INFO[Container($PARAM[list]).ListItem.Label]</label>
				<visible>String.IsEmpty(Container($PARAM[list]).ListItem.Art(clearlogo))</visible>
			</control>
			<!-- buttons: a picture of the Jellyfin theme's (OK opens the details page) -->
			<control type="image">
				<left>16</left><top>212</top><width>48</width><height>48</height>
				<texture>moodyfin/buttons/pop_play_arrow.png</texture>
			</control>
			<control type="image">
				<left>74</left><top>212</top><width>48</width><height>48</height>
				<texture>moodyfin/buttons/pop_favorite.png</texture>
			</control>
			<control type="image">
				<left>132</left><top>212</top><width>48</width><height>48</height>
				<texture>moodyfin/buttons/pop_check.png</texture>
			</control>
			<control type="image">
				<left>132</left><top>212</top><width>48</width><height>48</height>
				<texture colordiffuse="mf_accent">moodyfin/shapes/circle_line.png</texture>
				<visible>Integer.IsGreater(Container($PARAM[list]).ListItem.PlayCount,0)</visible>
			</control>
			<control type="image">
				<right>16</right><top>212</top><width>48</width><height>48</height>
				<texture>moodyfin/buttons/pop_expand_more.png</texture>
			</control>
			<!-- ★ 6.9   2026   2h 8m   [R]   (shows: N Seasons) -->
			<control type="grouplist">
				<left>16</left><top>272</top><width>328</width><height>30</height>
				<orientation>horizontal</orientation>
				<itemgap>16</itemgap>
				<usecontrolwidth>true</usecontrolwidth>
				<control type="label">
					<width>auto</width><height>30</height>
					<aligny>center</aligny>
					<font>mf_semibold20</font>
					<label>$INFO[Container($PARAM[list]).ListItem.Rating,[COLOR mf_accent]★ ,[/COLOR]]</label>
				</control>
				<control type="label">
					<width>auto</width><height>30</height>
					<aligny>center</aligny>
					<font>mf_semibold20</font>
					<textcolor>mf_text</textcolor>
					<label>$INFO[Container($PARAM[list]).ListItem.Year]</label>
				</control>
				<control type="label">
					<width>auto</width><height>30</height>
					<aligny>center</aligny>
					<font>mf_semibold20</font>
					<textcolor>mf_text</textcolor>
					<label>$INFO[Container($PARAM[list]).ListItem.Property(mf.runtime)]</label>
					<visible>!String.IsEmpty(Container($PARAM[list]).ListItem.Property(mf.runtime))</visible>
				</control>
				<control type="label">
					<width>auto</width><height>30</height>
					<aligny>center</aligny>
					<font>mf_semibold20</font>
					<textcolor>mf_text</textcolor>
					<label>$INFO[Container($PARAM[list]).ListItem.Duration(mins),, min]</label>
					<visible>String.IsEmpty(Container($PARAM[list]).ListItem.Property(mf.runtime)) + String.IsEqual(Container($PARAM[list]).ListItem.DBType,movie)</visible>
				</control>
				<control type="label">
					<width>auto</width><height>30</height>
					<aligny>center</aligny>
					<font>mf_semibold20</font>
					<textcolor>mf_text</textcolor>
					<label>$INFO[Container($PARAM[list]).ListItem.Property(TotalSeasons),, Seasons]</label>
					<visible>String.IsEqual(Container($PARAM[list]).ListItem.DBType,tvshow) + Integer.IsGreater(Container($PARAM[list]).ListItem.Property(TotalSeasons),1)</visible>
				</control>
				<control type="label">
					<width>auto</width><height>30</height>
					<aligny>center</aligny>
					<font>mf_semibold20</font>
					<textcolor>mf_text</textcolor>
					<label>1 Season</label>
					<visible>String.IsEqual(Container($PARAM[list]).ListItem.DBType,tvshow) + String.IsEqual(Container($PARAM[list]).ListItem.Property(TotalSeasons),1)</visible>
				</control>
				<control type="button">
					<top>3</top><width>auto</width><height>24</height>
					<label>$INFO[Container($PARAM[list]).ListItem.Mpaa]</label>
					<font>font_flag</font>
					<textoffsetx>8</textoffsetx>
					<aligny>center</aligny>
					<disabledcolor>E6F1F2F4</disabledcolor>
					<texturenofocus border="5" colordiffuse="B3F1F2F4">moodyfin/shapes/rr6_line.png</texturenofocus>
					<enable>false</enable>
					<visible>!String.IsEmpty(Container($PARAM[list]).ListItem.Mpaa)</visible>
				</control>
			</control>
			<control type="label">
				<left>16</left><top>304</top><width>328</width><height>28</height>
				<font>mf_small18</font>
				<textcolor>mf_muted</textcolor>
				<label>$INFO[Container($PARAM[list]).ListItem.Property(mf.genres)]</label>
				<visible>!String.IsEmpty(Container($PARAM[list]).ListItem.Property(mf.genres))</visible>
			</control>
			<control type="label">
				<left>16</left><top>304</top><width>328</width><height>28</height>
				<font>mf_small18</font>
				<textcolor>mf_muted</textcolor>
				<label>$INFO[Container($PARAM[list]).ListItem.Genre]</label>
				<visible>String.IsEmpty(Container($PARAM[list]).ListItem.Property(mf.genres))</visible>
			</control>
		</definition>
	</include>
''' % {"w": CARD_W, "h": CARD_H}


def visible(lst):
    return ("Control.HasFocus(%s) + System.IdleTime(1) + !Container(%s).Scrolling + "
            "[String.IsEqual(Container(%s).ListItem.DBType,movie) | String.IsEqual(Container(%s).ListItem.DBType,tvshow)]"
            % (lst, lst, lst, lst))


def row_include(name, maxx):
    """Hover card for a horizontal list; maxx = furthest right the card may go, relative to the list."""
    out = ['''	<!-- hover card over a horizontal poster list; place it right after the list with the list's left/top -->
	<include name="%s">
		<param name="list" />
		<definition>
			<control type="group">
				<top>-10</top><width>%d</width><height>%d</height>
				<visible>%s</visible>
				<animation effect="fade" start="0" end="100" time="200">Visible</animation>
				<animation effect="zoom" start="92" end="100" center="auto" time="200" tween="cubic" easing="out">Visible</animation>
''' % (name, CARD_W, CARD_H, visible("$PARAM[list]"))]
    for n in range(SLOTS):
        out.append(slide(min(max(-40, card_x(n)), maxx), 0, "Integer.IsEqual(Container($PARAM[list]).Position,%d)" % n))
    out.append('''				<include content="MFPopupBody"><param name="list" value="$PARAM[list]" /></include>
			</control>
		</definition>
	</include>
''')
    return "".join(out)


def grid_include():
    out = ['''	<!-- hover card over the poster panel (520); place it right after the panel with the panel's left/top -->
	<include name="MFPopupGrid">
		<param name="list" />
		<definition>
			<control type="group">
				<top>-10</top><width>%d</width><height>%d</height>
				<visible>%s</visible>
				<animation effect="fade" start="0" end="100" time="200">Visible</animation>
				<animation effect="zoom" start="92" end="100" center="auto" time="200" tween="cubic" easing="out">Visible</animation>
''' % (CARD_W, CARD_H, visible("$PARAM[list]"))]
    for n in range(SLOTS):
        out.append(slide(min(max(-40, card_x(n)), 1468), 0, "Integer.IsEqual(Container($PARAM[list]).Column,%d)" % n))
    for r in range(1, GRID_ROWS):
        out.append(slide(0, min(r * ROW_H, 510), "Integer.IsEqual(Container($PARAM[list]).Row,%d)" % r))
    out.append('''				<include content="MFPopupBody"><param name="list" value="$PARAM[list]" /></include>
			</control>
		</definition>
	</include>
''')
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
    print("wrote MFPopupBody, MFPopupRow, MFPopupGrid")


if __name__ == "__main__":
    main()
