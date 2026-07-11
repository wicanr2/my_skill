# Retro CJK:拉高內部畫布,別縮字 (Hi-Res Canvas for CJK)

**核心鐵則**:老遊戲(320×200 / 640×400 等固定低解析)做 CJK 中文化時,**不要把中文字縮小去塞原本的小字位**。正解是 **拉高引擎內部畫布解析度,把原始低解析底圖用 nearest-neighbor「pixel scaling」放大**,中文字用正常點陣尺寸(16×16 / 24×24)畫在放大後的畫布裡。

> 這件事被重複問過很多次。**預設就照本規則做,不要再問使用者「要不要縮小字/用幾 px 邏輯字」**。預設:畫布拉 640×480(或 4:3)、CJK 24×24、底圖 crisp 放大。除非使用者明確另指定。

## 為什麼

- 中文筆畫多,縮到原版 ~8px 邏輯字 = 糊成一團、不可讀。
- 反過來把 24px 硬畫進 320 寬的邏輯緩衝 = 單行容不下幾個字、UI 全破版。
- 兩難的解法不是二選一,而是**換維度**:把整個內部畫布放大(例 320×200 → 640×480),原始 pixel art 用整數 / nearest 放大保持銳利,中文字此時有足夠空間用 24×24,排版衝擊最小。

## 作法(recipe)

1. **拉高內部畫布常數**:找引擎的 `SCREEN_W/H`、`VGABUF_W/H`、`kScreenWidth/Height` 之類,改成放大值。
   - 優先 **4:3(如 640×480)** 讓方塊字不被垂直拉伸;或取**原解析整數倍**(320×200→640×400)讓底圖最乾淨。
   - 兩者取捨:640×480 觀感方正但底圖需 400→480 比例映射;640×400 是乾淨 2× 但非 4:3。
2. **底圖 nearest-neighbor 放大(crisp)**:原始低解析 framebuffer / 背景圖用**最近鄰**放大,**不要雙線性**(雙線性會糊掉 pixel art)。雙線性平滑版另做成獨立選項(如 1024×768 smooth)。
3. **舊版面座標重映射**:原始 UI/選單是為舊尺寸排的 → 加 `mapY()` / `mapX()` 比例映射,把 widget 位置換算到新畫布(例 400→480);寬不變時 X 不動,在原尺寸時為 no-op。
4. **CJK 走獨立點陣路徑**:中文碼點用固定點陣 atlas(16/24)畫在新畫布;ASCII 仍走原字型路徑。UTF-8 在繪字迴圈解碼分流。
5. **提供 crisp / smooth 兩種顯示版本**:nearest(銳利,推薦)與 bilinear(平滑 HD)做成不同 patch / 選項。
6. **變體 —— 引擎已內建 upscale 模式時,別自改畫布常數,直繪 display buffer**:有些引擎本身就有「邏輯低解畫布 → display 高解緩衝」的 upscale 機制(如 ScummVM SCI 的 `GFX_SCREEN_UPSCALED_640x400`)。這時**不必也不該去改 `SCREEN_W/H`**——讓底圖照引擎既有 nearest 放大(原畫不動),但 CJK 字**跳過 logical→display 的 nearest,用 `putPixelOnDisplay` 之類 API 以整數倍直接畫進 display buffer**。效果:同畫面「英文/底圖 art 仍是放大的原畫、中文字銳利」。關鍵是認出引擎有沒有現成 upscale 咽喉點,有就站上去(改動更小、不破壞原 render 管線),沒有才回到第 1 點自改畫布常數。

## 踩雷 (gotchas)

- **raw 座標 widget**(如小地圖 minimap)直接畫在舊座標空間 → 別重複套 mapY,單獨處理。
- **滑鼠命中區**:點擊座標到達時是新畫布空間 → hit-test 也要一起映射。
- **SDL2 相容**:smooth 版的 `SDL_SetTextureScaleMode` / `SDL_HINT_RENDER_SCALE_QUALITY` 在舊版 SDL2 設定不當會啟動 segfault,要做版本相容判斷。
- **整數 vs 非整數縮放**:非整數放大(如 320→ 任意寬)即使 nearest 也會出現不均勻 pixel,優先整數倍或固定目標解析。

## 何時套用

- 任何固定低解析 retro 引擎的 CJK 中文化:DOS 320×200、SCUMM、1oom(MOO1)、FreeSynd…。
- 出現「中文字太小看不清」「24px 塞不進原版 UI」「縮放後底圖糊掉」的取捨時,直接套本規則,不要退回「縮小字」方案。

## Reference cases

- **freesynd-cht**(極道梟雄,FreeSynd GPLv3):`patches/02-hd-640x480-crisp.patch`(640×480 + nearest + `Menu::mapY` 400→480)、`patches/03-hd-1024x768-smooth.patch`(1024×768 bilinear + SDL2 相容修正)。https://github.com/wicanr2/freesynd-cht
- **master-of-orion-1-cht-1oom**(銀河霸主,1oom):320×200 → 640×480,底圖 pixel-scale,CJK 24×24。
- **jones_in_the_fast_lane**(人生劇場,ScummVM SCI1 VGA):**變體(recipe 6)**——不改畫布常數,`ZH_TWN` 時切引擎既有 `GFX_SCREEN_UPSCALED_640x400`,art 照引擎 2× nearest,中文字用 32×30 hi-res 點陣以 `putPixelOnDisplay` 2× 直繪 display buffer。細節見 kb `scummvm-sci-cht-localization`「SCI1 增量②」。https://github.com/wicanr2/jones_in_the_fast_lane
- 字型烘製 pipeline:`build_cjk_font.py`(TTF → 點陣 atlas 子集,見 `retro-game-remake` skill)。
