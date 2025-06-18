// 創建職缺卡片
export function createJobCard(job) {
    const card = document.createElement('div');
    card.className = 'job-card';
    
    // 根据来源网站设置标签样式
    const sourceClass = job.source_website === '104人力銀行' ? 'source-104' : 'source-1111';
    
    card.innerHTML = `
        <div class="job-header">
            <h3 class="job-title">${job.title}</h3>
            <span class="source-badge ${sourceClass}">${job.source_website}</span>
        </div>
        <div class="job-company">${job.company}</div>
        <div class="job-details">
            <div class="job-detail">
                <i class="fas fa-map-marker-alt"></i>
                <span>${job.location}</span>
            </div>
            <div class="job-detail">
                <i class="fas fa-calendar-alt"></i>
                <span>${job.posting_date}</span>
            </div>
            <div class="job-detail">
                <i class="fas fa-graduation-cap"></i>
                <span>${job.education}</span>
            </div>
            <div class="job-detail">
                <i class="fas fa-briefcase"></i>
                <span>${job.experience}</span>
            </div>
            <div class="job-detail">
                <i class="fas fa-money-bill-wave"></i>
                <span>${job.salary_range}</span>
            </div>
            <div class="job-detail">
                <i class="fas fa-building"></i>
                <span>${job.industry || '未提供'}</span>
            </div>
        </div>
        <div class="job-footer">
            <select class="status-select" onchange="updateJobStatus('${job.job_url}', this.value)">
                <option value="unfollowed" ${job.status === 'unfollowed' ? 'selected' : ''}>未追蹤</option>
                <option value="followed" ${job.status === 'followed' ? 'selected' : ''}>已追蹤</option>
                <option value="applied" ${job.status === 'applied' ? 'selected' : ''}>已應徵</option>
                <option value="unsuitable" ${job.status === 'unsuitable' ? 'selected' : ''}>不適合</option>
            </select>
            <a href="${job.job_url}" target="_blank" class="view-job-btn">查看職缺</a>
        </div>
    `;
    
    return card;
}

// 獲取狀態樣式類
const getStatusClass = (status) => {
    switch (status) {
        case '未關注':
            return 'unfollowed';
        case '已關注':
            return 'followed';
        case '已投遞':
            return 'applied';
        case '不合適':
            return 'unsuitable';
        default:
            return 'unfollowed';
    }
};

// 更新職缺狀態
export async function updateJobStatus(jobUrl, newStatus) {
    try {
        const response = await fetch('/api/jobs/status', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                job_url: jobUrl,
                status: newStatus
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to update job status');
        }
        
        // 更新成功，可以在这里添加一些视觉反馈
        console.log('Job status updated successfully');
    } catch (error) {
        console.error('Error updating job status:', error);
        // 可以在这里添加错误提示
    }
}