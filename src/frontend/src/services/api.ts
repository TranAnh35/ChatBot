import api from '../lib/axios';
import { GenerateContentResponse } from '../types/api';
import { UploadedFile } from '../types/interface';
import { GenerateContentRequest, Conversation, Message } from '../types/chat';

// Gọi API tạo nội dung từ LLM và RAG
export const generateContent = async (data: GenerateContentRequest): Promise<GenerateContentResponse> => {
  // Lấy thông tin từ RAG (nếu cần)
  const ragResponse = await api.get<{ response: string }>('/rag/query', {
    params: { question: data.input }
  }).catch(() => ({ data: { response: '' } })); // Xử lý lỗi RAG nếu cần

  let fileContents = '';
  if (data.files && data.files.length > 0) {
    // Gửi từng file tới endpoint /read để backend đọc nội dung
    const filePromises = data.files.map(async (file) => {
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post<{ file_name: string; content: string }>('/files/read', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return `${response.data.file_name}: ${response.data.content}`;
    });
    const fileContentsArray = await Promise.all(filePromises);
    fileContents = fileContentsArray.join('\n');
  }

  let webResponse;
  if (data.isWebSearchEnabled) {
    const webSearchResult = await api.get<{ response: string }>('/web/search', {
      params: { query: data.input }
    }).catch(() => ({ data: { response: '' } }));
    console.log(webSearchResult.data);

    webResponse = await api.post<{ content: string }>('/generate/merge_context', {
      results: webSearchResult.data
    }).catch(() => ({ data: { content: '' } }));

    console.log(webResponse.data);
  }

  // console.log(webResponse.data);

  // Gọi API LLM với prompt bao gồm nội dung file
  const llmResponse = await api.get('/generate/gen_content', {
    params: {
      prompt: data.input,
      rag_response: ragResponse.data.response,
      file_response: fileContents,
      web_response: webResponse?.data.content,
      conversation_id: data.conversationId
    },
  });

  return { content: llmResponse.data.content };
};

// Gọi API lấy danh sách file đã upload
export const fetchFiles = async (): Promise<UploadedFile[]> => {
  const response = await api.get<{ files: UploadedFile[] }>("/files/files");
  return response.data.files;
};

// Upload file lên server
export const uploadFile = async (file: File): Promise<void> => {
  const formData = new FormData();
  formData.append("file", file);

  await api.post("/files/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  // Sau khi upload, đồng bộ vào vector database
  await api.post("/rag/sync-files");
};

// Xóa file khỏi server
export const deleteFile = async (filename: string): Promise<void> => {
  const encodedFilename = encodeURIComponent(filename);
  await api.delete(`/files/delete/${encodedFilename}`);
  await api.post("/rag/sync-files");
};

export const setApiKey = async (apiKey: string): Promise<string> => {
  const response = await api.post<{ message: string }>("/api/set_api_key", apiKey, {
    headers: { "Content-Type": "text/plain" }
  });
  return response.data.message;
};

export const validateApiKey = async (apiKey: string): Promise<boolean> => {
  try {
    // Giả sử bạn thêm một endpoint mới để kiểm tra
    const response = await api.post<{ valid: boolean }>("/api/validate_api_key", apiKey, {
      headers: { "Content-Type": "text/plain" }
    });
    return response.data.valid;
  } catch (error) {
    console.error("API key validation failed:", error);
    return false;
  }
};

// Conversation API methods
export const createConversation = async (userId: string): Promise<string> => {
  const response = await api.post<{ conversation_id: string }>('/conversations/create', {
    user_id: userId
  });
  return response.data.conversation_id;
};

export const getConversationHistory = async (conversationId: string, limit: number = 10): Promise<Message[]> => {
  const response = await api.get<{ messages: any[] }>(`/conversations/${conversationId}/history`, {
    params: { limit }
  });
  
  // Chuyển đổi dữ liệu từ backend (role: "user"/"assistant") sang dạng frontend (sender: "user"/"bot")
  return response.data.messages.map(message => ({
    id: message.timestamp, // Sử dụng timestamp làm ID nếu không có ID
    content: message.content,
    sender: message.role === "user" ? "user" : "bot", // Chuyển đổi role thành sender
    timestamp: new Date(message.timestamp)
  }));
};

export const listUserConversations = async (userId: string): Promise<Conversation[]> => {
  const response = await api.get<{ conversations: Conversation[] }>(`/conversations/user/${userId}`);
  return response.data.conversations;
};

export const deleteConversation = async (conversationId: string): Promise<boolean> => {
  const response = await api.delete<{ success: boolean }>(`/conversations/${conversationId}`);
  return response.data.success;
};