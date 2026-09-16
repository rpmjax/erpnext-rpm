# VM 內網入口切換：192.168.0.70

目標：既有 Ubuntu Nginx 的 HTTP 80 → 127.0.0.1:8085 → Docker frontend → 新 Work Log。
不重建站台、不搬資料、不改時區、不停止舊站資料庫。新舊站資料互不合併。
本流程不處理外網／DNS／HTTPS。不要把 8085 改成 0.0.0.0。

## 目前狀態

已備妥 deploy/nginx-worklog-lan.conf；尚未套用 VM。2026-09-16 非互動 SSH 認證被拒，尚未取得 VM 有效 Nginx 設定。
不能根據舊站網址猜測設定檔名稱，不能直接關閉全部 sites-enabled 或刪除舊 Bench。

## 1. 先取得唯讀資訊

Windows 執行 `ssh paskadmin@192.168.0.70`，進入 Ubuntu 後：

```bash
cd ~/src/erpnext-rpm
git pull --ff-only origin master
bash deploy/deploy.sh status
grep -E '^(RPM_SITE|RPM_BIND_IP|RPM_PORT|RPM_IMAGE)=' ~/.config/rpm-worklog-vm/deploy.env
sudo ss -ltnp | grep -E ':(80|443|8085)\b'
sudo nginx -t
sudo nginx -T 2>&1 | grep -E '^# configuration file|listen |server_name |proxy_pass |upstream |include '
ls -l /etc/nginx/sites-enabled /etc/nginx/conf.d
curl -sS -I http://127.0.0.1:8085/login
curl -sS -I http://192.168.0.70/login
```

上述輸出用來決定實際需要停用的舊站檔案。若 80 由 Docker 或其他服務持有，停止此 Nginx 流程，另行規劃，不執行停機猜測。
需要檢視完整 nginx -T 時，在 VM 本地閱讀；分享前刪除任何認證標頭或私人資訊。

## 2. 準備切換（已確認現行設定後）

1. 先透過 tunnel 驗收新版公司、人員、工作紀錄、主管報表與權限。
2. 若需更新程式，先 build／update 並通過 verify。切換入口本身不用 build 或 init。
3. 維護時段執行 `bash deploy/deploy.sh backup`，將備份另存 VM 外。
4. 建立 Nginx 備份：

```bash
cutover_backup="/var/backups/rpm-nginx-$(date +%Y%m%d-%H%M%S)"
sudo mkdir -m 700 "$cutover_backup"
sudo cp -a /etc/nginx "$cutover_backup/"
sudo sh -c 'nginx -T > "$1/effective-before.txt" 2>&1' sh "$cutover_backup"
printf 'Rollback backup: %s\n' "$cutover_backup"
```

若 sites-enabled 指向 /etc/nginx 以外的 Bench 生成檔，保留該目標並另存其副本；只移除入口連結，不修改生成檔內容。

## 3. 套用（檔案位置必須先核對）

將 repo 範本安裝至 `/etc/nginx/sites-available/rpm-worklog-lan.conf`，並在 sites-enabled 建立連結。
僅停用已確認與 192.168.0.70:80 衝突的舊站入口，記錄原連結或檔案位置以便復原。
若舊 server 同時供其他站台使用，需另行調整其 server_name，不可整份停用。

```bash
sudo install -m 644 deploy/nginx-worklog-lan.conf /etc/nginx/sites-available/rpm-worklog-lan.conf
# 完成已核對的舊入口停用與新連結建立後：
sudo nginx -t && sudo systemctl reload nginx
```

這裡刻意不提供猜測舊檔案名稱的 rm 指令。nginx -t 的 duplicate/conflicting server name 警告也必須處理，不能只看 exit code。
Docker frontend 已由 FRAPPE_SITE_NAME_HEADER 固定路由至 RPM_SITE，外部 Host 維持 192.168.0.70。所有路徑包含 socket.io、assets、files 都轉交 Docker frontend。

## 4. 切換驗收

```bash
curl -sS -I http://192.168.0.70/login
curl -fsS http://192.168.0.70/api/method/ping
bash deploy/deploy.sh verify
```

應出現 `X-RPM-Worklog-Gateway: lan` 與正常 ping；標頭僅確認經過新代理，不證明應用版本。
從另一台公司電腦不用 tunnel 開 http://192.168.0.70：重新登入、查看新站既有紀錄、保存測試草稿、主管工號搜尋、附件上下載及通知連線。
瀏覽器 Network 的 socket.io WebSocket 應可取得 101。確認一般員工不能讀取他人資料。
如果 VM 本機可用而其他電腦不通，先檢查 Ubuntu 防火牆及 Hyper-V 網路，再針對公司網段開放 80；不要停用整個防火牆。

## 5. 回復

移除本次新增的 rpm-worklog-lan.conf 啟用連結，恢復本次停用的舊入口連結／檔案（依步驟 2 備份）。
執行 `sudo nginx -t && sudo systemctl reload nginx`，再次確認舊站可達。
Docker 新站保持運行且資料保留，仍可透過 SSH tunnel 的 8085 驗收；回復入口不會把新站交易搬回舊站。
不要用清除 volumes、重建站台或重新初始化作為回復手段。

驗證：範本放入隔離的 events/http 測試設定，於本機 Docker frontend 執行 nginx -t 通過，沒有 reload 本機服務。此為語法驗證，VM 路由、WebSocket 與登入仍須依上述步驟驗收。
