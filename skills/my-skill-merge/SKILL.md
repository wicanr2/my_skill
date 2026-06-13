---
name: my-skill-merge
description: 把本機 `~/.claude/` 的 rules / skills / agents / personas 同步進「公開」GitHub repo `my_skill`,**內建機密過濾與去識別化**。方向單一:`~/.claude`(私有,含真實客戶名) → `my_skill`(公開清洗版)。每次都先用 denylist 排除客戶機密資產,再對保留的通用資產逐行 sanitize,最後列 diff 等使用者確認才 push。觸發條件:使用者要求「merge ~/.claude 進 my_skill」「同步我的 skill 到 GitHub」「更新 my_skill repo」「把新 rule/skill 推上去」「跑 my-skill-merge」。**不做 copy & paste — 一律 review 後再併**。
---

# my_skill merge skill

把本機 `~/.claude/` 累積的通用工作資產,安全地同步進**公開** repo `my_skill`(`github.com/wicanr2/my_skill`)。

## 最高原則(違反會洩漏客戶機密,不可妥協)

1. **方向單一**:`~/.claude`(私有 source) → `~/my_skill`(公開 target)。**絕不反向**用 `.claude` 覆蓋 `my_skill` — `my_skill` 的同名檔常是已清洗版,反向會把真實客戶名洩漏出去。
2. **review,不要 copy & paste**。每個要併入的檔案先讀內容、跑 denylist 掃描、做 sanitize,才寫進 target。
3. **公開即不可逆**。push 到公開 GitHub 後,即使刪除仍可能被快取/索引。寧可漏掉一個通用 skill,不可放進一個機密 skill。
4. **真名只存在私有檔**。所有真實客戶名 / 場域 / 系統碼 / 黑名單 skill 名,集中在本機私有設定 `~/.claude/.my-skill-merge-private.sh`(**不進 repo**)。本公開 SKILL.md 與 commit、README 一律只用代號(客戶A/B/C、vendor-x、專案X/Y)。新增客戶碼 → 只改私有檔。
5. **push 前必停**:`git add` + `commit` 後,列出 `git diff --staged` 摘要,**停下來等使用者確認**才 `git push`(符合 agent 邊界:對外/git push 需先確認)。
6. **永遠先 `fetch`,絕不擅自 `pull --rebase`**。`rebase` 在「兩台電腦同時 push」場景會洗掉遠端的 commit,屬於不可逆損失。安全 sync 流程:
   - `git fetch` → 只更新 remote-tracking,不動 local
   - `git status -sb` 看 ahead/behind
   - **fast-forward 才自動 merge**:`git merge --ff-only origin/main`(local clean、remote 領先)
   - **diverged 必停**:雙方都有新 commit → 列出兩邊 commit 給使用者,問「merge / cherry-pick / 手動 review」哪個
   - **`--force` 系列必須使用者明確要求**:`--force` / `--force-with-lease` / `git reset --hard` 都需 explicit go-ahead
   - 等價於「`pull` 只在 fast-forward 場景使用,其他都要先報告」

## repo 定位

`my_skill` 只收**與專案/客戶無關的通用資產**:通用方法論 rule、可公開的 game-port / 工具 / 自動化 skill、agent persona。客戶專屬一律不進。

## 私有設定(denylist 與 sanitize 的真值來源)

執行前先載入:

```bash
source ~/.claude/.my-skill-merge-private.sh
# 提供:
#   $MSM_DENY         denylist 關鍵字 regex(真實客戶/系統名)
#   $MSM_DENY_SKILLS  整資料夾排除的 skill 名單(客戶專屬)
#   msm_sanitize      真名→代號 的 sed 過濾函式(stdin→stdout)
```

私有檔不存在時 **停止並回報**,不要用空 denylist 跑(等於關掉防護)。

## 哪些併入 / 哪些排除

| 類別 | 併入 | 排除 |
|---|---|---|
| **Skills** | 與客戶/公司無關的通用工具、game-port、自動化、persona-style skill | `$MSM_DENY_SKILLS` 名單內者;或 `description`/內文命中 `$MSM_DENY` 者 |
| **Rules** (`~/.claude/rules/`) | 編號 **≥ 40** 的通用方法論(learning-loop、ubiquitous-language、feedback-loop、deep-modules、retro-readme…) | 編號 **< 40**(個人身分 / 客戶領域規則 / 私有 agent 邊界) |
| **Agents** (`~/.claude/agents/`) | 預設**整類不併**(現有皆帶客戶/公司 lore,含看似通用者) | 全部,除非日後出現確認零客戶 lore 的通用 agent,逐一 review 才議 |
| **Personas** (`~/.claude/personas/`) | 通用人格(研究協作者、技術老師…) | 帶客戶/公司 lore 者 |

## denylist 自動掃描(判斷新資產可否公開)

對每個「target 沒有、source 有」的候選檔,跑關鍵字掃描;**命中任一即排除**並回報原因:

```bash
grep -iEl "$MSM_DENY" "$candidate"   # 有輸出 = 命中 = 排除
```

> 注意誤命中:`VmState`(含 "vms")、遊戲 XOR `delta`、vendor 範例字串等,可能同形命中 denylist。命中後**讀上下文確認**是真客戶機密還是同形誤命中,再決定。

## sanitize 去識別化(保留的通用資產若殘留私有資訊,改寫後才寫入)

`my_skill` 既有清洗慣例:真實客戶名 → 代號、絕對 home 路徑 → `~`、移除對私有 skill 的交叉引用。具體對照表在私有檔的 `msm_sanitize`;用法:

```bash
msm_sanitize < "$src_skill" > "$target_skill"
```

公開可見的代號集合:`客戶A/B/C`、`vendor-x`、`專案X`、`專案Y`。新出現的客戶名/場域/專案碼 → 在私有檔 `msm_sanitize` 補一條 `sed` 規則 + 在 `$MSM_DENY` 補關鍵字,**不要**把真名寫進本檔或 commit。

## 工作流

1. **載入私有設定**:`source ~/.claude/.my-skill-merge-private.sh`(不存在則停)。
2. **盤點差集**(source vs target):
   ```bash
   comm -13 <(ls ~/my_skill/skills|sort) <(ls ~/.claude/skills|sort)   # .claude 獨有 = merge 候選
   comm -23 <(ls ~/my_skill/skills|sort) <(ls ~/.claude/skills|sort)   # my_skill 獨有 = 不動
   comm -12 <(ls ~/my_skill/skills|sort) <(ls ~/.claude/skills|sort)   # 交集 = 檢查清洗版是否仍同步
   ```
3. **候選過濾**:對 `.claude` 獨有的每個 skill,先比對 `$MSM_DENY_SKILLS`,再跑 `$MSM_DENY` 關鍵字掃描;通過者才進下一步。
4. **交集檢查**:同名 skill 用 `diff` 比對。差異純為去識別化(my_skill 是清洗版)→ **保留 my_skill,不動**。source 有真正的通用內容更新(非客戶相關)→ 手動把那段 sanitize 後併入,**不整檔覆蓋**。
5. **Rules**:併入 ≥40 的通用 rule;新編號 rule 先掃 denylist。
6. **sanitize + 寫入**:`msm_sanitize < src > target`,連同必要的非機密附檔。
7. **更新 README**:在 Skills/Rules/Personas 表格與「結構」樹補上新項;一句話描述沿用 repo 風格(用途 + 觸發時機)。
8. **全 repo 終掃**:`grep -rinE "$MSM_DENY" ~/my_skill --exclude-dir=.git` 必須只剩誤命中或本 skill 的代號說明,無真實客戶名殘留。
9. **commit + 列 diff + 停**:
   ```bash
   cd ~/my_skill && git add -A && git status --short
   git commit -m "<繁中說明本次 merge 了什麼、排除了什麼>"
   git diff HEAD~1 --stat
   ```
   **停在這裡**,把「併入了什麼 / 排除了什麼(附原因) / sanitize 了哪些」回報使用者,等確認才 `git push`。

## commit message 慣例

- 繁體中文,說明「併入 X / 排除 Y(機密原因)/ sanitize 了哪些」。一律用代號,不寫真名。
- 結尾帶:
  ```
  Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
  ```

## 自我檢查(push 前最後一關)

- [ ] `grep -rinE "$MSM_DENY" ~/my_skill --exclude-dir=.git` 無真實客戶名/系統碼殘留(僅誤命中或代號說明)。
- [ ] 沒有反向覆蓋掉 my_skill 既有清洗版。
- [ ] 沒有把真名寫進 SKILL.md / README / commit message。
- [ ] README 表格與結構樹已同步。
- [ ] 已列 diff 並取得使用者明確 push 同意。
