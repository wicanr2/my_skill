---
name: retro-argos-cht-debug
description: Debug and verify Traditional Chinese patches for AGOS/ScummVM retro games, especially Big5 or other multibyte text paths. Use when investigating Chinese-localization crashes, dialogue-box layout, save/load UI, deterministic reproduction, debug logs, Docker/Xvfb playtests, or Windows/Linux/macOS packaged builds for Waxworks-like AGOS games.
---

# AGOS 老遊戲繁中化除錯與驗證

## 核心原則

- 先辨識引擎與資料流。Waxworks 是 AGOS，不要套用 SCUMM 或 SCI 的假設。
- 先重建玩家現象，再宣稱修好；`build` 成功、headless 啟動或 debug marker 成功都不等於可玩。
- 交付 patch-only。不要把遊戲本體、ROM、原始素材、存檔或含版權影音放進公開產物。
- 以引擎原始碼、反組譯/腳本與實機畫面互相核對；不要只根據單一 log 行猜測。
- 把臨時 debugger 指令、自測 boot parameter、截圖鷹架在驗證後移除。

## Crash 排查流程

1. 記錄精確玩家路徑：場景、物件、verb、前一個成功畫面與最後一行 log。
2. 沿 opcode 到繪字/資料葉節點追蹤。例如 Waxworks 的 `SEARCH → LOOK AT` 會經過 `oww_printBox()`、`printBox()`、`getBoxSize()`，再進文字繪製。
3. 檢查編碼假設。Big5/雙位元組文字不能用 ASCII 字元數、空白斷詞或單位元組遞增來推算顯示寬度。
4. 對可疑函式建立最小、確定性的 A/B 輸入：同一段無空白 Big5 字串分別走舊路徑與修正路徑，記錄 exit code/backtrace；不要以盲點滑鼠導航作為唯一重現方式。
5. 在共用葉節點修正不安全假設。Waxworks 的 `checkFit()` 以「上一個 ASCII 空白」作回溯點；中文沒有空白時會得到 null，CHT `getBoxSize()` 應依 Big5 顯示格數與實際視窗寬度計算，繞過該 ASCII-only 演算法。
6. 保留最小必要診斷 log，例如 box 長度、選定大小、render start/done；不要把 raw Big5 當 UTF-8 印出後，將替代字元誤判成畫面亂碼。

## Big5/CJK 文字檢查

- 將 ASCII 字元按一格、Big5 lead+trail 按一個顯示格、明確換行按新列計算。
- 使用實際 `printBox()` 的視窗寬度/高度，不要只用 byte length。
- 檢查字串結尾、未成對的 Big5 lead、buffer 邊界與多行數量。
- 分別驗證「log 的位元組表示」與「畫面 glyph」；debug console 的 UTF-8 顯示不是渲染 oracle。
- 同步修改 canonical source patch。若專案以 `.patch` 重建，不能只改被忽略的 build checkout。

## 可重跑驗證

在 Docker 中執行，所有長操作包 `timeout`；使用 Xvfb 的真實視窗模式，避免只測 dummy/headless 表面。

至少完成：

1. `git diff --check` 與臨時 hook/marker 搜尋。
2. clean 或等價的 Docker 編譯，記錄明確 `BUILD_OK`。
3. 正常玩家路徑：啟動、進入中文模式、觸發原始 crash 動作、完成對話框 render；不要以 `chtbox` 或自測參數取代它。
4. 存檔與讀檔：確認 Windows portable 包的 `saves/` 是可寫且檔案非空；確認覆寫確認的熱區/語言變更沒有阻擋存檔。
5. 以非零 crash 訊號、`SIGSEGV`、`segmentation fault`、render start 無 done 作失敗條件。
6. 驗證實際打包產物，而不是只驗 build 目錄；檢查相對路徑、字型、DLL、`--extrapath`、save path 與工作目錄。

`timeout` 結束本身不是 crash；例如 `SMOKE_EXIT=124` 代表測試被有界停止，仍需查看 log 是否有 SIGSEGV 或未完成的 render。

## 測試策略陷阱

- 不要在片頭長過場、警告框或 cutscene 中盲送按鍵；先確認畫面狀態，再送下一步。
- 不要把「載入錯誤」與「存檔失敗」混淆；AGOS 快速鍵的 save/load 方向要以實測與 source 為準。
- 不要因為某一個一般文字框正常，就推論特殊物件描述或圖像路徑也正常；逐條資料流驗證。
- 不要因為 Linux native 正常，就推論 Windows zip 或 macOS app 正常；各平台的 cwd、路徑前綴、DLL、字型與訊息框行為都要檢查。
- 不要把臨時驗證碼留在正式 patch；驗證通過後 grep 清除，重新編譯一次。

## 交付判定

只有同時具備「根因可由 source 解釋、最小 A/B 或 backtrace 重現、正式玩家路徑修後通過、Docker build 通過、實際包可執行、patch-only 邊界未破壞」才標示完成。若只有 issue log 而沒有完整玩家路徑，標示為「已定位/待實機確認」，不要過度宣稱。
