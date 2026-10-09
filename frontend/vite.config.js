import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Proxy API calls to the FastAPI backend during development
      '/auth':       { target: 'http://localhost:8000', changeOrigin: true },
      '/metrics':    { target: 'http://localhost:8000', changeOrigin: true },
      '/servers':    { target: 'http://localhost:8000', changeOrigin: true },
      '/predictions':{ target: 'http://localhost:8000', changeOrigin: true },
      '/alerts':     { target: 'http://localhost:8000', changeOrigin: true },
      '/health':     { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})
