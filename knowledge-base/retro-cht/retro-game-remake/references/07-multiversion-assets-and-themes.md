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
- **PCM 音效**：8-bit **signed** mono（波形/Goertzel 主頻分析確認是真音訊非雜訊）；轉 WAV 入庫。**SFX 化**：原始音效庫常是 1–3s 持續音，當事件音（門/撞牆/命中）太長 → 播放時截短到 ~0.3–0.7s + 尾端線性淡出（防 click），**保留完整 WAV 不改檔**。

### 音樂:渲染 > 即時模擬;先確認 DOS「音樂」是不是其實是音效

- **別即時模擬 68k 自訂音樂播放器**。Amiga 自訂音樂（`.tune`，如 "MANIACS of NOISE"）= 68k 機械碼播放器 + 內嵌曲目。正解是**離線渲染成音檔**:用 **UADE**（Unix Amiga Delitracker Emulator）把 Amiga 自訂格式播成 WAV——**不需 Kickstart ROM**（避開授權）、認得多數知名 player。再讓引擎循環播放渲染好的音檔。「remake 渲染成音檔」勝「即時逆向播放器格式」。
- **DOS「PC speaker 音樂」常常其實是音效**:反組譯該位址確認——若是 `OUT` 到 PIT `0x43`/`0x40`（設方波 + 除頻）就是**單發音效播放碼**,不是音符表旋律。先確認音樂到底存不存在,別假設（Dragon Wars DOS 版根本沒有背景音樂）。
- **引擎端 BGM 模式**:music 頻道在 audio callback 循環混音（gain 壓在 SFX 之下）;**依遊戲 state 每幀 idempotent 切曲**（title/explore/combat/ending）;缺檔/靜音/無裝置一律 **no-op**（不影響 build/CI）。素材渲染與引擎播放**解耦**——引擎先就緒、放好 WAV 即播。
- **沙箱網路陷阱**:程式碼託管站（github/gitlab）可能被 auth 牆擋而 apt 鏡像可用 → 渲染工具（UADE）抓不到。對策:引擎端先做好 + 附**本機渲染 recipe**（`uade123 -w` + ffmpeg 轉 mono 22050），不卡在環境網路。

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

### viewport / sprite 圖塊重組:slot 對映 > 尺寸匹配(Dragon Wars Amiga 第一人稱實戰)

把另一版的「第一人稱 viewport 圖塊」接進引擎時,**用 slot 索引對映,不要用尺寸最近匹配**。

- **症狀**:Amiga 地牢牆面接進來後「亂貼圖」——圖塊散落、透視碎裂。根因:引擎用「DOS template 尺寸 → Amiga 子圖塊裡挑尺寸最接近的」來選圖塊,把近/中/遠的同尺寸牆面挑錯 slot。
- **正解**:抽取工具是按 offset 表序(= 引擎 pointer-table 的 sprite_offset slot 序)抽出子圖塊的,**圖塊 index 應 = slot index**(本例 `blockidx = (sprite_offset-4)/2`),不是尺寸。改回 slot 對映後粗暴錯位立刻消失、側牆正確收斂。
- **🔑 你自己的抽取工具 docstring 就是 oracle**:這條對映關係**早就寫在抽取腳本的 docstring 裡**(「blockidx = (sprite_offset-4)/2」),只是引擎端沒照做。在引擎裡重新猜多版本對映前,**先回頭讀抽取工具的 docstring/註解**——當初抽的人通常記了 index 語意。

### 受阻時的乾淨退路:「重著色正確幾何」勝過「忠實重組破碎幾何」

slot 對映修好錯位後,可能還有**落點**問題:另一版圖塊尺寸 ≠ 參考版 sprite,直接套參考版 xpos/ypos 仍重疊/破洞。若剩餘差異不阻塞目前玩家路徑，先依已證實規格完成可重現近似，並保留原生圖塊整合為明確待辦：

- **沿用參考版(byte-faithful)的透視幾何,只換 palette** 來營造另一版氛圍。本例:Amiga 第一人稱 = DOS golden 精確透視 + 一套「青藍石牆 / 棕地板」的 Amiga 風格盤 → 透視 100% 收斂、視覺仍是 Amiga 藍石地城、完全不破碎。**「把正確的幾何重著色」遠勝「把破碎的幾何忠實重組」**;誠實標示為 remake 加值,原生圖塊成果保留待後續逆向。
- **直方圖驅動配色 + 校準自真機截圖,別憑空調**:要設計重著色盤,先 dump framebuffer 目標區域的**索引直方圖**得知「哪個 index 承載哪種表面」(石牆/地板/天花),再**對著真機官方截圖取樣**那些表面的實際 RGB。教訓:我先憑印象調青藍,被打槍兩次——真機其實是**土黃磚牆**。**且要挑對參考畫面**:同一版不同區域配色不同(Dragon Wars Amiga「Mines」是灰石、「Purgatory」起始區是土黃),**校準到玩家開局第一印象的起始區**最有記憶點。索取一張真機截圖當對位/對色真值,勝過任何臆測。

### 打破單盤隔閡:RGB 區域覆寫(remake 不必受原版 16 色所限)

當「背景(主題盤)+ 前景物件(自帶盤)」需同框、但兩者色域在單一 16 色盤衝突時(本例:土黃地牢牆 + 鮮豔藍蜘蛛,套牆盤則蜘蛛被 nearest-color 洗淡、套蜘蛛盤則牆變紅磚橘地)——**remake 可以在 RGB 層合成,不必被單盤綁死**:

- 顯示層加一個 **region RGB 覆寫**:`compose()` 把 fb→RGB 上傳 texture **前**,把指定矩形像素直接換成呼叫端算好的 RGB(隨 texture 一起整數放大),用後清除(僅本幀)。
- 呼叫端各自轉 RGB 再疊:背景(牆)以主題盤轉 RGB、前景(怪物)以自帶盤逐像素轉 RGB 疊上(透明色露出背景),整塊 set 進 region 覆寫。UI/面板維持主題盤畫進 fb。
- 結果:鮮豔前景 + 正確背景同框,**對齊真機構圖**,且不動既有單盤 golden 路徑(DOS 維持原樣)。原版受硬體 16 色所限只能二選一,remake 沒這限制——這正是「打破技術隔閡」該用的地方。

## 3. 多輪逆向的證據停止線

硬格式（如 X68000 `.PKH` 標題）可能**每一輪都推翻上一輪的靜態假設**（以為 plane 交錯→其實 chunky；以為有參數表→其實檔頭垃圾）。教訓:
- **靜態臆測屢錯 → 改全程式模擬**(unicorn 跑真實 binary，讓遊戲自己解出來、dump 結果)，比猜 w/h/layout 可靠。
- **每輪精確重定位斷點**並寫進文件（「已釘死的事實」表 + 「屢錯假設」表 + 「下一步假設」），讓下一輪/下一個 agent 不重走死路。
- 證據足以寫成 `READY` 規格並驗證目前玩家路徑時，停止該 RE 切片；未解素材仍保留在
  完整性清單，不可因成本效益永久刪除。新玩家功能依賴它時再以窄任務重開。

## 4. 多 agent 編排與存活性
多版本抽取/渲染/RE 適合**並行背景 worktree agent**。**派工與監控紀律見 rule `35-background-agent-container-liveness`**（禁背景 sentinel/無界 dump/GUI viewer/plan mode；以活躍 process/branch commit/SendMessage 回應判活死，非 .output 新鮮度；殭屍容器要清）。

## 何時套用
重製/移植/中文化有多平台版本的老遊戲，想抽各版美術/音樂、做主題切換、或攻硬壓縮格式時。配合 `03-asset-archaeology.md`（基礎抽取）與 `04-engine-localization.md`（雙層渲染）。
