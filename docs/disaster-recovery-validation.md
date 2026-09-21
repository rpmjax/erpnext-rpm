# Backup / restore：現有能力與最小災難復原驗證方案

日期：2026-09-21。本文為待執行方案，不是 DR 通過報告；不要求刪除來源站台模擬事故。

## 已有文件與實測範圍

- [SSH 部署手冊](ssh-vm-deploy.md)：備份、更新、回滾原則；記錄早期合成資料、私人附件與報表的局部還原測試。
- [2026-09-17 baseline restore](baseline-restore-2026-09-17.md)：VM 離機備份在隔離站成功 restore/migrate，比對多張資料表 fingerprint；當時附件為空，且不含新 Work Target 功能、登入及完整切換驗收。
- [Hyper-V 上線手冊](ubuntu-hyperv-go-live-runbook.md)：恢復策略與開放前查核，非完整可直接照抄的 restore 指令手冊。
- [第二主機 GCP 驗證](gcp-cyberpanel-deployment-2026-09-21.md)：空白站重建及 HTTPS login 成功，不是有資料站台災難復原。

因此並非「從未測試 restore」，而是尚缺整合、可重複執行、只依離機交付物完成的全流程 DR runbook 與驗收證據。deploy.sh 沒有 restore 子命令。

## 腳本能力核對（625514b3b806）

`backup` 執行 `bench --site ... backup --with-files`，將站台 backups 目錄、site_config.json、deploy.env、running-image.txt 複製至 state_dir/backups/UTC時間，限制備份目錄權限。

實際限制：

- 複製整個站台 backups 目錄，可能混入多個時間批次；restore 必須選擇同一批資料庫／公開附件／私人附件，不按檔案列出順序任意配對。
- running-image.txt 記錄 image tag 和 image ID，不是已保存可在異地拉取的 registry digest 或 image archive。Git commit tag 也不等於完整可重建的位元組鎖定。
- Dockerfile 的上游 ERPNext 使用版本 tag，未鎖 digest；需另外留存實際 image，避免事故時上游不可用或內容差異。
- 未自動產生 checksum/manifest、離機複製、加密備份、保留策略或定期還原驗證。
- 未備份部署 db-password/admin-password、完整主機 proxy/firewall/TLS 設定。fresh DR 可產生新 DB root credential，但必須保留來源 encryption_key；還原後登入以備份資料庫的 User 密碼為準，不是新站 admin-password 檔。
- 單独 backup 不停止應用寫入，不能據此宣稱資料庫與附件在活躍寫入期間為同一時間點；DR 演練應安排維護窗口、排空工作並凍結寫入。
- 沒有保存待處理 Redis 工作的災難復原流程；應先排空佇列，無法排空時記錄待補償工作，而非任意恢復舊 Redis queue 引發重送。
- `init` 只用於 fresh site，遇既有站拒絕覆寫；不是 restore/repair 工具。init 成功會啟動所有九個服務，不能直接拿來還原真實資料而忽略外寄／排程隔離。
- `verify` 是啟動健康與 60 秒無重啟觀察，不驗證登入、業務資料、附件或任務實際完成。

## 最小可驗證 DR 演練

1. **固定來源與驗收基線**：記錄 commit、image ID/digest、Frappe/ERPNext/rpm_worklog 版本、站名、時區；以測試資料準備兩員工、一主管、部門、跨日目標、至少兩列工作紀錄、各審核狀態與公開／私人非空附件。記錄筆數、關聯、工時、附件 hash 及權限矩陣。不把密碼或資料內容寫入 Git。
2. **建立一致備份**：維護窗口停止外部寫入與排程，等背景工作結束；來源維持完整。執行 deploy.sh backup，挑明本次批次；保存來源 encryption_key 與必要 site configuration、程式及部署設定。生成 SHA256 manifest，保存可用的映像 archive 或受控 registry digest。將完整交付物送至 VM 外，驗證可讀與 hash。
3. **模擬來源不可用**：使用另一個空白 VM 或隔離 project/new volumes，還原操作者只使用離機包、文件及映像，不讀來源 volume 或依賴開發機私有腳本。禁止刪除來源資料。低資源 GCP 主機不並行另起完整 DR stack。
4. **隔離目的站**：使用未使用的 loopback port、獨立 project/network/volumes；阻止外寄及外部整合。先只啟動 DB、必要 Redis 與受控 bench runner；不啟動 frontend、worker、scheduler 接受外部操作。核對實際映像 `bench --site SITE restore --help` 後才編寫該環境的逐條命令。
5. **Restore**：先建立隔離目的站所需 DB credentials，還原選定資料庫與同批公開／私人附件；保留目的站 DB 連線設定，只移入來源 encryption_key 及經審核必要設定，不能整份覆寫 source site_config 造成連到舊資料庫。檢查還原後 email mute、scheduler、外部整合仍停用，再以相同版本 migrate。恢復不強制重設來源時區。
6. **資料與功能驗收**：對照下表；以受控測試登入，不能因能開 login page 就標記 PASS。完成後才在隔離環境啟動 worker/scheduler，驗證 short/default/long 實際任務、排程與 WebSocket，並持續阻止外部副作用。
7. **重建／重啟及報告**：保留 volumes 重建容器並重啟目的主機，再驗證資料與登入；記錄復原耗時、備份時間點、可接受資料損失與人工步驟。正式 DNS/入口切換與回復是獨立窗口，不在本演練直接執行。

| 驗收範圍 | 最低通過條件 |
|---|---|
| User / Employee / Department | 筆數、帳號啟用、員工 User 綁定、工號、Reports To 一致 |
| Daily Work Log / Work Entry | 原編號、子列、數量、工時、合計、狀態、審核歷程一致 |
| Work Target | 目標、狀態、工作列關聯及彙總一致 |
| Attachments | 非空公開/私人檔案內容 hash 一致；授權者可讀、未授權者不可讀私人附件 |
| Permissions | 員工本人隔離、主管僅見直屬、一般人不能管理開通、核准後編輯限制符合來源 |
| Settings / secrets | 時區保留；來源加密設定可解密但不輸出值；外寄和整合受控 |
| Runtime | 九服務穩定、實際佇列工作完成、登入/保存/查詢/審核正常、容器與主機重啟後資料保留 |

演練產出：經審核的實際 restore 命令、脫敏 manifest、驗收表、RTO/RPO 實測值與未通過項目。上述步驟尚未執行，不能標記 DR PASS。

## deploy.sh proposed changes（僅建議，未修改）

| Proposed change | 理由 | 風險／限制 |
|---|---|---|
| 唯讀 preflight 子命令 | 彙整 port、disk、RAM、Docker/Compose、設定及資源壓力 | 無法以單一 RAM 門檻保證容量；不自動改 firewall/服務 |
| backup manifest + checksum | 明確標示本批檔案、版本、image identity 及完整性 | 大附件計算耗 I/O；須保持舊備份相容、避免輸出 secrets |
| 可選 image 離機封存 | 降低 registry/上游不可用影響 | 增加空間和傳输時間，不應每次無條件執行 |
| 獨立 restore guard/tool | 檢查目的站隔離、版本、附件、encryption_key 及 side effects | 覆寫資料風險高，先完成手動隔離演練再實作，不併入 init |

本次沒有修改部署 scripts、Worklog 資料模型、permissions 或 UI；不將 CyberPanel/CSF 規則放入通用部署流程。
