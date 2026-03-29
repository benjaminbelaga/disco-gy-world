import { useState, useEffect, useRef, useCallback } from 'react'
import './ContributorBadge.css'

const API_BASE = import.meta.env.VITE_API_URL || ''

export default function ContributorBadge({ username }) {
  const [points, setPoints] = useState(0)
  const [leaders, setLeaders] = useState([])
  const [open, setOpen] = useState(false)
  const panelRef = useRef(null)

  // Fetch user points
  useEffect(() => {
    if (!username) return
    fetch(`${API_BASE}/api/contributors/${username}`)
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data?.profile) setPoints(data.profile.total_points)
      })
      .catch(() => {})
  }, [username])

  // Fetch leaderboard when panel opens
  useEffect(() => {
    if (!open) return
    fetch(`${API_BASE}/api/contributors/leaderboard?limit=10`)
      .then(r => r.ok ? r.json() : [])
      .then(setLeaders)
      .catch(() => setLeaders([]))
  }, [open])

  // Close on outside click
  useEffect(() => {
    if (!open) return
    const handler = (e) => {
      if (panelRef.current && !panelRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  const toggle = useCallback(() => setOpen(prev => !prev), [])

  if (!username) return null

  return (
    <div className="contributor-badge" ref={panelRef}>
      <button
        className="contributor-badge-button"
        onClick={toggle}
        title="View leaderboard"
        aria-label={`${points} contributor points — click to view leaderboard`}
        aria-expanded={open}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
        </svg>
        <span className="points-count">{points}</span>
      </button>

      {open && (
        <div className="contributor-panel" role="dialog" aria-label="Top contributors">
          <h3>Top Contributors</h3>
          {leaders.length === 0 ? (
            <div className="contributor-panel-empty">No contributions yet</div>
          ) : (
            <ul className="leaderboard-list">
              {leaders.map(entry => (
                <li key={entry.username} className="leaderboard-entry">
                  <span className="leaderboard-rank">#{entry.rank}</span>
                  <span className="leaderboard-name">
                    {entry.display_name || entry.username}
                  </span>
                  <span className="leaderboard-points">{entry.total_points} pts</span>
                  <span className="leaderboard-count">{entry.contributions_count}x</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
