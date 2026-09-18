# VM 更新：跨日工作目標第一版（2026-09-18）

本次將已驗收的開發內容提供至 master，沿用既有 worklog.internal 站台、資料卷、帳號與內部入口 http://192.168.0.70。
不搬入 8086 測試資料或測試密碼；數量進度、多人共用目標、自動結案不在此版本。

## 包含內容
- 姓／名與真實工號顯示，共用本人／直屬主管讀取範圍。
- 個人跨日工作目標、工作列選填關聯、關聯工時及審核狀態彙整。
- 工作列表格直接選目標、雙向快速導覽、主管唯讀工作紀錄明細。
- 選填開始／結束時間；完整同日時間換算工時，不完整保留手填值。
- 主管查詢卡片樣式；保留原審核流程。

## 升級前演練
- 從離機備份 20260917_144522-worklog_internal 還原到全新隔離 project rpm-worklog-release-check。
- 未使用／覆寫 production VM、8086 或原 baseline restore 的資料卷；無發布埠、內部網路、郵件靜音及停用排程。
- 新版 migrate 成功。比對既有欄位的資料指紋，Company 1、Department 14、User 35、Employee 32、Item 1、Work Log 1、Work Log Line 2、Review Event 0 均一致。
- 帳號驗證資料 __Auth 指紋一致；System Settings 時區維持 Asia/Taipei。
- 以還原帳號執行 rollback-only 測試：建立目標、時間換算、工作列關聯、目標彙整與唯讀明細通過。
- 原始還原驗證程式遇本機工作目錄／log 路徑問題；修正驗證程式後從已還原資料繼續，未重設或重建站台。
- 備份附件無一般檔案，因此不宣稱驗證了非空附件。備份為 9/17 時點，不代表目前 VM 全部資料。

## 在 Windows 開啟 SSH

```powershell
ssh paskadmin@192.168.0.70
```

## 以下在 Ubuntu SSH 執行

安排短暫維護時間。先確認沒有未保存的填寫；更新期間入口會暫停。

```bash
bash -e <<'SH'
cd ~/src/erpnext-rpm
if [ "$(git branch --show-current)" != master ]; then
  echo '目前不是 master，請停止並核對分支。'; exit 1
fi
if [ -n "$(git status --porcelain)" ]; then
  echo '工作目錄有修改，請停止並核對；不要強制 reset。'; exit 1
fi
bash deploy/deploy.sh backup
git pull --ff-only origin master
git log -1 --oneline
bash deploy/deploy.sh build
bash deploy/deploy.sh update
bash deploy/deploy.sh status
SH
```

update 會再於維護期間備份，再 migrate，成功後啟動九個服務並觀察 60 秒。
請保留备份路徑，複製到 VM 外受控位置。更新使用既有設定，不執行 configure 或 init，也不重設帳號密碼。
既有 Nginx 入口不需改動；更新後仍使用 http://192.168.0.70。

## 更新後驗收
1. 確認出現 SERVICES_STABLE，九個服務包含 queue-short 正常；記錄 git commit 與執行映像。
2. 員工原帳號登入，原紀錄可讀；側欄可見跨日工作目標。若無新欄位，先保存後強制重新載入。
3. 新增草稿可手填工時；09:00–10:30 換算為 1.5 小時；關聯目標後目標頁可查。
4. 主管只能看直屬資料，原送審／退回／核准流程仍正常。
5. System Settings 原時區應保留；此 VM 預期仍是 Asia/Taipei。

## 若更新失敗
保留終端輸出，執行 bash deploy/deploy.sh logs 蒐集錯誤。
不要 init、刪除資料卷或自行關閉維護模式；失敗時腳本刻意保留維護狀態。
若需回復舊版，先備存事故時資料，再用更新前資料庫／附件／site_config 與對應舊映像於隔離環境還原核對。
只 git checkout 舊版不等於資料回復；baseline/worklog-before-target-2026-09-17 標籤仍保留。

本文件描述已準備的更新方式；未代替使用者在正式 VM 執行，也不宣稱正式站已更新。

服務啟動驗證補充：九個常駐服務連續 60 秒 running、RestartCount=0，啟動時間未變；DB/backend healthcheck 正常。演練結束後停止該隔離 project，保留資料卷；不影響 8086。
