from fastapi import APIRouter
from typing import List, Dict
from services.web_search import WebSearch

router = APIRouter()
web_search = WebSearch()

@router.get("/search")
async def search(query: str):
    """Thực hiện tìm kiếm trên Google và lấy kết quả."""
    return await web_search.perform_search(query)

@router.post("/page-content")
async def page_content(url: str):
    """Lấy nội dung trang web từ URL đã cho."""
    return await web_search.get_page_content(url)