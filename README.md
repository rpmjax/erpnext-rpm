# ERPNext RPM

以 Frappe / ERPNext + rpm_worklog 提供個人工作紀錄、直屬主管審核、跨日工作目標與報表。使用獨立 Docker Compose；CyberPanel 不是必要元件。

## 五分鐘接手

1. **[目前位置與安全下一步](docs/PROJECT_STATUS.md)**：發布、候選、各環境最後觀测與未完成事項。
2. **[唯一部署／更新操作程序](docs/ssh-vm-deploy.md)**：盤點、備份、固定版本、build、update、verify 與失敗處理。
3. **[備份還原缺口與演練方案](docs/disaster-recovery-validation.md)**：不把新站重建當成完整 DR。

不由 README、branch 名稱或本機 Git 推定 VM 已更新。狀態頁中的環境版本都是帶來源的最後觀測，不是即時監控。

## 開發與文件規則

- 變更程式在 `apps/rpm_worklog`；部署工具在 `deploy`；驗證腳本在 `scripts`。
- 每批提交留下版本、驗證範圍、未完成事項及下一步；更新狀態頁後 push。只有發布決策確認後才建立不可移動的 release tag。
- 日期進度／交付文件是歷史證據，不是另一套更新程序。既有版本紀錄由 Git 保存。
- 不提交帳密、site_config、真實資料備份或私人附件。
- 資料模型與權限不因介面簡化而放寬；不直接修改 Frappe / ERPNext 核心。

需求與延期決策見 [backlog](docs/requirements-backlog.md)；早期架構背景見 [ADR-001](docs/adr-001-work-log-model.md)。
