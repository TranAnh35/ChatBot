import React from 'react';
import { Conversation, ConversationSidebarProps } from '../../types/chat';
import { Button } from '../ui/button';
import { Trash2, Plus, MessageSquare, X } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { vi } from 'date-fns/locale';

export const ConversationSidebar: React.FC<ConversationSidebarProps & { isOpen: boolean; onClose: () => void }> = ({
  userId,
  conversations,
  currentConversationId,
  onConversationSelect,
  onCreateNewConversation,
  onDeleteConversation,
  isLoading,
  isOpen,
  onClose
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="bg-white/90 backdrop-blur-sm w-80 h-full overflow-y-auto animate-slide-in-left shadow-xl">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="font-semibold text-lg">Lịch sử trò chuyện</h2>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </div>

        <div className="p-4">
          <Button 
            className="w-full mb-4 flex items-center justify-center gap-2" 
            onClick={onCreateNewConversation}
          >
            <Plus className="h-4 w-4" />
            Cuộc trò chuyện mới
          </Button>
        </div>

        {isLoading ? (
          <div className="p-4 text-center">Đang tải...</div>
        ) : conversations.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            Chưa có cuộc trò chuyện nào
          </div>
        ) : (
          <div className="p-2">
            {conversations.map((conversation) => (
              <ConversationItem 
                key={conversation.conversation_id}
                conversation={conversation}
                isSelected={conversation.conversation_id === currentConversationId}
                onSelect={() => onConversationSelect(conversation.conversation_id)}
                onDelete={() => onDeleteConversation(conversation.conversation_id)}
              />
            ))}
          </div>
        )}
      </div>
      <div className="flex-1 bg-transparent" onClick={onClose}></div>
    </div>
  );
};

interface ConversationItemProps {
  conversation: Conversation;
  isSelected: boolean;
  onSelect: () => void;
  onDelete: () => void;
}

const ConversationItem: React.FC<ConversationItemProps> = ({
  conversation,
  isSelected,
  onSelect,
  onDelete
}) => {
  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete();
  };

  const formattedDate = formatDistanceToNow(new Date(conversation.updated_at), { 
    addSuffix: true,
    locale: vi 
  });

  return (
    <div 
      className={`p-3 rounded-md mb-2 flex items-start gap-3 cursor-pointer hover:bg-gray-100 relative group ${
        isSelected ? 'bg-blue-50 hover:bg-blue-100 border border-blue-200' : ''
      }`}
      onClick={onSelect}
    >
      <MessageSquare className="h-5 w-5 mt-1 text-gray-500" />
      <div className="flex-1 min-w-0">
        <div className="font-medium truncate">
          {conversation.preview || "Cuộc trò chuyện mới"}
        </div>
        <div className="text-xs text-gray-500">{formattedDate}</div>
      </div>
      <Button 
        variant="ghost" 
        size="icon" 
        className="opacity-0 group-hover:opacity-100 absolute right-2 top-2"
        onClick={handleDelete}
      >
        <Trash2 className="h-4 w-4 text-red-500" />
      </Button>
    </div>
  );
}; 