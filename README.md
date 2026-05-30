# my_skill

個人 Claude Code skill 收藏庫。每個 skill 一個資料夾,內含 `SKILL.md`(YAML frontmatter 定義 `name` / `description` + 工作流說明)。

## Skills

| Skill | 用途 | 觸發時機 |
|-------|------|----------|
| [`github-weekly-radar`](skills/github-weekly-radar/SKILL.md) | 每週彙整 GitHub 近期重要**新**專案 + senior-PM 重要性評估 | 「這週 github 重要新專案」「新 repo 週報」「trending 摘要」 |

### github-weekly-radar 一句話

不要相信 web 榜單。trending / aggregator blog 會把**老牌爆紅**誤當「新建」、星數還常過時或灌水。
本 skill 用 `gh api search/repositories q="created:>DATE" sort:stars` 核實**真實建立日與當下星數**,
剔除非新建者,再用 senior-PM 視角分級(S/A/B/C)、標紅旗、給行動建議。為每週固定執行設計。

核心指令(PowerShell):
```powershell
$since = (Get-Date).AddDays(-30).ToString("yyyy-MM-dd")
$j = gh api -X GET "search/repositories" -f q="created:>$since stars:>2000" `
       -f sort=stars -f order=desc -f per_page=50 | ConvertFrom-Json
$j.items | ForEach-Object {
  "{0,7}  {1}  {2}  {3}" -f $_.stargazers_count,$_.created_at.Substring(0,10),$_.full_name,$_.description
}
```

## 安裝 / 使用

讓 Claude Code 讀得到這些 skill,二選一:

1. **clone 到 skills 目錄**
   ```powershell
   git clone https://github.com/wicanr2/my_skill.git
   # 把 skills/* 複製或 symlink 到 ~/.claude/skills/
   ```
2. **直接在對話中引用**:把需要的 `SKILL.md` 內容貼給 Claude,或放進專案的 `.claude/skills/`。

## 報告產物

`github-weekly-radar` 每次執行都會在 [`reports/`](reports/) 產生一份 standalone HTML 週報
(單檔可雙擊開、每個 repo 附 GitHub 連結、Tier 色塊)。最新一份:
[`reports/github-radar-2026-05-30.html`](reports/github-radar-2026-05-30.html)。

## 結構

```
my_skill/
├── README.md
├── reports/
│   └── github-radar-<date>.html   # 每次執行產生的 HTML 週報
└── skills/
    └── github-weekly-radar/
        └── SKILL.md
```

新增 skill:在 `skills/` 下開一個 kebab-case 資料夾,放一份有 frontmatter 的 `SKILL.md`,
更新上方表格即可。

## 前置需求

- [`gh`](https://cli.github.com/) GitHub CLI,且 `gh auth status` 已登入。
- Windows / PowerShell 環境(skill 內指令以 PowerShell 撰寫;中文使用者目錄下 Bash 可能失敗)。
