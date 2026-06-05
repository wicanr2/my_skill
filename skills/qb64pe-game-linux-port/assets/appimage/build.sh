#!/usr/bin/env bash
# 從 AK_CHT_src/akalabeth (Docker 編出的 ELF) + data files → AppImage
#
# 前置:
#   1. 先跑 tools/build-in-docker.sh 產出 AK_CHT_src/akalabeth
#   2. (選用)M3 字型升級後,AK_CHT_src/font_t16_wqy.dat 存在
#
# 用法:
#   ./appimage/build.sh
#
# 產出:
#   ./Akalabeth-CHT-x86_64.AppImage

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT="$(cd "$HERE/.." && pwd)"
SRC_DIR="$PROJECT/AK_CHT_src"
OUTPUT="${OUTPUT:-$PROJECT/Akalabeth-CHT-x86_64.AppImage}"

# 檢查必要檔
[ -x "$SRC_DIR/akalabeth" ] || {
    echo "ERROR: $SRC_DIR/akalabeth 不存在或非可執行"
    echo "→ 先跑 tools/build-in-docker.sh"
    exit 1
}

WORK="$(mktemp -d /tmp/akcht-appimage.XXXXXX)"
APPDIR="$WORK/Akalabeth.AppDir"
trap 'rm -rf "$WORK"' EXIT

echo "[1/5] 建 AppDir 結構"
mkdir -p "$APPDIR"/{usr/bin,usr/lib,opt/game}

echo "[2/5] 複製 ELF binary 與 data files"
install -m 755 "$SRC_DIR/akalabeth" "$APPDIR/usr/bin/akalabeth"
install -m 644 "$SRC_DIR/AK_CHT.ini" "$APPDIR/opt/game/AK_CHT.ini"
install -m 644 "$SRC_DIR/font_a16.dat" "$APPDIR/opt/game/font_a16.dat"
install -m 644 "$SRC_DIR/font_t16.dat" "$APPDIR/opt/game/font_t16.dat"

# 可選的字型(WQY / Taipei)
for opt in font_t16_wqy.dat font_t16_taipei.dat; do
    [ -f "$SRC_DIR/$opt" ] && install -m 644 "$SRC_DIR/$opt" "$APPDIR/opt/game/$opt"
done

echo "[3/5] 用 ldd 找 ELF 依賴,把 non-system .so bundle 進 AppDir"
# 簡化版 linuxdeploy:把 ELF 直接依賴的 libs copy 進去
# 排除 glibc/glibcxx 等基礎(targets 系統會自帶且 ABI 通常相容)
EXCLUDE_PATTERNS='libc\.so|libm\.so|libdl\.so|libpthread\.so|librt\.so|ld-linux|libgcc_s\.so|libstdc\+\+\.so|libnsl\.so|libresolv\.so'

ldd "$SRC_DIR/akalabeth" | awk '{print $3}' | grep -v '^$' | while read -r lib; do
    [ -f "$lib" ] || continue
    name="$(basename "$lib")"
    if echo "$name" | grep -qE "$EXCLUDE_PATTERNS"; then
        continue
    fi
    cp -L "$lib" "$APPDIR/usr/lib/$name"
done
echo "    bundled $(ls "$APPDIR/usr/lib" | wc -l) libs"

echo "[4/5] AppRun + desktop + icon"
install -m 755 "$HERE/AppRun" "$APPDIR/AppRun"
install -m 644 "$HERE/akalabeth.desktop" "$APPDIR/akalabeth.desktop"

# 用 ImageMagick 把 .ico 轉成 256x256 PNG 當 AppImage icon
if [ -f "$HERE/akalabeth.png" ]; then
    install -m 644 "$HERE/akalabeth.png" "$APPDIR/akalabeth.png"
elif command -v convert >/dev/null 2>&1 && [ -f "$SRC_DIR/ak_cht_256.ico" ]; then
    convert "$SRC_DIR/ak_cht_256.ico[0]" -resize 256x256 "$APPDIR/akalabeth.png"
else
    echo "    WARN: 沒 ImageMagick 也沒預先準備的 png,用空白 icon"
    # 1x1 透明 PNG fallback
    printf '\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82' > "$APPDIR/akalabeth.png"
fi
ln -sf akalabeth.png "$APPDIR/.DirIcon"

echo "[5/5] appimagetool 打包"
if [ ! -x "$HERE/appimagetool" ]; then
    echo "    抓 appimagetool ..."
    wget -q "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage" \
        -O "$HERE/appimagetool"
    chmod +x "$HERE/appimagetool"
fi

echo "    AppDir 大小:$(du -sh "$APPDIR" | cut -f1)"
ARCH=x86_64 "$HERE/appimagetool" --comp zstd "$APPDIR" "$OUTPUT"
ls -lh "$OUTPUT"
echo "完成 → $OUTPUT"
