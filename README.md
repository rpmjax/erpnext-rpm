# ERPNext RPM

以 ERPNext / Frappe 建立公司的工作管理平台，第一個落地用途為 **員工每日工作紀錄**。

## 目前狀態

2026-09-11：[資料規則與手動驗收](docs/worklog-data-rules.md)已部署 Docker。允許同日多張及重複 Title；伺服器驗證、單張總工時、本人每日彙總完成自動測試，待使用者手動驗收。

最新：[兩位員工登入與本人隔離驗收](docs/employee-access-poc-2026-09-10.md)已通過；專用入口、自動帶入、保存重載與跨帳號拒絕存取已實測。其餘員工尚未開放，主管流程與資料規則仍待完成。以下匯入進度為前一階段紀錄。

2026-09-10：[最新進度彙整](docs/progress-2026-09-10.md)。Docker 已匯入 33 個 User、來源公司及 7 個部門、33 個 Employee（32 個 User 綁定、32 個主管關聯）。來源缺漏與重複員工號已記錄；一般員工工作紀錄權限及完整流程尚未完成。人員資料與帳密未提交 Git。

使用者已選擇 **B：先驗證 Daily Work Log 模型，再決定 C 正式化**。獨立 [Docker 模型原型](docs/docker-model-poc.md) 已於 http://127.0.0.1:8083 建立，管理員可分欄保存數量／單位／結果／工時，不需起訖時間；員工權限、審核與完整規則尚未驗收，未建立 Custom App。

兩份後續研究報告已納入 [需求清單](docs/requirements-backlog.md)、[ADR-001 架構決策](docs/adr-001-work-log-model.md) 與 [下一輪驗收](docs/next-poc-acceptance.md)。已選 B 並建立 Custom DocType 原型，不再預設直接往 Timesheet 加欄位；Custom App 尚未授權或部署。

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

- [2026-09-10 模型與組織匯入進度](docs/progress-2026-09-10.md)

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

依使用者決定忽略來源例外；兩位員工本人存取已驗收，接著驗證 B 模型的資料規則、直屬主管權限與同單補正。翻譯先核對匯入結果、建立受 Git 管理的小批清單，再評估自動同步。Custom App 與原站部署另行決定。不要將密碼、API token、站台備份或真實員工資料加入 Git。
