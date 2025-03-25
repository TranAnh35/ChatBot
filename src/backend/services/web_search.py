import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import json
from fastapi import HTTPException
import aiohttp

class WebSearch:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    async def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """
        Thực hiện tìm kiếm web với query đã cho
        
        Args:
            query (str): Từ khóa tìm kiếm
            num_results (int): Số kết quả muốn lấy
            
        Returns:
            List[Dict]: Danh sách các kết quả tìm kiếm
        """
        try:
            # Sử dụng DuckDuckGo API
            url = f"https://api.duckduckgo.com/?q={query}&format=json"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status != 200:
                        raise HTTPException(status_code=response.status, detail="Lỗi khi tìm kiếm")
                    data = await response.json()
            
            results = []
            for result in data.get('Results', [])[:num_results]:
                results.append({
                    'title': result.get('Text', ''),
                    'url': result.get('FirstURL', ''),
                    'description': result.get('Text', '')
                })
            
            return results
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi khi tìm kiếm: {str(e)}")

    async def get_page_content(self, url: str) -> str:
        """
        Lấy nội dung của một trang web
        
        Args:
            url (str): URL của trang web
            
        Returns:
            str: Nội dung đã được xử lý của trang web
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status != 200:
                        raise HTTPException(status_code=response.status, detail="Lỗi khi lấy nội dung trang")
                    html = await response.text()
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Loại bỏ các thẻ script và style
            for script in soup(["script", "style"]):
                script.decompose()
                
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi khi lấy nội dung trang: {str(e)}")