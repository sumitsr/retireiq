
import { LLMConfig, ChatMessage, SuggestedQuestion, UserProfile } from '@/types/chat';

// Note: Replace with your actual deployed Python API URL
const API_BASE_URL = 'http://localhost:5000/api';

// Helper to handle HTTP errors
const handleResponse = async (response: Response) => {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || `HTTP error! Status: ${response.status}`);
  }
  return response.json();
};

// Get the auth token from localStorage
const getAuthToken = (): string | null => {
  return localStorage.getItem('retireiq_auth_token');
};

// Set the auth token in localStorage
const setAuthToken = (token: string): void => {
  localStorage.setItem('retireiq_auth_token', token);
};

// Headers for authenticated requests
const authHeaders = (): HeadersInit => {
  const token = getAuthToken();
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  };
};

// Authentication
export const authService = {
  async register(email: string, password: string, name: string) {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, name })
    });
    
    const data = await handleResponse(response);
    setAuthToken(data.token);
    return data;
  },
  
  async login(email: string, password: string) {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    const data = await handleResponse(response);
    setAuthToken(data.token);
    return data;
  },
  
  logout() {
    localStorage.removeItem('retireiq_auth_token');
  },
  
  isAuthenticated(): boolean {
    return !!getAuthToken();
  }
};

// User Profile
export const profileService = {
  async getProfile(): Promise<UserProfile> {
    const response = await fetch(`${API_BASE_URL}/profile`, {
      headers: authHeaders()
    });
    
    return handleResponse(response);
  },
  
  async updateProfile(profile: UserProfile): Promise<UserProfile> {
    const response = await fetch(`${API_BASE_URL}/profile`, {
      method: 'PUT',
      headers: authHeaders(),
      body: JSON.stringify(profile)
    });
    
    return handleResponse(response);
  }
};

// Chat
export const chatService = {
  async sendMessage(message: string, conversationId?: string) {
    const response = await fetch(`${API_BASE_URL}/chat/message`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ 
        message, 
        conversation_id: conversationId 
      })
    });
    
    return handleResponse(response);
  },
  
  async getHistory(conversationId: string): Promise<ChatMessage[]> {
    const response = await fetch(`${API_BASE_URL}/chat/history?conversation_id=${conversationId}`, {
      headers: authHeaders()
    });
    
    const data = await handleResponse(response);
    return data.messages;
  }
};

// LLM Configuration
export const configService = {
  async getLLMConfig(): Promise<LLMConfig> {
    const response = await fetch(`${API_BASE_URL}/config/llm`, {
      headers: authHeaders()
    });
    
    return handleResponse(response);
  },
  
  async updateLLMConfig(config: LLMConfig): Promise<LLMConfig> {
    const response = await fetch(`${API_BASE_URL}/config/llm`, {
      method: 'PUT',
      headers: authHeaders(),
      body: JSON.stringify(config)
    });
    
    return handleResponse(response);
  }
};

// Combined exports
export const pythonBackendService = {
  auth: authService,
  profile: profileService,
  chat: chatService,
  config: configService
};

export default pythonBackendService;
