import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const EmotionGraph = ({ emotionVector }) => {
  const data = emotionVector ? Object.keys(emotionVector).map(key => ({
    name: key.charAt(0).toUpperCase() + key.slice(1),
    value: Math.round(emotionVector[key] * 100)
  })) : [];

  const colors = {
    Tension: '#FF6B57',
    Excitement: '#F6C12B',
    Fear: '#6E3DC7',
    Joy: '#FF3C88',
    Calm: '#3B82F6',
  };

  return (
    <div className="card-pixel">
      <h2>Live Emotion Graph</h2>
      <div className="panel-content" style={{ height: '300px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <XAxis type="number" domain={[0, 100]} stroke="var(--text-secondary)" />
            <YAxis type="category" dataKey="name" stroke="var(--text-secondary)" width={80} />
            <Tooltip
              cursor={{ fill: 'rgba(255,255,255,0.1)' }}
              contentStyle={{
                backgroundColor: 'var(--background-card)',
                borderColor: 'var(--primary-purple)'
              }}
            />
            <Bar dataKey="value" barSize={30}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={colors[entry.name]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default EmotionGraph;