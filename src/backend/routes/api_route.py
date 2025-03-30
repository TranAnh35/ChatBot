from fastapi import APIRouter, Body
from services.api_manager import ApiManager

router = APIRouter()
api_manager = ApiManager()

@router.get("/get_api_key")
async def get_api_key():
    return api_manager.get_api_key()

@router.post("/set_api_key")
async def set_api_key(apiKey: str = Body(...)):
    try:
        api_manager.set_api_key(apiKey)
        return {"message": "API key set successfully"}
    except Exception as e:
        return {"error": str(e)}, 500
    
@router.post("/validate_api_key")
async def validate_api_key(apiKey: str = Body(...)):
    is_valid = api_manager.is_api_key_valid(apiKey)
    return {"valid": is_valid}
    
    