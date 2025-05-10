from fastapi import APIRouter
from services.generator import GeneratorService
from typing import List, Dict
from pydantic import BaseModel

router = APIRouter()
gen_service = GeneratorService()

class WebSearchItem(BaseModel):
    title: str
    link: str
    snippet: str

class WebResults(BaseModel):
    results: List[List[WebSearchItem]]

@router.get("/gen_content")
async def generate_content(prompt: str, conversation_id: str = None, rag_response: str = None, 
                          web_response: str = None, file_response: str = None):
    """Generate content with optional conversation history"""
    return {"content": await gen_service.generate_content(prompt, conversation_id, rag_response, web_response, file_response)}

@router.post("/merge_context")
async def merge_context(web_results: WebResults):
    content = await gen_service.merge_context(web_results.results)
    return {"content": content}