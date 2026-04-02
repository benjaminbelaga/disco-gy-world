import { useCallback, useEffect, useRef } from 'react'
import useStore from '../stores/useStore'

export default function ExploreButton() {
  const genres = useStore(s => s.genres)
  const setActiveGenre = useStore(s => s.setActiveGenre)
  const setCameraTarget = useStore(s => s.setCameraTarget)
  const resetCamera = useStore(s => s.resetCamera)
  const year = useStore(s => s.year)
  const autoTourRef = useRef(null)
  const autoTourActive = useStore(s => s.autoTour)

  const explore = useCallback(() => {
    if (!genres.length) return
    // Pick a random visible genre
    const visible = genres.filter(g => g.year <= year)
    if (!visible.length) return
    const random = visible[Math.floor(Math.random() * visible.length)]
    setActiveGenre(random)
    setCameraTarget(random)
  }, [genres, year, setActiveGenre, setCameraTarget])

  // Auto-tour: cycle through genres every 30 seconds (time to actually listen)
  useEffect(() => {
    if (autoTourActive) {
      autoTourRef.current = setInterval(explore, 30000)
      explore() // Start immediately
    } else {
      clearInterval(autoTourRef.current)
    }
    return () => clearInterval(autoTourRef.current)
  }, [autoTourActive, explore])

  return (
    <div style={{
      position: 'fixed',
      bottom: 80,
      left: 24,
      display: 'flex',
      gap: 8,
      zIndex: 20,
    }}>
      <button
        onClick={resetCamera}
        style={{
          background: 'rgba(255,255,255,0.05)',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: 10,
          color: 'rgba(255,255,255,0.6)',
          padding: '8px 12px',
          fontSize: 13,
          fontWeight: 500,
          fontFamily: 'inherit',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          transition: 'all 0.2s',
        }}
        onMouseEnter={e => e.target.style.background = 'rgba(255,255,255,0.12)'}
        onMouseLeave={e => e.target.style.background = 'rgba(255,255,255,0.05)'}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
          <polyline points="9 22 9 12 15 12 15 22" />
        </svg>
        Home
      </button>
      <button
        onClick={explore}
        style={{
          background: 'rgba(255,255,255,0.08)',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(255,255,255,0.12)',
          borderRadius: 10,
          color: '#fff',
          padding: '8px 16px',
          fontSize: 13,
          fontWeight: 500,
          fontFamily: 'inherit',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          transition: 'all 0.2s',
        }}
        onMouseEnter={e => e.target.style.background = 'rgba(255,255,255,0.15)'}
        onMouseLeave={e => e.target.style.background = 'rgba(255,255,255,0.08)'}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <path d="M16.24 7.76l-2.12 6.36-6.36 2.12 2.12-6.36z" />
        </svg>
        Explore
      </button>
      <button
        onClick={() => useStore.setState({ autoTour: !autoTourActive })}
        style={{
          background: autoTourActive ? 'rgba(100,180,255,0.2)' : 'rgba(255,255,255,0.05)',
          backdropFilter: 'blur(12px)',
          border: `1px solid ${autoTourActive ? 'rgba(100,180,255,0.3)' : 'rgba(255,255,255,0.08)'}`,
          borderRadius: 10,
          color: autoTourActive ? '#88ccff' : 'rgba(255,255,255,0.5)',
          padding: '8px 12px',
          fontSize: 12,
          fontWeight: 500,
          fontFamily: 'inherit',
          cursor: 'pointer',
          transition: 'all 0.2s',
        }}
      >
        {autoTourActive ? '■ Stop Tour' : '▶ Auto Tour'}
      </button>
    </div>
  )
}
