Để khởi động được chương trình, cần thực hiện các bước sau:

1. Cài đặt các thư viện cần thiết:
```
pip install -r requirements.txt
```

2. Chạy chương trình backend:
Tạo file `.env` trong thư mục `src/backend/` và thêm API cho Gemini.
```
GEMINI_API_KEY=your_gemini_api_key
```

Chạy chương trình:
```
cd src/backend/ && uvicorn main:app
```

3. Chạy chương trình frontend:

    **Chú ý:** 
      - Cần có node và npm để chạy được chương trình frontend.


  - Chạy lệnh `cd src/frontend/` để chuyển đến thư mục frontend.
  - Chạy lệnh `npm install` để cài đặt các thư viện cần thiết.
  - Chạy lệnh `npm run dev` để chạy chương trình frontend.

4. Chạy chương trình:

- Mở trình duyệt và truy cập vào địa chỉ `http://localhost:5173/` để sử dụng chương trình.