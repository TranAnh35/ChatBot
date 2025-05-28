import sqlite3
from typing import List, Tuple, Optional

class VectorDBRepository:
    def __init__(self, db_path: str = "vector_store.db"):
        self.db_path = db_path

    def get_all_files(self) -> List[Tuple[int, str, int, str, str]]:
        """Lấy danh sách tất cả các file đã được lưu trong database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, size, created_at, updated_at
            FROM files
            ORDER BY name
        """)
        files = cursor.fetchall()
        conn.close()
        return files

    def get_chunks_by_file(self, file_name: str) -> List[Tuple[int, str, int]]:
        """Lấy tất cả các chunks thuộc về một file cụ thể."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id, c.content, c.chunk_index
            FROM chunks c
            JOIN files f ON f.id = c.file_id
            WHERE f.name = ?
            ORDER BY c.chunk_index
        """, (file_name,))
        chunks = cursor.fetchall()
        conn.close()
        return chunks

    def get_chunk_by_id(self, doc_id: int) -> Optional[str]:
        """Lấy nội dung chunk dựa trên ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM chunks WHERE id = ?", (doc_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def delete_file(self, file_name: str) -> None:
        """Xóa toàn bộ dữ liệu liên quan đến một file khỏi database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM files WHERE name = ?", (file_name,))
        result = cursor.fetchone()
        if result:
            file_id = result[0]
            cursor.execute("DELETE FROM chunks WHERE file_id = ?", (file_id,))
            cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
        conn.commit()
        conn.close() 