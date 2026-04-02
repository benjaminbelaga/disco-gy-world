import { useState, useEffect } from 'react'

export default function InstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState(null)
  const [dismissed, setDismissed] = useState(false)
  const [isOffline, setIsOffline] = useState(!navigator.onLine)

  useEffect(() => {
    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) return

    // Check if previously dismissed
    if (sessionStorage.getItem('pwa-install-dismissed')) {
      setDismissed(true)
      return
    }

    const handler = (e) => {
      e.preventDefault()
      setDeferredPrompt(e)
    }
    window.addEventListener('beforeinstallprompt', handler)
    return () => window.removeEventListener('beforeinstallprompt', handler)
  }, [])

  useEffect(() => {
    const goOnline = () => setIsOffline(false)
    const goOffline = () => setIsOffline(true)
    window.addEventListener('online', goOnline)
    window.addEventListener('offline', goOffline)
    return () => {
      window.removeEventListener('online', goOnline)
      window.removeEventListener('offline', goOffline)
    }
  }, [])

  const handleInstall = async () => {
    if (!deferredPrompt) return
    deferredPrompt.prompt()
    const { outcome } = await deferredPrompt.userChoice
    if (outcome === 'accepted') {
      setDeferredPrompt(null)
    }
  }

  const handleDismiss = () => {
    setDismissed(true)
    sessionStorage.setItem('pwa-install-dismissed', '1')
  }

  return (
    <>
      {/* Offline indicator */}
      {isOffline && (
        <div style={{
          position: 'fixed',
          top: 8,
          left: '50%',
          transform: 'translateX(-50%)',
          background: 'rgba(255, 140, 0, 0.9)',
          color: '#0a0a0f',
          padding: '4px 16px',
          borderRadius: 20,
          fontSize: 12,
          fontFamily: "'JetBrains Mono', monospace",
          fontWeight: 600,
          zIndex: 9999,
          pointerEvents: 'none',
          backdropFilter: 'blur(8px)',
        }}>
          offline mode
        </div>
      )}

      {/* Install banner */}
      {deferredPrompt && !dismissed && (
        <div style={{
          position: 'fixed',
          bottom: 16,
          left: '50%',
          transform: 'translateX(-50%)',
          background: 'rgba(10, 10, 15, 0.95)',
          border: '1px solid rgba(0, 212, 255, 0.3)',
          borderRadius: 12,
          padding: '10px 16px',
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          zIndex: 9998,
          backdropFilter: 'blur(12px)',
          maxWidth: 'calc(100vw - 32px)',
          boxShadow: '0 4px 24px rgba(0, 0, 0, 0.5)',
        }}>
          <svg width="20" height="20" viewBox="0 0 32 32" style={{ flexShrink: 0 }}>
            <circle cx="16" cy="16" r="15" fill="#0a0a0f" stroke="#00d4ff" strokeWidth="1" opacity="0.8"/>
            <circle cx="16" cy="16" r="7" fill="none" stroke="#ff8c00" strokeWidth="0.8" opacity="0.5"/>
            <circle cx="16" cy="16" r="3" fill="#fff" opacity="0.9"/>
          </svg>
          <span style={{
            color: 'rgba(255, 255, 255, 0.8)',
            fontSize: 13,
            fontFamily: "'JetBrains Mono', monospace",
            whiteSpace: 'nowrap',
          }}>
            Install DiscoWorld
          </span>
          <button
            onClick={handleInstall}
            style={{
              background: 'rgba(0, 212, 255, 0.15)',
              border: '1px solid rgba(0, 212, 255, 0.4)',
              borderRadius: 6,
              color: '#00d4ff',
              padding: '5px 12px',
              fontSize: 12,
              fontFamily: "'JetBrains Mono', monospace",
              cursor: 'pointer',
              whiteSpace: 'nowrap',
            }}
          >
            Add
          </button>
          <button
            onClick={handleDismiss}
            style={{
              background: 'none',
              border: 'none',
              color: 'rgba(255, 255, 255, 0.3)',
              cursor: 'pointer',
              padding: '2px 4px',
              fontSize: 16,
              lineHeight: 1,
            }}
            aria-label="Dismiss install prompt"
          >
            x
          </button>
        </div>
      )}
    </>
  )
}
