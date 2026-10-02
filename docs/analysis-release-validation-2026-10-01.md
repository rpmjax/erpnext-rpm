# 公司分析候選：完整映像驗證

## 版本與範圍

- 應用候選：`19fe20ac17d5a0d0480268e1d7eda3486f1f23ed`，分支 `codex/worklog-management-analysis`。
- 舊版基準：`54b9d95e687fb661ecb97f573dedcd48984c4a3c`；映像內沒有 `analysis.py`。
- 使用 repository 的 `docker/Dockerfile.worklog`，底層映像
  `frappe/erpnext:v16.34.1@sha256:eee240a179ff494cb82ad067d853c8db3f87171d86324f4b326892654e342144`。
- WSL Ubuntu-24.04 獨立 Docker daemon 的候選 tag：`rpm-worklog-vm:19fe20ac17d5`；
  image ID：`sha256:2c37506b023f10d08e5b3cdf591536eef56a5c85ca19d1d82880def3686b4612`。
- Docker Desktop 同份原始碼另一次 build 的 image ID 不同，不把 tag 視為跨 daemon 相同 digest。
- 僅隔離測試站；沒有變更原 8086、Hyper-V、GCP，沒有合併工時分支或修原生 exporter。

## 新站安裝：PASS

`deploy.sh init` 使用候選完整映像建立 `analysis-fresh.internal`，frontend 僅綁 loopback 8091。

- Frappe / ERPNext / rpm_worklog 安裝、migration 完成。
- 自動建立管理角色與分析入口；讀取允許，write/create/delete/submit/cancel/amend/share/export/import 均關閉。
- 資料庫 Client Script 與映像內 analytics.js + analysis.js 完整一致。
- 九服務通過腳本穩定性檢查，DB/backend healthy，觀察期間沒有 restart。
- HTTP login 200、ping pong、Guest 分析 API 拒絕、實際 Administrator 登入成功。
- 直接匯入映像程式跑分析／CSV／XLSX 契約測試通過，不注入候選模組。

## 既有站更新：PASS（2026-10-02 核對完整結果）

舊版 `54b9d95` 初始化後，建立合成資料、保存指紋並執行備份；切換候選 image，
使用原 `deploy.sh update` 完成維護模式、再次備份、migrate、重建服務與穩定性檢查。

- 更新內備份批次 `20261001T081814Z`，包含資料庫、公開／私人檔案、site config、
  deploy.env 與舊 running-image 身分。先行備份批次為 `20261001T081400Z`。
- `SERVICES_STABLE`：九服務 running、健康檢查通過、觀察期間沒有 restart。
- `RELEASE_CHECK_PASS`：資料／認證／時區／附件指紋保持一致；管理角色入口為唯讀；
  Client Script 與完整 image 一致；310 列／335.6h／28 欄的分析與匯出測試通過。
- `HTTP_PASS`：login 200、ping、Guest 拒絕存取、實際 Administrator 登入成功。
- 更新成功後，隔離 project 全部停止，restart policy 設為 no，保留 volumes。
  停止後部分服務顯示 137/1 是清理停止結果，不作為先前穩定性檢查結果。
- 持久目錄中的 `upgrade-init.log`、`backup.log`、`update.log`、`release-check.log`、
  `http-check.log` 與 `image-id.txt` 為本機證據；設定／備份包含 secrets，不提交 Git。

公司設定與使用者授權不會自動猜測或指派；更新後須核對有效 Company、
`rpm_worklog_company`、管理使用者的 Employee 對應，再明確授予管理角色。

## 本地驗收入口（2026-10-02）

8086 維持既有局部覆蓋驗收環境，未換 image；六個分析相關檔案 hash、資料庫 Client Script
及 PS00010 的 Organization scope 已重新核對，與候選相符。這不表示整個 8086 容器等同候選 image。

1. 以 PS00010（ps00019@outlook.com）登入本地，開啟工作紀錄報表／Analytics。
2. 點「工作明細分析／匯出」（窄視窗可能在「…」），選「公司全員（含離職歷史）」。
3. 選日期範圍，使用工號／姓名搜尋並多選員工；紀錄部門也可搜尋多選。
4. 核對同欄位 OR、跨欄位 AND；修改條件後必須重新查詢才能下載。
5. 下載 CSV／XLSX，核對兩者工作列數、28 個欄位及工時合計與完整查詢一致。
6. 管理角色只擴充分析讀取／下載；不能因此編輯或審核全公司紀錄。

先前實測 J250301 + T181001、兩部門、2026-09-01～10-01 為 16 張／26 列／37.229h；
這是當時資料結果，若使用者已修改資料，應以目前相同條件重新對帳，不能硬要求舊數字。

## 測試資料與重跑界線

`scripts/test_analysis_release.py` 僅接受 `analysis-fresh.internal`、`analysis-upgrade.internal`，
另要求 `rpm_worklog_managed`。禁止用於正式站。

- seed 建立最小合成資料：5 個 User/Employee、1 張 Log、2 列、8.4h、2 個非空附件。
  Company/Employee/Log 是 SQL fixture；不代表 ERPNext 公司設定精靈驗收。
- before 儲存 Company、Department、User、Employee、Log、Line、Target、Review Event、
  User Permission、Has Role、File、認證資料、時區與附件檔案的指紋。
- check 比對指紋、安裝結果與讀取角色，直接 import 映像內的 analysis service。
  重用 `test_analysis_poc.py`，僅替換其 PoC 站名 guard；不替換應用程式碼。
  測試包含權限隔離、inactive 歷史、多選、JOIN 範圍、310 列／335.6h、28 欄匯出；fixture 修改 rollback。

在 bench 的 `sites` 目錄，以 bench Python 執行（兩個測試檔先複製到同一 `/tmp` 目錄）：

```sh
../env/bin/python /tmp/test_analysis_release.py analysis-upgrade.internal seed
../env/bin/python /tmp/test_analysis_release.py analysis-upgrade.internal before
# 執行既有 deploy.sh backup / update，再複製測試檔至重建的 backend
../env/bin/python /tmp/test_analysis_release.py analysis-upgrade.internal check
```

## 環境中斷與未驗證項目

初次舊版測試站初始化後，WSL 環境重啟、`/tmp` 設定消失，測試中斷，未算更新通過。
後續改用 `/home/ps00010/.local/state/rpm-analysis-check-20261001` 保存設定與 logs，
以全新 project `rpm-analysis-upgrade-v2-20261001` 重跑。此為驗證環境修正，未改通用 deploy scripts。
正式操作應依 [唯一 VM 操作程序](ssh-vm-deploy.md)，不能把測試腳本當發布 wrapper。

未涵蓋：正式主機更新、完整真實資料 DR／restore、負載、所有角色的瀏覽器操作、
私人附件 HTTP 授權矩陣、主管審核功能完整回歸。保留既有原生 0-row export 獨立問題。
沒有宣稱管理角色可以直接使用原生 DocType export。
