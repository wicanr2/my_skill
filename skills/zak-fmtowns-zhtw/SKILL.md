---
name: zak-fmtowns-zhtw
description: Zak McKracken (FM-Towns Steam 版) 繁中化的完整工具鏈、編碼陷阱與 ScummVM patch 點。當使用者談到「Zak McKracken」「Zak 中文化」「scummtr 不認 CJK」「Unknown function id 0xAB / 0xCF」「Truncated escaping」「FM-Towns 中文」「SCUMM 中文化」「chinese_gb16x12.fnt」等情境觸發。
---

# Zak McKracken FM-Towns 繁中化完整 SOP

LucasArts SCUMM v3 老遊戲的中文化路徑。表面看有兩個結構性卡點（字型 8×8 太小 + scummtr 拒收 CJK），實際兩個都可以繞過——scummtr 的「不認 CJK」是參數誤用，字型靠 patch ScummVM 走 ZH_CHN 12×12 路徑。本 skill 把所有非顯然的關鍵點記下來。

## 工作目錄結構

```
~/zak-zh/
├── original/   完整 Steam 快照（136 MB，含 ScummVM exe + PDF）
├── working/    工作副本，所有改動都在這裡（136 MB）
│   └── ScummVM/enhanced/   ← FM-Towns 遊戲資料（59 LFL + 98/99.LFL 字型 + Track*.mp3）
├── dumps/      抽出的英文 dump + 中文譯文 + 字型 BMP
├── tools/
│   ├── scummtr-0.5.1-linux86/   官方 release binary
│   ├── scummtr-src/             從 dwatteau/scummtr clone，自己 build
│   └── scummvm-src/             從 scummvm/scummvm clone，含 patch
└── sandbox_*/  各種編碼回填實驗（en/zh/big5/gb/gb_v2/zh_raw/gb_final）
```

**不可動的東西**：
- `~/.local/share/Steam/steamapps/common/Zak Mckracken/` — Steam 會驗證覆蓋
- 你自己維護的壓縮備份目錄（解壓來源，受損時靠它還原）

Steam 路徑裡實際的 FM-Towns 遊戲檔在 `ScummVM/enhanced/` 子目錄，不是最外層。同捆還有 V2/DOS 版在 `ScummVM/FDD/`（gameid `zakv2`，對照用）。

## 版本辨識（FM-Towns vs PC V2）

| 特徵檔案 | 出現於 | gameid |
|---|---|---|
| 98.LFL + 99.LFL (各 2042 bytes) | enhanced/ | `zaktowns` |
| Track1-21.mp3 (CD 音軌) | enhanced/ | `zaktowns` |
| 00-58.LFL（無 98/99）| FDD/ | `zakv2` |

`zak.ini` 寫 `platform=fmtowns`、`gameid=zak`、`path=enhanced`。

## 工具鏈速查

```bash
# 官方 binary
~/zak-zh/tools/scummtr-0.5.1-linux86/linux-x64/{scummtr,scummfont,scummrp,FontXY}

# 自 build 版（cmake + make，無外部依賴；C++11 即可）
~/zak-zh/tools/scummtr-src/build/bin/{scummtr,scummfont,scummrp,FontXY}
```

scummtr `-L` 列支援遊戲：`zaktowns` 是 FM-Towns 變體的 gameid。

## ⭐ scummtr CJK 突破（最非顯然的發現）

scummtr 0.5.1 **預設參數下會 reject** 中文 byte stream，會丟以下任一錯誤：
- `ERROR: Bad escaping in line N`
- `ERROR: Truncated escaping in line N`
- `ERROR: Unknown function id 0xAB`（Big5/GB lead byte 撞 SCUMM 0xFF/0xFE escape）

**錯誤結論**（PROGRESS.md 早期版本曾寫過、已撤回）：scummtr 不認 CJK。

**正確解法**：兩個參數一起改就過：

1. **加 `-r` (raw mode)**：bypass charset 翻譯（不是 `-c`）
2. **譯文必須 CRLF 行尾**：scummtr `_unEsc()` 對 LF-only 行尾有 byte-count bug，CRLF 修復

### 可運作的命令

```bash
# 1. 譯文 UTF-8 → CRLF
sed -i 's/$/\r/' zak_zh_draft.txt

# 2. 譯文放到 working dir，scummtr 預設讀 scummtr.txt
cd ~/zak-zh/working/ScummVM/enhanced/
cp /path/to/zak_zh_draft.txt scummtr.txt

# 3. 回填（注意是 -rwh 不是 -cwh）
~/zak-zh/tools/scummtr-0.5.1-linux86/linux-x64/scummtr \
    -g zaktowns -rwh -A aov -if

# 4. 抽英文 dump（如要 round-trip 驗證）
~/zak-zh/tools/scummtr-0.5.1-linux86/linux-x64/scummtr \
    -g zaktowns -rwh -A aov -of dump.txt
```

英文 round-trip（`-cwh` dump → 同檔 `-cwh` import → re-dump）已驗證 **byte-perfect**（85091 bytes 完全相同，diff 無輸出）。

`Bad data was found and ignored at 0x6 in 47.LFL (Block too big: 0x220F5708)` 警告是 GOG/Steam FM-Towns Zak 已知無害現象（dwatteau/scummtr FAQ 明說可忽略）。

## 編碼選擇與 0xFE 衝突

| 編碼 | 譯文大小 | 0xFE byte 數 | 0xFF byte 數 |
|---|---|---|---|
| UTF-8 | ~80 KB | 0 | 0 |
| Big5 | 66400 | 41 | 0 |
| GBK | 66400 | 89 | 0 |
| GB2312 | 63078 | **29** | 0 |
| GB18030 | 68441 | 89 | 0 |

ScummVM 端走 ZH_CHN 路徑需要 GB18030/GBK 編碼（用 `chinese_gb16x12.fnt` GB2312 字型）。Big5 對應的 ZH_TWN 路徑只支援 v7+ 遊戲，Zak v3 不適用。

UTF-8 雖無 0xFE/0xFF byte 最乾淨，但 ScummVM 處理 CJK 假設雙位元組編碼（`is2ByteCharacter`），UTF-8 3-byte 中文會被切錯。**結論：用 GBK 或 GB2312 把譯文 encode，搭配 ScummVM 端的 v3 escape patch**。

```bash
# UTF-8 → GBK + CRLF（用 Python 確保 encode 行為一致）
python3 -c "
text = open('zak_zh_draft.txt').read()
gbk = text.encode('gbk', errors='replace')
open('zak_zh_gbk.txt','wb').write(gbk.replace(b'\n', b'\r\n'))"
```

## ScummVM patch 點（路線 B）

**Patch 寫在** `~/tmp/zak/scummvm-zhtw.patch`（git apply 可直接套用）。

### Patch 1: `engines/scumm/charset.cpp` line ~126

把 `GID_ZAK` 加進 ZH_CHN 字型白名單：

```cpp
case Common::ZH_CHN:
    if (_game.id == GID_FT || _game.id == GID_LOOM || _game.id == GID_INDY3 ||
        _game.id == GID_INDY4 || _game.id == GID_MONKEY || _game.id == GID_MONKEY2 ||
-        _game.id == GID_TENTACLE) {
+        _game.id == GID_TENTACLE || _game.id == GID_ZAK) {
        fontFile = "chinese_gb16x12.fnt";
        numChar = 8178;
    }
```

### Patch 2: `engines/scumm/string.cpp` line ~1487

`drawString()` 對 0xFE escape 處理，在 ZH_CHN/ZH_TWN CJK mode 跳過（GB lead byte 不應視為 SCUMM escape）：

```cpp
- } else if ((c == 0xFF || (_game.version <= 6 && c == 0xFE)) && (_game.heversion <= 71)) {
+ } else if ((c == 0xFF || (_game.version <= 6 && c == 0xFE
+         /* ZH-CJK 模式下，0xFE 是 GB18030 lead byte，不可視為 SCUMM escape */
+         && !(_useCJKMode &&
+              (_language == Common::ZH_CHN || _language == Common::ZH_TWN))
+         )) && (_game.heversion <= 71)) {
```

預期還需要 2-3 處 minor patch（`convertMessageToString`、`addMessageToStack` 等），實機跑遊戲時迭代修補。

## ScummVM build

build deps（一次性 sudo）：

```bash
sudo apt install -y build-essential libsdl2-dev libsdl2-net-dev libfreetype6-dev \
    libpng-dev libogg-dev libvorbis-dev libflac-dev libmad0-dev libmpeg2-4-dev \
    liba52-dev libfaad-dev libfluidsynth-dev libcurl4-openssl-dev libgtk-3-dev \
    nasm pkg-config
```

build：

```bash
cd ~/zak-zh/tools/scummvm-src
git apply ~/tmp/zak/scummvm-zhtw.patch
./configure --backend=sdl --enable-release --disable-debug
make -j$(nproc)   # 8 核約 12-15 分鐘，~4500 個 .o 檔
# 產出: ./scummvm
```

注意：`git clone` 時用 sparse-checkout 不夠 build；需 `git sparse-checkout disable` 抓完整 source（約 808 MB）。

## 字型檔 `chinese_gb16x12.fnt`

格式（依 charset.cpp 推導）：
- 8178 字符 × 24 byte/字 = 196 272 bytes
- 每字 12 rows × 2 byte (12 bit + 4 bit padding)
- 排列：`index = (lead - 0xa1) * 94 + (trail - 0xa1)`
- 對映：GB2312 EUC (lead 0xa1-0xfe × trail 0xa1-0xfe)

**ScummVM 內建 fonts-cjk.dat 不含此檔**（只有 Noto Sans TTF）。三條取得路徑：

1. **找現成**：ScummVM 中文化社群（Monkey Island 等專案）的 fan-translation patch 包
2. **自製**：`~/tmp/zak/build-zh-font.py` 用 Noto Sans CJK SC 渲染 12×12 點陣（依賴 PIL + `/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc`）
3. **從老中文系統提取**：PalmOS / 老 Windows 中文系統有類似格式

字型檔放到 `~/zak-zh/working/ScummVM/enhanced/chinese_gb16x12.fnt`。ScummVM 偵測邏輯（`engines/scumm/detection_internal.h`）：只要遊戲資料夾有此檔，自動把 `_language` 設為 `Common::ZH_CHN`，不需手動指定。

## 跑遊戲

```bash
~/zak-zh/tools/scummvm-src/scummvm -p ~/zak-zh/working/ScummVM/enhanced/ zaktowns
```

如果 `chinese_gb16x12.fnt` 缺，ScummVM fallback 用英文 8×8 字型，看到的是 mojibake。

## 已知陷阱清單

| 陷阱 | 症狀 | 解法 |
|---|---|---|
| 動了 Steam 原始資料夾 | Steam 啟動會把改動覆蓋 | 只動 `~/zak-zh/working/` |
| 譯文 LF 行尾 | `ERROR: Truncated escaping in line 187` | `sed -i 's/$/\r/' file` 改 CRLF |
| 用 `-c` 對中文 | `ERROR: Unknown function id 0xAB` | 改用 `-r` raw mode |
| 譯文 UTF-8 不轉碼 | ScummVM 把 3-byte UTF-8 切錯 | 用 Python encode 成 GBK |
| ScummVM sparse-checkout build | 缺 audio/video/math 等目錄 | `git sparse-checkout disable` 抓全 |
| `chinese_gb16x12.fnt` 期望 fonts-cjk.dat 內建 | 不在 ScummVM 官方資源 | 自製或社群取得 |
| `Bad data at 0x6 in 47.LFL` warning | scummtr 每次都印 | 已知無害，忽略 |

## 翻譯草稿

`~/zak-zh/dumps/zak_zh_draft.txt`（2050 行繁中，UTF-8）由 Claude Opus 4.7 一次性翻譯：
- 完整覆蓋 2039 行英文 dump
- 保留所有 `\255\X` 控制碼與 `@@@` padding
- 開發者名單區保留原文
- 待校對：The King（貓王致敬）、雙頭松鼠新聞標題雙關語、SCUMM verb interface 慣用詞

## 工時估算

從零開始走完整路線 B：
- 環境 + scummtr 突破 + ScummVM patch 設計：**已完成**（一晚）
- ScummVM 編譯：1-2 小時（含下載依賴 + make）
- 取得/自製 `chinese_gb16x12.fnt`：自製 4-8 小時；找現成 30 分鐘起
- 實機跑遊戲 + 迭代 patch 0xFE 邊際 case：1-2 天
- 翻譯校對：2-3 天

預計總工時 4-6 天（比初估 5-7 天樂觀，因為 scummtr 不必 patch）。

## 2026-05-20 PoC 實測結果

走到 build + 實機跑為止，剩下一個 charset render crash 沒解：

### 已驗證通的部分

- ✅ scummtr 修改 `funcLen` → `funcLenSafe` 容忍未知 SCUMM function id（GBK 0xFE lead 不再炸） — patch 在 `~/zak-zh/tools/scummtr-src/src/ScummTr/text.cpp`
- ✅ Python state-machine 轉 UTF-8 → GBK 並 escape GBK trail 0x5C（「運」= 0xDF 0x5C 等字會撞 scummtr `\` 解析）：對每對 GBK 雙位元組，若 trail byte 是 0x5C，轉成 `5C 5C` 兩個 byte（scummtr `_unEsc` 看到 `\\` 還原成單一 `\`）
- ✅ ScummVM patch 三處：
  - `charset.cpp` `loadCJKFont` 加 `GID_ZAK` 進 ZH_CHN 白名單
  - `charset.cpp` `getDrawWidthIntern/getDrawHeightIntern` 移除 `assert(_cjkFont)`，nullptr 時 fallback 到 `_2byteWidth/_2byteHeight`
  - `string.cpp` `drawString()` 在 ZH_CHN/ZH_TWN 跳過 v3 SCUMM 0xFE escape
  - `scumm.cpp` `setupCharsetRenderer` 對 ZH_CHN/ZH_TWN FMTowns 用 V3 而非 TownsV3 renderer
- ✅ 自製 12×12 字型 generator `build-zh-font.py`：8178 字全 render 無 skip，196272 bytes 完全匹配
- ✅ ScummVM 偵測為 `(FM-TOWNS/Chinese (Simplified))` 自動切 ZH_CHN
- ✅ 標題畫面（ZAK MCKRACKEN AND THE ALIEN MINDBENDERS）正常顯示
- ✅ Intro 動畫第一場景（地球地圖 + alien 警報黃色閃光）跑出來

### 已知未解 issue

- ❌ **drawBits1 對 12×12 _2byteFontPtr glyph 在 V3 renderer 也 segfault**（gdb stack: `displayDialog → V3::printChar → drawBits1`）。Crash 發生在 intro 第一段對話框（Zak 的 dream sequence）渲染。
  - 推測：V3::drawBits1 path 計算 src offset 對 12×12 字型 idx 算出來可能 out-of-range
  - 或：12 寬度時，drawBits1 `pitch = dest.pitch - width * bytesPerPixel` 對 320x240 螢幕有寬度 alignment 問題
  - 下一步：
    1. gdb 抓 crash 時 src 指標值，看是否 out of `_2byteFontPtr` 範圍
    2. 在 `get2byteCharPtr` 加 bounds check，idx out of [0,8178) 時返回 safe glyph
    3. 或 patch `drawBits1` 對 width != 8 用 separate code path

### 譯文中 GB18030 4-byte 字陷阱

UTF-8 → GBK encode 時，某些字會被擴展成 GB18030 4-byte 編碼（lead byte 在 0x81-0xFE 但跟 0x30-0x39 ASCII digit）。實際統計：

| 編碼 | 0xFE byte | 0xFF byte | 0x5C trail |
|---|---|---|---|
| UTF-8 | 0 | 0 | 0 |
| Big5 | 41 | 0 | (未測) |
| GBK | 89 | 0 | 多處（「運」「橋」等繁中字）|
| GB2312 | 29 | 0 | 0 |
| GB18030 | 89 | 0 | 多處 |

GB2312 trail 範圍 0xA1-0xFE 不含 0x5C，最乾淨；但只支援 6763 簡體常用字，**繁中譯文有 476 字 unencode 會變 `?`**。所以繁中專案實務上仍須用 GBK + 0x5C escape transformer。

### Sandbox 副本快速參考

| 目錄 | 內容 | 狀態 |
|---|---|---|
| `~/zak-zh/sandbox_en/` | 英文 round-trip 驗證 | LFL byte-perfect |
| `~/zak-zh/sandbox_final/` | GBK 譯文 + chinese_gb16x12.fnt | LFL 中文已寫入 + 字型備齊；ScummVM 開到對話框前 crash |
| `~/zak-zh/working/` | 乾淨工作副本 | 原始（含產出的字型檔） |
| `~/zak-zh/original/` | Steam 完整快照 | 不動 |

### 立即可繼續的方向

1. **加 bounds check 到 `get2byteCharPtr`** — 最 minimal patch，避免 invalid idx 引起 segfault
2. **用 valgrind 跑 scummvm** 看詳細 memory access pattern
3. **改用社群字型** — 自製字型可能有 layout 問題，社群 chinese_gb16x12.fnt 可能 layout 不同（pixel row 順序、stride 等）
4. **試 Big5 編碼 + ZH_TWN 路徑** — 但 ZH_TWN 字型 `chinese.fnt` 是 16x15，要再做一份；同樣需 patch SCUMM v3 走 ZH_TWN

### 2026-05-20 下午後續

valgrind 抓到 root cause：`get2byteCharPtr` 對 FMTowns 早期 return `nullptr`（原本給 JA_JPN）。Patch（**關鍵 fix**）：

```diff
 if (!isScummvmKorTarget() && (_game.platform == Common::kPlatformFMTowns || _game.platform == Common::kPlatformPCEngine)
+    && _language != Common::ZH_CHN && _language != Common::ZH_TWN)
 	return nullptr;
```

Patch 後 ZH 版本能跑到 **Mars+Earth 太空場景 + Dream sequence Zak+Annie 相遇**，比之前多走 2 個場景。但更後面還有 silent crash，需繼續 debug。

ASCII-only 對照組（譯文中 byte >= 0x80 換成 `?`）證明流程其他部分都對 — crash 純粹在 CJK render path。

8 處 patch 全清單見 PROGRESS.md。

### 2026-05-20 下午後續 3 — 中文完全顯示成功 ✨

兩個關鍵 fix 解決所有亂碼：

**Fix 1: V3 renderer height hardcoded 為 8**

```cpp
// 原本 (charset.cpp line 893)
int CharsetRendererV3::getDrawHeightIntern(uint16) {
    return 8;  // ← CJK chr 也用這 → 12x12 字被截只剩上 8 rows
}

// Patch:
int CharsetRendererV3::getDrawHeightIntern(uint16 chr) {
    if (chr >= 256 && _vm->_useCJKMode)
        return _vm->_2byteHeight;  // ZH_CHN = 12
    return 8;
}
```

同樣 patch `getDrawWidthIntern` 對 CJK 返回 `_2byteWidth`。**這是核心 root cause** — 之前所有「亂碼」其實是 12x12 字 render 成 12x8（被截下半），加上 V3 8x8 spacing 算錯，看起來像橫條紋噪點。

**Fix 2: 字型擴到 GBK 全 range**

繁中字大多在 GBK 擴展區 (lead 0x81-0xA0)，原本 generator 只 cover GB2312 (lead 0xA1-0xFE)。

```python
# build-zh-font-gbk.py — GBK 線性 index
def gbk_index(lead, trail):
    return (lead - 0x81) * 190 + (trail - 0x40 if trail < 0x7F else trail - 0x41)
# NUM_CHAR = (0xFE - 0x81 + 1) * 190 = 23940
```

對應 ScummVM 端 `get2byteCharPtr` ZH_CHN ZAK case 改用 GBK 線性公式。`loadCJKFont` 對 GID_ZAK 設 `numChar = 23940`。

**字型選擇 — 設計師視角**

12x12 點陣中文不易識別，需 careful 選字型：

| 字型 | 12px 效果 | 評語 |
|---|---|---|
| Noto Sans CJK Regular | ❌ 太細像噪點 | 不適 |
| Noto Sans CJK Black | ⚠️ 太粗筆畫融合 | 中央太擠 |
| **WenQuanYi MicroHei** | ✅ **清晰** | **推薦** |
| WenQuanYi Zen Hei Sharp | ✅ 點陣設計 | 也好 |
| AR PL UMing TW | ⚠️ 細明體偏細 | 對比度不夠 |

`apt install fonts-wqy-microhei` 後 `/usr/share/fonts/truetype/wqy/wqy-microhei.ttc` 是最終選擇。

### 2026-05-20 深夜 — 譯文 review + auto-wrap + verb 中文化嘗試

**Auto-wrap 對話框（已 patch）**

ScummVM 預設 `addLinebreaks` 只在「半形空格」處 break，中文無空格 → 不 wrap。Patch `engines/scumm/charset.cpp` 加 byte-level CJK break：

```cpp
// CJK byte-level line break for ZH_CHN / ZH_TWN: every CJK char is a valid break point.
if ((_vm->_language == Common::ZH_CHN || _vm->_language == Common::ZH_TWN) && (chr & 0x80)) {
    lastspace = pos - 2;
}
```

Wrap 觸發條件：當行 `curw > maxwidth`。對 12x12 中文，maxwidth ~280-300px = 約 23-25 字一行。短句不 wrap，長句自動 break。

**Dialog 高度限制 → 改用 click-to-continue（已解，2026-05-20 終夜）**

對話框預設高度 16px（一行 ASCII 8x8 + margin）。CJK wrap 成 2 行 = 24px 時第 1 行會被頂到 viewport 上方外。曾嘗試 `initScreens` 把 text area 從 16→24px，但背景偏移 8px 整個畫面糊掉 → **撤回**。

**最終方案**：把 wrap 點從 `0x0D` newline 改成 `\255\003`（end-of-message + 等 click），長對話自動分頁、不撞 main virtscreen。Patch `engines/scumm/charset.cpp` `addLinebreaks()` 對 ZH 路徑：

```cpp
// CJK 模式下：wrap 點變成 \255\003 而非 0x0D
// 需插入 2 bytes (0xFF, 0x03)，把 lastspace 後面 memmove 右移
byte *breakPtr = str + lastspace;
int tail = strLength - lastspace + 1;  // +1 含 NUL
memmove(breakPtr + 2, breakPtr, tail);
str[lastspace] = 0xFF;
str[lastspace + 1] = 0x03;
strLength += 2;
pos = lastspace + 2;
lastspace = -1;
```

非 CJK 路徑仍走原 `str[lastspace] = 0x0D`。

**Verb interface 中文化嘗試**

- 譯文 verb 還原中文（推/拉/開/關/讀/拿起/是什麼 等）
- Patch `engines/scumm/verbs.cpp drawVerb` 對 ZH 加 row spacing：

```cpp
if (_useCJKMode && _2byteHeight > 8 && _game.version <= 3
    && (_language == Common::ZH_CHN || _language == Common::ZH_TWN)) {
    int verbTopline = _virtscr[kVerbVirtScreen].topline;
    int rel = vs->curRect.top - verbTopline;
    if (rel >= 0) {
        int rowIdx = rel / 8;
        adjustedYpos = verbTopline + rowIdx * _2byteHeight;
    }
}
```

**scummtr verb update 注意**：`-A aov` 中的 `v`=verbs 是「保護不被改 size」flag。verb 中文短於英文要用 `-A ao` (不含 v) 才能 resize。

**Verb hit-test 對齊（容易漏掉）**：drawVerb 把 ypos 從 `row*8` 改成 `row*_2byteHeight` 後，**`findVerbAtPos` 的 hit-test 必須做同樣的換算**，否則點擊位置會錯位（看到的 verb 跟實際 hit 的 verb 不同 row）。`curRect.top` 仍保留原始 8-aligned 值，hit-test 端在 `findVerbAtPos` 重新算：

```cpp
// engines/scumm/verbs.cpp findVerbAtPos
const bool cjkAdjustRow = _useCJKMode && _2byteHeight > 8 && _game.version <= 3
    && (_language == Common::ZH_CHN || _language == Common::ZH_TWN);
// 每個 verb 比對前：
int hitTop = vs->curRect.top;
if (cjkAdjustRow) {
    int rel = hitTop - verbTopline;
    if (rel >= 0)
        hitTop = verbTopline + (rel / 8) * _2byteHeight;
}
if (vs->curmode != 1 || !vs->verbid || vs->saveid || y < hitTop || y >= vs->curRect.bottom)
    continue;
```

**已知問題**：verb 中文化後 ScummVM 可能出現黑白條紋（palette 失效）—**這是獨立問題，跟 verb 中文化「無關」(使用者觀察)**，可能是某個 byte sequence 觸發 SCUMM v3 dual-layer mode 問題。需更深 debug。

**譯文 review (677 行修訂)**

Fork agent 後 review 對話品質，產出 `/tmp/zh_review.txt` 677 行修訂套用 484 個改動。包括：
- 人名統一：Zak→札克, Zachary→札克瑞, Annie→安妮, Melissa→梅麗莎, Leslie→萊絲莉, Jayne→珍, Sally→莎莉, Sandy→珊蒂, Ed→艾德, Edna→艾德娜
- 招牌笑話保留：The King→貓王, Caponian→卡彭星人, Skolarian→斯科拉里安
- 媽媽電話對話更口語親切
- Boss 對話嚴肅口吻
- 報紙標題保留 tabloid 噱頭
- 卡彭星人對話帶誇張戲謔

**SCUMM 控制碼速查**

| 序列 | 意思 |
|---|---|
| `\255\001` | 換行 (newline) |
| `\255\002` | 等待繼續顯示 |
| `\255\003` | 暫停等用戶 click |
| `\255\004\XX\YY` | 顯示變數值 |
| `\255\005\XX\YY` | 切換顏色 |
| `\255\006\XX\YY` | 插入物件名 |
| `\255\007\XX\YY` | 插入 actor 名 |

**Sandbox import 重要 quirks**

1. **`cp` 不覆蓋已存在 executable mode files** — 用 `rsync --delete` 或 `rm -f *.LFL` + `cp -f`
2. **scummtr -if 中途 fail 會 partial-modify LFL** — 之後再 import 撞 stale state，先 rm + cp fresh
3. **`scummio-tmp` 殘留** — import 失敗會留下 `*.LFL~~scummio-tmp`，下次 import 報「already exists」，要 `rm -f *scummio-tmp`
4. **`-A aov` 保護 verb size** — verb 中文短於英文，要去掉 `v` flag (用 `-A ao`)
5. **譯文編碼**：用 `text.encode('gbk', errors='replace')` + 0x5C escape transformer + CRLF 行尾 + scummtr `-rwh -A ao -if`

**字型 generator 演進**

- `build-zh-font.py` v1：Noto Sans CJK Regular 12px → 太細像噪點
- `build-zh-font.py` v2：Noto Sans CJK Black 12px → 太粗筆畫黏
- `build-zh-font.py` v3：GBK 全 range (擴 23940 字) 解決繁中字漏
- **`build-zh-font-wqysharp.py` 最終版**：freetype 直接 access WenQuanYi Zen Hei Sharp face 2 embedded bitmap (12px) — 真實點陣字，清晰可讀

字型載入：`face = freetype.Face(path, 2); face.select_size(0)` (face 2 = Sharp variant, size 0 = 12px)

### 譯文版本演進

| 檔案 | 內容 |
|---|---|
| `/tmp/zh_test.txt` | 原 AI 翻譯草稿（無還原） |
| `/tmp/zh_full.txt` | verb sections 英文還原（section-level） |
| `/tmp/zh_line.txt` | line-level 英文還原（<12 char 短句保留英文） |
| `/tmp/zh_polished.txt` | + 人名中譯 + 19 處短譯文 polish |
| `/tmp/zh_final.txt` | + 484 個 review 修訂套用 ← **當前最佳** |
| `/tmp/zh_verb_zh.txt` | + verb 中文化（會撞黑白條紋 — 待 fix）|

對應 GBK encoded 版各有 `_gbk.txt` 後綴。Import 命令：

```bash
rsync --delete -av ~/zak-zh/working/ScummVM/enhanced/ ~/zak-zh/sandbox_final/
cp /tmp/zh_final_gbk.txt ~/zak-zh/sandbox_final/scummtr.txt
cd ~/zak-zh/sandbox_final/
rm -f *scummio-tmp
~/zak-zh/tools/scummtr-src/build/bin/scummtr -g zaktowns -rwh -A aov -if
```

跑 ScummVM：

```bash
systemctl --user reset-failed
systemd-run --user ~/zak-zh/tools/scummvm-src/scummvm \
    --no-aspect-ratio --no-fullscreen zak-fm-cn
```

### 2026-05-20 晚 — 終局最佳配置 🎉

8 處 ScummVM patch + WQY Zen Hei Sharp embedded bitmap 字型 + line-level 譯文還原 = **可玩 Zak 中文版**！

- ✅ 對話框中文清晰：「我應該把夢裡看到的地圖畫下來。」可讀
- ✅ 彩色畫面 (TownsV3 renderer 保留 dual-layer)
- ✅ Verb interface 英文整齊（avoid 12px 中文擠 verb area）
- ✅ Inventory items 英文（avoid 擠）
- ✅ 字型 12x12 點陣（WQY 真實 embedded bitmap，非 PIL outline rasterize）

**字型 — 用 freetype-py 直接 access embedded bitmap**：

```python
# build-zh-font-wqysharp.py
face = freetype.Face('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 2)  # face 2 = Sharp
face.select_size(0)  # 12px embedded bitmap
face.load_char(ch, FT_LOAD_RENDER | FT_LOAD_MONOCHROME | FT_LOAD_TARGET_MONO)
# baseline 對齊：dst_y_start = 10 - face.glyph.bitmap_top
```

PIL TTF outline 12px 渲染太細變雜訊；WQY Sharp 真實點陣 → 設計師手繪 12x12，清晰許多。

**譯文 — line-level 還原英文**：

```python
# 對每行單獨判斷，不是整 section
en_stripped = stripped_len(en_content)  # 去 @ padding
is_short_en = (en_stripped < 12 and not '\\255' in en_content)
if is_short_en:
    用英文  # verb names, short interactions, "I'll keep it." 等
else:
    用中文  # 長對話、新聞標題、敘述
```

**避免坑點**：
- scummtr -if 中途 fail 後會 partial-modify LFL。每次 import 前 `cp -f` 強制覆蓋所有 *.LFL
- cp -r 對已存在的 file 可能不覆蓋，要 `rm -f` + `cp` 或 `cp -f`
- TownsV3 renderer 必須保留（不能改用 V3），否則 FM-Towns dual-layer color 失效 → 黑白條紋
- verb sections 整 section restore 英文太 aggressive — 會把對話也還原英文。要 line-level 判斷
- `_2byteWidth`/`Height` 對 V3 path 必須返回 _2byteWidth/Height，而非 hardcoded 8

### 完整 patch 清單 (2026-05-20 終版)

ScummVM (`engines/scumm/`)：
1. **charset.cpp `loadCJKFont`** — `GID_ZAK` 進 ZH_CHN 白名單，numChar = 23940 (GBK 全 range)
2. **charset.cpp `get2byteCharPtr`** — 對 FMTowns + ZH_CHN/ZH_TWN 不再 early return null；ZAK case 用 GBK 線性 index
3. **charset.cpp `CharsetRendererV3::getDrawWidthIntern`** — CJK 返回 `_2byteWidth`
4. **charset.cpp `CharsetRendererV3::getDrawHeightIntern`** — CJK 返回 `_2byteHeight` (**最關鍵**)
5. **charset.cpp `CharsetRendererTownsV3::getDraw*/drawBits1`** — 移除 `assert(_cjkFont)` (備用，因為改用 V3 renderer 後不會走這路徑)
6. **string.cpp `drawString`** — ZH 模式跳 v3 SCUMM 0xFE escape
7. **scumm.cpp `setupCharsetRenderer`** — ZH FMTowns 用 V3 (不是 TownsV3)

scummtr (`src/ScummTr/text.cpp`)：
8. **funcLenSafe** — CJK lead 後未知 byte 視為字面而非錯

字型 (`~/tmp/zak/build-zh-font-gbk.py`):
- WenQuanYi MicroHei 12px
- GBK linear index (lead 0x81-0xFE × trail 0x40-0xFE 跳 0x7F)
- 23940 字 / 574 KB

譯文編碼：UTF-8 → GBK + CRLF + 0x5C escape transformer

scummtr 命令：`-rwh -A aov -if` (raw mode + CRLF + 確認 verb safety)

### 2026-05-20 下午後續 2 — 突破到房間 + 中文亂碼根因

加 systemd-run --user 真 detach 跑 valgrind 後發現 **ScummVM 沒 internal crash** — 整個流程通了！

進度：
- ✅ Title → intro → dream → room 001 (Zak 房間) **完整跑出來**
- ✅ Verb interface 顯示 (Push/Pull/Open 等)
- ✅ Zak 可以走動 + cursor 工作
- ❌ **inventory + 對話框中文「亂碼」** — 用 Black Noto Sans CJK 重 render 也沒救

**亂碼根因（剛找到）**：

譯文 byte stream 統計：
- GB2312 lead 範圍 (0xa1-0xfe)：8923 byte ✓
- **GBK 擴展 lead 範圍 (0x81-0xa0)：1109 byte** ← 我自製字型沒覆蓋
- Other：0

我的 `build-zh-font.py` 只 render GB2312 (8178 字)，但譯文中 1109 個 byte 對應 GBK 擴展字 (0x81-0xa0 lead)。ScummVM 的 ZH_CHN idx 公式 `(lead-0xa1)*94 + (trail-0xa1)` 對 lead < 0xa1 算出**負數**，patch 的 bounds check 把它 clamp 到 idx=0 → render 同一個 glyph → 看起來像「噪點/亂碼」。

**解法（下次接續）**：

1. **擴充 generator cover 完整 GBK** (lead 0x81-0xFE, ~23940 字)，並 patch ScummVM 公式：
   ```cpp
   // ScummVM 公式需從「GB2312 區位碼」改成「GBK 線性 index」
   case Common::ZH_CHN: {
       int lead = idx % 256;
       int trail = idx / 256;
       // GBK 線性 index (0x81-0xFE × 0x40-0xFE 但跳 0x7F)
       int t = trail - (trail < 0x7F ? 0x40 : 0x41);
       idx = (lead - 0x81) * 190 + t;
   }
   ```
   字型檔變大 ~24x 大 (4.5 MB)，需要 patch `loadCJKFont` 設 numChar 對應

2. **或譯文預處理**：把 GBK 擴展字替換成 GB2312 內近似字 (用 OpenCC 簡繁轉換工具)

3. **或用 GB18030 4-byte 編碼**：但 ScummVM 沒有 GB18030 路徑

### 當前 sandbox 狀態（下次接續位置）

- `~/zak-zh/sandbox_final/` — minimal 譯文 + chinese_gb16x12.fnt (Black, 12x12 GB2312 only)
- `~/zak-zh/working/ScummVM/enhanced/chinese_gb16x12.fnt` — 同上
- `~/zak-zh/tools/scummvm-src/` — patched (8+ 處 patch in charset/string/scumm.cpp)
- `~/zak-zh/tools/scummvm-src/scummvm` — patched binary 可跑
- `~/zak-zh/tools/scummtr-src/build/bin/scummtr` — patched scummtr (funcLenSafe)
- ScummVM config: `~/.config/scummvm/scummvm.ini` target `zak-fm-cn` 指向 sandbox_final

跑命令：

```bash
DISPLAY=:1 systemd-run --user \
    ~/zak-zh/tools/scummvm-src/scummvm \
    --no-aspect-ratio --no-fullscreen zak-fm-cn
```

debug log:
```bash
~/zak-zh/debug-dream.sh  # valgrind wrapper
```

### Files 在 `~/tmp/zak/`

- `PROGRESS.md` — 詳細進度
- `scummvm-zhtw.patch` — 原始三處 patch (v1)
- **`scummvm-zhtw-v2.patch` — 最新合併 patch (8 處改動，含關鍵 get2byteCharPtr fix)**
- **`scummtr-cjk.patch` — scummtr CJK-tolerant funcLenSafe patch**
- `install-deps.sh` — sudo apt install script
- `build-zh-font.py` — Noto Sans CJK 12×12 字型 generator
- `test-zh.sh` — 回填 + 試跑 script

## 物件名批次翻譯（2026-05-20 晚）

`scummtr -of` dump 出來譯文中 verb 上方的 ON (object name) / OC (object class) sections 是英文。逐筆翻成中文太慢；**用 dict patch 一輪一輪自動取代**：

1. Dump 譯文檔（`/tmp/zh_verb_zh.txt`）裡所有 ON/OC 英文短句抽出來
2. AI 一次翻譯成中文 dict（`"door" → "門"`, `"rock" → "石頭"` 等）
3. Python script 對譯文檔做 replace（要小心避開已是中文的部分）
4. Re-encode UTF-8 → GBK + 0x5C escape → CRLF
5. Import 到 `~/zak-zh/sandbox_final/`
6. 跑遊戲檢查，補翻沒覆蓋到的 token
7. 重複 3-4 輪直到只剩冷僻 token

實測 4 輪後 359 個英文 ON/OC 翻到剩 15 個（多是含 `\255` 控制碼的 `Y A K - 1` 等特殊名）。tool 在 `~/zak-cht/tools/translate-objects.py`。

## Release repo `~/zak-cht/`

對外發佈 git repo（origin: `git@github.com:wicanr2/zak-cht.git`）。

```
zak-cht/
├── README.md
├── LICENSE              MIT for original work
├── NOTICE.md            版權合規說明
├── docs/                5 篇中文 docs（patch清單/字型方案/控制碼速查/編碼import/進度）
├── patches/
│   ├── scummvm-zhtw.patch
│   └── scummtr-cjk.patch
├── tools/
│   ├── build-zh-font-wqysharp.py
│   ├── encode-gbk.py
│   ├── translate-objects.py
│   └── import-to-game.sh
├── translations/zh_verb_zh.txt
├── screenshots/
└── vendor/
    ├── scummvm/         GPLv3+ — 修改過的 charset.cpp / string.cpp / verbs.cpp / scumm.cpp
    │                    + COPYING + AUTHORS + MODIFICATIONS.md
    │                    (上游 commit f4526cf007688d02b8c558f048f0889088545fd5)
    └── scummtr/         MIT — 修改過的 text.cpp
```

**版權合規關鍵**：因為 release 包內含修改過的 ScummVM binary（GPLv3+），必須附 source；放在 `vendor/scummvm/` + `MODIFICATIONS.md` 滿足 GPL「accompanying source」要求。

**Release 包**（不在 git 內，太大）：`~/zak-cht-build/`
- `zak-cht-linux-x86_64.7z` (82 MB) — patched ScummVM binary + game data
- `zak-cht-linux-x86_64.AppImage` (95 MB)
- `zak-cht-windows-x86.7z` (64 MB) — MinGW i686 cross-compile

Windows cross-compile：`scummvm-win-src/` configure 時加 `--host=i686-w64-mingw32`，deps 在 `~/zak-cht-build/mingw-deps/`。注意 `make distclean` 後要重 build Linux binary（同 source tree 切換 target）。

## 相關 skill / 檔案

- [[panzer-general-wine]] — 另一個老遊戲繁中化（PG，Win32 PE patch）

歷史產出檔（早期 PoC 在 `~/tmp/zak/`）：
- `PROGRESS.md` — 詳細進度報告
- `scummvm-zhtw.patch` / `scummvm-zhtw-v2.patch` — 早期 patch 版本
- `install-deps.sh` — sudo apt install script
- `build-zh-font.py` / `build-zh-font-gbk.py` — 字型 generator 早期版

當前正式產出檔請看 `~/zak-cht/`（release repo）。
