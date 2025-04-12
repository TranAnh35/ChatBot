# Giới thiệu
Chương trình này bao gồm một backend (dùng FastAPI) và một frontend (dùng Node.js). Bạn có thể chạy chương trình theo hai cách: cục bộ (local) hoặc sử dụng Docker. Hãy làm theo các bước dưới đây để thiết lập và khởi động.

# Yêu cầu
- Cục bộ:
  - Python 3.10+
  - Node.js 18+ và npm
- Docker:
  - Docker và Docker Compose
- API key cho Gemini (được cấu hình trong file .env)

# Cách 1: Chạy cục bộ (Local)
1. Cài đặt backend
   
   1.1. Cài đặt các thư viện Python:

   ```
   pip install -r requirements.txt
   ```
 
   1.2. Cấu hình API key:
   - Tạo file .env trong thư mục src/backend/ với nội dung:

   ```
   GEMINI_API_KEY=your_gemini_api_key
   ```
   - Thay your_gemini_api_key bằng API key thực tế của Gemini.

   1.3. Chạy backend:

   ```
   cd src/backend/
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

   - Backend sẽ chạy tại http://localhost:8000.

2. Cài đặt frontend

   2.1. Chuyển đến thư mục frontend:

   ```
   cd src/frontend/
   ```

   2.2. Cài đặt các thư viện Node.js:

   ```
   npm install
   ```

   2.3. Chạy frontend:

   ```
   npm run dev
   ```

   - Frontend sẽ chạy tại http://localhost:5173

3. Truy cập chương trình
- Mở trình duyệt và truy cập: http://localhost:5173.

# Cách 2: Chạy bằng Docker
1. Chuẩn bị
- Đảm bảo bạn đã cài đặt Docker và Docker Compose.
- Tạo file .env trong thư mục src/backend/ với nội dung:

```
GEMINI_API_KEY=your_gemini_api_key
```
- Thay your_gemini_api_key bằng API key thực tế của Gemini.

2. Xây dựng và chạy (lần đầu)
   2.1. Chạy Docker Compose:

   ```
   docker-compose up --build
   ```

   - Lệnh này sẽ xây dựng và chạy cả backend (FastAPI) và frontend (Nginx).
   - Backend sẽ chạy tại http://localhost:8000
   - Frontend sẽ chạy tại http://localhost:5173

   2.2. Truy cập chương trình:
   - Mở trình duyệt và truy cập: http://localhost:5173

3. Chạy lại mà không build
- Nếu bạn đã build image trước đó và không muốn build lại, sử dụng lệnh:
```
docker-compose up
```
- Lệnh này sẽ sử dụng các image đã build sẵn để khởi động container.

4. Dừng chương trình
Để dừng các container:

```
docker-compose down
```

# Lưu ý
- Nếu gặp vấn đề về cổng (port), hãy đảm bảo các cổng 8000 (backend) và 5173 (frontend) không bị chiếm dụng.