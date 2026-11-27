<div align="center">
<img src="skin.moodyfin/resources/icon.png" alt="MoodyFin" height="128px" />

# MoodyFin

A Kodi 21 (Omega) skin that brings the Jellyfin theme's look to Kodi.
</div>

Made for a Jellyfin library synced with [Jellyfin for Kodi](https://github.com/jellyfin/jellyfin-kodi), and for
remote control on CoreELEC boxes.

> Work in progress. Right now it is Estuary with MoodyFin's fonts, colours and icon. The Home page comes next.

## Install (development)

Link the skin folder into Kodi's add-ons folder, restart Kodi, then pick **MoodyFin** in
*Settings > Interface > Skin*.

```powershell
# Windows (a junction needs no admin rights)
New-Item -ItemType Junction -Path "$env:APPDATA\Kodi\addons\skin.moodyfin" -Target "C:\workflow\kodi\moodyfin\skin.moodyfin"
```

## Accent colour

*Settings > Interface > Skin > Colours*: Default (cyan), Molten, Red, Blue, Green, Purple, Amber, Pink, White.

## Credits

- Based on [Estuary](https://github.com/xbmc/xbmc/tree/master/addons/skin.estuary) by phil65 and Ichabod Fletchman
  (CC BY-SA 4.0 / GPL-2.0). See `skin.moodyfin/LICENSE.txt`.
- Fonts: [Bebas Neue](https://github.com/dharmatype/Bebas-Neue) and [Funnel Sans](https://github.com/Dicotype/Funnel)
  (SIL Open Font License 1.1), Noto Mono (SIL OFL). Licences in `skin.moodyfin/fonts/`.
- Look: [Jellyfin theme](https://github.com/moodyjim/moodyjim-jellyfin-theme) for Jellyfin.

Unofficial. Not affiliated with Team Kodi or the Jellyfin project.
