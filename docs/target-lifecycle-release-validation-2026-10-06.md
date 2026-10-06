# Target lifecycle 完整 image 驗證（2026-10-06）

應用候選 `2c6b022`，分支 `codex/work-target-lifecycle`。從該提交的 git archive 建置；
image `rpm-worklog-vm:2c6b022`，實際 image ID
`sha256:6c9b25edc4b4cdbca61f727dfe01562807ca80506c881e6a54cc550a28854e89`。
後續文件提交不改應用候選。未 push／merge，未更新 8086、Hyper-V 或 GCP。

## 結果

| 驗證 | 結果／範圍 |
|---|---|
| 新站 | PASS：configure → init，analysis-fresh.internal，loopback 8095 |
| 既有站 | PASS：21ae5b5ec051 → backup → 2c6b022 update/migrate → verify，analysis-upgrade.internal，loopback 8092 |
| 服務 | 兩站九服務穩定性檢查 PASS，觀察期內無重啟，健康檢查通過 |
| Apps | frappe 16.33.0、erpnext 16.34.1、rpm_worklog 0.1.0 均已安裝 |
| HTTP | 兩站 GET /（指定 site Host）均 200；本輪未重做互動登入 |
| 資料完整性 | 既有站完整指紋一致：Company、Department、User、Employee、Log、Line、Target、Review Event、User Permission、Has Role、File、認證、時區及 public/private 附件內容 |
| 分析／設定 | test_analysis_release.py check PASS，包含 analysis／settings suite 與 Client Script 內容一致性 |
| Lifecycle | 新站與更新站皆 PASS：既有關聯保存、新關聯拒絕、重開、legacy、主管唯讀及 admin 無業務繞過 |
| Migration | 新 image 上合成 Open／Closed／Archived，installer 連跑兩次 PASS；不猜測狀態，只補 legacy flag；Log／Line／Review Event 指紋一致 |
| 欄位標籤 | 既有站 DocField 確認「關聯單號（選填）」 |

測試僅匯入 image 內應用程式，未覆蓋 candidate app 檔案。新站先用
`test_analysis_release.py seed` 建立 5 名合成員工、1 張 8.4h Log、2 工作列及 2 附件，
再執行 before/check。既有站沿用隔離合成資料並於更新前保存 before 指紋。
Lifecycle 更新站測試只將測試 script 的固定 site 名改為 analysis-upgrade.internal，
業務断言未改；測試交易 rollback。

完整 update 的原始 Target 集合由全表指紋檢查；legacy 三狀態補值另以合成資料重跑
installer 驗證。這不是正式業務資料的更新／備份還原演練，也不代表完整 DR 通過。

## 操作證據與可重跑方式

WSL Docker，候選 archive 解壓位置：
`/home/ps00010/.local/state/rpm-target-lifecycle-20261006/repo`。

- 新站 state：`/home/ps00010/.local/state/rpm-target-lifecycle-20261006/fresh`。
- 更新站 state：`/home/ps00010/.local/state/rpm-analysis-check-20261001/upgrade`。
- 更新前備份：上述 upgrade 的 `backups/20261006T005403Z`；update 內停服務後備份：`backups/20261006T005816Z`。含 DB、public/private files、site config 與 image 紀錄；不提交 secrets。
- 實際流程使用候選 `deploy/deploy.sh configure/init/backup/update`，非直接改 DB 模擬更新。
- 將 repository 的 `test_analysis_release.py`、`test_analysis_poc.py`、`test_worklog_settings_poc.py` 複製至測試 backend `/tmp/`；在 bench `sites` 目錄以絕對路徑 `env/bin/python` 執行 release script 的 SITE before/check。
- 新站另執行 `test_target_lifecycle.py`、`test_target_lifecycle_migration.py`。不可對正式站執行合成資料 seed／migration 測試。

首次啟動既有隔離站時 DB 尚未就緒，before 讀取失敗；尚未 backup/update。
DB 就緒後完整重跑成功。未放寬指紋比對。相對 Python 路徑引發 sys.prefix 警告，測試仍通過；重跑宜用絕對 env 路徑。
停止服務依原程序每服務最多等待 120 秒，測試耗時不代表 migration 卡住。

## 下一步與限制

使用者已回報本地操作驗收。此批可準備發布候選分支與 VM 交接，VM 更新仍只依
[唯一操作程序](ssh-vm-deploy.md) 重新盤點並備份，不能從本次隔離結果宣稱 VM 已更新。
新 Completed 與獨立封存語意不能直接交給舊程式處理；rollback 必須評估資料相容性，
需要還原時使用配套備份，不只切回舊 image。
Calendar 僅 backlog；公司 Target 分析與 Daily Work Log archive/delete 不在本批。
