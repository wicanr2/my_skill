---
name: github-weekly-radar
description: >-
  每週彙整 GitHub「近期重要新專案」並做 senior-PM 重要性評估的工作流。當使用者說「這週/這兩天
  github 重要新專案」「github trending 摘要」「新 repo 週報」「重要開源專案彙整」「100 個新專案 summary」
  時觸發。核心鐵則:web 榜單(github/trending、aggregator blog、medium、dev.to)會把「老牌爆紅」誤當
  「新建」,且常列出過時或灌水的星數;**必須**用 `gh api search/repositories q="created:>DATE" sort:stars`
  核實真實 created_at 與當下星數,剔除非新建者。產出 = 已驗證新建清單 + 分級(S/A/B/C)+ 紅旗 + 行動建議。
---

# GitHub Weekly Radar

每週固定產出一份「近期重要 GitHub 新專案 + 重要性評估」週報。重點不是「抄 trending」,
而是**用 GitHub API 把真假/新舊分清楚**,再用 senior-PM 視角排出該關注什麼。

## 為什麼需要這個 skill(踩過的雷)

web 榜單**不可信**,實測 2026-05 一輪後確認三種失真:

1. **老牌當新品**:`openclaw/openclaw`、`NousResearch/hermes-agent`、`ruvnet/RuView` 等被 blog
   寫成「本月新專案」,實際 `created_at` 是 2025 或 2026 初(建立數月)。它們真實存在、星數甚至更高,
   但**不是新建**。
2. **星數過時/誇大**:同一 repo 不同來源差很多(例:openclaw 被寫 302K,實查 375K)。一律以 `gh api` 當下值為準。
3. **trending ≠ 新建**:github.com/trending 排的是「近期爆星」,新舊混合;要「真·新建」只有 Search API 的 `created:>` 能精準篩。

**結論:任何要報給人看的清單,先過 `gh api` 核實 `created_at` 與 `stargazers_count`,不核實不出稿。**

## 前置

- 需要 `gh`(GitHub CLI)且已登入:`gh auth status` 應顯示 logged in。
- 環境為 Windows / PowerShell(本 repo 作者機)。Bash 在中文路徑下可能 `Exit 127`,**優先用 PowerShell**。
- gh 的 `--jq` 用 PowerShell 傳會被吃掉反斜線跳脫;**改用 `| ConvertFrom-Json` 在 PowerShell 端解析**。

## 工作流

### Step 1 — 確認日期與視窗
```powershell
Get-Date -Format "yyyy-MM-dd"
$since = (Get-Date).AddDays(-30).ToString("yyyy-MM-dd")   # 週報用 7,需要更多用 30
```
向使用者確認視窗:「過去兩天」太窄(高星新建往往 <5 個),「30 天」較實用。預設 30 天、星數門檻 2000。

### Step 2 — 撈真·新建高星 repo(權威來源)
```powershell
$since = (Get-Date).AddDays(-30).ToString("yyyy-MM-dd")
$j = gh api -X GET "search/repositories" `
      -f q="created:>$since stars:>2000" -f sort=stars -f order=desc -f per_page=50 |
     ConvertFrom-Json
"total=$($j.total_count)"
$j.items | ForEach-Object {
  "{0,7}  {1}  {2}  [{3}]  {4}" -f `
    $_.stargazers_count, $_.created_at.Substring(0,10), $_.full_name, $_.language, $_.description
}
```
- 調 `stars:>N` 控制清單長度(2000→約 25 個;降到 500 可到上百)。
- 這份就是**可信主清單**。其餘來源只拿來補語境,不直接信。

### Step 3 — (可選)web 榜單補語境,但一律回核
用 WebSearch / WebFetch 抓 trending / aggregator,擷取具名 repo。**每一個**要報的都丟回 gh 核實:
```powershell
foreach ($r in @("owner/repoA","owner/repoB")) {
  try { $d = gh api "repos/$r" | ConvertFrom-Json
        "{0,8}  {1}  created {2}" -f $d.stargazers_count,$r,$d.created_at.Substring(0,10) }
  catch { "NOTFOUND  $r" }
}
```
凡 `created_at` 不在視窗內 → 標「老牌、非新建」移到附註,不混進主清單。

### Step 4 — senior-PM 重要性評估
把核實後的清單交給一個 PM agent(`Agent` tool,subagent_type=general-purpose),產出:
1. **分級** S/A/B/C:
   - **S** = 策略性、缺它不行(基礎設施 / 會被天天用的工具)。
   - **A** = 值得導入 / pilot。
   - **B** = 小眾,挑 1–2 個即可(可互換的長尾)。
   - **C** = 炒作/雜訊/雙刃,略過。
2. **真·新且重要的 3–5 個訊號**(趨勢,不是單一 repo)。
3. **紅旗清單**:灌水星數、無 benchmark 的「self-improving/autonomous」宣稱、雙刃(過 bot 偵測、deepfake、OSINT)、內容包(content repo 非 code,流行曲線易棄)。每項附「tell(辨識特徵)」。
4. **行動建議 5–8 條**:adopt / pilot / monitor / ignore,具體到該怎麼做。

PM prompt 要點:自足(agent 看不到本對話)、附完整清單與星數、要求 <900 字、decision-oriented。

### Step 5 — 輸出格式(交付給使用者)
- **A. 已驗證新建清單**:依領域分群,每列 `星數 · created · owner/name · 一句話`。
- **B. PM 簡報**:分級表 + 訊號 + 紅旗 + 行動。
- **附註**:被誤報為新的老牌 repo(列真實 created_at)。
- 預設繁體中文(zh-TW),技術術語保留原文。

## 每週節奏

使用者會**每週**跑一次。第二週起:
- 視窗用上次執行日至今(避免重複報同一批)。
- 維護一份「已報過」清單(可存在本 repo `seen/CHENGYYYY-WW.md` 或記憶),只報增量 + 重大星數躍升。
- 趨勢類訊號可跨週比較(某主題持續升溫 vs 退燒)。

## 領域分群參考(2026 觀察到的 bucket)

agents / coding-agents・skills 生態(skill 包,本身高 churn)・memory/context/RAG/MCP・
本地 on-device・inference/training・MLX(Apple Silicon)・audio/TTS・vision/video・infra/platform・
其他(security / OSINT / 硬體周邊 / 中文工具)。
