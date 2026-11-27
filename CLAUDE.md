# CLAUDE.md

## Communication
- Blunt, short replies.
- If I say "talk", don't touch any code — just answer.

## Editing rules
- Only change what I explicitly ask.
- Never commit API keys (TMDB, Jellyfin tokens). Before every push, scan the diff for 32-hex strings and abort if found.
- Commit messages must end with: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`
- Commit or push only when I ask.

## What this is
MoodyFin: a Kodi skin that recreates the Jellyfin theme on Kodi.
- Reference theme (read-only, never edit): `c:\workflow\jellyfin\moodyjim-jellyfin-theme`
  - Look/tokens: `look/Inject/Theme/ue-tokens.css`, `ue-ambient.css`; hero `look/Inject/Hero/`; details `look/Inject/Details/`
  - Features: `web-src/js/NN-*.js`, `web-src/theme.css`
- Reference screenshots (copied into this repo): `docs/reference/`
  - `home.jpg`, `home-rows.jpg`, `home-wide.png` — header, hero, studio row, Continue Watching, Top 10 (#1 wide card), Latest / Recently added rows
  - `details-movie.png`, `details-series.png` — centred clearlogo, poster card with badges + "Genre • ★ x", info bar, track rows, cast, collections, more like this, next up, seasons
  - `library-movies.png` — title + count, toolbar, 12-column poster grid, A–Z rail
  - `player-osd.png`, `player-paused.png` — floating glass control panel, "Ends at" pill, clearlogo; pause screen "You're watching"
  - `search.png` — "Discover something new", pill search field, filter chips, sectioned results
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
- Logo: the flame from the reference theme (`docs/logo-white.png`, only 48x48 — needs a larger source for Kodi).
- Accent colour: changeable in the skin settings.
- Studio logos: copy the 22 from the reference theme (`src/.../Assets/studio_*.svg`), converted to PNG (Kodi can't show SVG).
- First milestone: the Home page.
- Repo is private for now and will go public later, so keep licences and third-party notices correct from day one
  (fonts: SIL OFL; studio logos: KefinTweaks, MIT).

## Look (from the Jellyfin theme — keep in sync with the reference)
- Background `#000`, surface `#101113`, raised `#1a1c20`, border `#26292e`, text `#f1f2f4`, muted `#969aa1`.
- Accent: cyan `#4DD8F5`-ish as on the screenshots (user-selectable).
- Fonts: **Bebas Neue** (titles, row headings, uppercase), **Funnel Sans** (body). Both SIL OFL — ship TTF in `fonts/` with licences.
- Cards: 12px corners (diffuse masks), wide thumbs for Continue Watching with progress bar + "Xm left", posters elsewhere.
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
- `script.moodyfin.helper/` — Python helper (blur cache, stats, time left, hero picks). Not created yet.
- `docs/reference/` — screenshots of the Jellyfin theme + logo source. Not shipped.

## Dev workflow
- Skin is symlinked into `%APPDATA%\Kodi\addons\` (same as moodyskin). Edit here, then `ReloadSkin()` in Kodi.
- Log: `%APPDATA%\Kodi\kodi.log`. Check it after every reload for XML errors.
- Never edit files in `C:\Program Files\Kodi`.
