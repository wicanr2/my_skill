#!/usr/bin/env python3
"""P1-2:開場字卡(Designer Review §4.1)。

在 Sub Instructions 開頭(片頭後、Y/N 提示前)插入「世界書頁」字卡:

    ────────  阿 卡 拉 貝  ────────

     在那一個黑暗時代
     巨龍啃食著王國邊緣
     蒙召之人必須走入末日之境
     尋回山中那一塊失落的神物

                  —— 1979

         ⟨任意鍵繼續⟩

按任意鍵後再進入原本的 Y/N 提示。
"""

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from patch_bas import BasFile, encode_big5  # noqa: E402

SRC = Path(__file__).parent.parent / "AK_CHT_src" / "AK_CHT.bas"
MARKER = b"' AK_UI_OPENING_PATCH v1"

CARD_LINES = [
    "",
    "",
    "      阿 卡 拉 貝",
    "",
    "",
    "在那一個黑暗時代",
    "巨龍啃食著王國邊緣",
    "蒙召之人必須走入末日之境",
    "尋回山中那一塊失落的神物",
    "",
    "",
    "                  - 1979",
    "",
    "",
    "          〈任意鍵繼續〉",
]


def main() -> None:
    bas = BasFile.load(SRC)
    if any(MARKER in line for line in bas.lines):
        print("已套過 ui-opening patch,略過")
        return

    # 找 Sub Instructions
    sub_idx = bas.find_line_starting_with(b"Sub Instructions")
    # 插入 BEFORE the Screen 12 setup (line after Sub Instructions ())
    # Sub Instructions ()
    #     Screen 12       ← original line+1
    #     SetScrollBlock ...
    #     Cls: ...
    # We insert between "Sub Instructions ()" and "Screen 12":
    insert_at = sub_idx + 1

    new_lines: list[bytes] = []
    new_lines.append(b"    " + MARKER)
    new_lines.append(b"    Screen 12")
    # 用原作 Instructions 同一個 SetScrollBlock pattern,避開意外的 layer 狀態
    new_lines.append(b"    SetScrollBlock 0, 1, 30, 20, 60: SetColor 0, 14, 0")
    new_lines.append(b"    Cls: LocateC 0, 3, 1")
    # 印出每行
    for i, text in enumerate(CARD_LINES):
        if text == "":
            new_lines.append(b'    PrintC 0, "", -1')
        else:
            # Big5 encode
            big5 = encode_big5(text)
            # 用 14 黃色印 (古卷羊皮味),但 "—— 1979" 用 8 暗灰
            if "1979" in text:
                new_lines.append(b"    SetColor 0, 8, 0")
                new_lines.append(b'    CenterPrintC 0, "' + big5 + b'", -1')
                new_lines.append(b"    SetColor 0, 14, 0")
            elif "任意鍵繼續" in text:
                new_lines.append(b"    SetColor 0, 11, 0")
                new_lines.append(b'    CenterPrintC 0, "' + big5 + b'", -1')
                new_lines.append(b"    SetColor 0, 14, 0")
            else:
                new_lines.append(b'    CenterPrintC 0, "' + big5 + b'", -1')
    new_lines.append(b"    Do: akWait$ = InKey$: Loop Until akWait$ <> \"\"")
    new_lines.append(b"    SetColor 0, 15, 0")

    bas.insert_after(sub_idx, new_lines)
    bas.save()
    print(f"插入開場字卡在 Sub Instructions 之後 (line {sub_idx+1})")


if __name__ == "__main__":
    main()
