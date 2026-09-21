# Ubuntu／Hyper-V 正式上線操作手冊

> 狀態註記（2026-09-21）：本文為早期規劃快照，第 4、11 節的未完成描述不代表目前部署套件狀態。部署套件已完成，第二主機空白部署也已通過；最新事實見 [GCP 驗證紀錄](gcp-cyberpanel-deployment-2026-09-21.md)，完整 DR 仍待 [專項驗證](disaster-recovery-validation.md)。以下保留歷史規劃供追溯。

日期：2026-09-15。更新：獨立站部署套件已完成本機全新安裝與還原演練，請依 [SSH VM 部署指令](ssh-vm-deploy.md) 執行；VM 安裝、HTTPS 與切換尚未執行。以下前置事項保留作為正式上線查核。

## 1. 部署選擇與範圍

建議路線：Ubuntu VM 上使用獨立 Docker Compose 正式環境，搭配獨立資料庫、Redis、站台與附件 volumes，延續目前 Docker 驗證方式。先演練，再搬至目標 Hyper-V 主機，最後開放員工。

既有原生 Bench 的 erpnext.local／rpm-test.local 暫時保留；不可共用資料庫或把原生站台覆蓋成 Docker 測試站。若要把工作紀錄直接裝入既有原生站台，需另行選定此路線並驗證同 Bench 兩站的影響。

官方 Frappe 建議容器化生產部署；frappe_docker 的 pwd.yml 為一次性示範用途，不能直接複製目前測試配置當正式配置。[Frappe production](https://docs.frappe.io/framework/user/en/bench/guides/setup-production)、[Docker 部署選擇](https://github.com/frappe/frappe_docker/blob/main/docs/01-getting-started/01-choosing-a-deployment-method.md)。

建議正式入口採公司 DNS 名稱與 HTTPS。192.168.0.70 是目前 VM 位址，只有目標網段允許且無衝突時才能保留。正式 DNS 名稱、目標主機與備份位置尚待填入。

## 2. 開始前填寫的部署紀錄

| 項目 | 目前／需決定 |
|---|---|
| VM／登入 | rpm-erpnext；paskadmin；192.168.0.70（需重新核對） |
| 目標 Hyper-V 主機、交換器、VLAN | 待填 |
| Ubuntu 版本、CPU、RAM、磁碟 | 重新盤點；歷史資料不能當本次檢查結果 |
| 正式 DNS、站台名稱、HTTPS 憑證方式 | 待填；內網可使用受信任的公司 CA |
| 資料來源 | 建議全新正式站匯入核准主資料；不得預設全部 PoC 紀錄正式化 |
| 發布版本 | 待選經驗收 commit＋映像 digest；不用 latest 或可覆寫的 PoC 標籤 |
| 停機窗口／執行者／驗收者／回滾決策者 | 待填 |
| 備份目的地、保留期限、復原目標 | 待填；建議先以每日離機備份、最多損失一天資料、4 小時內復原為討論基準，非已承諾 SLA |

## 3. 先做 SSH 唯讀盤點

Windows 終端：

```powershell
ssh paskadmin@192.168.0.70
```

核對首次 SSH 指紋，互動輸入密碼。Ubuntu 內執行：

```bash
hostnamectl
cat /etc/os-release
ip -br addr
ip route
free -h
df -h
timedatectl
ss -lnt
command -v docker
command -v bench
```

如 Docker 已安裝，再檢查 `docker version`、`docker compose version`、`docker ps`。有權限錯誤先確認管理方式，不任意擴大權限。若使用既有 Bench，於 `/home/paskadmin/frappe-bench` 核對 `bench version` 與各站 `bench --site erpnext.local list-apps`、`bench --site rpm-test.local list-apps`。

確認 Ubuntu 版本符合 Docker 官方支援清單，再安排套件安裝；不要在未知版本上直接執行安裝腳本。[Docker Ubuntu 安裝與防火牆注意事項](https://docs.docker.com/engine/install/ubuntu/)。

通過條件：目標 VM、IP、版本、資源與埠使用情況均有紀錄；沒有使用舊站的 80／443／8080 埠啟動另一套服務。RAM 與磁碟需留足新舊環境並行、映像、資料庫與至少一次完整備份的空間；以實測負载核定，不宣稱固定規格必定足夠。

## 4. 必須先完成的程式交付

目前此 repo 還不是可直接在空白站台安裝的正式套件。以下為部署前必要開發工作：

- 將 RPM Daily Work Log、子表、審核歷程、查詢頁、報表設定及入口完整納入可重複執行的安裝／migration。
- 處理 setup.py 對 frontend、rpm_worklog_model_poc、已存在 Server Script／DocType 的依賴，改為明確的新站初始化與既有站升級路徑；不能只刪除 assert。
- 將權限角色、本人限制、Reports To 查詢及腳本遷移納入版本管理。全新站及既有資料站各驗證一次，重跑不覆蓋管理者的報表設定／翻譯。
- 將 PoC Server Script 依賴遷移或明確封裝，避免正式站臨時開啟廣泛腳本執行權限。
- 提供正式 Compose、必要環境變數範例、健康檢查、站台初始化及遷移命令。現有 docker/worklog-app.override.yaml 不是完整 Compose。
- 建置包含 apps/rpm_worklog 的固定映像，记录 ERPNext、Frappe、App commit 與 digest；本 repo 根目錄不是直接可供 bench get-app 的 App 根目錄。
- 驗證首次安裝、升級失敗、資料還原與舊版恢復。

真實工號搜尋／顯示仍是另項待辦；需列入上線驗收範圍或由使用者明確接受延期，不能標成已完成。

通過條件：在全新隔離站由 Git 交付物完成重建，不依靠開發機私有腳本、密碼或手動殘留配置。目前独立 managed 新站的安裝／migration／還原演練已通過；既有原生站移植仍不在套件範圍。

## 5. 建置隔離候選環境

完成第 4 節後，由部署套件提供逐條命令，順序如下：

1. SSH 拉取 repo，確認工作目錄乾淨，fetch 後選定已验收的 release commit；不在正式執行目錄直接追蹤 master 自動升級。
2. 建立獨立 Compose project、網路及持久 volumes。資料庫、Redis 不對公司網路或公網發布埠。
3. 將正式秘密放在受控部署目錄或秘密管理系統；不沿用 PoC 的 admin／測試密碼，不進 Git。
4. 拉取或離線載入固定 digest 的映像；檢查映像包含 rpm_worklog 與預期版本。
5. 建立正式候選站，安裝 App、執行 migration；初期關閉外寄通知與外部整合，限制只有管理／驗收者可訪問。
6. 配置 HTTPS 與站台 Host routing、反向代理的 WebSocket、附件路徑。初期候選 frontend 綁 loopback 的未使用埠，用 SSH tunnel 驗收；不能只依賴 UFW 假設 Docker 埠未暴露。
7. 正式入口如沿用目前 Ubuntu 反向代理，應安排獨立 vhost 修改與設定測試，保留原站路由。這屬後續部署變更，本次未執行。

不得現在執行不存在的部署指令或套用舊 scripts/setup-native-services.sh 來準備 Docker；該舊腳本會重建原生 Nginx／Supervisor 配置。

## 6. 主資料、帳號與備份

建議正式站只匯入經核准的 Company、Department、Designation、User、Employee、Reports To、Activity Type 及需要的 Item。依依賴順序匯入並核對筆數、唯一使用者綁定、真實工號與主管關係。測試工作紀錄、合成物料及測試密碼不自動帶入。

如需保留既有正式交易資料，先在隔離還原副本驗證 App 安裝；不可把 Docker PoC 全庫直接還原覆蓋原站。是否保留 PoC 工作紀錄需另列資料清單。

備份包需包含資料庫、公開／私人附件、必要站台設定與 encryption_key、對應程式版本及部署設定。備份加密金鑰另行受控保存，站台設定含秘密，不上傳 repo。

在已確認的既有原生站台，可於維護計畫內建立備份：

```bash
cd /home/paskadmin/frappe-bench
bench --site erpnext.local backup --with-files
bench --site rpm-test.local backup --with-files
```

將完成的備份複製至 VM 外受控目的地，核對大小與雜湊。必須在隔離站實際還原，驗證登入、附件、加密欄位與資料筆數。恢復時依選定 Frappe 版本的 restore 命令及站台設定處理，不把不同版本資料庫盲目降版。[官方 backup](https://docs.frappe.io/framework/user/en/bench/reference/backup)、[官方 restore](https://docs.frappe.io/framework/user/en/bench/reference/restore)。

## 7. 正式開放前驗收

| 測項 | 通過條件 |
|---|---|
| 員工登入 | 正式帳號可進；測試共用密碼停用或已更換 |
| 組織與工號 | 真實員工、部門、主管映射正確；工號需求的交付／延期已明確 |
| 本人隔離 | 列表、直接網址、API 均不能讀寫他人工作紀錄 |
| 審核 | 整單送審、批次送審、退回原因、同編號補正、核准鎖定、歷程正確 |
| 主管隔離 | 只見當下直屬；改 Reports To 後立即失去原範圍；不可自行修改員工內容 |
| 報表 | 工時與原單相符、日期／狀態清楚、無 HTML 字串、無跨員工洩漏 |
| 介面 | 桌面入口、窄畫面、中文翻譯及員工操作由使用者手動驗收 |
| 系統 | HTTPS、靜態資源、Socket.IO、佇列、排程與附件存取正常 |
| 恢復 | Ubuntu 重啟後服務恢復；離機備份可還原，記錄耗時 |
| 負載 | 以預計同時使用人數演練保存及查詢，無錯誤或資源耗盡 |

不得將目前僅兩位員工／一位主管的 Pilot 角色開放狀態當作全員已可用；正式人員需逐批賦予最低必要權限。

## 8. 搬移至目標 Hyper-V 主機

建議先完成候選環境驗收，再於正式開放前搬 VM，避免一邊搬主機一邊接受新工作紀錄。

1. 核對目標主機 VM 相容性、磁碟、記憶體、外部虛擬交換器、VLAN、DNS、網關及固定 IP 可用性。
2. 冻結候選資料寫入，完成最終應用備份與 VM 外副本；正常關閉 Ubuntu。
3. 使用 Hyper-V Export／Import 搬移。匯入時選定註冊／還原／複製模式並記錄 VM ID 與實際存放位置，不僅複製正在使用的 VHDX。
4. 來源 VM 保持關機，目的 VM 接正確交換器；同網段不能同時啟動相同 IP 的兩份 VM。
5. 從 Hyper-V 主控台核對網卡名稱與網路，必要時按目的網段調整 Netplan；恢復 SSH 後再檢查服務。
6. 核對 Hyper-V 自動啟動／正常關機設定，以及 Ubuntu Docker 與容器重啟策略；這些是不同層次。
7. 重跑第 7 節關鍵驗收，確認目標機備份仍送往 VM 外位置。

Microsoft 的匯出／匯入程序見[官方說明](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/deploy/export-and-import-virtual-machines)。

## 9. 正式切換

1. 登記發布 commit、映像 digest、備份時間、驗收結果及值班聯絡方式。
2. 如有來源資料仍在變動，先停止寫入並處理排程／佇列，再做最終一致資料搬移與比對；遷移期間不讓新舊站雙寫。
3. 在約定窗口切換 DNS／反向代理正式入口至已驗收候選站，驗證 HTTPS、登入及附件。
4. 由一位員工、一位主管各完成一筆受控驗證，再分批開放。通知使用者正式網址與開始填寫日期。
5. 按需求啟用排程、外寄郵件與必要整合；確認不重送測試通知。
6. 觀察錯誤率、佇列、磁碟與備份。正式資料開始寫入的時間要記錄，供回滾判斷。

## 10. 回滾與日後更新

觸發回滾：資料隔離失效、無法保存／審核、資料損壞、主要入口不可用且無法在維護窗口修復。權限洩漏時先停止開放。

- 未開始正式寫入：將入口切回原站／維護頁，保留失敗環境供查核，使用相符程式與備份復原。
- 已有正式新資料：先停止新站寫入，保存事故時資料庫與附件；核對切換後新增／修改／審核事件。由決策者選擇修復或遷移差異後回復，不能直接回舊快照丟失工作紀錄。
- 資料庫 schema 已 migration：單純切回舊映像未必相容；使用已演練的「舊映像＋同時間資料庫／附件／設定」還原方案。
- 不以 git reset、刪 volumes、bench reinstall 或原地降版作為回滾捷徑；Hyper-V checkpoint 不是離機應用備份替代品。

日後更新：新版本 → 隔離演練 → 備份 → 維護窗口 → 更新固定映像／migration → 冒煙驗收 → 開放；Git pull 僅取得程式，不自動更新執行中的服務。

## 11. 執行狀態

- [x] 正式上線步驟文件與資料／回滾策略已準備。
- [ ] VM 本次 SSH 盤點。
- [x] 獨立站可重現安裝與部署套件（本機驗證；VM 待驗）。
- [ ] 正式 DNS／備份目的地／上線窗口確認。
- [ ] 隔離站部署、資料匯入及還原演練。
- [ ] 使用者手動驗收。
- [ ] 遠端 Hyper-V 搬移與目標主機重驗。
- [ ] 正式切換。

下一個實作工作為第 4 節：完成可重現的 App 安裝／遷移與正式部署套件。文件準備完成不代表以上未勾選項目已執行。
