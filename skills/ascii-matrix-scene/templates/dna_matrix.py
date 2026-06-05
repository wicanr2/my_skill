#!/usr/bin/env python3
# HELIX // CODEX
# 全螢幕 3D 雙股 DNA 螺旋 + Matrix 程式雨
# 跑法: python3 /tmp/dna_matrix.py
# 離開: Ctrl+C
import math
import sys
import time
import signal
import random
import shutil

# ===== ANSI =====
HIDE    = '\033[?25l'
SHOW    = '\033[?25h'
CLEAR   = '\033[2J\033[H'
HOME    = '\033[H'
RESET   = '\033[0m'
BOLD    = '\033[1m'
ALT_ON  = '\033[?1049h'    # 進入 alternate screen (隔離 scrollback,避免捲動殘影)
ALT_OFF = '\033[?1049l'    # 離開 alternate screen,還原原本畫面

# 雙股顏色 (青 / 洋紅 兩極)
S1_DIM    = '\033[38;5;24m'    # 深青
S1_NORM   = '\033[38;5;44m'    # 青
S1_BRIGHT = '\033[38;5;51m'    # 亮青
S1_HOT    = '\033[38;5;195m'   # 冰白藍

S2_DIM    = '\033[38;5;53m'    # 深洋紅
S2_NORM   = '\033[38;5;163m'   # 洋紅
S2_BRIGHT = '\033[38;5;201m'   # 桃粉
S2_HOT    = '\033[38;5;225m'   # 粉白

# 鹼基對 (綠色光譜)
R_DIM     = '\033[38;5;22m'
R_NORM    = '\033[38;5;34m'
R_BRIGHT  = '\033[38;5;46m'
R_HOT     = '\033[38;5;226m'

WHITE = '\033[97m'
GOLD  = '\033[38;5;220m'
DGRAY = '\033[38;5;238m'

# 背景 Matrix 雨色階
M_HEAD  = '\033[97m'
M_LIME  = '\033[38;5;46m'
M_GRN   = '\033[38;5;34m'
M_DIM   = '\033[38;5;28m'
M_FAINT = '\033[38;5;22m'

# Panzer General 徽章色盤 (參考 panzer-general.png:金黃邊 + 綠內裡 + 金星)
B_BORDER   = '\033[38;5;226m'   # 金黃邊框
B_FILL_F   = '\033[38;5;40m'    # 亮綠 (正面)
B_FILL_M   = '\033[38;5;28m'    # 中綠 (側面)
B_FILL_B   = '\033[38;5;22m'    # 深綠 (背面)
B_STAR     = '\033[38;5;220m'   # 金星
B_STAR_HOT = '\033[38;5;229m'   # 星閃

# Castle 色盤 (參考 Ultima I 標題畫面:金字 + 灰石 + 紅頂 + 紅旗)
C_TITLE    = '\033[38;5;220m'   # 金黃 ULTIMA I 標題
C_TITLE_H  = '\033[38;5;229m'   # 標題反光
C_WALL_F   = '\033[38;5;250m'   # 石牆 正面 (亮灰)
C_WALL_M   = '\033[38;5;244m'   # 石牆 側面 (中灰)
C_WALL_B   = '\033[38;5;238m'   # 石牆 背面 (暗灰)
C_ROOF     = '\033[38;5;124m'   # 屋頂 (深紅)
C_ROOF_H   = '\033[38;5;196m'   # 屋頂 (亮紅)
C_FLAG     = '\033[38;5;196m'   # 旗幟 鮮紅
C_POLE     = '\033[38;5;240m'   # 旗桿 暗灰
C_WINDOW   = '\033[38;5;220m'   # 窗 (亮著的金光)
C_WINDOW_D = '\033[38;5;94m'    # 窗 (背面/側面)
C_DOOR     = '\033[38;5;94m'    # 門 (棕)
C_CREN     = '\033[38;5;246m'   # 城垛 灰白

# 字符集
MCHARS  = 'ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ0123456789ABCDEF#$%&*+=<>?'
BASE    = 'ATGC'


def rung_char():
    # 70% 鹼基字母 (像真的 DNA),30% Katakana (Matrix 風)
    if random.random() < 0.7:
        return random.choice(BASE)
    return random.choice(MCHARS)


def cleanup(*_):
    sys.stdout.write(ALT_OFF + SHOW + RESET)
    sys.stdout.flush()
    print('helix.unlocked = FALSE  //  connection closed')
    sys.exit(0)


signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)


# ===== 3D 模型 =====
def build_helix():
    """回傳 list of (x, y, z, kind) — kind in {'S1', 'S2', 'R'}"""
    pts = []
    R = 4.0
    turns = 4.0
    pts_per_turn = 40
    n = int(turns * pts_per_turn)
    height = 18.0
    y_start = -height / 2

    # 兩股骨架
    for i in range(n + 1):
        t = 2 * math.pi * turns * i / n
        y = y_start + height * i / n
        x1 = R * math.cos(t)
        z1 = R * math.sin(t)
        pts.append((x1, y, z1, 'S1'))
        x2 = R * math.cos(t + math.pi)
        z2 = R * math.sin(t + math.pi)
        pts.append((x2, y, z2, 'S2'))

    # 鹼基對 (橫桿)
    rung_every = 4
    rung_samples = 18
    for i in range(0, n + 1, rung_every):
        t = 2 * math.pi * turns * i / n
        y = y_start + height * i / n
        x1 = R * math.cos(t)
        z1 = R * math.sin(t)
        x2 = R * math.cos(t + math.pi)
        z2 = R * math.sin(t + math.pi)
        for k in range(1, rung_samples):
            ratio = k / rung_samples
            rx = x1 + (x2 - x1) * ratio
            rz = z1 + (z2 - z1) * ratio
            pts.append((rx, y, rz, 'R'))

    return pts


def build_badge():
    """Panzer General 徽章 3D 模型:XY 平面上的金黃菱形 + 綠內裡 + 10 顆金星金字塔。
    沿 Y 軸旋轉時,正面→側面→背面會自然壓扁成薄條再展開。"""
    pts = []
    DW = 3.4   # 菱形半寬
    DH = 3.4   # 菱形半高

    # 內裡 + 邊框 (用 L1 norm 取菱形:|x|/DW + |y|/DH ≤ 1)
    n = 14
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            x = i * DW / n
            y = j * DH / n
            d = abs(x) / DW + abs(y) / DH
            if d > 1.02:
                continue
            kind = 'border' if d > 0.90 else 'fill'
            pts.append((x, y, 0.0, kind))

    # 10 顆金星: 1-3-4-2 排列
    star_xy = [
        (0.00,  0.62),
        (-0.32, 0.28), (0.00,  0.28), (0.32,  0.28),
        (-0.42,-0.10), (-0.14,-0.10), (0.14, -0.10), (0.42, -0.10),
        (-0.18,-0.46), (0.18, -0.46),
    ]
    # 給 z 一點微微浮起,確保畫在 fill/border 之上
    for sx, sy in star_xy:
        pts.append((sx * DW, sy * DH, -0.01, 'star'))

    return pts


def build_castle():
    """Ultima I 風格城堡:ULTIMA I 金字標題 + 3 塔 + 紅頂紅旗。XY 平面上,沿 Y 軸旋轉。"""
    pts = []

    # ---- ULTIMA I 標題 (3x5 像素字型) ----
    FONT = {
        'U': ['# #', '# #', '# #', '# #', '###'],
        'L': ['#  ', '#  ', '#  ', '#  ', '###'],
        'T': ['###', ' # ', ' # ', ' # ', ' # '],
        'I': ['###', ' # ', ' # ', ' # ', '###'],
        'M': ['# #', '###', '###', '# #', '# #'],
        'A': [' # ', '# #', '###', '# #', '# #'],
        ' ': ['   ', '   ', '   ', '   ', '   '],
    }
    title = 'ULTIMA I'
    px = 0.16
    char_w_px = 3
    pitch_px = char_w_px + 1
    total_px = pitch_px * len(title) - 1
    title_top_y = 3.7
    for ci, ch in enumerate(title):
        glyph = FONT.get(ch, FONT[' '])
        for row in range(5):
            for col in range(char_w_px):
                if glyph[row][col] == '#':
                    x = (ci * pitch_px + col - total_px / 2) * px
                    y = title_top_y - row * px
                    pts.append((x, y, 0.0, 'title'))

    def fill_rect(xmin, xmax, ymin, ymax, density, kind):
        nx = max(1, int((xmax - xmin) * density))
        ny = max(1, int((ymax - ymin) * density))
        for i in range(nx + 1):
            for j in range(ny + 1):
                x = xmin + (xmax - xmin) * i / nx
                y = ymin + (ymax - ymin) * j / ny
                pts.append((x, y, 0.0, kind))

    def fill_triangle(cx, base_w, ybase, peak_h, kind):
        ny = max(2, int(peak_h * 6))
        for j in range(ny + 1):
            t = j / ny
            y = ybase + peak_h * t
            half_w = base_w / 2 * (1 - t)
            nx = max(1, int(half_w * 12))
            for i in range(nx + 1):
                x = cx - half_w + 2 * half_w * i / nx
                pts.append((x, y, 0.0, kind))

    # ---- 3 塔 ----
    fill_rect(-3.0, -2.0, -2.6, 0.6, 5, 'wall_f')   # 左塔
    fill_rect(-0.6,  0.6, -2.6, 1.0, 5, 'wall_f')   # 中塔 (較高)
    fill_rect( 2.0,  3.0, -2.6, 0.6, 5, 'wall_f')   # 右塔

    # ---- 連牆 ----
    fill_rect(-2.0, -0.6, -2.6, -0.5, 4, 'wall_m')
    fill_rect( 0.6,  2.0, -2.6, -0.5, 4, 'wall_m')

    # ---- 城垛 (連牆頂) ----
    for cx_ in (-1.75, -1.35, -0.95, 0.95, 1.35, 1.75):
        pts.append((cx_, -0.35, 0.0, 'cren'))

    # ---- 屋頂 (3 個三角) ----
    fill_triangle(-2.5, 1.2, 0.6, 0.7, 'roof')
    fill_triangle( 0.0, 1.4, 1.0, 0.9, 'roof')
    fill_triangle( 2.5, 1.2, 0.6, 0.7, 'roof')

    # ---- 旗桿 + 旗幟 ----
    for cx_, top in ((-2.5, 1.3), (0.0, 1.9), (2.5, 1.3)):
        for j in range(4):
            pts.append((cx_, top + j * 0.18, 0.0, 'pole'))
        pts.append((cx_ + 0.14, top + 0.55, 0.0, 'flag'))
        pts.append((cx_ + 0.28, top + 0.55, 0.0, 'flag'))
        pts.append((cx_ + 0.14, top + 0.42, 0.0, 'flag'))

    # ---- 窗戶 ----
    for cx_, y_ in (
        (-2.5,  0.0), (-2.5, -0.8), (-2.5, -1.6),
        ( 0.0,  0.4), ( 0.0, -0.4), ( 0.0, -1.2), ( 0.0, -2.0),
        ( 2.5,  0.0), ( 2.5, -0.8), ( 2.5, -1.6),
    ):
        pts.append((cx_, y_, 0.0, 'window'))

    # ---- 城門 ----
    fill_rect(-0.32, 0.32, -2.6, -1.5, 6, 'door')

    return pts


# ===== Matrix 雨 =====
class Rain:
    def __init__(self, w, h):
        self.resize(w, h)

    def resize(self, w, h):
        self.w, self.h = w, h
        self.drops  = [random.randint(-h * 2, 0) for _ in range(w)]
        self.speeds = [random.choice([1, 1, 1, 2]) for _ in range(w)]
        self.trails = [random.randint(8, 22) for _ in range(w)]
        self.grid   = [[' '] * w for _ in range(h)]
        self.age    = [[999] * w for _ in range(h)]

    def step(self):
        w, h = self.w, self.h
        for y in range(h):
            row = self.age[y]
            for x in range(w):
                row[x] += 1
        for x in range(w):
            self.drops[x] += self.speeds[x]
            head = self.drops[x]
            if 0 <= head < h:
                self.grid[head][x] = random.choice(MCHARS)
                self.age[head][x] = 0
            if head > h + self.trails[x]:
                self.drops[x] = random.randint(-h, -1)
                self.speeds[x] = random.choice([1, 1, 1, 2])
                self.trails[x] = random.randint(8, 22)


# ===== Panzer 坦克縱隊 (參考 panzer-general 戰場 hex grid 上的單位 icon) =====
TANK_SPRITES_R = [
    ('▙█▟▶', '\033[38;5;58m'),    # 標準坦克 (橄欖綠)
    ('▙▣▟▶', '\033[38;5;94m'),    # 重坦克 (棕)
    ('◣█◢▶', '\033[38;5;245m'),   # 輕坦克 (灰)
    ('╤█╤▶', '\033[38;5;130m'),   # 自走炮 (深橘)
    ('▙▤▟▶', '\033[38;5;28m'),    # 裝甲車 (深綠)
    ('▙▦▟▶', '\033[38;5;100m'),   # 步兵戰車 (橄欖)
]
TANK_SPRITES_L = [
    ('◀▙█▟', '\033[38;5;58m'),
    ('◀▙▣▟', '\033[38;5;94m'),
    ('◀◣█◢', '\033[38;5;245m'),
    ('◀╤█╤', '\033[38;5;130m'),
    ('◀▙▤▟', '\033[38;5;28m'),
    ('◀▙▦▟', '\033[38;5;100m'),
]


class TankConvoy:
    """Panzer 坦克縱隊,在 matrix 動畫上下兩列水平行進。
    上排朝右(進攻),下排朝左(回防)。每輛車隨機 sprite/速度。"""

    def __init__(self, w, h):
        self.tanks = []
        self.resize(w, h)

    def resize(self, w, h):
        self.w = w
        self.h = h
        self.tanks = []
        # 上排:gap between castle (rows 0..~15) and badge (rows ~21..~33) → row ~ H/2
        top_y = max(1, h // 2)
        # 下排:badge 之下,在 status bar 之上
        bot_y = max(top_y + 1, h - 2)
        self._populate(top_y, +1, max(3, w // 30), TANK_SPRITES_R)
        if bot_y != top_y:
            self._populate(bot_y, -1, max(3, w // 30), TANK_SPRITES_L)

    def _populate(self, y, direction, count, sprites):
        spacing = max(8, self.w // count)
        for i in range(count):
            offset = i * spacing + random.randint(0, 4)
            x = offset if direction > 0 else self.w - offset
            sp, col = random.choice(sprites)
            self.tanks.append({
                'x': float(x), 'y': y, 'dir': direction,
                'sprite': sp, 'color': col, 'sprites': sprites,
                'speed': random.uniform(0.20, 0.55),
            })

    def step(self):
        for t in self.tanks:
            t['x'] += t['speed'] * t['dir']
            sl = len(t['sprite'])
            if t['dir'] > 0 and t['x'] > self.w + 1:
                t['x'] = float(-sl - random.randint(0, 8))
                t['sprite'], t['color'] = random.choice(t['sprites'])
                t['speed'] = random.uniform(0.20, 0.55)
            elif t['dir'] < 0 and t['x'] + sl < -1:
                t['x'] = float(self.w + random.randint(0, 8))
                t['sprite'], t['color'] = random.choice(t['sprites'])
                t['speed'] = random.uniform(0.20, 0.55)

    def render(self, canvas, cmap, mask):
        for t in self.tanks:
            y = t['y']
            if not (0 <= y < self.h):
                continue
            base_x = int(t['x'])
            for k, ch in enumerate(t['sprite']):
                x = base_x + k
                if 0 <= x < self.w and ch != ' ':
                    canvas[y][x] = ch
                    cmap[y][x] = t['color']
                    mask[y][x] = True


def fill_rain(canvas, cmap, mask, rain):
    """把 Matrix 雨填到 mask 為 False 的格子,inline 跑比較快。"""
    h, w = rain.h, rain.w
    trails = rain.trails
    grid = rain.grid
    age = rain.age
    for y in range(h):
        crow = canvas[y]
        krow = cmap[y]
        mrow = mask[y]
        arow = age[y]
        grow = grid[y]
        for x in range(w):
            if mrow[x]:
                continue
            a = arow[x]
            c = grow[x]
            t = trails[x]
            if c == ' ' or a > t:
                continue
            if a == 0:
                color = M_HEAD
            elif a < 2:
                color = M_LIME
            elif a < 6:
                color = M_GRN
            elif a < 12:
                color = M_DIM
            else:
                color = M_FAINT
                if random.random() < 0.02:
                    c = random.choice(MCHARS)
            crow[x] = c
            krow[x] = color


# ===== 渲染 =====
def render_helix(pts, angle, cx, cy, zone_w, zone_h, w, h, frame_n, canvas, cmap, mask):
    # 螺旋等比縮放: 模型 18 高 / 8 寬,依分配到的 zone 大小縮放
    scale_y = max(0.8, 0.78 * zone_h / 18.0)
    scale_x = max(2.0, 0.55 * zone_w / 8.0)
    # 鎖在合理長寬比 (文字格子約 2:1 高寬)
    scale_x = min(scale_x, scale_y * 2.6)
    scale_x = max(scale_x, scale_y * 1.7)
    persp = 32.0

    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    # 3 道能量脈衝 (在模型 y 軸 -9..+9 之間循環)
    period = 18.0
    pulse_y = [
        ((frame_n * 0.18 + k * period / 3) % period) - period / 2
        for k in range(3)
    ]

    # z-buffer (overload zbuf via cmap-None test? 用獨立 buffer 比較乾淨)
    zbuf = [[1e9] * w for _ in range(h)]

    for x, y, z, kind in pts:
        rx = x * cos_a + z * sin_a
        rz = -x * sin_a + z * cos_a
        f = persp / (persp + rz)
        sx = rx * scale_x * f
        sy = -y * scale_y * f
        ix = int(round(sx + cx))
        iy = int(round(sy + cy))
        if not (0 <= ix < w and 0 <= iy < h):
            continue
        if rz >= zbuf[iy][ix]:
            continue
        zbuf[iy][ix] = rz

        # 與最近脈衝的距離 → 熱度
        dpulse = min(abs(y - py) for py in pulse_y)
        hot  = dpulse < 0.5
        warm = dpulse < 1.6

        front = rz < 0  # 朝相機那一側

        if kind == 'S1':
            if hot:
                ch, col = '★', WHITE
            elif warm:
                ch, col = '◉', S1_HOT
            elif front:
                ch, col = '●', S1_BRIGHT
            else:
                ch, col = ('·' if random.random() < 0.5 else 'o'), S1_DIM
        elif kind == 'S2':
            if hot:
                ch, col = '★', WHITE
            elif warm:
                ch, col = '◉', S2_HOT
            elif front:
                ch, col = '●', S2_BRIGHT
            else:
                ch, col = ('·' if random.random() < 0.5 else 'o'), S2_DIM
        else:  # rung
            ch = rung_char()
            if hot:
                col = R_HOT
            elif warm:
                col = R_BRIGHT
            elif front:
                col = R_NORM
            else:
                col = R_DIM

        canvas[iy][ix] = ch
        cmap[iy][ix] = col
        mask[iy][ix] = True


def render_badge(pts, angle, cx, cy, zone_w, zone_h, w, h, frame_n, canvas, cmap, mask):
    """繪製 Panzer General 徽章,與螺旋共享同一角度。"""
    # 徽章模型最大 ~ 7 寬 × 7 高
    scale_y = max(0.6, 0.85 * zone_h / 7.0)
    scale_x = max(1.5, 0.50 * zone_w / 7.0)
    # 菱形要看起來像菱形,文字格 2:1 → 水平要拉
    scale_x = min(scale_x, scale_y * 2.2)
    scale_x = max(scale_x, scale_y * 1.7)
    persp = 40.0

    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    face = abs(cos_a)  # 0 = 側面, 1 = 正面

    # 排序:先 fill,再 border,星最後 (確保星不被覆蓋)
    order = {'fill': 0, 'border': 1, 'star': 2}
    sorted_pts = sorted(pts, key=lambda p: order[p[3]])

    zbuf_local = {}

    for x, y, z, kind in sorted_pts:
        rx = x * cos_a + z * sin_a
        rz = -x * sin_a + z * cos_a
        f = persp / (persp + rz)
        sx = rx * scale_x * f
        sy = -y * scale_y * f
        ix = int(round(sx + cx))
        iy = int(round(sy + cy))
        if not (0 <= ix < w and 0 <= iy < h):
            continue

        if kind == 'star':
            # 星偶爾閃 (依星座標 + frame 偏移,避免一起閃)
            phase = (frame_n + int(x * 13) + int(y * 7)) % 22
            sparkle = phase < 3
            ch = '✦' if sparkle else '★'
            col = B_STAR_HOT if sparkle else B_STAR
            canvas[iy][ix] = ch
            cmap[iy][ix] = col
            mask[iy][ix] = True
            continue

        # fill / border 的 z-buffer
        key = (iy, ix)
        prev_z = zbuf_local.get(key, 1e9)
        if rz >= prev_z:
            continue
        zbuf_local[key] = rz

        if kind == 'border':
            # 邊框:正面用 ◆,側面壓扁用 ┃
            ch = '◆' if face > 0.45 else '┃'
            col = B_BORDER
        else:  # fill
            if face > 0.70:
                ch = '▓'
                col = B_FILL_F
            elif face > 0.35:
                ch = '▒'
                col = B_FILL_M
            else:
                ch = '░'
                col = B_FILL_B

        canvas[iy][ix] = ch
        cmap[iy][ix] = col
        mask[iy][ix] = True


def render_castle(pts, angle, cx, cy, zone_w, zone_h, w, h, frame_n, canvas, cmap, mask):
    """繪製 Ultima I 城堡,與螺旋共享同一角度。"""
    # 模型寬 ~ 6.6, 高 ~ 6.5 (含標題)
    scale_y = max(0.55, 0.82 * zone_h / 7.0)
    scale_x = max(1.4, 0.52 * zone_w / 7.0)
    scale_x = min(scale_x, scale_y * 2.4)
    scale_x = max(scale_x, scale_y * 1.7)
    persp = 36.0

    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    face = abs(cos_a)

    # 繪製順序:wall → door → roof → cren → window → pole → flag → title
    order = {
        'wall_f': 0, 'wall_m': 0, 'door': 1, 'roof': 2,
        'cren': 3, 'window': 4, 'pole': 5, 'flag': 6, 'title': 7,
    }
    sorted_pts = sorted(pts, key=lambda p: order.get(p[3], 0))

    zbuf_local = {}

    for x, y, z, kind in sorted_pts:
        rx = x * cos_a + z * sin_a
        rz = -x * sin_a + z * cos_a
        f = persp / (persp + rz)
        sx = rx * scale_x * f
        sy = -y * scale_y * f
        ix = int(round(sx + cx))
        iy = int(round(sy + cy))
        if not (0 <= ix < w and 0 <= iy < h):
            continue

        # 標題/旗幟/窗光/旗桿 不參與 z-buffer (一定畫在最上層)
        bypass_z = kind in ('title', 'flag', 'window', 'pole')
        if not bypass_z:
            key = (iy, ix)
            prev_z = zbuf_local.get(key, 1e9)
            if rz >= prev_z:
                continue
            zbuf_local[key] = rz

        if kind == 'title':
            # 固定方塊,只做顏色閃爍 (小尺寸下避免字元 shimmer 干擾辨識)
            phase = (frame_n + int(x * 11) + int(y * 7)) % 30
            ch = '█'
            col = C_TITLE_H if phase < 5 else C_TITLE
        elif kind == 'wall_f':
            if face > 0.70:
                ch, col = '█', C_WALL_F
            elif face > 0.35:
                ch, col = '▓', C_WALL_M
            else:
                ch, col = '▒', C_WALL_B
        elif kind == 'wall_m':
            if face > 0.55:
                ch, col = '▓', C_WALL_M
            else:
                ch, col = '▒', C_WALL_B
        elif kind == 'roof':
            ch = '▲' if face > 0.55 else '┃'
            col = C_ROOF_H if face > 0.75 else C_ROOF
        elif kind == 'cren':
            ch = '▄' if face > 0.45 else '╴'
            col = C_CREN
        elif kind == 'pole':
            ch, col = '│', C_POLE
        elif kind == 'flag':
            ch = '◣' if (frame_n // 3) % 2 == 0 else '◢'
            col = C_FLAG
        elif kind == 'window':
            phase = (frame_n + int(x * 7) + int(y * 5)) % 40
            if face < 0.30:
                ch, col = '▪', C_WINDOW_D
            elif phase < 30:
                ch, col = '▣', C_WINDOW
            else:
                ch, col = '▪', C_WINDOW_D
        elif kind == 'door':
            ch, col = '▓', C_DOOR
        else:
            continue

        canvas[iy][ix] = ch
        cmap[iy][ix] = col
        mask[iy][ix] = True


def serialize(canvas, cmap):
    out = []
    for row, crow in zip(canvas, cmap):
        parts = []
        cur = None
        for ch, col in zip(row, crow):
            if col != cur:
                parts.append(RESET if col is None else col)
                cur = col
            parts.append(ch)
        parts.append(RESET)
        out.append(''.join(parts))
    return out


# ===== 主程式 =====
def main():
    angle = 0.0
    speed = 0.055
    frame_n = 0
    helix_pts = build_helix()
    badge_pts = build_badge()
    castle_pts = build_castle()

    term = shutil.get_terminal_size((80, 30))
    W = max(40, term.columns)
    H = max(20, term.lines - 2)   # 上 1 行 title + 下 1 行 status
    rain = Rain(W, H)
    convoy = TankConvoy(W, H)

    quotes = [
        '> sequencing genome.dat ...',
        '> 0xCAFEBABE :: helix locked',
        '> CRISPR.signal = ALIVE',
        '> consciousness loaded',
        '> the code dreams of you',
        '> 雙股 // 共振 // 同步',
        '> A T G C  —  read frame +1',
        '> 你看見的不是字符 // 是你自己',
    ]
    q_idx = 0

    # 進 alternate screen + 隱藏游標,離開時還原
    sys.stdout.write(ALT_ON + HIDE + CLEAR)
    sys.stdout.flush()
    try:
        while True:
            # 終端尺寸自適應
            term = shutil.get_terminal_size((80, 30))
            nw = max(40, term.columns)
            nh = max(20, term.lines - 2)
            if (nw, nh) != (W, H):
                W, H = nw, nh
                rain.resize(W, H)
                convoy.resize(W, H)

            rain.step()
            convoy.step()
            frame_buf = [HOME]

            # ----- 標題列 (頂端 1 行,跨整個 W) -----
            spinner = '◐◓◑◒'[(frame_n // 2) % 4]
            deg = int(math.degrees(angle) % 360)
            title = f' {spinner} HELIX // ULTIMA // PANZER  φ={deg:3d}° '
            tlen = len(title) - 1  # 中文字寬調整 (這裡都半形,忽略)
            left_n = max(0, (W - len(title)) // 2)
            right_n = max(0, W - len(title) - left_n)
            title_bar = (
                S1_BRIGHT + '═' * left_n +
                BOLD + GOLD + title + RESET +
                S2_BRIGHT + '═' * right_n + RESET
            )
            frame_buf.append(title_bar + '\n')

            # ----- 動畫主體 -----
            canvas = [[' '] * W for _ in range(H)]
            cmap   = [[None] * W for _ in range(H)]
            mask   = [[False] * W for _ in range(H)]

            # 左欄上半:Ultima 城堡; 左欄下半:Panzer 徽章; 右側:DNA 螺旋
            # 三者共用同一個 angle,同步繞 Y 軸 turnaround
            castle_cx = W * 3 // 16
            castle_cy = max(5, H // 4)
            castle_zw = W * 5 // 16
            castle_zh = max(8, H // 2 - 2)

            badge_cx = W * 3 // 16
            badge_cy = min(H - 5, (H * 3) // 4)
            badge_zw = W * 5 // 16
            badge_zh = max(8, H // 2 - 2)

            helix_cx = W * 5 // 8
            helix_cy = H // 2
            helix_zw = W * 3 // 4
            helix_zh = H - 2

            render_castle(castle_pts, angle, castle_cx, castle_cy,
                          castle_zw, castle_zh, W, H, frame_n,
                          canvas, cmap, mask)
            render_badge(badge_pts, angle, badge_cx, badge_cy,
                         badge_zw, badge_zh, W, H, frame_n,
                         canvas, cmap, mask)
            render_helix(helix_pts, angle, helix_cx, helix_cy,
                         helix_zw, helix_zh, W, H, frame_n,
                         canvas, cmap, mask)
            convoy.render(canvas, cmap, mask)
            fill_rain(canvas, cmap, mask, rain)

            frame_buf.append('\n'.join(serialize(canvas, cmap)))
            frame_buf.append('\n')

            # ----- 狀態列 (底端 1 行) -----
            if frame_n > 0 and frame_n % 110 == 0:
                q_idx = (q_idx + 1) % len(quotes)
            stat = f' {quotes[q_idx]}   //   [Ctrl+C] disconnect'
            if len(stat) > W:
                stat = stat[:W]
            frame_buf.append(M_LIME + stat.ljust(W) + RESET)

            # 整幀一次 write,降低部分 flush 造成的中間狀態 flicker
            sys.stdout.write(''.join(frame_buf))
            sys.stdout.flush()

            angle += speed
            frame_n += 1
            time.sleep(0.06)
    finally:
        sys.stdout.write(ALT_OFF + SHOW + RESET + '\n')
        sys.stdout.flush()


if __name__ == '__main__':
    main()
