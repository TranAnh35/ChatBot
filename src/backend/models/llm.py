import google.generativeai as genai
from dotenv import load_dotenv
import os
from typing import List, Dict, Optional
load_dotenv()

class LLM:
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel("gemini-2.0-flash")
        
        # Định nghĩa system prompt
        self.system_prompt = """Bạn là ChatBox, một trợ lý AI thông minh được phát triển để hỗ trợ người dùng một cách toàn diện và chuyên nghiệp.

Nguyên tắc hoạt động:
1. Luôn cung cấp thông tin chính xác, đáng tin cậy và cập nhật.
2. Trả lời tự nhiên, thân thiện và dễ hiểu.
3. Không đưa ra thông tin sai lệch hoặc có hại.
4. Tôn trọng quyền riêng tư của người dùng.
5. Thừa nhận giới hạn kiến thức khi cần thiết.

Khả năng:
- Phân tích và trả lời các câu hỏi về nhiều lĩnh vực khác nhau
- Tổng hợp thông tin từ nhiều nguồn (tài liệu, web, file đính kèm)
- Hỗ trợ nhiều ngôn ngữ, đặc biệt là tiếng Việt
- Điều chỉnh giọng điệu phù hợp với ngữ cảnh (chính thức, thân thiện, hỗ trợ kỹ thuật)

Khi cung cấp câu trả lời:
- Ưu tiên sử dụng thông tin từ nguồn đáng tin cậy (tài liệu RAG, web, file đính kèm)
- Cấu trúc câu trả lời rõ ràng, dễ đọc
- Khi thích hợp, đề xuất các bước tiếp theo hoặc tài nguyên bổ sung
- Nếu không chắc chắn, nêu rõ những giới hạn và cung cấp câu trả lời tốt nhất có thể

Bạn được thiết kế để giúp đỡ trong các lĩnh vực từ giáo dục, công việc đến giải trí và đời sống hàng ngày, nhưng luôn tuân thủ các nguyên tắc đạo đức và pháp luật.
"""

    async def generateContent(self, prompt: str, rag_response: str = None, web_response: str = None, 
                             file_response: str = None, conversation_history: str = None) -> str:
        """Tạo nội dung từ prompt và thông tin từ RAG"""
        try:
            analysis_response = await self.analyze_communication_context(prompt)
            # Kết hợp prompt gốc với thông tin từ RAG
            combined_prompt = f"""System: {self.system_prompt}

Dựa trên thông tin sau đây, hãy trả lời câu hỏi một cách tự nhiên và đầy đủ:
            """

            # Thêm lịch sử hội thoại nếu có
            if conversation_history is not None:
                combined_prompt += f"""
                Lịch sử hội thoại:
                {conversation_history}
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

            Hãy dựa vào kết quả phân tích prompt, lịch sử hội thoại (nếu có), kết hợp thông tin từ tài liệu RAG, web và file đính kèm (nếu có) với kiến thức của bạn để trả lời câu hỏi.
            Người dùng không cần quan tâm đến các thông tin phân tích prompt, chỉ cần trả lời câu hỏi một cách tự nhiên và đầy đủ."""
            
            # Gọi API để tạo nội dung
            response = await self.model.generate_content_async(combined_prompt)
            return response.text

        except Exception as e:
            print(f"Lỗi khi tạo nội dung: {str(e)}")
            return "Xin lỗi, tôi không thể tạo nội dung lúc này."
    
    async def analyze_communication_context(self, prompt: str) -> str:
        """Phân tích prompt và trả về các thông tin cần thiết"""
        try:
            # Kết hợp prompt gốc với thông tin từ RAG
            combined_prompt = f"""System: {self.system_prompt}
            
            Câu hỏi: {prompt}

            Hãy phân tích prompt và hãy đưa ra là có cần thông tin từ web hay không, có cần thông tin từ file hay không.
            Và hãy phân tích prompt xem prompt đang thuộc trạng thái giao tiếp nào. (Ví dụ: xã giao, nghiêm túc, vui vẻ, ...)"""
            
            # Gọi API để tạo nội dung
            response = await self.model.generate_content_async(combined_prompt)

            return response.text

        except Exception as e:
            print(f"Lỗi khi phân tích prompt: {str(e)}")
            return "Xin lỗi, tôi không thể phân tích prompt lúc này."


    
    async def merge_context(self, web_results: List[List[Dict]]):
        """Gộp kết quả tìm kiếm web thành một chuỗi duy nhất và loại bỏ trùng lặp"""
        seen_snippets = set()
        merged_context = ""

        for result in web_results:
            for item in result:
                snippet = item.snippet.strip()
                if snippet and snippet not in seen_snippets:
                    merged_context += f"- {snippet}\n"
                    seen_snippets.add(snippet)

        if not merged_context:
            return "Không có thông tin hợp lệ để tổng hợp."

        prompt = f"""System: {self.system_prompt}
        
        Tôi có thông tin từ nhiều trang web, bạn hãy tổng hợp lại thành một đoạn văn duy nhất với đầy đủ nội dung cần thiết.
        
        Dưới đây là các thông tin được thu thập:
        {merged_context}
        
        Hãy viết lại nội dung thật đầy đủ, dễ hiểu nhưng không mất đi ý chính. Không cần nhắc lad dữ liệu nà được lấy ở trên web mà chỉ cần nói như những thông tin bình thường.
        """

        response = await self.model.generate_content_async(prompt)
        return response.text