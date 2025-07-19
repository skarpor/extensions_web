import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    //让所有人都能访问 0.0.0.0
    open: true,
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/static/chat/img': {
        target: 'http://localhost:8000', // 后端地址
        changeOrigin: true,
        //rewrite: (path) => path.replace(/^\/api/, '') // 可选：去掉 /api 前缀
      },
      '/static/avatars/': {
        target: 'http://localhost:8000', // 后端地址
        changeOrigin: true,
        //rewrite: (path) => path.replace(/^\/api/, '') // 可选：去掉 /api 前缀
      },
      '/api/': {
        target: 'http://localhost:8000', // 后端地址
        changeOrigin: true,secure: false
        //rewrite: (path) => path.replace(/^\/api/, '') // 可选：去掉 /api 前缀
      },
    }
  }

})
