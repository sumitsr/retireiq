
import React from 'react';
import { Button } from '@/components/ui/button';
import { usePythonChat } from '@/contexts/PythonChatContext';

const ChatHeader: React.FC = () => {
  const { clearChat } = usePythonChat();

  return (
    <div className="p-4 border-b border-gray-200 bg-lloyds-darkGreen text-white flex justify-between items-center">
      <div>
        <h2 className="text-lg font-semibold">RetireIQ Assistant</h2>
        <p className="text-sm opacity-80">Your retirement planning companion</p>
      </div>
      
      <Button 
        variant="ghost" 
        onClick={clearChat}
        className="text-white hover:bg-lloyds-green"
      >
        New Chat
      </Button>
    </div>
  );
};

export default ChatHeader;
