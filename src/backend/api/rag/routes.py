from fastapi import APIRouter
from services.rag.rag import RAGService
from typing import Dict

router = APIRouter()
rag_service = RAGService()
# rag_service.index_files()

@router.get("/query", response_model=Dict[str, str])
async def rag_query(question: str):
    """Truy vấn hệ thống RAG với câu hỏi đầu vào.
    
    Hệ thống sẽ tìm kiếm thông tin liên quan từ cơ sở dữ liệu vector
    và trả về câu trả lời dựa trên ngữ cảnh tìm được.
    
    Agrs:
        question (str): Câu hỏi cần tìm kiếm thông tin.
        
    Returns:
        dict: Chứa câu trả lời được tạo ra bởi mô hình RAG.
    """
    return {"response": rag_service.query(question)}

@router.post("/sync-files", response_model=Dict[str, str])
async def sync_files():
    """Đồng bộ dữ liệu từ thư mục upload vào VectorDB.
    
    Quét thư mục upload, kiểm tra các file mới hoặc thay đổi,
    sau đó cập nhật vào cơ sở dữ liệu vector để sử dụng cho việc tìm kiếm.
    
    Returns:
        dict: Thông báo kết quả quá trình đồng bộ.
    """
    updated = rag_service.check_and_update_files()
    return {
        "message": "Đã đồng bộ dữ liệu thành công" if updated 
        else "Không có thay đổi nào được phát hiện"
    }