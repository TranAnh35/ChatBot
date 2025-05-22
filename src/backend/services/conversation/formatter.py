"""Service định dạng lịch sử hội thoại cho LLM context."""

from typing import List, Dict

class ConversationFormatter:
    """Định dạng lịch sử hội thoại cho LLM context."""
    @staticmethod
    def format(messages: List[Dict], max_messages: int = 5) -> str:
        """Định dạng lịch sử hội thoại thành chuỗi context.

        Args:
            messages (List[Dict]): Danh sách tin nhắn.
            max_messages (int): Số lượng tin nhắn tối đa.
        Returns:
            str: Chuỗi context đã định dạng.
        """
        if not messages:
            return ""
        if len(messages) > 3:
            for i in range(len(messages) - 3):
                if len(messages[i]["content"]) > 100:
                    messages[i]["content"] = messages[i]["content"][:100] + "..."
        formatted_history = ""
        for message in messages:
            role_prefix = "U" if message["role"] == "user" else "A"
            formatted_history += f"{role_prefix}: {message['content']}\n"
        return formatted_history 