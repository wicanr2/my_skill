# 背景 agent 與容器存活性(Liveness)

編排背景 sub-agent 與 docker 時,**主動監控存活性、主動處理卡死/殭屍狀態**。不可讓 agent 或容器空跑數小時。源自實戰:一個背景 sentinel 迴圈空轉 **16 小時**、headless app 無 frame 限制 20 個 process 各 70% CPU 卡 2-3 小時、ephemeral 容器 `--rm` 卻 Up 32 小時。

## 禁止模式(踩過的雷,絕不再犯)
1. **背景 sentinel / 輪詢迴圈**:`until [ -f x ]; do sleep N; done`、`&` detach 後輪詢等檔 → 等的檔沒出現就空轉整夜。**一律禁止;所有 docker / 長操作同步前景執行、等回傳再下一步。**
2. **headless app dump 無 frame/時間上限**:dummy SDL 下 `--dump` 不帶 `--frames N` → 進互動無限 poll,~70% CPU 殭屍。**一律帶 frame 限制(`--frames N`)或 `timeout`。**
3. **GUI viewer**(`eog`/`feh`/`xdg-open`/瀏覽器開圖)在 headless/agent 環境 → 開視窗永久阻塞。**只用檔案輸出(dump PNG 後用 Read 看),不開 GUI。**
4. **agent 誤入 plan mode** → 0 tool use 靜默退出。派工 prompt 明寫**「直接執行、不要進 plan mode」**。

## 主動監控(orchestrator 的責任)
- 定期檢查每個背景 agent:**output 檔新鮮度**(`stat -c %Y` 距今秒數)+ **有無活躍真實 process**(該有 docker/build/python 在跑,還是凍結?)。
- 區分「**長操作**」(有活躍 docker/build process)vs「**卡死**」(無 process + output 凍在很小 byte 數)。**小 output + 無 process + 數分鐘不動 = 卡死前兆,立刻介入,不等數小時。**
- SendMessage 回應判活死:`queued for delivery at its next tool round` = 活著(進行中);`resumed from transcript` = 原本 at rest/卡住。

## 處理卡死
- agent 卡住 → SendMessage 喚醒(多為 transient rate limit)或在新分支重派;失控狂跑 → `TaskStop`。
- 孤兒 sentinel process → kill。
- **殭屍 docker 容器**(`--rm`+`timeout` 卻 Up 數小時、ephemeral 任務跑不停)→ `docker kill`;定期清 build cache / dangling images(`docker builder prune` / `image prune`,**不加 `-a`、不碰 volumes** 以免誤刪資料)。
- **共用機器**:只動「本專案」的資源;**其他專案的容器/volume/image 先回報使用者、不擅自 kill**。
- worktree 收尾:合併後移除 agent worktree(root-owned 先 docker `chown -R` 再 `git worktree remove --force`)。

## 派工紀律(每個背景 agent prompt 必含)
- 禁 sentinel 迴圈、要求 docker 同步前景、**有界**(逆不出/做不到就誠實標受阻結束,**不掛起**)、禁 GUI viewer、「直接執行不進 plan mode」、dump 帶 `--frames N`。
- worktree 隔離需 **cwd 在 git repo 內**(session 主目錄可能不是 repo,會導致 worktree 建立失敗)。

## CI / GitHub Action 監控 → 派有界便宜 agent（不要旗艦背景 poll）
等 CI（`gh run watch`）+ 取 artifact + `gh release upload --clobber` + 重建 `dist-all/` 這類「等待 + 搬運」是機械活，**別用旗艦的背景 Bash job 每次 CI 收尾就重新喚醒主迴圈**（每次喚醒燒最貴的 token）。派 **haiku/sonnet** 監控：`gh run watch` 會阻塞到 run 結束（天然有界，再配 `timeout` 上限），它盯完 + 搬完 + 回報「哪些資產更新/時間戳/成敗」，旗艦只看結論。成本面的完整理由見 `rules/45` 機械活清單「CI / GitHub Action 監控」條；本檔管的是它仍須遵 liveness——**有界、禁無界 sentinel、盯到結束或收掉**。

## 何時套用
任何 spawn 背景 sub-agent 或在 agent 流程跑 docker 時(尤其多 agent 編排、逆向/素材抽取、build/test 迴圈)。**開了背景工作就有責任盯到它結束或收掉,不可放生。**
