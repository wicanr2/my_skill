# Ubiquitous Language (CONTEXT.md)

每個專案應該維護一份 domain glossary,讓 agent 與人共用同一套術語。
源頭概念來自 Eric Evans 的 DDD,被 `/grill-with-docs` skill 直接用來縮短溝通。

## Rules

- Each repo should have a `CONTEXT.md` at root listing **canonical terms + 1-line definition**.
- 寫程式 / 命名變數 / 寫文件時優先使用 CONTEXT.md 中的詞;遇到不明確或新出現的概念,**先進 CONTEXT.md 再用**。
- 詞條格式:`Term — definition. _Avoid_: forbidden synonyms`。
- 重大設計決策不寫在 CONTEXT.md,寫到 `docs/adr/NNNN-decision.md`。
- 模糊或重疊的詞 → 列在 CONTEXT.md 末尾的「Flagged ambiguities」區段,等待釐清。

## When to apply

- 開新 repo 時:`grill-with-docs` 會主動建立 CONTEXT.md。
- 既有 repo 沒有 CONTEXT.md 時:第一次跨領域對話前,先 sketch 一份草稿問使用者確認。
- 每次新增同義詞、簡稱、技術術語前,先檢查是否需要登錄。

## Why

- Reduces agent verbosity (1 term beats 20 words of paraphrasing).
- 程式碼命名一致 → codebase 更好導航。
- agent 用詞收斂 → thinking token 顯著下降。
- 出現新概念時主動釐清,避免後續返工。

## Reference

- `/grill-with-docs` skill: 對話過程中即時更新 CONTEXT.md 與 ADR。
- `/improve-codebase-architecture` skill 的 `LANGUAGE.md` 章節:架構檢視時的語言審查指引。
