// 創建職缺卡片
export function createJobCard(job) {
    const card = document.createElement('div');
    card.className = 'job-card';
    
    // 根據來源網站設置標籤樣式
    const sourceClass = job.source_website === '104人力銀行' ? 'source-104' : 'source-1111';
    
    card.innerHTML = `
        <div class="job-card-banner ${sourceClass}">
            <div class="job-card-banner-inner">
                <div class="job-banner-row1">
                    <span class="job-title">${job.title}</span>
                </div>
                <div class="job-banner-row2">
                    <span class="job-company">${job.company}</span>
                </div>
            </div>
        </div>
        <div class="job-details">
            <div class="job-detail"><span class="detail-icon">📍</span><span>${job.location}</span></div>
            <div class="job-detail"><span class="detail-icon">🎓</span><span>${job.education}</span></div>
            <div class="job-detail"><span class="detail-icon">💼</span><span>${job.experience}</span></div>
            <div class="job-detail"><span class="detail-icon">💰</span><span>${job.salary_range}</span></div>
            <div class="job-detail"><span class="detail-icon">🏢</span><span>${job.industry || '未提供'}</span></div>
            <div class="job-detail"><span class="detail-icon">🗓️</span><span>${job.posting_date}</span></div>
        </div>
        <div class="job-card-actions" style="display: flex; flex-direction: column; gap: 0.5rem;">
            <a href="/jobs/${job.id}" class="button button-primary" target="_blank" style="align-self: stretch; margin-bottom: 0.5rem;">✨ AI 履歷分析</a>
            <div style="display: flex; justify-content: space-between; gap: 0.5rem;">
                <select class="status-select ${job.status ? job.status.toLowerCase() : ''}" data-job-id="${job.id}" style="flex:1; max-width: 50%;">
                    <option value="unfollowed" ${!job.status || job.status === 'unfollowed' ? 'selected' : ''}>未追蹤</option>
                    <option value="followed" ${job.status === 'followed' ? 'selected' : ''}>已追蹤</option>
                    <option value="applied" ${job.status === 'applied' ? 'selected' : ''}>已應徵</option>
                    <option value="rejected" ${job.status === 'rejected' ? 'selected' : ''}>不合適</option>
                </select>
                <a href="${job.job_url}" target="_blank" style="flex:1; max-width: 50%; text-align:left; color:#2563eb; background:none; border:none; box-shadow:none; font-weight:400; text-decoration:underline; display:inline-block; padding:0; margin-left:0.5rem;">
                    <span style="font-size:1.1em;">🔗</span> 查看原始職缺
                </a>
            </div>
        </div>
    `;
    
    // 動態設置卡片底部對齊
    card.style.display = 'flex';
    card.style.flexDirection = 'column';
    const actions = card.querySelector('.job-card-actions');
    if (actions) {
        actions.style.marginTop = 'auto';
    }
    
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
export async function updateJobStatus(jobId, newStatus) {
    try {
        const response = await fetch(`/api/jobs/${jobId}/status`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
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