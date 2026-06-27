---
name: mac-app-cross-pack
description: 不用 Mac 開發機，也要 ship 1990s 風格 SDL 1.2 / C++ 老遊戲的 macOS Universal Binary `.app` + `.dmg`。涵蓋 GitHub Actions macOS-14 (Apple Silicon) runner 上 build arm64+x86_64 universal `.app`、Homebrew 移除 sdl_image/mixer 後改自 source build SDL 1.2、Xcode 15 Clang C++20 default 把 `std::unary_function` 弄壞的 C++14 fallback、dylibbundler 把 SDL2/PNG dylib 包進 bundle、CI 同時 ship `.dmg` 和 `.tar.gz`(繞 APFS DMG 在 Windows 端不可讀問題)、CI 完從 Windows/WSL 把 local 遊戲檔注入 `.app/Contents/Resources/data/` 重打私用版、WSL2 kernel 沒 hfsplus 模組改用 `mkisofs -hfs` 產 raw HFS+ image rename `.dmg`、Gatekeeper `xattr -dr com.apple.quarantine` 解未簽署 app。當使用者談到「Mac DMG build」「macos-14 Apple Silicon runner」「universal binary arm64+x86_64」「SDL 1.2 brew 沒了」「sdl12-compat」「Failed loading SDL3 library」「brew sdl2 變 sdl2-compat」「macOS 黑畫面/載入 SDL 失敗」「自編 SDL2 from source」「`std::unary_function` 找不到」「dylibbundler」「Mac .app 注入遊戲檔」「APFS DMG 在 Windows 讀不到」「WSL2 hfsplus unknown filesystem」「mkisofs -hfs」「xattr quarantine」「Gatekeeper 未驗證開發者」「.tar.gz vs .dmg 私用版」「跨平台 build Mac」「OpenXcom Mac 打包」「老遊戲 Mac 移植 ship」時觸發。**主動觸發**：即使使用者只說「補 Mac 版」「加 macOS support」也要套用此 skill。
---

# 不用 Mac 開發機 ship macOS Universal `.app` + `.dmg` SOP

把任何 SDL 1.2 / C++ 老遊戲（OpenXcom、ScummVM patch、1990s remake）的 ship matrix 加上 macOS universal binary，**整條 pipeline 在 Windows / Linux dev box 上跑**。Mac host 只在 GitHub Actions macOS-14 runner 借用幾分鐘做 build。

## 觸發場景

- ship matrix 原本只有 Win portable + Linux AppImage，要補 Mac
- 用戶用 Mac 跑老遊戲被 Gatekeeper 擋
- 1990s SDL 1.2 程式碼在 Xcode 15 build 不過
- 想把 GitHub 上 build 好的空 `.app` 注入自己 local 的版權遊戲檔給自己 / 私人朋友
- APFS DMG 在 Windows 7-Zip 讀不出來

## 核心限制（為什麼 cross-build 是「半套」）

```
macOS .app + .dmg 必須在 macOS host 上 build
   └─ 法律: Apple SDK EULA 限制 Apple host 才能編 macOS binary
   └─ 技術: codesign / hdiutil / iconutil 只在 macOS
```

**所以不能像 AppImage 那樣從 Windows 直接 cross-compile**。但可以用 **GitHub Actions `macos-14` runner**（Apple Silicon M1, 免費 6 小時 / 月）幫忙 build，之後一切後處理（注入本地檔、重打包）回 Windows / WSL 做。

## 完整 pipeline 三段

```
[1] GitHub Actions macOS-14 runner
       ├─ build SDL 1.2 from source (Homebrew 沒了)
       ├─ cmake -DCMAKE_OSX_ARCHITECTURES="arm64;x86_64"
       ├─ dylibbundler 包 .dylib 進 .app
       ├─ 產 .dmg + .tar.gz (雙保險，繞 APFS)
       └─ upload artifact
              ↓
[2] dev box (Windows / WSL) 下載 artifact
       ├─ 解 .tar.gz (繞過 APFS DMG 不可讀)
       ├─ 注入 local data/UFO/, data/TFTD/ 進 .app/Contents/Resources/data/
       └─ 重打成 .tar.gz (perm 保留版) + .dmg (mkisofs -hfs hybrid，方便雙擊)
              ↓
[3] 目標 Mac 解 quarantine + 安裝
       xattr -dr com.apple.quarantine /Applications/Game.app
```

## 段 1: GitHub Actions Universal Build

### 1.1 workflow skeleton

```yaml
# .github/workflows/build-mac-universal.yml
name: Build Mac Universal
on:
  workflow_dispatch:
  push:
    tags: ['v*-mac']

jobs:
  build:
    runs-on: macos-14    # Apple Silicon (M1)，免費 6 小時/月
    steps:
      - uses: actions/checkout@v4
      - name: Install homebrew deps
        run: |
          brew install yaml-cpp sdl2 sdl2_image sdl2_mixer sdl2_gfx \
                       sdl12-compat dylibbundler
      # NOTE: brew 已移除 sdl_image / sdl_mixer / sdl_gfx (SDL 1.2)
      # 必須走 source build
```

### 1.2 SDL 1.2 source build（Homebrew 殺了 brew sdl 後唯一路）

Homebrew 2023 砍 SDL 1.2 family（除了 `sdl12-compat` shim）。對純 SDL 1.2 程式碼，需要：

- 路線 A：用 `sdl12-compat` binary shim（轉 SDL 2 API）— 比較新但有相容性風險
- 路線 B：source build 一份 `libSDL-1.2.0.dylib` + `libSDL_image-1.2`/`SDL_mixer`/`SDL_gfx` — 100% 跟原版相容

OpenXcom 走路線 B：

```bash
# Download tarballs from official archive (SDL 1.2 EOL since 2012, URL 穩定)
SDL_VER=1.2.15
IMG_VER=1.2.12
MIX_VER=1.2.12
GFX_VER=2.0.26

for pkg in SDL-${SDL_VER} SDL_image-${IMG_VER} SDL_mixer-${MIX_VER} SDL_gfx-${GFX_VER}; do
  curl -LO https://www.libsdl.org/release/${pkg}.tar.gz \
       || curl -LO https://www.libsdl.org/projects/${pkg%-*}/release/${pkg}.tar.gz
  tar xzf ${pkg}.tar.gz
  pushd ${pkg}
  ./configure --prefix=/usr/local CFLAGS="-arch arm64 -arch x86_64" \
              CXXFLAGS="-arch arm64 -arch x86_64" \
              LDFLAGS="-arch arm64 -arch x86_64"
  make -j$(sysctl -n hw.ncpu)
  sudo make install
  popd
done
```

**Universal Binary**：`-arch arm64 -arch x86_64` 一次餵兩個 target，產生的 dylib `lipo` 能看到兩 slice。⚠️ **這招只對 CMake / 直接吃 CFLAGS 的 build 有效**。**autoconf 專案(尤其 ScummVM)單次雙弧會炸** configure 版本解析(`-mmacosx-version-min` 餵進去 → `integer expression expected`),那邊要改成「**每弧 native 各編一次 + `lipo -create` 合併**」——見 `retro-game-cht-package` skill(patched-ScummVM 漢化三平台打包)。

### 1.2b SDL2 也別用 brew（sdl2-compat → SDL3 雷，[HARD]）

**[HARD] SDL2 程式的 macOS CI 不要 `brew install sdl2`，改源碼編 pinned 真 SDL2。** 2026-06 起 Homebrew 把 `sdl2` 換成 **sdl2-compat** —— 一個 ~0.5MB 的「SDL2 API 架在 SDL3 上」shim，**runtime 才 `dlopen` libSDL3**。dylibbundler 只打包**靜態連結**相依,不會把 runtime dlopen 的 `libSDL3` 放進 `.app` → 玩家端 **「Failed loading SDL3 library」/ 黑畫面**。同一份 CI 腳本,brew 哪天換內容就突然壞,且**本機(有裝 SDL3)測不出來**。

- **一眼辨識**:拆 `.app/Contents/libs`(或 `Frameworks`),`libSDL2-2.0.0.dylib` **~0.5MB = sdl2-compat shim**(壞);**~2MB = 真 SDL2**(好)。`otool -L libSDL2 | grep -i SDL3` 有命中就是 shim。
- **修法**:從 release tarball 編 pinned 真 SDL2(`2.30.9`)+ SDL2_image + SDL2_mixer 到一個 prefix,`-DCMAKE_PREFIX_PATH`/`PATH` 指過去。**只連必要 codec**:image 用 `--enable-stb-image`(PNG/JPG,不連 libpng)、mixer 視需要(很多老引擎自帶合成器走 `Mix_HookMusic`,WAV 用 `Mix_LoadWAV` 即內建 → **mixer 可零外部 codec**,`--disable-music-*` 全關)。`-mmacosx-version-min=13.4` 讓 dylib 對舊 Mac 相容(brew bottle 是為 runner 的新 macOS 編的,deployment target 太高)。
- **x86_64 slice**:在 Apple Silicon runner 上用 `arch -x86_64 /bin/sh build.sh`(Rosetta,toolchain 原生 x86_64,configure run-tests 能跑)比 autotools `--host=` cross 穩。
- **防呆**:腳本結尾斷言 `otool -L "$PREFIX/lib/libSDL2-2.0.0.dylib" | grep -qi SDL3 && exit 1`,把 shim 擋在 CI。

```sh
SDL_VER=2.30.9; IMG_VER=2.8.2; MIX_VER=2.8.0; MIN=13.4
export CFLAGS="-arch $ARCH -mmacosx-version-min=$MIN" CXXFLAGS="$CFLAGS" LDFLAGS="$CFLAGS"
# SDL2 core → make install --prefix=$P ; then PATH=$P/bin:$PATH
# SDL2_image: ./configure --with-sdl-prefix=$P --disable-png --disable-jpg ... --enable-stb-image
# SDL2_mixer: ./configure --with-sdl-prefix=$P --disable-music-ogg --disable-music-midi ...（引擎自帶合成器時全關）
```

來源:`open-king-bounty-cht` issue #3(brew 換 sdl2-compat 的實戰根因)、`freesynd-cht` `ci/build-sdl2-from-source.sh`(零 mixer codec：引擎用 ADLMIDI + `Mix_HookMusic`)。

### 1.3 C++14 fallback（Xcode 15 Clang 把 1990s 程式碼弄壞）

Xcode 15.4 的 Clang 預設 C++20，`std::unary_function` / `std::binary_function` C++17 後被移除，**1990s 程式碼會直接 build 不過**。修法：

```cmake
# CMakeLists 補：
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wno-deprecated-declarations")
```

或 CMake config 階段 `-DCMAKE_CXX_STANDARD=14`。

### 1.4 CMake 設 universal

```bash
cmake -B build \
      -DCMAKE_OSX_ARCHITECTURES="arm64;x86_64" \
      -DCMAKE_CXX_STANDARD=14 \
      -DCMAKE_CXX_EXTENSIONS=OFF \
      -DCMAKE_CXX_FLAGS="-Wno-deprecated-declarations" \
      -DCMAKE_BUILD_TYPE=Release
cmake --build build -j$(sysctl -n hw.ncpu)
```

**lipo verify**：

```bash
lipo -info build/openxcom.app/Contents/MacOS/openxcom
# 預期: Architectures in the fat file: ... arm64 x86_64
```

注意：很多 SDL 老遊戲 CMake 直接產 `Game.app` bundle（不是 `bin/game` 裸 binary），lipo 對 `app/Contents/MacOS/<binary>`，**不要對 `bin/`**（會 No such file）。

### 1.5 dylibbundler 包 dylib

`.app` 跑到別人 Mac 上，Homebrew 路徑（`/opt/homebrew/lib/`、`/usr/local/lib/`）的 dylib 一定不在。用 `dylibbundler`：

```bash
dylibbundler -od -b \
  -x build/openxcom.app/Contents/MacOS/openxcom \
  -d build/openxcom.app/Contents/Frameworks/ \
  -p @executable_path/../Frameworks/
```

`-od` overwrite dir, `-b` copy binaries, `-x` 主 binary, `-d` 目標 Frameworks dir, `-p` rpath prefix。

### 1.6 .dmg + **.tar.gz 雙保險**

只 ship `.dmg` 是常見錯誤。**APFS DMG 在非 Mac 平台讀不到**（7z 16.02 看到 GPT partition 但解不開 APFS layer，7z 21+ 才行）。

CI 同時 ship `.tar.gz`：

```bash
# DMG (給 Mac 用戶雙擊)
hdiutil create -volname "Game" -srcfolder build/openxcom.app \
               -ov -format UDZO Game.dmg

# .tar.gz (給開發者後續注入用 - 繞 APFS)
tar czf Game-mac.tar.gz -C build openxcom.app
```

`tar` 保留 Unix `+x` permission 和 symlink，比 zip 安全。

## 段 2: 從 Windows / WSL 注入 local data

### 2.1 為什麼要注入

CI build 的 `.app` 只含 `common/` + `standard/` 資料（OpenXcom mod 數據），但 **`data/UFO/`、`data/TFTD/` 是原版 1994 X-COM 版權檔**，CI 不能附帶。私用版要把自己的 local 版權檔注入進去。

### 2.2 注入腳本（用 .tar.gz 路線）

```bash
#!/bin/bash
# inject_mac_data.sh — 從 CI .tar.gz artifact 注入 local 遊戲檔
set -e
DIST=/mnt/d/dist
SRC=$DIST/_mac_artifact          # 從 gh run download 下載到這
BIN=/mnt/d/Game/bin              # local 含版權 data 的目錄
TMP=/tmp/mac_inject
rm -rf $TMP && mkdir -p $TMP

inject() {
    local VARIANT=$1; local DATA_DIR=$2
    local TAR_IN="$SRC/Game-${VARIANT}-mac.tar.gz"
    local OUT="$DIST/Game-${VARIANT}-mac-with-data.tar.gz"
    local WORK="$TMP/$VARIANT"
    mkdir -p $WORK && cd $WORK

    tar xzf "$TAR_IN"
    local APP=$(ls -d *.app | head -1)
    local TARGET="$APP/Contents/Resources/data"
    mkdir -p "$TARGET"
    cp -r "$BIN/$DATA_DIR" "$TARGET/"
    [ -d "$TARGET/common"   ] || cp -r "$BIN/common"   "$TARGET/"
    [ -d "$TARGET/standard" ] || cp -r "$BIN/standard" "$TARGET/"

    tar czf "$OUT" "$APP"
}
inject UFO  UFO
inject TFTD TFTD
```

**為什麼不直接改 CI 加 data**：版權檔不能 push 到 GitHub（即使 private repo 也要避免）。

### 2.3 .dmg 私用版（mkisofs -hfs hybrid 路線）

`.tar.gz` 給開發者夠用，但要「雙擊掛載」體驗就要 `.dmg`。**WSL2 kernel 沒 hfsplus module**（`mount -t hfsplus` → unknown filesystem），改用 userland mkisofs：

```bash
sudo apt install -y hfsprogs genisoimage   # hfsprogs 提供 mkfs.hfsplus；
                                            # genisoimage 提供 mkisofs/genisoimage
# Step A: 解 with-data .tar.gz
cd $WORK
tar xzf "$TAR_WITH_DATA"
APP=$(ls -d *.app | head -1)

# Step B: mkisofs -hfs 產 hybrid HFS+ISO，rename → .dmg
mkisofs -V "Game-Volume" \
        -hfs -part -no-desktop \
        -hide-hfs "*.DS_Store" \
        -o output.img "$APP"
mv output.img Game-with-data.dmg
```

**重要踩雷**：
- `mkisofs -hfs` **跟 `-apple` 不能同時用**（"Can't have both -apple and -hfs options"），二選一
- 產出是 **raw HFS+ image（沒 UDIF/UDZO 壓縮）**，size 比 .tar.gz 大 3 倍。但 macOS hdiutil 認得 raw HFS+，雙擊 OK
- 不保證所有 Unix permission 被保留（hybrid HFS 邊界情況），所以 **.tar.gz 必須同時 ship 作 fallback**

### 2.4 真壓縮 UDZO `.dmg` 需要

要 7z 21+ 那種 fully compressed APFS/HFS+ DMG，必須跑 `hdiutil` — **必須在 Mac host**。Windows / WSL 端拿不到，認命接受 mkisofs raw image 或 libdmg-hfsplus（要 source build，工程量大）。

## 段 3: 目標 Mac 安裝

未簽署 app 第一次跑會被 Gatekeeper 擋（「未驗證開發者」）：

```bash
# 解 .tar.gz 路線
tar xzf Game-with-data.tar.gz
mv Game.app /Applications/
xattr -dr com.apple.quarantine /Applications/Game.app
open /Applications/Game.app

# 解 .dmg 路線
# 雙擊 .dmg → 拖 .app 到 Applications → 同樣 xattr 解隔離
```

如果 `chmod +x .../Contents/MacOS/Game` 沒繼承到（mkisofs -hfs 邊界情況）：

```bash
chmod +x /Applications/Game.app/Contents/MacOS/Game
```

## 完整 artifact 矩陣建議

| Platform | 公版（無版權檔，可 ship Releases） | 私用版（含版權遊戲檔） |
|---|---|---|
| Windows | `*-portable.zip` | （同 + bin/ data） |
| Linux | `*.AppImage` | （同 + AppDir/usr/share/data） |
| **Mac** | **`*-mac.dmg`** (APFS, CI 產) | **`*-mac-with-data.tar.gz`** + **`*-mac-with-data.dmg`** (hybrid HFS, mkisofs 產) |

`.dmg` 公版可推 GitHub Releases。`*-with-data.*` 純本機，**絕不推 git**（版權）。

## 三個常踩雷

1. **`bin/game` lipo 失敗**：CMake 直接產 `.app` bundle，binary 在 `app/Contents/MacOS/<name>`，不在 `bin/`。檢查 CMake `set_target_properties(... MACOSX_BUNDLE TRUE)`。
2. **PowerShell heredoc commit message 中文 parser error**：commit message 含中文時 `git commit -m "..."` 在 PowerShell 5.1 會被 cp950 codec 弄爛，改用 `git commit -F commit_msg.txt`（檔案 UTF-8 BOM）。
3. **WSL /tmp 跨 session 蒸發**：build 中途如果 WSL session 重啟，`/tmp/mac_inject_*` 全沒。把 build + package 串成一個 bash 指令（用 `&&` 鏈），別分段跑。

## 案例（已驗證）

- [openxcom-cht](https://github.com/wicanr2/openxcom-cht) v2.29
  - workflow: `.github/workflows/build-mac-universal.yml` (v7 = +tar.gz output)
  - 注入工具: `tools/inject_mac_data_v2.sh` (tar.gz route)、`tools/inject_mac_data_dmg.sh` (mkisofs -hfs route)
  - Final 矩陣: UFO+TFTD × {portable.zip, AppImage, mac.dmg (公版), mac-with-data.tar.gz, mac-with-data.dmg (私用版)}

## 一句話

**Mac host 只在 CI 借 5 分鐘 build 一次**；之後 `.app` 變成普通 tar.gz 內容，後續注入/重打/分發都在 Windows / WSL 完成。`.dmg` 是「方便雙擊」版本，`.tar.gz` 是「保證 perm 對」版本，**雙保險同時 ship 是必要的**。
