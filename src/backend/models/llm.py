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
            analysis_response = await self.analyze_communication_context(prompt)
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
    
    async def analyze_communication_context(self, prompt: str) -> str:
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

    async def inDepth_context_analysis(self, prompt: str) -> dict:
        """Phân tích prompt và quyết định chiến lược tìm kiếm"""
        
        from services.text_processing import TextProcessing
        
        text_processing = TextProcessing()
        
        analysis_prompt = f"""
            Bạn là một chuyên gia phân tích truy vấn tìm kiếm. Nhiệm vụ của bạn là xác định mức độ phức tạp của câu hỏi do người dùng đặt ra để tối ưu hóa chiến lược tìm kiếm thông tin trên web.

            ## 1 Loại người dùng có thể đặt câu hỏi:
            Người dùng có thể thuộc các nhóm khác nhau, bao gồm:
            - **Người dùng phổ thông**: Hỏi những câu hỏi đơn giản về thời gian, thời tiết, sự kiện hằng ngày.
            - **Người dùng doanh nghiệp**: Cần thông tin về sản phẩm, thị trường, tài chính, đối thủ cạnh tranh.
            - **Người nghiên cứu/kỹ thuật**: Tìm hiểu sâu về các công nghệ, thuật toán, báo cáo nghiên cứu, dữ liệu phức tạp.

            ## 2 Hãy phân tích câu hỏi sau:
            "{prompt}"

            ## 3 Các yếu tố cần xem xét để đánh giá độ sâu thông tin:
            ### 🔹 **A. Loại câu hỏi**
            - **Câu hỏi đơn giản (depth: little)**: Yêu cầu một câu trả lời trực tiếp, ngắn gọn (ví dụ: ngày tháng, thời gian, thời tiết, giá sản phẩm, sự kiện gần đây).
            - **Câu hỏi trung bình (depth: medium)**: Cần tổng hợp từ nhiều nguồn nhưng không đòi hỏi nghiên cứu sâu (ví dụ: so sánh sản phẩm, thông tin sự kiện, hướng dẫn ngắn, phân tích xu hướng thị trường).
            - **Câu hỏi phức tạp (depth: high)**: Đòi hỏi tìm hiểu chuyên sâu, có thể liên quan đến nghiên cứu, phân tích chuyên môn hoặc nội dung có nhiều góc nhìn (ví dụ: giải thích thuật toán AI, báo cáo tài chính chi tiết, nghiên cứu khoa học).

            ### 🔹 **B. Phạm vi thông tin**
            - Nếu câu hỏi chỉ yêu cầu thông tin tại một thời điểm nhất định hoặc một địa điểm cụ thể → **độ sâu thấp (little)**.
            - Nếu cần tổng hợp từ nhiều nguồn hoặc phân tích dữ liệu → **độ sâu trung bình (medium) hoặc cao (high)**.

            ### 🔹 **C. Ngữ cảnh chuyên môn**
            - Câu hỏi có mang tính học thuật, nghiên cứu hoặc kỹ thuật chuyên sâu không?
            - Nếu có, hãy xem xét nó là câu hỏi **có độ sâu cao (high)**.

            ## 4 Định dạng output:
            Hãy trả về kết quả theo định dạng JSON:
            ```json
            {{
                "depth": "little"  # Nếu câu hỏi đơn giản, dễ trả lời ngay lập tức từ một nguồn tin duy nhất
                "depth": "medium"  # Nếu câu hỏi cần tổng hợp từ nhiều nguồn nhưng không quá chuyên sâu
                "depth": "high"    # Nếu câu hỏi mang tính nghiên cứu, phân tích, hoặc liên quan đến kiến thức chuyên môn sâu
            }}"""
        
        response = await self.model.generate_content_async(analysis_prompt)
        json_result = text_processing.split_JSON_text(response.text)
        return json_result[0]['depth']
