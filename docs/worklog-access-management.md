# 工作紀錄開通管理

管理員入口：首頁「工作紀錄開通管理」，或 `/desk/rpm-work-log-access/RPM%20Work%20Log%20Access`。
僅 Administrator／啟用的 System Manager 可使用，普通 Work Log 主管不具開通權限。

## 操作與驗收

1. 本機 8083 以管理員登入，重新載入，開啟上述入口。
2. 依 Email、姓名或 Username 查詢；每次最多顯示 50 人，超過會提示縮小查詢。
3. 核對工號姓名、員工／主管角色及檢查原因。需唯一 Active Employee 綁定、啟用 System User。
4. 勾選一人或多人，按「開通員工」，確認後逐人顯示結果。已配置者不重複寫入。
5. 需要管理直屬員工時明確按「開通主管」。主管仍依 Reports To 授權，不是全部門權限；需要填本人紀錄則另外開通員工。
6. 使用者登出再登入，確認入口、本人紀錄與主管範圍。
7. 以一般員工／Work Log 主管開啟管理頁或 API，應被拒絕。

既有 Employee User Permission 指向其他員工、範圍旗標不同、預設員工衝突時停止開通，提示人工核對；不刪除或覆寫既有權限。不建立帳號、不修改密碼、不改 Reports To、不撤銷其他角色。
每次有變更的開通，在該 User 的 Comment 留下操作人與模式。SSH enroll 共用同一檢查邏輯。
本版只處理授權開通；離職、撤銷角色、調整既有衝突仍由管理員在原生設定處理。

## 驗證

scripts/test_access_poc.py 在本機 PoC 使用回滾交易驗證 System Manager 操作、批次部分成功、重複操作、角色保留、稽核紀錄、衝突權限、停用帳號、重複員工及普通員工／主管／Guest 拒絕。
JavaScript 語法檢查及本機 migrate 通過，入口與 Client Script 安裝成功。瀏覽器互動由使用者手動驗收。

## VM 更新

本次含 App 程式與新管理頁，不能只 git pull：

```bash
cd ~/src/erpnext-rpm
git pull --ff-only origin master
bash deploy/deploy.sh build &&
bash deploy/deploy.sh update &&
bash deploy/deploy.sh status
```

於維護時段執行，update 會備份及 migrate。既有資料、時區與內網代理維持原設定，不執行 init。
更新後管理員重新登入，開啟 http://192.168.0.70/desk/rpm-work-log-access/RPM%20Work%20Log%20Access 。

實際 HTTP 拒絕測試 scripts/test_access_http.py 通過：一般員工與 Work Log 主管的管理頁讀取、帳號查詢、開通端點均 403，Guest 查詢遭拒。
