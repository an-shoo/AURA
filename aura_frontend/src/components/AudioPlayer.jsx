import React, { useEffect, useRef, useState } from 'react';

/**
 * AudioPlayer: streams (actually just plays locally) the uploaded DNA track and
 * adjusts playbackRate based on aura tempo modulation. To satisfy browser
 * autoplay policies, user m      });
  };

  // Auto-boost: if user started, context running, RMS stays below -50 dB for >3s, raise boost gradually up to 4x.
  useEffect(() => {
    if (!userStarted) return;
    if (rms === null) return;
    if (rms > -50) return; // signal already okay
    const t = setTimeout(() => {
      setBoost(prev => prev < 4 ? Math.min(4, prev * 1.5) : prev);
    }, 3000);
    return () => clearTimeout(t);
  }, [rms, userStarted]);nce; after that we can update rate.
 */
const AudioPlayer = ({ audio }) => {
  const audioRef = useRef(null);
  const audioCtxRef = useRef(null);
  const gainNodeRef = useRef(null);
  const filterNodeRef = useRef(null);
  const sourceNodeRef = useRef(null);
  const analyserRef = useRef(null);
  const meterReqRef = useRef(null);
  const [rms, setRms] = useState(-120);
  const [boost, setBoost] = useState(1.0);
  const [bypass, setBypass] = useState(false);
  const [userStarted, setUserStarted] = useState(false);
  const [ready, setReady] = useState(false);
  const [volume, setVolume] = useState(1.0);
  const [effectiveGain, setEffectiveGain] = useState(1.0);
  const [lastTrackUrl, setLastTrackUrl] = useState(null);
  const [audioLoaded, setAudioLoaded] = useState(false);

  // Prefer fully-qualified URL from backend; fallback to relative path.
  const trackUrl = audio?.full_track_url || (audio?.track_url ? resolveRelative(audio?.track_url) : null);
  const tempoMultiplier = audio?.tempo_multiplier || 1.0;

  function resolveRelative(rel) {
    if (!rel) return null;
    if (/^https?:\/\//i.test(rel)) return rel;
    // Assume backend on same host but port 8000; could be env driven later.
    const backend = `${window.location.protocol}//${window.location.hostname}:8000`;
    return backend + rel;
  }

  useEffect(() => {
    if (!audioRef.current) return;

    // If a new track arrives, load it (but don't auto-play unless already user-initiated)
    if (trackUrl && trackUrl !== lastTrackUrl) {
      setReady(false);
      setAudioLoaded(false);
      
      console.log(`[AudioPlayer] Loading new track: ${trackUrl}`);
      audioRef.current.src = trackUrl;
      audioRef.current.load();
      setLastTrackUrl(trackUrl);
      
      audioRef.current.oncanplay = () => {
        setReady(true);
        setAudioLoaded(true);
        console.log('[AudioPlayer] canplay', { trackUrl });
        if (userStarted) {
          audioRef.current.play()
            .then(() => console.log('[AudioPlayer] autoplay after canplay success'))
            .catch(err => console.warn('Play attempt failed after canplay:', err));
        }
      };
      
      audioRef.current.onplay = () => console.log('[AudioPlayer] onplay, currentTime=', audioRef.current.currentTime);
      audioRef.current.onpause = () => console.log('[AudioPlayer] onpause');
      audioRef.current.onerror = (e) => {
        console.error('Audio element error loading track', trackUrl, e, audioRef.current.error);
        if (audioRef.current.error) {
          console.error('Error code:', audioRef.current.error.code);
          console.error('Error message:', audioRef.current.error.message);
        }
      };
    }
  }, [trackUrl, lastTrackUrl, userStarted]);

  // Initialize Web Audio graph after user interaction (play click)
  function ensureGraph() {
    if (audioCtxRef.current) return;
    
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const gainNode = ctx.createGain();
      const filterNode = ctx.createBiquadFilter();
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 2048;
      analyser.smoothingTimeConstant = 0.5;
      filterNode.type = 'lowpass';
      gainNode.gain.value = 1.0;
      filterNode.frequency.value = 5000;
      const src = ctx.createMediaElementSource(audioRef.current);
      // Chain: src -> filter -> gain -> analyser -> destination
      src.connect(filterNode);
      filterNode.connect(gainNode);
      gainNode.connect(analyser);
      analyser.connect(ctx.destination);
      audioCtxRef.current = ctx;
      gainNodeRef.current = gainNode;
      filterNodeRef.current = filterNode;
      sourceNodeRef.current = src;
      analyserRef.current = analyser;

      // Start meter loop
      const updateMeter = () => {
        if (!analyserRef.current) return;
        const a = analyserRef.current;
        const buf = new Float32Array(a.fftSize);
        a.getFloatTimeDomainData(buf);
        let sum = 0;
        for (let i=0;i<buf.length;i++) sum += buf[i]*buf[i];
        const mean = sum / buf.length;
        const rmsVal = Math.sqrt(mean);
        const db = 20 * Math.log10(rmsVal || 1e-8);
        setRms(db);
        meterReqRef.current = requestAnimationFrame(updateMeter);
      };
      updateMeter();
      
      console.log('[AudioPlayer] Web Audio graph initialized successfully');
      return true;
    } catch (err) {
      console.error('[AudioPlayer] Failed to initialize Web Audio graph:', err);
      return false;
    }
  }

  useEffect(() => {
    if (!audioRef.current) return;
    // Smoothly adjust playback rate (simple approach)
    const target = Math.max(0.5, Math.min(2.0, tempoMultiplier));
    audioRef.current.playbackRate = target; // Could interpolate if desired
  }, [tempoMultiplier]);

  // React to modulation metadata (gain + filter cutoff)
  useEffect(() => {
    if (!audio?.modulation) return;
    if (!audioRef.current) return;
    if (!audioCtxRef.current) return; // graph not ready until user plays
    const { gain, filter_cutoff_hz } = audio.modulation;
    if (gainNodeRef.current) {
      const targetGain = (bypass ? 1.0 : gain) * volume * boost;
      gainNodeRef.current.gain.linearRampToValueAtTime(targetGain, audioCtxRef.current.currentTime + 0.25);
      setEffectiveGain(targetGain);
    } else {
      setEffectiveGain((audio.modulation?.gain ?? 1) * volume * (audioRef.current?.volume ?? 1));
    }
    if (filterNodeRef.current) {
      const cutoff = bypass ? 20000 : filter_cutoff_hz;
      filterNodeRef.current.frequency.linearRampToValueAtTime(cutoff, audioCtxRef.current.currentTime + 0.25);
    }
  }, [audio?.modulation, volume, boost, bypass]);

  // Volume slider manual override
  useEffect(() => {
    if (gainNodeRef.current && audioCtxRef.current) {
      const baseGain = audio?.modulation?.gain ?? 1.0;
      const val = (bypass ? 1.0 : baseGain) * volume * boost;
      gainNodeRef.current.gain.setValueAtTime(val, audioCtxRef.current.currentTime);
      setEffectiveGain(val);
    } else if (audioRef.current) {
      audioRef.current.volume = volume; // fallback if graph not ready
    }
  }, [volume, audio?.modulation, boost, bypass]);

  const handlePlayClick = () => {
    if (!audioRef.current) return;
    
    console.log('[AudioPlayer] Play button clicked');
    
    // Initialize Web Audio context first
    const graphInitialized = ensureGraph();
    if (!graphInitialized) {
      console.warn('[AudioPlayer] Could not initialize audio graph, trying native audio element playback');
    }
    
    // Try to play the audio
    audioRef.current.play()
      .then(() => {
        console.log('[AudioPlayer] Audio playback started successfully');
        setUserStarted(true);
        // Resume context if suspended
        if (audioCtxRef.current?.state === 'suspended') {
          audioCtxRef.current.resume()
            .then(() => console.log('[AudioPlayer] Audio context resumed'))
            .catch(err => console.warn('[AudioPlayer] Failed to resume audio context:', err));
        }
      })
      .catch(err => {
        console.warn('[AudioPlayer] Play failed (autoplay?):', err);
        
        // Fallback: Try to play a silent audio to unblock audio context
        try {
          const silentCtx = new (window.AudioContext || window.webkitAudioContext)();
          const silent = silentCtx.createOscillator();
          silent.connect(silentCtx.destination);
          silent.start();
          silent.stop(silentCtx.currentTime + 0.001);
          
          // Try again after silent audio
          setTimeout(() => {
            if (audioRef.current) {
              audioRef.current.play()
                .then(() => {
                  console.log('[AudioPlayer] Second play attempt succeeded');
                  setUserStarted(true);
                })
                .catch(err => console.error('[AudioPlayer] Second play attempt failed:', err));
            }
          }, 100);
        } catch (e) {
          console.error('[AudioPlayer] Silent audio fallback failed:', e);
        }
      });
    
    // Additional fallback retry after a delay
    setTimeout(() => {
      if (audioRef.current && audioRef.current.paused) {
        console.log('[AudioPlayer] Retrying play after initial attempt');
        audioRef.current.play().catch(err => console.warn('[AudioPlayer] Retry play failed:', err));
      }
    }, 1000);
  };

  const handleForcePlay = () => {
    if (!audioRef.current) return;
    
    // Try to unblock audio context
    if (audioCtxRef.current?.state === 'suspended') {
      audioCtxRef.current.resume()
        .then(() => console.log('[AudioPlayer] Audio context forced resume'))
        .catch(err => console.warn('[AudioPlayer] Force resume failed:', err));
    }
    
    // Try to play audio directly
    audioRef.current.play()
      .then(() => console.log('[AudioPlayer] Force play succeeded'))
      .catch(err => console.warn('[AudioPlayer] Force play failed:', err));
      
    // Set user started flag
    setUserStarted(true);
  };

  const spawnTestTone = () => {
    try {
      ensureGraph();
      const ctx = audioCtxRef.current;
      const osc = ctx.createOscillator();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(440, ctx.currentTime);
      const gainNode = ctx.createGain();
      gainNode.gain.setValueAtTime(0.1, ctx.currentTime);
      osc.connect(gainNode).connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 1.0);
      console.log('[AudioPlayer] Played 1s test tone (A4)');
    } catch (e) {
      console.warn('Test tone failed', e);
    }
  };

  const audioEl = audioRef.current;
  const readyStateMap = ['HAVE_NOTHING','HAVE_METADATA','HAVE_CURRENT_DATA','HAVE_FUTURE_DATA','HAVE_ENOUGH_DATA'];

  // Auto-boost: if user started, context running, RMS stays below -50 dB for >3s, raise boost gradually up to 4x.
  useEffect(() => {
    if (!userStarted) return;
    if (rms === null) return;
    if (rms > -50) return; // signal already okay
    const t = setTimeout(() => {
      setBoost(prev => prev < 4 ? Math.min(4, prev * 1.5) : prev);
    }, 3000);
    return () => clearTimeout(t);
  }, [rms, userStarted]);

  return (
    <div className="card-pixel" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      <h2>Adaptive Music</h2>
      {trackUrl ? (
        <>
          <div style={{ fontSize: '0.8rem', opacity: 0.8 }}>
            Track: <b>{audio?.current_track}</b><br />
            Base Tempo: {audio?.base_tempo} BPM | Target: {audio?.tempo_bpm} BPM<br />
            Rate: x{(audio?.tempo_multiplier || 1).toFixed(2)} | Emotion: {audio?.primary_emotion}<br />
            Mod Gain: {audio?.modulation?.gain ?? '-'} | LPF: {audio?.modulation?.filter_cutoff_hz ?? '-'} Hz
          </div>
          <audio 
            ref={audioRef} 
            src={trackUrl}
            loop 
            style={{ display: 'none' }} 
            preload="auto"
            crossOrigin="anonymous"
          />
          <div className="aura-audio-controls" style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
            {!userStarted && (
              <button
                onClick={handlePlayClick}
                className="btn-pixel primary"
                style={{ padding: '12px 18px' }}
              >
                {ready ? '► Start Music' : 'Load & Start'}
              </button>
            )}
            {userStarted && (
              <button
                onClick={() => audioRef.current?.paused ? audioRef.current.play() : audioRef.current.pause()}
                className={`btn-pixel small ${audioRef.current?.paused ? 'primary' : 'secondary'}`}
              >
                {audioRef.current?.paused ? '► Play' : '❚❚ Pause'}
              </button>
            )}
            <label style={{ fontSize: '0.6rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              Vol
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={volume}
                onChange={e => setVolume(parseFloat(e.target.value))}
                style={{ width: '80px' }}
              />
            </label>
            {!ready && trackUrl && <span style={{ fontSize: '0.6rem', opacity: 0.7 }}>loading...</span>}
          </div>
        </>
      ) : (
        <p style={{ fontSize: '0.8rem' }}>Upload a music DNA file to enable playback.</p>
      )}
    </div>
  );
};

export default AudioPlayer;
