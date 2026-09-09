# Docker Daily Work Log 模型原型

狀態：B 模型驗證第一步已建立，整體仍 PARTIAL。使用者已同意 B 先驗證、再決定 C；未建立 Custom App。

## 環境

- Docker Compose project：`erpnext-worklog-poc`。
- 入口：http://127.0.0.1:8083 。僅繫結 loopback，與既有 Dolibarr 8080–8082 分開。
- 版本實讀：ERPNext 16.34.1、Frappe 16.33.0。
- Compose 以官方 [frappe_docker pwd.yml](https://github.com/frappe/frappe_docker/blob/main/pwd.yml) 為基礎，ERPNext 固定 v16.34.1、port 改 loopback 8083。
- 本機 compose 位於 `.local/worklog-poc/compose.yaml`，含官方 demo 設定，未提交 Git。這是本機示範環境，不能將 demo 設定直接公開上線。
- 獨立 project network 與 named volumes；未讀取／複製 192.168.0.70 的業務資料，未改其服務，也未修改 Dolibarr 容器。
- 官方 create-site 成功後，以原生 setup_complete 初始化 Taiwan、TWD、Asia/Taipei、English，建立合成公司。未只改 setup_complete 旗標跳過初始化。

## 模型與證據

`RPM Daily Work Log`（custom=1、Track Changes）＋`RPM Work Log Line` 子表。主表日期、Employee、Department 連結；明細 Activity Type、Work Item、Completed Quantity、UOM、Result、Hours、Note。

資料與 schema 由 [bootstrap_worklog_model_poc.py](../scripts/bootstrap_worklog_model_poc.py) 建立，受 site 名 `frontend` 與 `rpm_worklog_model_poc` 設定雙重保護。腳本只建立缺少的模型，不是 schema 升級工具；不得用在原站。

合成測試單 `RWL-2026-00001`：2026-09-09、合成 Employee、組裝後避震器、5、PoC Piece、Completed、1 小時。PoC Piece 為測試單位，不表示支／組換算規則已確認。

已驗證：

- 後端建立並重讀數量 5、工時 1、Completed。
- 模型不含 From/To、Project/Task，無須捏造起訖時間。
- 瀏覽器以 Administrator 開啟明細，修改 Work Item 為中文、Save、重載後保留。
- Track Changes 在 Activity 顯示該次工作內容修改。

## 尚未完成

僅 System Manager 可用的模型原型，並未開放一般員工。尚無登入員工自動帶入、總工時自動計算、每日唯一、負數／計量單位配對規則、直屬主管權限、Workflow、專用 Workspace、手機與操作步數驗收。Department 欄位存在，合成員工尚未配置部門。

模型可保存不等於符合正式驗收；總工時不能用可手填值冒充伺服器加總，UOM 主檔也不自動保證自訂數量驗證。下一步先做多列與資料規則、合成員工／主管權限，再安排真實員工試用。若須 C 的伺服器程式封裝，另行決定，不偷偷擴大範圍。

## 本機操作

在 repo 根目錄：

```powershell
docker compose -p erpnext-worklog-poc -f .local/worklog-poc/compose.yaml ps -a
docker compose -p erpnext-worklog-poc -f .local/worklog-poc/compose.yaml stop
docker compose -p erpnext-worklog-poc -f .local/worklog-poc/compose.yaml start
```

停止／啟動使用現有容器與資料卷；勿用 `down -v`，那會刪除此 PoC 資料。既有原站、其他 Docker project 不屬於這組指令範圍。登入使用本地 demo 管理員；憑證不納入 repo。
