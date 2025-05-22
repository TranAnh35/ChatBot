# 👥 Hướng dẫn đóng góp

Cảm ơn bạn đã quan tâm đến việc đóng góp cho dự án ChatBot! Tài liệu này sẽ hướng dẫn bạn cách tham gia phát triển dự án.

## 📋 Mục lục

- [Quy tắc ứng xử](#-quy-tắc-ứng-xử)
- [Cách bắt đầu](#-cách-bắt-đầu)
- [Quy trình đóng góp](#-quy-trình-đóng-góp)
- [Môi trường phát triển](#-môi-trường-phát-triển)
- [Kiểm thử](#-kiểm-thử)
- [Báo cáo lỗi](#-báo-cáo-lỗi)
- [Yêu cầu tính năng mới](#-yêu-cầu-tính-năng-mới)
- [Quy tắc code](#-quy-tắc-code)
- [Giấy phép](#-giấy-phép)

## 🤝 Quy tắc ứng xử

Chúng tôi cam kết tạo ra một cộng đồng thân thiện và tôn trọng lẫn nhau. Vui lòng đọc và tuân thủ [Quy tắc ứng xử](CODE_OF_CONDUCT.md) của chúng tôi.

## 🚀 Cách bắt đầu

1. **Fork repository**
   - Nhấn nút "Fork" ở góc trên bên phải của trang repository
   - Clone repository đã fork về máy tính của bạn:
     ```bash
     git clone https://github.com/your-username/ChatBot.git
     cd ChatBot
     ```

2. **Thêm upstream remote**
   ```bash
   git remote add upstream https://github.com/original-owner/ChatBot.git
   ```

3. **Cập nhật nhánh chính**
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

## 🔄 Quy trình đóng góp

1. **Tạo nhánh mới**
   ```bash
   git checkout -b feature/ten-tinh-nang
   # hoặc
   git checkout -b fix/ten-loi
   ```

2. **Thực hiện thay đổi**
   - Thực hiện các thay đổi cần thiết
   - Kiểm tra kỹ mã nguồn trước khi commit

3. **Commit thay đổi**
   ```bash
   git add .
   git commit -m "Mô tả ngắn gọn về thay đổi"
   ```
   
   **Quy tắc commit message**:
   - Sử dụng thì hiện tại ("Thêm tính năng" thay vì "Đã thêm tính năng")
   - Giới hạn dòng đầu tiên trong 50 ký tự
   - Thêm mô tả chi tiết sau một dòng trống nếu cần

4. **Đẩy thay đổi lên repository của bạn**
   ```bash
   git push origin your-branch-name
   ```

5. **Tạo Pull Request**
   - Truy cập repository của bạn trên GitHub
   - Nhấn "Compare & pull request"
   - Điền đầy đủ thông tin theo mẫu
   - Nhấn "Create pull request"

## 💻 Môi trường phát triển

### Yêu cầu hệ thống

- Python 3.10+
- Node.js 18+
- npm hoặc yarn
- Docker (khuyến nghị)

### Cài đặt Backend

1. **Thiết lập môi trường ảo**
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Cài đặt phụ thuộc**
   ```bash
   pip install -r requirements-dev.txt
   ```

3. **Cấu hình biến môi trường**
   - Tạo file `.env` trong thư mục `src/backend/`
   - Thêm các biến môi trường cần thiết (xem `.env.example`)

4. **Chạy máy chủ phát triển**
   ```bash
   cd src/backend
   uvicorn main:app --reload
   ```

### Cài đặt Frontend

1. **Cài đặt phụ thuộc**
   ```bash
   cd src/frontend
   npm install
   ```

2. **Chạy máy chủ phát triển**
   ```bash
   npm run dev
   ```

### Chạy bằng Docker

```bash
docker compose up --build
```

## 🧪 Kiểm thử

### Backend Tests
```bash
# Chạy tất cả các test
pytest

# Chạy test với coverage
pytest --cov=src/backend
```

### Frontend Tests
```bash
cd src/frontend
npm test
```

## 🐛 Báo cáo lỗi

Khi gặp lỗi, vui lòng tạo issue mới với các thông tin sau:

1. **Mô tả chi tiết** về lỗi
2. **Các bước tái hiện** lỗi
3. **Kết quả mong đợi**
4. **Thông tin môi trường** (hệ điều hành, phiên bản trình duyệt, v.v.)
5. **Ảnh chụp màn hình** (nếu có)

## ✨ Yêu cầu tính năng mới

Chúng tôi luôn chào đón các ý tưởng mới! Để đề xuất tính năng mới:

1. Kiểm tra xem tính năng đã được yêu cầu chưa
2. Mô tả chi tiết về tính năng
3. Giải thích lý do tại sao tính năng này hữu ích
4. Đề xuất cách triển khai (nếu có)

## 📝 Quy tắc code

### Nguyên tắc chung
- Tuân thủ [PEP 8](https://www.python.org/dev/peps/pep-0008/) cho Python
- Sử dụng [Google Style Python Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- Đặt tên biến và hàm một cách rõ ràng, có ý nghĩa
- Giữ các hàm ngắn gọn và tập trung vào một nhiệm vụ duy nhất

### Định dạng code
- Sử dụng `black` để định dạng code Python
- Sử dụng `isort` để sắp xếp import
- Sử dụng `prettier` cho frontend code

### Kiểm thử
- Viết unit test cho các tính năng mới
- Đảm bảo tất cả các test đều pass trước khi tạo PR
- Duy trì độ phủ code cao (trên 80%)

## 📜 Giấy phép

Bằng cách đóng góp vào dự án này, bạn đồng ý rằng đóng góp của bạn sẽ được cấp phép theo giấy phép [MIT](LICENSE).

---

Cảm ơn bạn đã dành thời gian đóng góp cho dự án! ❤️