#!/usr/bin/env python3
"""P0-1B 完整版:商店左右並列重排(Designer Review §3.2)。

設計
----
原版商店 row 5-10 顯示 stat | inventory item, row 17-24 顯示 price | damage | item
(重複品名)。版面 40% 留白。

新版面:擴 block 至 1-78 整寬,把 4 欄整合到 row 5-10 同一行:
    生命   22     ⟨F⟩食物         1/10    --
    力量   23     ⟨R⟩長劍            8    1-10
    敏捷   19     ⟨A⟩斧頭            5    1-5
    耐力   21     ⟨S⟩盾牌            6    1
    智慧   23     ⟨B⟩長弓與箭矢      3    1-4
    金幣   17     ⟨M⟩魔法護身符     15    ?????

並刪除 row 17-24 重複資訊。Row 3 加 header「屬 性 / 商 品 / 價 / 傷」標題列。

實作
----
- 60080 改 SetScrollBlock 1, 78,For 迴圈內加 price + damage
- 60085 (pw 數量更新位置) 不動 (LocateC 5+z, 25-Len 依然 work in wider block)
- 60090/60100/60110/60120 替換為 Rem(no-op,清掉底部冗餘)
- 60130 Return 不動
- 60237 (gold 更新位置) LocateC 0, 10, 16 → 改 LocateC 0, 10, 8 (對應 c(5) value position)
- 60240 (item count 更新位置) LocateC col 不動
"""

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from patch_bas import BasFile, encode_big5  # noqa: E402

SRC = Path(__file__).parent.parent / "AK_CHT_src" / "AK_CHT.bas"
MARKER = b"' AK_SHOP_REDESIGN_PATCH v1"

ATTR = encode_big5("屬 性")
ITEM = encode_big5("商 品")
PRICE = encode_big5("價")
DMG = encode_big5("傷")


def main() -> None:
    bas = BasFile.load(SRC)
    if any(MARKER in line for line in bas.lines):
        print("已套過 shop redesign patch,略過")
        return

    # 先移掉先前 patch-shop-header.py 的 header (避免雙 header)
    # Find marker
    for i, line in enumerate(bas.lines):
        if b"AK_SHOP_HEADER_PATCH" in line:
            bas.lines.pop(i)
            print(f"  拿掉舊 shop-header patch marker")
            break

    # ─ 1. 加 Shared 陣列 + 重寫 60080(用陣列查表避開 QB 單行 If/Else 限制)
    idx_isMap = bas.find_line(b"Dim Shared isMap As Integer")
    bas.insert_after(idx_isMap, [
        b"Dim Shared akShopPrice(5) As String",
        b"Dim Shared akShopDmg(5) As String",
    ])

    idx_60080 = bas.find_basic_line(60080)
    new_60080 = (
        b'60080 Screen 12: View Print: SetScrollBlock 0, 1, 30, 1, 78: Cls: SetColor 0, 15, 0: '
        b'akShopPrice(0) = "1/10": akShopPrice(1) = "8": akShopPrice(2) = "5": '
        b'akShopPrice(3) = "6": akShopPrice(4) = "3": akShopPrice(5) = "15": '
        b'akShopDmg(0) = "--": akShopDmg(1) = "1-10": akShopDmg(2) = "1-5": '
        b'akShopDmg(3) = "1": akShopDmg(4) = "1-4": akShopDmg(5) = "?????": '
        b'LocateC 0, 1, 25: PrintC 0, LangRes$("60080_1"), -1: '
        b'LocateC 0, 3, 5: SetColor 0, 14, 0: '
        b'PrintC 0, "' + ATTR + b'", 0: '
        b'PrintC 0, TabC$(0, 30), 0: PrintC 0, "' + ITEM + b'", 0: '
        b'PrintC 0, TabC$(0, 50), 0: PrintC 0, "' + PRICE + b'", 0: '
        b'PrintC 0, TabC$(0, 62), 0: PrintC 0, "' + DMG + b'", -1: '
        b'SetColor 0, 15, 0: '
        b'For x = 0 To 5: LocateC 0, 5 + x, 5: '
        b'PrintC 0, c$(x), 0: PrintC 0, " ", 0: PrintC 0, Str$(c(x)), 0: '
        b'PrintC 0, TabC$(0, 30), 0: PrintC 0, "0-", 0: PrintC 0, w$(x), 0: '
        b'PrintC 0, TabC$(0, 50), 0: PrintC 0, akShopPrice(x), 0: '
        b'PrintC 0, TabC$(0, 62), 0: PrintC 0, akShopDmg(x), -1: '
        b'Next: LocateC 0, 1, 1'
    )
    bas.lines[idx_60080] = new_60080
    print(f"  line 60080 重寫(寬版面 + header + 陣列查表 prices/damages)")

    # ─ 2. 60090 / 60100 / 60110 / 60120 移除(替換成 Rem)
    for lineno in (60090, 60100, 60110, 60120):
        try:
            idx = bas.find_basic_line(lineno)
        except ValueError:
            continue
        bas.lines[idx] = f"{lineno} Rem [SHOP-REDESIGN] removed (merged into 60080)".encode("ascii")
        print(f"  line {lineno} → Rem (清空)")

    # ─ 3. 60237 gold update position
    # 原: LocateC 0, 10, 16: PrintC 0, Str$(c(5)), 0: PrintC 0, "  ", -1
    # 新 block 1-78,row 10 是 c(5) (金幣)。
    # 在新版面金幣在 col 8 開始("金幣 NN")。LocateC col=8 對應 abs col 8.
    # 為 force-clear 用 Space 後再 print
    idx_60237 = bas.find_basic_line(60237)
    old_60237 = bas.lines[idx_60237]
    if b"LocateC 0, 10, 16" in old_60237:
        new_60237 = old_60237.replace(
            b"LocateC 0, 10, 16: PrintC 0, Str$(c(5)), 0: PrintC 0, \"  \", -1",
            b"LocateC 0, 10, 8: PrintC 0, Space$(8), 0: LocateC 0, 10, 8: PrintC 0, Str$(c(5)), -1",
        )
        bas.lines[idx_60237] = new_60237
        print(f"  line 60237 gold update 位置調整 + 補強清除")

    bas.insert_before(0, [MARKER])
    bas.save()
    print("完成 P0-1B 完整版 shop redesign")


if __name__ == "__main__":
    main()
