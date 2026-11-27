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
  - Screenshots: `docs/home.jpg`, `docs/rows.jpg`, `docs/login.jpg`
- Sibling Kodi projects (patterns to reuse, never edit from here):
  - `c:\workflow\kodi\moodyskin` — MoodySkin (BBS look) + `plugin.video.moodyskin` helper (PIL artwork, home rows, service)
  - `c:\workflow\kodi\moodyjim-skin` — Estuary fork + `plugin.video.moodysimilar`
- Remote: https://github.com/moodyjim/moodyfin.git

## Target
- Kodi 21 Omega, `xbmc.gui` 5.17.0, `xbmc.python` 3.0.1. Windows dev box, 1920x1080 skin resolution.
- Library comes from `plugin.video.jellyfin` (Jellyfin for Kodi, native DB sync mode).

## Look (from the Jellyfin theme — keep in sync with the reference)
- Background `#000`, surface `#101113`, raised `#1a1c20`, border `#26292e`, text `#f1f2f4`, muted `#969aa1`.
- Accent: cyan `#4DD8F5`-ish as on the screenshots (user-selectable).
- Fonts: **Bebas Neue** (titles, row headings, uppercase), **Funnel Sans** (body). Both SIL OFL — ship TTF in `fonts/` with licences.
- Cards: 12px corners (diffuse masks), wide thumbs for Continue Watching with progress bar + "Xm left", posters elsewhere.
- Row headings: Bebas, accent bar on the left.
- Header: logo + library stats left, centred dark pill nav, avatar right.
- Hero: full-bleed fanart, clearlogo (or Bebas title), rating · year · type · genres, plot, Play / More info.
- Ambient background: blurred, dimmed fanart of the focused item behind every page.

## Layout (planned)
- `skin.moodyfin/` — the skin (`addon.xml`, `xml/`, `colors/`, `fonts/`, `media/`, `language/`, `extras/`)
- `script.moodyfin.helper/` — Python helper (blur cache, stats, time left, hero picks). Only if the skin needs it.

## Dev workflow
- Skin is symlinked into `%APPDATA%\Kodi\addons\` (same as moodyskin). Edit here, then `ReloadSkin()` in Kodi.
- Log: `%APPDATA%\Kodi\kodi.log`. Check it after every reload for XML errors.
- Never edit files in `C:\Program Files\Kodi`.
