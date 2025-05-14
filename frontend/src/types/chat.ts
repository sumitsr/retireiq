
export type MessageType = 'bot' | 'user' | 'system';

export interface ChatMessage {
  id: string;
  content: string;
  type: MessageType;
  timestamp: Date;
}

export interface LLMConfig {
  provider: 'openai' | 'anthropic' | 'perplexity';
  modelName: string;
  apiKey: string;
  temperature: number;
}

export interface SuggestedQuestion {
  id: string;
  text: string;
  category: 'general' | 'planning' | 'investment' | 'pension';
}

export interface UserProfile {
  age?: number;
  name: string;
  email: string;
  userId: string;
  retirementAge?: number;
  currentSavings?: number;
  monthlySavings?: number;
  riskTolerance?: 'low' | 'medium' | 'high';
}
