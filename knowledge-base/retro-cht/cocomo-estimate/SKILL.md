---
name: cocomo-estimate
description: 用經典 COCOMO Basic SLOC 模型反推「這個專案用傳統方式要投入多少人力」，然後對照 2026 AI-agent 工具棧的實際投入，產出「三數字並陳」開發成本估算章節。當使用者談到「開發成本估算」「人力評估」「工時統計」「COCOMO」「KLOC」「PM 人月」「AI vs 傳統人力差距」「這專案要做多久」「估個 baseline」「逆向漢化工時估算」「跟 1990s 比快多少倍」「合理人力上界」「2026 工具棧校正」「給 PM 看的 estimate」等情境觸發。也適用於對既有 repo 補做 COCOMO 章節（如 README 末段 ship 紀錄）。**主動觸發**：使用者只說「估一下這專案」「給我算個 baseline」也要套用此 skill。
---

# COCOMO 開發成本估算（含 2026 AI 校正）SOP

把任何 repo 的工程規模換算成「**傳統方式人月**」+「**單人無 AI 人月**」+「**2026 AI-agent 實測**」三個數字並陳，給讀者一個量化參考。**核心立場：不誇大壓縮倍率、清楚揭露 COCOMO 系統性偏差**。

## 觸發場景

- README 結尾「ship 紀錄」想加開發成本章節
- 跟 PM / 老闆解釋「為什麼 AI agent 工具棧加速 N 倍」
- 對比 1990s 軟工教科書數字
- 多人問「這要做多久 / 多少錢」
- 跨專案比較工時尺度

## 核心方法：COCOMO Basic

```
工作量 PM (人月) = a · KLOC^b
工期 TDEV (月)   = c · PM^d
並行人數          = PM / TDEV
```

| 模式 | a | b | c | d | 對應 |
|---|---|---|---|---|---|
| **Organic 有機** | 2.4 | 1.05 | 2.5 | 0.38 | 一般應用、小團隊、熟領域 |
| **Semi-detached 半嵌入** | 3.0 | 1.12 | 2.5 | 0.35 | 中等複雜度、混合熟悉度 |
| **Embedded 嵌入** | 3.6 | 1.20 | 2.5 | 0.32 | 緊約束、高複雜度、新領域、PE 逆向、kernel、嵌入式 |

教科書值（Boehm 1981）。

## 三模式怎麼選（單一專案）

```
這專案是「黑箱反推/PE 二進位 hex patch/自訂格式逆向/kernel/硬即時」嗎？
   YES → Embedded
   NO  ↓
這專案有「跨多個模組/與既有大型系統整合/部分新技術」嗎？
   YES → Semi-detached
   NO  ↓
這專案是「一般 web/CLI/script/已知技術棧」嗎？
   YES → Organic
```

## 多 sub-project 拆解（漢化/翻譯/混合型專案）

**不要**整個專案塞一個模式。漢化專案通常是 3 sub-project 合成：

| Sub-project | 模式 | 理由 |
|---|---|---|
| **Source patches**（C++ widget / font / palette）| Embedded | 緊約束、跨 mod、widget 重排有相依 |
| **翻譯本身**（YAML / .nam 音譯） | Organic | 大量機械重複、低複雜度 |
| **工具 + 文件 + 驗證**（Py / PS / Sh / Markdown）| Semi-detached | 混合熟悉度、跨平台 |

每個 sub-project 算 COCOMO → 加總 PM。

## SLOC 統計規則

### 算入
- `*.py`, `*.ps1`, `*.sh`, `*.bat`, `*.cmd` — 工具/腳本
- `*.cpp`, `*.h`, `*.hpp` — patches / 改寫
- `*.c`, `*.go`, `*.rs`, `*.js`, `*.ts` — 其他原生語言
- 一次性分析腳本（**核心爭議點**）— 主張「**這是真實工時的載體**」必算

### 不算入（不在 PM 內）
- 翻譯 YAML（雖然行數多但屬「翻譯產出」不屬「程式行」）
- Markdown 文件（單獨列出但不代入 COCOMO）
- `*.nam` 名字檔（同上）
- 生成的字型 PNG / 二進位
- vendor / 第三方程式碼

### 統計指令

```bash
# 去空行 + 去純註解行
find <repo> -name "*.py" -o -name "*.ps1" -o -name "*.sh" -o -name "*.cpp" -o -name "*.h" \
  | xargs grep -v -E '^\s*$|^\s*(#|//|/\*|\*)' \
  | wc -l
```

Python 版（更精準的 comment skip）：

```python
import re
from pathlib import Path

EXTS = {".py", ".ps1", ".sh", ".cpp", ".h", ".hpp", ".cmd", ".bat"}
COMMENT = {".py": "#", ".ps1": "#", ".sh": "#", ".cpp": "//", ".h": "//"}

def sloc(path):
    n = 0
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if not s: continue
        c = COMMENT.get(path.suffix, "#")
        if s.startswith(c): continue
        n += 1
    return n

total = 0
for f in Path("repo_root").rglob("*"):
    if f.suffix in EXTS:
        total += sloc(f)
print(f"SLOC: {total}")
```

## 三數字並陳（最後輸出）

**鐵則**：永遠列三個數字，不要只給一個「AI agent X 小時」（看起來像吹牛）。

| 視角 | 人力 | 解釋 |
|---|---|---|
| **COCOMO 教科書（純 SLOC math）** | A 人月 | 1980s-2000s 團隊全生命週期等效；視為「**傳統人力合理上界**」 |
| **資深工程師單幹、無 AI、校正 overhead 後** | B 人月 | 拔掉團隊 overhead 的單人現實落點 |
| **2026 實測（AI agent + 人主導測試）** | C 人月 | wall-clock + 真實 session 紀錄 |

**壓縮倍率**：A/C 跟 B/C 兩個都列。

## 系統性偏差揭露（絕對必寫）

寫 estimate 章節時**必須揭露**以下兩個偏差，否則讀者不信：

### 低估
SLOC 抓不到「**0 行卻最燒時間**」的工作：
- 讀反組譯、反推自訂格式文法
- bug 獵殺、palette 配色
- 逐張點陣圖目視驗證
- 翻譯卡譯名一致性
- 跨 mod widget 重排撞牆 debug

逆向/漢化是典型「**低 SLOC / 每行高心智成本**」。

### 高估
COCOMO 校準自 1980-2000 年代**團隊全生命週期**開發**新應用**：
- 內含大量 team meeting / spec doc / QA cycle / regression test
- 內含 PM 流程 overhead

本案是**單人 + 大量拋棄式腳本**，沒有那層 overhead。

**兩者部分相抵** → 用 COCOMO 數字當「**合理上界**」而非「實際工時」。

## 2026 校正方法

**wall-clock 量法**（最容易引用、最不易吹牛）：
- 從 first commit 到 ship 的 wall-clock days
- 標註人實際投入小時（不含 idle / 睡覺 / 工作其他事）
- 人小時 ÷ 22 工作日 ÷ 8 小時/天 = 人月

**互動 session 量法**（claude code 用戶）：
- 從 transcript 抓 first message 到 last response 的 elapsed time
- 不算 idle (>30 min gap)
- 算 user 真實 reply 數 × 每 reply 平均思考時間

**校正後人力區間**：給範圍不給單點（如 0.25-0.5 人月、不是 0.4）

## 章節 markdown 模板

```markdown
## 開發成本估算（COCOMO SLOC 模型）

用經典 **COCOMO Basic**（`工作量 PM = a · KLOC^b`）反推「這套東西**用傳統方式**要投入多少人力」，再對照 **2026 AI-agent 工具棧**的實際投入。

### 實測 SLOC（本專案實際產出）

| 類別 | 檔數 | 有效碼行 |
|---|---|---|
| <repo sub-project 1> | N | NNN |
| <repo sub-project 2> | N | NNN |
| **程式碼小計** | N | **NNNN** |
| <翻譯資產 / 文件 — 不計入 COCOMO> | N | NNN 行 |

### COCOMO Basic 結果（取程式碼 X.XX KLOC）

| 模式 | 工作量（PM） | 工期 | 並行人數 | 人年 |
|---|---|---|---|---|
| Organic 有機 | A | M mo | P | YY |
| Semi-detached 半嵌入 | A | M mo | P | YY |
| **<採用模式> ★採用★** | **A** | **M mo** | **P** | **YY** |

### 為何這樣計算（方法論註解）

1. **為何選 <模式>**：[說明本專案的工作性質如何符合該模式特徵]
2. **為何 KLOC 取 X 而非只算交付的 Y**：[辯護一次性分析腳本算工時載體]
3. **COCOMO 在此類專案的兩個系統性偏差（必須揭露）**：
   - **低估**：[本專案 0 SLOC 高工時的工作清單]
   - **高估**：[COCOMO 內含的 1980s 團隊 overhead 不存在於本案]
   - 兩者部分相抵 → **X 人月**視為「**傳統人力合理上界**」
4. **★2026 工具棧現實校正（本專案即為實測 spike）★**：
   - **時程**：[wall-clock 區間 + 約 X 週]
   - **人的投入**：[X-Y 小時 ≈ Z 人月]
   - **AI agent**：[做了什麼、用了什麼工具]
   - 相對「單人無 AI」壓縮約 **N×**

### 結論（三個數字並陳）

| 視角 | 人力 |
|---|---|
| COCOMO 教科書（<模式>, X.XX KLOC） | **~A 人月（B 人年）** |
| 資深工程師單幹、無 AI（校正 overhead 後） | **~C-D 人月** |
| **2026 實際（AI agent + 人主導測試）** | **~X 週、~Y-Z 人月** |

> **一句話**：COCOMO 純按行數會喊「將近 K 人年」，但那是「**用 1990s 方式硬幹的等效規模**」；在 2026 AI-agent 工具棧下實際壓到 **M 週 / N 人月以內** —— 差距約 **N×**。
>
> *(SLOC 由 `*.py / *.ps1 / *.sh / *.cpp / *.h` 去空行去純註解行統計；COCOMO 係數採教科書 Basic 值 Organic/Semi/Embedded = a:2.4/3.0/3.6, b:1.05/1.12/1.20。)*
```

## 已知校準案例（迭代參考）

### Case 1: pg-cht（Panzer General 繁中化，2026-05）
- 工作性質：PE 二進位逆向 + RLEi 自訂格式反推 + 數十處 hex patch
- SLOC: 6.18 KLOC（**含 5006 行一次性分析腳本**）
- 模式：**Embedded**（單一）
- 三數字：**32 PM**（教科書）/ 4-9 PM（單人無 AI）/ 0.25-0.5 PM（2026 實測 2 週）
- 壓縮倍率：30-60×

### Case 2: openxcom-cht（OpenXcom 雙作中文化 + 雙作打包，2026-05~06）
- 工作性質：**漢化專案**（翻譯為主、source patches 為輔、tooling 完善）
- SLOC（待 COCOMO agent 實測填入）
- 模式：**3 sub-project 加總**（Embedded + Organic + Semi-detached）
- 三數字：[待 agent 報告]
- 壓縮倍率：[待 agent 報告]

## 給用戶的小提醒

寫完 estimate 章節，請對方**自己讀一遍三數字**：
- 如果 COCOMO 數字大到「不可思議」（如 >100 PM）→ 你的 SLOC 統計可能納入太多 vendor code
- 如果 2026 實測數字小到「沒人會信」（如 <0.1 PM 0.05 人月）→ 你可能漏算 idle/regression/review

**目標：給讀者一個 ballpark，不是給 PM 一個合約報價**。

## 不要做

- ❌ 把翻譯 YAML 算進 SLOC（會虛胖）
- ❌ 只給 2026 實測數字而不列 COCOMO baseline（看起來像吹牛）
- ❌ 不揭露低估/高估偏差（不誠實）
- ❌ 用單點數字而非區間（過度精確）
- ❌ 把 wall-clock 直接當「人月」（沒扣 idle）

## 參考

- **Boehm, B. (1981).** *Software Engineering Economics*. Prentice-Hall — COCOMO 原典
- **Boehm, B. et al. (2000).** *Software Cost Estimation with COCOMO II*. — 進階版（含 cost driver 修正）
- pg-cht README 開發成本章節（本 skill case 1）
- openxcom-cht README 開發成本章節（本 skill case 2）
- 本機文件參考：`feedback_estimate_2026_tools.md`（user 偏好：2026 工具棧 baseline、扣 3 層加速、spike 1hr 優先於空口報數）
