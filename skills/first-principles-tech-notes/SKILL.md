---
name: first-principles-tech-notes
description: 建立/擴展「第一性原理 + 圖文並茂」的技術知識庫 GitHub repo(每主題一篇 markdown、概念都配手繪 SVG、用研究 sub-agent 查證、專家+學生審查、worklist 一項一項做)。觸發:使用者要「整理某領域筆記成 repo」「把 X 主題寫成第一性原理教學」「擴展某技術文件並配圖」「一項一項做我監看」「ASCII 圖升級 SVG」「每輪 push 後啟動專家/學生審查」,或延續 robot-notes 這類知識庫專案。
---

# 第一性原理技術知識庫工作法

從 robot-notes 專案萃取的可重用工作法。目標:把一個領域整理成**能在 GitHub 上隨時閱讀、每篇都從根本問題推導、圖文並茂**的知識庫。

## 核心原則(每篇都要守)

1. **第一性原理**:每個概念先問「要解決什麼根本問題」「為什麼是這個設計/公式」,再講怎麼用。**不要堆事實或抄結論**。會動到公式的地方(運動學、odometry、CRC、控制、機率…)要把式子「逼出來」,不是先給再解釋符號。範本寫法:從兩條獨立路徑推出結論(如高斯 = 最大熵 ∧ 中央極限定理)。
2. **數學/流程概念一律配 SVG**,不要只用文字/ASCII(使用者明確不接受純文字講數學)。
3. **正確性優先**:涉及版本/API/協定/標準/文獻一律查證官方原始來源,**不確定標「待查證」,絕不臆造**(不發明不存在的 API/plugin 名)。查證凌駕流暢度。
4. **繁體中文、中性技術風格**,術語首次出現當場一句話翻譯;程式碼/識別符保留原文。
5. **誠實標限制**:roadmap vs 現成、官方 vs 社群、瞬移 vs 真物理——分清楚寫明,不要把「可能」寫成「已有」。

## 每輪流程(一項一項做,主迴圈監看)

一次只推進一個主題、開**一個** sub-agent,我(主迴圈)監看、整合、不放生:

1. **研究**:開一個 sub-agent 用 WebSearch/WebFetch 查官方來源,回傳「素材」(不要它直接寫終稿),要求標待查證、列實際查的 URL、不臆造名稱。
2. **第一性原理書寫**:主迴圈自己 Read/Write 文件(從根本問題推導);開頭一段「一句話定位 + 延伸閱讀連結」。
3. **配 SVG**:見下節。
4. **接索引**:更新 `README.md`(索引入口)、`PLAN.md`(分輪進度)、`CONTEXT.md`(術語表)。
5. **push**:`git add -A` → 繁中 commit(結尾 Co-Authored-By)→ push。每輪結束就 push。
6. **審查**:開**專家**(技術正確性、有無說過頭/缺邊界)+ **學生**(軟體背景看不看得懂、圖能不能秒懂)兩個 review agent;把意見整理成修訂清單。
7. **套修正**:逐條改,**自己驗證**審查 agent 的指控(它也會出錯——曾把 MIT 授權誤判成 Apache,查 LICENSE 才確認);改完再 push(R*.5)。

## SVG 製作 SOP

- **手繪 SVG**(直接 Write),白底、克制配色(可帶橘色點綴),圓角框,`font-family="'Noto Sans CJK TC','PingFang TC','Microsoft JhengHei',sans-serif"`。
- **曲線**(高斯、sin、拋物線、鋸齒…)用 **awk 算 path 點**再貼進 SVG(`exp`/`sin`;Python 要 docker uv venv,純算點用 awk 即可,不污染系統)。
- **畫完一定 chrome-headless 轉 PNG 自我檢查**(CJK 文字、標籤重疊、溢出):
  ```
  google-chrome --headless --no-sandbox --disable-gpu --screenshot=/tmp/x.png \
    --window-size=W,H --force-device-scale-factor=2 "file://$PWD/img/x.svg"
  ```
  用 Read 看 PNG,有破圖(重疊/截斷/比例誤導)就修再驗。
- 圖放 `img/`,文件引用相對路徑(`docs/<topic>/` 深度 2 → `../../img/`);用 `<p align="center"><img src=... width=... alt=...></p>` 置中。
- **取代 ASCII**:把純文字/ASCII 的關鍵概念圖升級成 SVG(對比型最有效:左壞右好、前後對照、輸入→輸出)。

## 目錄與索引慣例

```
README.md   # 索引入口 + 「從哪開始讀」動線 + 零起點導言
PLAN.md     # 分輪計畫與進度表、每輪收尾流程、審查 backlog
CONTEXT.md  # 術語表(ubiquitous language)
img/        # 所有 SVG
docs/NN-主題/*.md   # 數字前綴維持閱讀順序;每檔一主題
```

## 工程紀律(背景 agent / docker / 環境)

- 背景 sub-agent 要監看存活,不放生;派工 prompt 寫明「直接執行、不要進 plan mode」。
- docker / Python 一律容器內 uv venv,不污染系統(本工作法多數只需 awk + chrome-headless,不太用到 Python)。
- 不開 GUI viewer;一律 dump 檔案再 Read。

## 對應記憶與範本

- 記憶:`robot-notes-first-principles`、`robot-notes-math-needs-diagrams`。
- 範本檔:robot-notes 的 `docs/90-foundations/gaussian-from-first-principles.md`(第一性原理 + 一批數學 SVG 的標竿)。
