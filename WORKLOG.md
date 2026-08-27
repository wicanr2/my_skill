# 工作歷程

本檔只記錄 `my_skill` 的逐輪變更、驗證與勘誤。穩定用途、安裝入口及目錄結構留在
`README.md`；技能規則留在各技能與 `rules/`，不得從本檔反推目前有效契約。

## 2026-08-27：建立復古 remake 的規格閘門與 README 契約

- 以近期 `~/cht/mm2`、`~/cht/dragon` 與 `~/fd2` 的 README 章節與開頭作結構參考，
  抽出可跨專案重用的穩定骨架，不複製專案特有完成度或能力聲明。
- `reverse-engineer-retro-game-remake` 新增強制流程：RE 證據 → `DRAFT` 規格 → 證據審查
  → `READY` 規格 → 正式實作 → 同狀態驗證 → `CONFORMED`。
- 新增 README 與 WORKLOG 專案範本，並修正 `rules/80-retro-cht-readme-polish.md`：README
  不再強制雜誌式文案，也不得承載日期型工作流水帳。
- Codex 與 `my_skill` 的技能入口均通過官方 `quick_validate.py`。

## 2026-08-27：retro 區域與 remake 技能再稽核

- 將 `re-retro-cht-rulebook` 從固定技能數量與 `~/.claude` 路徑改成儲存庫內的按需路由；
  通用 remake 只保留 `reverse-engineer-retro-game-remake` 一個主流程。
- 將舊 `retro-game-remake` 降為 Ultima、FM Towns、多版本素材、Heineman opcode 與
  Genesis 圖形案例庫；修正其 Ghidra 優先、未鎖下載與 ROI 放棄斷言。
- 主 remake 技能補上平台規格停止線及 CJK 文字安全區驗證。
- 修正三份因未引用冒號而無法解析的 YAML frontmatter，並移除非必要 metadata。
- 移除無反向引用且仍保存 `~/.claude`、固定模型分工與舊打包斷言的
  `knowledge-base/retro-cht/CLAUDE-Scummvm-Template.md`；現行方法改由按需技能與規則提供。
