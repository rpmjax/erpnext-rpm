# VM 操作程序 — 唯一有效入口

更新：2026-10-02。版本目標與環境最後觀測只看 [PROJECT_STATUS](PROJECT_STATUS.md)。日期型 vm-update 文件僅為歷史紀錄，不再依其舊版本命令更新。

本程序對應 deploy/deploy.sh 現有實作，未新增 wrapper。命令在 Linux VM 執行，逐條執行、錯誤即停。GCP 暫不操作；若日後使用仍須先核對該機資源與防火牆。

## 1. 選定環境（每次 SSH session 都做）

Hyper-V，使用 paskadmin：

```bash
cd ~/src/erpnext-rpm
export RPM_STATE_DIR=/home/paskadmin/.config/rpm-worklog-vm
```

GCP，依操作者確認使用 root（僅將來需要操作時），沿用既有 state directory：

```bash
cd /opt/erpnext-rpm
export RPM_STATE_DIR=/home/paskcoltd/.config/rpm-worklog-gcp
```

不要因登入 root 就改用 root 的預設 state directory，也不要切換另一個 Compose project。不修改主機 DB/Redis、其他網站或全域 listeners。

## 2. 唯讀盤點：先辨識正在運行什麼

```bash
date -Is
git status --short --branch
git rev-parse HEAD
test -f "$RPM_STATE_DIR/deploy.env"
# 僅讀管理者已建立的可信設定檔
set -a
. "$RPM_STATE_DIR/deploy.env"
set +a
printf 'Project=%s Site=%s TargetImage=%s\n' "$RPM_PROJECT" "$RPM_SITE" "$RPM_IMAGE"
docker compose --env-file "$RPM_STATE_DIR/deploy.env" -p "$RPM_PROJECT" -f deploy/compose.yaml ps -a
for cid in $(docker compose --env-file "$RPM_STATE_DIR/deploy.env" -p "$RPM_PROJECT" -f deploy/compose.yaml ps -q); do
    docker inspect --format '{{.Name}} image={{.Config.Image}} id={{.Image}} running={{.State.Running}} restarts={{.RestartCount}}' "$cid"
done
bash deploy/deploy.sh status
```

Git SHA＝下載的程式；TargetImage＝下次操作使用的設定；inspect＝實際運行。三者不同不一定是故障，但代表更新階段尚未一致。`0.1.0 UNVERSIONED` 不能辨識自訂 app commit。detached HEAD 是固定版本部署的預期狀態，不必修成 branch。

有工作目錄修改、站名/project 不符、服務異常或混用 app images 時先停，保留輸出和 logs；不要 reset、init 或刪 volumes。

## 3. 既有站更新

先安排無人寫入的維護窗口、確認磁碟/記憶體與備份目的地。低資源機不並行操作。

```bash
free -h
df -h . "$RPM_STATE_DIR"
bash deploy/deploy.sh backup
```

記下輸出的備份路徑，複製到 VM 外受控位置，確認檔案完整。備份含秘密，不貼公開訊息。活躍寫入期間備份不保證附件與 DB 同一時間點；update 還會在維護期間再備份。

從狀態頁選定固定候選 SHA 或 release tag，替換下列字串；不要照貼占位文字，也不以 branch HEAD 默認目標：

```bash
TARGET_REF='替換為狀態頁的固定SHA或release標籤'
git fetch origin --tags
git rev-parse --verify "$TARGET_REF^{commit}"
git switch --detach "$TARGET_REF"
git log -1 --oneline
bash deploy/deploy.sh build
```

build 成功僅代表映像完成，設定 TargetImage 已改，運行容器此時仍可能是舊版。重跑第 2 節核對目標後：

```bash
bash deploy/deploy.sh update
bash deploy/deploy.sh status
```

update 的實際順序：維護模式→停止入口/worker/scheduler→備份舊容器資料→停 backend→新映像 migrate→重啟 app 服務→關閉維護模式→九服務 verify。它已內建 60 秒觀察，不必成功後立刻重複測試；需要獨立補驗時用 `bash deploy/deploy.sh verify`。

注意：目前腳本在 verify 前已恢復入口及關閉維護模式，因此 verify 失敗不保證站台仍停用。失敗時須重新盤點，不能一概視為封閉安全狀態。這是已知行為，未在本批修改腳本。

## 4. 成功與驗收

### 公司分析版本的額外核對

先依第 1～3 節完成既有站更新，不執行 init。公司分析需要明確設定與授權，migration
只建立角色，不會自動授予任何使用者公司全員存取。

1. 在目的站核對 Company 的實際文件名稱為「均輝企業股份有限公司」。
2. 核對預定管理者為 enabled User，且只有一筆 Active Employee 對應，Employee.company
   與上述公司相同；不能沿用本地測試的 Employee ID，也不能假定 rpmjaxadmin 已有對應。
3. 完成核對後，在同一 SSH session 執行以下設定（第 2 節已載入環境變數）：

```bash
docker compose --env-file "$RPM_STATE_DIR/deploy.env" -p "$RPM_PROJECT" -f deploy/compose.yaml exec -T backend bench --site "$RPM_SITE" set-config rpm_worklog_company '均輝企業股份有限公司'
docker compose --env-file "$RPM_STATE_DIR/deploy.env" -p "$RPM_PROJECT" -f deploy/compose.yaml exec -T backend bench --site "$RPM_SITE" clear-cache
```

4. 由有權管理 User 的操作者，在目的站將 `RPM Worklog Management` 角色授予已核對的管理者。
   不因此授予 System Manager／HR 角色；不批次套用本地角色名單。
5. 管理者重新登入，從 Analytics 的「工作明細分析／匯出」驗證公司範圍、
   員工／部門多選、CSV/XLSX 實際資料列與工時對帳。普通員工仍只能查本人；
   普通主管仍依原直屬範圍。原生列表的 0-row export 問題並未在此版本修復。

缺設定或 Employee 對應時，公司分析拒絕存取是預期行為，不能藉擴大原生 DocType 權限繞過。
Company 採目前 Employee.company；離職員工歷史可納入，並非歷史公司／主管 snapshot。

### 一般成功條件

更新成功至少有 SERVICES_STABLE；實際 app 容器映像與目標一致，DB/backend healthy。保存 migration/verify 結果，重新執行唯讀盤點。

```bash
curl --max-time 10 -I -H "Host: $RPM_SITE" "http://${RPM_BIND_IP}:${RPM_PORT}/login"
curl --max-time 10 -H "Host: $RPM_SITE" "http://${RPM_BIND_IP}:${RPM_PORT}/api/method/ping"
```

浏览器保存未存變更後 Ctrl+Shift+R，使用原帳號核對：本人紀錄/附件、主管範圍、送審/退回/核准、本批功能。翻譯帳號語系需為 zh-TW；若原始碼更新而 Client Script 未同步，檢查 migrate，不能只靠清瀏覽器快取。

將觀測時間、實際版本與結果回填狀態頁。沒有回報就維持 unknown；HTTP 200 不等於業務驗收通過。

## 5. 失敗／接續／回復

```bash
bash deploy/deploy.sh logs
```

- build 失敗：舊容器通常仍在運行；先查資源與 build log，不能進 update。
- migration 失敗：保留資料、備份與維護狀態，確認原因後再決定接續；不反覆 init。
- verify 失敗：盤點實際容器、維護狀態與入口，不假設未開放。
- 已完成更新但未驗收：先驗收，不重新執行整套流程。
- 需要回復：先保存事故後新增資料，再按 [DR 方案](disaster-recovery-validation.md) 以相符映像、DB、附件及 encryption_key 在隔離環境還原；不把 git switch 舊 SHA 當作資料回復。

backup 的 deploy.env 可能指向新目標，但 running-image.txt 才記錄當時執行映像。兩者不一致時，依同批備份與實際映像證據判斷，不盲目覆蓋設定。完整 DR 尚未通過，不宣稱有一鍵 rollback。

## 6. 全新站（獨立流程，既有站禁止使用）

確認目標為空白、獨立 project/volumes、loopback 埠未占用，Docker/Compose/Git/OpenSSL 可用，並選好固定程式版本及 state directory：

```bash
bash deploy/deploy.sh configure
# 在 init 前核對 deploy.env 的 project/site/bind/port
bash deploy/deploy.sh build
bash deploy/deploy.sh init
bash deploy/deploy.sh status
```

configure 產生 DB/Administrator secrets，不能提交 Git。init 不覆寫既有站；中途失敗先查 logs，不刪資料重試。新站 Asia/Taipei 驗證應 PASS，既有站更新保留時區。HTTPS、DNS、主機 firewall 另行處理；[GCP 特例](gcp-cyberpanel-deployment-2026-09-21.md)不是通用必要條件。

## 7. 下一批工具改善（尚未實作）

優先新增唯讀 report：一次列出 Git/設定/各服務 image ID 與差異；其次輸出脫敏部署 manifest。安全 wrapper 待另批實作，須保留備份、固定版本、停機、驗證及錯誤退出，不自動選最新版或自動降版。
