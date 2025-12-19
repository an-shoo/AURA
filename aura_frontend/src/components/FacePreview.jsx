import React, { useEffect, useRef, useState } from 'react';

/**
 * FacePreview: purely a local browser webcam preview (not used for backend emotion;
 * that still comes from Python DeepFace script). Gives audience/director visual feedback.
 */
const FacePreview = () => {
  const videoRef = useRef(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let stream;
    navigator.mediaDevices.getUserMedia({ video: true }).then(s => {
      stream = s;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    }).catch(err => {
      setError(err.message || 'Camera access denied');
    });
    return () => {
      if (stream) stream.getTracks().forEach(t => t.stop());
    };
  }, []);

  return (
    <div className="card-pixel" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      <h2>Face Preview</h2>
      {error ? (
        <div style={{ color: 'var(--accent-red)', fontSize: '0.75rem' }}>
          Camera Error: {error}<br />
          <span style={{ opacity: 0.7 }}>
            Tip: If the Python face sensor is using the webcam exclusively, close it or start this preview first.
          </span>
        </div>
      ) : (
        <video ref={videoRef} autoPlay playsInline style={{ width: '100%', border: '1px solid var(--primary-purple)' }} />
      )}
      <p style={{ fontSize: '0.65rem', opacity: 0.7 }}>
        This preview is local. Emotion analysis still comes from the Python sensor script.
      </p>
    </div>
  );
};

export default FacePreview;
