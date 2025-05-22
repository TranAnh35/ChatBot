# API Endpoints

## API Manager

### Get API Key
```http
  GET /api/get_api_key
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| None | None | None |

### Set API Key
```http
  POST /api/set_api_key
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `api_key` | `string` | **Required**. API key mới cần thiết lập |

### Validate API Key
```http
  POST /api/validate_api_key
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `api_key` | `string` | **Required**. API key cần kiểm tra tính hợp lệ |

## RAG (Retrieval-Augmented Generation)

### Query
```http
  GET /rag/query
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `question` | `string` | **Required**. Câu hỏi cần truy vấn |

### Sync Files
```http
  POST /rag/sync-files
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| None | None | None |

## File Manager

### Upload File
```http
  POST /files/upload
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `file` | `file` | **Required**. File cần tải lên |

### Get Files
```http
  GET /files/files
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| None | None | None |

### Delete File
```http
  DELETE /files/delete/{file_name}
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `file_name` | `string` | **Required**. Tên file cần xóa |

### Read File
```http
  POST /files/read
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `file` | `file` | **Required**. File cần đọc |

## Web Search

### Search
```http
  GET /web/search
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `query` | `string` | **Required**. Query cần tìm kiếm |

### Page Content
```http
  GET /web/page-content
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `url` | `string` | **Required**. URL cần tìm kiếm |

## Generative Content

### Generate Content
```http
  GET /generate/gen_content
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `question` | `string` | **Required**. Câu hỏi cần truy vấn |

### Merge Context
```http
  POST /generate/merge_context
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `web_results` | `WebResults` | **Required**. Kết quả tìm kiếm web |

## Conversation

### Create
```http
  POST /conversations/create
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `user_id` | `string` | **Required**. ID của người dùng |

### Add Message
```http
  POST /conversations/message
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `conversation_id` | `string` | **Required**. ID của cuộc trò chuyện |
| `role` | `string` | **Required**. Vai trò của người dùng |
| `content` | `string` | **Required**. Nội dung tin nhắn |

### Rename
```http
  POST /conversations/rename
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `conversation_id` | `string` | **Required**. ID của cuộc trò chuyện |
| `title` | `string` | **Required**. Tiêu đề mới |

### Get Conversation
```http
  GET /conversations/{conversation_id}
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `conversation_id` | `string` | **Required**. ID của cuộc trò chuyện |

### Get Conversation History
```http
  GET /conversations/{conversation_id}/history
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `conversation_id` | `string` | **Required**. ID của cuộc trò chuyện |
| `limit` | `int` | **Required**. Số lượng tin nhắn cần lấy |

### List User Conversations
```http
  GET /conversations/user/{user_id}
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `user_id` | `string` | **Required**. ID của người dùng |

### Delete Conversation
```http
  DELETE /conversations/{conversation_id}
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `conversation_id` | `string` | **Required**. ID của cuộc trò chuyện |