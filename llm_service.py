# 檔案: llm_service.py

import os
import json
from dotenv import load_dotenv
from google import genai as google_genai_sdk
from google.genai import types as google_genai_types

# 載入環境變數
load_dotenv()

def get_match_analysis(job_description: str, resume_text: str) -> dict:
    """
    接收職缺描述和履歷文字，使用 google-genai SDK 進行分析。
    """
    #api_key = os.getenv('GEMINI_API_KEY')
    api_key = "AIzaSyCukaLLnaXYRYVpNjxrPR1RtZvPKxAjuS8"

    #if not api_key:
    #   return {"error": "在 .env 檔案中找不到 GEMINI_API_KEY，或 .env 未被正確載入。"}
    
    try:
        client = google_genai_sdk.Client(api_key=api_key)
        
        prompt = f"""
        你是一位頂尖的 AI 技術獵頭與職涯教練，擅長為求職者提供深入、具體的求職建議。

        請嚴格根據下方提供的【職缺描述】與【履歷內容】，對兩者進行深度交叉比對，並執行以下五項任務：

        1.  **強項分析 (strengths_analysis)**: 找出來【履歷內容】中，有哪些技能或經驗是與【職缺描述】直接相關的。針對每一項，簡要說明其為何重要。
        2.  **技能差距 (skill_gaps)**: 找出【職缺描述】中要求，但【履歷內容】裡沒有提到的關鍵技能。並為每個技能標示其重要性（分為'核心要求'或'加分項'）。
        3.  **面試問題建議 (interview_questions)**: 基於此職缺的要求和履歷的內容，設計 2 至 3 個面試官最可能提出的技術或情境問題。
        4.  **整體優化建議 (overall_suggestion)**: 綜合以上分析，用繁體中文提供一句總結性的履歷優化建議。
        5.  **匹配度分數 (match_score)**: 請根據履歷與職缺描述的整體相符程度，給出一個 0~100 的整數分數，100 代表完全符合，0 代表完全不符。請只給數字，不要附加說明。

        你的回答**必須**是一個格式嚴謹的 JSON 物件，絕對不要包含任何 JSON 格式以外的文字。JSON 物件的結構如下：

        {{
          "strengths_analysis": [
            {{
              "skill": "<string, 履歷中符合的技能>",
              "relevance": "<string, 解釋為何此技能與職缺相關>"
            }}
          ],
          "skill_gaps": [
            {{
              "skill": "<string, 履歷中缺失的技能>",
              "importance": "<string, '核心要求' 或 '加分項'>"
            }}
          ],
          "interview_questions": [
            "<string, 建議的面試問題1>",
            "<string, 建議的面試問題2>"
          ],
          "overall_suggestion": "<string, 一句總結性的優化建議>",
          "match_score": <int, 0~100 的整數分數>
        }}

        ---
        <職缺描述>
        {job_description}
        </職缺描述>
        ---
        <履歷內容>
        {resume_text}
        </履歷內容>
        """

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )

        # 增加對回應文字的清理步驟，以應對非純 JSON 的情況
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:] # 移除開頭的 ```json
        if response_text.endswith("```"):
            response_text = response_text[:-3] # 移除結尾的 ```
        
        analysis_result = json.loads(response_text)
        
        return analysis_result

    except Exception as e:
        print(f"與 LLM API 互動時發生錯誤: {e}")
        error_details = str(e)
        if 'response' in locals() and hasattr(response, 'text'):
             error_details += f" | AI原始回應: {response.text}"
        return {"error": f"AI 分析時發生錯誤", "details": error_details}