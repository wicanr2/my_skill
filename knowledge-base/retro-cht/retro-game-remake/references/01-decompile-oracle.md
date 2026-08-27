# 01 · 反編當 oracle

## 原則
反編出的東西**只當「原版實際怎麼算」的真值參考**,抽演算法 → 在乾淨引擎重寫;**絕不照抄** `FUN_xxx`(無型別、纏繞 MFC/runtime、不可維護)。
信心標 `[確定]/[推測]/[未解]`。把分析寫成 `docs/ORACLE_MECHANICS.md`,函式索引 `oracle/functions_index.tsv`、字串對應 `oracle/oracle_string_map.txt`。

## 取得可反編的 binary
- 優先找**官方授權重製版 / 移植版**的 binary(LairWare、Alderson Windows port…),通常結構比原 DOS exe 好反編。
- 反編匯出可能含受保護內容；預設留在私有研究區。公開 repo 只提交必要的位址索引、規格、
  自製測試與不含原版程式碼的 clean-room 實作。

## 工具優先序

已有 IDA Pro 專用 image 時，以 `.i64` 的函式邊界、xref 與資料流為主。Ghidra headless
只用於獨立交叉驗證或專案明確指定；先沿用既有、鎖版、可重建的專用 image，不在任務中
臨時下載未鎖版本。Capstone 只適合核對短指令區段，不可取代資料庫關係。

## ⚠️ auto-analysis 進不了遊戲主碼
stripped binary 的遊戲邏輯多在 **indirect call / jump table** 後,Ghidra/capstone 從 entry 遞迴只覆蓋到 runtime(MetaWare/RUN386 startup、DOS int 21h wrapper)。
**破法 = 線索常數**:已知某機制會用某常數(例 CD-BIOS 中斷號 `0x93`、埠號、magic),decompile **全部函式**並 grep 該常數出現的函式 → 從那反查呼叫鏈。
Ghidra 腳本實用招:`DecompInterface` 反編每個 func → grep C 文字找線索;`getReferencesTo` 找呼叫端/寫入者;看 caller 的 `PUSH imm`/`MOV` 取常數參數。

## capstone(快速反組譯,免 Ghidra)
在專用 Docker image 內使用鎖版 Capstone。線性掃要**遇壞 byte 跳 1 續掃**；gap-skip 在
data 區可能誤判成指令，必須回到 IDA 資料庫並以第二工具交叉驗證。

## 抽演算法的常見真值
- RNG:多為 LCG `seed = seed*0x343fd + 0x269ec3`。
- 戰鬥命中/傷害/掉落、狀態效果(麻痺/睡眠)計時器、亂數機率 → 抽公式後在引擎重寫,再用回歸對照。
- 用「字串錨定」導航:先在反編裡找已知文字(訊息、選單),回溯誰引用它 → 定位那段邏輯。

## bytecode VM 的「NULL opcode」破解(反編沒逆出的 op)
反編的 opcode dispatch 表常把部分 op 標 **NULL**(未逆出)→ script 跑到即 halt;中後期 quest 物品/旗標
取得端常卡這。**NULL op 沒 C oracle,但原版 binary 反組譯本身即真值**:查 dispatch 表取 handler 位址 →
反組譯原版該位址(.COM 檔案 offset = 位址−0x100)→ 逐行 ASM 對映 VM state → **照已實作的孿生 op
借定址** → 實作 + **vm_selftest 逐指令自證**(無 oracle 時唯一驗證)→ **動態 trace 掃全 script 找「用在哪」**
(常推翻「逆不出 set 來源」:取得端多在共享/對話 script,不在地圖格 script)。
- 完整 SOP + Heineman 引擎(火龍之戰/Bard's Tale 同血脈)VM 資料區/定址速查 + 已逆出 op 範本
  (op_64/65/67 物品 CRUD、0x4754 物品簽章比對、char_data↔char_ext 重疊雷、event↔party 持久化):
  見 `references/08-null-opcode-heineman-engine.md`。**Bard's Tale 系列中文化可直接遷移**(同引擎,opcode 編號異、定址形同)。
- 誠實:逆得出標真值;子程式沒逆出就標 ⚠️ 部分 + 記卡點;順手把「已實作卻仍標 NULL」的 op 更正。
