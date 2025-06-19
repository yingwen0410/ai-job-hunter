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

    // 根據回傳的 JSON 動態生成 HTML
    const strengthsHTML = data.strengths_analysis.map(item => 
        `<li><strong>${item.skill}:</strong> ${item.relevance}</li>`
    ).join('');

    const gapsHTML = data.skill_gaps.map(item =>
        `<li><strong>${item.skill}</strong> <span class="tag ${item.importance === '核心要求' ? 'core' : ''}">${item.importance}</span></li>`
    ).join('');

    const questionsHTML = data.interview_questions.map(q => `<li>${q}</li>`).join('');

    const finalHTML = `
        <div class="ai-result-section">
            <h4>✅ 強項分析</h4>
            <ul>${strengthsHTML}</ul>
        </div>
        <div class="ai-result-section">
            <h4>⚠️ 技能差距</h4>
            <ul>${gapsHTML}</ul>
        </div>
        <div class="ai-result-section">
            <h4>❓ 建議面試問題</h4>
            <ul>${questionsHTML}</ul>
        </div>
        <div class="suggestion">
            <p><strong>💡 整體優化建議：</strong>${data.overall_suggestion}</p>
        </div>
    `;

    aiResultDiv.innerHTML = finalHTML;
}