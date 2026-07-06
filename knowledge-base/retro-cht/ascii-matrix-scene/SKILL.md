---
name: ascii-matrix-scene
description: 產出全螢幕終端 ASCII art 動畫(Matrix Katakana 背景雨 + 共用 angle 繞 Y 軸 turnaround 的 3D billboard + 水平行進 sprite 縱隊,單一 canvas/cmap/mask 協議 + 防閃爍)。觸發:「做 ASCII 動畫」「matrix 風格 ASCII」「全螢幕 3D ASCII 場景」「終端螢幕保護」「把 PNG/icon 變 ASCII 並 turnaround」「ASCII 雨加 3D 物件」,或改 ~/ascii-art/(尤其 dna_matrix.py 衍生)。
---

# ASCII Matrix Scene Skill

## 何時用此 Skill

啟動條件 (任一即可):

- 「做一個 ASCII art 動畫」「matrix 風格 ASCII」「終端螢幕保護」
- 「全螢幕 3D ASCII 場景」「ASCII 雨 + 3D 物件」
- 「把這張 PNG / icon 變成 ASCII 並讓它 turnaround」(尤其當對方附 PNG/JPEG)
- 「在 ~/ascii-art/ 加一個 X」/「dna_matrix.py 再加 Y」/「融合 A 和 B 變成 ascii art」
- 「擴充現有 ASCII 動畫」「加坦克 / 飛機 / 旗幟 / 文字 標題到 matrix」

**不適用**:

- 真實 GUI 圖像生成 → 用 PIL / chrome-headless / SVG
- ASCII 直接渲染靜態圖(image → ASCII converter)→ 用 `jp2a` / `chafa`,本 skill 不做純轉檔
- 需要鍵盤輸入互動 / 遊戲邏輯 → 那是 TUI(用 curses / textual),不是這裡的單向動畫
- HTML / 網頁版動畫 → 自己寫 HTML canvas(本 skill 不做)

## 核心架構

| 元件 | 角色 | reference 範例 |
|------|------|----------------|
| **3D billboard 物件** | 一組 `(x, y, z, kind)` 點,共用全域 `angle` 繞 Y 軸旋轉,kind 決定字元/顏色 | `build_helix` (DNA 雙股 + 鹼基) / `build_badge` (Panzer 菱形) / `build_castle` (Ultima I 城堡) |
| **Bitmap font** | 3×5 像素字典 → 像素映射到 model `(x, y)` 點,kind='title' | `build_castle()` 內 FONT dict |
| **Sprite 圖層** | 水平/垂直移動的多字元 sprite,有 step + render | `TankConvoy` (上排朝右、下排朝左) |
| **背景 Matrix 雨** | Katakana 字元雨,mask 為 False 的格子才會被填 | `Rain` class + `fill_rain()` |
| **Shared canvas/cmap/mask** | 所有 render 都寫進同一張 H×W 字元/顏色/佔位矩陣 | `main()` 內 canvas/cmap/mask 三個 list |
| **Atomic 主迴圈** | alt-screen + 整幀組成 list 後 single write | `frame_buf = [HOME]` … `sys.stdout.write(''.join(frame_buf))` |

## Reference template

`templates/dna_matrix.py` 是凍結版的 2026-05 reference。新增動畫**從它複製改名**,不要從零寫。

```
HELIX / ULTIMA / PANZER 場景 (~766 lines, 25 KB)
├── ANSI 常數 (HIDE/SHOW/CLEAR/HOME/ALT_ON/ALT_OFF/RESET/BOLD)
├── 物件色盤 (S1_*, S2_*, R_*, B_*, C_*, M_*)
├── 字符集 (MCHARS, BASE)
├── cleanup(*_)
├── build_helix() / build_badge() / build_castle()
├── Rain class
├── TANK_SPRITES_R/L + TankConvoy class
├── fill_rain(canvas, cmap, mask, rain)
├── render_helix / render_badge / render_castle
├── serialize(canvas, cmap)
└── main()
```

## 渲染協議 (極重要)

所有 render 函式都遵守同一個介面:

```python
def render_X(pts, angle, cx, cy, zone_w, zone_h, w, h, frame_n, canvas, cmap, mask):
    """繪製 X 到 canvas,佔據 (cx, cy) 為中心、zone_w × zone_h 的螢幕區。"""
```

- **pts**: `[(x, y, z, kind), ...]` 由對應 `build_X()` 產出
- **angle**: 全域旋轉角度,所有物件共用 → 同步 turnaround
- **cx, cy, zone_w, zone_h**: 螢幕分配給此物件的中心與區域,scale 從 zone size 推
- **w, h**: 整個畫布尺寸(用來做 bounds check)
- **frame_n**: 用來做閃爍、shimmer、相位等動畫
- **canvas[iy][ix] = ch**: 寫字元
- **cmap[iy][ix] = ansi_color_string**: 寫顏色(None = RESET)
- **mask[iy][ix] = True**: 標記「這格被佔了,雨水跳過」

**所有 render 必須三個都寫**(canvas + cmap + mask)。漏寫 mask → 雨水會蓋掉你的字元。

## Layout 公式

`main()` 內依 W, H 算出每個物件的 zone。Reference template 用的:

```python
# 左欄上半 = castle, 左欄下半 = badge, 右側 = helix
castle_cx = W * 3 // 16;  castle_cy = max(5, H // 4);  castle_zw = W * 5 // 16; castle_zh = max(8, H // 2 - 2)
badge_cx  = W * 3 // 16;  badge_cy  = min(H - 5, (H * 3) // 4); badge_zw = W * 5 // 16; badge_zh = max(8, H // 2 - 2)
helix_cx  = W * 5 // 8;   helix_cy  = H // 2;            helix_zw = W * 3 // 4;  helix_zh = H - 2
```

加新物件時思考:它要佔哪一欄、要不要跟既有物件搶位置、scale 公式怎麼讓它在 80 ≤ W ≤ 200 都長得正常。

## 新增物件的標準流程

### 1. 設計階段:看圖找出特徵

- 多色?多型?有沒有標題文字?
- 主要形狀是什麼幾何體(菱形 / 城堡輪廓 / 飛機側視 / 機甲)?
- 旋轉後該長怎樣 — 正面、側邊、背面 face 字元如何切換?
- 跟既有物件如何視覺區分(顏色 / 字元密度 / 位置)?

### 2. 模型階段:寫 `build_X()`

- 用 `fill_rect(xmin, xmax, ymin, ymax, density, kind)` 取點
- 三角(尖頂)用 `fill_triangle(cx, base_w, ybase, peak_h, kind)`
- 旗幟、星星等小物件直接 `pts.append((x, y, z, 'flag'))`
- Bitmap font (3×5 px) 處理文字 — 見 `build_castle()` 標題段

### 3. 著色階段:加色盤常數

色盤命名慣例 `X_DESCRIPTION`(例 `C_WALL_F` = Castle wall front)。
顏色用 ANSI 256 色 `'\033[38;5;NNNm'`,參考 reference 已用色號避免衝突。

### 4. 渲染階段:寫 `render_X()`

- 算 `face = abs(cos(angle))` → 0 = 側邊,1 = 正面 → 切字元/亮度
- 用區域 z-buffer (`zbuf_local` dict) 處理同物件內遮擋
- 「總是畫在上面」的元素(旗、星、窗光)bypass z-buffer
- 結尾務必三個都寫:`canvas[iy][ix] = ch; cmap[iy][ix] = col; mask[iy][ix] = True`

### 5. 整合階段:更新 `main()`

- `X_pts = build_X()` 在迴圈外
- 算 zone(cx/cy/zw/zh),寫進 layout 區
- 在合適順序呼叫 `render_X(X_pts, angle, ...)`
  - 順序決定遮擋:後渲染的會覆寫先渲染的(同一格)
  - 標準順序:castle → badge → helix → sprites → rain (rain 用 mask 跳)

### 6. 驗證階段

```bash
# 語法 + smoke test
python3 -c "import ast; ast.parse(open('NEWFILE.py').read()); print('OK')"

# headless 跑幾幀,檢查 painted cells 數量隨 angle 變化
python3 -c "
import sys; sys.path.insert(0, '~/ascii-art')
import importlib, mod; importlib.reload(mod)
# ... 直接 call build/render,驗 mask 統計
"

# 實跑 0.5s
timeout 0.5 python3 NEWFILE.py 2>&1 > /dev/null; echo "exit=$? (124=timeout 正常)"
```

## Sprite 圖層模式 (TankConvoy)

當需要水平/垂直移動的多字元 entity(坦克縱隊、飛機編隊、子彈、粒子):

```python
class XYZSprite:
    SPRITES_R = [('sprite_chars', 'color'), ...]
    SPRITES_L = [...]  # 反向版本(箭頭在另一邊)

    def __init__(self, w, h):
        self.tanks = []   # 命名隨意
        self.resize(w, h)

    def resize(self, w, h):  # 重建 sprites,接終端尺寸變化
        ...

    def step(self):          # 推進位置,出界回收
        ...

    def render(self, canvas, cmap, mask):  # 寫進 shared canvas
        ...
```

在 `main()` 的迴圈中:
- terminal resize → 也 resize sprite layer
- 每幀:`layer.step()` → `layer.render(canvas, cmap, mask)`
- 順序通常在 3D 物件後、`fill_rain` 前(讓 sprite 蓋在 3D 物件上,但雨跳過 sprite)

## Anti-flicker checklist

主迴圈必備:

```python
sys.stdout.write(ALT_ON + HIDE + CLEAR)  # 進 alt screen,隔離 scrollback
sys.stdout.flush()
try:
    while True:
        # ... 動畫邏輯 ...
        frame_buf = [HOME]
        frame_buf.append(title_bar + '\n')
        frame_buf.append('\n'.join(serialize(canvas, cmap)))
        frame_buf.append('\n')
        frame_buf.append(status_bar)
        sys.stdout.write(''.join(frame_buf))   # 整幀一次 write
        sys.stdout.flush()
        # ...
finally:
    sys.stdout.write(ALT_OFF + SHOW + RESET + '\n')
    sys.stdout.flush()
```

`cleanup(*_)` 也要 `ALT_OFF + SHOW + RESET`,並 hook 在 SIGINT / SIGTERM。
**不要每幀寫 CLEAR**,只在 resize 時。每幀的位置同步靠 `HOME`,內容由 alt screen 緩衝。

## 字元 cheat sheet

ASCII art 常用字元(從 dna_matrix 萃出):

- **塊**: `█ ▓ ▒ ░ ▌ ▐ ▀ ▄`(densities)
- **形**: `◆ ◇ ◉ ● ◐ ◓ ◑ ◒ ◣ ◢ ◤ ◥ ▣ ▤ ▦ ▪`
- **線**: `═ ║ ─ │ ┃ ┄ ┅ ╤ ╧ ╔ ╗ ╚ ╝`
- **箭**: `▶ ◀ ▲ ▼ ← → ↑ ↓`
- **星**: `★ ☆ ✦ ✧ ✶ ✷`
- **Matrix 雨字元**: `ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ`
- **DNA**: `A T G C` + 鹼基對

## 命名與檔案配置

- 動畫存放於 `~/ascii-art/<name>.py`
- 一個場景一個檔,不共用 utility(reference template 自包含,複製即可)
- 命名:主題為主(`dna_matrix.py`, `space_battle.py`, `castle_siege.py`),不冠日期
- 跑法 docstring 統一:`# 跑法: python3 ~/ascii-art/X.py` + `# 離開: Ctrl+C`

## 不要做的事

- ❌ 不要每幀 `CLEAR`(整螢幕清除 = 大閃)
- ❌ 不要分多次 `sys.stdout.write` + flush(中間狀態會閃)
- ❌ 不要忘記 `mask[iy][ix] = True`(雨會蓋掉你)
- ❌ 不要為了「未來抽象化」把 build/render 拆到多檔(reference 自包含的設計是故意的)
- ❌ 不要 emoji(終端寬度不一致,排版會亂);要視覺效果用 Unicode 幾何字元
- ❌ 不要把實作放在 `/tmp/`(重開機消失,使用者實際被坑過)

## 範例對話開頭

當對方說「再加個 Y」時,標準回應流程:

1. 開 `~/ascii-art/dna_matrix.py` 確認現有 layout
2. 看附圖(若有)→ 整理特徵
3. 套上面「新增物件的標準流程」5+1 階段
4. 寫完先語法檢查 + headless smoke test,再讓對方 `python3 ~/ascii-art/X.py` 看效果
5. 微調(scale / 顏色 / 位置)→ 收到「OK」才算交付

## Maintenance

- Reference template (`templates/dna_matrix.py`) 是凍結版。`~/ascii-art/dna_matrix.py` 後續若大改,可以更新此 template,但保留 commit message 說明版本演進
- 新增可重用 building block(例如新的 Sprite 型別、新的 3D 模型 helper)→ 寫進此 SKILL.md 而不是放到 template,template 維持「整段 copy 即可用」
