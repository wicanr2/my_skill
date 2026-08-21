---
name: kimi-pptd-deck-authoring
description: 用 open-kimi-ppt 的 PPTD 格式做簡報,以及**瀏覽器匯出管線失效時改用 python-pptx 自行產 pptx** 的替代路徑。觸發:「用 kimi ppt 做簡報」「PPTD」「.pptd / .page」「pptd 轉 pptx」「export_pptx.py 失敗」「deckStatus === ready 逾時」「timed out waiting for download」「匯出對話框沒就緒 / 找不到下载按鈕」「PPT 產不出來」,或任何要交付 .pptx 而 open-kimi-ppt 的匯出卡住的情況。
---

# 用 PPTD 做簡報,以及匯出失敗時怎麼辦

## 先把「格式」和「管線」分開

這是整份筆記的關鍵,分不開就會在錯的地方修很久。

- **PPTD 是格式**:本機 YAML,一個 `.pptd` 主檔 + 一堆 `.page`。可版控、可 diff、可程式產生。**很好用。**
- **Kimi 的匯出是管線**:把 PPTD 餵進遠端公開編輯器,用它**瀏覽器端**的 OOXML writer 產檔。**不可靠。**

**兩者可以拆開**:用 PPTD 寫內容,用 python-pptx 產 `.pptx`。內容與呈現的價值在格式那一半,不在管線。

## 三條輸出路徑的可靠度

| 路徑 | 依賴 | 實測 |
|---|---|---|
| `scripts/export_pptx.py` | 遠端編輯器 + agent-browser + Chrome | ❌ 三個階段都會失敗(見下) |
| `scripts/export_images.py` | 同上 | ⚠️ 可用,但偶爾逾時,重跑即可 |
| **自寫 python-pptx 轉換器** | 只有本機 docker | ✅ 確定性,無遠端依賴 |

## 匯出失敗的三個階段(照這個順序判別)

```
① wait --fn document.documentElement.dataset.deckStatus === "ready"
   ✗ Wait timed out after 60000ms          → deck 根本沒載進編輯器

② [open-kimi-ppt] generating PPTX in the browser
   download capture reported a timeout      → 載進去了,但產檔/下載沒完成
   timed out waiting for download; observed files:
     .../payload.json  .../export_host.html  → 下載目錄空的

③ export dialog did not become ready        → 匯出對話框裡找不到「下载」按鈕,
                                               snapshot 只有幾個無名稱 button
```

三個階段會**隨機出現不同的那一個**,很容易誤以為是偶發、一直重試。

### [HARD] 下結論前先做正對照

不要憑失敗訊息判斷是自己的簡報有問題。**用 skill 自帶的範例跑一次**:

```bash
cp -r <skill>/example/yu7-ppt /tmp/ctrl && rm -f /tmp/ctrl/yu7.pptx
cd /tmp/ctrl && python3 <skill>/scripts/export_pptx.py yu7.pptd --output ctrl.pptx
```

範例也在**完全相同的階段**失敗 = 環境／上游問題,不是你的簡報。這一步省下的是
「反覆簡化自己的簡報想找出哪個元素害的」那種白工。

⚠️ 正對照本身也可能只跑到階段 ①(那個是偶發的)。**要重試到它走過 ① 為止**,
否則證明不了什麼。

### 順手排除掉的假設

- **不是中日韓字型內嵌太慢** —— `--no-embed-fonts` 一樣失敗。
- **不是簡報太大** —— 自帶範例(8 張圖 / 7.6 MB)也失敗。

## 替代路徑:python-pptx

作法沿用「週報用 docker + uv 產 pptx」那一套。**確定性、全程本機。**

```bash
# ① PPTD → PPTX
docker run --rm --log-opt max-size=10m --log-opt max-file=3 \
  -v "$(pwd)":/work -w /work ghcr.io/astral-sh/uv:python3.12-bookworm-slim \
  bash -c "uv run --with python-pptx --with pyyaml pptd_to_pptx.py deck.pptd deck.pptx"

# ② PPTX → PDF
docker run --rm --log-opt max-size=10m --log-opt max-file=3 \
  -v "$(pwd)":/work -w /work linuxserver/libreoffice:latest \
  bash -c "libreoffice --headless --convert-to pdf deck.pptx"

# ③ [HARD] docker 以 root 寫檔,交付前一律 chown 回來
docker run --rm -v "$(pwd)":/work -w /work alpine chown -R "$(id -u):$(id -g)" /work
```

可直接取用的轉換器:**`kimi-pptd-to-pptx.py`(與本檔同目錄)**。
涵蓋 text(含富文字)/ shape / line(含箭頭虛線)/ table,不含 image 與 chart。

### 座標換算

PPTD 規格 **1px = 1pt**,原點左上。`960×540` 正好是 16:9 寬螢幕(13.333×7.5 in),
所以 python-pptx 直接 `Pt(x)` 就對,不需要任何比例換算。

```python
prs.slide_width  = Pt(960)
prs.slide_height = Pt(540)
slide = prs.slides.add_slide(prs.slide_layouts[6])   # 6 = 空白版面
```

### [HARD] python-pptx 沒有 API、必須自己寫 XML 的五件事

這五項是重寫轉換器時最花時間的部分,每一項都在 `font.name` / `cell.border` 這種
「看起來應該有」的地方撲空。

**① 東亞字型**。`font.name` 只設 latin;中文會掉回預設字型。要自己加 `a:ea`:

```python
rPr = run._r.get_or_add_rPr()
for tag in ("a:ea", "a:cs"):
    el = rPr.find(qn(tag))
    if el is None:
        el = rPr.makeelement(qn(tag), {}); rPr.append(el)
    el.set("typeface", "Microsoft JhengHei")
```

**② 表格逐邊框線**。`cell` 沒有 border API。要寫 `a:lnT/lnR/lnB/lnL`,
而且**必須 insert 到 `tcPr` 開頭**(OOXML 要求的順序);不要的邊要明確填 `a:noFill`,
不然會沿用預設樣式。

**③ 關掉預設表格樣式**。python-pptx 加出來的表格帶首列強調與斑馬紋。
自己畫線之前先把 `tblPr` 的 `firstRow/bandRow/lastRow/firstCol/lastCol/bandCol`
全設 `"0"`,並移除 `a:tableStyleId`。

**④ 切換動畫的位置**。`<p:transition>` 必須是 `<p:sld>` 的**直接子元素**,
且排在 `cSld` / `clrMapOvr` 之後(CT_Slide 的順序要求)。

> ⚠️ **塞進 `cSld` 裡面 Office 會直接忽略,而 `grep '<p:fade>'` 驗不出這個差別** ——
> 字串照樣搜得到。要驗的是**子元素順序**,不是字串存在。

**⑤ 連接線箭頭與字距**。箭頭:在 `line._get_or_add_ln()` 上加
`<a:tailEnd type="stealth"/>`。字距:`rPr` 的 `spc` 屬性,單位是 1/100 pt。

### 折線怎麼畫

PPTD 的 `line` 用 `viewBox` + `points`,可以是折線。**拆成多段直線連接器畫,
箭頭只加在最後一段** —— 比造自由形狀幾何簡單,PowerPoint 相容性也最好。

## 四個會安靜出錯的坑

**① 不要把圖檔放進 PPTD 專案目錄。**
匯出器會把專案底下**所有** jpg/jpeg/png/gif/svg 當成簡報資源打包成 data URL。
把算圖檢查產物 `.qa-images/` 留在裡面,log 會出現
`prepared 15 local image resource(s), 3008411 bytes` —— 而那份簡報一張圖都沒有。
**看到這行就核對數字對不對得上你真正用到的圖。**

**② 遠端 chart 渲染會整張消失。**
同一份 PPTD 連續匯出兩次,第二次的長條圖變成空白區域,而 `.page` 裡元素好好的。
**需要圖表就用原生 `shape` 自己畫長條**:確定性,而且能去掉預設圖表的框線、圖例、
格線 —— 技術類簡報的風格指南本來就要求移除那些。畫法很簡單:一條基線 + 幾個
`rect` + 直接標值。

**③ 字型替代會撐寬版面。**
PPTX 裡寫的字型名在對方機器上不一定存在(LibreOffice 容器就沒有微軟正黑體),
替代字型通常更寬。**標題不要排到剛好填滿版心** —— 留餘裕,否則會在別人機器上換行。
中文用 `Microsoft JhengHei`、西文用 `Arial` 是相對安全的組合(交付對象多為 Windows)。

**④ `.page` 是產物,不要手改。**
用一支產生器把內容與版面常數寫成程式,改內容改產生器再重跑。
手改 `.page` 之後下次重跑就被蓋掉,而且 diff 沒有意義。

## 驗證(兩層,都要)

**結構驗證**(本機沒有官方 checker,自己寫一支):必填欄位、`bounds` 在頁內、
`$` 主題引用解得開、`elementId` 唯一、表格 `columnWidths`/`rowHeights` 加總為 1、
合併儲存格後每列填滿、chart 的 `cols` 唯一且 `rows` 長度相符。

**視覺驗證**(結構驗證抓不到):把 PDF 算成圖逐頁看。

```bash
pdftoppm -r 110 -jpeg deck.pdf preview        # 再把 preview-*.jpg 拼成一張總覽
```

逐頁對照:① 文字有沒有溢出文字框 ② 元素有沒有出界 ③ 有沒有被上層遮擋
④ 對比夠不夠 ⑤ 排版是否一致。**實測四頁缺陷全是這一關抓到的**,
結構驗證那關是 0 錯 0 警。

`export_images.py` 也能算圖(走 Kimi 編輯器),但它算的是編輯器的渲染;
**最終交付是 python-pptx 產的檔,要驗的就該是那個檔轉出的 PDF。**

## PPTD 格式速查

```yaml
# deck.pptd
version: v2
size: [960, 540]
theme:
  colors: {ink: "#1A1A17", accent: "#B4472B"}      # 引用寫 "$ink"
  textStyles:
    h1: {fontSize: 27, color: "$ink", bold: true}   # 引用寫 style: "$h1"
  tableStyles:
    cmp: {cellStyle: {...}, firstRowStyle: {...}}   # 引用寫 style: "$cmp"
pages: [pages/01_cover.page]
```

```yaml
# pages/01_cover.page
elements:                       # 陣列順序 = 圖層,越後面越上層
  - elementId: t1               # 同頁內唯一
    elementType: text           # text|shape|line|image|icon|table|chart
    bounds: [x, y, w, h]        # px,原點左上
    content:
      style: "$h1"
      align: [left, top]        # [水平, 垂直]
      wrap: false               # 單行文字建議明確設 false
      text: |
        <p>富文字:<strong>粗</strong>、<span style="color:$accent">上色</span></p>
```

- `shape` **不支援內嵌文字**,要另外疊一個文字框。
- `line` 的 `viewBox` 比例要等於 `bounds` 比例,否則線會被拉伸變形。
- 表格的 `columnWidths` / `rowHeights` 是**比例**不是 px,各自加總必須為 1。
- 合併儲存格:被覆蓋的位置**直接從 `rows` 陣列省略**,不放 `null` 佔位。

## 手動匯出的後路

真的需要走官方 writer:`npx open-kimi-ppt-skills serve`,開
`http://127.0.0.1:55173/` 授權整個 PPTD 專案目錄,在自己的瀏覽器裡手動匯出。
需要 Chromium 系瀏覽器才有寫入權限(資料夾上傳的退路是唯讀)。
