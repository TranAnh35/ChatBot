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