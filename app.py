"""
Main Application & API Server

用 Flask 框架建立一個 Web 應用程式。
主要功能:
1. 提供 RESTful API 端點 (`/api/jobs`)，以 JSON 格式回傳所有職缺資料。
2. 處理跨來源資源共用，允許前端網頁進行 API 請求。
3. 使用 APScheduler 在背景中定時執行爬蟲任務，實現資料的自動化更新。
"""


from flask import Flask, jsonify, Response, request
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
import database
import scraper
import atexit # 用於在應用程式關閉時，優雅地關閉排程器
import json
from datetime import datetime
import math # 导入 math 模块用于计算总页数

# --- Flask 應用程式設定 ---
app = Flask(__name__)
# 允許所有來源的跨域請求，這在開發階段非常方便
CORS(app) 

# 設定 JSON 編碼
app.config['JSON_AS_ASCII'] = False  # 確保 JSON 回應中的中文不會被轉換為 Unicode
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'  # 設定正確的 MIME 類型和字符集

print("--- Flask app 已初始化，CORS 已設定 ---")

def datetime_handler(obj):
    """處理 datetime 物件的 JSON 序列化"""
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

# --- API 路由 ---
@app.route('/api/jobs', methods=['GET'])
def api_get_jobs():
    """
    提供所有職缺資料的 API 接口，支持分頁。
    """
    try:
        # 從請求中獲取分頁參數，並提供預設值
        page = int(request.args.get('page', 1))  # 預設頁碼為 1
        limit = int(request.args.get('limit', 10)) # 預設每頁顯示 10 筆

        jobs, total_jobs_count = database.get_all_jobs(page, limit)
        
        if jobs is not None:
            # 計算總頁數
            total_pages = math.ceil(total_jobs_count / limit) if limit > 0 else 0

            response_data = {
                'jobs': jobs,
                'page': page,
                'limit': limit,
                'total_jobs_count': total_jobs_count,
                'total_pages': total_pages
            }
            json_str = json.dumps(response_data, ensure_ascii=False, default=datetime_handler, indent=2)
            return Response(json_str, mimetype='application/json; charset=utf-8')
        else:
            print("錯誤：從資料庫獲取資料失敗 (回傳值為 None)。")
            return jsonify({"error": "無法從資料庫獲取資料"}), 500
            
    except Exception as e:
        print(f"處理 /api/jobs 請求時發生未知錯誤: {e}")
        return jsonify({"error": f"伺服器發生未知錯誤: {str(e)}"}), 500

# --- 自動化排程設定 ---
def scheduled_job():
    """定義排程需要執行的任務。"""
    print("\n--- 排程任務觸發：開始執行每日爬蟲任務 ---")
    scraper.scrape_all_jobs() # 使用 scraper.py 中定義的預設參數
    print("--- 每日爬蟲任務執行完畢 ---\n")

scheduler = BackgroundScheduler(daemon=True)
# 設定排程器：每天的凌晨 2:00 執行一次 scheduled_job 函式
scheduler.add_job(scheduled_job, 'cron', hour=2, minute=0)
scheduler.start()
print("--- 背景排程器已啟動，將於每日凌晨 2:00 執行爬蟲 ---")

# 確保應用程式關閉時，排程器也會一併關閉
atexit.register(lambda: scheduler.shutdown())

# --- 主程式執行入口 ---
if __name__ == '__main__':
    print("\n" + "="*50)
    print("AI Job Hunter 伺服器正在啟動...")
    print("="*50 + "\n")
    
    # debug=True 讓我們在修改程式碼後，伺服器會自動重啟，方便開發
    # use_reloader=False 是為了防止在 debug 模式下，排程器被重複初始化兩次
    print("Flask 伺服器設定：")
    print("- 主機：0.0.0.0")
    print("- 端口：5000")
    print("\n請在瀏覽器中訪問：http://127.0.0.1:5000/api/jobs")
    print("\n" + "="*50 + "\n")
    
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)

