import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { v4 as uuidv4 } from "uuid";
import { useToast } from "@/hooks/use-toast";
import {
  ChatMessage,
  LLMConfig,
  SuggestedQuestion,
  UserProfile,
} from "@/types/chat";
import { pythonBackendService } from "@/services/pythonBackendService";

interface ChatContextProps {
  messages: ChatMessage[];
  isProcessing: boolean;
  conversationId: string | null;
  suggestedQuestions: SuggestedQuestion[];
  llmConfig: LLMConfig;
  userProfile: UserProfile | null;
  sendMessage: (content: string) => void;
  clearChat: () => void;
  updateLLMConfig: (config: LLMConfig) => void;
  updateUserProfile: (profile: UserProfile) => void;
}

const defaultLLMConfig: LLMConfig = {
  provider: "openai",
  modelName: "gpt-4o",
  apiKey: "",
  temperature: 0.7,
};

const defaultSuggestedQuestions: SuggestedQuestion[] = [
  {
    id: "1",
    text: "How much should I save for retirement?",
    category: "planning",
  },
  { id: "2", text: "What is a good retirement age?", category: "planning" },
  {
    id: "3",
    text: "Should I invest in stocks or bonds?",
    category: "investment",
  },
  { id: "4", text: "What is a pension?", category: "pension" },
];

const PythonChatContext = createContext<ChatContextProps | undefined>(
  undefined
);

export const PythonChatProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [suggestedQuestions, setSuggestedQuestions] = useState<
    SuggestedQuestion[]
  >(defaultSuggestedQuestions);
  const [llmConfig, setLLMConfig] = useState<LLMConfig>(defaultLLMConfig);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const { toast } = useToast();

  // Initialize with welcome message
  useEffect(() => {
    if (messages.length === 0) {
      const welcomeMessage: ChatMessage = {
        id: uuidv4(),
        content:
          "Hello! I'm RetireIQ, your retirement planning assistant. How can I help you today?",
        type: "bot",
        timestamp: new Date(),
      };
      setMessages([welcomeMessage]);
    }
  }, [messages.length]);

  // Try to load LLM config from backend when component mounts
  useEffect(() => {
    const loadConfig = async () => {
      if (pythonBackendService.auth.isAuthenticated()) {
        try {
          const config = await pythonBackendService.config.getLLMConfig();
          setLLMConfig(config);
        } catch (error) {
          console.log("Could not load LLM config:", error);
          // Continue with defaults
        }
      }
    };

    loadConfig();
  }, [pythonBackendService.auth.isAuthenticated()]);

  // Try to load user profile from backend when component mounts
  useEffect(() => {
    const loadProfile = async () => {
      if (pythonBackendService.auth.isAuthenticated()) {
        try {
          const profile = await pythonBackendService.profile.getProfile();
          setUserProfile(profile);
        } catch (error) {
          console.log("Could not load user profile:", error);
          // Continue with no profile
        }
      }
    };

    loadProfile();
  }, [pythonBackendService.auth.isAuthenticated()]);

  const addMessage = (content: string, type: "bot" | "user" | "system") => {
    const newMessage: ChatMessage = {
      id: uuidv4(),
      content,
      type,
      timestamp: new Date(),
    };

    setMessages((prevMessages) => [...prevMessages, newMessage]);
    return newMessage;
  };

  const sendMessage = async (content: string) => {
    if (!content.trim()) return;

    // Add user message to chat
    addMessage(content, "user");
    setIsProcessing(true);

    try {
      // Send message to Python backend
      const response = await pythonBackendService.chat.sendMessage(
        content,
        conversationId || undefined
      );

      // Set the conversation ID if this is a new conversation
      if (!conversationId && response.conversation_id) {
        setConversationId(response.conversation_id);
      }

      // Add bot response to chat
      addMessage(response.response, "bot");

      // Update suggested questions if available
      if (
        response.suggested_questions &&
        response.suggested_questions.length > 0
      ) {
        setSuggestedQuestions(response.suggested_questions);
      }
    } catch (error) {
      console.error("Failed to send message:", error);
      toast({
        title: "Error",
        description: "Failed to get a response. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setConversationId(null);
    setSuggestedQuestions(defaultSuggestedQuestions);

    // Add welcome message
    const welcomeMessage: ChatMessage = {
      id: uuidv4(),
      content:
        "Hello! I'm RetireIQ, your retirement planning assistant. How can I help you today?",
      type: "bot",
      timestamp: new Date(),
    };
    setMessages([welcomeMessage]);
  };

  const updateLLMConfig = async (config: LLMConfig) => {
    try {
      // Update config in backend if authenticated
      if (pythonBackendService.auth.isAuthenticated()) {
        await pythonBackendService.config.updateLLMConfig(config);
      }

      setLLMConfig(config);
      toast({
        title: "Settings updated",
        description: "Your AI model settings have been saved.",
      });
    } catch (error) {
      console.error("Failed to update settings:", error);
      toast({
        title: "Error",
        description: "Failed to update settings. Please try again.",
        variant: "destructive",
      });
    }
  };

  const updateUserProfile = async (profile: UserProfile) => {
    try {
      // Update profile in backend if authenticated
      if (pythonBackendService.auth.isAuthenticated()) {
        await pythonBackendService.profile.updateProfile(profile);
      }

      setUserProfile(profile);
      toast({
        title: "Profile updated",
        description: "Your retirement profile has been saved.",
      });
    } catch (error) {
      console.error("Failed to update profile:", error);
      toast({
        title: "Error",
        description: "Failed to update profile. Please try again.",
        variant: "destructive",
      });
    }
  };

  return (
    <PythonChatContext.Provider
      value={{
        messages,
        isProcessing,
        conversationId,
        suggestedQuestions,
        llmConfig,
        userProfile,
        sendMessage,
        clearChat,
        updateLLMConfig,
        updateUserProfile,
      }}
    >
      {children}
    </PythonChatContext.Provider>
  );
};

export const usePythonChat = (): ChatContextProps => {
  const context = useContext(PythonChatContext);
  if (context === undefined) {
    throw new Error("usePythonChat must be used within a PythonChatProvider");
  }
  return context;
};
