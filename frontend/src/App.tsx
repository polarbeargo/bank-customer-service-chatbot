/**
 * Main App Component
 */

import React from 'react';
import { ChatBox } from './components/ChatBox';
import './styles/App.css';

const App: React.FC<any> = () => {
  return (
    <div className="app">
      <ChatBox />
    </div>
  );
};

export default App;
