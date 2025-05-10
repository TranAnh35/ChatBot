from fastapi import APIRouter, HTTPException
from services.conversation_service import ConversationService
from pydantic import BaseModel
from typing import List, Dict, Optional

router = APIRouter()
conversation_service = ConversationService()

class Message(BaseModel):
    role: str
    content: str

class ConversationCreate(BaseModel):
    user_id: str

class MessageCreate(BaseModel):
    conversation_id: str
    role: str
    content: str

class ConversationRename(BaseModel):
    conversation_id: str
    title: str

@router.post("/create")
async def create_conversation(request: ConversationCreate):
    """Create a new conversation"""
    conversation_id = conversation_service.create_conversation(request.user_id)
    return {"conversation_id": conversation_id}

@router.post("/message")
async def add_message(request: MessageCreate):
    """Add a message to a conversation"""
    success = conversation_service.add_message(
        request.conversation_id, 
        request.role, 
        request.content
    )
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"success": True}

@router.post("/rename")
async def rename_conversation(request: ConversationRename):
    """Rename a conversation"""
    success = conversation_service.rename_conversation(
        request.conversation_id,
        request.title
    )
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"success": True}

@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get a conversation by ID"""
    conversation = conversation_service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@router.get("/{conversation_id}/history")
async def get_conversation_history(conversation_id: str, limit: int = 10):
    """Get conversation history"""
    messages = conversation_service.get_conversation_history(conversation_id, limit)
    return {"messages": messages}

@router.get("/user/{user_id}")
async def list_user_conversations(user_id: str):
    """List all conversations for a user"""
    conversations = conversation_service.list_conversations(user_id)
    return {"conversations": conversations}

@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    success = conversation_service.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"success": True} 