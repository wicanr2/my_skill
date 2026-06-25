# 計畫書 markdown → docx pipeline(含架構圖嵌入)

把分章 `plan/*.md` 合併成單檔、轉成含架構圖的 Word docx。實證可行,規避 LibreOffice 對 SVG 內嵌的 IO abort。

## 前置
- 章節檔在 `$DIR/plan/`,架構圖 `$DIR/architecture.svg`。
- 工具:`chrome-headless`(SVG→PNG)、`libreoffice/soffice`、docker uv image `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`。
- Python 一律 docker uv venv,不污染系統。

## 步驟

### 1. 合併章節 → 單檔(修正圖路徑)
```bash
cd $DIR
{
  echo "# 計畫書標題"; echo
  echo "| 版本 | vX | 日期 | YYYY-MM-DD |"; echo "|---|---|---|---|"; echo
  for f in 00-executive-summary 00-introduction 01-related-work 02-proposed-approach \
           03-implementation 04-discussion 05-schedule 06-conclusion references terminology; do
    cat "plan/$f.md"; echo; echo
  done
} | sed 's#\.\./architecture\.svg#architecture.svg#g' > plan-final.md
```

### 2. 架構圖 SVG → PNG(chrome-headless,2x 解析)
```bash
google-chrome --headless=new --disable-gpu --no-sandbox --screenshot=architecture.png \
  --window-size=1100,560 --force-device-scale-factor=2 --hide-scrollbars \
  --default-background-color=FFFFFFFF architecture.svg
```

### 3. markdown → HTML(docker uv + markdown 套件)
`build_html.py`(讀 plan-final.md,套 CSS,extensions=tables/fenced_code/sane_lists/attr_list,寫 AI-...-Plan.html;img 用 `<img src="architecture.svg">` 給瀏覽)。
```bash
docker run --rm -v "$PWD":/w -w /w $IMG bash -c \
  "uv venv /tmp/v -q && . /tmp/v/bin/activate && uv pip install markdown -q && python build_html.py"
```

### 4. HTML → docx(LibreOffice,先 strip img)
**關鍵**:SVG 內嵌 LibreOffice 會 `IO abort Code:27`。先移除 `<img>` 再轉。
```bash
pkill -9 soffice 2>/dev/null; sleep 2
sed 's#<img[^>]*>##g' AI-...-Plan.html > _nofig.html
soffice --headless -env:UserInstallation=file:///tmp/lo_x --infilter="HTML (StarWriter)" \
  --convert-to 'docx:MS Word 2007 XML' --outdir . _nofig.html
mv -f _nofig.docx AI-...-Plan.docx && rm -f _nofig.html
```
注意:用 `HTML (StarWriter)` infilter 才會對應 Word 標準 Heading 樣式(可自動生成目錄);預設 Writer/Web 模式排版較陽春。

### 5. python-docx 插架構圖 PNG(以圖說文字定位)
`insert_fig.py`:找含「圖 1」且「系統架構」的段落,在其前 `insert_paragraph_before()` + `add_picture(PNG, width=Inches(6.4))`,置中,save。
```bash
docker run --rm -v "$PWD":/w -w /w $IMG bash -c \
  "uv venv /tmp/v -q && . /tmp/v/bin/activate && uv pip install python-docx -q && python insert_fig.py"
```

### 6. 驗證
```bash
cd /tmp && rm -rf chk && mkdir chk && cd chk && unzip -q $DIR/AI-...-Plan.docx
grep -o 'w:val="Heading1"' word/document.xml | wc -l   # 章數
ls word/media/                                          # 應有 image1.png(架構圖已嵌入)
grep -o '<w:tbl>' word/document.xml | wc -l             # 表格數
```

## 常見坑
- **docx 沒圖(word/media 空)**:LibreOffice 的 HTML filter 不嵌入外部 `<img>`;必須走步驟 5 用 python-docx 補插。
- **store IO abort**:殘留 soffice 實例或 SVG 內嵌;`pkill soffice` + strip `<img>`。
- **png 太大撐爆版面**:`insert_fig.py` 用 `Inches(6.0~6.4)` 控寬。
- **中文字型**:HTML CSS 指定 `Noto Sans CJK TC`;SVG `font-family` 同。
