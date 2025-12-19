import React from 'react';

const AudiencePanel = ({ audienceVotes, sendVote }) => {
  const votes = audienceVotes || {};
  const moods = ["tension", "excitement", "fear", "joy", "calm"];

  return (
    <div className="card-pixel">
      <h2>Audience Conductor</h2>
      <div className="panel-content">
        <ul className="metric-list">
          {moods.map(mood => (
            <li key={mood} className="metric-item">
              <span className="metric-label">{mood.charAt(0).toUpperCase() + mood.slice(1)}</span>
              <span className="metric-value">{votes[mood] || 0}</span>
            </li>
          ))}
        </ul>
        <div className="audience-buttons">
          {moods.map(mood => (
             <button key={mood} className="btn-pixel secondary" onClick={() => sendVote(mood)}>
              Vote {mood}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AudiencePanel;