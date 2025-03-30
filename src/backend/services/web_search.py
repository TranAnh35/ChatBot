import requests
from typing import List, Dict
import os
import dotenv
from models.llm import LLM

dotenv.load_dotenv()

class WebSearch:
    """Lớp xử lý tìm kiếm trên Google."""

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_SEARCH_API_KEY")  # API Key của Google
        self.cx = os.getenv("GOOGLE_SEARCH_ID")  # Custom Search Engine ID
    
    async def search(self, query: str, num_results: int = 4, filter_by: str = None) -> List[Dict]:
        """Thực hiện tìm kiếm trên Google và lấy num_results đầu tiên mà không giới hạn trang web cụ thể."""
        
        url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={self.api_key}&cx={self.cx}&num={num_results}"
        
        # Thêm bộ lọc theo thời gian (nếu có)
        if filter_by in ["d1", "w1", "m1", "y1"]:
            url += f"&dateRestrict={filter_by}"
        
        response = requests.get(url)
        
        if response.status_code == 200:
            items = response.json().get("items", [])[:num_results]  # Lấy num_results đầu tiên
            return [{"title": item["title"], "link": item["link"], "snippet": item["snippet"]} for item in items]
        
        return []

    async def perform_search(self, prompt: str) -> List[Dict]:
        """Thực hiện tìm kiếm dựa trên mức độ chiều sâu của prompt."""
        depth = await LLM().inDepth_context_analysis(prompt)
        results = []

        if depth == "little":
            results.append(await self.search(prompt, num_results=1))
        elif depth == "medium":
            results.append(await self.search(prompt, num_results=2, filter_by="y1"))
            results.append(await self.search(prompt, num_results=2))
        elif depth == "high":
            results.append(await self.search(prompt, num_results=4, filter_by="y1"))
            results.append(await self.search(prompt, num_results=4))
        return results
