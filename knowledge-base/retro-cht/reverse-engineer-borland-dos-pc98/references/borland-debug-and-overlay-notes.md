# Borland DOS／PC-98 除錯表與 Overlay 筆記

## 目錄

- [判定 MZ load image](#判定-mz-load-image)
- [0x52FB 除錯資料](#0x52fb-除錯資料)
- [舊式 16-bit symbol record](#舊式-16-bit-symbol-record)
- [Turbo Pascal TPOV](#turbo-pascal-tpov)
- [PC-98 音訊追蹤](#pc-98-音訊追蹤)

## 判定 MZ load image

DOS MZ 宣告檔案映像大小：

```text
e_cblp == 0: e_cp * 512
otherwise:   (e_cp - 1) * 512 + e_cblp
```

從此位址開始檢查附加資料。`FB 52` 是 little-endian 的 `0x52FB` Borland
除錯表簽章；它後面的資料不是可直接反組譯的 resident code。

## 0x52FB 除錯資料

Borland Open Architecture 第 3 章列出 `debug_header`、表格順序、
`symbol_record` 與名稱池。注意文件主要描述較新的 Borland C++ 格式；較舊
Turbo Pascal 版本可能使用 16-bit count，不能直接套用 32-bit C struct。

可靠解析步驟：

1. 讀取 magic 與 version。
2. 以候選欄位寬度計算所有 table 的最小界線。
3. 驗證 `symbols_count`、`names_count` 與 `names` 不超出 EOF。
4. 名稱池編碼須由 bytes 判定；本作 Turbo Pascal `0x0208` 使用 ASCIIZ，
   其前方另有 length-prefixed data pool。必須以 count、pool byte size
   與 EOF 邊界雙重驗證，不能把兩個 pool 混在一起。
5. 由 name index 連到 symbol，再把 segment/offset 對回 MZ segment map。

## 舊式 16-bit symbol record

在 Turbo Pascal 5.x 時代的 16-bit 表格中，本作可驗證每筆 9 bytes：
排列：

```text
+0  u16 name_index
+2  u16 type_index
+4  u16 offset
+6  u16 segment
+8  u8  flags/class
```

使用錯誤的 10-byte stride 會出現「只有每第 9 筆像正常 symbol」的週期性
假象；這是應立即檢查 record width 的診斷訊號。此 layout 是實證導向，
不是把 BC4 的 32-bit struct 強制縮窄。
解析器必須用 symbol count、下一表起點、name index 範圍與程式地址共同驗證。

## Turbo Pascal TPOV

`GAME.OVR` 類檔案若以 `TPOV` 開頭，可由 resident MZ 中的 overlay control
records 建立 chain。常見 control 會給：

- overlay 檔案位址；
- code size；
- relocation size；
- entry count。

每段下一個檔案位址應等於：

```text
current_file_offset + code_size + relocation_size
```

只在 code span 掃描 opcode。Relocation bytes 中的 `CD xx` 不能算成
`INT xx` 指令。

## PC-98 音訊追蹤

若除錯名稱含 `BGMPLAY`、`MSCPLAY`、`MSCSTOP`、`INITSOUND` 或
`MUSICNO`：

1. 先把 symbol index 對回 resident／overlay 地址。
2. 從命名 routine 找 caller 與參數，不先猜曲目用途。
3. 搜尋 literal `INT D2h` 之外，也檢查 interrupt vector、far call 與 driver
   wrapper。
4. 用執行期 trace 記錄曲目號、場景、呼叫順序與停止時機。
5. 場景—曲目對照屬於遊戲 game pack；interrupt contract 才適合回存共用
   engine／skill。
