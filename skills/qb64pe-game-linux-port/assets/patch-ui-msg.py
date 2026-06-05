#!/usr/bin/env python3
"""P0-2:訊息欄分色 + 重複指令合併(Designer Review §2.2)。

兩個改動:
1. 連續同方向移動只印一次(dedup)
   - 加 Shared akLastDirMsg
   - 加 Sub PrintDirC(msg, dirCode) — 若 dirCode 與上次相同,suppress
   - 改 line 1100/1200/1300/1400(戶外四方向)、1150 forward、1250/1350/1450 turn 改用 PrintDirC
   - 非方向動作(1080/1085/1086/1087/1089)reset akLastDirMsg = 0
2. 訊息分色
   - 方向訊息 → 暗灰 8(透過 PrintDirC 內建)
   - 餓死 (1090_1) → 紅 12
   - 撿金幣 (1170_1) → 綠 10
"""

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from patch_bas import BasFile  # noqa: E402

SRC = Path(__file__).parent.parent / "AK_CHT_src" / "AK_CHT.bas"
MARKER = b"' AK_UI_MSG_PATCH v1"

# 新增 Sub PrintDirC,放在檔尾(其他 Sub 之間)
PRINT_DIR_SUB = b"""
' AK_UI_MSG_PATCH v1: PrintDirC for direction dedup + dark gray
Sub PrintDirC (msg As String, dirCode As Integer)
    If akLastDirMsg = dirCode Then Exit Sub
    akLastDirMsg = dirCode
    Dim oldFc As Integer, oldBc As Integer
    oldFc = currentLayer(1).colorFore
    oldBc = currentLayer(1).colorBack
    SetColor 1, 8, 0
    PrintC 1, msg, -1
    SetColor 1, oldFc, oldBc
End Sub
"""


def main() -> None:
    bas = BasFile.load(SRC)
    if any(MARKER in line for line in bas.lines):
        print("已套過 ui-msg patch,略過")
        return

    # ─ 1. 加 Shared dim akLastDirMsg
    # 找到 Dim Shared isMap 那行,在後面加
    idx_isMap = bas.find_line(b"Dim Shared isMap As Integer")
    bas.insert_after(idx_isMap, [
        b"Dim Shared akLastDirMsg As Integer  ' AK_UI_MSG_PATCH",
    ])

    # ─ 2. 改方向 line:用 PrintDirC 取代 PrintC
    # 1100 (向北), 1200 (向東), 1300 (向西), 1400 (向南)
    # 1150 (前進), 1250 (右轉), 1350 (左轉), 1450 (迴轉)
    # 1155 forward msg 是另一個
    direction_lines = {
        1100: 1100,
        1200: 1200,
        1300: 1300,
        1400: 1400,
        1155: 1155,
        1250: 1250,
        1350: 1350,
        1450: 1450,
    }

    for lineno in direction_lines:
        idx = bas.find_basic_line(lineno)
        old = bas.lines[idx]
        # 找 `PrintC 1, LangRes$("XXXX_1"), -1` 並換 PrintDirC
        key = f'LangRes$("{lineno}_1")'.encode("ascii")
        pat_old = b"PrintC 1, " + key + b", -1"
        pat_new = b"PrintDirC " + key + b", " + str(lineno).encode("ascii")
        if pat_old in old:
            new = old.replace(pat_old, pat_new, 1)
            bas.lines[idx] = new
            print(f"  line {lineno} → PrintDirC")
        else:
            print(f"  line {lineno} 沒找到 PrintC pattern,略過")

    # ─ 3. reset akLastDirMsg 在非方向動作 handler
    # 1080 (A/U/C 動作), 1085 (I/Z/S), 1086/1087 (P), 1089 unknown key
    reset_lines = [1080, 1085, 1086, 1087, 1089]
    for lineno in reset_lines:
        try:
            idx = bas.find_basic_line(lineno)
        except ValueError:
            continue
        old = bas.lines[idx]
        prefix = f"{lineno} ".encode("ascii")
        if old.lstrip(b" \t").startswith(prefix):
            stripped = old.lstrip(b" \t")
            lead = old[:len(old) - len(stripped)]
            # 把 "1080 " 後面 prepend `akLastDirMsg = 0: `
            content = stripped[len(prefix):]
            new = lead + prefix + b"akLastDirMsg = 0: " + content
            bas.lines[idx] = new
            print(f"  line {lineno} prepended akLastDirMsg reset")

    # ─ 4. 餓死 (1090_1) 紅色 + 金幣 (1170_1/1170_2) 綠色
    # 1090: `pw(0) = pw(0) - 1 + Sgn(in) * .9: If pw(0) < 0 Then ... PrintC 1, "", -1: PrintC 1, LangRes$("1090_1"), -1: GoTo 1093`
    idx_1090 = bas.find_basic_line(1090)
    old_1090 = bas.lines[idx_1090]
    if b'LangRes$("1090_1")' in old_1090:
        new_1090 = old_1090.replace(
            b'PrintC 1, LangRes$("1090_1"), -1',
            b'SetColor 1, 12, 0: PrintC 1, LangRes$("1090_1"), -1: SetColor 1, 15, 0',
        )
        bas.lines[idx_1090] = new_1090
        print(f"  line 1090 餓死訊息 → 紅色")

    # 1170: `If dn%(px, py) = 5 Then ... PrintC 1, LangRes$("1170_1"), 0 ... PrintC 1, LangRes$("1170_2"), -1`
    idx_1170 = bas.find_basic_line(1170)
    old_1170 = bas.lines[idx_1170]
    if b'LangRes$("1170_1")' in old_1170:
        new_1170 = old_1170
        new_1170 = new_1170.replace(
            b'PrintC 1, LangRes$("1170_1"), 0',
            b'SetColor 1, 10, 0: PrintC 1, LangRes$("1170_1"), 0',
        )
        new_1170 = new_1170.replace(
            b'PrintC 1, LangRes$("1170_2"), -1',
            b'PrintC 1, LangRes$("1170_2"), -1: SetColor 1, 15, 0',
        )
        bas.lines[idx_1170] = new_1170
        print(f"  line 1170 撿金幣 → 綠色")

    # ─ 5. 在 LangRes Sub 之前插入 PrintDirC Sub
    # 找 Function LangRes$ 並在前面插
    idx_langres = bas.find_line_starting_with(b"Function LangRes$")
    sub_lines = PRINT_DIR_SUB.strip().split(b"\n")
    sub_lines.append(b"")
    bas.insert_before(idx_langres, sub_lines)

    bas.insert_before(0, [MARKER])
    bas.save()
    print("完成 P0-2 訊息分色 + dedup patch")


if __name__ == "__main__":
    main()
