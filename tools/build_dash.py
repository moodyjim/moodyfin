"""Writes skin.moodyfin/xml/Custom_1153_MoodyFinDashboard.xml: MoodyFin's dashboard, the Jellyfin theme's admin dashboard
home (web-src/js/19-dashboard-skin.js) with its Now Playing panel (24-now-playing.js). Sizes, colours and fonts come
from those files' CSS (theme px = skin units, text a px or two larger for a TV). Data: script.moodyfin.helper's
resources/lib/dashboard.py.

Kodi notes that shaped it: a list's item layout can't hold grouplists or buttons (so the stream cards are six fixed
slots fed by window properties), and a grouplist puts every child at its own top (so small round things sit in
full-height images with aspectratio keep, and the server chips use a 26 px pill drawn in a 68 px texture).

    python build_dash.py
"""
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skin.moodyfin", "xml", "Custom_1153_MoodyFinDashboard.xml")
D = "Window(Home).Property(MoodyFin.Dash.%s)"


def prop(k):
    return D % k


def info(k, pre="", post=""):
    return "$INFO[%s%s%s]" % (prop(k), "," + pre if pre or post else "", "," + post if post else "")


def row(part):
    return ("plugin://script.moodyfin.helper/?row=dash&amp;part=%s&amp;reload=$INFO[Window(Home).Property(MoodyFin.Dash.%s.Reload)]"
            % (part, part))


GLASS = "8C121216"     # rgba(18,18,22,.55)
LINE = "14FFFFFF"      # rgba(255,255,255,.08)
MUTED = "80FFFFFF"     # rgba(255,255,255,.5)
COL = {"dp": "FF3EE0A1", "ds": "FF4FB4FF", "rm": "FFB98CFF", "tc": "FFFF6B8A", "pa": "FFFFBE55"}


def box(left, top, width, height, extra=""):
    return """		<control type="image">
			<left>%s</left><top>%s</top><width>%s</width><height>%s</height>
			<texture border="14" colordiffuse="%s">moodyfin/shapes/rr14.png</texture>%s
		</control>
		<control type="image">
			<left>%s</left><top>%s</top><width>%s</width><height>%s</height>
			<texture border="14" colordiffuse="%s">moodyfin/shapes/rr14_line.png</texture>%s
		</control>
""" % (left, top, width, height, GLASS, extra, left, top, width, height, LINE, extra)


def heading(left, top, text, arrow=True, extra=""):
    """.tbh-h: Bebas 30, uppercase; links get an accent › (600 20 px)."""
    a = """
			<control type="label">
				<width>auto</width><height>42</height><aligny>center</aligny>
				<font>mf_semibold22</font><textcolor>mf_accent</textcolor>
				<label>›</label>
			</control>""" if arrow else ""
    return """		<control type="grouplist">
			<left>%s</left><top>%s</top><width>600</width><height>42</height>
			<orientation>horizontal</orientation><itemgap>8</itemgap><usecontrolwidth>true</usecontrolwidth>%s
			<control type="label">
				<width>auto</width><height>42</height><aligny>center</aligny>
				<font>mf_heading32</font><textcolor>FFFFFFFF</textcolor>
				<label>%s</label>
			</control>%s
		</control>
""" % (left, top, extra, text, a)


def label(text, font, color, extra="", height=34):
    return """				<control type="label">
					<width>auto</width><height>%d</height><aligny>center</aligny>
					<font>%s</font><textcolor>%s</textcolor>
					<label>%s</label>%s
				</control>
""" % (height, font, color, text, extra)


def spacer(w, h=34):
    return """				<control type="image"><width>%d</width><height>%d</height><texture /></control>
""" % (w, h)


def sep(h=30, top=None):
    t = "<top>%d</top>" % top if top is not None else ""
    return """				<control type="image">%s<width>1</width><height>%d</height><texture colordiffuse="1AFFFFFF">colors/white.png</texture></control>
""" % (t, h)


def zero_fade(k):
    return '\n\t\t\t\t\t<animation effect="fade" start="100" end="38" time="0" condition="String.IsEqual(%s,0)">Conditional</animation>' % prop(k)


def chip(text, kind, visible):
    """.tbh-chip: 700 12, padding 4/10, pill; ok = green, acc = accent, warn = orange."""
    fg, bg, line = {"": ("D1FFFFFF", "0FFFFFFF", "1AFFFFFF"), "ok": ("FF3EE0A1", "1A3EE0A1", "593EE0A1"),
                    "acc": ("mf_accent", "1FFFFFFF", "66FFFFFF"), "warn": ("FFFFB347", "1FFF9F43", "66FF9F43")}[kind]
    return """				<control type="button">
					<width>auto</width><height>68</height>
					<label>%s</label><font>mf_bold13</font><textoffsetx>12</textoffsetx><aligny>center</aligny>
					<disabledcolor>%s</disabledcolor>
					<texturenofocus border="13,0,13,0" colordiffuse="%s">moodyfin/shapes/chip26_68.png</texturenofocus>
					<enable>false</enable>%s
				</control>
""" % (text, fg, bg, "\n\t\t\t\t\t<visible>%s</visible>" % visible if visible else "")


def stat(lbl, key, width, live=None):
    color = "FFFFFFFF" if not live else "$VAR[MFDashTcColor]"
    return """				<control type="group">
					<width>%d</width><height>68</height>
					<control type="label">
						<top>16</top><width>%d</width><height>14</height>
						<font>mf_bold12</font><textcolor>%s</textcolor><label>%s</label>
					</control>
					<control type="label">
						<top>33</top><width>%d</width><height>22</height>
						<font>mf_bold18</font><textcolor>%s</textcolor><label>$INFO[%s]</label>
					</control>
				</control>
""" % (width, width, MUTED, lbl, width, color, prop(key))


def lib_tile(i, lbl, key, color):
    left = "%d" % (i * 217)
    return """			<control type="group">
				<left>%s</left><width>217</width><height>92</height>
				<control type="image">
					<left>20</left><top>0</top><width>177</width><height>2</height>
					<texture border="1" colordiffuse="%s">moodyfin/shapes/rr6.png</texture>
				</control>
				<control type="label">
					<left>20</left><top>16</top><width>177</width><height>14</height>
					<font>mf_bold12</font><textcolor>%s</textcolor><label>%s</label>
				</control>
				<control type="grouplist">
					<left>20</left><top>30</top><width>190</width><height>48</height>
					<orientation>horizontal</orientation><itemgap>6</itemgap><usecontrolwidth>true</usecontrolwidth>
					<control type="label">
						<width>auto</width><height>48</height><aligny>center</aligny>
						<font>mf_heading40</font><textcolor>FFFFFFFF</textcolor><label>$INFO[%s]</label>
					</control>
					<control type="label">
						<top>8</top><width>auto</width><height>40</height><aligny>center</aligny>
						<font>mf_bold13</font><textcolor>FF3EE0A1</textcolor><label>$INFO[%s]</label>
					</control>
				</control>
%s			</control>
""" % (left, color, MUTED, lbl, prop(key), prop(key + ".New"),
       "" if i == 3 else """				<control type="image">
					<left>216</left><top>0</top><width>1</width><height>92</height>
					<texture colordiffuse="%s">colors/white.png</texture>
				</control>
""" % LINE)


# ---------------------------------------------------------------- Now Playing card (24-now-playing.js .np-card)
def np_slot(n):
    def q(k):
        return "Window(Home).Property(MoodyFin.Dash.np.%d.%s)" % (n, k)
    left, top = 264 + (n - 1) % 3 * 531, 238 + (n - 1) // 3 * 104
    edge = "".join("""			<control type="image">
				<left>0</left><top>0</top><width>8</width><height>94</height>
				<texture border="4,14,0,14" colordiffuse="%s">moodyfin/shapes/rr14.png</texture>
				<visible>String.IsEqual(%s,%s)</visible>
			</control>
""" % (c, q("edge"), k) for k, c in COL.items() if k != "rm")
    pills = ""
    for k, c in COL.items():
        pills += """				<control type="button">
					<width>auto</width><height>22</height>
					<label>%s$INFO[%s]</label><font>mf_card_badge</font><textoffsetx>8</textoffsetx><aligny>center</aligny>
					<disabledcolor>%s</disabledcolor>
					<texturenofocus border="11,0,11,0" colordiffuse="14%s">moodyfin/shapes/pill_40.png</texturenofocus>
					<enable>false</enable>
					<visible>String.IsEqual(%s,%s)</visible>
				</control>
""" % ("     " if k == "pa" else "", q("pill"), c, c[2:], q("m"), k)
    return """		<!-- stream %(n)d -->
		<control type="group">
			<left>%(left)d</left><top>%(top)d</top><width>521</width><height>94</height>
			<visible>!String.IsEmpty(%(title)s)</visible>
%(edge)s			<control type="image">
				<left>3</left><top>0</top><width>518</width><height>94</height>
				<texture border="14" colordiffuse="D1101014">moodyfin/shapes/rr14.png</texture>
			</control>
			<control type="image">
				<left>3</left><top>0</top><width>518</width><height>94</height>
				<aspectratio>stretch</aspectratio>
				<texture background="true" colordiffuse="33FFFFFF" diffuse="moodyfin/masks/npcard.png">$INFO[%(bg)s]</texture>
			</control>
			<control type="image">
				<left>3</left><top>0</top><width>518</width><height>94</height>
				<texture border="14" colordiffuse="1AFFFFFF">moodyfin/shapes/rr14_line.png</texture>
			</control>
			<control type="image">
				<left>13</left><top>11</top><width>48</width><height>72</height>
				<texture border="7" colordiffuse="FF111111">moodyfin/shapes/rr7.png</texture>
			</control>
			<control type="image">
				<left>13</left><top>11</top><width>48</width><height>72</height>
				<aspectratio>scale</aspectratio>
				<texture background="true" diffuse="moodyfin/masks/npposter.png">$INFO[%(poster)s]</texture>
			</control>
			<!-- title, sub (700 15 / 500 12 at 55 %%) and this stream's Mbps (700 12 accent chip) -->
			<control type="grouplist">
				<left>73</left><top>9</top><width>320</width><height>22</height>
				<orientation>horizontal</orientation><itemgap>8</itemgap><usecontrolwidth>true</usecontrolwidth>
				<control type="label">
					<width>auto</width><height>22</height><aligny>center</aligny>
					<font>mf_bold16</font><textcolor>FFFFFFFF</textcolor><label>$INFO[%(title)s]</label>
				</control>
				<control type="label">
					<width>auto</width><height>22</height><aligny>center</aligny>
					<font>mf_medium13</font><textcolor>8CFFFFFF</textcolor><label>$INFO[%(sub)s]</label>
				</control>
			</control>
			<control type="grouplist">
				<right>12</right><top>9</top><width>150</width><height>22</height>
				<orientation>horizontal</orientation><align>right</align><usecontrolwidth>true</usecontrolwidth>
				<control type="button">
					<width>auto</width><height>22</height>
					<label>$INFO[%(mbps)s]</label><font>mf_bold13</font><textoffsetx>8</textoffsetx><aligny>center</aligny>
					<disabledcolor>mf_accent</disabledcolor>
					<texturenofocus border="7" colordiffuse="0FFFFFFF">moodyfin/shapes/rr7.png</texturenofocus>
					<enable>false</enable>
				</control>
			</control>
			<!-- avatar 18, user (700 12), client . device (500 12 at 50 %%) -->
			<control type="image">
				<left>73</left><top>36</top><width>18</width><height>18</height>
				<texture colordiffuse="FF333333">moodyfin/shapes/circle.png</texture>
			</control>
			<control type="label">
				<left>73</left><top>36</top><width>18</width><height>18</height>
				<align>center</align><aligny>center</aligny>
				<font>mf_bold12</font><textcolor>FFFFFFFF</textcolor><label>$INFO[%(initial)s]</label>
			</control>
			<control type="image">
				<left>73</left><top>36</top><width>18</width><height>18</height>
				<aspectratio>scale</aspectratio>
				<texture background="true" diffuse="moodyfin/shapes/circle.png">$INFO[%(av)s]</texture>
			</control>
			<control type="grouplist">
				<left>99</left><top>36</top><width>410</width><height>18</height>
				<orientation>horizontal</orientation><itemgap>8</itemgap><usecontrolwidth>true</usecontrolwidth>
				<control type="label">
					<width>auto</width><height>18</height><aligny>center</aligny>
					<font>mf_bold13</font><textcolor>FFFFFFFF</textcolor><label>$INFO[%(user)s]</label>
				</control>
				<control type="label">
					<width>auto</width><height>18</height><aligny>center</aligny>
					<font>mf_medium13</font><textcolor>80FFFFFF</textcolor><label>$INFO[%(dev)s]</label>
				</control>
			</control>
			<!-- progress, 3 px. A progress control can't read a window property as a number, but it can read a list
			     item's: a one-item list carries it (never focused). -->
			<control type="list" id="%(barid)d">
				<left>73</left><top>60</top><width>436</width><height>3</height>
				<itemlayout width="436" height="3">
					<control type="progress">
						<width>436</width><height>3</height>
						<texturebg border="1" colordiffuse="24FFFFFF">moodyfin/shapes/rr6.png</texturebg>
						<lefttexture />
						<midtexture border="1" colordiffuse="mf_accent">moodyfin/shapes/rr6.png</midtexture>
						<righttexture />
						<info>ListItem.Property(pct)</info>
					</control>
				</itemlayout>
				<focusedlayout width="436" height="3">
					<control type="progress">
						<width>436</width><height>3</height>
						<texturebg border="1" colordiffuse="24FFFFFF">moodyfin/shapes/rr6.png</texturebg>
						<lefttexture />
						<midtexture border="1" colordiffuse="mf_accent">moodyfin/shapes/rr6.png</midtexture>
						<righttexture />
						<info>ListItem.Property(pct)</info>
					</control>
				</focusedlayout>
				<content>
					<item>
						<label>-</label>
						<property name="pct">$INFO[%(pct)s]</property>
						<onclick>noop</onclick>
					</item>
				</content>
			</control>
			<!-- method pill (600 11 in its colour), what happens to the picture, time . ends -->
			<control type="grouplist">
				<left>73</left><top>68</top><width>250</width><height>22</height>
				<orientation>horizontal</orientation><itemgap>8</itemgap><usecontrolwidth>true</usecontrolwidth>
%(pills)s				<control type="button">
					<width>auto</width><height>22</height>
					<label>$INFO[%(summary)s]</label><font>mf_card_badge</font><textoffsetx>8</textoffsetx><aligny>center</aligny>
					<disabledcolor>FFFFFFFF</disabledcolor>
					<texturenofocus border="7" colordiffuse="12FFFFFF">moodyfin/shapes/rr7.png</texturenofocus>
					<enable>false</enable>
					<visible>!String.IsEmpty(%(summary)s) + String.IsEmpty(%(conv)s)</visible>
				</control>
				<control type="button">
					<width>auto</width><height>22</height>
					<label>$INFO[%(summary)s]</label><font>mf_card_badge</font><textoffsetx>8</textoffsetx><aligny>center</aligny>
					<disabledcolor>FFFF8FA5</disabledcolor>
					<texturenofocus border="7" colordiffuse="1AFF6B8A">moodyfin/shapes/rr7.png</texturenofocus>
					<enable>false</enable>
					<visible>!String.IsEmpty(%(conv)s)</visible>
				</control>
			</control>
			<control type="image">
				<left>81</left><top>73</top><width>12</width><height>12</height>
				<texture colordiffuse="%(gold)s">moodyfin/icons/pause.png</texture>
				<visible>String.IsEqual(%(m)s,pa)</visible>
			</control>
			<control type="label">
				<right>12</right><top>68</top><width>230</width><height>22</height>
				<align>right</align><aligny>center</aligny>
				<font>mf_card_badge</font><textcolor>80FFFFFF</textcolor><label>$INFO[%(time)s]</label>
			</control>
		</control>
""" % dict(n=n, left=left, top=top, edge=edge, pills=pills, gold=COL["pa"], barid=3110 + n, **{k: q(k) for k in (
        "title", "sub", "poster", "bg", "user", "dev", "av", "initial", "m", "summary", "conv", "mbps", "pct", "time")})


# ---------------------------------------------------------------- activity row (.tbh-ev)
GLYPH = {"play": "moodyfin/icons/play_arrow.png", "ring": "moodyfin/shapes/circle_line.png",
         "dot": "moodyfin/shapes/circle.png", "spark": "moodyfin/icons/star.png", "gear": "moodyfin/icons/settings.png"}


def act_row(focus):
    bg = ("""				<control type="image">
					<width>674</width><height>38</height>
					<texture border="9" colordiffuse="12FFFFFF">moodyfin/shapes/rr10.png</texture>
				</control>
""" if focus else """				<control type="image">
					<width>674</width><height>38</height>
					<texture border="9" colordiffuse="06FFFFFF">moodyfin/shapes/rr10.png</texture>
					<visible>Integer.IsOdd(ListItem.CurrentItem)</visible>
				</control>
""")
    glyphs = "".join("""				<control type="image">
					<left>%d</left><top>%d</top><width>%d</width><height>%d</height>
					<texture colordiffuse="FF111111">%s</texture>
					<visible>String.IsEmpty(ListItem.Art(thumb)) + String.IsEqual(ListItem.Property(mf.glyph),%s)</visible>
				</control>
""" % (((89, 14, 10, 10) if g in ("dot", "ring") else (87, 12, 14, 14)) + (path, g)) for g, path in GLYPH.items())
    # one coloured circle per colour the helper uses (colordiffuse can't take a property reliably)
    colors = ["mf_accent", "FFFF5D73", "FF8A8F98", "FF3EE0A1", "FFB98BFF", "FFFF9F43", "FF4FC3FF"]
    circles = "".join("""				<control type="image">
					<left>82</left><top>8</top><width>22</width><height>22</height>
					<texture colordiffuse="%s">moodyfin/shapes/circle.png</texture>
					<visible>String.IsEqual(ListItem.Property(mf.color),%s)</visible>
				</control>
""" % (c, c) for c in colors)
    rings = "".join("""				<control type="image">
					<left>80</left><top>6</top><width>26</width><height>26</height>
					<texture colordiffuse="%s">moodyfin/shapes/circle_line.png</texture>
					<visible>!String.IsEmpty(ListItem.Art(thumb)) + String.IsEqual(ListItem.Property(mf.color),%s)</visible>
				</control>
""" % (c, c) for c in colors)
    return """%(bg)s				<control type="label">
					<left>12</left><top>0</top><width>66</width><height>38</height><aligny>center</aligny>
					<font>mf_tag13</font><textcolor>%(muted)s</textcolor><label>$INFO[ListItem.Property(mf.time)]</label>
				</control>
%(circles)s%(glyphs)s				<control type="label">
					<left>89</left><top>8</top><width>8</width><height>22</height><align>center</align><aligny>center</aligny>
					<font>mf_bold12</font><textcolor>FF111111</textcolor><label>!</label>
					<visible>String.IsEmpty(ListItem.Art(thumb)) + String.IsEqual(ListItem.Property(mf.glyph),alert)</visible>
				</control>
				<control type="image">
					<left>82</left><top>8</top><width>22</width><height>22</height>
					<aspectratio>scale</aspectratio>
					<texture background="true" diffuse="moodyfin/shapes/circle.png">$INFO[ListItem.Art(thumb)]</texture>
				</control>
%(rings)s				<control type="label">
					<left>114</left><top>0</top><width>500</width><height>38</height><aligny>center</aligny>
					<font>mf_card_genre</font><textcolor>FFFFFFFF</textcolor><label>$INFO[ListItem.Label]</label>
				</control>
				<control type="image">
					<right>12</right><top>10</top><width>30</width><height>18</height>
					<texture border="6" colordiffuse="24FFFFFF">moodyfin/shapes/rr6.png</texture>
					<visible>String.IsEqual(ListItem.Property(mf.nw),1) + String.IsEmpty(ListItem.Property(mf.red))</visible>
				</control>
				<control type="image">
					<right>12</right><top>10</top><width>38</width><height>18</height>
					<texture border="6" colordiffuse="24FFFFFF">moodyfin/shapes/rr6.png</texture>
					<visible>String.IsEqual(ListItem.Property(mf.nw),2) + String.IsEmpty(ListItem.Property(mf.red))</visible>
				</control>
				<control type="label">
					<right>19</right><top>10</top><width>38</width><height>18</height><align>right</align><aligny>center</aligny>
					<font>mf_bold12</font><textcolor>mf_accent</textcolor><label>$INFO[ListItem.Property(mf.n)]</label>
					<visible>String.IsEmpty(ListItem.Property(mf.red))</visible>
				</control>
				<control type="image">
					<right>12</right><top>10</top><width>30</width><height>18</height>
					<texture border="6" colordiffuse="29FF465A">moodyfin/shapes/rr6.png</texture>
					<visible>String.IsEqual(ListItem.Property(mf.nw),1) + !String.IsEmpty(ListItem.Property(mf.red))</visible>
				</control>
				<control type="image">
					<right>12</right><top>10</top><width>38</width><height>18</height>
					<texture border="6" colordiffuse="29FF465A">moodyfin/shapes/rr6.png</texture>
					<visible>String.IsEqual(ListItem.Property(mf.nw),2) + !String.IsEmpty(ListItem.Property(mf.red))</visible>
				</control>
				<control type="label">
					<right>19</right><top>10</top><width>38</width><height>18</height><align>right</align><aligny>center</aligny>
					<font>mf_bold12</font><textcolor>FFFF8A9A</textcolor><label>$INFO[ListItem.Property(mf.n)]</label>
					<visible>!String.IsEmpty(ListItem.Property(mf.red))</visible>
				</control>
""" % dict(bg=bg, muted=MUTED, circles=circles, glyphs=glyphs, rings=rings)


# ---------------------------------------------------------------- recently added card (.tb-rcard)
def rec_card(focus):
    ring = """				<control type="image">
					<left>2</left><top>2</top><width>116</width><height>172</height>
					<texture border="14" colordiffuse="mf_accent">moodyfin/shapes/rr14_line.png</texture>
				</control>
""" if focus else ""
    lift = '\n\t\t\t\t<animation effect="slide" end="0,-4" time="200" tween="cubic" easing="out">Focus</animation>' if focus else ""
    return """			<control type="group">
				<left>4</left><top>8</top>%s
				<control type="image">
					<width>112</width><height>168</height>
					<texture border="12" colordiffuse="FF17171C">moodyfin/shapes/rr12.png</texture>
				</control>
				<control type="image">
					<width>112</width><height>168</height>
					<aspectratio>scale</aspectratio>
					<texture background="true" diffuse="moodyfin/masks/dashposter.png">$INFO[ListItem.Art(poster)]</texture>
				</control>
%s			</control>
			<control type="label">
				<left>4</left><top>183</top><width>112</width><height>18</height>
				<font>mf_tag13</font><textcolor>FFFFFFFF</textcolor><label>$INFO[ListItem.Label]</label>
			</control>
			<control type="label">
				<left>4</left><top>201</top><width>112</width><height>16</height>
				<font>mf_regular12</font><textcolor>%s</textcolor><label>$INFO[ListItem.Property(mf.sub)]</label>
			</control>
""" % (lift, ring.replace("<left>2</left><top>2</top>", "<left>-2</left><top>-2</top>"), MUTED)


# ---------------------------------------------------------------- the page
def page():
    stats = (
        # .np-total: Bebas 34 count + 700 11 caps
        label(info("Streams"), "mf_heading36", "FFFFFFFF", height=34)
        + label("STREAMS", "mf_bold12", "8CFFFFFF", '\n\t\t\t\t\t<top>4</top>', height=34)
        + spacer(4) + sep(26, 4) + spacer(4))
    for k, lbl in (("DP", "Direct Play"), ("DS", "Direct Stream"), ("RM", "Remux"), ("TC", "Transcode")):
        c = COL[k.lower()]
        stats += ("""				<control type="image">
					<width>9</width><height>34</height><aspectratio>keep</aspectratio>
					<texture colordiffuse="%s">moodyfin/shapes/circle.png</texture>%s
				</control>
""" % (c, zero_fade(k)) + label(info(k), "mf_bold18", "FFFFFFFF", zero_fade(k)) + label(lbl, "mf_card_meta", "E0FFFFFF", zero_fade(k)) + spacer(6))
    stats += (sep(26, 4) + spacer(4)
              + """				<control type="image">
					<width>14</width><height>34</height><aspectratio>keep</aspectratio>
					<texture colordiffuse="%s">moodyfin/icons/pause.png</texture>%s
				</control>
""" % (COL["pa"], zero_fade("Paused"))
              + label(info("Paused"), "mf_bold18", COL["pa"], zero_fade("Paused"))
              + label("Paused", "mf_card_meta", COL["pa"], zero_fade("Paused")))
    up = (label(info("UpStreams"), "mf_bold24", "mf_accent")
          + label("MBPS STREAMS", "mf_bold12", MUTED, '\n\t\t\t\t\t<top>4</top>') + spacer(8)
          + label(info("UpTotal"), "mf_bold24", "BFFFFFFF")
          + label("MBPS TOTAL UPLOAD", "mf_bold12", MUTED, '\n\t\t\t\t\t<top>4</top>'))

    health = (label(info("Name"), "mf_heading36", "FFFFFFFF", height=68) + spacer(22, 68)
              + chip("[COLOR FF3EE0A1]•[/COLOR] Online", "ok", None)
              + chip("v" + info("Version"), "", "!String.IsEmpty(%s)" % prop("Version"))
              + chip("Theme v" + info("Theme"), "", "!String.IsEmpty(%s)" % prop("Theme"))
              + chip("Update available", "acc", "!String.IsEmpty(%s)" % prop("Update"))
              + chip("Restart pending", "warn", "!String.IsEmpty(%s)" % prop("Restart"))
              + spacer(14, 68) + sep(30, 19) + spacer(14, 68)
              + stat("UPTIME", "Uptime", 74) + stat("CPU · JELLYFIN", "Cpu", 112) + stat("MEMORY", "Memory", 84)
              + stat("TRANSCODING", "Transcoding", 104, live=True) + stat("DEVICES", "Devices", 70) + stat("USERS", "Users", 56))

    return """<?xml version="1.0" encoding="UTF-8"?>
<!-- MoodyFin dashboard (window 1153): the Jellyfin theme's admin dashboard home (web-src/js/19-dashboard-skin.js) with its
     Now Playing panel (24-now-playing.js). Written by tools/build_dash.py from those files' CSS; data from the helper
     (resources/lib/dashboard.py): Window(Home).Property(MoodyFin.Dash.*) and the rows
     plugin://script.moodyfin.helper/?row=dash&part=np|att|rec|sto|task|act.
     Left out (web only): the admin menu column, Compact / Hide / Show details, card details on click, the folders
     under each drive, the CPU sparkline, "Update all & restart".
     Focus: 3001 Scan all libraries, 3002 Server menu, 3200 Recently added, 3600 Activity; left menu (MFDashMenu,
     Includes_MoodyFin.xml): 3690 MoodyFin (home), 3700 System items, 3710 Settings items.
     Opened from the user menu (administrators). -->
<window id="1153">
	<defaultcontrol always="true">3001</defaultcontrol>
	<onload>SetProperty(MoodyFin.AdminPage,dashboard,home)</onload>
	<backgroundcolor>background</backgroundcolor>
	<controls>
		<include>MFAmbient</include>
		<!-- the page; moves up while the lower half (recently added, deep in the activity list) has focus -->
		<control type="group">
		<top>-64</top>
		<animation effect="slide" end="0,-340" time="300" tween="cubic" easing="out" condition="Control.HasFocus(3200) | [Control.HasFocus(3600) + Integer.IsGreater(Container(3600).CurrentItem,9)]">Conditional</animation>

		<!-- ======================================================== NOW PLAYING -->
		<control type="grouplist">
			<left>264</left><top>114</top><width>600</width><height>40</height>
			<orientation>horizontal</orientation><itemgap>10</itemgap><usecontrolwidth>true</usecontrolwidth>
			<control type="image">
				<width>26</width><height>40</height><aspectratio>keep</aspectratio>
				<texture>moodyfin/icons/play_circle.png</texture>
			</control>
			<control type="label">
				<width>auto</width><height>40</height><aligny>center</aligny>
				<font>mf_heading32</font><textcolor>FFFFFFFF</textcolor><label>NOW PLAYING</label>
			</control>
			<control type="image">
				<width>9</width><height>40</height><aspectratio>keep</aspectratio>
				<texture colordiffuse="FF3EE0A1">moodyfin/shapes/circle.png</texture>
				<animation effect="fade" start="100" end="35" time="800" pulse="true" condition="true">Conditional</animation>
			</control>
		</control>
%(statsbox)s		<control type="grouplist">
			<left>284</left><top>178</top><width>960</width><height>34</height>
			<orientation>horizontal</orientation><itemgap>7</itemgap><usecontrolwidth>true</usecontrolwidth>
			<control type="group"><width>0</width><height>12</height></control>
%(stats)s		</control>
		<control type="grouplist">
			<right>92</right><top>178</top><width>700</width><height>34</height>
			<orientation>horizontal</orientation><align>right</align><itemgap>8</itemgap><usecontrolwidth>true</usecontrolwidth>
%(up)s		</control>
		<!-- one card per stream, 3 across, up to 6 -->
%(cards)s
		<control type="group">
			<left>264</left><top>238</top><right>72</right><height>50</height>
			<visible>String.IsEqual(%(streams)s,0)</visible>
			<control type="image">
				<width>100%%</width><height>50</height>
				<texture border="14" colordiffuse="24FFFFFF">moodyfin/shapes/rr14_line.png</texture>
			</control>
			<control type="label">
				<left>18</left><width>1200</width><height>50</height><aligny>center</aligny>
				<font>mf_tag13</font><textcolor>%(muted)s</textcolor><label>Nothing is playing right now.</label>
			</control>
		</control>

		<!-- everything under the cards: down one card row when there are more than 3 streams -->
		<control type="group">
		<top>352</top>
		<animation effect="slide" end="0,104" time="0" condition="Integer.IsGreater(%(streams)s,3)">Conditional</animation>

		<!-- ======================================================== server strip (.tbh-health) -->
%(healthbox)s		<control type="grouplist">
			<left>284</left><top>2</top><width>1160</width><height>68</height>
			<orientation>horizontal</orientation><itemgap>8</itemgap><usecontrolwidth>true</usecontrolwidth>
%(health)s		</control>
		<!-- Scan all libraries (accent pill; shows the scan's progress) and the Server menu -->
		<control type="button" id="3001">
			<right>246</right><top>18</top><width>214</width><height>36</height>
			<label>$VAR[MFDashScanLabel]</label><font>mf_tag14b</font>
			<textcolor>FF111111</textcolor><focusedcolor>FF111111</focusedcolor>
			<textoffsetx>40</textoffsetx><aligny>center</aligny>
			<texturenofocus border="18,0,18,0" colordiffuse="mf_accent">moodyfin/shapes/pill_40.png</texturenofocus>
			<texturefocus border="18,0,18,0" colordiffuse="mf_accent">moodyfin/shapes/pill_40.png</texturefocus>
			<onclick>RunScript(script.moodyfin.helper,action=dashscan)</onclick>
			<onup>9120</onup><ondown>3200</ondown><include>MFDashMenuLeft</include><onright>3002</onright>
		</control>
		<control type="image">
			<right>242</right><top>14</top><width>222</width><height>44</height>
			<texture border="22,0,22,0" colordiffuse="FFFFFFFF">moodyfin/shapes/pill_line_48.png</texture>
			<visible>Control.HasFocus(3001)</visible>
		</control>
		<control type="image">
			<right>428</right><top>28</top><width>16</width><height>16</height>
			<texture colordiffuse="FF111111">moodyfin/icons/refresh.png</texture>
			<animation effect="rotate" end="-360" center="auto" time="1100" loop="true" condition="!String.IsEmpty(%(scan)s)">Conditional</animation>
		</control>
		<control type="button" id="3002">
			<right>92</right><top>18</top><width>142</width><height>36</height>
			<label>Server</label><font>mf_tag14b</font>
			<textcolor>FFFFFFFF</textcolor><focusedcolor>FFFFFFFF</focusedcolor>
			<textoffsetx>18</textoffsetx><aligny>center</aligny>
			<texturenofocus border="18,0,18,0" colordiffuse="0DFFFFFF">moodyfin/shapes/pill_40.png</texturenofocus>
			<texturefocus border="18,0,18,0" colordiffuse="1AFFFFFF">moodyfin/shapes/pill_40.png</texturefocus>
			<onclick>RunScript(script.moodyfin.helper,action=dashserver)</onclick>
			<onup>9120</onup><ondown>3600</ondown><onleft>3001</onleft><onright>noop</onright>
		</control>
		<control type="image">
			<right>92</right><top>18</top><width>142</width><height>36</height>
			<texture border="18,0,18,0" colordiffuse="24FFFFFF">moodyfin/shapes/pill_line_40.png</texture>
			<visible>!Control.HasFocus(3002)</visible>
		</control>
		<control type="image">
			<right>88</right><top>14</top><width>150</width><height>44</height>
			<texture border="22,0,22,0" colordiffuse="FFFFFFFF">moodyfin/shapes/pill_line_48.png</texture>
			<visible>Control.HasFocus(3002)</visible>
		</control>
		<control type="image">
			<right>108</right><top>26</top><width>20</width><height>20</height>
			<texture>moodyfin/icons/expand_more.png</texture>
		</control>

		<!-- ======================================================== left column -->
		<control type="group">
		<left>264</left><top>98</top><width>870</width>
		<!-- attention: only what needs you -->
		<control type="group">
			<visible>Integer.IsGreater(Container(3400).NumItems,0)</visible>
%(atthead)s		</control>
		<control type="list" id="3400">
			<left>0</left><top>42</top><width>870</width><height>248</height>
			<orientation>vertical</orientation>
			<itemlayout width="870" height="62">
%(att)s			</itemlayout>
			<focusedlayout width="870" height="62">
%(att)s			</focusedlayout>
			<content>%(attrow)s</content>
		</control>
		<control type="group">
		<animation effect="slide" end="0,%(att1)d" time="0" condition="Integer.IsEqual(Container(3400).NumItems,1)">Conditional</animation>
		<animation effect="slide" end="0,%(att2)d" time="0" condition="Integer.IsEqual(Container(3400).NumItems,2)">Conditional</animation>
		<animation effect="slide" end="0,%(att3)d" time="0" condition="Integer.IsEqual(Container(3400).NumItems,3)">Conditional</animation>
		<animation effect="slide" end="0,%(att4)d" time="0" condition="Integer.IsEqual(Container(3400).NumItems,4)">Conditional</animation>
%(libhead)s%(libbox)s		<control type="group">
			<top>42</top>
%(tiles)s		</control>
%(rechead)s		<control type="list" id="3200">
			<left>-4</left><top>196</top><width>878</width><height>226</height>
			<orientation>horizontal</orientation>
			<scrolltime tween="cubic" easing="out">200</scrolltime>
			<onup>3001</onup><ondown>noop</ondown><include>MFDashMenuLeft</include><onright>3600</onright>
			<onclick>RunScript(script.moodyfin.helper,action=info,type=$INFO[ListItem.Property(mf.kind)],dbid=$INFO[ListItem.Property(mf.dbid)])</onclick>
			<itemlayout width="124" height="226">
%(rec)s			</itemlayout>
			<focusedlayout width="124" height="226">
%(recf)s			</focusedlayout>
			<content target="videos">%(recrow)s</content>
		</control>
%(stohead)s%(stobox)s		<control type="list" id="3300">
			<left>0</left><top>476</top><width>421</width><height>368</height>
			<orientation>vertical</orientation>
			<itemlayout width="421" height="92">
%(sto)s			</itemlayout>
			<focusedlayout width="421" height="92">
%(sto)s			</focusedlayout>
			<content>%(storow)s</content>
		</control>
%(taskhead)s%(taskbox)s		<control type="list" id="3310">
			<left>449</left><top>476</top><width>421</width><height>310</height>
			<orientation>vertical</orientation>
			<itemlayout width="421" height="62">
%(task)s			</itemlayout>
			<focusedlayout width="421" height="62">
%(task)s			</focusedlayout>
			<content>%(taskrow)s</content>
		</control>
		<control type="label">
			<left>467</left><top>476</top><width>390</width><height>52</height><aligny>center</aligny>
			<font>mf_medium14</font><textcolor>%(muted)s</textcolor><label>$INFO[%(idle)s]</label>
			<visible>Integer.IsEqual(Container(3310).NumItems,0)</visible>
		</control>
		</control>
		</control>

		<!-- ======================================================== right column: activity -->
		<control type="group">
		<right>72</right><top>98</top><width>686</width>
%(acthead)s%(actbox)s		<control type="list" id="3600">
			<left>6</left><top>48</top><width>674</width><height>760</height>
			<orientation>vertical</orientation>
			<scrolltime tween="cubic" easing="out">150</scrolltime>
			<onup>3002</onup><onleft>3200</onleft><onright>noop</onright><ondown>noop</ondown>
			<itemlayout width="674" height="38">
%(act)s			</itemlayout>
			<focusedlayout width="674" height="38">
%(actf)s			</focusedlayout>
			<content>%(actrow)s</content>
		</control>
		<control type="label">
			<left>18</left><top>42</top><width>640</width><height>52</height><aligny>center</aligny>
			<font>mf_medium14</font><textcolor>%(muted)s</textcolor><label>No activity in the last 3 days</label>
			<visible>Integer.IsEqual(Container(3600).NumItems,0)</visible>
		</control>
		</control>
		</control>
		</control>

		<include content="MFDashMenu"><param name="right" value="3001" /></include>
		<include content="MFHeader"><param name="down" value="3001" /><param name="stats" value="false" /><param name="nav" value="false" /><param name="avatarleft" value="3001" /></include>
	</controls>
</window>
""" % dict(
        statsbox=box(264, 166, "1776", 58).replace("<width>1776</width>", "<right>72</right>"),
        stats=stats, up=up, cards="".join(np_slot(n) for n in range(1, 7)), streams=prop("Streams"), muted=MUTED,
        healthbox=box(264, 0, "1776", 72).replace("<width>1776</width>", "<right>72</right>"),
        health=health, scan=prop("Scan"),
        atthead=heading(0, 0, "ATTENTION"), att=att_row(), attrow=row("att"),
        att1=42 + 62 + 26 - 6, att2=42 + 124 + 26 - 6, att3=42 + 186 + 26 - 6, att4=42 + 248 + 26 - 6,
        libhead=heading(0, 0, "LIBRARY"), libbox=box(0, 42, 870, 92),
        tiles="".join(lib_tile(i, *t) for i, t in enumerate((("MOVIES", "Movies", "FFFF5D73"), ("SERIES", "Series", "FF4FC3FF"),
                                                             ("EPISODES", "Episodes", "FF4FC3FF"), ("COLLECTIONS", "Collections", "FF3EE0A1")))),
        rechead=heading(0, 160, "RECENTLY ADDED", arrow=False), rec=rec_card(False), recf=rec_card(True), recrow=row("rec"),
        stohead=heading(0, 434, "STORAGE", arrow=False), stobox=sto_box(), sto=sto_row(), storow=row("sto"),
        taskhead=heading(449, 434, "RUNNING TASKS"), taskbox=task_box(), task=task_row(), taskrow=row("task"),
        idle=prop("Idle"),
        acthead=heading(0, 0, "ACTIVITY"), actbox=box(0, 42, 686, 772), act=act_row(False), actf=act_row(True), actrow=row("act"),
    )


def att_row():
    """.tbh-al: 12/16 padding, radius 12, icon chip 30 (its colour at 16 %), bold 14 title, 500 12.5 muted line."""
    colors = ["FFFF5D73", "FFFFB347", "mf_accent"]
    chips = "".join("""				<control type="image">
					<left>16</left><top>13</top><width>30</width><height>30</height>
					<texture border="8" colordiffuse="29%s">moodyfin/shapes/rr10.png</texture>
					<visible>String.IsEqual(ListItem.Property(mf.c),%s)</visible>
				</control>
				<control type="label">
					<left>16</left><top>13</top><width>30</width><height>30</height><align>center</align><aligny>center</aligny>
					<font>mf_bold16</font><textcolor>%s</textcolor><label>$INFO[ListItem.Property(mf.i)]</label>
					<visible>String.IsEqual(ListItem.Property(mf.c),%s)</visible>
				</control>
""" % ((c[2:] if c.startswith("FF") else "FFFFFF"), c, c, c) for c in colors)
    return """				<control type="image">
					<width>870</width><height>56</height>
					<texture border="12" colordiffuse="%s">moodyfin/shapes/rr12.png</texture>
					<visible>String.IsEmpty(ListItem.Property(mf.red))</visible>
				</control>
				<control type="image">
					<width>870</width><height>56</height>
					<texture border="12" colordiffuse="12FF3C50">moodyfin/shapes/rr12.png</texture>
					<visible>!String.IsEmpty(ListItem.Property(mf.red))</visible>
				</control>
				<control type="image">
					<width>870</width><height>56</height>
					<texture border="14" colordiffuse="%s">moodyfin/shapes/rr12_line.png</texture>
					<visible>String.IsEmpty(ListItem.Property(mf.red))</visible>
				</control>
				<control type="image">
					<width>870</width><height>56</height>
					<texture border="14" colordiffuse="59FF5064">moodyfin/shapes/rr12_line.png</texture>
					<visible>!String.IsEmpty(ListItem.Property(mf.red))</visible>
				</control>
%s				<control type="image">
					<left>23</left><top>20</top><width>16</width><height>16</height>
					<texture colordiffuse="FFFFB347">moodyfin/icons/$INFO[ListItem.Property(mf.icon)].png</texture>
					<visible>!String.IsEmpty(ListItem.Property(mf.icon)) + !String.IsEqual(ListItem.Property(mf.c),mf_accent) + !String.IsEqual(ListItem.Property(mf.c),FFFF5D73)</visible>
				</control>
				<control type="image">
					<left>23</left><top>20</top><width>16</width><height>16</height>
					<texture colordiffuse="FFFF5D73">moodyfin/icons/$INFO[ListItem.Property(mf.icon)].png</texture>
					<visible>!String.IsEmpty(ListItem.Property(mf.icon)) + String.IsEqual(ListItem.Property(mf.c),FFFF5D73)</visible>
				</control>
				<control type="image">
					<left>23</left><top>20</top><width>16</width><height>16</height>
					<texture colordiffuse="mf_accent">moodyfin/icons/$INFO[ListItem.Property(mf.icon)].png</texture>
					<visible>!String.IsEmpty(ListItem.Property(mf.icon)) + String.IsEqual(ListItem.Property(mf.c),mf_accent)</visible>
				</control>
				<control type="label">
					<left>60</left><top>8</top><width>790</width><height>20</height>
					<font>mf_tag14b</font><textcolor>FFFFFFFF</textcolor><label>$INFO[ListItem.Label]</label>
				</control>
				<control type="label">
					<left>60</left><top>29</top><width>790</width><height>18</height>
					<font>mf_medium13</font><textcolor>%s</textcolor><label>$INFO[ListItem.Property(mf.s)]</label>
				</control>
""" % (GLASS, LINE, chips, MUTED)


def sto_box():
    out = ""
    for n in range(1, 5):
        out += box(0, 476, 421, 92 * n, "\n\t\t\t<visible>Integer.IsEqual(Container(3300).NumItems,%d)</visible>" % n)
    out += box(0, 476, 421, 52, "\n\t\t\t<visible>Integer.IsEqual(Container(3300).NumItems,0)</visible>")
    return out


def task_box():
    out = box(449, 476, 421, 52, "\n\t\t\t<visible>Integer.IsLessOrEqual(Container(3310).NumItems,0)</visible>")
    for n in range(1, 6):
        out += box(449, 476, 421, 62 * n, "\n\t\t\t<visible>Integer.IsEqual(Container(3310).NumItems,%d)</visible>" % n)
    return out


def sto_row():
    """.tbh-drv: 14/18 padding; Bebas 22 title, 500 12 muted sizes (free in white); 8 px bar in the drive's colour;
    '72 % used · 5 folders' 700 12 accent."""
    bars = "".join("""				<control type="progress">
					<left>18</left><top>47</top><width>385</width><height>8</height>
					<texturebg border="4" colordiffuse="14FFFFFF">moodyfin/shapes/rr6.png</texturebg>
					<lefttexture />
					<midtexture border="4" colordiffuse="%s">moodyfin/shapes/rr6.png</midtexture>
					<righttexture />
					<info>ListItem.Property(mf.pct)</info>
					<visible>String.IsEqual(ListItem.Property(mf.color),%s)</visible>
				</control>
""" % (c, c) for c in ("FF3EE0A1", "FFFFB347", "FFFF4D6D"))
    return """				<control type="image">
					<left>0</left><top>0</top><width>421</width><height>1</height>
					<texture colordiffuse="%s">colors/white.png</texture>
					<visible>!Integer.IsEqual(ListItem.CurrentItem,1)</visible>
				</control>
				<control type="label">
					<left>18</left><top>12</top><width>240</width><height>28</height><aligny>center</aligny>
					<font>mf_heading24</font><textcolor>FFFFFFFF</textcolor><label>$INFO[ListItem.Label]</label>
				</control>
				<control type="label">
					<right>18</right><top>12</top><width>260</width><height>28</height><align>right</align><aligny>center</aligny>
					<font>mf_medium13</font><textcolor>%s</textcolor>
					<label>$INFO[ListItem.Property(mf.size)][COLOR FFFFFFFF]$INFO[ListItem.Property(mf.free)][/COLOR]</label>
				</control>
%s				<control type="label">
					<left>18</left><top>62</top><width>385</width><height>18</height><aligny>center</aligny>
					<font>mf_bold13</font><textcolor>mf_accent</textcolor><label>$INFO[ListItem.Property(mf.summary)]</label>
				</control>
""" % (LINE, MUTED, bars)


def task_row():
    """.tbh-task: 14/18 padding, 600 14 name, % right (muted), 6 px accent bar."""
    return """				<control type="image">
					<left>0</left><top>0</top><width>421</width><height>1</height>
					<texture colordiffuse="%s">colors/white.png</texture>
					<visible>!Integer.IsEqual(ListItem.CurrentItem,1)</visible>
				</control>
				<control type="label">
					<left>18</left><top>12</top><width>310</width><height>20</height><aligny>center</aligny>
					<font>mf_card_meta</font><textcolor>FFFFFFFF</textcolor><label>$INFO[ListItem.Label]</label>
				</control>
				<control type="label">
					<right>18</right><top>12</top><width>80</width><height>20</height><align>right</align><aligny>center</aligny>
					<font>mf_card_meta</font><textcolor>%s</textcolor><label>$INFO[ListItem.Property(mf.pct),,%%]</label>
				</control>
				<control type="progress">
					<left>18</left><top>41</top><width>385</width><height>6</height>
					<texturebg border="3" colordiffuse="14FFFFFF">moodyfin/shapes/rr6.png</texturebg>
					<lefttexture />
					<midtexture border="3" colordiffuse="mf_accent">moodyfin/shapes/rr6.png</midtexture>
					<righttexture />
					<info>ListItem.Property(mf.pct)</info>
				</control>
""" % (LINE, MUTED)


open(OUT, "w", encoding="utf-8", newline="\n").write(page())
print("wrote", os.path.normpath(OUT))
