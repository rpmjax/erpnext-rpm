# PROJECT STATUS — 五分鐘接手

## 2026-10-02：公司分析候選可本地驗收

- 固定應用候選：`19fe20ac17d5a0d0480268e1d7eda3486f1f23ed`；分支
  `codex/worklog-management-analysis`。後續驗證腳本／文件提交不改應用 image。
- 完整 image 新站安裝、`54b9d95` 舊站 backup → update/migrate → verify 均通過。
  含九服務穩定性、資料／附件指紋、28 欄 CSV/XLSX、權限與 HTTP 登入驗證。
  [完整證據、限制及驗收步驟](analysis-release-validation-2026-10-01.md)。
- 8086 仍是局部覆蓋驗收環境；分析六檔 hash、Client Script 與 PS00010 公司 scope
  已核對一致。隔離測試 project 已停止。Hyper-V／GCP 未更新，未 merge／push。
- 下一步：依上方驗收步驟作最後確認；發布前核對目的 VM 的實際 image、公司設定、
  管理 Employee／角色及备份，依唯一 [操作程序](ssh-vm-deploy.md) 更新。
  不能直接把此候選當成 Hyper-V／GCP 已部署版本。
- 下方各日期段落是當時 checkpoint；「未提交／待驗證」不再代表本批目前狀態。

## 2026-10-01：目前開發 checkpoint（未提交／未發布）

- 目前分支：`codex/worklog-management-analysis`，基底 `54b9d95`；候選仍是工作目錄變更，
  尚無可供 VM 更新的固定 candidate commit/tag。
- 使用者已回報本地公司分析與員工／部門多選操作確認；這是該操作範圍的驗收，
  不等於正式 VM 部署、完整權限稽核或災難復原驗證。
- 本輪重新執行 analysis、reports、target summary 三組測試，全部通過。
  執行命令見下方 2026-09-30 紀錄；測試資料 rollback，未部署。
- Analysis Contract 已升為長期完成條件；README 與 PR 範本指向同一規則。
- 下一步：保留此候選供提交前審查；發布前須產生固定提交，並在隔離環境以完整 image
  驗證安裝／更新流程。本地 8086 目前是局部程式覆蓋，不能作為完整 image 驗證證據。
- 既有報表共用 Dataset 是後續獨立範圍；原生 0-row export 另支處理。
  本批不合併工時分支、不修原生 exporter、不更新 Hyper-V/GCP。

### 本批 Analysis impact

用途：授權範圍內逐工作列分析與完整匯出。
Dataset：Worklog analysis v1，契約見 [Analysis Contract](WORKLOG_ANALYSIS_CONTRACT.md)。
粒度：一筆工作子列；鍵為 work_log + line_id。
權限：Self／Team 保留既有規則；Organization 使用管理角色、Employee 與設定公司。
分析授權可與原生 DocType 不同，但不新增原始單據編輯／審核／原生匯出權限。
JOIN / 加總規則：子列連母單及目前 Employee；Hours 按子列加總，單數 distinct；
不重複累加母單總時數，Quantity 不跨不同單位／業務意義任意合計。
使用端：明細 dialog、CSV、XLSX；既有摘要 Report 保留原查詢，未新增 Dashboard。
驗證：`scripts/test_analysis_poc.py` 覆蓋授權／越權、JOIN 範圍、分頁與完整匯出；
310 列案例對帳 335.6h，CSV/XLSX 均 28 欄；既有 reports、target summary 回歸通過。
本地多選實測 16 張／26 列／37.229h；完整 image 更新驗證尚未完成。
不納入理由（如適用）：審核事件未 JOIN，以免同一工作列因事件數重複。

## 2026-10-01：分析多選（本地 8086 已套用）

- 員工可依工號／姓名搜尋並複選；部門依授權紀錄的保存值搜尋複選。
  同欄位 OR、跨欄位 AND；CSV/XLSX 使用同一 filters。每欄最多 100 項。
- scope 改變會清空選取；條件改變使舊查詢／下载失效。候選不受日期限制，介面有提示。
- 新增後端多選、去重、越權排除、候選隔離、工號／姓名、歷史部門與下載集合測試；
  analysis 和既有 reports 回歸通過，JS syntax 與 diff check 通過。
- PS00010 瀏覽器實測選 J250301 + T181001 與兩部門，2026-09-01～10-01 得到
  16 張／26 列／37.229h。僅本地更新，Hyper-V/GCP、Frappe exporter 未改。
- 修正分析入口 DocPerm 的 Frappe 預設 write/create：明確關閉管理角色入口寫入，
  原始 Work Log 寫入權限從未新增。未 commit/merge/push。

## 2026-09-30：公司分析候選（僅本地 8086 已套用，未發布）

- 分支 `codex/worklog-management-analysis`，基底 `54b9d95`；獨立 worktree，沒有帶入
  `codex/reported-hours-reference` 未提交的工時修改。下方既有環境觀測仍是舊觀測。
- 已完成測試／[資料契約](WORKLOG_ANALYSIS_CONTRACT.md)、Organization scope、逐工作列
  analysis service、管理角色初始化、Analytics 明細 dialog、CSV/XLSX 完整下載。
- 後端 `analysis.query` 提供 28 欄明細與完整篩選總計；Self／Team 保留舊語意。
  既有摘要報表仍使用原查詢；不宣稱所有消費端已完成一致化。
- 測試：`python scripts/run_analysis_checks.py rpm-work-target-phase1-backend-1
  scripts/test_analysis_poc.py scripts/test_reports_poc.py scripts/test_target_summary_poc.py`
  全數通過。以獨立 Python 程序載入候選 scope/analysis，資料庫 fixture 最後 rollback；
  測試模擬 session roles，未指派實際使用者角色。沒有替換容器程式或部署。
- 2026-09-30 使用者授權本地驗收後，僅複製 scope/analysis/analysis_export/analysis_ui
  與 analytics.js/analysis.js 到 8086 backend；執行限定的 analysis_ui.install 並重啟 backend。
  不是整個分支 image 重建；原容器既有其他候選修改保留。Hyper-V/GCP 未修改。
- 本地 Company 已核對並設定「均輝企業股份有限公司」；使用者指定 PS00010
  (ps00019@outlook.com) 加入管理角色。實際公司查詢 2026-09-01～30：16 張、26 列、37.229h。
  rpmjaxadmin 沒有 Employee 對應，未豁免限制或替它建立對應。
- 瀏覽器以現有普通員工 session 驗證：本人 5 張／8 列／18h，CSV 和 XLSX 實際下載
  均 8 列、28 欄、18h。公司角色後端已驗證，PS00010 瀏覽器驗收待使用者進行。
- 本地更新前備份：`C:/Users/PS00010/Documents/ChatGPT/erpnext-rpm-backups/local-analysis-20260930/`
  包含 app-before 與 20260930_123004 frontend 資料庫／檔案備份。未 commit/merge/push。
- 下一步：使用者本地驗收，再安排既有報表共用查詢。原生 0-row export defect 另支處理。

## 以下為 2026-09-22 歷史交接基線（非目前開發下一步）

更新日期：2026-09-22。唯一「目前狀態」入口；實際主機狀態須依 [操作程序](ssh-vm-deploy.md) 重新讀取。未取得部署證據，不能標記部署完成。

## 版本位置

| 身分 | 固定版本 | 意義 |
|---|---|---|
| 最近發布標籤 | release/worklog-2026-09-21 → e530d84985e268d23437901f53a81d74d533438e | 通知／目標刪除版本；具隔離升級、九服務及 HTTP 檢查紀錄，不等於每台 VM 正在使用 |
| 下一候選程式版本 | 13d5689ffa1d9f02a57e2c3f9af8377b8495728c | 含後續側欄、物料、手機卡片、右欄及翻譯；尚未建立新 release tag |
| 開發位置 | codex/work-target-phase1 | 會移動，不作部署版本承諾；文件提交可能比候選程式 SHA 新 |
| master | 本次盤點為 625514b | 舊版本，不用 master 名稱推定最新或正式 |

## 環境：最後觀測，不是即時狀態

| 環境 | 最後已知狀態 | 證據／限制 |
|---|---|---|
| 本地 8086 | 候選 13d5689 的翻譯已部署、翻譯字典檢查通過 | 開發操作紀錄 2026-09-22；dev image tag 可變，未作完整發布重驗 |
| Hyper-V | Git HEAD 13d5689；運行 rpm-worklog-vm:faa506b1373e | 操作者於本次交接前貼回 status，九服務在運行、DB/backend healthy；回報未附主機採集時間。後續 build/update 指令已提供，但未收到完成證據，現在版本未知 |
| GCP | 625514b3b806 新站部署與 HTTPS login 成功 | [操作者實測紀錄](gcp-cyberpanel-deployment-2026-09-21.md)，非本次重新驗證；目前不在操作範圍 |

## 最近完成與驗證層次

- 發布版本：通知導向唯讀紀錄、原審核操作、未關聯目標刪除；[發布檢查與界線](release-candidate-2026-09-21.md)。
- 候選 UI：物料確認替換／鍵盤候選、手機卡片、雙欄版面、個人右欄切換。操作者回報操作尚可；[批次紀錄](ui-update-2026-09-22.md)記錄測試範圍。双欄最終版未有獨立完整驗收矩陣。
- 側欄：修正新舊 Workspace 共存及桌面導向；有程式測試，最終刷新回歸仍需明確人工確認。
- 翻譯：In Progress→進行中、Completed→已完成、Blocked→擱置；13d5689 已納入 Git，本地翻譯字典確認，Hyper-V 畫面未確認。

## 正在做／未完成

正在做：將維運狀態與操作程序集中到 repository，先完成交接基線，不新增業務功能。

尚缺：Hyper-V 更新後證據；候選整批九服務／HTTP及操作重驗；完整離機資料災難復原；正式負載；GCP WebSocket/憑證續期等獨立驗證。新站重建、既有局部 restore 不等於完整 DR。

延期：自動刷新查詢頁低優先級；數量進度、完成率、自動結案暫不開發；Work Target 狀態翻譯待處理。決策與需求背景見 [backlog](requirements-backlog.md)。

## 唯一建議下一步

**先依操作程序的「唯讀盤點」取得 Hyper-V Git／設定／實際映像三者。** 不假設上次更新完成：

- 若仍運行 faa506b：依既有站更新程序，在備份與維護窗口準備妥當後套用候選 13d5689。
- 若已運行 13d5689：不重跑 init/update，先 verify 與畫面驗收，回填證據。
- 若服務異常或有混用映像：先保存 logs，不盲目重建或回滾。

## Checkpoint 與狀態更新規約

每批收尾更新本頁，證據留在既有交付紀錄，不另開平行狀態文件。最少記錄：候選 SHA、完成範圍、自動測試、使用者驗收、未完成、下一步。commit 後 push，確認遠端 SHA；不在本頁寫入包含本頁自身提交的自我引用 SHA。

環境回報格式（置於上表或相關既有交付紀錄）：環境別名、採集時間/時區、操作者、Git SHA、設定目標 image、實際各服務 image ID、備份批次/離機確認、migration 結果、verify 結果、人工驗收與未完成。缺任何證據如實寫未確認；不提交 secrets 或原始私人輸出。

`planned`、`implemented`、`tested`、`accepted`、`observed running` 分開表達；「給過命令」不代表已執行。「stable」只限註明的驗證條件。
