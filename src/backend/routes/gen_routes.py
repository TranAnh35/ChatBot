from fastapi import APIRouter
from services.generator import GeneratorService

router = APIRouter()
gen_service = GeneratorService()

@router.get("/content")
async def generate_content(prompt: str, rag_response: str = None, web_response: str = None, file_response: str = None):
    print(file_response)
    return {"content": await gen_service.generate_content(prompt, rag_response, web_response, file_response)}