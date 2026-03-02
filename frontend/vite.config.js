import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../static',
    emptyOutDir: false,   // preserve login.html, register.html, style.css, app.js
  },
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:5099",
        changeOrigin: true,
      },
    },
  },
})
