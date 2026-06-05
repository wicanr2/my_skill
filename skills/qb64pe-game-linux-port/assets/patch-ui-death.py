#!/usr/bin/env python3
"""P1-3:死亡畫面儀式感(Designer Review §4.2)。

在 line 6000 (死亡入口) 之前先做:
1. 畫面紅閃 2 次
2. 中央用 ScaleText 2x 印「汝之冒險於此終結」(大字標題)
3. 玩家統計(層數 / 金幣 / 食物)
4. 才進入原本的 6000 流程(吾等哀悼...)

實作:加 GoSub 65000 到 line 6000 開頭,新增 65000 區段。
"""

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from patch_bas import BasFile, encode_big5  # noqa: E402

SRC = Path(__file__).parent.parent / "AK_CHT_src" / "AK_CHT.bas"
MARKER = b"' AK_UI_DEATH_PATCH v1"

EPITAPH = encode_big5("汝之冒險於此終結")


def main() -> None:
    bas = BasFile.load(SRC)
    if any(MARKER in line for line in bas.lines):
        print("已套過 ui-death patch,略過")
        return

    # 找到 60250 之後的位置(也就是 AKSAVE 區塊之後),在那插入 death sub
    # 安全起見,找 AK_SAVE_PATCH marker 後最後一個 line number,加 death sub 在後面
    last_gw_idx = bas.find_basic_line(60250)
    # 跳過 save patch 區塊到第一個 Sub
    insert_at = last_gw_idx + 1
    while insert_at < len(bas.lines):
        line = bas.lines[insert_at].lstrip(b" \t")
        if line.startswith(b"Sub ") or line.startswith(b"Function "):
            break
        insert_at += 1

    block: list[bytes] = []
    block.append(MARKER)
    block.append(b"65000 Rem === DEATH_RITUAL ===")
    block.append(b'65010 SetColor 0, 15, 0')
    block.append(b'65020 For akFlash% = 0 To 1: Line (0, 0)-(639, 479), 12, BF: _Delay 0.25: Cls: _Delay 0.15: Next')
    block.append(b'65030 Cls')
    block.append(b'65040 ScaleText 130, 200, "' + EPITAPH + b'", 14, 0, 2')
    block.append(b'65050 _Delay 1.5')
    block.append(b"65099 Return")
    block.append(b"")
    bas.insert_before(insert_at, block)
    print(f"插入 death ritual 區塊在 line {insert_at+1}")

    # 在 line 6000 開頭加 GoSub 65000
    idx_6000 = bas.find_basic_line(6000)
    original = bas.lines[idx_6000]
    if original.startswith(b"6000 "):
        new_line = b"6000 GoSub 65000: " + original[5:]
    else:
        stripped = original.lstrip(b" \t")
        lead = original[:len(original) - len(stripped)]
        new_line = lead + b"6000 GoSub 65000: " + stripped[5:]
    bas.lines[idx_6000] = new_line
    print(f"line 6000 加上 GoSub 65000")

    bas.save()
    print("完成 P1-3 死亡畫面 patch")


if __name__ == "__main__":
    main()
