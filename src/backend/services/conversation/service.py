from models.conversation import Conversation
from typing import List, Dict, Optional, Any
from services.conversation.formatter import ConversationFormatter


class ConversationService:
    """Dịch vụ quản lý hội thoại.
    
    Lớp này cung cấp các phương thức để tương tác với dữ liệu hội thoại,
    đóng vai trò trung gian giữa các route và model xử lý dữ liệu.
    """
    
    def __init__(self) -> None:
        """Khởi tạo dịch vụ hội thoại với một đối tượng Conversation."""
        self.conversation_model = Conversation()
    
    def create_conversation(self, user_id: str) -> str:
        """Tạo một hội thoại mới cho người dùng.
        
        Agrs:
            user_id (str): Định danh duy nhất của người dùng.
            
        Returns:
            str: ID của hội thoại vừa được tạo.
        """
        return self.conversation_model.create_conversation(user_id)
    
    def add_message(self, conversation_id: str, role: str, content: str) -> bool:
        """Thêm một tin nhắn vào hội thoại.
        
        Agrs:
            conversation_id (str): ID của hội thoại.
            role (str): Vai trò người gửi (user/assistant).
            content (str): Nội dung tin nhắn.
            
        Returns:
            bool: True nếu thêm thành công, False nếu không tìm thấy hội thoại.
        """
        return self.conversation_model.add_message(conversation_id, role, content)
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin chi tiết của một hội thoại.
        
        Agrs:
            conversation_id (str): ID của hội thoại cần lấy.
            
        Returns:
            Optional[Dict]: Thông tin hội thoại nếu tìm thấy, None nếu không.
        """
        return self.conversation_model.get_conversation(conversation_id)
    
    def get_conversation_history(self, conversation_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Lấy lịch sử tin nhắn của một hội thoại.
        
        Agrs:
            conversation_id (str): ID của hội thoại.
            limit (int, optional): Giới hạn số lượng tin nhắn. Mặc định là 10.
            
        Returns:
            List[Dict]: Danh sách các tin nhắn trong hội thoại.
        """
        return self.conversation_model.get_conversation_history(conversation_id, limit)
    
    def list_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """Liệt kê tất cả hội thoại của một người dùng.
        
        Agrs:
            user_id (str): ID của người dùng.
            
        Returns:
            List[Dict]: Danh sách các hội thoại của người dùng.
        """
        return self.conversation_model.list_conversations(user_id)
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Xóa một hội thoại.
        
        Agrs:
            conversation_id (str): ID của hội thoại cần xóa.
            
        Returns:
            bool: True nếu xóa thành công, False nếu không tìm thấy.
        """
        return self.conversation_model.delete_conversation(conversation_id)
    
    def rename_conversation(self, conversation_id: str, title: str) -> bool:
        """Đổi tên một hội thoại.
        
        Agrs:
            conversation_id (str): ID của hội thoại cần đổi tên.
            title (str): Tiêu đề mới cho hội thoại.
            
        Returns:
            bool: True nếu đổi tên thành công, False nếu không tìm thấy hội thoại.
        """
        return self.conversation_model.rename_conversation(conversation_id, title)
    
    def format_conversation_for_context(self, conversation_id: str, max_messages: int = 5) -> str:
        """Định dạng lịch sử hội thoại để sử dụng làm ngữ cảnh cho mô hình ngôn ngữ.
        
        Tối ưu hóa lịch sử hội thoại bằng cách giảm kích thước để phù hợp với giới hạn token.
        
        Agrs:
            conversation_id (str): ID của hội thoại cần định dạng.
            max_messages (int, optional): Số lượng tin nhắn tối đa cần lấy. Mặc định là 5.
            
        Returns:
            str: Chuỗi đã được định dạng đại diện cho lịch sử hội thoại.
        """
        messages = self.get_conversation_history(conversation_id, max_messages)
        return ConversationFormatter.format(messages, max_messages)