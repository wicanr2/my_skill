#!/usr/bin/env bash
# 一鍵 Docker 編譯 AK_CHT.bas → Linux native ELF
#
# 用法:
#   ./tools/build-in-docker.sh                # build image + compile
#   ./tools/build-in-docker.sh --skip-image   # 跳過 image build,直接 compile
#
# 產出:
#   AK_CHT_src/akalabeth        ELF binary
#   AK_CHT_src/akalabeth.txt    QB64-PE 編譯 log (warning/error)

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="ak-cht-qb64pe:latest"
SRC_DIR="$HERE/AK_CHT_src"

cd "$HERE"

if [ "${1:-}" != "--skip-image" ]; then
    echo "[1/2] Build docker image $IMAGE (第一次約 5–10 分鐘)..."
    docker build \
        -f tools/qb64pe.Dockerfile \
        -t "$IMAGE" \
        .
fi

echo "[2/2] Compile AK_CHT.bas → akalabeth"
# qb64pe CLI flags:
#   -x : compile,進度寫 console (適合 headless docker,跟 -c 互斥)
#   -w : 顯示 warning
#   -o : 指定輸出檔名
# 不用 -u $UID:$GID,因為 qb64pe 在 non-root 下會莫名出 "Press enter to continue"
# 然後不寫任何 log 就 exit 1。改為以 root 編,編完 chown 輸出回 host user。
UID_GID="$(id -u):$(id -g)"
docker run --rm \
    -v "$SRC_DIR:/work" \
    -w /work \
    "$IMAGE" \
    bash -c "qb64pe -x -w AK_CHT.bas -o akalabeth && chown ${UID_GID} akalabeth"

echo "---"
ls -lh "$SRC_DIR/akalabeth" 2>/dev/null || {
    echo "ERROR: akalabeth ELF 沒產出,看 $SRC_DIR/*.txt log"
    exit 1
}

file "$SRC_DIR/akalabeth"
echo
echo "完成。執行:cd AK_CHT_src && ./akalabeth"
