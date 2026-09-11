# 資料規則開發與手動驗收

日期：2026-09-11。伺服器自動測試 PASS；瀏覽器操作由使用者手動驗收，尚待回報。

## 已實作

- 同員工同日多張、重複 Title 均允許；編號識別紀錄，不加每日唯一鍵。
- Before Validate 原生 Server Script：Title／工作內容不可只含空白，至少一列，結果限既有選項。
- 每列工時 > 0 且 <= 24，單張合計 <= 24；8 小時不是上限。伺服器覆算 total_hours。
- 記錄數量 checkbox 區分零產出與不計量；勾選時須單位，非零數量或單位會自動視為計量；負數拒絕。
- Employee 必須對應登入者（Administrator 保留管理能力）；Department、Employee Name 依主檔重取，覆蓋 API 偽造值。
- 列表加入 Employee Name、Department、Total Hours，保留日期、Employee、Title 與原生 ID；實際畫面排列待手動驗收。
- 每張表單提示本人所選日期的已保存張數與總工時；修改保存、切換日期、重開時重新查詢。每日總量不儲存在各張文件，避免其他單的快取總量過期。
- API 依 session 查 Employee，忽略外部傳入 employee，使用有權限的 get_list；Guest 拒絕。彙總只含本人有權存取的紀錄，不涵蓋管理員代建但未授權的單。
- 每日 > 24 小時橘色提醒，不做跨張硬限制／併發鎖定。其他分頁保存後需重載，目前沒有即時跨頁推送。

## 實作範圍與部署

只在隔離 Docker Bench 以 bench set-config -g server_script_enabled 1 啟用原生 Server Script；此版本要求 common_site_config，作用於本 Docker Bench，沒有更改原 VM 或安裝 App／修改 Core／重啟服務。未向員工授予 Script Manager。

worklog_rules/ 保存事件驗證、本人彙總 API 與前端提示。將目錄複製到容器 /tmp/worklog_rules，再於已標記 frontend site 的 Administrator bench console 執行 scripts/configure_worklog_rules_poc.py。

設定腳本新增欄位、更新命名腳本，回填既有單總工時與姓名、計量標記；不刪單、不合併、不改原始工時及數量，回填保留 modified。既有 00005、00006、00007 有數量缺單位，已保留，後續保存須補齊；不宣稱歷史資料全數合法。

scripts/test_worklog_rules_poc.py 在兩位員工權限下測試相同標題多張、多列覆算、日期移動與每日查詢、非法輸入與跨人讀取隔離；測試交易最後 rollback，不留下測試單。另以兩個 HTTP session 驗證 API 200 與 Guest 拒絕。未代替人工介面驗收。

## 手動步驟

1. 試辦員工重新整理 /desk，進入我的工作紀錄並新增一張；Title 填「檢查測試」，日期選測試日。
2. 第一列填工作內容、Completed、1.25 小時，不勾記錄數量且不填單位。第二列填工作內容、Completed、0.75 小時，勾記錄數量、填 5、選 PoC Piece。保存：總工時應為 2。
3. 同日期同 Title 再建一張 1 小時，應成功。提示的每日總量應比開始測試前增加 3 小時、2 張。
4. 第一張改成總工時 3，保存後每日合計再增加 1。將第二張改到其他日期保存，查原日期時合計應減少 1。
5. 分別試空白 Title、空白工作內容、零或負工時、負數量、勾計量但不填單位：應阻擋保存。修正後能存。
6. 計量勾選、數量 0、有單位應可存；不計量則取消勾選、數量清空、單位清空。
7. 重開紀錄確認總工時；返回列表確認日期、姓名、部門、Title、總工時及編號可辨識。另一位員工仍不能開啟你的單。
8. 既有 00005–00007 如需修改，先補單位再保存。不要為通過測試任意刪除原有數量。

尚未實作主管授權／審核與同單退回。若擴大人員範圍、增加管理員代填或公司級每日彙總，需另驗證授權語意。原 Employee User Permission 仍生效。
