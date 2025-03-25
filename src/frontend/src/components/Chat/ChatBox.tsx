import React, { useState } from 'react';
import { ChatBoxProps, Message } from '../../types/chat';
import { generateContent } from '../../services/api';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import FileSelector from './FileSelector';
import FileDropzone from './FileDropzone';
import { GenerateContentRequest } from '../../types/chat';
import { UploadedFile } from '../../types/interface';

export const ChatBox: React.FC<ChatBoxProps> = ({ uploadedFiles, selectedFiles, onFileSelect, onUploadClick }) => {
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
  
    const uploadedFilesArray = chatFiles.length > 0 ? convertFilesToUploadedFiles(chatFiles) : undefined;
    console.log(uploadedFilesArray)

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
    </div>
  );
};