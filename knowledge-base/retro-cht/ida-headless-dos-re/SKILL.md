---
name: ida-headless-dos-re
description: 用 docker 化的 IDA Pro 9.4 headless 反組譯 16 位元 DOS 老遊戲執行檔,重點在「讓 IDAPython 真的能跑」與「別把零輸出讀成不存在」。觸發:「IDA headless」「idat 批次分析」「IDAPython 沒有輸出」「IDAPython 在容器裡不能用」「idapyswitch」「libpython3.12 找不到」「IDA 產不出 .i64」「Failed to initialize IDA as library (error code 4)」「16-bit real mode 沒有反編譯」「grep .asm 找位址找不到」「怎麼查誰讀寫這個全域變數」。
---

# IDA Pro 9.4 Headless:16 位元 DOS 執行檔逆向

> 來源:2026-07～08 多個 1980s–90s DOS 遊戲逆向專案的實測。
> 與 `ghidra-headless-dos-re` 互補 —— 兩者擇一即可,不要同時維護兩套位址體系。

**核心結論**:IDA 對 16-bit real mode **沒有反編譯器**(只有組語),這反而擋掉了
Ghidra「靜默捏造控制流」那一類坑;而真正會吃掉時間的不是反組譯本身,
是**工具鏈的靜默失敗** —— 見 §2。

## 何時用

反組譯 DOS 老遊戲的 `.EXE` / `.COM` / 自訂副檔名主程式;要函式清單、字串表、
交叉參考圖;要回答「誰讀寫這個全域變數」「這個資料結構被誰用」。

---

## 1. 基本用法

`idat` 是 headless 的那支(`ida` 是 GUI)。一律包成專案裡的 `tools/ida.sh`:

```sh
docker run --rm --network none --memory 2g --cpus 2 --pids-limit 256 \
  -u "$(id -u):$(id -g)" \
  -v "$WORK:/work" -v "$ROOT/tools:/work/tools:ro" -w /work \
  "$IMAGE" idat -A -B TARGET.EXE          # -A 自動模式、-B 批次,產 .i64 + .asm
```

原版執行檔唯讀掛載,**複製到工作目錄再分析**,不要就地產生 `.i64`。
`.i64` / `.asm` / 解包後的 binary 全部 gitignore。

---

## 2. ⭐⭐ 讓 IDAPython 能動(最會浪費時間的一節)

**優先寫 IDAPython,不要寫 IDC。** 有 `idautils` / `ida_funcs` / `ida_xref` 這些模組,
比 IDC 好寫太多。但預設的 IDA docker image **多半跑不起來 IDAPython**,
而且失敗的樣子會讓人往完全錯的方向修。

### 失敗長什麼樣

**沒有錯誤訊息、沒有 stdout、沒有 stderr、沒有輸出檔。** 實測某基底 image 的完整輸出
是空字串。這與「腳本寫錯」「路徑打錯」「IDA 沒裝 Python」長得一模一樣。

⚠ **exit code 不能當證據**:同一種「沒有輸出」的失敗,在不同 image 上分別回 rc=0 與 rc=1。
**唯一可信的訊號是輸出檔本身。**

### 兩個獨立的根因,要一起修

| 根因 | 症狀 | 修法 |
|---|---|---|
| ① 缺 `libpython3.x.so` | image 只有 interpreter 與 stdlib,沒有 shared library | `apt-get install libpython3.12t64`(Ubuntu 24.04 的套件名有 `t64`,是 64-bit `time_t` 轉換,不是 `libpython3.12`)|
| ② `idapyswitch` 的選擇寫進 `$HOME/.idapro` | 用 root 跑它會寫進 `/root/.idapro`,之後以 `-u 1000` 執行讀不到 | **以最終執行身分跑 `idapyswitch`**,不要用 root |

**只修 ① 忘了 ②,症狀與完全沒修一模一樣。** 這是最容易卡住的地方:
會看到「我明明裝了 libpython 啊」,然後開始懷疑授權、懷疑 image、懷疑 IDA 版本。

### 可用的 Dockerfile

```dockerfile
ARG BASE_IMAGE=<你的 IDA 9.4 基底 image>
FROM ${BASE_IMAGE}

USER root
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpython3.12t64 \
    && rm -rf /var/lib/apt/lists/*
RUN install -d -m 0755 -o 1000 -g 1000 /home/ubuntu/.idapro

USER 1000:1000
ENV HOME=/home/ubuntu
RUN /opt/ida-pro-9.4/idapyswitch --force-path \
        /usr/lib/x86_64-linux-gnu/libpython3.12.so.1.0

WORKDIR /work
```

順序不能換:`idapyswitch` 那一步必須在 `USER 1000:1000` **之後**。

### 三十秒驗證(換 image、換機器、換專案都先跑)

寫一支只做「數函式、寫 JSON」的探針,確認**輸出檔存在且欄位對**:

```python
import json, sys, idautils, idaapi, ida_auto, ida_pro
ida_auto.auto_wait()                       # 等自動分析,等同 IDC 的 Wait()
with open(sys.argv[1], "w") as f:          # 對應 -S"probe.py /work/out.json"
    json.dump({
        "python": sys.version.split()[0],
        "ida": idaapi.get_kernel_version(),
        "funcs": len(list(idautils.Functions())),
    }, f)
ida_pro.qexit(0)                           # 不能省,否則 headless 會掛在那
```

**在下「IDAPython 在這個環境不能用」的結論之前,一定要換一顆 image 做正對照。**
零輸出只證明「這個組合不成立」,不能推廣成「這個工具不能用」。

### IDC 當退路時的兩個坑

- **少了 `#include <idc.idc>` 會安靜地 exit 1** —— 沒有錯誤訊息、沒有輸出。
  看到 exit 1 先檢查 include,不要先懷疑語法。
- **腳本崩掉那次會把 `.i64` 留在不可開啟狀態**(IDAPython 也會)。之後任何針對那個
  `.i64` 的指令都回 `Failed to initialize IDA as library (error code 4)`,
  訊息讀起來像授權失效或 image 壞掉,而它提到的 `ida.log` 根本不存在。
  **判別法:拿另一個 `.i64` 跑同一支已知可用的腳本。** 別的正常 → 刪掉那個 `.i64`
  重跑分析就好。

---

## 3. ⭐ 不要 grep `.asm`,要查資料庫

`.asm` 是攤平的文字,**它沒有交叉參考圖**。想知道「這個全域變數是什麼」,
只 grep `.asm` 的話只能從呼叫端的參數順序反推 —— 那是間接證據,會推錯。

真實案例:某個全域變數被從「呼叫端參數順序」推成「第二方的代表單位」,
後來出現反證只好整條退回未解。改用 xref 圖一次就問出答案:
**它被 `mul` 了 14 次,乘的是將領記錄大小 —— 它是一個單位 ID**。

```python
import idautils, idc, ida_funcs, ida_name
ea = ida_name.get_name_ea(idc.BADADDR, "word_64944")
for xref in idautils.XrefsTo(ea):
    print(hex(xref.frm), xref.type, idc.GetDisasm(xref.frm),
          ida_funcs.get_func_name(xref.frm))
```

### ⛔ 讀寫判定不要自己猜指令語意

| 寫法 | 為什麼錯 |
|---|---|
| 比對 `"mov " + name + ","` | IDA 助憶碼後面補的是**多個空格**,`mov     word_x, dx` 會漏掉 |
| `print_operand(x, 0) == name` | `push` 的第 0 個運算元是**來源**不是目的,於是所有 `push` 都被判成寫 |
| **問 IDA 標好的 xref 型別** | ✅ 建庫時就標好了 |

兩種錯法都是在重造 IDA 已經有的東西。**先找 API,再考慮自己算。**

### 間接寫入抓不到

xref 只涵蓋直接參考。Turbo Pascal / Borland C 常見的 `ptr = &x` → `es:[di] = v`
這種間接寫入**不會出現在 xref 裡**。症狀是「讀 74 處、寫 1 處」——
看到寫入數異常少,先去看「取位址」那幾筆。

---

## 4. ⛔ 16-bit:線性位址**不會出現在 `.asm` 文字裡**

想確認「有沒有程式碼碰某塊記憶體」時,很自然會 grep `.asm` 找那個位址。
**在 16-bit 專案這是假陰性製造機。**

`byte_6EFAA` 這種符號名來自 IDA 資料庫的**線性位址**,但反組譯文字顯示的是
**`segment:offset`**。實測一份 375 KB、1098 函式的執行檔,整份 `.asm`
**連一個 5 位十六進位常數都沒有**。

```sh
grep -oP '\b6[0-9A-F]{4}h\b' TARGET.asm     # → 0 筆,永遠 0 筆
```

零命中與「真的沒人碰」長得一模一樣。**先問「這個 grep 抓得到任何一個裸位址嗎」**,
答案是零就表示查法本身壞了。

### 正確的問法:逐 byte 查 xref 圖

查單一具名符號不夠 —— 結構化的記憶體通常只有起點有名字,
中間的 `base + i*stride + col` 會被標成對「某個無名位址」的參考,查基址什麼都查不到。
對整段範圍**逐 byte** 呼叫 `DataRefsTo`。1,400 個位址跑幾秒,
比「掃二十萬條指令的立即數」快兩個數量級(後者實測跑 45 分鐘還沒輸出)。

### 掃立即數:xref 圖看不到的那一半

把位址當純數字算的程式碼(`mov ax, 6EFAAh`、或位址被拆成兩次加法)在 xref 圖上是空的,
症狀是「這塊記憶體只有存檔讀寫碰過,遊戲中沒人用」—— 那通常不是真的。
補法是掃全部指令的運算元數值,落在指定範圍就報出來(輸出帶「+偏移」欄好判斷)。
⚠ 慢,而且立即數與位址同值也會中。

---

## 5. 找數字:掃常數,不要掃結果

**當年的數字幾乎都是從少數幾個基數用公式算出來的,不是查表存起來的。**
所以「在執行檔裡搜不到遊戲顯示的那個數字」是**正常的**,代表你搜錯東西了。

做法:把懷疑的常數 `struct.pack('<d', x)` 成 8 bytes 掃全檔
(16-bit 遊戲也要試 `<f`、Q16.16、BCD);命中後改掃「誰載入它」——
`mov bx,imm16` 的那三個 byte 通常只有一兩處,等於直接指到使用點。

**沒命中也是情報。** 掃不到通常表示它是用多個立即數 push 上堆疊的,
也就是內嵌在單一處,跟著那段碼走就好。

---

## 6. Turbo Pascal / Borland C 的辨識重點

- **Pascal 呼叫慣例**:參數由左至右壓棧、被呼叫者清棧(`retn N`)。
  用 C 的直覺讀參數順序會全部反過來。
- **巢狀程序**:看到「只有一個 `arg_0` 卻在裡面 `ss:[di+n]` 亂取」,
  那是巢狀程序,`arg_0` 是外層的 bp —— 不是「參數很少」。
- **48-bit Real 常數**:三個 push。byte0 = 指數,bytes1-5 = 尾數(低位先、隱含最高位)。
  值 = `±(mantissa|1<<39)/2^39 × 2^(exp−0x81)`。
- **32-bit 值拆兩半**:相鄰兩個 word 各被 `cmp` 一次,就是一個 32-bit 比較。
  **先想 32-bit**,不要當成兩個獨立欄位。

## 7. PKLITE 打包

IDA 9.4 對部分 PKLITE 執行檔**會自動解開**。
**解出 0 函式 0 字串就是沒解開的徵兆**,不是「這支沒有程式碼」。
未打包的檔案直接進 IDA,而且通常是最大的那個,從它開始最省事。

---

## 8. 工作紀律

- **每份筆記標「輸入檔 + SHA-256 + IDA 位址」**。位址一律寫 database 的 linear address。
- **讀任何 `sub_XXXXX` 之前先查函式索引。** 專案超過二三十份筆記之後,
  光靠記憶一定會重讀已經解過的函式。做法:掃 `docs/**/*.md` 抽出所有 `sub_[0-9A-F]+`
  產生索引表。
- **不要用 `grep -v` 過濾組合語言。** 為了讓輸出短而濾掉 `mov di, ax` / `shl di, 1`
  這類「看起來是樣板」的行,濾掉的正是**索引計算**,
  會把 `旗標[f(x)] = 1` 讀成 `旗標[0] = 1`。要短就用 `sed -n` 取行段。
- **「唯一」「只有一處」沒有全檔掃描佐證就不要寫。**
- 容器衛生:一律 `--rm --network none`,帶記憶體/CPU/pid 上限;
  輸出目錄才掛可寫;退出前確認沒留 root-owned 檔案。

## 9. 授權與邊界

只做靜態分析、格式保存與互通性研究。不協助破解 DRM、繞過授權、修改付費驗證。
license 只唯讀掛載,不出現在 log、截圖或報告裡。不在 container 內執行老遊戲。
不把整個 home 目錄或 SSH agent 掛進 container。
