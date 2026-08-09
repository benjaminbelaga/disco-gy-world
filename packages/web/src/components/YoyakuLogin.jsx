import { useEffect, useRef } from 'react'
import { initiateLogin } from '../lib/discogsApi'

// Discogs OAuth is the only sign-in this app has.
//
// There used to be a second path here — "Continue with YOYAKU", an email +
// password form POSTing to /api/auth/login. That route does not exist: the auth
// router only serves /discogs/login, /discogs/callback, /discogs/login/token and
// /logout, so every submission 404'd and the panel answered "Login failed".
// It was removed rather than wired, because what it collected was a live
// yoyaku.io shop password, sent cross-origin to a world.yoyaku.io endpoint. A
// naive implementation of that route (look the email up, compare the hash) is a
// credential-stuffing oracle against the shop's 16k customer accounts. Sign-in
// with a YOYAKU account belongs behind OAuth on yoyaku.io, not behind a password
// field on this domain.
export default function YoyakuLogin({ onClose }) {
  const panelRef = useRef(null)
  const previouslyFocusedRef = useRef(null)

  // Modal a11y: Esc to close, focus first button on mount, restore focus on close
  useEffect(() => {
    previouslyFocusedRef.current = document.activeElement
    // Focus the first focusable element inside the panel
    const timer = setTimeout(() => {
      const firstBtn = panelRef.current?.querySelector('button, [href], input')
      if (firstBtn) firstBtn.focus()
    }, 50)
    const onKeyDown = (e) => {
      if (e.key === 'Escape') {
        e.preventDefault()
        onClose?.()
      }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => {
      clearTimeout(timer)
      document.removeEventListener('keydown', onKeyDown)
      // Restore focus on unmount
      if (previouslyFocusedRef.current?.focus) {
        previouslyFocusedRef.current.focus()
      }
    }
  }, [onClose])

  const handleDiscogs = async () => {
    // Discogs redirects to the API callback, which exchanges tokens and
    // redirects to /auth/callback?session_token=... on the frontend
    const apiCallback = `${window.location.origin}/api/auth/discogs/callback?frontend_url=${encodeURIComponent(window.location.origin)}`
    await initiateLogin(apiCallback)
    // initiateLogin redirects — nothing to do after
  }

  return (
    <div className="yl-panel" ref={panelRef} role="dialog" aria-modal="true" aria-labelledby="yl-login-title">
      <button className="yl-close" onClick={onClose} aria-label="Close login panel">&times;</button>

      <div className="yl-logo">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
          <circle cx="16" cy="16" r="15" stroke="rgba(255,255,255,0.12)" strokeWidth="1"/>
          <circle cx="16" cy="16" r="11" stroke="rgba(255,255,255,0.07)" strokeWidth="1"/>
          <circle cx="16" cy="16" r="7" stroke="rgba(255,255,255,0.07)" strokeWidth="1"/>
          <circle cx="16" cy="16" r="3" stroke="rgba(255,255,255,0.1)" strokeWidth="1"/>
          <circle cx="16" cy="16" r="1.5" fill="rgba(255,255,255,0.3)"/>
        </svg>
      </div>

      <h2 id="yl-login-title" className="yl-title">Connect</h2>
      <p className="yl-subtitle">Unlock your collection &amp; recommendations</p>

      {/* Primary: Discogs OAuth */}
      <button className="yl-btn yl-btn-discogs" onClick={handleDiscogs}>
        <svg className="yl-btn-icon" viewBox="0 0 24 24" fill="currentColor">
          <circle cx="12" cy="12" r="11" opacity="0.15"/>
          <circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" strokeWidth="1.5"/>
          <circle cx="12" cy="12" r="5" fill="none" stroke="currentColor" strokeWidth="1.5"/>
          <circle cx="12" cy="12" r="2" fill="none" stroke="currentColor" strokeWidth="1.5"/>
          <circle cx="12" cy="12" r="0.8" fill="currentColor"/>
        </svg>
        Continue with Discogs
      </button>

      <div className="yl-footer">
        <a href="https://yoyaku.io/my-account/" target="_blank" rel="noopener noreferrer">
          Create YOYAKU account
        </a>
      </div>
    </div>
  )
}
