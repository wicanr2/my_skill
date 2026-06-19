# 07 — 多版本素材考古 + 遊戲中 Theme 切換 + 多輪 RE 何時收手

老遊戲常有多平台版本(DOS / Amiga / X68000 / PC-98 / FM-Towns…),美術/音樂各異但**資料結構常共用**。把各版美術抽出來、做成「遊戲中可切換的 theme」,是高 CP 的加值功能。本篇是 Dragon Wars remake 實戰(DOS + Amiga + X68000)淬煉的具體 pattern。

## 1. 多版本素材考古(format-cracking 具體 pattern)

### 先猜「同血緣 = 同格式」
**移植版常沿用同一套壓縮/資源容器,只換美術資料**。Dragon Wars 的 **Amiga `data1-6` = DOS opendw archive 同格式**(768B header 384×LE16 size，≥0xFF00=資源在別檔，接 Huffman 壓縮資源)，**資源編號與 DOS 一致** → DOS 的解壓/抽取邏輯直接重用。先試「拿 DOS 解碼器解 Amiga 檔」，對了就省一輪。

### 各平台像素格式速查(實測）
- **Amiga 全螢幕圖**:`[size_LE]` + DOS 同款 Huffman → 解出 `[16×0x0RGB BE word palette][planar **sequential** 4-bitplane MSB-first]`。palette word = `0x0RGB`，每 nibble ×17 還原 8-bit。**注意是 plane-sequential(plane0 全圖→plane1…），非 Amiga 典型 interleaved-by-row**。
- **Amiga sprite**:header `word[1]=高 word[2]=每plane每列bytes(寬=×8)`，4-plane sequential，**自帶 palette**（各怪色系不同）。literal count 單位常是 **nibble 數非 byte 數**（踩過）。
- **X68000 `.PIX`**:headerless **chunky 4bpp**（2px/byte，high nibble first），stride 用 **byte-autocorrelation** 還原。
- **X68000 文字（MONS 等）**:**nibble-swapped Shift-JIS**（`nibswap(b)=((b<<4)|(b>>4))&0xFF` → cp932）。
- **X68000 GVRAM blit**:可能是 **chunky-word**（每 word 直接=色號，**非 plane 分離、不需 deinterleave**），stride 常 1024 words/line。別預設 planar。
- **PCM 音效**：8-bit **signed** mono（波形/Goertzel 主頻分析確認是真音訊非雜訊）；轉 WAV 入庫。
- **音樂**常是 **68k 機械碼播放器 + 音符表**（如 Amiga `.tune` "MANIACS of NOISE"）或 PC-speaker PIT 方波 → 需模擬/音符解碼，多半 **deferred**。

### 原檔不入庫、工具可重現
原始 `.DIM/.adf/.PIX/.PKH/DRAGON.*` 一律 gitignore；只入庫**解碼後資產**（PNG/.spr/WAV）+ **可重現的抽取工具**（docker python/pillow）+ 文件。磁碟取檔：`.DIM`→去 256B header→Human68k FAT12；`.adf`→FS-UAE/WHDLoad HD 的 `data/`。
- **PC-98 等版本可能根本不存在**：先在 TOSEC/合集裡 grep 確認，別假設（Dragon Wars 日版只出過 X68000）。

## 2. 遊戲中 Theme 切換(架構)

讓 F8（或熱鍵）即時循環多套美術。**單一引擎、同一份在地化文字，換的是 title 立繪 / 調色盤 / sprite / viewport 元件 / backdrop / 音效**。

- **`UiTheme` 結構**(deep module，窄介面)：`title_scene` / `palette[16]` / `combat backdrop` / `overlay style` / `sprite_dir` / `sprite_own_palette` / `sprite_transparent` / `component_dir` / `ending_scenes` / `vga256` 旗標…。`theme_list()`/`by_index()`/`count()`，F8 循環 + toast 顯示主題名。
- **per-theme palette**：indexed framebuffer 維持 16 色，**切 theme 時換 palette**（SDL 端 `set_palette(theme.palette)`）。**保留「不帶 palette 的舊路徑=預設盤」→ golden 對拍/既有呼叫零變動、不破**。
- **256 色增強(真 VGA)**：若引擎是**程式化即時繪製**（非預烤 tile），256 色做在 **framebuffer(16色)→RGB 的 post-process**（`enhance_to_256`：同色直向漸層+交界壓暗+ordered dither+非線性 ramp），**不是離線重畫 tile**。只該 theme 走 256，其餘維持 16。
- **theme-aware sprite/viewport**：戰鬥/第一人稱載美術時依當前 theme 選來源 + 套對應 palette；缺檔**回退預設 theme**並誠實標 partial。
- **置中 + backdrop 陷阱**:某版 sprite 套自帶盤時，backdrop 的 DOS 索引（sky/ground）在新盤下會變怪色（如橘）→ 該 theme 改純黑底；不同尺寸 sprite 要**置中**而非固定左上落點（DOS 維持原落點保 golden）。

## 3. 多輪逆向「何時收手」(ROI 紀律)

硬格式（如 X68000 `.PKH` 標題）可能**每一輪都推翻上一輪的靜態假設**（以為 plane 交錯→其實 chunky；以為有參數表→其實檔頭垃圾）。教訓:
- **靜態臆測屢錯 → 改全程式模擬**(unicorn 跑真實 binary，讓遊戲自己解出來、dump 結果)，比猜 w/h/layout 可靠。
- **每輪精確重定位斷點**並寫進文件（「已釘死的事實」表 + 「屢錯假設」表 + 「下一步假設」），讓下一輪/下一個 agent 不重走死路。
- **設 ROI 上限**：多輪後仍受阻、玩家可感價值低 → **誠實暫時放棄、保留 RE 成果**，不無限投入。收手是專業判斷不是失敗。

## 4. 多 agent 編排與存活性
多版本抽取/渲染/RE 適合**並行背景 worktree agent**。**派工與監控紀律見 rule `35-background-agent-container-liveness`**（禁背景 sentinel/無界 dump/GUI viewer/plan mode；以活躍 process/branch commit/SendMessage 回應判活死，非 .output 新鮮度；殭屍容器要清）。

## 何時套用
重製/移植/中文化有多平台版本的老遊戲，想抽各版美術/音樂、做主題切換、或攻硬壓縮格式時。配合 `03-asset-archaeology.md`（基礎抽取）與 `04-engine-localization.md`（雙層渲染）。
