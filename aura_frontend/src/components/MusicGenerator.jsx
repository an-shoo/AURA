import React, { useState, useRef } from 'react';

/* global mm */ // for Magenta global if loaded via script tag (fallback)

/**
 * MusicGenerator: lightweight Magenta MusicVAE client-side generation box.
 * Strategy:
 *  - Load @magenta/music dynamically (ESM import handled by bundler) OR rely on window.mm if script tag added.
 *  - Provide model choices & temperature.
 *  - Generate a NoteSequence; preview via simple WebAudio synth (manual) to avoid heavy Tone.js dependency.
 *  - Allow export to MIDI (Blob) and naive WAV render (sine stub) for quick DNA upload.
 *    (True multi-timbral rendering would need a small synth engine – kept simple here.)
 */
// Note: the original mel_4bar_med URL returns 404; use the q2 checkpoint instead.
const MODEL_MAP = {
  'mel_2bar_small': 'https://storage.googleapis.com/magentadata/js/checkpoints/music_vae/mel_2bar_small',
  'mel_4bar_med': import.meta?.env?.VITE_MVAE_MEL4_URL
    || 'https://storage.googleapis.com/magentadata/js/checkpoints/music_vae/mel_4bar_med_q2',
  'trio_4bar': 'https://storage.googleapis.com/magentadata/js/checkpoints/music_vae/trio_4bar'
};

const seedMelodies = {
  twinkle: [60,60,67,67,69,69,67,65,65,64,64,62,62,60],
  happy: [60,60,62,60,65,64,60,60,62,60,67,65],
  scale: [60,62,64,65,67,69,71,72],
  custom: [60,62,64,65,67]
};

function buildSeedSequence(pitches) {
  const stepsPerQuarter = 4;
  const seq = {
    quantizationInfo: { stepsPerQuarter },
    totalQuantizedSteps: pitches.length * 4,
    timeSignatures: [{ time: 0, numerator: 4, denominator: 4 }],
    tempos: [{ time: 0, qpm: 120 }],
    notes: []
  };
  pitches.forEach((p, i) => {
    seq.notes.push({ pitch: p, quantizedStartStep: i*4, quantizedEndStep: i*4 + 4, velocity: 80 });
  });
  return seq;
}

const MusicGenerator = ({ onExportWav }) => {
  const [modelName, setModelName] = useState('mel_2bar_small');
  const [temperature, setTemperature] = useState(1.0);
  const [seedType, setSeedType] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('Idle');
  const [sequence, setSequence] = useState(null);
  const modelRef = useRef(null);
  const audioCtxRef = useRef(null);
  const activeOscsRef = useRef([]);

  async function ensureModel() {
    if (modelRef.current && modelRef.current.checkpointURL === MODEL_MAP[modelName]) return modelRef.current;
    setStatus('Loading model...');
    // Some Magenta modules reference global (Node pattern). Polyfill if absent.
    if (typeof window !== 'undefined' && typeof window.global === 'undefined') {
      // eslint-disable-next-line no-undef
      window.global = window; // minimal shim
    }
    const mod = await import('@magenta/music');
    const m = new mod.MusicVAE(MODEL_MAP[modelName]);
    await m.initialize();
    modelRef.current = m;
    return m;
  }

  async function handleGenerate() {
    try {
      setLoading(true);
      setStatus('Initializing...');
      const m = await ensureModel();
      let seed = null;
      if (seedType && seedMelodies[seedType]) seed = buildSeedSequence(seedMelodies[seedType]);
      setStatus('Sampling...');
      const samples = await m.sample(1, temperature, seed || undefined);
      setSequence(samples[0]);
      setStatus(`Generated ${samples[0].notes.length} notes (~${samples[0].totalTime?.toFixed?.(1) || '?'}s)`);
    } catch (e) {
      console.error(e);
      setStatus('Error: ' + e.message);
    } finally {
      setLoading(false);
    }
  }

  function stopPreview() {
    activeOscsRef.current.forEach(o => { try { o.stop(); } catch (_) {} });
    activeOscsRef.current = [];
  }

  function playPreview() {
    if (!sequence) return;
    stopPreview();
    if (!audioCtxRef.current) audioCtxRef.current = new (window.AudioContext || window.webkitAudioContext)();
    const ctx = audioCtxRef.current;
    const startTime = ctx.currentTime + 0.05;
    const qpm = (sequence.tempos && sequence.tempos[0]?.qpm) || 120;
    const spq = 60 / qpm; // seconds per quarter
    sequence.notes.forEach(n => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      const freq = 440 * Math.pow(2, (n.pitch - 69)/12);
      const durQ = (n.quantizedEndStep - n.quantizedStartStep)/4; // stepsPerQuarter=4
      const start = startTime + (n.quantizedStartStep/4)*spq;
      const end = start + durQ*spq;
      osc.frequency.value = freq;
      osc.type = 'triangle';
      gain.gain.setValueAtTime(0, start);
      gain.gain.linearRampToValueAtTime(0.25, start + 0.01);
      gain.gain.linearRampToValueAtTime(0.0001, end);
      osc.connect(gain).connect(ctx.destination);
      osc.start(start);
      osc.stop(end + 0.05);
      activeOscsRef.current.push(osc);
    });
    setStatus('Preview playing... (synthetic)');
    // Auto cleanup
    setTimeout(() => stopPreview(), (sequence.totalTime || 8) * 1000 + 500);
  }

  function exportMidi() {
    if (!sequence) return;
    import('@magenta/music').then(mod => {
      const bytes = mod.sequenceProtoToMidi(sequence);
      const blob = new Blob([bytes], { type: 'audio/midi' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = 'generated.mid'; a.click();
      URL.revokeObjectURL(url);
    });
  }

  async function exportWav(uploadDirect=false) {
    if (!sequence) return;
    // Simple offline render: mix sine voices (approx) -> WAV for upload.
    const sampleRate = 44100;
    const qpm = (sequence.tempos && sequence.tempos[0]?.qpm) || 120;
    const spq = 60 / qpm;
    const totalSeconds = Math.max(4, sequence.totalTime || 4);
    const length = Math.ceil(totalSeconds * sampleRate);
    const buffer = new Float32Array(length);
    sequence.notes.forEach(n => {
      const startSec = (n.quantizedStartStep/4)*spq;
      const endSec = (n.quantizedEndStep/4)*spq;
      const freq = 440 * Math.pow(2, (n.pitch - 69)/12);
      for (let t = Math.floor(startSec * sampleRate); t < Math.min(length, Math.floor(endSec * sampleRate)); t++) {
        const env = Math.min(1, (t - startSec*sampleRate)/ (0.01*sampleRate)) * // attack
                    Math.max(0, 1 - (t - startSec*sampleRate)/( (endSec-startSec)*sampleRate));
        buffer[t] += Math.sin(2*Math.PI*freq * (t/sampleRate)) * 0.15 * env;
      }
    });
    // Normalize
    let peak = 0; for (let i=0;i<buffer.length;i++) peak = Math.max(peak, Math.abs(buffer[i]));
    if (peak > 0) { const g = 0.95/peak; for (let i=0;i<buffer.length;i++) buffer[i]*=g; }
    // Encode WAV (16-bit PCM)
    const wavBytes = encodeWav(buffer, sampleRate);
    const blob = new Blob([wavBytes], { type: 'audio/wav' });
    if (uploadDirect) {
      try {
        setStatus('Uploading generated WAV...');
        const form = new FormData();
        form.append('file', blob, 'generated.wav');
        const backendUrl = `${window.location.protocol}//${window.location.hostname}:8000/upload_music_dna/`;
        const resp = await fetch(backendUrl, { method: 'POST', body: form });
        if (!resp.ok) throw new Error('Upload failed ' + resp.status);
        setStatus('Uploaded & DNA updated. Switch to Adaptive Music to play.');
      } catch (e) {
        console.error(e);
        setStatus('Upload error: ' + e.message);
      }
    } else {
      if (onExportWav) onExportWav(blob);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = 'generated.wav'; a.click();
      URL.revokeObjectURL(url);
      setStatus('Exported WAV (sine mix) – you can now upload as DNA.');
    }
  }

  return (
    <div className="card-pixel">
      <h2>AI Music Generator</h2>
      <div className="panel-content" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <label style={{ fontSize: '0.6rem' }}>Model:
          <select className="select-pixel" value={modelName} onChange={e => setModelName(e.target.value)} style={{ marginLeft: '0.5rem' }}>
            <option value="mel_2bar_small">2-bar Melody (fast)</option>
            <option value="mel_4bar_med">4-bar Melody (med)</option>
            <option value="trio_4bar">4-bar Trio (band)</option>
          </select>
        </label>
        <label style={{ fontSize: '0.6rem' }}>Temperature: {temperature.toFixed(1)}
          <input type="range" min={0.1} max={2} step={0.1} value={temperature} onChange={e => setTemperature(parseFloat(e.target.value))} style={{ width: '100%' }} />
        </label>
        <label style={{ fontSize: '0.6rem' }}>Seed Melody:
          <select className="select-pixel" value={seedType} onChange={e => setSeedType(e.target.value)} style={{ marginLeft: '0.5rem' }}>
            <option value="">Random</option>
            <option value="twinkle">Twinkle</option>
            <option value="happy">Happy Birthday</option>
            <option value="scale">C Major Scale</option>
            <option value="custom">Custom (C D E F G)</option>
          </select>
        </label>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.6rem' }}>
          <button disabled={loading} className="btn-pixel primary" onClick={handleGenerate}>Generate</button>
          <button disabled={!sequence} className="btn-pixel secondary" onClick={playPreview}>Preview</button>
          <button disabled={!sequence} className="btn-pixel secondary" onClick={exportMidi}>Export MIDI</button>
          <button disabled={!sequence} className="btn-pixel secondary" onClick={() => exportWav(false)}>Export WAV</button>
          <button disabled={!sequence} className="btn-pixel primary" onClick={() => exportWav(true)}>Upload DNA</button>
          <button disabled={!sequence} className="btn-pixel secondary" onClick={stopPreview}>Stop Preview</button>
        </div>
        <div style={{ fontSize: '0.6rem', minHeight: '1.2rem' }}>{status}</div>
        {sequence && (
          <div style={{ fontSize: '0.55rem', opacity: 0.8 }}>
            Notes: {sequence.notes.length} | Est Time: ~{sequence.totalTime?.toFixed?.(1) || '?'}s | Pitch Range: {
              (() => {
                const ps = sequence.notes.map(n => n.pitch); return Math.min(...ps) + '–' + Math.max(...ps);
              })()
            }
          </div>
        )}
      </div>
    </div>
  );
};

// --- WAV Encoder Utility (16-bit PCM) ---
function encodeWav(float32Array, sampleRate) {
  const numFrames = float32Array.length;
  const buffer = new ArrayBuffer(44 + numFrames * 2);
  const view = new DataView(buffer);
  function writeStr(offset, str) { for (let i=0;i<str.length;i++) view.setUint8(offset+i, str.charCodeAt(i)); }
  let offset = 0;
  writeStr(offset, 'RIFF'); offset+=4;
  view.setUint32(offset, 36 + numFrames*2, true); offset+=4;
  writeStr(offset, 'WAVE'); offset+=4;
  writeStr(offset, 'fmt '); offset+=4;
  view.setUint32(offset, 16, true); offset+=4; // PCM chunk size
  view.setUint16(offset, 1, true); offset+=2; // audio format PCM
  view.setUint16(offset, 1, true); offset+=2; // channels
  view.setUint32(offset, sampleRate, true); offset+=4;
  view.setUint32(offset, sampleRate * 2, true); offset+=4; // byte rate
  view.setUint16(offset, 2, true); offset+=2; // block align
  view.setUint16(offset, 16, true); offset+=2; // bits per sample
  writeStr(offset, 'data'); offset+=4;
  view.setUint32(offset, numFrames*2, true); offset+=4;
  for (let i=0;i<numFrames;i++) {
    let s = Math.max(-1, Math.min(1, float32Array[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    offset += 2;
  }
  return buffer;
}

export default MusicGenerator;