import React, { useCallback, useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';

const DnaVisualizer = ({ audioInfo, dnaInfo }) => {
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);

  // Reset success message when audioInfo changes (new track uploaded)
  useEffect(() => {
    if (audioInfo?.current_track) {
      setUploadSuccess(true);
    }
  }, [audioInfo?.current_track]);

  const onDrop = useCallback(acceptedFiles => {
    setError('');
    setUploading(true);
    setUploadSuccess(false);
    const file = acceptedFiles[0];
    if (file) {
      const formData = new FormData();
      formData.append('file', file);
      
      // Use absolute URL to ensure proper routing
      const backendUrl = `${window.location.protocol}//${window.location.hostname}:8000/upload_music_dna/`;
      
      console.log(`Uploading file to ${backendUrl}`);
      fetch(backendUrl, {
        method: 'POST',
        body: formData,
      })
      .then(response => {
        if (!response.ok) {
          throw new Error(`Server responded with ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        setUploading(false);
        if(data.error) {
          setError(data.error);
        } else {
          setUploadSuccess(true);
          console.log('Upload success:', data);
        }
      })
      .catch(err => {
        setUploading(false);
        console.error('Upload error:', err);
        setError(`Upload failed: ${err.message || 'See console for details'}`);
      });
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'audio/*': ['.mp3', '.wav', '.ogg'] },
    multiple: false,
  });
  
  const info = dnaInfo?.info || {};

  return (
    <div className="card-pixel">
      <h2>Music DNA</h2>
      <div className="panel-content">
        <div {...getRootProps()} className="dropzone">
          <input {...getInputProps()} />
          {isDragActive ? <p>Drop the music here ...</p> : <p>Drag 'n' drop music file here, or click to select</p>}
        </div>
        {uploading && <p style={{color: 'var(--primary-purple)', marginTop: '1rem'}}>Uploading...</p>}
        {error && <p style={{color: 'var(--sun-orange)', marginTop: '1rem'}}>{error}</p>}
        {uploadSuccess && <p style={{color: 'var(--primary-green)', marginTop: '1rem'}}>Upload successful! Click play in the Adaptive Music panel.</p>}
        <div className="dna-info">
          <h3>Track: <span>{audioInfo?.current_track || 'N/A'}</span></h3>
          <h3>Tempo: <span>{audioInfo?.tempo_bpm || 0} BPM</span></h3>
          <h3>Key Emotion: <span>{audioInfo?.primary_emotion || 'N/A'}</span></h3>
          {info.duration_seconds && <h3>Duration: <span>{info.duration_seconds.toFixed(1)}s</span></h3>}
        </div>
      </div>
    </div>
  );
};

export default DnaVisualizer;