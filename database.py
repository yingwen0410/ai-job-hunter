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
                status VARCHAR(50) DEFAULT '未關注',
                crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                industry VARCHAR(100)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            cursor.execute(create_table_query)
            print("資料表 'jobs' 已確認存在。")

            try:
                cursor.execute("ALTER TABLE jobs ADD COLUMN status VARCHAR(50) DEFAULT '未關注' AFTER posting_date")
                print("成功新增 status 欄位")
            except Error as e:
                if "Duplicate column name" in str(e):
                    print("status 欄位已存在")
                else:
                    raise e
            
            try:
                cursor.execute("ALTER TABLE jobs ADD COLUMN industry VARCHAR(100) AFTER crawled_at")
                print("成功新增 industry 欄位")
            except Error as e:
                if "Duplicate column name" in str(e):
                    print("industry 欄位已存在")
                else:
                    raise e
            
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
    如果職缺已存在 (依 job_url 判斷)，則更新其資料。
    """
    db_connection = None
    cursor = None
    
    query = """
    INSERT INTO jobs (title, company_name, location, experience, education, salary_range, job_url, source_website, posting_date, status, industry)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        title = VALUES(title),
        company_name = VALUES(company_name),
        location = VALUES(location),
        experience = VALUES(experience),
        education = VALUES(education),
        salary_range = VALUES(salary_range),
        source_website = VALUES(source_website),
        posting_date = VALUES(posting_date),
        industry = VALUES(industry)
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
        job_data.get('posting_date'),
        job_data.get('status', '未關注'),
        job_data.get('industry', '')
    )

    try:
        db_connection = get_db_connection()
        if db_connection.is_connected():
            cursor = db_connection.cursor()
            cursor.execute(query, values)
            db_connection.commit()
            # rowcount > 0 表示有新增或更新，rowcount == 0 表示沒有改變 (例如，所有值都相同)
            return True
    except Error as e:
        print(f"新增或更新職缺時發生錯誤: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if db_connection and db_connection.is_connected():
            db_connection.close()

def get_all_jobs(page=1, limit=10, keyword=None, status=None):
    """
    獲取所有職缺資料，支持分頁、關鍵字搜尋和狀態篩選。
    
    Args:
        page (int): 當前頁碼，從 1 開始
        limit (int): 每頁顯示數量
        keyword (str): 搜尋關鍵字
        status (str): 職缺狀態篩選
        
    Returns:
        tuple: (職缺列表, 總數量)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)  # 使用字典游标
        
        # 構建 WHERE 子句
        where_clauses = []
        params = []
        
        if keyword:
            where_clauses.append("(title LIKE %s OR company_name LIKE %s)")
            params.extend([f'%{keyword}%', f'%{keyword}%'])
            
        if status:
            where_clauses.append("status = %s")
            params.append(status)
            
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # 獲取總數
        count_sql = f"SELECT COUNT(*) as total_count FROM jobs WHERE {where_sql}"
        cursor.execute(count_sql, params)
        total = cursor.fetchone()['total_count']
        
        # 獲取分頁數據
        offset = (page - 1) * limit
        sql = f"""
            SELECT * FROM jobs 
            WHERE {where_sql}
            ORDER BY id DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        cursor.execute(sql, params)
        jobs = cursor.fetchall()
        
        return jobs, total
        
    except Exception as e:
        print(f"獲取職缺列表時發生錯誤: {e}")
        return None, 0
    finally:
        if conn:
            conn.close()

def update_job_status(job_id, new_status):
    """
    更新單一職缺的狀態。
    """
    db_connection = None
    cursor = None
    try:
        db_connection = get_db_connection()
        if db_connection.is_connected():
            cursor = db_connection.cursor()
            query = "UPDATE jobs SET status = %s WHERE id = %s"
            cursor.execute(query, (new_status, job_id))
            db_connection.commit()
            if cursor.rowcount > 0:
                print(f"成功更新職缺 ID {job_id} 的狀態為 {new_status}")
                return True
            else:
                print(f"未找到職缺 ID {job_id} 或狀態未改變")
                return False
    except Error as e:
        print(f"更新職缺狀態時發生錯誤: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if db_connection and db_connection.is_connected():
            db_connection.close()

def get_last_update_time():
    """获取最后一次爬虫更新的时间"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(crawled_at) FROM jobs")
        last_update = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return last_update.strftime('%Y-%m-%d %H:%M:%S') if last_update else None
    except Exception as e:
        print(f"获取最后更新时间时发生错误: {str(e)}")
        return None

def main():
    """主執行函式，用於獨立執行此腳本時進行初始化。"""
    print("正在執行資料庫初始化...")
    if init_db():
        print("資料庫初始化成功。")
    else:
        print("資料庫初始化失敗，請檢查 .env 設定或資料庫服務狀態。")

if __name__ == '__main__':
    main()