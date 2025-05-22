"""Tiện ích xử lý relevance, web search result, batch embedding cho RAGService."""

from typing import List, Dict, Any
import numpy as np

def calculate_relevance(query: str, result: Dict[str, Any]) -> float:
    """Tính điểm relevance của kết quả tìm kiếm với query.

    Args:
        query (str): Truy vấn tìm kiếm.
        result (Dict[str, Any]): Kết quả tìm kiếm.
    Returns:
        float: Điểm relevance từ 0.0 đến 1.0.
    """
    query_terms = set(term.lower() for term in query.split() if len(term) > 2)
    if not query_terms:
        return 0.0
    title = result.get('title', '').lower()
    snippet = result.get('snippet', '').lower()
    title_matches = sum(1 for term in query_terms if term in title)
    snippet_matches = sum(1 for term in query_terms if term in snippet)
    relevance = (title_matches * 0.7) + (snippet_matches * 0.3)
    max_possible = len(query_terms)
    if max_possible > 0:
        relevance = min(1.0, relevance / max_possible)
    return round(relevance, 2)

def process_web_search_results(query: str, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Xử lý và sắp xếp kết quả tìm kiếm web theo relevance.

    Args:
        query (str): Truy vấn tìm kiếm.
        search_results (List[Dict[str, Any]]): Danh sách kết quả thô.
    Returns:
        List[Dict[str, Any]]: Danh sách kết quả đã xử lý và sắp xếp.
    """
    processed_results = []
    for result in search_results:
        processed_result = {
            'title': result.get('title', ''),
            'link': result.get('link', ''),
            'snippet': result.get('snippet', ''),
            'relevance': calculate_relevance(query, result)
        }
        processed_results.append(processed_result)
    processed_results.sort(key=lambda x: x['relevance'], reverse=True)
    return processed_results

def process_chunk_batch(model, chunks_batch: List[Any]) -> tuple:
    """Tạo embedding và mapping cho batch chunk.

    Args:
        model: SentenceTransformer model.
        chunks_batch (List[Any]): Batch chunk.
    Returns:
        tuple: (embeddings np.ndarray, batch_mappings list)
    """
    batch_texts = [chunk[2] for chunk in chunks_batch]
    batch_embeddings = model.encode(batch_texts, show_progress_bar=False)
    batch_mappings = []
    for chunk in chunks_batch:
        batch_mappings.append({
            'chunk_id': chunk[0],
            'file_id': chunk[1],
            'metadata': {
                'file_name': chunk[3],
                'chunk_index': chunk[4]
            }
        })
    return np.array(batch_embeddings, dtype='float32'), batch_mappings 