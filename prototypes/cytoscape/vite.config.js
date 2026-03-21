import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    host: '0.0.0.0',  // expose to Windows host via WSL2 port forwarding
    port: 5173,
    proxy: {
      // Proxy /api to the local FastAPI backend (tools/api.py on port 8088)
      '/api': 'http://localhost:8088',
    },
  },
})
