# 技術報告(實驗 / 工程量測)的結構與誠實表述

寫「做了一批實驗 / 調校 / 量測,現在要交報告」時套用。與既有三份分工:
`90-plain-language` 管白話怎麼寫、`91-deslop-ai-writing` 管 AI 味怎麼刪、
`86-proposal-writing` 管計畫書(提案、未來要做的事)。**本檔管已經做完的事怎麼交代**,
只放那三份沒有的增量。

## 結構

1. **結論(Conclusions)與建議(Recommendations)拆成兩個段落,不要混在同一句。**
   結論只講「觀察到什麼」,建議才講「所以要做什麼」。混寫時讀者分不清哪句是事實、
   哪句是你的主張。
   - 壞:承重比只有 0.027,所以應該把高度改成 1.084。
   - 好:結論段「承重比 0.027,齒面比孔底高 70~75 mm」;建議段「把 `rack_height` 改成 1.084」。
   > 依據:ANSI/NISO Z39.18 技術報告結構。

2. **假設(Assumptions)獨立列一段,不要藏在方法描述裡。**
   讓讀者不必先拆解你的方法就能直接挑戰前提。這是柵欄原則在文件格式上的對應:
   前提寫在明處,別人才有機會告訴你前提錯了。
   > 依據:同上(Methods, Assumptions, and Procedures 是一個並列的必寫欄位)。

3. **分發範圍寫在報告開頭的 metadata,不要假設讀者自己會判斷。**
   對外交付、含主機位址或內部代號的報告尤其要寫。這與「repo 一律佔位符」是同一件事的
   兩端:一端管內容,一端管流向。

## 證據與不確定性

4. **「機率」與「把握程度」是兩個軸,同一句不要混用。**
   「這件事發生的可能性有多高(likelihood)」與「我對這個判斷本身有多篤定(confidence)」
   要分開陳述,各自可以校準。
   - 壞:應該不太會發生。
   - 好:40 輪統計的發生率是 35%(信賴區間寬,n 太小,對這個數字本身把握不高)。
   > 依據:ICD 203 / Words of Estimative Probability。

5. **參數表每一列標「驗證方法」,不要只分已驗證/未驗證兩態。**
   四種強度不同:**Test 實測**(自己跑過量到)/ **Analysis 推導**(由實測值加公式算出)/
   **Inspection 查核**(讀規格或設定檔確認存在)/ **Demonstration 觀察**(看到行為符合,
   但沒有量化)。混成兩態會讓推導值被當成定案去用。
   > 依據:NASA Systems Engineering Handbook 5.3 Product Verification。

6. **開放項目分三種,而且要配負責方向與消除條件。**
   **TBD** 完全未知,得由對方判斷;**TBC** 有初步值待確認;**TBR** 雙方都定不了、要協商。
   每項都盡量給一個 best estimate 而不是空白,並寫「什麼條件成立就可以結案」。
   沒有消除條件的「待確認」會變成永久掛著的免責聲明。
   > 依據:航太業 TBx 慣例。

## 小樣本與負面結果

7. **樣本小的時候報效應量與信賴區間,不要只寫「無顯著差異」或「測不出效果」。**
   「顯著 / 不顯著」是二分標籤,丟掉了精確度資訊。給區間讓讀者自己判斷。
   同時,**「測不出效果」不等於「沒有效果」** —— 這兩句在報告裡要用不同的寫法,
   而且要附上「要測得出來需要多少樣本」。
   - 好:30% vs 40%,n=10,信賴區間 3~56% 與 19~81% 大幅重疊,分不出差別;
     要偵測「砍半」需每組約 121 輪。

8. **負面結果走完整的方法 → 結果 → 討論,不要省略成一句「未達預期」。**
   結果段只陳述觀察到的事實,因果解讀留給討論段。除錯細節要寫進去 —— 那正是
   後人不用重踩的部分。
   ⚠ 業界有一種建議是「幫負面結果找 positive spin 讓它比較容易被接受」,
   **不採納**(與 `10-lcy-core` 的中性客觀衝突)。只取「結構完整、不省略」這部分。

9. **加一段「有效性威脅」自我審查,四個角度各自具體填。**
   內部效度(是不是真的這個原因造成)/ 外部效度(能不能推廣到其他情境)/
   建構效度(量的東西是不是真的量到你要量的)/ 結論效度(統計或資料分析本身可不可信)。
   ⚠ **每一項都要寫「這條在我們這個場景的威脅是什麼、怎麼緩解」** ——
   寫成套版免責聲明就完全沒有價值,那正是這個慣例最常見的失敗樣態。
   > 依據:Feldt & Magazinius, Validity Threats in Empirical Software Engineering Research。

## 讀者

10. **執行摘要(executive summary)與摘要(abstract)是兩種文類,不要混用。**
    摘要給「決定要不要讀全文」的技術讀者,可以被全文完整涵蓋;
    執行摘要給「可能只讀這一段就做決策」的主管,要自足(背景 + 分析 + 結論),
    **不能假設讀者會回頭讀正文**。
    ⚠ 兩者都不要寫「本報告供 XX 閱讀」這類受眾自述(`90` 準則 6)——
    差別做在**內容自足程度**上,不是做在標籤上。
    > 依據:University of Waterloo ECE, Executive Summaries。

## 何時套用

- 寫實驗報告、調校報告、量測結果報告、故障調查報告、對外技術交付報告。
- 與 `90` / `91` 疊加:90 先把白話寫對、本檔把結構與證據強度定好、91 最後刪 slop。
- 提案性質(要做什麼、要多少資源)走 `86-proposal-writing`,不走本檔。

## Reference

- [ANSI/NISO Z39.18 技術報告結構](https://www.slideshare.net/camiloperez123/z39-18-2005r2010)
- [NASA SE Handbook 5.3 Product Verification](https://www.nasa.gov/reference/5-3-product-verification/)
- [ICD 203 Analytic Standards](https://legalclarity.org/icd-203-analytic-standards-for-all-source-intelligence/)
- [Feldt & Magazinius, Validity Threats in Empirical SE Research](https://www.cse.chalmers.se/~feldt/publications/feldt_2010_validity_threats_in_ese_initial_survey.pdf)
- [UWaterloo ECE, Executive Summaries](https://ece.uwaterloo.ca/~dwharder/Reports/Executive_summaries/)
