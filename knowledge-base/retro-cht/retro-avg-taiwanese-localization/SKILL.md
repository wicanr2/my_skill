---
name: retro-avg-taiwanese-localization
description: 老 AVG(冒險遊戲)繁中化的三個進階增量 —— (1)AGI(EGA)引擎 CHT(有別於既有 scummvm-sci-cht-localization 的純 SCI 方法);(2)遊戲內「標題 logo 疊繪」中文(不改原美術,引擎 render 期疊點陣圖,EGA 索引直寫 vs SCI nearest-palette-map);(3)「台式幽默在地化」管線 —— 把美式黃色冷笑話「重寫」成台灣人一看就笑,而非直譯(風格聖經+統一譯名表+批次 subagent fan-out+合併驗證+尺度校準)。外加 headless 破防拷擷取。素材:幻想空間(Leisure Suit Larry 1, AGI+SCI 雙版)。觸發:「Leisure Suit Larry / 幻想空間 / LSL1 中文化」「AGI 引擎繁中化 / Sierra AGI LOGIC 抽字 / avis durgan」「遊戲內中文標題 / 標題 logo 疊圖 / title overlay CJK」「台式在地化 / 台式笑話 / 黃色雙關在地化 / 成人喜劇漢化 / 讀者文摘梗」「批次 subagent 翻譯 fan-out / 譯名一致性 / 非 Big5 字 corrections」「headless 破年齡驗證 / 防拷問答 / debugger room 擷取」。repo: github.com/wicanr2/Leisure_Suit_Larry1-cht。
metadata:
  type: reference
---

# 老 AVG 繁中化進階增量 —— AGI 引擎、遊戲內標題疊圖、台式幽默在地化

## 一句話定位

既有 `scummvm-sci-cht-localization` 講的是「SCI 引擎怎麼吐中文」。本篇是三個**跨引擎、跨層次的增量**,以《幻想空間》(Leisure Suit Larry 1,1987 AGI/EGA + 1991 SCI/VGA 雙版)為素材:
1. **AGI 引擎** CHT —— Sierra 更早的引擎,踩雷跟 SCI 完全不同。
2. **遊戲內標題 logo 疊中文** —— 不改原始美術,引擎在標題畫面 render 期疊一塊中文點陣 logo。
3. **台式幽默在地化** —— 把笑話「重寫」成在地版,是**再創作**不是翻譯;用批次 subagent 規模化又保住一致性與尺度。

核心哲學延續 SCI 篇:**不改遊戲資源,只 patch 引擎 + 執行期內容比對替換**(英文原文當 key → 查表換 Big5)。

---

## 增量一:AGI(EGA)引擎 CHT —— 跟 SCI 不一樣的雷

AGI(Adventure Game Interpreter,LSL1 EGA 用 AGI 2.440)比 SCI 更老更簡單,但有幾個 SCI 沒有的坑:

### [HARD] 語言 gating 會讓遊戲無法啟動 → 改「字型檔存在」當開關
- AGI 走 fallback 偵測。一旦把 target 語言設成**任何非英文**(tw/de 皆然),遊戲直接回啟動器、進不去。與「中文」無關,是 AGI detector 的行為。
- 解法:**不靠 `--language`**。中文啟用改成判斷「遊戲目錄有沒有 `lsl_big5.fnt`」——`GfxMgr::loadChtResources()` 開檔失敗就 `_chtEnabled=false` 維持英文。遊戲照英文正常啟動,中文照樣生效。
- 對比:SCI 是設 `config language=tw`(寫進 config,非 CLI)。兩引擎啟用機制不同,別混。

### LOGIC 訊息抽字:連續 XOR "Avis Durgan"
- AGI 的對白在 LOGIC 資源裡,訊息段用 **avis-durgan 金鑰連續 XOR** 加密。抽字工具 `extract_agi.py`:對訊息區塊逐 byte XOR 循環金鑰 `"Avis Durgan"` 還原明文。1850 則 100% 乾淨。

### 拉畫布不縮字:forceHires 640×400
- EGA 原生 320×200,16×16 中文塞不下。`_chtEnabled` 時強制 ScummVM 內建 `DISPLAY_UPSCALED_640x400` hi-res(`initVideo` 裡 `if (_chtEnabled) forceHires=true`),中文字有空間。**與 rulebook 81「拉畫布非縮字」同源。**
- 早期誤判「hires 把 EGA 背景畫黑」——真因是上面的語言 gating(遊戲根本沒啟動);改 file-based enable 後 hires 正常。**除錯教訓:畫面全黑先確認遊戲有沒有真的跑起來,別急著怪 render。**

### 繪字 API:drawBig5CharacterOnDisplay
- `_displayScreen` 是 8-bit 索引 buffer。畫中文 = 先填背景色、`Big5Font::drawBig5Char` 寫前景,再 `copyDisplayRectToScreen(x,y,16,16)` 推到螢幕。這支 API 是後面「標題疊圖」的基礎(同一套 blit 機制)。

---

## 增量二:遊戲內「標題 logo 疊中文」—— 不改原美術

目標:標題畫面的英文 logo 旁/上疊一塊中文「幻想空間」點陣 logo(**並存**,保留經典英文字),不動原始 PIC。

### 資產管線:設計 PNG → 索引 .ovl 疊圖
- 設計師產透明 PNG(中文 logo 字樣)。`build_title_overlay.py` 烘成 `.ovl`:header(origin/size)+ 像素(0xFF=透明,否則調色盤索引)。
- **EGA**:量化到標準 16 色 EGA 調色盤(索引 0-15),引擎直接寫 display buffer。標題常用的洋紅/亮紅/青正好都在 EGA-16 內。
- **VGA**:PIL 量化到 ≤16 色**內嵌調色盤**(存 RGB),引擎端 nearest-map 到當前遊戲 palette。

### 引擎疊繪 + gate(何時疊)
- **AGI**:hook `PictureMgr::showPicture`/`showPictureWithTransition` 尾端,`drawChtTitleOverlay(picNr)`。gate = 「第一張 show 的 pic 視為標題 pic」自動捕捉(`_chtTitlePic==-1` 時記下),只疊在該 pic。索引直寫 `_displayScreen` + copyRect。
- **SCI**:沒有現成「畫背景」的乾淨 hook 點,改**piggyback 文字替換路徑**——偵測到 Sturgeon 警告文字(`strstr(text,"contains some elements of plot")`)時,渲染完在 `GfxText16::Box`/`DrawString` 尾端呼叫 `drawChtTitleOverlay()`。內嵌調色盤 nearest-map 到 `_gfxPalette16->_sysPalette`,寫 `_gfxScreen->putPixelOnDisplay` 後 `copyToScreen()` 全螢幕 present。

### [HARD] 陷阱:SCI display 是 320×200,不是 640×400
- 直覺以為 CHT 走 hi-res → display 640×400。**錯。** SCI 的 `_gfxScreen->getDisplayWidth()` 回 320×200(游戲原生解析度;字型 upscale 是另一條路)。overlay 座標/尺寸要用 **320×200**,設計稿(640×400)得先 `convert -resize 320x200` 再烘,否則 guard 判越界直接不疊。
- 診斷法:在 draw 函式開頭 `warning("disp=%dx%d")` 一次就看穿(印出 320×200)。**RE 疊圖前先印出目標 buffer 的實際尺寸,別靠假設。**

### 通則
- 缺 `.ovl` 檔自動略過(不影響其他中文化),資產隨 `game/` 目錄自帶進包;macOS CI 從版控 `fonts/` 快照 staging。

---

## 增量三:台式幽默在地化 —— 把笑話「重寫」不是「翻譯」(本篇重點)

成人喜劇(LSL1)/任何靠在地哏的老遊戲,直譯會讓笑點涼掉:「Johnny Carson 的搭檔」「菸盒衛生署警語」台灣人讀得懂英文也不會笑。**在地化 = 把 Al Lowe 想逗你笑的那個點,換成台灣人生活裡真的會笑的講法。**

### 定位一句話(先跟使用者校準尺度再動手)
> **色在雙關、笑在自嘲、賤在旁白——露骨留白,台語提味,年代感點到為止。**

兩個尺度務必先問使用者定案(用 AskUserQuestion):
- **台味濃度**:中度提味(口語國語為主+情緒點插少量台語詞:歹勢/衝/款/衰/凍未條/乎/齁啦語尾)vs 濃重 vs 淡。
- **色色尺度**:點到為止靠雙關(字面乾淨、諧音聯想、露骨留白=原作 double entendre)vs 更大膽 vs 收斂。

### 手法對照(梗庫)
先蒐一份**風格聖經**(讀者文摘中文版調性、台語激骨話/諺語、1980-90s 流行語、諧音雙關文化、原作官方笑話頁對齊目標調性)。分類手法:
- 死法旁白 = 報紙社會版標題腔/命理腔/綜藝誇張腔(「驚傳!中年男夜闖暗巷慘遭關切,當場領便當」)。
- 賴瑞台詞 = 自嘲魯蛇(「口袋比臉還乾淨」)。
- NPC 吐槽 = 一句冷回。
- 性暗示 = 諧音雙關(「小雨衣」保險套、「提早『領』出違約金」、em-bare-assing→丟「腚」、organ→生殖風琴)。
- [HARD] 分寸:涉真人/政治/族群諧音一律避開;原作年代性歧視玩笑改成「賴瑞自己很衰很糗」;族裔口音刻板笑話拿掉口音、改語言新手的通用誤用。

### 規模化管線(關鍵:批次 subagent + 一致性防漂移)
全量 3586 則(EGA 1160 + VGA 2426),流程:

1. **prep**(`prep_localize_batches.py`):從翻譯表抽「可在地化散文句」,**跳過控制碼(%開頭)、防拷雙語問答(a./b./c. 或中文含 20+ 連續英文)、過短機械字串**。切 ~130 則/批。
2. **試作一批**先給使用者看品質、確認風格,**再 fan-out 其餘**(別一次燒 27 批 token 才發現風格歪)。
3. **共用指令檔 + 統一譯名表**:寫一份 `LOCALIZE_INSTRUCTIONS.md`(風格尺度+硬規則+**統一譯名表**),每個 subagent 先 Read 同一份,降低獨立 subagent 的譯名/風格漂移。用 sonnet(品質)非 haiku。
4. **硬規則(給 subagent)**:第一欄英文原文一字不改(遊戲查表 key);`\n`/`%s`/`%v` 等控制序列位置數量保留;長度 ±30%;功能句別硬塞梗;繁中且 Big5 打得出來。
5. **合併驗證**(`merge_localized.py`):逐行核對**英文 key 一致 + 控制碼數量**,只替換有在地化的行。→ 攔下任何被污染的批次(多個 subagent 曾因**共用 scratchpad 暫存檔名撞車**互相覆寫;有的自己 diff 抓到重建,合併驗證是最後防線)。
6. **譯名一致性掃描**:即使發了統一譯名表,仍會漂移(Larry Laffer 姓氏出現 拉弗/拉佛/賴福 三種、Fawn 出現 佛恩/芬妮、Larry 出現 拉瑞)。合併後對**中文欄**做一次全域 replace 收斂(拉瑞→賴瑞、佛恩/芬妮→芳恩…)。
7. **非 Big5 字 corrections**:在地化會引入 Big5 打不出的字(𨑨迌的𨑨、腚、啧、咔、銹、é、・)。掃描 → 補 `corrections.tsv`(啧→嘖 腚→股 咔→喀 銹→鏽 ・→· é→e),`build_cht.py` 烘字時套用。**字型是從在地化譯文烘出來的 → 字元覆蓋由建構保證,唯一破口就是非 Big5 字,掃掉即可。**
8. **重烘字型 + 部署 + 實機驗證**:build_cht → 複製 game/ → headless 擷取確認在地化台詞渲染無缺字(見增量四)。

### 為何值得
翻譯只是「看得懂」,在地化是「會心一笑」。這是成人喜劇/靠哏老遊戲漢化的**招牌賣點**,也最花心思——README 要專章突顯(找遊戲文案 subagent 潤,附 before→after 對照)。

---

## 增量四:headless 破防拷擷取(截圖/驗證用)

老 AVG 開場常有**年齡驗證/防拷問答**,擋住 headless 自動擷取 gameplay。踩雷與解法:

- **年齡輸入卡住的真因**:不是「數字鍵送不到」——是**前面的警告對話框沒關掉**。先 `Return` 關警告 → 「你多大了?」才吃得下數字(38 有 echo)。踩 7 次才發現,別急著怪 xfocus。
- Xvfb 無 window manager:`xdotool windowactivate`/`windowfocus` 都可能無效;直接 `search --class scummvm` 抓 WID 對它送鍵。
- **AGI debugger `room N` 只改變數、不重繪畫面**(teleport 沒用);**SCI debugger `room N` 會正確重繪**(可 teleport,但跳到不存在的 room = fatal 直接關遊戲,只跳已知存在的)。
- 防拷 trivia 沒有可靠 skip 碼(`Ctrl+Alt+X` DOS 有效、ScummVM 無效)→ 最穩是 **detached 容器 + `docker exec` 互動逐題作答**(答案查 allowe.com/攻略),過關後 **ScummVM `Ctrl+F5` 存檔當 checkpoint**,之後 `--save-slot=N` 直接載入 gameplay,免每次答隨機題。
- 要一張「確定含在地化台詞」的畫面:載存檔後 **TYPE `look` + Return**——parser 房間描述最可靠會跳在地化旁白(比「走進門觸發換場」穩,後者對時序/起步位置敏感,偶爾要重跑)。
- docker liveness:每個 `docker run` 包 `timeout`,腳本結尾 kill 遊戲 process,跑完 `docker kill $(docker ps -q --filter ancestor=<img>)` 清殘留(容易 hang)。見 rulebook 35。

---

## 增量五:AGI 非-LOGIC 文字全覆蓋 + F8 中英切換(「完整」在地化的最後一哩)

主體對白翻完≠完整在地化。玩家還會看到**選單、道具欄、系統 UI、狀態列**。這些不在 LOGIC 訊息裡,是最容易漏、也最破壞「完整感」的殘留英文。

### AGI 文字有三個來源,少抽一個就露英文
1. **LOGIC 訊息**(`extract_agi.py`,avis-durgan XOR)——對白主體。
2. **OBJECT 道具名**(20 項:Wallet/Rose/Prophylactic…)——**OBJECT 檔也是 `Avis Durgan` XOR 加密**(同 WORDS.TOK)。解密後抽 null 結尾字串。顯示走 `InventoryMgr` → `_text->displayText(name)` → **會呼叫 `getChtTranslation`**,所以**加進 translation 表就會翻**,不必改引擎。
3. **SystemUI 引擎硬寫字串**——道具欄標題「You are carrying:」、暫停、存讀檔提示、**狀態列 Score/Sound**。這些在 `systemui.cpp` 建構子裡**按語言 switch 寫死**(有 RU/HE/FR 分支),**不走 content-key**,得自己加分支。

### [HARD] gotcha 1:EGA 用「字型檔存在」啟用中文 → `getLanguage()` 不是 ZH_TWN
- 承增量一,EGA 不能用 `--language`(會進不去)。所以 systemui 那個 `switch (getLanguage())` **永遠不會命中 `case ZH_TWN`**。
- 正解:在 switch 之後補 `if (_gfx->chtEnabled()) { ... }` 覆蓋為中文。**判 chtEnabled、不判 language。**

### [HARD] gotcha 2:init 順序——SystemUI 建構早於字型載入
- `agi.cpp`:`new SystemUI(...)` 在 `_gfx->loadChtResources()`(設 `_chtEnabled=true`)**之前**。→ 建構子讀 chtEnabled **還是 false**,中文分支不生效(道具名卻正常,因為它是顯示時即時查表)。
- 正解:把 `loadChtResources()` **移到 `new SystemUI` 之前**。它只開 `lsl_big5.fnt`/`translation.tsv`、建自己的 Big5Font,**不依賴 `_font->init()`**,可安全前移(仍在 initVideo 前)。**教訓:凡「建構子時抓一次狀態」的字串,要確認該狀態在建構前已就緒。**

### 狀態列 Score/Sound 中文化(小改動、大提升)
- 狀態列 `TextMgr::statusDraw` 用的也是 `displayText` → **本就支援 Big5**,不必另做狀態列繪字。
- 設 `_textStatusScore = "得分:%v3 / %v7"`(Big5)、`_textStatusSoundOn/Off`。**`%v3/%v7` 是 AGI 變數代換(分數),`stringPrintf` 會填,務必保留。**
- 中文比英文短,score@col1 / sound@col30 排版不撞。黑字白底(charAttrib 0,15)與英文一致。

### F8 中英對照切換(雙引擎,玩家可即時對照原文)
- **獨立旗標 `_chtLangOn`**,別重用 `_chtEnabled`——後者還牽動 hi-res 與 Big5 繪製 gate,拿來當語言開關會壞畫面。`getChtTranslation` 開頭 `if (!_chtEnabled || !_chtLangOn) return 原文/nullptr`。
- F8 在**各引擎事件入口攔截並消費**(AGI `processScummVMEvents` 的 `EVENT_KEYDOWN`、SCI `getScummVMEvent`),不傳給遊戲腳本(免被原本 F8 功能吃掉);只在中文化啟用時攔。
- **AGI=當前訊息框原地即時重繪**:`messageBox` 入口快取英文原文+wanted 排版,F8 時 `drawMessageBox(getChtTranslation(原文))`——`drawMessageBox` 內部先 `closeWindow` 再畫,**可重入**,切換即翻。
- **SCI=下一則生效**:SCI 文字框與 transient port 狀態緊耦合,就地重繪風險高,採「下次繪製生效」語意。

### 內容為 key 的漏字盤點法(通用)
- **SCI 的坑:`extract_strings.py` 只抽 message/text 資源,漏掉整批 SCRIPT 內嵌 Print/物件描述字串**(如「You see alleys…」)。→ `SCI_DUMP_RES` 已 dump `script.*`,自己寫抽取器抽 script 內英文 prose,diff 翻譯表補齊。
- **選單按鈕的 key 帶 padding 空格**(如 `" Beer "`、`"  Save  "`)——SCI 按鈕置中用空格填。key 要**逐字保留空格**才命中,譯文也保留(` 啤酒 `)免破版。
- **零成本驗渲染路徑**:同一選單裡若「已譯的顯示中文、未譯顯示英文」呈**混雜態**(如點酒選單「一輪酒」中文、`Champagne` 英文),就證明該 UI 走 `getChtTranslation`,補表即完成——不必先猜要不要改引擎。

### 引擎內 Big5 字串怎麼寫
- C++ 字面值用 **`\xNN` 逐 byte hex escape**(mirror 既有 RU/HE/FR 分支),別放裸 Big5 byte(檔案非 UTF-8)。
- **字元必須在烘出的字庫內**:字庫由 `build_cht.py` 從 translation 表的**譯文 value**取字。若引擎硬寫字串用了表裡沒有的字,先確認覆蓋(這幾組系統 UI/狀態列字剛好都被既有譯文涵蓋)。

---

## 可複用清單(換一款靠哏的老 AVG)

| 要素 | 這次做法 | 換遊戲要改 |
|---|---|---|
| 引擎繪字 | AGI drawBig5CharacterOnDisplay / SCI GfxFontChinese | 看引擎;AGI/SCI 已有範本 |
| 啟用開關 | AGI 字型檔存在 / SCI config language=tw | 依引擎 detector 行為 |
| 抽字 | AGI LOGIC avis-durgan XOR / SCI SCI_DUMP_RES | 各引擎資源格式 |
| 非-LOGIC 文字 | AGI OBJECT 道具名(avis-durgan XOR,走 displayText 免改引擎)/ SCI script.* 內嵌+選單按鈕(padding 空格當 key) | 別漏道具/選單/系統 UI,才叫完整 |
| 系統 UI/狀態列 | AGI systemui.cpp 加 `if(chtEnabled)` 分支(判 chtEnabled 非 language);狀態列走 displayText 支援 Big5,保留 %v3/%v7 | 引擎硬寫字串處各異;init 順序要 chtEnabled 先就緒 |
| F8 中英切換 | 獨立 `_chtLangOn`(勿重用 chtEnabled);事件入口攔截;AGI 原地重繪/SCI 下則生效 | 各引擎事件入口與重繪機制 |
| 標題疊圖 | .ovl 索引點陣,EGA 直寫 / VGA nearest-palette-map | 確認 display 實際尺寸!320 vs 640 |
| 幽默在地化 | 風格聖經+統一譯名表+批次 subagent+合併驗證+譯名掃描+corrections | 梗庫換該語言文化;尺度先跟使用者校準 |
| headless 擷取 | 關警告→輸入年齡→存檔 checkpoint→look 觸發 | 各遊戲防拷流程 |
| 打包 | AppImage/Windows(mingw,保 config.guess)/macOS CI(自編 SDL2 非 brew) | 見 mac-app-cross-pack、BUILD.md |

### [HARD] 通用慣例:所有 ScummVM 中文化都 enable MT-32
Roland MT-32 音樂比 AdLib/PC speaker 好很多,老 Sierra 遊戲(AGI/SCI)本就內附 MT32.DRV。**慣例:configure 一律不帶 `--disable-mt32emu`**(讓 Munt MT-32 模擬器編入;`grep USE_MT32EMU config.h` 應為 `#define`)。要點:
- 實際發聲需 **MT-32 ROM**(`MT32_CONTROL.ROM`+`MT32_PCM.ROM`,**有版權、絕不隨引擎散布/入 GitHub**;`.gitignore` 加 `*.ROM`)。LSL1 用 1987 v1.07 老 MT-32 ROM(合年代)。
- **完整包(dist-all/本機)可附 ROM** → 打包腳本從本機 ROM 目錄複製進遊戲資料夾、AppRun/.bat 設 `--music-driver=mt32 --extrapath=<游戲夾>`,開箱即用。
- **GitHub/patch-only 不附 ROM** → 不設 mt32 預設(否則無 ROM 會**彈一次阻擋框**「MT-32 emulator cannot be used…」再回退 AdLib),文件教玩家自備 ROM 後於音效選項選 Roland MT-32。
- macOS CI(GitHub runner)拿不到本機 ROM → 只開 mt32 能力、不設預設。
- 驗證:log 出現 `Falling back to MT32`(=MT32 ROM 成功載入,Munt 先找 CM32L 才回退)且無 `cannot be used` 即 OK。

### 互補
- 純 SCI 繪字/baked-art 深水區 → `scummvm-sci-cht-localization`。
- 實機「正常玩家路徑」驗收 → `retro-game-playtest`。
- 推廣片(配原版音樂) → `game-promo-video-ffmpeg` + rulebook 93。
- 驗收對 reference 非內部訊號 → rulebook 65。
