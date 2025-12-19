import React from 'react';

const Header = ({ isConnected }) => {
  return (
    <header className="header">
      <h1 className="pixel-title">AURA Studio</h1>
      <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
        {isConnected ? 'LIVE' : 'OFFLINE'}
      </div>
    </header>
  );
};

export default Header;