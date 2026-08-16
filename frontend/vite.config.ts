import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  define: mode === 'e2e'
    ? { 'import.meta.env.VITE_API_BASE_URL': JSON.stringify('http://127.0.0.1:18000') }
    : undefined,
  server: mode === 'e2e'
    ? { proxy: { '/api': 'http://127.0.0.1:18000' } }
    : { proxy: { '/api': process.env.VITE_API_PROXY_TARGET ?? 'http://127.0.0.1:18005' } },
  preview: mode === 'e2e'
    ? { proxy: { '/api': 'http://127.0.0.1:18000' } }
    : { proxy: { '/api': process.env.VITE_API_PROXY_TARGET ?? 'http://127.0.0.1:18005' } },
}))
