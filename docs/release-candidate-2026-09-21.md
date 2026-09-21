# 候選版本差異與既有站升級驗證（2026-09-21）

範圍：相較正式部署基準 625514b，候選功能為 0ae6306。僅本地驗證，尚未發布 master 或更新 GCP/Hyper-V。

## 功能差異

- 344c27b：本人可刪除未被工作列關聯的目標；已有關聯（含取消紀錄）禁止刪除，使用鎖定避免關聯與刪除競爭。
- 26fa818：送審/重新送審通知主管、核准/退回通知本人；交易內建立站內通知、避免重複，不寄信。
- 7138d66 / 0ae6306：通知直接載入指定紀錄唯讀明細與原審核操作；支援 route_options，新增資料庫 Client Script 部署一致性檢查。使用者已回報操作確認、體感可接受。
- 其他提交為 GCP/DR 文件與翻譯待辦；不是新 UI 或自動翻譯。
- 自動刷新低優先級；數量進度、完成率、自動結案繼續延期。

## 本輪執行與證據界線

使用先前保留的 rpm-worklog-release-check / vm-release-check.internal，沒有公開 frontend port，網路 internal，無 worker/scheduler 執行。本次啟動保留的舊 backend 容器（其 review.py 尚無 notify_review），以原 volumes 作既有站。此環境源於 9/17 VM 備份、已經過前次版本升級，不宣稱是本次由 625514b 精確重建或完整 DR。

在舊容器加入隔離測試目標與公開/私人非空附件，保存 before fingerprint，再以目前本地候選 image 重建 backend、migrate，核對：

- UPGRADE_PRESERVATION_PASS：Company、Department、User、Employee、Daily Work Log、Work Log Line、Review Event、Work Target、File、User Permission、Has Role、__Auth、時區與 4 個非空附件檔案內容保持一致。
- RESTORED_SITE_FEATURE_SMOKE_PASS：本人新增目標/工作列，時間換算、目標工時彙總與關聯明細通過；交易 rollback。
- NOTIFICATIONS_PASS：送審、退回、重新送審、核准通知對象及連結、重複抑制、批次略過、交易回滾、他人通知隔離與不寄信通過；精確讀取及失去直屬關係後不回傳通過。
- TEAM_VIEWER_DEPLOYMENT_PASS：資料庫啟用的 Client Script 與映像 source 完全一致。
- 測試後再跑 preservation PASS，確認臨時角色/主管關係與資料均 rollback；停止本輪四個服務，保留 volumes。

通知測試最初套用 8086 帳號假設而遇未開通角色；enroll 又正確拒絕未確認的舊 User Permission 調整。改用隔離交易內臨時測試角色和主管關係後通過，未更改正式資料，也未改通用開通規則。

## 尚待發布階段

本輪不是新一輪九服務穩定性、瀏覽器登入、私人附件 HTTP 授權、負載或完整 DR 驗證。__Auth 相同證明密碼資料保留，不等於完成實際登入測試。發布前應固定候選映像身份，補九服務/HTTP驗收，並準備 VM 更新指示。不得直接讓 VM pull 開發分支當成已發布版本。

可重用檢查：scripts/test_upgrade_preservation.py（硬性限定隔離站，before 會建立測試 fixture）；scripts/test_team_viewer_deployment.py。通知測試適配版存於 ignored .local/vm-release-check/notifications.py；migration log 位於同目錄 upgrade-20260921.log。不得提交備份/帳密/私人資料。

## 發布補驗

候選 app image 固定為 rpm-worklog-vm:61e9698-candidate，image ID sha256:063cc9b152c4ccd33be00d33117a7f3a39109375eb8987b1dcffefe95fbd4c08。此為已測 app 原始碼映像，後續提交只新增測試與文件；未宣稱此 image 在 61e9698 重新 build。

HTTP 經隔離 Docker frontend 驗證：/login 200 且包含登入頁內容、/api/method/ping 回 pong、Guest 存取主管查詢被拒（401/403）。使用內部網路，未開公開埠。VM 操作者仍須驗證實際帳號登入與域名路徑。

固定版本更新手冊：[VM 更新](vm-update-notifications-2026-09-21.md)。

九服務至少 60 秒觀察通過：均 running、RestartCount=0、啟動時間不變，DB/backend healthy。驗證後停止隔離 project，保留 volumes。此為啟動穩定性，非負載或任務完成驗證。
