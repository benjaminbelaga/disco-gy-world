import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { registerSW } from 'virtual:pwa-register'

// Register service worker with auto-update
registerSW({
  onRegisteredSW(_swUrl, r) {
    // Check for updates every hour
    if (r) {
      setInterval(() => {
        r.update()
      }, 60 * 60 * 1000)
    }
  },
  onOfflineReady() {
    console.log('[DiscoWorld] Ready to work offline')
  }
})

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
