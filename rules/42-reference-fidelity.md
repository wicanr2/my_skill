# 參考保真度(Reference Fidelity)— 指定 reference 就逐項照抄,別憑記憶替換

使用者說「**參考 X 專案 / 照 X 的作法 / 先前 X 都做過**」時,X 是一個**已經驗證能動的事實來源**。
你的工作不是「自己重想一套」,是**先打開 X、逐項對照、採用 X 的 proven values**;每一個偏離 reference
的點都要有**明確、講得出口的理由**,且該理由不能是「我記得 / 我以為 / 慣例上」。

> 來源:FOA 中文化打包,CLAUDE.md 寫 `@~/willy`、使用者一再說「參考 willy 的經驗」「先前 willy 都做過」。
> willy 的 `build.yml` 白紙黑字 `runs-on: macos-14`,我沒去讀,憑「Intel macos-13 相容性較好」的假設
> 自己填 `macos-13` → 該 runner 已退役 → CI run 卡 queued 48 分、燒掉兩個 dead run。

## 硬規則

- **[HARD] 被指定 reference,動手前先實際讀它的對應檔案。** `@路徑`、「參考 X」、「X 做過」=
  先 `Read` / `grep` X 的那份 config / script / workflow,把它的具體值(版本標籤、依賴清單、旗標、流程順序、
  目錄結構)抓出來當預設,**不要憑記憶或訓練印象重建一套**。沒讀過 reference 就產出,等於沒參考。
- **[HARD] 偏離 reference 的每個點都要標明理由。** 確實有理由偏離(如「willy 用 brew sdl2、但使用者明確要自編
  universal」)→ 採用偏離、**並說出為什麼**。沒有理由的偏離 = 預設照抄 reference。**reference 用什麼版本/標籤,
  你就用什麼**,除非有具體證據要改。
- **[HARD] 外部版本標籤會退役,不能憑記憶寫死。** CI runner image(`macos-13`/`ubuntu-20.04`)、base image
  tag、SDK / 語言版本、action 版本都有生命週期。要嘛**從一個「現在還是綠的」reference 抄現用標籤**,要嘛
  當場查當前可用版本(`gh`、registry、release page),**別寫一個你記憶中存在、實際已下架的標籤**。

## 訊號 → 診斷(別誤判成程式 bug)

- **CI job「queued 很久 + 執行時間 0s / 0m」** = runner 標籤不存在或已退役/無可用機器,**不是 YAML 語法錯、
  不是程式 bug**。第一件事去比對「一個正在動的 reference 用哪個 runner 標籤」,不要瞪 build script。
- **reference 能動、我的不能動** → 第一步是 **diff「我的設定」vs「reference 的設定」逐行**,差異點就是嫌疑犯
  (承 `82-cross-platform-port-verification` 第 3 條「能跑的那個變體會遮住 bug,先比對構造差異」)。

## 反模式(這次踩的)

- ❌ CLAUDE.md `@~/willy` + 使用者說「參考 willy」,卻沒開 willy 的 `build.yml` 就自己填 runner。
- ❌ 用「Intel 相容性較好」這種**記憶裡的慣例**覆蓋掉 reference 的 proven 選擇(reasoning by analogy)。
- ❌ 寫死一個記憶中的版本標籤(`macos-13`),不查它是否還在線上。
- ❌ 「參考」只參考了精神(走 GitHub Action、自編 SDL2),**沒參考到具體值**(runner 版本)—— 半套參考
  比沒參考更危險,因為你以為你照做了。

## 何時套用

- 使用者給 `@路徑` / 說「參考 X / 照 X / 仿 X / X 做過 / 上次怎麼弄的」/ 指一個範例專案、範例檔、現有實作。
- 寫任何含**外部版本標籤**的東西:CI workflow(runner image / action 版本)、Dockerfile(base image tag)、
  lockfile 外的版本 pin、SDK / toolchain 版本。
- 多平台打包、CI 設定、複製既有 pipeline 到新專案。

## 與其他 rule 的關係

| Rule | 關係 |
|---|---|
| `41-first-principles` | 「憑記憶/慣例替換 reference」就是 reasoning by analogy;本檔是它在「有現成 reference」場景的特化 |
| `82-cross-platform-port-verification` | 「能跑的變體遮住 bug,先比對構造差異」——本檔把它前移到「動手前先抄 reference 的值」 |
| `62-static-provenance-trace` | reference 的值是靜態可讀的源頭,先靜態讀出來,別憑印象 |
| `40-learning-loop` | 「先驗證再下結論」——reference 的實際內容就是要先驗證的事實 |

## Reference

- 反例(本 rule 來源):FOA-CHT,`@~/willy` 指定卻沒抄 `runs-on: macos-14` → 寫成退役的 `macos-13`。
