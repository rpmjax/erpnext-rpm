# 目前進度與 Hyper-V SSH 部署準備（2026-09-14）

## 已完成

- 本機 Docker：工作紀錄、本人隔離、直屬主管審核、同單補正、單筆及批次送審。
- 可設定工作紀錄報表／圖表第一版：日期、狀態、本人／直屬範圍；完整服務端彙總，測試通過，畫面仍由使用者驗收。
- 報表 HTML 數值顯示錯誤已修正（a5d26ab）。
- 額外彩色狀態標籤已撤回；沿用原生列表欄位挑選。

## 已確認、尚未實作

- 主管報表新增個別員工搜尋；輸入真實工號或姓名，清除選擇回到全部直屬員工。
- 搜尋候選顯示「真實工號｜姓名｜部門」，報表員工標籤使用「真實工號｜姓名」。
- T870602、PS00012 等真實工號為主要辨識；HR-EMP 內部鍵保留關聯，一般操作不呈現。
- 先確認 Employee 實際工號欄位與缺值情況，不以內部 ID 或其他字串推算工號。
- 搜尋端點及彙總端點都檢查當下 Reports To，不能透過指定員工擴權。

## 透過 SSH 拉取原始碼

以下供使用者操作，本輪未連線或修改 VM。SSH 連到 VM 客體 IP，不是 Hyper-V 管理主機。

在 Windows 終端執行（以目前 IP 為例）：

```powershell
ssh paskadmin@192.168.0.70
```

第一次連線請核對 SSH 主機指紋。密碼互動輸入，不放在指令或 Git。進入 Ubuntu 後，首次拉取可使用獨立目錄：

```bash
mkdir -p ~/src
cd ~/src
git clone https://github.com/rpmjax/erpnext-rpm.git
cd erpnext-rpm
git log -1 --oneline
```

若該目錄已經存在，不重做 clone；確認是正確 repo 且工作目錄乾淨後更新：

```bash
cd ~/src/erpnext-rpm
git remote -v
git status --short
git branch --show-current
git fetch origin
git pull --ff-only origin master
git log -1 --oneline
```

以上 pull 適用本地 master 且無待保留變更；若分支不同或有修改，先檢視，不強制 reset。私有 repo 使用已授權的 SSH key／credential helper，不把 token 嵌入 URL。

## 為何目前不能直接安裝上 VM

目前 `apps/rpm_worklog/rpm_worklog/setup.py` 限定站名 frontend 且 rpm_worklog_model_poc 為真；還依賴先前原型建立的 Custom DocType、Client/Server Script、角色與權限設定。

歷史 VM 文件記錄 Bench 為 `/home/paskadmin/frappe-bench`，站台為 erpnext.local／rpm-test.local；本輪未重新盤點。不能把既有站台改名或改旗標來繞過安裝保護。

repo 是含 apps/rpm_worklog 子目錄的專案，不是根目錄即為 Frappe App 的單一套件；不能假設直接 bench get-app 此 repo 就能安裝。Dockerfile 可建 App 映像，但 Compose override 不是完整獨立環境，亦不包含資料庫、附件或人員資料。

## 建議部署路線

先在 VM 建立獨立 Docker 測試環境，延續目前已驗證版本，避免與原生 Bench 兩站共享 Python／工作程序。若決定採原生 Bench，需另做 App 安裝封裝與共用站台影響驗證。

部署前需完成：

1. SSH 唯讀盤點目標站台、版本、資源與連接埠；備份現有資料庫、附件與設定，確認可還原。
2. 將原型 schema、腳本、角色／權限及入口納入可重複執行的遷移，移除對已存在 PoC 資料的隱性依賴；設計明確目標站台保護，而非直接刪除 assert。
3. 提供完整部署 Compose／站台初始化文件與固定版本映像。真實人員與測試密碼不進 Git。
4. 在隔離測試站實際執行安裝、升級及回滾演練，再搬移所需主資料或受控備份；不覆蓋原站。
5. 驗收登入、本人隔離、主管範圍、送審／補正、報表與備份還原後，才規劃正式站切換。

因此目前可先 SSH 拉取原始碼；正式部署命令須在上述移植工作完成後提供，不能宣稱 git pull 等同上線。
