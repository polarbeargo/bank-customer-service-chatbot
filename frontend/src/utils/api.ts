/**
 * API utility for communication with the chatbot backend
 * Implements streaming responses using Server-Sent Events (SSE)
 */

import axios, { AxiosInstance } from 'axios';
import { ApiError } from '../types/api';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

console.log('🔌 API Base URL:', API_BASE_URL);

export class ChatbotApiClient {
  private client: AxiosInstance;
  private sessionId: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}/api`,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
      },
    });

    this.client.defaults.headers.common['X-Client-Version'] = '1.0.0';
    console.log('✅ API Client initialized');
  }

  /**
   * Create a new chat session
   */
  async createSession(): Promise<string> {
    try {
      console.log('📝 Creating new session...');
      const response = await this.client.post('/session', {});
      this.sessionId = response.data.session_id;
      console.log('✅ Session created:', this.sessionId);
      return this.sessionId || '';
    } catch (error) {
      console.error('❌ Session creation failed:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Send a message and stream response via SSE
   */
  async sendMessageStream(
    message: string,
    onChunk: (chunk: string) => void,
    onComplete: () => void,
    onError: (error: Error) => void
  ): Promise<void> {
    if (!this.sessionId) {
      throw new Error('No active session. Create a session first.');
    }

    try {
      const url = `${API_BASE_URL}/api/chat/${this.sessionId}?message=${encodeURIComponent(message)}`;
      console.log('[DEBUG] SSE URL:', url);
      
      const eventSource = new EventSource(url, {
        withCredentials: true,
      }) as any;

      eventSource.addEventListener('message', (event: MessageEvent) => {
        try {
          console.log('[DEBUG] SSE Event received:', event.data.substring(0, 50));
          const data = JSON.parse(event.data);
          
          if (data.done) {
            console.log('[OK] SSE stream complete');
            eventSource.close();
            onComplete();
          } else if (data.text) {
            console.log('[INFO] SSE chunk:', data.text);
            onChunk(data.text);
          }
        } catch (error) {
          console.error('[ERROR] Error parsing SSE data:', error);
          console.error('Raw data:', event.data);
        }
      });

      eventSource.addEventListener('error', (event: any) => {
        console.error('[ERROR] SSE Error:', event, 'readyState:', eventSource.readyState);
        
        // readyState: 0=CONNECTING, 1=OPEN, 2=CLOSED
        if (eventSource.readyState === 2) {
          console.error('[ERROR] Server closed connection unexpectedly');
          if (event.message) {
            onError(new Error(`Server error: ${event.message}`));
          } else {
            onError(new Error('Connection to server lost'));
          }
        } else {
          console.error('[ERROR] Connection error, readyState:', eventSource.readyState);
          onError(new Error('Connection to server failed'));
        }
        eventSource.close();
      });

      setTimeout(() => {
        if (eventSource.readyState !== 2) {
          console.error('[TIMEOUT] SSE timeout - server took too long to respond');
          eventSource.close();
          onError(new Error('Server timeout'));
        }
      }, 30000);

    } catch (error) {
      console.error('[ERROR] SSE creation error:', error);
      onError(this.handleError(error));
    }
  }

  /**
   * Send a message (non-streaming fallback)
   */
  async sendMessage(message: string): Promise<string> {
    if (!this.sessionId) {
      throw new Error('No active session. Create a session first.');
    }

    try {
      const response = await this.client.post(
        `/chat/${this.sessionId}`,
        { message },
        {
          headers: {
            'Accept': 'text/event-stream',
          },
        }
      );
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Get conversation history
   */
  async getHistory() {
    if (!this.sessionId) {
      throw new Error('No active session. Create a session first.');
    }

    try {
      const response = await this.client.get(`/session/${this.sessionId}/history`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Validate current session by attempting to fetch history
   */
  async validateSession(): Promise<boolean> {
    if (!this.sessionId) {
      return false;
    }

    try {
      await this.client.get(`/session/${this.sessionId}/history`);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Delete session (logout)
   */
  async deleteSession(): Promise<void> {
    if (!this.sessionId) {
      return;
    }

    try {
      await this.client.delete(`/session/${this.sessionId}`);
      this.sessionId = null;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  /**
   * Get current session ID
   */
  getSessionId(): string | null {
    return this.sessionId;
  }

  /**
   * Set session ID (for resuming sessions)
   */
  setSessionId(id: string): void {
    this.sessionId = id;
  }

  /**
   * Handle API errors
   */
  private handleError(error: any): Error {
    if (axios.isAxiosError(error)) {
      const apiError = error.response?.data as ApiError;
      if (apiError && apiError.message) {
        return new Error(`${apiError.error}: ${apiError.message}`);
      }
      return new Error(
        error.response?.statusText || 'An error occurred while communicating with the server'
      );
    }
    return error instanceof Error ? error : new Error('An unknown error occurred');
  }
}

export const chatbotApi = new ChatbotApiClient();
