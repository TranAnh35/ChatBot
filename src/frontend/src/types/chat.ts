import { UploadedFile } from "./interface";

export interface Message {
    id: string;
    content: string;
    sender: 'user' | 'bot';
    timestamp: Date;
    file?: {
      name: string;
      type: string;
      size: number;
    };
    attachments?: UploadedFile[];
  }

export interface MessageListProps {
    messages: Message[];
    isLoading: boolean;
    currentBotMessage: Message | null;
    displayedContent: string;
    stoppedContent: string | null;
    isTyping: boolean;
    setDisplayedContent: (content: string) => void;
    setIsTyping: (isTyping: boolean) => void;
}

export interface MessageContentProps {
  content: string;
  attachments?: UploadedFile[];
}

export interface FileSelectorProps {
  uploadedFiles: ChatBoxProps['uploadedFiles'];
  selectedFiles: ChatBoxProps['selectedFiles'];
  onFileSelect: ChatBoxProps['onFileSelect'];
  onClose: () => void;
}

export interface ChatBoxProps {
  uploadedFiles: UploadedFile[];
  selectedFiles: UploadedFile[];
  onFileSelect: (file: UploadedFile) => void;
  onUploadClick: () => void;
}

export interface FileDropzoneProps {
  chatFiles: File[];
  setChatFiles: (files: File[] | ((prev: File[]) => File[])) => void; // Cập nhật kiểu của setChatFiles
  children: React.ReactNode;
}

export interface ChatInputProps {
  input: string;
  setInput: (input: string) => void;
  isLoading: boolean;
  isTyping: boolean;
  isWebSearchEnabled: boolean;
  chatFiles: File[];
  onSend: () => void;
  onStopTyping: () => void;
  toggleWebSearch: () => void;
  open?: () => void; // Thêm open vào interface
}

export interface GenerateContentRequest {
  input: string; // Nội dung tin nhắn
  files?: File[]; // Danh sách file đính kèm (tùy chọn)
}

export interface GenerateContentResponse {
  content: string; // Nội dung phản hồi từ API
  // Thêm các trường khác nếu API trả về thêm dữ liệu
}

