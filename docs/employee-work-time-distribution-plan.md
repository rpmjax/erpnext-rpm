# 員工工作時間分布 — Audit 與最小實作方案

日期：2026-10-12。狀態：已依使用者授權完成首批實作與隔離自動測試；未部署、未完成 browser acceptance。分支 `codex/employee-work-time-distribution`。此文件是本功能規劃與驗證入口，下方 audit 保留背景。

## 正式決策與實作結果

2026-10-13 使用者驗收：已於本地 sandbox 使用主管帳號操作並驗收，尚未發現特殊狀況。記錄為主管帳號已操作範圍通過，不代替其他角色、所有瀏覽器／觸控、完整 image 或 VM 驗證。

2026-10-13 互動修正：使用者同意將兩段式員工搜尋改為單欄 combobox（部分文字、滑鼠、上下鍵、Enter、Escape），重新輸入即清除舊選取並使舊結果失效。圓餅扇形可 click／Enter／Space 展開相應 details，選取描邊與 focus-visible 虛線保留鍵盤辨識。只修改前端與測試，授權／aggregation 不變。

本地已備份 analytics-before-interaction.js 與 client-script-before-interaction.txt 至既有 distribution-20261013 備份目錄並同步 Client Script。Node preset/render/navigation tests PASS。實際 8086 瀏覽器：部分工號 181001 → 候選 → ArrowDown/Enter 選取 → 查詢成功；Communication 扇形 click、PoC Assembly Enter 均使 aria-expanded=true 並展開明細。尚未涵蓋所有瀏覽器、觸控或搜尋失敗時序。未 commit/push 或更新 VM。

2026-10-13 更新：已備份後限定套用到本地 8086，Client Script 同步、資料指紋與唯讀 smoke check 通過；等待使用者 browser acceptance。下列「未同步本地」為 2026-10-12 初始 checkpoint，已由本段取代；仍未部署 VM。

- 週為週一至週日；空 Activity Type 顯示未分類且保留 Hours，不計入非空類型數；Self 自動解析本人，Team/Organization 必須指定單一員工。使用者已正式確認。
- 新增 `activity_distribution.py`，透過 analysis.py 共用 source_query 授權與 JOIN。SQL 以 HEX 原始內容分組，保留大小寫／尾端空白；NULL 與空 Activity Type 合併為未分類，NULL 與空 work_item 分開保留。
- 新報表置於選單第一並明確預設；原三種報表與 run() 不變。新模式使用簡單 HTML 長條與 SVG 圓餅，原報表仍使用 frappe.Chart。原生 title 提供 hover 內容，details 提供觸控／鍵盤可展開資訊；不引入圖表套件或修改核心。
- 預設日期沿用本月初至今日，標示「自訂」；選日／週／月時以基準日期套用完整日期區間。
- 沒有 schema／歷史資料 migration；未同步本地 8086 的 Client Script，未更新任何 VM。

### 2026-10-12 自動驗證

只使用 WSL disposable `rpm-nav01-fresh-20261008` / `analysis-fresh.internal` 合成站。候選 Python 模組複製到 `/tmp/distribution`，僅測試 Python process 以 package path 優先載入；未覆蓋運行 image 程式或同步 Client Script。所有測試交易 rollback。

- `scripts/test_activity_distribution.py` PASS：1,100 Line = 110.0h（不取母單 999h），跨兩張母單／審核狀態；七種精確內容的 Top 5 + remaining 對帳；Self/Team/Organization、越權、離職／跨公司／停用／缺公司設定、取消、無資料、零分母、8.4h 未分類及 NULL/空內容。
- `scripts/test_activity_distribution_ui.cjs` PASS：週一／週日與跨年、閏月、日／自訂；單群圓餅、Tooltip 字串、SVG escaping、可展開明細、空結果。Node DOM stub，不等同真實 browser 測試。
- 既有 `test_analysis_poc.py` PASS：公司隔離、離職歷史、Self/Team、欄位、加總、篩選、分頁、CSV/XLSX 與 fail-closed。
- 既有 `test_reports_poc.py` PASS：超過 300 張母單、Log/Entry grain、Sum/Count/Average、員工搜尋與權限。兩份舊測試只將 PoC site guard 換成明確 disposable site；reports 測試先於交易內配置合成 Pilot/Manager，未修改測試業務斷言。
- JS syntax 與 git diff whitespace 檢查通過。未建置完整候選 image，未跑部署／互動登入驗收。

### Browser acceptance checklist（尚待執行）

1. 新報表第一且預設；原三報表仍可查詢且原設定不變。
2. Self 自動本人；Team/Organization 未選人不發送分析查詢；工號／姓名搜尋正確，清除後不沿用前人結果。
3. 日／週／月／自訂顯示正確日期；跨年週、閏月正確；手動改日期回到自訂。
4. 已知資料核对總 Hours、工作列数、非空類型數與未分類；hover Top 5 與展開明細一致，圓餅／長條對帳。
5. 原始文字含大小寫、空白、HTML 字元忠實且安全顯示；觸控／鍵盤能展開明細。
6. 快速切換 scope／員工／日期與網路失敗，不顯示舊結果為新結果；空期間顯示無符合紀錄。
7. 員工不能查看他人；主管只見有效直屬（本人另用 Self）；公司管理只見設定公司。

未解風險：真實瀏覽器 title 換行／SVG hover 與窄螢幕可讀性待驗收；高基數自由文字會增加 backend 分組記憶體（後端僅回 Top 5，不截斷總數）；此次不是完整 image／更新驗證。無歷史數據改寫或授權模型擴張。

## 需求與範圍

在 RPM Work Log Analytics 新增第四種報表「員工工作時間分布」，排第一且作為預設；保留每日工時、各員工工時、審核狀態分布及其既有行為。新報表為「單一員工 × 指定期間 × Activity Type」的描述性分析，非 KPI 或效率評分。

- 員工以工號／姓名搜尋並單選；日／週／月／自訂期間統一成 from_date/to_date。
- 審核篩選沿用現有規則，預設 All。
- 顯示員工、日期、申報總工時、工作列筆數、Activity Type 數量。
- 依 Activity Type 顯示 SUM(Line Hours)、占比、工作列筆數；提供主要長條圖、圓餅或甜甜圈比例圖及數值明細。
- Tooltip 顯示該類型的工時、比例、筆數，以及按原始 work_item 精確值彙整的 Top 5（按工時降序）。其餘顯示不同內容數、工作列數與工時，避免「其他 N 筆」混淆粒度。
- 不進行自由文字改寫、大小寫合併、模糊或語意分組。momo、MOMO、momo出貨分開。
- 不包含多人比較、排名、分數、8 小時達成率、出勤／加班、taxonomy 重做、AI、Calendar、Target lifecycle 或其他 Dashboard 大改版。

## Repository audit

路徑以下均相對 repository root，應用模組在 `apps/rpm_worklog/rpm_worklog/`。

| 檔案 | 現有責任 |
|---|---|
| public/js/analytics.js | 表單、單選員工、日期／審核篩選、frappe.Chart 及表格 |
| reports.py | options/search_employees/run，設定驗證、授權與 SQL 彙總 |
| report_setup.py | 預設三種報表；穩定 ID 保留管理員修改 |
| analysis.py | 工作列 Dataset、篩選、明細分頁與完整匯出 |
| scope.py | Self／Team／Organization 授權 |
| analysis_ui.py | analytics.js 與 analysis.js 合併寫入資料庫 Client Script |

現有預設每日工時按日期 SUM(parent.total_hours)，各員工工時按員工 SUM(parent.total_hours)，審核分布 COUNT(Work Log)；都是 Log 粒度。報表可由管理員設定，不應覆寫既有紀錄。前端使用 frappe.Chart，超過 60 組只顯示完整表格。新報表必须使用 Line Hours，不能因展開子列而重複加總母單值。

可重用 analysis_scope、員工搜尋／標籤、日期與狀態驗證、既有 Parent/Employee/Line JOIN 與 line_id/activity_type/work_item/hours。員工候選目前僅來自已有授權工作紀錄，與查詢日期無關；最小方案保留。

### 權限實際語意

- Self：Pilot 角色、唯一有效 Employee，紀錄 employee 及 owner 都符合本人。
- Team：Manager Pilot、目前有效直屬員工，排除主管本人，不遞迴。
- Organization：Management 角色、唯一有效 Employee 及設定公司檢核；公司來源員工包含離職歷史。
- 所有 scope 排除取消紀錄；前端 employee 只縮小範圍，後端每次驗證。
- 主管查本人仍走 Self，查直屬走 Team；只有 Manager Pilot 不自動增加 Self 能力。此批不更動角色或合併 scope。
- Tooltip 與圖表必須使用相同 authorized source；不得另開較寬查詢。

## 最小設計

新增內建分析模式，options 放第一並由前端明確設為預設；不要為此增加通用報表設定欄位或修改原三筆設定。新模式禁止「目前範圍全部員工」；Self 由後端解析本人，其餘範圍必須選一人。

在 analysis.py 抽出共用授權／篩選／JOIN 建構，既有 dataset() 與新 aggregation service 使用同一來源。既有明細契約、分頁及匯出限制不變；新聚合不能只加總當前頁，也不需將全部原始工作內容傳至瀏覽器。

建議回傳契約：

```text
contract_version / scope
employee：識別碼、姓名／工號標籤
from_date / to_date / review_state
totals：reported_hours / line_count / activity_type_count / unclassified_line_count
groups[]：
  activity_type / display_label / hours / percentage / line_count
  top_items[]：原始 work_item / hours / line_count
  remaining：distinct_item_count / line_count / hours
```

Top 5 在 backend 聚合，與主圖共同篩選；須有穩定的同工時排序。資料庫一般 collation 可能忽略大小寫或尾端空白，原始文字精確分組需用 binary 比對或等效方法並測試。NULL／空字串的內容顯示與分組規則應明列，不修剪／美化其他文字。

比例使用完整篩選結果的儲存 Line Hours；先計算再顯示四捨五入，不強迫湊滿 100%。沒有資料或零分母顯示明確空狀態，保留既有零工時寫入規則。Tooltip 文字須 escape；數值明細提供同樣內容給觸控／鍵盤使用者。現有程式沒有自訂 Tooltip，實作前核對安裝版 frappe-charts 的擴充方式，不假定原生已支援。

日／週／月僅前端計算日期，後端保持 from_date/to_date 與最多 366 天驗證；手動改日期切「自訂」。不新增三套查詢或時間排程邏輯。

### 已採用的預設決策

1. 週起始為週一，週一至週日；日／週／月以選定基準日期計算。
2. 空 Activity Type 顯示「未分類」，保留其工時與工作列；不算入實際非空類型數，另列未分類筆數。
3. 新報表未選員工時不執行；Self 可自動解析本人。

上述三項已由使用者在 implementation 指示中正式確認。

## 預計修改檔案與順序

1. 先建立新契約及測試：新增 `scripts/test_activity_distribution.py`、前端 preset／顯示測試；依共用查詢重構影響擴充既有 analysis/reports 回歸。
2. 修改 `analysis.py` 抽出共用 source；新增 `activity_distribution.py` 做單人驗證、聚合、Top 5／比例。
3. 修改 `reports.py` options，保留既有 run 行為；修改 `public/js/analytics.js` 加模式、preset、圖表、Tooltip／明細。
4. 依既有安裝程序同步 Client Script；不需要新增 schema、資料表或歷史 Hours migration。無 schema change 不等於可省略既有安裝同步。
5. 更新本文件驗證證據與 PROJECT_STATUS；Analysis Contract 的長期規則不另複製成新規則來源。

## Automated tests 與 acceptance criteria

- Self 越權、非直屬、跨公司、停用帳號、角色移除、缺少公司設定 fail closed；Team 離職排除、Organization 離職歷史保留。
- 同日多張 Log／多 Line、超過分頁大小仍完整；單人限制與空選擇行為。
- JOIN 前後唯一 line_id 與 row count 一致；原始 Hours = 類型加總 = Top 5 加 remaining。
- 空 Activity Type／空內容、大小寫與尾端空白、同工時排序、超過五種內容、HTML 特殊字元。
- All 不額外篩審核狀態；個別狀態正確；取消紀錄排除；無資料、零分母安全。
- 日期含邊界、跨月／跨年週、閏年；快速切換條件的舊回應不可覆蓋新結果；查詢失敗不能留舊結果冒充新結果。
- 原三報表設定及行為、CSV／XLSX 明細欄位與授權不變。
- UI 新模式第一且預設，單人可選、實際日期可見，長條／比例圖與明細可核對，觸控可取得 Top 5。
- 實際自動測試與尚待執行項目以上方驗證紀錄為準；完整 browser checklist 不視為已通過。

## Analysis impact

- 用途：描述單一員工自主申報工時分布，不作績效評價。
- Dataset：既有授權 Worklog analysis 工作列的聚合投影。
- 粒度：來源一 Line（line_id）；輸出一 Activity Type 群組，Top 5 再按原始內容群組。
- 權限：重用 Self／Team／Organization；不更動寫入／審核／原生匯出權限。
- JOIN／加總：Employee 唯一 name、Parent 唯一 name；Line 關聯含 parenttype/parentfield。只 SUM 儲存 Line Hours，不重算 Start/End，不加總母單值或 Quantity。
- 使用端：Analytics 圖表、Tooltip、數值明細；本批不新增聚合 CSV／XLSX 匯出，既有明細匯出保持原契約。
- 驗證：依上節建立授權、JOIN row count、Hours reconciliation、既有匯出欄位回歸證據。
- 不納入理由：不適用；本功能本身屬管理分析。

長期規則見 [WORKLOG_ANALYSIS_CONTRACT.md](WORKLOG_ANALYSIS_CONTRACT.md)。
