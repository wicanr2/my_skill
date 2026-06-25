---
name: retro-keyboard-to-touch
description: 把「鍵盤操作」的老遊戲 / SDL C 引擎移植到 Android / 觸控的方法論——核心是「不重寫輸入,讀引擎每畫面的 keymap 動態渲染 context-aware 觸控控制,手指事件合成 SDLK_* 餵回原事件迴圈」。觸發:「把老遊戲移植到 Android」「設計觸控 UI / on-screen 控制」「鍵盤遊戲改觸控」「keyboard game → touch」「SDL2 android-project 移植」「openkb / King's Bounty / CRPG 手機版」「UX 設計畫面 / 觸控覆蓋層」。配 retro-game-remake(母方法論)、retro-game-playtest(存檔/唯讀 cwd 雷)。
---

# 鍵盤老遊戲 → 觸控 / Android 移植

把鍵盤操作的 1980s–90s 老遊戲(尤其 SDL C 引擎的 CRPG)搬上 Android / 觸控。**這是 port,不是打包**:輸入模型、生命週期、存檔路徑、資產載入都要改;桌面打包(AppImage/dmg/exe)是另一回事。

## 何時啟用
- 把鍵盤驅動的老遊戲 / SDL 引擎做成 Android / 觸控可玩。
- 設計遊戲的 on-screen 觸控控制(D-pad、虛擬按鈕、情境鍵)。
- 不確定觸控怎麼對應一堆鍵盤快捷的 CRPG/策略選單。

## 最高原則:不重寫輸入,讓引擎自己告訴你能按什麼

老 SDL 遊戲幾乎都用「**每個畫面一張 keymap / context 表**」描述當下有效的按鍵,再 `KB_event()` / `SDL_WaitEvent` 等輸入。**這就是觸控設計的金礦**:

```
進畫面 → 讀「當前 keymap 的有效鍵清單」→ 只渲染這畫面真的能按的觸控控制
手指點控制 → 合成一個 SDL_KEYDOWN(SDLK_*) → 餵進「原本的事件迴圈」→ 引擎主流程零改動
```

- **不要**自己造一套輸入狀態機去對應遊戲邏輯——你只是把「手指 → 鍵碼」翻譯一層。
- **不要**全畫面塞滿按鈕:讀 keymap → 畫面切換時控制列自動跟著換(選單浮 A–E、地圖浮方向鍵、Y/N 浮兩顆)。context-aware 才不擋畫面。
- 先 grep `SDLK_` 統計遊戲到底用哪些鍵 / 在哪些情境,別憑感覺設計。

## 設計先行(UI 先於 code),且視覺稿用 SVG 不要 ASCII

觸控手感是這類移植的**成敗關鍵**,先把界面設計定下來再寫 code:

1. **列輸入**:`grep -rhoE "SDLK_[A-Za-z0-9_]+" src/*.c | sort | uniq -c | sort -rn` → 知道要做哪些控制。
2. **定控制方案**(下節)。
3. **產視覺稿**:每個代表畫面一張 mockup。**用 SVG(向量,GitHub 直接渲染,中文清楚),不要 ASCII art**(醜、不好對齊)。寫個純文字 SVG 產生器(無相依),日後改設計重跑即可;要 PNG 預覽用 `rsvg-convert` 或 chrome-headless。
4. **簽核後**才進實作骨架。可把設計階段合併進 main 當 milestone(`--no-ff` + tag),實作續在 feature branch。

## 控制方案(可重用 pattern;拇指優先、少用收進選單)

| 控制 | 對應鍵 | 位置 / 時機 |
|---|---|---|
| 虛擬 D-pad(+滑動) | ↑↓←→ | 左下;移動 / 清單上下 / 走位 |
| A / B 主鈕 | Enter·Space / ESC | 右下;**D-pad+A/B 就能跑完所有「方向+確認」型畫面** |
| 情境快捷列 | 該畫面字母選項(讀 keymap) | 隨畫面浮現;`[A 接任務][B 租船]…` |
| 直接點選單那一行 | = 送該行字母 | 文字清單畫面;情境列是其顯式備援 |
| 數字步進器 `[−] 12 [+]` | 0–9 + Enter | 數量輸入時才出現,免叫全鍵盤 |
| 原生 IME | 文字 | 命名等;`SDL_StartTextInput()` 吃 `SDL_TEXTINPUT`,**不自製鍵盤** |
| ☰ 系統選單 | F-keys / 存退 / 讀檔 | 右上;不常用的收進去不佔畫面 |
| 清單捲動 ▲▼ | PageUp/Down | 長清單旁 |

**兩種手感讓玩家切**:點擊模式(選單,直接點項目)、手把模式(地圖/戰鬥,D-pad+A/B 放大);可依畫面型態自動偏好。

## 踩雷(這些最容易在真機才炸)

1. **存檔路徑**:Android 的 cwd / APK 是**唯讀**。存檔必須走內部儲存——`SDL_AndroidGetInternalStoragePath()` / `getFilesDir()`。用相對 cwd 寫檔=靜默失敗(與 `retro-game-playtest` 的「唯讀 cwd 存檔失敗」同源雷)。
2. **資產**:`data/`、字型 atlas 等打包進 APK `assets/`;用 `SDL_RWops`(SDL android 會轉走 AAssetManager)直讀,或首次啟動解到內部儲存。**別假設檔案在 cwd**。
3. **生命週期**:SDL android 的 pause/resume(來電、切背景)會丟 `SDL_APP_WILLENTERBACKGROUND` 等;GL context 可能失效要重建。離開要存檔(每條離開路徑都存,呼應 playtest skill)。
4. **觸控人體工學**:目標 **≥48dp**;控制**半透明**(~60%)、長按可暫時淡出看畫面;支援**左右手對調**;避開瀏海/手勢條(WindowInsets);**橫向為主**設計。
5. **觸控 → 合成鍵**:在 SDL 事件層把 touch 轉成 `SDL_KEYDOWN/UP`,**塞回原事件佇列**(`SDL_PushEvent`),不要繞過引擎自己解。按下/放開都要送(有些引擎吃 keyup)。
6. **方向的「按住連續移動」**:D-pad 要支援按住重複觸發(repeat),否則地圖一步一點很痛苦。
7. **headless 測不到觸控**:真機(或 emulator)實測才算數,呼應 `retro-game-playtest`(CI 綠 ≠ 可玩)。

## 分期(feature branch 上做)

1. **界面設計 + SVG 視覺稿**(本 skill 重點;簽核後合 main 當 milestone)。
2. **SDL2 android-project 骨架** + NDK build 全 C 源 + assets 打包 → 先求「跑得起來、看到畫面」。
3. **觸控覆蓋層**:D-pad + A/B + ☰ → 先讓地圖能走、選單能用 Enter/ESC。
4. **情境快捷列**(讀 keymap)+ 直接點選單項目。
5. **數字步進器、命名 IME、存檔路徑**。
6. **手感打磨**(透明度、左右手、portrait/landscape、repeat)+ **真機實測**。

## SVG mockup 產生器(recipe)

純 Python 輸出 SVG 字串(無相依):helper 畫 phone 邊框 + 遊戲畫布示意 + 控制元件(`dpad/rbtn/pill/hamburger/stepper/ime`),每畫面一個函式組合。中文 `font-family` 帶 CJK fallback。產出後 `rsvg-convert -w 1180 x.svg -o x.png` 肉眼檢查重疊。文件用 `![](mockups/xx.svg)` 嵌入(GitHub 會渲染 SVG)。

## Reference case
- **openkb-cht**(御封戰將 / King's Bounty Android port):`docs/android/ui-design.md` + `docs/android/mockups/*.svg` + `gen_mockups.py`。核心洞見即「讀 openkb 每畫面的 `KB_event` keymap → 動態觸控」。
- 姊妹 skill:`retro-game-remake`(逆向+乾淨重寫母方法論)、`retro-game-playtest`(存檔/唯讀 cwd/正常玩家路徑雷)、`classic-mac-c-game-sdl-port`、`mac-app-cross-pack`(桌面打包)。
