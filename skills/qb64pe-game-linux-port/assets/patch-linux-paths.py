#!/usr/bin/env python3
"""把 AK_CHT.bas 內所有 ".\\" 改成 "./",讓 Linux 能正確開檔。

原作 Windows-only 寫法:
    Open ".\\AK_CHT.ini" For Input
    Open ".\\" + CHTFileName For Binary

在 Linux 下 ".\\" 不是路徑分隔符,QB64-PE 會把整個字串當檔名,失敗。

執行:
    python3 tools/patch-linux-paths.py
    # in-place 修改 AK_CHT_src/AK_CHT.bas
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from patch_bas import BasFile  # noqa: E402

SRC = Path(__file__).parent.parent / "AK_CHT_src" / "AK_CHT.bas"


CHDIR_MARK = b"' AK_CHT_LINUX_PATCH: chdir to startup CWD"


def main() -> None:
    bas = BasFile.load(SRC)
    changed = 0
    for i, line in enumerate(bas.lines):
        # Open ".\..." 與 ".\" + var 兩種 pattern 都換掉
        new = line.replace(b'".\\', b'"./')
        if new != line:
            print(f"  line {i+1}: {line!r}")
            print(f"        → {new!r}")
            bas.lines[i] = new
            changed += 1

    # 在 _Title 之後插入 ChDir _STARTDIR$,
    # 抵消 QB64-PE 啟動時自動 chdir 到 binary 目錄的行為
    # (這樣 AppRun 設好的 $USER_DATA_HOME 才生效)
    if CHDIR_MARK not in bas.lines:
        title_idx = bas.find_line_starting_with(b"_Title")
        bas.insert_after(title_idx, [
            CHDIR_MARK,
            b"ChDir _STARTDIR$",
        ])
        print(f"  inserted ChDir _STARTDIR$ after line {title_idx+1} (_Title)")
        changed += 1
    else:
        print("  ChDir patch 已存在,跳過")

    bas.save()
    print(f"完成,改了 {changed} 處")


if __name__ == "__main__":
    main()
