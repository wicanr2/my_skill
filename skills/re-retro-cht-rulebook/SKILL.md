---
name: re-retro-cht-rulebook
description: 逆向工程 + 老遊戲中文化/移植/remake/素材抽取/逆向整合 的按需路由(收攏 rulebook 62/64/65/80/81/82/83/84/93 + 60/62/63/64 互補;並收攏已降級為 knowledge-base 的遊戲 skill)。觸發:逆向工程·分析原始碼寫筆記·「這值從哪來·某欄位·某機制」斷言前·RE 撞牆(封死·要動態·DOSBox·截圖/原版錄影/他版反推位置);老遊戲中文化·移植·remake·素材抽取;retro README 大改;CJK 中文化畫面/字型/解析度(縮字 vs 拉畫布);ScummVM/AGOS/DGDS/SCUMM talkie 繁中化·有語音沒字幕·對齊兩版·.RED 壓縮;跨平台 port 對齊原版。**特定遊戲/工具/任務**(命中即先 Read 本 skill 再按下方表路由 kb):Golden Box·Gold Box·黃金盒·金盒·PC-98·PC98·PC-9801·克萊恩英豪·幽靈騎士·Champions of Krynn·Death Knights of Krynn·Pool of Radiance·Curse of the Azure Bonds·Secret of the Silver Blades·Pools of Darkness;火龍之戰·Dragon Wars·opendw;Zak McKracken·scummtr·FM-Towns 中文;火龍之吼·孟波·中國之心·威利奇遇記·DGDS;Panzer General·裝甲元帥·PG-cht·wine 256色;Classic Mac·QuickDraw·Carbon·CGrafPtr·CopyBits→SDL2·LairWare;QB64·.bas·QuickBasic→Linux/Windows;u2/u3/u6-cht·反編當 oracle 重寫;game tester·實機驗證·「進去就壞/不存檔/能不能玩」;鍵盤老遊戲→Android/觸控·openkb·King's Bounty;做遊戲推廣片·trailer·zoompan·MIDI+SoundFont 抽配樂;ESC/F10 離開鍵·quit dialog·自動存檔;ASCII 動畫·Matrix·螢幕保護·PNG→ASCII turnaround;Mac DMG·universal binary·sdl12-compat·dylibbundler·Gatekeeper;COCOMO·KLOC·PM 人月·開發成本/工時估算·AI vs 傳統人力。
---

# 逆向工程 + 老遊戲中文化 路由集(rulebook + 已降級遊戲 skill)

> **這是「按需規則 + 按需遊戲 skill」的路由集合**,不是完整方法論本身。
> - rulebook 細節在 `rules/*.md`(不自動載入)。
> - 遊戲 skill 已於 2026-07-06 降級為 `knowledge-base/retro-cht/*/SKILL.md`(不自動載入,省常駐 token)。
> 用法:命中任一觸發點時,**先 `Read` 對應檔再動手**(同 `knowledge-base/` 的觸發式載入)。
> 多個觸發同時成立就都 Read(如做 Zak 中文化撞牆對齊原版 → zak kb + 62 + 65;做遊戲推廣片 → promo kb + 93)。

## A. rulebook 路由(craft 硬紀律)→ Read

| 觸發情境 | Read |
|---|---|
| 逆向工程 / 分析原始碼寫筆記 / 斷言「某機制做X·某欄位·某規則適用」前 / 「這值從哪來」/ 撞牆想說「封死·要動態·DOSBox·看不出來」 | `rules/62-static-provenance-trace.md` |
| 逆向找某筆資料(tileset/圖/表/字庫/音色)撞牆 / 動態 dump 卡(對話框·注入·要進特定狀態) / 已破解碼器但追資料流(JSL·跳表)成本爆高 / 想用實機截圖·原版錄影·另一版本當對照反推位置 | `rules/64-re-screenshot-oracle.md` |
| **任何老遊戲中文化/移植/remake/素材抽取/逆向整合**(完整性 > 投報,保全歷史,`[HARD]`)| `rules/83-retro-completeness-over-roi.md` |
| 老遊戲(1990s)繁中化專案 README 寫/重寫/大改 | `rules/80-retro-cht-readme-polish.md` |
| 老遊戲 CJK 中文化的畫面/字型/解析度(縮字 vs 拉畫布)| `rules/81-retro-cjk-hires-canvas.md` |
| **ScummVM/AGOS talkie 老遊戲繁中化**(Simon/Feeble/Waxworks);「有語音卻沒字幕·嘴動無字」;對齊兩版資料;安裝檔自訂壓縮(.RED)| `rules/84-scummvm-talkie-cht-fusion.md`(CD 缺字幕→floppy 融合·id 為 key·引擎反組譯對齊·DOSBox 熱抽換解壓)|
| 跨平台移植的驗證 / port 對齊原版 | `rules/82-cross-platform-port-verification.md` |
| **有 reference 的長專案(port/remake/遷移/重寫/對齊規格)宣稱「完成」前** / agent 多輪產出卻「玩不通·對不上原版」 / 想靠測試綠當驗收 / debug 捷徑串起來的「能跑完」 / 深挖 RE 前判方向 | `rules/65-verify-against-reference-not-internal-signals.md`(驗收=對 reference 實測非內部訊號;測試綠會謊報完成)|
| **做/改/重出推廣影片·trailer·遊戲宣傳片**;選/換配樂或音效;比對音色·聲紋·音訊品質(`[HARD]`:配樂用原版,不自產)| `rules/93-promo-video-original-assets.md`(素材來源鐵則)+ Read 下方 B 表 `game-promo-video-ffmpeg`(ffmpeg/docker 合成實務)|

## B. 已降級遊戲 skill 路由(kb,按需 Read)→ Read

> 這些原本是常駐 skill，現已降級為 kb 以省常駐 token。命中觸發 → `Read` 對應 `SKILL.md`（內容不會在每次工作階段自動載入）。路徑前綴：`knowledge-base/retro-cht/`。

| 觸發情境 | Read(retro-cht/…/SKILL.md) |
|---|---|
| **PC-98 日文 Golden Box／Gold Box 介面研究** / 黃金盒·金盒 / 640×400 / 16×15·16×16 點陣字 / 日文或繁中 CRPG 排版 / 隊伍狀態欄·對話分頁·戰鬥 HUD / 克萊恩英豪·幽靈騎士·Champions of Krynn·Death Knights of Krynn·Pool of Radiance·Curse of the Azure Bonds·Secret of the Silver Blades·Pools of Darkness | `research-pc98-golden-box-ui/SKILL.md` |
| 《火龍之戰》Dragon Wars 1989 繁中化 / opendw / opendw_remake / C++20·SDL2 重寫 / DATA1·DATA2 資產萃取 / Read Paragraph 防拷 / 逐指令差異測試 | `dragon-wars-cht-remake/SKILL.md` |
| Zak McKracken(FM-Towns Steam)繁中化 / scummtr 不認 CJK / Unknown function id 0xAB·0xCF / Truncated escaping / chinese_gb16x12.fnt / SCUMM 中文化 / FM-Towns 中文 | `zak-fmtowns-zhtw/SKILL.md` |
| Rise of the Dragon·火龍之吼·孟波 / Heart of China·中國之心 / Willy Beamish·威利奇遇記 / ScummVM DGDS·TTM 字串·STORE AREA / 電腦·視訊電話英文 / drawTitleSubtitle / Android APK 注入·liboboe.so·eglCreateWindowSurface | `rise-of-the-dragon-cht/SKILL.md` |
| **ScummVM SCI 引擎中文化**(Sierra 老遊戲)/ 英雄傳奇·Quest for Glory·Hero's Quest·人生劇場 Jones in the Fast Lane / SCI0(EGA)·SCI1·SCI1.1(VGA)/ 內容比對替換·GfxFontChinese·Big5·ZH_TWN / SCI_DUMP_RES 抽字 / baked-art view·pic 中文化·.v56·.p56·sci_view.py / 向量 pic vs bitmap pic 難度 / **640×400 hi-res CJK 直繪·kFormat 動態組字翻譯·clipRectTranslated 疊繪·分色重繪** | `scummvm-sci-cht-localization/SKILL.md` |
| Panzer General·裝甲元帥·PG-cht.exe(wine 老遊戲)/ 256 色才能執行 / exNilPtr / 缺 WING32.dll / 記憶體不足 | `panzer-general-wine/SKILL.md` |
| Classic Mac(Carbon/QuickDraw/CoreFoundation)C 遊戲 → SDL2 / `CGrafPtr`·`CopyBits`·`NewGWorld`·`CFStringRef`·Pascal string `\p..`·`GetResource`·`FSSpec` / LairWare / SDL2 取代 QuickDraw | `classic-mac-c-game-sdl-port/SKILL.md` |
| QB64-PE / .bas·.qb·QuickBasic 遊戲 → Linux ELF·AppImage / Wine 跨編 Windows exe / 中文點陣字·自動存檔·cheat modular patch | `qb64pe-game-linux-port/SKILL.md` |
| 1980s–90s 老遊戲(尤其 CRPG)逆向 + 乾淨重寫 C/SDL2 + 繁中化(反編當 oracle 不照抄)/ 反組譯執行檔 / 破解資料格式 / 抽 FM-Towns·DOS 美術音樂 / u2-cht·u3-cht·u6-cht·opendw(**母方法論**)| `retro-game-remake/SKILL.md` |
| 老遊戲 remake/移植「正常玩家路徑」實機驗證(game tester)/ headless 全綠但玩家一開就壞 / 「進去就壞·卡住·沒畫面·不存檔·能不能玩」/ 存檔寫不進唯讀目錄 / 剛打包完要驗收 | `retro-game-playtest/SKILL.md` |
| 鍵盤操作老遊戲/SDL C 引擎 → Android·觸控 / on-screen 控制·context-aware 覆蓋層 / 手指事件合成 SDLK_* / openkb·King's Bounty·CRPG 手機版 | `retro-keyboard-to-touch/SKILL.md` |
| 做/改遊戲推廣片·trailer·宣傳片(ffmpeg+ImageMagick·全 docker)/ zoompan 幀數爆炸·CPU 跑太兇 / MIDI+SoundFont 離線抽遊戲配樂(fluidsynth)/ Ken Burns / 靜態 fallback(配 rules/93 素材鐵則)| `game-promo-video-ffmpeg/SKILL.md` |
| 互動 app(GUI/TUI/遊戲)離開語意:ESC 只 cancel/back·F10/Ctrl+Q 才 quit·離開前 Yes/No + 自動存檔 / 做 input handler·選單導航·quit 鍵·存檔系統 / 「按錯鍵丟進度」·quit dialog·modal | `esc-cancel-f10-quit-autosave/SKILL.md` |
| 全螢幕終端 ASCII art 動畫(Matrix Katakana 雨 + 3D billboard turnaround + sprite 縱隊)/ 終端螢幕保護 / PNG·icon → ASCII turnaround / 改 `~/ascii-art/`(尤其 dna_matrix.py 衍生)| `ascii-matrix-scene/SKILL.md` |
| 1990s SDL 1.2·C++ 老遊戲 → macOS Universal(arm64+x86_64)`.app`·`.dmg` / GitHub Actions macos runner / dylibbundler / sdl12-compat / WSL 產 HFS+ dmg / Gatekeeper quarantine / `std::unary_function`(Xcode 15 C++20)/ 補 Mac 版 | `mac-app-cross-pack/SKILL.md` |
| **反組譯 DOS 老遊戲執行檔**(MZ 16-bit real mode)/ Ghidra headless / analyzeHeadless 跑不起來 / `segment:offset` 對不回檔案位移 / Ghidra 12.x post-script 失敗·API 方法消失 / 字串錨定找遊戲主邏輯 | `ghidra-headless-dos-re/SKILL.md` |
| **老遊戲中文化的字形來源**(預設倚天點陣字,非 TTF rasterize)/ 用倚天字形·ETEN 字型 / `stdfont.15`·`spcfont.15`·`STD.24M` 格式怎麼解 / 全形標點掉 fallback·標點字型不一致 / Big5 點陣字抽字烘 `.fnt` / 16×15 vs 24×24 選哪個 | `eten-bitmap-font/SKILL.md` |
| COCOMO Basic SLOC 反推傳統人力 / KLOC·PM 人月 / 開發成本·工時估算 / AI-agent vs 傳統人力差距 / 逆向漢化工時 / 給 PM 看的 baseline estimate / 「估一下這專案」| `cocomo-estimate/SKILL.md` |

## C. 60 / 62 / 63 / 64 互補(RE 與除錯的四種真相來源)

> 這四條互補,別把其中一條當萬用解:

- **`60`(`rules/60-feedback-loop-priority.md`)**:建動態 pass/fail loop(驗 bug)。
- **`62`(`rules/62-static-provenance-trace.md`)**:靜態反追溯源(查值「從哪來」別退回動態)。
- **`63`(`rules/63-truth-in-code-not-stale-markers.md`)**:驗狀態(誰做了沒:code 是唯一真相,別重查已完成、dated 文件會過期)。
- **`64`(`rules/64-re-screenshot-oracle.md`)**:RE 撞牆改用「已破解碼器 + 已知輸出(截圖)反推未知資料位置」(第三條路,別只在動態/靜態追資料流兩條死磕)。

> `60`/`63` 仍留在 常駐核心規則(除錯/狀態驗證通用,不限 RE);`62`/`64` 與本 skill 的其餘 retro 規則一起由此路由。
> 與第一性原理同源互補:RE 重寫「反編當 oracle 不照抄」= 逆向重建既有設計背後的必然性。
