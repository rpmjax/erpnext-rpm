# ERPNext RPM

以 ERPNext / Frappe 建立公司的工作管理平台，第一個落地用途為 **員工每日工作紀錄**。

## 目前狀態

兩份後續研究報告已納入 [需求清單](docs/requirements-backlog.md)、[ADR-001 架構決策提案](docs/adr-001-work-log-model.md) 與 [下一輪驗收](docs/next-poc-acceptance.md)。下一步先決定 Timesheet／Daily Work Log 模型，不再預設直接往 Timesheet 加欄位；目前未授權或部署新 DocType／Custom App。

2026-09-09 員工瀏覽器 PoC 結論為 **PARTIAL**：無 Project / Task 可保存本人紀錄，但結構化數量／單位、主管審核及資料隔離尚未完成。最新範圍與修正順序見 [PoC 結論與修正計畫](docs/work-log-poc-plan-2026-09-09.md)；本輪僅應用層 PoC，不建立 Custom App 或修改服務。

已完成 Hyper-V VM 內的 ERPNext 服務啟用與獨立測試站建置，正在驗證每日工作紀錄的實作路線；尚未完成客製日報 App。

| 用途 | 區網網址 | 站台 |
|---|---|---|
| 原有站台／未來正式站候選 | http://192.168.0.70 | erpnext.local |
| 本地測試 | http://192.168.0.70:8080 | rpm-test.local |

實測版本為 ERPNext 16.34.1 / Frappe 16.33.0。兩站使用不同資料庫與附件目錄，但共用同一台 VM、Bench 程式碼與服務；尚非完全隔離的開發環境。正式上線與搬移前須再處理環境分離。

## 第一階段目標

- 員工一天一張紀錄，像表格一樣新增與刪除工作列。
- 每列記錄分類、工作事項、結果／進度與工時。
- 自動計算當日工時，Project / Task 選填。
- 儲存草稿、送主管審核、退回修改、核准後鎖定。
- 依日期、人員、部門與分類查看工作及工時。
- 提供清楚的繁體中文入口，減少每天填寫的操作成本。

這些是第一版提案；主管制度、部門名單及試辦人數仍需依實際組織確認。第一階段範圍集中於工作紀錄，既有 ERP 的整合另行規劃。

## 文件

- [工作紀錄與翻譯需求清單](docs/requirements-backlog.md)
- [ADR-001：模型與翻譯維護路線](docs/adr-001-work-log-model.md)
- [下一輪 PoC 驗收](docs/next-poc-acceptance.md)

- [2026-09-09 員工 PoC 結論與修正計畫](docs/work-log-poc-plan-2026-09-09.md)

- [每日工作紀錄 MVP 規格](docs/daily-work-log.md)
- [技術路線與原生功能驗證](docs/implementation-plan.md)
- [試辦驗收清單](docs/acceptance.md)
- [VM 操作、備份與搬移](docs/vm-operations.md)
- [原生 Timesheet 實測結果](docs/timesheet-findings.md)

## 開發原則

優先驗證 ERPNext 原生 Timesheet；若輸入方式或員工資料要求不適合，再使用獨立 Frappe App 建立 Daily Work Log。客製程式與可匯出的設定納入此 repo，避免直接修改 ERPNext / Frappe 核心。

附上的研究報告是背景參考，其中的命令、建議、公司資訊與時程不自動成為使用者已確認的需求。官方能力與實際站台行為也應分開記錄。

## 下一步

先完成需求清單 P0、核對修訂鏈與翻譯匯入結果，依 ADR-001 決定資料模型及允許實作範圍。翻譯先建立受 Git 管理的小批清單，再評估自動同步。部署前確認目標站台；目前提交的是計畫，不是設定變更。不要將密碼、API token、站台備份或真實員工資料加入 Git。
