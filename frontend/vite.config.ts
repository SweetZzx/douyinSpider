import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 7777,
    proxy: {
      '/api': {
        target: 'http://localhost:77',
        changeOrigin: true,
      },
    },
  },
})
