import { useState, useEffect, useRef } from 'react';

// Resolve a default WS URL based on current host if not provided
const resolveUrl = (url) => {
  if (url) return url;
  const host = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
  const port = 8000;
  return `ws://${host}:${port}/ws/studio`;
};

const useAuraSocket = (url) => {
  const [isConnected, setIsConnected] = useState(false);
  const [auraData, setAuraData] = useState(null);
  const socket = useRef(null);

  useEffect(() => {
    const wsUrl = resolveUrl(url);
    socket.current = new WebSocket(wsUrl);

    socket.current.onopen = () => {
      console.log('Studio WebSocket Connected');
      setIsConnected(true);
    };

    socket.current.onclose = () => {
      console.log('Studio WebSocket Disconnected');
      setIsConnected(false);
    };

    socket.current.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        switch (message.type) {
          case 'aura_update': {
            // Ensure we maintain nested objects (source_data, audio, etc.)
            setAuraData(prev => ({
              ...prev,
              final_emotion_vector: message.payload.final_emotion_vector,
              source_data: message.payload.source_data,
              audio: {
                ...prev?.audio,
                ...message.payload.audio
              }
            }));
            break;
          }
          case 'dna_loaded': {
            setAuraData(prev => ({ ...prev, dna_info: message.payload }));
            break;
          }
          case 'vote_ack': {
            // Optionally reflect updated tally quickly
            setAuraData(prev => ({
              ...prev,
              source_data: {
                ...prev?.source_data,
                audience_votes: {
                  ...prev?.source_data?.audience_votes,
                  [message.payload.mood]: message.payload.tally
                }
              }
            }));
            break;
          }
          case 'face_frame': {
            setAuraData(prev => ({
              ...prev,
              source_data: {
                ...prev?.source_data,
                face_frame: `data:image/jpeg;base64,${message.payload.frame}`
              }
            }));
            break;
          }
          default:
            // Other message types (errors, etc.)
            break;
        }
      } catch (error) {
        console.error('Error parsing message:', error);
      }
    };

    socket.current.onerror = (error) => {
      console.error('WebSocket Error:', error);
    };

    return () => {
      socket.current.close();
    };
  }, [url]);

  const sendVote = (mood) => {
    if (socket.current && socket.current.readyState === WebSocket.OPEN) {
      socket.current.send(JSON.stringify({
        type: 'audience_vote',
        payload: { mood }
      }));
    }
  };

  const sendControl = (type, payload) => {
    if (socket.current && socket.current.readyState === WebSocket.OPEN) {
      socket.current.send(JSON.stringify({ type, payload }));
    }
  };

  return { isConnected, auraData, sendVote, sendControl };
};

export default useAuraSocket;