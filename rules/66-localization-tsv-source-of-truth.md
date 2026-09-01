# Localization TSV Source of Truth

所有可翻譯的玩家顯示文字，強制以 UTF-8 TSV 作唯一正式來源。程式碼、JSON、
版面組態、規則資料與素材 manifest 只能保存穩定 key，不得內嵌任何語言的譯文。

## Rules

- 英文原文也必須是 locale TSV；不得把程式碼內英文 literal 當永久 fallback。
- runtime fallback 只能是 catalog 鏈，例如 `zh-Hant → en → key`。
- TSV 必須檢查 key 唯一、欄數、UTF-8、placeholder／控制碼相容、漏譯、孤兒 key
  與字型覆蓋。
- 改譯文、加語言或換 fallback 不得要求修改或重新編譯程式。
- 測試可保存預期文字 fixture；production runtime 與資料生成器不得複製譯文。
- 語意比較、查找、序列化與協定欄位永遠使用穩定 key／原始值，不可使用譯文。

## Gate

提交前搜尋 production source 與 JSON 的玩家顯示 literal。發現可翻譯 literal 即
失敗，先移入 locale TSV，再以穩定 key 取用。
