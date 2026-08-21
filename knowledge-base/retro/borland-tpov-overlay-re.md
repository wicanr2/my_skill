# Borland／Turbo Pascal overlay（TPOV）遊戲的逆向

適用於 1980s–90s 用 Turbo Pascal／Borland 工具鏈編譯、帶 `.OVR` overlay 檔的
DOS（與 PC-98）遊戲。SSI Gold Box 全系列是典型案例。

搭配 [`ida-pro-9.4.md`](ida-pro-9.4.md) 使用：那份講本機 IDA 環境與 headless
坑，這份講 overlay 這個檔案格式帶來的方法問題。

## ⭐ 最重要的一件事：raw overlay 丟進 IDA 會得到 0 個函式

實測 SSI《Curse of the Azure Bonds》的 DOS `GAME.OVR`（272 KB）直接載入
IDA 9.4，**只產生 1 個函式**。PC-98 版同樣。

原因不是 IDA 有問題：overlay 的 code span 沒有 MZ header、沒有 entry point，
自動分析無從開始。而遊戲的絕大部分程式碼都在 overlay 裡——那個專案的
resident executable 只有 23 KB 程式碼，overlay 有 260 KB。

**症狀是「這個檔案好像沒有程式碼」，而它與「真的沒有程式碼」長得一模一樣。**
在下這個結論之前，先確認你有沒有種 entry point。

## TPOV 容器格式

`.OVR` 檔以 `TPOV` 四個 ASCII bytes 開頭，之後是一串 code span。每一段的
**control record 在 resident executable 裡**，不在 `.OVR` 裡：

```text
control record（在 EXE 內，長 30h）：
  +00  CD 3F              INT 3Fh（Borland overlay manager 的觸發）
  +04  u32  file offset   指向 .OVR 內的 code 起點
  +08  u16  code size
  +0A  u16  relocation size
  +0C  u16  entry count
  +20  entry stub 表，每筆 5 bytes：
         CD 3F, handler_local_offset:u16le, flags:u8
       第 i 筆的 stub offset = 20h + i*5
```

`.OVR` 內每段是 `code size` bytes 的可反組譯 code，緊接 `relocation size`
bytes 的 fixup（**嚴格遞增的 u16 code offset，不是 code**，別反組譯它）。

驗證方式：control record 必須**串成一條鏈**——第一段的 file offset 等於
`len("TPOV")`，之後每段的 file offset 等於前一段的 `offset + code + reloc`。
只靠「找到 `CD 3F`」會把 resident code 裡剛好出現的 bytes 誤判成 overlay。

## 建庫流程

1. 解容器，取出每段 code 與 **entry stub 的 handler-local offset 清單**。
2. 每段 code 單獨存檔，以 `idat -A -B -p8086 -b0 <段>.bin` 建庫
   （16-bit、base 0；binary loader 可能給 32-bit segment，腳本裡要
   `seg.bitness = 0` 再 `update()`，否則整段解碼錯）。
3. **種 entry point**：對每個 handler offset 做 `del_items` → `create_insn`
   → `add_func`，然後 `ida_auto.auto_wait()` 讓 near call 自然傳染。
4. **另外補 code offset 0**：unit 初始化程序固定在那裡，而它**不在 entry stub
   表內**。忘了補，每段都會少一塊。
5. 有除錯符號的話，把符號位址也當種子（見下節）。

實測效果：DOS 側從 1 個函式變成 1,344 個；補上符號種子後 PC-98 從 1,421
變成 1,481。

殘量要如實記帳：種子失敗數（entry 指到已屬其他函式的位址）、未定義 byte 數。
**不要用線性掃描硬湊函式**——那會製造假函式，讓「還剩多少沒看」的分母虛胖。

## Borland 除錯符號：最大的槓桿

部分版本的 executable 在 MZ load image 之後附了 legacy Borland 除錯表
（header magic `0x52FB`）。CoAB 的 PC-98 版有，DOS 版沒有——**同一款遊戲的
不同平台版本，有無符號可以完全不同，值得每個版本都試一次**。

那張表給的是：

- **module 表**＝原始的 Turbo Pascal 單元名（`INTERPET`、`COMBAT`、`SPELLS`、
  `TACMAP`、`THREED`、`LOS`、`OVERLAND`…）。等於拿到整個遊戲的架構。
- **symbol 表**＝函式與全域變數名，位址是 `segment:offset`。
- **type／member 表**＝record 版面與欄位名。資料結構還原通常最貴，這裡直接給。

關鍵接法：**符號位址的 segment 等於該 overlay 的 control segment，offset 等於
overlay-local code offset**。control segment 由
`(control record 的 file offset − MZ header 大小) / 16` 得到。實測 332 個
overlay-code 符號有 297 個（89%）直接落在 IDA 的函式起點，其餘多是 code
offset 0 的 unit 初始化。

`LOADxxx`／`INITxxx` 這種在 code offset 0 的符號直接給出 **overlay ↔ 單元名**
的對應。

## 跨平台／跨版本搬名字

同一份原始碼編出的兩個版本，**stub offset 與 entry index 相同，code offset 不同**
（CoAB 實測 36 段中 29 段 entry count 完全相同）。所以：

- ✅ 用 **entry index** 把有符號版本的名字搬到無符號版本 → `strong inference`
- ❌ 用 **code offset** 對應 → 整片查不到（`READVAR` 在 PC-98 是 `008Eh`、
  DOS 是 `0034h`）
- ❌ 用「位址 ＋ 固定偏移」換算 → 偏移會隨模組增長，不是常數

搬過去之後仍然只是候選語意，個別函式要各自證明。

## 解 far call：stub offset → entry index → 符號名

跨 unit 呼叫長這樣：`9A <off:u16> <seg:u16>`（far call ptr16:16）。**目標是
被呼叫 overlay 的 control block stub offset，不是 code offset**，所以直接拿
去查函式表會查不到。解法：

```text
far call 0062:0025
  → segment 0062h 是哪一段 overlay 的 control segment
  → stub offset 0025h → entry index (0025h − 20h) / 5 = 1
  → 該 overlay 的 entry 1 → code offset
  → 符號名
```

這條鏈一通，「這個函式呼叫了哪些共用 routine 幾次」就變成可以直接統計的
訊號，非常適合拿來交叉驗證既有的規格假設。

## ⛔ 六個會產生「假結論」的坑（都實際踩過）

這些的共同點是：**結果看起來自洽、有數字、可重跑，但是錯的。**

1. **只比對 stub offset、不比對 segment。** `014A:002A` 被當成 `0062:002A`，
   於是完全無關的 overlay 的呼叫被算進統計。Borland 的 stub offset 只有
   `20h + 5i` 這種值，撞號是常態不是意外。
2. **正規表示式把立即數的 `h` 後綴吃掉。** `([0-9A-Fa-f]+)h?` 讓
   `cmp al, 10h` 變成十進位 `10`（＝`0Ah`）。凡是全為數字的十六進位值都會
   算錯，而且錯出來的表仍然自洽。後綴要留給解析函式判斷。
3. **信任 IDA 的函式邊界。** 個位數 bytes 的「函式」幾乎一定是邊界建錯。
   實測 `ON GOTO` handler 在一個平台是 3 bytes、另一平台是 149 bytes。
   要逐指令讀就**指定位址範圍**，不要用函式邊界。
4. **用「排序後取前一個起點」猜函式區間。** 函式在位址上並不連續，後面
   函式的指令會被算到前一個頭上。用 IDA 的實際 chunk 範圍。
5. **用「數量最多的分支＝預設分支」猜 default。** 當每個分支各只有一個值時，
   這個啟發式會把第一筆真的值當成 default 刪掉。改用「走到 epilogue 才算
   未識別」這種有語意的判準。
6. **拿呼叫次數當 arity。** 「取用第 i 個 operand」的 routine 可以被呼叫零次
   或多次，與宣稱的 operand 數量無關。真正的訊號是**解碼器的參數**。

第 6 點是通則：**統計某個 helper 被呼叫幾次之前，先確認那個 helper 的語意
是不是「每次一個」。** 否則會做出一張很有說服力的錯表。

## 符號執行小比較鏈：可靠地解分派表

Turbo Pascal 編出來的 dispatcher 常是線性 `cmp／jz／call` 鏈而不是跳表，
巢狀條件會讓「掃 `cmp` 後面接哪個 `call`」的字串比對漏掉一半。

可靠做法是**對每個候選值各跑一次符號執行**：只認 `cmp`＋條件跳躍、無條件
跳躍、載入被追蹤值的指令，走到第一個 `call` 就停；**分支目標一律取 IDA 的
code ref，不從助憶碼字串解析標籤名**；遇到不在支援集合內的指令就停下並
標記為「需人工讀」。

「需人工讀 = 0」是必要條件不是充分條件（見坑 2）。收工前一定要**用原始
bytes 手動抽驗至少兩筆**。

## 覆蓋台帳：讓「還剩多少沒看」可回答

逐題反組譯（每次寫一支腳本回答當下那一題）累積再久，也答不出剩餘量。
建議把全掃結果變成一份台帳，每個函式三選一：

- `已解讀`＋推論等級＋引用規格
- `不阻塞`＋**具體理由**（不是「看起來不重要」）
- `待解讀`（預設）

**狀態只能來自明確記錄，不能由關鍵字比對產生**——否則「文件裡剛好出現同一個
十六進位數字」會把待解讀的函式自動升級成已解讀。分母是全掃的函式全集，
可重跑重生。

## Turbo Pascal RTL 的亂數（跨作品直接沿用）

所有 Borland Turbo Pascal 編譯的遊戲共用同一個 RTL RNG。在 CoAB 兩個平台上
逐指令讀出並以 20 萬組種子數值驗證：

```text
RandSeed := (RandSeed * 134775813 + 1) mod 2^32      ← 134775813 = 08088405h
Random(n) := if n = 0 then 0 else (RandSeed shr 16) mod n
Randomize  := RandSeed := INT 21h AH=2Ch 的系統時間
```

**怎麼在反組譯裡認出它**——不要搜 `08088405h`，程式裡沒有這個常數。8086 沒有
32-bit 乘法，RTL 只用 `mul cs:xxxx` 乘低位字 `8405h`，高位字 `0808h` 由一串
`shl` 加上 **`add ch, cl`／`add dh, bl`**（用 8-bit 加法製造 `<<8` 的部分積）
湊出來。看到「`mul` 一個 `8405h` 常數 ＋ 一串 `shl` ＋ `add ch, cl`」這個形狀，
就是它。函式本體 54 bytes，結尾 `add ax,1 / adc dx,0`。

兩個容易寫錯的地方：

1. **`Random` 只用高 16 位**。`call` 之後緊接 `xor ax, ax` 丟掉低位字，
   接著 `xchg ax, dx` ／ `div bx` ／ `xchg ax, dx`。漏看那條 `xor` 會推成
   「32-bit 亂數對 n 取餘數」，序列完全對不上。
2. **取模偏差是原版行為**。`(seed shr 16) mod 6` 的六個結果不等機率；
   remake 把它「修正」成均勻分佈，就重現不了原版的骰子序列。

驗收方式：種子設 0，`Random(6)+1` 的前十次應為
`1, 5, 6, 5, 1, 2, 6, 2, 6, 3`。

## 玩家可見文字在 code 段裡，不在資料檔

Turbo Pascal 的 string 常數是「長度位元組 ＋ 內容」，編譯後**直接躺在 code
段**，用 `mov di, offset X` ＋ `push cs` 把位址傳出去。所以在資料檔裡找不到
大部分 UI 與訊息文字是正常的——它們在 `.OVR` 的 overlay code 內。

掃描要兩條同時成立，只靠形狀會把大量普通資料誤讀成字串：

1. 位址 `i` 的位元組是長度 `n`，其後 `n` 個位元組全是合法字元
   （日文版另外接受 Shift-JIS 雙位元組序列與半形片假名）。
2. 某條 `BF lo hi`（`mov di, imm16`）的立即值等於 `i`——**有指令指著它**。

代價是用其他方式取址的字串掃不到，所以結果是下界不是全集，不得由缺席推論
不存在。

**跨語言版本對照不能按出現順序。** 英文有單複數分歧、日文沒有，同一模組的
條數就不同，按序號對會整段錯位。正確做法是走已配對的函式（助憶碼序列相同）
再比 `mov di` 的**第幾個引用**——同一條指令必然指同一件事。

對到之後會發現**在地化版本常常不是逐句直譯**：CoAB 的 `Not with that weapon`
（武器不對）在 PC-98 版是「そこへは進めない」（過不去）。配對沒錯，是譯法
換了。做中文化時以**原作語言版本**為準，另一個語言版本只用來理解語境。

## 32 bytes 的 set 常數

看到「函式前方剛好 32 bytes 的常數 ＋ 一個帶該位址與一個 byte 的 far call」，
那是 Turbo Pascal 的 `set of byte`（256 bits）與 RTL 的 set-in 測試。
直接把 32 bytes 展開成成員清單即可，不必追那個 far call。CoAB 用它表達
「哪些 effect 需要走完整條鏈」「哪些狀態可以被治療」這類規則表。
