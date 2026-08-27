---
name: retro-game-remake
description: Ultima、FM Towns、多版本素材與舊 C／SDL2 remake 的歷史案例庫。當任務需要 u2／u3／u6-cht、opendw、FM Towns 素材、跨版本 theme、Heineman opcode 或 Genesis 圖形案例時按需使用；通用 clean-room remake 流程改用 reverse-engineer-retro-game-remake。
---

# 老遊戲逆向 + 乾淨重製 Skill(階層式)

> 本檔是歷史案例與專項參考，不是現行通用主流程。任何新 remake 先使用
> [`reverse-engineer-retro-game-remake`](../../../reverse-engineer-retro-game-remake/SKILL.md)，
> 完成 RE → `READY` 規格 → 實作 → 同狀態驗證；本檔只補充命中的舊平台案例。

> **怎麼用這個 skill**:先讀本檔(總覽 + 決策 + **踩雷**)。實際做某一階段時,**才**去讀 `references/` 下對應檔取細節 ── 避免一次載入全部。

## 何時啟用
重製 / 移植 / 中文化 1980s–90s 老遊戲(CRPG 為主);反組譯遊戲 binary;破解資料格式;抽取美術/音樂/音效;做跨平台可玩版本。

## 核心策略:反編當 oracle,乾淨重寫
直接把反編出的 `FUN_xxx`(纏繞 runtime、無型別)當引擎是死路。改採:

```
IDA 資料庫為主、Ghidra 交叉驗證 ──(只當行為 oracle，不照抄 runtime 殼)──────┐
破解原版資料格式(地圖/對話/存檔/sprite)──────────────────────────────┼─▶ 手寫乾淨 SDL2 C 引擎
原版資料檔(玩家自備,不散布)─────────────────────────────────────────┘    (deep modules,可公開可維護好中文化)
```

## 七階段流程(各階段細節見 references/)
| 階段 | 做什麼 | 細節檔 |
|---|---|---|
| 1. 反編當 oracle | 以 IDA 資料庫追 xref／資料流；Ghidra／Capstone 交叉驗證；抽 RNG、戰鬥與移動規則 | `references/01-decompile-oracle.md` |
| 2. 破解資料格式 | 地圖/實體/對話/存檔格式;DOSBox 差分驗證 | `references/02-data-formats.md` |
| 3. 美術/音訊考古 | 各版本 tileset/sprite、FM Towns TIF、CD 音樂、音效抽取 | `references/03-asset-archaeology.md` |
| 4. 乾淨引擎 + 中文化 | deep modules 垂直切片;CJK 雙層渲染;UTF-8 覆蓋層翻譯 | `references/04-engine-localization.md` |
| 5. 驗證 | headless 確定性回歸;可破關鏈;**正常玩法可達性** | `references/05-verification.md` |
| 6. 打包 | Docker first;引擎/資料分離;AppImage/Windows/Mac CI/Android APK(觸控) | `references/06-packaging.md` |
| 7. 攻略/文件 | README 作穩定入口；研究、規格與工作歷程分檔；繁中攻略另立文件 | 現行標準見通用主技能 |

## 進階(跨階段加值)

- **多版本素材考古 + 遊戲中 Theme 切換 + RE 證據停止線** → `references/07-multiversion-assets-and-themes.md`。抽 Amiga/X68000/PC-98 各版美術音樂、做 F8 主題切換，並在證據足以完成玩家可見規格後停止；未解內容保留為明確待辦，不因成本效益永久刪除。
- **多 agent 並行 + 存活性紀律** → rule `35-background-agent-container-liveness`(禁背景 sentinel/無界 dump/GUI viewer;以活躍 process/branch commit/SendMessage 回應判活死)。

## ⚠️ 最痛的踩雷(這些用時間換來的,務必記住)

1. **debug hook 會遮住真 bug**。可破關回歸測試常用 debug hook(發全道具/瞬移/強制進城)繞過正常行走 → **測得過卻不能正常玩**。
   - 真實案例:回歸全 PASS,但全新角色開局被放在「只連城堡的 12 格小島」soft-lock,進不了任何城鎮。
   - 對策:**一定要另外驗「無 debug 的正常玩家路徑」**。世界可達性用**連通分量(flood-fill)分析**:落點必在最大陸地分量、且城鎮與落點同分量(可步行到)。船要放在「鄰接玩家陸地分量的水格」才登得上。
2. **反編 auto-analysis 進不了遊戲主碼**。stripped binary 的遊戲邏輯多在 indirect call / jump table 後,Ghidra 自動分析只覆蓋到 runtime。**靠「線索常數」跳進去**(例:CD-BIOS 中斷號 0x93 當 data 出現 → 從那反查播放鏈)。
3. **打包要帶「全部」資料,不要只帶 demo 子集**。只帶幾張地圖 → 玩家「進不了城鎮/找不到資料」。
4. **不要打包測試角色存檔**:玩家會看到「滿狀態怪角色」;開局該走建角流程。headless 預設**不要寫回** `player_save`(會覆寫餵入的 fixture)。
5. **引擎與版權資料分離**:原版 binary/資料/美術/音樂一律 gitignore、不散布;公開包只給引擎,玩家自備合法副本。
6. **全程 Docker build**；工具鏈與 runtime 必須在容器內自洽，不掛入主機 Python 或 venv。
7. **FM Towns 是素材富礦但有陷阱**:TIF 是 FillOrder=2(LSB-first);CDDA 走 INT 93h 但**經 RUN386 反射**(0x93 是 data 不是字面指令);遊玩音樂是 EUP(非 CDDA);.SND 是 sign-magnitude PCM。細節見 `03-asset-archaeology.md`。

## 姊妹專案(同一套 RE+乾淨重寫方法論)
- `u2-cht`(Ultima II)— 本 skill 主要來源 · `u3-cht`(Ultima III)· `u6-cht`(Ultima VI)· `opendw`(Dragon Wars)。
- 註:QB64/BASIC 老遊戲移植是**另一套**做法(不反編、直接跨編 .bas),見 `qb64pe-game-linux-port` skill,與本 skill 無關。
