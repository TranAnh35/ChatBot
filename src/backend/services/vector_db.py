import os
import sqlite3
from bs4 import BeautifulSoup
import PyPDF2
from docx import Document
import re
import yaml
from datetime import datetime

class VectorDB:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorDB, cls).__new__(cls)
            cls._instance.db_path = "vector_store.db"
            cls._instance.uploaded_files_dir = "uploaded_files"
            cls._instance.chunk_size = 1000
            cls._instance.chunk_overlap = 100
            cls._instance.current_version = 2
            if not os.path.exists(cls._instance.db_path):
                print("Database không tồn tại, tạo mới...")
                cls._instance.init_db()
        return cls._instance

    def init_db(self):
        """Khởi tạo database SQLite"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tạo bảng version để quản lý phiên bản database
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS version (
                    id INTEGER PRIMARY KEY,
                    version INTEGER NOT NULL
                )
            ''')
            
            # Kiểm tra phiên bản database
            cursor.execute("SELECT version FROM version WHERE id = 1")
            result = cursor.fetchone()
            
            if result is None:
                # Database mới, tạo cấu trúc ban đầu
                self._create_initial_schema(cursor)
                cursor.execute("INSERT INTO version (id, version) VALUES (1, ?)", (self.current_version,))
            else:
                db_version = result[0]
                if db_version < self.current_version:
                    # Cập nhật cấu trúc database nếu cần
                    self._update_schema(cursor, db_version)
                    cursor.execute("UPDATE version SET version = ? WHERE id = 1", (self.current_version,))
            
            conn.commit()
            conn.close()
            print("Đã khởi tạo/cập nhật database thành công")
        except Exception as e:
            print(f"Lỗi khi khởi tạo database: {str(e)}")
            raise

    def _create_initial_schema(self, cursor):
        """Tạo cấu trúc ban đầu của database"""
        # Tạo bảng files
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                size INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tạo bảng chunks
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

    def _update_schema(self, cursor, old_version):
        """Cập nhật cấu trúc database từ phiên bản cũ lên phiên bản mới"""
        if old_version < 2:
            try:
                # Kiểm tra xem bảng documents có tồn tại không
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
                if cursor.fetchone() is None:
                    # Nếu không có bảng documents, chỉ cần tạo cấu trúc mới
                    self._create_initial_schema(cursor)
                    return
                
                # Backup dữ liệu cũ
                cursor.execute("CREATE TABLE IF NOT EXISTS documents_backup AS SELECT * FROM documents")
                
                # Tạo bảng mới
                self._create_initial_schema(cursor)
                
                # Chuyển dữ liệu từ bảng cũ sang bảng mới
                # 1. Thêm thông tin file
                cursor.execute("""
                    INSERT INTO files (name, size, created_at, updated_at)
                    SELECT DISTINCT source, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    FROM documents_backup
                """)
                
                # 2. Thêm chunks với xử lý trùng lặp
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
                
                # Xóa bảng backup
                cursor.execute("DROP TABLE documents_backup")
                
            except Exception as e:
                print(f"Lỗi khi cập nhật schema: {str(e)}")
                # Rollback nếu có lỗi
                cursor.execute("DROP TABLE IF EXISTS documents_backup")
                raise

    def split_text(self, text: str) -> list:
        """Tách văn bản thành các chunk với kích thước và overlap được chỉ định."""
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + self.chunk_size
            
            if end >= text_length:
                chunks.append(text[start:])
                break
                
            # Tìm vị trí kết thúc chunk phù hợp (kết thúc câu hoặc dấu xuống dòng)
            while end > start and text[end] not in ['.', '!', '?', '\n']:
                end -= 1
                
            if end == start:
                end = start + self.chunk_size
                
            chunks.append(text[start:end])
            start = end - self.chunk_overlap
            
        return chunks

    def process_file(self, file_path: str):
        from services.file_manager import read_file_from_path
        """Xử lý file và lưu vào database chỉ khi nội dung thay đổi"""
        try:
            file_name = os.path.basename(file_path)
            
            # Đọc nội dung file
            content = read_file_from_path(file_path)
            
            # Kết nối database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Kiểm tra file hiện tại trong database
                cursor.execute("SELECT id, size FROM files WHERE name = ?", (file_name,))
                result = cursor.fetchone()
                
                # Nếu file đã tồn tại, kiểm tra xem nội dung có thay đổi không
                if result:
                    file_id, old_size = result
                    if old_size == len(content):
                        # Nội dung không thay đổi, không cần xử lý lại
                        cursor.execute("UPDATE files SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (file_id,))
                        conn.commit()
                        return  # Thoát nếu không cần cập nhật
                
                # Tách nội dung thành chunks
                chunks = self.split_text(content)
                
                # Thêm hoặc cập nhật thông tin file
                cursor.execute("""
                    INSERT INTO files (name, size, created_at, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT(name) DO UPDATE SET
                        size = excluded.size,
                        updated_at = CURRENT_TIMESTAMP
                """, (file_name, len(content)))
                
                # Lấy file_id
                cursor.execute("SELECT id FROM files WHERE name = ?", (file_name,))
                file_id = cursor.fetchone()[0]
                
                # Xóa chunks cũ và thêm chunks mới chỉ khi cần
                cursor.execute("DELETE FROM chunks WHERE file_id = ?", (file_id,))
                for chunk_index, chunk in enumerate(chunks):
                    cursor.execute("""
                        INSERT INTO chunks (file_id, content, chunk_index, created_at)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """, (file_id, chunk, chunk_index))
                
                conn.commit()
                
        except Exception as e:
            print(f"Lỗi khi xử lý file {file_path}: {str(e)}")
            raise

    def delete_file_from_db(self, file_name: str):
        """Xóa dữ liệu của file khỏi database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute("BEGIN TRANSACTION")
                
                # Lấy file_id
                cursor.execute("SELECT id FROM files WHERE name = ?", (file_name,))
                result = cursor.fetchone()
                
                if result:
                    file_id = result[0]
                    # Xóa chunks
                    cursor.execute("DELETE FROM chunks WHERE file_id = ?", (file_id,))
                    # Xóa file
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

    def update_from_uploaded_files(self):
        """Đồng bộ dữ liệu từ uploaded_files vào VectorDB"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Lấy danh sách các file trong database
            cursor.execute("SELECT name FROM files")
            db_files = {row[0] for row in cursor.fetchall()}
            
            # Lấy danh sách các file trong thư mục uploaded_files
            uploaded_files = set()
            for file in os.listdir(self.uploaded_files_dir):
                if file.endswith(('.txt', '.pdf', '.doc', '.docx', '.yaml', '.yml')):
                    uploaded_files.add(file)
            
            conn.close()
                    
            # Xóa dữ liệu của các file không còn tồn tại trong thư mục
            files_to_delete = db_files - uploaded_files
            for file_name in files_to_delete:
                self.delete_file_from_db(file_name)
                
            # Cập nhật dữ liệu cho các file mới hoặc đã thay đổi
            for file_name in uploaded_files:
                file_path = os.path.join(self.uploaded_files_dir, file_name)
                self.process_file(file_path)
                    
        except Exception as e:
            print(f"Lỗi khi đồng bộ dữ liệu: {str(e)}")

    def reset_db(self):
        """Xóa và tạo lại database"""
        try:
            # Xóa file database cũ nếu tồn tại
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
                print(f"Đã xóa database cũ: {self.db_path}")
            
            # Tạo database mới
            self.init_db()
            print("Đã tạo database mới thành công")
        except Exception as e:
            print(f"Lỗi khi reset database: {str(e)}")
            raise

    def get_chunk_by_id(self, doc_id: int) -> str:
        """Lấy nội dung chunk theo ID"""
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

    def get_all_chunks(self) -> list:
        """Lấy tất cả các chunks từ database"""
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

    def get_chunks_by_file(self, file_name: str) -> list:
        """Lấy tất cả chunks của một file"""
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

    def get_all_files(self) -> list:
        """Lấy danh sách tất cả các file từ database"""
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

    def delete_file_data(self, file_name: str):
        """Xóa dữ liệu của file khỏi database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Lấy file_id
                cursor.execute("SELECT id FROM files WHERE name = ?", (file_name,))
                result = cursor.fetchone()
                
                if result:
                    file_id = result[0]
                    # Xóa chunks
                    cursor.execute("DELETE FROM chunks WHERE file_id = ?", (file_id,))
                    # Xóa file
                    cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
                    print(f"Đã xóa dữ liệu của file {file_name} khỏi database")
                
                conn.commit()
                
        except Exception as e:
            print(f"Lỗi khi xóa dữ liệu của file {file_name}: {str(e)}")
            raise 