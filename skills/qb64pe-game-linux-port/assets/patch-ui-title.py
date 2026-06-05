#!/usr/bin/env python3
"""P1-1:片頭分色 + 指南針放大(Designer Review §3.1, §3.3.3)。

片頭(TitleScreen Sub):
- TITLE_3 (小心了) + TITLE_4 (愚昧的凡人) → 11 亮青 (警告語)
- TITLE_5 (膽敢擅闖) + TITLE_6 (末日之境) → 12 亮紅 (威脅語)
- TITLE_7 (BY LORD BRITISH 1979) + TITLE_8 (CHINESE LOCALIZED ...) → 8 暗灰 (signature 沉下)

指南針(地下城/戶外右下角的 北/南/東/西 字):放大兩倍 + 亮黃。
注意:指南針是 LangRes "1100_1"=向北、"1200_1"=向東、"1300_1"=向西、"1400_1"=向南 渲染,
不是 ScaleText 出來,先 skip,專注片頭。

執行:python3 tools/patch-ui-title.py
"""

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from patch_bas import BasFile  # noqa: E402

SRC = Path(__file__).parent.parent / "AK_CHT_src" / "AK_CHT.bas"
MARKER = b"' AK_UI_TITLE_PATCH v1"


def main() -> None:
    bas = BasFile.load(SRC)
    if any(MARKER in line for line in bas.lines):
        print("已套過 ui-title patch,略過")
        return

    changed = 0
    # ScaleText x, y, LangRes$("TITLE_N"), <color>, -1, 2|1
    # 改 color 欄位
    color_map = {
        b'LangRes$("TITLE_3")': 11,  # 小心了
        b'LangRes$("TITLE_4")': 11,  # 愚昧的凡人
        b'LangRes$("TITLE_5")': 12,  # 膽敢擅闖
        b'LangRes$("TITLE_6")': 12,  # 末日之境
        b'LangRes$("TITLE_7")': 8,   # BY LORD BRITISH 1979
        b'LangRes$("TITLE_8")': 8,   # CHINESE LOCALIZED ...
    }

    for i, line in enumerate(bas.lines):
        if b"ScaleText" not in line:
            continue
        for key, new_color in color_map.items():
            if key in line:
                # parse: ScaleText X, Y, KEY, OLDCOLOR, -1, N
                # 用簡單字串替換:KEY, OLDCOLOR → KEY, NEWCOLOR
                # 因為 OLDCOLOR 永遠是 6 或 15,直接 split match
                import re
                pattern = re.compile(
                    re.escape(key) + rb",\s*\d+,\s*-1,\s*(\d+)"
                )
                m = pattern.search(line)
                if m:
                    scale = m.group(1)
                    new_text = (
                        key + b", " + str(new_color).encode("ascii")
                        + b", -1, " + scale
                    )
                    new_line = pattern.sub(new_text, line)
                    if new_line != line:
                        print(f"  line {i+1}: TITLE_? color → {new_color}")
                        bas.lines[i] = new_line
                        changed += 1
                break

    if changed:
        bas.insert_before(0, [MARKER])
    bas.save()
    print(f"完成,改了 {changed} 行")


if __name__ == "__main__":
    main()
