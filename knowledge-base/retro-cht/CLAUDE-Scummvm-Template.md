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
 - @../qfg-1/（SCI VGA+EGA 範本）  @../larry_suit_leisure_suit/（AGI+SCI 雙軌 + MT-32 範本）
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
| 畫布 | `_chtEnabled` 時 `forceHires` → 640×400，中文 16×16 佔 1 格 | **display 是 320×200**（`getDisplayWidth`），不是 640；疊圖/座標用 320×200 |
| 文字來源 | LOGIC 訊息 + **OBJECT 道具名(XOR "Avis Durgan")** + **systemUI 硬寫字串** | text/message 資源 + **script 內嵌 Print 字串** |
| 繪字 | `drawBig5CharacterOnDisplay`（graphics.cpp） | `GfxFontChinese`（整檔 patch，patches/fontchinese_sci.*） |

> 動手前先 Read `~/.claude/knowledge-base/retro-cht/retro-avg-taiwanese-localization/SKILL.md`（AGI 引擎 + 標題疊圖 + 台式在地化 + headless；含增量一～五）。SCI 純繪字深水區另見 kb `scummvm-sci-cht-localization`。

---

## ④ 中文化技術要點（跨引擎共通 + 各軌雷）

- **內容為 key 的替換**：英文原文當 HashMap key → Big5 譯文。查無 key 就露原文。`getChtTranslation()`。
- **字型由建構保證覆蓋**：`build_cht.py` 從 translation 表的**譯文 value** 烘 Big5 字型；表裡出現的字，字型一定有。引擎硬寫的中文字串（systemUI）用到的字須確認也在表值內覆蓋。非 Big5 字用 `corrections.tsv` 補。
- **[HARD] 完整 = 別漏非主線文字**：主對白翻完 ≠ 完整。還有**選單/道具欄/系統 UI/狀態列**。
  - AGI：OBJECT 道具名（解密 `Avis Durgan` XOR）走 `displayText`→getChtTranslation，加表即翻；systemUI（道具欄標題/暫停/存讀檔/狀態列 Score-Sound）是**引擎硬寫**，要加 `if (_gfx->chtEnabled())` 分支（**判 chtEnabled 非 getLanguage()**，因 AGI 非 `--language`）。狀態列走 displayText 支援 Big5，保留 `%v3/%v7`。**init 順序**：`loadChtResources()` 要在 `new SystemUI` 之前（建構子建構時就抓 chtEnabled）。
  - SCI：`extract_strings.py` 只抽 message/text，**會漏 script 內嵌 Print 字串**；用 `SCI_DUMP_RES` dump `script.*` 另抽。選單按鈕 key **帶 padding 空格**（如 `" Beer "`），逐字保留。
  - **零成本驗渲染路徑**：同一選單「已譯顯中文、未譯顯英文」的混雜態＝證明該 UI 走 getChtTranslation，補表即可。
- **F8 中英切換**（雙引擎，玩家對照原文）：獨立旗標 `_chtLangOn`（**別重用 `_chtEnabled`**，它牽動 hires+Big5 gate）；F8 在事件入口攔截並消費；AGI 當前訊息框原地重繪（快取原文 + `drawMessageBox` 可重入），SCI 下一則生效。
- **斷行**：Big5 是 2 byte，wrap 要以「顯示欄」算（1 中文字=1 欄），別按 byte（會提早斷行）。
- **背景色**：Big5 填格用「原始意圖色」`_textAttrib.foreground/.background`，別用 `combined*`（含 invert 位會變灰底）。

---

## ⑤ 音樂 — [HARD] 所有 ScummVM 中文化都 enable MT-32

Roland MT-32 遠優於 AdLib，老 Sierra 本就內附 MT32.DRV。**configure 一律不帶 `--disable-mt32emu`**（Munt 編入，`grep USE_MT32EMU config.h` 應 `#define`）。改所有 configure 點：Linux 本機、macOS CI(arm64+x86_64)、mingw、docs。

- **MT-32 ROM 位置（本機）**：`~/cht/mt32`（含 1987 v1.07 control + MT32_PCM.ROM；用 v1.07 合老遊戲年代）。
- **[HARD] ROM 有版權**：`.gitignore` 加 `*.ROM`，**絕不入 GitHub / patch 包**。
- **完整包（dist-all，本機）可附 ROM**：`pkg_common.sh` `stage_mt32_rom()` 從 `MT32_ROM_SRC`(預設上面路徑) 取檔改名成 `MT32_CONTROL.ROM`+`MT32_PCM.ROM` 放進包內 `game/`；AppRun/.bat 加 `--music-driver=mt32 --extrapath=<游戲夾>`。**有 ROM 才設 mt32 預設**。
- **patch-only / GitHub / macOS CI 不附 ROM、不設 mt32 預設**：無 ROM 又設 mt32 會**彈一次阻擋框**「MT-32 emulator cannot be used…」再回退 AdLib。玩家自備 ROM 放遊戲夾後於音效選項選 Roland MT-32。
- **驗證**：跑起來 log 出現 `Falling back to MT32`（Munt 先找 CM32L 才回退＝MT32 ROM 載入成功）且無 `cannot be used` 即 OK。

---

## ⑥ 打包 — 完整包 vs patch 包

- **[HARD] 完整遊戲包不上 GitHub**；GitHub repo 只放 **patch-only**（引擎 patch + 中文資料，不含遊戲資源）。
- **完整包集中放 `dist-all/`**（gitignore）。平台：**Windows / macOS / AppImage**。
  - Windows：`scummvm-win/`（獨立 mingw source 樹）configure `--host=x86_64-w64-mingw32 ...`（**去 --disable-mt32emu**）+ make → `scummvm.exe`；`package_windows.sh` 附完整 DLL（SDL2.dll、libwinpthread-1.dll）+ 遊戲 + ROM + .bat。**[HARD] source 複製勿排除 `config.guess`/`config.sub`**（否則 endianness unknown）。
  - macOS：**GitHub Actions CI**（`.github/workflows/build-macos.yml`）；**自編 SDL2**（別用 brew sdl2-compat）；universal = 每弧各編 + `lipo`。CI 拿不到本機 ROM → 只開 mt32 能力不設預設。
  - AppImage：`package_appimage.sh`，`--appimage-extract-and-run` 免 FUSE。
- **引擎改動後 scummvm-win 要同步**：它是純目錄（無 .git）。從 `scummvm-src`（git checkout）`for f in $(git diff --name-only HEAD); do cp ...`（連 untracked fontchinese）即同步 patch 改動的檔。
  - **[雷] 啟用新子系統時補 vendor 靜態檔**：上法只補「patch 改動的檔」。啟用先前停用的子系統（如 `mt32emu`）時，其 vendor 靜態標頭可能在 scummvm-win **缺席**（當初停用時被剪）→ mingw 編譯報 `MT32EMU_VERSION_MAJOR/MINOR/PATCH` 未宣告。具體：`audio/softsynth/mt32/config.h`（Munt 版本標頭，內容跨平台相同、scummvm-src 有 git 追蹤）。修法：從 scummvm-src 補該檔。**更穩**：啟用新子系統後編譯前，`diff -rq scummvm-src/audio/softsynth/mt32 scummvm-win/audio/softsynth/mt32`（濾掉 `.o/.dwo/.d` build 產物）比對缺檔補回。
- patch 維護：改完引擎 `cd scummvm-src && git diff HEAD -- engines/agi > patches/0001-*.patch`（SCI 同理 0002）。scummvm-src 是 pinned commit 的 git checkout，`git diff HEAD` 即完整 patch。
- 相關規則：mingw/macOS 細節見 rulebook `82-cross-platform-port-verification` + `mac-app-cross-pack` skill；完整性優先見 `83-retro-completeness-over-roi`。

---

## ⑦ 改圖 / 美術 — Designer subagent + 標題疊圖

- **美術一律啟動 Designer subagent 處理**（別自己硬幹像素）。
- **遊戲內中文標題**：不改原美術，用 **`.ovl` 索引點陣疊圖**（英文 logo 旁/上疊中文）。`build_title_overlay.py`：EGA 量化到 16 色 EGA 調色盤直寫；VGA 內嵌 ≤16 色調色盤 + 引擎 nearest-map。
  - **[HARD] SCI 疊圖陷阱**：display 是 **320×200 非 640×400**，設計稿要先 `convert -resize 320x200` 再烘，否則 guard 判越界不疊。診斷：draw 函式開頭 `warning("disp=%dx%d")` 印一次看穿。
- **拉畫布不縮字**（rulebook 81）：CJK 塞不下時拉 hi-res 畫布，別硬縮字。AGI forceHires 640×400。
- promo 影片：配樂用**原版遊戲音樂**（rulebook 93），ffmpeg 合成見 kb `game-promo-video-ffmpeg`（配樂比影片短用 `aloop` 循環，別 `-shortest`）。

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

---

*模板版本：v1（2026-07-11，萃取自 LSL1《幻想空間》AGI+SCI 雙軌 + MT-32 實戰）。後續每代若有新雷，回填此模板對應區塊。*
