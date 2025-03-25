import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

class LLM:
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    async def generateContent(self, prompt: str, rag_response: str = None, web_response: str = None, file_response: str = None) -> str:
        """Tạo nội dung từ prompt và thông tin từ RAG"""
        try:
            analysis_response = await self._prompt_analysis(prompt)
            # Kết hợp prompt gốc với thông tin từ RAG
            combined_prompt = """Dựa trên thông tin sau đây, hãy trả lời câu hỏi một cách tự nhiên và đầy đủ:
            """

            # Thêm thông tin từ tài liệu nếu rag_response không phải None
            if rag_response is not None:
                combined_prompt += f"""
                Thông tin từ hệ thống RAG:
                {rag_response}
                """
                
            if web_response is not None:
                combined_prompt += f"""
                Thông tin từ web:
                {web_response}
                """

            if file_response is not None:
                combined_prompt += f"""
                Thông tin từ file đính kèm:
                {file_response}
                """

            # Thêm thông tin từ web (giữ nguyên vì không có điều kiện loại bỏ)
            combined_prompt += f"""

            Câu hỏi: {prompt}
            
            Kết quả phân tích prompt:
            {analysis_response}

            Hãy dựa vào kết quả phân tích prompt, kết hợp thông tin từ tài liệu RAG, web và file đính kèm (nếu có) với kiến thức của bạn để trả lời câu hỏi.
            Người dùng không cần quan tâm đến các thông tin phân tích prompt, chỉ cần trả lời câu hỏi một cách tự nhiên và đầy đủ."""
            
            # Gọi API để tạo nội dung
            response = await self.model.generate_content_async(combined_prompt)
            return response.text

        except Exception as e:
            print(f"Lỗi khi tạo nội dung: {str(e)}")
            return "Xin lỗi, tôi không thể tạo nội dung lúc này."
    
    async def _prompt_analysis(self, prompt: str) -> str:
        """Phân tích prompt và trả về các thông tin cần thiết"""
        try:
            # Kết hợp prompt gốc với thông tin từ RAG
            combined_prompt = f"""
            Câu hỏi: {prompt}

            Hãy phân tích prompt và hãy đưa ra là có cần thông tin từ web hay không, có cần thông tin từ file hay không.
            Và hãy phân tích prompt xem prompt đang thuộc trạng thái giao tiếp nào. (Ví dụ: xã giao, nghiêm túc, vui vẻ, ...)"""
            
            # Gọi API để tạo nội dung
            response = await self.model.generate_content_async(combined_prompt)

            return response.text

        except Exception as e:
            print(f"Lỗi khi phân tích prompt: {str(e)}")
            return "Xin lỗi, tôi không thể phân tích prompt lúc này."
