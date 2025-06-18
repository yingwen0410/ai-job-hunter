import { currentKeyword, currentStatus, currentPage, currentLimit, loadJobs } from './main.js';

// 構建 API URL
const buildApiUrl = () => {
    const baseUrl = '/api/jobs';
    const params = new URLSearchParams({
        page: currentPage,
        limit: currentLimit
    });

    if (currentKeyword) {
        params.append('keyword', currentKeyword);
    }

    if (currentStatus !== 'all') {
        params.append('status', currentStatus);
    }

    return `${baseUrl}?${params.toString()}`;
};

// 清除篩選
const clearFilters = () => {
    currentKeyword = '';
    currentStatus = 'all';
    currentPage = 1;
    document.getElementById('search-keyword').value = '';
    updateStatusFilterButtons();
    loadJobs();
};

// 更新狀態篩選按鈕
const updateStatusFilterButtons = () => {
    document.querySelectorAll('.status-filter-btn').forEach(button => {
        if (button.dataset.status === currentStatus) {
            button.classList.add('active');
        } else {
            button.classList.remove('active');
        }
    });
};

// 導出需要的函數
export {
    buildApiUrl,
    clearFilters,
    updateStatusFilterButtons
}; 