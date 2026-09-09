# 原生 Timesheet 實測結果

> 後續員工瀏覽器實測（2026-09-09）為 PARTIAL，見 [PoC 結論與修正計畫](work-log-poc-plan-2026-09-09.md)。以下為 2026-09-07 的歷史後端測試，不能與新一輪權限、站台與保存結果混為一談。

日期：2026-09-07。ERPNext 16.34.1 / Frappe 16.33.0。

在 erpnext.local 與 rpm-test.local 分別執行 [check_timesheet.py](../scripts/check_timesheet.py)，使用管理員身分測試伺服器文件流程，結束時回滾交易。兩站結果一致：

| 測試 | 實際結果 |
|---|---|
| 五列工時 2、1.5、0.5、3、1，各自提供起始時間 | 儲存、提交、重新載入成功，總工時 8 |
| 五列 Project / Task 留白 | 成功 |
| 表頭 Employee 留白 | 成功；Activity Type 同時留白亦成功 |
| 僅填 Hours，不填 From / To | 提交失敗：From Time and To Time is mandatory |
| 回滾前後 Timesheet 數量 | 相同，未留下測試日報 |

這修正了研究報告對 Employee 必填的假設。實機 JSON 的 `employee.reqd` 為 0；提交時的程式邏輯在有 Employee 時才要求 Activity Type。因此不可僅因 HR 欄位就判定必須另做 App。

不過，原生 Timesheet 仍要求時間資訊；「不綁 Project」不等於「只填小時即可」。如果員工希望填摘要與總時數、不必回想每件工作起訖時間，自訂 Daily Work Log 仍值得考慮。

原站登入頁已透過瀏覽器檢查：設定 zh-TW 後仍有簡體字與英文混用。常用介面的繁中整理仍是實際工作項目。

## 驗證限制

本次沒有以一般員工或主管權限驗證，也沒有完成日報 Workflow、每日唯一限制、結果欄位、手機輸入或報表。原生「提交」不代表完成主管審核。MVP 驗收清單的 A01 僅完成後端資料模型部分，不應因此將整份清單標示通過。

## 重現

```bash
cd /home/paskadmin/frappe-bench
env/bin/python /path/to/erpnext-rpm/scripts/check_timesheet.py --site rpm-test.local
```

只在測試站執行。腳本使用管理員權限與真實文件 hooks，雖然回滾資料庫，也不能保證未來新增的外部整合 hooks 沒有副作用。
