# 員工本人工作紀錄 PoC — 2026-09-10

## 結果

本輪指定範圍 PASS：兩位已正確綁定 User 的一般員工可建立、修改及讀取本人紀錄，不能查看或修改對方紀錄。整體產品仍 PARTIAL，主管審核、完整資料規則與全面帳號開放尚未完成。依使用者指示，來源例外不阻擋本輪，也沒有猜配或改寫來源。

僅修改 loopback Docker `erpnext-worklog-poc` 的 frontend site；原 VM 未變更。未建立 Custom App、HRMS 或修改 Core。

## 設定

- RPM Work Log Pilot：僅兩位不同部門且正確綁定的 User。父單原生 read/write/create + if_owner。
- 每位 User 的 Employee User Permission 限定本人，hide_descendants。apply_to_all_doctypes 會同時縮限其他適用的 Employee 關聯文件，不只是工作紀錄。
- Activity Type / UOM 僅授予 select，不授予 read 或主檔管理權。瀏覽器初測發現缺 UOM 選取權，補上後完成保存。
- Client Script 自動帶入 Employee、Department 與預設標題，Employee UI 唯讀。安全限制依靠原生伺服器權限，並非只靠隱藏欄位。
- Workspace：My Work Logs，依試辦角色顯示。入口 `/desk/my-work-logs`。
- 尚未設定全站預設首頁；可直接使用帶 redirect-to 的登入網址。

設定腳本：`scripts/configure_worklog_employee_poc.py`。只接受有 rpm_worklog_model_poc 標記的 frontend site，需本機提供 /tmp/worklog-pilots.json（兩個 User ID）。人員及帳密不納入版本控制。

## 驗收證據

| 測試 | 結果 |
|---|---|
| 實際一般員工 Email 登入 | PASS；本輪不依賴 username 登入 |
| Workspace → My Work Logs → 新增 | PASS，無需搜尋 DocType |
| 本人、部門、日期與標題自動帶入 | PASS，Employee 顯示唯讀 |
| 瀏覽器填列、保存、重新載入 | PASS：RWL-2026-00004，數量 5、PoC Piece、Completed、1 小時保持一致 |
| 兩位員工的伺服器 create/read/write/reload | PASS：RWL-2026-00002、RWL-2026-00003 |
| 對方 read/write 與列表隔離 | PASS |
| 偽造對方 Employee 建單 | PermissionError，PASS |
| 兩個獨立 HTTP 登入 session：本人 GET | 200，PASS |
| 兩個獨立 HTTP 登入 session：對方 GET | 403，PASS；第二位亦無法讀取瀏覽器建立的 00004 |
| 兩個 HTTP session 列表 | 只見本人測試單，PASS |

伺服器測試腳本 `scripts/test_worklog_employee_poc.py` 每次會建立兩張測試單，並不清除既有資料；不要當成可無限重跑的唯讀健康檢查。HTTP 測試使用獨立登入 cookie，沒有把帳密提交 Git。第二位是 HTTP session 驗證，尚未以第二個 Guest Browser 完整量測介面。

瀏覽器實測使用當日 2026-09-10 與合成分類／單位，工作文字為組裝後避震器（登入測試），僅验证登入與保存，不代表重做指定生產部門 2026-09-09 業務案例。

## 試用方式

1. 在同一台電腦的 Guest Browser 開啟 http://127.0.0.1:8083/login?redirect-to=%2Fdesk%2Fmy-work-logs 。
2. 使用本地 `.local/worklog-poc/pilot-login-credentials.json` 中的 email / password；只有這兩位開通本輪角色。
3. My Work Logs 捷徑 → Add RPM Daily Work Log → 填寫工作列 → Save。
4. 返回列表再開啟紀錄，確認內容。

這是流程說明，並非精確逐次點擊量測；分類／單位需選下拉項目，工作列展開操作仍有改善空間。試辦目前可直接修改自己的已保存單，不含主管核准鎖定。

## 待辦與限制

- 主管依 Reports To 的授權、待審鎖定、退回原因及同單補正尚未實作。
- 每日唯一、多列總工時、數量配單位、負數與上限等伺服器規則尚待驗證／實作。
- 部門由前端帶入，本輪未驗證 API 偽造部門；不能把此結果當作全部欄位不可篡改的保證。
- 匯出、報表、分享未授權；附件、其他 API 路徑與多角色疊加未做完整安全稽核。
- if_owner 代表建立者本人；管理員代建即使連到員工，員工也不會自動獲得該單存取權。
- zh-TW 仍有混合翻譯；本輪未匯入翻譯。

下一步先處理資料規則，再做主管與同單補正流程；若需要 Custom App，另做 C 的決策，不以本輪 PASS 取代正式化驗收。
