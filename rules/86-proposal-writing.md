# 研究計畫書 / 技術計畫書撰寫原則

撰寫國科會送審、技術整合、展會提案等長篇計畫書時套用。分「內容原則」「多 agent 流程原則」「格式落地」三塊。對應 skill:`/proposal-writer`。

## 內容原則

1. **定位先行**:先判斷是「工程開發」還是「學術研究」。國科會 / 學術送審必須有**可否證的科學主張** + 假說(H1..Hn,各附 reject-H0 判準、效應量 MDE、統計校正如 Holm–Bonferroni / power)。純工程提案送學術單位前要先「問題化」。展會 demo 定位成「驗證主張的載體」,不是研究目的本身。
2. **範圍誠實 (最常被審查肯定的態度)**:把「計畫期可保證」vs「展後 / 規模外 upside」切分清楚;主動寫死 open problems 與**最大殘餘風險**(典型:demo 規模 → 生產規模的外推 gap)。寧可自己先講限制,不要被審查抓。單一假說落空不應使整個計畫懸空。
3. **標準結構**:前言 → 相關工作 → 提案方法 → 實作 → 議題討論 → 時程 → 展望與結論 → 參考文獻 → 術語(Appendix: Terminology)。
4. **評估協議**:每個假說配 baseline + 量化指標 + benchmark + 消融(ablation);量測前先有 baseline 與判準,不要事後找數字。
5. **[HARD] 文獻真實性**:每篇參考文獻用網路(WebSearch + WebFetch)驗證 arxiv id / DOI / 標題 / 作者 / 卷期,**絕不憑記憶捏造編號**。找不到可靠來源就略過或標「待確認」,不硬湊。中文業界報導以官方 / 原始來源交叉佐證。
6. **[HARD] 技術校正對照原始碼**:凡涉及既有系統的欄位 / API / 協定版本,一律對照**當前版本的原始碼或 dataschema**,不照抄舊協定、不臆測欄位名——系統常跨版本改欄位名 / 型別 / 語意,舊文件與記憶都不可信。落地前 grep 逐行覆核過濾條件,不要照抄後端過濾(可能漏防)。專案的具體版本演進實例(欄位改名、語意變更)寫在對應 repo 的 `CONTEXT.md` 或 `knowledge-base/domain/*.md`,不寫進本通則。
7. **中文計畫書不中英夾雜**:概念性術語首見用「中文(英文)」、之後用中文(規劃期(plan-time)、護欄(guardrail)、基線(baseline));通用縮寫首見「中文全名(縮寫)」(大型語言模型(LLM));**程式碼 / 識別符 / API 路徑 / 檔名 / arxiv id 保留原文**(`do_something()`、`snake_case_field`、`GET /v2/resource/{id}`)。消除「術語堆疊」,讓句子像中文而非翻譯腔。
8. **主管可懂**:配一份**執行摘要(Executive Summary)**,白話 + 生活化比喻、不堆術語,讓非技術決策者 2–3 分鐘懂「做什麼 / 為何現在做 / 怎麼做 / 要什麼資源 / 成果與風險」。技術深度留正文,門面給決策者。
9. **關鍵性質形式化**:把口語安全 / 正確性規則寫成可驗證的不變量(`inv.1..n`,inv = invariant),並明示**證明 / 驗證的範圍界限**(窮舉規模、PBT 抽樣量、覆蓋率),不宣稱超出驗證規模的全稱保證。
10. **ROI / 效益**:數字標明示意 / 假設值,給量化模型 + 敏感度分析;上界取保守值、不用樂觀文獻峰值;先驗目標以文獻區間估計,實測一出即回填。
11. **圖要有帶入感**:架構圖用分層、漸層、邊界標註(如雙層框架 + 確定性橋接 + 時間尺度分界),勝過純文字方塊;圖說一句話點出「讀者該看到什麼」。

## 多 agent 流程原則(長文件協作)

12. **章節分離**:長計畫書拆成章節檔(一章一檔 + `INDEX.md` 導覽),不要單一巨檔——降 token、可分工、可並行、避免混淆。
13. **[HARD] 檔案為中心,不層層傳遞全文**:多 agent 協作時各 agent 自己 Read / Edit 檔案,**agent 之間只傳精簡 findings / changelog,不把整份文件當回傳值層層傳遞**。真實教訓:讓每輪 agent 輸出整份 markdown,文件越滾越大,後期單一 agent 的超大 output 會觸發 API hang;改成「博士只用 Edit 局部改檔、回傳 changelog」即根治。
14. **角色分工**:架構師(整合性 / 設計調整)、撰稿博士(補強)、各領域教授(審查 + 術語譯名 + 文獻可靠度)、設計師(架構圖)、技術文案(跨章統合 + 文獻驗證 + 建 INDEX)、中高階主管(執行摘要 + 可懂度總檢)。
15. **看顧長背景任務**:用 background 哨兵(bash until-loop)偵測三種終態——完成標誌檔出現 / transcript 目錄 N 分鐘無更新(疑卡死)/ 逾時;判斷「卡死 vs 慢生成」靠量測該 agent 的 jsonl 是否還在增長。workflow 卡死用 `resumeFromRunId` 從快取續跑,不從頭。
16. **分章並行 > 單檔迭代**:迭代 review 能收斂品質(分數軌跡可觀測),但邊際效益遞減;分章節並行一次到位通常更省時(實測:分章 24 分鐘 vs 單檔 50 輪 5 小時)。「至少 N 輪」類需求用 review 迴圈,「完成一份高品質文件」用分章分工。

## 格式落地

17. **md → docx pipeline**:markdown 套件(docker uv venv)轉 HTML → LibreOffice(`HTML (StarWriter)` infilter)轉 docx。**SVG 內嵌 LibreOffice 會 IO abort(Code:27)**,須先 `sed 's#<img[^>]*>##g'` strip 掉 `<img>` 再轉,docx 生成後用 `python-docx` 插入 PNG(以圖說文字定位)。**SVG → PNG 用 chrome-headless**(`--screenshot --force-device-scale-factor=2`)。
18. **[HARD] Python 一律 docker uv venv**:用 `ghcr.io/astral-sh/uv:python3.12-bookworm-slim` 等 image 在容器內 `uv venv` 裝套件,不污染系統 Python。

## 何時觸發

- 使用者要寫 / 改 / 審 國科會計畫、技術整合計畫書、展會提案、研究白皮書。
- 涉及多輪 review、多 agent 分工撰寫長文件。
- 對應 skill:`/proposal-writer`(多 agent 分章節撰寫工作流)。
