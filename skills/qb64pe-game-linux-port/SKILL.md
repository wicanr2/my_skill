---
name: qb64pe-game-linux-port
description: 用 QB64-PE + Docker 把 QuickBasic / GW-Basic 風 .bas 遊戲(尤其中文化版本)cross-compile 成 Linux native ELF + AppImage,並用 Wine 跨編成 Windows .exe + zip/7z。內建處理兩個 QB64-PE on Linux 必踩雷(Windows 反斜線路徑、QB64-PE 啟動自動 chdir 到 binary dir),以及完整 modular patch pipeline:中文點陣字 BDF→自家格式轉檔、自動存檔、作弊模式、Designer Review 視覺優化(片頭分色、熱鍵亮青、HP bar、minimap 雷達游標、開場字卡、死亡儀式、商店並列重排)。觸發條件:使用者想把 .bas / .qb / QuickBasic 4.5 / QB64 遊戲跑在 Linux/Windows、想包 AppImage、想做 Windows 跨編譯、需要中文字型升級、或想加入 cheat / 自動存檔 / UI 優化。產出:Dockerfile + 一鍵 build pipeline + 12 個 modular patch + Windows .exe 雙格式打包。基於 AK_CHT (Akalabeth 阿卡拉貝中文化, 2026-05) 完整移植經驗 v1.1。
---

# QB64-PE BASIC 遊戲 → Linux + Windows 跨平台移植 Skill

## 何時啟用

使用者出現以下任一情境:
- 「把這個 .bas / QuickBasic 遊戲跑在 Linux 或 Windows」
- 「QB64 / QB64-PE 編譯怎麼做」
- 「把 [QB64 遊戲] 包成 AppImage / Windows zip / 7z」
- 「中文點陣字 16x16 BDF 怎麼轉成 game 自家格式」
- 「QB64 遊戲想加自動存檔 / 作弊模式 / UI 優化」
- README 提到 QB64.com 或 QB64-PE,而 source 是純 .bas
- 任務描述含 `Screen 12`、`_Title`、`_FullScreen`、`$ExeIcon`、`PrintC` 等 QB64 關鍵字

**不適用** 場景:
- 純 DOS 16-bit BASIC.EXE 要原汁原味跑 → 用 DOSBox
- VB6 / VB.NET → 跟 QB64 完全不同生態
- FreeBASIC source → 語法相近但 QB64 擴充函數不相容
- 純 BASIC 解譯需求(不要編譯) → 用 bas55 / Just-BASIC

## 核心原則

| 原則 | 細節 |
|---|---|
| **Docker first** | 一律用 Docker 建編譯環境(`ubuntu:24.04` base)。Linux ELF / Windows .exe 都在 Docker 內產出,不污染 host。 |
| **QB64-PE 自編譯** | QB64-PE 4.5+ 釋出 source/Windows tarball,Linux side 跑 `make BUILD_QB64=y`,Windows side 用 Wine 跑現成 .exe |
| **以 root 編,輸出檔 chown 回 user** | `docker run -u $UID:$GID` 在某些 QB64-PE 版本會 silent fail(會印 "Press enter to continue" 就 exit 1),改用 root + 完 `chown` 還給 host user。 |
| **Linux port 兩雷一次解** | (1)`Open ".\..."` 反斜線在 Linux 是 literal byte;(2)QB64-PE 啟動時 auto-chdir 到 binary 目錄。兩個都用 `patch-linux-paths.py` 一次處理。 |
| **AppRun cwd = user data dir** | AppImage 啟動把 data files copy 到 `${XDG_DATA_HOME:-$HOME/.local/share}/<gamename>`,從那跑,玩家存檔自然外置。 |
| **字型升級走 BDF 路徑** | WenQuanYi 點陣正宋 / VonWaon / Unifont 等公開 BDF + Unicode→Big5 對照表(`BIG5.TXT`),用 Python 自寫 parser 轉成遊戲自家 32 byte/字 格式。**不要** 引入 freetype rasterize TTF(會有 hinting 變糊問題)。 |
| **Patch pipeline 從 .bas.orig 重套** | 所有改動寫成獨立 Python patch script,從 baseline 重套確保可重現。每個 patch 用 MARKER 防重複。 |
| **Big5 + CRLF byte-level safe** | .bas 通常是 Big5 encoding + CRLF 結尾。Python 處理必須 binary mode,絕對不 `.decode('utf-8')`。共用 `patch_bas.py` helper。 |

## 兩個 Linux Port 必踩雷(✱重點)

### 雷 1:Windows 反斜線路徑

原始 .bas 常見:
```basic
Open ".\config.ini" For Input As #1
Open ".\" + FontFile For Binary As #2
```

Linux 下 `.\` 不被 normalize,整個被當檔名,結果:
```
Runtime error: Line: NNN (in main module)
File not found
```

修法:**byte-level safe** 把 `".\\` 改成 `"./`(注意:.bas 通常是 Big5 編碼,別用 utf-8 decode)。

```python
new = line.replace(b'".\\', b'"./')
```

### 雷 2:QB64-PE 啟動會 chdir 到 binary 所在目錄

證據:
```bash
$ cd /home/user/game-data && exec /path/to/binary/akalabeth
$ cat /proc/$PID/cwd
/path/to/binary           ← 不是 /home/user/game-data
```

即使 AppRun 寫了 `cd "$USER_DATA_HOME"; exec ./akalabeth`,QB64-PE 還是會 chdir 回去。這是 Windows 遺毒。

修法:用 QB64-PE 內建的 `_STARTDIR$` 拉回原 CWD,在 `_Title` 之後立刻:

```basic
_Title "Akalabeth T-Chinese Edition v0.5.1"
ChDir _STARTDIR$         ' ← 抵消 auto-chdir,讓 AppRun 的 cwd 生效
```

兩個修法都封裝在 `assets/patch-linux-paths.py`,直接套即可。

## 標準流程

### Step 1 — 建 QB64-PE Docker image

```bash
# 複製 assets/qb64pe.Dockerfile 到專案 tools/
docker build -f tools/qb64pe.Dockerfile -t my-game-qb64pe:latest .
# 第一次 ~5 分鐘(QB64-PE 自編譯),後續 cache 秒級
```

### Step 2 — 用 patch pipeline 一鍵套全部修改

```bash
./tools/apply-all-patches.sh
# 從 .bas.orig baseline 開始,依序套必跑 patch(linux-paths)、
# save game、UI 優化(P0-1 ~ P2)、cheat、credit,
# 然後編 ELF + 打 AppImage
```

每個 patch 都是 in-place 修 `AK_CHT.bas`,順序很重要,定義在 `apply-all-patches.sh` 的 `PATCHES` 陣列:

```
1. patch-linux-paths.py       必跑(Windows 路徑 + chdir 兩雷)
2. patch-savegame.py          自動存檔
3. patch-ui-title.py          片頭分色(警告青/威脅紅)
4. patch-ui-opening.py        開場世界書頁字卡
5. patch-ui-shop.py           PrintC 內 <X> 自動染亮青(熱鍵)
6. patch-ui-msg.py            訊息分色 + 連續同方向 dedup
7. patch-ui-hpbar.py          HP bar + 顏色 ramp + 低血量閃爍
8. patch-ui-death.py          死亡儀式感(紅閃 + 大字標題)
9. patch-ui-minimap.py        Minimap player marker 雷達游標化
10. patch-cheat.py            .ini Cheat=true 模式 + 起始食物 buffer
11. patch-fix-statusclear.py  狀態列 Space$(N) 清寬度修正
12. patch-shop-header.py      商店 header 簡化版
13. patch-shop-redesign.py    商店 4 欄並列完整版(覆蓋 12)
14. patch-credit.py           譯者署名行
```

### Step 3 — Windows 跨編譯(選用)

```bash
docker build -f tools/winbuild.Dockerfile -t my-game-winbuild:latest .
docker run --rm -v "$PWD:/work" -w /work my-game-winbuild:latest \
    bash tools/build-windows.sh
# 產出:Akalabeth-CHT-Windows.7z + Akalabeth-CHT-Windows.zip
# 兩個都含 PE32+ x64 AK_CHT.exe + data files + README-Windows.txt
```

Wine + QB64-PE Windows release 跨編譯。雙格式(.zip Windows 內建支援、.7z 高壓縮)。**不做 SFX 自解壓**(7-Zip extras 不含 SFX module、自編 SFX 用 mingw cross-compile LZMA SDK 太重)。

### Step 4 — 字型升級(選用)

只在使用者要求「中文字型不夠漂亮」/「字體模糊」/「用 WQY 等公開字型」時才走這步。

```bash
docker build -f tools/fonttools.Dockerfile -t my-game-fonttools:latest .
docker run --rm -v "$PWD:/work" -w /work my-game-fonttools:latest \
    python tools/bdf-to-font_t16.py \
        --bdf /opt/fonts/wqy-bitmapsong/wenquanyi_13px.bdf \
        --big5-table /opt/fonts/BIG5.TXT \
        --out src/font_t16_wqy.dat
```

## 字型格式參考(BDF → 自家格式)

不同遊戲的中文字型檔格式不一,但典型(AK_CHT、其他 1990s 中文遊戲)結構:

| 屬性 | 值 |
|---|---|
| 每字大小 | 32 byte (16 列 × 2 byte = 16×16 bit) |
| 索引方式 | Big5 ETen,offset (1-based) = `(big5_code - 0xA140 + 1) * 32` |
| Bit order | MSB first(左邊起算) |
| 英文字型 | 通常 16 byte/字(8×16),offset = `(ascii - 0x20 + 1) * 16` |

驗證方法:讀原檔 0xA140 (「、」)字符的 32 byte,bit 視覺化(`X` = 1, `.` = 0),用肉眼比對「、」的形狀。

## QB Basic 寫 patch 時必踩雷

| 雷 | 細節 | 修法 |
|---|---|---|
| **單行 If/Then `:` 延續** | `If X Then GoTo Y: more` — `more` 變 Then 子句一部分,不是獨立 statement | 改用反向邏輯 `If NOT X Then more` 或 multi-line If |
| **module-scope 變數 Sub 不能存取** | 主程式 `Dim pw(5)` 在 Sub 內看不到 | 改 `Dim Shared` 或 GoSub label 走 line-numbered 區 |
| **單行 If/Else 巢狀解析失敗** | `If x = 0 Then A Else If x = 1 Then B Else C` 有時 NEXT without FOR | 改用 `Select Case`、`Read Data`、或 Shared 陣列查表 |
| **LocateC 越界** | row > 30 或 col > 80 觸發 `Locate` Illegal function call | 自寫 LocateC 加 row bound check,或在進入畫面前 `LocateC layer, 1, 1` reset |
| **Big5 字串字面值** | Python `b"..."` 不能含中文 (SyntaxError) | 用 `encode_big5("...")` helper 在 binary level concat |

## 可移植的 assets

`assets/` 目錄含可直接 copy 進新專案的範本(以下基於 AK_CHT v1.1 最終狀態):

### 核心 build pipeline
- `qb64pe.Dockerfile` — QB64-PE Linux 編譯環境
- `winbuild.Dockerfile` — QB64-PE Windows 跨編譯環境 (Wine + 7zip)
- `fonttools.Dockerfile` — Python 字型轉檔環境
- `build-in-docker.sh` — Linux 一鍵編譯
- `build-windows.sh` — Windows 跨編譯 + 雙格式打包
- `apply-all-patches.sh` — Patch pipeline 主控腳本
- `qa-helper.sh` — QA 自動截圖 / 按鍵 helper

### Patch 工具
- `patch_bas.py` — 共用 Big5+CRLF byte-level .bas 編輯 helper
- `patch-linux-paths.py` ✱必跑 — 兩個 Linux port 雷修正
- `patch-savegame.py` — 自動存檔 + Y/N 詢問繼續
- `patch-cheat.py` — Cheat 模式 + 起始食物 buffer
- `patch-credit.py` — 譯者署名
- `patch-fix-statusclear.py` — 狀態列清寬度修正

### Designer Review 視覺優化
- `patch-ui-title.py` — 片頭分色
- `patch-ui-opening.py` — 開場字卡
- `patch-ui-shop.py` — PrintC `<X>` 熱鍵亮青
- `patch-ui-msg.py` — 訊息分色 + dedup
- `patch-ui-hpbar.py` — HP bar + ramp + 閃爍
- `patch-ui-death.py` — 死亡儀式
- `patch-ui-minimap.py` — Minimap 雷達游標
- `patch-shop-header.py` — 商店 header 簡化版
- `patch-shop-redesign.py` — 商店 4 欄並列完整版

### 字型轉檔
- `bdf-to-font_t16.py` — BDF Unicode → Big5 索引 32B/字 字型檔

### AppImage 打包
- `appimage/AppRun` — Linux launcher,自動 setup user data dir
- `appimage/build.sh` — AppImage 一鍵打包
- `appimage/game.desktop.template` — desktop entry 範本

## 常見錯誤與診斷

| 症狀 | 原因 | 修法 |
|---|---|---|
| `Press enter to continue` 後 exit 1,沒任何 log | docker run 用 `-u $UID:$GID`,QB64-PE 寫不進 `internal/temp/` | 改用 root 跑 + 輸出 chown 還原 |
| `Runtime error Line N: File not found` | 雷 1:`.\` 路徑 | 套 patch-linux-paths.py |
| AppImage 跑會出 `File not found` 但 raw ELF 從 user dir 跑 OK | 雷 2:QB64-PE auto-chdir 到 binary dir | 套 patch-linux-paths.py(同一個 script) |
| `make clean OS=lnx` 報 "No rule to make target 'clean'" | tar `--strip-components=1` 套錯,Makefile 跑到 `/opt/qb64pe/qb64pe/` | 拿掉 `--strip-components`,讓 tarball 自己的 `qb64pe/` 前綴生效 |
| `useradd: UID 1000 is not unique` | Ubuntu 24.04 base image 預設有 `ubuntu` user 占 UID 1000 | `RUN userdel -r ubuntu` 先 |
| `locale-gen: zh_TW.BIG5 not supported` | Ubuntu 24.04 沒有預設 Big5 locale entry | 別 gen,QB64-PE byte-level 處理不需要 locale |
| chmod -R 後 chmod 沒被套到某些檔 | 後續 `RUN qb64pe -?` 又以 root 寫進 internal/temp 蓋掉 perm | chmod 放在所有 RUN qb64pe 之後 |
| Wine 跑 .exe `c0000135` (DLL not found) | QB64-PE Windows release tarball 解開後有額外 `qb64pe/` 子目錄 | 路徑加深一層 `/opt/qb64pe-win/qb64pe/qb64pe.exe` |
| QA 自動測試 game 一啟動就死 | bash subshell exit 時 SIGHUP 殺 backgrounded process | 用 `Bash run_in_background: true` 跑遊戲,subshell 不會 propagate SIGHUP |
| `If X Then GoTo Y: <body>` 的 body 永遠執行 | QB single-line If 內 `:` 後 statements 屬於 Then 子句 | 反向邏輯:`If NOT X Then <body>` |

## 參考成果

- **AK_CHT v1.1(2026-05-20)**:Akalabeth 阿卡拉貝中文化 1979 → Linux + Windows 雙平台
  - Repo:https://github.com/wicanr2/AK_CHT
  - Source:`~/game/AK_CHT/`
  - 完整時間軸 / 設計審查 / QA 驗收 / 兩雷分析:`docs/PLAN.md`、`docs/UI-REVIEW.md`、`docs/QA-REPORT.md`
  - Build artifacts:`Akalabeth-CHT-x86_64.AppImage` 3.1 MB / `Akalabeth-CHT-Windows.zip` 1.6 MB / `Akalabeth-CHT-Windows.7z` 1.1 MB
  - 設計審查項目 12/12 全套交付

## 不會做的

- ❌ 不寫 SDL2 / Raylib re-implementation(離原作太遠)
- ❌ 不轉換為 HTML5 / WebAssembly(那是另一個技能)
- ❌ 不引入 Steam 整合 / 成就系統(這類遊戲是私下分享,不是商業發行)
- ❌ 不在 host 系統 apt 裝 QB64-PE(全程 Docker)
- ❌ 不做 7zip SFX 自解壓 .exe(extras 不含 SFX module,自編太重,改用 .zip + .7z 雙格式)
