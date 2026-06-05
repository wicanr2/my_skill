#!/usr/bin/env python3
"""BDF → font_t16.dat 轉檔工具

用途
----
把 WenQuanYi 點陣正宋(或任何 16×16 BDF Unicode/Big5 點陣字)轉成
AK_CHT 使用的 font_t16.dat 格式。

格式
----
- 32 byte/字,16 列 × 2 byte/列 (16 bit MSB-first)
- 索引:Big5 ETen,offset(1-based) = (big5_code - 0xA140 + 1) * 32
- 檔案前 32 byte 視為 padding (對應 big5_code < 0xA140)

執行(必須走 docker uv.venv,不污染系統 Python):
    docker run --rm -v "$PWD:/work" -w /work -u "$(id -u):$(id -g)" \\
        ak-cht-fonttools:latest \\
        python tools/bdf-to-font_t16.py \\
            --bdf wenquanyi_13px.bdf \\
            --big5-table BIG5.TXT \\
            --out AK_CHT_src/font_t16_wqy.dat
"""

import argparse
import struct
import sys
from pathlib import Path


def parse_bdf(path: Path) -> dict[int, list[int]]:
    """Parse BDF file → dict[unicode_codepoint] = [16 rows of 16-bit MSB int].

    僅支援 16×16 等寬 bitmap。非 16×16 的字會被填白/裁切到 16×16。
    """
    glyphs: dict[int, list[int]] = {}
    code: int | None = None
    bbx_w = bbx_h = bbx_ox = bbx_oy = 0
    in_bitmap = False
    bitmap_rows: list[int] = []

    with path.open("rb") as f:
        for raw in f:
            line = raw.decode("ascii", errors="replace").strip()
            if line.startswith("ENCODING"):
                code = int(line.split()[1])
            elif line.startswith("BBX"):
                parts = line.split()
                bbx_w = int(parts[1])
                bbx_h = int(parts[2])
                bbx_ox = int(parts[3])
                bbx_oy = int(parts[4])
            elif line == "BITMAP":
                in_bitmap = True
                bitmap_rows = []
            elif line == "ENDCHAR":
                in_bitmap = False
                if code is not None and code >= 0:
                    glyphs[code] = _normalize_to_16x16(
                        bitmap_rows, bbx_w, bbx_h, bbx_ox, bbx_oy
                    )
                code = None
            elif in_bitmap:
                # 每列 hex string,左邊起算的 bbx_w bit
                bitmap_rows.append(int(line, 16))
    return glyphs


def _normalize_to_16x16(
    rows: list[int], w: int, h: int, ox: int, oy: int
) -> list[int]:
    """把任意 BBX 的 bitmap 補齊成 16×16,回傳每列一個 16-bit int (MSB first)。

    BDF 列的 hex 是 left-justified,寬度向上 round 到 byte。
    """
    # 每列原始 bit 寬度 round 到 8 的倍數
    row_byte_w = (w + 7) // 8
    row_bit_w = row_byte_w * 8

    # 上下對齊:把字元 vertical-center 進 16 列
    # 大部分 WenQuanYi 16px BDF 的 BBX 就是 16x16 ox=0 oy=-2,直接平移
    top_pad = max(0, (16 - h) // 2)
    bot_pad = max(0, 16 - h - top_pad)

    out: list[int] = [0] * top_pad
    for r in rows[: 16 - top_pad - bot_pad]:
        # 把 r 從 row_bit_w 寬 align 到 16 bit,左邊起算
        # 例如 BBX 8x16 ox=4 → 右移 4 bit;BBX 16x16 ox=0 → 不動
        if row_bit_w >= 16:
            v = r >> (row_bit_w - 16)
        else:
            v = r << (16 - row_bit_w)
        v &= 0xFFFF
        # X offset(BBX 第 3 個值)右移
        if ox > 0:
            v = (v >> ox) & 0xFFFF
        elif ox < 0:
            v = (v << -ox) & 0xFFFF
        out.append(v)
    out.extend([0] * bot_pad)
    return out[:16] + [0] * max(0, 16 - len(out))


def load_unicode_to_big5(path: Path) -> dict[int, int]:
    """讀官方 BIG5.TXT(Unicode mapping),回傳 unicode → big5 dict。

    BIG5.TXT 格式:每行 `0xBig5 0xUnicode # comment`
    """
    table: dict[int, int] = {}
    with path.open("r", encoding="ascii", errors="replace") as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            try:
                big5 = int(parts[0], 16)
                uni = int(parts[1], 16)
            except ValueError:
                continue
            # 取 unicode → big5(若多個 Big5 對到同個 Unicode 取第一個)
            table.setdefault(uni, big5)
    return table


def build_font_t16(
    glyphs: dict[int, list[int]],
    uni_to_big5: dict[int, int] | None,
    out_path: Path,
) -> None:
    """組出 font_t16.dat。

    若 glyphs key 是 Big5 直接用;否則透過 uni_to_big5 轉。
    Big5 範圍 0xA140–0xFEFE,但 32 byte/字 平鋪。
    """
    # 計算最大 Big5 code(決定檔案大小)
    if uni_to_big5:
        big5_glyphs: dict[int, list[int]] = {}
        for code, rows in glyphs.items():
            big5 = uni_to_big5.get(code)
            if big5 is None:
                continue
            big5_glyphs[big5] = rows
    else:
        big5_glyphs = glyphs

    if not big5_glyphs:
        sys.exit("ERROR: 沒有任何字成功對到 Big5,檢查 BIG5.TXT 與 BDF 編碼")

    max_big5 = max(big5_glyphs.keys())
    # 公式:offset = (code - 0xA140 + 1) * 32
    # 最後一字尾 byte = (max_big5 - 0xA140 + 2) * 32 - 1
    file_size = (max_big5 - 0xA140 + 2) * 32

    buf = bytearray(file_size)
    written = 0
    for big5, rows in big5_glyphs.items():
        if big5 < 0xA140:
            continue
        offset = (big5 - 0xA140 + 1) * 32  # 1-based for QB Get,但 buf 是 0-based
        # QB Get position 是 1-based byte position → buf index = position - 1
        buf_pos = offset - 1
        if buf_pos + 32 > file_size:
            continue
        for i, row in enumerate(rows[:16]):
            buf[buf_pos + i * 2] = (row >> 8) & 0xFF
            buf[buf_pos + i * 2 + 1] = row & 0xFF
        written += 1

    out_path.write_bytes(bytes(buf))
    print(
        f"已寫出 {out_path} 大小 {file_size} bytes,"
        f"含 {written} 個 Big5 字 (max code 0x{max_big5:04X})"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bdf", type=Path, required=True, help="輸入 BDF 字型檔")
    ap.add_argument(
        "--big5-table",
        type=Path,
        help="Unicode → Big5 對照表(BIG5.TXT,如 BDF 是 Unicode 編碼必填)",
    )
    ap.add_argument("--out", type=Path, required=True, help="輸出 font_t16.dat")
    ap.add_argument(
        "--encoding",
        choices=["unicode", "big5"],
        default="unicode",
        help="BDF 字型的編碼空間(預設 unicode)",
    )
    args = ap.parse_args()

    print(f"[1/3] 讀 BDF: {args.bdf}")
    glyphs = parse_bdf(args.bdf)
    print(f"    {len(glyphs)} glyphs")

    uni_to_big5 = None
    if args.encoding == "unicode":
        if not args.big5_table:
            sys.exit("ERROR: BDF 是 Unicode 編碼,必須提供 --big5-table BIG5.TXT")
        print(f"[2/3] 讀 Big5 對照表: {args.big5_table}")
        uni_to_big5 = load_unicode_to_big5(args.big5_table)
        print(f"    {len(uni_to_big5)} Unicode→Big5 mappings")
    else:
        print("[2/3] BDF 自身是 Big5 編碼,跳過對照表")

    print(f"[3/3] 寫出 {args.out}")
    build_font_t16(glyphs, uni_to_big5, args.out)


if __name__ == "__main__":
    main()
