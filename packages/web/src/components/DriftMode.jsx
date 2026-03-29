import { useState, useEffect, useRef, useCallback } from 'react'
import useStore from '../stores/useStore'
import { startDrift, stopDrift } from '../lib/driftEngine'

export default function DriftMode() {
  const [active, setActive] = useState(false)
  const [adventurousness, setAdventurousness] = useState(50)
  const [currentGenreName, setCurrentGenreName] = useState(null)
  const [currentDriftTrack, setCurrentDriftTrack] = useState(null)
  const [panelVisible, setPanelVisible] = useState(false)
  const cleanupRef = useRef(null)

  const genres = useStore(s => s.genres)
  const links = useStore(s => s.links)
  const releases = useStore(s => s.releases)
  const activeGenre = useStore(s => s.activeGenre)
  const setActiveGenre = useStore(s => s.setActiveGenre)
  const setCameraTarget = useStore(s => s.setCameraTarget)
  const setCurrentTrack = useStore(s => s.setCurrentTrack)

  const handleStart = useCallback(() => {
    if (active) return

    setActive(true)
    setPanelVisible(true)

    const cleanup = startDrift({
      genres,
      links,
      tracks: releases,
      adventurousness,
      startSlug: activeGenre?.slug || null,
      onGenreChange: (genre) => {
        setCurrentGenreName(genre.name)
        setActiveGenre(genre)
      },
      onTrackPlay: (track) => {
        setCurrentDriftTrack(track)
        setCurrentTrack(track)
      },
      onFlyTo: (genre) => {
        setCameraTarget(genre)
      },
    })
    cleanupRef.current = cleanup
  }, [active, genres, links, releases, adventurousness, activeGenre, setActiveGenre, setCameraTarget, setCurrentTrack])

  const handleStop = useCallback(() => {
    setActive(false)
    stopDrift()
    cleanupRef.current = null
  }, [])

  const handleStopHere = useCallback(() => {
    handleStop()
    // Keep current genre selected, just stop moving
  }, [handleStop])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (cleanupRef.current) {
        stopDrift()
      }
    }
  }, [])

  // Keyboard: D to toggle drift
  useEffect(() => {
    const handler = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return
      if (e.key === 'd' || e.key === 'D') {
        if (active) {
          handleStop()
        } else {
          handleStart()
        }
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [active, handleStart, handleStop])

  const viewMode = useStore(s => s.viewMode)
  if (viewMode !== 'genre') return null

  return (
    <>
      {/* Drift toggle button — always visible in genre view */}
      {!panelVisible && (
        <button
          onClick={() => { setPanelVisible(true); handleStart() }}
          className="drift-btn"
          title="Drift mode — auto-explore genres (D)"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" style={{ marginRight: 6 }}>
            <circle cx="8" cy="8" r="3" stroke="currentColor" strokeWidth="1.5" fill="none" />
            <path d="M8 1v3M8 12v3M1 8h3M12 8h3" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
          </svg>
          Drift
        </button>
      )}

      {/* Drift control panel */}
      {panelVisible && (
        <div className="drift-panel">
          <div className="drift-panel-header">
            <span className="drift-panel-title">
              {active ? 'Drifting...' : 'Drift Mode'}
            </span>
            <button
              className="close-btn"
              onClick={() => { handleStop(); setPanelVisible(false) }}
              style={{ position: 'static', padding: '2px 6px', fontSize: 16 }}
            >
              &times;
            </button>
          </div>

          {/* Current genre */}
          {currentGenreName && active && (
            <div className="drift-current-genre">
              {currentGenreName}
            </div>
          )}

          {/* Mini track info */}
          {currentDriftTrack && active && (
            <div className="drift-track-info">
              <div className="drift-track-bars">
                <span /><span /><span />
              </div>
              <div className="drift-track-text">
                <span className="drift-track-artist">{currentDriftTrack.artist}</span>
                <span className="drift-track-title">{currentDriftTrack.title}</span>
              </div>
            </div>
          )}

          {/* Adventurousness slider */}
          <div className="drift-slider-wrap">
            <label className="drift-slider-label">
              <span>Familiar</span>
              <span>Adventurous</span>
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={adventurousness}
              onChange={(e) => setAdventurousness(Number(e.target.value))}
              className="drift-slider"
            />
            <div className="drift-slider-value">{adventurousness}</div>
          </div>

          {/* Action buttons */}
          <div className="drift-actions">
            {!active ? (
              <button className="drift-action-btn drift-start" onClick={handleStart}>
                Start Drift
              </button>
            ) : (
              <>
                <button className="drift-action-btn drift-stop-here" onClick={handleStopHere}>
                  Stop Here
                </button>
                <button className="drift-action-btn drift-stop" onClick={handleStop}>
                  Stop
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </>
  )
}
