import requests
from typing import List, Dict, Union, Optional
import os
from dotenv import load_dotenv
from models.llm import LLM
import urllib.parse
import time
import json
from bs4 import BeautifulSoup
import re

load_dotenv()

class WebSearch:
    """Lớp xử lý tìm kiếm trên Google với khả năng tối ưu hóa truy vấn."""

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_SEARCH_API_KEY")  # API Key của Google
        self.cx = os.getenv("GOOGLE_SEARCH_ID")  # Custom Search Engine ID
    
    async def search(self, query: str, num_results: int = 4, filter_by: str = None, site_restrict: str = None) -> List[Dict]:
        """Thực hiện tìm kiếm trên Google với các tùy chọn lọc."""
        
        # Kiểm tra API key và Search Engine ID
        if not self.api_key or not self.cx:
            print("Lỗi: Thiếu GOOGLE_SEARCH_API_KEY hoặc GOOGLE_SEARCH_ID trong file .env")
            return []
        
        # Mã hóa truy vấn tìm kiếm
        encoded_query = urllib.parse.quote(query)
        
        # Xây dựng URL cơ bản
        url = f"https://www.googleapis.com/customsearch/v1?q={encoded_query}&key={self.api_key}&cx={self.cx}&num={num_results}"
        
        # Thêm bộ lọc theo thời gian (nếu có)
        if filter_by in ["d1", "w1", "m1", "y1"]:
            url += f"&dateRestrict={filter_by}"
        
        # Hạn chế tìm kiếm trong một trang web cụ thể (nếu có)
        if site_restrict:
            url += f"&siteSearch={urllib.parse.quote(site_restrict)}"
        
        # Thêm thông số để yêu cầu kết quả an toàn
        url += "&safe=active"
        
        # Thử tìm kiếm với thử lại trong trường hợp lỗi mạng tạm thời
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Kiểm tra xem có kết quả nào không
                    if "items" not in data:
                        print(f"Không tìm thấy kết quả cho '{query}'")
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
                elif response.status_code == 429:
                    # Nếu gặp giới hạn tỷ lệ, đợi và thử lại
                    print("Đã đạt giới hạn tỷ lệ tìm kiếm. Đợi trước khi thử lại...")
                    time.sleep(2)
                    retry_count += 1
                elif response.status_code == 403:
                    # Vấn đề với API key
                    print("Lỗi xác thực: API key không hợp lệ hoặc không được phép truy cập")
                    return []
                else:
                    print(f"Lỗi khi tìm kiếm: {response.status_code}")
                    try:
                        error_data = response.json()
                        print(f"Chi tiết lỗi: {json.dumps(error_data, indent=2)}")
                    except:
                        print(f"Nội dung phản hồi lỗi: {response.text[:200]}")
                    return []
            
            except requests.RequestException as e:
                print(f"Lỗi kết nối: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    print(f"Thử lại lần {retry_count}/{max_retries}...")
                    time.sleep(1)
        
        print("Đã hết số lần thử lại. Không thể hoàn thành tìm kiếm.")
        return []
        
    async def extract_search_keywords(self, prompt: str) -> Dict[str, Union[str, List[str]]]:
        """Trích xuất từ khóa và ngữ cảnh tìm kiếm từ prompt người dùng."""
        
        llm = LLM()
        analysis_prompt = f"""
        Hãy phân tích câu hỏi sau và trích xuất các từ khóa tìm kiếm hiệu quả:
        
        Câu hỏi: "{prompt}"
        
        Hãy trả về kết quả BẮT BUỘC theo định dạng JSON. Không được trả về kết quả khác:
        {{
            "main_query": "câu truy vấn chính, ngắn gọn, chứa từ khóa quan trọng nhất",
            "alternative_queries": ["truy vấn thay thế 1", "truy vấn thay thế 2"],
            "time_relevance": "none|recent|very_recent",
            "domain_specific": "tên miền cụ thể nếu câu hỏi liên quan đến một trang web nhất định, hoặc null",
            "query_type": "factual|technical|opinion|news|comparison"
        }}
        """
        
        from services.text_processing import TextProcessing
        text_processing = TextProcessing()
        
        try:
            response_text = await llm.generateContent(analysis_prompt)
            json_results = text_processing.split_JSON_text(response_text)
            if json_results and len(json_results) > 0:
                return json_results[0]
            else:
                return {
                    "main_query": prompt,
                    "alternative_queries": [],
                    "time_relevance": "none",
                    "domain_specific": None,
                    "query_type": "factual"
                }
        except Exception as e:
            print(f"Lỗi khi trích xuất từ khóa: {e}")
            return {
                "main_query": prompt,
                "alternative_queries": [],
                "time_relevance": "none",
                "domain_specific": None,
                "query_type": "factual"
            }
    
    async def perform_search(self, prompt: str) -> List[Dict]:
        """Thực hiện tìm kiếm thông minh dựa trên phân tích prompt."""
        
        search_info = await self.extract_search_keywords(prompt)
        
        results = []
        main_query = search_info.get("main_query", prompt)
        alternative_queries = search_info.get("alternative_queries", [])
        query_type = search_info.get("query_type", "factual")
        time_relevance = search_info.get("time_relevance", "none")
        domain_specific = search_info.get("domain_specific")
        
        time_filter = None
        if time_relevance == "recent":
            time_filter = "m1"  # Tìm kiếm trong 1 tháng gần đây
        elif time_relevance == "very_recent":
            time_filter = "d1"  # Tìm kiếm trong 1 ngày gần đây
        
        # Chiến lược tìm kiếm dựa trên loại truy vấn
        if query_type in ["news", "recent"]:
            # Tin tức ưu tiên nội dung gần đây
            results.append(await self.search(main_query, num_results=1, filter_by=time_filter or "w1"))
        elif query_type == "technical":
            # Truy vấn kỹ thuật ưu tiên độ chính xác và mức độ chuyên sâu
            results.append(await self.search(main_query, num_results=2))
            if domain_specific:
                results.append(await self.search(main_query, num_results=2, site_restrict=domain_specific))
        elif query_type == "comparison":
            # Truy vấn so sánh cần nhiều góc nhìn
            results.append(await self.search(main_query, num_results=2))
            # Thêm kết quả từ các truy vấn thay thế
            for alt_query in alternative_queries[:2]:
                results.append(await self.search(alt_query, num_results=1))
        else:
            # Truy vấn thông thường
            results.append(await self.search(main_query, num_results=1, filter_by=time_filter))
            # Thêm một kết quả từ truy vấn thay thế nếu có
            if alternative_queries:
                results.append(await self.search(alternative_queries[0], num_results=1))

        # Làm phẳng danh sách kết quả
        flat_results = []
        for result_group in results:
            flat_results.extend(result_group)

        return [flat_results]
        
    async def get_page_content(self, url: str) -> Dict[str, str]:
        """Lấy nội dung từ một trang web dựa trên URL được cung cấp."""
        try:
            print(f"Đang lấy nội dung từ URL: {url}")
            
            # Xác thực URL
            if not url.startswith(('http://', 'https://')):
                return {"error": "URL không hợp lệ. URL phải bắt đầu bằng http:// hoặc https://"}
            
            # Thử truy cập trang web với cơ chế thử lại
            max_retries = 3
            retry_count = 0
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0'
            }
            
            while retry_count < max_retries:
                try:
                    response = requests.get(url, headers=headers, timeout=15)
                    print(f"Mã trạng thái phản hồi: {response.status_code}")
                    
                    if response.status_code == 200:
                        # Phát hiện mã hóa
                        encoding = response.encoding
                        if encoding is None or encoding.lower() == 'iso-8859-1':
                            # Thử tìm mã hóa từ nội dung
                            encodings = ['utf-8', 'windows-1252', 'cp1252']
                            content = None
                            
                            for enc in encodings:
                                try:
                                    content = response.content.decode(enc)
                                    break
                                except UnicodeDecodeError:
                                    continue
                                    
                            if content is None:
                                content = response.text  # Sử dụng mã hóa mặc định nếu không tìm thấy mã hóa phù hợp
                        else:
                            content = response.text
                        
                        # Phân tích HTML
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Lấy tiêu đề
                        title = soup.title.string if soup.title else "Không có tiêu đề"
                        
                        # Loại bỏ các phần tử không cần thiết
                        for element in soup(['script', 'style', 'header', 'footer', 'nav', 'iframe', 'noscript']):
                            element.decompose()
                            
                        # Lấy nội dung văn bản từ phần thân trang
                        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|article|body|main', re.I))
                        
                        if main_content:
                            text_content = main_content.get_text(separator="\n", strip=True)
                        else:
                            # Nếu không tìm thấy phần tử chính, lấy tất cả văn bản từ thẻ body
                            text_content = soup.body.get_text(separator="\n", strip=True) if soup.body else soup.get_text(separator="\n", strip=True)
                        
                        # Loại bỏ khoảng trắng và dòng trống thừa
                        text_content = re.sub(r'\n\s*\n', '\n\n', text_content)
                        
                        return {
                            "title": title,
                            "content": text_content,
                            "url": url
                        }
                    
                    elif response.status_code in [429, 503, 504]:
                        # Có thể là giới hạn tỷ lệ hoặc quá tải máy chủ, thử lại
                        print(f"Lỗi máy chủ tạm thời ({response.status_code}). Đợi trước khi thử lại...")
                        time.sleep(2)
                        retry_count += 1
                    
                    else:
                        # Lỗi HTTP khác
                        return {"error": f"Không thể truy cập trang. Mã trạng thái: {response.status_code}"}
                
                except requests.exceptions.SSLError as ssl_err:
                    # Xử lý lỗi SSL bằng cách thử lại mà không xác minh chứng chỉ
                    print(f"Lỗi SSL: {ssl_err}. Thử lại không xác minh SSL...")
                    try:
                        response = requests.get(url, headers=headers, timeout=15, verify=False)
                        # Xử lý phản hồi giống như trường hợp thành công ở trên
                        if response.status_code == 200:
                            content = response.text
                            soup = BeautifulSoup(content, 'html.parser')
                            title = soup.title.string if soup.title else "Không có tiêu đề"
                            
                            for element in soup(['script', 'style', 'header', 'footer', 'nav', 'iframe', 'noscript']):
                                element.decompose()
                                
                            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|article|body|main', re.I))
                            
                            if main_content:
                                text_content = main_content.get_text(separator="\n", strip=True)
                            else:
                                text_content = soup.body.get_text(separator="\n", strip=True) if soup.body else soup.get_text(separator="\n", strip=True)
                            
                            text_content = re.sub(r'\n\s*\n', '\n\n', text_content)
                            
                            return {
                                "title": title,
                                "content": text_content,
                                "url": url,
                                "warning": "Kết nối không an toàn: Chứng chỉ SSL không được xác minh"
                            }
                        else:
                            return {"error": f"Không thể truy cập trang. Mã trạng thái: {response.status_code}"}
                    except requests.RequestException as e:
                        print(f"Lỗi kết nối ngay cả khi bỏ qua xác minh SSL: {e}")
                        retry_count += 1
                
                except requests.RequestException as e:
                    print(f"Lỗi kết nối: {e}")
                    retry_count += 1
                    if retry_count < max_retries:
                        print(f"Thử lại lần {retry_count}/{max_retries}...")
                        time.sleep(1)
                    else:
                        return {"error": f"Lỗi kết nối đến trang web: {str(e)}"}
            
            return {"error": "Đã hết số lần thử lại. Không thể truy cập trang web."}
        
        except Exception as e:
            print(f"Lỗi khi lấy nội dung trang: {e}")
            return {"error": f"Lỗi khi xử lý nội dung trang: {str(e)}"}
