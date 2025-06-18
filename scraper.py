"""
網頁爬蟲模組 (Web Scraper) - Requests 版

本模組使用 Requests 來爬取求職網站。
目前專注於穩定爬取 104 人力銀行。
"""
import time
import requests
import database

# --- 爬蟲設定檔 ---
TARGET_CONFIG = {
    '104': {
        'api_url': 'https://www.104.com.tw/jobs/search/list',
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'Referer': 'https://www.104.com.tw/jobs/search/',
            'Accept': 'application/json, text/plain, */*',
        },
        'params': {
            'keyword': '', 'order': '15', 'page': 1, 'mode': 's',
            'jobsource': '2018indexpoc'
        }
    }
}

print("--- TARGET_CONFIG 設定檔已載入 ---")

def convert_104_experience(exp_code):
    """將 104 的工作經歷代碼轉換為可讀文本"""
    exp_map = {'01': '無經驗', '02': '1年以下', '03': '1-3年', '04': '3-5年', '05': '5-10年', '06': '10年以上'}
    return exp_map.get(exp_code, '經歷不拘')

def scrape_104_jobs(config, keyword, page_limit):
    """專門爬取 104 人力銀行職缺的函式"""
    print("\n--- 開始爬取 104 人力銀行 (Requests) ---")
    job_count = 0
    session = requests.Session()
    params = config['params'].copy()
    params['keyword'] = keyword
    for page in range(1, page_limit + 1):
        params['page'] = page
        print(f"[104] 正在爬取第 {page} 頁...")
        page_job_count = 0
        try:
            response = session.get(config['api_url'], headers=config['headers'], params=params)
            response.raise_for_status()
            data = response.json()
            jobs = data.get('data', {}).get('list', [])
            if not jobs:
                print("[104] 此頁沒有更多職缺，停止爬取。")
                break
            for job in jobs:
                job_data = {
                    'title': job.get('jobName', ''),
                    'company': job.get('custName', ''),
                    'location': f"{job.get('jobAddrNoDesc', '')}{job.get('jobAddress', '')}".strip(),
                    'experience': convert_104_experience(job.get('period', '')),
                    'education': job.get('optionEdu', '未提供'),
                    'salary_range': job.get('salaryDesc', '面議'),
                    'job_url': f"https:{job.get('link', {}).get('job', '')}",
                    'source_website': '104人力銀行',
                    'posting_date': job.get('appearDate', ''),
                    'industry': job.get('coIndustryDesc', '')
                }
                if database.add_job(job_data):
                    job_count += 1
                    page_job_count += 1
            print(f"[104] 第 {page} 頁完成，新增了 {page_job_count} 筆職缺。")
            time.sleep(1)
        except Exception as e:
            print(f"[104] 爬取第 {page} 頁時發生錯誤: {e}")
            break
    print(f"--- 104 人力銀行爬取完成，共新增 {job_count} 筆職缺 ---")
    return job_count

def scrape_all_jobs(keyword='AI 工程師', page_limit=3):
    """主執行函式。"""
    print("--- 已進入 scrape_all_jobs 函式 ---")
    total_new_jobs = 0
    if '104' in TARGET_CONFIG:
        total_new_jobs += scrape_104_jobs(TARGET_CONFIG['104'], keyword, page_limit)
    
    # 暫時移除了 1111 的部分
    
    print(f"\n所有爬取任務完成，本次共新增 {total_new_jobs} 筆職缺。")

if __name__ == '__main__':
    scrape_all_jobs(keyword='AI 工程師', page_limit=2)
    print("--- 主程式區塊執行完畢 ---")