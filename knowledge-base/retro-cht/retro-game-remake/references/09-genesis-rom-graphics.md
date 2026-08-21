# Genesis / Mega Drive ROM 圖形抽取 (tile / sprite / palette)

從 Sega Genesis (Mega Drive) ROM 抽取美術的格式速查 + 實戰工具。適用：把 Genesis 版
美術導入重製引擎、做 theme 切換、或單純 dump sprite。實證來源：King's Bounty (Genesis)
中文化專案 (openkb MD 模組;troop/villain palette 修正)。

外部教學 (已驗證可用)：
- Tiles & sprites: https://huguesjohnson.com/programming/genesis/tiles-sprites/
- Palettes:        https://huguesjohnson.com/programming/genesis/palettes/
- PNG↔tile 工具:   https://github.com/yuv422/png2tile (SMS/GG/MD;PNG→tile 為主，**抽取用不到**)

## 1. Tile 格式 (背景 tile 與 sprite cell 共用)

- **8×8 像素、4bpp、每 tile 32 bytes**。
- 每 byte = **2 像素**，**高 nibble = 左像素**，低 nibble = 右像素。
- 列順序：由上而下，每列 4 bytes (8px ÷ 2)。
- index 0 慣例為**透明**色 (colorkey)。

解碼一個 8×8 tile：
```c
for (int y=0;y<8;y++) for (int x=0;x<8;x+=2){
    u8 by = rom[off + y*4 + x/2];
    idx[y][x]   = by >> 4;   // 左
    idx[y][x+1] = by & 0xF;  // 右
}
```

## 2. Sprite 組成 (多 tile 大圖) — **column-major!**

- 一個 sprite = W×H 個 8×8 cell。Genesis VDP 的 sprite pattern 是 **column-major**：
  先一整欄由上到下，再下一欄。**不是** row-major。
- 重製引擎要照 column-major 重組，否則大圖會「打散」。
  openkb `md-rom.c` 的 `for col(6) for row(4)` 即正確的 column-major (troop = 48×32 = 6×4 cell)。
- Sprite Attribute Table (SAT) 每筆 8 bytes：
  `+0 word Y` / `+2 byte size(hhvv)` / `+3 byte link` / `+4 word pccvh nnn... (priority/palette/flip/pattern)` / `+6 word X`。
  pattern 的 bit 13-14 = palette index (共 4 個 palette)。
- 背景 tile (非 sprite，如地圖 tileset) 通常是單純連續 8×8 cell，依引擎排版而定，**不一定** column-major。

## 3. Palette (CRAM)

- **4 個 palette × 16 色 = 最多 64 色同屏**；每色一個 16-bit word。
- 硬體位元配置 (BGR、每通道 3-bit)：`0000 BBB0 GGG0 RRR0`
  - R = `(w >> 1) & 7`
  - G = `(w >> 5) & 7`
  - B = `(w >> 9) & 7`
  - bit 0/4/8 與高 nibble 恆為 0 → **找 palette 的特徵：`(w & 0xF111) == 0`**。
- 轉 RGB888：`comp8 = comp3 * 36` (0,36,…,252;夠用)。要更準可 `comp3*255/7`。
- 在 ROM 找 palette：掃連續 ≥16 個「合法色字」(且非全 0,至少數種非零)。
  KB Genesis 的 sprite palette 在 `0x25698`。

## 4. 在 ROM 定位圖形 (最花時間的一步)

graphics **通常未壓縮** (KB Genesis 即是;troop/villain/tile 都 raw 4bpp) → 可用「算繪掃描」找：

- **灰階掃結構** (palette 無關)：把 ROM 區段當連續 8×8 tile,index→灰 (`index*17`),
  輸出 PNG sheet。程式碼 = noise → 雜點;graphics → 有組織的形狀/條紋。
- 找到候選區後**換彩色** (套候選 palette) 確認是不是要的圖。
- 空白區 = 全 index 0 → PNG 只有 1-2 色 (`identify` 顯示 `2c`),直接跳過。
- 已知一個 sprite 的 offset 後，**同類資源常等距排列** (KB troop 間距 = 768×4 = 0xC00)。

### 掃描工具 (彩色版,docker 內 gcc 即可編)
```c
/* romcol rom start_hex num_tiles tiles_per_row pal_hex → PPM (P3) */
#include <stdio.h>
#include <stdlib.h>
typedef unsigned char u8; typedef unsigned short u16;
int main(int ac,char**v){
  FILE*f=fopen(v[1],"rb");fseek(f,0,SEEK_END);long n=ftell(f);fseek(f,0,SEEK_SET);
  u8*b=malloc(n);fread(b,1,n,f);fclose(f);
  long s=strtol(v[2],0,16);int nt=atoi(v[3]),tpr=atoi(v[4]);long pal=strtol(v[5],0,16);
  u8 pr[16],pg[16],pb[16];
  for(int i=0;i<16;i++){u16 w=(b[pal+i*2]<<8)|b[pal+i*2+1];pr[i]=((w>>1)&7)*36;pg[i]=((w>>5)&7)*36;pb[i]=((w>>9)&7)*36;}
  int rows=(nt+tpr-1)/tpr,W=tpr*8,H=rows*8;
  u8*R=calloc(W*H,1),*G=calloc(W*H,1),*B=calloc(W*H,1);
  for(int t=0;t<nt;t++){long o=s+t*32;if(o+32>n)break;int tx=(t%tpr)*8,ty=(t/tpr)*8;
    for(int y=0;y<8;y++)for(int x=0;x<8;x+=2){u8 by=b[o+y*4+x/2];int hi=by>>4,lo=by&0xF;
      int p=(ty+y)*W+(tx+x);R[p]=pr[hi];G[p]=pg[hi];B[p]=pb[hi];R[p+1]=pr[lo];G[p+1]=pg[lo];B[p+1]=pb[lo];}}
  printf("P3\n%d %d\n255\n",W,H);for(int i=0;i<W*H;i++)printf("%d %d %d ",R[i],G[i],B[i]);return 0;
}
```
配 `convert sheet.ppm -filter point -resize 400% out.png` 放大看 (nearest 保持像素銳利)。
**注意**：`convert +append` 多張小圖常退化成灰階 — 寧可輸出單張大 sheet 直接 Read。

## 5. 踩雷

- **sprite 用 column-major、背景 tile 多 row-major** — 搞錯會「圖形打散」。
- **每類資源可能各自 palette** — 一個 palette 不一定全 troop 都對;先用一個改善總比 EGA 好,
  再逐類找專屬 palette。
- **graphics 若壓縮** (部分 Genesis 遊戲會) → 算繪全是雜點、找不到;需反組譯找解壓常式。
  KB Genesis 未壓縮,屬幸運案例。
- **offset 定位是主要成本**,不是格式 — 格式 30 分鐘搞定,定位每種資源各要視覺迭代。
- headless docker 用 `convert ppm→png` + Read 看圖;**不要開 GUI viewer** (rule 35)。

## 6. KB Genesis 已知 offset (案例參考)
| 資源 | offset | 備註 |
|---|---|---|
| troop sprite | `0x668EC` | 48×32 (6×4 cell),每隻 4 frame,間距 `0xC00`;**未壓縮** |
| villain 臉 | `0x4B04C` | 同 troop 結構;未壓縮 |
| cursor | `~0x62D6C` | openkb 註記 |
| 世界地圖 cell 資料 | `0x1AA8E` | 4 大陸 × 64×64 cell-type byte (非圖形;值 0..145,引擎 `&0x7F`→0..71) |
| sprite palette | `0x25698` | troop/villain 用;9-bit BGR |
| **LZSS 解壓器** | `0x18B0C` | jumptable `$c(a5)`;Okumura LZSS (見 §8) |
| **地形 tile pattern** | `0x30E82` | **LZSS 壓縮**;解出 638 個 8×8 4bpp tile (skip 2-byte header) |
| **地形 cell template** | `0x19666` | 每 cell-type 60 bytes = 6×5 nametable word (見 §8) |
| **地形 palette** | `0x256B8` | 4 line × 16 色 |

> 此表是逐項 RE 的進行式。完整化 = 把 UI/cursor/select/title 等的 offset+palette 都補上。

## 7. 反組譯找未知資源 (當靜態掃描找不到 → 可能壓縮)

工具：capstone M68K (docker uv venv)：
```python
from capstone import *
md=Cs(CS_ARCH_M68K, CS_MODE_BIG_ENDIAN|CS_MODE_M68K_000)
for ins in md.disasm(rom[start:end], start): ...
```

**找資源 offset 的反查法**：
1. 搜 ROM 內對「已知資料位址」的 32-bit big-endian 引用 (e.g. map data) → 找到讀它的碼。
2. Genesis 遊戲常用 **a5 = ROM 跳表基底**；`jsr d16(a5)` = 跳到 (a5+d16) 的 `jmp $func.l`。
   - 找 a5：搜全 ROM `movea.l #imm,a5` (opcode `2A7C`) / `lea abs,a5` (`4BF9`)。
   - **陷阱**：開機處 `lea $xx(pc),a5` 設的是 **Sega 標準初始化表**(VDP 暫存器值),不是遊戲跳表 — 別被騙。遊戲 a5 在 main init 另設 (KB Genesis = `0x312`)。
   - a5 相對負位移 (`lea -$1b28(a5),a0`) 通常指向 **RAM 遊戲狀態** (a5_small + 負 disp 環繞到 0xFFxxxx)。
3. sprite/graphics 直接定址：`base + index*size`，DMA 進 VRAM (未壓縮)。troop = `0x668EC + type*0x300*4`。

**KB Genesis RE 進度**：
- 遊戲 a5 = `0x312`;跳表 `0x312` 起 6-byte 一項 (`4ef9` + addr)。a5+0x96 (`0x3A8`) → `0x18F2A` = **memcpy**;地圖資料只是被 memcpy 到 RAM (-0x66c0(a5))，**不在此處碰 tileset**。
- **地形 tileset 是 LZSS 壓縮 (見 §8 完整破解)** — 靜態掃描找不到是因為壓縮,不是不存在。
- ⚠️ ROI 教訓:單一資源 (地圖 tile) 的反組譯追蹤耗了大量回合。**「靜態掃找不到乾淨圖形」→ 第一假設應是壓縮,直接去追解壓器 (`jsr` 進某 helper 後 ROM src→RAM),別先暴力掃 base**。

## 8. KB Genesis 地形 tileset 完整解碼 (LZSS,已破)

靜態掃不到地形圖形 = **自製 Okumura LZSS 壓縮**。解壓器 ROM `0x18B0C` (jumptable `$c(a5)`)。

**LZSS 參數** (逐指令逆自 0x18B0C-0x18BD8):
- ring buffer 4096 bytes、初值填 `0x20`、起始寫入位 `r = 0xFEE`
- src header 8 bytes;`out_size` = header offset+4 的 **big-endian long**;壓縮流從 `src+8` 起
- flag byte 用 `>>1` 由 **LSB** 取 8 個 bit (每 8 bit 重載一個 flag byte)
- flag bit=1 → **literal** (1 byte 直出 + 寫 ring)
- flag bit=0 → **match**:讀 2 bytes `b1,b2`
  - offset = `b1 | ((b2 & 0xF0) << 4)` (12-bit)
  - **length = `(b2 & 0xF) + 3`** ★ 關鍵 off-by-one:ASM `cmp d5,d4; bge` 迴圈是 `d5=0..d4` 共 d4+1 次。算成 +2 會少拷 1 byte/match → 後續全錯成雜訊。

```python
def lzss(rom, src):
    osz=(rom[src+4]<<24)|(rom[src+5]<<16)|(rom[src+6]<<8)|rom[src+7]
    p=src+8; ring=bytearray([0x20]*4096); r=0xFEE; out=bytearray(); flags=0
    while len(out)<osz:
        flags>>=1
        if (flags&0x100)==0: flags=rom[p]|0xFF00; p+=1
        if flags&1:
            c=rom[p]; p+=1; out.append(c); ring[r]=c; r=(r+1)&0xFFF
        else:
            b1=rom[p]; b2=rom[p+1]; p+=2
            off=b1|((b2&0xF0)<<4); ln=(b2&0xF)+3   # +3 !
            for k in range(ln):
                if len(out)>=osz: break
                c=ring[(off+k)&0xFFF]; out.append(c); ring[r]=c; r=(r+1)&0xFFF
    return bytes(out[:osz])
```

**地形 render pipeline**:
1. `pattern = lzss(rom, 0x30E82)[2:]` → 638 個 8×8 Genesis 4bpp chunky tile (skip 2-byte header)。
2. `cell template @ 0x19666`:每 cell-type 60 bytes = **6×5=30 個 VDP nametable word** (一個 cell = 48×40 px metatile):
   - bit0-10 = tile index (`&0x7FF`);bit11 = hflip;bit13-14 = palette line;bit15 = priority
3. `map @ 0x1AA8E`:4 大陸 × 64×64 cell-type byte (引擎 `&0x7F` → 0..71)。
4. `palette @ 0x256B8`:4 line × 16 色 (9-bit BGR ×36)。
5. 組 cell:對 30 個 word,取 `pattern[idx]` 8×8 tile,套 hflip + palette line,鋪成 48×40;**index 0 = 透明** (露出底層 plane B 海色,別畫成黑)。

**驗證鐵則**:解出來「當 4bpp 看仍像雜訊」時 — 先檢查 (a) LZSS length off-by-one、(b) 是 nametable 不是 pattern (word array 高 byte 多為 0/0x40/0x60 → nametable;有連續同 nibble 純色塊 → pattern)、(c) palette index 0 是否壓掉內容 (改成醒目色重看)、(d) chunky vs planar (chunky 對則單 tile grid 乾淨,planar 會出每隔一欄條紋)。

**落地** (openkb `src/lib/md-rom.c`):`md_lzss_decompress` + 快取 `md_terrain_pattern` (解一次) + `md_build_cell` (template 組 metatile) + `GR_TILE`(sub_id=cell-type)/`GR_TILESET`(KB_LoadTileset_TILES)。引擎 map `&0x7F`→0..71 恰好對齊 72-tile 模型,零越界。

> ⚠️ 引擎 tile rect (free ui.ini `[tile]`=48×34) 與 Genesis cell (48×40) 差 6px;完美對齊需把 ui.ini 改 48×40,否則底 6px 被裁 (地形仍可辨識)。
