# Isaac Sim 5.1 監控與物理調參 playbook(專案X 專案實例)

> 這是 `wicanr2/<專案私有 repo>` 的 `docs/<專案內部文件目錄>/118-isaac51-monitoring-playbook.md` 快照。
> 交叉連結指向該 repo 同目錄的文件,在本 skill 內不可點;內容以該 repo 為準。

> 對象:要在 專案X(或任何 headless Isaac Sim 5.1 主機)上判斷「模擬到底發生了什麼」、
> 並據此調物理參數的人(或 LLM)。
> 這份記的是**方法**——怎麼觀測、觀測到的數字怎麼讀、哪些觀測方式會騙你。
> 具體參數值與備份清單在 [117](117-isaac-scene-backup-20260726.md);場景建置 know-how 在姊妹 KB
> [`docs/<專案內部 KB>/`](../<專案內部 KB>/README.md)。
>
> 對應 skill:`isaac-sim-monitoring`(repo `wicanr2/my_skill`)。

---

## 1. 為什麼 Isaac Sim 需要一套專門的監控方法

一般服務壞掉會噴 exception、會 5xx、會有 stack trace。Isaac Sim 這條鏈的失效**大多沒有任何錯誤訊息**:

| 實際壞掉的事 | 表面症狀 | 錯誤訊息 |
|---|---|---|
| PhysX simulation view 失效 | 車永遠不動,模擬時鐘照走 | **無** |
| FastDDS 共享記憶體版本不相容 | ROS graph 有 tick,資料面全丟 | **無** |
| 叉齒碰撞近似是 convexHull | 叉齒咬不進棧板叉孔 | **無** |
| 場景載入了舊 USD | demo 兩三分鐘「假完成」 | **無** |
| WebRTC relay 長跑退化 | 畫面 1-5 fps,Isaac 其實 20 fps | **無** |
| 剛體查詢對非剛體回傳未初始化記憶體 | 座標是 1e9 或 1e-41 | **`ret_val=True`** |

所以監控的第一原則是:**不要等錯誤訊息,主動去問狀態**。第二原則是:**每個數字都要知道它是從哪一層取的**——同一個「棧板在哪裡」的問題,USD authored 值、Fabric 即時值、DB 登記值三者可以同時存在且互相矛盾,而且都不報錯。

---

## 2. 三個觀測面,各自能回答什麼

```
                ┌─────────────────────────────────────────────┐
                │  Isaac Sim 5.1 (headless, streaming kit)     │
                │                                             │
   ①  stdout ───┤  [open_fullusd] ... 印出來的一切             │
      (log)     │                                             │
                │  ┌───────────────────────────────────────┐  │
   ②  UDP  ─────┼─▶│ 127.0.0.1:9901 探針(問什麼答什麼)      │  │
      9901      │  └───────────────────────────────────────┘  │
                │                                             │
   ③  ROS2  ────┤  /tf, /joint_states, ActionGraph            │
                └─────────────────────────────────────────────┘
```

| 觀測面 | 回答得了 | 回答不了 |
|---|---|---|
| ① log | 「發生過什麼」(歷史)、載入了哪個場景、有沒有例外 | 「現在的座標是多少」——除非你先用 ② 問 |
| ② UDP 探針 | 「現在」的物理真相:位姿、碰撞近似、摩擦、相對叉齒的位移 | 跨時間的趨勢(要自己連續取樣) |
| ③ ROS2 | 控制面通不通、servo 有沒有送軌跡 | 物理層對不對(topic 全綠但東西沒動是常態) |

**三個都要看**。只看 ③ 會得到「帳面全綠、實體沒動」;只看 ① 會對著早就被取代的 log 下判斷。

---

## 3. ① log:一律從活著的行程反查,不要猜檔名

這台機器上 Isaac 可能由三個來源啟動——手動、`isaac_watchdog.sh`、`reset_self_heal.py`——各寫各的檔。**實戰誤判過兩次**:對著自己啟動時指定的 log 下結論,但那支早被別人重啟取代,log 停在幾分鐘前。

正確做法是問 `/proc`:

```bash
PID=$(pgrep -f '[i]saacsim.exp.full.streaming.kit' | head -1)
LOG=$(readlink -f /proc/$PID/fd/1)
```

現成工具 `~/<專案>/scripts/isaac_logs.sh` 就是把這件事包起來:

```bash
./isaac_logs.sh            # 各元件 PID + 真正的 log 路徑 + 最後幾行 + 距今幾秒
./isaac_logs.sh isaac 40   # 只看 Isaac
./isaac_logs.sh ros 40     # 只看 ROS(bridge/servo)
./isaac_logs.sh errors     # 只抓錯誤/關鍵訊號
```

它會印「最後寫入距今幾秒」——**這個數字比 log 內容更重要**。距今幾百秒代表這支已經沒在動,你正在讀化石。

> ⚠ 這個技巧有個前置條件:**log 必須落在真實檔案上**。如果啟動時 stdout 導到 pipe 或 `/dev/null`,`/proc/<pid>/fd/1` 反查全部失效。`<專案>-boot.service` 為此特別把每支的輸出都寫成具名檔案(見 [116](116-boot-resilience.md))。

### 判斷「Isaac 到底載了哪支 USD」

不要看啟動腳本裡寫什麼——腳本可能被改過、可能有旗標覆寫。看行程實際 mmap 了什麼:

```bash
grep -o '/[^ ]*\.usd[a-z]*' /proc/$PID/maps | sort -u
```

這是唯一能證明「現在跑的是哪個場景檔」的方法。**AMR 不動時第一件事就是查這個 + 對 md5**。

---

## 4. ② UDP 探針:9901 問答協議

`open_fullusd_streaming.py` 在背景開了一個 UDP listener(`127.0.0.1:9901`),收 JSON 單行命令。這是**唯讀查詢 Isaac 內部真相的主要管道**——不用進 GUI、不用附加 debugger、不影響模擬。

送法:

```bash
printf '%s' '{"cmd":"check_place"}' | nc -u -q0 -w1 127.0.0.1 9901
```

回應**不從 socket 回**,而是印到 Isaac 的 stdout。所以標準流程是「先記下 log 目前大小 → 送命令 → 等一下 → 只讀新增那段」(見 §5)。

### 命令表

| cmd | 用途 | 何時用 |
|---|---|---|
| `check_place` | 每顆棧板即時姿態 vs 真值,輸出 `dxy` / `dz` / `dyaw` 與 OK/OUT | 驗收放置精度、量漂移。**最常用** |
| `carry_probe` | 每顆棧板**相對承重叉齒**的位姿(不變量)+ 絕對 rpy | 判斷搬運途中有沒有滑動 |
| `check_physics` | 5 顆棧板的 `RigidBodyAPI` / `CollisionAPI` / `MassAPI` authored 狀態 | 「東西穿過去了」「不受重力」時 |
| `dump_scene` | 棧板 + AMR + 叉齒的即時位姿、物理材質、材質**綁定** | 全面體檢;調摩擦前後對照 |
| `dump_collider` | 碰撞近似型別(convexHull / sdf / …)與解析度 | 抓握失敗時的第一嫌疑 |
| `fix_fork_collider` | 把 `fork_liftA1` 改成 SDF | 這是抓握能成立的關鍵手術 |
| `get_friction` / `set_friction` | 讀/寫靜/動摩擦與 restitution | 調摩擦的 A/B |
| `list_prims` | 列 prim(可 `match` 過濾、`physics_only`) | 找不到某個東西叫什麼路徑時 |
| `capture_truth` | 把當下棧板位姿存成「真值」基準 | reset 後、量漂移之前 |
| `probe_pose` | 同一 prim 用多種方法取世界座標,列出各方法結果 | 懷疑座標來源不對時的對照組 |
| `cam` | 切鏡頭(`top` / `fixed`) | 錄影前切 top view |
| `reset` | 場景重置 | 走 `reset_self_heal.py`,不要手動打 |

### `check_place` 輸出怎麼讀

```
[check_place] /target_pallet: dxy=5.2cm dz=+0.1cm dyaw=0.3deg OUT (live=(5.132,-0.651,1.147) yaw=-0.1)
[check_place] 結果 2/5 在容差內(xy<=1cm, yaw<=3deg)
```

- `dxy` / `dyaw` 是**相對真值**的誤差,不是相對目標端點。
- 預設容差 xy 1cm / yaw 3°,**這是驗收門檻不是告警門檻**——實測單次放置誤差本身就有 5~7cm,拿 1cm 當告警會每輪都紅。
- `live=` 那組是 Fabric 即時座標。**只要它跟 authored 值一致到小數點後三位,就要懷疑你拿到的其實是 authored 值**(見 §6)。

### `carry_probe` 輸出怎麼讀

```
[carry_probe] fork  pos=(3.100,-0.650,0.930) rpy=(+0.00,+0.00,-0.10)
[carry_probe] CARRIED /target_pallet: p_rel=(+0.0120,-0.0031,+0.1180) |0.119| rpy_rel=(+0.10,-0.05,+0.12) ...
```

判讀規則(這是設計時就寫進 docstring 的):

- `|p_rel|` 很小(< 2.5 m 標 `CARRIED`)= 這顆壓在叉齒上。
- 整趟中 `p_rel` / `rpy_rel` **不變** → 沒滑動,不要去動摩擦。
- **單調漂移** → 才是真的滑動,這時談摩擦/接觸參數才有意義。

**這個不變量是關鍵**:絕對座標在車行進時本來就一直變,拿絕對座標看不出「棧板有沒有相對叉齒滑掉」。

---

## 5. 連續取樣:位元組偏移法

單點量測回答不了「有沒有在漂」。要看趨勢就得連續送探針 + 連續收 log。天真的做法是每輪 `tail -n 100`,但 Isaac 的 log 一天長到幾百 MB,行號 tail 是 O(檔案大小),取樣頻率會被拖垮。

正確做法是**記位元組偏移,只讀新增的那段**(O(1) seek):

```bash
F=$(readlink -f /proc/$(pgrep -f '[k]it.*open_fullusd' | head -1)/fd/1)
OFF=$(stat -c %s "$F")
while ...; do
  printf %s '{"cmd":"check_place"}' | nc -u -q0 -w1 127.0.0.1 9901
  sleep 1.5
  NEW=$(stat -c %s "$F")
  [ "$NEW" -gt "$OFF" ] && { tail -c +$((OFF+1)) "$F" | grep -F '[check_place]'; OFF=$NEW; }
done
```

現成的三支:

| 腳本 | 取樣什麼 | 適用問題 |
|---|---|---|
| `pose_watch.sh <out> <n>` | 所有棧板位姿,1.5s 一輪 | 「棧板到底停在哪」 |
| `carry_watch.sh <out> <n>` | `CARRIED` 行,1s 一輪 | 「搬運途中有沒有脫鉤」 |
| `slip_sampler.sh <out> <秒>` | `check_place` 的 dxy/dyaw/live/yaw 攤成 TSV,3s 一輪 | 「棧板是不是邊走邊歪」 |

> `slip_sampler.sh` 的由來:使用者回報「棧板在運送途中就從叉齒上歪掉,不是放置瞬間才歪」。
> 要證實這件事,**必須在搬運過程中連續取樣**,放完之後量一次是量不出來的。
> 這是通則:懷疑「過程中」的現象,就不能只在「結束後」量。

---

## 6. [HARD] 取位姿只能用 `omni.physx`

```python
from omni.physx import get_physx_interface
r = get_physx_interface().get_rigidbody_transformation(prim_path)
```

**不可以改用 `isaacsim.core.prims` / `SimulationContext`**。那些會建立 PhysX tensor view,曾導致 ActionGraph 的 simulation view 失效 → `ArticulationController` 之後永遠拿不到 DOF → **車再也不會動,而且完全沒有錯誤訊息、模擬時鐘照走**。復原要跑完整 RESET。

> 誠實標註:這條規則的**因果機制未經官方文件證實**,是實測歸因。但代價太高(整場 demo 報廢),所以當成硬規則守。
> 另一條曾經寫過的 `usdrt` 路徑**已作廢**,不要照舊文件抄。

### `ret_val=True` 不代表值可用

對非剛體(例如 articulation 的根 Xform)查剛體變換,實測會回 `ret_val=True` 但內容是**未初始化記憶體**:位置量級 `1e9` 或 `1e-41`、四元數范數 ≈ 0。不驗證就會把垃圾座標餵給跟車鏡頭與量測工具,**而且完全不報錯**。

所以每次取完都要過合理性檢查:

```python
if max(abs(v) for v in pos) > 500.0:  return False   # 遠超場景尺度(±20m)
n = sqrt(sum(q*q))
if not (0.5 < n < 2.0):               return False   # 垃圾四元數
```

### 知道自己拿到的是哪一層的值

`live_world_pose()` 取不到即時值時會退回 **USD authored 值**——那是模型檔裡寫死的初始位置,**不是即時值**。它會把 `_LIVE_POSE_BACKEND["name"]` 標成 `authored-fallback`,`dump_scene` 結尾也會印 `pose backend=`。

**每次判讀前先確認 backend 是 `physx`**。拿 authored 值當即時值,會把「車正在動」讀成「車不動」——這正是誤判 FastDDS 事件的其中一環。

---

## 7. 判讀陷阱:同名不同義的量測

`check_place` 會**連帶執行** `check_wip`,而 `check_wip` 量的是「棧板離 WIP 暫存位多遠」。搬運途中經過那附近會量到 40~57cm。

如果你 grep 時不限定行別:

```bash
grep -oE 'dxy=[0-9.]+cm'          # ❌ 會撈到 check_wip 的數字
grep -F '[check_place]' | grep -oE 'dxy=[0-9.]+cm'   # ✅
```

不限定的結果是**每趟都誤觸 RESET**(drift_guard 曾踩過,現在腳本裡標了 `[HARD]`)。

通則:**一支探針印出多種語意的同名欄位時,grep 一定要先鎖行別**。

---

## 8. 漂移:一個會累積的正回饋

實測每跑一輪一鍵 DEMO,棧板就被往層架深處推 5~10 cm,而且**會累積**:

```
真值 5.100 → 5.132 → 5.203 → 5.302 …
```

機制:叉齒以固定行程插入,棧板若已偏深就會被頂得更深 → 正回饋。摩擦補綁只能稍緩,不會消失。連續操作五六輪後,棧板會深到叉不到或撞後擋。

`drift_guard.sh` 的門檻取值理由(這種「為什麼是這個數字」的紀錄比數字本身值錢):

| 門檻 | 值 | 為什麼 |
|---|---|---|
| `DRIFT_LIMIT_CM` | 15 | 8cm 太低——單次放置誤差本身就 5~7cm,連 RESET 自測搬運都會製造這個量級,會變成每輪觸發,而一次 RESET 要 9 分鐘,展場受不了。實測漂到 20.2cm 仍能正常叉取,取 15 留邊際,約每 2~3 輪觸發一次 |
| `DRIFT_LIMIT_DEG` | 5 | 六輪耐久測試收尾時 xy=14.9cm(剛好卡在門檻下沒觸發)但 yaw 已達 9.2°,肉眼看得出歪斜、舊版完全沒擋。正常放置 0.3~1.1°、驗收門檻 3°,取 5 讓正常波動不誤觸,又能在肉眼可見(6.9~9.2°)之前擋下 |

用法:

```bash
./drift_guard.sh          # 只量不動
./drift_guard.sh --auto   # 超標就自動 RESET
DRIFT_LIMIT_CM=8 DRIFT_LIMIT_DEG=4 ./drift_guard.sh --auto
```

### 劇本換了,判準要跟著換(2026-07-26 實測踩到)

v10 兩輪驗收都通過後跑 drift_guard,它回報「最大漂移 **1450.5 cm**」並判定超標。
那 1450 cm 是 PO-B8 停在 WIP 的**正常位置**——劇本刻意搬去的。

根因:舊版取「所有棧板 dxy 的最大值」。v7 劇本是自我復位的兩道指令循環,收工時所有棧板
都回真值,那個寫法當時成立;**v10 收工時故意留兩顆在別處**,於是最大值恆為十幾公尺,
15cm 門檻形同虛設,drift_guard 再也分不出「漂了」與「demo 正常跑完」。

修法:離真值超過 `DRIFT_RELOCATED_CM`(預設 100cm)的不計入漂移——漂移是每輪 5~10cm 的潛移,
不會一次跑掉幾公尺。但也不吞掉,另外列出顆數。修正後同一時刻讀到 13.0 cm / 3.0°(真實漂移),
並標出「另有 1 顆離真值 >100cm」。

> **通則**:守衛程式的判準往往內建了「當時的劇本長什麼樣」這個隱含假設。改劇本、改流程時,
> 要回頭問一次「原本的判準還成立嗎」——它不會報錯,只會安靜地變成永遠觸發或永遠不觸發。

---

## 9. A/B 試驗紀律

調物理參數必然要 A/B。`ab_trial.sh` 把一輪試驗標準化成:寫旗標檔 → 殺 Isaac(看門狗用新旗標拉回)→ 等就緒 → 重啟 relay → 跑一輪 demo → 收判定。

判定四項**全部取地面真相**,不看畫面也不看佇列狀態:

| 判定 | 怎麼取 | 為什麼不能用別的 |
|---|---|---|
| `moved` | TF `world→base_link` 最遠距離 > 1.0 m | 佇列說 done 不代表車動過 |
| `pallet` | 任一棧板即時世界座標位移 > 0.30 m | DB 登記會在車沒動的情況下更新 |
| `mission` | 最後一筆任務終態(finish/abort/close) | UI 狀態 chip 會說謊 |
| `servo` | servo 有沒有送軌跡、有沒有 ABORT | 「沒送軌跡」和「送了但沒動」是不同問題 |

### 兩個踩過的坑(腳本註解裡有,這裡重述)

1. **不能用 `tail -N` 比對看門狗日誌**判斷「就緒」——上一輪殘留的「ROS 鏈已就緒」會讓等待提前放行,Isaac 還沒起來就開始量測。要**記行號,只認之後新增的行**。
2. **每輪先重載看門狗**。它的防抖計數是記憶體變數,重啟才歸零;不這樣做,連續做幾輪 A/B 就會撞到「1 小時 3 次」上限而卡住(實測踩過)。

### 最重要的一條

**A/B 前先確認沒有同時改別的東西。** 這條看起來廢話,但這個專案已經因此浪費過整輪測試——結論歸給了 A,實際上 B 也動了。

---

## 10. 耐久與自癒

| 工具 | 做什麼 |
|---|---|
| `demo_endurance.sh <輪數>` | 每輪:跑 demo → 量放置精度 → 跑 drift_guard(超標自動 RESET)→ 記錄;收尾出完成率與誤差統計。**這是回答「展場整天撐不撐得住」的唯一方式** |
| `isaac_watchdog.sh` | Isaac 進程層看門狗 |
| `relay_watchdog.sh` | WebRTC relay 層 |
| 前端 `framesDecoded` 停格偵測 | 瀏覽器層(ICE 狀態不可靠,要看 framesDecoded 有沒有前進) |

三層看門狗**執行器不重疊**——同一件事只能有一個角色負責重啟,否則會互相踩。殺掉 Isaac 後畫面自動回復實測 1 分 47 秒。

---

## 11. 調參的實際流程

```
① 先建可重跑的 pass/fail 訊號   ← 沒有這個就不要開始調
      └ 通常是 check_place 的 dxy/dyaw,或 ab_trial.sh 的四項判定
② 量 baseline(至少 3 輪,單輪數字沒有意義——漂移會累積)
③ dump 現況:dump_collider + get_friction + dump_scene(含材質綁定)
      └ ⚠ 材質存在 ≠ 有生效。要看碰撞體有沒有真的綁到它(DUMP_BIND 的 computed 欄)
④ 一次只改一項 → ab_trial.sh → 量同樣的訊號
⑤ 判讀:是「放置精度」變好,還是只是「這一輪運氣好」?
      └ 3 輪內的差異多半是噪聲。漂移是累積的,要看斜率不是看單點
⑥ 改動落回 open_fullusd_streaming.py(帶 .bak-before-<主題>-<日期>)
```

### 具體教訓:先看碰撞近似,再談摩擦

`fork_liftA1` 原本是 `convexHull`——薄板叉齒的凸包是**實心楔形**,根本咬不進棧板叉孔。改成 SDF(resolution 512)之後 yaw 誤差直接降到 0.1°。

這裡有個值得記住的後續:當時我們同時上了「μ=5.0 高摩擦材質」,並長期以為抓握是靠摩擦撐住的。活機 `dump_scene` 實測推翻了這件事——材質**確實有** `static=5.0 / dynamic=4.0`,但**承重叉齒 `fork_liftA1` 與所有棧板的 `computed` 綁定都指向外觀材質**(`Metal_Glossy_A` / `Wood_Recycled_A`),唯一綁到高摩擦的是不接觸的 `fork_tilt`;負責補綁的 `bind_high_friction()` 又被 marker 閘住(**預設關,是刻意的**——場景物理由建模者負責)。也就是說,**現行設定下**的抓握完全來自 SDF 碰撞近似。

但這不等於「摩擦無關」。同期的 A/B(doc 112 §三之二)顯示補綁開啟時**橫向偏移從最大 9.3 cm 收斂到 0.9 cm 以內**,深度累積則完全不變。兩件事要分開講:

| 問題 | 歸誰管 | 症狀 |
|---|---|---|
| **咬不咬得住** | 幾何(碰撞近似) | convexHull → 薄板變實心楔形,完全插不進孔 → 「從未被抬起」 |
| **咬住後會不會側滑** | 摩擦(材質 + 綁定) | 抬得起來但橫向偏移大、放下歪掉 |
| **插入深度逐輪變深** | 動作行程(無感知回授) | 兩者都治不了,靠 drift_guard 止血 |

搞混這三件事的代價,就是在錯的旋鈕上花一整天。

> ⚠ 我自己在這件事上判錯過一次:第一版寫成「材質沒有 authored 摩擦值」,那是離線解析**頂層** USD 的誤讀(值在子層)。結論對、理由錯——而錯的理由會害下一個人去查錯地方。**能量的時候就去量**:一道 `dump_scene` 就分得出「沒有值」與「有值但沒綁」。

兩層教訓:
- **接觸問題先查幾何(碰撞近似),再查材質(摩擦)**。順序反了會得到一堆「有效但說不出為什麼」的魔數。
- **「我設了這個參數」≠「這個參數生效了」**。`dump_scene` 的 `DUMP_MAT` 會印材質存不存在、`DUMP_BIND` 印有沒有綁上,兩個都要看。以為在調的東西其實沒接上,是最貴的一種錯覺——它會讓你把功勞歸給錯的改動,下次照抄就失敗。


---

## 12. 快速體檢清單

車不動 / 東西沒搬走 / 數字很怪的時候,照這個順序問:

1. **`isaac_logs.sh`** — 各元件 PID 在不在?log 最後寫入距今幾秒?
2. **`/proc/<pid>/maps`** — 載的是哪支 USD?md5 對不對?
3. **`{"cmd":"dump_scene"}`** — 結尾的 `pose backend=` 是不是 `physx`?
4. **`{"cmd":"check_physics"}`** — RigidBody / Collision API 在不在?
5. **`{"cmd":"dump_collider"}`** — 碰撞近似是 sdf 還是 convexHull?
6. **ROS2** — `/tf` 有沒有在更新?servo 有沒有送軌跡?
7. **DB vs 物理** — `pushback_verify.sh` 雙軌對照。兩邊都單獨說過謊,要一起看。

前六項全綠但東西還是沒動 → 看 [99](99-headless-ros-bridge-fastdds-shm-rootcause.md)(FastDDS SHM 版本不相容,資料面靜默全丟)。

---

## 13. 環境前提(給接手的人/LLM)

- 啟動入口 **一律** `isaac-sim.streaming.sh`;裸 kit 會導致 ROS2 bridge 死、沒有 `/tf`。
- 啟動前**不可** `source /opt/ros/humble`——python 版本不同。
- 主機:`ssh <host>`(`<user>@<host>`,RTX5090),資料在 `~/SMARTMOVE`,腳本在 `~/<專案>/scripts`。
- 探針全部是**唯讀**的,除了 `set_friction` / `fix_fork_collider` / `reset` 這三支。跑診斷不會影響正在進行的 demo。
- 改 `open_fullusd_streaming.py` 前先 `cp` 成 `.bak-before-<主題>-<日期>`——這個目錄現在有二十幾個 bak,每一個都是一次可回溯的決策點。
