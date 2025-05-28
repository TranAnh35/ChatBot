import os
import sqlite3
import threading
from typing import Optional, Tuple, List
from contextlib import contextmanager


class DatabaseManager:
    """Quản lý các operations liên quan đến database SQLite."""
    
    def __init__(self, db_path: str = "vector_store.db") -> None:
        self.db_path = db_path
        self.current_version = 2
        self._lock = threading.Lock()
        
    def init_db(self) -> None:
        """Khởi tạo cơ sở dữ liệu SQLite."""
        with self._lock:
            try:
                with self.get_connection() as conn:
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
                        cursor.execute(
                            "INSERT INTO version (id, version) VALUES (1, ?)", 
                            (self.current_version,)
                        )
                    else:
                        db_version = result[0]
                        if db_version < self.current_version:
                            self._update_schema(cursor, db_version)
                            cursor.execute(
                                "UPDATE version SET version = ? WHERE id = 1", 
                                (self.current_version,)
                            )
                    
                    conn.commit()
                    print("Đã khởi tạo/cập nhật database thành công")
            except Exception as e:
                print(f"Lỗi khi khởi tạo database: {str(e)}")
                raise

    @contextmanager
    def get_connection(self):
        """Context manager để quản lý database connection."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

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
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='documents'"
                )
                if cursor.fetchone() is None:
                    self._create_initial_schema(cursor)
                    return
                
                cursor.execute(
                    "CREATE TABLE IF NOT EXISTS documents_backup AS SELECT * FROM documents"
                )
                
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

    def check_file_changed(
        self, 
        file_name: str, 
        content_size: int
    ) -> Tuple[bool, Optional[int]]:
        """Kiểm tra xem file đã thay đổi so với bản lưu trữ trong database chưa."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
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
                conn.commit()
                return False, file_id
                
            return True, file_id

    def update_file_metadata(self, file_name: str, content_size: int) -> int:
        """Cập nhật thông tin metadata của file trong database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO files (name, size, created_at, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(name) DO UPDATE SET
                    size = excluded.size,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (file_name, content_size))
            
            result = cursor.fetchone()
            conn.commit()
            return result[0] if result else None

    def update_file_chunks(self, file_id: int, chunks: List[str]) -> None:
        """Cập nhật các chunks của file trong database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chunks WHERE file_id = ?", (file_id,))
            
            for chunk_index, chunk in enumerate(chunks):
                cursor.execute("""
                    INSERT INTO chunks (file_id, content, chunk_index, created_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (file_id, chunk, chunk_index))
            
            conn.commit()

    def delete_file_from_db(self, file_name: str) -> None:
        """Xóa dữ liệu của file khỏi database."""
        with self.get_connection() as conn:
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