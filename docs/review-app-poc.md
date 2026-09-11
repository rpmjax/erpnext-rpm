# RPM Work Log App：審核 PoC

2026-09-11。使用者已授權 C／Custom App，名稱 rpm_worklog；中文顯示使用翻譯，既有 DocType 與 RWL 編號保留。已部署本地 Docker，伺服器／HTTP 測試通過，人工瀏覽器驗收待使用者執行。

## 行為

Draft → Pending Review → Approved；Pending Review → Returned → Pending Review。

- 保存與送審分開。同日多張與重複 Title 繼續允許。
- 員工僅能送審自己的有效紀錄，需有有效已啟用且配置試辦角色的直屬主管。
- 待審、已核准禁止透過原單保存修改內容，包括 Administrator 的正常表單保存。狀態不可由一般 REST PUT 自行改寫。
- 核准／退回 API 重新檢查目前 Reports To 與主管角色；不得核准自己。沒有同部門或遞迴下屬授權。
- 退回須非空白原因，最多 2000 字。補正仍同編號；重送清除本次退回欄位，但歷程保留原原因。
- 審核使用非 submittable 自訂 review_state，不用 ERPNext submit/cancel/amend，也不改 docstatus。
- 狀態更新以資料庫列鎖串行化，要求 expected_modified；過期畫面與重複核准拒絕，不靜默覆蓋。
- 審核事件與狀態同一交易。RPM Work Log Review Event 記錄前後狀態、動作、操作者、時間、原因；一般客戶端無寫入權，正常 save/delete hook 禁止改歷程。資料庫管理員直改 DB 不在應用層防護範圍。
- 經歷審核的單禁止刪除。已核准更正、撤回送審、代理主管、通知與簽核附件不在本輪範圍。

## 結構與遷移

apps/rpm_worklog 為可安裝 Frappe App；仍依賴本 repo 已建的 Custom DocTypes 與試辦角色，尚非空白站一鍵部署產品。review.py 是伺服器鎖定與動作 API；rules.py 封裝既有資料規則。setup.install 可重跑：新增狀態／退回欄位、審核事件 DocType、Client Scripts；停用原 RPM Work Log Validation Server Script，由 App hook 接手。原本人／主管查詢 API Server Scripts 仍保留，主管回傳另加狀態與 modified。

既有所有單初始化為 Draft，沒有代送審或代核准；有歷史數量缺單位的單仍須補正才可送審。沒有刪除、合併或重編工作單。

員工表單提供 Send for Review／Review History；主管查閱頁待審單提供 Approve／Return for Correction 與歷程，查詢、返回首頁、黃色圖示保留。常用審核字串存 translations/zh-TW.csv；實際語系顯示仍待人工核對。

## 部署與備份

Dockerfile：docker/Dockerfile.worklog，映像 rpm-worklog-poc:0.1.0，基於 ERPNext v16.34.1。App 與 pip 安裝封裝於映像，不是只複製到可消失的容器層。建置隔離僅引入 flit build backend；無新的業務 runtime dependency。

本地 .local/worklog-poc/compose.yaml 已改用此映像；公開 override 為 docker/worklog-app.override.yaml。Sites／DB 原 named volumes 保留。不要以舊原版 image recreate 已裝 App 的站台。

首次部署：build image → 更新 backend／workers／scheduler／frontend／websocket → 確認 sites/apps.txt 包含 rpm_worklog → bench --site frontend install-app rpm_worklog。後續更新：重建 image 並 recreate 相同服務 → bench --site frontend execute rpm_worklog.setup.install（或 migrate）。程式／設定僅允許已標記 rpm_worklog_model_poc 的 frontend。前端 upstream 容器 IP 改變時需重啟本地 frontend；本次已處理並確認登入頁恢復 200。

安裝前備份位於 site private/backups，前綴 20260911_155020-frontend，包含資料庫、public/private files 與 site config。需要完整回退時，以此備份搭配先前映像及本地 compose-before-app.yaml 復原；不能只刪 App 或只重新啟用舊 Server Script 來當作安全回退。帳密、備份與原始人員資料不提交 Git。

## 自動驗證

scripts/test_review_poc.py：草稿保存 → 送審 → 鎖定 → 退回原因 → 同單修改重送 → 核准；驗證四筆不可修改的歷程。測試交易最後 rollback，沒有留下測試單或審核事件。

拒絕案例：直接改 review_state、鎖定後改內容、其他員工讀歷程／核准、空白退回原因、過期版本、重複核准、刪已審單、修改歷程。已使用列鎖，但尚未做大量平行請求壓力測試。

既有資料規則與主管動態直屬查閱測試再次 PASS。獨立 HTTP session 驗證原生資源 PUT 狀態偽造遭拒且原單未變、本人 history API 可用、GET 不可觸發審核動作、Guest 被拒。瀏覽器未由 agent 代操作。

## 使用者手動驗收

先 Ctrl+Shift+R；若語系或按鈕快取仍舊，登出再登入。員工與主管維持兩個獨立視窗。

1. 員工：建立或選一張合法草稿，補齊單位、保存。應顯示 Draft／草稿。
2. 按 Send for Review／送審並確認。應變 Pending Review／待審，工作內容不能再保存修改。
3. 主管：直屬員工工作紀錄 → 選涵蓋該日期的範圍 → 查詢 → 展開該單。待審单應有核准與退回按鈕。
4. 按 Return for Correction／退回修改，填原因。空白不可送出。
5. 員工重開同一 RWL 編號，應見 Returned／退回修改及原因。修改、保存、重新送審。
6. 主管重新查詢，按 Approve／核准並確認。員工重開應為 Approved／已核准且不可修改。
7. 點 Review History／審核歷程，應依序看到送審、退回、重送、核准，含操作者、時間與退回原因。

請回報每個步驟結果及失敗訊息，不需提供密碼。此輪人工驗收通過後再討論核准後更正及通知。
