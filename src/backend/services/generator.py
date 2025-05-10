from models.llm import LLM
from typing import List, Dict
from services.conversation_service import ConversationService

class GeneratorService:
    def __init__(self):
        self.llm = LLM()
        self.conversation_service = ConversationService()

    async def generate_content(self, prompt, conversation_id: str = None, rag_response: str = None, 
                              web_response: str = None, file_response: str = None) -> str:
        """Generate content with conversation history if available"""
        conversation_history = None
        
        # If conversation_id is provided, get conversation history
        if conversation_id:
            conversation_history = self.conversation_service.format_conversation_for_context(conversation_id)
            
        # Generate content with all available context
        response = await self.llm.generateContent(
            prompt, 
            rag_response, 
            web_response, 
            file_response, 
            conversation_history
        )
        
        # If conversation_id is provided, save the interaction
        if conversation_id:
            # Save user message
            self.conversation_service.add_message(conversation_id, "user", prompt)
            # Save assistant response
            self.conversation_service.add_message(conversation_id, "assistant", response)
        
        return response
    
    async def merge_context(self, web_results: List[List[Dict]]):
        return await self.llm.merge_context(web_results)