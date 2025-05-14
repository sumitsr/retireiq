
import React from 'react';
import { ChatMessage as ChatMessageType } from '@/types/chat';
import { formatDistanceToNow } from 'date-fns';

interface ChatMessageProps {
  message: ChatMessageType;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  return (
    <div className={`${
      message.type === 'bot' ? 'chat-message-bot' : 
      message.type === 'user' ? 'chat-message-user' : 
      'bg-yellow-100 text-yellow-800 chat-message-container'
    }`}>
      <div className="flex flex-col">
        <div className="text-sm break-words">{message.content}</div>
        <div className="text-xs mt-1 opacity-70 text-right">
          {formatDistanceToNow(new Date(message.timestamp), { addSuffix: true })}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;
