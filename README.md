<div align="center">
<img src="skin.moodyfin/resources/icon.png" alt="MoodyFin" height="128px" />

# MoodyFin

A Kodi 21 (Omega) skin that brings the Jellyfin theme's look to Kodi.
</div>

Made for a Jellyfin library synced with [Jellyfin for Kodi](https://github.com/jellyfin/jellyfin-kodi), and for
remote control on CoreELEC boxes.

> Home, details, library, search, player, splash and sign-in are MoodyFin's own; Estuary's other screens (settings,
> dialogs, music) use MoodyFin's fonts, colours, focus style and rounded panels.

## What's in it

| Folder | What it is |
|---|---|
| `skin.moodyfin/` | The skin (a fork of Estuary). |
| `script.moodyfin.helper/` | The helper the skin needs: Home rows, library stats, the blurred background, studio pages. |
| `tools/` | Scripts that build the skin's pictures and fonts, and drive a local Kodi for testing. |
| `docs/reference/` | Screenshots of the the Jellyfin theme Jellyfin theme, the look MoodyFin copies. |

## Home

- **Header:** logo, library stats, a pill menu (Favorites, Collections, Movies, Shows, Sports, Search) and your profile.
- **Hero:** the newest unwatched titles, one every 9 seconds: backdrop, title logo, rating, year, genres, plot,
  **Play** and **More info**. Left and right on the buttons flip through them.
- **Studios:** 21 studio and streaming logos; each opens that studio's movies or shows.
- **Rows:** Continue Watching & Next Up (time left, progress), Top 10, Latest Releases, Recently Added Movies,
  Recently Added Shows (with a *New season* tag).
- **Ambient background:** a blurred copy of the focused title's picture behind the page.
- **Hover card:** rest on a poster for a second and a wide card shows its backdrop, logo, rating, year, runtime and
  genres.

## Details page

Opened from a card or More info. Blurred backdrop, title logo, poster, the title's facts, **Play** (resume), **Play
next** for shows, **Trailer** (when it can play), **Watched**, the file's video / audio / subtitles, plot, tags and
people; then Next Up and Seasons for shows, Cast & Crew, the movie's Collection and More Like This
(from [Moody Similar](https://github.com/moodyjim) when installed).

## Library and search

- **Library pages** (Favorites, Collections, Movies, Shows, Sports in the menu): title and count, sort, order,
  watched and filter buttons, a poster grid, an episode list for episodes, a plain list for everything else.
- **Search** (magnifier in the menu): type a few letters; movies, shows and episodes whose title contains them.
- **A-Z rail:** on poster pages sorted by name, right from the grid, then a letter.
- **Sign-in page:** turn on Kodi's login screen (*Settings > Profiles > General*) to choose a profile at start.

Tip: to open the details page when you press OK on a movie in a library page (as the Jellyfin theme does), set
*Settings > Media > Videos > Default select action* to *Show information*.

## Player

- **Controls** (OK during playback): a floating glass panel with time, progress, time left, subtitles, audio,
  back 10 s, play / pause, forward 30 s, video settings and stop; the title logo and when it ends.
- **Pause screen:** after 3 s paused, the title, its facts and plot over the dimmed picture.
- **Up Next:** 30 s before an episode ends, the next one with Play now / Cancel; it plays when this one ends.

## Settings

- **Accent colour:** *Settings > Interface > Skin > Colours*: Default (cyan), Molten, Red, Blue, Green, Purple, Amber,
  Pink, White.
- **Top 10 style:** *Skin settings > General > Top 10: big outlined numbers*. Off (default): rank badges, with #1 as a
  wide card.
- **Up Next pop-up:** *Skin settings > General*.

## Install (development)

Link both folders into Kodi's add-ons folder, restart Kodi, enable both in *Add-ons > My add-ons*, then pick
**MoodyFin** in *Settings > Interface > Skin*.

```powershell
# Windows (a junction needs no admin rights)
New-Item -ItemType Junction -Path "$env:APPDATA\Kodi\addons\skin.moodyfin" -Target "C:\workflow\kodi\moodyfin\skin.moodyfin"
New-Item -ItemType Junction -Path "$env:APPDATA\Kodi\addons\script.moodyfin.helper" -Target "C:\workflow\kodi\moodyfin\script.moodyfin.helper"
```

The blurred background needs `script.module.pil` (Kodi on Windows has it). Without it the picture is shown dimmed,
not blurred.

## Credits

Based on [Estuary](https://github.com/xbmc/xbmc/tree/master/addons/skin.estuary) by phil65 and Ichabod Fletchman.
Fonts, icons and studio logos are listed with their licences in [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
The look is the [Jellyfin theme](https://github.com/moodyjim/moodyjim-jellyfin-theme) for Jellyfin.

Unofficial. Not affiliated with Team Kodi or the Jellyfin project.
