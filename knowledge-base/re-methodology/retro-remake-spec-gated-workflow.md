# Retro remake spec-gated workflow

正式重製功能固定依序通過：

```text
RE evidence → DRAFT spec → evidence review → READY spec
            → implementation → same-state verification → CONFORMED spec
```

`DRAFT` 只允許研究與可丟棄 probe；`READY` 才能授權 production implementation；
`CONFORMED` 必須同時通過 spec 的 remake 內部測試及適用的原版 oracle。新證據推翻舊
結論時標記 `SUPERSEDED`，保留舊證據與訂正原因。

READY spec 至少記錄範圍、排除範圍、原版版本與 SHA-256、工具與位址空間、原始
位址／offset／bytes／xref 或實驗、推論等級、typed input、狀態轉移、邊界、失敗模式、
正常玩家垂直鏈、存檔影響、驗收方法、已知差異、停止線及權利邊界。

實作發現未知時回到 RE／spec，不得在程式或測試內默默猜補。純重構不必新開 RE spec，
但不得改變既有行為契約。詳細執行規則由
`reverse-engineer-retro-game-remake/references/spec-gated-workflow.md` 提供。

## RND() 固定種子對拍鐵則

- 測試項目涉及 `RND()` 或其他亂數判定時，必須透過 dosgolem 固定原版的測試種子（seed），
  remake 也必須固定測試 seed，再以可重播的相同初始狀態與等價輸入做對拍驗證。
- 測試收據必須記錄兩側 seed、設定方式、工具／程式版本、初始狀態、輸入與比較結果。
  seed 必須在執行前固定；不得反覆重擲或挑選碰巧通過的結果當作驗收。
- 不強求未受控的正式執行、即時時鐘初始化或自然運行的真實 `RND()` 也能逐次對拍；
  不把跨整段流程的精確骰序、重擲次數或亂數內部呼叫次數一致列為預設完成閘門，
  也不得為此持續深挖原版亂數內部實作。
- 相同 seed 數字不保證不同亂數實作產生相同結果。比較前須確認比較點的狀態與
  亂數條件可比；必要時以明示的受控亂數輸入隔離待驗規則，並在收據標示方法。
  固定 seed 本身不是對拍通過的證據，不得用它掩蓋規則、狀態轉移或玩家可見結果的差異。
- 固定 seed／受控亂數僅屬測試條件，不得把正式遊戲永久鎖成測試結果。局部常式
  對拍不能取代正常玩家路徑驗收；完成聲明須限於實際驗證的範圍。
