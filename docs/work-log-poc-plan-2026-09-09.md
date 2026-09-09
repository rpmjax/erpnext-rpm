# 員工工作紀錄 PoC 結論與修正計畫

日期：2026-09-09。狀態：PARTIAL；本文件為計畫，尚未部署欄位、Workflow 或權限變更。

## 範圍與證據界線

本輪使用瀏覽器操作 192.168.0.70（未帶 8080），以一般員工及使用者切換的管理員帳號檢查。這與 2026-09-07 的管理員後端回滾測試不同；不能將兩者視為完整員工驗收。

本輪以 ERPNext v16 為前提，未重新確認完整 patch 版本。約 31 個 User、31 個已綁 User 的 Employee、5 個 Department 及組織資料為使用者提供的前提，未逐筆盤點。語系後續由使用者切換為 English。

不公開員工姓名、帳號、密碼或個人資料。文件提交不代表授權部署；後續變更前須確認目標站台，不能自行改到另一站。

## 已確認的結論

| 項目 | 結果 |
|---|---|
| 員工建立本人 Timesheet | 成功，自動帶入 Employee 與部門 |
| Project / Task 留白 | 保存並重新讀取成功，未建立任何 Project / Task |
| 工作分類 | 管理員建立 Assembly(組裝) 後，員工可選取 |
| 案例 | 生產管理部員工，2026-09-09，組裝後避震器 5 組，測試工時 1 小時 |
| 保存內容 | 09:00–10:00、Description 工作與數量文字、Completed 勾選均保留 |
| 員工操作權限 | Employee 角色有讀／寫／建立，無 Submit／Cancel／Amend；本機權限畫面已確認 |
| 管理員操作 | 使用者實測 Submit、Cancel；後續唯讀確認原單為 Cancelled，Amend 為按鈕 |
| 結構化數量與單位 | 原生 Timesheet / Timesheet Detail 無對應標準欄位；不是僅未顯示 |
| 三筆紀錄 | 使用者回報後續出現三筆；尚未逐筆核對 Amended From，不可斷言全部屬同一修訂鏈 |
| 本人／直屬主管資料隔離 | 未完成跨帳號驗證；Employee 選單僅見本人不足以證明隔離 |

資料品質屬「Timesheet＋文字說明＋完成勾選」，不是具備可彙總產量的完整 Work Log。Description 可表達 5 組，但無法自然作數值加總；Expected Hrs、Billing Hours、Costing Amount 等不得改作產量。

## 操作成本與友善度

從登入後桌面計算有效操作：

1. Projects。
2. Timesheet。
3. Add Timesheet。
4. 展開明細第 1 行。
5. 在 Activity Type 輸入搜尋文字。
6. 選 Assembly(組裝)。
7. 輸入 From Time。
8. 輸入 Hrs；To Time 自動計算。
9. 輸入 Description。
10. 勾 Completed。
11. Esc 收合明細。
12. Save。

這是實際有效操作整理，非整場探索的純點擊總數；欄位輸入各算一個操作，排除工具重試、管理員準備分類及探索。含帳號、密碼、登入為 15 個操作。首次登入導向無權限 Department 的額外提示另計。員工未完成 Submit，不能把草稿當作送審完成。

員工友善度中：有 Workspace 入口、不必搜尋 DocType，但主要內容需展開填寫。主管友善度低：尚無經驗證的直屬待審入口及產量彙總。狀態友善度低：保存不等於送審，Completed 不等於核准，Cancel 不等於退回。

## 修正階段與交付

| 階段 | 工作 | 驗收與交付 |
|---|---|---|
| P0 現況核對 | 三筆單據的狀態、來源、建立者；User 角色、User Permissions、既存 Workflow／Custom Field | 去識別化證據，辨識有效單與版本；確認實際部署站台 |
| P1 計量 | Timesheet Detail 增加 Completed Quantity（Int 或 Float）、UOM（Link → UOM） | 數量與單位分欄保存並重讀；整數／負數／缺值規則通過 |
| P2 員工畫面 | 優先顯示描述、數量、單位、工時、Completed；提供工作紀錄入口 | 主要填寫不必展開明細或橫向找欄位；重新量測步數與時間 |
| P3 審核 | 建立明確 Workflow、退回原因與操作歷程 | 一般補正不新增單據，待審鎖定，核准才 Submit |
| P4 權限 | 員工本人、授權直屬主管的存取與狀態操作範圍 | 跨部門、直接網址、列表、API、報表、匯出均不可越權 |
| P5 查詢 | 本人紀錄、主管待審、部門明細及歷史版本查詢 | 正式統計只計有效已核准版本，不重複加總主表或取消單 |

P1 的兩欄是計量最低方案，不包含 Workflow 狀態、原因、稽核等可能需要的額外欄位。不要將全站既有 Timesheet 直接套上未評估的必填限制；歷史列不會自動從描述解析產量。

## 計量規則待確認

- 數量記本次新增完成量，避免累計值每天重複加總。
- 支與組不可視為相等；如需換算，先定義按工作項目的換算規則。
- 明確區分完成量與合格量；Completed 並不代表驗收合格。
- 多人合作、返工與分工不得重複計入部門產量。
- 會議與協調等工作可以不計件；哪些分類必填數量須先定義。
- 只計整件可用 Int；需要小數可用 Float。UOM 連結本身不保證自訂數量的整數驗證或自動換算，須另驗證伺服器規則。
- 工作內容暫用 Description；若要可靠地按產品／工作項目統計，需受控項目欄位。已有合適 Item 時再評估連結，不因此強迫新增主檔。
- 新增數量不會自動產生入庫、製造完工或更新原生工時報表。

## 狀態與修訂設計提案

| 業務狀態 | docstatus | 員工修改 | 主管操作 |
|---|---|---|---|
| 草稿 | 0 Draft | 本人可修改 | 依授權查閱 |
| 待審核 | 0 Draft | 不可直接修改 | 核准／附原因退回 |
| 退回補正 | 0 Draft | 本人可修改再送審 | 查閱原因與內容 |
| 已核准 | 1 Submitted | 不可一般修改 | 必要時進入受控更正 |
| 已作廢 | 2 Cancelled | 不可修改原單 | 查歷史／依權限 Amend |

此表為待驗證 Workflow 設計，不是已設定結果。docstatus 0 本身不會鎖定待審內容，須以 Workflow 與伺服器權限確保。不可只改 Submit／Cancel 按鈕名稱。

Completed 是明細工作結果，與審核狀態分開。正常退回保持同一單號；核准後錯誤才 Cancel → Amend。Amend 保存新稿會增加一張關聯單，舊單保留。日常清單排除取消單，但歷史查詢可追溯；修訂稿尚未核准時不得算正式產量。

主管應只處理授權直屬員工；不得因取得主管角色就看全公司。Reports To 不自動證明權限成立。先評估 Configuration；自動直屬（不含間接下屬）若不能滿足，再評估 Permission Query＋文件權限檢查／Small Customization，不以隱藏按鈕替代資料隔離。

## 範圍限制與驗收門檻

本轮為 application-level PoC：不安裝套件／HRMS、不建立 Custom App、不修改 ERPNext Core、不重建 nginx／supervisor 設定、不變更服務、不為測試建立 Project／Task。Custom Field、Workflow 與權限現階段僅提案；不得為通過測試擴大員工權限或弱化需求。

下一輪須由一位員工、一位授權主管及無關部門帳號驗證：記錄 5 支 → 送審 → 退回 → 同單補正 → 核准；核准後一般修改被拒絕；取消／修訂只保留一個有效統計版本；跨部門不可越權。通過後再擴大試辦。原有五筆三分鐘、每日唯一、手機與併發等 MVP 指標仍未驗收，不能以本次一列成功取代。

部署前記錄可回復的設定差異與資料備份安排。回復 Workflow／權限須處理在途單據；不要以刪除數量欄位回復而丟失已填資料。設定匯出與重現方式須另規劃，文件提交不包含自動套用腳本。

## 參考

- [Timesheet Detail v16 標準欄位](https://raw.githubusercontent.com/frappe/erpnext/version-16/erpnext/projects/doctype/timesheet_detail/timesheet_detail.json)
- [Custom Field](https://docs.frappe.io/erpnext/custom-field)
- [Workflows](https://docs.frappe.io/erpnext/workflows)
- [Cancel and Amend](https://docs.frappe.io/erpnext/edit-submitted-document)
- [User Permissions](https://docs.frappe.io/erpnext/user-permissions)

官方能力參考不等於本機已部署或完整驗收。
