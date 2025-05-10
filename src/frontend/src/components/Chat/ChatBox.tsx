import React, { useState, useEffect, useCallback } from 'react';
import { ChatBoxProps, Message, Conversation } from '../../types/chat';
import { generateContent, createConversation, getConversationHistory, listUserConversations, deleteConversation, renameConversation } from '../../services/api';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import FileSelector from './FileSelector';
import FileDropzone from './FileDropzone';
import { GenerateContentRequest } from '../../types/chat';
import { UploadedFile } from '../../types/interface';
import { ConversationSidebar } from './ConversationSidebar';
import { useSnackbar } from 'notistack';

// Sử dụng ID người dùng cố định cho toàn bộ ứng dụng
// Vì không có hệ thống đăng nhập, chúng ta sẽ sử dụng một ID cố định cho tất cả cuộc trò chuyện
const DEFAULT_USER_ID = "default_user";

export const ChatBox: React.FC<ChatBoxProps> = ({ 
  uploadedFiles, 
  selectedFiles, 
  onFileSelect,
  showConversations,
  onCloseConversations
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [displayedContent, setDisplayedContent] = useState<string>('');
  const [stoppedContent, setStoppedContent] = useState<string | null>(null);
  const [currentBotMessage, setCurrentBotMessage] = useState<Message | null>(null);
  const [isTyping, setIsTyping] = useState(false);
  const [showFileSelector, setShowFileSelector] = useState(false);
  const [isWebSearchEnabled, setIsWebSearchEnabled] = useState(false);
  const [chatFiles, setChatFiles] = useState<File[]>([]);
  
  // Conversation state
  const [userId] = useState<string>(DEFAULT_USER_ID);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | undefined>(undefined);
  const [isConversationsLoading, setIsConversationsLoading] = useState(false);
  // State để theo dõi xem đã tải xong cuộc trò chuyện hay chưa
  const [isConversationsLoaded, setIsConversationsLoaded] = useState(false);

  const { enqueueSnackbar } = useSnackbar();

  // Load danh sách cuộc trò chuyện khi component mounts
  useEffect(() => {
    loadConversations();
  }, []);

  // Load conversation history when selecting a conversation
  useEffect(() => {
    if (currentConversationId) {
      loadConversationHistory(currentConversationId);
    } else {
      // Nếu không có cuộc trò chuyện nào được chọn, làm sạch danh sách tin nhắn
      setMessages([]);
    }
  }, [currentConversationId]);

  const loadConversations = useCallback(async () => {
    setIsConversationsLoading(true);
    try {
      const userConversations = await listUserConversations(userId);
      setConversations(userConversations);
    } catch (error) {
      console.error('Error loading conversations:', error);
      enqueueSnackbar('Lỗi khi tải danh sách cuộc trò chuyện', { 
        variant: 'error',
      });
    } finally {
      setIsConversationsLoading(false);
      setIsConversationsLoaded(true); // Đánh dấu là đã tải xong conversations
    }
  }, [userId, enqueueSnackbar]);

  const loadConversationHistory = useCallback(async (conversationId: string) => {
    setIsLoading(true);
    try {
      const history = await getConversationHistory(conversationId);
      if (history && history.length > 0) {
        setMessages(history);
      } else {
        setMessages([]);
      }
    } catch (error) {
      console.error('Error loading conversation history:', error);
      enqueueSnackbar('Lỗi khi tải lịch sử cuộc trò chuyện', { 
        variant: 'error',
      });
    } finally {
      setIsLoading(false);
    }
  }, [enqueueSnackbar]);

  const handleCreateNewConversation = useCallback(async () => {
    setIsLoading(true);
    try {
      const newConversationId = await createConversation(userId);
      setCurrentConversationId(newConversationId);
      setMessages([]);
      loadConversations(); // Refresh the list
      if (onCloseConversations) {
        onCloseConversations();
      }
      enqueueSnackbar('Đã tạo cuộc trò chuyện mới', { 
        variant: 'success',
      });
    } catch (error) {
      console.error('Error creating new conversation:', error);
      enqueueSnackbar('Lỗi khi tạo cuộc trò chuyện mới', { 
        variant: 'error',
      });
    } finally {
      setIsLoading(false);
    }
  }, [userId, loadConversations, enqueueSnackbar, onCloseConversations]);

  const handleConversationSelect = useCallback((conversationId: string) => {
    setCurrentConversationId(conversationId);
    if (onCloseConversations) {
      onCloseConversations();
    }
  }, [onCloseConversations]);

  const handleRenameConversation = useCallback(async (conversationId: string, title: string) => {
    try {
      const success = await renameConversation(conversationId, title);
      if (success) {
        loadConversations(); // Tải lại danh sách để cập nhật tiêu đề mới
        enqueueSnackbar('Đã đổi tên cuộc trò chuyện', { 
          variant: 'success',
        });
      } else {
        enqueueSnackbar('Không thể đổi tên cuộc trò chuyện', { 
          variant: 'error',
        });
      }
    } catch (error) {
      console.error('Error renaming conversation:', error);
      enqueueSnackbar('Lỗi khi đổi tên cuộc trò chuyện', { 
        variant: 'error',
      });
    }
  }, [loadConversations, enqueueSnackbar]);

  const handleDeleteConversation = useCallback(async (conversationId: string) => {
    try {
      await deleteConversation(conversationId);
      
      // Nếu xóa cuộc trò chuyện hiện tại, hãy cập nhật UI
      if (conversationId === currentConversationId) {
        // Không tự động tạo cuộc trò chuyện mới, chỉ xóa ID và làm sạch tin nhắn
        setCurrentConversationId(undefined);
        setMessages([]);
      }
      
      // Tải lại danh sách cuộc trò chuyện
      loadConversations();
      enqueueSnackbar('Đã xóa cuộc trò chuyện', { 
        variant: 'success',
      });
    } catch (error) {
      console.error('Error deleting conversation:', error);
      enqueueSnackbar('Lỗi khi xóa cuộc trò chuyện', { 
        variant: 'error',
      });
    }
  }, [currentConversationId, loadConversations, enqueueSnackbar]);

  const convertFilesToUploadedFiles = (files: File[]): UploadedFile[] => {
    return files.map((file, index) => ({
      id: `${Date.now()}-${index}`, // Tạo id duy nhất (có thể thay đổi logic nếu cần)
      name: file.name,
      size: file.size,
      type: file.type,
    }));
  };

  const handleSend = async () => {
    if (!input.trim()) return;
  
    // Nếu không có cuộc trò chuyện hiện tại, tạo một cuộc mới
    if (!currentConversationId) {
      try {
        const newConversationId = await createConversation(userId);
        setCurrentConversationId(newConversationId);
        loadConversations(); // Refresh the list
      } catch (error) {
        console.error('Error creating conversation:', error);
        enqueueSnackbar('Lỗi khi tạo cuộc trò chuyện, thử lại sau', { 
          variant: 'error',
        });
        return;
      }
    }

    const uploadedFilesArray = chatFiles.length > 0 ? convertFilesToUploadedFiles(chatFiles) : undefined;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: input,
      sender: 'user',
      timestamp: new Date(),
      attachments: uploadedFilesArray,
    };
  
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
  
    try {
      const requestData: GenerateContentRequest = {
        input: userMessage.content,
        files: chatFiles.length > 0 ? [...chatFiles] : undefined,
        isWebSearchEnabled: isWebSearchEnabled,
        conversationId: currentConversationId
      };
  
      const data = await generateContent(requestData);
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: data.content,
        sender: 'bot',
        timestamp: new Date(),
      };
      setCurrentBotMessage(botMessage);
      setDisplayedContent('');
      setIsTyping(true);
      setMessages((prev) => [...prev, botMessage]);
  
      setChatFiles([]); // Xóa file sau khi gửi để không lưu lại
      
      // Refresh conversations list after sending a message
      loadConversations();
    } catch (error) {
      console.error('Error generating content:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Sorry, something went wrong.',
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStopTyping = () => {
    setIsTyping(false);
    setStoppedContent(displayedContent);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] pt-16">
      <MessageList
        messages={messages}
        isLoading={isLoading}
        currentBotMessage={currentBotMessage}
        displayedContent={displayedContent}
        stoppedContent={stoppedContent}
        isTyping={isTyping}
        setDisplayedContent={setDisplayedContent}
        setIsTyping={setIsTyping}
      />
      {showFileSelector && (
        <FileSelector
          uploadedFiles={uploadedFiles}
          selectedFiles={selectedFiles}
          onFileSelect={onFileSelect}
          onClose={() => setShowFileSelector(false)}
        />
      )}
      <FileDropzone
        chatFiles={chatFiles}
        setChatFiles={setChatFiles}
      >
        <ChatInput
          input={input}
          setInput={setInput}
          isLoading={isLoading}
          isTyping={isTyping}
          isWebSearchEnabled={isWebSearchEnabled}
          chatFiles={chatFiles}
          onSend={handleSend}
          onStopTyping={handleStopTyping}
          toggleWebSearch={() => setIsWebSearchEnabled(!isWebSearchEnabled)}
        />
      </FileDropzone>

      {/* Conversation Sidebar */}
      <ConversationSidebar
        userId={userId}
        conversations={conversations}
        currentConversationId={currentConversationId}
        onConversationSelect={handleConversationSelect}
        onCreateNewConversation={handleCreateNewConversation}
        onDeleteConversation={handleDeleteConversation}
        onRenameConversation={handleRenameConversation}
        isLoading={isConversationsLoading}
        isOpen={showConversations || false}
        onClose={onCloseConversations || (() => {})}
      />
    </div>
  );
};