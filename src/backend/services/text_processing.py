import re
import json
from typing import List, Dict, Any

class TextProcessing:
    """Xử lý văn bản với các chức năng làm sạch, phân tích và chuyển đổi."""

    def split_JSON_text(self, text: str) -> List[Dict[str, Any]]:
        """Tách văn bản chứa JSON thành danh sách các đối tượng JSON.
        
        Args:
            text (str): Chuỗi văn bản chứa các đối tượng JSON cần trích xuất.
            
        Returns:
            List[Dict[str, Any]]: Danh sách các đối tượng JSON được trích xuất từ văn bản.
            
        Raises:
            Exception: Nếu có lỗi xảy ra trong quá trình phân tích cú pháp JSON.
            
        Example:
            >>> tp = TextProcessing()
            >>> result = tp.split_JSON_text('abc{"key": "value"}def{"another": 123}')
            >>> print(result)
            [{'key': 'value'}, {'another': 123}]
        """
        try:
            # Tách text thành các đoạn JSON
            json_blocks = re.findall(r'\{[^{}]*\}', text)
            
            # Chuyển các đoạn JSON thành dict
            json_list = [json.loads(block) for block in json_blocks]
            return json_list
        except Exception as e:
            raise Exception(f"Lỗi khi tách text thành các đoạn JSON: {str(e)}")