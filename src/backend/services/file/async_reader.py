import os
from fastapi import UploadFile
from docling.document_converter import DocumentConverter
from docx import Document
import yaml
from typing import Any
import io

UPLOAD_FOLDER = "upload"

class AsyncFileReader:
    
    async def read_uploaded_file(self, file: UploadFile) -> str:
        file_name = file.filename
        content: str = ""
        try:
            if file_name.endswith('.pdf'):
                content = await self.read_pdf_from_upload(file)
            elif file_name.endswith(('.doc', '.docx')):
                content = await self.read_docx_from_upload(file)
            elif file_name.endswith(('.yaml', '.yml')):
                content = await self.read_yaml_from_upload(file)
            else:
                content = await self.read_txt_from_upload(file)
            return content
        except Exception as e:
            raise Exception(f"Không thể đọc file {file_name}: {str(e)}")
        finally:
            await file.close()

    async def read_pdf_from_upload(self, file: UploadFile) -> str:
        file_content = await file.read()
        temp_file_path = os.path.join(UPLOAD_FOLDER, "temp_" + file.filename)
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(file_content)
        converter = DocumentConverter()
        result = converter.convert(temp_file_path)
        text = result.document.export_to_markdown()
        os.remove(temp_file_path)
        return text

    async def read_docx_from_upload(self, file: UploadFile) -> str:
        doc = Document(file.file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text

    async def read_yaml_from_upload(self, file: UploadFile) -> str:
        content = await file.read()
        data = yaml.safe_load(content)
        return str(data)

    async def read_txt_from_upload(self, file: UploadFile) -> str:
        content = await file.read()
        encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
        for encoding in encodings:
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise Exception("Không thể đọc file với các encoding đã thử") 