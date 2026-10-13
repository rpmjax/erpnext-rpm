# 員工工作時間分布 — 完整 image 驗證

日期：2026-10-13。固定應用候選 `645d81250796a995fc54019d76bf4986f0b9cb5e`，
分支 `codex/employee-work-time-distribution`。包含已本地驗收的工時分布、搜尋／圓餅互動及 Target Link 名稱顯示。

從 git archive 建置，未向容器覆蓋應用模組。
Image `rpm-worklog-vm:645d81250796`，實際 ID
`sha256:47ab3e4c71c68232d80bb68285f94937424276a7a853a3509a2d8ef1ce18a9b7`。
文件提交不改應用候選。

## 環境與結果

| 項目 | 結果 |
|---|---|
| 新站 | 候選 deploy.sh configure/init；WSL project rpm-distribution-fresh-20261013，analysis-fresh.internal，loopback 8097 |
| 更新站 | WSL project rpm-analysis-upgrade-v2-20261001，analysis-upgrade.internal，loopback 8092；55f0043acf4d → backup → 候選 update/migrate |
| 資料完整性 | 更新前後 Company／Department／User／Employee／Log／Line／Target／Review Event／User Permission／Has Role／File、認證、時區及 public/private 附件指紋完全一致 |
| 兩站 release suite | analysis／settings、安裝 apps、唯讀管理角色、資料庫 Analytics Client Script 與 image 原始檔一致 PASS |
| 兩站工時分布 | 1,100 列完整彙總、精確文字分组、Top 5 reconciliation、Self/Team/Organization、8.4h／未分類／零分母等 PASS |
| 兩站 lifecycle | 既有關聯保存、新關聯限制、重開、legacy、主管唯讀 PASS |
| 兩站 UI 程式測試 | preset、render／escaping、候選鍵盤索引及圖表語意 PASS（Node stub，不是 browser） |
| 更新站既有報表 | >300 張資料、Log/Entry grain、Sum/Count/Average、員工搜尋與權限 PASS |
| Target Link | 兩站 title_field=target_name、show_title_field_in_link=1 PASS |
| HTTP | 兩站 GET / 200；本輪未重做互動登入 |
| 服務 | 兩站九服務健康／穩定性觀察 PASS，觀察期間無重啟 |
| 版本 | 兩站 Frappe 16.33.0、ERPNext 16.34.1、rpm_worklog 0.1.0 |

新站 seed 僅建立合成資料：5 員工、1 張 8.4h Log、2 工作列、2 附件。
其餘測試 rollback。更新站測試只將原測試固定 site guard 改為明確的 disposable 更新站，
沒有放寬業務斷言；舊 reports suite 在交易內配置測試角色／Reports To。
首次嘗試更新站測試時 backend 尚未重啟，因此未執行；待重啟後完整測試通過。

## 證據位置

WSL `/home/ps00010/.local/state/rpm-distribution-20261013/`：
`repo/` 候選 archive、`build.log`、`fresh.log`、`backup.log`、`update.log`，新站設定 `fresh/`。
更新站設定 `/home/ps00010/.local/state/rpm-analysis-check-20261001/upgrade/`；
當次備份 `backups/20261013T073645Z`，update 維護期間備份 `backups/20261013T073649Z`。
秘密／原始資料備份不提交 repository。

可重跑測試來源在 scripts/test_analysis_release.py（before/check）、test_analysis_poc.py、
test_worklog_settings_poc.py、test_activity_distribution.py、test_target_lifecycle.py、
test_reports_poc.py、test_activity_distribution_ui.cjs。
只在明確 disposable site 執行，Python 以 bench sites 為 cwd；不在正式業務站 seed。

## 限制與交接

本地主管帳號操作驗收見 [功能紀錄](employee-work-time-distribution-plan.md)。
未新增權限、重算 Hours 或做 schema 擴充；既有更新仍須 migrate 同步 Client Script 與 Target metadata。
未更新 8086／Hyper-V／GCP，尚未 push/merge。這不是完整 DR／負载壓測，也不宣稱所有角色瀏覽器矩陣完成。
後續發布與 VM 更新只依 [唯一操作程序](ssh-vm-deploy.md)，先盤點、當次備份及離機保存。
