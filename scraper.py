"""
網頁爬蟲模組 (Web Scraper) - Requests 版

本模組使用 Requests 搭配 BeautifulSoup 來爬取求職網站。
主要功能:
1. 透過 Requests 發送 HTTP 請求獲取資料。
2. 使用 BeautifulSoup 解析 HTML 內容。
3. 清洗並結構化爬取到的資料。
4. 將結構化資料傳遞給 database 模組進行儲存。
"""

import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import database
import json

print("--- 已成功匯入所有模組 ---")

# --- 爬蟲設定檔 ---
TARGET_CONFIG = {
    '104': {
        'url': 'https://www.104.com.tw/jobs/search/',
        'api_url': 'https://www.104.com.tw/jobs/search/list',
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Referer': 'https://www.104.com.tw/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        },
        'page_limit': 3,
        'params': {
            'keyword': 'AI 工程師',
            'order': '15',
            'page': 1,
            'mode': 's',
            'jobsource': '2018indexpoc',
            'langFlag': '0',
            'langStatus': '0',
            'recommendJob': '1',
            'hotJob': '1'
        }
    }
}

print("--- TARGET_CONFIG 設定檔已載入 ---")

def scrape_104_jobs(config):
    """
    專門爬取 104 人力銀行職缺的函式 (Requests 版)。
    """
    print("--- 已進入 scrape_104_jobs 函式 ---")
    job_count = 0
    session = requests.Session()
    
    for page in range(1, config['page_limit'] + 1):
        print(f"正在爬取第 {page} 頁...")
        config['params']['page'] = page
        page_job_count = 0
        
        try:
            # 發送 API 請求
            response = session.get(
                config['api_url'],
                headers=config['headers'],
                params=config['params']
            )
            response.raise_for_status()
            
            # 解析 JSON 回應
            data = response.json()
            jobs = data.get('data', {}).get('list', [])
            
            print(f"在第 {page} 頁找到 {len(jobs)} 個職缺。")
            
            for job in jobs:
                try:
                    job_data = {
                        'title': job.get('jobName', ''),
                        'company_name': job.get('custName', ''),
                        'location': job.get('area', '未提供'),
                        'experience': job.get('period', '未提供'),
                        'education': job.get('edu', '未提供'),
                        'salary_range': job.get('salary', '面議'),
                        'job_url': f"https://www.104.com.tw/job/{job.get('jobNo', '')}",
                        'source_website': '104'
                    }
                    
                    if database.add_job(job_data):
                        job_count += 1
                        page_job_count += 1
                        
                except Exception as e:
                    print(f"解析單一職缺時發生錯誤: {e}")
                    continue
            
            print(f"第 {page} 頁完成，新增了 {page_job_count} 筆職缺。")
            time.sleep(1)  # 避免請求過於頻繁
            
        except requests.exceptions.RequestException as e:
            print(f"請求失敗: {e}")
            continue
        except json.JSONDecodeError as e:
            print(f"解析 JSON 失敗: {e}")
            continue
        except Exception as e:
            print(f"發生未知錯誤: {e}")
            continue
    
    print(f"104 人力銀行爬取完成。")
    return job_count

def scrape_all_jobs():
    """主執行函式。"""
    print("--- 已進入 scrape_all_jobs 函式 ---")
    total_new_jobs = 0
    if '104' in TARGET_CONFIG:
        total_new_jobs += scrape_104_jobs(TARGET_CONFIG['104'])
    print(f"\n所有爬取任務完成，本次共新增 {total_new_jobs} 筆職缺。")

if __name__ == '__main__':
    print("--- 腳本即將進入 if __name__ == '__main__' 主程式區塊 ---")
    scrape_all_jobs()
    print("--- 主程式區塊執行完畢 ---")




