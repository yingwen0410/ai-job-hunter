import os
import docx
from io import BytesIO
import pdfplumber

def _parse_pdf_with_pdfplumber(file_stream) -> str:
    text = ""
    try:
        with pdfplumber.open(file_stream) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"使用 pdfplumber 解析 PDF 時發生錯誤: {e}")
    return text

def _parse_docx(file_stream) -> str:
    text = ""
    try:
        doc = docx.Document(file_stream)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"解析 DOCX 時發生錯誤: {e}")
    return text

def _parse_txt(file_stream) -> str:
    # 嘗試用多種編碼來解碼，增加成功率
    try:
        return file_stream.read().decode('utf-8')
    except UnicodeDecodeError:
        try:
            # 如果 utf-8 失敗，回到檔案開頭，嘗試用 big5
            file_stream.seek(0)
            return file_stream.read().decode('big5')
        except Exception as e:
            print(f"解析 TXT 時發生錯誤: {e}")
    return ""

def parse_resume(file_stream, file_name: str) -> str:
    # 防呆：確保 file_name 是字串
    if not isinstance(file_name, str) or not file_name:
        raise ValueError("無效的檔案名稱")

    # 從檔名中取得副檔名，並轉為小寫
    _, extension = os.path.splitext(file_name)
    extension = extension.lower()
    
    # 將檔案流轉換為 BytesIO，使其可被函式庫重複讀取
    file_bytes = BytesIO(file_stream.read())
    
    if extension == ".pdf":
        return _parse_pdf_with_pdfplumber(file_bytes)
    elif extension == ".docx":
        return _parse_docx(file_bytes)
    elif extension == ".txt":
        return _parse_txt(file_bytes)
    else:
        raise ValueError(f"不支援的檔案格式: {extension}")