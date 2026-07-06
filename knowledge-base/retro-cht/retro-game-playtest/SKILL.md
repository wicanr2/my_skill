---
name: retro-game-playtest
description: 老遊戲 remake / 移植的「正常玩家路徑」實機驗證(game tester)。專治「headless CI 全綠、但玩家一開就壞」這類 bug——預設視角錯、存檔寫不進唯讀目錄、視窗縮放偏移、dump 時機遮住真相。觸發:使用者說「game tester」「實機驗證」「能不能玩」「進去就壞 / 卡住 / 沒畫面 / 不存檔」「驗證 remake 可玩性」「老遊戲測試」,或剛打包完老遊戲要驗收。配套 retro-game-remake(重製)/ retro-cjk-hires-canvas / retro-game-cht-readme。
---

# retro-game-playtest — 老遊戲 remake 實機可玩性驗證(game tester)

## 核心鐵則(這就是為什麼需要它)

**headless `--frames 0` dump 會 PASS,但玩家真的開來玩可能整個壞掉。** ctest/CI 綠 ≠ 可玩。
必須另外走**玩家真的會走的路徑**,看**玩家真的會看到的畫面**。

> 真實教訓(火龍之戰 remake,2026-06):CI 37/37 + 四平台 headless smoke 全綠,但玩家開 AppImage:
> ① 預設是俯視彩格不是第一人稱 3D(`fp_mode` 預設 false)② 離開不存檔(存檔路徑相對唯讀
> cwd + 關窗 SDL_QUIT 直接 break 不 autosave)③ 抱怨畫面偏移(視窗 logical-size)。
> **這三個 headless dump 全測不到。** 這正是 `retro-game-remake` skill 第 1 條雷的延伸。

## 會抓到、headless 測不到的 bug 類別

1. **預設狀態錯**:預設視角 / 模式 / 難度與玩家期待不符(top-down vs first-person)。headless 用顯式旗標(`--fp`)繞過了預設。
2. **唯讀 cwd 存檔失敗**:存檔走 cwd 相對路徑,但 AppImage(squashfs)/ macOS `.app` / Android assets 的 cwd 是**唯讀掛載** → 寫檔失敗。要存到使用者可寫目錄(XDG / APPDATA / App Support / `getFilesDir`)。
3. **離開不存檔**:只有某條離開路徑 autosave(F10/Esc),關窗(SDL_QUIT)/Q 直接 break。每條離開路徑都要存。
4. **真實視窗 ≠ headless dummy**:`SDL_RenderSetLogicalSize` / letterbox / 縮放偏移**只在真實視窗**出現;headless dummy 視窗 == logical 不縮放 → 測不到。要 xvfb + 真窗截圖或 non-headless dump。
5. **dump 時機遮真相**:plain `--dump` 常抓「按鍵套用前」的早幀 → 移動/狀態變化沒反映,讓你**誤判移動卡住或誤判正常**。要用 `--dump-frame N`(按鍵之後的幀)。
6. **測錯對象**:只測 `build/` binary,沒測**實際打包產物**(AppImage/zip/.app)在它自己的執行環境(cwd、相對路徑、bundled 字型/dll)。
7. **平台分歧**:同一段程式在不同 OS 行為不同 → 只在 Linux 驗會漏。實戰(御封戰將,2026-06):
   - `KB_errlog` 在 Linux 印 stderr(噪音),在 **Windows 卻彈 `MessageBox`**(阻斷玩家)→ Linux 判定的「無害 log」在 Windows 是擋路的牆。
   - 設定相對模組路徑 `data/free/` 撞上引擎自動前綴 `datadir=data` → `data/data/free/`(**雙重前綴**)→ Win/Mac 全檔讀不到、解析回 NULL → 連鎖崩潰。**AppImage 用絕對路徑(`buf2[0]=='/'`)跳過前綴故倖免** → 只有 Win/Mac 中招。
   - macOS CI binary 預設 arm64-only(macos-14 runner)→ Intel Mac 跑不起來,需 universal build。

## 跨平台移植驗證(Win/Mac 別只信 Linux;用 Wine/VM 跑目標平台)

**「Linux native 重現不出」≠「不可重現」。** 跨平台打包 bug 常只在目標平台現形:

- **第一動作不是向使用者要 backtrace,是自己在目標平台重現。** Windows → `wine`(host 端,WINEPREFIX 放 `$HOME` 非 `/tmp`,Xvfb 獨立 display,`timeout -s KILL` 有界);Mac 無機器時靠 CI macos runner / 程式碼推理 + Wine 旁證。
- **「能跑的變體」會遮 bug**:一個打包正常(AppImage/絕對路徑)、其他不正常(Win/Mac/相對路徑)時,先比對**路徑構造差異**,別假設同份 config 到處能用。
- **verbose flag 一兼兩用**:出貨預設靜默(把 resolve 失敗等噪音從 `errlog` 改 `debuglog`),診斷時開(`KB_VERBOSE=1`)印出**字面路徑** → 一眼看到 `data\data/free/` 才破案。修復與診斷是同旗標兩面。
- **`-g` + `addr2line` 跨平台定位**:mingw PE 帶 DWARF,`addr2line -e openkb.exe <fault VMA>` 直接給 `file:line`(Windows 崩潰也能在 Linux 上定位,免猜)。Wine page fault 訊息會給 `at address 0x14002A051`,PE 預設 base `0x140000000`。
- **NULL 防護打最底層共用葉節點**:根因 `KB_strlist_ind(NULL)` 一處 deref → 修它一個保護所有呼叫端,勝過逐一 call site。資料缺失應一路 NULL-safe 回退到內建預設(`bounty.c` 表)/ 上游模組,不可 deref。
- **Wine 限制**:`xdotool` 合成鍵常送不進 Wine 下的 SDL app(事件轉譯)→ 改用「引擎層證據」(`FAILED TO OPEN=0`、模組數、`page fault=0`、log 進度)判定,不必硬驅動 UI。

## 方法(game tester 三件事)

1. **驅動正常玩家路徑**(非 debug hook、非顯式繞過旗標):
   title → 新遊戲 → 建角 → 進遊戲(看預設視角)→ 移動/轉向 → 踩事件 → 存檔 → **關窗離開** →
   重開讀檔還原 → 戰鬥 → 物品/角色表 → 結局。用真實鍵序(`--keys`)+ 最小必要旗標。
2. **擷取玩家真的會看到的畫面**(PNG),兩種:
   - 一般狀態:引擎自身 `--dump`(**配 `--dump-frame N` 抓按鍵後的幀**)。
   - 偏移/縮放/真窗類:`xvfb-run` 跑 **non-headless** + 真窗截圖(或 non-headless `--dump`,會經真實 renderer/logical-size)。
3. **判讀**:① 目視每張截圖(人或 agent 讀 PNG:是不是該有的視角?偏移?亂碼?文字對?怪出現?)
   ② 機械檢查(存檔檔案有落地且非空、讀檔還原隊伍/座標、全程不崩、退碼 0)。

## 落地工具:game_tester harness

可重複的 harness(火龍之戰版 `opendw_remake/tools/verify/game_tester.sh`)產出**截圖藝廊 + 機械 PASS/FAIL**;
目視判讀由人或 **agent 讀 PNG** 完成(headless 無法自動判「這是不是第一人稱」)。骨架:

```bash
run(){ DWR_SAVE_DIR=<可寫> SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy "$BIN" --bundle "$B" --mute "$@"; }
shot(){ python3 -c "from PIL import Image;Image.open('$1').save('$2')"; }   # ppm→png 供 Read
# 01 title / 02 建角 / 03★進遊戲預設視角 / 04 移動後(--dump-frame!) / 05★存檔落地 /
# 06★讀檔還原 / 07 戰鬥 / 08 物品欄 / 09 結局 → 每步 dump + 機械 assert
# 05: rm save; run --keys S; [ -s "$SAVE" ] || FAIL "存檔壞"
# 06: run --load "$SAVE"; grep "load applied" || FAIL "讀檔壞"
# 04: cmp 03 04 → 相同則 FAIL「移動卡住」(且務必 --dump-frame 抓按鍵後幀,否則假性相同)
```

**用 agent 當 game tester**:派一個 sub-agent 跑 harness + **逐張讀截圖**比對「期待視覺」清單 + 回報問題。
這層是 headless 給不了的(autonomous「看畫面對不對」)。

## 判讀 checklist(每個 checkpoint 的期待視覺)

- 進遊戲:**第一人稱透視走廊**(地板/天花/側牆收斂),不是俯視格盤 / 大地圖。
- 移動後:視角/牆面**改變**(撞牆則露出邊界但仍正常渲染)。
- 文字:在地化正確、不截斷、不亂碼、CJK 銳利。
- 存檔:離開後檔案**落在可寫目錄且非空**;重開「繼續」回到原隊伍 + 座標。
- 戰鬥:怪物立繪出現 + 指令列 + 戰報。
- UI:無偏移 / 無黑邊吃掉內容 / 縮放後文字仍對齊像素層。

## 收尾

- 抓到的每個 bug:修 → **重跑 game tester**(不是只重跑 ctest)→ 截圖確認 → commit。
- 把新發現的 bug 類別補進本 skill(累積老遊戲常見地雷)。
- 驗**打包產物本身**(解開 AppImage/zip/.app 在其 cwd 跑),別只驗 `build/`。

## 來源
火龍之戰(Dragon Wars)繁中 remake 2026-06 收尾:玩家實機回報「卡大地圖/沒3D/不存檔」,
而 CI 全綠 → 萃取此 game-tester 方法 + `game_tester.sh` harness。配 `retro-game-remake`(第 1 條雷:
「一定要驗無 debug 的正常玩家路徑」)。

跨平台分歧章節來源:御封戰將(openkb)繁中 2026-06,GitHub issue 回報 Windows/macOS 選角後
`Critical Error: Unable to resolve DAT_*` + 閃退,而 Linux(native free/full)完全正常。三層根因
(Windows MessageBox / NULL deref / 相對路徑雙 data)只有 Wine + `KB_VERBOSE` + `addr2line` 才挖到。
