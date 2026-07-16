# CLAUDE.md 模板 — ScummVM 老遊戲繁體中文化（AGI / SCI）

> **用法**：新開一款 ScummVM 中文化專案時，把本檔複製成該專案 `workplace` 上一層的 `CLAUDE.md`，
> 填掉「① 專案填空」區塊，其餘（②～⑨）是跨專案共用的工程慣例，直接沿用。
> 目的：**把已踩過的雷與定案的做法固化成常駐提示，減少每代重新摸索、省 token**。
> 本模板由 LSL1《幻想空間》(EGA=AGI / VGA=SCI) 中文化的實戰經驗萃取（2026-07）。

---

## ① 專案填空（每個遊戲改這裡）

```
# <中文遊戲名>（<English Title>）中文化
 - 目標：中文化當年的經典
 - 引擎：EGA=<AGI 或 SCI0> / VGA=<SCI1 或 無>   ← 決定走哪條軌，見 ③
 - 中文化僅放 scummvm patch
 - README.md 圖文並茂 + 中文手冊要點索引 + 引言（盡量蒐羅當年中文資料）
 - 遊戲畫面放大到 640x480（塞中文較好；AGI 走 forceHires，見 ④）

# github repo（只放 patch-only）
 - <repo url>

# 工作目錄
 - @./workplace

# 遊戲檔
 - EGA @./<...>.7z    VGA @./<...>.zip

# 遊戲手冊
 - @./<...> 或「沒有，上網收集 manual + walkthrough」

# Reference 同類 CHT 專案（可複用做法）
 - @../qfg-1/（**SCI 深水區範本**：SCI0 EGA + SCI1.1 VGA、hi-res live 中文文字、kFormat 動態句、GetLongest 斷行、baked-art；見 ④-S）
 - @../qfg2-ega-cht/（**SCI0 純 EGA 範本**：baked-art view 中文重繪（`sci0_view.py` decode/encode）、同劇情他版譯本高複用、三平台雙軌打包；見 ④-S、⑥）
 - @../kq4/（**SCI0 EGA + 標題疊圖 hook 範本**：kFormat `%s` 參數翻譯、drawPicture `.ovl` 中文副標 hook、防拷 BOBALU 萬用碼、三平台 full（macOS 本機注入）、推廣片；見 ④-S、⑥、⑦）
 - @../leisure_suit_2/（**SCI0 EGA + 版權保護 bypass + 中文選單列範本**：`kStrCmp` hook 略過電話號碼防拷（ZH_TWN 預設略過）、ZH_TWN 選單列加高塞中文修殘影、選單字串在 `script.997`、`kBig5Width` 縮字寬、無標題畫面、右鍵 debug 座標；見 ④-S、⑥）
 - @../space_quest3/（**SCI0 EGA + 多行 crawl 補譯 + MT-32 即時側錄 promo 範本**：script 內嵌硬 `\n` 多行 crawl 被抽字拆裂整段漏譯（覆蓋率看不出、playtest 才揪出）、`build_crawl_fixups.py` 正規化 key 補譯、原版 MT-32 音樂 SDL disk 即時側錄、純資料變更只重打包不重編；見 ④-S、⑥、⑦）
 - @../larry_suit_leisure_suit/（AGI+SCI 雙軌 + MT-32 範本）
```

---

## ② 工作模式 — 誰做什麼、用哪個 model（省 token 關鍵）

| 工作 | 負責 | model | 備註 |
|---|---|---|---|
| **架構決策 / 逆向 / 引擎 hook / 除錯歸因** | 主 session（旗艦） | 當前 session model（Opus 等） | 深水區自己做，別派便宜 model |
| **大量對白翻譯 / 台式在地化改寫** | subagent 平行 | **sonnet** | 批次 fan-out，見 `workflows/batch-subagent-localization.md` |
| **打包（AppImage/Windows/mingw build）** | subagent | **sonnet** | 機械但多步；給精確 brief（含 MT-32/容器清理） |
| **headless 實機擷取 / 截圖驗證** | subagent | sonnet | 破防拷 + 存檔 checkpoint，見 kb「headless 擷取」 |
| **美術（中文標題 logo、改圖）** | **Designer subagent** | — | 見 ⑦ |
| **README 潤稿 / 遊戲文案** | subagent | sonnet | 見 rulebook 80、90、91 |

- **[HARD] 容器清理**：subagent `docker run` 一律 `--name <專案>-<用途>`，收工只 `docker rm -f` 自己那些名字。
  **絕不** `docker kill $(docker ps -q --filter ancestor=<img>)`——會誤殺別專案容器（踩過）。
- 派多 review/核實 subagent 或喊「太貴/省 token」時，先 Read `rulebook/45-model-cost-division-of-labor.md`。
- 背景 subagent / 長操作監看 / 等 CI：Read `rulebook/35-background-agent-container-liveness.md`。

---

## ③ 引擎軌 — 先認清 AGI vs SCI（決定所有做法）

| | **AGI**（1980s，如 LSL1 EGA、早期 Sierra） | **SCI**（SCI0/1，如 LSL1 VGA、QFG1） |
|---|---|---|
| ScummVM 引擎 | `agi` | `sci` |
| 中文啟用 | **[HARD] 靠「字型檔存在」**（`lsl_big5.fnt`），**不能 `--language`**（AGI fallback 偵測遇非英文語言會**無法啟動**） | `config language=tw`（寫 config，非 CLI）；VGA target 帶 `--language=tw` |
| 畫布 | `_chtEnabled` 時 `forceHires` → 640×400，中文 16×16 佔 1 格 | **pic/view 疊圖 display 預設 320×200**（`getDisplayWidth`），座標用 320×200；**但對白文字可另開 hi-res 路徑** → 640×400 銳利（QFG1 #3，見 ④「SCI hi-res live 文字」） |
| 文字來源 | LOGIC 訊息 + **OBJECT 道具名(XOR "Avis Durgan")** + **systemUI 硬寫字串** | text/message 資源 + **script 內嵌 Print 字串** + **kFormat 動態句(`%s/%d` 模板)** + 狀態列 `DrawStatus` |
| 繪字 | `drawBig5CharacterOnDisplay`（graphics.cpp） | `GfxFontChinese`（整檔 patch，patches/fontchinese_sci.*）；**低解析借 `Graphics::Big5Font`(寫死 16px)**，要 hi-res 得自寫 32px loader |

> 動手前先 Read `~/.claude/knowledge-base/retro-cht/retro-avg-taiwanese-localization/SKILL.md`（AGI 引擎 + 標題疊圖 + 台式在地化 + headless；含增量一～五）。SCI 純繪字深水區另見 kb `scummvm-sci-cht-localization`。

---

## ④ 中文化技術要點（跨引擎共通 + 各軌雷）

- **[複用·開工先做] grep「同劇情他版譯本」命中率**：同一遊戲的其他版本（VGA remake、他平台移植）若已有繁中譯本＝**最大複用來源**——正規化 key 後比對命中率，命中的直接填、只翻未命中。QFG2 EGA 複用同劇情 VGA remake 譯本(qog-2)達 **44%**（比對前作 QFG1 僅 2%，因劇情不同）→ **別只比對前作，先找同劇情他版**。
- **內容為 key 的替換**：英文原文當 HashMap key → Big5 譯文。查無 key 就露原文。`getChtTranslation()`。
- **字型由建構保證覆蓋**：`build_cht.py` 從 translation 表的**譯文 value** 烘 Big5 字型；表裡出現的字，字型一定有。引擎硬寫的中文字串（systemUI）用到的字須確認也在表值內覆蓋。非 Big5 字用 `corrections.tsv` 補。
- **[HARD] 完整 = 別漏非主線文字**：主對白翻完 ≠ 完整。還有**選單/道具欄/系統 UI/狀態列**。
  - AGI：OBJECT 道具名（解密 `Avis Durgan` XOR）走 `displayText`→getChtTranslation，加表即翻；systemUI（道具欄標題/暫停/存讀檔/狀態列 Score-Sound）是**引擎硬寫**，要加 `if (_gfx->chtEnabled())` 分支（**判 chtEnabled 非 getLanguage()**，因 AGI 非 `--language`）。狀態列走 displayText 支援 Big5，保留 `%v3/%v7`。**init 順序**：`loadChtResources()` 要在 `new SystemUI` 之前（建構子建構時就抓 chtEnabled）。
  - SCI：`extract_strings.py` 只抽 message/text，**會漏 script 內嵌 Print 字串**；用 `SCI_DUMP_RES` dump `script.*` 另抽。選單按鈕 key **帶 padding 空格**（如 `" Beer "`），逐字保留。
  - **零成本驗渲染路徑**：同一選單「已譯顯中文、未譯顯英文」的混雜態＝證明該 UI 走 getChtTranslation，補表即可。
- **F8 中英切換**（雙引擎，玩家對照原文）：獨立旗標 `_chtLangOn`（**別重用 `_chtEnabled`**，它牽動 hires+Big5 gate）；F8 在事件入口攔截並消費；AGI 當前訊息框原地重繪（快取原文 + `drawMessageBox` 可重入），SCI 下一則生效。
- **斷行**：Big5 是 2 byte，wrap 要以「顯示欄」算（1 中文字=1 欄），別按 byte（會提早斷行）。
- **背景色**：Big5 填格用「原始意圖色」`_textAttrib.foreground/.background`，別用 `combined*`（含 invert 位會變灰底）。
- **[HARD] 引擎硬寫 Big5 字串要 clang-safe**：C++ 字面值用 `\xNN`（別裸 byte）。**clang（macOS）的 `\x` 貪婪吃後續 hex 數字**：`\xNN` 直接接 hex 字元（0-9a-fA-F，含字母 A~F）會併吞成越界 → `hex escape sequence out of range`。典型：中文逗號 `，`(`\xA1\x41`) 接 `ESC`/`ENTER` → `\x41ESC`。**GCC/mingw 放過、只 macOS CI 的 clang 爆（本機 Linux 測不出）**。修法：字面值串接打斷 `"\xA1\x41" "ESC"`（位元組相同、不加字、可攜）。字元須在烘出的 Big5 字庫內（build_cht 從譯文 value 取字）。

### ④-S SCI 專軌深化雷（QFG1 SCI0 EGA + SCI1.1 VGA 實戰，動 SCI 引擎前先讀）

- **[HARD] 內容為 key 要先「空白正規化」**：SCI 的 message/text 資源常內嵌**硬換行 `\r\n`**（如金錢句 `You have %d gold piece%s and %d silver piece%s,\r\n weighing %d.%d pounds.`），但 `translation.tsv` 的 key 是單行空白。**未正規化 → 內容比對 MISS → 退回英文**（單元測試會過、實機卻沒翻，最難查）。修法：`sciChtNormKey()` 把 key 與查詢字串的所有空白（` \r\n\t`）都收斂成單一空格 + trim，`loadChtTranslation`(建表) 與 `getChtTranslation`(查表) **兩邊都套**。
- **kFormat 動態句 hook**（`%s/%d` 帶入前的句子，如「Good luck in your quest, <名>」、金錢句）：`GfxText16` 的內容比對只看**帶入後**字串，抓不到模板 → 要在 `kstring.cpp kFormat` **帶入前**把「含 `%s/%d` 的模板」查表換成中文模板。中文規格數可**少於**英文（丟英文複數 `%s`）→ 需**子序列對應 + 參數重映射**（算出中文每個 spec 對到英文第幾個 arg，重排 `arguments[]`）。**[HARD] 防呆**：中文模板若殘留 `%s` 且非精確對應要**退回英文**——`%s` 走 `argv[startarg+idx]` 直取、不經重映射陣列，錯位會崩（`%d/%c/%x/%u` 才走 `arguments[]`）。
- **kFormat `%s` 參數本身也翻譯**（KQ4 加）：模板翻了，但**插入的 `%s` 字串（如防拷「On page N…」問題句、動態塞入的道具/地名）仍是英文** → 在 `case 's':` 取到 `tempsource` 後、**只在模板已翻時**（`chtArgCount>=0`）對 `tempsource` 也跑 `getChtTranslation`（查無回原樣、玩家自輸名不受影響）。讓「中文框架 + 英文插字」變全中文。**限模板已翻才做**＝把風險關進已知譯句，安全。
- **[HARD] GetLongest 的 PC-98 日文 kinsoku 會誤傷 Big5**（對白框**行首字掉左偏旁**：你→尔、據→豦、這掉辶）：`text16.cpp GetLongest` 對 `curChar>0xFF` 的無空格斷行走**日文 SJIS kinsoku**（刻意多塞一個超出 maxWidth 的雙位元組字 + 標點回退）。`isDoubleByte` 對 Big5 也成立 → 中文（無空格）被誤觸 → 接近滿寬的行 `textWidth>rect.width()` → `Box()` 的 CENTER `offset=(width-textWidth)/2` 變負 → 行首字被推出左邊界裁掉。**低解析也有、hi-res 更明顯**。修法：`ZH_TWN` 改「斷在容得下的最後一字」（標準中文 word-wrap，保證 offset≥0），日文路徑以 `lang!=ZH_TWN` gate 不動。**教訓**：CJK 共用碼路徑（`isDoubleByte`/kinsoku/標點表/font 900 切換）預設是為**日文 SJIS PC-98** 寫的，套 Big5 前先查有沒有「日文專屬假設」。
- **SCI hi-res live 文字**（想要對白/credits 中文銳利、非 2× 馬賽克）：SCI0 EGA 本無內部 hi-res buffer（只 Mac 有）。`screen.cpp` 在 `ZH_TWN && _upscaledHires==DISABLED` 時強制 `GFX_SCREEN_UPSCALED_640x400`（`_displayWidth/Height` ×2）；`GfxFontChinese` 另載一份 **32×28 hi-res Big5 字模**（自寫 loader，因 `Graphics::Big5Font` 寫死 16px；`bake_hires_font.py` 烘，VGA+EGA 共用一份 `qfg1_big5_hi.fnt`）。draw() 雙位元組字若 `getDisplayWidth()>getWidth()` 且 hi-res index 有此字 → `drawHiRes()`：暫開 `_screen->setFontIsUpscaled(true)`、座標 `left*2,top*2` **直寫 display buffer**（`putFontPixel`→`putPixelOnDisplay`，不再 nearest-scale），畫完還原。**ASCII 仍走原字型 2× upscale**（與美術對齊、不動）。注意：狀態列/分數列的 `font.0 glyph drawn out of bounds` 警告是**英文上游本來就有**（水平溢出 x>320），不是 hi-res 迴歸，別追。
- **hi-res 字型密度甜蜜點 + 分離 advance**（玩家常回饋「字太大/太鬆/台詞截斷」）：**advance=10 / glyph 20×20** 是實測好值（leisure_suit_2 挑出、KQ4 沿用）——20px glyph 剛好填滿 `2×advance=20px` 的 display cell，字**邊到邊密排、每行塞很多字但仍夠大好讀**。① **hi-res 與低解析 advance 要分離**：hi-res 對白用小 advance（如 10），但**選單走低解析、`Graphics::Big5Font` 固定 16px 寬，advance 太小會夾字** → 低解析維持 ≥14。用 `getCharWidth()` 依 `useHiRes()`（=非選單且 upscaled）回不同 advance，**且 draw() 的 hi-res gate 用同一條件**，否則 `GetLongest` 斷行寬度與實際繪製不一致 → 文字溢出對話框。② **row stride 用 `ceil(_hiW/8)`**（loader `bytesPerGlyph=_hiH*((_hiW+7)/8)`、drawHiRes `rowBytes=(_hiW+7)/8`、`bake_hires_font.py` 同步）→ **glyph 寬不必是 8 倍數**（20 可行）。③ 換 glyph 尺寸＝改 `kHiW/kHiH` 引擎常數 **和** `bake_hires_font.py --width/--height` 兩邊，`bytesPerGlyph` 要對得上否則 loader desync（驗算：`字數×(2 code+_hiH×ceil(_hiW/8))+2` = 檔案 bytes）。④ 行高 `_big5Height` cap 收緊（如 12）讓行間更密、對話框容更多。
- **[HARD] 對話框/Print 視窗過高會蓋頂端狀態列、關閉留白影殘留**（KQ4「F1 遊戲說明關閉後殘留遮住分數」）：SCI Print 視窗置中、依文字自動長高；**譯文太長→視窗上緣頂到狀態列區（y0-9），關閉時該區沒被 restore → 白塊殘留**（診斷特徵：殘留是視窗白底、蓋住 Score 行中段）。最省事修法：**把過長的引擎/UI 文字（如自加的 HELP 說明）精簡**到視窗落在狀態列下方不重疊（也是更好 UX）；根治則需在視窗 dispose 後重繪狀態列。判是不是自己造成：長文字是不是你加/改長的。
- **[雷] `build_translation.sh` 的 `.done` glob 路徑**：批次翻譯的 `*.done` 常放 `translation/done/` 而非 `translation/batch/`，glob 寫錯會**漏收全部翻譯、只剩 skeleton 英文 → 輸出 0% 覆蓋**（KQ4 踩過、差點污染 master）。**部署真相是手維護的 master `translation/translation.tsv`，非 build 腳本的 batch merge**（master 常多出手加項）；重烘字型/tsv 從 master，別盲跑 build_translation.sh 覆蓋 master。
- **抽字別漏 script 內嵌 + 動態句**：`SCI_DUMP_RES=<dir>` env hook dump text/message/**script**；`extract_strings.py` 只抽 message/text，會漏 script 內 Print 與 kFormat 模板。找某畫面 view id 用 `SCI_LOG_GFX=1`，全 view dump `SCI_DUMP_ALLVIEWS`。**[HARD] 引擎 dump/env hook 跑完不自退，`docker run` 一律 `timeout` 包；headless 別用 `wait` 等背景 `&` 的 Xvfb（不退會永久卡，踩過容器跑 44 分鐘）→ 用 `pkill -f scummvm` 收、讓 script 自然結束**。
  - **[HARD] script 內嵌對白常黏前導 bytecode → 別「含控制碼就整條跳過」**：SCI script 字串前常黏 bytecode（`Press '?'` 前是 `\xb0\x03`，含控制碼 `\x03`）。`extract_ega_scripts.py` 若「含控制碼一律 skip」會漏一批玩家可見對白。修法：**剝前導非文字 byte 取乾淨文字**（第一個字母/引號起、到下個控制碼止）再嚴格過濾（≥2 英文詞、純 ASCII、排 bytecode 雜訊/debug）。**playtest 進實際畫面才揪得出**（QFG2 進職業選擇才發現「Press '?'…」殘留→補抽 50 則）。
  - **[HARD] script 內嵌「多行硬 `\n` crawl」被逐行工具拆裂 → 整段漏譯、覆蓋率統計看不出（SQ3 踩過，最隱蔽的漏譯）**：開場旁白/過場敘事/星球掃描讀數/片尾致謝這類 crawl 常是**單一 script 字串內含硬 `\n` 換行**（null 終止、非 text/message 資源）。`full_skeleton.tsv` 用逐行 tsv 存 → 多行 key/value 被拆成多個物理行、TAB 分隔符落在中間某行 → `merge_translations.py`/`build_cht.py` 逐行讀時把那些**無 tab 的續行當 malformed 整批丟棄，從不進 translation.tsv → 實機整段顯英文**，而**覆蓋率統計看不出**（碎片不在 worklist、`grep 全句`也因換行搜不到）。**只有 playtest 走到那些過場畫面才揪得出**（SQ3 是做 promo 擷取開場才發現，WORKLIST 還誤記「開場旁白中文 ✅」→ 印證 ⑨ / rulebook 63「truth in code」）。抽字階段就防：從 script dump 抽 **null 終止字串**、對含 `\n` 的多行敘事**先正規化成單行**再入 skeleton。補救（`tools/build_crawl_fixups.py`）：用原文子字串在 script dump 定位確切字串（**取最短命中**避免抓到更長的黏連塊）→ `\s+→單空格+trim` 算正規化 key（**與引擎 `sciChtNormKey` 逐字一致**：忽略前導空白、連續空白收斂成一個、去尾）→ 配譯文 append 進 skeleton（引擎載入 tsv key 也走 `sciChtNormKey`，故單行 key 對得上多行遊戲字串）。**渲染路徑不用擔心**：`cache.cpp getFont` 在 ZH_TWN 下**包裝每一個 font**（含 crawl 用的特殊斜體 serif 字型）→ 雙位元組一律走 Big5 hi-res。
- **小雷**：① Big5 `translation.tsv` 被當 binary → `grep -a` 才搜得到；② 引擎內用 `getenv` 開 debug 需檔頭 `#define FORBIDDEN_SYMBOL_EXCEPTION_getenv`（ScummVM forbids，見 paint16/view.cpp）；③ SCI **文字**啟用判 `getLanguage()==ZH_TWN`（config `language=tw`），與 AGI 的判 `chtEnabled()` 不同軌，別混。

### ④-S2 SCI 選單/防拷/字型深化雷（LSL2《幻想空間II》SCI0 EGA 實戰，動選單·防拷·字寬前先讀）

- **[HARD] 中文選單列殘影 → 根因是「選單列太矮，中文字溢出清不掉」**：SCI 選單列 `_menuBarRect`（`ports.cpp`）寫死高 **9px**，但 Big5 字高 14px → 中文選單標題**下緣溢出到列外**；`GfxMenu::kernelDrawStatus` 的 `fillRect(_menuBarRect,…)` 只清 9px 的 bar rect → 溢出部分**永久殘留**在遊戲畫面上（英文標題只 ~7px 不溢出，故英文乾淨、中文才爆）。修法：`ports.cpp` **ZH_TWN 時把 `_menuBarRect`/`_menuRect`/`_menuLine` 高度加到 15px**（`g_sci->getLanguage()==Common::ZH_TWN ? 15 : 9`），中文塞得下、fillRect 清得掉。加高的列落在畫面最頂（天空/屋頂區），不破壞場景。
  - **[HARD] 併發雷（invert 反白項黑底黑字隱形）**：hi-res `drawHiRes` 走 `putPixelOnDisplay` **只寫 display buffer 不寫 visual**，而選單 highlight（`invertRect`）、還原（`bitsSave/Restore`、`fillRect`+`bitsShow`）走 **visual buffer** → 選單被 highlight 的項目 invert 只翻 visual、bitsShow re-upscale 把 hi-res 中文蓋成黑底 → **黑底黑字隱形**（ASCII 快捷鍵活在 visual buffer 故正常反白成白字＝「只剩快捷鍵可見」診斷特徵，KQ4 玩家回饋「選項全黑」）。低解析路徑 `putFontPixel`（非 upscaled 分支）**同時寫 visual+display** → 走低解析就能正確 invert/清除。**修法：`GfxScreen` 加 `_menuTextActive` 旗標，`GfxMenu::drawBar`（列標題）＋`drawMenu`（下拉項）繪字時設 true，`GfxFontChinese::draw` 旗標開啟時跳過 hi-res 走低解析**（受改 `screen.h`/`menu.cpp`/`fontchinese.cpp`）。低解析+加高列兩者都做才乾淨。**⚠ 別用 `top<8` heuristic**（leisure_suit_2 舊做法）——那只涵蓋選單列標題、**漏下拉項**（下拉在 top≈15+，仍 hi-res 仍隱形）；KQ4 用明確旗標涵蓋列標題+下拉才完整。**教訓**：任何「先 hi-res 中文再對該區 invert/重繪」的 UI（選單、反白清單）都有此雷。
- **選單字串在 `script.997`（kSetMenu 組合字串），非 text/message 資源**：格式 `Name`#N:Name2`^x:--! :…`（` `` `=accelerator 分隔、`#N`=Fn 鍵、`^x`=Ctrl-x、`:`=分項、`--!`=分隔線）。`GfxMenu::drawBar`/`drawMenu` 對**每個 item 的 `textSplit`（backtick 前的字）**走 `getChtTranslation`→補表即翻。**標題帶 padding**（`" File "`）、**item 不帶**（`"Save Game"`）。抽字工具會漏（含控制碼被過濾）→ **手動從 `script.997` `strings` 撈、把 bare item 加進 `full_skeleton.tsv` 再翻**（漏加 skeleton＝不進 runtime tsv/字型）。零成本驗：開選單看「混雜態」哪些還英文就補哪些。
- **[HARD] 版權保護（電話號碼/問答式）用 `kStrCmp` hook 略過**：LSL2 開場要輸入照片女子的電話（`555-dddd`），答錯兩次**直接退出**。答案存 `script.010`（16 組號碼、女子隨機），玩家對照手冊電話簿。做法：`kstring.cpp kStrCmp` 加 hook——`result!=0 && (getLanguage()==ZH_TWN || getenv("SCI_CP_BYPASS")) && 運算元符合 "555-dddd"` 時強制 `result=0`。**gate 在「答案的特徵格式」**（`555-`+4 數字，只有防拷會用）＝把風險關進已知字串，一般字串比較不受影響。**CHT 版預設略過**（ZH_TWN 即生效，重玩友善；原版退出太兇）；`SCI_CP_BYPASS` env 另供英文/debug。**先 grep dump 找答案格式所在 script** 再決定 hook 哪個 kernel（可能是 `kStrCmp`/`kStrEnd`/parser）。
- **[HARD] 多題/多型驗證要略過 → 「跳門」直接換到門後房間，別逐題答對或逐題 hook**（LSL1《幻想空間》年齡+成人問答，EGA/VGA 雙版）：驗證是「年齡選單 + 一連串問答（常識/笑話/手冊防拷，各題輸入方式不同）」時，`kStrCmp` hook 那種「攔一個字串比較」不夠用，逐題模擬作答更是無底洞（每種題型一個特例，見 `rulebook/41`）。**第一性原理：驗證只是一道門，直接跳到門後的起始房間**（LSL1 EGA=room 11、VGA=room 100，皆遊戲第一個場景）。用引擎**自己的 restore/除錯換場機制**（不要自己重造流程）：
  - **SCI**：事件層攔 `Ctrl+Alt+X`（`event.cpp` getScummVMEvent，F8 handler 旁）→ `_gamestate->setRoomNumber(N)`（＝除錯器 `room` 指令；`console.cpp cmdRoomNumber` 就這行）＋ `abortScriptProcessing = kAbortLoadGame`（**打斷驗證控制項的 VM 阻塞事件迴圈**——光設 room 不會中斷它；`kAbortLoadGame` 讓 VM unwind 後呼叫遊戲 `replay` 進 `currentRoomNumber()`＝剛設的 N，即「在選單時載入存檔」的恢復路徑）＋ `_gfxPorts->reset()`（**清掉殘留的年齡選單對話框 window**，否則疊在新場景上；同 `savegame.cpp` restore 路徑）。
  - **AGI**：`keyboard.cpp processScummVMEvents` 攔 `Ctrl+Alt+X`（room==6）→ `_text->closeWindow()` ＋ `_game.exitAllLogics = true`（中止驗證室 logic）＋ `cycleInnerLoopInactive()`（打斷 getnumber/messagebox 內迴圈）＋ `newRoom(N)`（直接換場，比照 AGI restore 從 inner loop 動手）；一律消化該按鍵避免 `x` 漏進遊戲 parser。
  - **通用心法**：需要強制引擎狀態時，**看引擎自己的 debugger / restore 怎麼做，照抄那套 primitive**（此處全抄 `cmdRoomNumber` + savegame restore），比自己模擬遊戲流程穩得多。細節見 qfg-1 同層 LSL1 `docs/45-sci-age-verify.md`。
- **[SCI 中文字大小/密度調整（`fontchinese.cpp` 三顆旋鈕）]**——玩家嫌「字太大 / 字距太寬」都調這裡：
  - **`kBig5Width`＝advance（字距）**：Big5 字在 320 空間的前進寬度（getCharWidth 回它、GetLongest/Box 算寬也用它）。**這顆決定「字間距」**——縮它中文變密、每行容更多字（中文行數本就 ≈ 英文，縮窄更寬鬆）。顯示字距 = `kBig5Width × 2` px。
  - **`kHiW`/`kHiH`＝hi-res glyph box（字大小）**：hi-res 字模的像素寬高。**這顆決定「字大小」**。烘字 `bake_hires_font --width<kHiW> --height<kHiH> --size<略小>`。
  - **`bake --size`＝字框內留白**：size 越接近 height，字填滿字框、內部留白越少（視覺更密）。
  - **[HARD] 三顆的鐵律**：① `kHiW ≤ kBig5Width×2`（否則 glyph 溢出下一格、疊字）；② glyph box == advance 顯示寬（`kHiW == kBig5Width×2`）時字框緊貼、最密；③ **`build_translation.sh` 的 bake 參數必須跟引擎 `kHiW/kHiH` 一致**，否則被預設值蓋回、引擎讀錯 `bytesPerGlyph` → hi-res 亂碼。
  - **非 8 倍數字寬**（要 20px 這種）：`kHiW` 原本假設 8 倍數（rowBytes=`kHiW/8`）。放寬＝bake 打包與引擎 `bytesPerGlyph`/`rowBytes` 都改 **`ceil = (kHiW+7)/8`**、bake 內層 `x < W` guard。這樣 20px（rowBytes=3）等任意寬都行。
  - **實戰檔位**（LSL2 定案，供起手）：advance 16/glyph 32＝原始偏大；**14/24**＝小一號；**12/24**＝更密；**10/20**＝密又可讀（玩家定這個）；8/16＝經典 Big5、偏小。**改字型是主觀來回**，先出對照截圖（同一句 narration 裁切併排 `convert -append`）給玩家挑檔位，**確認後才做全平台重編/重打包**（別重建兩次）。
- **無標題畫面別硬找**：LSL2 EGA 開機→**版權房 pic（本作 pic 10）→ 遊戲街景**，**沒有獨立標題 logo pic**（`SCI_LOG_GFX=1` 只見 pic 10→23）。動標題疊圖前先確認真有標題 pic，沒有就別做（不像 KQ4 有 pic 96）。
- **F1 = 遊戲內建操作說明**（打字式冒險必看），LSL2 的 F1 help 在 text 資源、抽字即翻 → 新手「不知道打什麼指令」的需求靠它 + 手冊指令對照表解決，不必自加 help 畫面。
- **右鍵顯示 `43/153` 之類數字 = SCI 內建 debug 滑鼠座標**（`Shift-click shows mouse location`），非中文化迴歸（改動沒碰 event/mouse）→ 文件標注即可。判別法同 ⑨：跑英文版對照。

---

## ⑤ 音樂 — [HARD] 所有 ScummVM 中文化都 enable MT-32

Roland MT-32 遠優於 AdLib，老 Sierra 本就內附 MT32.DRV。**configure 一律不帶 `--disable-mt32emu`**（Munt 編入，`grep USE_MT32EMU config.h` 應 `#define`）。改所有 configure 點：Linux 本機、macOS CI(arm64+x86_64)、mingw、docs。

- **MT-32 ROM 位置（本機）**：`~/cht/mt32`（含 1987 v1.07 control + MT32_PCM.ROM；用 v1.07 合老遊戲年代）。
- **[HARD] ROM 有版權**：`.gitignore` 加 `*.ROM`，**絕不入 GitHub / patch 包**。
- **完整包（dist-all，本機）可附 ROM**：`pkg_common.sh` `stage_mt32_rom()` 從 `MT32_ROM_SRC`(預設上面路徑) 取檔改名成 `MT32_CONTROL.ROM`+`MT32_PCM.ROM` 放進包內 `game/`；AppRun/.bat 加 `--music-driver=mt32 --extrapath=<游戲夾>`。**有 ROM 才設 mt32 預設**。
- **patch-only / GitHub / macOS CI 不附 ROM、不設 mt32 預設**：無 ROM 又設 mt32 會**彈一次阻擋框**「MT-32 emulator cannot be used…」再回退 AdLib。玩家自備 ROM 放遊戲夾後於音效選項選 Roland MT-32。
- **驗證**：跑起來 log 出現 `Falling back to MT32`（Munt 先找 CM32L 才回退＝MT32 ROM 載入成功）且無 `cannot be used` 即 OK。
- **[HARD] 複用他專案已編 binary 前先 `grep USE_MT32EMU config.h` 查證**：別假設「跨專案通用的引擎 binary」就合規——QFG2 踩過：想複用 qfg-1 的 scummvm，實測竟是 `#undef USE_MT32EMU`（該次 configure 帶了 `--disable-mt32emu`）→ 只好自建 scummvm-src 重編。複用前一律 grep 確認，不符就重編（`apply_patches.sh` 支援自 clone pinned commit 重建）。

---

## ⑥ 打包 — 每平台雙軌：patch 版(→Release) + full 完整版(→本機 dist-all)

- **[HARD] 交付是「每平台雙軌」，動手打包前先把這張表列全、別等使用者問才補 full 版**：三平台（AppImage / Windows / macOS）各出**兩種**包，去處/含遊戲/啟動/ROM 見表——

  | 版本 | 含遊戲? | 去處 | 啟動 | MT-32 ROM |
  |---|---|---|---|---|
  | **patch 版** | ❌ 只引擎+中文資料 | **上 GitHub Release**（公開下載，玩家自備遊戲） | `.bat`/`.app`/`AppRun` 需玩家指 `--path` 到自備遊戲夾 | 不附（玩家自備） |
  | **full 完整版** | ✅ 內嵌整個 `game/` | **只本機 `dist-all/`（gitignore）**，私人保留 | 啟動器**直指內嵌 game**、免輸路徑，直接玩 | **可附**（本機無 IP 顧慮） |

- **[步驟一·編 engine]** 各平台先編出引擎（patch 版基礎；full 版用同一份 exe/.app 再塞 game）：
  - **Windows**：`scummvm-win/`（獨立 mingw source 樹）configure `--host=x86_64-w64-mingw32 ...`（**去 --disable-mt32emu**）+ make → `scummvm.exe` + DLL（SDL2.dll、libwinpthread-1.dll）。**[HARD] source 複製勿排除 `config.guess`/`config.sub`**（否則 endianness unknown）。
  - **macOS**：`.app` 只能 macOS host build（CI）→ 見下方「macOS CI 常見雷」專段（**這條最常出問題**）。
  - **AppImage**：`package_appimage.sh`，`--appimage-extract-and-run` 免 FUSE。
- **[步驟二·組 patch 版]** engine + 中文資料（`dist-cht/`）打包，**不塞遊戲** → 上 GitHub Release。啟動器要玩家指 `--path` 到自備遊戲夾。**中文資料放獨立夾、啟動器帶 `--extrapath=<cht夾>`**：引擎的 `translation.tsv`/`qfg1_big5*.fnt` 走 `Common::File::open`（經 `SearchMan`，含 extrapath）→ 玩家遊戲夾（`--path`）+ 內建中文資料（`--extrapath`）兩處都搜得到，免玩家自己複製中文檔進遊戲夾。實機驗一次（`--path=game --extrapath=cht` 進 in-game 看對白中文）。
- **[步驟三·組 full 版]** engine + 中文資料 + **整個 `game/`（遊戲+ROM）** 打包 → 本機 `dist-all/`：
  - **一鍵** `tools/build_distall.sh`（複用 qfg-1）三函式：`mk_appimage_full`（game 內嵌 squashfs、AppRun `--path=$HERE/usr/share/game`）、`mk_windows_zip`（exe+DLL+`game/`+.bat）、macOS（見下方 KQ4 注入流程）。full 版啟動器**直接** `--path=<內嵌game> --language=tw --auto-detect`，**不互動輸路徑**（那是 patch 版才做的）。
  - **[HARD] Linux(AppImage) / Windows full 在本機直接建**（有本機 game/ROM）；**macOS full 不是——`.app` 只能 macOS host build（CI），CI 又拿不到遊戲/ROM（不在公開 repo）→ full 版 = 「下載 CI 的 engine-only artifact → 本機注入」**。`tools/package_macos_full.sh`（KQ4 定案）流程：
    1. `gh run download <run> --name <macos-artifact>` 取 CI 的 engine-only tar.gz（內含 universal `.app` + SDL2 dylib + cht-data，**無遊戲、無 ROM**）。
    2. 建**統一 `game/` 夾**於 `ScummVM.app/Contents/Resources/game/`：`RESOURCE.*` + `translation.tsv` + 兩個 `.fnt` + **title `.ovl`** + MT-32 `MT32_CONTROL.ROM`/`MT32_PCM.ROM`（正名）。
    3. **啟動包裝**：`mv Contents/MacOS/scummvm scummvm.bin`；新寫 `Contents/MacOS/scummvm` 為 bash wrapper（CFBundleExecutable 仍指 `scummvm`）＝`exec "$DIR/scummvm.bin" --path="$DIR/../Resources/game" --auto-detect --language=tw --music-driver=mt32 --extrapath=…`。`@executable_path/../Frameworks` 的 SDL2 rpath 因 `scummvm.bin` 同在 `MacOS/` 仍解析。
    4. **[HARD] 改動已簽名 .app → 簽章失效**：`rm -rf Contents/_CodeSignature`（變「未簽」勝過「壞簽」），並附 `修復-macOS.command`（`xattr -cr ScummVM.app && codesign --force --deep --sign - ScummVM.app`）。**Linux 端無法 codesign 代簽/實測** → full 版是本機組的，**引擎已 CI 驗、注入是機械步驟，但整包要請使用者在 Mac 上跑一次 `修復.command` 再開 app 確認**（第一性驗證，別假設）。
    5. 打包 `tar czf`（保 perm + .app 結構；`.dmg` 需 macOS hdiutil，Linux 端只出 tar.gz）。
  - **full 版可附 MT-32 ROM**（見 ⑤ `stage_mt32_rom`，本機無 IP 顧慮）；**ROM 仍 `*.ROM` gitignore、絕不入 git**。
- **[步驟四·驗收]** **[HARD] 收尾必做**：`dist-all/` 有「三平台 × full」齊、GitHub Release 有「三平台 × patch」齊；解開驗證——任一 **full 包必含** `RESOURCE.00x`（`unzip -l`/`--appimage-extract` grep），任一 **patch 包/Release 資產必不含**任何 `RESOURCE.*`/`.DRV`/`SCIV.EXE`（誤含=違反 [HARD] patch-only）。
- **[效率] 只改資料（translation.tsv/字型/ovl）沒動引擎碼 → 別重編引擎、只重打包**（SQ3 crawl 補譯後發 v1.1 用此法）：純資料變更下引擎 binary 不變 → **Linux/Windows 沿用現成 `scummvm`/`scummvm.exe` 只重跑 `package_*.sh`**（吃更新後的 `game/`+`dist-cht/`）；**macOS 重跑 CI**（它用新 committed `dist-cht/` 重新注入+ad-hoc 簽章，引擎輸出不變；**先 push 新 dist-cht 再觸發**，雷 12）。省掉整輪重編。重打包後照樣跑 [步驟四] 收尾（patch 無 `resource.*`、full 有、`grep -a 新譯 key` 在包內）。**發修正版**：新 tag（v1.1）+ `gh release create`；舊版若含缺陷資產，`gh release delete <舊> --cleanup-tag` 刪掉免玩家下到缺陷版（**發/刪公開 Release 屬對外動作，先取得使用者確認**）。
- **引擎改動後 scummvm-win 要同步**：它是純目錄（無 .git）。從 `scummvm-src`（git checkout）`for f in $(git diff --name-only HEAD); do cp ...`（連 untracked fontchinese）即同步 patch 改動的檔。
  - **[雷] 啟用新子系統時補 vendor 靜態檔**：上法只補「patch 改動的檔」。啟用先前停用的子系統（如 `mt32emu`）時，其 vendor 靜態標頭可能在 scummvm-win **缺席**（當初停用時被剪）→ mingw 編譯報 `MT32EMU_VERSION_MAJOR/MINOR/PATCH` 未宣告。具體：`audio/softsynth/mt32/config.h`（Munt 版本標頭，內容跨平台相同、scummvm-src 有 git 追蹤）。修法：從 scummvm-src 補該檔。**更穩**：啟用新子系統後編譯前，`diff -rq scummvm-src/audio/softsynth/mt32 scummvm-win/audio/softsynth/mt32`（濾掉 `.o/.dwo/.d` build 產物）比對缺檔補回。
- patch 維護：改完引擎 `cd scummvm-src && git diff HEAD -- engines/agi > patches/0001-*.patch`（SCI 同理 0002）。scummvm-src 是 pinned commit 的 git checkout，`git diff HEAD` 即完整 patch。
  - **[雷] SCI 若 scummvm-src 非 git（純目錄）或 patch 走 `patch -p0` 拼接**：新檔（如 `fontchinese.{h,cpp}`）**整檔複製**、既有檔逐檔 diff。重生某檔 hunk：`curl` `patches/UPSTREAM_COMMIT.txt` 記的 pinned commit 的 **pristine** 檔（`raw.githubusercontent.com/scummvm/scummvm/<commit>/...`）→ `diff -u --label <path> --label <path> pristine 現檔` 產 -p0 hunk → 抽換進總 patch 對應區段 → **抓齊全部受改檔對 pristine `patch -p0 --dry-run` 驗證整份可套**再 commit。
- 相關規則：mingw/macOS 細節見 rulebook `82-cross-platform-port-verification` + `mac-app-cross-pack` skill；完整性優先見 `83-retro-completeness-over-roi`。

### macOS CI 常見雷（**最常壞的一環，動 build/CI 前先讀**；深水區 → kb `mac-app-cross-pack`）

> 前提：macOS `.app`/`.dmg` **只能在 macOS host build**（codesign/hdiutil/iconutil 都 macOS 限定），走 GitHub Actions `macos-14`(Apple Silicon) runner。**本機 Linux 測不出這些雷**（尤其 SDL、Gatekeeper），只能靠 CI 實跑。

1. **[HARD] 別 `brew install sdl2`**——2026-06 起 brew 的 sdl2 = **sdl2-compat shim**（runtime 才 `dlopen libSDL3`）；dylibbundler 只打包靜態相依、抓不到 libSDL3 → 玩家端 **「Failed loading SDL3 library」/ 黑畫面**。**本機有裝 SDL3 測不出來**、CI 也是哪天 brew 換內容才突然壞。→ **CI 自源碼編 pinned 真 SDL2**（如 2.30.9），universal 用「每弧各編 + `lipo -create`」。
2. **[HARD] ScummVM configure 不是 autoconf 友善**：`CXXFLAGS=-arch ...` 直接餵會 `integer expression expected`/`unrecognized`。**CXXFLAGS/LDFLAGS 只能當環境變數餵**，不能塞 configure 參數。
3. **universal 別單次雙 `-arch`**：autoconf 版本解析在雙弧下會炸。要**每弧 native 各編一次 + `lipo -create` 合併**；x86_64 弧在 Apple Silicon runner 上走 `arch -x86_64`(Rosetta)，arch 值須與 runner 一致。用**兩份獨立 per-arch checkout**（免共用 build 目錄互汙）。
4. **clang 比 GCC/mingw 嚴（本機 Linux 測不出，只 macOS CI 爆）**：① `std::unary_function` 找不到（Xcode 15 C++20 移除），1990s 老碼需 patch；② **引擎硬寫的 Big5 `\xNN` 貪婪 escape 越界**（`，ESC`→`\x41ESC`>255 `hex escape out of range`），見 ④ 末條，修法字面值串接 `"\xA1\x41" "ESC"`。**凡在引擎硬寫 Big5/加 C++20 語法後，第一條 macOS CI 必實跑。**
5. **依賴面保持最小**：AGI/SCI 裁剪配置只需自編 SDL2；zlib/curl 是 macOS 系統庫；libvorbis/FLAC/png/freetype 不需要（別多自編/brew）。
6. **啟用新子系統（如 mt32emu）首次 CI 要盯**：跟 mingw 一樣可能缺 vendor 檔或觸發平台特有編譯錯——**動了 configure flag 後第一條 CI 一定實跑驗證**，別假設。
7. **版本 drift**：SDL2 release tarball 網址、ScummVM pinned 版本、runner 映像（`macos-13` 退役、Intel job 改 `macos-15-intel`）會隨時間變，首次/久沒跑要微調 workflow。
8. **dmg 相容**：APFS dmg 在 Windows/WSL 讀不到 → 同時產 `.tar.gz`(保 perm) + `.dmg`(mkisofs -hfs hybrid)。dylibbundler 偶爾無限「Try again / can't get path for @rpath」。
9. **Gatekeeper**：未簽署 app 首次執行要 `xattr -dr com.apple.quarantine /Applications/ScummVM.app`（README 要寫）。
10. **cht 資料 post-build 注入**：`game/` gitignore、CI 拿不到 → `package_macos_data.sh` 從版控 `dist-cht/`（或 `fonts/`）快照注入（跟 Linux/Windows md5 一致才不 drift）。ROM 同理 CI 拿不到 → macOS(patch 版) 只開 mt32 能力、不設預設。**[雷] 注入清單要含「全部」cht 檔——別只 `translation.tsv` + `*.fnt` 就收手，漏了 `kq4_title.ovl`（中文標題疊圖）→ macOS 版連中文標題都不顯示（KQ4 踩過）。凡 `dist-cht/` 有的都要注入。**
11. **[HARD] CI 監控別用旗艦背景 poll**：派 **haiku/sonnet** 一次盯完整條（給 run id + `gh run watch <id> --exit-status`，**明確要求「不 block 到 exit 不准返回」**——便宜 agent 常誤判提早返回；或旗艦用 harness 追蹤的**背景 `gh run watch`** 指令自己盯，且**指令尾別接 `echo`/pipe** 否則 exit code 被蓋成 0、誤判成功——用 `WATCH_EXIT` 或 `gh run view --json conclusion` 確認）。見 rulebook `35`(liveness) + `45`(機械活分工)。
12. **[雷] push 後立刻 `gh workflow run --ref main` 會 dispatch 在 push 前的 commit**（GitHub 的 main ref 未即時更新）→ CI 用舊碼白跑一輪。修法：觸發前 `git ls-remote origin main` 確認 remote HEAD 已是新 commit，或觸發後 `gh run view <id> --json headSha` 核對 headSha 等於你要的 commit 再等。
13. **[雷] 全新空 repo 首推後 `gh workflow run`（workflow_dispatch）一直 404 `workflow not found on the default branch`**：GitHub 只在「**push 到預設分支**」時掃描註冊 workflow；若首推的分支當下不是預設分支（空 repo 預設常是 `main`，你推了 `master`），workflow 不會註冊，且**用 API 改預設分支不會觸發重掃**。修法：① 推一個符合 workflow `on: push: tags:` 樣式的 **tag**（如 `v*-macos`）直接觸發（tag push 事件會就地評估該 ref 的 workflow，繞過 dispatch 註冊）；或 ② 確保首推即推到預設分支、或改預設分支後再 push 一個 commit。本專案就是靠 `git push origin v1.0-macos` tag 才跑起來的。

---

## ⑦ 改圖 / 美術 — Designer subagent + 標題疊圖

- **美術一律啟動 Designer subagent 處理**（別自己硬幹像素）。
- **遊戲內中文標題**：不改原美術，用 **`.ovl` 索引點陣疊圖**（英文 logo 旁/上疊中文）。`build_title_overlay.py`：EGA 量化到 16 色 EGA 調色盤直寫；VGA 內嵌 ≤16 色調色盤 + 引擎 nearest-map。
  - **[HARD] SCI 疊圖陷阱**：低解析路徑 display 是 **320×200 非 640×400**，設計稿要先 `convert -resize 320x200` 再烘，否則 guard 判越界不疊。診斷：draw 函式開頭 `warning("disp=%dx%d")` 印一次看穿。
  - **[HARD] SCI 標題 pic 是「向量指令流」不是點陣，不能重繪**（用 `SCI_DUMP_PIC=<dir>` + `SCI_LOG_GFX=1` 找出標題 pic id；KQ4 是 pic 96）。SCI 又**無內建 `.ovl` 支援** → 要**自己在 `paint16.cpp drawPicture()` 末尾加 hook**：`pictureId==<標題> && getLanguage()==ZH_TWN` 時開 `kq4_title.ovl`（`u16LE w,h,x,y` + `w*h` 個 EGA index，`0xFF`=透明），逐點畫上去（**寫哪個 buffer 有雷，見下方 visual plane 那條**；座標用 320×200 script 座標）。回填 patch 0001。
  - **中文副標得體做法**：**不蓋經典英文 logo**，在其下方空白區疊中文副標（`build_title_overlay.py` 烘金字）；副標壓到 logo 忙亂色塊時，加**黑色圓角底板 plaque**（`rounded_rectangle` 填 index 0）當背景，金字才在任何底色上可讀。
  - **[HARD] 疊圖寫 visual plane 非 display buffer，且要對抗「標題星光動畫」逐幀重繪**（KQ4 血淚）：① 若寫 `putPixelOnDisplay`（display buffer），ZH_TWN 每次 re-upscale 會**抹掉**疊圖 → 改 `putPixel(GFX_SCREEN_MASK_VISUAL)` 寫 visual plane（會被 bitsShow 帶上螢幕、且 re-upscale 保留）。② 標題常有**星光/閃爍 view 動畫**逐幀畫在疊圖上蓋住中文：動畫多**走 `kAnimate`（`GfxAnimate::updateScreen`）非 `kDrawCel`（`drawCelAndShow`）** → 只在 `drawCelAndShow` re-assert overlay **攔不到**（會出現「中間幾個字被蓋、兩側字正常」的怪象）。修法：**兩處都 re-assert**——`drawCelAndShow` 的 `drawCel` 後、`GfxAnimate::updateScreen` 的 `bitsShow` 迴圈前，各 `if (_chtTitleActive) drawChtTitleOverlay();`（把 `drawChtTitleOverlay()`/`_chtTitleActive` 移到 `GfxPaint16` 的 public 供 `GfxAnimate` 呼叫）。診斷：先 headless 截標題連續幀，若「同幾個字每幀都被蓋」＝動畫路徑沒攔到，往 `kAnimate` 找。回填 patch 0001（含 `engines/sci/graphics/animate.cpp`）。
- **[HARD] 分清 SCI baked-art 兩種載體 → 兩種改法**（上面標題講 pic，選單/UI 常是 view，別搞混）：
  - **pic（背景圖，向量指令流）**：**不可重繪** → 走上面 `drawPicture` hook blit `.ovl` 點陣（標題常見，KQ4 pic 96）。
  - **view（cel 點陣圖，選單/職業名/按鈕等 UI）**：**可 decode/encode 直接重繪** → **`sci0_view.py`（SCI0 EGA，非 `sci_view.py`＝SCI1.1 VGA，用錯 cel 讀成 0 bytes）** decode 各 cel 成 PNG → 中文重繪 → encode 回 `view.NNN` patch（**SCI0 檔名是 `view.NNN` 非 SCI1 的 `NNN.v56`**，放 game dir）。QFG2 主選單（序章/建立英雄…）＝view.765、職業選擇（戰士/法師/盜賊）＝view.800。
    - **[HARD] rebuild 只重編被 replace 的 cel**：`sci0_view.py rebuild_view` 原本每 cel 都重編 append + 保留原 buffer → 多 cel replace 撐爆 **16-bit offset 上限(65535)**（原 9502→roundtrip 就膨脹 18464，encode RLE 不如原始緊湊）。修法：未替換 cel 保留原 offset 表 entry 不動，只 append 被 replace 的（→僅 13435）。
    - **[HARD] 中文 cel 硬邊二值化**：PIL 畫字有抗鋸齒（灰邊），nearest EGA 量化把灰邊映成抖動雜色 → RLE 爆炸（單 cel ~7600 bytes）。改「只用 bg+fg 純色 threshold 二值化」；首字可另給強調色（對齊原花體紅首字母）。
    - **定位**：`SCI_LOG_GFX=1` 走到目標畫面看 `view=N`；decode 匯出 cel 拼 montage 認哪 loop/cel 是哪字。**9px 高的 cel 塞不下中文**（保留英文）。
- **拉畫布不縮字**（rulebook 81）：CJK 塞不下時拉 hi-res 畫布，別硬縮字。AGI forceHires 640×400。
- promo 影片：配樂用**原版遊戲音樂**（rulebook 93），ffmpeg 合成見 kb `game-promo-video-ffmpeg`（配樂比影片短用 `aloop` 循環，別 `-shortest`）。
  - **最小可套規格（下一款直接照抄骨架，不用翻 kb 也有起手式）**：
    1. **片型**：~40–60s，每畫面 3–4s，**左英文原版／右繁中對照式蒙太奇**（`convert +append en cht` 併排，上角貼「英文原版／繁體中文化」小標），中間穿插純中文亮點畫面。
    2. **素材清單（涵蓋才算完整，別只放標題）**：① 標題卡（`遊戲名 + 中文名 + EGA+VGA + So You Want…`）；② **baked-art**（主選單/職業選擇/角色創建/片頭字/credits 職稱）；③ **live 文字**（版權框 + **in-game NPC 對白**——SCI hi-res 的最亮點，務必收）；④ EGA+VGA 各給鏡頭（雙版都做的證明）；⑤ 片尾卡（`Fully Translated / <對白則數> / repo url / 致敬原作者`）。
    3. **[HARD] 素材來源**：畫面一律**引擎實機 headless 截圖**（真成品，非設計稿）；配樂用**原版遊戲音樂離線抽**（MT-32+SoundFont/fluidsynth，rulebook 93），**不自產配樂**。
    4. **工具**：ffmpeg + ImageMagick **全 docker**；Ken Burns/zoompan 幀數會爆 CPU，靜態 crossfade 較穩（kb 有實務）。成品 `out/video/`，素材 `out/video_src/`（含遊戲畫面→版權素材 gitignore）。
    5. **改版重拍判斷**：baked-art 佔多數的影片，**只有動到 live 文字路徑（如新增 hi-res）才需補拍**，且只補受影響的 live 鏡頭（版權框/對白）即可，別整支重做——先比對 montage 縮圖看哪些畫面真的變了。
  - **[先試] 開場/場景有樂 → 直接即時側錄 MT-32（音色正宗，勝 GM 離線；SQ3 定案）**：SQ3 開場有配樂，`SDL_AUDIODRIVER=disk SDL_DISKAUDIOFILE=/out/cap.raw` + `--music-driver=mt32 --extrapath=<mt32 rom 夾> --music-volume=255 --output-rate=44100`（ROM 兩顆改名 `MT32_CONTROL.ROM`/`MT32_PCM.ROM` 放 extrapath），**不設 `SDL_DISKAUDIODELAY=0`**（realtime，105s wall≈99s 音檔 17MB，非全速灌 GB）；log 見 `Falling back to MT32`＝ROM 載入 OK。轉檔 `ffmpeg -f s16le -ar 44100 -ac 2 -i cap.raw x.wav`；**整檔** `volumedetect` 確認 mean≈-19dB（非 -91dB 靜音）、max<0（無 clipping），裁 60-72s（`afade` 淡入）→ 刪 GB raw。**[雷] per-段 `volumedetect` 的 `grep` 在 `docker ... bash -c` subshell 常吞掉輸出→誤判靜音**：改對**整檔**或用 `... 2>&1 | tail` 看，別信空輸出。錄音在 capture image（有 scummvm runtime+SDL），轉檔在 video image（有 ffmpeg）。**這是 rulebook 93 最佳解**（真實 Munt MT-32 晶片輸出，非 GM sf2 逼近）——只有場景真無樂（下條）才退而離線抽 sound 資源。
  - **[HARD] SCI 配樂抽不到？先分辨「pipeline 壞」還是「該場景無樂」**（LSL2 踩過，開場全靜音）：
    1. **`SDL_DISKAUDIODELAY=0`（全速灌）→ 保證靜音**：SCI 音樂排序器依**遊戲時鐘**推進，全速下 audio callback 狂抽但排序器不動 → 灌 GB 大檔全 -91dB。**即時側錄**（不設 DELAY=0，`SDL_AUDIODRIVER=disk SDL_DISKAUDIOFILE=x.raw --music-driver=adlib --music-volume=255`）排序器才正常。轉檔 `ffmpeg -f s16le -ar 22050 -ac 2`（LSL1 是 22050；先 `volumedetect` 確認 sample rate 與有聲窗）。
    2. **即時仍靜音 → 用「已知有樂的遊戲」驗 pipeline**：拿 reference（如 **LSL1 VGA** SCI）同法錄，若出樂（-25dB）＝側錄沒問題 → **目標遊戲那場景本來就無樂**（LSL2 開場版權/街景真靜音，音樂在深場景）。**別對著靜音場景鬼打牆**。
    3. **場景無樂就離線抽 sound 資源**（不必玩到有樂場景）：`SCI_DUMP_RES` hook 加 `kResourceTypeSound` dump `sound.NNN`（= 2-byte patch header + 1-byte 數位旗標 + 16×2 channel headers + MIDI stream）→ **`tools/sci0_sound_to_midi.py`** 依 `midiparser_sci.cpp midiFilterChannels`（delta 0xF8=+240、running-status MIDI、0xFC=end、channel 15=SCI 控制通道跳過）轉 SMF（division=30 tempo=500000 ≈ 60 ticks/秒）→ `fluidsynth -ni -F x.wav FluidR3_GM.sf2 x.mid`（qfg1-video image 內含 sf2）。**挑主題曲**：轉全部、比 note-on 數/末 tick，最多音符+夠長者＝主題（LSL2 是 **sound.101** 1688 音符 66s；別選 sound.007 那種 5 音符 init jingle）。音色 GM 非 MT-32、但**作曲是原版**（rulebook 93 可接受）。

---

## ⑧ 該 Read 哪些 knowledge-base & rulebook（觸發式，別憑記憶）

| 觸發 | Read |
|---|---|
| 開工（AGI/SCI 中文化通則、引擎 hook、headless 擷取、標題疊圖、台式在地化） | kb `retro-cht/retro-avg-taiwanese-localization/SKILL.md`（**主方法論，必讀**） |
| SCI 純繪字 / baked-art 深水區 | kb `scummvm-sci-cht-localization` |
| 大規模批次翻譯編排 | kb `workflows/batch-subagent-localization.md` |
| 逆向找資料撞牆（tileset/字庫/表）/ 想用截圖·原版錄影反推 | `rulebook/64-re-screenshot-oracle.md` |
| 斷言「某機制·某欄位·某值從哪來」前 / 逆向寫筆記 | `rulebook/62-static-provenance-trace.md` |
| port/remake 宣稱「完成」前 / 想靠測試綠驗收 | `rulebook/65-verify-against-reference-not-internal-signals.md`（**驗收對 reference 實測，非內部訊號**） |
| 除錯 / 找 bug / 效能 regression | `rulebook/60-feedback-loop-priority.md`（先建可重跑 pass/fail loop） |
| 老遊戲完整性 > 投報（保全歷史） | `rulebook/83-retro-completeness-over-roi.md` |
| README 寫/大改（老遊戲繁中） | `rulebook/80-retro-cht-readme-polish.md` + 對外白話 `90` + 去 AI 味 `91` |
| CJK 畫面/字型/解析度（縮字 vs 拉畫布） | `rulebook/81-retro-cjk-hires-canvas.md` |
| 做推廣片 / 換配樂 | `rulebook/93-promo-video-original-assets.md` + kb `game-promo-video-ffmpeg` |
| ScummVM/AGOS talkie（有語音沒字幕·對齊兩版） | `rulebook/84-scummvm-talkie-cht-fusion.md` |

> 逆向/老遊戲中文化細分規則已收攏進 skill **`re-retro-cht-rulebook`**，命中該類任務可直接 invoke。

---

## ⑨ 驗證紀律（避免假完成）

- **對 reference 實機實測，不靠內部訊號**：測試綠 / headless 全綠 ≠ 玩得通。玩家正常路徑實機驗（rulebook 65、`retro-game-playtest` skill）。
- **truth in code, not stale markers**：斷言「X 已完成」前查 code（唯一真相），別信 dated 文件（rulebook 63）。
- **第一性原理 + 柵欄原則**：判既有設計多餘/錯誤前，先重建它當初為何存在。逆向「反編當 oracle 不照抄」。
- 每項在地化補完，親自 Read 產出的截圖確認（別假設）。
- **headless 重現 in-game 對白（SCI）**：選單/過場好截，但**真正的 NPC 對白要走完角色創建→開始→在世界裡走到並點 NPC**（timing 敏感、易失敗）。做法：`Xvfb` + `xdotool` 狂送 Esc/點擊跳過 intro → 選職業 → 配點/姓名/開始 → 進世界後點 NPC；沿路每步 `import -window root` 截圖，事後挑出有對白框的那張。**640×400 視窗在 Xvfb 是置中 letterbox**（上下黑邊），點 NPC 座標要照視窗實際位置抓。**判別「是我的迴歸還是上游本來就這樣」**：同存檔/同場景**跑一次英文版（不帶 `--language=tw`）對照**——QFG1 的狀態列破圖警告就是這樣證實為英文上游既有、非在地化造成（別急著修不是你弄壞的東西）。

---

*模板版本：v6（2026-07-13，v1 萃取自 LSL1《幻想空間》AGI+SCI 雙軌 + MT-32；v2 融入 QFG1《英雄傳奇 I》SCI0 EGA + SCI1.1 VGA 深水區實戰；v3 融入 QFG2《英雄傳奇 II》SCI0 EGA 純 EGA 實戰；v4 融入 KQ4《羅塞拉的冒險》SCI0 EGA 實戰；v5 融入 LSL2《幻想空間II》SCI0 EGA 實戰；v6 融入 SQ3《宇宙傳奇 III》SCI0 EGA 實戰）。*
*v6 新增：**④-S script 內嵌「多行硬 `\n` crawl」被逐行工具拆裂 → 整段漏譯且覆蓋率統計看不出**（開場/過場敘事/掃描讀數/致謝，`build_crawl_fixups.py` 從 script dump 定位、`\s+→單空格` 算正規化 key 與引擎 `sciChtNormKey` 一致、cache.cpp 包裝每個 font 故 crawl 特殊字型也走 Big5；playtest 才揪得出，印證 rulebook 63）；**⑦ 開場/場景有樂 → 直接即時側錄 MT-32**（`--music-driver=mt32 --extrapath=<rom>` + SDL disk-audio 不設 DELAY=0、realtime 錄真實 Munt 輸出，音色勝 GM 離線；per-段 volumedetect 的 grep 在 docker subshell 會吞輸出→看整檔）；**⑥ 純資料變更（translation.tsv/字型）別重編引擎、只重打包**（Linux/Win 沿用 binary 重跑 package_*.sh、macOS 重跑 CI 注入；發修正版新 tag + 刪含缺陷舊 release，對外先確認）。*
*v5 新增（④-S2 專段）：**中文選單列殘影根因 = 選單列 9px 太矮、中文 14px 溢出清不掉 → ports.cpp ZH_TWN 加高到 15px**（併 hi-res 直寫 display-only 清不掉 → 選單區走低解析）；**選單字串在 script.997**（kSetMenu 組合字串、backtick 分 accelerator、item 走 getChtTranslation 要補進 skeleton）；**版權保護（電話號碼式）用 kStrCmp hook 略過**（gate 在 `555-dddd` 答案格式 + ZH_TWN 預設略過 / SCI_CP_BYPASS env）；**SCI 中文字大小/密度三旋鈕**（`kBig5Width`=字距、`kHiW/kHiH`=字大小、bake `--size`=字框留白；`kHiW≤kBig5Width×2`；非 8 倍數字寬把 rowBytes 改 ceil；build_translation bake 參數要同步；LSL2 定案 advance10/glyph20px）；無標題畫面別硬找；F1 內建中文操作說明；右鍵 43/153 = SCI debug 座標非迴歸。⑥ 新增 **patch 版中文資料經 `--extrapath` 由 SearchMan 載入**（免玩家複製）、macOS CI 雷 13 **全新空 repo workflow_dispatch 404 → 推 `v*-macos` tag 觸發**。⑦ 新增 **SCI 配樂抽取：全速 disk-audio 靜音（排序器依遊戲時鐘）→ 即時側錄；仍靜音先用 LSL1 VGA 驗 pipeline；場景無樂就離線抽 sound 資源 → `sci0_sound_to_midi.py` → fluidsynth GM 渲染**。*
*v4 新增：**⑥ macOS full 版是「CI engine-only artifact → 本機注入 game/ROM/ovl/wrapper」不是 CI 產**（`package_macos_full.sh`：統一 game 夾 + bash wrapper 當 CFBundleExecutable + 移除失效 _CodeSignature + 附 `修復.command` 重簽，Linux 無法代簽須 Mac 上驗）、**macOS cht 注入清單漏 title `.ovl` → 中文標題不顯**（雷 10）；⑦ SCI 標題 pic 是向量不可重繪 + 無內建 .ovl → **自加 `paint16.cpp drawPicture` hook blit 到 640×400 display buffer**、中文副標黑底板；④-S kFormat **`%s` 參數本身也翻**（限模板已翻時）。*
*v2 內容：④-S 內容 key 空白正規化、kFormat 動態句 hook、GetLongest 日文 kinsoku 誤傷 Big5、SCI hi-res live 文字路徑、抽字/env/grep 小雷；⑨ headless SCI 對白重現 + 英文對照判迴歸；⑦ promo 影片最小可套規格骨架 + 改版重拍判斷。*
*v3 新增：**⑥ 明確「每平台雙軌交付 patch(→Release)+full(→本機)」+ 交付驗收表**（本代最易漏，每次被使用者追問才補 full 版）；④-S SCI0 EGA baked-art view 重繪（sci0_view.py rebuild 只重編 replaced cel 免撐爆 16-bit offset、中文 cel 硬邊二值化免 RLE 爆炸、view.NNN patch 檔名）、extract 剝前導 bytecode 補抽 script 內嵌對白、複用他專案 binary 前 `grep USE_MT32EMU` 查證、headless docker 別 `wait` Xvfb（用 pkill）、同劇情他版譯本複用命中率遠高於前作（qog-2→QFG2 EGA 44%）。詳見 qfg2 `docs/lessons-qfg2.md`。後續每代若有新雷，回填此模板對應區塊。*
