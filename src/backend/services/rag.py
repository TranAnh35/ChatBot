import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from services.vector_db import VectorDB
from models.llm import LLM
import time

FAISS_INDEX_PATH = "faiss_index.bin"
CHUNK_MAPPING_PATH = "chunk_mapping.npy"
LAST_CHECK_FILE = "last_check.txt"

class RAGService:
    def __init__(self):
        self.upload_dir = "upload"
        os.makedirs(self.upload_dir, exist_ok=True)
        self.vector_db = VectorDB()
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.llm = LLM()
        self.chunk_id_mapping = []
        self.load_or_create_index()  # Chỉ tải hoặc tạo index, không index lại files
        self.last_check_time = self.load_last_check_time()

    def load_last_check_time(self):
        """Tải thời gian kiểm tra cuối cùng"""
        try:
            if os.path.exists(LAST_CHECK_FILE):
                with open(LAST_CHECK_FILE, 'r') as f:
                    return float(f.read().strip())
            return 0
        except Exception as e:
            print(f"Lỗi khi tải thời gian kiểm tra cuối: {str(e)}")
            return 0

    def save_last_check_time(self):
        """Lưu thời gian kiểm tra hiện tại"""
        try:
            with open(LAST_CHECK_FILE, 'w') as f:
                f.write(str(time.time()))
        except Exception as e:
            print(f"Lỗi khi lưu thời gian kiểm tra: {str(e)}")

    def check_and_update_files(self):
        """Kiểm tra và cập nhật database nếu có thay đổi thực sự trong thư mục upload"""
        try:
            current_time = time.time()
            should_reindex = False
            
            files = os.listdir(self.upload_dir)
            db_files = self.vector_db.get_all_files()
            db_file_names = {file[1] for file in db_files}
            db_file_dict = {file[1]: file[4] for file in db_files}
            
            upload_info = {}
            for file_name in files:
                file_path = os.path.join(self.upload_dir, file_name)
                if file_name.endswith(('.txt', '.pdf', '.doc', '.docx', '.yaml', '.yml')):
                    mtime = os.path.getmtime(file_path)
                    upload_info[file_name] = mtime
            
            new_or_modified_files = []
            for file_name, mtime in upload_info.items():
                if file_name not in db_file_names or mtime > self.last_check_time:
                    new_or_modified_files.append(file_name)
                    should_reindex = True
            
            deleted_files = [f for f in db_file_names if f not in upload_info]
            if deleted_files:
                should_reindex = True
            
            if should_reindex:
                print("Phát hiện thay đổi trong thư mục upload:")
                if new_or_modified_files:
                    print(f"File mới hoặc đã sửa: {new_or_modified_files}")
                if deleted_files:
                    print(f"File đã xóa: {deleted_files}")
                
                for file_name in deleted_files:
                    self.vector_db.delete_file_data(file_name)
                
                for file_name in new_or_modified_files:
                    file_path = os.path.join(self.upload_dir, file_name)
                    try:
                        self.vector_db.process_file(file_path)
                    except Exception as e:
                        print(f"Lỗi khi xử lý file {file_name}: {str(e)}")
                
                self.index_files()
                self.save_last_check_time()
                self.last_check_time = current_time
                return True
            
            return False
        
        except Exception as e:
            print(f"Lỗi khi kiểm tra và cập nhật files: {str(e)}")
            return False

    def load_or_create_index(self):
        """Tải hoặc tạo mới FAISS index và chunk mapping"""
        try:
            if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(CHUNK_MAPPING_PATH):
                self.index = faiss.read_index(FAISS_INDEX_PATH)
                self.chunk_id_mapping = np.load(CHUNK_MAPPING_PATH).tolist()
                print("Đã tải FAISS index và chunk mapping")
            else:
                # Tạo index mới với kích thước vector phù hợp
                vector_size = self.model.get_sentence_embedding_dimension()
                self.index = faiss.IndexFlatL2(vector_size)
                self.chunk_id_mapping = []
                print("Đã tạo FAISS index mới")
        except Exception as e:
            print(f"Lỗi khi tải/tạo FAISS index: {str(e)}")
            raise

    def index_files(self):
        """Index tất cả các file trong thư mục upload"""
        try:
            # Lấy danh sách các file trong thư mục
            files = os.listdir(self.upload_dir)
            
            # Xóa index cũ và mapping cũ
            self.index = faiss.IndexFlatL2(self.model.get_sentence_embedding_dimension())
            self.chunk_id_mapping = []
            
            for file_name in files:
                if file_name.endswith(('.txt', '.pdf', '.doc', '.docx', '.yaml', '.yml')):
                    file_path = os.path.join(self.upload_dir, file_name)
                    try:
                        # Xử lý file với VectorDB
                        self.vector_db.process_file(file_path)
                        
                        # Lấy chunks từ database
                        chunks = self.vector_db.get_chunks_by_file(file_name)
                        
                        # Xử lý từng chunk
                        for chunk_id, content, chunk_index in chunks:
                            # Tạo vector embedding
                            vector = self.model.encode(content, convert_to_tensor=False).reshape(1, -1)
                            self.index.add(vector)
                            # Lưu mapping giữa FAISS index và chunk_id
                            self.chunk_id_mapping.append(chunk_id)
                            
                    except Exception as e:
                        print(f"Lỗi khi xử lý file {file_name}: {str(e)}")
                        continue
            
            # Lưu FAISS index và chunk mapping
            faiss.write_index(self.index, FAISS_INDEX_PATH)
            np.save(CHUNK_MAPPING_PATH, np.array(self.chunk_id_mapping))
                    
        except Exception as e:
            print(f"Lỗi khi index files: {str(e)}")
            raise

    def retrieve_context(self, query):
        """Tìm kiếm file phù hợp nhất bằng FAISS."""
        try:
            # Tạo vector embedding cho câu hỏi
            query_vector = self.model.encode(query, convert_to_tensor=False).reshape(1, -1)
            
            # Tìm kiếm 5 kết quả gần nhất
            distances, indices = self.index.search(query_vector, 5)
            
            if indices[0][0] == -1 or len(self.chunk_id_mapping) == 0:
                return "Không tìm thấy thông tin phù hợp."

            # Lấy nội dung từ các chunks gần nhất
            contexts = []
            for idx in indices[0]:
                if idx != -1 and idx < len(self.chunk_id_mapping):
                    # Lấy chunk_id từ mapping
                    chunk_id = self.chunk_id_mapping[idx]
                    content = self.vector_db.get_chunk_by_id(chunk_id)
                    if content:
                        contexts.append(content)

            # Kết hợp các contexts thành một đoạn văn bản
            if contexts:
                return "\n".join(contexts)
            return "Không tìm thấy nội dung phù hợp."

        except Exception as e:
            print(f"Lỗi khi tìm kiếm context: {str(e)}")
            return "Có lỗi xảy ra khi tìm kiếm thông tin."

    async def query(self, question: str) -> str:
        """Tìm kiếm và sinh câu trả lời từ LLM."""
        try:
            # Lấy context từ FAISS
            context = self.retrieve_context(question)
            
            # Sử dụng generateContent với context từ RAG
            response = await self.llm.generateContent(question, context)
            return response

        except Exception as e:
            print(f"Lỗi khi xử lý câu hỏi: {str(e)}")
            return "Xin lỗi, tôi không thể xử lý câu hỏi của bạn lúc này."
