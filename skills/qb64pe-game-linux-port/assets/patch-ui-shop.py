#!/usr/bin/env python3
"""P0-1:商店熱鍵 <X> 自動塗亮青(Designer Review §2.1, §3.2)。

簡化版:不重排商店版面(影響太多 LocateC 絕對位置),只改 Sub PrintC,
讓所有 PrintC 印到 `<X>` 模式(X 是 A-Z/a-z)時,把 X 字母用亮青 11 渲染。
這樣 LangRes 內所有「<F>食物」「<R>長劍」「<Q>離開」「<S>狀態 <A>攻擊」
熱鍵字母會自動視覺凸顯,玩家不用提醒就能掃到。

修改點:Sub PrintC 的 English 繪製分支,加 `<X>` lookahead。
"""

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from patch_bas import BasFile  # noqa: E402

SRC = Path(__file__).parent.parent / "AK_CHT_src" / "AK_CHT.bas"
MARKER = b"' AK_UI_SHOP_HOTKEY_PATCH v1"

OLD_ENGLISH_BLOCK = b"""            ' Draw English
            If Asc(chGet) >= 32 And Asc(chGet) <= 126 Then
                Line (px, py)-(px + charWidth, py + charHeight), currentLayer(nowLayer).colorBack, BF
                DrawEnglishChar Asc(chGet), px, py, currentLayer(nowLayer).colorFore, 1
                px = px + charWidth
                col = col + 1
            Else"""

NEW_ENGLISH_BLOCK = b"""            ' Draw English (with <X> hotkey detect: P0-1)
            If Asc(chGet) >= 32 And Asc(chGet) <= 126 Then
                akHkX% = 0
                If Asc(chGet) = 60 And i + 2 <= Len(text) Then
                    akHkN% = Asc(Mid$(text, i + 1, 1))
                    If ((akHkN% >= 65 And akHkN% <= 90) Or (akHkN% >= 97 And akHkN% <= 122)) Then
                        If Mid$(text, i + 2, 1) = ">" Then akHkX% = 1
                    End If
                End If
                If akHkX% = 1 Then
                    Line (px, py)-(px + charWidth, py + charHeight), currentLayer(nowLayer).colorBack, BF
                    DrawEnglishChar 60, px, py, currentLayer(nowLayer).colorFore, 1
                    px = px + charWidth: col = col + 1
                    Line (px, py)-(px + charWidth, py + charHeight), currentLayer(nowLayer).colorBack, BF
                    DrawEnglishChar akHkN%, px, py, 11, 1
                    px = px + charWidth: col = col + 1
                    Line (px, py)-(px + charWidth, py + charHeight), currentLayer(nowLayer).colorBack, BF
                    DrawEnglishChar 62, px, py, currentLayer(nowLayer).colorFore, 1
                    px = px + charWidth: col = col + 1
                    i = i + 2
                Else
                    Line (px, py)-(px + charWidth, py + charHeight), currentLayer(nowLayer).colorBack, BF
                    DrawEnglishChar Asc(chGet), px, py, currentLayer(nowLayer).colorFore, 1
                    px = px + charWidth
                    col = col + 1
                End If
            Else"""


def main() -> None:
    bas = BasFile.load(SRC)
    if any(MARKER in line for line in bas.lines):
        print("已套過 ui-shop hotkey patch,略過")
        return

    # 找完整 English 繪製區塊,跨多行用 join 比對
    full_text = b"\r\n".join(bas.lines)
    if OLD_ENGLISH_BLOCK not in full_text:
        # 試 \n 分隔(內部 storage)
        full_joined = b"\n".join(bas.lines)
        if OLD_ENGLISH_BLOCK not in full_joined:
            print("ERROR: 找不到原 English 繪製區塊,可能 PrintC 結構已改")
            sys.exit(1)
        full_joined = full_joined.replace(OLD_ENGLISH_BLOCK, NEW_ENGLISH_BLOCK, 1)
        # 重組回 lines
        bas.lines = full_joined.split(b"\n")
    else:
        full_text = full_text.replace(OLD_ENGLISH_BLOCK, NEW_ENGLISH_BLOCK, 1)
        bas.lines = full_text.split(b"\r\n")

    bas.insert_before(0, [MARKER])
    bas.save()
    print("完成 P0-1 hotkey 塗亮青 patch")


if __name__ == "__main__":
    main()
