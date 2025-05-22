import google.generativeai as genai
from dotenv import load_dotenv
import os
from typing import List, Dict, Optional
load_dotenv()

class LLM:
    """Lớp xử lý tương tác với mô hình ngôn ngữ.
    
    Lớp này cung cấp các phương thức để tạo nội dung sử dụng Google's Generative AI,
    với hỗ trợ ngữ cảnh từ RAG, tìm kiếm web và file đính kèm.
    """
    
    def __init__(self):
        """Khởi tạo LLM với cấu hình Google's Generative AI.
        
        Đọc khóa API từ biến môi trường và thiết lập mô hình.
        Đồng thời định nghĩa prompt hệ thống để hướng dẫn hành vi của mô hình.
        """
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel("gemini-2.0-flash")
        
        self.system_prompt = """Bạn là ChatBot, một trợ lý AI thông minh được phát triển để hỗ trợ người dùng một cách toàn diện và chuyên nghiệp.

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
        """Tạo nội dung dựa trên prompt và ngữ cảnh được cung cấp.
        
        Kết hợp prompt hệ thống, lịch sử hội thoại và bất kỳ ngữ cảnh nào được cung cấp
        (RAG, web, file) để tạo ra phản hồi phù hợp và mạch lạc.
        
        Agrs:
            prompt (str): Prompt đầu vào từ người dùng.
            rag_response (str, optional): Ngữ cảnh từ RAG (Retrieval-Augmented Generation).
            web_response (str, optional): Kết quả tìm kiếm web.
            file_response (str, optional): Nội dung từ file đính kèm.
            conversation_history (str, optional): Lịch sử hội thoại.
            
        Returns:
            str: Phản hồi được tạo ra từ mô hình ngôn ngữ.
            
        Ghi chú:
            Tự động phân tích prompt để xác định xem có cần thêm ngữ cảnh không
            và điều chỉnh phản hồi cho phù hợp.
        """
        try:
            needs_analysis = self.should_analyze_prompt(prompt)
            analysis_response = ""
            if needs_analysis:
                analysis_response = await self.analyze_communication_context(prompt)
                
            combined_prompt = f"System: {self.system_prompt}\n\n"

            if conversation_history is not None and len(conversation_history.strip()) > 0:
                combined_prompt += f"Lịch sử hội thoại:\n{conversation_history}\n\n"
            
            context_added = False
            
            if rag_response is not None and len(rag_response.strip()) > 0:
                combined_prompt += f"Thông tin RAG:\n{rag_response}\n\n"
                context_added = True
                
            if web_response is not None and len(web_response.strip()) > 0:
                combined_prompt += f"Thông tin web:\n{web_response}\n\n"
                context_added = True

            if file_response is not None and len(file_response.strip()) > 0:
                combined_prompt += f"Thông tin file:\n{file_response}\n\n"
                context_added = True

            combined_prompt += f"Câu hỏi: {prompt}\n\n"
            
            if needs_analysis and analysis_response:
                combined_prompt += f"Phân tích: {analysis_response}\n\n"

            if context_added:
                combined_prompt += "Trả lời dựa trên thông tin cung cấp và kiến thức của bạn."
            else:
                combined_prompt += "Trả lời dựa trên kiến thức của bạn."
            
            response = await self.model.generate_content_async(combined_prompt)
            return response.text

        except Exception as e:
            print(f"Lỗi khi tạo nội dung: {str(e)}")
            return "Xin lỗi, tôi không thể tạo nội dung lúc này."
    
    def should_analyze_prompt(self, prompt: str) -> bool:
        """Xác định xem prompt có cần phân tích chi tiết không.
        
        Sử dụng các heuristic như độ dài, dấu hỏi và từ khóa cụ thể
        để quyết định xem prompt có cần xử lý bổ sung không.
        
        Agrs:
            prompt (str): Đầu vào từ người dùng cần phân tích.
            
        Returns:
            bool: True nếu prompt cần phân tích, False nếu không.
        """
        if len(prompt) < 10 or "?" not in prompt:
            return False
            
        analysis_keywords = ["tìm kiếm", "tìm", "web", "file", "tài liệu", 
                           "so sánh", "nghiên cứu", "phân tích", "giải thích"]
        for keyword in analysis_keywords:
            if keyword in prompt.lower():
                return True
                
        return False
    
    async def analyze_communication_context(self, prompt: str) -> str:
        """Phân tích ngữ cảnh giao tiếp của một prompt.
        
        Xác định thông tin bổ sung có thể cần thiết để phản hồi prompt,
        chẳng hạn như kết quả tìm kiếm web hoặc nội dung file.
        
        Agrs:
            prompt (str): Đầu vào từ người dùng cần phân tích.
            
        Returns:
            str: Phân tích ngắn gọn về thông tin cần thiết để phản hồi prompt.
        """
        try:
            combined_prompt = f"""Phân tích ngắn gọn câu hỏi: "{prompt}"
                Cần thông tin web? (có/không)
                Cần thông tin từ file? (có/không)
                Trạng thái giao tiếp? (xã giao/nghiêm túc/vui vẻ/...)
                Chỉ trả lời 3 dòng ngắn gọn.
            """
            
            response = await self.model.generate_content_async(combined_prompt)
            return response.text

        except Exception as e:
            print(f"Lỗi khi phân tích prompt: {str(e)}")
            return ""
    
    async def merge_context(self, web_results: List[List[Dict]]) -> str:
        """Hợp nhất và loại bỏ trùng lặp kết quả tìm kiếm web thành ngữ cảnh mạch lạc.
        
        Xử lý nhiều kết quả tìm kiếm web, loại bỏ trùng lặp và định dạng
        thành một chuỗi dễ đọc cho mô hình ngôn ngữ.
        
        Agrs:
            web_results (List[List[Dict]]): Danh sách kết quả tìm kiếm web, mỗi kết quả
                                          là một danh sách từ điển chứa trường 'snippet'.
                                          
        Returns:
            str: Một chuỗi đã được hợp nhất và loại bỏ trùng lặp chứa thông tin
                 liên quan từ kết quả tìm kiếm web.
                 
        Ghi chú:
            Nếu không tìm thấy snippet hợp lệ, trả về thông báo cho biết
            không có thông tin hợp lệ nào được tìm thấy.
        """
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

        prompt = f"""Tổng hợp ngắn gọn các thông tin sau thành một đoạn văn duy nhất:
            {merged_context}
            Viết lại đầy đủ, dễ hiểu nhưng không mất ý chính. Không đề cập nguồn gốc thông tin.
        """

        response = await self.model.generate_content_async(prompt)
        return response.text