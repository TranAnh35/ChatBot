from models.conversation import Conversation
from typing import List, Dict, Optional, Any
from services.conversation.formatter import ConversationFormatter


class ConversationService:
    
    def __init__(self) -> None:
        """Khởi tạo dịch vụ hội thoại với một đối tượng Conversation."""
        self.conversation_model = Conversation()
    
    def create_conversation(self, user_id: str) -> str:
        """Tạo một hội thoại mới cho người dùng."""
        return self.conversation_model.create_conversation(user_id)
    
    def add_message(self, conversation_id: str, role: str, content: str) -> bool:
        """Thêm một tin nhắn vào hội thoại."""
        return self.conversation_model.add_message(conversation_id, role, content)
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin chi tiết của một hội thoại."""
        return self.conversation_model.get_conversation(conversation_id)
    
    def get_conversation_history(self, conversation_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Lấy lịch sử tin nhắn của một hội thoại."""
        return self.conversation_model.get_conversation_history(conversation_id, limit)
    
    def list_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """Liệt kê tất cả hội thoại của một người dùng."""
        return self.conversation_model.list_conversations(user_id)
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Xóa một hội thoại."""
        return self.conversation_model.delete_conversation(conversation_id)
    
    def rename_conversation(self, conversation_id: str, title: str) -> bool:
        """Đổi tên một hội thoại."""
        return self.conversation_model.rename_conversation(conversation_id, title)
    
    def format_conversation_for_context(self, conversation_id: str, max_messages: int = 5) -> str:
        """Định dạng lịch sử hội thoại để sử dụng làm ngữ cảnh cho mô hình ngôn ngữ.
        
        Tối ưu hóa lịch sử hội thoại bằng cách giảm kích thước để phù hợp với giới hạn token."""

        messages = self.get_conversation_history(conversation_id, max_messages)
        return ConversationFormatter.format(messages, max_messages)