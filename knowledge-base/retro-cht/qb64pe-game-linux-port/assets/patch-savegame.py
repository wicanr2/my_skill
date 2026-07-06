#!/usr/bin/env python3
"""M4 patch:外部自動儲存 + 啟動時詢問繼續上次遊戲。

設計
----
Akalabeth 1979 原作沒存讀檔。AK_CHT 的程式碼分兩段:
1. 上半:GW-Basic 行號 spaghetti(line 0-60250),所有遊戲狀態變數(pw, c,
   pn$, dn%, te%, ...)以 module scope 宣告,Sub 不能直接存取。
2. 下半:QB64 Sub 區(DrawChineseChar、PrintC、TitleScreen、LangRes、LoadINIFile)。

→ Save/Load 必須走 GoSub label 形式,不能寫成 Sub。

插入內容
--------
- 行號 61000 區段:`AKSAVE_LOAD` LoadGame 子程式 (從 ./akalabeth.sav 讀)
- 行號 62000 區段:`AKSAVE_SAVE` SaveGame 子程式 (寫到 ./akalabeth.sav)
- 行號 63000 區段:`AKSAVE_CHECK` 啟動時詢問 Y/N

- 在 line 1000 (主操作迴圈頂) 前插入 `GoSub 62000`
- 在 line 7 (GoSub 60000) 後插入 `GoSub 63000`,若選 Y 則 GoSub 61000 + GoTo 1000

存檔欄位
--------
binary:
  magic 'AKAL' (4B)
  version i32 = 1
  ln single (4B)
  in, tx, ty, px, py, dx, dy, pa: integer (16B = 8*2)
  mm, MR: integer (4B)
  pw(0..5): single (24B)
  c(0..5): single (24B)
  xx(0..10), yy(0..10): integer (44B)
  pe(10,3), ld(10,5), cd(10,3), ft(10,5), la(10,3): integer (各 44/66/44/66/44 = 264B)
  dn(10,10): integer (242B)
  te(20,20): integer (882B)
  ml(10,1), mz(10,1): integer (44B)
  pnLen: i16
  pn$: variable
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from patch_bas import BasFile  # noqa: E402

SRC = Path(__file__).parent.parent / "AK_CHT_src" / "AK_CHT.bas"

MARKER = b"' AK_SAVE_PATCH v1"

# 整段 SaveGame / LoadGame / CheckSave GoSub 區塊
# 注意:這是純 ASCII BASIC,Big5 字串字面值直接 inline encode
SAVE_LOAD_BLOCK_HEADER = """
' ===== AK_SAVE_PATCH v1 ===== auto-save / load / continue prompt
' AKSAVE_LOAD (61000): read state from ./akalabeth.sav
' AKSAVE_SAVE (62000): write state to ./akalabeth.sav
' AKSAVE_CHECK (63000): prompt Y/N to continue at startup
"""

SAVE_LOAD_BLOCK = r"""
61000 Rem === AKSAVE_LOAD ===
61010 If _FileExists("./akalabeth.sav") = 0 Then Return
61015 akMagic$ = "    " : akVer& = 0
61020 Open "./akalabeth.sav" For Binary As #99
61030 Get #99, , akMagic$
61031 If akMagic$ <> "AKAL" Then Close #99: Return
61032 Get #99, , akVer&
61033 If akVer& <> 1 Then Close #99: Return
61040 Get #99, , ln
61041 Get #99, , in : Get #99, , tx : Get #99, , ty
61042 Get #99, , px : Get #99, , py : Get #99, , dx : Get #99, , dy
61043 Get #99, , pa : Get #99, , mm : Get #99, , MR
61050 For akI% = 0 To 5: Get #99, , pw(akI%): Next
61051 For akI% = 0 To 5: Get #99, , c(akI%): Next
61060 For akI% = 0 To 10: Get #99, , xx%(akI%): Next
61061 For akI% = 0 To 10: Get #99, , yy%(akI%): Next
61070 For akI% = 0 To 10: For akJ% = 0 To 3: Get #99, , pe%(akI%, akJ%): Next: Next
61071 For akI% = 0 To 10: For akJ% = 0 To 5: Get #99, , ld%(akI%, akJ%): Next: Next
61072 For akI% = 0 To 10: For akJ% = 0 To 3: Get #99, , cd%(akI%, akJ%): Next: Next
61073 For akI% = 0 To 10: For akJ% = 0 To 5: Get #99, , ft%(akI%, akJ%): Next: Next
61074 For akI% = 0 To 10: For akJ% = 0 To 3: Get #99, , la%(akI%, akJ%): Next: Next
61080 For akI% = 0 To 10: For akJ% = 0 To 10: Get #99, , dn%(akI%, akJ%): Next: Next
61081 For akI% = 0 To 20: For akJ% = 0 To 20: Get #99, , te%(akI%, akJ%): Next: Next
61082 For akI% = 0 To 10: For akJ% = 0 To 1: Get #99, , ml%(akI%, akJ%): Next: Next
61083 For akI% = 0 To 10: For akJ% = 0 To 1: Get #99, , mz%(akI%, akJ%): Next: Next
61090 akPnLen& = 0 : Get #99, , akPnLen&
61091 If akPnLen& > 0 And akPnLen& < 64 Then akPnBuf$ = String$(akPnLen&, 32): Get #99, , akPnBuf$: pn$ = akPnBuf$
61099 Close #99
61100 Return

62000 Rem === AKSAVE_SAVE ===
62005 Open "./akalabeth.sav" For Output As #99: Close #99
62010 Open "./akalabeth.sav" For Binary As #99
62020 akMagic$ = "AKAL"
62021 Put #99, , akMagic$
62022 akVer& = 1
62023 Put #99, , akVer&
62030 Put #99, , ln
62031 Put #99, , in : Put #99, , tx : Put #99, , ty
62032 Put #99, , px : Put #99, , py : Put #99, , dx : Put #99, , dy
62033 Put #99, , pa : Put #99, , mm : Put #99, , MR
62040 For akI% = 0 To 5: Put #99, , pw(akI%): Next
62041 For akI% = 0 To 5: Put #99, , c(akI%): Next
62050 For akI% = 0 To 10: Put #99, , xx%(akI%): Next
62051 For akI% = 0 To 10: Put #99, , yy%(akI%): Next
62060 For akI% = 0 To 10: For akJ% = 0 To 3: Put #99, , pe%(akI%, akJ%): Next: Next
62061 For akI% = 0 To 10: For akJ% = 0 To 5: Put #99, , ld%(akI%, akJ%): Next: Next
62062 For akI% = 0 To 10: For akJ% = 0 To 3: Put #99, , cd%(akI%, akJ%): Next: Next
62063 For akI% = 0 To 10: For akJ% = 0 To 5: Put #99, , ft%(akI%, akJ%): Next: Next
62064 For akI% = 0 To 10: For akJ% = 0 To 3: Put #99, , la%(akI%, akJ%): Next: Next
62070 For akI% = 0 To 10: For akJ% = 0 To 10: Put #99, , dn%(akI%, akJ%): Next: Next
62071 For akI% = 0 To 20: For akJ% = 0 To 20: Put #99, , te%(akI%, akJ%): Next: Next
62072 For akI% = 0 To 10: For akJ% = 0 To 1: Put #99, , ml%(akI%, akJ%): Next: Next
62073 For akI% = 0 To 10: For akJ% = 0 To 1: Put #99, , mz%(akI%, akJ%): Next: Next
62080 akPnLen& = Len(pn$)
62081 Put #99, , akPnLen&
62082 If akPnLen& > 0 Then Put #99, , pn$
62099 Close #99
62100 Return

63000 Rem === AKSAVE_CHECK ===
63010 akLoadFlag% = 0
63020 If _FileExists("./akalabeth.sav") = 0 Then Return
63030 Screen 12: Cls: LocateC 0, 10, 1: SetColor 0, 14, 0
63031 CenterPrintC 0, ___AKQ1___, -1
63032 CenterPrintC 0, ___AKQ2___, -1
63040 Do: akQ$ = UCase$(InKey$): Loop Until akQ$ = "Y" Or akQ$ = "N"
63050 If akQ$ = "Y" Then akLoadFlag% = 1
63060 If akQ$ = "N" Then Kill "./akalabeth.sav"
63099 Return

64000 Rem === AKSAVE_RESTORE_SCENE ===
64010 Cls
64020 If in = 0 Then GoSub 100 Else GoSub 200
64099 Return
"""


def main() -> None:
    bas = BasFile.load(SRC)

    if any(MARKER in line for line in bas.lines):
        print("已套過 save patch,略過")
        return

    # ─ 1. 找出最後一個 GW-Basic 行(60250 之後就是 Sub 區)
    # 直接掃 line "60250" 開頭的 index,在它之後 + 在 Sub 之前插入新區塊
    last_gw_idx = bas.find_basic_line(60250)
    # 從 last_gw_idx+1 之後找空行 / Sub 開始
    insert_at = last_gw_idx + 1
    while insert_at < len(bas.lines) and bas.lines[insert_at].strip() == b"":
        insert_at += 1
    # insert_at 現在指向第一個 Sub 行(或檔尾)

    # 把 ___AKQ1___ / ___AKQ2___ 換成 Big5 字串字面值
    q1 = "「偵測到上次存檔,要繼續上次遊戲嗎? (Y/N)」".encode("big5")
    q2 = "(選 N 會刪除存檔重新開始)".encode("big5")

    block_lines: list[bytes] = []
    block_lines.append(MARKER)
    for raw in SAVE_LOAD_BLOCK_HEADER.strip().splitlines():
        block_lines.append(raw.encode("ascii"))
    for raw in SAVE_LOAD_BLOCK.strip().splitlines():
        rb = raw.encode("ascii")
        rb = rb.replace(b"___AKQ1___", b'"' + q1 + b'"')
        rb = rb.replace(b"___AKQ2___", b'"' + q2 + b'"')
        block_lines.append(rb)
    block_lines.append(b"")

    bas.insert_before(insert_at, block_lines)
    print(f"插入 save/load 區塊在 .bas line {insert_at+1}")

    # ─ 2. 在 line 7 (GoSub 60000 = char creation) 之前插入 CheckSave
    # line 7 是整個 char creation 入口(lucky 數字 → 屬性 → 商店),
    # CheckSave 必須在它之前跑,否則人物已建立完才問「繼續」就太晚
    # 用 line 6 (原始無此行) 插在 line 5 (Rem HIMEM) 之後
    idx_5 = bas.find_basic_line(5)
    bas.insert_after(idx_5, [
        b"' AK_SAVE_PATCH: prompt continue + jump to main loop",
        b"6 GoSub 63000",
        b"If akLoadFlag% = 1 Then GoSub 61000: Randomize ln: GoSub 64000: GoTo 1000",
    ])
    print(f"插入 continue prompt 在 .bas line {idx_5+1} (line 5 之後,line 7 之前)")

    # ─ 3. 在 line 1000 之前插入 SaveGame call
    # 用 "在 line 1000 之 *前* " 插入一個無 line-number 的 GoSub 62000
    # 但這樣會破壞 line 1000 的可 GoTo,因為 GoTo 1000 找的是 line number "1000"
    # 比較安全:把 GoSub 62000 接在 line 1000 的內容開頭,line number 不動
    idx_1000 = bas.find_basic_line(1000)
    original = bas.lines[idx_1000]
    # original 開頭應為 "1000 " 或 "1000:"
    # 改成 "1000 GoSub 62000: ..."
    if original.startswith(b"1000 "):
        new_line = b"1000 GoSub 62000: " + original[5:]
    elif original.startswith(b"1000:"):
        new_line = b"1000 GoSub 62000: " + original[5:].lstrip(b":")
    else:
        # 前導空白情況
        stripped = original.lstrip(b" \t")
        lead = original[:len(original) - len(stripped)]
        new_line = lead + b"1000 GoSub 62000: " + stripped[5:]
    bas.lines[idx_1000] = new_line
    print(f"line 1000 加上 GoSub 62000 prefix:{new_line[:80]!r}...")

    bas.save()
    print("完成 M4 SaveGame patch")


if __name__ == "__main__":
    main()
