"""Các hằng số dùng chung cho RAGService và các tiện ích liên quan."""

FAISS_INDEX_PATH = "faiss_index.bin"
CHUNK_MAPPING_PATH = "chunk_mapping.npy"
LAST_CHECK_FILE = "last_check.txt"
SUPPORTED_FILE_EXTENSIONS = {
    '.txt', '.pdf', '.doc', '.docx', '.yaml', '.yml'
} 