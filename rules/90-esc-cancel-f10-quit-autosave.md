# ESC = cancel only · F10 = quit + auto-save + confirm dialog

**核心**：互動式 app（CLI 之外的 GUI / TUI 遊戲 / wizard 流程）裡的離開語意，**必須**分成
「取消當前操作」與「結束整個 app」兩條完全不同的路徑。**ESC 永遠是前者**。

本 rule 從 [wizardry-1-cht v1.25.3 game-tester 回報事件](https://github.com/wicanr2/wizardry-1-cht/commit/e70dfe2)
萃取：QA agent 兩次誤觸 ESC 把 60 分鐘 progress 噴掉 → 鐵則化。

## 鐵則

### 1. ESC 只能取消，不能結束

| 場景層級 | ESC 行為 |
|---|---|
| 子選單 / 對話框 / picker | 關閉這個 sub-mode，回上層 |
| 場景級（戰鬥 / 商店 / 旅館）| 回上一個 scene（Castle / EdgeOfTown）|
| **最外層選單**（EdgeOfTown / 主選單）| 回 Title，**不能 kill main loop** |
| Title 畫面 | 不做事 OR 進入確認流程，**不能直接 exit** |

**Why**：使用者按 ESC 的肌肉記憶是「我按錯了，回去」。任何 ESC 路徑造成不可逆損失（沒存檔的進度、未提交的編輯、買到的 IAP）= **設計失誤**。

**How to apply**：每加一個新場景時，先想清楚 ESC 對應的「上一層」是什麼。寫 unit 或 smoke test 證明 ESC 不會 `return false` 主迴圈。

### 2. F10（或 Ctrl+Q）是唯一的離開手勢

選擇單一鍵作為**明確的「我要離開」訊號**。建議 F10（單鍵、跟 ESC 在物理鍵盤上分開）或 Ctrl+Q（保留 Ctrl 慣例）。

**禁止**：
- ❌ ESC = 在某個場景退出（破壞 ESC 一致性）
- ❌ 視窗叉叉按下 = 直接 exit（沒給確認機會）
- ❌ Alt+F4 / Cmd+Q 直接 kill（OS 級事件也應該攔截到 dialog 流程）

**How to apply**：在全域 input handler 加 F10 監聽，所有「離開」入口（menu L)eave Game、視窗關閉事件等）都路由到同一個 quit-dialog state。

### 3. 結束遊戲必須跳 Yes/No dialog

按下 F10 → 不能直接 exit，**必須**先彈出確認視窗：

```
+----------------------------------+
|        確定離開遊戲？             |
|                                  |
|  離開前會自動存檔到 Slot 1。      |
|                                  |
|  Y / Enter — 存檔退出             |
|  N / ESC   — 取消                 |
+----------------------------------+
```

UI 要求：
- **置中 modal**、translucent 黑色 scrim 暗化背後場景
- 標題用 accent 色強調
- **Yes 按鍵明確**（Y 或 Enter）
- **No 按鍵明確**（N 或 **ESC**，因為 ESC = cancel 的鐵則延伸到這個 modal）
- 不可有「**確定**」「**取消**」這種模糊雙按鈕；要有單鍵 yes/no 對應

### 4. Yes 一定先 auto-save，再 exit

按下 Yes 之後的順序**必須**是：

```
save_game(state, default_save_path())  // 先存
↓
return false                            // 才退出主迴圈
```

**理由**：玩家明確選了 Yes = 他相信你不會吃他的存檔。Save 失敗時（disk full / 權限問題）必須回頭顯示錯誤訊息 + 不退出，**不能默默吞掉**。

**例外**：title 場景 / 還沒進遊戲狀態時可以不存（沒東西可存）。但其他每個場景都要存。

## 實作模式（C++ / SDL2 範例）

```cpp
// 1. State 加 flag
struct State {
    bool quit_dialog_active = false;
    ...
};

// 2. 主 tick() 最頂層處理 dialog 覆蓋
bool tick(State& state, const SDL_Event* ev, const UI& ui) {
    if (state.quit_dialog_active) {
        if (ev && ev->type == SDL_KEYDOWN) {
            auto k = ev->key.keysym.sym;
            if (k == SDLK_y || k == SDLK_RETURN) {
                save_game(state, default_save_path());
                return false;  // 主迴圈退出
            }
            if (k == SDLK_n || k == SDLK_ESCAPE) {
                state.quit_dialog_active = false;
                return true;
            }
        }
        draw_quit_dialog(ui);
        return true;
    }

    // 3. F10 全域熱鍵
    if (ev && ev->type == SDL_KEYDOWN && ev->key.keysym.sym == SDLK_F10) {
        state.quit_dialog_active = true;
        return true;
    }

    // 4. 場景級 ESC 永遠只 back 一層
    // ...
}

// 5. L)eave Game 選單路由同一個 dialog
if (target == Scene::Quit) {
    state.quit_dialog_active = true;
    return true;  // NOT return false
}
```

## 反模式（會踩雷）

- ❌ ESC 在最外層直接 `return false` — QA 誤觸丟進度
- ❌ F10 / Quit 路徑沒有確認 → 玩家手滑直接結束
- ❌ Dialog 用 OK/Cancel 兩按鈕但 ESC 預設選 OK → ESC 意義崩壞
- ❌ Save 失敗時靜默 exit — 玩家不知道存檔沒寫進去
- ❌ Title 畫面 ESC = exit + 其他畫面 ESC = back — 不一致

## When to apply

- 任何 GUI / TUI / interactive CLI app
- 有「狀態值得保留」（存檔、編輯中的文件、購物車、未提交的表單）
- 多層次選單結構（>= 2 層）

## When NOT to apply

- 純一次性 CLI（`grep`、`ls`）— ESC 沒語意
- Vim 等以 ESC 為**模式切換**的特殊應用（ESC = 進 normal mode 是它的鐵則之一，跟這條不衝突）
- 對話 chat 介面（按 Enter 送、按上下換歷史，沒有「結束」概念）

## Reference case

- [wizardry-1-cht v1.25.3](https://github.com/wicanr2/wizardry-1-cht/commit/e70dfe2) —
  原本 ESC 在 EdgeOfTown 直接 `return false`，QA agent 兩次誤觸丟進度。
  修法：state.quit_dialog_active flag + F10 全域熱鍵 + 三個 Scene::Quit
  短路徑改路由到 dialog + draw_quit_dialog() centred modal。
