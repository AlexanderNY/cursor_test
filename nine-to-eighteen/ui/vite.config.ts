import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  // Workers dynamic-import pyodide / sql.js, which code-splits. IIFE cannot
  // emit multiple chunks; both workers are already constructed as modules.
  worker: {
    format: 'es',
  },
  optimizeDeps: {
    exclude: ['pyodide', 'sql.js'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 8200,
    host: '0.0.0.0',
    allowedHosts: [
      'localhost',
      '.9to18.ru',
    ],
    proxy: {
      '/api/resume': {
        target: process.env.VITE_RESUME_API_URL || 'http://127.0.0.1:8021',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
        timeout: 90_000,
        proxyTimeout: 90_000,
      },
      '/api/portfolio': {
        target: process.env.VITE_PORTFOLIO_API_URL || 'http://127.0.0.1:8022',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/api': {
        target: process.env.VITE_SITE_API_URL || 'http://127.0.0.1:8020',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  preview: {
    port: 8200,
    host: '0.0.0.0',
  },
})
