---
name: osxcross-macos-cross-build
description: 沒有 Mac，在 Linux（docker）上用 osxcross 交叉編出 macOS universal binary（arm64 + x86_64）並做靜態驗收的 SOP。涵蓋取得工具鏈（預編 image vs 從源碼編）、per-arch 編譯 + lipo、arm64 的 ad-hoc 簽章（沒有會被 Apple Silicon 直接殺掉）、以及在 Linux 上驗得到／驗不到什麼。觸發：「沒有 Mac 要出 macOS 版」「GitHub Actions macos runner 額度用完」「osxcross」「交叉編 macOS」「cross compile mac」「universal binary」「lipo」「x86_64-apple-darwin 工具鏈」「Apple Silicon Killed: 9」「LC_CODE_SIGNATURE」「libxar.so.1 cannot open shared object file」「can't figure out the architecture type」「dyld: Library not loaded」「.app 打包但沒有 Mac」。**主動觸發**：專案要出三平台而 macOS 那條線卡住時。
---

# 沒有 Mac，在 Linux 上編 macOS 版

原理與每個坑的成因寫在 `~/.claude/knowledge-base/workflows/osxcross-macos-cross-build.md`；這份是照著做的順序。

一句話的原理：**clang 本來就能為任何目標產生機器碼，缺的只有 SDK、Mach-O 的連結器與工具（cctools-port），以及一層把旗標包好的 wrapper。** 所以出事的幾乎都在連結與工具鏈那一層，不在編譯。

## 0. 先決條件與界線

- **要 notarization（對外散布過 Gatekeeper）就別走這條**，那一定要 Mac。
- SDK 的授權只允許在 Apple 硬體上使用。自用交叉編是一回事，**散布 SDK 或含 SDK 的 image 是另一回事，不要做**。
- 有 CI 額度就用 CI（原生編還能 `codesign`）。這條路是給「額度用完 / 沒有 Mac / 要在本機快速迭代」。
- **Linux 上執行不了 macOS binary。** 交付時要講明：靜態檢查全過只代表不會因結構問題開不起來，不代表功能正常。

## 1. 工具鏈 image（先試預編的）

```dockerfile
FROM crazymax/osxcross:15.5-debian AS osxcross      # tag 就是 SDK 版本
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends \
      clang lld llvm cmake make patch git curl ca-certificates xz-utils \
      libssl-dev liblzma-dev libxml2-dev zlib1g-dev python3 pkg-config file \
    && rm -rf /var/lib/apt/lists/*
COPY --from=osxcross /osxcross /osxcross
RUN echo /osxcross/lib > /etc/ld.so.conf.d/osxcross.conf && ldconfig   # 少這行 ld64 起不來
ENV PATH="/osxcross/bin:${PATH}"
```

`crazymax/osxcross` 是 scratch image（沒有 shell，直接 `docker run` 會報 `exec: "sh": not found`），就是給 `COPY --from` 用的。SDK tag：`11.3` / `12.3` / `13.1` / `14.5` / `15.5` / `26.1`。

從源碼編（`tpoechtrager/osxcross` + `joseluisq/macosx-sdks` 的 SDK tarball）也可以，但要先編一份 LLVM（libtapi 需要），共用機器上會跟別人搶很久；`JOBS` 一定要設，`build.sh` 預設吃滿所有核心。

## 2. 開工前先問工具鏈自己

```sh
osxcross-conf        # OSXCROSS_TARGET、SDK 路徑、linker 版本
```

**前綴帶 SDK 次版號**：SDK 15.5 → `darwin24.5`。腳本裡讀 `OSXCROSS_TARGET`，不要寫死也不要憑印象。

## 3. 每弧各編一次，最後 lipo

不要用單次雙 `-arch`（很多 `configure` 的版本偵測會爆）。

```sh
t_of() { [ "$1" = arm64 ] && echo "arm64-apple-$OSXCROSS_TARGET" || echo "x86_64-apple-$OSXCROSS_TARGET"; }
h_of() { [ "$1" = arm64 ] && echo "aarch64-apple-$OSXCROSS_TARGET" || echo "x86_64-apple-$OSXCROSS_TARGET"; }

for arch in arm64 x86_64; do
  t=$(t_of $arch)
  env CC=$t-clang CXX=$t-clang++ AR=$t-ar RANLIB=$t-ranlib \
      STRIP=$t-strip NM=$t-nm AS=$t-as LD=$t-ld \
      MACOSX_DEPLOYMENT_TARGET=$MIN \
      CFLAGS="-arch $arch -mmacosx-version-min=$MIN" \
      LDFLAGS="-arch $arch -mmacosx-version-min=$MIN" \
    ./configure --host=$(h_of $arch) --enable-static --disable-shared --prefix=$P-$arch
  make -j"$JOBS" && make install
done
lipo -create out-arm64 out-x86_64 -output out-universal
```

- **`--host` 用 `aarch64-`，工具前綴用 `arm64-`**（`config.sub` 會把前者正規化）。兩個名字都要留著。
- **相依庫全部靜態編、每弧各一份 prefix。** 動態庫在交叉編下幾乎必然踩到「連到編譯機才有的路徑」。
- 環境變數**每個套件都要套一次**；少傳一個就會有一步悄悄用到 host 的工具，產出 ELF，而且常常到連結才爆。
- 自家寫的 `configure`（非 autoconf）多半也接這組變數 —— 先 `grep SAVED_AR configure` 確認，有的話就不必改建置系統。

## 4. 五個會咬人的地方

| 症狀 | 真正的原因 |
|---|---|
| `unable to execute command: No such file or directory` | 前綴寫成 `darwin24`（少了次版號），或 `/osxcross/lib` 沒進 `ldconfig` → `ld64` 起不來報 `libxar.so.1`。clang 把兩者都轉述成同一句 |
| `ar: <某某>.a: No such file or directory` | 你替建置系統補了它自己會補的旗標（例：ScummVM 的 `_ar="$AR cr"`，你再傳 `AR="…-ar cr"` → `ar cr cr -S`，第二個 `cr` 被當成保存檔名）。**動手前先看目標專案怎麼用 `AR`** |
| 相依檢查永遠失敗，指著執行檔自己 | `otool -L` 對 fat binary 會為每個架構印一行檔名標頭。要先 `lipo -thin` 拆單弧再查 |
| `can't figure out the architecture type` | 在對一支 shell 包裝腳本問架構。打包流程常把 `.app/Contents/MacOS/<name>` 換成腳本、真正的執行檔改名 `<name>.bin` |
| 使用者回報 `Killed: 9`（Apple Silicon） | arm64 沒有 `LC_CODE_SIGNATURE`。ld64 連結 arm64 時會自己加 ad-hoc 簽章，但**要驗**；x86_64 沒這限制 |

`c++filt` 與 `objcopy` 在 cctools 裡不存在，別把 `CXXFILT` / `OBJCOPY` 指過去（`c++filt` 用 host 的就好，名稱修飾同為 Itanium ABI）。

## 5. 靜態驗收（收工前必跑）

```sh
T=x86_64-apple-$OSXCROSS_TARGET
$T-lipo -info  BIN                                   # 雙弧
for a in arm64 x86_64; do
  $T-lipo -thin $a BIN -output /tmp/$a
  $T-otool -l /tmp/$a | grep -q LC_CODE_SIGNATURE    # arm64 必須有
  $T-otool -l /tmp/$a | grep minos                   # 最低系統版本
  $T-otool -L /tmp/$a | tail -n +2 | awk '{print $1}' \
    | grep -vE '^(/usr/lib/|/System/Library/)'       # 空的才對
done
strings BIN | grep -x '<這次要補的功能一定會出現的字串>'
```

最後一行常被忽略但很有用：這次重編如果是為了補某個功能，直接在 binary 裡找那個功能必然出現的字串（檔名、資源名、旗標名），新舊兩份比對。它證明「這份 binary 真的含有那段程式碼」，不需要 Mac。

## 6. `.app` 與簽章

bundle 層的 `_CodeSignature` 在 Linux 上做不出來。**乾脆不簽 bundle**，在說明文件寫「首次開啟要右鍵 → 打開」並附重簽指令——「未簽」勝過「壞簽」，壞簽是直接被拒絕，未簽只是多按一次。執行檔本身的 ad-hoc 簽章（第 4 節）才是能不能跑的關鍵。

## 7. 與 CI 版並存

CI 原生版與交叉編版兩份腳本要**逐項對齊 configure 開關，改一邊就改另一邊**，否則兩個平台的產物會悄悄長得不一樣。在兩支腳本的檔頭互相指名對方。

## worked example

`~/scummvm/maniac_mansion_2/workplace/`：`docker/Dockerfile.osxcross`、`day_of_the_tentacle_cht/tools/build-mac-osxcross.sh`（SDL2 / libogg / FLAC / ScummVM / ScummTR 各兩弧 + lipo + 組 `.app`，四道守門）、`tools/verify-mac-binary.sh`（第 5 節）、`tools/build-mac.sh`（CI 原生版對照組）。

實測（14 核機器，另有其他工作佔掉約一半，`JOBS=6`）：預編工具鏈 image 2 分鐘；相依庫六份（SDL2 / libogg / libFLAC 各兩弧）6.5 分鐘；ScummVM 兩弧 10 分鐘；ScummTR 兩弧加打包 1 分鐘。從零跑完約 20 分鐘。
