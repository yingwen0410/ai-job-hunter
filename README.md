# AI Job Hunter

一個自動化、可持續維護的求職資訊整合平台。系統每日自動化爬取指定求職網站的「AI 工程師」職缺，經過結構化清洗與篩選後，存入專業資料庫。最終，透過一個現代化的 Web 介面，將最新、最相關的職缺呈現給使用者。

## 功能特點

- 自動化爬取 104 和 1111 人力銀行的 AI 工程師職缺
- 結構化資料儲存與管理
- 現代化的 Web 介面
- 職缺狀態追蹤（已關注/未關注）
- 即時更新職缺資訊

## 系統需求

- Python 3.8+
- Chrome 瀏覽器
- ChromeDriver

## 安裝步驟

1. 克隆專案：
```bash
git clone https://github.com/your-username/ai-job-hunter.git
cd ai-job-hunter
```

2. 建立虛擬環境：
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

3. 安裝依賴套件：
```bash
pip install -r requirements.txt
```

4. 下載 ChromeDriver：
- 從 [ChromeDriver 官網](https://sites.google.com/chromium.org/driver/) 下載對應版本的 ChromeDriver
- 將 chromedriver.exe 放在專案根目錄

## 使用方法

1. 啟動爬蟲程式：
```bash
python scraper.py
```

2. 啟動 Web 服務：
```bash
python app.py
```

3. 開啟瀏覽器訪問：`http://localhost:5000`

## 專案結構

```
ai-job-hunter/
├── app.py              # Flask Web 應用
├── scraper.py          # 爬蟲程式
├── database.py         # 資料庫操作
├── requirements.txt    # 依賴套件
├── static/            # 靜態檔案
├── templates/         # HTML 模板
└── README.md          # 專案說明
```

## 授權

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案

## 貢獻

歡迎提交 Pull Request 或開 Issue 來協助改進這個專案！
