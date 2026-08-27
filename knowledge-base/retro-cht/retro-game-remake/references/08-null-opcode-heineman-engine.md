# 火龍之戰 / Bard's Tale — Heineman 引擎 unknown opcode 破解方法論 + VM 速查

> 來源:opendw_dragon_wars_cht 專案的反組譯實戰(2026)。
> **為何對 Bard's Tale 中文化有用**:《火龍之戰》(Dragon Wars, 1989) 在發行前一個月還叫
> **《吟遊詩人傳說 IV》(Bard's Tale IV)**,由 **Rebecca Heineman** 主程式;與 BT1/2/3、Wasteland
> 同一條 Heineman 引擎血脈。**bytecode VM 結構、opcode dispatch、資料區定址法大量共用** ——
> 這份方法論與 VM 速查可直接遷移到 Bard's Tale 系列的中文化/重製逆向。

---

## 1. 核心情境:反編把 opcode 標 NULL / 未實作

反編產物(如 Devin Smith 的 opendw)常把部分 opcode 在 dispatch 表 `targets[]` 標 **NULL**
(原作者沒逆出語意)。這些就是「unknown op」。任何 script 跑到它們 → VM halt(`last_unimpl`)。
中後期 quest 物品鏈、祝福、商店交換往往卡在這幾個 NULL op(取得端)。

**真值原則**:NULL op **沒有 C oracle 可對拍**。但**原始 binary 的反組譯本身就是真值來源** ——
直接反組譯原版執行檔該 opcode 的 handler,即可逆出語意,再以 vm_selftest 逐指令自證。

## 2. 破解 SOP(七步,實戰驗證)

1. **取 dispatch 位址**:opcode → handler 位址,查反編的 dispatch 表(火龍之戰:`targets[0x3960 + op*2]`)。
   例:op_64 → 0x446E。
2. **反組譯原版 binary 該位址**。`.COM` 載入 `CS:0x100`,故**檔案 offset = 記憶體位址 − 0x100**
   (op_64 @0x446E → file 0x436E)。工具:capstone / objdump / 專案的 `dwdisasm.py`。
3. **逐行 ASM → VM state 對映**。認出它讀寫哪個資料區(見 §3 速查)、用哪種定址、有無 operand
   (`lodsb`/`lodsw` = 取 1/2-byte operand)、改了哪些暫存(r2/r4/mode/flags)。
4. **找已實作的「孿生」opcode 借鏡**。同資料區的相鄰 op 多半已實作 —— 照它的定址寫,風險最低。
   例:op_64(寫 char_ext)直接照 op_68/op_69(讀/寫 char_ext)的 `base=(selector<<8)+unknown_4456[slot]`。
5. **實作 handler + dispatch 註冊**(`t[0x64]=&...`)。bound-check 所有陣列存取(DOS 會 OOB,重製要防)。
6. **vm_selftest 逐指令自證**(NULL op 無 oracle → 這是唯一驗證):手塞一段 bytecode(設好 game_state /
   data_bytes / char_ext)→ `Interpreter(s).run()` → 斷言結果符合反組譯語意。涵蓋正常 + 邊界(如「物品欄全滿」)。
7. **動態 trace 找「用在哪」**。寫工具掃全部 level/shared script 動態跑 VM、記錄該 op 出現處
   (火龍之戰實戰:`trace_item_grants` 發現給物品 op **不在 tile script,在 op_58 載入的對話/商店/祝福共享 script**)。
   這一步常推翻「逆不出 set 來源」的舊結論。

**證據誠實**:逆得出才標真值;子程式(如 op_65 的簽章比對 0x4754)沒逆出就**精確記錄卡點**
(位址 + 為何)、標 ⚠️ 部分,不臆造。OPCODE_REFERENCE 之類的表把舊「(inferred) 推測」改真值時,
順手把已實作但仍標 ❌ 的 op 一併更正(火龍之戰實戰:0x68 早實作卻仍標 NULL)。

## 3. Heineman 引擎 VM 速查(火龍之戰逆出;Bard's Tale 系列高度共用)

**暫存 / 全域**(位址為火龍之戰 DOS;BT 版位址不同但語意對映在):
- `game_state[]`(gs)@0x3860 — 持久遊戲狀態 bit/byte 旗標(進度 gate 用 op_9b 設 / op_9d/op_50 測)。
  - `gs[6]` = 當前角色 index(0..3);`gs[7]` = 當前物品槽 index;`gs[0x1F]` = 隊伍人數。
  - `gs[gs[6]+0x0A]` = **selector**(record 頁高位 = record_index*2)。
- `r2` = `word_3AE2`(運算暫存 / 資料資源內 offset);`r4` = `word_3AE4`;`mode` = `byte_3AE1`(0=byte,非0=word)。
- `word_3ADF` = 當前資料資源(running script / 物品模板…)的 bytes;`data_bytes` 即它。

**角色資料兩塊(取得端各走一塊)**:
| 區段 | 內容 | 定址 | 原語 |
|---|---|---|---|
| `char_data`(data_C960,512B/員) `+0x55`=flags[85] | 屬性、祝福/詛咒旗標 | `(selector<<8)+operand` | op_5F 設 bit / op_60 清 / op_61 測;op_62 掃描 |
| `char_ext`(data_CA4C,23B×12 格/員) | 12 格物品欄(裝備/任務物品) | `(selector<<8)+unknown_4456[slot]+operand` | **op_64 給** / op_67 刪+壓 / op_68 讀欄 / op_69 寫欄 / op_65 持有檢查 |

- `unknown_4456[slot]` = slot*23 的偏移表(12 格:0,0x17,0x2E,…,0xFD)。
- **祝福旗標** `flags[85]`（char +0x55）：`0x80` Irkalla、`0x10` 永恆之神（+3 全屬性）、`0x20` Enkidu。

> ⚠️ **char_data 與 char_ext 在原版記憶體中重疊(別建成兩塊獨立陣列!)**:`data_CA4C = data_C960 + 0xEC`
> ——背包(char_ext)其實是 512B 角色 record 內偏移 **0xEC** 起的後半段(stats 前 236B + 背包 12 槽×23B = 512)。
> 即 `char_ext[k] ≡ char_data[0xEC + k]`。若重製時把兩者建成獨立陣列,op_64 寫進 char_ext 的物品**不會**進 512B
> record(→ 存檔 → 隊伍背包)→ 給物品看似成功卻丟失。**踩過的雷**:火龍之戰 remake 初版兩塊獨立,給物品端到端
> 失效;修法 = 兩塊視為重疊窗(讀寫互鏡),或事件前後同步。BT 系列同一套 record + ext 佈局,直接套此認知。

### 事件↔角色狀態的持久化(NULL op 實作後常見的「最後一哩」漏接)

實作了 op_64(給物品)/op_5F(設祝福)後,**還要把事件 VM 的角色狀態接回遊戲的隊伍 records**,否則事件對角色
的修改是暫態、跑完就丟。Heineman 引擎的事件執行迴圈(`run_event`)要:
- **事件前**:party 512B records → VM `char_data`(member i → record i,`selector = i*2`);設角色 context
  `gs[6]`(當前角色)/`gs[0x1F]`(隊伍人數,op_64 的 party 迴圈靠它)/`gs[0x0A+i]`(各員 selector);
  背包鏡射進 char_ext(重疊窗)。
- **事件後**:char_ext → char_data[0xEC+],逐欄比對寫回 party records(**只有實際變動才重建** → flavor 事件零副作用)。
- **端到端自證**:無 oracle → 寫一個 deterministic test(record → VM char → op_64 → 同步 → 驗 record `[236+slot*23]`
  有物品),證明「op_64 給物品 + 同步 → 持久進 512B record 背包」。配 combat/save golden 確認不破。
- **誠實殘留**:互動觸發層(上鎖寶箱按鍵解鎖、NPC 對話選擇)多在未反編的 walking-engine,headless 難自動觸發
  op_64;但「事件一旦跑到 op_64 物品就確實入背包」可獨立驗證。物品-地點逐一綁定 = 內容工(攻略反推:用攻略
  各區圖例「哪地點給哪物品」對 op_58 呼叫端的 gs[0xD7]=模板 offset)。
  (opendw struct 把 0x55 標 `gold` 是早期推測誤植 —— 以 fraterrisus 手冊為準。**RE 標籤要對拍,別照抄反編註解**。)

**物品 CRUD 一組**:op_64 給 / op_65 查 / op_67 刪 / op_68 讀 / op_69 改 —— 共用 char_ext 定址 + 物品模板資源
(`word_3ADF`@`word_3AE2`,模板 = DATA1 物品定義區,23B/件)。

## 4. 已逆出的代表性 unknown op(火龍之戰;當 BT 對照範本)

- **op_64 GIVE_ITEM**(0x446E):找空格(該格 offset 0x0B==0)→ 從模板複製 23B → gs[7]=槽;全滿放棄。無 operand。
- **op_67 REMOVE_ITEM**(0x44CB):從 gs[7] 槽起後格往前壓 23B、末槽清 0。
- **op_6B move_party_reverse**(0x45A1):`adjust_position(gs[3]^2)`(反向移動)。
- **op_8D read_string_input**（0x49D3）：玩家文字輸入 → `gs[0xC6..]`（說暗語 gate 用）。
- **op_65 HAS_ITEM**(0x44B8):0x4754 簽章比對 → 命中設 word_3AE6 bit 0x40。見下「物品簽章比對」。

### 物品簽章比對(0x4754;DW/BT 系列通用,物品識別的核心)

「隊伍是否持有某物品 X」= 拿 X 的**模板記錄**逐位元組比對角色物品欄裡的 23-byte 記錄:
- **header(bytes 1-6, 8-10)= type/id,須完全相等;byte 7 跳過**(數量/充能,因實例而異 → 不納入識別)。
- **bytes 11+ = 物品名,7-bit 編碼**:該 byte 高位元 `0x80` set = 還有字、clear = 結尾。比到名稱結尾且全符 = 命中。
- 命中 carry-clear、不符 carry-set;上限 ~byte 22。
- **這套「header 比對 + 跳數量 byte + 7-bit 名稱終止」是 Dragon Wars / Bard's Tale 物品識別的共用形**;
  BT 中文化處理物品名顯示 / 存檔 / gate 時直接套(名稱的高位元終止 = CJK 覆蓋層要小心,別把終止位元當資料)。

### 條件旗標慣例:word_3AE6 的 bit 0x40 / 0x80 / 0x01

Heineman 引擎的 VM 條件分支(jz/jnz/jb)讀 **word_3AE6**:`bit 0x01`=carry、`bit 0x40`=zero、`bit 0x80`=sign。
- 「設旗標」子程式如 `or [word_3AE6],0x40`(設 zero)、清為 `and …,0xbf`。NULL op 實作要對映到引擎的 flags 字,
  **別只設 C++ 的 cf/zf 暫存而漏寫 word_3AE6**(分支 op 讀的是後者)。
- ⚠️ opendw 把 0x40 標 `sign_flag` 是**標籤誤植**(實為 zero);照反組譯的 bit 行為走,別照抄反編函式名。

## 5. 遷移到 Bard's Tale 的提醒

- BT1/2/3 與 DW 的 opcode **編號/位址不同**,但**dispatch 表 + 資料區 + 定址法的「形」共用** ——
  先在 BT binary 找 dispatch 表(字串錨定 / 已知常數跳進去),建立 op→位址,再套本 SOP。
- **存檔 / 角色 record 結構**多半同源(512B record + ext 物品欄);BT 中文化的存讀檔 byte-for-byte
  與 char 欄位定址可參照本速查。
- 動態 trace 工具(掃全關卡跑 VM、記錄 op 分佈)是「逆不出 set 來源」類卡點的**通用破法**,直接重用。

## Reference

- 專案文件:`docs/reverse-engineering/OPCODE_REFERENCE.md`(全 opcode 表)、`67_ITEM_ACQUISITION_RE.md`
  (取得端逆向)、`42_COMBAT_BYTECODE.md`(戰鬥真值)、`55_…QUEST_GATE…`(進度 flag gate)。
- 方法論亦見 `/retro-game-remake` skill `references/01-decompile-oracle.md`(反編當 oracle 通則);
  本檔是該通則在 **Heineman 引擎 + NULL opcode** 的具體 playbook。
- 血緣:`docs/reference/66_BARDS_TALE_LINEAGE.md`(DW = 沒掛招牌的 Bard's Tale IV)。
