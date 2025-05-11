from models.conversation import Conversation
from typing import List, Dict, Optional

class ConversationService:
    def __init__(self):
        self.conversation_model = Conversation()
    
    def create_conversation(self, user_id: str) -> str:
        """Create a new conversation"""
        return self.conversation_model.create_conversation(user_id)
    
    def add_message(self, conversation_id: str, role: str, content: str) -> bool:
        """Add a message to a conversation"""
        return self.conversation_model.add_message(conversation_id, role, content)
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Get a conversation by ID"""
        return self.conversation_model.get_conversation(conversation_id)
    
    def get_conversation_history(self, conversation_id: str, limit: int = 10) -> List[Dict]:
        """Get conversation history with optional limit"""
        return self.conversation_model.get_conversation_history(conversation_id, limit)
    
    def list_conversations(self, user_id: str) -> List[Dict]:
        """List all conversations for a user"""
        return self.conversation_model.list_conversations(user_id)
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        return self.conversation_model.delete_conversation(conversation_id)
    
    def rename_conversation(self, conversation_id: str, title: str) -> bool:
        """Rename a conversation"""
        return self.conversation_model.rename_conversation(conversation_id, title)
    
    def format_conversation_for_context(self, conversation_id: str, max_messages: int = 5) -> str:
        """Format conversation history for inclusion in LLM context"""
        messages = self.get_conversation_history(conversation_id, max_messages)
        if not messages:
            return ""
        
        # Tối ưu độ dài lịch sử hội thoại
        # Nếu có quá nhiều tin nhắn, giảm số lượng và độ dài nội dung
        if len(messages) > 3:
            # Nén các tin nhắn cũ hơn, chỉ giữ những tin nhắn gần đây đầy đủ
            for i in range(len(messages) - 3):
                # Giới hạn độ dài tin nhắn cũ hơn để tiết kiệm token
                if len(messages[i]["content"]) > 100:
                    messages[i]["content"] = messages[i]["content"][:100] + "..."
        
        # Sử dụng định dạng ngắn gọn cho lịch sử hội thoại
        formatted_history = ""
        for message in messages:
            role_prefix = "U" if message["role"] == "user" else "A"
            formatted_history += f"{role_prefix}: {message['content']}\n"
        
        return formatted_history 