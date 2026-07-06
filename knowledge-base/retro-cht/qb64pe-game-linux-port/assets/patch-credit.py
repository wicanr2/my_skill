#!/usr/bin/env python3
"""版權署名:加 Linux Port 王俊又 + 僅供同好分享。

在 TitleScreen Sub 既有 BY LORD BRITISH 1979 / CHINESE LOCALIZED BY INDIANA CHIOU
署名(y=450)之下,新增 y=465 一行 Linux port 譯者:
    LINUX PORT BY CHUN-YU WANG, 2026 - 僅供同好分享
"""

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from patch_bas import BasFile, encode_big5  # noqa: E402

SRC = Path(__file__).parent.parent / "AK_CHT_src" / "AK_CHT.bas"
MARKER = b"' AK_CREDIT_PATCH v1"


def main() -> None:
    bas = BasFile.load(SRC)
    if any(MARKER in line for line in bas.lines):
        print("已套過 credit patch,略過")
        return

    # 找 TITLE_8 ScaleText line,在後面插入新的 credit line
    target_substr = b'ScaleText 270, 450, LangRes$("TITLE_8")'
    for i, line in enumerate(bas.lines):
        if target_substr in line:
            credit_text = encode_big5("LINUX PORT BY CHUN-YU WANG, 2026  -  僅供同好分享 不得商用")
            new_line = b'    ScaleText 30, 466, "' + credit_text + b'", 8, -1, 1'
            bas.insert_after(i, [new_line])
            print(f"  插入 Linux port credit 在 line {i+2}")
            bas.insert_before(0, [MARKER])
            bas.save()
            print("完成 credit patch")
            return

    print("ERROR: 找不到 TITLE_8 ScaleText line")


if __name__ == "__main__":
    main()
