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
