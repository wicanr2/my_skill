# 未完成項是資料，不是散文：每一條掛一個會自己開口的 verify

> 情境型紀律（按需）。與 [`63-truth-in-code-not-stale-markers`](63-truth-in-code-not-stale-markers.md)
> 同一個主題：63 講「動手前先 grep 確認那條還成不成立」，本檔講**怎麼讓那個
> grep 不必靠人記得**——把它寫進資料，讓機器每次都問。
> 與 [`60-feedback-loop-priority`](60-feedback-loop-priority.md) 互補：60 講
> 「先建可重跑的 pass/fail loop」，本檔是那個 loop 用在「狀態」而不是「行為」上。

## 為什麼

markdown 的 `- [ ]` 清單會長出**過期斷言**：東西做好了，而沒有人回頭改那一條。
症狀不是報錯，是清單上留著一句自信的「還沒接」，然後有人照它去重做一遍、或
拿它當「還剩多少」的依據去回報進度。

它活得久是因為**沒有任何機制會問「這條還成立嗎」**。63 要求動手前先 grep，
但那依賴人記得；記不得的那一次就是它繼續活下去的那一次。

> 2026-09-10 Pool remake：清單上寫著「臭雲術（`22h`）還沒接，派發表六十七格裡
> **只剩這一支**」。實際上派發那一格早就接上，連釘住數量的測試都是綠的；缺的
> 只是盤面上的雲團物件。那條斷言活了好幾輪，每一輪都被當成「還剩什麼」的依據。

## 做法

**未完成項的權威是一份 JSON，markdown 那一節由工具產生。**

```json
{
  "schema": "<專案>-worklist/1",
  "layers": { "feature": "玩家會撞到的", "verification": "接了但沒驗過" },
  "items": [
    {
      "id": "wandering-monsters",
      "layer": "feature",
      "title": "地圖上沒有怪物群",
      "body": "…現況與證據…",
      "blocked_by": "…卡在什麼（可選）…",
      "acceptance": "…怎樣算做完…",
      "verify": {
        "kind": "present",
        "paths": ["cmd/game/encounter.go"],
        "pattern": "還沒有地圖上的怪物群",
        "note": "程式裡的自承還在"
      }
    }
  ]
}
```

**`verify` 跑起來為真＝「這一條仍然未完成」**，為假就是東西做好了而條目沒改。

| kind | 語意 | 綁什麼 |
|---|---|---|
| `present` | pattern 找得到 → 仍未完成 | 程式碼裡的**自承註解**（「remake 還沒有…」） |
| `absent` | pattern 找不到 → 仍未完成 | 東西還沒出現（型別名、函式名） |
| `json_len` | 某份 JSON 的欄位長度 ≤ max → 仍未完成 | 進度型的清單（涵蓋幾張圖、抽樣幾項） |
| `manual` | 一律回「仍未完成」並標出來 | 真的沒有機器訊號的 |

## 四條硬規則

- **[HARD] 不要用 SQLite 或別的二進位格式。** `git diff` 看不出「哪條斷言什麼
  時候被改成什麼」，而那正是要追的東西。JSON 純文字、結構化、任何語言都讀得動。
  資料量到幾百條之前都用不到 SQL；真正缺的從來不是查詢能力。
- **[HARD] 不硬湊 `manual` 的 pattern。** 會誤判的 verify 比沒有 verify 更糟：
  它給人「有在看」的假象。沒有訊號就標 `manual`，並在 `note` 寫明**將來接上時
  該綁什麼**（「改好之後那三行字會消失，到時把這一條改成綁那個」）。
- **[HARD] `manual` 一律回「仍未完成」並在報表上標出來。** 沉默不等於通過。
- **[HARD] verify 的測試要有正反對照。** 只驗「它印出仍未完成」證明不了機制有
  在看——空的檔案、寫錯的路徑、永遠為真的 pattern 都會印出一樣的好消息。測試
  要先確認訊號在時報未完成，**再把訊號拿掉、確認它真的開口**。

## 綁什麼訊號比較穩

由穩到不穩：

1. **數量**（`json_len`）——註解會被順手改掉，項數不會。
2. **型別／函式名**（`absent`）——接上時一定會出現，改名的機率低。
3. **自承註解**（`present`）——最好寫，但改動程式時可能被順手刪掉。刪掉就開口，
   那其實是對的：該回頭看那一條了。
4. **`manual`**——沒得綁時的誠實選項。

## 參考實作（語言中立的最小版）

```python
#!/usr/bin/env python3
"""worklist.py verify|render — 未完成項的權威是 worklist.json。"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "docs/worklist.json").read_text(encoding="utf-8"))

def hit(v):
    expr = re.compile(v["pattern"])
    for target in v["paths"]:
        p = ROOT / target
        files = p.rglob("*") if p.is_dir() else [p]
        for f in files:
            if f.is_file() and f.suffix in {".go", ".py", ".sh", ".md", ".json"}:
                if expr.search(f.read_text(encoding="utf-8", errors="ignore")):
                    return str(f.relative_to(ROOT))
    return None

def still_open(item):
    v = item["verify"]
    if v["kind"] == "manual":
        return True, "要人判"
    if v["kind"] == "json_len":
        field = json.loads((ROOT / v["path"]).read_text(encoding="utf-8"))[v["field"]]
        return len(field) <= v["max"], f'{v["path"]} 的 {v["field"]} 有 {len(field)} 項'
    where = hit(v)
    if v["kind"] == "present":
        return bool(where), f"自承還在 {where}" if where else f'找不到 {v["pattern"]}'
    return not where, f"已經出現在 {where}" if where else "還沒出現"

stale = 0
for item in DATA["items"]:
    open_, why = still_open(item)
    if not open_:
        stale += 1
    print(f'{item["id"]:<28} {"仍未完成" if open_ else "**可能已完成**":<14} {why}')
sys.exit(1 if stale else 0)
```

Go 專案的完整版（含 render、schema 檢查與八條測試）在
`Pool-of-Radiance-cht` 的 `cmd/pool-worklist`。

## 收尾紀律

- markdown 那一節由 `render` 產生，開頭寫明「不要手改」。
- 條目做完就**從 JSON 移走或標完成**，不是在 markdown 打勾——打勾的那一份下次
  就被 render 蓋掉了。
- 每一輪核實抓到的過期斷言記在同一處（日期＋哪一條＋錯在哪），不要散在條目裡。
