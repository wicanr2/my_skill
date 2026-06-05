#!/usr/bin/env bash
# 從 AK_CHT.bas.orig 開始,依序套上所有 patches,然後編 ELF + 打 AppImage
#
# 用法:
#   ./tools/apply-all-patches.sh                # 套全部 + build
#   ./tools/apply-all-patches.sh --no-build     # 只套 patch,不 build
#   ./tools/apply-all-patches.sh --no-appimage  # build ELF 但不打 AppImage
#
# 每個 patch script 都是 in-place 修 AK_CHT_src/AK_CHT.bas,順序很重要:
#   1. patch-linux-paths.py     必跑(Windows 路徑 + chdir)
#   2. patch-savegame.py        M4 (auto-save)
#   3. patch-ui-title.py        P1-1 (片頭分色+指南針)
#   4. patch-ui-opening.py      P1-2 (開場字卡)
#   5. patch-ui-shop.py         P0-1 (商店左右並列)
#   6. patch-ui-msg.py          P0-2 (訊息欄)
#   7. patch-ui-hpbar.py        P0-3 (生命條)
#   8. patch-ui-death.py        P1-3 (死亡畫面)
#   9. patch-ui-minimap.py      P2 (小地圖標)

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$HERE/AK_CHT_src/AK_CHT.bas"
ORIG="$HERE/AK_CHT_src/AK_CHT.bas.orig"

cd "$HERE"

if [ ! -f "$ORIG" ]; then
    echo "ERROR: 找不到 $ORIG (baseline .bas),先 git show HEAD:AK_CHT_src/AK_CHT.bas > $ORIG"
    exit 1
fi

echo "[0/N] restore .bas from .orig"
cp "$ORIG" "$SRC"

PATCHES=(
    patch-linux-paths.py
    patch-savegame.py
    patch-ui-title.py
    patch-ui-opening.py
    patch-ui-shop.py
    patch-ui-msg.py
    patch-ui-hpbar.py
    patch-ui-death.py
    patch-ui-minimap.py
    patch-cheat.py
    patch-fix-statusclear.py
    patch-shop-header.py
    patch-shop-redesign.py
    patch-credit.py
)

idx=1
total=${#PATCHES[@]}
for p in "${PATCHES[@]}"; do
    full="$HERE/tools/$p"
    if [ -f "$full" ]; then
        echo "[$idx/$total] apply $p"
        python3 "$full" || { echo "ERROR: $p failed"; exit 1; }
    else
        echo "[$idx/$total] skip $p (not yet written)"
    fi
    idx=$((idx+1))
done

if [ "${1:-}" = "--no-build" ]; then
    echo "完成 patch,不 build"
    exit 0
fi

echo "=== Build ELF ==="
rm -f "$HERE/AK_CHT_src/akalabeth"
"$HERE/tools/build-in-docker.sh" --skip-image 2>&1 | tail -5

if [ "${1:-}" = "--no-appimage" ]; then
    echo "完成 build,不打 AppImage"
    exit 0
fi

echo "=== Build AppImage ==="
"$HERE/appimage/build.sh" 2>&1 | tail -5
