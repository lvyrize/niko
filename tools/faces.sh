#!/usr/bin/env bash
set -e
export LC_ALL=C
SRC="$1"; MASK="$2"; OUT="$3"
W=$(mktemp -d)
SKIN="#E49D9A"; INK="#5e231c"; MOUTH_IN="#a8433f"; EYE="#ffd200"

magick "$SRC" -resize 1024x1024 "$W/base.png"
magick "$MASK" -resize 1024x1024 -threshold 50% "$W/eye.png"
magick "$W/base.png" -region 250x150+645+175 -fuzz 22% -fill "$SKIN" -opaque "#74322f" +region "$W/nolid.png"
magick "$W/nolid.png" \( -size 1024x1024 xc:"$SKIN" \) "$W/eye.png" -composite "$W/noeyes.png"

arc() {
    local pts="" t v u
    for t in $(seq 0 0.1 1); do
        v=$(awk -v t=$t 'BEGIN{printf "%.1f", 540 + 300*t}')
        u=$(awk -v t=$t -v m=$1 -v b=$2 'BEGIN{printf "%.1f", m + b*sin(3.14159*t)}')
        if [ -z "$pts" ]; then pts="M $u,$v"; else pts="$pts L $u,$v"; fi
    done
    echo "path '$pts'"
}

magick "$W/noeyes.png" -fill none -stroke "$INK" -strokewidth 22 -draw "stroke-linecap round $(arc 905 30)" "$W/e_closed.png"
magick "$W/noeyes.png" -fill none -stroke "$INK" -strokewidth 24 -draw "stroke-linecap round $(arc 965 -48)" "$W/e_happy.png"
LID=$(arc 962 22)
LIDPOLY=$(echo "$LID" | sed "s/^path '//; s/'\$//; s/M //; s/ L / /g")
magick "$W/eye.png" \( -size 1024x1024 xc:black -fill white -draw "polygon 760,520 $LIDPOLY 760,860" -draw "rectangle 760,440 860,940" \) -compose multiply -composite "$W/upper.png"
magick "$W/nolid.png" \( -size 1024x1024 xc:"$SKIN" \) "$W/upper.png" -compose over -composite \
    -fill none -stroke "$INK" -strokewidth 18 -draw "stroke-linecap round $LID" "$W/e_half.png"
magick "$W/base.png" -fill "$EYE" -stroke none -draw "ellipse 919,690 62,32 0,360" \
    -fill "$INK" -draw "ellipse 919,690 26,14 0,360" "$W/e_wide.png"
cp "$W/base.png" "$W/e_open.png"

mouth() {
    local in="$1" kind="$2" out="$3"
    if [ "$kind" = "cat" ]; then cp "$in" "$out"; return; fi
    magick "$in" -fill "$SKIN" -stroke none -draw "rectangle 528,466 612,504" "$out"
    case "$kind" in
        o)     magick "$out" -fill "$INK" -draw "ellipse 569,488 12,14 0,360" -fill "$MOUTH_IN" -draw "ellipse 569,491 7,8 0,360" "$out" ;;
        smile) magick "$out" -fill none -stroke "$INK" -strokewidth 7 -draw "stroke-linecap round path 'M 540,478 Q 569,510 598,478'" "$out" ;;
        frown) magick "$out" -fill none -stroke "$INK" -strokewidth 7 -draw "stroke-linecap round path 'M 545,498 Q 569,476 593,498'" "$out" ;;
        dot)   magick "$out" -fill "$INK" -draw "ellipse 569,487 4,3 0,360" "$out" ;;
    esac
}

mkdir -p "$OUT"
mouth "$W/e_open.png"   cat   "$W/neutral.png"
mouth "$W/e_open.png"   o     "$W/talk.png"
mouth "$W/e_open.png"   smile "$W/smile.png"
mouth "$W/e_closed.png" cat   "$W/blink.png"
mouth "$W/e_closed.png" dot   "$W/asleep.png"
mouth "$W/e_happy.png"  smile "$W/happy.png"
mouth "$W/e_happy.png"  o     "$W/laugh.png"
mouth "$W/e_half.png"   cat   "$W/sleepy.png"
mouth "$W/e_half.png"   frown "$W/sad.png"
mouth "$W/e_wide.png"   o     "$W/surprised.png"
mouth "$W/e_open.png"   frown "$W/worried.png"
for f in neutral talk smile blink asleep happy laugh sleepy sad surprised worried; do
    magick "$W/$f.png" -resize 512x512 "$OUT/face_$f.png"
done
rm -rf "$W"
ls "$OUT"
