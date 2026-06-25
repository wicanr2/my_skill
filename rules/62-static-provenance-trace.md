# 靜態溯源紀律(別太早退回「動態/封死/看不出來」)

問「這個值 / 設定 / 字串 / 行為從哪來」時,**先把資料反向追到靜態源頭,再談動態分析或「追不到」**。
源自實戰:逆向某 DOS 遊戲時反射性下「在 overlay 封死、要跑模擬器」結論三次,答案其實全是純靜態、且不深
(資源選擇器就是地圖檔 header 的一個 byte 欄位)。同一失誤在一般 codebase 也會犯:「這值是 runtime
設的 / framework 魔法 / generated code,看不出來」。

> `[HARD]` = 違規會白白放掉本可一步查到的答案,或誤導使用者去做昂貴的動態/手動驗證。

## 核心鐵則

- **[HARD] 撞牆時不准直接下「封死 / 要動態 / 看不出來」結論。** 撞牆 = far-call 進 overlay、搜尋落空、
  值「來自別處」、framework 注入、generated/minified——都先跑下面的反向溯源 SOP,跑完仍無解才宣告受阻,
  並列出已試步驟。
- **[HARD] 搜尋落空 ≠ 不存在。** 一次 grep/搜尋沒命中,只證偽「我的 query」,不證偽「事實存在」。
  宣告「沒有」前先換 query:大小寫(踩過雷:檔名是**小寫**,搜大寫漏掉)、編碼、
  拆字 / 部分比對、同義詞、別名、不同分隔符。

## 反向溯源 SOP(撞牆時跑這套,先做、別放最後)

1. **錨定已知實例。** 取一個已驗證的具體 case(如「這城對話 = 某文字檔,內容已對上」),用它當不動點。
2. **找實際用到該資料的 sink。** 開檔 / syscall / 查表 / 印字 / 寫 DOM / 發 request / log 那一行——
   資料一定在某處被「用掉」,從用掉的點開始最短。
3. **把運算元反向走到靜態源。** disasm 就 register-by-register、原始碼就「這變數誰賦值」往回追,直到落在
   一張表、一個 header 欄位、一個常數、一個 config key。實例:開檔 → poke 數字進檔名模板 → bank=暫存器 →
   地圖檔 section header 的某 byte 欄位。通常 20 分鐘內見底,不深。
4. **選擇邏輯在 caller,不在被呼叫的 loader。** 「loader 在 overlay / 在第三方庫」不等於「選哪個資源的邏輯
   在那」——選擇器幾乎總在呼叫端的可讀主段 / 自家程式碼。別把「loader 不可讀」當「來源不可知」。
5. **驗證源頭。** 用內容對齊反證(逆向:逐句對地名/任務;一般 code:值域、邊界 case、實際 log)。

## 動態分析的定位(不是 fallback,是末段)

- **[HARD] 動態 / 重手段(跑完整流程、模擬器、debugger、加 production instrumentation、跑整個系統)
  只保留給真正 runtime-only 的東西**:timing/race、RNG 狀態、實際執行進度態、外部輸入相依、非決定性。
  **「這個靜態值/設定從哪來」不算 runtime-only**,別用動態去查本可靜態回答的溯源。
- 與 `60-feedback-loop-priority` 的關係:60 是「修 bug 前先建可重跑 pass/fail loop」(動態,對症);
  本檔是「查溯源先靜態反追」(別把溯源誤當需要動態)。兩者互補:先靜態查清來源,再用 60 的 loop 驗修法。

## 何時套用

- 逆向工程:反組譯撞 overlay/far-call、找資源選擇器、欄位來源、檔名/表來源。
- 一般 codebase:「這個 config/flag/字串/狀態哪裡設的」「為什麼載這個檔/走這條分支」「這值怎麼算出來的」。
- 任何想說出口「看不出來 / 是動態的 / 要跑起來才知道 / 在框架裡 / 在 generated code」之前。

## Why

- 反向 data-flow 在主段 / 自家程式碼幾乎總能靜態回答「值從哪來」,且通常不深(一條 sink 往回幾跳)。
- 太早退回動態 = 把昂貴成本(跑完整系統、手動驗證、麻煩使用者)花在本可一步查到的事,還常因此給錯結論。
- 「在 overlay / 是框架魔法」是 thought-terminating cliché;點破它就繼續追。

## Reference

- 同類心法:資源 bank / 選擇器常寫在資料檔(地圖 header)而非 EXE 全域表;反組譯器 file offset ≠ 符號表
  logical offset(混用會追進隔壁函式);間接跳表派發的 data-driven id 反推。
- `60-feedback-loop-priority`(動態 pass/fail loop 紀律,互補)、`40-learning-loop`(先驗證再下結論)。
