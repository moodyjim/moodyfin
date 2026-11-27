<div align="center">
<img src="skin.moodyfin/resources/icon.png" alt="MoodyFin" height="128px" />

# MoodyFin

A Kodi 21 (Omega) skin that brings the Jellyfin theme's look to Kodi.
</div>

Made for a Jellyfin library synced with [Jellyfin for Kodi](https://github.com/jellyfin/jellyfin-kodi), and for
remote control on CoreELEC boxes.

> Work in progress. Home and the details pages are done; the other screens are still Estuary's, in MoodyFin's fonts
> and colours.

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

## Details page

Opened from a card or More info. Blurred backdrop, title logo, poster, the title's facts, **Play** (resume), **Play
next** for shows, **Trailer** (when it can play), **Watched**, the file's video / audio / subtitles, plot, tags and
people; then Next Up and Seasons for shows, Cast & Crew, the movie's Collection and More Like This
(from [Moody Similar](https://github.com/moodyjim) when installed).

## Settings

- **Accent colour:** *Settings > Interface > Skin > Colours*: Default (cyan), Molten, Red, Blue, Green, Purple, Amber,
  Pink, White.
- **Top 10 style:** *Skin settings > General > Top 10: big outlined numbers*. Off (default): rank badges, with #1 as a
  wide card.

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
