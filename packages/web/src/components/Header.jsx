import { useState, useCallback } from 'react'
import useStore from '../stores/useStore'
import { buildShareUrl } from '../hooks/useUrlState'
import SearchBar from './SearchBar'
import CollectionButton from './CollectionButton'
import CollectionToggle from './CollectionToggle'
import AudioSourceToggle from './AudioSourceToggle'

export default function Header() {
  const genres = useStore(s => s.genres)
  const [toast, setToast] = useState(false)

  const handleShare = useCallback(() => {
    const url = buildShareUrl()
    navigator.clipboard.writeText(url).then(() => {
      setToast(true)
      setTimeout(() => setToast(false), 2000)
    }).catch(() => {
      // Fallback: try again with a temporary textarea (for non-HTTPS contexts)
      try {
        const ta = document.createElement('textarea')
        ta.value = url
        ta.style.position = 'fixed'
        ta.style.opacity = '0'
        document.body.appendChild(ta)
        ta.select()
        document.execCommand('copy')
        document.body.removeChild(ta)
      } catch (_) { /* last resort failed */ }
      setToast(true)
      setTimeout(() => setToast(false), 2000)
    })
  }, [])

  return (
    <header className="header" role="banner">
      <div className="logo" aria-label="DiscoWorld">
        Disco<span>World</span>
      </div>
      <SearchBar />
      <nav style={{ display: 'flex', alignItems: 'center', gap: 12 }} aria-label="Site controls">
        <button
          onClick={handleShare}
          title="Copy shareable link"
          aria-label="Share current view — copy link to clipboard"
          style={{
            background: 'rgba(255,255,255,0.06)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 8,
            color: 'rgba(255,255,255,0.6)',
            cursor: 'pointer',
            padding: '6px 10px',
            fontSize: 13,
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            transition: 'all 0.2s',
            backdropFilter: 'blur(8px)',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.background = 'rgba(255,255,255,0.12)'
            e.currentTarget.style.color = 'rgba(255,255,255,0.9)'
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = 'rgba(255,255,255,0.06)'
            e.currentTarget.style.color = 'rgba(255,255,255,0.6)'
          }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
            <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
          </svg>
          Share
        </button>
        <AudioSourceToggle />
        <CollectionToggle />
        <CollectionButton />
        <span className="header-genre-count" style={{ fontSize: 12, opacity: 0.3, fontFamily: "'JetBrains Mono', monospace" }}>
          {genres.length} genres
        </span>
      </nav>

      {toast && (
        <div role="status" aria-live="polite" style={{
          position: 'fixed',
          bottom: 32,
          left: '50%',
          transform: 'translateX(-50%)',
          background: 'rgba(20,20,30,0.85)',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(255,255,255,0.12)',
          borderRadius: 10,
          padding: '10px 20px',
          color: 'rgba(255,255,255,0.9)',
          fontSize: 13,
          fontFamily: "'JetBrains Mono', monospace",
          zIndex: 9999,
          animation: 'toastFade 2s ease-in-out forwards',
          pointerEvents: 'none',
        }}>
          Link copied!
          <style>{`
            @keyframes toastFade {
              0% { opacity: 0; transform: translateX(-50%) translateY(8px); }
              15% { opacity: 1; transform: translateX(-50%) translateY(0); }
              75% { opacity: 1; transform: translateX(-50%) translateY(0); }
              100% { opacity: 0; transform: translateX(-50%) translateY(-4px); }
            }
          `}</style>
        </div>
      )}
    </header>
  )
}
