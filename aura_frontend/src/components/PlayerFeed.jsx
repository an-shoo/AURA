import React, { useEffect, useRef, useState } from 'react';

const PlayerFeed = ({ sourceData }) => {
  const face = sourceData?.face_emotion || { emotion: 'N/A', confidence: 0 };
  const speech = sourceData?.speech_emotion || { emotion: 'N/A', confidence: 0 };
  // Full-frame (with bounding box) coming from sensor
  const faceFrame = sourceData?.face_frame; // data URL
  const canvasRef = useRef(null);
  const lastFrameRef = useRef(null); // keep previous frame if momentary gap
  const [meta, setMeta] = useState(null);

  useEffect(() => {
    if (!faceFrame) return; // keep last frame displayed
    const img = new Image();
    img.onload = () => {
      lastFrameRef.current = img; // store
      if (!canvasRef.current) return;
      const ctx = canvasRef.current.getContext('2d');
      if (canvasRef.current.width !== img.width || canvasRef.current.height !== img.height) {
        canvasRef.current.width = img.width;
        canvasRef.current.height = img.height;
      }
      ctx.imageSmoothingEnabled = false;
      ctx.drawImage(img, 0, 0, img.width, img.height);
    };
    img.src = faceFrame;
  }, [faceFrame]);

  // If meta data embedded (width/height/fps) we could show fps overlay (coming through orchestrator not yet). For now attempt to parse from URL length heuristics is overkill; skip.

  return (
    <div className="card-pixel">
      <h2>Player Input</h2>
      <div className="panel-content" style={{ gap: '0.5rem' }}>
        <div className="player-feed-cam" style={{ position: 'relative', width: '100%' }}>
          {lastFrameRef.current || faceFrame ? (
            <canvas
              ref={canvasRef}
              style={{
                width: '100%',
                display: 'block',
                border: '1px solid var(--primary-purple)',
                imageRendering: 'pixelated'
              }}
            />
          ) : (
            <div style={{ fontSize: '0.7rem', opacity: 0.7 }}>[ Awaiting Face Frames ]</div>
          )}
        </div>
        <div className="emotion-readout">
          <h3>Face: <span>{face.emotion}</span> ({(face.confidence * 100).toFixed(1)}%)</h3>
          <h3>Speech: <span>{speech.emotion}</span> ({(speech.confidence * 100).toFixed(1)}%)</h3>
        </div>
      </div>
    </div>
  );
};

export default PlayerFeed;