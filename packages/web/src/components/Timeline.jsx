import { useMemo } from 'react'
import useStore from '../stores/useStore'

export default function Timeline() {
  const year = useStore(s => s.year)
  const setYear = useStore(s => s.setYear)
  const genres = useStore(s => s.genres)
  const currentTrack = useStore(s => s.currentTrack)

  const visibleCount = useMemo(
    () => genres.filter(g => g.year <= year).length,
    [genres, year]
  )

  return (
    <div className="timeline-bar" style={currentTrack ? { bottom: 48 } : undefined}>
      <span className="year-label">
        {year}
        {visibleCount > 0 && (
          <span style={{
            fontSize: 11,
            opacity: 0.35,
            fontWeight: 400,
            marginLeft: 8,
            fontFamily: "'JetBrains Mono', monospace",
          }}>
            · {visibleCount} genre{visibleCount !== 1 ? 's' : ''}
          </span>
        )}
      </span>
      <input
        type="range"
        min={1960}
        max={2026}
        value={year}
        onChange={(e) => setYear(parseInt(e.target.value))}
        aria-label="Timeline year"
        aria-valuetext={`${year}, ${visibleCount} genre${visibleCount !== 1 ? 's' : ''} visible`}
      />
      <span style={{ fontSize: 11, opacity: 0.3, fontFamily: "'JetBrains Mono', monospace" }}>
        2026
      </span>
    </div>
  )
}
