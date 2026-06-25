---
name: proposal-writer
description: 用多 agent 分章節分工撰寫 / 精鍊長篇計畫書(國科會送審、技術整合、展會提案),含文獻驗證、技術校正、術語中文化、執行摘要與 docx 產出。
version: 1.2
metadata:
  hermes:
    tags: [proposal, research-plan, multi-agent, workflow, docx]
    category: productivity
    related_skills: [grill-with-docs]
---

# Proposal Writer Skill

用 dynamic workflow 編排多個角色 agent,分章節分工撰寫或精鍊一份長篇計畫書,並輸出分章 markdown(分工閱讀)+ 合併 docx(單檔交付)。原則面見 `rules/86-proposal-writing.md`,本 skill 是落地工作流。

不適合:單段短文、一次性回答(直接寫即可,不需 workflow)。

## When to Use

- 撰寫 / 大改 / 精鍊國科會計畫、技術整合計畫書、展會提案、研究白皮書。
- 需要多輪 review 收斂、或多角色(架構師 / 教授 / 文案 / 主管 / 設計師)分工。
- 已有草稿要做結構重排、術語中文化、文獻驗證、可讀性提升。

## 核心原則(務必遵守,血淚教訓)

1. **章節分離**:一章一檔(`plan/00-introduction.md` … + `plan/INDEX.md`),不要單一巨檔。降 token、可並行、可分工、不混淆。
2. **檔案為中心,不層層傳遞全文**:agent 各自 `Read`/`Edit` 章節檔,agent 之間**只傳精簡 findings / changelog**。讓 agent 每輪輸出整份文件 → 後期超大 output → API hang(踩過三次)。撰稿 agent 一律「`Edit` 局部改檔 + 回傳 changelog」,禁止整檔 `Write` 重寫大檔。
3. **分章並行優先**:`parallel()` 各章各一 agent,又快又不卡(實測分章 ~24 分鐘 vs 單檔 50 輪 review ~5 小時)。「至少 N 輪精鍊」才用 review 迴圈。
4. **看顧 + 可續跑**:background 哨兵偵測完成標誌檔 / transcript 停滯 / 逾時;卡死用 `resumeFromRunId` 從快取續跑,不從頭。

## Procedure

### 1. 規劃章節骨架
標準結構,每章一檔:
```
plan/00-introduction.md      前言(摘要+背景+研究問題/假說 H1..Hn+定位)
plan/01-related-work.md      相關工作(文獻綜述+相對 SOTA 的 delta)
plan/02-proposed-approach.md 提案方法(架構+設計,含架構圖)
plan/03-implementation.md    實作(落地工程細節)
plan/04-discussion.md        議題討論(競品+評估協議+ROI+風險+open problems)
plan/05-schedule.md          時程(分工+預算+里程碑)
plan/06-conclusion.md        展望與結論
plan/references.md           參考文獻(IEEE)
plan/terminology.md          Appendix: Terminology
plan/INDEX.md                導覽(閱讀順序+各章摘要)
plan/00-executive-summary.md 執行摘要(白話,給管理層)
```

### 2. 多 agent workflow(用 Workflow 工具)
分階段 dynamic workflow:
- **WriteChapters**(`parallel`):每章一 agent,各自 `Read` 來源 + 抽取重組 + `Write` 該章檔。
- **Unify**(技術文案):跨章一致性統合(`Edit` 局部)+ WebSearch/WebFetch 逐篇驗證文獻 → `reference-check.md` + 建 `INDEX.md`。
- **Review**(各領域教授):依領域(如 Robotics / Physical AI / LLM)各自審查術語譯名 + 通順 + 文獻可靠度,產出建議或修正。
- **ExecSummary**(中高階主管):寫執行摘要 + 站決策者視角做可懂度總檢 → `readability-check.md`。
- (選)**Refine 迴圈**:架構師(整合性)→ 撰稿(`Edit` 補強)→ 教授(評分+must-fix),迭代到分數收斂 / must-fix 歸零;只在「至少 N 輪」需求時用。

範例 workflow 骨架見 `references/workflow-skeleton.js`。

### 3. 內容把關(寫進各 agent prompt)
- 文獻:每篇 WebSearch/WebFetch 驗證 arxiv id/DOI,**不捏造**。
- 技術:涉及既有系統欄位/API/協定,對照**當前版本原始碼**,不照抄舊協定(教訓:某狀態欄位跨版本改名)。
- 文字:不中英夾雜——概念術語首見「中文(英文)」之後中文;通用縮寫首見全名(縮寫);程式碼/API/識別符/arxiv id 保留原文。
- 形式化:關鍵安全性質寫成 `inv.1..n` + 明示驗證範圍界限。
- 範圍誠實:計畫期可保證 vs 展後 upside 切分;明列 open problems。
- **標題正式且讀者看得懂**:章節標題用正式名稱,避免不正式(「一句話」→「核心研究主張 / 計畫概述」)與術語黑話(「相對 SOTA 的 delta」→「主要創新與技術特色」)——一般讀者(尤其決策者)看不懂的標題一律改寫。
- **禁導引式 meta 標籤**:不寫「30 秒抓重點 / 看懂」「約 X 分鐘可讀完」「白話版」「(N 個)白話概念」等「告訴讀者這是給你的簡單版」框架字;白話自然融入正文,標題中性。(對齊 `90-plain-language` 寫作準則。)
- **既有系統描述分層,不混為一談**:既有後端(無 AI)/ 介面層(如 MCP,只是工具介面、**不賦予思考**)/ agent(LLM,負責理解與規劃)三者分清——避免讀者誤以為「加了介面 = 系統會思考」或「既有系統本身有 AI」。一句話框架:思考在 agent、執行在後端、介面只是橋。
- **關鍵概念配示意圖**:架構、創新點等核心概念不只用文字——由設計師 agent 繪 SVG(formal 不浮誇、配色全書一致、圖說一句點出「讀者該看到什麼」);多張圖時 docx 整合用 `python-docx` 逐張以各自圖說文字定位插入。
- **計畫書是引導讀者理解、不是研究過程報告**:不寫「嚴謹度證據 / 查過 N 篇文獻 / 精鍊 N round / 答辯 X 行」等研究過程蒐證,也不寫「我們如何查證 / 覆核文獻」的過程說明——文獻出處進參考文獻表格即可。過程蒐證另存(`research-trail` / `reference-check` / `loop-rounds`),不入正文。同理不寫檔案屬性 / 受眾自述句(如「格式與全書一致」)。
- **參考文獻集中於最後一章**:全書文獻只列在末章參考文獻表;各章正文僅用 `[n]` 行內引用、不自附本章文獻清單(否則編號分散、難維護、易出現孤兒引用)。
- **移除超出計畫範圍的內容**:多輪 reviewer 常導入延伸主題(某對標定位、某周邊技術),若不在本計畫範圍,**移除而非硬留**;移除後務必一併修交叉引用(`§N` 指涉、因移除而產生的孤兒文獻)。
- **核心術語首見中文化要正式**:關鍵專名首見用「中文(英文)」且譯名正式(如 Final Guard → 最終守護(Final Guard));術語表對最核心的不變量 / 機制逐條展開強化解釋,不只列名。

### 4. 產出 docx(見 `references/build-docx.md`)
合併 `plan/*.md` → 單檔 → markdown(docker uv)轉 HTML → strip `<img>` → LibreOffice 轉 docx → `python-docx` 插架構圖 PNG(SVG 用 chrome-headless 轉 PNG)。

## Pitfalls

- **單檔大重寫會 hang**:agent 一次 `Write` 十幾萬字元的檔會超時。用分章 + `Edit` 局部。
- **SVG 內嵌 LibreOffice IO abort(Code:27)**:轉 docx 前先 `sed` strip `<img>`,docx 生成後 `python-docx` 插 PNG。
- **哨兵誤判**:後期 agent 生成慢 ≠ 卡死;量測 jsonl 是否還增長再決定 resume。
- **文獻編號漂移**:agent 精鍊時可能新增文獻使編號變動(如 [26]→[38]→[89]);以 `reference-check.md` 為對齊基準。
- **loop / 多輪擴增的文獻必逐篇覆核(別只查首批)**:多輪精鍊時 agent 會大量新增文獻,其中**真的會混入捏造**——曾抓到一筆捏造作者(假名 + 標題張冠李戴 + 殘缺 DOI),藏在 50+ 篇新增裡。每次擴增後對**新增區段**重跑 WebSearch/WebFetch 覆核,捏造者標註或移除,不可假設「之前查過就沒事」。這是文獻誠信的最後防線。
- **Python 污染系統**:一律 docker uv venv。

## Verification
- 各章檔存在且自洽、`INDEX.md` 連結正確。
- `reference-check.md` 每篇有驗證結論。
- docx:章節標題對應 Word Heading 樣式、架構圖已嵌入(`word/media/`)、表格為真表格。
- 全文無未處理的中英夾雜(概念術語)、無術語堆疊段落。
