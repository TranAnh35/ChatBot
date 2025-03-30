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
async def generate_content(prompt: str, rag_response: str = None, web_response: str = None, file_response: str = None):
    print()
    return {"content": await gen_service.generate_content(prompt, rag_response, web_response, file_response)}

@router.get("/inDepth_context")
async def inDepth_context(prompt: str):
    content = await gen_service.inDepth_context(prompt)
    return {"content": content}

@router.post("/merge_context")
async def merge_context(web_results: WebResults):
    content = await gen_service.merge_context(web_results.results)
    return {"content": content}