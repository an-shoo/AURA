import React, { useState, useEffect } from 'react';

/**
 * AudiencePollingBoard: A Twitch-style audience polling launcher.
 * Currently non-weighted (server ignores / treats audience votes weight=0) – strictly engagement.
 * Provides:
 *  - Quick link & QR (future) for viewers
 *  - Real-time tally display (reusing votes passed from parent props if desired later)
 *  - Popup overlay that could embed a separate audience web page (placeholder iframe slot)
 */
const AudiencePollingBoard = ({ audienceUrl }) => {
  const [open, setOpen] = useState(false);
  const resolvedUrl = audienceUrl || `${window.location.protocol}//${window.location.hostname}:5173/audience.html`;
  const [copied, setCopied] = useState(false);

  // Close on Escape
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') setOpen(false); };
    if (open) window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open]);

  return (
    <div className="card-pixel">
      <h2>Audience Polling Board</h2>
      <div className="panel-content" style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
        <p style={{ fontSize: '0.65rem', lineHeight: 1.2 }}>
          Launch a viewer-facing poll page. Votes here are engagement-only (0 weight) – they do not alter live music yet.
        </p>
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button className="btn-pixel primary" onClick={() => setOpen(true)}>Open Poll Overlay</button>
          <a href={resolvedUrl} target="_blank" rel="noreferrer" className="btn-pixel secondary" style={{ textDecoration: 'none' }}>Open in New Tab</a>
          <button
            className="btn-pixel secondary"
            onClick={() => { navigator.clipboard.writeText(resolvedUrl).then(()=>{setCopied(true); setTimeout(()=>setCopied(false),1500);}); }}
          >{copied ? 'Copied!' : 'Copy Link'}</button>
        </div>
        <small style={{ opacity: 0.7 }}>Press ESC to close overlay.</small>
      </div>
      {open && (
        <div
          className="overlay-poll"
          style={{
            position: 'fixed', inset: 0, background: 'rgba(10,8,20,0.92)',
            zIndex: 4000, display: 'flex', flexDirection: 'column', padding: '1rem'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 style={{ margin: 0 }}>Audience Polling</h2>
            <button
              className="btn-pixel secondary small"
              onClick={() => setOpen(false)}
            >✕ Close</button>
          </div>
          <div style={{ flex: 1, marginTop: '0.75rem', border: '2px solid var(--primary-purple)', padding: 0, overflow: 'hidden', position:'relative' }}>
            <iframe
              title="Audience Poll"
              src={resolvedUrl}
              style={{ width: '100%', height: '100%', border: 'none', background: '#0e0b17' }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default AudiencePollingBoard;