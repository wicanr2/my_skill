# msdostest：567 款老遊戲的 DOSBox-X 實測設定

> 做老遊戲逆向／中文化／remake 時，**要跑原版就先查這裡**，不要自己從零調 DOSBox。
> 別人已經調好並實測過的設定，省掉「開不起來到底是設定錯還是素材壞」這一整輪。

## 這是什麼

```
https://github.com/joncampbell123/msdostest
```

DOSBox-X 作者 joncampbell123 維護的 MS-DOS／PC-98 軟體測試庫。
**567 個遊戲目錄**，每個目錄裡：

| 檔案 | 內容 |
|---|---|
| `dosbox.conf` | **實測可跑的設定**（machine、memsize、cputype、cycles、autoexec 掛載與開機指令） |
| `__DOWNLOAD__` | 素材的合法下載網址（多半指向 archive.org 的 Neo Kobe 或 dosgamesarchive 收藏） |
| `__PASS__` | 通過測試的時間戳 ＋ DOSBox-X commit hash |
| `__FAIL_STAGING__`／`__NOTES_STAGING__` | 失敗紀錄與備註（有問題的遊戲才有） |

**repo 本身不含遊戲檔**，只有設定與網址（README 明講）。

**342 個是 PC-98**（目錄名帶 `pc98`），這在別處很難找——
PC-98 遊戲的 DOSBox-X 設定散落各處且大多沒實測。

## 怎麼查

```sh
# 列出全部目錄，找目標遊戲（用日文羅馬字、英文名、開發商名都試一次）
gh api repos/joncampbell123/msdostest/git/trees/HEAD --jq '.tree[].path' > tree.txt
grep -iE 'garyou|hokusho|sangoku' tree.txt

# 取設定
D=<目錄名>
gh api repos/joncampbell123/msdostest/contents/$D/dosbox.conf --jq '.content' | base64 -d
gh api repos/joncampbell123/msdostest/contents/$D/__DOWNLOAD__ --jq '.content' | base64 -d
```

目錄命名慣例：`<遊戲羅馬字名>-<開發商>-<來源收藏>-ia`。
**開發商欄位可以拿來反查公司名**——例如查《臥竜伝》查到
`garyouden-sangoku-seiha-no-kei-hokusho-neo-kobe-pc98-ia`，
直接確認開發商是 **Hokusho（ホクショー）**。

## PC-98 設定的樣板

```ini
[dosbox]
memsize=8
machine=pc98
pc-98 sound bios=true
cascade interrupt ignore in service=true

[cpu]
core=normal
cputype=486
cycles=20000

[autoexec]
imgmount 2 "遊戲.hdi" -t hdd -fs none
boot -l c
```

四個非顯而易見的點：

1. **`machine=pc98` 只有 DOSBox-X 有**，原版 DOSBox 與 DOSBox Staging 都不支援。
   要跑 PC-98 遊戲就是 DOSBox-X，不用再找 Neko Project／np2 了。
2. **`pc-98 sound bios=true`** —— 沒開的話 FM 音源（YM2203／OPN）多半不出聲。
3. **`cascade interrupt ignore in service=true`** —— PC-98 的 8259 串接行為與 PC/AT 不同，
   不開會有中斷相關的當機。
4. **`imgmount` 掛的是 `.hdi` 硬碟映像，開機用 `boot -l c`**。
   手上如果是 `.fdi` 磁片，改成 `imgmount 0 a.fdi b.fdi … -t floppy` ＋ `boot -l a`；
   遊戲若有 `HDINST.EXE` 之類的硬碟安裝程式，裝成 HD 映像會比每次換片省事。

## ⭐ 這份設定對「即時制老遊戲」特別重要

`core=normal` ＋ **固定 `cycles`**（不是 `cycles=auto`）＝ **可重現的執行速度**。

即時制遊戲（不是回合制）沒有這一條就沒有 oracle：同一串按鍵每次跑到的
遊戲內時間點都不同，截圖對不起來、bug 重現不了。
**`cycles=auto` 是預設值，而它正是可重現性的敵人。**

js-dos／各種打包版附的 `dosbox.conf` 幾乎都是 `cycles=auto`——
那是給玩家玩的設定，不是給逆向用的。**別直接沿用打包者的設定。**

## ⭐ headless 容器裡的 DOSBox-X 不會因為 SIGTERM 而結束

**遊戲還在跑的時候送 SIGTERM，DOSBox-X 會彈一個 `xmessage` 確認框**
（"You are currently running a program or game. Are you sure to quit anyway now?"），
然後等一個永遠不會來的答案。腳本裡的 `kill "$PID"; wait "$PID"` 就此掛住，
**容器永遠不退出**——即使 `docker run --rm`、即使擷取腳本的工作早就做完了。

症狀是**看起來完全正常**：`docker ps` 有一排同名容器、CPU 各 0.1%、
輸出檔一張不少。只有數量會慢慢累積（每個約 140 MB）。
查法是 `docker top <容器>`，會看到 `xmessage -buttons Yes:1,No:0 …`。

兩道一起做：

```ini
[dosbox]
quit warning=false          ; 不要跳確認框
```

```sh
kill "$PID" 2>/dev/null || true
for _ in $(seq 1 20); do kill -0 "$PID" 2>/dev/null || break; sleep 0.25; done
kill -9 "$PID" 2>/dev/null || true      # 5 秒還在就直接砍
```

一般化的規則：**在 headless 環境跑任何 GUI 程式，都要先問「它結束前會不會問我問題」**。
會問的話，沒有人在那裡按確定。

## 使用紀律

- **設定要抄進自己專案的 repo 並註明出處與抓取日期**，不要每次上網查。
- `__PASS__` 的時間戳與 commit hash 代表「當時的 DOSBox-X master 可跑」。
  版本差太多時仍可能要調——**設定是起點不是保證**。
- 打包者（js-dos、各種「免安裝版」）附的 `machine=`／`cycles=` 反映的是打包者的選擇，
  **不代表原版需求**。以這個 repo 的設定為準。

## 相關

- `~/.claude/knowledge-base/retro/ida-pro-9.4.md`（反組譯環境）
- `~/.claude/skills/re-retro-cht-rulebook/SKILL.md`（老遊戲中文化／remake 路由）
- `rulebook/64-re-screenshot-oracle.md`（用實機截圖當 oracle 反推資料位置）
