---
name: reverse-engineer-pc-engine
description: 以 HuC6280、MPR bank mapping、HuC6270 VDC、HuC6260 VCE 與具除錯能力的模擬器，對 PC Engine／TurboGrafx-16／SuperGrafx HuCard 遊戲做可追溯逆向工程。用於 PCE ROM inventory、Mesen2／Mednafen debugger、Lua callback、bank-aware trace、地圖／地形／單位配置、圖塊／sprite／色盤、戰鬥與 AI 邏輯、IDA／Ghidra 適用性評估、乾淨 remake 資料擷取及證據交接；特別適合一般 6502 反組譯器無法正確處理 HuC6280 特有指令與 MPR 位址脈絡時。
---

# 逆向 PC Engine 遊戲

將原版視為行為與資料格式 oracle。以具 PCE debugger 的模擬器建立動態主線；靜態工具只有
在通過 HuC6280 與 bank fixture 後，才能擔任主反組譯器。

## 固定工作順序

1. 讀取專案 `AGENTS.md`、目前狀態表與證據帳本；原版 ROM 一律唯讀並記錄檔名、大小、
   SHA-256、archive entry、區域與 header／padding 判定。
2. 明確分開 ROM file offset、CPU logical、CPU physical bank、work RAM、I/O physical、
   VDC VRAM、SAT、VCE palette 與模擬器內部 state。需要換算時同列保存 MPR snapshot。
3. 先以正常玩家輸入建立短而可重播的 checkpoint；再加 execution／read／write callback。
   不用座標注入、RAM 修改或 direct-entry 取代正常路徑證據。
4. 每次只追一條垂直鏈，例如 `raw record → typed terrain → movement consumer → overlay`，
   或 `end turn → AI candidate → target/path → battle`。足以實作並測試後停止。
5. 用第二個 emulator、固定 source model、raw bytes 或靜態 xref 交叉驗證。相近畫面或相近
   frame 只能是候選，不能冒稱同一 state。
6. 將結論分成 `已證實`、`強推論`、`假說`、`未知`；保留原始位址、bytes、工具版本、
   address space、輸入 trace、consumer 與明確 non-claims。
7. 只有完整 vertical chain 才接到 remake typed data。PCE IRQ、掃描線排程與控制器 polling
   cadence 通常只屬原版平台證據；現代引擎使用自己的 update／input／audio 機制。

## 工具裁決

- 優先用 Mesen2 做有界 Lua 探索與 memory-space callback，再以 Mednafen 正常玩家路徑作
  oracle。兩者必須固定 binary／source revision 與輸入 checkpoint。
- IDA Pro 並非一律禁用；但 stock 6502 顯示若未正確解出 `TAM`、`TMA`、`TAI`、`TII`、
  `TDD`、`TIN`、`ST0`、`ST1`、`ST2` 與 MPR context，只能作 raw-byte／xref 輔助。
- Ghidra、Capstone、`da65` 同樣必須先通過 opcode 長度與 bank fixture；工具能顯示組語，
  不等於已理解 HuC6280 控制流。
- 靜態註記採非破壞性契約：保留原名稱／位址／operand，另附語意、等級與來源；推測性
  rename 不得成為證據。

## 按需載入

- 處理 MPR、logical／physical、VDC／VCE／SAT 時，讀
  [平台與位址空間](references/platform-and-address-spaces.md)。
- 選擇 IDA、Mesen2、Mednafen 或其他工具時，讀
  [工具鏈與適用閘門](references/toolchain-and-gates.md)。
- 設計 trace、callback、A/B 或正常玩家 checkpoint 時，讀
  [動靜態工作流](references/reproducible-workflow.md)。
- 擷取地圖、圖塊、sprite、色盤、單位 placement 或規則表時，讀
  [資料與視覺擷取](references/data-and-visual-extraction.md)。
- 新增研究筆記、推翻結論或交接時，讀
  [證據契約與模板](references/evidence-contract.md)。

## 停止條件

當證據已能支撐 typed parser、runtime consumer、deterministic test 與原版抽樣，就停止擴張
反組譯。完整理解 ROM、逐行翻譯 executable、模擬原版 IRQ schedule 或發布可重建原版的
資產，不是 remake 的預設完成條件。
