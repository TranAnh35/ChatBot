import api from '../lib/axios';
import { GenerateContentResponse } from '../types/api';
import { UploadedFile } from '../types/interface';
import { GenerateContentRequest } from '../types/chat';

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

  let webResponse = '';
  if (data.isWebSearchEnabled) {
    const inDepth_context = await api.get('/generate/inDepth_context', {
      params: { question: data.input }
    });

    let num_web_google = 0;

    if (inDepth_context.data === 'high') {
      num_web_google = 5;
    } else if (inDepth_context.data === 'medium') {
      num_web_google = 2;
    } else {
      num_web_google = 1;
    }

    const webSearchResult = await api.get<{ response: string }>('/web/search', {
      params: { question: data.input }
    }).catch(() => ({ data: { response: '' } }));
    webResponse = webSearchResult.data.response;
  }

  // Gọi API LLM với prompt bao gồm nội dung file
  const llmResponse = await api.get('/generate/gen_content', {
    params: {
      prompt: data.input,
      rag_response: ragResponse.data.response,
      file_response: fileContents,
      web_response: webResponse,
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
