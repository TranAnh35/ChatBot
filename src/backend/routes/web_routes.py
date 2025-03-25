from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from services.web_search import WebSearch

router = APIRouter()
web_search = WebSearch()

class SearchQuery(BaseModel):
    query: str
    num_results: int = 5

class URLQuery(BaseModel):
    url: str

@router.post("/search")
async def search(query: SearchQuery):
    """
    Thực hiện tìm kiếm web với query đã cho
    """
    if not query.query:
        raise HTTPException(status_code=400, detail="Query không được để trống")
    
    results = web_search.search(query.query, query.num_results)
    return {"results": results}

@router.post("/page-content")
async def get_page_content(query: URLQuery):
    """
    Lấy nội dung của một trang web
    """
    if not query.url:
        raise HTTPException(status_code=400, detail="URL không được để trống")
    
    content = web_search.get_page_content(query.url)
    return {"content": content} 