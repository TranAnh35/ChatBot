import os
import faiss
import numpy as np
from typing import Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

FAISS_INDEX_PATH = "faiss_index.bin"
CHUNK_MAPPING_PATH = "chunk_mapping.npy"

def create_new_index(vector_size: int, num_vectors: int = 0, use_gpu: bool = False) -> Any:
    """Tạo FAISS index mới với thuật toán tối ưu dựa trên số lượng vectors."""
    
    # Chọn thuật toán index dựa trên số lượng vectors
    if num_vectors < 1000:
        # Với dataset nhỏ, sử dụng FlatL2 (exact search)
        index = faiss.IndexFlatL2(vector_size)
        logger.info("Created IndexFlatL2 for small dataset")
    elif num_vectors < 10000:
        # Với dataset trung bình, sử dụng HNSW
        index = faiss.IndexHNSWFlat(vector_size, 32)
        index.hnsw.efConstruction = 200  # Tăng chất lượng build
        index.hnsw.efSearch = 50         # Tăng chất lượng search
        logger.info("Created IndexHNSWFlat for medium dataset")
    else:
        # Với dataset lớn, sử dụng IVF với clustering
        nlist = min(int(np.sqrt(num_vectors)), 4096)  # Số clusters
        quantizer = faiss.IndexFlatL2(vector_size)
        index = faiss.IndexIVFFlat(quantizer, vector_size, nlist)
        logger.info(f"Created IndexIVFFlat with {nlist} clusters for large dataset")
    
    # GPU support nếu có
    if use_gpu and faiss.get_num_gpus() > 0:
        try:
            res = faiss.StandardGpuResources()
            index = faiss.index_cpu_to_gpu(res, 0, index)
            logger.info("Moved index to GPU")
        except Exception as e:
            logger.warning(f"Failed to move index to GPU: {e}")
    
    return index

def create_optimized_index(vector_size: int, num_vectors: int, training_vectors: Optional[np.ndarray] = None) -> Any:
    """Tạo index được tối ưu hóa với training data."""
    
    if num_vectors < 1000:
        return create_new_index(vector_size, num_vectors)
    
    # Sử dụng composite index cho hiệu suất tốt nhất
    if num_vectors < 10000:
        # Với dataset trung bình, sử dụng HNSW thay vì PQ
        index = faiss.IndexHNSWFlat(vector_size, 32)
        index.hnsw.efConstruction = 200
        index.hnsw.efSearch = 50
        logger.info("Created IndexHNSWFlat for optimized medium dataset")
    elif num_vectors < 50000:
        # HNSW với PQ compression cho dataset lớn hơn
        try:
            index = faiss.IndexHNSWPQ(vector_size, 8, 8)  # 8 bytes per vector
            index.hnsw.efConstruction = 200
            index.hnsw.efSearch = 50
            logger.info("Created IndexHNSWPQ for optimized large dataset")
        except Exception as e:
            logger.warning(f"Failed to create HNSWPQ, falling back to HNSW: {e}")
            index = faiss.IndexHNSWFlat(vector_size, 32)
            index.hnsw.efConstruction = 200
            index.hnsw.efSearch = 50
    else:
        # IVF với clustering cho dataset rất lớn
        nlist = min(int(np.sqrt(num_vectors)), 4096)
        
        # Đảm bảo có đủ training data cho clustering
        min_training_points = nlist * 39  # FAISS recommends 39x clusters
        if training_vectors is not None and len(training_vectors) < min_training_points:
            logger.warning(f"Not enough training data ({len(training_vectors)}) for {nlist} clusters, using simpler index")
            index = faiss.IndexHNSWFlat(vector_size, 32)
            index.hnsw.efConstruction = 200
            index.hnsw.efSearch = 50
        else:
            try:
                index = faiss.IndexIVFPQ(faiss.IndexFlatL2(vector_size), vector_size, nlist, 8, 8)
                index.nprobe = min(32, nlist // 4)  # Số clusters để search
                logger.info(f"Created IndexIVFPQ with {nlist} clusters for very large dataset")
            except Exception as e:
                logger.warning(f"Failed to create IVFPQ, falling back to IVFFlat: {e}")
                index = faiss.IndexIVFFlat(faiss.IndexFlatL2(vector_size), vector_size, nlist)
                index.nprobe = min(32, nlist // 4)
    
    # Training nếu cần thiết và có training data
    if hasattr(index, 'is_trained') and not index.is_trained and training_vectors is not None:
        try:
            logger.info("Training index with sample data...")
            index.train(training_vectors.astype('float32'))
            logger.info("Index training completed")
        except Exception as e:
            logger.error(f"Training failed: {e}")
            # Fallback to simpler index
            return faiss.IndexFlatL2(vector_size)
    
    return index

def save_index_to_disk(index: Any, chunk_id_mapping: list) -> None:
    """Lưu FAISS index và chunk mapping ra file với compression."""
    try:
        os.makedirs(os.path.dirname(FAISS_INDEX_PATH) or '.', exist_ok=True)
        
        # Lưu index
        faiss.write_index(index, FAISS_INDEX_PATH)
        
        # Lưu mapping với compression
        np.savez_compressed(
            CHUNK_MAPPING_PATH.replace('.npy', '.npz'), 
            mapping=np.array(chunk_id_mapping, dtype=object)
        )
        
        logger.info(f"Saved index with {index.ntotal} vectors and {len(chunk_id_mapping)} mappings")
        
    except Exception as e:
        logger.error(f"Error saving index to disk: {e}")
        raise

def load_index_and_mapping() -> Tuple[Any, list]:
    """Load FAISS index và chunk mapping từ file."""
    try:
        # Load index
        index = faiss.read_index(FAISS_INDEX_PATH)
        
        # Load mapping (hỗ trợ cả .npy và .npz)
        npz_path = CHUNK_MAPPING_PATH.replace('.npy', '.npz')
        if os.path.exists(npz_path):
            data = np.load(npz_path, allow_pickle=True)
            chunk_id_mapping = data['mapping'].tolist()
        else:
            # Fallback to old .npy format
            chunk_id_mapping = np.load(CHUNK_MAPPING_PATH, allow_pickle=True).tolist()
        
        logger.info(f"Loaded index with {index.ntotal} vectors and {len(chunk_id_mapping)} mappings")
        return index, chunk_id_mapping
        
    except Exception as e:
        logger.error(f"Error loading index from disk: {e}")
        raise

def optimize_search_params(index: Any, num_queries: int = 100) -> None:
    """Tối ưu hóa tham số search cho index."""
    try:
        if hasattr(index, 'hnsw'):
            # Tối ưu HNSW parameters
            if num_queries < 10:
                index.hnsw.efSearch = 100  # Chất lượng cao cho ít queries
            else:
                index.hnsw.efSearch = 50   # Cân bằng speed/quality
                
        elif hasattr(index, 'nprobe'):
            # Tối ưu IVF parameters
            total_clusters = index.nlist
            if num_queries < 10:
                index.nprobe = min(64, total_clusters // 2)  # Search nhiều clusters
            else:
                index.nprobe = min(32, total_clusters // 4)  # Cân bằng
                
        logger.info("Optimized search parameters")
        
    except Exception as e:
        logger.warning(f"Failed to optimize search params: {e}")

def get_index_info(index: Any) -> dict:
    """Lấy thông tin về FAISS index."""
    info = {
        "type": type(index).__name__,
        "vector_size": index.d,
        "num_vectors": index.ntotal,
        "is_trained": getattr(index, 'is_trained', True)
    }
    
    # Xử lý HNSW attributes với error handling
    if hasattr(index, 'hnsw') and index.hnsw is not None:
        try:
            info.update({
                "efConstruction": getattr(index.hnsw, 'efConstruction', 'N/A'),
                "efSearch": getattr(index.hnsw, 'efSearch', 'N/A'),
                "M": getattr(index.hnsw, 'M', 32)  # Default value
            })
        except Exception as e:
            logger.warning(f"Could not get HNSW attributes: {e}")
            info["hnsw_info"] = "Available but attributes not accessible"
    
    # Xử lý IVF attributes
    if hasattr(index, 'nprobe'):
        try:
            info.update({
                "nlist": getattr(index, 'nlist', 'N/A'),
                "nprobe": getattr(index, 'nprobe', 'N/A')
            })
        except Exception as e:
            logger.warning(f"Could not get IVF attributes: {e}")
    
    return info 