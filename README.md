# my_skill

<p align="center">
  <img src="assets/family-all.png" alt="wicanr2 一家四口 像素/十字繡風格家庭合照" width="440">
</p>

<p align="center">
  <img src="assets/me-bro.png" alt="我跟哥哥" width="220">
  <img src="assets/me-bro-sis.png" alt="我跟哥哥妹妹" width="220">
  <img src="assets/bro-sis.png" alt="哥哥妹妹" width="220">
</p>

<p align="center">
  <em>wicanr2 一家 — 像素 / 十字繡風格家庭合照</em>
</p>

---

個人 Claude Code skill 收藏庫。每個 skill 一個資料夾,內含 `SKILL.md`(YAML frontmatter 定義 `name` / `description` + 工作流說明)。

## Skills

| Skill | 用途 | 觸發時機 |
|-------|------|----------|
| [`kneron-edge-ai-integration`](skills/kneron-edge-ai-integration/SKILL.md) | **階層式** 把 YOLO/物件偵測整合部署到耐能 Kneron NPU (KL730/720) 的 SOP + 必踩雷:量化崩潰根因 (raw-logit 須用 mmse 非 percentage=1.0)、kneron-mmdetection docker 6 坑、ONNX→NEF、decode+NMS、逐 channel 驗收、記憶體/CPU 上限。SKILL.md 精簡+三大致命雷,references/ 4 檔按需讀 | 「YOLO 跑在耐能/Kneron NPU」「KL730/KL720 部署」「ONNX 轉 NEF」「NPU 量化後輸出全 0/崩潰」「kneron-mmdetection 環境」「edge AI 晶片整合物件偵測」 |
| [`github-weekly-radar`](skills/github-weekly-radar/SKILL.md) | 每週彙整 GitHub 近期重要**新**專案 + senior-PM 重要性評估 | 「這週 github 重要新專案」「新 repo 週報」「trending 摘要」 |
| [`cocomo-estimate`](skills/cocomo-estimate/SKILL.md) | 用 COCOMO Basic SLOC 模型 + 2026 AI 校正法產出「三數字並陳」開發成本章節 | 「估個 baseline」「人力評估」「跟 1990s 比快多少倍」「給 PM 看的 estimate」 |
| [`classic-mac-c-game-sdl-port`](skills/classic-mac-c-game-sdl-port/SKILL.md) | Classic Mac (QuickDraw/Carbon) C 遊戲 → SDL2 Linux/Windows 移植 + 中文化(含 CF prototype 截斷等六大雷) | 出現 `CGrafPtr`/`CopyBits`/`CFStringRef`/Pascal 字串、做 Mac remake 中文化 |
| [`qb64pe-game-linux-port`](skills/qb64pe-game-linux-port/SKILL.md) | QB64-PE + Docker 把 QuickBasic/.bas 遊戲 cross-compile 成 Linux/Windows + AppImage | 「把 .bas 遊戲跑在 Linux/Windows」「包 AppImage」 |
| [`dragon-wars-cht-remake`](skills/dragon-wars-cht-remake/SKILL.md) | 《火龍之戰》(Dragon Wars, 1989)繁中化 + C++20/SDL2 重寫:用 opendw 當 oracle 做逐指令差異測試、DATA1/DATA2 資產萃取(5-bit 文字/Huffman/場景圖去交錯)、CJK 渲染、Read Paragraph 防拷 | 「火龍之戰」「Dragon Wars」「opendw」「opendw_remake」「火龍之戰中文化」 |
| [`panzer-general-wine`](skills/panzer-general-wine/SKILL.md) | 在 wine 跑《裝甲元帥》(Panzer General, Borland Pascal Win95) 完整解法:256 色 bypass(自製 `pgs.dll` PE forwarder)+ 兩個 nil-deref PE patch + 中文字型 substitute + Windows 端 `WING32.dll` 打包 | 「PG」「Panzer General」「裝甲元帥」「256 色才能執行」「exNilPtr」「缺 WING32.dll」 |
| [`zak-fmtowns-zhtw`](skills/zak-fmtowns-zhtw/SKILL.md) | 《Zak McKracken》(FM-Towns) 繁中化完整 SOP:`scummtr -r` raw + CRLF 突破 CJK、ScummVM 8 處 patch 走 ZH_CHN 12×12 GBK 字型路徑、WQY 點陣字、GBK 0x5C escape transformer | 「Zak McKracken」「scummtr 不認 CJK」「Unknown function id 0xAB」「FM-Towns 中文」「chinese_gb16x12.fnt」 |
| [`rise-of-the-dragon-cht`](skills/rise-of-the-dragon-cht/SKILL.md) | ScummVM **DGDS 引擎**老遊戲(Rise of the Dragon / Heart of China / Willy Beamish)繁中化 + 全平台 ship 完整 SOP:engine-side overlay 攔截繪字→查表→點陣 CJK 疊 hi-res;三繪字路徑、DDS 對白(動態版本述詞通吃 1.211/1.216/1.224)、TTM 持久層(STORE AREA 模型)、名牌剝除+矮牌置中 clamp、對話框溢出自動長高、第二編碼字型(Big5+SJIS 共存)= 日文 F8 字幕模式(whisper 聽寫 Sega CD 日配)、時代雜誌攻略當術語 oracle、文化在地化、Windows/macOS/Android 全平台打包 | 「Rise of the Dragon」「孟波」「DGDS 中文化」「ScummVM dgds CJK」「對話名牌英文」「威利奇遇記」「Willy Beamish」「TTM 字串」「Android APK 注入」「日文字幕/F8」「全平台 ship」 |
| [`retro-game-cht-package`](skills/retro-game-cht-package/SKILL.md) | patched-ScummVM/SDL2 老遊戲漢化 → **三平台打包**:Linux 單檔 AppImage(slim 自備遊戲/full 內嵌開箱即玩)、Windows docker mingw cross(自編 SDL2 靜態、force LE 繞端序、objdump 遞迴收 DLL、zip)、macOS GitHub Actions(**autoconf 不能單次雙弧** → macos-14 + macos-15-intel 分弧 native 編 + lipo universal)。含 slim/full 版權切分、每包附繁中 使用說明.txt(SmartScreen/FUSE/quarantine 首跑雷)、`.app` 用 tar.gz | 「打包這個中文化」「Windows/AppImage/macOS 三平台」「docker mingw cross」「自編 SDL2」「Checking endianness unknown」「macos universal/Intel」「app 已損毀無法打開」「dist-all」 |
| [`retro-game-remake`](skills/retro-game-remake/SKILL.md) | **階層式**老遊戲(CRPG)RE+乾淨重製方法論:反編當 oracle、破格式、FM Towns 美術/CDDA/EUP 音樂考古、CJK 重寫、headless 可破關+**連通分量可達性**驗證、Docker 跨平台+Mac CI 打包、引擎/資料分離。SKILL.md 精簡+踩雷,references/ 6 檔按需讀 | 「重製/反組譯/中文化老遊戲」「破解遊戲資料格式」「抽 FM Towns/DOS 美術音樂」「u2-cht/u3-cht/u6-cht/Ultima」 |
| [`game-promo-video-ffmpeg`](skills/game-promo-video-ffmpeg/SKILL.md) | 用 ffmpeg + ImageMagick(全 docker、無剪輯軟體、LLM 驅動)把老遊戲/remake/中文化專案的截圖 + 遊戲音樂合成 60–75 秒推廣短片;內建硬雷:**zoompan 幀數爆炸(燒滿 CPU)**、CPU 控制(--cpus/預建 image/veryfast/靜態 fallback)、**MIDI+SoundFont 遊戲音樂離線抽取(fluidsynth)**、滑鼠驅動遊戲改靜態截圖、docker 字型/IM policy 雷;附 CPU-safe make.sh 骨架。配 `rules/93`(配樂用原版[HARD]) | 「做推廣片/trailer/宣傳片」「截圖+配樂合成影片」「ffmpeg 投影片/Ken Burns」「遊戲介紹影片」「影片 CPU 跑太兇/卡住」「抽遊戲配樂當 BGM」 |
| [`agent-browser`](skills/agent-browser/SKILL.md) | 瀏覽器自動化 CLI(導航/填表/截圖/抓資料/測 web app) | 「開網站」「填表單」「截圖」「scrape 資料」「測 web app」 |
| [`dogfood`](skills/dogfood/SKILL.md) | 系統化探索測試 web app 找 bug/UX 問題,附完整重現證據 | 「dogfood」「QA」「exploratory test」「bug hunt」 |
| [`electron`](skills/electron/SKILL.md) | 自動化 Electron 桌面 app(VS Code/Slack/Discord 等) via CDP | 「自動化 Slack app」「控制 VS Code」「測 Electron app」 |
| [`slack`](skills/slack/SKILL.md) | Slack workspace 自動化(讀未讀/發訊/搜尋/抓資料) via 瀏覽器 | 「查我的 Slack」「發訊到」「搜尋 Slack」 |
| [`vercel-sandbox`](skills/vercel-sandbox/SKILL.md) | 在 Vercel Sandbox microVM 內跑 agent-browser + Chrome | 「Vercel Sandbox browser」「microVM Chrome」 |
| [`prompt-master`](skills/prompt-master/SKILL.md) | 為任何 AI 工具生成優化 prompt(LLM/Cursor/Midjourney/coding agent) | 「寫/改/優化 prompt」 |
| [`english-prompt-coach`](skills/english-prompt-coach/SKILL.md) | user 用英文下 prompt 時,任務前附 (1) 自然改寫版 (2) 中文修正解析表,當日常英文寫作練習;ON/OFF toggle 跨 session 沿用 | 「start coaching」「開始 coach」「再幫我看英文」「stop coaching」 |
| [`ascii-matrix-scene`](skills/ascii-matrix-scene/SKILL.md) | 全螢幕終端 ASCII art 動畫(Matrix 雨 + 3D turnaround + sprite 縱隊) | 「做 ASCII 動畫」「matrix 風格」「終端螢幕保護」 |
| [`organize-folder`](skills/organize-folder/SKILL.md) | 整理目錄為「客戶→類型」兩層結構 + 機密辨識(pem/key/token→機密區) | 「整理 XX 目錄」「重組資料夾」「歸位散落檔案」 |
| [`mac-app-cross-pack`](skills/mac-app-cross-pack/SKILL.md) | 不用 Mac 開發機 ship macOS universal `.app` + `.dmg`：GitHub Actions macos-14 build → Windows/WSL 注入本地版權資料 → mkisofs -hfs 產 hybrid HFS+ DMG → Gatekeeper xattr quarantine | 「Mac DMG build」「universal binary arm64+x86_64」「SDL 1.2 brew 沒了」「`std::unary_function`」「dylibbundler」「APFS DMG Windows 讀不到」「WSL2 hfsplus」「mkisofs -hfs」「補 Mac 版」「`unrecognized option: CXXFLAGS=-arch`」「Frameworks SDL2 單弧/非-fat」 |
| [`my-skill-merge`](skills/my-skill-merge/SKILL.md) | 把本機 `~/.claude/` 的 rules/skills/agents/personas 同步進本公開 repo,**內建客戶機密 denylist + 去識別化**,push 前列 diff 等確認(review 不 copy-paste) | 「merge ~/.claude 進 my_skill」「同步 skill 到 GitHub」「更新 my_skill repo」「跑 my-skill-merge」 |
| [`dev-setup-bundle`](skills/dev-setup-bundle/SKILL.md) | 把專案開發環境打包成可攜 dev-setup(source+完整 git+Dockerfile+腳本+素材),**重點是內含 Claude 對話記錄+記憶**,讓另一台電腦 `claude -r`/`--continue` 接續同一個對話繼續工作;附 `previous-work.md` 工作交接 + 跨機 session 路徑編碼眉角(同路徑/改名/`--resume <UUID>`);排除可重建的 `build/` 與 docker images | 「打包開發環境」「dev-setup」「搬到另一台機器繼續」「讓 claude -r 在別台接續」「開發環境包含素材重新打包」「session handoff bundle」 |
| [`retro-game-playtest`](skills/retro-game-playtest/SKILL.md) | 老遊戲 remake/移植「正常玩家路徑」實機驗證(game tester):專治「CI 全綠但玩家一開就壞」—預設視角錯/唯讀 cwd 不存檔/視窗縮放偏移/dump 時機遮真相,**跨平台分歧章**(Win/Mac 用 Wine/VM 重現、log 嚴重度因平台異、相對路徑雙重前綴、addr2line 跨平台定位) | 「game tester」「實機驗證」「能不能玩」「進去就壞/卡住/不存檔」「驗證 remake 可玩性」 |
| [`verification-fidelity`](skills/verification-fidelity/SKILL.md) | **階層式** 宣稱「修好/驗過」前的驗證忠實度自檢:在真的會壞的環境/碼頁/locale 重現(別用寬鬆替身)、別拿 stale binary 當證據、靜態檢查≠runtime、改 render 座標要**同步改 hit-test 並真的互動**、在地化會戳破引擎隱藏假設。`60-feedback-loop-priority` 的另一半。SKILL.md 精簡六問+心法,references/cases.md 四則真實踩雷按需讀 | 「驗過了嗎/真的修好了嗎」「為何 tester/玩家又找到 bug」「跨環境(OS/locale/碼頁)、在地化驗證」「UI 座標/縮放/命中判定改動」「重打出貨前最後一關」 |
| [`retro-keyboard-to-touch`](skills/retro-keyboard-to-touch/SKILL.md) | 鍵盤老遊戲/SDL C 引擎移植到 Android/觸控的方法論:不重寫輸入,讀引擎每畫面 keymap 動態渲染 context-aware 觸控控制,手指事件合成 SDLK_* 餵回原事件迴圈 | 「老遊戲移植到 Android」「鍵盤遊戲改觸控」「SDL2 android-project 移植」「觸控覆蓋層/UX 設計」 |
| [`first-principles-tech-notes`](skills/first-principles-tech-notes/SKILL.md) | 建立/擴展「第一性原理+圖文並茂」技術知識庫 GitHub repo:每主題一篇 markdown、概念配手繪 SVG、研究 sub-agent 查證、專家+學生審查、worklist 一項一項做 | 「整理某領域筆記成 repo」「把 X 主題寫成第一性原理教學」「一項一項做我監看」「ASCII 圖升級 SVG」 |
| [`proposal-writer`](skills/proposal-writer/SKILL.md) | 多 agent 分章節撰寫/精鍊長篇計畫書(送審/技術整合/展會提案):含文獻驗證、技術校正、術語中文化、執行摘要、md→docx 產出 | 「寫/改/審計畫書」「研究白皮書」「展會提案」「多 agent 分章節長文件」 |

### cocomo-estimate 一句話

不要只給「AI agent 做了 X 小時」 — 看起來像吹牛。本 skill 永遠列**三個數字**：
**COCOMO 教科書值**（傳統人力合理上界）/ **單人無 AI 校正後**（拔掉 1980s 團隊 overhead）/ **2026 實測**（wall-clock + 真實人小時）。
顯式揭露 COCOMO 兩個系統性偏差（低估 0-SLOC 高心智成本工作、高估 1980s 團隊 overhead），給讀者一個 ballpark 而非合約報價。
案例：[pg-cht](https://github.com/wicanr2/pg-cht)（32 PM 教科書 vs 0.5 PM 實測，60× 壓縮）、[openxcom-cht](https://github.com/wicanr2/openxcom-cht)（雙作漢化 3 sub-project 拆解）。

### github-weekly-radar 一句話

不要相信 web 榜單。trending / aggregator blog 會把**老牌爆紅**誤當「新建」、星數還常過時或灌水。
本 skill 用 `gh api search/repositories q="created:>DATE" sort:stars` 核實**真實建立日與當下星數**,
剔除非新建者,再用 senior-PM 視角分級(S/A/B/C)、標紅旗、給行動建議。為每週固定執行設計。

核心指令(PowerShell):
```powershell
$since = (Get-Date).AddDays(-30).ToString("yyyy-MM-dd")
$j = gh api -X GET "search/repositories" -f q="created:>$since stars:>2000" `
       -f sort=stars -f order=desc -f per_page=50 | ConvertFrom-Json
$j.items | ForEach-Object {
  "{0,7}  {1}  {2}  {3}" -f $_.stargazers_count,$_.created_at.Substring(0,10),$_.full_name,$_.description
}
```

## Rules(通用工作方法論)

放進 `~/.claude/rules/` 可讓 Claude Code 全域套用的通用方法論(與專案/客戶無關)。

| Rule | 主旨 |
|------|------|
| [`40-learning-loop`](rules/40-learning-loop.md) | 探索/除錯/重構的 learning loop:定義 goal/constraint/可驗證成功標準,先做最小測試,每輪更新假設,先驗證再下結論 |
| [`42-reference-fidelity`](rules/42-reference-fidelity.md) | 參考保真度:使用者指定「參考 X 專案」時,動手前先讀 X 的實際設定、逐項照抄其 proven values(runner 版本/依賴/旗標),偏離要有講得出口的理由;外部版本標籤(CI runner image 等)會退役不能憑記憶寫死;「CI job queued 很久+執行 0s」=runner 標籤退役非程式 bug。源自沒抄 willy 的 macos-14 寫成退役 macos-13 卡死 |
| [`45-model-cost-division-of-labor`](rules/45-model-cost-division-of-labor.md) | 模型成本分工:貴模型留給判斷/寫作,對碼核實/盤點/grep 比對等粗活用便宜模型(`/model` 切換或 sub-agent 指定 `model: haiku/sonnet`);不預設 fan-out review agent;筆記寫到「夠用」就停(長尾登 PLAN 被動維護);review 文件抽可驗證斷言回 code grep(配 `63`) |
| [`50-ubiquitous-language`](rules/50-ubiquitous-language.md) | DDD ubiquitous language:每個 repo 維護 `CONTEXT.md` 術語表,人與 agent 共用同一套詞,降低 verbosity 與返工 |
| [`60-feedback-loop-priority`](rules/60-feedback-loop-priority.md) | 棘手 bug/效能 regression 最高優先:先建快速、決定性、可執行的 pass/fail 訊號(failing test > curl > CLI > headless > replay) |
| [`62-static-provenance-trace`](rules/62-static-provenance-trace.md) | 靜態溯源紀律:問「這值/設定/字串從哪來」別反射性下「封死/要動態/看不出來」——錨定實例→找 sink→運算元反向追到靜態源(表/header 欄位/config);搜尋落空=換 query 非不存在;動態手段只留給真正 runtime-only。`60` 的互補(查來源 vs 驗修法) |
| [`63-truth-in-code-not-stale-markers`](rules/63-truth-in-code-not-stale-markers.md) | 多輪/長專案的狀態紀律:**code 是唯一真相**——動手查「未完成」項前先 grep code 確認(別把已完成工作當沒做又重查/鬼打牆),完成即標 done、dated 盤點文件會過期要回頭刪錯誤斷言、記憶只存教訓不存狀態、改有單測的系統用「可選參數+預設=現行」零回歸。`60`/`62` 的互補(驗狀態 vs 驗 bug/來源) |
| [`70-deep-modules`](rules/70-deep-modules.md) | Ousterhout deep modules:模組好壞 = 隱藏複雜度 / 介面複雜度;按 feature 垂直切、adapter 只在邊界、拒絕 pass-through 與提早抽象 |
| [`80-retro-cht-readme-polish`](rules/80-retro-cht-readme-polish.md) | 老遊戲（1990s 經典）繁中化專案 README 三層 voice register（Hero 信 / Magazine 編輯人聲 / Technical 工程文件）+ 1990s 雜誌風 SOP + 譯名考古感 + TOC sync checklist。萃取自 openxcom-cht v2.27 review。 |
| [`82-cross-platform-port-verification`](rules/82-cross-platform-port-verification.md) | 跨平台打包(Linux/Win/macOS/Android)驗證紀律:目標平台先自己重現(Win→Wine,別先要 backtrace)、驗實際打包產物、缺資料 NULL-safe 回退;6 類分歧雷(log 嚴重度因平台異/相對路徑雙重前綴/能跑的變體遮 bug/唯讀 cwd/編譯器嚴格度/CI 架構)+ Wine·verbose flag·addr2line 手法 |
| [`83-retro-completeness-over-roi`](rules/83-retro-completeness-over-roi.md) | 老遊戲素材抽取/移植[HARD]:完整性>投報(文物保存不能談 ROI),不預先砍版本/資產、卡關記錄方法續做別寫「低投報」;**別漏看資產檔**——同類檔先 `strings EXE\|grep ext` 列舉全(別假設單檔含全部:漏一個檔=子系統用錯來源還報「完成」) |
| [`84-scummvm-talkie-cht-fusion`](rules/84-scummvm-talkie-cht-fusion.md) | ScummVM/AGOS talkie 老遊戲繁中化(Simon/Feeble/Waxworks):[HARD] 先驗來源版本字幕完整度(talkie 版常缺字幕→用 floppy 完整文字+CD 語音融合)、注入以行 id 為 key(非英文比對,救語音-only 行)、重用引擎內建反組譯器對齊兩版、DOSBox-in-docker 目錄熱抽換跑原版安裝解自訂壓縮、CJK 24px 加大引擎文字緩衝、硬編碼 UI 加 ZH 分支 |
| [`86-proposal-writing`](rules/86-proposal-writing.md) | 研究/技術計畫書撰寫:定位先行(可否證主張+假說)、範圍誠實、標準結構、評估協議、文獻真實性(WebSearch 驗 arxiv/DOI 不憑記憶)、對照原始碼校正、中文不夾雜、執行摘要;多 agent 分章節 + md→docx pipeline |
| [`90-plain-language`](rules/90-plain-language.md) | 白話寫作七準則:結論先行(BLUF)、短句常用詞、術語即時翻譯、具體勝抽象、數據配「所以呢」、自然不貼標籤、不犧牲正確性。對外/客戶/管理層文件逐條套 |
| [`91-deslop-ai-writing`](rules/91-deslop-ai-writing.md) | 去 AI 味反面清單:AI 詞黑名單、copula 迴避、權威揭示腔、格言公式、粗體列表症、filler/hedging;draft→audit→final 去 slop 審查 loop + 防改過頭的 false-positive 清單。來源 Wikipedia「Signs of AI writing」 |
| [`93-promo-video-original-assets`](rules/93-promo-video-original-assets.md) | 推廣影片[HARD]鐵則:配樂/音效一律用**原版實際素材**(CD-DA/模擬器錄原版/官方 OST),不可用自寫合成器逼近頂替;比對音色用第一性原理(ffprobe/頻譜/provenance)不憑記憶。**IP 但書**:用原版音樂≠可任意散布——個人保存 OK、對外公開先 flag 著作權。配 skill `game-promo-video-ffmpeg` |

## Personas(agent 人格)

可當 agent system persona 的角色定義(與專案/客戶無關)。

| Persona | 風格 |
|---------|------|
| [`hermes-research-collaborator`](personas/hermes-research-collaborator.md) | 研究協作者:好奇、誠實面對不確定、區分推測與證據、重概念深度勝過淺層完整 |
| [`patient-technical-teacher`](personas/patient-technical-teacher.md) | 耐心技術老師:重理解非表現、清楚解釋、不預設先備知識、由直覺到細節 |

## 安裝 / 使用

讓 Claude Code 讀得到這些 skill,二選一:

1. **clone 到 skills 目錄**
   ```powershell
   git clone https://github.com/wicanr2/my_skill.git
   # 把 skills/* 複製或 symlink 到 ~/.claude/skills/
   ```
2. **直接在對話中引用**:把需要的 `SKILL.md` 內容貼給 Claude,或放進專案的 `.claude/skills/`。

## 報告產物

`github-weekly-radar` 每次執行都會在 [`reports/`](reports/) 產生一份 standalone HTML 週報
(單檔可雙擊開、每個 repo 附 GitHub 連結、Tier 色塊)。最新一份:
[`reports/github-radar-2026-05-30.html`](reports/github-radar-2026-05-30.html)。

## 結構

```
my_skill/
├── README.md
├── rules/                          # 通用工作方法論 (放 ~/.claude/rules/)
│   ├── 40-learning-loop.md
│   ├── 42-reference-fidelity.md
│   ├── 45-model-cost-division-of-labor.md
│   ├── 50-ubiquitous-language.md
│   ├── 60-feedback-loop-priority.md
│   ├── 63-truth-in-code-not-stale-markers.md
│   ├── 70-deep-modules.md
│   ├── 80-retro-cht-readme-polish.md
│   ├── 82-cross-platform-port-verification.md
│   ├── 83-retro-completeness-over-roi.md
│   ├── 84-scummvm-talkie-cht-fusion.md
│   ├── 86-proposal-writing.md
│   ├── 90-plain-language.md
│   └── 91-deslop-ai-writing.md
├── personas/                       # agent 人格 (system persona)
│   ├── hermes-research-collaborator.md
│   └── patient-technical-teacher.md
├── reports/
│   └── github-radar-<date>.html   # github-weekly-radar 產生的 HTML 週報
└── skills/                         # 每個 skill 一個資料夾,內含 SKILL.md
    ├── github-weekly-radar/  cocomo-estimate/
    ├── classic-mac-c-game-sdl-port/
    ├── qb64pe-game-linux-port/  dragon-wars-cht-remake/
    ├── panzer-general-wine/  zak-fmtowns-zhtw/  rise-of-the-dragon-cht/   # 老遊戲繁中化/wine
    ├── game-promo-video-ffmpeg/   # 遊戲推廣片 ffmpeg 合成(配 rules/93)
    ├── agent-browser/  dogfood/  electron/  slack/  vercel-sandbox/
    ├── prompt-master/  english-prompt-coach/  ascii-matrix-scene/  organize-folder/
    └── mac-app-cross-pack/  my-skill-merge/
```

新增 skill:在 `skills/` 下開一個 kebab-case 資料夾,放一份有 frontmatter 的 `SKILL.md`,
更新上方表格即可。

## 前置需求

- [`gh`](https://cli.github.com/) GitHub CLI,且 `gh auth status` 已登入。
- Windows / PowerShell 環境(skill 內指令以 PowerShell 撰寫;中文使用者目錄下 Bash 可能失敗)。
