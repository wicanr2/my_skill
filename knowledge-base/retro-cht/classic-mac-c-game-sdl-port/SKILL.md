---
name: classic-mac-c-game-sdl-port
description: 把 Classic Mac (Carbon/QuickDraw/CoreFoundation) C 遊戲移植成 SDL2 Linux/Windows/macOS + 繁中化(保留上游邏輯,shim 取代 Mac API)。內建六大必踩雷(最關鍵:shim 缺 prototype→64-bit 指標截斷)+ macOS 打包三雷(無 objcopy→編譯期 weak 宣告、BSD `cp -n` 撞 `set -e`、GITHUB_TOKEN 缺 contents:write)。觸發:出現 `CGrafPtr`/`CopyBits`/`NewGWorld`/`CFStringRef`/Pascal string `\p..`/`GetResource`/`FSSpec`、做 LairWare/Mac remake 中文化、SDL2 取代 QuickDraw、打包 AppImage/Windows/macOS Universal `.app`+`.dmg`(GitHub Actions macos runner、源碼編真 SDL2 非 brew shim、dylibbundler、lipo 雙弧)。完整 shim 對照與打包見內文。
---

# Classic Mac C 遊戲 → SDL2 跨平台移植 + 中文化 Skill

## 何時啟用

- 「把這個 Mac (LairWare / Carbon) C 遊戲跑在 Linux/Windows」「用 SDL2 取代它的繪圖」
- 上游原始碼出現:`CGrafPtr`、`CopyBits`、`NewGWorld`、`SetGWorld`、`DrawThemeTextBox`、
  `CFStringRef`、`CFPreferencesCopyAppValue`、Pascal 字串 `"\p..."`、`GetResource`、`FSSpec`
- 「Classic Mac 遊戲中文化」「resource fork 抽資料」「QTMA `.mov` 音樂轉檔」
- 想加復古顯示(單色/CRT 濾鏡、多平台 tileset 切換)、想打包 AppImage / Windows zip / **macOS Universal `.app`+`.dmg`**(「補 Mac 版」「加 macOS support」也算)

**不適用**:純 QuickBasic/.bas → 用 `qb64pe-game-linux-port`;DOS 16-bit binary → DOSBox;
ScummVM 已支援的遊戲 → 直接用 ScummVM。

## 移植策略(垂直切片,先打通主幹)

1. **抽出可攜 C 遊戲邏輯**,剝離 Mac API 呼叫(純邏輯檔 0 改動,平台檔逐段移植)。
2. **強制 `-include mac_shim.h`** 到所有上游 `.c`:集中放 Mac 型別 typedef + **所有 shim 函式 prototype**。
3. **QuickDraw shim** (`src/compat/qd_*.c`):`CGrafPtr`→`SDL_Surface`、`NewGWorld`→`SDL_CreateRGBSurfaceWithFormat(ARGB8888)`、`CopyBits`→等尺寸 `SDL_BlitSurface` / 不等尺寸 `SDL_BlitScaled`、`RectCopy`→`SDL_RenderCopy`。
4. **平台層** (`src/platform_sdl/`):自寫 `main.c` (present 迴圈 + 影格節流)、`plat_event.c` (SDL→Mac event)、`plat_cf.c` (CoreFoundation shim)、`plat_image/sound/resource.c`。
5. **文字漏斗**:`UDrawThemePascalString`/`DrawThemeTextBox` → `SDL_ttf` (CJK TTF)。
6. **Docker first** 全程建置;game-tester 截圖當 pass/fail loop。

## ⚠️ 六大必踩雷(Classic Mac → SDL,血淚)

### 1. 🔴 shim 函式缺 prototype → 64-bit 指標截斷(最隱蔽、最致命)

上游檔若**看不到** shim 函式宣告(prototype 只在平台層 header、上游沒 include),C 會**隱式宣告該函式回 `int`**。x86-64 下,回 **64-bit 指標**的函式(`CFArrayGetValueAtIndex`、`CFPreferencesCopyAppValue`、`Copy*` 等)回傳值被**截斷成 32 位** → 壞指標 → 各種詭異行為(掃描錯亂、隨機崩潰、資料錯位)。

> **u3-cht 實例**:`GetGraphics()` 用 `CFArrayGetValueAtIndex` 掃 tileset 目錄,該函式 prototype 只在 `plat.h`(上游不 include),`CFArrayGetCount` 等完全沒宣告 → 上游隱式回 int → 指標截斷 → 目錄掃描只比對 1 次、即使檔案存在也載不進 → tileset 渲染成青條紋。耗 ~17 輪才定位。

- **clang `-Wno-implicit-function-declaration`**(為壓上游雜訊常設)會**把警告壓掉**,所以編得過、跑起來壞,極難察覺。
- **鐵律**:**所有 shim 函式(尤其回指標 / `CFIndex` / handle 者)的 prototype 必須集中在被 `-include` 到所有上游檔的 header (mac_shim.h)**。移植初期就把它們補齊,別等出怪事。
- 診斷:暫時拿掉 `-Wno-implicit-function-declaration` 編譯,看哪些函式報 implicit declaration。

### 2. 🔴 `-fpascal-strings`(clang 必須,GCC 不支援)

上游大量 `"\p..."` Classic Mac Pascal 字串字面值(長度前綴)。**clang 需 `-fpascal-strings`**;GCC 不支援 → 把 `\p` 當普通字元 `'p'`,首位元組 `0x70`=112 被當 Str255 長度 → 讀 112 byte 亂碼。**故上游檔用 clang 編**(compat/平台層可 gcc,混合連結)。clang 較嚴需 `-Wno-implicit-function-declaration -Wno-int-conversion -Wno-incompatible-pointer-types*`。

### 3. UTF-8 高位元被 `& 0x7F` 砍掉

上游文字處理常見 `char & 0x7F`(假設單位元組 ASCII / MacRoman)。中文 UTF-8 多位元組的高位元被砍 → 亂碼。需逐一找出文字路徑上的 `& 0x7F`,在 UTF-8 化後移除(但 talk/resource 解碼端的 `& 0x7F` 可能是必要的還原,要分辨)。

### 4. 上游檔 ISO-8859 / MacRoman 編碼

GNU grep 預設把含高位元組的檔當 binary 靜默跳過 → **一律用 `grep -a`**。Edit 工具寫回時會把遠處註解的高位元組 transcode(純註解無妨,但**產 patch 要手動只留目標 hunk**)。

### 5. intra-TU 呼叫無法 objcopy weaken(+ macOS 無 objcopy)

想用 `objcopy --weaken-symbol` 重導向某函式時,**同一 translation unit 內的呼叫**已在編譯期綁定,weaken 無效 → 必須直接實作該函式(或改用 `-include` 注入)。

- **典型用途**:上游檔(如 `UltimaText.c`)**自帶** `UDrawThemePascalString`/`UThemePascalStringWidth` 的 Mac 實作,compat/`qd_text.c` 又以 SDL_ttf CJK 版定義同名強符號 → 連結期重複符號。Linux/Windows 靠 `objcopy --weaken-symbol` 把上游那份弱化,由 compat 強符號覆蓋。
- 🔴 **複合雷(踩過)**:上游檔常是 **NEL(0x85)換行的 Classic Mac 編碼**,普通 `grep` 靜默把它當 binary 略過(見雷#4)→ 誤判「上游沒定義該符號、objcopy 是 no-op」→ **在 macOS 省掉 weaken → 連結才炸重複符號**。**判斷任何符號在不在某上游檔前,一律 `grep -a`**,別信普通 grep 的「找不到」。
- 🔴 **macOS 無 `objcopy`**(Apple 工具鏈不含):不要為此裝笨重的 `brew llvm`。改**編譯期 weak 宣告**達同效——只在編譯該上游檔時 `-include` 一個小 header,把函式在定義前先宣告成 `__attribute__((weak))`,clang 便把後續定義發成 weak 符號,連結由 compat 強符號覆蓋。**對 fat(universal)物件原生生效、免外部工具**。範例:`src/compat/weaken_upstream_text.h`(型別靠先一步 `-include mac_shim.h` 提供)。

### 6. Pascal string → UTF-8 邊界

`Str255` 長度前綴(255 byte 上限)、單位元組寬度假設。中文化要:Pascal↔UTF-8 轉換加長度安全截斷;CJK-aware 換行/寬度(`RewrapString`/`PixelsWideString` 餵全形 2 倍寬)。

## 文字中文化

- **字串外部化**:上游 `STR#` / plist / `GetIndString` → 抽成自家格式(每行一字串 + lang 目錄),載入器一個函式(`GetPascalStringFromArrayByIndex`)重寫即可,取字程式不動。
- **單一繪字漏斗**:定位 `UDrawThemePascalString` / `UPrintChar` / `DrawThemeTextBox` → 全部導向 `SDL_ttf` (`TTF_RenderUTF8_Blended`)。換行/寬度邏輯餵 CJK 寬度。
- **「名稱首字 = 代碼」陷阱**:種族/職業表常以「名稱首字母」當比對代碼(load-bearing)。中文化名稱會破壞比對 → 解耦:表改中文,另立 `char codes[]` 陣列供比對。

## 資產

- **tileset / 美術**:多半已是 PNG/GIF → `SDL_image` 直載。多平台 tileset 切換機制(`<name>-Tiles/-Mini/-Mask/-Font/-UI` 前綴)只要修好雷#1 就能用。
- **音樂**:QuickTime Music (`.mov`, QTMA 'musi' 音符序列,非取樣) → 解析 mdat 事件轉 MIDI → fluidsynth (GM soundfont) → ogg。樂器在 stsd tune header 的 ToneDescription (gmNum)。
- **音效**:wav/mp3 → `SDL_mixer` `Mix_LoadWAV` 直用(不必轉 ogg)。
- **resource fork** (`.rsrc`):殘留資料走 `GetResource('CONS'/'snd '/…)` → 抽出轉一般檔(注意程式的 BASERES 與資源編號可能差 ±100)。

## 功能增強(present 迴圈是注入點)

- **影格節流**:上游每輪詢都 present → 快 GPU 達上千 fps → 回合/動畫過快。`U3_PlatPresent` 加 `SDL_Delay` 補足固定 fps(可調速檔位存偏好)。
- **F1 指令表 overlay**:在 `RenderCopy(gameTex)` 後、`RenderPresent` 前,於 renderer 層疊半透明面板 + TTF 指令表。截圖要從 `SDL_RenderReadPixels` 讀(才含 overlay)。
- **F2 顏色濾鏡**(復古單色/CRT):present 上傳 texture 前逐像素 `y=(77R+150G+29B)>>8` 取亮度再上色(綠磷光/琥珀/灰階)。不依賴 tileset,中文一併單色 → 風格統一。
- **F3 多平台 tileset 切換**:改 tileset 偏好 + 重新呼叫上游 `GetGraphics()` 重載;世界狀態即時重畫。
- **放大視窗滑鼠修正**:`RenderCopy(NULL,NULL)` 等比填滿後,滑鼠座標要依 `畫布/視窗` 比例換算。

## 偏好持久化(CFPreferences shim)

- `CFPreferences*` → 文字檔(`key value` 每行,鍵→long)。**白名單只存遊戲選項**(音效/音樂/速度/顏色…);Mac 顯示/視窗偏好(FullScreen/座標/DisplayMode)維持 no-op,避免污染。
- **字串型偏好用「索引」存**:如 tileset 名含空格,存 int 索引(`TileSetIdx`)避開 `fscanf` 空格解析問題,讀取時索引→名稱查表。

## 測試與驗證(Docker first)

- **game-tester 腳本**:env 指定腳本檔,內容逐 byte 當鍵盤注入 + 控制指令(等待 gUpdateWhere、合成點擊、切換熱鍵)。截圖比對為決定性 pass/fail loop。
- **env 測試鉤子**(env-gated,一般遊玩無影響):teleport 座標、強制 tileset/顏色、dump 狀態、`*_DBG_*`。**printf 需程式乾淨退出(MAX_FRAMES)才 flush**。
- **載入序列 debug 是利器**:在 `IMG_Load` 包裝印 `[IMG] path -> WxH pitch`,改 tileset/資產類問題優先用它看「實際載入了什麼」。
- **對照法排除變因**:`cp 原生資產 改名` 測試,排除「檔名/編碼」假設,鎖定真正異常點。
- **ASan**:會誤報上游良性溢位,真崩潰看 NULL deref。
- **截圖陷阱**:`U3_SHOT_DIR` 須先 `mkdir`(否則 `IMG_SavePNG` 靜默失敗 = 0 截圖,易誤判凍結);timeout 殺進程時最後一張 PNG 可能半毀,取倒數第二張。
- **wine smoke**:Windows exe 用 `xvfb-run wine`,腳本時序可能與真機不同 → 驗渲染用 env 直接設狀態(別只靠腳本熱鍵)。
- **AppImage headless 驗證**:無 FUSE 時用 `--appimage-extract-and-run`;**務必從「非 AppImage 所在目錄」啟動**(如 `cd /tmp` 再跑絕對路徑 AppImage),否則驗不到上面的「雙擊閃退」修法對 AppImage 是否生效;同時驗「不設字型 env 時中文是否仍正常」(font fallback)。Windows zip 同理:解壓後 `cd /tmp` 再用絕對路徑跑 exe + **不設 U3_FONT**,才是最接近真機雙擊的測法。兩個交付物(`*.AppImage` / `*-windows-x64.zip`)都在 `dist/`(gitignore,靠重新打包產生)。

## 打包(Docker first)

- **AppImage**:Ubuntu 22.04 容器建置(求 glibc 相容),含資料 + Noto CJK 字型,AppRun 設字型/語言;排除 libc/GPU 驅動,其餘 `.so` 自含。
- **Windows**:`clang --target=x86_64-w64-mingw32 -fuse-ld=lld -fpascal-strings` + binutils-mingw + gcc-mingw CRT + libsdl.org SDL2/image/ttf/mixer mingw devel;`cp -r assets`(含全部 tileset)+ `.bat` 啟動腳本(設語言/字型)。檔名含空格/`&` 的資產走目錄列舉不經 shell,安全。
- 🔴 **雙擊 exe 閃退陷阱(必修)**:exe 用相對路徑讀 `assets/`,**依賴啟動工作目錄**。Windows 雙擊 exe、`.bat` 的 `start`、或從別處啟動時 cwd ≠ 解壓目錄 → 找不到 `assets/` → 資源載入後 NULL deref **閃退 (signal 11)**。**wine 從解壓目錄 `cd` 進去再跑不會重現**(工作目錄剛好對),要 `cd /tmp` 再用絕對路徑跑 exe 才複現。修:`main()` 啟動時若「exe 旁有 `assets/`」(`SDL_GetBasePath`+`stat`)就 `chdir` 過去(條件式 → 不破壞 exe 在 build/、assets 在 repo 根的開發/測試);AppImage 任意路徑啟動同樣受惠。
- 🔴 **字型 fallback**:未設字型環境變數時,別只落到 Linux 系統字型路徑(Windows 不存在 → 中文變方塊)。fallback 到 exe 旁打包的字型(chdir 後相對路徑即可);`.bat` 雖設了字型 env,但使用者常直接雙擊 exe 繞過 bat。

### macOS Universal `.app` + `.dmg`(GitHub Actions,非 Docker)

**Linux 無法可靠跨編 Mach-O、`codesign`/`hdiutil`/`lipo` 只在 macOS** → 走 GitHub Actions `macos-14`(Apple Silicon)runner 原生 build。這個 SDL port 把 macOS 當純 POSIX+SDL 目標(`-include mac_shim.h` + `-I fakeinc` 攔截真實 Carbon SDK,完全不連 Apple 原生框架),故 build 幾乎 = Linux 那套 clang 命令加 `-arch`。實作範例:`u3-cht` `tools/package_macos.sh` + `.github/workflows/build-mac.yml`。

- **Universal**:因 build 是手寫 clang(非 CMake),一趟 `-arch arm64 -arch x86_64` 直接出 fat binary;SDL 系列用 CMake `-DCMAKE_OSX_ARCHITECTURES="arm64;x86_64"` 編 fat dylib。**單一 SDL prefix** → 剛好避開「per-arch 各自 prefix + lipo 讓 dylibbundler 退化成單弧」的陷阱(見 `mac-app-cross-pack` skill)。
- 🔴 **[HARD] 別 `brew install sdl2`**:2026 起 brew 的 sdl2 是架在 SDL3 上的 shim,runtime 才 `dlopen` libSDL3;dylibbundler 只打包靜態相依,不會收 libSDL3 → 玩家端「Failed loading SDL3 library」黑畫面,**本機(有裝 SDL3)測不出來**。改從 release **源碼** tarball 編真 SDL2(自帶 vendored 相依,免 submodule):image 用 `-DSDL2IMAGE_BACKEND_STB=ON`(PNG/JPG 免 libpng/jpeg,GIF 內建)、ttf 用 vendored freetype `-DSDL2TTF_HARFBUZZ=OFF`、mixer OGG 用 `-DSDL2MIXER_VORBIS=STB`(WAV 內建)其餘 codec 全關;`-DCMAKE_POLICY_VERSION_MINIMUM=3.5` 相容 CMake4。**辨識**:`.app/Contents/Frameworks/libSDL2-2.0.0.dylib` ~2–3.5MB=真、~0.5MB=shim;`otool -L … | grep SDL3` 有命中就是 shim。
- 🔴 **dylibbundler 對自編 SDL 互動式無限 hang**:自編 dylib install name 是 `@rpath/…`(非 brew 的絕對路徑),dylibbundler 解不到 → 進互動模式問路徑,CI 無 stdin → 無限「Try again」卡爆。修:`-s "$PREFIX/lib"`(給搜尋路徑)+ `</dev/null`(保險絲,解不到就 fail-fast 而非 hang)。
- 🔴 **[HARD] macOS(BSD)`cp -n` 跳過已存在檔案回「非 0」exit**(GNU cp 回 0)。在 `bash -e`(GitHub Actions run 預設 `-eo pipefail`)下,回填/複製資產時只要跳過任一既有檔,整步就**零輸出中止**、超難定位。要「只補不覆蓋」改 **`rsync -a --ignore-existing`**(回 0)。診斷 CI 零輸出 exit 1:先在該 step 加 `set -x`。
- 🔴 **無 objcopy → 編譯期 weak 宣告**化解上游/compat 同名繪字符號重複(見雷#5)。
- **.app 佈局**:binary + `launch` wrapper 在 `Contents/MacOS/`,assets 在 `Contents/Resources/`,SDL dylib 由 dylibbundler 收進 `Contents/Frameworks/`。若 `main()` 已有「exe 旁有 assets 就 chdir + 未設字型 env 就 fallback 相對路徑字型」(見上「雙擊閃退/字型 fallback」),wrapper 只需 `cd ../Resources` 後 exec,零 env 依賴。字型:mac 無 fonts-noto-cjk → `curl` 取 Noto Sans CJK TC OTF 命名為 `U3Font.ttc`(TTF_OpenFont 開 face 0)。
- **防呆斷言(擋「CI 綠但玩家壞」)**:對主 binary 與 `Frameworks/libSDL2` 都 `lipo -info` 須同時見 `arm64`+`x86_64`,任一非雙弧 `exit 1`;`otool -L` 不得命中 SDL3。ad-hoc `codesign --force --deep --sign -`;`ditto` 出 zip + `hdiutil create -format UDZO` 出 dmg(雙保險)。Gatekeeper:附「右鍵打開 / `xattr -dr com.apple.quarantine`」說明。
- 🔴 **附產物到 Release 需 `permissions: contents: write`**:workflow 沒宣告時預設 GITHUB_TOKEN 唯讀,`softprops/action-gh-release` 更新既有 release 被擋「Resource not accessible by integration」。tag 觸發即自動附;手動觸發驗證時可本機 `gh release upload --clobber` 補上綠燈產物,不必重跑 CI。
- **gitignore 資產回填**:LairWare 美術刻意不進 git tree(引擎/資料分離),CI checkout 缺料 → build 前從既有 Release 的 Windows zip 抓完整 `assets/` 以 `rsync --ignore-existing` 補齊。
- **[成本][HARD]** 等 CI + 搬 artifact 派便宜 agent(haiku/sonnet)盯,旗艦別背景 poll(見 `rulebook/35`+`45`)。

## 上游修改納管(patch 流)

- **上游目錄唯讀**;中文化/修正放 `patches/*.patch`,build 腳本開頭 idempotent 套用(`git apply --reverse --check` 偵測已套用則略過)。重新 clone 上游仍可還原。
- 手寫 patch hunk 起始 context 易被 GNU patch 拒 → **用 `git apply` 套用後 `git diff` 重生標準格式**(對 ISO-8859 檔的 transcode 雜訊 hunk 要手動剔除)。

## Reference

- 完整實作範例:`u3-cht` repo (github.com/wicanr2/u3-cht) — Ultima III: Exodus LairWare Mac 版 → SDL2 中文化,三平台交付(Linux AppImage / Windows zip / macOS Universal `.app`+`.dmg`)。
- 關鍵檔:`src/compat/mac_shim.h` (prototype 集中)、`src/compat/qd_*.c` (QuickDraw shim)、`src/compat/weaken_upstream_text.h` (macOS 編譯期 weak)、`src/platform_sdl/plat_cf.c` (CoreFoundation shim)、`tools/package_macos.sh` + `.github/workflows/build-mac.yml` (macOS Universal 打包)、`docs/單色模式評估.md` (CF prototype 截斷根因記錄)。
- 互補 skill:`mac-app-cross-pack`(SDL 1.2 / 更廣的 macOS Universal + dmg + Gatekeeper SOP)。
