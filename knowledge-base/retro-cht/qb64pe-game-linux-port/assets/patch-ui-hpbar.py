#!/usr/bin/env python3
"""P0-3:生命條 + 顏色 ramp + 低血量閃爍(Designer Review §2.3)。

設計
----
原作狀態列只印「生命=NN」純白文字,玩家對 HP 危急沒視覺感。

加入:
1. Shared akMaxHp 追蹤 max HP(char creation 設定,level up 同步)
2. HP 數字本身染色:
   - HP% > 70 → 亮綠 10
   - HP% 30-70 → 亮黃 14
   - HP% < 30 → 亮紅 12 + 每 0.25 秒閃爍
3. HP 數字旁畫 10 格 pixel bar(直接 Line BF,不用字元)

實作
----
- 加 Shared akMaxHp、akHpBarFg、akHpClr 等變數
- 加 GoSub 66000 (DRAW_HP_BAR_COLORED) — 算 % + 染色 + 畫 bar
- line 60050 (char creation 統計骰點) 後加 akMaxHp = c(0)
- line 7070 (level up) 後加 akMaxHp = akMaxHp + 1
- line 1091, 1096 (status panel 重繪) 改用 GoSub 66000 取代直接 PrintC c(0)
"""

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from patch_bas import BasFile  # noqa: E402

SRC = Path(__file__).parent.parent / "AK_CHT_src" / "AK_CHT.bas"
MARKER = b"' AK_UI_HPBAR_PATCH v1"

HP_BAR_BLOCK = r"""
' ===== AK_UI_HPBAR_PATCH v1 =====
66000 Rem === DRAW_HP_BAR_COLORED ===
66010 If akMaxHp <= 0 Then akMaxHp = c(0)
66015 If c(0) > akMaxHp Then akMaxHp = c(0)
66020 akHpPct! = c(0) / akMaxHp
66025 If akHpPct! < 0 Then akHpPct! = 0
66026 If akHpPct! > 1 Then akHpPct! = 1
66030 akHpClr% = 10
66031 If akHpPct! < .7 Then akHpClr% = 14
66032 If akHpPct! < .3 Then akHpClr% = 12
66040 akHpBlink% = 0
66050 If akHpPct! < .3 Then akHpBlink% = (Int(Timer * 4) Mod 2)
66060 If akHpBlink% = 1 Then akHpClr% = 8
66070 SetColor 2, akHpClr%, 0
66080 PrintC 2, LTrim$(Str$(c(0))), 0
66085 SetColor 2, 15, 0
66090 Rem --- pixel bar (10 cells, 6x6 px each) ---
66100 akHpBarX% = 552
66105 akHpBarY% = 420
66110 akHpBarFill% = Int(akHpPct! * 10 + .5)
66115 If akHpBarFill% > 10 Then akHpBarFill% = 10
66120 Line (akHpBarX% - 1, akHpBarY% - 1)-(akHpBarX% + 60, akHpBarY% + 6), 8, B
66130 For akHpBarI% = 0 To 9
66140     akHpBarColor% = 8
66150     If akHpBarI% < akHpBarFill% Then akHpBarColor% = akHpClr%
66160     Line (akHpBarX% + akHpBarI% * 6, akHpBarY%)-(akHpBarX% + akHpBarI% * 6 + 4, akHpBarY% + 4), akHpBarColor%, BF
66170 Next akHpBarI%
66199 Return
"""


def main() -> None:
    bas = BasFile.load(SRC)
    if any(MARKER in line for line in bas.lines):
        print("已套過 ui-hpbar patch,略過")
        return

    # 1. 加 Shared dim akMaxHp
    idx_isMap = bas.find_line(b"Dim Shared isMap As Integer")
    bas.insert_after(idx_isMap, [
        b"Dim Shared akMaxHp As Integer  ' AK_UI_HPBAR_PATCH",
    ])

    # 2. 插入 66000 區段在 60250 之後、Sub 之前
    last_gw_idx = bas.find_basic_line(60250)
    insert_at = last_gw_idx + 1
    while insert_at < len(bas.lines):
        line = bas.lines[insert_at].lstrip(b" \t")
        if line.startswith(b"Sub ") or line.startswith(b"Function "):
            break
        insert_at += 1

    block_lines: list[bytes] = []
    for raw in HP_BAR_BLOCK.strip().splitlines():
        block_lines.append(raw.encode("ascii"))
    block_lines.append(b"")
    bas.insert_before(insert_at, block_lines)
    print(f"插入 HP bar 區塊在 line {insert_at+1}")

    # 3. line 60050 後加 akMaxHp init
    idx_60050 = bas.find_basic_line(60050)
    old = bas.lines[idx_60050]
    # 在 Next x 之後 append: akMaxHp = c(0)
    if b"Next x" in old and b"akMaxHp" not in old:
        new = old.replace(b"Next x", b"Next x: akMaxHp = c(0)", 1)
        bas.lines[idx_60050] = new
        print(f"  line 60050 加 akMaxHp = c(0)")

    # 4. line 7070 (level up) 後加 akMaxHp += 1
    idx_7070 = bas.find_basic_line(7070)
    old = bas.lines[idx_7070]
    # 7070 內含: For x = 0 To 5: c(x) = c(x) + 1: Next: Cls: GoTo 1090
    if b"c(x) = c(x) + 1: Next" in old and b"akMaxHp" not in old:
        new = old.replace(
            b"c(x) = c(x) + 1: Next",
            b"c(x) = c(x) + 1: Next: akMaxHp = akMaxHp + 1",
            1,
        )
        bas.lines[idx_7070] = new
        print(f"  line 7070 加 akMaxHp +1")

    # 5. line 1091 / 1096 改 PrintC c(0) → GoSub 66000
    # Original pattern: `PrintC 2, LTrim$(Str$(c(0))), 0` 出現在這兩行
    # 改成: `GoSub 66000`(用 HP bar 子程式取代直接印數字)
    for lineno in (1091, 1096):
        idx = bas.find_basic_line(lineno)
        old = bas.lines[idx]
        pat = b"PrintC 2, LTrim$(Str$(c(0))), 0"
        if pat in old:
            new = old.replace(pat, b"GoSub 66000", 1)
            bas.lines[idx] = new
            print(f"  line {lineno} 用 GoSub 66000 取代純印 c(0)")

    bas.insert_before(0, [MARKER])
    bas.save()
    print("完成 P0-3 HP bar patch")


if __name__ == "__main__":
    main()
