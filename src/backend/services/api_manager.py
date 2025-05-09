import os
from dotenv import load_dotenv, set_key
import requests
load_dotenv()

class ApiManager:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")

    def get_api_key(self):
        return self.api_key

    def set_api_key(self, api_key):
        self.api_key = api_key
        os.environ["GEMINI_API_KEY"] = api_key
        set_key(".env", "GEMINI_API_KEY", api_key)
        
    def is_api_key_valid(self, api_key: str) -> bool: 
        """
        Kiểm tra xem API key của Gemini có hợp lệ không bằng cách gửi một yêu cầu thử nghiệm.
        """
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key=" + api_key
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": "Hello"}]}],  # Prompt thử nghiệm
        }
        params = {"key": api_key}

        try:
            response = requests.post(url, json=payload, headers=headers, params=params)
            data = response.json()
            # Nếu API key hợp lệ, phản hồi có 'candidates' hoặc không báo lỗi
            return "candidates" in data
        except Exception as e:
            print(f"Error validating API key: {e}")
            return False