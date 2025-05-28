from fastapi import APIRouter, HTTPException
from .schemas import ConversationCreate, MessageCreate, ConversationRename
from services.conversation.service import ConversationService
from typing import List, Dict, Any

router = APIRouter()
conversation_service = ConversationService()

@router.post("/create", response_model=Dict[str, str])
async def create_conversation(request: ConversationCreate):
    """Tạo một hội thoại mới."""
    conversation_id = conversation_service.create_conversation(request.user_id)
    return {"conversation_id": conversation_id}

@router.post("/message", response_model=Dict[str, bool])
async def add_message(request: MessageCreate):
    """Thêm tin nhắn vào hội thoại."""
    success = conversation_service.add_message(
        request.conversation_id,
        request.role,
        request.content
    )
    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy hội thoại")
    return {"success": True}

@router.post("/rename", response_model=Dict[str, bool])
async def rename_conversation(request: ConversationRename):
    """Đổi tên hội thoại."""
    success = conversation_service.rename_conversation(
        request.conversation_id,
        request.title
    )
    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy hội thoại")
    return {"success": True}

@router.get("/{conversation_id}", response_model=Dict[str, Any])
async def get_conversation(conversation_id: str):
    """Lấy thông tin chi tiết của một hội thoại."""
    conversation = conversation_service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Không tìm thấy hội thoại")
    return conversation

@router.get("/{conversation_id}/history", response_model=Dict[str, List[Dict]])
async def get_conversation_history(conversation_id: str, limit: int = 10):
    """Lấy lịch sử tin nhắn của một hội thoại."""
    messages = conversation_service.get_conversation_history(conversation_id, limit)
    return {"messages": messages}

@router.get("/user/{user_id}", response_model=Dict[str, List[Dict]])
async def list_user_conversations(user_id: str):
    """Liệt kê tất cả hội thoại của một người dùng."""
    conversations = conversation_service.list_conversations(user_id)
    return {"conversations": conversations}

@router.delete("/{conversation_id}", response_model=Dict[str, bool])
async def delete_conversation(conversation_id: str):
    """Xóa một hội thoại."""
    success = conversation_service.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Không tìm thấy hội thoại")
    return {"success": True}