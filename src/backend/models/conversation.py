import os
import json
from typing import List, Dict, Optional
from datetime import datetime

class Conversation:
    """Lớp xử lý lưu trữ và quản lý hội thoại.
    
    Lớp này cung cấp các phương thức để tạo, truy xuất, cập nhật và xóa hội thoại,
    cũng như quản lý tin nhắn trong các hội thoại đó. Các hội thoại được lưu trữ
    dưới dạng file JSON trong thư mục được chỉ định.
    """
    
    def __init__(self):
        """Khởi tạo trình quản lý hội thoại với thư mục lưu trữ.
        
        Thư mục lưu trữ sẽ được tạo nếu nó chưa tồn tại.
        """
        self.storage_dir = "storage/conversations"
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def create_conversation(self, user_id: str) -> str:
        """Tạo một hội thoại mới cho người dùng được chỉ định.
        
        Agrs:
            user_id (str): Định danh duy nhất của người dùng.
            
        Returns:
            str: Mã hội thoại duy nhất có định dạng 'userid_YYYYMMDDHHMMSS'.
        """
        conversation_id = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        conversation_data = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "title": "Cuộc trò chuyện mới",  # Thêm tiêu đề mặc định
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self._save_conversation(conversation_id, conversation_data)
        return conversation_id
    
    def add_message(self, conversation_id: str, role: str, content: str) -> bool:
        """Thêm một tin nhắn vào hội thoại được chỉ định.
        
        Agrs:
            conversation_id (str): ID của hội thoại cần thêm tin nhắn.
            role (str): Vai trò của người gửi (ví dụ: 'user', 'assistant').
            content (str): Nội dung tin nhắn.
            
        Returns:
            bool: True nếu thêm tin nhắn thành công, False nếu không.
            
        Ghi chú:
            Tự động tạo tiêu đề từ tin nhắn đầu tiên của người dùng nếu hội thoại
            vẫn đang sử dụng tiêu đề mặc định.
        """
        conversation = self._load_conversation(conversation_id)
        if not conversation:
            return False
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        conversation["messages"].append(message)
        conversation["updated_at"] = datetime.now().isoformat()
        
        if conversation.get("title") == "Cuộc trò chuyện mới" and role == "user" and len(conversation["messages"]) <= 2:
            conversation["title"] = content[:30] + ("..." if len(content) > 30 else "")
        
        self._save_conversation(conversation_id, conversation)
        return True
    
    def rename_conversation(self, conversation_id: str, title: str) -> bool:
        """Đổi tên một hội thoại hiện có.
        
        Agrs:
            conversation_id (str): ID của hội thoại cần đổi tên.
            title (str): Tiêu đề mới cho hội thoại.
            
        Returns:
            bool: True nếu đổi tên thành công, False nếu không.
        """
        conversation = self._load_conversation(conversation_id)
        if not conversation:
            return False
        
        conversation["title"] = title
        conversation["updated_at"] = datetime.now().isoformat()
        
        self._save_conversation(conversation_id, conversation)
        return True
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Lấy thông tin hội thoại theo ID.
        
        Agrs:
            conversation_id (str): ID của hội thoại cần lấy.
            
        Returns:
            Optional[Dict]: Dữ liệu hội thoại nếu tìm thấy, None nếu không.
        """
        return self._load_conversation(conversation_id)
    
    def get_conversation_history(self, conversation_id: str, limit: int = 10) -> List[Dict]:
        """Lấy lịch sử tin nhắn của một hội thoại.
        
        Agrs:
            conversation_id (str): ID của hội thoại.
            limit (int, optional): Số lượng tin nhắn gần nhất cần lấy. Nếu là 0 hoặc âm,
                                 Returns tất cả tin nhắn. Mặc định là 10.
                   
        Returns:
            List[Dict]: Danh sách các từ điển tin nhắn, tin nhắn mới nhất ở cuối.
                      Returns danh sách rỗng nếu không tìm thấy hội thoại.
        """
        conversation = self._load_conversation(conversation_id)
        if not conversation:
            return []
        
        messages = conversation["messages"]
        if limit > 0:
            messages = messages[-limit:]
            
        return messages
    
    def list_conversations(self, user_id: str) -> List[Dict]:
        """Liệt kê tất cả hội thoại của một người dùng cụ thể.
        
        Agrs:
            user_id (str): ID của người dùng cần liệt kê hội thoại.
            
        Returns:
            List[Dict]: Danh sách các từ điển hội thoại, mỗi từ điển chứa siêu dữ liệu
                      hội thoại và bản xem trước của tin nhắn cuối cùng. Được sắp xếp theo
                      thời gian cập nhật giảm dần (mới nhất lên đầu).
        """
        conversations = []
        
        if not os.path.exists(self.storage_dir):
            return conversations
            
        for filename in os.listdir(self.storage_dir):
            if filename.startswith(f"{user_id}_") and filename.endswith(".json"):
                file_path = os.path.join(self.storage_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    conversation = json.load(f)
                    if conversation["messages"]:
                        last_message = conversation["messages"][-1]["content"]
                        conversation["preview"] = last_message[:50] + "..." if len(last_message) > 50 else last_message
                    else:
                        conversation["preview"] = "Empty conversation"
                    conversations.append(conversation)
        
        conversations.sort(key=lambda x: x["updated_at"], reverse=True)
        return conversations
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Xóa một hội thoại theo ID.
        
        Agrs:
            conversation_id (str): ID của hội thoại cần xóa.
            
        Returns:
            bool: True nếu xóa thành công, False nếu hội thoại không tồn tại.
        """
        file_path = os.path.join(self.storage_dir, f"{conversation_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    
    def _save_conversation(self, conversation_id: str, data: Dict) -> None:
        """Lưu dữ liệu hội thoại vào file JSON.
        
        Agrs:
            conversation_id (str): ID của hội thoại cần lưu.
            data (Dict): Dữ liệu hội thoại cần lưu.
            
        Ghi chú:
            Đây là phương thức nội bộ và không nên được gọi trực tiếp.
        """
        file_path = os.path.join(self.storage_dir, f"{conversation_id}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Tải dữ liệu hội thoại từ file JSON.
        
        Agrs:
            conversation_id (str): ID của hội thoại cần tải.
            
        Returns:
            Optional[Dict]: Dữ liệu hội thoại đã tải nếu file tồn tại, None nếu không.
            
        Ghi chú:
            Đây là phương thức nội bộ và không nên được gọi trực tiếp.
        """
        file_path = os.path.join(self.storage_dir, f"{conversation_id}.json")
        if not os.path.exists(file_path):
            return None
            
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)