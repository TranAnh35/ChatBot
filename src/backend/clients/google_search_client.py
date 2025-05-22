"""Client cho Google Search API."""

import os
import requests
import urllib.parse
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class GoogleSearchClient:
    """Client cho Google Custom Search API."""
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        self.cx = os.getenv("GOOGLE_SEARCH_ID")

    def search(self, query: str, num_results: int = 4, filter_by: Optional[str] = None, site_restrict: Optional[str] = None) -> List[Dict]:
        """Gọi Google Search API.

        Args:
            query (str): Truy vấn tìm kiếm.
            num_results (int): Số kết quả trả về.
            filter_by (Optional[str]): Bộ lọc thời gian.
            site_restrict (Optional[str]): Giới hạn domain.
        Returns:
            List[Dict]: Danh sách kết quả (title, link, snippet).
        """
        if not self.api_key or not self.cx:
            print("Lỗi: Thiếu GOOGLE_SEARCH_API_KEY hoặc GOOGLE_SEARCH_ID trong file .env")
            return []
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.googleapis.com/customsearch/v1?q={encoded_query}&key={self.api_key}&cx={self.cx}&num={num_results}"
        if filter_by in ["d1", "w1", "m1", "y1"]:
            url += f"&dateRestrict={filter_by}"
        if site_restrict:
            url += f"&siteSearch={urllib.parse.quote(site_restrict)}"
        url += "&safe=active"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "items" not in data:
                    return []
                items = data.get("items", [])
                results = []
                for item in items:
                    result = {
                        "title": item.get("title", "Không có tiêu đề"),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", "Không có mô tả")
                    }
                    results.append(result)
                return results
            else:
                print(f"Lỗi khi tìm kiếm: {response.status_code}")
                return []
        except requests.RequestException as e:
            print(f"Lỗi kết nối: {e}")
            return [] 