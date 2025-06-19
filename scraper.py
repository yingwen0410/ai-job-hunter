"""
網頁爬蟲模組 (Web Scraper) - FINAL VERSION

本模組使用 Requests 搭配 BeautifulSoup 來爬取求職網站，並能抓取完整的職缺描述(JD)。
"""
import time
import requests
import database
import re
from bs4 import BeautifulSoup

# --- 爬蟲設定檔 ---
TARGET_CONFIG = {
    '104': {
        'api_url': 'https://www.104.com.tw/jobs/search/list',
        'content_api_url': 'https://www.104.com.tw/job/ajax/content/{job_id}', # 此行已不再使用，但保留以備不時之需
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'Referer': 'https://www.104.com.tw/jobs/search/',
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
    """
    使用 Requests + BeautifulSoup 爬取 104 職缺，包含完整的職缺描述 (JD)。
    """
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
            # 1. 獲取職缺列表 API
            list_response = session.get(config['api_url'], headers=config['headers'], params=params)
            list_response.raise_for_status()
            data = list_response.json()
            jobs = data.get('data', {}).get('list', [])
            if not jobs:
                print("[104] 此頁沒有更多職缺，停止爬取。")
                break
            
            print(f"[104] 在第 {page} 頁找到 {len(jobs)} 個職缺，開始深入抓取 JD...")
            for job in jobs:
                try:
                    job_url = f"https:{job.get('link', {}).get('job', '')}"
                    job_description = ""
                    
                    # 2. 直接請求職缺的網頁 URL
                    page_response = session.get(job_url, headers=config['headers'])
                    if page_response.status_code == 200:
                        # 3. 使用 BeautifulSoup 解析 HTML
                        soup = BeautifulSoup(page_response.text, 'lxml')
                        
                        # --- vvvvvv 【核心修改】 vvvvvv ---
                        # 4. 使用更新後、更穩定的選擇器來尋找 JD 元素
                        description_element = soup.select_one('div[data-qa-id="jobDescription"]')
                        # --- ^^^^^^ 【核心修改】 ^^^^^^ ---

                        if description_element:
                            job_description = description_element.text.strip()
                        else:
                             print(f"[104] 在 {job_url} 頁面中找不到 JD 元素，可能頁面結構已變更。")
                    
                    # 5. 組合完整的職缺資料
                    job_data = {
                        'title': job.get('jobName', ''),
                        'company': job.get('custName', ''),
                        'location': f"{job.get('jobAddrNoDesc', '')}{job.get('jobAddress', '')}".strip(),
                        'experience': convert_104_experience(job.get('period', '')),
                        'education': job.get('optionEdu', '未提供'),
                        'salary_range': job.get('salaryDesc', '面議'),
                        'job_url': job_url,
                        'source_website': '104人力銀行',
                        'posting_date': job.get('appearDate', ''),
                        'industry': job.get('coIndustryDesc', ''),
                        'job_description': job_description
                    }

                    if database.add_job(job_data):
                        job_count += 1
                        page_job_count += 1

                except Exception as e:
                    print(f"[104] 解析職缺 {job.get('jobName', '')} 時發生錯誤: {e}")

            print(f"[104] 第 {page} 頁完成，新增/更新了 {page_job_count} 筆職缺。")
            time.sleep(2) 
        except Exception as e:
            print(f"[104] 爬取第 {page} 頁列表時發生錯誤: {e}")
            break
            
    print(f"--- 104 人力銀行爬取完成，共新增/更新 {job_count} 筆職缺 ---")
    return job_count

def scrape_all_jobs(keyword='AI 工程師', page_limit=2):
    """主執行函式。"""
    print("--- 已進入 scrape_all_jobs 函式 ---")
    total_new_jobs = 0
    if '104' in TARGET_CONFIG:
        total_new_jobs += scrape_104_jobs(TARGET_CONFIG['104'], keyword, page_limit)
    print(f"\n所有爬取任務完成，本次共新增/更新 {total_new_jobs} 筆職缺。")

if __name__ == '__main__':
    scrape_all_jobs()
    print("--- 主程式區塊執行完畢 ---")