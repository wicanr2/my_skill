---
name: english-prompt-coach
description: 當用戶用英文輸入 prompt 時，在執行任務前額外提供 (1) 修正版 (2) 中文解析表，當作日常英文寫作練習。狀態 ON/OFF 切換，由 `start coaching` / `stop coaching` 控制。觸發時機：user 顯式 invoke skill、或 ON 狀態下偵測到 user 主要用英文 prompt。
---

# English Prompt Coaching

> 目的：把「下指令」與「學英文寫作」合併進同一個迴圈，proactively 提供修正建議讓 user 累積寫作技能。

## 開關狀態（重要）

本 skill 為「toggle」式 — 預設 **OFF**，需顯式 invoke 才啟動：

| 動作 | 語句 |
|---|---|
| 啟動 | `start coaching` / 「開始 coach」/「再幫我看英文」/「啟用英文教練」|
| 停用 | `stop coaching` / 「停掉 coaching」/「別 coach」/「停止英文教練」|
| 單次跳過 | `skip coaching` / `just answer` / 「這次別 coach」|

開關狀態跨 session 沿用 — 在 user-level memory（`~/.claude/projects/*/memory/feedback-english-prompt-coaching.md` 或本 skill 的 state-of-mind）持續到下次切換。

## 觸發條件（當狀態 ON 時）

**會觸發**：
- 主要為英文的 user message（> 50% 英文字句）
- 完整的英文句子，不只是技術名詞

**不會觸發**：
- 純技術名詞 / 程式碼貼上 / log
- 中英夾雜（中文敘述 + 英文識別符）
- 引用他人英文（明顯為 quote）
- 純命令 (`run docker compose up -d`)
- 已正確的英文 → 只標「✅ 句子已正確，無需修改」

## 回應格式（當觸發時）

執行任務**之前**，在回應開頭加：

### 1. 原句引用
> 「i want to add a rule; if i type the prompt in english...」

### 2. 修正版（recommended）
自然、慣用的英文改寫：
> "I'd like to add a rule: when I type a prompt in English..."

### 3. 更精煉版（optional）
若可進一步壓縮：
> "Add a rule for English prompts:..."

### 4. 修正點解析表（中文）

| # | 原 | 改 | 說明 |
|---|---|---|---|
| 1 | `i` | `I` | 第一人稱單數永遠大寫 |
| 2 | `want to` | `'d like to` | 客氣語氣，want 較直接 |
| 3 | `;` | `:` | 分號連接獨立子句；冒號引出說明 |
| 4 | `if i type` | `when I type` | when 表常規條件，if 表特例 |

### 5. 執行任務
正常回應 user 的請求。

## 修正方向（不只挑文法）

- **用字精準度**：the vs a/an / want vs would like / can vs should/please
- **慣用搭配 collocation**：brush up on / sharpen skills / take a look at
- **大小寫**：I 永遠大寫；語言名/國名/專有名詞大寫
- **標點**：; vs : / comma splice / Oxford comma
- **語氣**：祈使句 vs 客氣句 / 規則描述 vs 一次性請求 / formal vs casual
- **自然度**：native speaker 會這樣講嗎？

**中文解析要點出「為什麼這樣改」**，不只「該這樣改」，讓 user 能類推到未來。

## 表格規範

- 欄位固定 `# | 原 | 改 | 說明`，視覺結構穩定
- 短 prompt (< 10 字) 可用條列代替表格
- 一次性說明，不要重複過往修正

## 絕對不要持久化的內容

- 個別 prompt 的修正版內容（ephemeral）
- 個別錯字 / 文法 typo 對應表
- 單次修正範例（原句 → 改句 pair）
- coaching 過程中觸發的具體文法示例

**只在以下情況更新 memory**：

1. user 對「規則本身」提出修正（改變觸發條件、修改回應格式）→ 更新本 skill
2. user 顯式指出「我每次都搞錯 X」這類反覆出現的長期 weakness，且要求記錄 → 另開 memory file（如 `weakness-affect-vs-effect.md`）

## 示例

✅ **會觸發 coaching**：
- "i want to add a rule; if i type the prompt in english..."
- "pls help me debug this race condition in the connection pool"

❌ **不會觸發**：
- 「幫我看一下這個 race condition」（純中文）
- "run `docker compose up -d`"（純命令）
- 「參考 `parseConfig` 這個 function」（中文 + identifier）

## 啟用 / 停用 確認

每次切換狀態，**簡短回應確認**：

- ON：「✅ Coaching activated. 從下一個英文 prompt 開始會附修正版 + 中文解析。」
- OFF：「⏸ Coaching paused. 直接回應任務不附修正。需要時打 `start coaching` 再啟用。」
- 單次跳過：直接執行任務，不額外確認

## 跨 session 持久

本 skill 為**長期 toggle**，狀態不會因 session 結束 reset。每次新 session 開始時，預設沿用上次 ON/OFF 狀態（無記錄則 OFF）。

實作建議：把當前狀態存入 user-level memory file（如 `~/.claude/projects/*/memory/feedback-english-prompt-coaching.md` 的「當前狀態」行），每次 invoke 時讀取 + 視需要更新。

## 關聯

- `feedback-english-prompt-coaching.md`（memory 版，可逐專案啟用 / 持久化開關狀態）
