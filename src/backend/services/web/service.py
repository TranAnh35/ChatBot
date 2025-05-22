"""Service điều phối tìm kiếm web thông minh."""

from typing import List, Dict
from clients.google_search_client import GoogleSearchClient
from services.web.query_analyzer import SearchQueryAnalyzer
from services.web.content_extractor import WebContentExtractor

class WebSearchService:
    """Điều phối tìm kiếm web: phân tích truy vấn, gọi API, trích xuất nội dung."""
    def __init__(self):
        self.client = GoogleSearchClient()
        self.analyzer = SearchQueryAnalyzer()
        self.extractor = WebContentExtractor()

    async def perform_search(self, prompt: str) -> List[Dict]:
        """Thực hiện tìm kiếm thông minh dựa trên phân tích prompt.

        Args:
            prompt (str): Câu hỏi hoặc yêu cầu tìm kiếm từ người dùng.
        Returns:
            List[Dict]: Danh sách các kết quả tìm kiếm đã được làm phẳng.
        """
        search_info = await self.analyzer.analyze(prompt)
        results = []
        main_query = search_info.get("main_query", prompt)
        alternative_queries = search_info.get("alternative_queries", [])
        query_type = search_info.get("query_type", "factual")
        time_relevance = search_info.get("time_relevance", "none")
        domain_specific = search_info.get("domain_specific")
        time_filter = None
        if time_relevance == "recent":
            time_filter = "m1"
        elif time_relevance == "very_recent":
            time_filter = "d1"
        if query_type in ["news", "recent"]:
            results.append(self.client.search(main_query, num_results=1, filter_by=time_filter or "w1"))
        elif query_type == "technical":
            results.append(self.client.search(main_query, num_results=2))
            if domain_specific:
                results.append(self.client.search(main_query, num_results=2, site_restrict=domain_specific))
        elif query_type == "comparison":
            results.append(self.client.search(main_query, num_results=2))
            for alt_query in alternative_queries[:2]:
                results.append(self.client.search(alt_query, num_results=1))
        else:
            results.append(self.client.search(main_query, num_results=1, filter_by=time_filter))
            if alternative_queries:
                results.append(self.client.search(alternative_queries[0], num_results=1))
        flat_results = []
        for result_group in results:
            flat_results.extend(result_group)
        return [flat_results]

    def get_page_content(self, url: str) -> Dict[str, str]:
        """Lấy nội dung chính của một trang web.

        Args:
            url (str): Đường dẫn URL của trang web cần lấy nội dung.
        Returns:
            Dict[str, str]: title, content, url, warning nếu có.
        """
        return self.extractor.extract(url) 