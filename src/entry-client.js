// src/entry-client.js
import { createApp } from './app'

const { app, router } = createApp(false)
router.isReady().then(() => {
  app.mount('#app')
})