
import React, { useRef, useEffect } from 'react';
import ChatMessage from './ChatMessage';
import { usePythonChat } from '@/contexts/PythonChatContext';

const ChatContainer: React.FC = () => {
  const { messages, isProcessing } = usePythonChat();
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div 
      ref={containerRef} 
      className="flex-1 overflow-y-auto p-4 space-y-4"
    >
      {messages.map((message) => (
        <ChatMessage key={message.id} message={message} />
      ))}
      
      {isProcessing && (
        <div className="chat-message-bot">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 rounded-full bg-lloyds-darkBlue animate-pulse"></div>
            <div className="w-2 h-2 rounded-full bg-lloyds-darkBlue animate-pulse delay-100"></div>
            <div className="w-2 h-2 rounded-full bg-lloyds-darkBlue animate-pulse delay-200"></div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatContainer;
