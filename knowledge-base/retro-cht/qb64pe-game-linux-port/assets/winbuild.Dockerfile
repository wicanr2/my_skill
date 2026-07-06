# Windows cross-build via Wine + QB64-PE Windows release
# 用途:把 AK_CHT.bas 編成 Windows EXE,再用 7z SFX 包成自解壓 .exe
#
# Build:
#   docker build -f tools/winbuild.Dockerfile -t ak-cht-winbuild:latest .
#
# Run (from project root):
#   docker run --rm -v "$PWD:/work" -w /work ak-cht-winbuild:latest \
#       bash tools/build-windows.sh

FROM ubuntu:24.04

ARG QB64PE_VERSION=4.5.0
ARG DEBIAN_FRONTEND=noninteractive

# Wine + 7zip + curl
RUN dpkg --add-architecture i386 && \
    apt-get update && apt-get install -y --no-install-recommends \
    wine wine64 wine32:i386 \
    p7zip-full \
    curl \
    ca-certificates \
    xvfb \
    cabextract \
 && rm -rf /var/lib/apt/lists/*

# Ubuntu 24.04 預設 ubuntu user 占 UID 1000,砍掉
RUN userdel -r ubuntu 2>/dev/null || true

# 抓 QB64-PE Windows x64 release
WORKDIR /opt
RUN curl -sSL -o /tmp/qb64pe-win.7z \
    "https://github.com/QB64-Phoenix-Edition/QB64pe/releases/download/v${QB64PE_VERSION}/qb64pe_win-x64-${QB64PE_VERSION}.7z" \
 && mkdir -p /opt/qb64pe-win \
 && 7z x /tmp/qb64pe-win.7z -o/opt/qb64pe-win \
 && rm /tmp/qb64pe-win.7z \
 && ls /opt/qb64pe-win/

# zip 工具(7-Zip extras 不含 sfx,改用 .7z + .zip 雙格式給玩家)
RUN apt-get update && apt-get install -y --no-install-recommends \
    zip \
 && rm -rf /var/lib/apt/lists/*

# Wine prefix 初始化(避免每次 run 都跑 wineboot)
ENV WINEPREFIX=/opt/wine-prefix
ENV WINEARCH=win64
ENV WINEDLLOVERRIDES="mscoree,mshtml="
ENV WINEDEBUG=-all
RUN mkdir -p /opt/wine-prefix && \
    xvfb-run -a wineboot --init 2>&1 | tail -5 || true && \
    wineserver -w

# 開放權限讓 bind-mount user 也能用
RUN chmod -R a+rwX /opt/qb64pe-win /opt/wine-prefix

WORKDIR /work
