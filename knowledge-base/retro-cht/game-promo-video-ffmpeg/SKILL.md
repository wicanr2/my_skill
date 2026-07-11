---
name: game-promo-video-ffmpeg
description: 用 ffmpeg + ImageMagick(全 docker、無剪輯軟體、LLM 驅動)把老遊戲/remake/中文化專案的截圖 + 遊戲音樂合成成 60–75 秒推廣短片 / trailer。內建本人用時間換來的硬地雷:**ffmpeg zoompan 幀數爆炸(燒滿 CPU 8 分鐘)**、CPU 控制(--cpus / 預建工具 image / veryfast / 靜態 fallback)、**MIDI+SoundFont 遊戲音樂離線抽取(fluidsynth)**、滑鼠驅動遊戲改用靜態截圖、docker 內字型/IM policy 雷。觸發:「做推廣片/trailer/宣傳片」「把截圖+配樂合成影片」「ffmpeg 做投影片」「Ken Burns」「遊戲介紹影片」「promo video」「影片 CPU 跑太兇/卡住」「抽遊戲配樂當 BGM」。配 rulebook/93(配樂用原版真實素材的[HARD]鐵則)+ 各專案 docs/llm-promo-video-pipeline.md。
---

# game-promo-video-ffmpeg — 腳本化遊戲推廣片合成(地雷優先)

> 這支管「**怎麼用 ffmpeg/IM 把片做出來、又不燒爆 CPU**」的工程實務。
> 「素材來源真實性(配樂用原版、不自產)」的[HARD]鐵則在 `rulebook/93-promo-video-original-assets.md`;
> 三段式 pipeline 總覽在各專案 `docs/llm-promo-video-pipeline.md`(u1-cht 起源)。本檔聚焦**踩過的雷 + 可重用骨架**。

## 何時用
做老遊戲 / remake / 中文化專案的推廣短片、trailer、README 影片。全程 docker(不污染系統)、不開剪輯軟體、可重跑、可 CI、LLM 看算繪幀迭代。

## 三段 pipeline(總覽)
`① 擷取(截圖/錄影/音樂)→ ② 素材(標題卡/字幕卡,程序生成)→ ③ ffmpeg 合成(投影片+字幕+轉場+配樂)`。
每段一支腳本、輸入輸出是檔案。設計 token(色票/字體/母題)放 `make.sh` 最上面 = 換遊戲只改那幾行。

---

## ⚠️ 最痛的雷(用 CPU 與時間換來的,務必記住)

### 1. [HARD] ffmpeg zoompan 幀數爆炸 — 一段 6 秒算成上萬幀、燒滿 CPU 8 分鐘
**症狀**:合成卡住數分鐘、CPU 100%、容器不結束、output 一直空白。
**根因**:`-loop 1 -t $S -i img` + `-vf "...,fps=$FPS,...,zoompan=...:d=$((FPS*S))"`。
`fps` 濾鏡(或 `-loop 1 -t` 本身)先產生 `FPS*S` 個輸入幀,zoompan 的 `d` 是「**每個輸入幀**輸出 d 幀」
→ 變成 `(FPS*S) × (FPS*S)` 幀,6 秒 25fps = 150×150 ≈ 22500 幀。**這是 zoompan 最惡名昭彰的陷阱**。
**對策(擇一)**:
- **最省、最穩(預設選這個)**:**不要 zoompan**,靜態圖 + 淡入淡出即可。promo 用投影片+fade 完全夠看:
  ```bash
  ffmpeg -y -loop 1 -i "$IMG" -t "$S" -r $FPS \
    -vf "fade=t=in:st=0:d=0.5,fade=t=out:st=$(awk "BEGIN{print $S-0.5}"):d=0.5,format=yuv420p" \
    -threads 2 -c:v libx264 -preset veryfast -pix_fmt yuv420p "$OUT"
  ```
- **要動態才用 zoompan**:餵它**單一輸入幀**,`d` = 總幀數,輸出用 `-frames:v` 收(別放前置 `fps`、別用 `-t` 在 `-i` 前限輸入):
  ```bash
  ffmpeg -y -loop 1 -i "$IMG" \
    -vf "zoompan=z='min(zoom+0.0006,1.06)':d=$((FPS*S)):s=${W}x${H}:fps=$FPS,fade=...,format=yuv420p" \
    -frames:v $((FPS*S)) -threads 2 -c:v libx264 -preset veryfast "$OUT"
  ```
**先試靜態版確認流程通,再決定要不要加動態**——別一開始就 zoompan 然後卡住才 debug。

### 2. CPU 控制(docker 影片合成務必套)
- **`docker run --cpus=2`** 硬限核數(別讓 ffmpeg 吃滿所有核)。
- ffmpeg 全部加 **`-preset veryfast -threads 2`**(promo 不需 crf 18 的慢 preset)。
- **預建工具 image,別每次 apt**:`apt install ffmpeg imagemagick fonts-noto-cjk` 每跑一次裝 ~200MB =
  大半時間花在這。裝一次 `docker commit` 成 `mom-video:latest`,之後重跑零安裝。
- **長 docker run 會被 harness 自動轉背景**;跑壞要 `docker ps -q --filter ancestor=<img> | xargs -r docker kill` 收掉,
  別讓爆炸的容器在背景燒。**有界**:`timeout` 包起來。

### 3. [HARD] 配樂用原版/遊戲真實音訊,不自產(見 rulebook/93)
**MIDI + SoundFont 的遊戲(如 Ebiten/Go 引擎)**:別 live 錄(Ebiten 非 SDL,沒 `SDL_AUDIODRIVER=disk`;
xvfb 又沒音效卡)。**離線抽 + fluidsynth 算**最乾淨、可重現、音色一模一樣:
1. 用引擎自己的 reader 把曲目的 **XMI/MIDI 抽成標準 .mid**(例:`xmi.ReadMidiFromCache(cache,"music.lbx",idx)` →
   `smf.WriteFile("x.mid")`;先找「標題曲」index,如 MoM 的 `SongTitle=104`)。
2. 用遊戲**實際載入的同一顆 SoundFont**(`TimGM6mb.sf2` 等)算 wav:
   `fluidsynth -ni -F title.wav sf.sf2 title.mid`(docker 內 `apt install fluidsynth`)。
- **SDL 遊戲**:`SDL_AUDIODRIVER=disk SDL_DISKAUDIOFILE=cap.raw ./game` 直接錄實機音樂 → `ffmpeg -f s16le -ar 44100 -ac 2 -i cap.raw out.wav`。
- **驗證(鐵則 93-2)**:`ffmpeg -i x.wav -af volumedetect -f null /dev/null` 看 `mean_volume`/`max_volume` 非靜音、無 clipping、時長對。10KB/53s = 壞檔。

### 4. 截圖:滑鼠驅動遊戲 → 用靜態截圖,別跟 xdotool 纏鬥
- **先用專案既有截圖庫**(中文化專案通常 docs/img/ 已有 20+ 張)。夠了就別重錄。
- 鍵盤驅動遊戲:`xdotool key` 編排可錄 live;**滑鼠驅動(選單/法術書/城市畫面靠點)**:xdotool 點座標脆,
  改**靜態截圖 + Ken Burns/fade**(合成段本來就以截圖為主)。要新截圖就加極簡 render harness(SHOT/第 N 幀存 PNG),比驅動 UI 穩。
- 截圖**保留遊戲原色不調色**,只在合成時加金框。

### 5. docker 內字型 / ImageMagick policy
- `fonts-noto-cjk` 只有 **Regular / Bold** 的 `.ttc`(**沒有 Medium/SemiBold**)——用前先 `ls` 確認字型路徑存在,否則 `convert` 報 `unable to read font` 整段沒輸出。
- ImageMagick 預設 policy 可能擋 `@`/URL 讀檔:`sed -i 's/rights="none" pattern="@\*"/rights="read" pattern="@*"/' /etc/ImageMagick-6/policy.xml`(只讀本地檔仍安全)。
- 中文字幕用**襯線**(Noto Serif CJK)較有質感;西方奇幻尤其(黑體=手遊味)。

---

## 可重用骨架(CPU-safe，靜態+fade 版)

`make_promo.sh` —— 設計 token 放最上面(換皮只改這裡),函式 + 分鏡在下面:

```bash
#!/usr/bin/env bash
set -eu
# ===== 設計 token(換遊戲只改這段)=====
BG='#1a1230'; BGD='#0c0818'; GOLD='#c9a227'; GOLDSH='#7a5c14'; BLOOD='#8c1c13'; CREAM='#f2ead2'
FB=/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc      # 標題(先確認存在!)
FR=/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc   # 字幕(沒有 Medium)
W=1280; H=720; FPS=25; SHOT=/shots; OUT=/out; TMP=/tmp/c; mkdir -p "$TMP" "$OUT"

card(){  # $1 out $2 中標 $3 英標 $4 副標 —— 深色徑向漸層 + 鎏金浮雕標題
  convert -size ${W}x${H} "radial-gradient:#241844-${BGD}" -font "$FB" -gravity center \
    -fill "$GOLDSH" -pointsize 92 -annotate +3+3 "$3" -fill "$GOLD" -pointsize 92 -annotate +0+0 "$3" \
    -fill "$CREAM" -pointsize 64 -annotate +0+90 "$2" -fill "$BLOOD" -pointsize 30 -annotate +0+170 "$4" "$1"; }
slide(){ # $1 out $2 screenshot $3 字幕 —— 截圖加金框置中 + 底部字幕
  convert -size ${W}x${H} "gradient:${BG}-${BGD}" "$TMP/bg.png"
  convert "$SHOT/$2" -resize x576 -bordercolor "$GOLD" -border 3 "$TMP/sc.png"
  convert "$TMP/bg.png" \( "$TMP/sc.png" \) -gravity north -geometry +0+24 -composite \
    -fill "#000000aa" -draw "rectangle 0,640 ${W},720" \
    -font "$FR" -fill "$CREAM" -gravity south -pointsize 34 -annotate +0+30 "$3" "$1"; }
kb(){    # $1 png $2 mp4 $3 秒 —— 靜態 + 淡入淡出(不用 zoompan!見雷 #1)
  local FO; FO=$(awk "BEGIN{print $3-0.5}")
  ffmpeg -y -loglevel error -loop 1 -i "$1" -t "$3" -r $FPS \
    -vf "fade=t=in:st=0:d=0.5,fade=t=out:st=$FO:d=0.5,format=yuv420p" \
    -threads 2 -c:v libx264 -preset veryfast -pix_fmt yuv420p "$2"; }

# ===== 分鏡(LLM 依專案填截圖/字幕)=====
card  "$TMP/00.png" '工作魔法大帝' 'Master of Magic' '重現經典 · 全程繁體中文'
slide "$TMP/01.png" overworld.png  '踏遍雙重位面的廣袤疆土'
# ... 更多 slide ...
card  "$TMP/99.png" '工作魔法大帝' 'Master of Magic' '繁體中文版 · 免費開源 · github.com/...'

# ===== concat + 鋪配樂(afade)=====
LIST="$TMP/list.txt"; : > "$LIST"
for f in 00 01 99; do kb "$TMP/$f.png" "$TMP/s_$f.mp4" 7; echo "file '$TMP/s_$f.mp4'" >> "$LIST"; done
ffmpeg -y -loglevel error -f concat -safe 0 -i "$LIST" -threads 2 -c:v libx264 -preset veryfast -pix_fmt yuv420p "$TMP/silent.mp4"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$TMP/silent.mp4"); FO=$(awk "BEGIN{print $DUR-3}")
ffmpeg -y -loglevel error -i "$TMP/silent.mp4" -i /music/title.wav \
  -filter_complex "[1:a]aloop=loop=-1:size=2000000000,atrim=0:$DUR,afade=t=in:st=0:d=2,afade=t=out:st=$FO:d=3[a]" \
  -map 0:v -map "[a]" -threads 2 -c:v libx264 -preset veryfast -c:a aac -b:a 192k -movflags +faststart \
  "$OUT/promo.mp4"
```

> ⚠️ **配樂比影片短 → `-shortest` 會砍掉結尾卡(慘雷)**。單段配樂常只有 40 幾秒;一旦後來加內容(多幾張金句卡)把影片撐到 50 秒+,舊寫法 `[1:a]atrim=0:$DUR ... -shortest` 的 atrim 無法把 44 秒音樂延長到 51 秒,`-shortest` 便以較短的音軌為準,把影片尾端(整張結尾卡!)一起截掉。症狀:`ffprobe` 出來視訊/音訊都變成配樂長度、結尾卡不見。**解法:先 `aloop=loop=-1:size=<大數>` 把配樂無限循環,再 `atrim=0:$DUR` 剪到影片長度,並拿掉 `-shortest`**(視訊音訊已等長)。改完務必 `ffprobe -select_streams v/a` 確認兩者 == 分鏡總長。

跑法:
```bash
# 一次性建工具 image
docker run --cpus=2 --name vb debian:bookworm-slim bash -c \
  'apt-get update -qq && apt-get install -y -qq ffmpeg imagemagick fonts-noto-cjk fluidsynth'
docker commit vb game-video:latest && docker rm vb
# 合成(限 2 核)
docker run --rm --cpus=2 -v $PWD/img:/shots:ro -v /tmp/music:/music:ro -v /tmp/out:/out \
  -v $PWD/make_promo.sh:/make.sh:ro game-video:latest bash /make.sh
```

---

## 迭代(LLM 看圖)
合成後 `ffmpeg -ss <t> -i promo.mp4 -frames:v 1 f.png` 抽 3–4 幀**讀圖**,檢查:標題糊不糊、字幕被裁沒、
配色對不對、黑邊多不多(滿版截圖 vs 中央小圖)、節奏。改 token / 字幕 / 秒數重跑(靜態版很快)。
字幕對比:深底上的暗紅副標常偏暗,改鎏金/米白更清楚。

## 節奏 / 品味
- 前段慢(標題 6s)、亮點段 6–8s/張、結尾留長音;整片 60–75s。
- 截圖保原色只加框;標題鎏金浮雕(暗金陰影 + 主金 + 高光三層)不要螢光黃。
- 配樂淡入 2s、淡出 3s;音色先 ffprobe 驗證非空白。

## 版面變化(避免千篇一律 — 重要)
單一「漸層底 + 置中小截圖 + 底部字幕」重複 12 段會很單調。**準備 5–6 種版面函式輪流用**:
- **分幕配色**:依敘事段落換背景主題(intro 紫 / 問題 暗紅 / 解法 青綠 / 展示 / 結尾金),同一 `bg()` 吃 `theme` 參數。
- **滿版截圖 `slide_full`**(`-resize WxH^ -extent` 填滿 + 下三分之一字幕條)vs **框內截圖 `slide_frame`**(金框置中)——兩者交替,別全用同一種。
- **大引號對白卡 `dcard`**:左對齊 + 巨型半透明引號 `"` + 場景標,和「置中標題卡 `card`」明顯不同視覺。
- **前後對比 `split_ba`**:左右分割(中文 | 英文,中間金色 F8 + ◀▶),秀「切換」類功能超直觀。
- **一兩段 Ken Burns 動態**穿插在靜態之間(用單幀安全法,見雷 #1),讓節奏有呼吸;不要全片靜止也不要全片都動。
- 對白卡可附**英文原文小字**(中文大、英文小灰)——秀翻譯又有層次。
> 判斷:抽 4 幀做 montage 讀圖,若四格「長得都一樣」就是還太單調,回去換版面/配色。

## 每片一個 theme:從遊戲本身萃取風格(避免部部同款 — 重要)

> 「版面變化」解決**一部片內**的單調;本節解決**片與片之間**長得一樣。
> 鐵則:**設計 token 不准沿用上一部片的**。每片開拍前先跑一次「theme 萃取」,產出這部片專屬的 `theme.sh`。

### 1. Token 從遊戲本身來(不是憑喜好挑)

| Token | 來源 | 萃取法 |
|---|---|---|
| 背景漸層兩端色 | 實機截圖的 dominant colors | `convert shot.png -resize 100x100 -colors 8 -depth 8 -format %c histogram:info:- \| sort -rn` → 取像素數多且**最暗**者做深端,次暗做淺端 |
| accent 色(標題/框線) | 遊戲 UI / logo 的強調色 | 同上 histogram 取**飽和度最高**者;或直接吸 logo 主色 |
| 文字色 | 截圖中的字幕/亮色 | 取最亮的非白色;確保與背景對比夠 |
| 標題字體氣質 | 遊戲文類+時代 | 西方奇幻→Serif;科幻/賽博→Sans 或等寬;日系/童話→圓體;軍事/硬派→heavy Bold;喜劇可 Serif+傾斜註記 |
| 版面母題(motif) | 遊戲 UI 元素 | 借遊戲的框:羊皮紙捲軸、魔法陣、軍規檔案框線、CRT 掃描線、石雕邊框——用 IM 畫進 `bg()`/`card()` |
| 節奏(每段秒數) | 文類 | 喜劇 4–5s 快切+對白卡多;史詩 7–8s 長鏡頭;恐怖 變速(長靜+短突) |
| 轉場 dip 色 | 主題色 | fade 不一定過黑——dip-to-color 用背景深端色,整片色調統一 |

### 2. theme.sh 檔案化(換遊戲=寫 theme,不動 pipeline)

把 make_promo.sh 頂部的 token 區抽成獨立 `theme.sh`,合成腳本 `source` 它:
```bash
# theme.sh — 每片一份,給 theme 取個名字錨定決策(如「羊皮紙與墨水」「軍規檔案」「星圖藍」)
THEME_NAME="羊皮紙與墨水"
BG_DEEP='#1a1006'; BG_LITE='#3a2a12'; ACCENT='#b8860b'; TEXT='#f4e8c8'; DIM='#8a7a5a'
FONT_TITLE=...Serif...; FONT_BODY=...
PACE_CARD=5; PACE_CLIP=8            # 節奏
MOTIF=scroll                        # bg()/card() 依此畫母題
```

### 3. 敘事結構庫(選一個「和上一部不同」的骨架)

| 骨架 | 結構 | 適合 |
|---|---|---|
| A 工程敘事 | 問題→解法→證據→CTA | 中文化/修復類(Simon 用過) |
| B 世界觀巡禮 | 場景輪播+一句世界觀/張 | 畫面美、地圖大的遊戲 |
| C 對白精選輯 | 對白卡為主、截圖為輔 | 喜劇/文字冒險 |
| D 前後對照 | 原版 vs 新版 split/交替 | remake、HD 化、漢化 |
| E live 混剪 | 實機錄影當主角、字卡穿插 | 有 x11grab 錄影的 |

### 4. 差異化驗收(硬條件)

- 開拍前寫下「與上一部片的差異至少 3 項」(配色來源、母題、節奏、敘事骨架任選)。
- 完成後:新舊兩部各抽 4 幀 montage **並排看**——若認不出是兩部不同的片=失敗,回去換 theme。
- 反例教訓:MoM(深紫鎏金/魔法史詩)之後 Simon 直接沿用紫金模板,被使用者點名「千篇一律」。
  Simon 該用的是自己的 theme:英式喜劇→羊皮紙暖木色+快切+對白卡為主(骨架 C/E)。

## SDL disk-audio 錄原版遊戲音樂當 BGM(補雷 #3)
SDL 遊戲用 `SDL_AUDIODRIVER=disk` 錄原版音樂時兩個雷:
1. **`SDL_DISKAUDIODELAY=0` = 全速輸出、非即時**:mixer 以 CPU 全速跑,55s wall-clock 可灌出**數小時**音訊、檔案數 GB,音高正確但「量」爆炸。→ 錄完**掃描整段找有聲窗**(逐 30s `ffmpeg volumedetect` 看 mean_volume,**別假設音樂在前 N 秒**;實例:前 80s 全 -91dB 靜音,音樂在 7900s+),截 60–75s 當 BGM,再刪 GB 大檔。
2. **音樂驅動要明確指定否則靜音**:引擎 headless 預設可能選 null MIDI → 只有稀疏 sfx。ScummVM AGOS 要 `-e adlib --music-volume=255` 才出音樂。

## 來源
魔法師西蒙(Simon)CD×Floppy 融合繁中推廣片 2026-07:多版面(分幕配色/滿版/框內/大引號/F8 前後對比/Ken Burns)破除單調;
配樂用 SDL `disk` 錄原版 AdLib 音樂(`-e adlib`,全速灌爆需掃描找有聲窗)。
工作魔法大帝(Master of Magic)繁中推廣片 2026-06-28:zoompan 幀數爆炸燒 8 分鐘 CPU、改靜態+fade 秒成;
配樂用 remake 的 `music.lbx` XMI #104 + `TimGM6mb.sf2` fluidsynth 離線算(乾淨可重現)。
配 `rulebook/93-promo-video-original-assets.md`(素材來源[HARD])、u1-cht `docs/llm-promo-video-pipeline.md`(pipeline 起源)、`retro-game-playtest`(截圖/可玩性)。
