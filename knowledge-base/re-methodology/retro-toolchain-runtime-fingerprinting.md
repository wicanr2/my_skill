# 復古遊戲工具鏈與執行期指紋

本頁是方法路由，不保存任何單一遊戲的結論。完整流程與證據矩陣見
[`../../reverse-engineer-retro-game-remake/references/toolchain-and-runtime-fingerprints.md`](../../reverse-engineer-retro-game-remake/references/toolchain-and-runtime-fingerprints.md)。
若已確認 Borland Turbo C++ 16-bit DOS 且遇到 32-bit 算術、huge pointer
或 near-to-far bridge helper，再讀
[`../../reverse-engineer-retro-game-remake/references/borland-turbo-cpp-16-runtime-patterns.md`](../../reverse-engineer-retro-game-remake/references/borland-turbo-cpp-16-runtime-patterns.md)。

把這一步放在大量未知函式逐筆判讀之前：先辨識 compiler 家族、linker／格式、
平台 runtime、middleware、driver、packer 與自製資產工具，再用 IDA 的原始函式
邊界、xref、writer／consumer 與 bytes 分開產品程式和編譯／中介層產物。

若 Watcom 函式出現遠離本體、再跳回早期位址的 distant tail／cold chunk，或 IDA owner
與最近外部符號衝突，必須讀上面的完整 reference：保存兩種歸屬、追 predecessor／successor
及 register provenance。相同 displacement 的自動命中只能列為 candidate，不得直接升格成
玩法欄位或用來批次修正函式邊界。

不可由版權年份、單一字串、LE／NE／PE 格式或相容簽章宣稱精確版本。精確版本、
家族、版本範圍與未知必須分級。專案輸出保存雜湊及位址；共用知識只保存方法與
經驗證樣板，不保存原始二進位、授權檔或專案專屬語意。

Watcom 遠端尾區塊的固定匯出欄位為：主函式入口與所有 chunk、tail 原始位址與
bytes、IDA owner、最近外部符號、所有 predecessor／successor、返回主體的 jump target，
以及 incoming edge 的暫存器定義鏈。工具未恢復的間接邊必須標為未知；不可用線性鄰接
補成控制流。區塊歸屬與欄位語意分開分級：前者閉合後，後者仍須取得
base＋stride＋index＋玩家可見 consumer 才能標為已證實。
