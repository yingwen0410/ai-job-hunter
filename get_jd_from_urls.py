import requests
import re
import time
import os
import mysql.connector
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
load_dotenv()

def get_job_description(job_url: str, session: requests.Session) -> str:
    """
    接收一個 104 的 job_url，回傳該職缺的完整文字描述 (JD)。
    """
    match = re.search(r'/job/([^?]+)', job_url)
    if not match:
        print(f"  [錯誤] 無法從 {job_url} 中解析出 Job ID。")
        return ""
    job_id = match.group(1)
    
    content_api_url = f"https://www.104.com.tw/job/ajax/content/{job_id}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Referer': job_url
    }

    try:
        response = session.get(content_api_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        description = data.get('data', {}).get('jobDetail', {}).get('jobDescription', '')
        return description.strip()
    except Exception as e:
        print(f"  [錯誤] 抓取 {content_api_url} 時發生錯誤: {e}")
        return ""

def backfill_job_descriptions():
    """
    主函式：連接資料庫，找出需要補全 JD 的職缺，並抓取、更新。
    """
    db_connection = None
    try:
        # 1. 連接資料庫
        print("正在連接到資料庫...")
        db_connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'ai_job_hunter_db')
        )
        cursor = db_connection.cursor()
        print("資料庫連接成功！")

        # 2. 查詢目標：找出 job_description 為 NULL 或空字串的職缺
        query_jobs = "SELECT id, job_url FROM jobs WHERE job_description IS NULL OR job_description = ''"
        cursor.execute(query_jobs)
        jobs_to_process = cursor.fetchall()

        if not jobs_to_process:
            print("資料庫中所有職缺都已有描述，無需補全。")
            return

        print(f"找到 {len(jobs_to_process)} 筆需要補全描述的職缺，開始處理...")

        # 建立一個共用的 Session
        with requests.Session() as session:
            # 3. 循環抓取與更新
            for job_id, job_url in jobs_to_process:
                print(f"\n正在處理 Job ID: {job_id}, URL: {job_url}")

                # 呼叫函式抓取 JD
                description = get_job_description(job_url, session)

                if description:
                    # 4. 如果抓取成功，更新資料庫
                    print(f"  成功獲取 JD，長度為 {len(description)} 字。")
                    update_query = "UPDATE jobs SET job_description = %s WHERE id = %s"
                    cursor.execute(update_query, (description, job_id))
                    db_connection.commit() # 提交變更
                    print(f"  已成功將 JD 更新至資料庫 (Job ID: {job_id})。")
                else:
                    print("  未能獲取職缺描述，跳過此筆。")
                
                # 暫停一下，避免請求過於頻繁
                time.sleep(1.5)

        print("\n所有需要補全的職缺都已處理完畢！")

    except mysql.connector.Error as err:
        print(f"資料庫錯誤: {err}")
    except Exception as e:
        print(f"發生未知錯誤: {e}")
    finally:
        # 確保資料庫連線在使用後被關閉
        if db_connection and db_connection.is_connected():
            cursor.close()
            db_connection.close()
            print("資料庫連線已關閉。")

# --- 主程式執行區 ---
if __name__ == '__main__':
    backfill_job_descriptions()