#!/usr/bin/env bash
# Studio logos: the Jellyfin theme's SVGs (KefinTweaks, MIT) -> white PNGs for Kodi.
# Same look as the theme's CSS `filter: brightness(0) invert(1)`: every drawn pixel becomes white, alpha kept.
# Needs ImageMagick 7 (magick) with the librsvg delegate.
set -euo pipefail
SRC="${1:-$(ls -d /c/workflow/jellyfin/moodyjim-jellyfin-theme/src/Jellyfin.Plugin.*/Assets | head -1)}"
OUT="$(dirname "$0")/../skin.moodyfin/media/moodyfin/studios"
mkdir -p "$OUT"
for f in "$SRC"/studio_*.svg; do
  name="$(basename "$f" .svg)"; name="${name#studio_}"
  magick -background none -density 600 "$f" -trim +repage \
    -resize 480x200 -fill white -colorize 100 "$OUT/$name.png"
  echo "$name $(magick identify -format '%wx%h' "$OUT/$name.png")"
done
