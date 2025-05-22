"""Service lưu trữ file (lưu, xóa, liệt kê) trong thư mục upload."""

import os
from fastapi import UploadFile
from typing import List, Dict, Any

UPLOAD_FOLDER = "upload"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class FileStorage:
    """Service lưu trữ file trong thư mục upload."""
    def save_file(self, file: UploadFile) -> str:
        """Lưu file tải lên vào thư mục upload.

        Args:
            file (UploadFile): Đối tượng file được tải lên từ client.
        Returns:
            str: Đường dẫn đầy đủ đến file đã lưu.
        """
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(file_path, "wb") as f:
            f.write(file.file.read())
        return file_path

    def delete_file(self, file_name: str) -> bool:
        """Xóa file khỏi thư mục upload.

        Args:
            file_name (str): Tên file cần xóa.
        Returns:
            bool: True nếu xóa thành công, False nếu file không tồn tại.
        """
        file_path = os.path.join(UPLOAD_FOLDER, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    def list_files(self) -> List[Dict[str, Any]]:
        """Liệt kê tất cả các file trong thư mục upload.

        Returns:
            List[Dict]: Danh sách các file với thông tin tên, kích thước và đường dẫn.
        """
        files = []
        for file_name in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, file_name)
            size = os.path.getsize(file_path)
            files.append({"name": file_name, "size": size, "path": file_path})
        return files 