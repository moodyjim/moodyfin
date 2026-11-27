#!/usr/bin/env bash
# MoodyFin textures: card masks, pills, rounded rects, gradients, icons. All white (tinted in the skin with colordiffuse).
# Needs ImageMagick 7. Icons: Material Symbols Rounded (Apache 2.0), SVGs in tools/icons/.
set -euo pipefail
cd "$(dirname "$0")"
M=../skin.moodyfin/media/moodyfin
mkdir -p "$M/masks" "$M/shapes" "$M/icons"

rr() { # rr <w> <h> <radius> <out> : filled white rounded rect
  magick -size "$1x$2" xc:none -fill white -draw "roundrectangle 0,0,$(($1-1)),$(($2-1)),$3,$3" "$4"; }
ring() { # ring <w> <h> <radius> <stroke> <out> : rounded outline
  local s=$4; magick -size "$1x$2" xc:none -fill none -stroke white -strokewidth "$s" \
    -draw "roundrectangle $((s/2)),$((s/2)),$(($1-1-s/2)),$(($2-1-s/2)),$3,$3" "$5"; }

# card masks (exact control sizes; diffuse is stretched to the control)
rr 190 285 12 "$M/masks/poster.png"
rr 356 200 12 "$M/masks/thumb.png"
rr 396 285 12 "$M/masks/wide.png"
rr 160 240 12 "$M/masks/poster_small.png"

# pills: height h, width 2h, used with border="h/2,0,h/2,0" so only the middle stretches
for h in 40 48 56 64; do
  rr $((h*2)) $h $((h/2)) "$M/shapes/pill_$h.png"
  ring $((h*2)) $h $((h/2)) 2 "$M/shapes/pill_line_$h.png"
done
# rounded rects for panels/badges, used with border="r"
rr 48 48 12 "$M/shapes/rr12.png"; ring 48 48 12 3 "$M/shapes/rr12_line.png"
rr 24 24 6 "$M/shapes/rr6.png"
magick -size 64x64 xc:none -fill white -draw "circle 31.5,31.5 31.5,0" "$M/shapes/circle.png"
magick -size 64x64 xc:none -fill none -stroke white -strokewidth 3 -draw "circle 31.5,31.5 31.5,2" "$M/shapes/circle_line.png"

# gradients (white, alpha ramps)
magick -size 8x512 gradient:none-white "$M/shapes/grad_down.png"      # transparent top -> white bottom
magick -size 8x512 gradient:white-none "$M/shapes/grad_up.png"        # white top -> transparent bottom
magick -size 8x1024 gradient:none-white -rotate -90 "$M/shapes/grad_right.png"  # transparent left -> white right
magick -size 8x1024 gradient:white-none -rotate -90 "$M/shapes/grad_left.png"   # white left -> transparent right

# icons, white on transparent, 96 px
for f in icons/*.svg; do
  n=$(basename "$f" .svg)
  magick -background none -density 400 "$f" -resize 96x96 -fill white -colorize 100 "$M/icons/$n.png"
done
ls -R "$M" | head -60

# quality badge strips: every combination of resolution, HDR and audio, e.g. badges/1080p_DolbyDigital.png
# (the helper sets ListItem.Property(mf.badge) to the file name). White pills, black text, like the Jellyfin theme's.
FONT=../skin.moodyfin/fonts/FunnelSans-Bold.ttf
mkdir -p "$M/badges"; rm -f "$M/badges/"*.png
key() { echo "$1" | tr -d ' ' | sed 's/+/plus/g'; }
for res in "4K" "1080p" "720p" "SD" ""; do
 for hdr in "Dolby Vision" "HDR10" "HDR10+" "HLG" ""; do
  for aud in "Dolby TrueHD" "Dolby Digital+" "Dolby Digital" "DTS-HD" "DTS" ""; do
   parts=(); for p in "$res" "$hdr" "$aud"; do [ -n "$p" ] && parts+=("$p"); done
   [ ${#parts[@]} -eq 0 ] && continue
   files=(); name=""
   for i in "${!parts[@]}"; do
     t="$(mktemp --suffix=.png)"
     w=$(( $(magick -font "$FONT" -pointsize 21 label:"${parts[$i]}" -format '%w' info:) + 16 ))
     magick -size ${w}x32 xc:none -fill white -draw "roundrectangle 0,0,$((w-1)),31,7,7"        -fill black -font "$FONT" -pointsize 21 -gravity center -annotate +0+1 "${parts[$i]}" +repage "$t"
     files+=("$t"); [ -n "$name" ] && name="${name}_"; name="${name}$(key "${parts[$i]}")"
     [ $i -lt $((${#parts[@]}-1)) ] && { s="$(mktemp --suffix=.png)"; magick -size 7x32 xc:none "$s"; files+=("$s"); }
   done
   magick "${files[@]}" -background none +append +repage "$M/badges/$name.png"
   rm -f "${files[@]}"
  done
 done
done
echo "badges: $(ls "$M/badges" | wc -l)"

# hero mask (used as diffuse on the hero picture): the Jellyfin theme's --ue-hero-backdrop-mask with the ambient background:
# opaque to 45 %, 0.75 at 62 %, 0.35 at 80 %, transparent at the bottom
magick -size 16x512 xc:white -alpha set -channel A \
  -fx "yy=j/h; yy<0.45 ? 1 : (yy<0.62 ? 1-(yy-0.45)/0.17*0.25 : (yy<0.8 ? 0.75-(yy-0.62)/0.18*0.4 : 0.35-(yy-0.8)/0.2*0.35))" \
  +channel "$M/masks/hero.png"
# card shades (white; tinted black in the skin), already cut to the card's rounded corners
magick -size 190x285 xc:white -alpha set -channel A -fx "yy=j/h; yy<0.5 ? 0 : (yy-0.5)/0.5*0.92" +channel \
  "$M/masks/poster.png" -compose DstIn -composite "$M/masks/poster_shade.png"
magick -size 356x200 xc:white -alpha set -channel A -fx "yy=j/h; yy<0.28 ? 0.55*(1-yy/0.28) : (yy>0.7 ? (yy-0.7)/0.3*0.6 : 0)" +channel \
  "$M/masks/thumb.png" -compose DstIn -composite "$M/masks/thumb_shade.png"
magick -size 396x285 xc:white -alpha set -channel A -fx "xx=i/w; yy=j/h; max(0.9*(1-xx/0.75), yy>0.55 ? (yy-0.55)/0.45*0.9 : 0)" +channel \
  "$M/masks/wide.png" -compose DstIn -composite "$M/masks/wide_shade.png"
# Top 10 numbers, outlined Bebas Neue
BEBAS=../skin.moodyfin/fonts/BebasNeue-Regular.ttf
mkdir -p "$M/numbers"
for n in 1 2 3 4 5 6 7 8 9 10; do
  magick -size 700x460 xc:none -font "$BEBAS" -pointsize 400 -fill none -stroke white -strokewidth 5 \
    -gravity center -annotate +0+0 "$n" -trim +repage "$M/numbers/$n.png"
done
echo "masks + numbers done"
