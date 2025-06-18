console.log('[DEBUG pagination.js] pagination.js 已載入。');

// 渲染分頁
export function renderPagination(currentPage, totalPages) {
    const prevButton = document.getElementById('prev-page');
    const nextButton = document.getElementById('next-page');
    const pageNumbers = document.getElementById('page-numbers');

    if (!prevButton || !nextButton || !pageNumbers) return;

    // 更新上一頁/下一頁按鈕狀態
    prevButton.disabled = currentPage === 1;
    nextButton.disabled = currentPage === totalPages;

    // 更新頁碼按鈕
    pageNumbers.innerHTML = '';
    
    // 計算要顯示的頁碼範圍
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, startPage + 4);
    if (endPage - startPage < 4) {
        startPage = Math.max(1, endPage - 4);
    }

    // 添加第一頁按鈕（如果不在範圍內）
    if (startPage > 1) {
        pageNumbers.appendChild(createPageButton(1));
        if (startPage > 2) {
            const ellipsis = document.createElement('span');
            ellipsis.textContent = '...';
            ellipsis.className = 'px-2';
            pageNumbers.appendChild(ellipsis);
        }
    }

    // 添加頁碼按鈕
    for (let i = startPage; i <= endPage; i++) {
        const pageButton = createPageButton(i);
        if (i === currentPage) pageButton.classList.add('active');
        pageNumbers.appendChild(pageButton);
    }

    // 添加最後一頁按鈕（如果不在範圍內）
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            const ellipsis = document.createElement('span');
            ellipsis.textContent = '...';
            ellipsis.className = 'px-2';
            pageNumbers.appendChild(ellipsis);
        }
        pageNumbers.appendChild(createPageButton(totalPages));
    }
}

// 創建頁碼按鈕
function createPageButton(pageNumber) {
    const button = document.createElement('button');
    button.className = 'page-number';
    button.textContent = pageNumber;
    button.addEventListener('click', () => changePage(pageNumber));
    return button;
}

export function setupPagination(totalPages) {
    const prevButton = document.getElementById('prev-page');
    const nextButton = document.getElementById('next-page');
    if (!prevButton || !nextButton) return;

    // 移除舊的事件監聽器
    const newPrevButton = prevButton.cloneNode(true);
    const newNextButton = nextButton.cloneNode(true);
    prevButton.parentNode.replaceChild(newPrevButton, prevButton);
    nextButton.parentNode.replaceChild(newNextButton, nextButton);

    // 上一頁按鈕事件
    newPrevButton.addEventListener('click', () => {
        const currentPage = parseInt(document.querySelector('.page-number.active')?.textContent || '1');
        if (currentPage > 1) changePage(currentPage - 1);
    });

    // 下一頁按鈕事件
    newNextButton.addEventListener('click', () => {
        const currentPage = parseInt(document.querySelector('.page-number.active')?.textContent || '1');
        if (currentPage < totalPages) changePage(currentPage + 1);
    });
}

// 切換頁面
export function changePage(page) {
    document.dispatchEvent(new CustomEvent('pageChange', { 
        detail: { page: parseInt(page) },
        bubbles: true
    }));
} 