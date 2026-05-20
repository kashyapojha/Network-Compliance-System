import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.resolve(__dirname, '..')

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, repoRoot, '')
  const proxyTarget = env.VITE_DEV_API_PROXY || env.BACKEND_URL || 'http://127.0.0.1:5000'

  return {
    plugins: [react()],
    envDir: repoRoot,
    server: {
      port: Number(env.VITE_DEV_PORT || 3000),
      proxy: {
        '/api': {
          target: proxyTarget,
          changeOrigin: true,
        },
      },
    },
  }
})
