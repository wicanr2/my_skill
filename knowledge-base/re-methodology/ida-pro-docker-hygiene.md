# IDA Pro Docker 非 root 長期作業清單

> 適用：IDA Pro 9.4、`.i64`、IDC、DOS 反組譯、專案內 `tools/ida.sh`。
> 目的：避免重複用 root 寫出資料庫，或到執行後才發現授權只能給 root 使用。

## 固定的故障形狀

`ida-pro-9.4-ver2` 把 `ida.reg`、`ida-config.json` 與 `idapro.hexlic` 只放在
`/root/.idapro/`。容器改用專案擁有者 UID/GID 後，`idat` 會回報：

```text
Cannot continue without a valid license
```

這不是 `.i64` 損壞，也不是 IDC 沒有執行；是 image 的授權佈署只支援 root。

## 每次開工前必做

1. 先讀專案 `AGENTS.md`、`tools/ida.sh` 與本清單。
2. 確認現有 IDA image；專案有指定 revision 就沿用，不另建重複 image。
3. 在容器寫入前，用唯讀掛載檢查 `.i64`、輸出目錄的 UID/GID。
4. 所有可寫容器明確設定 `-u "$(id -u):$(id -g)"`、`--network none`、
   `--memory`、`--cpus`、`--pids-limit` 與 `--rm`。
5. 先執行 `idat -v` 或最小已知可用 IDC，確認當前 UID 看得到授權；
   不可等到長時間分析後才發現。
6. 執行後立即抽查 `.i64`、匯出檔及目錄擁有權，必須是目前使用者。
7. 對舊 16-bit DOS 資料庫，把 IDC 查詢視為可能污染 DB 的一次性作業：
   每個證據查詢都從唯讀 EXE 在新的 `/tmp/<task>/` 重建 `.i64`，取得
   輸出後不再將該副本當作可重用資料庫。不可對正式 `.i64` 直接跑
   新寫或未驗證的 IDC。

## 玩法忠實度稽核的額外閘門

當目的不是定位單一函式，而是判斷 remake 是否忠實時，另讀
[`retro-remake-gameplay-parity-audit.md`](retro-remake-gameplay-parity-audit.md)，並遵守：

1. 自動分析辨識函式數、非 `sub_` 名稱數、外部符號數只可描述導航面積，不可換算成逆向完成度。
2. 具名函式仍須追 caller、runtime 參數、欄位、RNG、分支、回寫及下游 consumer；名稱不能取代資料流。
3. 外部符號表若曾有 parser 位移或相鄰名稱衝突，必須用內容錨點與 caller 驗證，不把名稱直接升格為事實。
4. Hex-Rays 出現 `JUMPOUT`、未定義變數、異常參數或控制流時，只作導航；結論回到原始指令、stack／register、xref 與 raw table。
5. 每個 IDA 探針必須能回填一列「玩家機制—原版—remake」矩陣；只產出大段反編譯文字而沒有玩家路徑與 Go 消費端，不算進度。
6. 一旦找到核心機制的已證實差異，立即修正活表與公開聲明，不等全部 executable 分析完。

## 既有 root-owned `.i64` 的處理

- 不對儲存庫、`workplace/ida/`、`$HOME` 做遞迴 `chown`。
- 若只需查詢，將原 `.i64` 唯讀掛載，在 `/tmp/<task>/` 以目前 UID/GID
  複製一份，只對使用者擁有的副本執行 IDA。
- 若要修復正式資料庫，只能針對已確認的個別檔案重建或修權，
  並立即再驗證；不得擴大到整個目錄。

## image 修正方式

不用 root runtime 當作長期解法。建立有明確版本與 Dockerfile 的後繼 revision：

1. `FROM` 現有專案 image。
2. 在 build 階段將 IDA runtime 所需的設定與授權複製到 image 內
   已有使用者的 `~/.idapro/`。
3. 目錄與檔案改為該 UID/GID 擁有；授權檔使用 `0600`。
4. runtime 仍由包裝器顯式傳入目前 UID/GID；不依賴 image 預設 root。
5. 用「版本、最小 IDC 產檔、輸出擁有權」三道機械檢查驗收。

授權檔不得複製到專案儲存庫、log、截圖或報告；Dockerfile 只記錄
image 內的搬移步驟，不包含授權內容。

## 失敗診斷順序

1. `Cannot continue without a valid license` → 先查當前 UID 的 `~/.idapro`。
2. IDC exit 1 無輸出 → 查 `#include <idc.idc>` 與參數傳遞。
3. exit 0 但沒有檔案 → 確認腳本有明確 `fopen` 寫檔，並查可寫目錄。
4. `Failed to initialize IDA as library` → 用另一份已知正常 `.i64`做正對照，
   分辨是輸入損壞還是 image／授權問題。
5. 查詢成功一次後，下一支 IDC 才出現 error 4 → 不要在同一副本重試；
   從唯讀 EXE 新建另一個一次性 DB。

## 專案已知實例

`~/cht/大時代的故事` 原使用 `ida-pro-9.4-ver2`，其
`workplace/ida/WAR.EXE.i64` 是 root-owned。長期修正為：

- `tools/ida-user.dockerfile` 定義 `ida-pro-9.4-ver3`。
- `tools/ida.sh` 使用 ver3，並加上非 root 與資源界限。
- 既有 root-owned DB 保持不動；一律使用安全入口：

  ```sh
  tools/ida.sh query tools/ida_xref.idc WAR.EXE.i64 byte_6FE7E
  ```

  `query` 會從同名 `WAR.EXE` 在 `/tmp` 重建一次性 DB，以目前
  UID/GID 執行，把 `.txt` 證據收到 `workplace/ida/user-output/`，再清理
  暫存。`raw ... WAR.EXE.i64` 會失敗即關閉，防止直接寫正式 DB。
