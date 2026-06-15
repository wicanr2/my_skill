# my_skill

<p align="center">
  <img src="assets/signature_preview.png" alt="原來是個胖仔 / wicanr2 chibi pixel art signature" width="384">
</p>

<p align="center">
  <em>原來是個胖仔 (wicanr2) — chibi pixel art 簽名</em><br>
  <sub>原始 48×24 8bpp paletted PNG，源自 <a href="https://github.com/wicanr2/openxcom-cht">openxcom-cht</a> 專案主選單簽名整合，這裡 8× 放大顯示</sub>
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
| [`rise-of-the-dragon-cht`](skills/rise-of-the-dragon-cht/SKILL.md) | ScummVM **DGDS 引擎**老遊戲(Rise of the Dragon / Heart of China / Willy Beamish)繁中化 + 全平台 ship 完整 SOP:engine-side overlay 攔截繪字→查表→點陣 CJK 疊 hi-res;三繪字路徑、DDS 對白(動態版本述詞通吃 1.211/1.216/1.224)、TTM 持久層(STORE AREA 模型)、名牌剝除+矮牌置中 clamp、對話框溢出自動長高、時代雜誌攻略當術語 oracle、文化在地化、Windows/macOS/Android 全平台打包 | 「Rise of the Dragon」「孟波」「DGDS 中文化」「ScummVM dgds CJK」「對話名牌英文」「威利奇遇記」「Willy Beamish」「TTM 字串」「Android APK 注入」「全平台 ship」 |
| [`retro-game-remake`](skills/retro-game-remake/SKILL.md) | **階層式**老遊戲(CRPG)RE+乾淨重製方法論:反編當 oracle、破格式、FM Towns 美術/CDDA/EUP 音樂考古、CJK 重寫、headless 可破關+**連通分量可達性**驗證、Docker 跨平台+Mac CI 打包、引擎/資料分離。SKILL.md 精簡+踩雷,references/ 6 檔按需讀 | 「重製/反組譯/中文化老遊戲」「破解遊戲資料格式」「抽 FM Towns/DOS 美術音樂」「u2-cht/u3-cht/u6-cht/Ultima」 |
| [`agent-browser`](skills/agent-browser/SKILL.md) | 瀏覽器自動化 CLI(導航/填表/截圖/抓資料/測 web app) | 「開網站」「填表單」「截圖」「scrape 資料」「測 web app」 |
| [`dogfood`](skills/dogfood/SKILL.md) | 系統化探索測試 web app 找 bug/UX 問題,附完整重現證據 | 「dogfood」「QA」「exploratory test」「bug hunt」 |
| [`electron`](skills/electron/SKILL.md) | 自動化 Electron 桌面 app(VS Code/Slack/Discord 等) via CDP | 「自動化 Slack app」「控制 VS Code」「測 Electron app」 |
| [`slack`](skills/slack/SKILL.md) | Slack workspace 自動化(讀未讀/發訊/搜尋/抓資料) via 瀏覽器 | 「查我的 Slack」「發訊到」「搜尋 Slack」 |
| [`vercel-sandbox`](skills/vercel-sandbox/SKILL.md) | 在 Vercel Sandbox microVM 內跑 agent-browser + Chrome | 「Vercel Sandbox browser」「microVM Chrome」 |
| [`prompt-master`](skills/prompt-master/SKILL.md) | 為任何 AI 工具生成優化 prompt(LLM/Cursor/Midjourney/coding agent) | 「寫/改/優化 prompt」 |
| [`english-prompt-coach`](skills/english-prompt-coach/SKILL.md) | user 用英文下 prompt 時,任務前附 (1) 自然改寫版 (2) 中文修正解析表,當日常英文寫作練習;ON/OFF toggle 跨 session 沿用 | 「start coaching」「開始 coach」「再幫我看英文」「stop coaching」 |
| [`ascii-matrix-scene`](skills/ascii-matrix-scene/SKILL.md) | 全螢幕終端 ASCII art 動畫(Matrix 雨 + 3D turnaround + sprite 縱隊) | 「做 ASCII 動畫」「matrix 風格」「終端螢幕保護」 |
| [`organize-folder`](skills/organize-folder/SKILL.md) | 整理目錄為「客戶→類型」兩層結構 + 機密辨識(pem/key/token→機密區) | 「整理 XX 目錄」「重組資料夾」「歸位散落檔案」 |
| [`mac-app-cross-pack`](skills/mac-app-cross-pack/SKILL.md) | 不用 Mac 開發機 ship macOS universal `.app` + `.dmg`：GitHub Actions macos-14 build → Windows/WSL 注入本地版權資料 → mkisofs -hfs 產 hybrid HFS+ DMG → Gatekeeper xattr quarantine | 「Mac DMG build」「universal binary arm64+x86_64」「SDL 1.2 brew 沒了」「`std::unary_function`」「dylibbundler」「APFS DMG Windows 讀不到」「WSL2 hfsplus」「mkisofs -hfs」「補 Mac 版」 |
| [`my-skill-merge`](skills/my-skill-merge/SKILL.md) | 把本機 `~/.claude/` 的 rules/skills/agents/personas 同步進本公開 repo,**內建客戶機密 denylist + 去識別化**,push 前列 diff 等確認(review 不 copy-paste) | 「merge ~/.claude 進 my_skill」「同步 skill 到 GitHub」「更新 my_skill repo」「跑 my-skill-merge」 |

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
| [`50-ubiquitous-language`](rules/50-ubiquitous-language.md) | DDD ubiquitous language:每個 repo 維護 `CONTEXT.md` 術語表,人與 agent 共用同一套詞,降低 verbosity 與返工 |
| [`60-feedback-loop-priority`](rules/60-feedback-loop-priority.md) | 棘手 bug/效能 regression 最高優先:先建快速、決定性、可執行的 pass/fail 訊號(failing test > curl > CLI > headless > replay) |
| [`70-deep-modules`](rules/70-deep-modules.md) | Ousterhout deep modules:模組好壞 = 隱藏複雜度 / 介面複雜度;按 feature 垂直切、adapter 只在邊界、拒絕 pass-through 與提早抽象 |
| [`80-retro-cht-readme-polish`](rules/80-retro-cht-readme-polish.md) | 老遊戲（1990s 經典）繁中化專案 README 三層 voice register（Hero 信 / Magazine 編輯人聲 / Technical 工程文件）+ 1990s 雜誌風 SOP + 譯名考古感 + TOC sync checklist。萃取自 openxcom-cht v2.27 review。 |

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
│   ├── 50-ubiquitous-language.md
│   ├── 60-feedback-loop-priority.md
│   ├── 70-deep-modules.md
│   └── 80-retro-cht-readme-polish.md
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
    ├── agent-browser/  dogfood/  electron/  slack/  vercel-sandbox/
    ├── prompt-master/  english-prompt-coach/  ascii-matrix-scene/  organize-folder/
    └── mac-app-cross-pack/  my-skill-merge/
```

新增 skill:在 `skills/` 下開一個 kebab-case 資料夾,放一份有 frontmatter 的 `SKILL.md`,
更新上方表格即可。

## 前置需求

- [`gh`](https://cli.github.com/) GitHub CLI,且 `gh auth status` 已登入。
- Windows / PowerShell 環境(skill 內指令以 PowerShell 撰寫;中文使用者目錄下 Bash 可能失敗)。
