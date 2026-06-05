# QB64-PE 編譯環境 (Ubuntu 24.04)
# 用途:把 AK_CHT.bas 編成 Linux native ELF
#
# Build:
#   docker build -f tools/qb64pe.Dockerfile -t ak-cht-qb64pe:latest .
#
# Compile (bind-mount source):
#   docker run --rm -v "$PWD/AK_CHT_src:/work" -w /work \
#     ak-cht-qb64pe:latest /opt/qb64pe/qb64pe -x -w AK_CHT.bas -o akalabeth
#
# 由 tools/build-in-docker.sh 包成一鍵流程

FROM ubuntu:24.04

ARG QB64PE_VERSION=4.5.0
ARG DEBIAN_FRONTEND=noninteractive

# QB64-PE setup_lnx.sh 要求的 deps + 我們額外需要的工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    x11-utils \
    mesa-common-dev \
    libglu1-mesa-dev \
    libasound2-dev \
    libpng-dev \
    libcurl4-openssl-dev \
    libfreetype-dev \
    libfontconfig1-dev \
    ca-certificates \
    curl \
    wget \
    file \
    locales \
    && rm -rf /var/lib/apt/lists/*

# Ubuntu 24.04 預設 ubuntu user 佔了 UID 1000,直接砍掉避免衝突
# 我們不走 setup_lnx.sh(它擋 root),手動跑 make 沒這限制
RUN userdel -r ubuntu 2>/dev/null || true \
 && mkdir -p /opt/qb64pe

WORKDIR /opt

# 抓 QB64-PE source tarball,展開後檔案在 /opt/qb64pe/
# (tarball 結構是 ./qb64pe/...,直接抽即可,別亂用 --strip-components)
RUN curl -sSL "https://github.com/QB64-Phoenix-Edition/QB64pe/releases/download/v${QB64PE_VERSION}/qb64pe_lnx-${QB64PE_VERSION}.tar.gz" \
        -o /tmp/qb64pe.tar.gz \
 && tar xzf /tmp/qb64pe.tar.gz -C /opt \
 && rm /tmp/qb64pe.tar.gz \
 && test -f /opt/qb64pe/Makefile

# 編譯 qb64pe compiler 本體 (不用 IDE,只要 CLI compiler)
# BUILD_QB64=y 是 setup_lnx.sh 用的 flag,等同手動 make
RUN cd /opt/qb64pe \
 && make OS=lnx BUILD_QB64=y -j"$(nproc)"

# 確認 binary 在(放 chmod 前,避免之後寫進去的檔案 perm 被覆寫)
RUN test -x /opt/qb64pe/qb64pe && /opt/qb64pe/qb64pe -? 2>&1 | head -20 || true

# 砍 object 釋出空間;然後讓 bind-mount user (隨機 uid) 也能寫 internal/temp
# qb64pe 編譯時會在這暫存 C++ 中間檔
RUN find /opt/qb64pe -name "*.o" -delete \
 && chmod -R a+rwX /opt/qb64pe/internal/temp /opt/qb64pe/internal/c

# 編譯時容器內預設工作目錄 /work,使用者由外部 bind-mount 進來
WORKDIR /work

ENV PATH="/opt/qb64pe:${PATH}"

# default cmd:把 AK_CHT.bas 編成 ./akalabeth
# -x 編完直接離開、-w 顯示 warning、-c 純編譯不 IDE
CMD ["qb64pe", "-x", "-w", "-c", "AK_CHT.bas", "-o", "akalabeth"]
