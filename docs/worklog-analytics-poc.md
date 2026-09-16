# CH-01 工作紀錄報表與圖表：第一版

狀態：已部署於本機 Docker PoC；後端與 HTTP 驗證通過，瀏覽器操作待使用者驗收。

## 入口與操作

- 員工：My Work Logs 列表 → 頁首「工作紀錄報表 / Work Log Analytics」。
- 主管：直屬員工工作紀錄查詢頁 → 頁首同名按鈕。
- 直接入口：http://127.0.0.1:8083/desk/rpm-work-log-analytics/RPM%20Work%20Log%20Analytics
- 選擇報表、範圍、開始／結束日期、審核狀態，再按「查詢報表」。查詢頁不用保存。
- 員工只能使用 Self（本人）；主管使用 Team（直屬員工）。同時具有兩種角色者可選兩個範圍，各自獨立。
- 預設本月與全部審核狀態。要查看已核准工時，請明確選 Approved。所有輸出均顯示實際日期、狀態、範圍及資料筆數。

## 初始設定與調整

三個可修改的範例：Daily Hours（每日工時）、Hours by Employee（各員工工時）、Review Status Distribution（審核狀態分布）。

System Manager／Administrator 可在 `/desk/rpm-work-log-report` 管理 RPM Work Log Report，新增、修改、停用設定。單純系統管理身分不取得跨員工報表資料；請以已綁定的員工／主管帳號查詢。設定頁使用原生表單保存。

| 設定 | 第一版規則 |
|---|---|
| Report Title | 可改顯示名稱；穩定內部 ID 不受改名影響 |
| Data Grain | Log：一張整單；Entry：一列工作內容 |
| Group Field | 主表：work_date、employee、department、review_state；工作列另有 activity_type、item_code、result |
| Operation | Sum、Count、Average |
| Measure Field | Log 使用 total_hours；Entry 使用 hours；Count 留空 |
| Sort Order | Group Ascending 或 Value Descending |
| Chart Type | bar、line、pie（使用原生 Frappe Charts） |
| Default Review Status | All、Draft、Pending Review、Returned、Approved |

例如「按作業分類合計工時」：Entry → activity_type → Sum → hours → bar。查詢仍受登入者權限限制。

平均值為每張或每列的平均工時，不是人均每日工時。Count 明確區分工作紀錄張數與工作列數。員工分組以 Employee ID 識別，不依姓名合併同名員工。

互動篩選為日期、審核狀態及個別直屬員工；尚無任意欄位條件編輯器、公式、跨文件報表或匯出功能。數量、停用 Work Item、單位及敏感文字不開放統計。

## 權限與資料品質

- 伺服器每次檢查啟用 User、唯一 Active Employee 與 Pilot 角色。
- 本人範圍限定 employee 與 owner；直屬範圍限定當下 Reports To 與有效員工。指定員工只縮小範圍，後端重新檢查關係，不能藉偽造 ID 擴大權限。
- 自訂端點提供有限的報表設定摘要；一般員工及主管不能修改設定，也不因此取得原始其他員工文件權限。
- 設定存檔及每次查詢都檢查 metadata 型態、hidden 狀態、靜態欄位允許清單、資料層級及統計相容性。
- 新增欄位需先審查加入目錄；既有欄位改名、停用或型態改變，相關報表報錯，禁止悄悄換欄位。
- 整張彙總不 join 工作列；列彙總只計列工時，禁止重複合計主表工時。
- 完整服務端 GROUP BY，不採主管明細頁的 300 筆截斷。日期最多 366 天；超過 500 個分組報錯，縮小日期後重查。
- 61–500 組提供完整表格但不繪圖；60 組以下提供圖表及完整表格，不用截斷圖表假裝完整統計。
- 取消的 docstatus=2 不納入；無資料明示，不推論缺勤、效率或產量。

## 手動驗收

1. 員工重新載入列表，按「工作紀錄報表」；應見本人範圍，無團隊選項。
2. 日期選 2026-09-01 至 2026-09-30，查每日工時；選一天，與本人該日各張 Total Hours 相加比對。
3. 將狀態從全部改為已核准，確認表格與圖表同步改變；沒有核准資料應顯示無資料。
4. 主管登入，從直屬查詢入口進報表；查各員工工時，確認僅包含其直屬員工。
5. 管理員新增上例「按作業分類合計工時」，一般帳號重開查詢頁後選此報表；核對工作列 hours，不可乘上整張總工時。
6. 確認窄視窗的查詢按鈕、範圍说明、表格與圖表可讀；原生列表欄位挑選與送審維持不變。

## 已執行檢查

`scripts/test_reports_poc.py` 使用回滾資料驗證：301 張本人／302 張團隊完整統計、每單兩列不重複、平均／筆數／狀態篩選、本人與團隊隔離、即時 Reports To 變更、Guest 拒絕、注入字串及不相容／停用欄位拒絕。全部回滾，不留測試紀錄。

實際登入員工與主管的 HTTP 測試：三個報表 200；員工 Team 403；一般帳號報表設定原始資源 403；Guest 被拒絕。JavaScript 語法檢查通過。上述不代替畫面與使用體驗驗收。

## 2026-09-16：真實工號與個別員工篩選

- Team 範圍新增工號／姓名即時搜尋（250ms 延遲），最多 20 個候選；超過時提示縮小搜尋。
- 來源為 Employee.employee_number、employee_name，不改動 Employee.name 或既有關聯。顯示「工號 | 姓名」。未填工號顯示 No employee number，不拿 HR-EMP 代替真實工號。
- 輸入關鍵字後須點選候選，頁面明示已選員工；按「全部直屬員工」清除選擇。切換 Self／Team 清除舊篩選。
- 各員工工時圖表與表格使用相同標籤，內部仍以 Employee ID 分組，同名不合併。若主檔同時重複工號與姓名，請先修正主檔以避免顯示混淆。
- 本批只調整 Analytics 的候選與圖表／表格顯示，其他原生 Employee Link／列表尚未全面更改。
- 已擴充回滾測試：真實工號大小寫搜尋、同名不同工號、指定一人統計、停用／轉主管即時失效、偽造 ID、SQL 字串、萬用字元與 Guest 拒絕。

手動驗收：主管進報表 → Team → 輸入實際工號片段或姓名 → 選候選 → 查詢。核對標頭已選人、表格與圖表，再按全部直屬員工重查。以一般員工確認只有本人範圍；未有真實工號資料時先由管理員填 Employee Number。

本批驗證結果：回滾整合測試 REPORT_TEST_PASS、原報表 HTTP 測試 REPORT_HTTP_PASS、新增 scripts/test_employee_filter_http.py 的 EMPLOYEE_FILTER_HTTP_PASS、JavaScript 語法檢查均通過。本機 8083 已先備份後建置新版映像並 migrate，九個服務皆運行；VM 尚未更新。畫面操作仍待使用者手動驗收。
