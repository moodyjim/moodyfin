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
magick -size 356x200 xc:white -alpha set -channel A -fx "yy=j/h; yy>0.7 ? (yy-0.7)/0.3*0.6 : 0" +channel \
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

# details page: big poster mask, cast photo mask
rr 400 600 16 "$M/masks/poster_large.png"
# icon buttons (128 px, shown at 64): normal = white icon, focus = white square + black icon,
# on = pale blue square + black icon (the Jellyfin theme's "watched" state)
mkdir -p "$M/buttons"
for n in play_arrow movie check skip_next info_outline sort_by_alpha swap_vert visibility filter_alt arrow_back subtitles music_note replay_10 forward_30 pause tune stop close; do
  magick -background none -density 400 "icons/$n.svg" -resize 60x60 -fill white -colorize 100 \
    -gravity center -extent 128x128 "$M/buttons/$n.png"
  magick -background none -density 400 "icons/$n.svg" -resize 60x60 -fill black -colorize 100 -gravity center -extent 128x128 /tmp/mf_black.png
  magick -size 128x128 xc:none -fill white -draw "roundrectangle 0,0,127,127,22,22" /tmp/mf_black.png -gravity center -composite "$M/buttons/${n}_focus.png"
  magick -size 128x128 xc:none -fill "#A9BBCC" -draw "roundrectangle 0,0,127,127,22,22" /tmp/mf_black.png -gravity center -composite "$M/buttons/${n}_on.png"
done
rm -f /tmp/mf_black.png
echo "buttons done"
ring 24 24 5 2 "$M/shapes/rr6_line.png"
# details backdrop mask: opaque to 30 %, gone at 72 % (the image box is 16:9, nothing cropped, so the mask lines up)
magick -size 16x512 xc:white -alpha set -channel A -fx "yy=j/h; yy<0.3 ? 1 : (yy<0.72 ? 1-(yy-0.3)/0.42 : 0)" +channel "$M/masks/details.png"
# player: big play / pause (white circle, black icon), 160 px
for n in play_arrow pause; do
  magick -background none -density 400 "icons/$n.svg" -resize 84x84 -fill black -colorize 100 -gravity center -extent 160x160 /tmp/mf_icon.png
  magick -size 160x160 xc:none -fill white -draw "circle 79.5,79.5 79.5,1" /tmp/mf_icon.png -gravity center -composite "$M/buttons/${n}_big.png"
done
rm -f /tmp/mf_icon.png
magick -size 176x176 xc:none -fill none -stroke white -strokewidth 5 -draw "circle 87.5,87.5 87.5,4" "$M/shapes/ring_big.png"
rr 64 64 24 "$M/shapes/rr24.png"; ring 64 64 24 2 "$M/shapes/rr24_line.png"
# splash: soft glow behind the flame
magick ../docs/reference/logo-flame-source.png -trim +repage -resize 300x300 -background none -gravity center -extent 640x640 -channel A -blur 0x60 -level 0,60% +channel -fill "#FD5004" -colorize 100 "$M/logo_glow.png"

# Estuary overrides: rounded dialog panels and dialog buttons (same sizes and borders as Estuary's, so every dialog
# keeps its layout). dialog-bg: border 21 in the XML -> panel from 9 px, radius 12. dialog buttons: border 30/40.
E=../skin.moodyfin/media
magick -size 80x80 xc:none -fill "rgba(16,17,19,0.95)" -draw "roundrectangle 9,9,70,70,12,12" \
  -fill none -stroke "rgba(255,255,255,0.10)" -strokewidth 1 -draw "roundrectangle 9.5,9.5,69.5,69.5,12,12" "$E/dialogs/dialog-bg.png"
magick -size 80x80 xc:none -fill white -draw "roundrectangle 12,12,67,67,16,16" "$E/buttons/dialogbutton-fo.png"
magick -size 80x80 xc:none -fill "rgba(255,255,255,0.08)" -draw "roundrectangle 12,12,67,67,16,16" "$E/buttons/dialogbutton-nofo.png"
# hover card buttons (the Jellyfin theme's hover preview: 38 px circles), drawn at 96 px.
# play = white disc + black icon (26/38); others = rgba(40,40,44,.6) disc, light ring, white icon (19/38);
# check_on = the watched state's lit ring; check_tick = the tick alone (tinted with the accent in the skin)
icon() { magick -background none -density 400 "icons/$1.svg" -resize ${2}x${2} -fill "$3" -colorize 100 -gravity center -extent 96x96 "$4"; }
icon play_arrow 66 black /tmp/mf_i.png
magick -size 96x96 xc:none -fill white -draw "circle 47.5,47.5 47.5,1" /tmp/mf_i.png -gravity center -composite "$M/buttons/pop_play_arrow.png"
for n in favorite check expand_more; do
  icon $n 48 white /tmp/mf_i.png
  magick -size 96x96 xc:none -fill "rgba(40,40,44,0.6)" -stroke "rgba(255,255,255,0.45)" -strokewidth 3 -draw "circle 47.5,47.5 47.5,3" /tmp/mf_i.png -gravity center -composite "$M/buttons/pop_$n.png"
done
magick -size 96x96 xc:none -fill "rgba(255,255,255,0.12)" -stroke white -strokewidth 3 -draw "circle 47.5,47.5 47.5,3" "$M/buttons/pop_check_on.png"
icon check 48 white "$M/buttons/pop_check_tick.png"
rm -f /tmp/mf_i.png
# hover card backdrop: rounded top corners only (336x189, 16:9)
magick -size 336x215 xc:none -fill white -draw "roundrectangle 0,0,335,214,12,12" -crop 336x189+0+0 +repage "$M/masks/pop.png"

# Continue Watching "time left" notch (the Jellyfin theme's 03-time-remaining.js tbNotch): the picture is cut away around the
# badge, inner corner r=10, joins r2=6, card corners 12. One mask per badge width: s 70 ("36m left"), m 81
# ("1h 3m left"), l 88 ("1h 13m left"); badge 24 tall (11 px SemiBold + 4/8 px padding, a size up for TV).
notch() { # notch <badge w> <out>
  local sw=356 sh=200 cr=12 r=10 r2=6 bw=$1 bh=24
  magick -size ${sw}x${sh} xc:none -fill white -draw "path 'M $((bw+r2)) 0 L $((sw-cr)) 0 Q $sw 0 $sw $cr L $sw $((sh-cr)) Q $sw $sh $((sw-cr)) $sh L $cr $sh Q 0 $sh 0 $((sh-cr)) L 0 $((bh+r2)) Q 0 $bh $r2 $bh L $((bw-r)) $bh Q $bw $bh $bw $((bh-r)) L $bw $r2 Q $bw 0 $((bw+r2)) 0 Z'" "$2"
}
notch 70 "$M/masks/thumb_notch_s.png"; notch 81 "$M/masks/thumb_notch_m.png"; notch 88 "$M/masks/thumb_notch_l.png"
# "New episode" / "New season" tag (08-new-episode-tags.js): #E50914, top corners 3 px, flush with the poster's bottom
magick -size 24x24 xc:none -fill white -draw "roundrectangle 0,0,23,23,3,3" -draw "rectangle 0,12,23,23" "$M/shapes/tag_top.png"
