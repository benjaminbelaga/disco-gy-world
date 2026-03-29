import { useState, useEffect, useRef, useCallback } from 'react'
import useStore from '../stores/useStore'
import { pathToUrl } from '../lib/pathSerializer'

export default function DigPathPanel() {
  const digPathMode = useStore(s => s.digPathMode)
  const waypoints = useStore(s => s.digPathWaypoints)
  const title = useStore(s => s.digPathTitle)
  const description = useStore(s => s.digPathDescription)
  const digPathPlaying = useStore(s => s.digPathPlaying)
  const playbackIndex = useStore(s => s.digPathPlaybackIndex)
  const genres = useStore(s => s.genres)

  const setDigPathMode = useStore(s => s.setDigPathMode)
  const removeDigPathWaypoint = useStore(s => s.removeDigPathWaypoint)
  const moveDigPathWaypoint = useStore(s => s.moveDigPathWaypoint)
  const updateDigPathNote = useStore(s => s.updateDigPathNote)
  const setDigPathTitle = useStore(s => s.setDigPathTitle)
  const setDigPathDescription = useStore(s => s.setDigPathDescription)
  const setDigPathPlaying = useStore(s => s.setDigPathPlaying)
  const setDigPathPlaybackIndex = useStore(s => s.setDigPathPlaybackIndex)
  const clearDigPath = useStore(s => s.clearDigPath)
  const setCameraTarget = useStore(s => s.setCameraTarget)
  const setActiveGenre = useStore(s => s.setActiveGenre)
  const setCurrentTrack = useStore(s => s.setCurrentTrack)
  const releases = useStore(s => s.releases)

  const [copied, setCopied] = useState(false)
  const [editingNote, setEditingNote] = useState(null)
  const playbackRef = useRef(null)

  // Build slug -> genre map
  const genreMap = {}
  genres.forEach(g => { genreMap[g.slug] = g })

  // Copy shareable URL
  const handleShare = useCallback(() => {
    const url = pathToUrl({
      title,
      description,
      waypoints: waypoints.map(w => ({ slug: w.slug, note: w.note })),
    })
    navigator.clipboard.writeText(url).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }, [title, description, waypoints])

  // Fly to a waypoint
  const flyToWaypoint = useCallback((index) => {
    const wp = waypoints[index]
    if (!wp) return
    const genre = genreMap[wp.slug]
    if (!genre) return
    setActiveGenre(genre)
    setCameraTarget(genre)
    setDigPathPlaybackIndex(index)

    // Auto-play a track from this genre
    const tracks = releases[genre.slug] || []
    if (tracks.length > 0) {
      setCurrentTrack(tracks[0])
    }
  }, [waypoints, genreMap, setActiveGenre, setCameraTarget, setDigPathPlaybackIndex, releases, setCurrentTrack])

  // Playback: auto-advance through waypoints
  useEffect(() => {
    if (!digPathPlaying) {
      if (playbackRef.current) clearInterval(playbackRef.current)
      return
    }

    flyToWaypoint(playbackIndex)

    playbackRef.current = setInterval(() => {
      const state = useStore.getState()
      const nextIdx = state.digPathPlaybackIndex + 1
      if (nextIdx >= state.digPathWaypoints.length) {
        // End of path
        setDigPathPlaying(false)
        return
      }
      setDigPathPlaybackIndex(nextIdx)
      const wp = state.digPathWaypoints[nextIdx]
      const genre = genreMap[wp?.slug]
      if (genre) {
        setActiveGenre(genre)
        setCameraTarget(genre)
        const tracks = releases[genre.slug] || []
        if (tracks.length > 0) setCurrentTrack(tracks[0])
      }
    }, 8000) // 8s per stop

    return () => clearInterval(playbackRef.current)
  }, [digPathPlaying, playbackIndex])

  const handlePlay = useCallback(() => {
    setDigPathPlaybackIndex(0)
    setDigPathPlaying(true)
  }, [setDigPathPlaybackIndex, setDigPathPlaying])

  const handleStop = useCallback(() => {
    setDigPathPlaying(false)
  }, [setDigPathPlaying])

  const viewMode = useStore(s => s.viewMode)
  if (!digPathMode || viewMode !== 'genre') return null

  return (
    <div className="dig-path-panel">
      <div className="dig-path-panel-header">
        <span className="dig-path-panel-title">
          {digPathMode === 'record' ? 'Creating Path' : 'Dig Path'}
        </span>
        <button
          className="close-btn"
          onClick={clearDigPath}
          style={{ position: 'static', padding: '2px 6px', fontSize: 16 }}
        >
          &times;
        </button>
      </div>

      {/* Title + Description */}
      <input
        className="dig-path-input"
        type="text"
        placeholder="Path title..."
        value={title}
        onChange={(e) => setDigPathTitle(e.target.value)}
      />
      <input
        className="dig-path-input dig-path-input-desc"
        type="text"
        placeholder="Description (optional)"
        value={description}
        onChange={(e) => setDigPathDescription(e.target.value)}
      />

      {/* Recording hint */}
      {digPathMode === 'record' && waypoints.length === 0 && (
        <div className="dig-path-hint">
          Click genres in the world to add waypoints
        </div>
      )}

      {/* Waypoint list */}
      {waypoints.length > 0 && (
        <div className="dig-path-waypoints">
          {waypoints.map((wp, i) => {
            const genre = genreMap[wp.slug]
            const isActive = digPathPlaying && i === playbackIndex
            return (
              <div
                key={`${wp.slug}-${i}`}
                className={`dig-path-waypoint${isActive ? ' active' : ''}`}
                onClick={() => flyToWaypoint(i)}
              >
                <span className="dig-path-wp-num">{i + 1}</span>
                <div className="dig-path-wp-info">
                  <span className="dig-path-wp-name" style={{ color: genre?.color || '#fff' }}>
                    {genre?.name || wp.slug}
                  </span>
                  {editingNote === i ? (
                    <input
                      className="dig-path-note-input"
                      type="text"
                      value={wp.note}
                      placeholder="Add note..."
                      autoFocus
                      onChange={(e) => updateDigPathNote(i, e.target.value)}
                      onBlur={() => setEditingNote(null)}
                      onKeyDown={(e) => { if (e.key === 'Enter') setEditingNote(null) }}
                      onClick={(e) => e.stopPropagation()}
                    />
                  ) : (
                    <span
                      className="dig-path-wp-note"
                      onClick={(e) => { e.stopPropagation(); setEditingNote(i) }}
                    >
                      {wp.note || 'add note...'}
                    </span>
                  )}
                </div>
                <div className="dig-path-wp-actions">
                  {i > 0 && (
                    <button
                      onClick={(e) => { e.stopPropagation(); moveDigPathWaypoint(i, i - 1) }}
                      title="Move up"
                    >
                      &#9650;
                    </button>
                  )}
                  {i < waypoints.length - 1 && (
                    <button
                      onClick={(e) => { e.stopPropagation(); moveDigPathWaypoint(i, i + 1) }}
                      title="Move down"
                    >
                      &#9660;
                    </button>
                  )}
                  <button
                    onClick={(e) => { e.stopPropagation(); removeDigPathWaypoint(i) }}
                    title="Remove"
                  >
                    &times;
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Actions */}
      <div className="dig-path-actions">
        {digPathMode === 'record' && (
          <button
            className="dig-path-action-btn dig-path-btn-play"
            onClick={() => setDigPathMode('playback')}
            disabled={waypoints.length < 2}
          >
            Done
          </button>
        )}
        {digPathMode === 'playback' && !digPathPlaying && (
          <>
            <button
              className="dig-path-action-btn dig-path-btn-play"
              onClick={handlePlay}
              disabled={waypoints.length < 2}
            >
              Play Path
            </button>
            <button
              className="dig-path-action-btn dig-path-btn-edit"
              onClick={() => setDigPathMode('record')}
            >
              Edit
            </button>
          </>
        )}
        {digPathPlaying && (
          <button className="dig-path-action-btn dig-path-btn-stop" onClick={handleStop}>
            Stop
          </button>
        )}
        <button
          className="dig-path-action-btn dig-path-btn-share"
          onClick={handleShare}
          disabled={waypoints.length === 0}
        >
          {copied ? 'Copied!' : 'Share'}
        </button>
      </div>

      {/* Waypoint count */}
      <div className="dig-path-count">
        {waypoints.length} waypoint{waypoints.length !== 1 ? 's' : ''}
      </div>
    </div>
  )
}
