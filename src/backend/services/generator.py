from models.llm import LLM
from typing import List, Dict
from services.conversation_service import ConversationService
import faiss

class GeneratorService:
    def __init__(self):
        self.llm = LLM()
        self.conversation_service = ConversationService()
        # Các câu trả lời nhanh giúp giảm token
        self.quick_responses = {
            "hello": "Xin chào! Tôi có thể giúp gì cho bạn?",
            "hi": "Chào bạn! Tôi có thể hỗ trợ gì cho bạn hôm nay?",
            "xin chào": "Chào bạn! Tôi là ChatBox, tôi có thể giúp gì cho bạn?",
            "chào": "Xin chào! Tôi có thể giúp gì cho bạn hôm nay?",
            "cảm ơn": "Không có gì, rất vui được giúp bạn!",
            "thank you": "Không có gì! Rất vui được giúp bạn.",
            "thanks": "Không có gì, rất vui được giúp bạn!"
        }

    async def generate_content(self, prompt: str, conversation_id: str = None, rag_response: str = None, 
                              web_response: str = None, file_response: str = None) -> str:
        """Generate content with conversation history if available"""
        # Kiểm tra nhanh cho prompt đơn giản, tiết kiệm token
        prompt_lower = prompt.lower().strip()
        if prompt_lower in self.quick_responses and not rag_response and not web_response and not file_response:
            # Nếu có câu trả lời nhanh và không cần thông tin bổ sung, trả về ngay
            response = self.quick_responses[prompt_lower]
            # Vẫn lưu tương tác vào lịch sử nếu có conversation_id
            if conversation_id:
                self.conversation_service.add_message(conversation_id, "user", prompt)
                self.conversation_service.add_message(conversation_id, "assistant", response)
            return response
        
        # Xử lý các prompt cần lịch sử hội thoại
        conversation_history = None
        if conversation_id:
            conversation_history = self.conversation_service.format_conversation_for_context(conversation_id)
        
        # Chỉ thu thập thông tin cần thiết từ các nguồn, không đưa vào nếu rỗng
        has_contextual_info = any(x is not None and len(str(x).strip()) > 0 
                              for x in [rag_response, web_response, file_response])
        
        # Generate content với các thông tin được lọc
        response = await self.llm.generateContent(
            prompt, 
            rag_response if has_contextual_info else None,
            web_response if has_contextual_info else None, 
            file_response if has_contextual_info else None, 
            conversation_history
        )
        
        # Lưu tương tác vào lịch sử nếu có conversation_id
        if conversation_id:
            self.conversation_service.add_message(conversation_id, "user", prompt)
            self.conversation_service.add_message(conversation_id, "assistant", response)
        
        return response
    
    async def merge_context(self, web_results: List[List[Dict]]):
        return await self.llm.merge_context(web_results)

    def create_vector_index(self):
        # During index creation, use HNSW instead of FlatL2
        vector_size = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexHNSWFlat(vector_size, 32)  # 32 is M parameter for HNSW