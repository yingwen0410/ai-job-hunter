"""
資料庫存取模組 (Data Access Layer) - FINAL VERSION

本模組負責處理所有與 MySQL 資料庫的互動。
功能包括：
1. 管理資料庫連接池，提供穩定高效的連線。
2. 初始化資料庫，確保 'jobs' 資料表存在且結構完整。
3. 封裝所有對 'jobs' 資料表的 CRUD 操作，並提供模組級別的函式供外部調用。
"""

import mysql.connector
from mysql.connector import Error
from mysql.connector.pooling import MySQLConnectionPool
import os
from dotenv import load_dotenv
from datetime import datetime

# 載入環境變數
load_dotenv()

class _Database:
    """
    私有類別，管理資料庫底層連線與操作。
    不應從外部直接實例化。
    """
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
        """初始化資料表，確保結構最新"""
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor()

            # 建立 jobs 表，並新增 job_description 欄位
            # 使用 ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 以支援 emoji 和特殊字元
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
                    job_description TEXT,
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
            print("資料表結構初始化/驗證成功。")
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

    def add_job(self, job_data: dict):
        """
        【重構後】使用 INSERT ... ON DUPLICATE KEY UPDATE 新增或更新職缺。
        這種方式更簡潔、高效，且能保證資料的原子性。
        """
        conn = None
        cursor = None
        
        # SQL 語句：如果 job_url 已存在，則更新指定欄位；否則，插入新的一筆。
        # 這樣就不用先 SELECT 再決定要 INSERT 或 UPDATE，一次搞定。
        query = """
            INSERT INTO jobs (
                job_url, title, company, location, experience, education,
                salary_range, source_website, posting_date, industry, job_description
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                company = VALUES(company),
                location = VALUES(location),
                experience = VALUES(experience),
                education = VALUES(education),
                salary_range = VALUES(salary_range),
                source_website = VALUES(source_website),
                posting_date = VALUES(posting_date),
                industry = VALUES(industry),
                job_description = VALUES(job_description),
                updated_at = CURRENT_TIMESTAMP;
        """
        
        # 準備要插入/更新的資料元組 (tuple)，順序必須與 INSERT 的欄位完全對應
        params = (
            job_data.get('job_url'),
            job_data.get('title'),
            job_data.get('company'),
            job_data.get('location'),
            job_data.get('experience'),
            job_data.get('education'),
            job_data.get('salary_range'),
            job_data.get('source_website'),
            job_data.get('posting_date'),
            job_data.get('industry'),
            job_data.get('job_description')
        )
        
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(query, params)
            
            # cursor.rowcount 在 INSERT 時返回 1，在 UPDATE 時返回 2，在未變動時返回 0
            if cursor.rowcount > 0:
                action = "新增" if cursor.rowcount == 1 else "更新"
                print(f"成功 {action} 職缺: {job_data.get('title', 'N/A')}")
            
            # 不論是新增還是更新，都更新最後操作時間
            self._update_last_update_time(cursor)
            conn.commit()
            return True

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
                # 搜尋範圍包含職稱、公司、以及新的職缺描述欄位
                query_conditions.append("(title LIKE %s OR company LIKE %s OR job_description LIKE %s)")
                params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
            
            if status and status != 'all':
                query_conditions.append("status = %s")
                params.append(status)

            where_clause = "WHERE " + " AND ".join(query_conditions) if query_conditions else ""
            
            cursor.execute(f"SELECT COUNT(*) as total FROM jobs {where_clause}", tuple(params))
            total = cursor.fetchone()['total']

            offset = (page - 1) * limit
            final_query = f"SELECT * FROM jobs {where_clause} ORDER BY posting_date DESC, id DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(final_query, tuple(params))
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

# 提供外部直接呼叫的函式
def add_job(job_data: dict) -> bool:
    return _db_instance.add_job(job_data)

def get_all_jobs(page=1, limit=10, keyword='', status=''):
    return _db_instance.get_all_jobs(page, limit, keyword, status)

def update_job_status(job_id, new_status):
    return _db_instance.update_job_status(job_id, new_status)

def get_last_update_time():
    return _db_instance.get_last_update_time()

# 測試區塊
if __name__ == '__main__':
    print("\n--- 正在測試資料庫模組 ---")
    try:
        # 測試 add_job (新增)
        print("\n[測試1] 新增一筆假資料...")
        add_job({
            'job_url': 'https://example.com/job/1',
            'title': '測試工程師',
            'company': '測試公司',
            'job_description': '這是一個詳細的職務描述。'
        })
        
        # 測試 add_job (更新)
        print("\n[測試2] 更新同一筆假資料...")
        add_job({
            'job_url': 'https://example.com/job/1',
            'title': '資深測試工程師',
            'company': '測試公司',
            'job_description': '這是更新後的詳細職務描述。'
        })

        # 測試 get_all_jobs
        print("\n[測試3] 獲取所有職缺...")
        jobs, total = get_all_jobs(limit=5)
        if jobs is not None:
            print(f"獲取到 {len(jobs)} 筆職缺，總數為 {total}。")
            # print("第一筆職缺:", jobs[0] if jobs else "無")
        
        print("\n--- 資料庫模組測試完畢 ---")

    except Exception as e:
        print(f"測試過程中發生錯誤: {e}")