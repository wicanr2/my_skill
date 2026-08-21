---
name: osxcross-macos-cross-build
description: 在 Linux（docker）上用 osxcross 交叉編出 macOS universal binary（arm64 + x86_64）。觸發：「沒有 Mac 要出 macOS 版」「GitHub Actions macos runner 額度用完」「osxcross」「交叉編 macOS」「universal binary / lipo」「x86_64-apple-darwin 工具鏈」「Apple Silicon 執行檔被殺掉 Killed: 9」「LC_CODE_SIGNATURE」「libxar.so.1: cannot open shared object file」「can't figure out the architecture type」，或 autoconf/自家 configure 專案要 cross 到 darwin。
---

# 在 Linux 上編 macOS binary（osxcross）

## 缺的到底是什麼

clang 本來就是交叉編譯器——同一支執行檔能為任何目標產生機器碼，`-target arm64-apple-macos13` 就會產出 arm64 的 Mach-O 目的檔。所以「Linux 編不出 macOS 程式」缺的不是編譯器，是另外三樣：

| 缺的東西 | 為什麼非它不可 |
|---|---|
| **SDK** | 標頭檔（`stdio.h`、`Cocoa/Cocoa.h`）與 framework 的符號清單。沒有它連 `#include` 都過不了 |
| **連結器與 Mach-O 工具** | Linux 的 `ld` 只會做 ELF。要 `ld64`、`lipo`、`ar`、`otool`、`strip` 的 Mach-O 版本——這是 cctools-port |
| **一層 wrapper** | 把 `-target`、`-isysroot`、`-mmacosx-version-min` 這些旗標包好，讓 `./configure` 之類的東西可以當成普通編譯器呼叫 |

osxcross 就是這三樣的組合包。理解這一點之後，後面所有的坑都能推：**編譯階段幾乎不會出事（clang 本來就會），出事的全在連結與工具鏈那一層。**

## 取得工具鏈：兩條路

### A. 用預編好的（快，建議先試）

```dockerfile
FROM crazymax/osxcross:15.5-debian AS osxcross
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends \
      clang lld llvm cmake make patch git curl ca-certificates xz-utils \
      libssl-dev liblzma-dev libxml2-dev zlib1g-dev python3 pkg-config file \
    && rm -rf /var/lib/apt/lists/*
COPY --from=osxcross /osxcross /osxcross
# [雷 1] 見下
RUN echo /osxcross/lib > /etc/ld.so.conf.d/osxcross.conf && ldconfig
ENV PATH="/osxcross/bin:${PATH}"
```

`crazymax/osxcross` 是 scratch image，沒有 shell，設計就是給 `COPY --from` 用；直接 `docker run` 它會報 `exec: "sh": executable file not found`。SDK 版本就是 tag（`11.3` / `12.3` / `13.1` / `14.5` / `15.5` / `26.1`，各有 `-debian` / `-ubuntu` / `-alpine` 變體）。

### B. 從源碼編（可重現，但慢）

```dockerfile
RUN git clone https://github.com/tpoechtrager/osxcross.git /opt/osxcross
RUN curl -fsSL -o /opt/osxcross/tarballs/MacOSX15.5.sdk.tar.xz \
      "https://github.com/joseluisq/macosx-sdks/releases/download/15.5/MacOSX15.5.sdk.tar.xz"
RUN cd /opt/osxcross && UNATTENDED=1 SDK_VERSION=15.5 JOBS=6 ./build.sh
```

**要先編一份 LLVM**——`libtapi`（處理 SDK 裡的 `.tbd` 符號存根）是從 Apple 的 tapi 原始碼建的，那份原始碼內嵌整棵 LLVM+clang。在共用機器上這一段會跟別人搶 CPU 搶很久。`JOBS` 一定要設，`build.sh` 預設吃滿所有核心。

**SDK 從哪來**：Apple 官方要 developer.apple.com 帳號下載 Xcode 或 Command Line Tools 才拆得出來。公開鏡像有 [`joseluisq/macosx-sdks`](https://github.com/joseluisq/macosx-sdks)（檔名已經是 osxcross 要的 `MacOSX<ver>.sdk.tar.xz`）與 `alexey-lysiuk/macos-sdk`。**SDK 的授權只允許在 Apple 硬體上使用**——自用交叉編譯是一回事，把 SDK 或含 SDK 的 image 散布出去是另一回事，後者不要做。

## 工具鏈的長相

```
/osxcross/bin/
  arm64-apple-darwin24.5-clang++   aarch64-apple-darwin24.5-clang++
  x86_64-apple-darwin24.5-clang++  x86_64-apple-darwin24.5-{ar,ranlib,strip,nm,as,ld,lipo,otool}
  o64-clang++   (= x86_64)         oa64-clang++   (= arm64)
  lipo          osxcross-conf      xcrun
/osxcross/SDK/MacOSX15.5.sdk
```

`osxcross-conf` 會印出 `OSXCROSS_TARGET`（例：`darwin24.5`）、SDK 路徑、`OSXCROSS_LINKER_VERSION`。**動手前先跑它**，不要憑印象猜前綴。

## 七個坑（每一個都踩過，症狀都不像成因）

### 1. 工具前綴帶 SDK 的次版號

SDK 15.5 → `darwin24.5`，不是 `darwin24`。寫錯的話所有 `$(TRIPLE)-ar`、`$(TRIPLE)-ld` 都不存在，而 clang 只會轉述成 `unable to execute command: No such file or directory`——看起來像編譯器壞了。

腳本裡不要寫死，讀 `OSXCROSS_TARGET`。

### 2. `libxar.so.1: cannot open shared object file`

`ld64` 連結的 `libxar` 與 `libtapi` 放在 `/osxcross/lib`，那不在動態載入器的搜尋路徑裡。症狀同樣被 clang 包成 `unable to execute command`。

修法是 image 裡加一行 `ldconfig` 設定（見上面 Dockerfile），不要靠 `LD_LIBRARY_PATH`——那個會在 `configure` 生出來的子 shell 裡掉。

### 3. cctools 沒有 `c++filt`，也沒有 `objcopy`

別把 `CXXFILT` / `OBJCOPY` 指過去。`c++filt` 用 host 的就好：名稱修飾是 Itanium ABI，兩邊產生的字串一樣。

### 4. arm64 一定要有 `LC_CODE_SIGNATURE`

Apple 從 arm64 開始強制簽章：**沒有簽章的 arm64 執行檔在 Apple Silicon 上會被核心直接殺掉（`Killed: 9`）**，而檔案格式完全正常，在 Linux 這端一點異狀都看不到。

好消息是 ld64 連結 arm64 時會自己加 ad-hoc 簽章，不需要 `codesign`。**但要驗**：

```sh
x86_64-apple-darwin24.5-otool -l bin-arm64 | grep -q LC_CODE_SIGNATURE || exit 1
```

x86_64 沒有這個限制，缺簽章是正常的。

bundle 層的 `_CodeSignature/CodeResources` 在 Linux 上做不出來（那是 `codesign` 的工作）。可以接受的做法是**乾脆不簽 bundle**，在說明文件寫上 macOS 首次開啟要「右鍵 → 打開」，並附重簽指令。「未簽」勝過「壞簽」——壞簽是直接被拒絕，未簽只是要多按一次。

### 5. 不要替建置系統補它自己會補的旗標

autoconf 慣例是 `AR` 只放執行檔名，旗標走 `AR_FLAGS`；但不是每個專案都照這個慣例。ScummVM 的 `configure` 是 `_ar="$AR cr"`，你再傳 `AR="…-ar cr"` 就變成 `ar cr cr -S`，`ar` 把第二個 `cr` 當成保存檔名，報出來的是

```
ar: engines/scumm/libscumm.a: No such file or directory
```

——看起來像「檔案沒產生」，其實是參數多了一組。**動手前先看目標專案怎麼用 `AR`**，不要照抄別的專案的寫法。

### 6. `otool -L` 對 fat binary 會多印檔名標頭

檢查「有沒有連到編譯機才有的 dylib」是交叉編最該做的檢查（連到 `/opt`、`/usr/local` 底下的東西，玩家的 Mac 上不存在，一開就 `dyld: Library not loaded`）。但對 universal binary 下 `otool -L`，它會為每個架構印一行

```
/path/to/bin (architecture x86_64):
```

當標頭。把這行當成相依項的話，檢查會**永遠失敗，而且指著執行檔自己**。要先 `lipo -thin` 拆成單弧再查。

### 7. `can't figure out the architecture type`

`lipo` 對著一個 shell script 問架構就會這樣講。很多打包流程會把 `.app/Contents/MacOS/<name>` 換成一支包裝腳本（負責帶 `--config` 之類的參數），真正的執行檔改名成 `<name>.bin`。驗證腳本兩種佈局都要認。

## 建置的形狀

**每個架構各編一次，最後 `lipo` 合起來。** 不要想用單次雙 `-arch` ——很多 `configure` 的版本偵測會在雙架構下爆掉。

```sh
for arch in arm64 x86_64; do
  t=$( [ $arch = arm64 ] && echo arm64-apple-$OSXCROSS_TARGET || echo x86_64-apple-$OSXCROSS_TARGET )
  env CC=$t-clang CXX=$t-clang++ AR=$t-ar RANLIB=$t-ranlib \
      STRIP=$t-strip NM=$t-nm AS=$t-as LD=$t-ld \
      MACOSX_DEPLOYMENT_TARGET=13.4 \
      CFLAGS="-arch $arch -mmacosx-version-min=13.4" \
      LDFLAGS="-arch $arch -mmacosx-version-min=13.4" \
    ./configure --host=$( [ $arch = arm64 ] && echo aarch64 || echo x86_64 )-apple-$OSXCROSS_TARGET \
      --enable-static --disable-shared --prefix=$PREFIX-$arch
  make -j6 && make install
done
lipo -create out-arm64 out-x86_64 -output out-universal
```

幾個要點：

* **`--host` 要用 `aarch64-`**（`config.sub` 會把 `arm64-apple-darwin24.5` 正規化成 `aarch64-apple-darwin24.5`），但**工具前綴是 `arm64-`**。兩個名字都要留著，別統一。
* **每個相依庫都要靜態編、每個架構各一份 prefix**。動態庫在交叉編下幾乎必然踩坑 6。
* 環境變數要**每個套件都套一次**。少傳一個，某一步就會悄悄用到 host 的工具，產出 ELF 而不是 Mach-O，而且往往要到連結那一步才爆。
* 自家寫的 `configure`（非 autoconf）多半也認 `CC/CXX/AR/RANLIB/STRIP/NM` 這組環境變數——先 grep 它有沒有 `SAVED_AR` 之類的接收點，有的話就不必改建置系統。

## 收工前的靜態驗收

**Linux 上執行不了 macOS binary，所以「編得出來」與「跑得起來」之間有一段只能靠靜態檢查補。** 這五項是實際會讓玩家開不起來的原因：

| 檢查 | 指令 | 沒過的後果 |
|---|---|---|
| 雙弧 | `lipo -info` | 其中一種 Mac 開不了 |
| arm64 有簽章 | `otool -l \| grep LC_CODE_SIGNATURE` | Apple Silicon 上 `Killed: 9` |
| 最低系統版本 | `otool -l \| grep minos` | 比宣稱的高 → 舊 Mac 直接拒絕 |
| 相依只在 `/usr/lib` 與 `/System/Library` | `lipo -thin` 後 `otool -L` | `dyld: Library not loaded` |
| 目標功能的字串在不在 | `strings \| grep <特徵字串>` | 編到舊版原始碼卻沒發現 |

最後一項常被忽略但很有用：如果這次重編的目的是補上某個功能，直接在 binary 裡找那個功能一定會出現的字串（檔名、資源名、旗標名），比對新舊兩份。它證明的是「這份 binary 真的含有那段程式碼」，不需要 Mac。

**做不到的事要講明**：以上全過只代表「不會因為結構問題開不起來」，不代表功能正常。真正的遊玩／執行驗證仍然需要一台 Mac。報告時不要把靜態檢查說成實機驗證。

## 什麼時候該走這條路

| 情境 | 建議 |
|---|---|
| 有 macOS runner 額度、專案已有 CI | 用 CI，原生編最省事，還能 `codesign` |
| CI 額度用完 / 要在本機快速迭代 / 根本沒有 Mac | osxcross |
| 需要 notarization（對外散布、要過 Gatekeeper） | **一定要 Mac**。notarize 要上傳到 Apple 並用 `notarytool`，交叉編這條路做不到 |

CI 與交叉編兩份腳本並存時，**configure 的開關要逐項對齊，改一邊就要改另一邊**——否則兩個平台的產物會悄悄長得不一樣。

## worked example

`~/scummvm/maniac_mansion_2/workplace/`：

* `docker/Dockerfile.osxcross` —— 上面的 A 路線
* `day_of_the_tentacle_cht/tools/build-mac-osxcross.sh` —— SDL2 / libogg / FLAC / ScummVM / ScummTR 各兩弧 + lipo + 組 `.app`，含四道守門
* `day_of_the_tentacle_cht/tools/verify-mac-binary.sh` —— 上表的五項靜態驗收
* `day_of_the_tentacle_cht/tools/build-mac.sh` —— 對照組，同一份設定的 GitHub Actions 原生版

實測（14 核機器，另有其他工作佔掉約一半，`JOBS=6`）：預編工具鏈 image 2 分鐘；相依庫六份（SDL2 / libogg / libFLAC 各兩弧）6.5 分鐘；ScummVM 兩弧 10 分鐘；ScummTR 兩弧加打包 1 分鐘。從零跑完約 20 分鐘。
