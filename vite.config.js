import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue({
    template: {
      compilerOptions: {
        isCustomElement: (tag) => tag === 'video-player' || tag === 'video-player-ce'
      }
    }
  })],
  server: {
    port: 3000
  },
  build: {
    cssCodeSplit: true,
    ssrManifest: true,
    rollupOptions: {
      input: {
        main: './index.html'
      }
    }
  }
})