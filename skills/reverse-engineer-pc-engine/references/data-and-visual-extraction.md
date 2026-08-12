# 資料與視覺擷取

## 地圖與地形

先區分三種形狀：遊戲 logical map、VDC background attribute grid、螢幕 viewport。它們的寬高、
座標與 stride 可能完全不同。要證實 terrain record，至少需要：raw locator、索引／stride、
movement 或 render consumer，以及 adjacent terrain A/B。

不要由畫面顏色直接猜移動成本；先追 `map record → terrain/type → cost lookup → overlay／path`。

## 單位 placement

畫面 sprite 位置或 SAT entry 只是 presentation locator。placement record 至少要閉合：

```text
unit identity／side／logical coordinate／status raw fields
  → typed record
  → SAT／HUD 或 movement consumer
  → 選取／移動前後 A/B
```

同一單位移動後，追「哪個 CPU-side record 被修改並再次上傳」，比單看 VRAM／SAT diff 有效。

## 圖塊、sprite 與色盤

1. 固定 VRAM／SAT／VCE dump 的 address unit、長度與 byte order。
2. 以 count、bounds、tile dimensions、palette index 寫 parser invariant。
3. 產生私人 contact sheet，人工比對正常玩家 screenshot。
4. 回追 upload source；不要將 VRAM 排列直接當 ROM archive 格式。
5. 保存原始格式與 locator。公開 repository 只放授權或不可重建的文件證據。

## 單位能力、戰鬥與 AI

- HUD／Guide 數值可先作 observation，不等同 raw field 已解。
- 攻防、地形、支援與包圍公式需用 boundary matrix：0／1、範圍內外、單一加成／組合加成、
  相同 RNG seed／stack count。
- AI 依序追 `turn dispatcher → candidate enumeration → score／filter → path → attack → RNG`。
  敵軍有移動只證明 AI 路徑存在，不證明 target score 或公式。
- 攻略可選 high-risk scenario 與驗證預期，但不能替代 ROM record／consumer。

## 音訊

PSG register trace、音符事件、音色資料與最後輸出的 PCM 是不同層次。現代 remake 可重新編曲
或使用新音效；若宣稱原版 parity，仍需固定 PSG write sequence、timing 與可聽抽樣。不得將
原版完整音訊放入未授權 repository。

## 發布邊界

ROM、BIOS、save state、完整 sprite／tile／font／palette、完整地圖 dump、音訊與可重建 payload
預設留在私人工作區。Git 可保存 parser、測試、不可逆 metadata、少量低解析文件截圖與新創作
remake 資產；實際範圍仍以專案 ADR／授權決策為準。
