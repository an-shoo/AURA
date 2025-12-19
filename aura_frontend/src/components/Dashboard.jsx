import React from 'react';
import EmotionGraph from './EmotionGraph';
import PlayerFeed from './PlayerFeed';
import GameStatePanel from './GameStatePanel';
import AudiencePanel from './AudiencePanel';
import DnaVisualizer from './DnaVisualizer';
import AudioPlayer from './AudioPlayer';
import AudiencePollingBoard from './AudiencePollingBoard';
import MusicGenerator from './MusicGenerator';
import DirectorControls from './DirectorControls';

const Dashboard = ({ auraData, sendVote, sendControl }) => {
  return (
    <div className="dashboard-grid">
      <div className="grid-item span-2">
        <EmotionGraph emotionVector={auraData?.final_emotion_vector} />
      </div>
      <div className="grid-item">
        <DirectorControls sourceData={auraData?.source_data} sendControl={sendControl} />
      </div>
      <div className="grid-item">
        <PlayerFeed sourceData={auraData?.source_data} />
      </div>
      <div className="grid-item">
        <GameStatePanel gameState={auraData?.source_data?.game_state} />
      </div>
      <div className="grid-item">
        <AudiencePanel audienceVotes={auraData?.source_data?.audience_votes} sendVote={sendVote} />
      </div>
      <div className="grid-item">
        <DnaVisualizer audioInfo={auraData?.audio} dnaInfo={auraData} />
      </div>
      <div className="grid-item">
        <AudioPlayer audio={auraData?.audio} />
      </div>
      <div className="grid-item">
        <AudiencePollingBoard audienceUrl={null /* supply external viewer URL when ready */} />
      </div>
      <div className="grid-item">
        <MusicGenerator />
      </div>
    </div>
  );
};

export default Dashboard;