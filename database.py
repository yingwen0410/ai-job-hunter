"""
資料庫存取模組 (Data Access Layer) - 新增欄位與偵錯版

本模組負責處理所有與 MySQL 資料庫的互動。
功能包括：
1. 管理資料庫連接池，提供穩定高效的連線。
2. 初始化資料庫，確保 'jobs' 資料表存在 (已新增 experience 和 education 欄位)。
3. 封裝所有對 'jobs' 資料表的 CRUD 操作。

採用參數化查詢以防止 SQL 注入攻擊。
採用環境變數來管理敏感的資料庫憑證。
"""

import mysql.connector
from mysql.connector import pooling
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME', 'ai_job_hunter_db'),
}

if not DB_CONFIG['password']:
    raise ValueError("錯誤：資料庫密碼未在 .env 檔案中設定 (DB_PASSWORD)")

try:
    connection_pool = pooling.MySQLConnectionPool(pool_name="job_pool",
                                                  pool_size=5,
                                                  **DB_CONFIG)
except Error as e:
    print(f"建立資料庫連接池時發生錯誤: {e}")
    connection_pool = None

def get_db_connection():
    """從連接池中取得一個資料庫連線。"""
    if not connection_pool:
        raise Exception("資料庫連接池不可用，請檢查設定。")
    try:
        return connection_pool.get_connection()
    except Error as e:
        print(f"從連接池取得連線時發生錯誤: {e}")
        return None

def init_db():
    """
    初始化資料庫，如果 'jobs' 資料表不存在，則建立它。
    如果資料表已存在，會嘗試新增 experience 和 education 欄位。
    """
    db_connection = None
    cursor = None
    try:
        db_connection = get_db_connection()
        if db_connection.is_connected():
            cursor = db_connection.cursor()
            
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} DEFAULT CHARACTER SET utf8mb4")
            cursor.execute(f"USE {DB_CONFIG['database']}")
            
            create_table_query = """
            CREATE TABLE IF NOT EXISTS jobs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                company_name VARCHAR(255),
                location VARCHAR(100),
                experience VARCHAR(100),
                education VARCHAR(100),
                salary_range VARCHAR(100),
                job_url VARCHAR(512) NOT NULL UNIQUE,
                source_website VARCHAR(100),
                posting_date VARCHAR(100),
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            cursor.execute(create_table_query)
            print("資料表 'jobs' 已確認存在。")

            
            db_connection.commit()
            return True
    except Error as e:
        print(f"資料庫初始化或升級失敗: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if db_connection and db_connection.is_connected():
            db_connection.close()

def add_job(job_data):
    """
    新增一筆職缺資料到資料庫中。
    """
    db_connection = None
    cursor = None
    
    query = """
    INSERT IGNORE INTO jobs (title, company_name, location, experience, education, salary_range, job_url, source_website, posting_date)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        job_data.get('title'),
        job_data.get('company_name'),
        job_data.get('location'),
        job_data.get('experience'),
        job_data.get('education'),
        job_data.get('salary_range'),
        job_data.get('job_url'),
        job_data.get('source_website'),
        job_data.get('posting_date')
    )

    try:
        db_connection = get_db_connection()
        if db_connection.is_connected():
            cursor = db_connection.cursor()
            cursor.execute(query, values)
            db_connection.commit()
            if cursor.rowcount > 0:
                return True
            else:
                return False
    except Error as e:
        print(f"新增職缺時發生錯誤: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if db_connection and db_connection.is_connected():
            db_connection.close()

def get_all_jobs(page=1, limit=10):
    """從資料庫中獲取所有職缺資料，並支持分頁。"""
    db_connection = None
    cursor = None
    jobs = []
    total_jobs_count = 0
    try:
        db_connection = get_db_connection()
        if db_connection.is_connected():
            cursor = db_connection.cursor(dictionary=True) # 以字典形式返回结果

            # 獲取總職缺數量
            count_query = "SELECT COUNT(*) AS total_count FROM jobs"
            cursor.execute(count_query)
            total_jobs_count = cursor.fetchone()['total_count']

            # 計算 OFFSET
            offset = (page - 1) * limit

            # 獲取分頁後的職缺資料
            jobs_query = "SELECT id, title, company_name, location, experience, education, salary_range, job_url, source_website, posting_date, crawled_at FROM jobs LIMIT %s OFFSET %s"
            cursor.execute(jobs_query, (limit, offset))
            jobs = cursor.fetchall()
            
            return jobs, total_jobs_count
    except Error as e:
        print(f"獲取所有職缺時發生錯誤: {e}")
        return None, 0
    finally:
        if cursor:
            cursor.close()
        if db_connection and db_connection.is_connected():
            db_connection.close()

def main():
    """主執行函式，用於獨立執行此腳本時進行初始化。"""
    print("正在執行資料庫初始化...")
    if init_db():
        print("資料庫初始化成功。")
    else:
        print("資料庫初始化失敗，請檢查 .env 設定或資料庫服務狀態。")

if __name__ == '__main__':
    main()