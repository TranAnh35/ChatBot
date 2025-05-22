from fastapi import APIRouter
from typing import Dict, Any
from services.web.service import WebSearchService

router = APIRouter()
web_search = WebSearchService()

@router.get("/search", response_model=Dict[str, Any])
async def search(query: str):
    """Thực hiện tìm kiếm trên công cụ tìm kiếm và trả về kết quả.

    Args:
        query (str): Từ khóa hoặc cụm từ cần tìm kiếm.
    Returns:
        dict: Danh sách các kết quả tìm kiếm, mỗi kết quả gồm tiêu đề, đường dẫn và đoạn mô tả ngắn.
    """
    return await web_search.perform_search(query)

@router.post("/page-content", response_model=Dict[str, Any])
async def page_content(url: str):
    """Lấy nội dung chính của một trang web từ URL được cung cấp.

    Args:
        url (str): Đường dẫn URL của trang web cần lấy nội dung.
    Returns:
        dict: Chứa tiêu đề và nội dung chính của trang web.
    """
    return await web_search.get_page_content(url)