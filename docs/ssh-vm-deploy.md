# Ubuntu VM：部署目前 Work Log 版本

本套件建立獨立 ERPNext + rpm_worklog 站台，不覆蓋既有原生 Bench、不攜帶測試人員／交易資料。角色內部名稱暫沿用 Pilot，功能與目前試辦版本相同。公司、人員及真實工號需在新站建立或匯入；個別工號搜尋尚未交付。

## 1. 必要條件

Ubuntu 已安裝 Docker Engine、Compose plugin、Git、OpenSSL；執行帳號能使用 Docker。尚未安裝 Docker 時，依 [Ubuntu 官方安裝文件](https://docs.docker.com/engine/install/ubuntu/) 安裝，先核對 OS 支援版本。本腳本不修改 Nginx、Supervisor、OS 網路或防火牆。

原站需已有離機備份；確認 VM 有足夠資源同時運作兩套 ERPNext。這是獨立部署，不是把 App 裝進原 erpnext.local。

## 2. SSH 下載與設定

Windows：

```powershell
ssh paskadmin@192.168.0.70
```

Ubuntu 首次下載：

```bash
mkdir -p ~/src
cd ~/src
git clone https://github.com/rpmjax/erpnext-rpm.git
cd erpnext-rpm
```

已有 repo：

```bash
cd ~/src/erpnext-rpm
git status --short
git pull --ff-only origin master
```

有未保存修改／不同分支時先處理，不使用強制 reset。正式使用請記錄本次 commit。

```bash
bash deploy/deploy.sh configure
```

設定在 `~/.config/rpm-worklog-vm/deploy.env`。預設 project `rpm-worklog-vm`、站名 `worklog.internal`、只綁 `127.0.0.1:8085`。先確認埠未使用。若要改站名／project，必須在 init 前修改；建立後不可只改變數當作搬站。

隨機密碼位於同目錄 `admin-password`（ERPNext Administrator）與 `db-password`（資料庫 root）。目錄只允許部署者存取，密碼檔供容器唯讀掛載；請用密碼管理器保存 Administrator 密碼，不貼到 Git／聊天紀錄。既有 VM 的 OS 密碼不變。

## 3. 建置並初始化

```bash
bash deploy/deploy.sh build
bash deploy/deploy.sh init
bash deploy/deploy.sh status
```

build 依 Git commit 建立 App 映像；init 建立獨立資料庫、Redis、站台與角色／入口，再啟動服務。第一次需下載映像並建立 ERPNext，可能耗時數分鐘。

成功應出現 `RPM_INIT_SUCCESS`，status 應列出 frappe、erpnext、rpm_worklog。若 init 中途中斷，不刪 volume 或強制重建；保留 logs 以辨識已完成階段。再次 init 遇既有站會拒絕覆寫，避免誤清資料。

## 4. 從自己電腦登入驗收

另開 Windows 終端，保持此 SSH tunnel 連線：

```powershell
ssh -N -L 8085:127.0.0.1:8085 paskadmin@192.168.0.70
```

瀏覽器開啟 http://127.0.0.1:8085 ，帳號 `Administrator`，密碼為上述 admin-password 檔內容。此處 127.0.0.1 經 tunnel 轉送 VM，不是本機舊 8083 Docker。

完成 ERPNext 設定精靈：國家 Taiwan、幣別 TWD、時區 Asia/Taipei、公司資料與管理員資料依實際填寫。語系可先 en 再调整 zh-TW。外寄郵件預設停用，正式通知需另行配置。

## 5. 匯入／開通人員

先建立 Company、Department、Designation、User（System User）、Employee，設定唯一 User 綁定與 Reports To；不要把範例主檔當正式人員。真實工號維持來源欄位，不改寫成 HR-EMP 編號。

管理員完成主檔後，Ubuntu shell 執行（替換實際已建立的 email）：

```bash
bash deploy/deploy.sh enroll employee@example.com employee
bash deploy/deploy.sh enroll manager@example.com manager
```

這會設定最低試辦角色、本人 Employee User Permission 與預設 Employee；不建立帳號、不重設密碼、不授予 System Manager。主管同時需要填本人工作紀錄時，對同帳號再執行 employee 開通。

主管的 Employee 必須為 Active 且 User 啟用；員工 Reports To 指向該主管。開通員工後，登入 /desk 應見「我的工作紀錄」；主管可見「直屬員工工作紀錄」。報表由列表／主管頁入口進入。

## 6. 備份與更新

```bash
bash deploy/deploy.sh backup
```

資料庫、附件與 site_config、部署設定及執行映像記錄複製到 `~/.config/rpm-worklog-vm/backups/時間/`。這仍在 VM 內，須複製到 VM 外受控位置，並演練還原。檔案含秘密及私人資料，不能上傳 Git。

更新必須在維護窗口進行：

```bash
git status --short
git pull --ff-only origin master
bash deploy/deploy.sh build
bash deploy/deploy.sh update
bash deploy/deploy.sh status
```

update 啟用維護、停止入口／工作程序後備份，再用新映像 migrate，成功才恢復服務。失敗時維持停用／維護狀態；不要反覆 init。更新前確認無長時間背景工作，腳本等待工作程序退出最多 120 秒。

如需回滾，先保留事故時資料。資料庫 schema 已改變時，不能只切回舊映像；依備份的版本／附件／site_config 還原到隔離環境，核對後再切入口。完整策略見 [正式上線手冊](ubuntu-hyperv-go-live-runbook.md)。

## 7. 公司網路正式開放

預設 tunnel 僅供驗收。正式開放前，以公司 DNS 與 HTTPS 反向代理轉送 loopback 8085，配置 WebSocket，完成備份還原與權限驗收。不要直接把 DB／Redis 發布到 LAN。

既有原站 80／443 的代理修改須另外安排；本套件不自動接管埠或改寫原站。遠端 Hyper-V 搬移亦依正式上線手冊辦理，避免來源／目的 VM 同時用相同 IP。

## 8. 驗收與診斷

- 員工登入、新增兩列工時、保存、本人隔離。
- 單筆／批次送審；主管退回、員工同單補正、主管核准與鎖定。
- 主管直屬範圍、報表與原單合計相符。
- 重啟後入口及背景服務恢復；備份可還原。

```bash
bash deploy/deploy.sh logs
bash deploy/deploy.sh status
```

切勿將秘密或完整站台設定貼入公開 issue。套件交付與本機全新安裝驗證不代表實際 VM 已安裝；VM 操作與畫面驗收仍由使用者執行。

## 已完成的交付驗證（2026-09-15）

- 以獨立 Compose project 與空白 volumes，在 MariaDB 11.8.6、ERPNext 16.34.1、Frappe 16.33.0 上完成 new-site、install-app、migrate，出現 RPM_INIT_SUCCESS。
- managed bootstrap 重跑保留三個報表設定，沒有依賴既有 PoC Server Script。
- `scripts/test_managed_install.py` 通過：開通／重複開通、兩員工隔離、每日合計、主管查詢、報表、退回補正及核准；測試人員與工作紀錄 rollback。
- HTTP：登入與 Administrator 驗證、表單 metadata、App 圖示資源成功；Guest 主管查詢被拒。
- 備份後在另一隔離站 restore＋migrate，確認合成 Activity Type 標記、私人測試附件內容及三個報表設定完整。
- Bash／JavaScript 語法檢查通過，backend healthcheck healthy。
- 此為本機 Docker Linux 全新安裝演練；未宣稱已在實際 Ubuntu VM 執行，也未替代使用者的瀏覽器驗收。

## 2026-09-15 queue-short 修正

abb1d86 的行內 YAML 未將 `short,default` 加引號，解析後變成兩個參數。映像實測 Bench 5.31.0／Frappe 16.33.0 的 `bench worker --help` 要求逗號分隔的單一字串；正確設定為 `command: [bench, worker, --queue, "short,default"]`。

已部署 abb1d86 且僅 worker 啟動異常的 VM，於 repo 目錄執行：

```bash
git pull --ff-only origin master
bash deploy/deploy.sh repair-workers
bash deploy/deploy.sh status
```

此修正只需套用 Compose，不需重新 build、init 或修改 VM 檔案。repair-workers 讓 Compose 套用 worker 設定，再檢查所有九個常駐服務。保留既有資料庫、附件、密碼與站台。

新安裝及一般 update 現在也會執行穩定性檢查：等待服務 running／已定義的健康檢查通過後，連續觀察 60 秒；任一服務停止、健康檢查失敗或容器重啟／更換則回報失敗。可獨立執行 `bash deploy/deploy.sh verify`。這是啟動檢查，不取代長期監控或實際背景工作驗收。

此修正重新以空白 volumes 建站，並額外投遞 short、default、long 三個背景工作，確認均 finished。Compose 參數回歸測試為 `scripts/test_compose_queues.py`，使用 Docker Compose 實際解析結果檢查 argv。

重新驗證結果：全新部署的 db、redis-cache、redis-queue、backend、websocket、queue-short、queue-long、scheduler、frontend 九個服務，在至少 180 秒觀察期間均 running、RestartCount=0，容器啟動時間未變；DB／backend 的健康檢查為 healthy。三種佇列測試工作均完成（`scripts/test_worker_queues.py`）。這是本機隔離新站的實測，VM 仍需拉取並執行上述修復指令。

## 新站時區

新部署固定初始化 **Frappe System Settings timezone = Asia/Taipei**，並保護首次設定精靈不被 Taiwan 的缺漏時區選項改回 Africa/Abidjan。初始化成功前會列出 `Frappe System Settings timezone -> Asia/Taipei -> PASS`。

既有站台的 build／update／repair 不設定或覆寫時區。已手動修正的 VM 不需重建或重跑 init。[原因與驗證](fresh-site-timezone.md)。
