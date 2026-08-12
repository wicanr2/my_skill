# 證據契約與模板

## 命題層級

- `H-xxx`：平台硬體／位址空間命題。
- `D-xxx`：模擬器、debugger、loader 或工具行為。
- `P-xxx`：特定 ROM／遊戲／checkpoint 個案。

遊戲個案不能自動升格為平台事實；模擬器 source model 也不能自動升格為 silicon 行為。

## 固定記錄

```text
ID=P-xxx
問題=<單一可裁決問題>
輸入=<ROM filename、SHA-256、size、region/revision>
工具=<名稱、binary version/hash、source commit、container image>
路徑=<正常玩家輸入、checkpoint、frame/state hash>
空間=<ROM file | CPU logical | CPU physical | I/O physical | WRAM | VDC VRAM | SAT | VCE>
原定位=<file offset、PC、MPR、operand、raw bytes>
觀察=<有界 trace／diff／screenshot／consumer>
語意=<附加說明；不得取代原定位>
等級=已證實|強推論|假說|未知
來源=<官方 URL、文件版本／頁碼或本地 evidence path>
nonclaim=<本證據不能推出什麼>
下一步=<最小 adjacent-value／writer／consumer 實驗>
```

## 升級規則

- `未知 → 假說`：有可回查線索。
- `假說 → 強推論`：兩種獨立來源，或來源加可重播動態實驗互相吻合。
- `強推論 → 已證實`：保留 raw bytes／原定位，且 writer／consumer 或原版行為完成交叉驗證。

函式 rename、欄位名稱、綠色 remake 單元測試與單一截圖都不是升級理由。

## 非破壞性反組譯顯示

每筆函式、位址或 operand 匯出採同列格式：

```text
raw locator | original name/operand | added semantics | confidence | evidence source
```

IDA／Ghidra 內可建立導覽別名，但版控索引必須保存原名稱、linear／logical address、MPR、
file offset 與 raw bytes。匯出工具要自動合併索引，不能依賴操作者記得查另一份筆記。

## 勘誤

推翻舊結論時保留舊 ID、原證據與形成原因；追加 erratum，說明新 bytes、版本、writer／consumer
或正常路徑為何足以否定。搜尋並修正目前狀態表，但不要重寫歷史讓錯誤來源消失。

## 交接分類

明確分開：

1. remake implementation required；
2. original reverse engineering required；
3. dynamic oracle required；
4. visual／audio production required；
5. packaging／release required；
6. optional modernization。

「原版仍未知」不一定阻塞 remake；若採現代設計補足，必須由產品決策授權並明示非 PCE exact。
