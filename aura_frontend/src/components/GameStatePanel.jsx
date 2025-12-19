import React from 'react';

const GameStatePanel = ({ gameState }) => {
  const gs = gameState || {};
  return (
    <div className="card-pixel">
      <h2>Game State</h2>
      <div className="panel-content">
        <ul className="metric-list">
          <li className="metric-item">
            <span className="metric-label">Health</span>
            <span className="metric-value">{gs.player_health || 0}</span>
          </li>
          <li className="metric-item">
            <span className="metric-label">Enemies</span>
            <span className="metric-value">{gs.enemy_count || 0}</span>
          </li>
          <li className="metric-item">
            <span className="metric-label">Score</span>
            <span className="metric-value">{gs.score || 0}</span>
          </li>
          <li className="metric-item">
            <span className="metric-label">Threat</span>
            <span className="metric-value">{((gs.threat_proximity || 0) * 100).toFixed(0)}%</span>
          </li>
        </ul>
      </div>
    </div>
  );
};

export default GameStatePanel;