# 逆向結論回填與跨規格防遺漏

## 問題形狀

長期逆向專案常把一個呼叫先記成 `unknown`，後續在另一份 spec 或另一平台解出
exact 語意，卻只更新函式台帳，沒有回填較早的玩家流程。結果是實作者忠實照著
過期 spec 實作，測試也只驗證那條被截短的流程。

典型案例：較早建角 spec 把姓名後的 `sub_3EE3` 留成未知；後續已證明同一個
DOS `overlay-17:03EE3h` 是 `SETACTIVEICON`，但沒有回填，remake 因此漏掉整個
READY／ACTION 戰鬥圖示編輯器。

## 固定方法

每次把函式、欄位或分支從 unknown／hypothesis 升為 exact／strong inference：

1. 建立不可變鍵：`平台＋映像／overlay／模組＋原始位址或 offset`。不可只用
   `sub_83`、反編譯變數名或後加語意名；不同 overlay 會重複使用短名稱。
2. 新 evidence spec 列出 callers、consumers、玩家垂直鏈、推論等級與被推翻的舊斷言。
3. 全域找出所有引用同一不可變鍵的舊 spec；逐份標成仍未知、已勘誤或不受影響。
4. 維護「resolution backlink ledger」：至少包含不可變鍵、語意、evidence spec、
   older spec、older spec 必須出現的勘誤標記。
5. 用 fail-closed 腳本檢查：evidence 不含原始位址、舊文件不存在、或缺勘誤標記
   都讓驗證失敗。不要靠人記得回查。
6. 若新結論改變玩家可見流程，規格狀態依序走 READY → 實作 → 正常按鍵／同狀態
   oracle → CONFORMED；函式台帳的綠色不能取代垂直鏈。
7. README／完成度只消費已回填的目前 spec，不直接從歷史 worklist 或舊 checkpoint
   推斷功能完成。

## 建議資料格式

```text
platform_module  address  semantic  evidence_spec  older_spec  required_correction
dos-overlay-17   03EE3h   SETACTIVEICON  spec-1037  spec-1093  已閉合為 SETACTIVEICON
```

## 自動化邊界

- 可以自動驗證 ledger 的位址、文件與勘誤 backlink。
- 可以列出仍含「沒有宣稱／unknown」的具名位址作候選清單。
- 不可用短函式名自動跨 overlay 配對，也不可把「另一份文件提過同名函式」當成
  已解；這會製造錯誤勘誤。
- 沒有玩家影響的 runtime helper 可維持不阻塞，但仍要記錄具體分類理由。

## 完成條件

一項 RE resolution 只有同時滿足下列條件才算閉合：

- 新證據保留原始定位與推論等級；
- 受影響的舊 spec 已明文勘誤；
- 玩家垂直鏈或不阻塞理由已更新；
- 自動 backlink 護欄通過；
- 若有行為改變，正常玩家路徑測試已覆蓋。
