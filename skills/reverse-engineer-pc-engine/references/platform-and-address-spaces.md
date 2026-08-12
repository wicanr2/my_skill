# PC Engine 平台與位址空間

## 先畫清楚的層次

```text
ROM archive／file offset
        │ loader／mapper／header
        ▼
HuC6280 physical bank（8 KiB page）
        │ MPR0..MPR7
        ▼
CPU logical $0000..$FFFF
        ├─ work RAM／save RAM
        ├─ I/O physical bank
        └─ VDC／VCE／PSG／controller registers

HuC6270 VDC VRAM／SAT ── 不屬於 CPU logical address space
HuC6260 VCE palette  ── 不等於 RGB framebuffer
```

HuC6280 將 64 KiB CPU logical 空間切成八個 8 KiB segment，由 MPR0–MPR7 選擇 physical
bank。同一 `$4000` 在不同 MPR snapshot 可指向不同內容；沒有 MPR 就不能可靠換算 ROM
file offset。physical bank `$FF` 常用於 I/O，但應以該 ROM／模擬器的實際 mapping 驗證。

## HuC6280 特有風險

- `TAM`／`TMA`：改變或讀取 MPR；bank-aware CFG 必須把它視為狀態轉移。
- `TAI`／`TII`／`TDD`／`TIN`：block transfer 的 source、destination、length 與方向都會
  影響資料流，不能按普通 6502 指令長度切割。
- `ST0`／`ST1`／`ST2`：VDC 存取捷徑，不是普通 direct-page store。
- indirect jump／table：raw table words、當時 MPR 與 case bounds 必須一起保存。
- direct page operand：`$39` 是 CPU direct-page operand；它的 backing 與語意要由 MPR／
  RAM context、寫入端及 consumer 證明。

## 圖形子系統

- HuC6270 VDC 管理 background tile map、VRAM、SAT、scroll 與顯示 timing。
- HuC6260 VCE 管理色彩與影像輸出；palette index、VCE raw value 與輸出的 RGB 必須分列。
- SuperGrafx 可能有第二組 VDC；工具 memory type 必須明示 VDC1／VDC2。
- VRAM attribute grid 是視覺 presentation，不必然等於遊戲的 logical map、terrain ID 或
  placement record。要回追 CPU-side producer 與 gameplay consumer。

## 固定紀錄格式

每個位址至少寫成：

```text
tool=Mesen2 2.1.1
space=CPU logical
address=$FA39
MPR=FF F8 13 14 01 02 03 00
physical/file-offset=pending
frame/checkpoint=<可重播定位>
classification=已證實|強推論|假說|未知
```

禁止把 `CPU logical $0003`、`I/O physical FF:0003`、`VDC register 02`、VRAM word offset
與 ROM file offset 寫成同一種「位址」。

## 平台與 remake 的邊界

保留原版 tick、IRQ、scanline 與 controller polling 供 oracle 對照；除非玩法 consumer 明確
依賴，現代 remake 不必重建硬體排程。移植的是可觀察規則與資料，不是 HuC6280／VDC 的
執行方式。
