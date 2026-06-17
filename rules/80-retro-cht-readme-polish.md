# Retro Game CHT README Polish

**核心**：老遊戲（1990s 經典）繁體中文化專案的 README 不是「使用手冊」，是**給 30 年後的同代玩家一封信**。寫法不是寫工程文件，也不是寫商品介紹 — 是寫**雜誌**。

本 rule 從 [openxcom-cht](https://github.com/wicanr2/openxcom-cht) v2.27 README 全文 review 萃取，適用於任何「90s 經典遊戲 → 現代漢化 + ship」類型專案的 README 維護。

## 三層結構（必備）

任何老遊戲 CHT README 應該分**三個明確的 voice register**，**不要混用**：

| 區段 | Voice | 風格 | 範例 |
|---|---|---|---|
| **Hero / 開場致詞** | 第一人稱「我」、溫情、低調 | 像信、像散文 | 「還記得嗎？1990 年代的某個深夜⋯⋯」 |
| **Magazine 主體**（戰史/兵種/武器/敵人/世界）| 編輯人聲「我們/你」+ 1990s 電玩用語 | 1990 年代《電腦玩家》《軟體世界》《PC Game》三大誌風 | 「**最殘酷的場景是**：你研究了三個月終於量產聲波加農⋯⋯」 |
| **Technical Deep Dive / Upstream / Patches** | 工程文件被動式 | 冷靜、可重現、有 code block | 「Font.cpp:193 `getHeight()` 取 max image height」 |

**Register signal switch** 要明確（`<a name>` anchor + 分隔 `---` + emoji 變化），但**voice 不可洩漏**：
- ❌ Hero 段裡突然出現「Font.dat 是 YAML 不是 binary」
- ❌ Technical 段裡突然出現「指揮官，地球的命運懸於一線」

## Magazine 主體的雜誌風 SOP

**6 個核心元素必備**：

### 1. 編輯人聲（subjective voice）
- 用「**你 / 玩家 / 老幽浮迷 / 老 X 迷 / 指揮官 / 我們**」直接對話
- 編輯帶情緒：「**最讓人崩潰的是⋯⋯**」「**老玩家絕對記得⋯⋯**」
- 適度的「我」：「**我當年在這關卡 30 個小時**」「**直到 1996 年某期玩家來信才解開**」

### 2. 1990s 電玩用語
- 「**團滅 / 打趴 / 燒裝備 / 死當 / 練功 / 卡關 / 神物 / 夢魘級 / 噩夢級 / 廢到笑**」
- 「**狠角色 / 神級 / 強到爆表 / 罵到狗血淋頭 / 傻眼**」
- 「**這一段你看完會傻眼**」「**這時候才是真正考驗你指揮能力的時候**」

### 3. 1990s 文化錨點（適度，不灑狗血）
- 「**那時候沒有 GameFAQ / Discord / wiki，只能靠《電腦玩家》《軟體世界》《PC Game》三大誌的手冊翻譯**」
- 「**BBS 上的攻略板（PCGAME-NEW、UFO-FANS、X-COM）**」
- 「**書局架上印刷油墨還沒乾的厚手冊**」
- 「**14 吋 CRT / 320×200 / Sound Blaster**」
- 慎用：光華商場（盜版聯想敏感）、青蛙撞奶（地域性過強）

### 4. 軍事/科幻雙線（若遊戲題材對應）
- **X-COM/MOO/MOM 類**：軍事公文體 + 洛夫克拉夫特恐怖（「**不寒而慄**」「**不可名狀**」）
- **Ultima/MM/EOB 類**：奇幻史詩體 + 古英文倒譯（「**汝**」「**爾**」「**卿**」）
- **Wing Commander 類**：軍機艦長日誌體 + 跨星系政治
- 寫到外星人/魔王時，**形態描寫**用一兩個比喻句（「**鉗子一夾鋼板像紙**」「**漂浮、長觸手、一觸便麻痺**」）

### 5. 譯名「考古」感（譯名警告章節）
- **像考古學家**還原 1990s 譯者為何錯譯
- 「**維京工作室那年代沒有洛夫克拉夫特原典在手，把 Deep One 當成編號**」
- 「**SONIC 在當年的台灣物理課本還寫『音速』，譯者也就跟著錯**」
- **不批判**，只是**還原時代條件**
- 譯者掛名（阮建成/維京工作室/聯合報 1990s 國際版音譯規範）= 致敬

### 6. 時代評論當情感引爆點（「他說沒有中文版。現在有了。」）
- 去找一篇**當代或當年的中文評論 / 報紙專欄 / 雜誌專文**寫過這款遊戲（聯合報電玩專欄、三大誌專文、部落格回顧），
  特別是結尾**喟嘆「可惜沒有中文版」「從來沒人漢化」**那種句子 —— 那正是這份專案存在的理由。
- 寫法：先用 Magazine 編輯人聲引出該文（盤點遊戲特色），**blockquote 引那句原話 + 標出處作者**，
  再用 **Hero 力道**一句收束反轉：「**他說沒有中文版。現在有了。這個 repo 就是那句話遲到 N 年的回答。**」
- 這招把「外部第三方的遺憾」轉成「本專案的使命」，比自己宣稱「我做了漢化」有力十倍。出處作者**掛名致謝**（致敬，等同譯者掛名）。
- ⚠️ 版權：評論原文（HTML/PDF/掃描）**只摘要 + 引一句 + 標出處**（合理引用），**不要貼全文、不要把版權媒體檔入 git**（gitignore）。

## Prose 結構 vs 表格密度

| 場景 | 用法 |
|---|---|
| **橫向對比**（5 個職業 / 7 個種族 / 三代武器）| 表格 |
| **序列步驟**（戰術鐵則 / 升級順序）| numbered list |
| **警告清單**（5 條譯名警告 / 不要回退）| bulleted list |
| **敘事 / 情境 / 編輯意見** | **prose 段落**（不要 bullet！）|

**每章節結構**：
1. **開頭 1-2 段 narrative**（編輯人聲 + 1990s 文化錨點）
2. **表格 / list**（橫向對比資料）
3. **表格之後 70-150 字 prose 收束**（**重要**！不要表格直接接下一個 H3）
4. **結尾 1 句 transition** → 下一個章節

## Transition 橋接（章節間）

老遊戲 CHT README 容易章節「硬切」。**每章開頭應該有 1-2 句承接上一章**：

```markdown
[上一章節結尾...]

---

<a name="next-chapter"></a>
## 🎯 Next Chapter Name

[承接句：「上一章講了 X，但這只是表面 — 真正讓玩家崩潰的是 Y」]

[正文 narrative...]
```

**橋接句範例**（openxcom-cht v2.27 review 加的）：
- Hero → Quick Start：「**這份回信你可以三層讀：跳到 Quick Start 直接玩 / 慢慢讀完每章當複習 / 把譯名對照當資料庫**」
- Why → 戰史：「**要懂這份譯名為什麼這樣翻，先回到 X-COM 的歷史本身**」
- 1995 手冊 → 士兵名：「**校對譯名是字面工作，招募水兵則是另一個維度**」
- 士兵名 → 截圖：「**講完文字了，最後讓眼睛看一輪實機畫面**」

## 重複內容收束

老遊戲 CHT README 通常有 3 處會講同一件事：
1. ship statistics（Hero 段）
2. 章節 narrative（戰役起源 / 武器章）
3. 結尾文獻學（手冊章）

**處理原則**：
- 最詳細版本留**第一次出現**的章節（通常是戰役起源 / 武器系統 / 手冊文獻學）
- 其他兩處改 `**詳見 [X 章](#anchor)**` cross-ref
- **5 條譯名警告**例外 — 在 species 章 + manual 章兩處都列，**因為角色不同**（一個是 in-context warning、一個是 archaeological discovery）

## TOC sync

每次重大編輯後**必跑**：
1. `grep -n '^## ' README.md` 拉出所有 H2 章節
2. 對照 TOC list 是否齊全 + 順序正確
3. `grep -n 'name="' README.md` 拉出所有 anchor
4. 對照 TOC link `#anchor` 是否每個都存在

**漏 anchor 的章節**要補：
```markdown
<a name="mod-i18n"></a>
## 🧩 v2.22 — Mod 列表中文化
```

## 不要做（反模式）

- ❌ **整份 README 都用工程文件 voice** — 沒人想讀
- ❌ **整份 README 都用 hero 溫情 voice** — 太膩
- ❌ **整份 README 都用 magazine 編輯人聲** — 失去技術可信度
- ❌ **照搬一個遊戲圈的用語到另一個** — UFO/X-COM 用「指揮官」/ Ultima 用「聖者」/ Wizardry 用「探險隊」，**不要混**
- ❌ **長 bullet list 替代 prose** — 雜誌不會用 10 個 bullet 寫一個故事
- ❌ **表格之後直接接下一個 H3** — 無敘事收束，視覺斷裂
- ❌ **譯名警告章節寫成「我們修正了 X」** — 改成「**1990s 譯者為何寫 Y / 我們在什麼考古證據下調整為 Z**」
- ❌ **TOC 落後實際章節** — 漏 anchor、順序亂

## When to apply

- 老遊戲 CHT 專案 README 寫 / 重寫 / 大改
- 把 fact-dump（表格 + bullet）的 README 升級為**可讀文件**
- 多個 voice（hero 信 + magazine prose + technical doc）混在同一份文件
- 跨章節 transition 突兀

## When NOT to apply

- 純技術 library README（沒有 1990s 文化錨點可以用）
- B2B / SaaS / AI paper README（voice register 完全不同）
- 1 頁 README 不需要 voice 分層
- 上游 vanilla 專案的 README（保持上游風格不要改）

## Reference cases

- [openxcom-cht v2.27](https://github.com/wicanr2/openxcom-cht/blob/master/README.md) — 雙作（UFO + TFTD）+ Hero 信 + TFTD 8 章雜誌風 + Technical Deep Dive 三層 voice
- [pg-cht](https://github.com/wicanr2/pg-cht) — 單作 + 軍事戰術書風 + 工程文件混合
- [u6-cht](https://github.com/wicanr2/u6-cht) — Ultima VI 文言文翻譯 + 八德哲學 + 1985 Garriott 致敬

## 校對 checklist

完成編輯後逐項對：

- [ ] 三層 voice 是否區隔清楚（hero / magazine / technical）？
- [ ] 每章是否有 1-2 段 narrative 開場？
- [ ] 每張表格之後是否有 prose 收束？
- [ ] 章節之間是否有 transition 橋接句？
- [ ] 1990s 文化錨點用了 3-5 處（不要太多）？
- [ ] 譯名警告章節是否用「考古感」而非「批判感」？
- [ ] 譯者掛名（1990s 第三波 / 第三波文化 / 聯合報國際版 / 軟體世界）是否在感謝段落？
- [ ] TOC anchor 與實際章節是否 1:1 對齊？
- [ ] 重複內容是否 cross-ref 而非重複 dump？
- [ ] 技術錨點（STR_* keys / ASCII 流程圖 / Glossary 連結）是否 100% 保留？
