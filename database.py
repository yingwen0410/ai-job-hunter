"""
資料庫存取模組 (Data Access Layer)

本模組負責處理所有與 MySQL 資料庫的互動。
功能包括：
1. 管理資料庫連接池，提供穩定高效的連線。
2. 初始化資料庫，確保 'jobs' 與 'metadata' 資料表存在。
3. 封裝所有對資料表的 CRUD 操作，並提供模組級別的函式供外部調用。

採用參數化查詢以防止 SQL 注入攻擊。
採用環境變數來管理敏感的資料庫憑證。
"""

import mysql.connector
from mysql.connector import Error
from mysql.connector.pooling import MySQLConnectionPool
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class _Database: # 將類別名稱改為私有，表示不應直接從外部實例化
    def __init__(self):
        self.dbconfig = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'ai_job_hunter_db')
        }
        self.pool = None
        self._init_pool()
        self._init_table()
        print("資料庫模組初始化完成。")

    def _init_pool(self):
        """初始化資料庫連接池"""
        try:
            self.pool = MySQLConnectionPool(
                pool_name="mypool",
                pool_size=5,
                **self.dbconfig
            )
            print("成功建立資料庫連接池。")
        except Error as e:
            print(f"建立連接池時發生錯誤: {e}")
            raise

    def _init_table(self):
        """初始化資料表"""
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor()
            
            # 創建 jobs 表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    company VARCHAR(255) NOT NULL,
                    location VARCHAR(255),
                    experience VARCHAR(100),
                    education VARCHAR(100),
                    salary_range VARCHAR(100),
                    job_url VARCHAR(512) UNIQUE,
                    source_website VARCHAR(50),
                    posting_date VARCHAR(50),
                    industry VARCHAR(255),
                    status VARCHAR(20) DEFAULT 'unfollowed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            
            # 創建 metadata 表來儲存最後更新時間
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    meta_key VARCHAR(50) PRIMARY KEY,
                    meta_value VARCHAR(255)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            
            conn.commit()
            print("資料表初始化成功。")
        except Error as e:
            print(f"初始化資料表時發生錯誤: {e}")
            raise
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def _update_last_update_time(self, cursor):
        """內部函式，用於更新最後更新時間"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO metadata (meta_key, meta_value)
            VALUES ('last_update', %s)
            ON DUPLICATE KEY UPDATE meta_value = %s
        """, (now, now))


    def add_job(self, job_data):
        """添加或更新職缺，並在成功時更新最後時間戳"""
        conn = None
        cursor = None
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id FROM jobs WHERE job_url = %s",
                (job_data['job_url'],)
            )
            
            if cursor.fetchone():
                # 更新現有職缺 (不更新 status 和 created_at)
                query = """
                    UPDATE jobs SET
                    title = %s, company = %s, location = %s, experience = %s, education = %s,
                    salary_range = %s, source_website = %s, posting_date = %s, industry = %s
                    WHERE job_url = %s
                """
                params = (
                    job_data['title'], job_data['company'], job_data['location'],
                    job_data['experience'], job_data['education'], job_data['salary_range'],
                    job_data['source_website'], job_data['posting_date'], job_data['industry'],
                    job_data['job_url']
                )
            else:
                # 新增職缺
                query = """
                    INSERT INTO jobs (
                        title, company, location, experience, education, salary_range,
                        job_url, source_website, posting_date, industry
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                params = (
                    job_data['title'], job_data['company'], job_data['location'],
                    job_data['experience'], job_data['education'], job_data['salary_range'],
                    job_data['job_url'], job_data['source_website'],
                    job_data['posting_date'], job_data['industry']
                )

            cursor.execute(query, params)
            
            if cursor.rowcount > 0:
                self._update_last_update_time(cursor) # 更新時間戳
                conn.commit()
                print(f"成功處理職缺: {job_data['title']}")
                return True
            return False

        except Error as e:
            if conn:
                conn.rollback()
            print(f"處理職缺 '{job_data.get('title', 'N/A')}' 時發生錯誤: {e}")
            return False
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    def get_all_jobs(self, page=1, limit=10, keyword='', status=''):
        """根據條件獲取職缺列表（供 API 使用）"""
        conn = None
        cursor = None
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor(dictionary=True) # 回傳結果為字典
            
            query_conditions = []
            params = []
            
            if keyword:
                query_conditions.append("(title LIKE %s OR company LIKE %s)")
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            
            if status and status != 'all':
                query_conditions.append("status = %s")
                params.append(status)

            where_clause = "WHERE " + " AND ".join(query_conditions) if query_conditions else ""
            
            # 獲取總數
            cursor.execute(f"SELECT COUNT(*) as total FROM jobs {where_clause}", params)
            total = cursor.fetchone()['total']

            # 獲取分頁資料
            offset = (page - 1) * limit
            final_query = f"SELECT * FROM jobs {where_clause} ORDER BY posting_date DESC, id DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(final_query, params)
            jobs = cursor.fetchall()
            return jobs, total

        except Error as e:
            print(f"獲取職缺列表時發生錯誤: {e}")
            return None, 0
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    def update_job_status(self, job_id, new_status):
        """更新指定 ID 的職缺狀態"""
        conn = None
        cursor = None
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE jobs SET status = %s WHERE id = %s", (new_status, job_id))
            conn.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"更新職缺 {job_id} 狀態時發生錯誤: {e}")
            return False
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
                
    def get_last_update_time(self):
        """獲取最後更新時間"""
        conn = None
        cursor = None
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT meta_value FROM metadata WHERE meta_key = 'last_update'")
            result = cursor.fetchone()
            return result['meta_value'] if result else "尚未更新"
        except Error as e:
            print(f"獲取最後更新時間時發生錯誤: {e}")
            return "獲取失敗"
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

# --- 模組級別的接口 ---
# 建立一個全域的資料庫實例，讓整個應用程式共享
_db_instance = _Database()

# 提供外部直接呼叫的函式，這些函式會去操作唯一的 _db_instance
def add_job(job_data):
    return _db_instance.add_job(job_data)

def get_all_jobs(page=1, limit=10, keyword='', status=''):
    return _db_instance.get_all_jobs(page, limit, keyword, status)

def update_job_status(job_id, new_status):
    return _db_instance.update_job_status(job_id, new_status)

def get_last_update_time():
    return _db_instance.get_last_update_time()