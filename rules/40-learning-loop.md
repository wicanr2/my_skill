# Learning Loop 規則

任務具有探索、除錯、規劃、重構、研究或需求不完整特性時,採用 learning loop,不一次下結論。

> Bug / 效能 regression 場景以 feedback loop (先建決定性 pass/fail 訊號) 為核心,見 `60-feedback-loop-priority`;本檔為通用框架,適用於 debug 以外的探索任務。

## Core principles
1. 定義 goal、constraint、可驗證 success criteria。
2. 區分 known facts / hypotheses / unknowns。
3. 先做 smallest useful test。
4. 每輪根據觀察更新假設,不重複無效嘗試。
5. 有工具、測試、log、檔案、程式碼或文件可驗證,**先驗證再下結論**。
6. 完成後輸出:結果、證據、剩餘風險、下一步。

## Loop
`Observe → Hypothesize → Test → Compare → Update → Repeat`

| 步驟 | 重點 |
|---|---|
| Observe | 整理輸入、環境、現象、限制;摘要真正的問題,不被表象帶偏 |
| Hypothesize | 列 1–3 個方向,標記信心高低 |
| Test | 設計最小區分性測試;coding/debug 場景優先用測試、重現步驟、log、diff、靜態檢查 |
| Compare | 明確寫出哪個假設被支持 / 削弱 / 排除 |
| Update | 根據證據調整,前一輪失敗要說明換方法的理由 |
| Repeat | 直到達成 success criteria,或證明資訊不足需向使用者補問 |

## 輸出格式 (複雜任務適用)
目標 / 已知事實 / 假設 / 驗證 / 結論 / 下一步

## Coding / agent 加強規則
- 不只產生看似合理答案,附上可驗證依據。
- 改程式或設定前先說目的,再實作,再驗證結果。
- 遇錯誤先 root cause analysis,再決定修補。
- 同類任務重複出現 → 整理到對應 rule / 工具,不要把暫時訊息混入全域偏好。

## 何時不展開完整 loop
- 純機械性任務
- 問題與答案都明確
- 使用者要求只給最終結果

即使簡化,仍保留「先驗證、再定論」精神。
