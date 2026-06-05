#!/usr/bin/env python3
"""作弊模式 patch:.ini Cheat=true 時,食物不衰退、HP 保持滿。

設計
----
1. .ini 新增 Cheat=false/true (user 拷貝會自動繼承)
2. LoadINIFile Sub 加 Case "Cheat" 解析 → akCheat Integer Shared
3. line 1090 食物衰退:用 If akCheat = 0 包起來,作弊不扣食物也不會餓死
4. GoSub 66000 HP bar 繪製前:if akCheat 則 c(0) = akMaxHp (每次重繪強制滿血)
5. 狀態列 row 28 顯示「[作弊]」黃字提示

實作
----
- patch_bas helper:LoadINIFile 內 `Case "ENGFont"` 後加 `Case "Cheat"`
- line 1090 改寫成條件式
- 66000 起頭加判斷
"""

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from patch_bas import BasFile  # noqa: E402

SRC = Path(__file__).parent.parent / "AK_CHT_src" / "AK_CHT.bas"
INI_SRC = Path(__file__).parent.parent / "AK_CHT_src" / "AK_CHT.ini"
MARKER = b"' AK_CHEAT_PATCH v1"


def main() -> None:
    bas = BasFile.load(SRC)
    if any(MARKER in line for line in bas.lines):
        print("已套過 cheat patch,略過")
        return

    # 1. 加 Shared dim akCheat
    idx_isMap = bas.find_line(b"Dim Shared isMap As Integer")
    bas.insert_after(idx_isMap, [
        b"Dim Shared akCheat As Integer  ' AK_CHEAT_PATCH",
    ])

    # 2. LoadINIFile 加 Case "Cheat"
    # 找 `Case "ENGFont"` 之後的 ENGFileName = sValue,在它之後加 Case "Cheat"
    idx_engfont = bas.find_line(b'Case "ENGFont"')
    # 下一行是 `                ENGFileName = sValue`,在它後面插
    bas.insert_after(idx_engfont + 1, [
        b'            Case "Cheat"',
        b'                If UCase$(sValue) = "TRUE" Then',
        b'                    akCheat = -1',
        b'                Else',
        b'                    akCheat = 0',
        b'                End If',
    ])
    print("加 LoadINIFile Case Cheat")

    # 2.5 起始食物 buffer:line 60050 後加 pw(0) = 100,避免「忘了買食物 = 立刻 gg」
    # (與 Cheat 獨立,即使 Cheat=false 也給,只是讓新手不會秒死)
    idx_60050 = bas.find_basic_line(60050)
    old_60050 = bas.lines[idx_60050]
    if b"akMaxHp = c(0)" in old_60050 and b"pw(0) = 100" not in old_60050:
        new_60050 = old_60050.replace(
            b"akMaxHp = c(0)",
            b"akMaxHp = c(0): pw(0) = 100",
            1,
        )
        bas.lines[idx_60050] = new_60050
        print("  line 60050 加起始食物 pw(0) = 100 buffer")

    # 3. line 1090 食物衰退 wrap
    # 原: `1090 pw(0) = pw(0) - 1 + Sgn(in) * .9: If pw(0) < 0 Then c(0) = 0: PrintC 1, "", -1: SetColor 1, 12, 0: PrintC 1, LangRes$("1090_1"), -1: SetColor 1, 15, 0: GoTo 1093`
    # 改: `1090 If akCheat = 0 Then pw(0) = pw(0) - 1 + Sgn(in) * .9: If pw(0) < 0 Then ... GoTo 1093`
    # 注意:這變成 single-line If,內含 nested If 與 GoTo,可能 BASIC 解析失敗
    # 比較穩:把整段移到新行,然後 line 1090 只放條件跳轉
    idx_1090 = bas.find_basic_line(1090)
    old_1090 = bas.lines[idx_1090]
    if b"pw(0) = pw(0) - 1" in old_1090 and b"akCheat" not in old_1090:
        # 把 1090 後面內容抽出來
        body = old_1090.split(b"1090 ", 1)[1] if b"1090 " in old_1090 else None
        if body is None:
            print("  WARN: 無法解析 line 1090,略過")
        else:
            # 注意:QB BASIC 內 `If X Then GoTo Y: rest` 的 rest 被視為 Then 子句的延續
            # 不能用 `If akCheat <> 0 Then GoTo 1092: body`(body 整段變 Then 子句)
            # 改用 `If akCheat = 0 Then body` —— cheat off 才執行 body(食物 decay)
            #                                 cheat on 整段 Then 不跑,fall through 到 line 1091
            new_1090 = b"1090 If akCheat = 0 Then " + body
            bas.lines[idx_1090] = new_1090
            print(f"  line 1090 加 akCheat=0 守衛(cheat off 才減食物)")

    # 4. GoSub 66000 (HP bar) 加 cheat 強制滿血
    # 找 66000 區段開頭 (66010 If akMaxHp <=...) 之前加 66005
    try:
        idx_66010 = bas.find_basic_line(66010)
        bas.insert_before(idx_66010, [
            b"66005 If akCheat <> 0 And akMaxHp > 0 Then c(0) = akMaxHp",
        ])
        print("  HP bar 加 cheat 強制滿血")
    except ValueError:
        print("  WARN: 找不到 line 66010,P0-3 patch 未套?")

    # 5. 狀態列加「作弊」指示
    # 在 line 1091 開頭加 If akCheat <> 0 Then ... PrintC 2 提示
    # 太複雜,簡化:GoSub 66000 內部加 cheat indicator
    # 找 line 66085 (SetColor 2, 15, 0,在印 HP 數字之後) 後插入 indicator
    try:
        idx_66085 = bas.find_basic_line(66085)
        bas.insert_after(idx_66085, [
            b"66086 If akCheat <> 0 Then SetColor 2, 14, 0: LocateC 2, 28, 1: PrintC 2, " + b'"[CHEAT]"' + b", 0: SetColor 2, 15, 0",
        ])
        print("  狀態列加 [CHEAT] 指示")
    except ValueError:
        pass

    bas.insert_before(0, [MARKER])
    bas.save()
    print("完成 CHEAT 模式 patch")

    # 6. 更新 .ini 加 Cheat=false 預設
    ini = INI_SRC.read_bytes()
    if b"Cheat=" not in ini:
        # 在 ;小地圖顯示 之前加
        addition = (
            b";\xa7@\xb9\xab\xbcg\xa6\xa1 true=\xad\xb0\xaa\xc5/\xb0\xc7\xb0\xeb\xa4\xa3\xb4\xee \xa6\xb3\xa5\xce false=\xa5\xbf\xb1`\xb9\xc1\xb8\xd3\r\n"  # ;作弊模式 true=食物/體力不減 有用 false=正常嘗試
            b"Cheat=false\r\n\r\n"
        )
        new_ini = ini.replace(b";\xa4p\xa6a\xb9\xcf\xc5\xe3\xa5\xdc", addition + b";\xa4p\xa6a\xb9\xcf\xc5\xe3\xa5\xdc", 1)
        if new_ini == ini:
            # fallback:append 在尾
            new_ini = ini + b"\r\n;\xa7@\xb9\xab\xbcg\xa6\xa1\r\nCheat=false\r\n"
        INI_SRC.write_bytes(new_ini)
        print(f"  .ini 加 Cheat=false 預設")


if __name__ == "__main__":
    main()
