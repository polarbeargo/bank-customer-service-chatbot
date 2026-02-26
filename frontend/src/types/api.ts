/**
 * Type definitions for the chatbot API
 */

export interface ChatMessage {
  id?: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

export interface ConversationHistory {
  user: string;
  assistant: string;
}

export interface SessionResponse {
  session_id: string;
  created_at: string;
}

export interface ChatResponse {
  text: string;
  done?: boolean;
}

export interface HistoryResponse {
  session_id: string;
  history: ConversationHistory[];
  count: number;
}

export interface ApiError {
  error: string;
  message: string;
}

export interface ApiConfig {
  baseURL: string;
  timeout: number;
  headers: Record<string, string>;
}
