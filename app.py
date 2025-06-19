"""
Main Application & API Server

用 Flask 框架建立一個 Web 應用程式。
主要功能:
1. 提供 RESTful API 端點 (`/api/jobs`)，以 JSON 格式回傳所有職缺資料。
2. 處理跨來源資源共用，允許前端網頁進行 API 請求。
3. 使用 APScheduler 在背景中定時執行爬蟲任務，實現資料的自動化更新。
"""
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify, Response, request, render_template
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
import database
import scraper
import atexit
import json
from datetime import datetime
import math 
import resume_parser
from werkzeug.utils import secure_filename
import llm_service


# --- Flask 應用程式設定 ---
app = Flask(__name__)
CORS(app) 

# 設定 JSON 編碼
app.config['JSON_AS_ASCII'] = False 
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8' 

print("--- Flask app 已初始化，CORS 已設定 ---")

def datetime_handler(obj):
    """處理 datetime 物件的 JSON 序列化"""
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

# --- API 路由 ---
@app.route('/api/jobs')
def get_jobs():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    keyword = request.args.get('keyword', '')
    status = request.args.get('status', '')
    
    print(f"[DEBUG app.py] /api/jobs 收到請求，參數：page={page}, limit={limit}, keyword='{keyword}', status='{status}'")

    jobs, total = database.get_all_jobs(page=page, limit=limit, keyword=keyword, status=status)
    
    print(f"[DEBUG app.py] database.get_all_jobs 返回：獲取到職缺數量：{len(jobs) if jobs else 0}, 總數：{total}")
    if jobs is None:
        print("[ERROR app.py] 從資料庫獲取職缺列表失敗，返回 500 錯誤。")
        return jsonify({'error': '獲取職缺列表失敗'}), 500
        
    response_data = {
        'jobs': jobs,
        'page': page,
        'limit': limit,
        'total_jobs_count': total,
        'total_pages': (total + limit - 1) // limit
    }
    return jsonify(response_data)

@app.route('/api/jobs/<int:job_id>/status', methods=['POST'])
def api_update_job_status(job_id):
    """
    更新指定職缺的狀態。
    """
    try:
        data = request.get_json()
        new_status = data.get('status')

        if not new_status:
            return jsonify({"error": "缺少新的狀態參數"}), 400

        if database.update_job_status(job_id, new_status):
            return jsonify({"message": "職缺狀態更新成功"}), 200
        else:
            return jsonify({"error": "職缺狀態更新失敗或未找到職缺"}), 404
    except Exception as e:
        print(f"處理 /api/jobs/{job_id}/status 請求時發生錯誤: {e}")
        return jsonify({"error": f"伺服器發生未知錯誤: {str(e)}"}), 500

@app.route('/api/last-update', methods=['GET'])
def get_last_update():
    try:
        last_update = database.get_last_update_time()
        return jsonify({
            'success': True,
            'last_update': last_update
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# 詳情頁面
@app.route('/jobs/<int:job_id>')
def job_detail(job_id):
    job_data = None
    try:
        conn = database._db_instance.pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
        job_data = cursor.fetchone()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"查詢職缺 {job_id} 詳情時發生錯誤: {e}")
        return "找不到該職缺", 404

    if not job_data:
        return "找不到該職缺", 404
    
    # 渲染 templates/job_detail.html 並傳入職缺資料
    return render_template('job_detail.html', job=job_data)

    
# AI 履歷匹配 
@app.route('/api/jobs/<int:job_id>/match', methods=['POST'])
def match_resume_with_job(job_id):
    # 1. 驗證並解析上傳的履歷檔案
    if 'resume' not in request.files:
        return jsonify({'error': '請求中缺少檔案部分'}), 400
    resume_file = request.files['resume']
    if resume_file.filename == '':
        return jsonify({'error': '未選擇任何檔案'}), 400

    try:
        resume_text = resume_parser.parse_resume(resume_file.stream, resume_file.filename)
        if not resume_text:
            return jsonify({'error': '無法從履歷中提取文字內容。'}), 500
    except Exception as e:
        return jsonify({'error': f'解析履歷時發生錯誤: {str(e)}'}), 500

    # 2. 從資料庫獲取職缺描述
    try:
        # 假設 database.py 中有一個 get_job_by_id 的函式
        # 如果沒有，我們直接在這邊查詢
        conn = database._db_instance.pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT job_description FROM jobs WHERE id = %s", (job_id,))
        job = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not job or not job['job_description']:
            return jsonify({'error': f'在資料庫中找不到 ID 為 {job_id} 的職缺描述。'}), 404
        job_description = job['job_description']
    except Exception as e:
        return jsonify({'error': f'查詢資料庫時發生錯誤: {str(e)}'}), 500

    # 3. 呼叫 LLM 服務進行分析
    print("--- 正在呼叫 LLM 進行分析 ---")
    analysis_result = llm_service.get_match_analysis(job_description, resume_text)
    print("--- LLM 分析完成 ---")

    # 4. 回傳分析結果給前端
    if "error" in analysis_result:
        return jsonify(analysis_result), 500
    
    return jsonify(analysis_result), 200

'''
# 測試履歷解析功能的 API 端點
@app.route('/api/resume/parse', methods=['POST'])
def parse_resume_endpoint():
    if 'resume' not in request.files:
        return jsonify({'error': '請求中缺少檔案部分'}), 400
    
    resume_file = request.files['resume']
    
    if resume_file.filename == '':
        return jsonify({'error': '未選擇任何檔案'}), 400

    try:
        filename = resume_file.filename
        
        resume_text = resume_parser.parse_resume(resume_file.stream, filename)
        
        if not resume_text:
            return jsonify({'error': '無法從檔案中提取文字內容，可能檔案為空或格式不受支援。'}), 500
            
        return jsonify({
            'message': '檔案解析成功！',
            'filename': filename,
            'character_count': len(resume_text),
            'preview': resume_text[:100] + "..."
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'處理檔案時發生未知錯誤: {e}'}), 500
'''

@app.route('/')
def index():
    return render_template('index.html')

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

