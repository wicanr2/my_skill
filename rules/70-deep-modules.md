# Deep Modules

**核心**:模組好壞 = (內部隱藏複雜度) / (對外介面複雜度)。深 > 淺 (Ousterhout, _A Philosophy of Software Design_)。

## Principles

- **Hide complexity behind narrow interfaces.** 對外介面越小越好,內部可以很複雜。
- **Vertical slices, not horizontal layers.** 按功能切,不要按抽象層切。
  - ❌ `controllers/` `services/` `repositories/` 全攤平
  - ✅ `features/order/` `features/invoice/` 每個 feature 內部自己分層
- **Each module owns its language.** 模組對外用 ubiquitous language,內部可以有自己的命名空間。
- **Adapters at the edges only.** 與外部系統交界處才放 adapter / port,不要每層都包一層。

## Smells (refactor signals)

- Shallow class:介面跟實作差不多大 (e.g. `getter`/`setter` 一比一)。
- 同一個 feature 的程式碼分散在 3+ 個目錄裡。
- 改一個行為要動 5+ 個檔案才能編譯通過。
- Public API 暴露的概念,呼叫端要先理解才能用。

## Anti-patterns to refuse

- 為了「未來可能要替換」而提早加抽象層 → YAGNI。
- 把 module A 的內部結構搬到 module B 的 import 路徑上 → leaky abstraction。
- 「Pass-through」class 只是把參數轉發到下一層 → 直接拿掉中間人。

## When to apply

- 規劃新 feature → 想清楚介面,而不是先想實作結構。
- code review → 看 public API,問「呼叫端需要知道幾個概念才能用?」
- Refactor → 找 deepening 機會 (合併 shallow class、收斂介面、移除 pass-through)。
- 定期架構檢視:整批掃 deepening 機會 (合併 shallow class、收斂介面、移除 pass-through)。

## Reference

- John Ousterhout, *A Philosophy of Software Design* — deep modules、information hiding、interface design 的原始出處。
