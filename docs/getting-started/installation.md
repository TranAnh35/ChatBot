# Hướng dẫn cài đặt

Tài liệu này hướng dẫn chi tiết cách cài đặt và chạy ChatBot trên môi trường local hoặc sử dụng Docker.

## Yêu cầu hệ thống

### Phương pháp 1: Chạy trực tiếp (không dùng Docker)
- Python 3.10 hoặc cao hơn
- Node.js 18.x hoặc cao hơn
- npm (đi kèm với Node.js)
- pip (trình quản lý gói Python)

### Phương pháp 2: Sử dụng Docker (khuyến nghị)
- Docker Engine 20.10.0 trở lên
- Docker Compose 2.0.0 trở lên

## Phương pháp 1: Cài đặt và chạy trực tiếp

### 1. Cài đặt Backend

1. Sao chép repository:
   ```bash
   git clone [repository-url]
   cd ChatBot
   ```

2. Tạo và kích hoạt môi trường ảo (khuyến nghị):
   ```bash
   # Trên Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # Trên macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Cài đặt các phụ thuộc Python:
   ```bash
   pip install -r requirements.txt
   ```

4. Cấu hình biến môi trường:
   - Tạo file `.env` trong thư mục `src/backend/` với nội dung:
     ```
     GOOGLE_API_KEY=your_google_api_key_here
     ```
   - Thay `your_google_api_key_here` bằng API key của bạn từ [Google AI Studio](https://makersuite.google.com/app/apikey)


5. Khởi động backend:
   ```bash
   cd src/backend
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
   - Backend sẽ chạy tại: http://localhost:8000
   - Tài liệu API (Swagger UI): http://localhost:8000/docs

### 2. Cài đặt Frontend

1. Mở terminal mới và chuyển đến thư mục frontend:
   ```bash
   cd src/frontend
   ```

2. Cài đặt các phụ thuộc Node.js:
   ```bash
   npm install
   ```

3. Khởi động máy chủ phát triển:
   ```bash
   npm run dev
   ```
   - Frontend sẽ chạy tại: http://localhost:5173

## Phương pháp 2: Chạy bằng Docker (Khuyến nghị)

1. Đảm bảo Docker và Docker Compose đã được cài đặt

2. Sao chép repository (nếu chưa có):
   ```bash
   git clone [repository-url]
   cd ChatBot
   ```

3. Tạo file `.env` trong thư mục `src/backend/` với nội dung:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   ```

4. Xây dựng và khởi động các container:
   ```bash
   # Lần đầu tiên hoặc khi có thay đổi về dependencies
   docker compose up --build
   
   # Các lần sau
   docker compose up
   ```

5. Truy cập ứng dụng:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - Tài liệu API: http://localhost:8000/docs

## Kiểm tra cài đặt

1. Mở trình duyệt và truy cập http://localhost:5173
2. Nhấp vào biểu tượng cài đặt (⚙️) ở góc trên bên phải
3. Nhập API key của bạn và nhấn "Lưu"
4. Thử gửi một tin nhắn để kiểm tra kết nối với AI

## Xử lý sự cố

### Lỗi cổng đang sử dụng
Nếu gặp lỗi cổng đang được sử dụng, hãy đảm bảo không có ứng dụng nào khác đang sử dụng các cổng sau:
- 8000 (backend)
- 5173 (frontend)

### Lỗi kết nối API
- Kiểm tra kết nối internet
- Đảm bảo API key đã được cấu hình đúng
- Kiểm tra nhật ký lỗi của backend để biết thêm chi tiết

## Dừng ứng dụng

### Khi chạy trực tiếp
- Nhấn `Ctrl+C` trong cửa sổ terminal đang chạy backend/frontend

### Khi sử dụng Docker
```bash
docker compose down
```
