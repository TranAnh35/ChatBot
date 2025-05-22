import os
import sqlite3
from typing import List, Dict, Tuple, Optional, Set, Any, Union
from pathlib import Path
from repositories.vector_db_repository import VectorDBRepository

class VectorDB:
    """Service quản lý logic xử lý file, chunk, đồng bộ, split text, ..."""
    _instance = None
    
    def __new__(cls):
        """Tạo instance mới của VectorDB nếu chưa tồn tại (Singleton pattern).
        
        Returns:
            VectorDB: Instance duy nhất của lớp VectorDB.
        """
        if cls._instance is None:
            cls._instance = super(VectorDB, cls).__new__(cls)
            cls._instance.db_path = "vector_store.db"
            cls._instance.upload_dir = "upload"
            cls._instance.chunk_size = 1000  # Kích thước mỗi chunk (số ký tự)
            cls._instance.chunk_overlap = 100  # Số ký tự chồng lấn
            cls._instance.current_version = 2  # Phiên bản cấu trúc database
            cls._instance.repository = VectorDBRepository(cls._instance.db_path)
            if not os.path.exists(cls._instance.db_path):
                print("Database không tồn tại, tạo mới...")
                cls._instance.init_db()
        return cls._instance

    def init_db(self) -> None:
        """Khởi tạo cơ sở dữ liệu SQLite.
        
        Tạo các bảng cần thiết nếu chưa tồn tại và kiểm tra phiên bản database.
        Tự động nâng cấp cấu trúc database nếu cần.
        
        Raises:
            Exception: Nếu có lỗi xảy ra trong quá trình khởi tạo.
        """
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

    def _create_initial_schema(self, cursor: sqlite3.Cursor) -> None:
        """Tạo cấu trúc ban đầu của cơ sở dữ liệu.
        
        Args:
            cursor (sqlite3.Cursor): Con trỏ đến cơ sở dữ liệu.
            
        Tạo các bảng:
            - files: Lưu trữ thông tin về các file đã tải lên.
            - chunks: Lưu trữ các đoạn văn bản đã được xử lý từ các file.
        """
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

    def _update_schema(self, cursor: sqlite3.Cursor, old_version: int) -> None:
        """Cập nhật cấu trúc database từ phiên bản cũ lên phiên bản mới.
        
        Args:
            cursor (sqlite3.Cursor): Con trỏ đến cơ sở dữ liệu.
            old_version (int): Phiên bản hiện tại của cơ sở dữ liệu.
            
        Note:
            - Phiên bản 1: Cấu trúc cũ với bảng 'documents'.
            - Phiên bản 2: Cấu trúc mới với bảng 'files' và 'chunks'.
        """
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

    def _find_optimal_split_point(self, text: str, start: int, end: int) -> int:
        """Tìm điểm tách tối ưu trong khoảng văn bản đã cho.
        
        Args:
            text: Văn bản cần tách.
            start: Vị trí bắt đầu tìm kiếm.
            end: Vị trí kết thúc tìm kiếm.
            
        Returns:
            int: Vị trí tách tối ưu (ưu tiên các dấu câu kết thúc câu hoặc xuống dòng).
        """
        # Các ký tự ưu tiên để tách câu
        SPLIT_CHARS = ['.', '!', '?', '\n', ',', ';', ' ']
        
        # Tìm ký tự phân tách phù hợp đầu tiên từ cuối về
        for split_char in SPLIT_CHARS:
            # Tìm từ cuối đoạn về trước để tìm ký tự phân tách
            pos = text.rfind(split_char, start, end + 1)
            if pos > start:  # Đảm bảo không trả về vị trí trước start
                return pos + 1  # +1 để bao gồm luôn ký tự phân tách
                
        # Nếu không tìm thấy điểm phân tách phù hợp, tách tại vị trí mặc định
        return end

    def split_text(self, text: str) -> List[str]:
        """Tách văn bản thành các đoạn (chunks) với kích thước và độ chồng lấn xác định.
        
        Args:
            text: Văn bản cần được tách thành các đoạn.
            
        Returns:
            Danh sách các đoạn văn bản đã được tách.
            
        Note:
            - Mỗi đoạn sẽ có độ dài tối đa là `chunk_size` ký tự.
            - Các đoạn liên tiếp sẽ chồng lấn nhau `chunk_overlap` ký tự.
            - Điểm tách ưu tiên các dấu câu kết thúc câu (., !, ?) hoặc xuống dòng.
        """
        if not text:
            return []
            
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            # Xác định điểm kết thúc tiềm năng
            end = min(start + self.chunk_size, text_length)
            
            # Nếu đã đến cuối văn bản, thêm phần còn lại và thoát
            if end >= text_length:
                if start < text_length:  # Chỉ thêm nếu còn dữ liệu
                    chunks.append(text[start:].strip())
                break
                
            # Tìm điểm tách tối ưu
            split_pos = self._find_optimal_split_point(text, start, end)
            
            # Nếu không tìm thấy điểm tách phù hợp, tách tại vị trí mặc định
            if split_pos <= start:
                split_pos = end
                
            # Thêm đoạn văn bản vào kết quả
            chunk = text[start:split_pos].strip()
            if chunk:  # Chỉ thêm nếu đoạn không rỗng
                chunks.append(chunk)
                
            # Di chuyển vị trí bắt đầu cho lần lặp tiếp theo (có tính đến độ chồng lấn)
            start = max(split_pos - self.chunk_overlap, start + 1)
            
        return chunks

    def _check_file_changed(self, cursor: sqlite3.Cursor, file_name: str, content_size: int) -> Tuple[bool, Optional[int]]:
        """Kiểm tra xem file đã thay đổi so với bản lưu trữ trong database chưa.
        
        Args:
            cursor: Con trỏ đến cơ sở dữ liệu.
            file_name: Tên file cần kiểm tra.
            content_size: Kích thước nội dung file hiện tại.
            
        Returns:
            Tuple[bool, Optional[int]]: 
                - bool: True nếu file đã thay đổi hoặc chưa tồn tại trong DB.
                - Optional[int]: ID của file nếu tồn tại, None nếu không.
        """
        cursor.execute("SELECT id, size FROM files WHERE name = ?", (file_name,))
        result = cursor.fetchone()
        
        if not result:
            return True, None  # File chưa tồn tại trong DB
            
        file_id, old_size = result
        if old_size == content_size:
            # Cập nhật thời gian truy cập nhưng không cần xử lý lại nội dung
            cursor.execute(
                "UPDATE files SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                (file_id,)
            )
            return False, file_id
            
        return True, file_id

    def _update_file_metadata(self, cursor: sqlite3.Cursor, file_name: str, content_size: int) -> int:
        """Cập nhật thông tin metadata của file trong database.
        
        Args:
            cursor: Con trỏ đến cơ sở dữ liệu.
            file_name: Tên file cần cập nhật.
            content_size: Kích thước nội dung file.
            
        Returns:
            int: ID của file đã được cập nhật hoặc tạo mới.
        """
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
        """Cập nhật các chunks của file trong database.
        
        Args:
            cursor: Con trỏ đến cơ sở dữ liệu.
            file_id: ID của file trong database.
            chunks: Danh sách các chunks cần lưu.
        """
        # Xóa các chunks cũ
        cursor.execute("DELETE FROM chunks WHERE file_id = ?", (file_id,))
        
        # Thêm các chunks mới
        for chunk_index, chunk in enumerate(chunks):
            cursor.execute("""
                INSERT INTO chunks (file_id, content, chunk_index, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (file_id, chunk, chunk_index))

    def process_file(self, file_path: str) -> None:
        """Xử lý file và lưu vào database nếu nội dung thay đổi.
        
        Args:
            file_path: Đường dẫn đến file cần xử lý.
            
        Raises:
            Exception: Nếu có lỗi xảy ra trong quá trình xử lý file.
        """
        from services.file_manager import read_file_from_path
        
        try:
            file_name = os.path.basename(file_path)
            content = read_file_from_path(file_path)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Kiểm tra xem file có thay đổi không
                has_changed, file_id = self._check_file_changed(cursor, file_name, len(content))
                if not has_changed:
                    conn.commit()
                    return  # Không cần xử lý thêm nếu không có thay đổi
                
                # Tách nội dung thành các chunks
                chunks = self.split_text(content)
                
                # Cập nhật thông tin file và lấy file_id
                file_id = self._update_file_metadata(cursor, file_name, len(content))
                
                # Cập nhật các chunks của file
                self._update_file_chunks(cursor, file_id, chunks)
                
                conn.commit()
                
        except Exception as e:
            print(f"Lỗi khi xử lý file {file_path}: {str(e)}")
            raise

    def delete_file_from_db(self, file_name: str) -> None:
        """Xóa dữ liệu của file khỏi database.
        
        Args:
            file_name (str): Tên file cần xóa.
            
        Note:
            - Xóa cả thông tin file trong bảng 'files' và các chunks liên quan trong 'chunks'.
            - Thực hiện trong một transaction để đảm bảo tính toàn vẹn dữ liệu.
        """
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

    def _get_db_files(self, cursor: sqlite3.Cursor) -> Set[str]:
        """Lấy danh sách tên các file đã lưu trong database.
        
        Args:
            cursor: Con trỏ đến cơ sở dữ liệu.
            
        Returns:
            Set[str]: Tập hợp các tên file đã lưu trong database.
        """
        cursor.execute("SELECT name FROM files")
        return {row[0] for row in cursor.fetchall()}
    
    def _get_uploaded_files(self) -> Set[str]:
        """Lấy danh sách các file trong thư mục upload.
        
        Returns:
            Set[str]: Tập hợp các tên file hợp lệ trong thư mục upload.
        """
        valid_extensions = {'.txt', '.pdf', '.doc', '.docx', '.yaml', '.yml'}
        return {
            file for file in os.listdir(self.upload_dir)
            if os.path.splitext(file)[1].lower() in valid_extensions
        }
    
    def _cleanup_missing_files(self, db_files: Set[str], uploaded_files: Set[str]) -> None:
        """Xóa dữ liệu của các file không còn tồn tại trong thư mục upload.
        
        Args:
            db_files: Tập hợp các tên file đã lưu trong database.
            uploaded_files: Tập hợp các tên file hiện có trong thư mục upload.
        """
        files_to_delete = db_files - uploaded_files
        for file_name in files_to_delete:
            try:
                self.delete_file_from_db(file_name)
                print(f"Đã xóa dữ liệu của file không còn tồn tại: {file_name}")
            except Exception as e:
                print(f"Lỗi khi xóa dữ liệu của file {file_name}: {str(e)}")
    
    def _process_uploaded_files(self, uploaded_files: Set[str]) -> None:
        """Xử lý các file mới hoặc đã thay đổi trong thư mục upload.
        
        Args:
            uploaded_files: Tập hợp các tên file cần xử lý.
        """
        for file_name in uploaded_files:
            try:
                file_path = os.path.join(self.upload_dir, file_name)
                self.process_file(file_path)
                print(f"Đã xử lý file: {file_name}")
            except Exception as e:
                print(f"Lỗi khi xử lý file {file_name}: {str(e)}")
    
    def update_from_upload(self) -> None:
        """Đồng bộ dữ liệu từ thư mục upload vào VectorDB.
        
        Thực hiện các thao tác:
            - Xóa dữ liệu của các file không còn tồn tại trong thư mục upload.
            - Cập nhật dữ liệu cho các file mới hoặc đã thay đổi.
            
        Note:
            - Chỉ xử lý các file có đuôi: .txt, .pdf, .doc, .docx, .yaml, .yml
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Lấy danh sách các file trong database
                db_files = self._get_db_files(cursor)
            
            # Lấy danh sách các file trong thư mục upload
            uploaded_files = self._get_uploaded_files()
            
            # Xử lý các file đã bị xóa khỏi thư mục upload
            self._cleanup_missing_files(db_files, uploaded_files)
            
            # Xử lý các file mới hoặc đã thay đổi
            self._process_uploaded_files(uploaded_files)
                    
        except Exception as e:
            print(f"Lỗi khi đồng bộ dữ liệu: {str(e)}")

    def reset_db(self) -> None:
        """Xóa và tạo lại cơ sở dữ liệu từ đầu.
        
        Cảnh báo: Hành động này sẽ xóa toàn bộ dữ liệu hiện có.
        
        Raises:
            Exception: Nếu có lỗi xảy ra trong quá trình reset.
        """
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

    def get_chunk_by_id(self, doc_id: int) -> Optional[str]:
        """Lấy nội dung chunk dựa trên ID.
        
        Args:
            doc_id (int): ID của chunk cần lấy.
            
        Returns:
            Optional[str]: Nội dung của chunk nếu tìm thấy, None nếu không tìm thấy.
            
        Raises:
            Exception: Nếu có lỗi khi truy vấn database.
        """
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
        """Lấy tất cả các chunks từ cơ sở dữ liệu.
        
        Returns:
            List[Tuple[int, str, str, int]]: Danh sách các chunks, mỗi chunk là một tuple
                chứa (id, nội dung, tên file, chỉ số chunk).
                
        Raises:
            Exception: Nếu có lỗi khi truy vấn database.
        """
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
        """Lấy tất cả các chunks thuộc về một file cụ thể.
        
        Args:
            file_name (str): Tên file cần lấy chunks.
            
        Returns:
            List[Tuple[int, str, int]]: Danh sách các chunks, mỗi chunk là một tuple
                chứa (id, nội dung, chỉ số chunk).
                
        Raises:
            Exception: Nếu có lỗi khi truy vấn database.
        """
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
        """Lấy danh sách tất cả các file đã được lưu trong database.
        
        Returns:
            List[Tuple[int, str, int, str, str]]: Danh sách các file, mỗi file là một tuple
                chứa (id, tên file, kích thước, ngày tạo, ngày cập nhật).
                
        Raises:
            Exception: Nếu có lỗi khi truy vấn database.
        """
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
        """Xóa toàn bộ dữ liệu liên quan đến một file khỏi database.
        
        Args:
            file_name (str): Tên file cần xóa.
            
        Note:
            - Xóa cả thông tin file trong bảng 'files' và tất cả các chunks liên quan.
            - Được thực hiện trong một transaction để đảm bảo tính toàn vẹn dữ liệu.
            
        Raises:
            Exception: Nếu có lỗi xảy ra trong quá trình xóa.
        """
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