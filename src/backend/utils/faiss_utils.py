import os
import faiss
import numpy as np
from typing import Any

FAISS_INDEX_PATH = "faiss_index.bin"
CHUNK_MAPPING_PATH = "chunk_mapping.npy"

def create_new_index(vector_size: int) -> Any:
    """Tạo FAISS index mới."""
    return faiss.IndexFlatL2(vector_size)

def save_index_to_disk(index: Any, chunk_id_mapping: list) -> None:
    """Lưu FAISS index và chunk mapping ra file."""
    os.makedirs(os.path.dirname(FAISS_INDEX_PATH) or '.', exist_ok=True)
    faiss.write_index(index, FAISS_INDEX_PATH)
    np.save(CHUNK_MAPPING_PATH, np.array(chunk_id_mapping, dtype=object), allow_pickle=True)

def load_index_and_mapping() -> tuple:
    """Load FAISS index và chunk mapping từ file."""
    index = faiss.read_index(FAISS_INDEX_PATH)
    chunk_id_mapping = np.load(CHUNK_MAPPING_PATH, allow_pickle=True).tolist()
    return index, chunk_id_mapping 