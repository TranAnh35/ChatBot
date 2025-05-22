from fastapi import APIRouter
from services.llm.generator import GeneratorService
from typing import Dict, Optional
from .schemas import WebResults

router = APIRouter()
gen_service = GeneratorService()

@router.get("/gen_content", response_model=Dict[str, str])
async def generate_content(
    prompt: str, 
    conversation_id: Optional[str] = None, 
    rag_response: Optional[str] = None, 
    web_response: Optional[str] = None, 
    file_response: Optional[str] = None
) -> Dict[str, str]:
    """Tạo nội dung dựa trên prompt và các ngữ cảnh bổ sung.
    
    Agrs:
        prompt (str): Nội dung prompt cần xử lý.
        conversation_id (Optional[str]): ID của hội thoại (nếu có).
        rag_response (Optional[str]): Phản hồi từ hệ thống RAG (nếu có).
        web_response (Optional[str]): Kết quả tìm kiếm web (nếu có).
        file_response (Optional[str]): Nội dung từ file đính kèm (nếu có).
        
    Returns:
        Dict[str, str]: Chứa nội dung được tạo ra từ mô hình ngôn ngữ.
    """
    return {
        "content": await gen_service.generate_content(
            prompt, 
            conversation_id, 
            rag_response, 
            web_response, 
            file_response
        )
    }

@router.post("/merge_context", response_model=Dict[str, str])
async def merge_context(web_results: WebResults) -> Dict[str, str]:
    """Hợp nhất và xử lý ngữ cảnh từ nhiều kết quả tìm kiếm web.
    
    Agrs:
        web_results (WebResults): Đối tượng chứa các kết quả tìm kiếm web.
        
    Returns:
        Dict[str, str]: Chứa nội dung đã được tổng hợp từ các kết quả tìm kiếm.
    """
    content = await gen_service.merge_context(web_results.results)
    return {"content": content} 