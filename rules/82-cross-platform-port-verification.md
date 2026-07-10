# 跨平台移植驗證紀律 (Cross-Platform Port Verification)

把 C/C++/SDL 老遊戲(或任何原生程式)打包成多平台(Linux AppImage / Windows / macOS / Android)時,**「在我的機器上好好的」是最貴的 bug**。dev 機(通常 Linux)全綠 ≠ 目標平台能跑。本規則是「跨平台打包 bug 怎麼找、怎麼防」的硬紀律,與 `retro-game-playtest` skill(可玩性實機驗證)互補:該 skill 管「玩家路徑 / 看到的畫面」,本規則管「跨平台分歧」。

> 來源:御封戰將(openkb)繁中 2026-06,使用者回報 Windows/macOS 開不起來 + 選角閃退,而 Linux(native free/full)完全正常;三層根因只有 Wine + verbose log + addr2line 才挖到。

## 硬規則

- [HARD] **跨平台打包 bug,先在「目標平台」自己重現,不要第一時間向使用者要 backtrace。** 「Linux native 重現不出」≠「不可重現」。Windows → `wine`(host 端);無 Mac 機 → CI macos runner / 程式碼推理 + Wine 旁證 + addr2line。建不出目標平台 loop 才走「請使用者提供 crash report」流程(見 `60-feedback-loop-priority`)。
- [HARD] **驗「實際打包產物」在「它自己的執行環境」**,不是只驗 dev 機的 `build/` binary。解開 AppImage/zip/.app 在其 cwd(可能唯讀、相對路徑、bundled dll/字型)跑。
- [HARD] **缺資料一路 NULL-safe 回退,不可 deref。** 資源/檔案解析失敗回 NULL 時,葉節點函式要 NULL-check;打在**最底層共用函式**(一處保護所有呼叫端)勝過逐一 call site。

## 跨平台分歧最常見的雷(逐一查)

1. **同段 log/錯誤在不同 OS 是不同嚴重度。** 例:`KB_errlog` 在 Linux 印 stderr(噪音),在 Windows 卻彈 `MessageBox`(阻斷玩家)。**別用單一平台的行為判斷某訊息「無害」。** Linux 的「紅鯡魚噪音」可能是 Windows 的阻斷牆。
2. **相對路徑 + 引擎/框架自動前綴 base dir = 雙重前綴。** 例:config `datadir=data` + 模組 `path=data/free/`,引擎對相對路徑前綴 datadir → `data/data/free/` → 全檔讀不到。寫設定/路徑時分清「相對 cwd」還是「相對某 base dir」。
3. **「能跑的那個變體」會遮住 bug。** 一個打包正常、其他不正常時(如 AppImage 用絕對路徑 OK、Win/Mac 用相對路徑壞),**第一件事是比對它們的路徑/設定構造差異**,別假設同一份 config 到處能用。
4. **唯讀 cwd / 存檔路徑。** AppImage(squashfs)/ macOS `.app` / Android assets 的 cwd 唯讀 → 存檔要寫使用者可寫目錄(XDG / `%APPDATA%` / App Support / `getFilesDir`)。建目錄要 `mkdir -p`(遞迴),別假設父層存在。
5. **編譯器嚴格度分歧。** clang(macOS)/ mingw(Windows)把 implicit-declaration、incompatible-pointer、conflicting-types 當**錯誤**(C23 預設),gcc 只警告。本機先用 `-Werror=implicit-function-declaration -Werror=incompatible-pointer-types -Werror=int-conversion -k` 一次抓出。
6. **CI 架構限制。** macOS runner(macos-14)預設出 **arm64-only** binary → Intel Mac 跑不起來,需 universal(x86_64+arm64)。Windows mingw 的 `mkdir` 是 1-arg、絕對路徑判斷(`path[0]=='/'`)對 `C:\` 失效等。

## 工具與手法

- **目標平台重現(有界、不污染)**:`wine`(`WINEPREFIX` 放 `$HOME` 非 `/tmp`(Wine 拒絕)、Xvfb 獨立 display、`timeout -s KILL N`、`--rm` 容器內更佳)。**Wine 下 `xdotool` 合成鍵常送不進 SDL app**(事件轉譯)→ 改看「引擎層證據」(log 進度、`FAILED TO OPEN` 數、模組數、`page fault` 數),不必硬驅動 UI。
- **verbose flag 一兼兩用**:出貨預設靜默(把 resolve/缺檔噪音從 `errlog` 改 debug 級),診斷時開(如 `KB_VERBOSE=1`)印出**字面路徑** → 一眼看到 `data\data/free/` 才破案。修復(不彈框)與診斷(開了看)是同旗標兩面。
- **`-g` + `addr2line` 跨平台定位**:mingw PE 帶 DWARF → `addr2line -e app.exe <fault VMA>` 直接給 `file:line`(Windows 崩潰也能在 Linux 上定位)。Wine page fault 訊息給 `at address 0x14002A051`;PE 預設 image base `0x140000000`。

## 何時套用

- 把原生程式打包成多平台、或收到「某平台開不起來 / 閃退,但別的平台正常」的回報。
- 配 `retro-game-playtest`(可玩性 + 「跨平台分歧」章)、`retro-game-remake`(打包章)、`mac-app-cross-pack`(macOS DMG)、`60-feedback-loop-priority`(先建可重跑訊號)、`35-background-agent-container-liveness`(Wine/Xvfb/容器有界、不放生)。
- 本規則管「驗**對的**打包產物在**它自己的**環境跑」;至於「打包產物**放哪、怎麼組織**」(ship matrix 統一輸出 `dist-all/`、清舊版省磁碟、build 腳本自足自清)是**組織慣例**、非 bug 紀律 → 見 kb `mac-app-cross-pack`「產物統一放 dist-all/」節,不在本規則。
