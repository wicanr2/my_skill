#!/usr/bin/env bash
# QA 用 helper:啟動 AppImage、模擬按鍵、截圖到 docs/qa/
set -eu

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
QA_DIR="$HERE/docs/qa"
mkdir -p "$QA_DIR"

screenshot() {
    local name="$1"
    local wid
    wid="$(DISPLAY=:1 wmctrl -l | grep "Akalabeth T-Chinese" | head -1 | awk '{print $1}')"
    if [ -z "$wid" ]; then
        echo "  [screenshot $name] no game window"
        return 1
    fi
    DISPLAY=:1 wmctrl -ia "$wid" 2>/dev/null || true
    sleep 0.5
    DISPLAY=:1 xwd -id "$wid" -out "/tmp/qa-$name.xwd" 2>/dev/null
    python3 - "$name" <<'PYEOF'
import sys, struct
from PIL import Image
from pathlib import Path
name = sys.argv[1]
src = Path(f"/tmp/qa-{name}.xwd")
dst = Path(f"~/game/AK_CHT/docs/qa/{name}.png")
data = src.read_bytes()
hdr = struct.unpack(">25I", data[:100])
hs, _, _, _, w, h, _, _, _, _, _, _, bpl = hdr[:13]
po = hs + hdr[19] * 12
img = Image.new("RGB", (w, h))
raw = data[po:po+bpl*h]
for y in range(h):
    for x in range(w):
        off = y*bpl+x*4
        b0,b1,b2,_ = raw[off:off+4]
        img.putpixel((x,y), (b2,b1,b0))
img.save(dst)
print(f"  saved {dst}")
PYEOF
    rm -f "/tmp/qa-$name.xwd"
}

press() {
    local key="$1"
    local wid
    wid="$(DISPLAY=:1 wmctrl -l | grep "Akalabeth T-Chinese" | head -1 | awk '{print $1}')"
    if [ -n "$wid" ]; then
        DISPLAY=:1 xdotool key --window "$wid" "$key" 2>/dev/null
    fi
}

type_text() {
    local text="$1"
    local wid
    wid="$(DISPLAY=:1 wmctrl -l | grep "Akalabeth T-Chinese" | head -1 | awk '{print $1}')"
    if [ -n "$wid" ]; then
        DISPLAY=:1 xdotool type --window "$wid" "$text" 2>/dev/null
    fi
}

case "${1:-}" in
    screenshot) shift; screenshot "$@";;
    press) shift; press "$@";;
    type) shift; type_text "$@";;
    *) echo "usage: $0 {screenshot NAME|press KEY|type TEXT}"; exit 1;;
esac
