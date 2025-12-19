import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // '/socket.io': {
      //   target: 'http://backend:8000', // Use the service name
      //   ws: true,
      //   changeOrigin: true // Important for websocket proxying
      // },
      // '/upload_music_dna': {
      //   target: 'http://backend:8000', // Use the service name
      //   changeOrigin: true
      // }
      '/socket.io': {
        target: 'http://localhost:8000',
        ws: true
      },
      '/upload_music_dna': {
        target: 'http://localhost:8000',
      }
    }
  }
})