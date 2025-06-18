import { createJobCard, updateJobStatus } from './jobCard.js';
import { renderPagination, setupPagination, changePage } from './pagination.js';

console.log('[DEBUG main.js] main.js 已載入。');
console.log('[DEBUG main.js] updateJobStatus 函數狀態：', typeof updateJobStatus);

// 全局變量
let currentPage = 1;
let currentLimit = 10;
let currentStatus = 'all';
let currentKeyword = '';
let totalJobs = 0;

// DOM 元素
const jobsContainer = document.getElementById('job-listings-container');
const loadingSpinner = document.getElementById('loading-spinner');
const errorMessage = document.getElementById('error-message');
const searchKeywordInput = document.getElementById('search-keyword');
const searchButton = document.getElementById('search-button');
const lastUpdateTime = document.getElementById('last-update-time');
const itemsPerPage = document.getElementById('items-per-page');

const API_URL = '/api/jobs';

// 載入職缺數據
const loadJobs = async (page = 1) => {
    console.log('loadJobs 函數被呼叫，頁碼：', page);
    try {
        loadingSpinner.classList.remove('hidden');
        errorMessage.classList.add('hidden');
        
        const response = await fetch(`${API_URL}?page=${page}&limit=${currentLimit}&status=${currentStatus}&keyword=${currentKeyword}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('從 API 接收到的資料：', data);
        
        totalJobs = data.total_jobs_count;
        currentPage = page; // 更新當前頁碼
        renderJobs(data.jobs);
        const totalPages = Math.ceil(totalJobs / currentLimit);
        renderPagination(currentPage, totalPages);
        setupPagination(totalPages);

        // 更新職缺總數
        const totalJobsElement = document.getElementById('total-jobs');
        if (totalJobsElement) {
            totalJobsElement.textContent = totalJobs;
        }

        // 更新最後更新時間
        const lastUpdateElement = document.getElementById('last-update-time');
        if (lastUpdateElement) {
            lastUpdateElement.textContent = new Date().toLocaleString('zh-TW');
        }
    } catch (error) {
        console.error('Error loading jobs:', error);
        errorMessage.classList.remove('hidden');
    } finally {
        loadingSpinner.classList.add('hidden');
        console.log('loadJobs 函數執行完畢。');
    }
};

// 渲染職缺列表
const renderJobs = (jobs) => {
    console.log('renderJobs 函數被呼叫，將渲染職缺數量：', jobs.length);
    if (!jobsContainer) {
        console.error('jobsContainer 元素未找到！');
        return;
    }
    console.log('jobsContainer 元素：', jobsContainer);
    jobsContainer.innerHTML = '';
    if (jobs.length === 0) {
        console.log('沒有職缺資料可顯示。');
        jobsContainer.innerHTML = '<p class="no-jobs-message">目前沒有符合條件的職缺。</p>';
        return;
    }
    jobs.forEach(job => {
        const card = createJobCard(job);
        jobsContainer.appendChild(card);
    });
    // 為新載入的職缺卡片設置狀態更新事件監聽器
    setupJobCardEventListeners();
};

// 設置事件監聽器
const setupEventListeners = () => {
    // 搜尋按鈕點擊事件
    searchButton.addEventListener('click', () => {
        currentKeyword = searchKeywordInput.value.trim();
        currentPage = 1;
        loadJobs();
    });

    // 搜尋框回車事件
    searchKeywordInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            currentKeyword = searchKeywordInput.value.trim();
            currentPage = 1;
            loadJobs();
        }
    });

    // 每頁顯示數量變更事件
    itemsPerPage.addEventListener('change', () => {
        currentLimit = parseInt(itemsPerPage.value);
        currentPage = 1;
        loadJobs();
    });

    // 狀態篩選按鈕點擊事件
    document.querySelectorAll('.filter-button').forEach(button => {
        button.addEventListener('click', () => {
            // 移除所有按鈕的 active 類
            document.querySelectorAll('.filter-button').forEach(btn => {
                btn.classList.remove('active');
            });
            // 添加當前按鈕的 active 類
            button.classList.add('active');
            currentStatus = button.dataset.status;
            currentPage = 1;
            loadJobs();
        });
    });

    // 監聽頁面切換事件
    document.addEventListener('pageChange', (event) => {
        const newPage = event.detail.page;
        console.log('頁面切換事件觸發，新頁碼：', newPage);
        if (newPage !== currentPage) {
            loadJobs(newPage);
        }
    });
};

// 初始化
const init = () => {
    console.log('DOMContentLoaded 事件觸發。');
    setupEventListeners();
    loadJobs();
    fetchLastUpdate();
};

// 當 DOM 完全載入後執行初始化
document.addEventListener('DOMContentLoaded', init);

// 獲取最後更新時間
const fetchLastUpdate = () => {
    fetch('/api/last-update')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.last_update) {
                lastUpdateTime.textContent = data.last_update;
            } else {
                lastUpdateTime.textContent = '無法獲取更新時間';
            }
        })
        .catch(error => {
            console.error('Error fetching last update time:', error);
            lastUpdateTime.textContent = '無法獲取更新時間';
        });
};

// 為職缺卡片上的狀態選單設置事件監聽器
const setupJobCardEventListeners = () => {
    jobsContainer.addEventListener('change', (event) => {
        const select = event.target.closest('.status-select');
        if (select) {
            const jobId = select.dataset.jobId;
            const newStatus = select.value;
            console.log(`[DEBUG main.js] 狀態選單變更 - Job ID: ${jobId}, 新狀態: ${newStatus}`);
            updateJobStatus(jobId, newStatus).then(() => {
                // 只在狀態更新成功後重新載入職缺列表
                loadJobs();
            });
        }
    });
};

// 導出需要的函數和變量
export {
    currentPage,
    currentLimit,
    currentStatus,
    currentKeyword,
    totalJobs,
    jobsContainer,
    loadingSpinner,
    errorMessage,
    loadJobs,
    renderJobs
}; 