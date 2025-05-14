
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { usePythonChat } from '@/contexts/PythonChatContext';
import { Send } from 'lucide-react';

const ChatInput: React.FC = () => {
  const [message, setMessage] = useState('');
  const { sendMessage, isProcessing } = usePythonChat();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isProcessing) {
      sendMessage(message);
      setMessage('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-center space-x-2 p-4 border-t border-gray-200">
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        disabled={isProcessing}
        placeholder={isProcessing ? "Waiting for response..." : "Type your message..."}
        className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-lloyds-green focus:border-transparent"
      />
      <Button 
        type="submit" 
        disabled={!message.trim() || isProcessing}
        className="lloyds-button-primary"
      >
        <Send size={18} />
      </Button>
    </form>
  );
};

export default ChatInput;
