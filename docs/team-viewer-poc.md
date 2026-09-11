# 直屬主管唯讀查閱 PoC

2026-09-11：應使用者要求開發；自動驗證 PASS，人工介面驗收待使用者執行。前一輪填寫與工時合計已由使用者認可。

## 範圍

新增原生 Custom Single DocType `RPM Team Work Log Viewer`、Client Script、API Server Script 與 Desktop Icon／Workspace Sidebar「直屬員工工作紀錄」。沒有安裝 Custom App、修改 Core 或原 VM。兩位試辦員工的 Reports To 指向同一位有效、已綁 User 的主管，只為該帳號配置 RPM Work Log Manager Pilot 角色。

主管從專用頁查看明細，不授予 RPM Daily Work Log 廣泛 read/write 權限，也不依赖僅影響列表的 Permission Query。原始單直接 URL／REST GET 仍被拒絕，主管需使用專用查閱入口。這是 B 模型階段的唯讀方案，不是主管取得原單表單權限；後續審核須另設授權動作。

每次查詢依 session User 查有效 Employee，再取 status Active 且 Reports To 等於主管的員工。僅當下直屬，沒有遞迴下屬或同部門擴權。歷史紀錄亦採目前 Reports To，不保留歷史主管存取。角色與有效 Employee 均須通過，再於 get_all 的 filters 限定直屬 Employee；回傳欄位採白名單，不回傳 Employee 私人欄位或帳密。前端所有文字 HTML escape。

日期起訖差最多 31 天，每次最多 300 張，超量明確提示縮小範圍；不以顯示上限冒充完整資料。可展開每張的分類、事項、數量、單位、結果、工時、備註。已開啟頁面不會撤回已讀內容；Reports To 變更後下一次查詢立即重新授權。

## 自動驗證

- 主管回傳的每一筆均屬直屬員工，無原單修改權。
- 交易內暫時移除直屬關係，重查即排除；偽造指定單號亦不回傳。最後 rollback 還原組織資料。
- 兩位一般員工被拒絕呼叫主管端點。
- 主管 bootinfo 有專用圖示。
- 真實獨立登入 HTTP session 查詢 200，原單 GET 403，Guest 被拒絕。
- 未代使用者操作瀏覽器，不宣稱前端點擊已人工驗收。

設定與測試：scripts/configure_team_viewer_poc.py、scripts/test_team_viewer_poc.py；API／前端：worklog_rules/team_summary.py、worklog_rules/team_viewer.js。部署先 docker cp worklog_rules/. 到容器 /tmp/worklog_rules/，再於標記 frontend site 的 Administrator console 執行設定腳本。帳密僅存本地忽略目錄。

## 手動驗收

1. 同一台電腦開 Guest Browser，用 `.local/worklog-poc/manager-login-credentials.json` 的 email、password 登入 http://127.0.0.1:8083/login 。
2. 開 /desk，Ctrl+Shift+R，應出現「直屬員工工作紀錄」。
3. 點圖示，應進入 /desk/rpm-team-work-log-viewer 。也可直接開此路徑。
4. 選 2026-09-01 至 2026-09-30，按「查詢」。應見直屬員工的紀錄。
5. 點紀錄摘要展開明細，核對姓名、部門、Title、編號、數量與工時。此頁没有保存員工紀錄或審核按鈕。
6. 一般員工登入時不應看到主管圖示，也不能取得主管查詢結果。
7. 回報圖示、查詢與展開是否正常；若錯誤，附訊息即可，不須改角色或組織。

待辦：主管審核、待審鎖定、退回原因、同單補正；本輪未實作。員工本人介面與資料限制繼續使用既有設定。

## 查詢按鈕與未保存提示修正

使用者回報看不到工具列「查詢」按鈕。本次將日期條件改為 HTML 暫存控制項，並在日期下方直接放置可見查詢按鈕，同時保留頁首查詢動作。查詢不再改動 Single DocType 欄位，進入時顯示「唯讀查詢」；結果更新只替換結果區，不移除查詢控制項。前端語法檢查通過，已更新 Client Script 並清快取；尚待使用者重載後人工確認，未將伺服器測試視為 UI 驗收。

請先 Ctrl+Shift+R，應見「開始日期／結束日期」及其下方藍色「查詢」。選日期後按此按鈕。若仍未顯示，回報畫面，需進一步確認該 session 是否載入新 Client Script。

## 返回首頁導覽

主管查閱頁日期控制項上方加入「← 返回首頁」原生連結，目的地 /desk，同分頁開啟；查詢結果更新不會移除導覽。JavaScript 語法與站台回傳 Client Script 已確認，未代操作瀏覽器。人工驗收：重新載入查閱頁 → 點返回首頁 → 應回到圖示首頁 → 點直屬員工工作紀錄可再次进入。

## 主管圖示外觀

沿用 Frappe 內建 users.svg 圖案，獨立副本採黃色 #FACC15 背景及深色 #713F12 人像。Desktop Icon 原生 bg_color 僅 gray/blue，因此以 icon_image／logo_url 指向站台公開 SVG，不擴充核心選項。原始素材未修改。腳本 scripts/configure_team_icon_poc.py，素材 assets/team-worklogs-yellow.svg；執行前複製素材至容器 /tmp/team-worklogs-yellow.svg。部署後實際 SVG URL 回應 200 且色碼符合；待使用者 Ctrl+Shift+R 人工確認。
