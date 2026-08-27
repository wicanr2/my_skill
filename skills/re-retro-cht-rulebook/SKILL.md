---
name: re-retro-cht-rulebook
description: 路由復古遊戲逆向、clean-room remake、中文化、原版素材解析、正常玩家路徑驗證與跨平台交付所需的 my_skill 規則及按需知識。當任務涉及老遊戲 RE、DOS／PC-98／主機 ROM、ScummVM、CJK 點陣字、README、打包、試玩或推廣片時使用；本技能只選入口，不取代主方法論。
---

# 復古遊戲按需路由

本技能只做路由。所有路徑都以 `my_skill/` 儲存庫根目錄為基準；不要改指向
`~/.claude`，也不要預讀整個 `knowledge-base/retro-cht/`。

## 先選主流程

- 逆向後建立 clean-room remake：讀
  [`reverse-engineer-retro-game-remake`](../../reverse-engineer-retro-game-remake/SKILL.md)。
  這是唯一通用主流程，強制執行「RE 證據 → `READY` 規格 → 實作 → 同狀態驗證」。
- `knowledge-base/retro-cht/retro-game-remake/` 是 Ultima、FM Towns、多版本素材等歷史案例
  與專項參考，不再是第二份通用主流程。
- 只做中文化、移植、打包或試玩時，直接選下列一份最接近的專項；需要多個子任務才各加
  一份，禁止因此載入整個 retro 知識庫。

## 通用規則

| 任務 | 讀取 |
|---|---|
| 靜態值／欄位／公式溯源 | [`rules/62-static-provenance-trace.md`](../../rules/62-static-provenance-trace.md) |
| 用截圖、錄影或另一版本反推未知資料 | [`rules/64-re-screenshot-oracle.md`](../../rules/64-re-screenshot-oracle.md) |
| 查目前是否真的已完成，避免舊 worklist 重開工作 | [`rules/63-truth-in-code-not-stale-markers.md`](../../rules/63-truth-in-code-not-stale-markers.md) |
| 對原版驗證完成宣稱 | [`rules/65-verify-against-reference-not-internal-signals.md`](../../rules/65-verify-against-reference-not-internal-signals.md) |
| README 建立或大改 | [`rules/80-retro-cht-readme-polish.md`](../../rules/80-retro-cht-readme-polish.md) |
| CJK 畫布、字型與文字安全區 | [`rules/81-retro-cjk-hires-canvas.md`](../../rules/81-retro-cjk-hires-canvas.md) |
| 跨平台移植與封包驗證 | [`rules/82-cross-platform-port-verification.md`](../../rules/82-cross-platform-port-verification.md) |
| 素材與功能完整性 | [`rules/83-retro-completeness-over-roi.md`](../../rules/83-retro-completeness-over-roi.md) |
| ScummVM／AGOS talkie 字幕融合 | [`rules/84-scummvm-talkie-cht-fusion.md`](../../rules/84-scummvm-talkie-cht-fusion.md) |
| 推廣片原版音樂／音效界線 | [`rules/93-promo-video-original-assets.md`](../../rules/93-promo-video-original-assets.md) |

`60` 建立動態 pass/fail 訊號；`62` 查資料來源；`63` 查實作現況；`64` 在直接追蹤
受阻時以已知輸出反推。它們互補，不可互相取代。

## 平台與逆向工具

| 觸發 | 按需入口 |
|---|---|
| 標準 DOS timer、DAC、PIT、DMA 或既有平台 API | [`retro-hardware-spec-first`](../../knowledge-base/retro-cht/retro-hardware-spec-first/SKILL.md) |
| DOS MZ、IDA headless | [`ida-headless-dos-re`](../../knowledge-base/retro-cht/ida-headless-dos-re/SKILL.md) |
| Ghidra 只作交叉驗證或專案明確指定 | [`ghidra-headless-dos-re`](../../knowledge-base/retro-cht/ghidra-headless-dos-re/SKILL.md) |
| Borland overlay、Turbo Pascal、DOS／PC-98 | [`reverse-engineer-borland-dos-pc98`](../../knowledge-base/retro-cht/reverse-engineer-borland-dos-pc98/SKILL.md) |
| PC Engine／HuC6280 | [`knowledge-base/retro/pce-huc6280-re-toolkit.md`](../../knowledge-base/retro/pce-huc6280-re-toolkit.md) |
| Mega Drive／Genesis ROM | [`megadrive-re-toolkit`](../../knowledge-base/retro-cht/megadrive-re-toolkit/SKILL.md) |
| 原版 DOSBox 設定 | [`knowledge-base/retro/dosbox-game-configs.md`](../../knowledge-base/retro/dosbox-game-configs.md) |

若已有 IDA Pro 專用 image，IDA 是主要資料庫；Ghidra、Capstone、objdump 只提供獨立
交叉驗證。平台公開規格已足夠時，不再把 BIOS、DOS TSR 或逐週期硬體時序當遊戲 RE。

## 中文化、試玩與交付

| 觸發 | 按需入口 |
|---|---|
| ScummVM SCI | [`scummvm-sci-cht-localization`](../../knowledge-base/retro-cht/scummvm-sci-cht-localization/SKILL.md) |
| AGI、AVG、台灣用語在地化 | [`retro-avg-taiwanese-localization`](../../knowledge-base/retro-cht/retro-avg-taiwanese-localization/SKILL.md) |
| 字模索引反查文字 | [`glyph-index-text-recovery`](../../knowledge-base/retro-cht/glyph-index-text-recovery/SKILL.md) |
| 倚天點陣字 | [`eten-bitmap-font`](../../knowledge-base/retro-cht/eten-bitmap-font/SKILL.md) |
| 正常玩家路徑與存讀檔 | [`retro-game-playtest`](../../knowledge-base/retro-cht/retro-game-playtest/SKILL.md) |
| 鍵盤介面改觸控 | [`retro-keyboard-to-touch`](../../knowledge-base/retro-cht/retro-keyboard-to-touch/SKILL.md) |
| 三平台封包 | [`retro-game-cht-package`](../retro-game-cht-package/SKILL.md) |
| macOS App／DMG | [`mac-app-cross-pack`](../../knowledge-base/retro-cht/mac-app-cross-pack/SKILL.md) |
| 推廣片 | [`game-promo-video-ffmpeg`](../../knowledge-base/retro-cht/game-promo-video-ffmpeg/SKILL.md) |

特定遊戲命中時，只載入 `knowledge-base/retro-cht/<對應遊戲>/SKILL.md`。資料夾名稱與遊戲
名稱無法唯一對應時，先搜尋檔名與 frontmatter；不要維護容易過期的固定數量清單。
