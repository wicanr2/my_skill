# 字型轉檔用 Docker image (Ubuntu 24.04 + uv-managed venv + WenQuanYi BDF)
# 用途:把 BDF 轉成 AK_CHT 的 font_t16.dat
#
# Build:
#   docker build -f tools/fonttools.Dockerfile -t ak-cht-fonttools:latest .
#
# Run:
#   docker run --rm -v "$PWD:/work" -w /work -u "$(id -u):$(id -g)" \\
#       ak-cht-fonttools:latest \\
#       python tools/bdf-to-font_t16.py \\
#           --bdf /opt/fonts/wenquanyi_13px.bdf \\
#           --big5-table /opt/fonts/BIG5.TXT \\
#           --out AK_CHT_src/font_t16_wqy.dat

FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    fonts-wqy-zenhei \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安裝 uv(獨立 venv,不污染系統 Python)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
 && cp /root/.local/bin/uv /usr/local/bin/uv

# 建立 venv 並用系統 uv 把 fonttools+pillow 裝進去
RUN uv venv /opt/venv \
 && VIRTUAL_ENV=/opt/venv uv pip install fonttools pillow

ENV PATH="/opt/venv/bin:${PATH}"
ENV VIRTUAL_ENV=/opt/venv

# 抓 WenQuanYi 點陣正宋(13px 是其中一個常用尺寸,16px 在另一檔)
# 注意:fonts-wqy-bitmapsong 在 Ubuntu 24.04 的 main repo 已不存在,改抓 upstream
WORKDIR /opt/fonts

# Unicode → Big5 對照表(Unicode 官方)
RUN curl -sSL "https://unicode.org/Public/MAPPINGS/OBSOLETE/EASTASIA/OTHER/BIG5.TXT" \
        -o BIG5.TXT

# WenQuanYi BitmapSong (含 13px BDF) — 從 sourceforge mirror
RUN curl -sSL "https://sourceforge.net/projects/wqy/files/wqy-bitmapfont/1.0.0-RC1/wqy-bitmapsong-bdf-1.0.0-RC1.tar.gz/download" \
        -o wqy-bdf.tar.gz \
 && tar xzf wqy-bdf.tar.gz \
 && rm wqy-bdf.tar.gz \
 && ls -la

WORKDIR /work
