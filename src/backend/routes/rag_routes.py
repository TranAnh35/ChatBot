from fastapi import APIRouter
from services.rag import RAGService

router = APIRouter()
rag_service = RAGService()
rag_service.index_files()

@router.get("/query")
async def rag_query(question: str):
    return {"response": await rag_service.query(question)}

@router.post("/sync-files")
async def sync_files():
    """Đồng bộ dữ liệu từ uploaded_files vào VectorDB"""
    updated = rag_service.check_and_update_files()
    return {"message": "Files synchronized successfully" if updated else "No changes detected"}
