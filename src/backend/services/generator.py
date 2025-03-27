from models.llm import LLM

class GeneratorService:
    def __init__(self):
        self.llm = LLM()

    async def generate_content(self, prompt, rag_response: str = None, web_response: str = None, file_response: str = None) -> str:
        return await self.llm.generateContent(prompt, rag_response, web_response, file_response)
    
    async def inDepth_context(self, prompt):
        return await self.llm.inDepth_context_analysis(prompt)