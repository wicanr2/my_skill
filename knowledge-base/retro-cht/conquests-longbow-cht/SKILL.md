---
name: conquests-longbow-cht
description: Conquests of the Longbow(羅賓漢傳奇,1991 Sierra,SCI1 Late 1.000.510)繁中化專案知識庫。SCI1 Late 與 SCI0/SCI1.1 的差異雷(message 資源、icon bar 介面、無 parser)、專案實戰紀錄。觸發:「Conquests of the Longbow / 羅賓漢傳奇 / longbow 中文化 / SCI1 Late SCI 1.000.510」。repo: github.com/wicanr2/conquests_of_longbow_cht。
metadata:
  type: reference
---

# Conquests of the Longbow(羅賓漢傳奇)繁中化 —— SCI1 Late 實戰知識庫

> 狀態:進行中(2026-07-18 開工)。方法論基底見 `retro-avg-taiwanese-localization` + `scummvm-sci-cht-localization`;本檔只記**本專案新增**的知識。

## 遊戲檔案指紋

- 版本:Floppy DOS 1.1(King's Quest Collection 1996 收錄版)。
- 引擎:**SCI1 Late,interpreter 1.000.510**(`SCIDHUV.EXE`)。ScummVM detection id = `longbow`。
- 資源:RESOURCE.MAP(6027B)+ RESOURCE.000-005。**無 RESOURCE.MSG**(非 SCI1.1 分離訊息檔)。
- 有 MT32.DRV(支援 Roland MT-32)。
- 官方他語版:德文版(ADGF_ADDENGLISH);另有俄文 fan 翻譯版(證明 message 資源可替換)。

## SCI1 Late 與範本專案的差異(動手前查清)

| | SCI0(QFG1 EGA/KQ4/LSL2/SQ3) | SCI1(Jones) | SCI1.1(QFG1 VGA) | **SCI1 Late(本作)** |
|---|---|---|---|---|
| 文字資源 | text + script 內嵌 | text? | message(RESOURCE.MSG) | message(內嵌 RESOURCE.000?) |
| 介面 | parser 打字 | icon bar 點選 | icon bar | icon bar(無 parser) |
| pic | 向量 | bitmap? | bitmap | bitmap(VGA 256 色) |
| 已知坑 | kinsoku/GetLongest | detector config language=tw | hi-res 路徑 | 待實測 |

- (待補:message 資源格式在 SCI1 Late 是否與 SCI1.1 相同 → ScummVM `engines/sci/engine/message.cpp` 支援度)
- (待補:本作有無防拷/手冊問答 → 決定要不要 kStrCmp hook / 跳門)

## 專案設定

- 工作目錄:`~/scummvm/conquest_of_longbow/workplace`
- pinned ScummVM commit:`3d408ec3516f7c29314d8ae8fb7916f31c9cd9aa`(沿用 qfg-1)
- 參考範本:qfg-1(SCI 深水區)、jones_in_the_fast_lane(SCI1 純 VGA,最接近)、kq4(標題疊圖)、space_quest3(crawl 補譯)
- **[HARD] configure 不帶 `--disable-mt32emu`**(qfg-1 BUILD.md 是舊例,本專案遵守 ⑤ MT-32 慣例);複用他專案 binary 前 `grep USE_MT32EMU config.h`——jones 的 binary 是 `#undef`,不可用。

## 實戰紀錄(依時間序,新雷往上疊)

### 2026-07-18 開工
- 驗明 SCI 版本:detection_tables.h 的 floppy entry(resource.map 6027B)與手邊 zip 逐檔 size 相符 → SCI1 Late。
- Jones 專案(`jones_in_the_fast_lane`)是 SCI1 純 VGA 範本,patches 0001-0005 含 SCI1 detector/config/hi-res/kFormat/button overlay,可大量複用。

(後續:抽字結果、翻譯、引擎 patch、打包...)
