# PC Engine / HuC6280 逆向工具箱

實測來源：`~/cht/nectaris`（PC Engine《Nectaris》remake，2026-08）。這份寫的是**可搬到
其他 PCE 專案的方法與工具形狀**，不含該專案的 ROM 資料或遊戲專屬結論。

## 為什麼 PCE 不能沿用 DOS/PC-98 的直覺

HuC6280 有 8 個 MPR（memory paging register），CPU 只看得到 64 KB logical 空間，
分成 8 個 8 KB page；每個 page 對應哪個 ROM bank 由 `MPR0–MPR7` 決定，而且**執行中會變**。
所以：

- **同一個 CPU logical 位址，在不同時刻對到不同 ROM file offset。** 任何「位址」都必須
  連 MPR 快照一起記，否則就是廢資料。
- `MPR0=$FF` 時 logical `$0000–$1FFF` 是 I/O（VDC `$0000-$0003`、VCE `$0400-$07FF`），
  不是 ROM。看到 `STA $0003` 別當成寫記憶體。
- **zero-page operand 不是 `$0000-$00FF`。** HuC6280 的 direct page 有 backing base
  （實測專案是 `$2000`，要自己取得證據）。`LDA $64` 讀的是 `$2064`。這條踩過就知道，
  不然整條 data flow 會接到錯的位址。
- file offset = `bank * 0x2000 + (logical & 0x1FFF)`，bank 從當下 MPR 取。

## 反組譯：不要用 IDA 的 `m6502`

IDA Pro 的 stock `m6502` 沒有 HuC6280 專有指令（`TAM`/`TMA`/`TII`/`TDD`/`TIN`/`TIA`/`TAI`/
`ST0`/`ST1`/`ST2`），指令邊界會切錯，也不懂 MPR。它只剩「保存 file offset 錨點」的價值。

可行做法是自己寫 256-entry decoder，opcode 表從固定版本的模擬器原始碼轉錄並記 commit +
SHA-256：

- Mesen2 `Core/PCE/PceCpu.cpp` — 完整 opcode / address-mode 矩陣
- Mednafen `src/pce_fast/huc6280_ops.inc` — 特殊指令行為交叉驗證

注意 block transfer（`TII`/`TDD`/`TIN`/`TIA`/`TAI`）是 **7 bytes**：opcode + src + dst + len。
漏掉它，線性反組譯會從那裡開始整段錯位；而且它是 memset/memcpy 的實作，追資料初始化
必須認得它。Mesen 把 `JSR` 的 address mode 標成 `None`（它自己抓 operand），照抄表格時
會讓所有 `JSR` 反查失效。

### region 而不是全域 mapper

decoder 不要猜 mapper。定義成 region：`{ROM file offset, CPU logical start, length,
MPR 快照, entry seeds, mapping status}`，遞迴只在 region 內追。以下一律保留 unresolved，
不寫成「不存在」：direct target 落在 region 外、`JMP (addr)` 間接、`TAM` 改了當前 page、
mirror 只有強推論。

## 三種「這個 byte pattern 是不是指令」的裁決

反查某個 RAM 位址的 writer 時，會掃到一堆 operand 命中，但它們可能落在資料區。用三級分：

| 裁決 | 方法 | 等級 |
|---|---|---|
| CFG 可達 | 在某 region 的 bounded recursive 可達集內 | 已證實（限該 region 與 seeds） |
| linear sweep 對齊 | 從 region 起點線性解碼會落在同一邊界 | 強推論 |
| 對齊投票 | 從前方 N 個起點各線性解碼，多數收斂到同一邊界 | 強推論 |
| 未映射 | file offset 不在任何 region | 未知，只標 bank 候選 |

對齊投票對 65xx 特別有效（指令長度 1–3 bytes，會自我同步）：解得越乾淨、控制流越完整
（有 `RTS`/`BRA` 收束）就越可信。判斷「函式在哪結束」的實用訊號是**解碼突然變得不合理**
——那通常不是錯位，而是後面接了資料表。

## 靜態反查與動態 watchpoint 是互補的，不是替代

這是本專案最貴的一課：

- **靜態 operand 掃描**列得出所有 absolute / direct-page 定址的 writer，**但結構上列不出
  指標間接的 writer**（`STA ($64),Y` 的目的位址執行期才成立）。
- **write watchpoint** 列得出實際執行的 writer，**但只涵蓋這次 route 走過的碼**。

任一方單獨的「沒找到」都不構成「不存在」。實務順序：先靜態掃（便宜、離線、可重跑）把
候選收斂到個位數，再用 watchpoint 裁決未映射的 bank 與指標間接的部分。

反過來也要注意：**zero-page 位址不適合靜態反查**。1-byte operand 的誤命中率極高（實測
一個 direct-page 位址掃出 953 個候選），那種要直接上動態。

## Mesen2 headless 是可腳本化的動態 oracle

固定 `2.1.1`，Docker + Xvfb。`--testRunner --timeout=N --doNotSaveSettings
--debug.scriptWindow.allowIoOsAccess=true script.lua rom.pce`。注意它**執行 Lua 前會檢查
`settings.json`**，所以要先跑一次 GUI 產生 private HOME 的設定。

Lua API 實測（2.1.1）：

```lua
emu.callbackType            -- exec, read, write  ← 三種都有
emu.memType.pceMemory       -- CPU 匯流排，watchpoint 用這個
emu.addMemoryCallback(fn, emu.callbackType.write, lo, hi, emu.cpuType.pce, emu.memType.pceMemory)
emu.read(addr, emu.memType.pceMemory, false)   -- 唯讀取樣
emu.getState()              -- cpu.pc, memoryManager.mpr[0..7], vdc.*
emu.setInput({run=true, i=false, ...}, 0)      -- 送控制器輸入，不必動遊戲記憶體
```

### probe 的三個設計要點（都是踩出來的）

1. **命中時一併取樣 direct-page backing 值。** 只記 PC 只能知道「誰寫的」；把指標、索引、
   長度一起讀出來才知道「寫去哪、寫多長、從哪來」。一次取樣抵好幾輪追查。
2. **per-site 上限 + 另計 skipped。** 每幀輪詢的 writer 會在幾秒內塞滿事件配額，罕見的
   writer 就永遠看不到。site key 要包含 context 值，否則同一個 PC 用不同指標執行時會被
   當成同一個 site 濾掉。被略過的筆數一定要另外計數並寫進輸出——否則「沒記到」會被
   後續讀者當成「沒發生」。
3. **能力清單先寫出來。** 就算 callback 註冊失敗，也把 `emu.memType` / `emu.callbackType`
   的鍵列進輸出。這樣「這次沒成功」不會被寫成「模擬器不支援」。

`cpu.pc` 是**寫入完成後**的 PC，回推指令起點要減掉該指令長度。

### exec callback 列舉間接跳躍目標

`JMP (addr)` 的完整 target 表靜態幾乎不可能定界。對該 PC 設 exec callback，配合 context
取樣讀出指標值，就能列出實際走過的 target。這比猜 jump table 邊界可靠得多——但同樣只
涵蓋走過的 route。

## Mednafen 的定位

`1.29` 的 `pce` module 適合做**畫面／state oracle**（F5 state 可抽 `VDC/VRAM`、`SAT`、
`MAIN/BaseRAM`、`CPU/MPR`）與 trace log。Mesen2 適合做**可腳本化的 callback**。兩者的
frame schedule 不同，要做 A/B 必須先固定同一 state 的 raw equality，不能因為都到達同一
畫面就當成等價。

## 常見的錯誤結論形狀

- 把 CPU logical 當 ROM file offset（數值剛好相同的時候最危險）。
- 把某次觀察到的 MPR 快照當全域 mapper。
- 檔案大小能整除某個數 → 宣稱圖形格式已知。整除只證明 layout「可能」。
- 一次 trace 沒捕到某段碼 → 宣稱它不執行。只能說這條 route 沒走到。
- 用 decompiler / 自訂函式名當事實。banked code 的 decompiler 會安靜地編造控制流。

## 工具形狀（可直接搬）

| 工具 | 職責 |
|---|---|
| `huc6280_disassembler.py` | 256 opcode decoder + region-aware bounded CFG + xref + unresolved |
| `scan_ram_xrefs.py` | 以 CPU logical 位址反查全 ROM producer/consumer，三級對齊裁決 |
| `mesen2_pce_write_watch_probe.lua` | write/exec watchpoint + context 取樣 + per-site 上限 |
| `mesen2_pce_headless_probe.sh` | 固定 timeout、private HOME、per-script output 收集、產物 hash |
| `rebuild_*_disassembly_kb.py` | 固定 ROM identity、region/anchor 驗證、語意索引合併、私人 bundle |

語意索引（region / anchor / mechanism coverage）版控，**反組譯 listing 與 bundle 不版控**
——它們含大量原版 raw bytes。每個 anchor 存 `file_offset + cpu_logical + MPR + raw_bytes +
mnemonic + 語意註記 + 證據等級 + 出處`，重建時用 ROM 驗證 raw bytes 與 decode 結果，
不符就 fail-closed。

## 相關

- `~/.claude/knowledge-base/retro/ida-pro-9.4.md`（IDA 本機環境；PCE 用它只為 file offset 錨點）
- `rulebook/62-static-provenance-trace.md`（先靜態反追再談動態）
- `rulebook/65-verify-against-reference-not-internal-signals.md`（測試綠不等於對齊原版）
