import React, { useEffect, useState } from 'react';

// Helper to clamp 0-1
const clamp01 = (v) => Math.max(0, Math.min(1, v));

const DirectorControls = ({ sourceData, sendControl }) => {

  const [weights, setWeights] = useState({ game_state: 0.8, face: 0.1, speech: 0.1 });
  const [overrideActive, setOverrideActive] = useState(false);
  const [overrideVector, setOverrideVector] = useState({ tension: 0, excitement: 0, fear: 0, joy: 0, calm: 0 });

  // Sync from backend state if available
  useEffect(() => {
    if (sourceData?.weights) setWeights(sourceData.weights);
    if (sourceData?.manual_override) {
      setOverrideActive(sourceData.manual_override.active);
      if (sourceData.manual_override.vector) setOverrideVector(sourceData.manual_override.vector);
    }
  }, [sourceData?.weights, sourceData?.manual_override]);

  const handleWeightChange = (key, value) => {
    const v = clamp01(parseFloat(value));
    const newWeights = { ...weights, [key]: v };
    setWeights(newWeights);
    sendControl('update_weights', newWeights);
  };

  const handleOverrideToggle = () => {
    const next = !overrideActive;
    setOverrideActive(next);
    sendControl('set_manual_override', { active: next, vector: overrideVector });
  };

  const handleVectorChange = (key, value) => {
    const v = clamp01(parseFloat(value));
    const vec = { ...overrideVector, [key]: v };
    setOverrideVector(vec);
    if (overrideActive) {
      sendControl('set_manual_override', { active: true, vector: vec });
    }
  };

  return (
    <div className="card-pixel">
      <h2>Director Controls</h2>
      <div className="panel-content" style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>

        <div>
          <h3 style={{ fontSize: '0.7rem', marginBottom: '0.4rem', color: 'var(--primary-purple)' }}>Source Weights</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr 40px', gap: '0.4rem', alignItems: 'center' }}>
            {['game_state', 'face', 'speech'].map((k) => (
              <React.Fragment key={k}>
                <label style={{ fontSize: '0.6rem', textTransform: 'capitalize' }}>{k.replace('_', ' ')}</label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={weights[k] ?? 0}
                  onChange={(e) => handleWeightChange(k, e.target.value)}
                />
                <span style={{ fontSize: '0.6rem' }}>{(weights[k] ?? 0).toFixed(2)}</span>
              </React.Fragment>
            ))}
          </div>
        </div>

        <div style={{ borderTop: '1px solid #444', paddingTop: '0.6rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
            <h3 style={{ fontSize: '0.7rem', color: 'var(--sun-orange)' }}>Manual Emotion Override</h3>
            <button
              className={`btn-pixel small ${overrideActive ? 'primary' : 'secondary'}`}
              onClick={handleOverrideToggle}
            >
              {overrideActive ? 'ACTIVE' : 'OFF'}
            </button>
          </div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 2fr 40px',
              gap: '0.4rem',
              alignItems: 'center',
              opacity: overrideActive ? 1 : 0.5,
              pointerEvents: overrideActive ? 'auto' : 'none'
            }}
          >
            {['tension', 'excitement', 'fear', 'joy', 'calm'].map((k) => (
              <React.Fragment key={k}>
                <label style={{ fontSize: '0.6rem', textTransform: 'capitalize' }}>{k}</label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={overrideVector[k] ?? 0}
                  onChange={(e) => handleVectorChange(k, e.target.value)}
                />
                <span style={{ fontSize: '0.6rem' }}>{(overrideVector[k] ?? 0).toFixed(2)}</span>
              </React.Fragment>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};

export default DirectorControls;

