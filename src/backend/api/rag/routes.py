from fastapi import APIRouter
from services.rag.rag import RAGService
from typing import Dict

router = APIRouter()
rag_service = RAGService()

@router.get("/query", response_model=Dict[str, str])
async def rag_query(question: str):
    """Truy vấn hệ thống RAG với câu hỏi đầu vào. """
    return {"response": rag_service.query(question)}

@router.post("/sync-files", response_model=Dict[str, str])
async def sync_files():
    """Đồng bộ dữ liệu từ thư mục upload vào VectorDB. """
    updated = rag_service.check_and_update_files()
    return {
        "message": "Đã đồng bộ dữ liệu thành công" if updated 
        else "Không có thay đổi nào được phát hiện"
    }