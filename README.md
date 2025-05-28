<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/Node.js-18+-green" alt="Node.js 18+">
</p>

ChatBot là một ứng dụng chat thông minh tích hợp AI sử dụng Google Gemini API, được xây dựng với FastAPI (backend) và React/TypeScript (frontend). Ứng dụng cung cấp khả năng trò chuyện thông minh, quản lý tài liệu và tìm kiếm thông tin từ nhiều nguồn khác nhau.

## 🌟 Tính năng nổi bật

- **Trò chuyện thông minh** với Google Gemini AI (mặc định sử dụng model gemini-2.0-flash-lite)
- **Hỗ trợ đa định dạng tài liệu** (TXT, PDF, DOC, DOCX, YAML, YML, MD)
- **Tìm kiếm thông tin** từ tài liệu đã tải lên (RAG - Retrieval Augmented Generation)
- **Tích hợp tìm kiếm web** để cập nhật thông tin mới nhất
- **Giao diện hiện đại**, dễ sử dụng với React + TypeScript
- **Hỗ trợ đính kèm file** trực tiếp trong cuộc trò chuyện
- **Quản lý hội thoại** với database SQLite
- **API endpoints toàn diện** với FastAPI và tài liệu Swagger tự động
- **Cấu hình linh hoạt** cho PDF reader (PyMuPDF nhanh hoặc Docling chính xác)

## 🚀 Bắt đầu nhanh

### Yêu cầu hệ thống

- Python 3.10+ và pip
- Node.js 18+ và npm
- Docker và Docker Compose (tùy chọn)
- [Google Gemini API key](https://makersuite.google.com/app/apikey)

### Cài đặt và chạy

Xem hướng dẫn chi tiết trong [tài liệu cài đặt](docs/getting-started/installation.md).

## 📚 Tài liệu

- [Hướng dẫn sử dụng](docs/guides/USER_GUIDE.md) - Hướng dẫn đầy đủ về cách sử dụng ChatBot
- [Tài liệu API](docs/guides/api/API_REFERENCE.md) - Tham khảo đầy đủ các API endpoints
- [Cấu trúc dự án](docs/PROJECT_STRUCTURE.md) - Tổng quan về kiến trúc và mã nguồn

## 📞 Liên hệ

- **Tác giả**: [Trần Anh]
- **Email**: tranleanh352004@gmail.com

---

**Lưu ý**: Đây là dự án cá nhân và hiện tại không nhận contributions từ bên ngoài.