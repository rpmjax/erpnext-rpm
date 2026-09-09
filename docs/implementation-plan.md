# 技術路線與驗證

> 2026-09-09 後續更新：先依 [ADR-001](adr-001-work-log-model.md) 決定 Timesheet／Daily Work Log 模型，再依 [新版驗收](next-poc-acceptance.md) 推進。先前直接補 Timesheet 欄位的順序不再是預設路線；禁止 Custom App、Core／服務變更的限制仍有效。以下內容保留為歷史規劃，實測見 [原 PoC 計畫](work-log-poc-plan-2026-09-09.md)。

## 已知與待確認

2026-09-07 初始 repo 無提交。後續已連線使用者提供的 Hyper-V VM，確認既有 ERPNext 16.34.1 / Frappe 16.33.0 安裝，啟用服務並新增 rpm-test.local 測試站。詳見 [VM 操作紀錄](vm-operations.md)。

使用者已指定 ERPNext 及「員工每日工作紀錄」用途、VM 名 rpm-erpnext、固定 IP 192.168.0.70，並說明安裝後會搬至遠端主機。研究報告中的公司名稱、30～50 人、六部門、預算與試辦時程均為參考，尚未逐項確認。

## 路線選擇

| 路線 | 適用條件 | 需實測的缺口 |
|---|---|---|
| 原生 Timesheet 加少量客製 | 起訖時間輸入可接受；此版本已驗證 Employee 可留白 | 結果欄位、每日唯一、主管範圍、Workflow、繁中入口、User 身分與資料權限 |
| 獨立 Frappe Daily Work Log App | 希望直接填小時、以 User 登入身分管理，或原生流程明顯增加負擔 | 自訂主子表、權限、狀態機、統計及升級維護 |

目前尚未選定。獨立 App 是備選實作路線，並非先重建 ERPNext。兩條路線都必須滿足 MVP 權限及驗收要求。

## 原生 Timesheet 驗證步驟

1. 記錄測試站 URL、ERPNext / Frappe 完整版本、已安裝 Apps、語言與時區；只在測試站操作。
2. 以測試帳號建立最低必要的 Company / Employee / Activity Type。記錄實際必填資料與操作成本，不以假資料填入正式員工主檔。
3. 新增一張 Timesheet，輸入五筆不同工作：2、1.5、0.5、3、1 小時；所有 Project / Task 留白。
4. 記錄是否需要開始／結束時間、是否有重疊限制，確認原生輸入方式是否符合只填工時的需求。
5. 儲存、重新開啟、提交，確認五筆明細保留且合計 8 小時。提交僅驗證原生行為，不視為主管已核准。
6. 記錄新增結果欄位、主管 Workflow 與每日唯一限制的方式；驗證 Workflow 與 docstatus 的對應，避免核准前已無法退回修改。
7. 以員工、指定主管及無關主管分別測試資料可見性；僅有管理員操作成功不算通過。
8. 依驗收清單記錄輸入時間與繁中缺口，再作路線決策。

## 里程碑

- M0（已完成）：初始化 repo 文件、MVP 提案、驗證及驗收清單。
- M1（進行中）：測試站與原生伺服器行為驗證已完成；仍需員工 UI／權限試用後完成技術決策。
- M2：可安裝的客製設定或 App，完成日報、權限、審核與繁中入口。
- M3：報表、手機操作與小規模員工試辦；修正後再擴大使用。

M2 須交付安裝與移除程序、固定的相容版本、資料移轉方式及適當的自動化測試。M3 須實測備份還原與版本升級。實際主機架構及部署命令在取得環境資訊後確定。

## 官方參考

以下為 2026-09-07 查閱的能力參考，不等於目標站台已驗證，亦非特定版本行為保證：

- [Timesheet](https://docs.frappe.io/erpnext/timesheets)：表頭與多列工時模型。
- [Child / Table DocType](https://docs.frappe.io/framework/user/en/basics/doctypes/child-doctype)：自訂主表與明細模型。
- [Workflows](https://docs.frappe.io/erpnext/workflows)：審核狀態與轉換設定。
