# 工具鏈與適用閘門

## 建議分工

| 工具 | 角色 | 適合 | 不能單獨證明 |
|---|---|---|---|
| Mesen2 | 動態探索主工具 | PCE memory types、HuC6280 PC/state、Lua memory／event callback、輸入與 screenshot | 與另一 emulator／原始硬體相同、遊戲欄位語意 |
| Mednafen | 相容性與正常玩家 oracle | PCE debugger、logical／physical breakpoint、Trace Log、state、玩家路徑 | 欄位名稱、完整 dataflow、現代 remake parity |
| IDA Pro | 條件式靜態輔助／主工具 | raw bytes、xref、函式邊界、jump table、外部語意索引 | HuC6280 特有 opcode 與 MPR-aware CFG，除非 processor／loader 已驗證 |
| Ghidra | 靜態第二意見 | CFG、xref、script、自訂 language | 未驗證 language 下的 HuC6280 完整反組譯 |
| Capstone／da65 | raw-byte regression | opcode search、短 fixture、第二套 decode | 函式邊界、MPR、VDC 與 gameplay consumer |

## HuC6280 processor fixture

靜態工具要升格為主反組譯器，至少驗證：

1. `TAM #imm`、`TMA #imm` 的 opcode、長度、operand 與 MPR side effect；
2. `TAI`、`TII`、`TDD`、`TIN` 的三個 operand 與正確 instruction boundary；
3. `ST0`、`ST1`、`ST2` 的 VDC 語意與長度；
4. 已知 reset／IRQ vector 與 raw bytes；
5. MPR 改變前後同 logical PC／data address 的 bank context；
6. indirect jump table 的 raw words、bounds 與所有 consumer。

未通過時，文件只能稱「6502／65C02 顯示」或「raw-byte candidate」。IDA 的官方支援列表
列有 6502，但不應由此推論 stock processor 已涵蓋完整 HuC6280；IDA SDK 可建立 processor
module，仍需專案 fixture 驗證。

## Mesen2 gate

固定 release、binary SHA-256、相容 source commit、Lua 文件 revision及容器 image。驗證：

- 可載入同一 ROM hash；
- `cpuType.pce` 與 `pcePrgRom`、`pceWorkRam`、`pceVideoRam`、`pceSpriteRam`、
  `pcePaletteRam` 等 memory type 能被明確選取；
- execution／read／write callback 有界且會移除；
- 可記錄 frame、PC、MPR、event address、space 與輸入；
- 正常玩家 checkpoint 能和 oracle 做畫面與關鍵 state A/B。

Mesen2 Lua state 欄位可能隨版本改名；欄位名稱屬 emulator contract，不是 silicon spec。

## Mednafen gate

Mednafen 官方 debugger 說明指出 PCE read breakpoint 也可能由 opcode／operand fetch 觸發，
所以「read breakpoint 命中」不自動等於 gameplay data read。PCE 的 logical breakpoint 與
以 `*` 前綴的 physical address 必須分列。固定實際 binary version；新版官方文件若標示其他
版本，只能作 source-model 參考，不能假裝與舊 binary 完全相同。

## 已驗證案例基線

Nectaris 專案曾固定 Mesen2 2.1.1 與 Mednafen 1.29，證實 Mesen2 headless Lua、PCE
memory callback、CPU／MPR state，以及 Mednafen 正常玩家路徑與有界 trace 可運作。這是工具
能力案例，不是所有 PCE ROM 或 emulator 版本都已通過。

## 官方入口

- [Mesen2 repository](https://github.com/SourMesen/Mesen2)
- [Mesen2 Lua API source document](https://github.com/SourMesen/Mesen2/blob/master/UI/Debugger/Documentation/LuaDocumentation.json)
- [Mesen2 releases](https://github.com/SourMesen/Mesen2/releases)
- [Mednafen debugger](https://mednafen.github.io/documentation/debugger.html)
- [Mednafen PCE module](https://mednafen.github.io/documentation/pce.html)
- [IDA supported processors](https://docs.hex-rays.com/8.5/user-guide/disassembler/supported-processors)
- [IDA SDK](https://docs.hex-rays.com/9.0/developer-guide/c%2B%2B-sdk)

查閱基線：2026-08-12。使用時重新確認目前 release／revision，不以 `master` 內容代表固定
binary。
