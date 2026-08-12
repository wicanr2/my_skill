# 可重播的動靜態工作流

## 1. 建立 oracle checkpoint

用正常玩家輸入從 power-on 到窄狀態，保存：ROM hash、emulator binary hash／version、設定、
輸入序列、frame／畫面 hash、MPR、必要 state section hash。save state 可協助縮短實驗，但
必須保留一條不靠 state／debug shortcut 到達同狀態的路徑。

## 2. 先做差分，再做長 trace

選 adjacent-value A/B：同一游標左右一步、合法／非法目的地、攻擊範圍內外、回合結束前後。
比較固定範圍與 address space；長 trace 只在差分已縮小候選後啟用。

```text
baseline state ── action A ── screenshot／RAM／VRAM／MPR
same checkpoint ─ action B ── screenshot／RAM／VRAM／MPR
```

若兩邊不是同一 checkpoint、輸入或 frame phase，結論必須標為 nearby-state。

## 3. callback／trace 保持有界

- 只監看候選 range、PC window 或 event count；設定 timeout、file-size cap 與 callback removal。
- 每筆 event 記錄 frame、PC、MPR、logical／physical address、memory type、access kind。
- read breakpoint 可能含 instruction fetch；需以 opcode／operand context 分類。
- 大量 reads、少量 writes 不代表沒有 writer；追取址端、block transfer 與 indirect write。

## 4. 從 presentation 回追 producer

```text
已知畫面 tile／sprite／palette
  → VDC VRAM／SAT／VCE raw locator
  → upload／transfer window
  → CPU-side source buffer
  → ROM／RAM record
  → gameplay consumer
```

VDC upload routine 常是共用 presentation helper。找到它只代表資料經過該處，不能把 source
buffer 直接命名為 terrain／unit／AI。

## 5. 靜態交叉驗證

將動態 PC 連回 raw bytes與 bank context；在靜態資料庫查 caller、callee、xref、indirect
table 與 writer。註解採：`原定位 | 附加語意 | 等級 | evidence ID`。如果 processor 不支援
HuC6280，僅使用 raw bytes、人工 instruction boundary 與外部位址索引。

## 6. 完成 vertical chain

最小充分範例：

```text
ROM bytes + hash + file range
  → parser（count／stride／bounds／raw round-trip）
  → typed Terrain／Placement
  → movement／render consumer
  → deterministic fixture
  → 原版同狀態抽樣
```

只有 UI、只有資料表、只有 VRAM dump 或只有動態差分都不算閉合。

## 7. 失敗分類

- breakpoint 未命中：先檢查 MPR 切換、logical／physical 基準、frame phase 與 fetch 行為；
  不宣稱 caller 不存在。
- 兩 emulator 不同：固定 ROM、input movie、state scalar 與 framebuffer；保留版本差異，
  不選自己偏好的結果當真相。
- trace 過大：回到窄 A/B 與 callback，不用無界 instruction logging 硬撐。
- remake 能跑但 oracle 未解：標成 `modern_design` 或 observation，不升格 PCE exact。
