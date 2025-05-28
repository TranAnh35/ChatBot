import os
from docling.document_converter import DocumentConverter
from docx import Document
import yaml
from typing import Any

class FileReader:
    
    def read_file_from_path(self, file_path: str) -> str:
        """Đọc nội dung file dựa trên phần mở rộng."""
        file_name = os.path.basename(file_path)
        if file_name.endswith('.pdf'):
            return self.read_pdf_from_path(file_path)
        elif file_name.endswith(('.doc', '.docx')):
            return self.read_docx_from_path(file_path)
        elif file_name.endswith(('.yaml', '.yml')):
            return self.read_yaml_from_path(file_path)
        elif file_name.endswith(('.txt', '.md')):
            return self.read_txt_from_path(file_path)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()

    def read_pdf_from_path(self, file_path: str) -> str:
        """Đọc nội dung từ file PDF sử dụng docling."""
        converter = DocumentConverter()
        result = converter.convert(file_path)
        return result.document.export_to_markdown()

    def read_docx_from_path(self, file_path: str) -> str:
        """Đọc nội dung từ file DOCX."""
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text

    def read_yaml_from_path(self, file_path: str) -> str:
        """Đọc nội dung từ file YAML."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return str(data)

    def read_txt_from_path(self, file_path: str) -> str:
        """Đọc nội dung từ file văn bản với nhiều bảng mã khác nhau."""
        encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        raise Exception("Không thể đọc file với các encoding đã thử") 