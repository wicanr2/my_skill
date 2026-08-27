# Borland Turbo C++ 16-bit DOS runtime helper patterns

更新：2026-08-27。用途：已由檔內字串、FLIRT 或多組 codegen idiom 確認
Borland Turbo C++ 16-bit 家族後，分流編譯器產生的算術、huge pointer 與
near／far 轉接 helper。

## 使用停止線

- 先確認 compiler family；不得將本頁套到僅因年代相近的 Microsoft C、
  Watcom、Turbo Pascal 或純組語模組。
- 每個專案都要保留輸入雜湊、工具版本、位址空間、完整 callee bytes、
  至少三個 caller 與成功／失敗 consumer。
- 本頁的 mnemonic 形狀是候選 pattern，不是可跨 binary 直接改名的
  byte signature。位址、寄存器分配與內部 entry 會隨版本、模型與最佳化改變。
- 證實 helper 只屬 RTL 且沒有玩家狀態 side effect 後就停止；不在 remake
  逐行移植。繼續追 caller 的 operand 寬度、符號與結果 consumer。

## 工具鏈正對照

高價值證據是連續內嵌的 `Turbo C++ - Copyright 1990 Borland Intl.`
類字串、啟動 ABI 與多組互相一致的 helper。`1990` 只能證明 RTL 年份，
不能單獨證明 Turbo C++ 的精確產品版本。IDA 檔頭的 compiler guess
與直接字串衝突時，以 binary 直接證據優先。

16-bit large-model 常見：

- far 函數 `push bp; mov bp,sp`，第一參數在 `[bp+6]`；
- near 函數第一參數在 `[bp+4]`；
- `retf N`／`retn N` 中的 `N` 是 callee 清除的參數 bytes，不是 local size；
- 大量 far call 是記憶體模型訊號，不是單獨的 compiler 版本訊號。

## 32-bit 算術 helper

### 乘法

候選形狀：把兩個 32-bit 數分成 16-bit halves，多次 `mul`，將交叉項
加入高 word，回傳低 32 bit。必須由三個 caller 確認輸入寄存器配對與
回傳 pair，才能標成 `u32_mul_low`。

### 除法／餘數分派

常見多個小 entry 先將 mode 設成 0–3，再共用一個 32 次 shift／rotate／
subtract 主體：

- mode bit 0 常用來選 signed／unsigned 前處理；
- mode bit 1 常用來選 quotient／remainder；
- 除數為零的分支可通往 RTL divide-error consumer，但要追到實際錯誤處理才定案；
- IDA 可能只建出部分 entry，不可把落在函數間的 wrapper 當 dead code。

### 32-bit 位移

候選形狀會以 `count < 16`／`count >= 16` 分流：

- 左移：低 word 的高位移入高 word；
- 算術右移：高 word 用 `sar`，大位移分支保留符號；
- 邏輯右移：高 word 用 `shr`，大位移分支清零新高 word。

判讀 caller 時把 call 收攝為單一 typed operation，但仍保留原始位址與
signedness 證據；不要用自然語言的「大數運算」取代寬度。

## huge pointer helper

16-bit huge pointer 正規化的核心特徵是：

```text
segment += offset >> 4
offset  &= 0x000f
```

當 32-bit 偏移跨過 64 KiB，還會看到 segment 以 `0x1000` 為單位增減。
常見家族：

- 正規化後比較兩個 far／huge pointer；
- pointer 加／減 32-bit 偏移，結果由寄存器 pair 回傳；
- 對記憶體中 `{offset, segment}` 四個 bytes 原地加減偏移。

這些形狀可證明指標算術，不能單獨證明指向的資料型別。資料型別要從
loader write、caller 的基址來源與後續 consumer 另行證明。

## near-to-far 轉接與 IDA 邊界陷阱

候選轉接片段：

```asm
pop  reg
push cs
push reg
; fall through into a far helper body
```

它將 near return address 擴成 far return frame。IDA 可能將它分成獨立函數並報
stack-analysis failure。驗證步驟：

1. 保留 wrapper 與直落 callee 的連續 bytes；
2. 追一個 near caller 進入前後的 SP 淨變化；
3. 追一個直接 far caller 到同一主體；
4. 兩邊回傳寄存器與 side effect 一致後，附加「near-to-far bridge」語意；
5. 不用重畫函數邊界或改名來取代原始定位證據。

## 負對照與重開條件

下列不可因為與 RTL 相鄰就併入 compiler helper：

- DOS interrupt／callback 安裝與還原；
- VGA、PIT、PIC、DMA、Sound Blaster、AdLib 或其他驅動模組；
- LZEXE 解包 stub、overlay entry、far-pointer dispatch table；
- 顯示、音效、壓縮、圖形搬移與自製資產工具。

若新 binary 的 helper 具有不同 calling convention、改變遊戲全域狀態、或失敗臂
通往玩家可見行為，立即重開分類，不得沿用本頁的 RTL 結論。
