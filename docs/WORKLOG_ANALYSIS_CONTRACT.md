# rpm_worklog Analysis Contract

## 長期開發完成條件

本契約適用於任何新增或擴充、且會保存使用者工作／管理資料的 DocType，
以及既有分析資料、權限、JOIN、彙總或輸出行為的變更。它不是單次功能備忘錄。
在 PR 提出審查及宣告開發完成前，必須回答下列問題並留下 Analysis impact。
沒有 PR 的修改也須在該批變更說明留下同樣紀錄。

1. 是否具有管理分析價值？說明用途。
2. 應接入既有 Dataset，還是建立另一個明確定義的 Dataset？
   不要求一律放入 `analysis.py`，也不因需要分析就新增持久化 DocType。
3. 分析存取不得超出明確授權的業務讀取範圍；若與原生 DocType 權限不同，
   記錄差異、理由與測試。讀取、審核、編輯及匯出能力須分開判定。
4. JOIN 是否造成資料列或 Hours／Quantity 等數值重複？說明關聯基數、
   去重或預先彙總方式，不能只靠畫面總計看似合理判定。
5. CSV、XLSX、Report、Dashboard 等哪些使用端需要資料？標明需要、
   不需要或尚未實作；不要把未實作寫成已支援。
6. 若不納入分析，留下明確理由；不納入是允許的決策，不能省略判定。
7. 定義 Dataset 粒度（grain）與 aggregation semantics：一列代表什麼、
   識別鍵是什麼、什麼能 SUM、什麼不能 SUM。數量須考慮單位與業務意義，
   母單值不得因子列展開而重複加總。
8. 留下驗證證據：授權／越權、JOIN 前後 row count、數值 reconciliation，
   以及匯出欄位完整性。已填寫的業務值不得因欄位選填或 hidden 而靜默遺失。
   不適用的驗證須說明理由；未驗證須明列，不能標記完成。

### Analysis impact 範本

```text
Analysis impact
──────────────────────────────
用途：
Dataset：
粒度：
權限：
JOIN / 加總規則：
使用端：
驗證：
不納入理由（如適用）：
```

「驗證」應連結測試／結果，並記錄可核對的筆數與數值比較；不要只填 PASS。
本文件是規則及 Dataset 契約的唯一入口；個別變更的判定與結果放在 PR／
該批變更說明，不在多份文件重複維護同一份規則。

## 現有 Dataset：Worklog analysis v1

以下是目前工作列 Dataset 的具體契約，不限制未來其他 Dataset 的粒度或實作位置。

Backend and minimal analytical download UI. No dashboard, Frappe exporter patch, or
transactional schema change. Hours are stored employee-reported input; this
service never derives them from start/end or rewrites historical records.

## Authorization

`analysis.query(scope, filters, offset, page_size)` always uses the current
session. There is no caller-supplied user or company override.

* Self: existing Pilot role, active unique Employee, matching employee AND owner.
* Team: existing Manager Pilot role, active unique manager Employee, current
  active direct reports only, excluding self. Self remains a separate scope.
* Organization: enabled user, RPM Worklog Management role, unique active Employee,
  whose current company equals `site_config.rpm_worklog_company`. That value must
  name an existing Company (operationally 均輝企業股份有限公司; verify its actual
  ERPNext document name before configuration). Missing/invalid settings fail closed.
  Source employees include inactive employees in that company.

All scopes exclude cancelled logs. Organization membership is current
Employee.company, NOT a historical company snapshot. Missing Employee/company
cannot be attributed to this company. Department is the stored Work Log value;
manager is current Employee.reports_to, never historical. No write, review,
Employee administration or native DocType export permission is granted.

## Grain and fields

One child line = one row. Stable keys: work_log + line_id; line_index is ordering
context. Join requires parenttype=RPM Daily Work Log and parentfield=lines.

Parent: work_log, title, work_date, employee, employee_name, department,
review_state, return_reason.

Current Employee context: employee_number, current_company,
current_manager_employee. employee_name is the stored parent value.

Child: line_id, line_index, activity_type, work_item, result, note, hours,
start_time, end_time, quantity, uom, record_quantity, item_code,
item_name_snapshot, item_stock_uom, item_conversion_factor, work_target.

No parent total_hours repeated in detail rows; no audit-event join; no automatic
addition of metadata or linked records. Optional recorded values are retained,
including hidden record_quantity. Null remains null. Dates/times are strings,
numeric values are JSON numbers; serializers must preserve these semantics.

## Filters and paging

Required from_date/to_date (inclusive, maximum 366 days). Optional employee,
department (stored), review_state, activity_type, result, work_target.
Employee and department accept a single legacy string or an array of at most
100 identifiers/values. Duplicates are removed; empty arrays mean no extra filter.
Within each array use OR; across filter fields use AND. The UI stores Employee
document IDs selected through Employee Number/name search, never ambiguous names.
`search_filters` returns up to 20 candidates (+ has_more) from authorized saved
logs independently of date selection. Department candidates use stored values.
Company/role scope is rechecked for candidates, queries and downloads. UI clears
selections on scope change and invalidates results/downloads on selection changes.
Unknown keys, invalid scopes/statuses and malformed pagination are rejected.
Filters only narrow authorized scope. Default All review states includes Draft,
Pending Review, Returned, Approved and any stored legacy states; explicit status
filters accept the four known states. Blank review state normalizes to Draft.

Response: contract_version, scope, filters, columns, rows, total_rows,
total_logs, reported_hours, offset, page_size, has_more. Totals cover the complete
filtered line dataset independently of pagination. total_logs counts distinct
parents with matching lines; a log without lines is not an analytical row.
Order: work_date, work_log, line_index, line_id. Maximum page_size 1000.
Separate requests reflect current data; v1 does not promise an export snapshot
across concurrent edits. Future complete exports must address snapshot consistency
and CSV/XLSX formula-injection escaping at the serializer boundary.

The existing Analytics form now has a 工作明細分析／匯出 button. Its dialog uses
query and analysis_export.download with the same filters and authorization.
Downloads return every matching line in one request (not browser page iteration).
More than 50,000 lines fails explicitly; no silent truncation. CSV has UTF-8 BOM
and prefixes formula-like strings with an apostrophe; XLSX stores strings as
literal string cells and keeps hours/quantity numeric. No Frappe export override.

Existing summary reports/viewers are not rewired in this batch. Consumers
must migrate to this contract before cross-consumer consistency is claimed.
