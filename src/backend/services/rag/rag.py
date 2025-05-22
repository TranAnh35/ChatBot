import os
import time
import logging
from typing import List, Dict, Tuple, Optional, Set, Any
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from services.vector_db.service import VectorDB
from models.llm import LLM

# Import các tiện ích đã tách
from utils.rag_file_utils import (
    load_last_check_time, save_last_check_time, get_uploaded_files_info, process_file_changes
)
from utils.faiss_utils import create_new_index, save_index_to_disk, load_index_and_mapping
from utils.rag_utils import calculate_relevance, process_web_search_results, process_chunk_batch
from utils.rag_constants import FAISS_INDEX_PATH, CHUNK_MAPPING_PATH, LAST_CHECK_FILE, SUPPORTED_FILE_EXTENSIONS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('rag_service.log')
    ]
)
logger = logging.getLogger(__name__)

class RAGService:
    """Service for Retrieval-Augmented Generation (RAG) operations.
    
    This class combines language models with a vector database to provide
    context-aware responses based on stored documents.
    
    Attributes:
        upload_dir (str): Directory containing uploaded files.
        vector_db (VectorDB): Manages the vector database operations.
        model (SentenceTransformer): Text embedding model.
        llm (LLM): Large language model for response generation.
        chunk_id_mapping (List[int]): Mapping of chunk IDs.
        index (faiss.Index): FAISS index for vector search.
        last_check_time (float): Timestamp of last file check.
    """
    
    def __init__(self, upload_dir: str = "upload") -> None:
        """Initialize RAGService with required components.
        
        Args:
            upload_dir (str): Path to the directory containing uploaded files.
        """
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)
        self.vector_db = VectorDB()
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.llm = LLM()
        self.chunk_id_mapping = []
        self.index = None
        self.last_check_time = 0.0
        self._initialize_service()

    def _initialize_service(self) -> None:
        """Initialize the RAG service components."""
        try:
            self.load_or_create_index()
            self.last_check_time = load_last_check_time()
            logger.info("RAGService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAGService: {str(e)}")
            raise

    def _get_database_files_info(self) -> Tuple[Set[str], Dict[str, float]]:
        """Retrieve information about files stored in the database.
        
        Returns:
            Tuple[Set[str], Dict[str, float]]: Set of filenames, dict of filename to mtime.
        """
        try:
            db_files = self.vector_db.get_all_files()
            db_file_names = {file[1] for file in db_files}
            db_file_mtimes = {file[1]: file[4] for file in db_files}
            logger.debug(f"Retrieved info for {len(db_file_names)} files from database")
            return db_file_names, db_file_mtimes
        except Exception as e:
            logger.error(f"Error getting file info from database: {str(e)}")
            return set(), {}

    def _process_modified_files(self, file_names: List[str]) -> None:
        """Process new or modified files.
        
        Args:
            file_names (List[str]): List of filenames to process.
        """
        if not file_names:
            return
        logger.info(f"Starting processing of {len(file_names)} new/modified files")
        for file_name in file_names:
            file_path = os.path.join(self.upload_dir, file_name)
            try:
                start_time = time.time()
                self.vector_db.process_file(file_path)
                process_time = time.time() - start_time
                logger.info(f"Processed file {file_name} in {process_time:.2f}s")
            except FileNotFoundError:
                logger.warning(f"File not found: {file_name}")
            except PermissionError:
                logger.error(f"Permission denied reading file: {file_name}")
            except Exception as e:
                logger.error(f"Error processing file {file_name}: {str(e)}", exc_info=True)

    def _process_deleted_files(self, deleted_files: List[str]) -> None:
        """Process files that have been deleted from the upload directory.
        
        Args:
            deleted_files (List[str]): List of filenames that have been deleted.
        """
        if not deleted_files:
            return
        logger.info(f"Starting processing of {len(deleted_files)} deleted files")
        for file_name in deleted_files:
            try:
                self.vector_db.delete_file(file_name)
                logger.info(f"Removed file {file_name} from database")
            except Exception as e:
                logger.error(f"Error removing file {file_name}: {str(e)}")

    def check_and_update_files(self) -> bool:
        """Check for and process any changes in the upload directory.
        
        Returns:
            bool: True if changes were detected and processed, False otherwise.
        """
        try:
            upload_info = get_uploaded_files_info(self.upload_dir)
            db_file_names, db_file_mtimes = self._get_database_files_info()
            new_or_modified, deleted = process_file_changes(
                upload_info, db_file_names, db_file_mtimes, self.last_check_time
            )
            if not new_or_modified and not deleted:
                logger.debug("No changes detected in upload directory")
                return False
            if deleted:
                self._process_deleted_files(deleted)
            if new_or_modified:
                self._process_modified_files(new_or_modified)
            self.last_check_time = time.time()
            save_last_check_time()
            logger.info("Successfully updated database")
            return True
        except Exception as e:
            logger.critical(f"LỖI NGHIÊM TRỌNG khi kiểm tra và cập nhật files: {str(e)}", exc_info=True)
            raise

    def load_or_create_index(self) -> None:
        """Load or create a new FAISS index and chunk mapping."""
        try:
            index_exists = os.path.exists(FAISS_INDEX_PATH)
            mapping_exists = os.path.exists(CHUNK_MAPPING_PATH)
            if index_exists and mapping_exists:
                logger.info("Loading FAISS index and chunk mapping from disk...")
                self.index, self.chunk_id_mapping = load_index_and_mapping()
                logger.info(
                    f"Loaded index with {self.index.ntotal} vectors and "
                    f"{len(self.chunk_id_mapping)} chunk mappings"
                )
                return
            logger.info("Index files not found or corrupted, creating new index...")
            self.index = create_new_index(self.model.get_sentence_embedding_dimension())
            self.chunk_id_mapping = []
            save_index_to_disk(self.index, self.chunk_id_mapping)
        except Exception as e:
            logger.critical(f"Critical error initializing index: {str(e)}")
            raise

    # Các hàm xử lý relevance, chunk batch, web search result sẽ dùng utils
    def calculate_relevance(self, query: str, result: Dict[str, Any]) -> float:
        """Tính điểm relevance của kết quả tìm kiếm với query."""
        return calculate_relevance(query, result)

    def process_chunk_batch(self, chunks_batch: List[Any]) -> Tuple[np.ndarray, List[Dict]]:
        """Tạo embedding và mapping cho batch chunk."""
        return process_chunk_batch(self.model, chunks_batch)

    def process_web_search_results(self, query: str, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Xử lý và sắp xếp kết quả tìm kiếm web theo relevance."""
        return process_web_search_results(query, search_results)

    def query(self, question: str) -> str:
        """Truy vấn hệ thống RAG với câu hỏi đầu vào và trả về câu trả lời."""
        # 1. Lấy embedding cho câu hỏi
        query_embedding = self.model.encode([question])
        # 2. Tìm kiếm các chunk liên quan trong FAISS index
        if self.index is None or self.index.ntotal == 0:
            return "Không có dữ liệu để truy vấn. Vui lòng upload tài liệu trước."
        D, I = self.index.search(query_embedding, k=5)  # Lấy 5 chunk liên quan nhất
        # 3. Lấy nội dung các chunk từ mapping
        context_chunks = []
        for idx in I[0]:
            if idx < len(self.chunk_id_mapping):
                chunk_info = self.chunk_id_mapping[idx]
                # chunk_info có thể là dict hoặc str, tùy cách bạn lưu
                context_chunks.append(str(chunk_info))
        context = "\n".join(context_chunks)
        # 4. Sinh câu trả lời từ LLM
        prompt = f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
        response = self.llm.generate(prompt)
        return response
