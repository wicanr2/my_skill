---
name: mac-app-cross-pack
description: 不用 Mac 開發機，也要 ship 1990s 風格 SDL 1.2 / C++ 老遊戲的 macOS Universal Binary `.app` + `.dmg`。涵蓋 GitHub Actions macOS-14 (Apple Silicon) runner 上 build arm64+x86_64 universal `.app`、Homebrew 移除 sdl_image/mixer 後改自 source build SDL 1.2、Xcode 15 Clang C++20 default 把 `std::unary_function` 弄壞的 C++14 fallback、dylibbundler 把 SDL2/PNG dylib 包進 bundle、CI 同時 ship `.dmg` 和 `.tar.gz`(繞 APFS DMG 在 Windows 端不可讀問題)、CI 完從 Windows/WSL 把 local 遊戲檔注入 `.app/Contents/Resources/data/` 重打私用版、WSL2 kernel 沒 hfsplus 模組改用 `mkisofs -hfs` 產 raw HFS+ image rename `.dmg`、Gatekeeper `xattr -dr com.apple.quarantine` 解未簽署 app。當使用者談到「Mac DMG build」「macos-14 Apple Silicon runner」「universal binary arm64+x86_64」「SDL 1.2 brew 沒了」「sdl12-compat」「Failed loading SDL3 library」「brew sdl2 變 sdl2-compat」「macOS 黑畫面/載入 SDL 失敗」「自編 SDL2 from source」「`std::unary_function` 找不到」「dylibbundler」「Mac .app 注入遊戲檔」「APFS DMG 在 Windows 讀不到」「WSL2 hfsplus unknown filesystem」「mkisofs -hfs」「xattr quarantine」「Gatekeeper 未驗證開發者」「.tar.gz vs .dmg 私用版」「跨平台 build Mac」「OpenXcom Mac 打包」「老遊戲 Mac 移植 ship」「dylibbundler 卡住 / 無限 Try again / can't get path for @rpath」「macOS CI hang / 卡 40 分鐘 / timeout」「自編 SDL_image 從源碼編很慢 / dav1d / libjxl」「macos-13 退役 / Intel job 一直 queued / 改 macos-15-intel」「CMake 4 policy version」時觸發。**主動觸發**：即使使用者只說「補 Mac 版」「加 macOS support」也要套用此 skill。CI 長 hang 定位法見 §1.2d、自編 SDL → dylibbundler `@rpath` 互動 hang [HARD] 見 §1.5。另涵蓋「`error: unrecognized option: CXXFLAGS=-arch`(ScummVM configure 非 autoconf,flags 走 env-var)」見 §1.2、「universal binary 但 Frameworks SDL2 是單弧/非-fat(per-arch+lipo 後 dylibbundler 只抓一弧)→ 改手動 bundle + 雙弧斷言」見 §1.5。
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

**Universal Binary**：`-arch arm64 -arch x86_64` 一次餵兩個 target，產生的 dylib `lipo` 能看到兩 slice。⚠️ **這招只對 CMake / 直接吃 CFLAGS 的 build 有效**。**autoconf 專案(尤其 ScummVM)單次雙弧會炸** configure 版本解析(`-mmacosx-version-min` 餵進去 → `integer expression expected`),那邊要改成「**每弧 native 各編一次 + `lipo -create` 合併**」(x86_64 弧在 Apple Silicon runner 上走 `arch -x86_64` Rosetta,arch 值須與 runner 一致)——見 `retro-game-cht-package` skill(patched-ScummVM 漢化三平台打包)。

> **[HARD] ScummVM 的 `configure` 不是 autoconf,`CXXFLAGS`/`LDFLAGS` 只能走環境變數,不能當 `KEY=VALUE` 位置參數。** 它是手寫 shell script,開頭 `SAVED_CXXFLAGS=$CXXFLAGS` 從環境讀;把 `CXXFLAGS="-arch arm64" ./configure ...` 當**引數**傳會直接 `error: unrecognized option: CXXFLAGS=-arch`。正解:`CXXFLAGS="-arch $arch -mmacosx-version-min=$MIN" LDFLAGS="..." ./configure --enable-engine=... --with-sdl-prefix=...`(flags 放前綴)。**同一輪腳本裡 SDL2 是 autoconf,`CFLAGS=... LDFLAGS=...` 當引數吃得下** → 很容易誤以為 ScummVM 也吃、SDL2 過了卻卡在 ScummVM configure。Linux 端先驗一次 patch 套用+configure(用 Linux-valid flag 如 `-O2` 代 `-arch`)可提前抓到這個介面差異,省一輪 mac runner。

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

### 1.2c 從源碼自編 SDL2(libsdl-org CMake 路線)的三個拖時間 / 卡編譯雷

走 `libsdl-org/SDL_image` 等 **CMake + vendored 子模組**(非上面的 autoconf tarball)自編時,以下三點會讓 CI 從「1 分鐘」變「30 分鐘起跳」或直接 config 失敗:

1. **[HARD] vendored 子模組是巨庫,別 `--recurse-submodules` 全 clone**:`SDL_image` 的 vendored deps 含 **dav1d(AVIF)、libjxl(JPEG-XL)、libavif、libwebp**,全 clone + 編是好幾百 MB / 數十分鐘。remake 通常**只用 PNG**。做法:`git clone --depth 1` 主庫後,**只選擇性 init 真正要的子模組**——
   ```bash
   git submodule update --init --depth 1 external/zlib external/libpng   # 只要這兩個
   ```
   並在 cmake 關掉其餘 codec:`-DSDL2IMAGE_AVIF=OFF -DSDL2IMAGE_JXL=OFF -DSDL2IMAGE_WEBP=OFF -DSDL2IMAGE_TIF=OFF -DSDL2IMAGE_JPG=OFF -DSDL2IMAGE_PNG=ON`。同理 `SDL_ttf` 只 init `external/freetype` + `-DSDL2TTF_HARFBUZZ=OFF`;`SDL_mixer` 不需 codec 時 `-DSDL2MIXER_WAVPACK=OFF -DSDL2MIXER_GME=OFF`。**實測:選擇性 submodule 後,4 個 SDL 庫在 macOS runner 1 分鐘內全編完。**
2. **`SDL2MIXER_VORBIS` 是 enum 不是 bool**:填 `ON` 會 config error。要 OGG 用內建 `STB`(免外部庫):`-DSDL2MIXER_VORBIS=STB`;不要 OGG 就連這個都不用開。
3. **CMake 4.x 拒絕 vendored 老 `cmake_minimum_required`**:freetype 等 vendored dep 的 `cmake_minimum_required(VERSION 3.0)` 在 CMake 4.x 直接報錯。全域加 **`-DCMAKE_POLICY_VERSION_MINIMUM=3.5`** 相容。

### 1.2d [重要] CI 長 hang 怎麼定位——別憑空猜「哪一步慢」

u1-cht 這次卡 40 分鐘,**前後猜錯三次**(以為是 codec 巨庫 → hdiutil → 「只能 brew」),全是憑印象換假設、白繞好幾輪。真正破案靠**時間戳逐階段排除**:

- **每個 build 階段印 `date +%H:%M:%S` + 階段名**(`build_dep` 在 config / build / OK 各印一行)。CI 結束後抓 job log,把時間軸排出來,**快的步驟一個個劃掉,逼出吃掉大半時間的那一步**。本案一看就清楚:4 個 SDL 庫 09:17:09→09:18:04(1 分鐘全完),遊戲也秒編,**剩下 39 分鐘全被 dylibbundler 一步吃掉** → 根因瞬間收斂到 §1.5。
- **「卡住」要先分類再動手**:是 **build 慢**(CPU 在跑、log 持續吐)、還是 **互動 hang**(log 卡在某行不動、在等 stdin,如 dylibbundler 的「Try again」)、還是 **runner 永遠 queued**(標籤死掉,見「常踩雷」#4)?三者修法完全不同,**先看 log 最後停在哪一行**再下結論,不要直接 `gh run cancel` 了事。
- **元教訓**:CI hang 不要靠記憶/直覺換假設(「大概是 X 吧」改成「那大概是 Y 吧」),要先建**可觀測訊號**(時間戳)把範圍逼小。對應 `rules/60-feedback-loop-priority`(先建可驗證訊號再下結論)與第一性原理。

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
  -p @executable_path/../Frameworks/ \
  -s "$PREFIX/lib" </dev/null      # ← 自編 SDL 必加,見下方 [HARD]
```

`-od` overwrite dir, `-b` copy binaries, `-x` 主 binary, `-d` 目標 Frameworks dir, `-p` rpath prefix。

#### [HARD] 自編 SDL(非 brew)→ dylibbundler 會 **互動式無限 hang**,卡爆整個 CI

**症狀**(u1-cht 2026-06-28 實測,卡 40 分鐘被 timeout 取消):job log 出現無限重複——

```
/!\ WARNING : can't get path for '@rpath/libSDL2-2.0.0.dylib'
libSDL2-2.0.0.dylib does not exist. Try again
libSDL2-2.0.0.dylib does not exist. Try again   ← 無限刷直到 timeout
```

**根因**:自編(from-source)的 SDL dylib,其 install name 是相對的 `@rpath/libSDL2-2.0.0.dylib`(不是 brew 那種絕對路徑 `/opt/homebrew/lib/...`)。dylibbundler 解不到 `@rpath` 的實體 → **進互動模式問使用者「實體在哪」**;CI 沒有 stdin → 永遠等不到輸入 → 無限「Try again」。**brew 版的 dylib 是絕對路徑故不中招——這正是為何會誤判成「只有 brew 能成功、自編不行」**(實際上自編完全能成,只是 dylibbundler 沒被告知搜尋路徑)。

**修法(兩個都要)**:
- **`-s "$PREFIX/lib"`**:把自編 prefix 的 lib 目錄加進 dylibbundler 搜尋路徑,讓它自己解到 `@rpath` 實體(`$PREFIX` = 你自編 SDL 系列 `--prefix` / `CMAKE_INSTALL_PREFIX` 的位置)。多個 prefix 就多給幾個 `-s`。
- **`</dev/null`**:保險絲。萬一仍有某個 dylib 解不到,讓 dylibbundler 讀到 EOF **fail-fast(報錯退出)而非 hang**;CI 立刻紅燈,你看得到根因,不會默默卡 40 分鐘。

**驗證**:打包後拆 `.app/Contents/Frameworks/`,該有 `libSDL2-2.0.0.dylib` 等實體(~2MB 才是真 SDL2,~0.5MB 是 sdl2-compat shim,見 §1.2b);`otool -L Contents/MacOS/<bin> | grep SDL` 應指向 `@executable_path/../Frameworks/`。**Frameworks 是空的 = dylibbundler 根本沒收到 → 在別人機器上一定黑畫面/閃退**。

#### [HARD] per-arch+lipo 路線:dylibbundler 會把 universal binary 的 SDL2 退化成**單弧非-fat**

「每弧各編一次 + lipo」(§1.2 的 autoconf/ScummVM 路線)時,兩弧各自 `--with-sdl-prefix` 指向**不同** prefix(`sdl-arm64` / `sdl-x86_64`),所以 lipo 後的 universal `scummvm` **兩個 slice 各自參照不同的 SDL2 載入路徑**。dylibbundler 只會解析並複製其中**一弧的非-fat dylib** → 主 binary 是 universal,但 `Frameworks/libSDL2-2.0.0.dylib` 卻是 **x86_64(或 arm64)單弧** → 另一半使用者一開就閃退。**CI 只查「有沒有 dylib / 是不是 shim」會綠燈放行,查不到這個。**

**修法:這條路線別用 dylibbundler,改手動 bundle(SDL2 通常是唯一非系統 dylib,png/freetype/vorbis 全關掉時)**:
```bash
# 1) 先 lipo 出 universal SDL2 放進 Frameworks
lipo -create "$SDL_ARM/lib/libSDL2-2.0.0.dylib" "$SDL_X86/lib/libSDL2-2.0.0.dylib" -output "$FW"
install_name_tool -id "@executable_path/../Frameworks/libSDL2-2.0.0.dylib" "$FW"
# 2) 對主 binary 的兩個舊 prefix 路徑各 -change 一次(每次只改到對應 slice)
install_name_tool -change "$SDL_ARM/lib/libSDL2-2.0.0.dylib" "@executable_path/../Frameworks/libSDL2-2.0.0.dylib" MacOS/scummvm
install_name_tool -change "$SDL_X86/lib/libSDL2-2.0.0.dylib" "@executable_path/../Frameworks/libSDL2-2.0.0.dylib" MacOS/scummvm
# 3) install_name_tool 改過必須 ad-hoc 重簽,否則載入/Gatekeeper 失敗
codesign --force --sign - "$FW"; codesign --force --sign - MacOS/scummvm
```

**驗證要斷言「雙弧」,不能只查存在**:`lipo -info` 對**主 binary 與 Frameworks 內 SDL2 都要**看到 `arm64` 且 `x86_64`,任一非雙弧就 `exit 1`;再 `otool -L MacOS/scummvm` 確認無殘留 build 期絕對路徑(`_macbuild`/`sdl-arm64` 之類)。這道防呆就是擋「CI 綠燈但玩家端壞掉」的關鍵。

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

## 常踩雷

1. **`bin/game` lipo 失敗**：CMake 直接產 `.app` bundle，binary 在 `app/Contents/MacOS/<name>`，不在 `bin/`。檢查 CMake `set_target_properties(... MACOSX_BUNDLE TRUE)`。
2. **PowerShell heredoc commit message 中文 parser error**：commit message 含中文時 `git commit -m "..."` 在 PowerShell 5.1 會被 cp950 codec 弄爛，改用 `git commit -F commit_msg.txt`（檔案 UTF-8 BOM）。
3. **WSL /tmp 跨 session 蒸發**：build 中途如果 WSL session 重啟，`/tmp/mac_inject_*` 全沒。把 build + package 串成一個 bash 指令（用 `&&` 鏈），別分段跑。
4. **runner 標籤被退役 → job 永遠 queued(不是失敗,是「永遠排不到」)**：
   - **症狀**:某個 matrix job 一直停在 `queued`、從不轉 `in_progress`,而同一 run 的別的 job 正常跑完。**永遠排隊 ≠ 排隊塞車**:塞車最終會跑;標籤無效則永遠排不到、也不會報錯。看到「卡很久」別只 `gh run cancel` 了事 —— 先查**標籤是否還存在**。
   - **根因 + 修法**:GitHub 退役了該 runner image。**`macos-13`(Intel)已於 2025-12-04 退役** → 用它的 x86_64 job 永遠 queued。**改用 `macos-15-intel`**(GitHub 給 Intel 的新標籤,撐到約 2027 秋)。`macos-14`+ 一律是 Apple Silicon(arm64)。
   - **更好的解法 = 本 skill 主路線**:單一 `macos-14` + **universal binary**(`-arch arm64 -arch x86_64`,見 §1.4)一次出雙架構,根本不碰 Intel runner → 對「Intel runner 退役」免疫。會踩 #4 的多半是改用了 per-arch matrix 而非 universal。
   - **元教訓**:CI 排隊狀態要分清「塞車(會好)」vs「標籤死掉(永遠卡)」。對應 `rules/60-feedback-loop-priority` 與第一性原理。
5. **dylibbundler 互動 hang 卡爆 CI(自編 SDL)**:見 §1.5 [HARD]。`@rpath` install name 解不到 → 無限「Try again」→ 40 分鐘 timeout。修法 `-s "$PREFIX/lib" </dev/null`。**這是「自編 SDL 在 CI 不行、只能 brew」這個錯誤結論的真正來源**——不是自編不行,是少給了搜尋路徑。

## 案例（已驗證）

- [openxcom-cht](https://github.com/wicanr2/openxcom-cht) v2.29
  - workflow: `.github/workflows/build-mac-universal.yml` (v7 = +tar.gz output)
  - 注入工具: `tools/inject_mac_data_v2.sh` (tar.gz route)、`tools/inject_mac_data_dmg.sh` (mkisofs -hfs route)
  - Final 矩陣: UFO+TFTD × {portable.zip, AppImage, mac.dmg (公版), mac-with-data.tar.gz, mac-with-data.dmg (私用版)}

## 一句話

**Mac host 只在 CI 借 5 分鐘 build 一次**；之後 `.app` 變成普通 tar.gz 內容，後續注入/重打/分發都在 Windows / WSL 完成。`.dmg` 是「方便雙擊」版本，`.tar.gz` 是「保證 perm 對」版本，**雙保險同時 ship 是必要的**。
