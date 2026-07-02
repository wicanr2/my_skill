# ScummVM / AGOS talkie 老遊戲繁中化:融合法 + 逆向對齊 + 資料解壓

> 觸發:做 ScummVM 支援的老遊戲(尤其 **AGOS**:Simon 1/2、Feeble Files、Waxworks)繁中化;
> 遇到「有語音卻沒字幕 / 嘴動無字」;要對齊兩個版本的遊戲資料;老遊戲安裝檔是自訂壓縮(如 `.RED`)。
> 與 `80`(retro README)、`81`(CJK hires)、`83`(完整性)、`62`(靜態溯源)、`64`(截圖 oracle)同源。
> 來源:simon-the-sorcerer-cht(2026-07,魔法師西蒙 CD×Floppy 融合)。

## 1. [HARD] 動手前先驗證「來源版本的字幕完整度」——talkie 版常缺字幕

老遊戲的 **CD talkie 版(有語音)常沒有完整字幕**:為塞語音把對白文字從資料裡拿掉了。
Simon 1 CD 英文版就是——ScummVM `engines/agos/agos.cpp` 明白註解 `// English and German versions don't have full subtitles`,
且對英文版**強制 `_subtitles=false`**。實測 CD 比 floppy 少約四成(字串表 368 vs 694、對白 ~1461 vs 3342),
玩家看到「嘴巴在動、一個字都沒有」。

**別預設 CD/talkie 版可翻**。先比對 floppy vs CD 的字串/對白數(GAMEPC 檔頭字串數、TEXT 檔行數)。
缺就用**融合**:以**文字完整的 floppy(pre-talkie)版為字幕來源** + **CD 版的語音**。前一版失敗的真正根因就是沒診斷這點,翻了一千多條仍一堆空白。

## 2. [HARD] 中文化注入以「行的身分(id)」為 key,不要用英文原文比對

在引擎取字串處(AGOS `getStringPtrByID(stringId)` 出口)**依 id 查譯表回傳**,譯表做成 `id → 譯文`。
**不要**拿螢幕上的英文字串去比對(`英文 → 譯文`)——語音-only / 空字串的行沒有英文可比對(script 是 `NULL_STRING`),
用英文當 key 天生救不了那些行。有語音的行以 `speechId` 為 key,無語音旁白以 `stringId`。

## 3. 對齊兩版資料:重用引擎自己的反組譯器,別自寫 bytecode parser

要把 floppy 文字對到 CD 的 speechId(融合的核心),**重用引擎內建的 script disassembler**:
ScummVM AGOS 有 `dumpAllSubroutines()` / `dumpOpcode()`(`debug.cpp`),`getSubroutineByID` 還會自動載入 tables,
遍歷即可 dump 全部子程式,含每個 opcode 的 operand(`'T'` 印 `"文字"(id)`、`'W'` 印數值/speechId)。
在 `go()` 載入後加旗標觸發 dump→退出,對兩版各跑一次(SDL dummy 影音 headless),再依「子程式 ID + opcode 位置」逐句配對。
實測 1655 子程式 1:1 對齊、0 mismatch。**別重寫 bytecode 解析**——opcode 表與 operand 編碼複雜易錯,引擎本來就有正確的。

## 4. 資料被自訂壓縮鎖住:DOSBox-in-docker 跑原版安裝,目錄熱抽換過換片驗證

老遊戲安裝檔常是自訂壓縮(Adventure Soft 的 "RR" 格式 `GAME.RED`),沒現成解壓器時**別硬逆向**——
用 **docker 內 DOSBox 跑原版 `INSTALL.EXE`** 讓它自己解。多磁片的雷:安裝器靠 `DISK.ID` 驗證插第幾片,
三片混一資料夾只解第一片。**解法:目錄熱抽換**——A: 掛可寫目錄先放 disk01,容器內 loop 監看輸出檔數,
**停滯就 `rm -f` 換成下一片檔案(含該片 DISK.ID)** 再送 Enter。全程 `SDL_VIDEODRIVER=dummy` + `xdotool` 無人值守。

## 5. 渲染:CJK 24px + 加大引擎文字緩衝

retro 引擎的文字緩衝是照原版小字型算的——AGOS 字幕 sprite 只額外配 6400 bytes(`res.cpp` loadVGAVideoFile id2type2:
"2 lines × 320 × 10px"),24px 全形中文會溢位。**要把該緩衝加大**(本次 6400→40000)。視窗文字(動詞列/物件名)走
獨立的 surface 繪字路徑,`windowPutChar` 需處理 Big5 雙位元組並前進正確欄寬。字級用 24px,不縮字塞小位(見 `81`)。

## 6. 硬編碼 UI 要在原始碼加 ZH 分支

動詞列(`verb.cpp` `english_verb_names[]`)、存讀檔訊息(`saveload.cpp`)、防拷提示是**寫死在引擎、不經 `getStringPtrByID`**,
查表攔不到。要在原始碼加 `case Common::ZH_TWN`(或以 `_chtActive` 判斷)提供 Big5 字串。防拷可用引擎內建
`_copyProtection=false` 的自動填答路徑 bypass。前一版就漏了動詞列,導致「操作選單永遠英文」。

## 驗收(呼應 `63`)
以「實機看得到中文 + dump 未翻歸零」為準,不信任譯表自報條數。遊戲原檔/語音/磁片映像/英文文字萃取全程 gitignore,push 前精確 grep 複檢。
