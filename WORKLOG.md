# 工作歷程

本檔只記錄 `my_skill` 的逐輪變更、驗證與勘誤。穩定用途、安裝入口及目錄結構留在
`README.md`；技能規則留在各技能與 `rules/`，不得從本檔反推目前有效契約。

## 2026-08-28：從 Rich2 收斂復古 remake 完整生命週期

- 新增 `knowledge-base/re-methodology/retro-remake-end-to-end-playbook.md`，把 Rich2 實作中
  驗證過的證據契約、工具鏈分流、規格閘門、垂直鏈、移動／事件狀態分層、同狀態對拍、
  多語系、音畫、統計完成、授權、跨平台封包、推廣片與停止線整理為跨遊戲方法。
- `reverse-engineer-retro-game-remake` 只新增按需路由，沒有把長篇方法塞入常駐入口。
- Rich2 的位址、常數、素材格式、299 份樣本及 PolyForm 選擇保留為案例，不升格成
  其他 remake 的固定要求。

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

## 2026-08-27：把原始工具鏈指紋納入 remake 前置流程

- `reverse-engineer-retro-game-remake` 在大量未知函式判讀前，先分開辨識 compiler、
  linker／executable、平台 runtime、middleware、driver、packer 與自製資產工具。
- 新 reference 固定精確版本、家族／範圍、runtime pattern、非破壞性索引與停止線的
  證據契約；版權年份、格式或相容簽章不再被誤升為精確工具版本。
- 新增 `knowledge-base/re-methodology/` 路由頁，讓其他復古遊戲專案能按需載入方法，
  而不攜帶 FD2 專屬位址、二進位或結論。
- Codex 部署副本與本庫來源均以官方 `quick_validate.py` 驗證通過。

## 2026-08-29：SunDog remake 通用經驗與授權規則入庫

- 新增 `knowledge-base/re-methodology/retro-remake-source-selection-and-byte-signatures.md`：
  多版本挑來源看程式碼形式、規則釘位元組簽章（JSON 工具重產＋md 語意）、找缺口三法、
  模擬器狀態只做驗證與快照解幀、原版素材 runtime 兩種讀法、remake-owned 到期、容器打包坑。
- `retro-remake-tactical-parity.md` 補快照解幀、種點法、執行時記錄三條。
- `reverse-engineer-retro-game-remake/SKILL.md` 在挑來源版本前引用新文件。
- 補上先前缺漏的 `rules/85-retro-remake-licensing.md`（去識別化：聯絡方式改佔位符）。

## 2026-09-01：固定 version-date 正式版號

- 新增 `rules/87-retro-remake-release-versioning.md`，把 retro remake 正式版號固定為
  `v.<主版>.<次版>.<修訂版>-YYYYMMDD`，並提供完整 regex 與同日提高修訂號的契約。
- 固定 Git tag、GitHub Release、程式版本、`dist-all/`、封包檔名、manifest、SHA-256
  與交接文件七處一致；無參數時不得退回裸日期。
- 已發布版本預設不可刪除；只有使用者明確授權撤回精確舊版號時，才能刪除後回讀確認，
  再從乾淨輸入驗證並發布新版本。
