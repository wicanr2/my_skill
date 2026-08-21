---
name: asan-native-crash-hunting
description: 用 AddressSanitizer 追 C/C++ 原生程式的記憶體錯誤(越界、use-after-free、重複釋放)。觸發:「玩一陣子就 crash」「偶爾閃退」「在我這台正常在別台會掛」「隨機崩潰」「記憶體越界」「segfault 但重現不了」「加 ASan」「sanitizer」,或改完緩衝區/繪圖/解碼相關程式碼要驗收。適用 ScummVM/SDL 遊戲、C++ 服務、任何自己編得出來的原生程式。
---

# ASan 追原生崩潰

## 為什麼「跑跑看」測不出來

**越界寫**通常會很快炸,因為它破壞了別人的資料。但**越界讀**不會 —— 它只是讀到隔壁的記憶體,拿到一個「看起來合理」的值,程式照樣往下跑。會不會出事取決於當下的記憶體佈局:那塊記憶體有沒有被映射、裡面是什麼。

於是同一份程式:

- 在 A 機器上跑一整晚沒事,在 B 機器上五分鐘就掛
- 加了一行 `printf` 之後就不再重現(佈局變了)
- 開發機正常,玩家那邊隨機閃退

這類 bug **測試次數再多也證明不了什麼**。要抓它必須改變遊戲規則:讓「讀到不該讀的位置」這件事本身變成可觀測的事件,而不是等它剛好造成後果。這就是 ASan 在做的事。

## 原理(知道它抓得到什麼、抓不到什麼)

編譯時插樁 + 執行時替換配置器,兩件事:

1. **Redzone**:每塊配置出來的記憶體前後都夾一段毒化的區域。碰到它就報錯。
2. **Shadow memory**:用 1/8 的額外記憶體記錄「每 8 bytes 的可定址狀態」。每次載入/儲存前先查表。

推論出三件實務上很重要的事:

- **抓得到**:heap/stack/global 的越界讀寫、use-after-free、use-after-return、double-free、部分記憶體洩漏(LeakSanitizer)。
- **抓不到**:邏輯錯誤、整數溢位、資料競爭、未初始化讀取(那是 MSan)、GPU 端與跨 process 的問題。**ASan 乾淨不等於程式正確。**
- **抓不到「在同一塊配置內部」的越界**:例如 struct 裡從欄位 A 越界寫到欄位 B、或陣列在一塊大 buffer 內部越界。redzone 在配置的邊界上,配置內部沒有邊界可言。這是最常見的漏抓情境。

代價:速度約慢 2 倍、記憶體約 3 倍。互動式程式仍可正常操作,不影響手動測試。

## 怎麼編

編譯與連結**都要**帶旗標,少一邊會連結失敗或靜默失效:

```bash
CXXFLAGS="-fsanitize=address -fno-omit-frame-pointer -g -O1" \
LDFLAGS="-fsanitize=address" \
./configure …
make -j$(nproc)
```

- `-fno-omit-frame-pointer`:沒有它 stack trace 會殘缺。
- `-g`:要有符號才看得到行號。
- `-O1`:`-O0` 太慢(互動測試會卡到不能玩),`-O2` 以上可能把出事的那行 inline 掉,行號變得難讀。

### [HARD] 編在獨立的樹,不要就地編

原本的 `.o` / `.a` 沒有插樁,混在一起時那些部分**不會被檢查**,而且不會有任何提示——你會得到一份「掃描乾淨」的假結果。

```bash
# 複製原始碼,排除既有的 build 產物
tar cf - --exclude="*.o" --exclude="*.a" --exclude=".git" . | tar xf - -C /path/asan-src
cd /path/asan-src && rm -f config.mk config.h
```

同一個坑的另一種形狀:mingw 交叉編譯時,共用樹裡殘留的 ELF `.o` 會被 mingw ld **靜默跳過**,症狀是「符號明明有定義卻連結失敗」。凡是換工具鏈或換旗標,一律用乾淨的樹。

## 怎麼跑

```bash
ASAN_OPTIONS="detect_leaks=0:halt_on_error=1:print_stacktrace=1" ./program …
```

- `detect_leaks=0`:先關掉 LeakSanitizer。找崩潰時,一堆「程式結束時沒釋放」的噪音只會蓋住重點;要查洩漏時再單獨開一輪。
- `halt_on_error=1`:預設就是這樣,寫出來是為了明確。

### 一個 process 只報第一顆錯

除非編譯時加 `-fsanitize-recover=address` 並設 `halt_on_error=0`,ASan 報完第一顆就會中止。這件事直接決定了測試設計:

**每個情境要各跑一輪獨立的 process,不要指望一次跑完全部。** 第一顆錯會把後面的都遮住,而被遮住的那些不會有任何跡象。

## 情境矩陣怎麼設計

隨機亂測的覆蓋率很差。有效的作法是**沿著程式碼的分支點展開**:哪裡有 `if` 決定走不同的記憶體路徑,就讓每一邊都跑到一輪。

以疊層合成為例,實際用過的五個情境:

| 情境 | 為什麼要單獨一輪 |
|---|---|
| 基準倍率 | 整數倍映射,最單純的路徑 |
| 非整數倍(x3) | 升採樣的索引計算在非整數倍時才會踩到邊界 |
| 高倍率(x4) | 等同高 DPI 螢幕回報物理像素的條件 |
| 另一種後端 | 每像素 2 bytes vs 4 bytes,是完全不同的程式分支 |
| 開比例校正 | 多一次 200→240 拉伸,緩衝區大小不同 |

每輪跑完先確認**條件真的生效**(例如印出實際的疊層尺寸)。倍率參數沒吃到的話,那一輪等於白跑,但結果看起來一樣是「乾淨」。

操作要密集且涵蓋不同子系統:移動、選單開關、存讀檔、視窗縮放、場景切換。互動用 `xdotool` 自動化,搭配 Xvfb 在容器裡跑。

## 判讀報告

```
ERROR: AddressSanitizer: heap-buffer-overflow on address 0x... at pc 0x... 
WRITE of size 1280
    #1 stretch200To240Nearest(...)   graphics/scaler/aspect.cpp:123
    #3 SurfaceSdlGraphicsManager::internUpdateScreen()
0x... is located 0 bytes to the right of 614400-byte region
```

讀的順序:

1. **`WRITE` 還是 `READ`、size 多少** —— WRITE 通常更急;size 是一次操作的位元組數,`1280` 這種數字往往等於「一列的寬度 × 每像素位元組」,能直接反推是哪個迴圈。
2. **`located N bytes to the right of M-byte region`** —— `to the right` 是越過尾端,`to the left` 是往前越界。`M` 是那塊配置的大小,拿它去反推「應該是幾乘幾」通常一眼就看出算錯在哪(`614400 = 640 × 480 × 2`)。
3. **stack trace 的第一個自己的函式** —— 前幾層常是 libc 或 sanitizer 自己的框架,往下找到專案內的檔名才是現場。
4. **配置點的 trace**(報告後半段會印 `allocated by thread T0 here`)—— 確認那塊記憶體當初是照什麼尺寸配的。

沒有 ASan 時的替代品:平台原生的 crash report 也有等價資訊。macOS 的 crash log 會印 `KERN_INVALID_ADDRESS at 0x...` 加上記憶體區段圖,若出事位址正好是某塊 region 的**結束位址 +1**,那就是越界,和 ASan 的 `0 bytes to the right` 是同一回事。這在只有玩家端 log、沒辦法自己重現時特別有用。

## 驗收:一定要做同條件前後對照

「修完之後掃描乾淨」單獨看沒有意義——可能是修正有效,也可能是這一輪剛好沒走到那條路徑。要的是**同一組條件、同一份操作腳本**下的前後對照:

```
修正前:1 顆 heap-buffer-overflow(stretch200To240Nearest)
修正後:0
```

而且**不能只驗「沒有崩潰」**。如果改的是顯示邏輯,還要確認畫面是對的——把越界的那行刪掉當然不會再越界,但畫面也沒了。

## 實戰紀錄

ScummVM AGOS 中文化(2026-07):

| 問題 | 怎麼發現的 |
|---|---|
| 疊層合成越界(高 DPI 下升採樣索引衝出來源畫面) | 玩家的 macOS crash report。出事位址 = 那塊 buffer 結束位址 +1 |
| 比例校正重複套用寫出緩衝區 | **ASan**。修完上一顆之後掃出來的第二顆 |
| 字型檔損毀時照著檔頭讀過界 | 讀程式碼時發現,補上檔頭驗證 |

三顆都用 ASan 的前後對照驗收。值得注意的是:**第一顆修好之後才掃得到第二顆**——第一顆會先中止 process,把第二顆完全遮住。這是「一個 process 只報第一顆」的實際後果,也是為什麼修完一顆要重新掃一輪,而不是假設剩下的都乾淨。

## 什麼時候該換工具

| 症狀 | 工具 |
|---|---|
| 越界、use-after-free、double-free | ASan |
| 未初始化的值被使用 | MSan(要整條依賴鏈都插樁,門檻高) |
| 多執行緒資料競爭 | TSan(不能和 ASan 同時開) |
| 整數溢位、對齊錯誤、null deref 等未定義行為 | UBSan(可與 ASan 同時開) |
| 不能重編、只有 binary | Valgrind memcheck(慢 10–50 倍,但不用重編) |
| 邏輯錯、狀態機錯 | 都不是。要插樁印狀態或反組譯 |

## 常見誤判

- **「ASan 乾淨 = 沒問題」**:它只涵蓋記憶體安全,而且抓不到同一塊配置內部的越界。
- **就地編**:混到未插樁的 `.o`/`.a`,掃描結果會是假的乾淨。
- **只跑一輪**:第一顆錯會遮住後面所有的。
- **忘了確認情境生效**:參數沒吃到,結果一樣印「乾淨」。
- **只驗不崩潰**:改顯示邏輯時要一併看畫面。
- **忘了關 LeakSanitizer**:滿版的洩漏報告會把真正的越界蓋掉。

## Reference

- [AddressSanitizer 演算法與 redzone/shadow memory 設計](https://github.com/google/sanitizers/wiki/AddressSanitizer)
- [ASAN_OPTIONS 旗標清單](https://github.com/google/sanitizers/wiki/SanitizerCommonFlags)
- 專案實例:`~/scummvm/elvira_cht/workplace/docs/TESTING.md`(headless 互動測試怎麼搭)、
  `docs/AGOS_PITFALLS.md` §3.2–3.6(那幾顆越界的完整根因)
