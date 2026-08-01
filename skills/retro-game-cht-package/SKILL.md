---
name: retro-game-cht-package
description: 把一個「patched-ScummVM(或 SDL2)老遊戲繁中化」專案打包成三平台可玩成品的 SOP。涵蓋 Linux 單檔 AppImage(slim 自備遊戲 / full 內嵌遊戲開箱即玩)、Windows 用 docker mingw-w64 cross-compile(自編 SDL2 靜態連結、關掉 mad/vorbis/flac 壓縮編解碼、force little-endian 繞 cross 端序檢測、objdump 遞迴收所有非系統 DLL、打成 .zip)、macOS 走 GitHub Actions(自編 universal SDL2 不用 brew sdl2、dylibbundler)再抓 .app artifact 回本機注入語音+遊戲。也涵蓋 slim/full 版權切分(原版遊戲資料 + TTS 中文語音只進本機完整包、不上公開 CI)。也涵蓋「玩家交付 UX」:每包附繁中 使用說明.txt(Windows SmartScreen、Linux 缺 FUSE、macOS 未簽章報「已損毀」其實是 quarantine),`.app` 用 tar.gz 不用 zip。當使用者談到「打包這個中文化」「Windows/AppImage/macOS 三平台」「cross-compile Windows」「docker mingw」「自編 SDL2」「AppImage 開箱即玩」「把遊戲也包進去」「DLL 都要打包」「Checking endianness unknown」「scummvm.exe 缺 DLL」「macos github action 編完抓回來打包」「macos universal/Intel」「app 已損毀無法打開」「使用說明要寫什麼」「dist-all」「解開後檔案不見了」「中文檔名亂碼」「.bat 中文亂碼」「記事本開 txt 亂碼」時觸發。**主動觸發**:使用者只說「幫這個漢化專案出 Windows / Linux / Mac 版」也套用。
---

# 老遊戲漢化專案 → 三平台打包 SOP

把一個「自家 patch 過的 ScummVM(或 SDL2)引擎 + 中文資產(字型 .dcjk / 譯表 .tab / 配音 .voc / 標題 .spr)」漢化專案,打成 Linux / Windows / macOS 三平台可玩成品。worked example:`indiana-jones-...-cht`(`scripts/package_appimage.sh`、`scripts/build_windows_docker.sh`、`scripts/package_windows.sh`、`scripts/package_macos_local.sh`、`.github/workflows/build-macos.yml`)。

## 平台分工(各走最省事的路)

| 平台 | 怎麼編 | 為什麼 |
|---|---|---|
| **Linux** | 本機 AppImage(bundle 系統 .so + AppRun) | 本機就是 Linux,直接 |
| **Windows** | 本機 **docker mingw-w64 cross-compile** | 不需 Windows 機,docker 內 cross 編 .exe |
| **macOS** | **GitHub Actions** macos runner → 抓 artifact 回本機注入 | Apple SDK EULA 只准 Apple host 編;後處理回本機 |

## slim / full 版權切分(鐵則)

- **slim**:引擎 + **自製**中文資產(字型/譯表/標題;**不含** TTS 語音也行)。**可公開散布**。
- **full**:再加 **TTS 中文語音(可能數百 MB)+ 原版遊戲資料**(`*.001`/`MONSTER.SOU` 等,**LucasArts/版權方所有**)→ 開箱即玩。**只進本機 `dist-all/`,個人自留,絕不上公開 CI / release**。
- `dist-all/`、cross-build 中間產物(`build-win/`)一律 `.gitignore`。

## Linux:單檔 AppImage(參考 willy 的 package_appimage)

```
AppDir/
  usr/bin/scummvm         # 引擎
  usr/lib/*.so            # ldd 撈出、排除 glibc/loader 的相依
  usr/share/<proj>/       # 中文資產(--extrapath 餵)
  game/                   # full 才有:內嵌遊戲資料
  AppRun .desktop .DirIcon
```
- AppRun 找遊戲順序:① 參數傳的路徑 ② 內嵌 `game/`(full 開箱即玩)③ .AppImage 旁 / CWD。`--extrapath=usr/share/<proj>` 餵中文資產、`-p <game>` 餵遊戲。
- `appimagetool --appimage-extract-and-run AppDir out.AppImage`(工具常在 `~/zak-cht-build/appimagetool`)。
- **驗證**:full AppImage 不傳任何路徑直接跑,應偵測內嵌遊戲 + 顯示中文(實測過 30MB slim / 155MB full)。

## Windows:docker mingw-w64 cross-compile(關鍵踩雷全在這)

```bash
docker run --rm -v $PWD:/work -w /work debian:12-slim bash scripts/build_windows_docker.sh
```
- toolchain:`apt install g++-mingw-w64-x86-64 binutils-mingw-w64-x86-64`(binutils 給 cross objdump/strings)。
- **自編 SDL2 + zlib 靜態**(`--host=x86_64-w64-mingw32 --disable-shared --enable-static`),prefix 持久化到掛載目錄,reruns 跳過。
- **[HARD] cross 端序檢測會卡死**:ScummVM `configure` 編一個 .exe 用 `strings` 判端序,cross 到 mingw 後 `strings` 抓不到 marker → 「Checking endianness... unknown」→ `exit 1`。修法:configure 前 `sed -i '/^echo_n "Checking endianness... "/a _endian=little' configure`(x64 Windows 恆 LE;ScummVM 對 emscripten 已有同款 force)。
- **相依瘦身**:原版 + TTS 語音都是 raw VOC → `--disable-mad --disable-vorbis --disable-flac --disable-fluidsynth ...` 全關 → .exe 幾乎零外部相依。⚠️ **ScummVM configure 沒有 `--extra-ldflags/cflags`**(寫了 "unrecognized option" 整個 configure 失敗);不需要它 —— **mingw-w64 預設就把 libgcc / libstdc++ / winpthread 靜態連進去**,.exe 的 import 表本來就只剩 Windows 系統 DLL。
- **[HARD] DLL 全收(objdump BFS)**:別寫死 DLL 清單。對 .exe 跑 `$HOST-objdump -p` 抓 `DLL Name`,過濾掉 Windows 系統 DLL(kernel32/user32/gdi32/msvcrt/ole32/...),把剩下的非系統 DLL 從 mingw sysroot 複製,**遞迴**對每個 bundled DLL 再掃。靜態連結後通常一個都不剩(import 表只有系統 DLL),但這個走訪保證未來改動動態連結時不漏。
- **[HARD] git clone source**:`git init + fetch --depth1 origin <SHA> + checkout FETCH_HEAD` 在 GitHub **抓不到任意 commit**(空 tree → patch 找不到檔)。用 `git clone --depth 1`(HEAD)+ `git apply patch`(patch 通常乾淨套 HEAD);要 pin commit 得 full clone + checkout。
- `scripts/package_windows.sh slim|full`:.exe + 收到的 DLL + 資產(+ full 的語音/遊戲)→ 目錄 → **`zip`**(參考 willy `dist/*.zip`)。
- **驗證**:`file scummvm.exe` 應為 `PE32+ ... x86-64`。**wine 在 dev box 不可靠**(Xvfb/wineboot 常抓不到輸出,且 ScummVM Windows 把 log 寫 `%APPDATA%/ScummVM/Logs/` **不寫 stdout**);驗到「PE32+ 有效 + wine 首跑達 SDL 視窗建立(objdump import 表正常、~100+ X requests)」即可,完整玩法驗證留給真 Windows。wine 別試超過 2-3 次(rabbit hole)。

## macOS:GitHub Action 編 → 抓回本機注入(參考 mac-app-cross-pack)

- `.github/workflows/build-macos.yml`:**universal(arm64 + x86_64)走「分弧 native 編 + lipo 合併」三 job**:
  - `build`(matrix):**`macos-14`** 編 arm64、**`macos-15-intel`** 編 x86_64(⚠️ **macos-13 已退役 → queued 卡死;Intel 一律用 `macos-15-intel`**)。每弧**自編 SDL2 native**(`./configure --disable-shared --enable-static`,**不加 `-arch`**)+ **乾淨 `./configure`**(對齊 willy)關壓縮編解碼,各上傳該弧 `scummvm` binary。**不用 `brew sdl2`**(會變 sdl2-compat → 黑畫面)。
  - `bundle`(`needs: build`):download 兩弧 binary → `lipo -create arm64 x86_64 -output scummvm`(`lipo -info` 應印 `x86_64 arm64`)→ 組 `.app` → 上傳 `.app` artifact。
  - ⚠️ **絕不單次 `-arch x86_64 -arch arm64 -mmacosx-version-min=...`**:min-version 會餵進 ScummVM configure 版本解析 → 炸 `test: ...integer expression expected`(~line 3228);**ScummVM configure 也沒有 `--extra-cflags/ldflags`**(寫了 "unrecognized option")。所以才要分弧 native + lipo。SDL2 靜態連結 → 無 dylib 要 bundle,lipo 後的 universal binary 自包。
- 觸發 + 抓回:`gh workflow run build-macos.yml` → `gh run watch <id> --exit-status` → `gh run download <id>`。
- `scripts/package_macos_local.sh <下載的.app>`:把 TTS 語音 + 你的遊戲資料注入 `.app/Contents/Resources/data/` → full `.app` 到 `dist-all/macos/`(個人自留)。
- 細節(Gatekeeper `xattr -dr com.apple.quarantine`、APFS DMG Windows 讀不到改 `.tar.gz`、dylibbundler、.dmg 產法)見 `mac-app-cross-pack` skill。**⚠ 自編 SDL 用 dylibbundler 必踩雷**:from-source SDL 的 install name 是 `@rpath/...`,dylibbundler 解不到會**互動式無限 hang**(CI 卡到 timeout);**務必 `dylibbundler … -s "$PREFIX/lib" </dev/null`**(給搜尋路徑 + fail-fast),見 `mac-app-cross-pack` §1.5。CI 長 hang 別憑記憶換假設,用時間戳逐階段排除(§1.2d)。⚠️ **關鍵分歧**:`mac-app-cross-pack` 是 **CMake** 遊戲(OpenXcom),`-arch arm64 -arch x86_64` **單次雙弧可行**;**ScummVM 是 autoconf**,單次雙弧會炸 configure 版本解析 → **必須分弧 native 編 + lipo**(本 skill)。同樣「runner 退役 → job queued」雷兩邊都有,對應 rule `42-reference-fidelity`(從會動的 reference 抄現用 runner 標籤)。

## [HARD] 交付包的檔名與純文字編碼(玩家端才會爆的一類)

這一類問題在 Linux 開發機上**完全測不出來**:本機解得開、看得懂,到了繁體中文 Windows
上檔案卻「不見了」。

### Windows zip 不能放中文檔名

**症狀**:玩家回報「下載解開之後,那個 .bat 檔不見了」或「檔名是一串亂碼」。

**根因(第一性)**:**zip 格式沒有檔名編碼欄位**。早期規格假設檔名是該系統的本地編碼,
後來才用 general purpose flag 的 **bit 11(EFS)** 追加「這個檔名是 UTF-8」的宣告。
Info-ZIP 的 `zip`(Linux 標準工具)把檔名以 UTF-8 bytes 寫入,**但預設不設那個旗標**:

```
UTF-8旗標=False 非ASCII=True  'τÄ⌐-Σ║₧τæƒτÄïσé│σÑç-τ╣üΣ╕¡.bat'
```

繁中 Windows 的解壓工具(檔案總管、舊版 WinRAR)看到沒有旗標,就用系統 ANSI(CP950)
去解讀那串 UTF-8 bytes:運氣好檔名變亂碼;**運氣差那串 bytes 在 CP950 裡是非法序列,
解壓工具直接跳過該檔** → 玩家看到的就是「檔案消失」。

**修法三層一起做**:

| 層 | 做法 | 為什麼 |
|---|---|---|
| **檔名** | **一律 ASCII**(`PLAY-XXX.bat`、`README-CHT.txt`) | 根治。中文留在檔案**內容**裡,玩家一開啟就看得到 |
| **zip** | 仍設 UTF-8 旗標,並在打包後驗一次 | 保險。日後有人加了中文檔名不會回到老問題 |
| **內容** | `.bat` 存 **CP950**、`.txt` 存 **UTF-8 with BOM**,都用 **CRLF** | 見下 |

別為了「中文檔名比較親切」而妥協——把親切度放進檔案內容(`.bat` 開頭 `echo` 幾行中文提示),
效果一樣而且不會壞。

**用 python `zipfile` 打包**(它對非 ASCII 檔名會自動設 bit 11),打完驗一次:

```python
with zipfile.ZipFile(out) as z:
    for i in z.infolist():
        if any(ord(c) > 127 for c in i.filename) and not (i.flag_bits & 0x800):
            sys.exit(f"✗ {i.filename!r} 沒有 UTF-8 旗標")
```

### `.bat` 存 CP950,`.txt` 存 UTF-8 with BOM

- **`.bat`**:`cmd.exe` 用**目前的字碼頁**解讀位元組。啟動器慣例是開頭 `chcp 950`,
  那**檔案本身也必須是 CP950(Big5)**,否則 `echo` 的中文是亂碼。
  存 UTF-8 + `chcp 65001` 也行,但舊版 cmd 在 65001 下有已知的批次檔行為異常,
  **CP950 對繁中玩家最穩**。
  副作用是 CP950 打不出的字會直接寫檔失敗——這是好事,逼你在打包階段就發現用字問題。
- **`.txt`**:沒有 BOM 的 UTF-8,舊版記事本會當 ANSI 解讀 → 中文全亂。
  用 `encoding='utf-8-sig'`。跨語系比 CP950 安全。
- **換行一律 CRLF**(`newline='\r\n'`)。`.bat` 用 LF-only 遇到 `goto`/label 會有難查的
  行為差異;`.txt` 用 LF-only 在舊記事本裡擠成一行。

### tar.gz 沒有這個問題

macOS/Linux 的 `.tar.gz` **不需要**改 ASCII 檔名:tar 的檔名欄位就是一串 bytes,
沒有「宣告編碼」這件事,解開時原樣還原;macOS 又是全系統 UTF-8。
所以 macOS 包裡「啟動.command」「修復-macOS.command」這種中文檔名是安全的。
**問題出在 zip 這個格式本身,不是「中文檔名」本身有罪。**

### [雷] 別用「先 cat 再轉檔」的兩段式寫法

```bash
cat > out.txt.tmp <<'TXT'
（中文內容）
TXT
python3 -c "open('out.txt','w',encoding='utf-8-sig').write(open('out.txt.tmp').read())"
```

**中間那步靜默失敗時,產物看起來「檔案有在」,但編碼是錯的**——沒有任何錯誤訊息,
`ls` 看得到、大小也正常,只有拿去 Windows 開才發現。實際踩過:BOM 沒寫進去而完全沒察覺,
最後逐檔驗編碼才抓到。**改成 quoted heredoc 餵給 python 一次寫對**:

```bash
python3 - "$STAGE/README-CHT.txt" <<'PYTXT'
import sys
open(sys.argv[1], 'w', encoding='utf-8-sig', newline='\r\n').write('''
（中文內容）
''')
PYTXT
```

### 收尾檢查(每次打包都跑)

```python
z = zipfile.ZipFile(p)
assert not [i for i in z.infolist() if any(ord(c) > 127 for c in i.filename)], "有非 ASCII 檔名"
z.read('PLAY-XXX.bat').decode('cp950')                       # 不是 CP950 會丟例外
assert z.read('README-CHT.txt')[:3] == b'\xef\xbb\xbf', "README 缺 BOM"
for n in ('PLAY-XXX.bat', 'README-CHT.txt'):
    raw = z.read(n)
    assert raw.count(b'\r\n') == raw.count(b'\n'), f"{n} 有 LF-only 行"
```

**驗編碼不能只看「檔案在不在」**——這一類問題的共同特徵就是「檔案都在、大小正常」,
壞的是內容的位元組。

## 玩家交付(distribution UX:每包附繁中 使用說明.txt)

打包好的二進位只是一半;**非技術玩家拿到第一關不是遊戲,是「打不開」**。每個平台都有一個會擋住玩家的首跑門檻,每包都附一份**繁中 `使用說明.txt`**寫清楚怎麼過:

| 平台 | 首跑門檻 | 使用說明.txt 要寫的 |
|---|---|---|
| **Windows** | SmartScreen 擋未簽章 | 雙擊 `play.bat`;警告 → 「更多資訊」→「仍要執行」。CRLF 換行(記事本才正常斷行,用 `sed 's/$/\r/'`)。 |
| **Linux** | 沒給執行權限 / 缺 FUSE | `chmod +x *.AppImage` 再跑;`Cannot mount ... FUSE` → `./x.AppImage --appimage-extract-and-run`。AppImage 是單檔 → 說明放**旁邊**。 |
| **macOS** | Gatekeeper:未簽章報「**已損毀,無法打開**」 | **那不是檔案壞掉,是隔離標記**:右鍵 →「打開」→ 再「打開」;或 `xattr -dr com.apple.quarantine <.app>`。 |

- **共通寫**:這是什麼(免裝原版/解壓即玩)、怎麼啟動、遊戲中熱鍵(F5 選單 / F8 字幕 / F9 語音)、存檔位置(不在包內)、版權備註(full 個人自留勿散布)。slim 另寫「把你合法持有的 `*.000/.001/MONSTER.SOU` 放進 `data/`」。
- **[HARD] `.app` 打包用 `tar.gz` 不用 `zip`**:zip 會破壞 `.app` 的執行權限(+x)與 bundle symlink,Mac 上點不開;tar 保留。Windows/Linux 包用 zip 無妨。
- full / slim 若同目錄並存,**說明檔名帶 mode**(`使用說明.txt` / `使用說明-FULL.txt`)避免互相覆蓋。
- 交付**資料夾**(`.app` + `使用說明.txt`)再壓,不要丟一個裸 `.app` / 裸 `.exe` 給人。

## 不要做

- ❌ 把原版遊戲資料 / 版權語音放進公開 CI 或 git → 散布盜版。
- ❌ Windows DLL 寫死清單 → 改動後缺 DLL。用 objdump BFS。
- ❌ 為了「自編 SDL2」結果 macOS 用了 `brew sdl2`(其實是 sdl2-compat)→ 黑畫面。一律 from source。
- ❌ cross-compile 還想跑 .exe 驗端序 → 用 sed force little-endian。
- ❌ wine 在 dev box 反覆鑽 → 抓到 PE 有效 + 載入到圖形初始化就收手。

## 何時套用 / 不套用

- 套用:任何 patched-ScummVM / SDL2 老遊戲漢化專案要出三平台成品。
- 配合:`mac-app-cross-pack`(macOS DMG 細節)、`dev-setup-bundle`(dev 環境)、`retro-game-playtest`(可玩性驗證)、`82-cross-platform-port-verification` rule(跨平台分歧)。
- 不套用:純 Linux 自用(只要 AppImage 那段);非 SDL/ScummVM 引擎(相依不同)。
