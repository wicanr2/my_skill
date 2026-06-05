#!/usr/bin/env python3
"""P0-1B 簡化版:商店畫面加分區 header,讓 row 5-10 的 stat|item 雙欄結構視覺清楚。

原版商店 row 5-10 已經是 dual column(左 stat 右 item),但沒 header,玩家可能
不知道為什麼這兩塊放一起。加 row 4 header 「屬 性    武 器」。

完整版(Designer Review §3.2 重排)風險太高(block-local LocateC、60237 / 60240
更新位置硬編碼),延後到後續版本。
"""

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from patch_bas import BasFile, encode_big5  # noqa: E402

SRC = Path(__file__).parent.parent / "AK_CHT_src" / "AK_CHT.bas"
MARKER = b"' AK_SHOP_HEADER_PATCH v1"

ATTR = encode_big5("屬 性")
ITEM = encode_big5("武 器")


def main() -> None:
    bas = BasFile.load(SRC)
    if any(MARKER in line for line in bas.lines):
        print("已套過 shop header patch,略過")
        return

    # 在 line 60080 的 `For x = 0 To 5:` 之前 inject header drawing
    idx_60080 = bas.find_basic_line(60080)
    old = bas.lines[idx_60080]
    pat = b"For x = 0 To 5: SetColor 0, 15, 0: PrintC 0, c$(x)"
    if pat not in old:
        print("ERROR: 找不到 line 60080 stats loop pattern")
        return

    # 插入 header drawing 在 For 之前
    # row 4, col 1 = "屬 性"; row 4, col 22 = "武 器"; 用亮黃 14 凸顯
    header = (
        b"LocateC 0, 4, 1: SetColor 0, 14, 0: "
        + b'PrintC 0, "' + ATTR + b'", 0: '
        + b'PrintC 0, TabC$(0, 22), 0: '
        + b'PrintC 0, "' + ITEM + b'", -1: '
        + b"SetColor 0, 15, 0: "
    )
    new = old.replace(pat, header + pat, 1)
    bas.lines[idx_60080] = new
    print(f"  line 60080: 加 row 4 header 「屬 性 / 武 器」")

    bas.insert_before(0, [MARKER])
    bas.save()
    print("完成 P0-1B 簡化版 shop header")


if __name__ == "__main__":
    main()
