
import React, { createContext, useContext, useState, ReactNode } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { ChatMessage, LLMConfig, SuggestedQuestion, UserProfile } from '@/types/chat';
import { toast } from '@/components/ui/sonner';

interface ChatContextType {
  messages: ChatMessage[];
  llmConfig: LLMConfig;
  isProcessing: boolean;
  userProfile: UserProfile;
  suggestedQuestions: SuggestedQuestion[];
  addMessage: (content: string, type: 'user' | 'bot' | 'system') => void;
  sendMessage: (content: string) => Promise<void>;
  updateLLMConfig: (config: Partial<LLMConfig>) => void;
  updateUserProfile: (profile: Partial<UserProfile>) => void;
  clearChat: () => void;
}

const defaultLLMConfig: LLMConfig = {
  provider: 'openai',
  modelName: 'gpt-4o-mini',
  apiKey: '',
  temperature: 0.7,
};

// Default suggested questions about retirement planning
const defaultSuggestedQuestions: SuggestedQuestion[] = [
  { id: '1', text: 'When should I start saving for retirement?', category: 'general' },
  { id: '2', text: 'How much should I be saving every month?', category: 'planning' },
  { id: '3', text: 'What investment options are best for retirement?', category: 'investment' },
  { id: '4', text: 'How does a pension scheme work?', category: 'pension' },
  { id: '5', text: 'What are the tax implications of different retirement accounts?', category: 'planning' },
  { id: '6', text: 'What should my asset allocation be at age 55?', category: 'investment' },
];

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: uuidv4(),
      content: 'Hello! I\'m your RetireIQ assistant. How can I help with your retirement planning today?',
      type: 'bot',
      timestamp: new Date(),
    },
  ]);
  const [llmConfig, setLLMConfig] = useState<LLMConfig>(defaultLLMConfig);
  const [isProcessing, setIsProcessing] = useState(false);
  const [userProfile, setUserProfile] = useState<UserProfile | null>();
  const [suggestedQuestions, setSuggestedQuestions] = useState<SuggestedQuestion[]>(defaultSuggestedQuestions);

  const addMessage = (content: string, type: 'user' | 'bot' | 'system') => {
    const newMessage: ChatMessage = {
      id: uuidv4(),
      content,
      type,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, newMessage]);
  };

  const sendMessage = async (content: string) => {
    if (!content.trim()) return;
    
    // Add user message
    addMessage(content, 'user');
    setIsProcessing(true);
    
    try {
      // Simulate API call to LLM
      // In a real implementation, this would call your Python backend
      setTimeout(() => {
        let response: string;
        
        if (content.toLowerCase().includes('retirement age')) {
          response = "The standard retirement age in the UK is currently 66, but it's set to rise to 67 between 2026 and 2028. However, your ideal retirement age depends on your personal circumstances, financial situation, and retirement goals. Would you like me to help you plan for your specific retirement timeline?";
        } else if (content.toLowerCase().includes('pension')) {
          response = "There are several types of pensions in the UK: State Pension (provided by the government), Workplace Pensions (arranged by your employer), and Personal Pensions (set up by you). Each has different benefits and contribution structures. What specific aspect of pensions would you like to know more about?";
        } else if (content.toLowerCase().includes('saving')) {
          response = "Financial experts often recommend saving 15-20% of your income for retirement. However, the ideal amount depends on your current age, desired retirement age, and lifestyle expectations. Would you like me to help calculate a more personalized savings target based on your situation?";
        } else {
          response = "That's an excellent question about retirement planning. To give you the most accurate guidance, I'd need to know a bit more about your current situation. Could you share your current age and when you're hoping to retire?";
        }
        
        addMessage(response, 'bot');
        setIsProcessing(false);
      }, 2000);
      
    } catch (error) {
      console.error('Failed to send message:', error);
      toast.error('Failed to get a response. Please try again.');
      setIsProcessing(false);
    }
  };

  const updateLLMConfig = (config: Partial<LLMConfig>) => {
    setLLMConfig(prev => ({ ...prev, ...config }));
    toast.success('Settings updated successfully');
  };

  const updateUserProfile = (profile: Partial<UserProfile>) => {
    setUserProfile(prev => ({ ...prev, ...profile }));
  };

  const clearChat = () => {
    setMessages([
      {
        id: uuidv4(),
        content: 'Hello! I\'m your RetireIQ assistant. How can I help with your retirement planning today?',
        type: 'bot',
        timestamp: new Date(),
      },
    ]);
  };

  return (
    <ChatContext.Provider 
      value={{ 
        messages, 
        llmConfig, 
        isProcessing, 
        userProfile, 
        suggestedQuestions,
        addMessage, 
        sendMessage, 
        updateLLMConfig, 
        updateUserProfile,
        clearChat 
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = (): ChatContextType => {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};
