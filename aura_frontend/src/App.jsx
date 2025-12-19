import React from 'react';
import Header from './components/Header';
import Dashboard from './components/Dashboard';
import useAuraSocket from './hooks/useAuraSocket';
import './assets/css/App.css';

function App() {
  // Use env override if provided, else auto-resolve in hook
  const wsUrl = import.meta?.env?.VITE_AURA_WS_URL || undefined;
  const { isConnected, auraData, sendVote, sendControl } = useAuraSocket(wsUrl);

  return (
    <div className="app-container">
      <Header isConnected={isConnected} />
      <main className="content-wrapper">
        <Dashboard auraData={auraData} sendVote={sendVote} sendControl={sendControl} />
      </main>
    </div>
  );
}

export default App;