# 第二主機部署驗證：GCP / CyberPanel（2026-09-21）

## 結論與證據範圍

目前 Docker 化方案具備跨主機重新部署的可行性，已由第二個實際環境驗證成功；但尚不能稱為完全無人值守的一鍵部署，也尚未完成完整 backup → disaster recovery → restore 演練。

本紀錄的 GCP 結果來自操作人提供的實測紀錄；本次文件整理未重新登入 GCP 或重跑部署。程式核對基準為 `625514b3b806` 的 `deploy/deploy.sh`、`deploy/compose.yaml`、`deploy/init_site.py` 和 `docker/Dockerfile.worklog`。8086 開發分支的新功能與未通過驗收的通知導向，不包含在此版本驗證中。

CyberPanel 是這次主機的入口管理方式，不是應用程式依賴。正式架構仍可採獨立 Linux VM + Docker + 適當的 HTTPS 反向代理。

## 環境與版本

| 項目 | 實測環境 |
|---|---|
| Host | GCP、Ubuntu 22.04.5、1 vCPU、約 1.9 GiB RAM、4 GiB swap |
| 既有服務 | CyberPanel / OpenLiteSpeed、host MariaDB / Redis、其他網站 |
| Docker / Compose | 29.1.3 / v2 2.40.3 |
| Repository / user | `/opt/erpnext-rpm` / `paskcoltd`；repository 不在 public_html |
| Commit / image | `625514b3b806` / `rpm-worklog-vm:625514b3b806` |
| 部署設定 | `/home/paskcoltd/.config/rpm-worklog-gcp` |

```dotenv
RPM_PROJECT=rpm-worklog-gcp
RPM_SITE=worklog.pask.com.tw
RPM_BIND_IP=127.0.0.1
RPM_PORT=8085
RPM_STATE_DIR=/home/paskcoltd/.config/rpm-worklog-gcp
RPM_IMAGE=rpm-worklog-vm:625514b3b806
```

後續操作使用 paskcoltd，且每次新 SSH session 都需指定此 state directory；否則腳本預設讀取另一個 `~/.config/rpm-worklog-vm`。

```bash
cd /opt/erpnext-rpm
export RPM_STATE_DIR=/home/paskcoltd/.config/rpm-worklog-gcp
bash deploy/deploy.sh status
```

無須替 Linux 部署帳號設定密碼；root 可切換帳號，主機防火牆和代理管理才使用管理權限。

## 各層責任與已驗證事項

| 層次 | 本次結果及責任 |
|---|---|
| Application / containers | Git clone、image build、configure/build/init/status、新建空白 site、Frappe/ERPNext/rpm_worklog 安裝成功 |
| Container isolation | frontend、backend、db、redis-cache、redis-queue、queue-short、queue-long、scheduler、websocket 共九個服務正常運作；db/Redis 為獨立容器，未借用主機服務 |
| Persistence | Compose 具 sites/logs/db-data/redis-data volumes；架構存在不等於資料復原已驗證 |
| Host prerequisites | Docker、Compose、部署者存取權、資源、DNS、主機防火牆須另外處理；低記憶體主機避免平行 build/init |
| Reverse proxy / TLS | 既有 OpenLiteSpeed 80/443 → 127.0.0.1:8085 → Docker frontend → Frappe；外部 HTTPS 瀏覽器可進 login page |
| Exposure | frontend 僅 bind loopback；資料庫及 Redis 無 host published ports |
| Backup / restore | 本次為 fresh deployment，沒有完成有資料站台的完整災難復原測試 |

這部 1 vCPU / 1.9 GiB VM 的成功只證明部署/staging 可行性，不能推論正式容量、長期穩定性或並發效能已足夠。正式 sizing 應另測。

## Host-specific：CSF OUTPUT 阻擋 Docker bridge

CyberPanel UI 沒有 CSF 管理頁，不代表 CSF 已移除。本次 CSF 14.24 仍存在、lfd.service active，INPUT/OUTPUT/FORWARD policy 為 DROP。TCP_OUT whitelist 未容許容器 TCP/8080、DOCKER=0，CSF 預設 Docker network 指向 docker0 / 172.17.0.0/16，而此 Compose bridge 實際是 172.18.0.0/16。

現象與定位順序：

1. 容器內 frontend:8080 回應 HTTP 200：應用入口可用。
2. 主機到當時容器 172.18.0.10:8080 被拒絕。
3. 主機到 127.0.0.1:8085 reset / empty reply，但 docker-proxy 正常存在。
4. 比對 OUTPUT 規則及命中計數，定位主機到容器的連線被阻擋；不是直接將原因歸為 Frappe、nginx 或 Compose。

唯讀診斷（在本次 GCP 主機，以部署者執行 Docker，管理者執行 firewall 檢查）：

```bash
cd /opt/erpnext-rpm
export RPM_STATE_DIR=/home/paskcoltd/.config/rpm-worklog-gcp
docker compose --env-file "$RPM_STATE_DIR/deploy.env" -p rpm-worklog-gcp -f deploy/compose.yaml ps -a
docker network ls --filter label=com.docker.compose.project=rpm-worklog-gcp
# 從上一行取得 network 名稱後，使用 docker network inspect 實際名稱
curl --max-time 10 -I -H 'Host: worklog.pask.com.tw' http://127.0.0.1:8085/
```

```bash
# root：只讀，不 reload 或清空規則
systemctl is-active lfd
csf -v
iptables -S OUTPUT
iptables -L OUTPUT -n -v --line-numbers
iptables -S FORWARD
grep -E '^(DOCKER|TCP_OUT)' /etc/csf/csf.conf
```

本次操作人回報：允許目的地 `172.18.0.0/16`、TCP destination port `8080`，透過 CSF hook 持久化，CSF reload 後仍見：

```text
ACCEPT tcp -- 0.0.0.0/0 172.18.0.0/16 tcp dpt:8080
```

隨後 loopback curl 回應 `HTTP/1.1 200 OK`、`X-Page-Name: login`，確認此網路路徑恢復。

這是本次主機 workaround，不是通用安裝指令。不得把 172.18.0.0/16 或容器 IP 硬編進 deploy.sh；新建網路可能改變。實際 hook 路徑、完整內容與原始規則備份未附於本次紀錄，應補存於受控主機維運紀錄。不可因部署而清空 firewall、改全域 ACCEPT、直接套 DOCKER=1 或全面開放 TCP_OUT。變更前須確認作用範圍及既有其他容器，reload/reboot 後需另驗持久性；本次僅回報 reload 通過。

## Reverse proxy 與憑證

本次僅調整 `/usr/local/lsws/conf/vhosts/worklog.pask.com.tw/vhost.conf`，保留 CyberPanel vhost/SSL 設定，新增 backend `127.0.0.1:8085`，並保留 `/.well-known/acme-challenge`。未替換全域 listeners 或其他網站。HTTPS 仍由 CyberPanel/OpenLiteSpeed + Let's Encrypt 負責。

完整 vhost diff 應在主機受控備存；本文不以未取得的設定內容拼湊可直接套用範本。公開 login page 成功不等於 Socket.IO/WebSocket、附件上傳、登入 session、HTTPS redirect、快取隔離或實際憑證 renewal 已驗證。這些需各自驗收。

## 後續

- [通用部署指令](ssh-vm-deploy.md)
- [備份／還原缺口與最小 DR 驗證方案](disaster-recovery-validation.md)
- 通知導向問題維持開發待辦，本紀錄不宣稱修復。
