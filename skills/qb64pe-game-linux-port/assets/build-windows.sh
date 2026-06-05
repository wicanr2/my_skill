#!/usr/bin/env bash
# Windows cross-build script — 在 winbuild docker image 內跑
# 把 AK_CHT.bas 編成 AK_CHT.exe,然後用 7z 打包成自解壓 .exe
#
# 預期執行位置:Docker container 內,bind-mount $PROJECT_ROOT → /work
#
# 從 host 端跑:
#   docker run --rm -v "$PWD:/work" -w /work ak-cht-winbuild:latest \
#       bash tools/build-windows.sh

set -euo pipefail

cd /work

echo "[1/4] 編 AK_CHT.bas → AK_CHT.exe (via Wine + QB64-PE)"
cp -r AK_CHT_src /tmp/win-src
cd /tmp/win-src

# 用 wine 跑 QB64-PE Windows compiler
# -x = compile, console progress
# -w = show warnings
# 必須在 .bas 同目錄跑,否則 QB64-PE 找不到 internal/temp
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x16 &
XVFB_PID=$!
sleep 1

wine /opt/qb64pe-win/qb64pe/qb64pe.exe -x -w AK_CHT.bas -o AK_CHT.exe 2>&1 | tail -20 || true

kill $XVFB_PID 2>/dev/null || true

if [ ! -f AK_CHT.exe ]; then
    echo "ERROR: AK_CHT.exe 沒產出"
    ls -la
    exit 1
fi
ls -lh AK_CHT.exe

echo "[2/4] 準備 release 目錄 + data files"
RELEASE=/tmp/AK_CHT_Windows
rm -rf "$RELEASE"
mkdir -p "$RELEASE"
cp AK_CHT.exe "$RELEASE/"
cp AK_CHT.ini "$RELEASE/"
cp font_a16.dat font_t16.dat font_t16_taipei.dat "$RELEASE/" 2>/dev/null || true
[ -f ak_cht_256.ico ] && cp ak_cht_256.ico "$RELEASE/"
ls -lh "$RELEASE/"

echo "[3/4] 打包成 7z"
cd /tmp
rm -f AK_CHT_Windows.7z
7z a -mx=9 AK_CHT_Windows.7z AK_CHT_Windows/
ls -lh AK_CHT_Windows.7z

echo "[4/4] 加 README + 打 .zip (玩家友善版)"
# 7-Zip extras 不含 SFX module,Windows SFX 自製要 cross-compile mingw,複雜度高
# 改提供 .7z 與 .zip 兩種格式 + README.txt 一目了然
cat > "$RELEASE/README-Windows.txt" <<'EOF'
Akalabeth 阿卡拉貝中文版 - Windows 執行說明
============================================

1. 把這個資料夾整包解壓到任何位置 (建議 C:\Akalabeth\)
2. 雙擊 AK_CHT.exe 即可玩

如有問題:
- 確認 AK_CHT.exe, AK_CHT.ini, font_a16.dat, font_t16.dat 在同一個資料夾
- AK_CHT.ini 內可調整:
    Fullscreen=true/false   全螢幕
    Map=true/false          小地圖
    Cheat=true/false        作弊模式 (食物 + HP 不減,前期練手用)
    CHTFont=font_t16.dat    預設 WenQuanYi 點陣正宋
            font_t16_taipei.dat 切換為 UW-Ming 倚天風復古字型

授權 / 版權聲明
---------------
- 原作 Akalabeth: World of Doom (1979) by Richard Garriott (Lord British)
- 繁體中文化 by Indiana Chiou, 2024
- Linux Port + AppImage + 視覺優化 + Windows build by Chun-Yu Wang (王俊又), 2026
- 字型來源:WenQuanYi Bitmap Song (Apache 2.0 / GPL3 雙授權)
- 僅供同好分享,不得商用
EOF

cd /tmp
rm -f AK_CHT_Windows.zip
cd AK_CHT_Windows
zip -r ../AK_CHT_Windows.zip . > /dev/null
cd ..
ls -lh AK_CHT_Windows.7z AK_CHT_Windows.zip

HOST_UID=$(stat -c %u /work)
HOST_GID=$(stat -c %g /work)
cp AK_CHT_Windows.7z /work/Akalabeth-CHT-Windows.7z
cp AK_CHT_Windows.zip /work/Akalabeth-CHT-Windows.zip
chown "$HOST_UID:$HOST_GID" /work/Akalabeth-CHT-Windows.7z /work/Akalabeth-CHT-Windows.zip

echo "完成:"
ls -lh /work/Akalabeth-CHT-Windows.* 2>/dev/null

# SFX config(自解壓後跑 AK_CHT.exe)
# (SFX 留法已移除,Linux 上沒有可用的 Windows PE32 SFX module)
echo "(完成)"
