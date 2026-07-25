---
name: eten-bitmap-font
description: 用「倚天中文系統」(ETEN 3.53) 的原生點陣字當老遊戲繁中化的字形來源——比 TTF rasterize 更對味的 1990s DOS 中文字。涵蓋 stdfont.15(16×15 漢字)/spcfont.15(符號區,漏帶會讓標點全 fallback)/ascfont(ASCII)/STD.24x(24 點六種字體,ETUNPACK 壓縮)的檔案格式、Big5 分區索引公式(已實測驗證)、與專案自訂碼表(cht_codec)對接、字模尺寸與排版格解耦(kCJKLogicalWidth + 置中)。觸發:「用倚天字形/ETEN 字型」「老遊戲中文化要原味 DOS 點陣字」「16×15 / 24×24 CJK 點陣字來源」「stdfont.15 / spcfont.15 / STD.24M 怎麼解」「Big5 點陣字抽字烘 fnt」「標點變成別的字型/fallback」。**retro CJK 中文化的字形預設來源**:16×15 與 24×24 都優先用倚天,而非 WQY/TTF rasterize。
---

# 倚天點陣字 (ETEN) 當 retro 中文化字形來源

1990s DOS 中文遊戲的中文長什麼樣,倚天中文系統就長什麼樣。做老遊戲繁中化時,**用倚天原生點陣字比拿現代 TTF rasterize 更對味**(TTF 縮到 12–24px 會糊、筆劃比例不對;倚天是為該尺寸手工調的點陣)。**本 kb 是 retro CJK 的字形預設來源**。

## 檔案格式(ETEN 3.53 光碟,已實測驗證)

| 檔案 | 內容 | 尺寸 | stride | 字數 | 狀態 |
|---|---|---|---|---|---|
| `STDFONT.15` | 漢字區 | 16×15 | 30 B | 13094 | ✅ 裸格式,直接可讀 |
| `SPCFONT.15` | **全形符號/標點** | 16×15 | 30 B | 408 | ✅ 裸格式 |
| `SPCFSUPP.15` | 符號補充 | 16×15 | 30 B | 365 | ✅ 裸格式 |
| `ASCFONT.15` / `.24` | ASCII 半形 | 8×15 / 16×24 | 15 / 48 B | 256 | ✅ 裸格式 |
| `STD.24M/K/L/R/B/S` | 24 點漢字,**六種字體**(明/楷/隸/圓/黑/宋) | 24×24 | 72 B | 13094 | ⚠️ **ETUNPACK 壓縮**,需解 |

點陣佈局:**每列 `(W+7)/8` bytes,MSB-first**,由上而下。`stride = rowBytes × H`。

### Big5 分區索引(關鍵,不是線性)

```python
def raw(hi, lo):                       # Big5 → 線性序號
    return (hi-0xA1)*157 + ((lo-0x40) if lo < 0x7F else (lo-0x62))

LAST_SPC    = raw(0xA3,0xBF)           # 符號區尾 = 407
BASE_A440   = raw(0xA4,0x40)           # 漢字區起點
LAST_COMMON = raw(0xC6,0x7E)           # 常用字尾
BASE_C940   = raw(0xC9,0x40)           # 次常用起點
N_COMMON    = 5401

r = raw(hi, lo)
if   r <= LAST_SPC:    idx = r;                             font = SPCFONT   # 符號區
elif r <= LAST_COMMON: idx = r - BASE_A440;                 font = STDFONT   # 常用字
else:                  idx = N_COMMON + (r - BASE_C940);    font = STDFONT   # 次常用
```

**驗證 oracle**:`STDFONT.15` 的 `idx=0` 必須是「一」(一條橫線);「中」(A4A4)、「猴」(B555) dump 成 ASCII art 必須可辨識。**先過這關再往下做**,否則整批字會整體偏移(看起來像「有字但都不對」)。

### [雷] `STDFONT` 只有漢字,標點在 `SPCFONT`

`STDFONT.15` 從 A440(「一」)起,**不含 A140–A3BF 的全形標點**。只帶 STDFONT 去烘字,`，。！？「」『』（）《》～` 全部會落到 fallback 字型 → 畫面上「字是倚天、標點是另一種字」很突兀。**一定要一起帶 `SPCFONT.15`。**(MI2 實測:漏帶時 19 字 fallback,帶了之後只剩 3 字。)

### [雷] Python `big5` codec 對不上的字要手動映射

少數全形符號的 Unicode 對應在 codec 與 Big5 表之間有歧義(如 `～` U+FF5E vs U+301C),`ch.encode('big5')` 會丟例外。用手動表補:

```python
MANUAL_BIG5 = {"～": b"\xa1\xe3"}
```

### 真缺字才 fallback

Big5 沒有的字(簡體字、罕用字)才用 TTF(WQY)烘同尺寸補。MI2 實測 2430 字中僅 `嘞 嗬 酞` 3 字(0.12%)。**fallback 數量是品質指標**:若一大批字掉進 fallback,先懷疑索引公式或漏帶 SPCFONT,不要無腦補字型。

## 與專案自訂碼表對接(最容易錯的一步)

倚天字型以 **Big5** 排列;而中文化專案的 `.fnt` 常以**自訂碼表**排列(如 `cht_codec`:字按出現順序連續配碼位)。兩者是**不同的碼空間**,必須逐字轉換:

```
碼表的字 (Unicode) → encode Big5 → 倚天 idx → 取 glyph → 寫進「該字在自訂碼表的碼位」對應 offset
```

**絕不可**用 `bytes([lead,trail]).decode('gb2312'/'big5')` 反推字元(那是把自訂碼位當標準編碼解讀)→ 會整批錯位成亂碼。

## 字模尺寸 vs 排版格(移植到引擎時)

字模尺寸換了,**排版不該跟著變**。把兩者解耦:

- **排版格寬固定**為原版邏輯字寬(SCUMM ZH_CHN = `kCJKLogicalWidth = 12`),斷行/游標推進一律用它 → 換任何字模都不破版、不疊字。
- **字模在格內置中**:`ox = (cellW - glyphW)/2`、`oy = (cellH - glyphH)/2`(`cellW = 12 × multiplier`)。24×24 時 ox/oy=0(no-op),16×15 時各 +4 → 字距均勻。

### 視覺大小取捨(選 16×15 還是 24×24)

視覺大小 = 字模寬 ÷ 畫布寬:

| 字模 | 畫布 | 佔畫面 | 觀感 |
|---|---|---|---|
| 12×12 | 320 | 3.75% | 原版基準(糊) |
| **24×24** | 640 (2×) | **3.75%** | **與原版同大、細節 2×** ← 想「一樣大但清楚」選這個 |
| **16×15** | 640 (2×) | **2.5%** | 比原版小 1/3,原味 DOS 點陣、小巧銳利 |

**要「和原版一樣大又清晰」→ 24×24;要「原汁原味 DOS 點陣」→ 16×15。** 別把 16×15 硬放大成 24(非整數倍放大點陣字必醜)。

## ETUNPACK(24 點字型的壓縮殼)

`STD.24*` 開頭是 `ETUNPACK V1.00`,offset 0x20 附近帶內含檔名 `stdfont.24`。解開後應為 `13094 × 72 = 942,768` bytes(同樣的 Big5 分區索引)。光碟內可能附倚天自己的解包程式,先找再逆向。解得開就等於免費拿到**六種**倚天 24 點字體。

## 相關

- 尺寸/畫布策略見 `rulebook/81-retro-cjk-hires-canvas.md`(拉畫布別縮字)。
- SCUMM 實作(text surface ×2、底圖 nearest 放大、清除座標)見各 SCUMM 中文化 template。
