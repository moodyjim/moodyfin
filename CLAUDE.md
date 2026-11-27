# CLAUDE.md

## Communication
- Blunt, short replies.
- If I say "talk", don't touch any code — just answer.

## Editing rules
- Only change what I explicitly ask.
- Never commit API keys (TMDB, Jellyfin tokens). Before every push, scan the diff for 32-hex strings and abort if found.
- Commit messages must end with: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`
- Commit or push only when I ask.
- **Every commit is a version.** `skin.moodyfin` and `script.moodyfin.helper` share one version number; the skin's
  `addon.xml` requires that exact helper version. Bump patch for fixes, minor for a new screen/phase
  (major stays 0 until release). Update both `addon.xml` files and both `changelog.txt`, start the commit message with
  `MoodyFin x.y.z: `, and tag the commit `vx.y.z` (annotated). Push tags with the commit (`git push --follow-tags`).

## What this is
MoodyFin: a Kodi skin that recreates the Jellyfin theme on Kodi.
- Reference theme (read-only, never edit): `c:\workflow\jellyfin\moodyjim-jellyfin-theme`
  - Look/tokens: `look/Inject/Theme/ue-tokens.css`, `ue-ambient.css`; hero `look/Inject/Hero/`; details `look/Inject/Details/`
  - Features: `web-src/js/NN-*.js`, `web-src/theme.css`
- Reference screenshots (copied into this repo): `docs/reference/`
  - `home.jpg`, `home-rows.jpg`, `home-wide.jpg` — header, hero, studio row, Continue Watching, Top 10 (#1 wide card), Latest / Recently added rows
  - `details-movie.jpg`, `details-series.jpg` — centred clearlogo, poster card with badges + "Genre • ★ x", info bar, track rows, cast, collections, more like this, next up, seasons
  - `library-movies.jpg` — title + count, toolbar, 12-column poster grid, A–Z rail
  - `player-osd.jpg`, `player-paused.jpg` — floating glass control panel, "Ends at" pill, clearlogo; pause screen "You're watching"
  - `search.jpg` — "Discover something new", pill search field, filter chips, sectioned results
  - `login.jpg` — sign-in look (for the profile picker)
- Sibling Kodi projects (patterns to reuse, never edit from here):
  - `c:\workflow\kodi\moodyskin` — MoodySkin (BBS look) + `plugin.video.moodyskin` helper (PIL artwork, home rows, service)
  - `c:\workflow\kodi\moodyjim-skin` — Estuary fork + `plugin.video.moodysimilar`
- Remote: https://github.com/moodyjim/moodyfin.git

## Target
- Kodi 21 Omega, `xbmc.gui` 5.17.0, `xbmc.python` 3.0.1. 1920x1080 skin resolution.
- Final device: **CoreELEC on a Ugoos box** (ARM, remote only). Windows is just the dev box.
  Everything must work with a remote (no mouse/hover-only features) and stay light on the ARM CPU.
- Library comes from `plugin.video.jellyfin` (Jellyfin for Kodi, native DB sync mode). All artwork comes from the Jellyfin server.

## Decisions
- Skin name **MoodyFin**, add-on id `skin.moodyfin`.
- Logo: the flame, from `docs/reference/logo-flame-source.png` (1266x1242, from the user) -> `media/moodyfin/logo.png`, `resources/icon.png`.
- Accent colour: changeable in the skin settings.
- Studio logos: the 21 from the reference theme (`src/.../Assets/studio_*.svg`), white PNGs (`tools/build_studios.sh`).
  Each logo stands for one or more library studio names (Home.xml `MFStudio` items); click = helper `action=studio`.
- Hero / Top 10 come from the library (no TMDB): hero = newest unwatched with a backdrop; Top 10 = best rated added lately.
- Top 10 style is a skin setting `mf.top10numbers`: off = rank badges + #1 wide card (default), on = outlined numbers.
- First milestone: the Home page.
- Repo is private for now and will go public later, so keep licences and third-party notices correct from day one
  (`THIRD-PARTY-NOTICES.md`).

## Look (from the Jellyfin theme — keep in sync with the reference)
- **Never guess a look.** Take sizes, fonts, colours and spacing from the theme's source (`web-src/js/NN-*.js` style
  blocks, `web-src/theme.css`, `look/Inject/**/*.css`). If it can't be found there, ask the user for the CSS.
  Theme CSS px are about MoodyFin skin units (their posters ~188 px, ours 190); text may go 1-2 px up for a TV.
- Made from the theme's source so far: hover card (`35-hover-preview.js`), time-left notch (`03-time-remaining.js`
  tbNotch), New episode / season tags (`08-new-episode-tags.js`).
- Remote first: no buttons inside the hover card (user's call: they can't be reached without breaking a row's
  left / right). Don't add focusable things inside cards.
- Background `#000`, surface `#101113`, raised `#1a1c20`, border `#26292e`, text `#f1f2f4`, muted `#969aa1`.
- Accent: cyan `#5CD8FA` (sampled from the screenshots); presets in `colors/`.
- Fonts: **Bebas Neue** (titles, row headings, uppercase), **Funnel Sans** (body). Both SIL OFL — ship TTF in `fonts/` with licences.
- Cards: 12px corners (diffuse masks), wide thumbs for Continue Watching with progress bar + "Xm left", posters elsewhere.
- **The user's Jellyfin posters already carry genre • ★ rating at the bottom and quality badges at the top** (better-posters).
  Never draw those on posters (it doubles them). Badge strips in `media/moodyfin/badges/` are for places without posters.
- Row headings: Bebas, accent bar on the left.
- Header: logo + library stats left, centred dark pill nav, avatar right.
- Hero: full-bleed fanart, clearlogo (or Bebas title), rating · year · type · genres, plot, Play / More info.
- Ambient background: blurred, dimmed fanart of the focused item behind every page.

## Layout
- `skin.moodyfin/` — the skin. **Fork of Estuary from Kodi `21.3-Omega`** (`xbmc/xbmc` repo, `addons/skin.estuary`,
  loose media, not the packed `Textures.xbt` in Program Files). Estuary screens we don't redesign keep working and are
  restyled through colours/fonts/textures only.
  - `xml/Font.xml` — Default fontset: Funnel Sans (Regular body, Bold for `*_title`), Bebas for `font_MainMenu`.
    MoodyFin fonts are `mf_*` (`mf_heading36/48/72/120` Bebas, `mf_semibold*`, `mf_medium*`). Every `mf_*` font must
    also exist in the Arial fontset.
  - `colors/defaults.xml` — `mf_*` tokens + Estuary names mapped onto them. Other files there = accent presets
    (override only the accent names). New accent-coloured things use `mf_accent`.
  - `media/moodyfin/` — MoodyFin's own textures (logo, masks, badges). Keep Estuary's media where it is.
  - Funnel Sans static weights were cut from the Google Fonts variable font with fontTools (`wght` 400/500/600/700).
  - `xml/Includes_MoodyFin.xml` — MoodyFin includes: `MFAmbient`, `MFHeader`, `MFRowHeading`, cards (`MFPosterCard`,
    `MFThumbCard`, `MFTop10Wide`, `MFCastCard`), `MFPosterRow`, details variables (`MFVideoLine`, `MFAudioLine`, ...).
    `xml/Home.xml`, `xml/DialogVideoInfo.xml` (details), `xml/MyVideoNav.xml` (library: views 520 posters, 521 episodes,
    522 list; SetFocus(520) = current view) and `xml/Custom_1150_MoodyFinSearch.xml` (search, window 11150 in Python)
    are MoodyFin's own; Estuary's versions are gone. Player: `VideoOSD.xml` (panel), `DialogSeekBar.xml` (seek bar and
    pause screen), `MoodyFin-UpNext.xml` (opened by the helper's `upnext.py`), `Startup.xml` (splash),
    `LoginScreen.xml` (profile picker). Estuary's other screens are restyled globally: `button_focus` is a soft light
    highlight (not the accent), and `media/dialogs/dialog-bg.png` + `media/buttons/dialogbutton-*.png` are redrawn
    rounded by `tools/build_media.sh` (same sizes/borders as Estuary's).
  - Details page = Kodi's video info dialog. Its `ListItem.*` is always the dialog's item. Kodi ids: 8 Play, 11 Trailer,
    50 Cast (Kodi fills it). Cards open it through the helper (`action=info`), which loads the whole record + cast.
- `script.moodyfin.helper/` — Python helper the skin requires:
  - plugin rows `plugin://script.moodyfin.helper/?row=hero|continue|top10[&part=first|rest]|latest|recentmovies|recentshows`
    (`resources/lib/rows.py`; `items.py` keeps dbid/mediatype/file so Play/resume/Info work; MoodyFin values are
    `ListItem.Property(mf.*)`, listed in the docstring of `items.py`)
  - service: `Window(Home).Property(MoodyFin.Stats|Reload|Ambient)`; the ambient blur reads its picture from label 9990
  - `RunScript(script.moodyfin.helper,action=studio|info|watched|play|playnext,...)` (docstring in `actions.py`)
- `tools/` — `build_media.sh` (masks, pills, gradients, icons, badge strips, Top 10 numbers), `build_studios.sh`,
  `build_fonts.py` (Funnel Sans static weights + star), `kodi.py` (drive the local Kodi), `icons/` (Material Symbols SVGs).
- `docs/reference/` — screenshots of the Jellyfin theme + logo source. Not shipped.

## Dev workflow
- `skin.moodyfin` and `script.moodyfin.helper` are **junctions** in `%APPDATA%\Kodi\addons\` (symlinks need admin here).
- Local Kodi 21.3 on this PC, JSON-RPC on 127.0.0.1:9090: `python tools/kodi.py restart|keys|shot|info|bool|log`.
  The user said I may use it for testing. Its window is 2560x1369, so Kodi uses the **2040x1080** layout: never
  hard-code 1920 widths; use `right`, `centerleft`, `100%`.
- Restart Kodi to pick up changes (`tools/kodi.py restart`). `ReloadSkin()` from a script crashed Kodi.
- Jellyfin for Kodi asks "N updates pending... Proceed anyway?" at start: answer **No** (the restart command does).
- If Kodi is minimized it stops drawing: screenshots fail and visibility doesn't update. Don't restore it over the
  user's work; ask.
- Log: `%APPDATA%\Kodi\kodi.log` (helper lines start with `[moodyfin]`).
- Never edit files in `C:\Program Files\Kodi`.

## Kodi gotchas (learned the hard way)
- Constants are used by bare name (`<left>mf_gutter</left>`); `$CONSTANT[...]` doesn't exist.
- A button's `textoffsetx` applies on both sides: icon + text buttons use separate label/image controls.
- Every item in a list gets the size of the first layout: a wider item (Top 10 #1) needs its own list.
- A grouplist only moves focus between its direct children: rows (group = heading + list) need explicit
  `onup`/`ondown` to the neighbouring row **groups**; a hidden group passes focus on through its own onup/ondown.
- Home scrolling = stacked conditional slide animations on grouplist 9000 (one per block above the focused row).
- Infolabel booleans over JSON-RPC: `XBMC.GetInfoBooleans` (GetInfoLabels returns "" for them).
- A list with its own `<onclick>` replaces Kodi's default click; `$INFO[ListItem.*]` in it is the clicked item.
- A `diffuse` mask doesn't follow `aspectratio scale` cropping: give masked backdrops a 16:9 box with `stretch`.
- `$VAR[]` doesn't work in a button's texture; use a `togglebutton` with `usealttexture`.
- Image `colordiffuse="$VAR[...]"` didn't update reliably: use two images with visible conditions.
- Autoscroll: `<autoscroll time="9000">` - `time` is the interval between moves.
- A list inside a hidden group isn't processed: its content won't reload when its path changes. Keep it visible
  while it loads (search sets `mf.searching` for a few seconds).
- Custom window `Custom_1150_*.xml` is window 11150 for Python (`xbmcgui.Window`); the skin's `Window(1150)` adds 10000.
- Media windows: `<defaultcontrol>` / SetFocus must name a view id that exists (520), not 50.
- Kodi doesn't draw VideoFullScreen.xml's own controls over a paused video: overlays go in DialogSeekBar (open during
  playback; the skin's `<visible>` decides when it shows).
- An empty `<texturebg />` on a progress control makes the fill draw at the image's own size: give it a transparent bg.
- JSON-RPC `Addons.ExecuteAddon` on the helper runs its *plugin* entry, not script.py: use RunScript via devbuiltin.
- Python `getInfoLabel("Container(id).ListItemAbsolute(n).SortLetter")` + `SetFocus(id,n,absolute)` = letter jump.
- Lists clip at their edges: anything drawn outside an item (focus ring at -3) needs the card inset (cards sit 4 px
  in; lists are 4 px up/left of where the cards appear).
- Hover card (`MFPopupRow` / `MFPopupRowTop10` / `MFPopupGrid`, written by `tools/build_popup.py`): its own control
  after the list, moved over the focused slot by conditional slides on Container.Position (or Column/Row); shows on
  `System.IdleTime(1)`. Any input hides it, **including kodi.py's screenshot action**: check it with a Windows screen
  capture of the Kodi window instead.
- Test playback with a local ffmpeg clip (`testsrc2`), muted, never a library title (it would change Jellyfin progress).
