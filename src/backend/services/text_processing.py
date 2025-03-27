import re
import json

class TextProcessing:
    """Xử lý văn bản: làm sạch, phân tích, chuyển đổi"""

    def split_JSON_text(self, text: str) -> list:
        """Trong text có chứa JSON, hãy tách ra thành một list các JSON"""
        try:
            # Tách text thành các đoạn JSON
            json_blocks = re.findall(r'\{[^{}]*\}', text)
            
            # Chuyển các đoạn JSON thành dict
            json_list = [json.loads(block) for block in json_blocks]
            return json_list
        except Exception as e:
            raise Exception(f"Lỗi khi tách text thành các đoạn JSON: {str(e)}")

if __name__ == "__main__":
    text_processing = TextProcessing()
    text = """Tìm hiểu về cấu trúc model CNN
    ```json {     
        "depth": "high" 
        } ```  
        
    **Giải thích:**  
    * **Loại câu hỏi:** Câu hỏi này yêu cầu giải thích về cấu trúc của mô hình CNN (Convolutional Neural Network),
        một khái niệm thuộc lĩnh vực học sâu (deep learning). 
        Đây là một câu hỏi phức tạp vì nó không chỉ đòi hỏi định nghĩa đơn thuần mà còn cần hiểu về các thành phần, cách chúng tương tác, và lý do tại sao cấu trúc đó lại hiệu quả.  
    * **Phạm vi thông tin:** Để trả lời đầy đủ câu hỏi này, cần tổng hợp thông tin từ nhiều nguồn khác nhau, bao gồm các bài báo khoa học, blog về AI, tài liệu hướng dẫn và có thể cả mã nguồn.
        Một câu trả lời tốt cần giải thích các lớp convolution, pooling, fully connected, hàm kích hoạt, và các tham số khác liên quan.  
    * **Ngữ cảnh chuyên môn:** CNN là một chủ đề thuộc lĩnh vực Khoa học Máy tính, cụ thể là Học sâu. Do đó, câu hỏi này mang tính học thuật và kỹ thuật chuyên sâu. 
        Việc hiểu cấu trúc của CNN đòi hỏi kiến thức nền tảng về toán học (đại số tuyến tính, giải tích), thống kê và lập trình."""
    print(text_processing.split_JSON_text(text)[0])
    print(text_processing.split_JSON_text(text)[0]['depth'])