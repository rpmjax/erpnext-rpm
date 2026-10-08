# NAV-01 隔離 image 驗證（2026-10-08）

固定應用候選 `55f0043acf4daf0e6b0b50f38981a1c95103e759`，分支
`codex/nav-target-context`。從 git archive 建置，未覆蓋 image 內應用檔案。
Image：`rpm-worklog-vm:55f0043acf4d`；Docker inspect ID：
`sha256:f5524dd1005d8461e4f661584f6ebaf7c53ba7e158860de808345d03e7667e8f`。

## 驗證範圍

- 新站：WSL Docker project `rpm-nav01-fresh-20261008`，site
  `analysis-fresh.internal`，loopback 8096，執行候選 deploy.sh configure/init。
- 更新站：沿用合成資料 project `rpm-analysis-upgrade-v2-20261001`，site
  `analysis-upgrade.internal`，loopback 8092；從 `rpm-worklog-vm:2c6b022`
  保存資料指紋、backup，再以候選執行 update/migrate。
- 兩站安裝版本：Frappe 16.33.0、ERPNext 16.34.1、rpm_worklog 0.1.0。
- 兩站 deploy.sh 九服務穩定性觀察 PASS：健康檢查通過、期間無重啟。
- 兩站 analysis/settings release checks、lifecycle regression、NAV-01 七項
  側欄選擇測試、targets.js syntax PASS。
- 更新站全表／附件／認證／時區指紋完全一致；沿用
  `scripts/test_analysis_release.py`，未放寬比較。
- 兩站資料庫 `RPM Optional Work Target` Client Script 與 image targets.js
  完全一致，含個人 sidebar 參數；HTTP sidebar.js 與候選檔案完全一致。
- 新站合成資料為 5 員工、1 張 8.4h Log、2 工作列、2 附件；lifecycle
  測試採 rollback。更新站只把 lifecycle 測試 site 名改成隔離更新站。

## 證據位置與限制

WSL 根目錄 `/home/ps00010/.local/state/rpm-nav01-20261008`：
`repo/` 是候選 archive，`fresh/` 是新站設定，`fresh.log`、`backup.log`、
`update.log` 是執行紀錄。設定、密碼及資料備份不提交 repository。
更新站 state 是 `/home/ps00010/.local/state/rpm-analysis-check-20261001/upgrade`；
備份目錄 `backups/20261008T074346Z`，update 停服務後另有
`backups/20261008T074351Z`。這不是正式站還原演練或完整 DR 驗證。

本輪未修改 Local 8086、Hyper-V 或 GCP。未重新進行互動登入／完整瀏覽器矩陣；
本地 NAV-01 使用者驗收見 PROJECT_STATUS。Hyper-V 跨帳號主管圖示 stale
仍為獨立未解問題，不能以本結果宣稱修復。

## 發布交接

後續文件提交不改固定應用候選。發布後仍只依
[唯一 VM 程序](ssh-vm-deploy.md) 盤點、backup、build、update/migrate、verify。
必須跑 migrate 同步資料庫 Client Script，不能只替換 sidebar.js。
VM 驗收包含個人 Log → Target 新分頁、直接開 Target、員工／主管兼員工側欄；
確認原分頁未保存輸入保留、lifecycle 未退步。跨帳號切換需另列結果。

Analysis impact：純導覽；不新增 Dataset 或業務資料，不改分析授權、grain、JOIN、
Hours／Quantity、匯出契約。無新 schema 或資料 migration；仍須既有安裝同步程序。
