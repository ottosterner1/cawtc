// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    cors: true,
    origin: 'http://localhost:5173',
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  },
  build: {
    outDir: '../app/static/dist',
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: {
        dashboard: path.resolve(__dirname, 'src/entry/dashboard.tsx'),
        navigation: path.resolve(__dirname, 'src/entry/navigation.tsx'),
        profile: path.resolve(__dirname, 'src/entry/profile.tsx'),
        lta_accreditation: path.resolve(__dirname, 'src/entry/lta_accreditation.tsx'), // Add this line
      },
      output: {
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]'
      }
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})