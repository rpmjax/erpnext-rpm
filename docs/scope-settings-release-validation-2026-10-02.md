# 分析入口與公司設定：候選驗證

## 固定候選

- 分支：`codex/analysis-scope-settings`
- 應用提交：`21ae5b5ec051da95d963fd03ef357bf190a04e6e`
- 映像：`rpm-worklog-vm:21ae5b5ec051`，以該提交 git archive 建置。
- 本地操作：使用者已確認 RPM Worklog Settings 驗收；公司摘要 16 張／37.229h 是當時本地資料觀測。
- 四組 rollback-only regression PASS：analysis、reports、settings、target summary；JS syntax PASS。
- 本批不含工時分支、原生 exporter 修正或審核／刪除／封存流程變更。

## 完整 image 驗證

驗證於獨立 WSL Ubuntu-24.04 Docker daemon；不使用 8086、Hyper-V 或 GCP 資料。
本機證據目錄：`/home/ps00010/.local/state/rpm-scope-settings-20261002`。
Logs 與 secrets／備份留在本機，不提交 Git。

- 完整 build：PASS。
- 舊站更新：2026-10-05 重跑 PASS。`19fe20ac17d5` → `21ae5b5ec051`，
  `analysis-upgrade.internal`，loopback 8092；backup 批次 `20261005T004929Z`。
  migration、九服務穩定性、嚴格完整指紋比對、analysis/settings 測試全部通過。
  設定面板 metadata／Client Script 與映像相符，公司設定保留。
- 新站安裝：PASS，`analysis-fresh.internal`，loopback 8093。九服務穩定性、
  完整 image 的 analysis/settings 測試、DocType 唯讀權限與 Client Script 一致性均通過。
- 映像 ID（WSL daemon）：`sha256:590af9fbd6696f202f5eb2c60e895bc91b79a8db131a898425c0dd9bc8044b9d`。
- HTTP：兩站 Administrator 實際登入及 settings.read 通過；舊站公司保留
  `Analysis Release Fixture`，新站保持未設定（不猜測公司）。

### 2026-10-05：舊站比對失敗原因與重跑

首次更新完成 migration／九服務穩定性，但資料指紋比對失敗。
比對前的 HTTP 登入測試改動了 Administrator 的 `last_active`、`last_login`；
從更新前 SQL 備份載入暫存表，與現有 User 逐欄比對，確認僅此兩欄不同。
其他業務表、認證、附件與時區指紋一致。未略過 User 指紋，未直接修改 User 資料。

WSL 閒置退出後，之前停用 restart 的 DB/Redis 沒有自動啟動，導致後續診斷 DNS 失敗；
只重新啟動隔離 project 的 DB/Redis，並保持本次驗證 session 運作。
重跑使用舊 `19fe20ac17d5` image 與保留的合成測試資料，重新保存指紋後執行
既有 update；將 HTTP 登入排在資料比對完成之後。保留第一次失敗紀錄，不當成 PASS。
這次重跑 DB 已含首次安裝的 Settings metadata；首次 migration 能建立面板的證據
另由首次更新 metadata 核對及全新站安裝測試支持。

## 範圍與操作限制

設定面板沿用 `rpm_worklog_company`，不新增第二份資料庫設定；更新不猜測公司或自動授予角色。
Administrator／System Manager 維護設定；Management 角色本身不足以修改公司。
摘要仍使用原 Report grain／stored hours，明細仍為一工作列、28 欄 CSV/XLSX。

驗證完成後重新測試 HTTP 登入及設定讀取均 PASS，再停止兩個隔離 project，
restart policy 設為 no，保留 volumes／備份。8086 未變更。
`recheck-upgrade.log`、`fresh.log`、`http-final.log` 是本機驗證證據。
未涵蓋正式 VM 更新、負載測試或完整 disaster recovery restore。
下一步為發布候選分支及 VM 更新交接；尚未 push、merge 或更新 VM。
正式更新仍依 [唯一 VM 程序](ssh-vm-deploy.md)。不能把本地操作驗收當成正式 VM 驗證。
