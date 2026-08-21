---
name: ida-docker-game-reversing
description: Use the local IDA Pro Docker/Compose environment to perform authorized static analysis and disassembly of locally owned or permitted legacy games and their binaries. Trigger for requests involving old-game reverse engineering, PE/ELF/DOS executable inspection, IDA batch analysis, strings/functions/imports review, or exporting analysis artifacts from this workspace.
---

# IDA Docker 老遊戲反組譯

> ⛔ **這份已被 `~/.claude/knowledge-base/retro/ida-pro-9.4.md` 取代（2026-08-01）。**
> 本檔寫的是通用 docker-compose 流程與 IDAPython，**與本機實際環境不符**：
> 本機 image 在 `~/ida_94_official/dist`（`ida-pro-9.4-ver2`），
> 直接 `docker run` 不用 compose；而且 **IDAPython 實測跑不起來，要寫 IDC**。
> 授權與邊界那幾節仍然有效，其餘請以新檔為準。


本 skill 的目標是把本地、合法取得且有權分析的老遊戲放入目前工作區，使用官方 IDA Pro Docker image 進行靜態分析。只做分析、相容性研究、保存檔案格式與互通性研究；不協助破解 DRM、繞過授權、修改付費驗證、植入惡意程式或散布遊戲內容。

## 工作區約定

- `Dockerfile`：以工作區內官方 `ida-pro_94_x64linux.run` 建立 image。
- `docker-compose.yml`：提供 IDA GUI、持久化 `ida-home`、`workspace/` 與 `samples/` 掛載。
- `samples/`：待分析的遊戲檔案，只放使用者有權處理的副本。
- `workspace/`：`.i64`、log、腳本、匯出報告等分析產物。
- `kg_patch/idapro.hexlic`：只有在使用者確認它是本人持有的合法 Hex-Rays license 時才可唯讀掛載；不可修改、重寫或與任何 patch/crack 一起使用。

若 image 尚未存在，先確認官方 installer 存在，再建置：

```bash
test -x ida-pro_94_x64linux.run || chmod +x ida-pro_94_x64linux.run
mkdir -p samples workspace
docker compose build
```

不要把遊戲檔、license、`.i64` 或分析結果提交到公開 repository；先檢查 `.gitignore` 或使用工作區外的私有儲存。

## 輸入檔案準備

先在 host 端保留原始檔，只把副本放入 `samples/`，並記錄雜湊與檔案類型：

```bash
cp --reflink=auto /path/to/game.exe samples/game.exe
sha256sum samples/game.exe | tee workspace/game.sha256
file samples/game.exe | tee workspace/game.file
```

遇到 ISO、ZIP、CAB、安裝程式或多個架構時，先列出內容並只解壓到暫存目錄；不要直接執行未知檔案。先確認真正要交給 IDA 的 PE、ELF、Mach-O 或 DOS binary。

## GUI 啟動

Linux X11：

```bash
xhost +si:localuser:$(id -un)
docker compose run --rm ida
xhost -si:localuser:$(id -un)
```

若不在本機 X11，確認 `DISPLAY`、`XAUTHORITY` 與 XWayland/SSH forwarding；不要為方便而長期使用 `xhost +`。在 IDA License Manager 指定 `/license/idapro.hexlic`，或使用 Compose 已設定的 `IDA_LICENSE`。如 license 不屬於使用者，停止並要求提供合法授權。

開啟遊戲副本：

```bash
docker compose run --rm ida /samples/game.exe
```

在 IDA 內依序檢查：載入器與 processor、segments、imports/exports、entry point、strings、交叉引用、函式圖、可能的資源與檔案格式。保存資料庫到 `workspace/`，例如 `/workspace/game.i64`。

## Batch / headless 分析

先確認輸入路徑與 image 內的 IDA 執行檔：

```bash
docker compose run --rm --entrypoint /bin/sh ida -c \
  'file /samples/game.exe; /opt/ida-9.4/ida --help'
```

基本 batch 分析：

```bash
docker compose run --rm ida -A -B /samples/game.exe
```

若要執行使用者自己的 IDAPython 腳本，腳本放在 `workspace/`，先讀取並檢查腳本，再執行：

```bash
docker compose run --rm ida \
  -A -S/workspace/analyze.py /samples/game.exe
```

需要輸出文字報告時，讓腳本將結果寫到 `/workspace/`，不要寫入 image 內，也不要覆蓋原始 binary。若 GUI 啟動會阻塞，可用 `QT_QPA_PLATFORM=offscreen` 做有限度的啟動測試；完整分析仍應確認 IDA 的載入器與 processor 選擇正確。

## 建議分析順序

1. 保存原始檔雜湊、檔案大小、格式、架構、時間戳與來源說明。
2. 建立初始 `.i64`，確認 entry point、segments、imports、exports 與 compiler/runtime 痕跡。
3. 用 strings、資源、API 交叉引用定位視窗、輸入、音效、存檔、網路與腳本系統。
4. 對重要函式重新命名並加上短註解；每個結論附上 address、檔名與可重現步驟。
5. 用 IDAPython 或 IDA 匯出資料到 `workspace/`，例如函式清單、字串清單、呼叫關係與格式筆記。
6. 以第二份原始副本重開或重新分析，確認結果不是暫存狀態或誤判。

## 安全與授權邊界

- 不使用 `kg_patch` 中的 DLL/SO、註冊機、patch script 或任何修改 IDA/遊戲的檔案。
- 不提供破解序號、偽造 license、繞過 DRM/反作弊/付費驗證或移除保護的步驟。
- 不在 container 內執行老遊戲；只讓 IDA 讀取檔案。需要動態分析時，另建隔離、無網路、可還原的 VM，並先取得明確授權。
- 來路不明的 binary 一律當作不可信輸入；不要把 `/home`、SSH agent、瀏覽器憑證或整個 host filesystem 掛入 container。
- license 只用唯讀掛載，避免在輸出、log、截圖或報告中洩漏其內容。

## 常見問題

- `could not connect to display`：檢查 `DISPLAY`、X11 socket、`.Xauthority`，並重新執行暫時性的 `xhost +si:localuser:$(id -un)`。
- `License not found`：確認 `/license/idapro.hexlic` 存在、`IDA_LICENSE` 路徑正確，且 license 是對應版本/帳戶的官方檔案；不要改檔案內容。
- IDA 把檔案當成錯誤格式：回到 `file`、header、processor 與 loader 選擇，檢查是否其實是封裝檔、壓縮檔、DOS stub 或資料檔。
- 分析結果消失：確認資料庫與腳本輸出寫到 `/workspace`，並且使用 `docker compose run --rm` 時沒有只寫到 container 內部。
- GUI 依賴錯誤：先重新 `docker compose build`；不要把 host 的 `/usr/lib` 或任意二進位檔直接掛入 image。
