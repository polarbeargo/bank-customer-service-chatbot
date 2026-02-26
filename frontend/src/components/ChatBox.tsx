/**
 * ChatBox Component
 * Main chat interface for the bank customer service chatbot
 */

import React, { useState, useRef, useEffect } from 'react';
import { useChat } from '../hooks/useChat';
import '../styles/ChatBox.css';

export const ChatBox: React.FC<any> = () => {
  const { messages, isLoading, error, sendMessage, clearChat, logout } = useChat();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const message = input.trim();
    setInput('');
    await sendMessage(message);
  };

  return (
    <div className="chatbox-container">
      {/* Header */}
      <div className="chatbox-header">
        <h1>🏦 Bank Customer Service Chatbot</h1>
        <div className="header-actions">
          <button onClick={clearChat} className="btn btn-secondary" title="Clear chat">
            Clear
          </button>
          <button onClick={logout} className="btn btn-secondary" title="Logout">
            Logout
          </button>
        </div>
      </div>

      {/* Messages Container */}
      <div className="chatbox-messages">
        {messages.length === 0 && (
          <div className="welcome-message">
            <h2>Welcome!</h2>
            <p>I'm your bank customer service assistant. I can help you with:</p>
            <ul>
              <li>Service information and offerings</li>
              <li>Branch locations and contact details</li>
              <li>Loan application process</li>
              <li>Account opening process</li>
              <li>Account information (with verification)</li>
            </ul>
            <p>How can I assist you today?</p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`message message-${message.sender}`}
          >
            <div className={`message-content ${message.sender}`}>
              <p>{message.text}</p>
              <span className="message-time">
                {message.timestamp.toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </span>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="message message-bot">
            <div className="message-content bot loading">
              <div className="loading-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="message message-error">
            <div className="message-content error">
              <p>❌ Error: {error}</p>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form className="chatbox-input-form" onSubmit={handleSendMessage}>
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message here..."
          disabled={isLoading}
          className="chatbox-input"
          maxLength={1000}
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="btn btn-primary"
          title="Send message"
        >
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </form>

      {/* Character Count */}
      <div className="input-info">
        <small>{input.length}/1000 characters</small>
      </div>
    </div>
  );
};
