# 員工工作時間分布 — Audit 與最小實作方案

日期：2026-10-12。狀態：已完成 repository audit，使用者要求保存供調閱；尚未實作、測試或部署。此文件是本功能規劃的唯一入口，不代表開發完成或已授權部署。

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

### 待實作前確認的預設建議

1. 週起始為週一，週一至週日；日／週／月以選定基準日期計算。
2. 空 Activity Type 顯示「未分類」，保留其工時與工作列；不算入實際非空類型數，另列未分類筆數。
3. 新報表未選員工時不執行；Self 可自動解析本人。

目前使用者要求「紀錄」，未將上述每個預設另標記為明確決策。

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
- 測試目前尚未新增／執行，不宣稱以上已通過。

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
