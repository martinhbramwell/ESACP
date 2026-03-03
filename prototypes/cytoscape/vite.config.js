import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    host: '0.0.0.0',  // expose to Windows host via WSL2 port forwarding
    port: 5173,
  },
})
