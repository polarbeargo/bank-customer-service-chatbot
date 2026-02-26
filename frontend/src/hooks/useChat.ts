/**
 * Custom React hooks for chatbot functionality
 */

import { useState, useCallback, useEffect } from 'react';
import { ChatMessage } from '../types/api';
import { chatbotApi } from '../utils/api';

const constants = {
  SESSION_STORAGE_KEY: 'chatbot_session_id',
};

/**
 * Hook for managing chat session
 */
export const useChat = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  // Initialize session
  useEffect(() => {
    const initializeSession = async () => {
      try {
        const savedSessionId = sessionStorage.getItem(constants.SESSION_STORAGE_KEY);
        
        if (savedSessionId) {
          console.log('Restoring existing session:', savedSessionId);
          chatbotApi.setSessionId(savedSessionId);
          const isValid = await chatbotApi.validateSession();
          if (isValid) {
            setSessionId(savedSessionId);
            return;
          }
          sessionStorage.removeItem(constants.SESSION_STORAGE_KEY);
        } else {
          console.log('No saved session, creating new one...');
          const newSessionId = await chatbotApi.createSession();
          if (newSessionId) {
            sessionStorage.setItem(constants.SESSION_STORAGE_KEY, newSessionId);
            setSessionId(newSessionId);
            console.log('Session saved to storage:', newSessionId);
          } else {
            throw new Error('Failed to create session: no session ID received');
          }
        }
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Failed to initialize session';
        console.error('Session initialization error:', errorMsg);
        setError(errorMsg);
      }
    };

    initializeSession();
  }, []);

  /**
   * Send a message and stream the response
   */
  const sendMessage = useCallback(
    async (userMessage: string) => {
      if (!sessionId) {
        setError('No active session');
        return;
      }

      const sessionValid = await chatbotApi.validateSession();
      if (!sessionValid) {
        try {
          const newSessionId = await chatbotApi.createSession();
          sessionStorage.setItem(constants.SESSION_STORAGE_KEY, newSessionId);
          setSessionId(newSessionId);
        } catch (err) {
          const errorMsg = err instanceof Error ? err.message : 'Failed to create new session';
          setError(errorMsg);
          return;
        }
      }

      const userMsg: ChatMessage = {
        id: `msg-${Date.now()}-user`,
        text: userMessage,
        sender: 'user',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setError(null);
      setIsLoading(true);

      const botMsgId = `msg-${Date.now()}-bot`;
      const botMsg: ChatMessage = {
        id: botMsgId,
        text: '',
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botMsg]);

      try {
        await chatbotApi.sendMessageStream(
          userMessage,
          (chunk: string) => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === botMsgId ? { ...msg, text: msg.text + chunk } : msg
              )
            );
          },
          () => {
            console.log('Message streaming complete');
            setIsLoading(false);
          },
          (err: Error) => {
            console.error('Streaming error:', err);
            const errorMsg = err.message || 'Failed to get response from server';
            setError(errorMsg);
            setIsLoading(false);
            setMessages((prev) => prev.filter((msg) => msg.id !== botMsgId));
          }
        );
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Failed to send message';
        console.error('Send message error:', errorMsg);
        setError(errorMsg);
        setIsLoading(false);
        setMessages((prev) => prev.filter((msg) => msg.id !== botMsgId));
      }
    },
    [sessionId]
  );

  /**
   * Clear chat history
   */
  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  /**
   * Logout (delete session)
   */
  const logout = useCallback(async () => {
    try {
      await chatbotApi.deleteSession();
      sessionStorage.removeItem(constants.SESSION_STORAGE_KEY);
      setSessionId(null);
      setMessages([]);
    
      const newSessionId = await chatbotApi.createSession();
      sessionStorage.setItem(constants.SESSION_STORAGE_KEY, newSessionId);
      setSessionId(newSessionId);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to logout';
      setError(errorMsg);
    }
  }, []);

  return {
    messages,
    isLoading,
    error,
    sessionId,
    sendMessage,
    clearChat,
    logout,
  };
};

/**
 * Hook for debouncing
 */
export const useDebounce = (value: string, delay: number = 300): string => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
};
