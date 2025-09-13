import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const api = env.VITE_API_URL || 'http://localhost:8000'
  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        '/tts': {
          target: api,
          changeOrigin: true,
        },
        '/files': {
          target: api,
          changeOrigin: true,
        },
      },
    },
  }
})
