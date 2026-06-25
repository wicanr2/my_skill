// 分章節分工撰寫計畫書的 Workflow 骨架(實證可行,不會 hang)。
// 用法:複製到 Workflow 工具的 script,改 CHAPTERS、DIR、各 agent prompt。
// 關鍵:各章 parallel 並行、agent 各自 Read/Edit 檔案、只傳精簡回報,不層層傳全文。

export const meta = {
  name: 'plan-by-chapters',
  description: '分章節分工撰寫計畫書(每章一 agent 並行)+ 文案統合 + 教授 review',
  phases: [
    { title: 'Init', detail: '建 plan/ 目錄' },
    { title: 'WriteChapters', detail: '各章 agent 並行寫獨立章節檔' },
    { title: 'Unify', detail: '技術文案統合 + 驗證文獻 + 建 INDEX' },
    { title: 'Review', detail: '教授 review + 文獻可靠度' },
  ],
}

const DIR = '/home/USER/PROJECT'
const P = `${DIR}/plan`
const SRC = `${DIR}/source-draft.md` // 若從既有草稿抽取;從零寫則改成需求描述

// 共同規範:寫進每個撰稿 agent 的 prompt(文獻真實性 / 技術校正 / 中文化 / 文風)
const COMMON = `
- 文獻:每篇 WebSearch+WebFetch 驗證 arxiv id/DOI,不捏造。
- 技術:涉及既有系統欄位/API 對照當前版原始碼,不照抄舊協定。
- 中文化:概念術語首見「中文(英文)」之後中文;通用縮寫首見全名(縮寫);程式碼/API/識別符/arxiv id 保留原文。
- 文風:繁中、中性、結論先行、不浮誇、無後設句;保留 IEEE 行內引用 [n]。
- 章節檔自洽:開頭一個一級標題,可獨立閱讀。`

const CHAPTERS = [
  { file: '00-introduction.md', scope: '前言:摘要+背景+研究問題與可否證假說 H1..Hn+定位' },
  { file: '01-related-work.md', scope: '相關工作:文獻綜述(按主題分組)+ 相對 SOTA 的 delta' },
  { file: '02-proposed-approach.md', scope: '提案方法:架構+設計', fig: true },
  { file: '03-implementation.md', scope: '實作:落地工程細節' },
  { file: '04-discussion.md', scope: '議題討論:競品+評估協議(baseline/指標/消融)+ROI+風險+open problems' },
  { file: '05-schedule.md', scope: '時程:分工+預算+里程碑' },
  { file: '06-conclusion.md', scope: '展望與結論' },
  { file: 'references.md', scope: '參考文獻:IEEE 格式,編號連續' },
  { file: 'terminology.md', scope: '附錄:Appendix: Terminology(術語中文(英文)對照)' },
]

phase('Init')
await agent(`用 bash 執行:mkdir -p ${P}。回報完成。`, { label: 'mkdir', phase: 'Init' })

phase('WriteChapters')
const written = await parallel(CHAPTERS.map((c) => () =>
  agent(`你負責計畫書一章。用 Read 讀 ${SRC}(可分頁),抽取與「${c.scope}」相關內容,重組成獨立章節,用 Write 寫到 ${P}/${c.file}。${c.fig ? '本章以 ![系統架構](../architecture.svg) 引用架構圖。' : ''}\n共同規範:${COMMON}\n回報:本章標題、行數。`,
    { label: c.file, phase: 'WriteChapters' })
))

phase('Unify')
const unify = await agent(`你是技術文案。Read ${P}/ 各章檔:(1) 跨章一致性統合,用 Edit 局部修(勿整檔重寫);(2) WebSearch+WebFetch 逐篇驗證 references.md 文獻 → 寫 ${DIR}/reference-check.md,有誤就 Edit 修;(3) 建 ${P}/INDEX.md 導覽(各章連結+一句摘要+閱讀順序)。回報:統合摘要+文獻通過/異常數。`,
  { label: 'copyeditor', phase: 'Unify' })

phase('Review')
const review = await agent(`你是資深審查教授。Read ${P}/ 各章與 ${DIR}/reference-check.md,以送審標準 review + 抽查關鍵文獻可靠度(WebFetch)。產出 ${DIR}/review-final.md:總評與等第+逐面向評分+must-fix+文獻可靠度結論。回報總評+must-fix。`,
  { label: 'professor', phase: 'Review' })

return { chapters: (written || []).filter(Boolean).length, unify_ok: !!unify, review_ok: !!review }

// ── 可讀性 / 中文化 pass(另一支 workflow):三領域教授定術語「中文(英文)」譯名 →
//    合併統一術語表 → 各章 parallel 依表改寫去夾雜 → 主管寫執行摘要+可懂度總檢。
// ── 卡死續跑:Workflow({scriptPath, resumeFromRunId}) 從快取續,已完成 agent 秒回。
