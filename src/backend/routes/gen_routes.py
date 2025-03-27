from fastapi import APIRouter
from services.generator import GeneratorService

router = APIRouter()
gen_service = GeneratorService()

@router.get("/gen_content")
async def generate_content(prompt: str, rag_response: str = None, web_response: str = None, file_response: str = None):
    return {"content": await gen_service.generate_content(prompt, rag_response, web_response, file_response)}

@router.get("/inDepth_context")
async def inDepth_context(prompt: str):
    print(prompt)
    content = await gen_service.inDepth_context(prompt)
    return {"content": content}