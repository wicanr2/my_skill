---
name: dev-setup-bundle
description: 把一個專案的開發環境打包成可攜的 dev-setup 壓縮檔，讓「另一台電腦」解開後能 (1) 重建整套 build/打包環境，且 ★重點★ (2) 用 `claude -r` / `--continue` 接續同一個 Claude 對話與記憶繼續工作。觸發：使用者說「打包開發環境」「dev-setup」「把專案搬到另一台機器繼續」「讓 claude -r 在別台接續」「開發環境包含素材重新打包」「session handoff bundle」「previous-work.md」。
---

# dev-setup bundle — 可攜開發環境 ＋ `claude -r` 跨機接續

**核心需求（重點）**：dev-setup 不只是「搬程式碼」。它要讓**另一台電腦**解開後能**無縫接續**——
最關鍵的是「**在別台電腦下 `claude -r` / `--continue` 就能接續同一個 Claude 對話與記憶**」，
而不只是有一份檔案。少了這層，就只是備份、不是 handoff。

## 必含三層（缺一不可）

1. **可重建的環境** — source（含完整 `.git` 所有分支）+ 所有 Dockerfile + build/打包/除錯腳本 + 素材（原始資料、字型、工具）。
2. **工作狀態交接** — `SETUP.md`（怎麼重建環境）+ `previous-work.md`（做到哪、為什麼、還有什麼沒做、記憶摘要）。
3. **Claude session** ★ — `claude-session/`：把 `~/.claude/projects/<encoded-cwd>/` 整個帶過去（對話記錄 `*.jsonl` + `memory/`），讓 `claude -r` 能接續。

## 打包（排除可重建的肥肉，省下數 GB）

```bash
# claude session 目錄編碼：cwd /home/me/proj → ~/.claude/projects/-home-me-proj
#   （絕對路徑、`/`→`-`、開頭加 `-`）
cp -a ~/.claude/projects/<encoded-cwd> ./claude-session/projects/

tar --zstd -cf dev-setup-YYYYMMDD.tar.zst \
  --exclude='*/build' --exclude='*/run-conf' --exclude='__pycache__' --exclude='*.AppImage' \
  <source-dirs> <docker-*/> <packaging-scripts> <assets...> \
  SETUP.md previous-work.md claude-session
```

**排除（都可重建，不入包）**：各專案的 `build/` 編譯產物、docker images（從 Dockerfile 重建；若某個 image 是 inline build 出來的、沒有 Dockerfile，要**先補一份 Dockerfile**再打包）。

## `claude -r` 跨機接續（關鍵機制 — 一定要寫進 previous-work.md / SETUP.md）

`claude -r` 的 session 清單**依「當前工作目錄編碼」分目錄**，所以跨機要對得上：

- **新機器把專案放到「相同絕對路徑」**，還原 `claude-session/projects/<dir>` 到 `~/.claude/projects/<dir>`，再 `cd <proj> && claude --continue`（接最近）或 `claude --resume`（挑清單）。
- **路徑不同（不同 user/home）時**：要嘛把 `~/.claude/projects/<dir>` 改名成新路徑的編碼，要嘛**直接 `claude --resume <SESSION-UUID>`**（用 UUID 就不卡路徑，同 repo 任意目錄都找得到）。
- **最小集**：`<UUID>.jsonl`（對話記錄）+ `memory/`。專案檔本身要存在於該路徑（git/驗證才會動）。
- **不需搬**：全域 `~/.claude/settings.json`、`~/.claude.json`（使用者層級偏好）；MCP/登入在新機重設即可。
- 把**最近一次 session 的 UUID 明寫在 previous-work.md**，接手者一行 `claude --resume <UUID>` 就上手。

## previous-work.md 應有

專案現況快照（分支 HEAD、成品清單、GitHub/patch 狀態）→ 本次做的工作（依主題）→ 工具鏈/harness →
待辦/開放項目 → 鐵則/硬約束 → **§ 在別台電腦接續（claude -r 步驟 + 最近 UUID）** → 記憶索引。

## ⚠️ 隱私

對話記錄 `*.jsonl` 含完整對話。dev-setup 屬**私用**（可能含版權素材／客戶名），**勿公開散布**；
要分享給他人時先評估是否該抽掉 `claude-session/` 與機敏素材。

## 來源

dev-setup 模式萃取自 freesynd-cht（極道梟雄 / Syndicate 繁中化）2026-06 收尾：source+Dockerfile+素材
重建包 + previous-work.md + claude-session 讓另一台機器 `claude -r` 接續。`claude -r` 機制經
Claude Code docs（Sessions）確認。
