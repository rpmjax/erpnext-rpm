# rpm-erpnext VM 操作與搬移

## 2026-09-07 實機盤點

| 項目 | 實測 |
|---|---|
| Hyper-V VM 名稱 | 使用者提供：rpm-erpnext；Windows 管理查詢權限不足，未能核對 VM 設定 |
| 客體 hostname | erpnext |
| 作業系統 | Ubuntu 26.04.1 LTS / Linux 7.0.0-30-generic |
| CPU／記憶體 | 4 vCPU／約 7.2 GiB |
| 根磁碟 | 約 61 GiB；啟動服務前約 47 GiB 可用 |
| IP | 192.168.0.70/24，eth0，Netplan 已停用 DHCP |
| Gateway／DNS | 192.168.0.254／168.95.1.1 |
| SSH 使用者 | paskadmin；密碼不納入 repo |
| Bench 位置 | /home/paskadmin/frappe-bench |
| Bench 版本 | 5.31.0 |
| ERPNext | 16.34.1，version-16，0b50853 |
| Frappe | 16.33.0，version-16，33bf510 |
| Python／Node | 3.14.4／24.20.0 |
| MariaDB | 11.8.6 |
| 既有站台 | erpnext.local；已完成 setup；zh-TW／Asia/Taipei |
| 既有資料 | 1 Company、1 Employee、0 Timesheet；未輸出其姓名或公司內容 |

ERPNext 工作目錄原有 `banking/yarn.lock` 修改，已保留。此次未升級或重裝 ERPNext / Frappe。

## 服務

補上 Nginx + Supervisor，透過 Bench 產生設定。Nginx、Supervisor、MariaDB 設為開機啟動。Supervisor 管理網頁、Socket.IO、兩個 Redis、排程及長／短工作佇列共七個程序。Gunicorn 設為三個 worker。

Nginx 設定使用 `combined` log format。透過 ACL 僅允許 www-data 穿越使用者家目錄以讀取公開資源，未將整個家目錄改成公開可讀。套件預設 Nginx 站台 symlink 留存為 `/etc/nginx/sites-available/default.disabled-link`。

可重現的設定程序：[setup-native-services.sh](../scripts/setup-native-services.sh)。僅適用已有可用 Bench 的本機原生安裝，不是空白 Ubuntu 的 ERPNext 安裝器；執行會重新產生 Nginx / Supervisor 設定。

```bash
cd /home/paskadmin/frappe-bench
sudo supervisorctl status
bench doctor
sudo nginx -t
systemctl is-enabled nginx supervisor mariadb
curl -I http://127.0.0.1/login
```

設定檔位置：

- `frappe-bench/config/nginx.conf` → `/etc/nginx/conf.d/frappe-bench.conf`
- `frappe-bench/config/supervisor.conf` → `/etc/supervisor/conf.d/frappe-bench.conf`
- `/etc/netplan/00-installer-config.yaml`（本次只讀，未修改）

已在 2026-09-07 03:44 UTC 實際重新啟動 Ubuntu，確認 boot ID 改變；重新登入後 Nginx、Supervisor、MariaDB 均 active、兩個 worker 上線，兩站登入頁均 HTTP 200，固定 IP 維持不變。這驗證客體內部服務恢復，尚未驗證遠端 Hyper-V 主機重啟後的 VM 自動啟動。

## 備份

既有站台已成功執行 `bench --site erpnext.local backup --with-files`，備份時間標記 `20260907_112925`，包含資料庫、站台設定、公開及私人附件。檔案在 VM 的 `sites/erpnext.local/private/backups/`。本次服務設定前的 common config 在 `/home/paskadmin/rpm-ops-backups/20260907/`。

這是 VM 內備份，尚不等於離機備援，也尚未驗證還原。

```bash
cd /home/paskadmin/frappe-bench
bench --site erpnext.local backup --with-files
# 測試站建立後亦需獨立備份
bench --site rpm-test.local backup --with-files
```

搬移前將備份及其站台設定／加密金鑰保存到受控的 VM 外位置；勿上傳到公開 GitHub repo。

## 測試站

已建立 `rpm-test.local`，入口為 `http://192.168.0.70:8080`。與 `erpnext.local` 資料庫、設定與附件分開，但程式碼、Redis、工作程序與 VM 共用。程式更新可能同時影響兩站，正式上線前須另作環境隔離決策。

測試公司為合成資料 `RPM Test Company`，幣別 TWD，語言 zh-TW，時區 Asia/Taipei；無測試員工與工時資料。已完成初始設定、管理員登入與 Desk HTTP 驗證。測試站設定 `mute_emails: true`。

Administrator 使用新產生的隨機密碼，不沿用 OS 密碼，亦未改動原站台的任何登入密碼。密碼僅存在 VM 的 `/home/paskadmin/.config/rpm-erpnext/test-site-admin.txt`（600 權限）及開發機 repo 目錄下被 Git 忽略的 `.local/test-site-admin.txt`。不要加入版本控制。

建置程序使用 [create_test_site.py](../scripts/create_test_site.py) 與 [initialize_test_site.py](../scripts/initialize_test_site.py)。前者需要 `sudo -v`，透過暫時資料庫管理帳號建立新站，finally 移除該帳號；實測結束確認暫時帳號數為零。不覆寫現有站台；若中途失敗，先盤點殘留狀態，不要使用 `--force`。

```bash
cd /home/paskadmin/frappe-bench
sudo -v
env/bin/python /path/to/erpnext-rpm/scripts/create_test_site.py
bench --site rpm-test.local set-config mute_emails True --parse
env/bin/python /path/to/erpnext-rpm/scripts/initialize_test_site.py
bench --site rpm-test.local set-config host_name http://192.168.0.70:8080
bench set-nginx-port rpm-test.local 8080
# 上一行會詢問覆寫 Nginx 設定，確認是此 Bench 後回答 y。
bench setup nginx --yes --log_format combined
sudo nginx -t && sudo systemctl reload nginx
```

測試站完整備份時間標記為 `20260907_114306`，包含資料庫、設定及附件，位於 `sites/rpm-test.local/private/backups/`。

## 遠端 Hyper-V 搬移清單

1. 確認遠端主機的 Hyper-V 版本、可用 CPU／記憶體／磁碟、外部虛擬交換器與 VLAN。
2. 確認目的網段可用 `192.168.0.70/24`、Gateway `192.168.0.254`、DNS `168.95.1.1`，並在 DHCP 範圍排除或保留此 IP；IP 設定成功不等於已完成 DHCP 保留。
3. 完成各站台備份及離機副本，在維護窗口停止寫入並正常關閉 VM，再 Export／搬移／Import。保留可回復的原 VM。
4. 目的 VM 網卡接到正確的外部交換器；如網卡名稱不再是 eth0，於主控台先調整 Netplan。遠端網路不同時不可盲目沿用此固定 IP。
5. 同一網段不可同時啟動兩份使用 `192.168.0.70` 的 VM。原 VM 保持關機後，再啟動目的 VM。
6. 驗證 SSH、各站台登入、CSS／JS、Socket.IO、Supervisor 全部 RUNNING、背景工作與排程，及資料／附件可讀。
7. 明確設定 Hyper-V VM 的自動啟動與關機動作，這與 Ubuntu 內部服務開機啟動是兩個層次。
8. 正式上線前決定正式 DNS／HTTPS、正式與測試環境隔離、定期離機備份及還原演練，再開放員工使用。

目前只啟用區網 HTTP，未設定公網網域、HTTPS、遠端 Hyper-V 或跨主機搬移。上述項目不能標示為已驗收。
