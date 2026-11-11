#!/bin/sh
# Screenshot every frame page with headless Chrome, then join into MP4s (one per period). Usage: sh make_animation.sh H
H="$1"; cd "$H/frames" || exit 1
for f in *.html; do
  [ -s "${f%.html}.png" ] || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars --allow-file-access-from-files --window-size=1200,1040 --screenshot="$PWD/${f%.html}.png" "file://$PWD/$f" >/dev/null 2>&1
done
for p in 2025-11 2021-11 2026-11; do
  ffmpeg -y -loglevel error -framerate 1.25 -pattern_type glob -i "$p-*.png" -vf "scale=1200:1040,format=yuv420p" -c:v libx264 -crf 23 -r 25 -movflags +faststart "$H/out/smoke-$p.mp4"
done
ls -la "$H"/out/smoke-*.mp4
# Contact sheet of November 2025 for the article (6 x 5 frames)
ffmpeg -y -loglevel error -pattern_type glob -i "2025-11-*.png" -vf "scale=400:347,tile=6x5:padding=4:color=white" -frames:v 1 -q:v 3 "$H/out/smoke-november-2025.jpg"
ls -la "$H"/out/smoke-*.mp4 "$H"/out/smoke-november-2025.jpg
