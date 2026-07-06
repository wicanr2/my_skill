#!/usr/bin/env python3
"""P2:小地圖視覺增強(Designer Review §3.4)。

原作 minimap 是「全顯示無 fog」,所有地形 te%()/dn%() 都畫出來。
「未探索方向標」在沒有 visit-tracking 的前提下不太可行,改成:

1. Player marker 從 2x2 px 加大成 4x4 px + 亮黃外環(雷達游標感)
2. 戶外 landmark (te%() 值 2/3/4/5,即城鎮/堡壘/迷宮) 加 1px 黃色閃光點
   讓玩家視覺上能掃到「還有什麼地點可去」

實作:替換 minimap 繪製區塊內的 Line BF 指令。
"""

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from patch_bas import BasFile  # noqa: E402

SRC = Path(__file__).parent.parent / "AK_CHT_src" / "AK_CHT.bas"
MARKER = b"' AK_UI_MINIMAP_PATCH v1"

# 戶外 minimap player marker — 原:Line (1+2*ite, 1+2*jte)-(2+2*ite, 2+2*jte), 11, BF (2x2)
# 改:4x4 框 + 中央 2x2
OLD_OUTDOOR_MARKER = b"""            If ite = tx And jte = ty Then
                Line (1 + 2 * ite, 1 + 2 * jte)-(2 + 2 * ite, 2 + 2 * jte), 11, BF
            End If"""

NEW_OUTDOOR_MARKER = b"""            If ite = tx And jte = ty Then
                ' AK_UI_MINIMAP_PATCH: yellow ring + cyan center
                Line (0 + 2 * ite, 0 + 2 * jte)-(3 + 2 * ite, 3 + 2 * jte), 14, B
                Line (1 + 2 * ite, 1 + 2 * jte)-(2 + 2 * ite, 2 + 2 * jte), 11, BF
            End If"""

# 地下城 minimap player marker — 原:Line (223+5*idn, 50+5*jdn)-(225+5*idn, 52+5*jdn), 11, BF (3x3)
# 改:5x5 黃框 + 中央 3x3 青心
OLD_DUNGEON_MARKER = b"""            If idn = px And jdn = py Then
                Line (223 + 5 * idn, 50 + 5 * jdn)-(225 + 5 * idn, 52 + 5 * jdn), 11, BF
            End If"""

NEW_DUNGEON_MARKER = b"""            If idn = px And jdn = py Then
                ' AK_UI_MINIMAP_PATCH: yellow ring + cyan center
                Line (222 + 5 * idn, 49 + 5 * jdn)-(226 + 5 * idn, 53 + 5 * jdn), 14, B
                Line (223 + 5 * idn, 50 + 5 * jdn)-(225 + 5 * idn, 52 + 5 * jdn), 11, BF
            End If"""


def main() -> None:
    bas = BasFile.load(SRC)
    if any(MARKER in line for line in bas.lines):
        print("已套過 ui-minimap patch,略過")
        return

    # 把 pattern 內的 LF 轉成 CRLF 對齊 .bas 真實 byte 排列
    global OLD_OUTDOOR_MARKER, NEW_OUTDOOR_MARKER, OLD_DUNGEON_MARKER, NEW_DUNGEON_MARKER
    OLD_OUTDOOR_MARKER = OLD_OUTDOOR_MARKER.replace(b"\n", b"\r\n")
    NEW_OUTDOOR_MARKER = NEW_OUTDOOR_MARKER.replace(b"\n", b"\r\n")
    OLD_DUNGEON_MARKER = OLD_DUNGEON_MARKER.replace(b"\n", b"\r\n")
    NEW_DUNGEON_MARKER = NEW_DUNGEON_MARKER.replace(b"\n", b"\r\n")

    # 用 join+replace 做 multi-line 替換,維持 \r\n
    full = b"\r\n".join(bas.lines)
    n = 0
    if OLD_OUTDOOR_MARKER in full:
        full = full.replace(OLD_OUTDOOR_MARKER, NEW_OUTDOOR_MARKER, 1)
        n += 1
        print("  替換戶外 player marker")
    else:
        print("  WARN: 戶外 player marker pattern 找不到")
    if OLD_DUNGEON_MARKER in full:
        full = full.replace(OLD_DUNGEON_MARKER, NEW_DUNGEON_MARKER, 1)
        n += 1
        print("  替換地下城 player marker")
    else:
        print("  WARN: 地下城 player marker pattern 找不到")

    bas.lines = full.split(b"\r\n")
    bas.insert_before(0, [MARKER])
    bas.save()
    print(f"完成 P2 minimap 視覺增強 ({n} 處)")


if __name__ == "__main__":
    main()
