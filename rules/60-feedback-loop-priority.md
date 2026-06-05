# Feedback Loop Priority

針對棘手 bug、效能 regression、不確定行為的最高優先動作:**先建立一個快速、決定性、agent 可執行的 pass/fail 訊號**。

沒有這個 pass/fail 訊號,瞪程式碼也救不了。

## Hierarchy of loops (try in order)

1. **Failing test** at the relevant seam (unit / integration / e2e)。
2. **Curl / HTTP script** against running dev server。
3. **CLI invocation** with fixture, diff stdout against known-good snapshot。
4. **Headless browser script** (Playwright / Puppeteer)。
5. **Replay captured trace** (network request / payload / event log)。

更多 fallback:throwaway harness / fuzz / bisection / differential / HITL,可依場景擴充。

## Iterate the loop itself

- Faster? (Cache setup, skip init, narrow scope.)
- Sharper signal? (Assert on specific symptom.)
- More deterministic? (Pin time, seed RNG, isolate FS, freeze network.)

2-second deterministic loop > 30-second flaky loop。

## Non-deterministic bugs

目標不是乾淨重現,是**提高重現率**。Loop 100×、並行化、加 stress、注入 sleep,直到 ≥50% repro rate 才好 debug。

## When you cannot build a loop

明確說出來,列出已試的方法。請使用者提供:
- (a) 可重現環境
- (b) 擷取的 artifact (HAR / log dump / core dump / 帶 timestamp 的螢幕錄影)
- (c) 暫時加 production instrumentation 的許可

**不要無 loop 直接 hypothesise。**

## When to trigger

- 遇到「除錯 / 找 bug / 效能變慢 / regression」場景時,此優先順序即適用 —— 先建訊號,再動手。
