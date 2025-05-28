import os
import sqlite3
from typing import List, Dict, Tuple, Optional, Set, Any, Union
from pathlib import Path
from repositories.vector_db_repository import VectorDBRepository

class VectorDB:
    _instance = None
    
    def __new__(cls):
        """Tạo instance mới của VectorDB nếu chưa tồn tại (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super(VectorDB, cls).__new__(cls)
            cls._instance.db_path = "vector_store.db"
            cls._instance.upload_dir = "upload"
            cls._instance.chunk_size = 2000
            cls._instance.chunk_overlap = 200
            cls._instance.current_version = 2
            cls._instance.repository = VectorDBRepository(cls._instance.db_path)
            if not os.path.exists(cls._instance.db_path):
                print("Database không tồn tại, tạo mới...")
                cls._instance.init_db()
        return cls._instance

    def init_db(self) -> None:
        """Khởi tạo cơ sở dữ liệu SQLite."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS version (
                    id INTEGER PRIMARY KEY,
                    version INTEGER NOT NULL
                )
            ''')
            
            cursor.execute("SELECT version FROM version WHERE id = 1")
            result = cursor.fetchone()
            
            if result is None:
                self._create_initial_schema(cursor)
                cursor.execute("INSERT INTO version (id, version) VALUES (1, ?)", (self.current_version,))
            else:
                db_version = result[0]
                if db_version < self.current_version:
                    self._update_schema(cursor, db_version)
                    cursor.execute("UPDATE version SET version = ? WHERE id = 1", (self.current_version,))
            
            conn.commit()
            conn.close()
            print("Đã khởi tạo/cập nhật database thành công")
        except Exception as e:
            print(f"Lỗi khi khởi tạo database: {str(e)}")
            raise

    def _create_initial_schema(self, cursor: sqlite3.Cursor) -> None:
        """Tạo cấu trúc ban đầu của cơ sở dữ liệu."""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                size INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (file_id) REFERENCES files (id),
                UNIQUE(file_id, chunk_index)
            )
        ''')

    def _update_schema(self, cursor: sqlite3.Cursor, old_version: int) -> None:
        """Cập nhật cấu trúc database từ phiên bản cũ lên phiên bản mới."""
        if old_version < 2:
            try:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
                if cursor.fetchone() is None:
                    self._create_initial_schema(cursor)
                    return
                
                cursor.execute("CREATE TABLE IF NOT EXISTS documents_backup AS SELECT * FROM documents")
                
                self._create_initial_schema(cursor)
                
                cursor.execute("""
                    INSERT INTO files (name, size, created_at, updated_at)
                    SELECT DISTINCT source, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    FROM documents_backup
                """)
                
                cursor.execute("""
                    INSERT INTO chunks (file_id, content, chunk_index, created_at)
                    SELECT DISTINCT f.id, d.text, d.chunk_index, CURRENT_TIMESTAMP
                    FROM documents_backup d
                    JOIN files f ON f.name = d.source
                    WHERE NOT EXISTS (
                        SELECT 1 FROM chunks c 
                        WHERE c.file_id = f.id AND c.chunk_index = d.chunk_index
                    )
                """)
                
                cursor.execute("DROP TABLE documents_backup")
                
            except Exception as e:
                print(f"Lỗi khi cập nhật schema: {str(e)}")
                cursor.execute("DROP TABLE IF EXISTS documents_backup")
                raise

    def _find_optimal_split_point(self, text: str, start: int, end: int) -> int:
        """Tìm điểm tách tối ưu trong khoảng văn bản đã cho."""
        SPLIT_CHARS = ['.', '!', '?', '\n', ',', ';', ' ']
        
        for split_char in SPLIT_CHARS:
            pos = text.rfind(split_char, start, end + 1)
            if pos > start:
                return pos + 1  
                
        return end

    def split_text(self, text: str) -> List[str]:
        """Tách văn bản thành các đoạn (chunks) với kích thước và độ chồng lấn xác định."""
        if not text:
            return []
            
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = min(start + self.chunk_size, text_length)
            
            if end >= text_length:
                if start < text_length:
                    chunks.append(text[start:].strip())
                break
                
            split_pos = self._find_optimal_split_point(text, start, end)
            
            if split_pos <= start:
                split_pos = end
                
            chunk = text[start:split_pos].strip()
            if chunk:
                chunks.append(chunk)
                
            start = max(split_pos - self.chunk_overlap, start + 1)
            
        return chunks

    def _check_file_changed(self, cursor: sqlite3.Cursor, file_name: str, content_size: int) -> Tuple[bool, Optional[int]]:
        """Kiểm tra xem file đã thay đổi so với bản lưu trữ trong database chưa."""
        cursor.execute("SELECT id, size FROM files WHERE name = ?", (file_name,))
        result = cursor.fetchone()
        
        if not result:
            return True, None  
            
        file_id, old_size = result
        if old_size == content_size:
            cursor.execute(
                "UPDATE files SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                (file_id,)
            )
            return False, file_id
            
        return True, file_id

    def _update_file_metadata(self, cursor: sqlite3.Cursor, file_name: str, content_size: int) -> int:
        """Cập nhật thông tin metadata của file trong database."""
        cursor.execute("""
            INSERT INTO files (name, size, created_at, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(name) DO UPDATE SET
                size = excluded.size,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id
        """, (file_name, content_size))
        
        result = cursor.fetchone()
        return result[0] if result else None

    def _update_file_chunks(self, cursor: sqlite3.Cursor, file_id: int, chunks: List[str]) -> None:
        """Cập nhật các chunks của file trong database."""
        cursor.execute("DELETE FROM chunks WHERE file_id = ?", (file_id,))
        
        for chunk_index, chunk in enumerate(chunks):
            cursor.execute("""
                INSERT INTO chunks (file_id, content, chunk_index, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (file_id, chunk, chunk_index))

    def process_file(self, file_path: str) -> None:
        """Xử lý file và lưu vào database nếu nội dung thay đổi."""
        from services.file.reader import FileReader
        
        try:
            file_name = os.path.basename(file_path)
            file_reader = FileReader()
            content = file_reader.read_file_from_path(file_path)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                has_changed, file_id = self._check_file_changed(cursor, file_name, len(content))
                if not has_changed:
                    conn.commit()
                    return  
                
                chunks = self.split_text(content)
                
                file_id = self._update_file_metadata(cursor, file_name, len(content))
                
                self._update_file_chunks(cursor, file_id, chunks)
                
                conn.commit()
                
        except Exception as e:
            print(f"Lỗi khi xử lý file {file_path}: {str(e)}")
            raise

    def delete_file_from_db(self, file_name: str) -> None:
        """Xóa dữ liệu của file khỏi database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute("BEGIN TRANSACTION")
                
                cursor.execute("SELECT id FROM files WHERE name = ?", (file_name,))
                result = cursor.fetchone()
                
                if result:
                    file_id = result[0]
                    cursor.execute("DELETE FROM chunks WHERE file_id = ?", (file_id,))
                    cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
                
                conn.commit()
                print(f"Đã xóa dữ liệu của file {file_name} khỏi database")
                
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
                
        except Exception as e:
            print(f"Lỗi khi xóa dữ liệu của file {file_name}: {str(e)}")

    def _get_db_files(self, cursor: sqlite3.Cursor) -> Set[str]:
        """Lấy danh sách tên các file đã lưu trong database."""
        cursor.execute("SELECT name FROM files")
        return {row[0] for row in cursor.fetchall()}
    
    def _get_uploaded_files(self) -> Set[str]:
        """Lấy danh sách các file trong thư mục upload."""
        valid_extensions = {'.txt', '.pdf', '.doc', '.docx', '.yaml', '.yml'}
        return {
            file for file in os.listdir(self.upload_dir)
            if os.path.splitext(file)[1].lower() in valid_extensions
        }
    
    def _cleanup_missing_files(self, db_files: Set[str], uploaded_files: Set[str]) -> None:
        """Xóa dữ liệu của các file không còn tồn tại trong thư mục upload."""
        files_to_delete = db_files - uploaded_files
        for file_name in files_to_delete:
            try:
                self.delete_file_from_db(file_name)
                print(f"Đã xóa dữ liệu của file không còn tồn tại: {file_name}")
            except Exception as e:
                print(f"Lỗi khi xóa dữ liệu của file {file_name}: {str(e)}")
    
    def _process_uploaded_files(self, uploaded_files: Set[str]) -> None:
        """Xử lý các file mới hoặc đã thay đổi trong thư mục upload."""
        for file_name in uploaded_files:
            try:
                file_path = os.path.join(self.upload_dir, file_name)
                self.process_file(file_path)
                print(f"Đã xử lý file: {file_name}")
            except Exception as e:
                print(f"Lỗi khi xử lý file {file_name}: {str(e)}")
    
    def update_from_upload(self) -> None:
        """Đồng bộ dữ liệu từ thư mục upload vào VectorDB."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                db_files = self._get_db_files(cursor)
            
                uploaded_files = self._get_uploaded_files()
                
                self._cleanup_missing_files(db_files, uploaded_files)
                
                self._process_uploaded_files(uploaded_files)
                    
        except Exception as e:
            print(f"Lỗi khi đồng bộ dữ liệu: {str(e)}")

    def reset_db(self) -> None:
        """Xóa và tạo lại cơ sở dữ liệu từ đầu."""
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
                print(f"Đã xóa database cũ: {self.db_path}")
            
            self.init_db()
            print("Đã tạo database mới thành công")
        except Exception as e:
            print(f"Lỗi khi reset database: {str(e)}")
            raise

    def get_chunk_by_id(self, doc_id: int) -> Optional[str]:
        """Lấy nội dung chunk dựa trên ID."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT content FROM chunks WHERE id = ?", (doc_id,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        except Exception as e:
            print(f"Lỗi khi lấy chunk: {str(e)}")
            raise

    def get_all_chunks(self) -> List[Tuple[int, str, str, int]]:
        """Lấy tất cả các chunks từ cơ sở dữ liệu."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id, c.content, f.name as source, c.chunk_index
                FROM chunks c
                JOIN files f ON f.id = c.file_id
                ORDER BY f.name, c.chunk_index
            """)
            chunks = cursor.fetchall()
            conn.close()
            return chunks
        except Exception as e:
            print(f"Lỗi khi lấy chunks: {str(e)}")
            raise

    def get_chunks_by_file(self, file_name: str) -> List[Tuple[int, str, int]]:
        """Lấy tất cả các chunks thuộc về một file cụ thể."""
        try:
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
        except Exception as e:
            print(f"Lỗi khi lấy chunks của file {file_name}: {str(e)}")
            raise

    def get_all_files(self) -> List[Tuple[int, str, int, str, str]]:
        """Lấy danh sách tất cả các file đã được lưu trong database."""
        try:
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
        except Exception as e:
            print(f"Lỗi khi lấy danh sách files: {str(e)}")
            raise

    def delete_file_data(self, file_name: str) -> None:
        """Xóa toàn bộ dữ liệu liên quan đến một file khỏi database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT id FROM files WHERE name = ?", (file_name,))
                result = cursor.fetchone()
                
                if result:
                    file_id = result[0]
                    cursor.execute("DELETE FROM chunks WHERE file_id = ?", (file_id,))
                    cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
                    print(f"Đã xóa dữ liệu của file {file_name} khỏi database")
                
                conn.commit()
                
        except Exception as e:
            print(f"Lỗi khi xóa dữ liệu của file {file_name}: {str(e)}")
            raise 