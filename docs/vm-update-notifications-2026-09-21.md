# 通知與目標刪除版本：既有 VM 更新（2026-09-21）

> 文件定位（2026-09-22）：下列為歷史需求／交付／驗證紀錄，當時狀態及命令不代表目前狀態。唯一現況見 [PROJECT_STATUS](PROJECT_STATUS.md)；更新 VM 只依 [操作程序](ssh-vm-deploy.md)。

固定版本標籤：release/worklog-2026-09-21。適用已完成初始化的站台；不是 fresh init 或完整 DR。功能差異與隔離升級證據見 [候選驗證](release-candidate-2026-09-21.md)。GCP 資源有限，安排低流量維護窗口，逐條執行，失敗即停；不並行 build/update。

## Hyper-V：以 paskadmin 執行

```bash
cd ~/src/erpnext-rpm
export RPM_STATE_DIR=/home/paskadmin/.config/rpm-worklog-vm
```

## GCP：以 paskcoltd 執行

```bash
cd /opt/erpnext-rpm
export RPM_STATE_DIR=/home/paskcoltd/.config/rpm-worklog-gcp
```

## 共用步驟（在已選定的 VM 執行）

```bash
# 確認工作目錄乾淨；若有輸出先停，不丟棄修改。
git status --short
bash deploy/deploy.sh status
bash deploy/deploy.sh backup
```

將備份複製到 VM 外受控位置；記錄原 commit、running-image.txt 和備份批次。確認可用磁碟、RAM/swap 及維護窗口後再繼續。

```bash
git fetch origin --tags
git switch --detach release/worklog-2026-09-21
git log -1 --oneline
bash deploy/deploy.sh build
bash deploy/deploy.sh update
bash deploy/deploy.sh status
```

使用標籤固定本次程式版本；detached HEAD 是預期狀態，之後更新另選經驗收版本，不在此狀態直接 git pull。deploy.sh build 會依目前 commit 產生映像；主機自行 build 不保證與本地候選 image ID 完全相同。

update 會再備份、migrate、啟動九服務及觀察 60 秒。migrate 必須完成，否則資料庫中的 Client Script 可能仍為舊版。不要 configure/init，不改主機 DB/Redis、防火牆或反向代理；GCP 維持 127.0.0.1:8085。

## 驗收與回復

- 原帳號登入，原工作紀錄/目標及附件仍在；時區未改。
- 員工送審後，主管通知可直達對應唯讀明細並核准/退回；本人收到結果通知。通知屬站內通知，不寄 email。
- 本人可刪未關聯目標；有關聯目標被阻擋，非本人不可刪。
- 請強制重新載入瀏覽器取得新 Client Script；既有未開通角色不會自動變成已開通。
- 失敗保留 logs 與維護狀態，不反覆 init。先保存事故後資料，以對應備份與映像在隔離環境還原；不要只切回 Git 版本就宣稱回復完成。

本機 HTTP/login/ping 和 Guest 拒絕不是正式 VM 登入驗收。完整離機災難復原、正式負載、GCP WebSocket/TLS renewal 驗證仍依 [DR 文件](disaster-recovery-validation.md) 另行安排。
