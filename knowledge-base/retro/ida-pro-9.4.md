# IDA Pro 9.4：本機環境與 16-bit DOS 逆向實務

> 取代 `ida94b1-skill.md`（那份寫的是通用 docker-compose 流程與 IDAPython，
> 與本機實際環境不符，見下方「實測結論」）。

## 本機環境（`[HARD]` 記住這三行）

```
image 來源：~/ida_94_official/dist
基底 image：ida-pro-9.4-ver2 / ida-pro-9.4-ver3
要用 IDAPython：ida-pro-9.4-idapython:py312-v1   ← 見 §「IDAPython」
```

不需要 docker compose，直接 `docker run`。專案裡一律包成 `tools/ida.sh`：

```bash
docker run --rm -v "$WORK:/work" -v "$ROOT/tools:/work/tools:ro" -w /work \
  ida-pro-9.4-ver2 idat -A -B WAR.EXE          # 產 .i64 + .asm
```

`idat` 是 headless 的那支（`ida` 是 GUI）。`-A` 自動模式、`-B` 批次產出。

## ⭐ 實測結論（能力矩陣）

| 能力 | 狀態 |
|---|---|
| **IDAPython**（`-S/work/tools/x.py`）| ✅ 可用，**但只在修好的 image 上**，見下一節 |
| **IDC 腳本**（`-S/work/tools/x.idc`）| ✅ 可用（任何 image），當退路 |
| **Hex-Rays decompiler** | ❌ 16-bit real mode 本來就不支援 |
| 產 `.asm` / `.i64` | ✅ |

---

## ⭐⭐ IDAPython：能用，但基底 image 會**靜默失敗**（2026-08-13 實測）

**優先寫 IDAPython，不要寫 IDC。** 有 `idautils` / `ida_funcs` / `ida_xref` 這些模組，
比 IDC 好寫太多；`~/cht/civ1/tools/ida/` 有三十幾支 `export_*.py` 可以直接抄形狀。

### 失敗長什麼樣（這是最會浪費時間的部分）

**沒有錯誤訊息、沒有 stdout、沒有 stderr、沒有輸出檔。** 實測 `ida-pro-9.4-ver3:latest`
跑 IDAPython 腳本的完整輸出是**空字串**，rc=1。
這與「腳本寫錯」「路徑打錯」「IDA 沒裝 Python」長得一模一樣。

**判準：在下「IDAPython 在這個環境不能用」的結論之前，一定要換一顆 image 做正對照。**
零輸出只證明「這個組合不成立」，不能推廣成「這個工具不能用」——
這正是 `~/diagnosis-notes/docs/02-query-returned-empty/` 說的：
下「不存在」的結論前先做正對照，差別只在這裡問的是「工具壞了還是這顆 image 壞了」。

### 兩個獨立的根因，要分開修

**根因一:基底 image 沒有 `libpython3.12.so`。**
只有 Python 3.12 的 interpreter 與 stdlib，缺 shared library，IDAPython 載不起來。
（某些基底的 `ida.reg` 還留著主機 Python 3.14 的絕對路徑，指向不存在的 uv 目錄。）

**根因二:`idapyswitch` 把選定的 interpreter 寫進 `$HOME/.idapro`。**
所以**必須以最終執行身分跑它**。用 root 跑會寫進 `/root/.idapro`，
之後以 `-u 1000:1000` 執行時讀不到 —— 於是又退回同一種靜默失敗。
**只修根因一、忘了根因二，症狀與完全沒修一模一樣。**

### 實測矩陣（同一支探針、同一個輸入檔）

| image | `-u $(id -u)` | 不加 `-u` |
|---|---|---|
| `ida-pro-9.4-ver3:latest`（基底）| ❌ | ❌ |
| `ida-pro-9.4-ver2:latest`（基底）| ❌ | ❌ |
| `ida-pro-9.4-ver2:uidfix-v1` | ❌ | ❌ |
| `ida-pro-9.4-ver2:civ1-py312-v1` | ❌ | ✅ |
| **`ida-pro-9.4-idapython:py312-v1`** | ✅ | ✅ |
| `ida-pro-9.4-ver3:py312-v1`（同一份 Dockerfile 的舊 tag）| ✅ | ✅ |

`civ1-py312-v1` 只修了根因一（`idapyswitch` 以 root 跑），所以加 `-u` 就壞。
**`uidfix-v1` 這個名字會誤導 —— 它修的不是這個問題。**

### 用哪一顆

```
ida-pro-9.4-idapython:py312-v1
```

Dockerfile 保存在 `~/.claude/knowledge-base/retro/assets/ida-pro-9.4-idapython.Dockerfile`
（原始來源 `~/cht/pto2-remake/tools/docker/ida/Dockerfile`），重建：

```sh
docker build -t ida-pro-9.4-idapython:py312-v1 \
  -f ~/.claude/knowledge-base/retro/assets/ida-pro-9.4-idapython.Dockerfile \
  ~/.claude/knowledge-base/retro/assets
```

兩個容易踩的細節：Ubuntu 24.04 的套件名是 **`libpython3.12t64`**（`t64` 是 64-bit
`time_t` 轉換）不是 `libpython3.12`；`idapyswitch` 那一步要在 `USER 1000:1000` **之後**。

### 三十秒驗證(換 image、換機器、換專案都先跑這個)

寫一支只做「數函式、寫 JSON」的探針，確認輸出檔存在且欄位對。
**不要靠 exit code** —— 見下一節。

### headless 的輸出不進 stdout（IDC 與 IDAPython 都一樣）

`print` 與 `Message()` 在 `idat -A` 底下看不到。**腳本一律把結果寫檔**，
而且收工前要**驗檔案存在、非空、schema 對、輸入檔 SHA-256 對**。

⚠ **exit code 完全不能當證據**：實測同一種「沒有輸出」的失敗，
在不同 image 上分別回 rc=0 與 rc=1。rc=0 不代表腳本跑過，rc=1 也不一定是語法錯。
**唯一可信的訊號是輸出檔本身。**

IDAPython 版的骨架（`ida_pro.qexit(0)` 那行不能省，否則 headless 會掛在那）：

```python
import json, sys, idautils, ida_auto, ida_pro
ida_auto.auto_wait()                       # 等自動分析跑完，等同 IDC 的 Wait()
with open(sys.argv[1], "w") as f:          # -S"script.py /work/out.json" 的參數
    json.dump({"funcs": len(list(idautils.Functions()))}, f)
ida_pro.qexit(0)
```

IDC 版：

```c
out = fopen("/work/result.txt", "w");
fprintf(out, "...");
fclose(out);
```

不寫檔就等於沒跑——會安靜地什麼都沒有，exit code 還是 0。

## ⭐⭐ 最重要的一課：不要 grep `.asm`，要查資料庫

`.asm` 是攤平的文字，**它沒有交叉參考圖**。想知道「這個全域變數是什麼」，
只 grep `.asm` 的話只能從呼叫端的參數順序反推——那是間接證據，會推錯。

真實案例（大時代的故事專案）：`word_64944` 被從「呼叫端參數順序」推成
「第二方的代表單位」，後來出現反證只好整條退回未解。
改用 IDA 的 xref 圖一次就問出答案：**`mul word_64944` 出現 14 次，
乘的是將領記錄大小 0x21——它是一個單位 ID**。

### 查 xref 的正確寫法

```c
#include <idc.idc>
static main() {
    auto ea, x, t, kind;
    Wait();                                   // 一定要等自動分析跑完
    ea = get_name_ea_simple("word_64944");
    for (x = get_first_dref_to(ea); x != BADADDR; x = get_next_dref_to(ea, x)) {
        t = XrefType();                       // ← 用 IDA 標的型別
        if (t == 2)      kind = "寫";          // dr_W
        else if (t == 1) kind = "取址";        // dr_O
        else             kind = "讀";          // dr_R
        // GetDisasm(x)、get_func_name(x) 取指令與所屬函式
    }
}
```

IDAPython 版（同一件事，短很多）：

```python
import idautils, idc, ida_funcs, ida_name
ea = ida_name.get_name_ea(idc.BADADDR, "word_64944")
for x in idautils.DataRefsTo(ea):          # 只要位址就用這個
    print(hex(x), idc.GetDisasm(x), ida_funcs.get_func_name(x))

# 要讀寫型別就走 XrefsTo，看 xref.type（dr_R=1? 以 XrefType 常數為準，不要憑記憶）
for xref in idautils.XrefsTo(ea):
    print(hex(xref.frm), xref.type, xref.iscode)
```

### ⛔ 讀寫判定連錯兩次的教訓

判定「這條 xref 是讀還是寫」時，**不要自己猜指令語意**：

| 寫法 | 為什麼錯 |
|---|---|
| `strstr(d, "mov " + name + ",")` | IDA 助憶碼後面補的是**多個空格**，`mov     word_64944, dx` 漏掉 |
| `print_operand(x, 0) == name` | `push` 的第 0 個運算元是**來源**不是目的，於是 30 個 `push` 全被判成寫 |
| `XrefType()` | ✅ IDA 建庫時就標好了，直接問 |

兩次都是在重造 IDA 已經有的東西。**先找 API，再考慮自己算。**

### 間接寫入抓不到

xref 只涵蓋直接參考。Turbo Pascal／Borland C 常見的
`ptr = &x` → `es:[di] = v` 這種間接寫入**不會出現在 xref 裡**。
症狀是「讀 74 處、寫 1 處」——看到寫入數異常少，先去看「取位址」那幾筆，
間接寫入一定是從那裡開始的。

## ⛔⛔ 腳本崩掉會**弄壞 `.i64`**，而症狀看起來像環境壞了（2026-08-02）

（坑 1 只發生在 IDC；**坑 2 對 IDC 與 IDAPython 都成立**。）

兩個坑連在一起，各自都會浪費半小時，合起來會讓人開始懷疑 docker image。

### 坑 1：IDC 少了 `#include <idc.idc>` 會**安靜地 exit 1**

沒有錯誤訊息、沒有輸出檔、stderr 一個字都沒有。就只是 exit 1。

```c
#include <idc.idc>      // ← 少這行 = 整支腳本安靜死掉

static main() { ... }
```

⚠️ 這與「headless 的 `print` 不進 stdout」是**不同的**坑：那個是 exit 0 卻沒輸出，
這個是 exit 1 且沒輸出。看到 exit 1，先檢查 include，不要先懷疑語法。

### 坑 2：崩掉的那次會把 `.i64` 留在不可開啟的狀態

之後**任何**針對那個 `.i64` 的指令都會回：

```
Failed to initialize IDA as library (error code 4)
Check ida.log!
```

**這個訊息會誤導人**——它讀起來像授權失效或 image 壞掉，
而且 `idat --version` 也會回同一族訊息（error code 2），
看起來就像「IDA 整個不能用了」。實際上 `ida.log` **根本不存在**，
`find / -name ida.log` 找不到任何東西。

**判斷方法（30 秒）：拿另一個 `.i64` 跑同一支已知可用的腳本。**

```sh
tools/ida.sh raw idat -A "-S/work/tools/ida_xref.idc <某符號>" GRTE.EXE.i64
```

- 別的 `.i64` 正常 → 是那個 `.i64` 壞了，**刪掉重跑 `analyze`**（幾分鐘）
- 全部都壞 → 才輪到懷疑 image／授權

> **一般化**：headless 工具回報「初始化失敗」時，先問「是工具壞了還是**這一份輸入**壞了」。
> 差別在於有沒有第二份輸入可以當對照——這就是
> `~/diagnosis-notes/docs/02-query-returned-empty/` 說的**正對照**，
> 只是換到了「工具壞了嗎」這個問題上。

## ⛔⛔ 16-bit：IDA 的線性位址**不會出現在 `.asm` 文字裡**（2026-08-02）

想確認「有沒有程式碼碰某塊記憶體」時，很自然會 grep `.asm` 找那個位址。
**在 16-bit 專案這是假陰性製造機。**

`byte_6EFAA` 這種符號名是從 IDA 資料庫的**線性位址**來的，但反組譯文字顯示的是
**`segment:offset`**。實測：整份 `WAR.EXE.asm`（375 KB 執行檔、1098 函式）
**連一個 5 位十六進位常數都沒有**。所以

```sh
grep -oP '\b6[0-9A-F]{4}h\b' WAR.EXE.asm     # → 0 筆，永遠 0 筆
```

零命中與「真的沒人碰」長得一模一樣。

> **正對照救了這次**：先問「這個 grep 抓得到任何一個裸位址嗎」，
> 答案是零，才發現查法本身是壞的。
> （`~/diagnosis-notes/docs/02-query-returned-empty/`：下「不存在」的結論前先做正對照。）

### 正確的問法：逐 byte 查 xref 圖

`ida_xref.idc` 只能查**一個具名符號**，而結構化的記憶體通常只有起點有名字——
中間的 `base + i*stride + col` 被 IDA 標成對「某個無名位址」的參考，
查基址什麼都查不到。

對整段範圍**逐 byte** 呼叫 `get_first_dref_to`／`get_next_dref_to`
（專案裡的 `tools/ida_range_xref.idc`）。1,416 個位址跑幾秒，
比「掃二十萬條指令的立即數」快兩個數量級——後者實測跑 45 分鐘還沒輸出。

## 掃立即數：xref 圖看不到的那一半

`tools/ida_xref.idc` 只讀 IDA 的 xref 圖，而 xref 圖只涵蓋 IDA **認得出來**的參考。
把位址當純數字算的程式碼（`mov ax, 6EFAAh`、或位址被拆成兩次加法）在圖上是空的，
症狀就是「這塊記憶體只有存檔讀寫碰過，遊戲中沒人用」——那通常不是真的。

補法是掃全部指令的運算元數值，落在指定範圍就報出來
（專案裡的 `tools/ida_range_refs.idc`，輸出帶「+偏移」欄好判斷是不是真的落在結構裡）。
⚠️ 慢，要跑幾分鐘；而且**立即數與位址同值也會中**，要靠偏移欄自己過濾。

## Turbo Pascal / Borland C 的辨識重點

- **Pascal 呼叫慣例**：參數由左至右壓棧、被呼叫者清棧（`retn N`）。
  用 C 的直覺讀參數順序會全部反過來。
- **巢狀程序**：`push bp` / `call sub_X`，被呼叫者用 `ss:[di+4]`、`ss:[di+6]`
  取回**外層**的參數。看到「只有一個 `arg_0` 卻在裡面 `ss:[di+n]` 亂取」，
  那是巢狀程序，`arg_0` 是外層的 bp——不是「參數很少」。
- **48-bit Real 常數**：三個 push（AX/BX/DX）。byte0 = 指數，bytes1-5 = 尾數
  （低位先、隱含最高位）。值 = `±(mantissa|1<<39)/2^39 × 2^(exp−0x81)`。
  寄存器形式 AL=exp, AH=m[0], BL=m[1], BH=m[2], DL=m[3], DH=m[4]。
- **32-bit 值拆兩半**：相鄰的兩個 word，各被 `cmp` 一次就是一個 32-bit 比較。
  看到兩個相鄰位址各比較一次，**先想 32-bit**，不要當成兩個獨立欄位。
- Graph unit 的呼叫（`PUTIMAGE`／`SETRGBPALETTE`）IDA 會直接認出名字。

## Borland／Turbo Pascal overlay（`.OVR`）

raw overlay 直接載入 IDA **只會得到 0–1 個函式**（沒有 MZ header、沒有 entry
point），而症狀與「這個檔案沒有程式碼」一模一樣。entry point 全在 resident
的 `CD 3F` five-byte stub 裡，必須自己種。格式、建庫流程、Borland 除錯符號
的接法與六個會產生「自洽但錯」結論的坑，見
[`borland-tpov-overlay-re.md`](borland-tpov-overlay-re.md)。

## PKLITE 打包

IDA 9.4 對部分 PKLITE 執行檔**會自動解開**（實測 `GRT.EXE`／`GRTE.EXE` 可以，
`SDFA.EXE` 不行——後者解出 0 函式 0 字串就是沒解開的徵兆）。
未打包的檔案直接進 IDA，而且通常是最大的那個，從它開始最省事。

## 工作紀律

- **每份筆記標「輸入檔 + SHA-256 + IDA 位址」**。位址一律寫 IDA database 的
  linear address；同時引用 Ghidra 位址時要明講是哪一套。
- `.i64`、`.asm`、解包後的 binary **全部 gitignore**。
- **讀任何 `sub_XXXXX` 之前先查函式索引**。專案超過二三十份反組譯筆記之後，
  光靠記憶一定會重讀已經解過的函式。做法：掃 `docs/**/*.md` 抽出所有
  `sub_[0-9A-F]+` 產生一份索引表（大時代的故事專案是
  `tools/gen_func_index.py` → `docs/re/00-function-index.md`，392 個函式）。
- **不要用 `grep -v` 過濾組合語言**。為了讓輸出短而濾掉 `mov di, ax`／
  `add di, ax`／`shl di, 1` 這類「看起來是樣板」的行，濾掉的正是**索引計算**，
  會把 `旗標[f(x)] = 1` 讀成 `旗標[0] = 1`。要短就用 `sed -n` 取行段。
- **「唯一」「只有一處」沒有全檔掃描佐證就不要寫。** 憑印象寫的「唯一」
  在大時代的故事專案錯過兩次（實際有 6 處）。

## 授權與邊界

- 只做靜態分析、格式保存與互通性研究。不協助破解 DRM、繞過授權、修改付費驗證。
- license 只唯讀掛載，不出現在 log、截圖或報告裡。
- 不在 container 內執行老遊戲；IDA 只讀檔案。
- 不把 `/home`、SSH agent 或整個 host filesystem 掛進 container。
- **不碰共用的 docker 資源**：禁止 `docker image prune`／`system prune`／
  `volume prune`／`builder prune`／`rmi`／`container prune`。
  這台機器同時放著多個客戶專案的 image，誤刪過一次事故。

## 批次操作要合併成單次 `idat` 執行

對同一個 `.i64` 連續快速開關會把資料庫弄壞:

```
Failed to initialize IDA as library (error code 4)
```

在一個專案裡踩過**四次**,每次都發生在一連串循序的 `idat` 執行之後
(例如「for 迴圈 dump 19 個位址」)。第 5 次左右開始失敗。

⚠ **不限於同一支腳本的迴圈** —— 第四次是不同腳本接連執行
(`find_dsref` → `imm_range`)。**對同一個 `.i64` 的任何連續執行都要當成風險。**

**修法:寫一支一次處理多個目標的腳本**(`dump_many.py` 那種,
參數用 `0x10303:0x18 0x105B4:0x18 …` 的形式),把 N 次執行縮成 1 次。
除了避開這個問題,也快得多(每次 `idat` 啟動有固定成本)。

壞掉之後的處置照本文既有的正對照程序:先確認別的 `.i64` 正常,
再刪掉重建(`analyze` + 重跑解鎖腳本)。

## headless 批次的四個靜默陷阱

跑 IDAPython 批次流程時，下面四件事**都不會報錯**，只會讓結果悄悄變成錯的：

1. **`ida_pro.qexit()` 不儲存資料庫。** 腳本裡 `add_func`／改名／加註解全部
   只活在那次執行的記憶體裡。要留下來必須顯式呼叫
   `ida_loader.save_database(ida_loader.get_path(ida_loader.PATH_TYPE_IDB), 0)`。
2. **輸出路徑落在掛載點外會被丟棄。** 容器裡 `/work/../out/x.json` 是 `/out`，
   不存在，寫入無聲失敗——目標檔的時間戳完全不動，看起來像「跑完了但沒變」。
   收工前一律驗檔案存在、非空、**且時間戳有更新**。
3. **把 `x.bin.i64` 當輸入交給 `idat`，會從 `x.bin` 重新載入並覆蓋資料庫。**
   先前 seed 進去的函式全沒了。要在既有資料庫上做純讀取的匯出，就只跑匯出
   腳本，不要再帶 loader 參數（`-p8086 -b0` 這類）讓它重新分析。
4. **不同腳本產生的 JSON 欄位不一樣。** 用 A 腳本產生、改用 B 腳本重產，
   下游 join 的鍵可能就不見了（模組名從 `overlay-25` 變成 `overlay-25.bin`）。
   下游的統計數字會安靜地掉一半而沒有任何錯誤輸出。

**通則：分母與判讀分開產生再 join 時，join 失敗只表現成「數字變了」。**
每次動到匯出流程，都要拿動之前的計數逐項對照。

## `add_func` 對完好的 prologue 也會失敗

位址已經是 code、不屬於任何函式、開頭是漂亮的 `55 89 e5 83 ec xx`，
`ida_funcs.add_func(ea)` 仍可能回 false——IDA 決定不了函式**結尾**（自動分析
根本沒走到那個區域）。

解法是先求邊界再建：

```python
bounds = ida_funcs.func_t(ea)
if ida_funcs.find_func_bounds(bounds, ida_funcs.FIND_FUNC_DEFINE) == ida_funcs.FIND_FUNC_OK:
    ida_funcs.add_func(ea, bounds.end_ea)
else:
    ida_funcs.add_func(ea, 下一個已知邊界)
```

另外 IDA 9.4 的 API 位置：`create_insn` 在 **`ida_ua`** 不在 `ida_bytes`；
列舉函式用 `idautils.Functions()`，`idc.Functions` 已經不存在。
