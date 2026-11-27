"""Writes skin.moodyfin/xml/Custom_1154_MoodyFinAdmin.xml: Jellyfin's admin pages (General, Users, Libraries, Devices,
Activity, Plugins, Scheduled tasks) for a remote, in the Jellyfin theme's admin look (web-src/js/19-dashboard-skin.js: glass
papers rgba(18,18,22,.55) with a 1 px white 8 % edge and radius 18; chips radius 8, 700 11 px, their colour at 14 %
with a 35 % edge; 8 px progress bars). Section headings as the dashboard's (.tbh-h, Bebas 30).

One page at a time: Window(Home).Property(MoodyFin.AdminPage). Rows come from the helper (resources/lib/admin.py):
plugin://script.moodyfin.helper/?row=admin. OK on a row = RunScript(...,action=admin,id=...): Kodi's own pickers.

    python build_admin.py
"""
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skin.moodyfin", "xml", "Custom_1154_MoodyFinAdmin.xml")
W = 1572                 # row width: 1920 - 264 (menu) - 72 - 12
PAGE = "Window(Home).Property(MoodyFin.AdminPage)"
CHIPS = {"accent": "mf_accent", "green": "FF3EE0A1", "red": "FFFF4D6D", "orange": "FFFFB347", "muted": "FFB4B8BF"}


def chip():
    out = ""
    for k, c in CHIPS.items():
        cond = "String.IsEqual(ListItem.Property(mf.chipc),%s) + !String.IsEmpty(ListItem.Property(mf.chip))" % k
        out += """				<control type="image">
					<right>18</right><top>14</top><width>132</width><height>24</height>
					<texture border="8" colordiffuse="%(c)s">moodyfin/shapes/chip_bg.png</texture>
					<visible>%(cond)s</visible>
				</control>
				<control type="image">
					<right>18</right><top>14</top><width>132</width><height>24</height>
					<texture border="8" colordiffuse="%(c)s">moodyfin/shapes/chip_line.png</texture>
					<visible>%(cond)s</visible>
				</control>
				<control type="label">
					<right>18</right><top>14</top><width>132</width><height>24</height><align>center</align><aligny>center</aligny>
					<font>mf_bold12</font><textcolor>%(c)s</textcolor><label>$INFO[ListItem.Property(mf.chip)]</label>
					<visible>%(cond)s</visible>
				</control>
""" % {"c": c, "cond": cond}
    return out


def row(focus):
    f = """				<control type="image">
					<left>4</left><top>4</top><width>%d</width><height>68</height>
					<texture border="10" colordiffuse="12FFFFFF">moodyfin/shapes/rr10.png</texture>
				</control>
				<control type="image">
					<left>4</left><top>20</top><width>3</width><height>36</height>
					<texture border="1" colordiffuse="mf_accent">moodyfin/shapes/rr6.png</texture>
				</control>
""" % (W - 8) if focus else ""
    return """				<control type="image">
					<left>18</left><top>0</top><width>%(lw)d</width><height>1</height>
					<texture colordiffuse="0FFFFFFF">colors/white.png</texture>
					<visible>!Integer.IsEqual(ListItem.CurrentItem,1)</visible>
				</control>
%(f)s				<!-- picture (users), else an icon on a 44 px tile -->
				<control type="image">
					<left>18</left><top>16</top><width>44</width><height>44</height>
					<texture border="10" colordiffuse="14FFFFFF">moodyfin/shapes/rr10.png</texture>
					<visible>String.IsEmpty(ListItem.Property(mf.round))</visible>
				</control>
				<control type="image">
					<left>18</left><top>16</top><width>44</width><height>44</height>
					<texture colordiffuse="FF2A2C31">moodyfin/shapes/circle.png</texture>
					<visible>!String.IsEmpty(ListItem.Property(mf.round))</visible>
				</control>
				<control type="image">
					<left>28</left><top>26</top><width>24</width><height>24</height>
					<texture colordiffuse="CCFFFFFF">$INFO[ListItem.Art(icon)]</texture>
				</control>
				<control type="image">
					<left>18</left><top>16</top><width>44</width><height>44</height>
					<aspectratio>scale</aspectratio>
					<texture background="true" diffuse="moodyfin/shapes/circle.png">$INFO[ListItem.Art(thumb)]</texture>
					<visible>!String.IsEmpty(ListItem.Property(mf.round))</visible>
				</control>
				<control type="image">
					<left>18</left><top>16</top><width>44</width><height>44</height>
					<aspectratio>scale</aspectratio>
					<texture background="true" diffuse="moodyfin/masks/tile44.png">$INFO[ListItem.Art(thumb)]</texture>
					<visible>String.IsEmpty(ListItem.Property(mf.round))</visible>
				</control>
				<!-- name, what it is -->
				<control type="label">
					<left>78</left><top>11</top><width>%(tw)d</width><height>26</height><aligny>center</aligny>
					<font>mf_bold16</font><textcolor>FFFFFFFF</textcolor><label>$INFO[ListItem.Label]</label>
				</control>
				<control type="label">
					<left>78</left><top>37</top><width>%(tw)d</width><height>22</height><aligny>center</aligny>
					<font>mf_medium14</font><textcolor>99FFFFFF</textcolor><label>$INFO[ListItem.Property(mf.sub)]</label>
				</control>
				<!-- progress while a scan / task runs: 8 px theme bars, 6 here inside a row -->
				<control type="progress">
					<left>78</left><top>62</top><width>420</width><height>6</height>
					<texturebg border="3" colordiffuse="14FFFFFF">moodyfin/shapes/rr6.png</texturebg>
					<lefttexture />
					<midtexture border="3" colordiffuse="mf_accent">moodyfin/shapes/rr6.png</midtexture>
					<righttexture />
					<info>ListItem.Property(mf.pct)</info>
					<visible>!String.IsEmpty(ListItem.Property(mf.pct))</visible>
				</control>
%(chip)s				<control type="label">
					<right>18</right><top>42</top><width>420</width><height>22</height><align>right</align><aligny>center</aligny>
					<font>mf_medium13</font><textcolor>80FFFFFF</textcolor><label>$INFO[ListItem.Property(mf.right)]</label>
					<visible>!String.IsEmpty(ListItem.Property(mf.chip))</visible>
				</control>
				<control type="label">
					<right>18</right><top>0</top><width>420</width><height>76</height><align>right</align><aligny>center</aligny>
					<font>mf_medium14</font><textcolor>99FFFFFF</textcolor><label>$INFO[ListItem.Property(mf.right)]</label>
					<visible>String.IsEmpty(ListItem.Property(mf.chip))</visible>
				</control>
""" % {"lw": W - 36, "f": f, "tw": W - 78 - 470, "chip": chip()}


def tool_button(bid, page, label, accent):
    if accent:
        look = """			<textcolor>FF111111</textcolor><focusedcolor>FF111111</focusedcolor>
			<texturenofocus border="18,0,18,0" colordiffuse="mf_accent">moodyfin/shapes/pill_40.png</texturenofocus>
			<texturefocus border="18,0,18,0" colordiffuse="mf_accent">moodyfin/shapes/pill_40.png</texturefocus>"""
    else:
        look = """			<textcolor>FFFFFFFF</textcolor><focusedcolor>FFFFFFFF</focusedcolor>
			<texturenofocus border="18,0,18,0" colordiffuse="0DFFFFFF">moodyfin/shapes/pill_40.png</texturenofocus>
			<texturefocus border="18,0,18,0" colordiffuse="1AFFFFFF">moodyfin/shapes/pill_40.png</texturefocus>"""
    nxt = {4001: "4002", 4002: "9120"}[bid]
    return """		<control type="button" id="%(id)d">
			<right>168</right><top>48</top><width>%(w)d</width><height>36</height>
			<label>%(label)s</label><font>mf_tag14b</font><align>center</align><aligny>center</aligny>
%(look)s
			<onclick>RunScript(script.moodyfin.helper,action=admintool)</onclick>
			<onup>%(nxt)s</onup><ondown>4100</ondown><include>MFDashMenuLeft</include><onright>9120</onright>
			<visible>String.IsEqual(%(page)s,%(pg)s)</visible>
		</control>
		<control type="image">
			<right>164</right><top>44</top><width>%(w8)d</width><height>44</height>
			<texture border="22,0,22,0" colordiffuse="FFFFFFFF">moodyfin/shapes/pill_line_48.png</texture>
			<visible>Control.HasFocus(%(id)d)</visible>
		</control>
""" % {"id": bid, "w": 214, "w8": 222, "label": label, "look": look, "nxt": nxt, "page": PAGE, "pg": page}


XML = """<?xml version="1.0" encoding="UTF-8"?>
<!-- MoodyFin admin pages (window 1154): written by tools/build_admin.py, which says where the look comes from.
     Page = Window(Home).Property(MoodyFin.AdminPage); rows from the helper (admin.py). 4100 the rows, 4001 Scan all
     libraries (Libraries), 4002 which entries (Activity); menu on the left = MFDashMenu. -->
<window id="1154">
	<defaultcontrol>4100</defaultcontrol>
	<backgroundcolor>background</backgroundcolor>
	<controls>
		<include>MFAmbient</include>
		<!-- page title + how many -->
		<control type="grouplist">
			<left>264</left><top>46</top><width>900</width><height>44</height>
			<orientation>horizontal</orientation><itemgap>14</itemgap><usecontrolwidth>true</usecontrolwidth>
			<control type="label">
				<width>auto</width><height>44</height><aligny>center</aligny>
				<font>mf_heading36</font><textcolor>FFFFFFFF</textcolor><label>$INFO[Window(Home).Property(MoodyFin.Admin.Title)]</label>
			</control>
			<control type="label">
				<width>auto</width><height>44</height><aligny>center</aligny>
				<font>mf_bold18</font><textcolor>80FFFFFF</textcolor><label>$INFO[Window(Home).Property(MoodyFin.Admin.Count)]</label>
			</control>
		</control>
%(tools)s		<!-- the page: one glass paper, a row per thing -->
		<control type="image">
			<left>264</left><top>110</top><width>1584</width><bottom>40</bottom>
			<texture border="18" colordiffuse="8C121216">moodyfin/shapes/rr18.png</texture>
		</control>
		<control type="image">
			<left>264</left><top>110</top><width>1584</width><bottom>40</bottom>
			<texture border="18" colordiffuse="14FFFFFF">moodyfin/shapes/rr18_line.png</texture>
		</control>
		<control type="list" id="4100">
			<left>270</left><top>116</top><width>%(W)d</width><bottom>46</bottom>
			<orientation>vertical</orientation>
			<scrolltime tween="cubic" easing="out">150</scrolltime>
			<onup>4001</onup><include>MFDashMenuLeft</include><onright>noop</onright><ondown>noop</ondown>
			<onclick>RunScript(script.moodyfin.helper,action=admin,id=$INFO[ListItem.Property(mf.id)])</onclick>
			<itemlayout width="%(W)d" height="76">
%(row)s			</itemlayout>
			<focusedlayout width="%(W)d" height="76">
%(rowf)s			</focusedlayout>
			<content>plugin://script.moodyfin.helper/?row=admin&amp;reload=$INFO[Window(Home).Property(MoodyFin.Admin.Reload)]</content>
		</control>
		<control type="label">
			<left>298</left><top>130</top><width>900</width><height>40</height><aligny>center</aligny>
			<font>mf_medium14</font><textcolor>80FFFFFF</textcolor><label>Loading…</label>
			<visible>Integer.IsEqual(Container(4100).NumItems,0)</visible>
		</control>
		<include content="MFDashMenu"><param name="right" value="4100" /></include>
		<include content="MFHeader"><param name="down" value="4100" /><param name="stats" value="false" /><param name="nav" value="false" /><param name="avatarleft" value="4100" /></include>
	</controls>
</window>
"""

xml = XML % {"W": W, "row": row(False), "rowf": row(True),
             "tools": tool_button(4001, "libraries", "Scan all libraries", True)
             + tool_button(4002, "activity", "$VAR[MFAdminFilter]", False)}
open(OUT, "w", encoding="utf-8", newline="\n").write(xml)
print("wrote", os.path.normpath(OUT))
