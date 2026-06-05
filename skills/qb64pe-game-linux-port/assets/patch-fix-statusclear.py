#!/usr/bin/env python3
"""FIX-1:line 1091/1096 status panel Space$(19) → Space$(21) 清完整 layer 2 寬度。

Layer 2 setScrollBlock 範圍 col 60-80,寬 21 cols。原版 Space$(19) 只清 col 60-78,
留下 col 79-80 殘留字元 — 這就是 v0.9 QA 看到「金幣=-8」殘影的成因。

把 19 改成 21 完整清空。
"""

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from patch_bas import BasFile  # noqa: E402

SRC = Path(__file__).parent.parent / "AK_CHT_src" / "AK_CHT.bas"
MARKER = b"' AK_FIX_STATUSCLEAR_PATCH v1"


def main() -> None:
    bas = BasFile.load(SRC)
    if any(MARKER in line for line in bas.lines):
        print("已套過 status clear fix,略過")
        return

    n = 0
    for lineno in (1091, 1096):
        try:
            idx = bas.find_basic_line(lineno)
        except ValueError:
            continue
        old = bas.lines[idx]
        if b"Space$(19)" in old:
            new = old.replace(b"Space$(19)", b"Space$(21)")
            bas.lines[idx] = new
            print(f"  line {lineno}: Space$(19) → Space$(21)")
            n += 1

    bas.insert_before(0, [MARKER])
    bas.save()
    print(f"完成 FIX-1 status clear,改 {n} 處")


if __name__ == "__main__":
    main()
