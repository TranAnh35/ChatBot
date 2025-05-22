# Cấu trúc dự án

```
ChatBot/
├── Dockerfile.backend      # Dockerfile cho backend
├── Dockerfile.frontend     # Dockerfile cho frontend
├── docker-compose.yml      # Cấu hình Docker Compose
├── requirements.txt        # Yêu cầu Python
└── src/                    # Thư mục chứa mã nguồn
    ├── backend/              # Mã nguồn backend FastAPI
    │   ├── models/           # Các model dữ liệu
    │   ├── routes/           # API endpoints
    │   ├── services/         # Các service xử lý logic
    │   ├── storage/          # Lưu trữ cuộc trò chuyện
    │   ├── upload/           # Thư mục lưu file người dùng tải lên
    │   ├── .env              # File chứa API key
    │   └── main.py           # File chính của backend
    │
    ├── frontend/             # Mã nguồn frontend React/TypeScript
    │   ├── public/           # Thư mục chứa các file tĩnh
    │   ├── src/              # Mã nguồn React/TypeScript
    │   │   ├── assets/       # Thư mục chứa các file tĩnh
    │   │   ├── components/   # Các component UI
    │   │   ├── libs/         # Các thư viện
    │   │   ├── services/     # Các service gọi API
    │   │   ├── types/        # Định nghĩa kiểu dữ liệu TypeScript
    │   │   └── App.tsx       # File chính của frontend
    │   └── vite.config.ts    # Cấu hình Vite
    │
    └── run.py                # File chính của chương trình
```

Tài liệu này mô tả chi tiết cấu trúc thư mục và các thành phần chính của dự án ChatBot, giúp nhà phát triển mới nhanh chóng làm quen với mã nguồn.