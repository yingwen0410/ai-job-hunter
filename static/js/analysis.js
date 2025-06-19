// 檔案: static/js/analysis.js

document.getElementById('resumeAnalysisForm').addEventListener('submit', async function(event) {
    event.preventDefault(); // 防止表單直接提交

    const resumeFile = document.getElementById('resumeFile').files[0];
    if (!resumeFile) {
        alert('請先選擇要上傳的履歷檔案！');
        return;
    }

    const aiResultDiv = document.getElementById('aiResult');
    const loader = document.getElementById('loader');
    const formData = new FormData();
    formData.append('resume', resumeFile);

    // 顯示讀取動畫，清空舊結果
    loader.classList.remove('hidden');
    aiResultDiv.innerHTML = '';

    try {
        // 使用從 HTML 中獲取的 JOB_ID
        const response = await fetch(`/api/jobs/${JOB_ID}/match`, {
            method: 'POST',
            body: formData,
        });

        const result = await response.json();

        // 隱藏讀取動畫
        loader.classList.add('hidden');

        if (response.ok) {
            // 如果成功，就呼叫函式來渲染結果
            renderAnalysisResult(result);
        } else {
            // 如果失敗，顯示錯誤訊息
            aiResultDiv.innerHTML = `<p><strong>分析失敗：</strong>${result.error || '未知錯誤'}</p><p>詳細資訊: ${result.details || ''}</p>`;
        }

    } catch (error) {
        loader.classList.add('hidden');
        aiResultDiv.innerHTML = `<p><strong>前端請求時發生錯誤：</strong>${error}</p>`;
    }
});

function renderAnalysisResult(data) {
    const aiResultDiv = document.getElementById('aiResult');

    // 清理之前的內容
    aiResultDiv.innerHTML = '';

    // 新增：匹配度分數 Dashboard
    let scoreHTML = '';
    if (typeof data.match_score === 'number') {
        // 分數顏色與說明
        let color = '#4f8cff';
        let label = '普通';
        if (data.match_score >= 80) {
            color = '#00c853'; // 綠
            label = '非常適合';
        } else if (data.match_score >= 60) {
            color = '#ffd600'; // 黃
            label = '普通';
        } else {
            color = '#ff5252'; // 紅
            label = '需加強';
        }
        scoreHTML = `
        <div class="score-dashboard">
            <div class="score-circle" style="background: linear-gradient(135deg, ${color} 60%, #e0e0e0 100%);">
                <span class="score-value">${data.match_score}</span>
                <span class="score-unit">/100</span>
            </div>
            <div class="score-label">履歷與職缺匹配度</div>
            <div class="score-desc" style="color: ${color};">${label}</div>
        </div>
        <style>
        .score-dashboard {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-bottom: 24px;
        }
        .score-circle {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin-bottom: 8px;
        }
        .score-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: #fff;
        }
        .score-unit {
            font-size: 1rem;
            color: #e0e0e0;
        }
        .score-label {
            font-size: 1.1rem;
            color: #333;
            font-weight: 500;
        }
        .score-desc {
            font-size: 1.1rem;
            font-weight: bold;
            margin-top: 2px;
        }
        </style>
        `;
    }

    // 卡片式設計 + 圖示與色彩引導
    const strengthsHTML = `
        <div class="ai-card ai-card-strengths">
            <div class="ai-card-header">
                <span class="ai-card-icon">✅</span>
                <span class="ai-card-title">強項分析</span>
            </div>
            <ul class="ai-card-list">
                ${data.strengths_analysis.map(item => 
                    `<li><strong>${item.skill}</strong>：${item.relevance}</li>`
                ).join('')}
            </ul>
        </div>
    `;

    const gapsHTML = `
        <div class="ai-card ai-card-gaps">
            <div class="ai-card-header">
                <span class="ai-card-icon">⚠️</span>
                <span class="ai-card-title">技能差距</span>
            </div>
            <ul class="ai-card-list">
                ${data.skill_gaps.map(item =>
                    `<li><span class="tag ${item.importance === '核心要求' ? 'core' : 'plus'}">${item.importance === '核心要求' ? '核心' : '加分'}</span> 缺少：<span class="${item.importance === '核心要求' ? 'core-skill' : 'plus-skill'}">${item.skill}</span></li>`
                ).join('')}
            </ul>
        </div>
    `;

    const questionsHTML = `
        <div class="ai-card ai-card-questions">
            <div class="ai-card-header">
                <span class="ai-card-icon">❓</span>
                <span class="ai-card-title">建議面試問題</span>
            </div>
            <ul class="ai-card-list">
                ${data.interview_questions.map((q, i) => `<li><strong>Q${i+1}：</strong>${q}</li>`).join('')}
            </ul>
        </div>
    `;

    const suggestionHTML = `
        <div class="ai-card ai-card-suggestion">
            <div class="ai-card-header">
                <span class="ai-card-icon">💡</span>
                <span class="ai-card-title">專家提示</span>
            </div>
            <div class="ai-card-suggestion-content">${data.overall_suggestion}</div>
        </div>
    `;

    const finalHTML = `
        ${scoreHTML}
        <div class="ai-cards-container">
            ${strengthsHTML}
            ${gapsHTML}
            ${questionsHTML}
            ${suggestionHTML}
        </div>
        <style>
        .ai-cards-container {
            display: flex;
            flex-direction: column;
            gap: 20px;
            margin-top: 10px;
        }
        .ai-card {
            background: #fff;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            padding: 20px 22px 16px 22px;
            position: relative;
        }
        .ai-card-header {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        .ai-card-icon {
            font-size: 1.5rem;
            margin-right: 8px;
        }
        .ai-card-title {
            font-size: 1.15rem;
            font-weight: bold;
        }
        .ai-card-strengths .ai-card-title {
            color: #2196f3;
        }
        .ai-card-gaps .ai-card-title {
            color: #e53935;
        }
        .ai-card-questions .ai-card-title {
            color: #1a237e;
        }
        .ai-card-suggestion {
            background: #fffbe7;
            border-left: 6px solid #ffe082;
        }
        .ai-card-suggestion .ai-card-title {
            color: #fbc02d;
        }
        .ai-card-suggestion-content {
            color: #795548;
            font-size: 1.05rem;
            margin-left: 2px;
        }
        .ai-card-list {
            padding-left: 0;
            margin: 0;
            list-style: none;
        }
        .tag {
            display: inline-block;
            font-size: 0.95em;
            padding: 2px 8px;
            border-radius: 8px;
            margin-right: 6px;
            font-weight: bold;
        }
        .tag.core {
            background: #ffebee;
            color: #e53935;
            border: 1px solid #e53935;
        }
        .tag.plus {
            background: #e3f2fd;
            color: #1976d2;
            border: 1px solid #1976d2;
        }
        .core-skill {
            color: #e53935;
            font-weight: bold;
        }
        .plus-skill {
            color: #1976d2;
            font-weight: bold;
        }
        </style>
    `;

    aiResultDiv.innerHTML = finalHTML;
}