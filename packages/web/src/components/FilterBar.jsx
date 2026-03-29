import { useMemo } from 'react'
import useStore from '../stores/useStore'

export default function FilterBar() {
  const genres = useStore(s => s.genres)
  const activeGenre = useStore(s => s.activeGenre)
  const setActiveGenre = useStore(s => s.setActiveGenre)
  const filterBarOpen = useStore(s => s.filterBarOpen)
  const setFilterBarOpen = useStore(s => s.setFilterBarOpen)

  // Get unique scenes (biomes) sorted by genre count
  const scenes = useMemo(() => {
    const counts = {}
    const colors = {}
    genres.forEach(g => {
      counts[g.scene] = (counts[g.scene] || 0) + 1
      colors[g.scene] = g.color
    })
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .map(([scene, count]) => ({ scene, count, color: colors[scene] }))
  }, [genres])

  return (
    <>
      {/* Mobile toggle button */}
      <button
        className="filter-toggle-btn"
        onClick={() => setFilterBarOpen(!filterBarOpen)}
        aria-label="Toggle filters"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M1 3h14M4 8h8M6 13h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
        <span>Scenes</span>
      </button>

      {/* Filter chips */}
      <div className={`filter-bar ${filterBarOpen ? 'filter-bar--open' : ''}`}>
        <button
          className={`filter-chip ${!activeGenre ? 'active' : ''}`}
          onClick={() => { setActiveGenre(null); setFilterBarOpen(false) }}
          style={!activeGenre ? { borderColor: '#fff' } : {}}
        >
          All
        </button>
        {scenes.map(s => (
          <button
            key={s.scene}
            className={`filter-chip ${activeGenre?.scene === s.scene ? 'active' : ''}`}
            onClick={() => {
              if (activeGenre?.scene === s.scene) {
                setActiveGenre(null)
              } else {
                const first = genres.find(g => g.scene === s.scene)
                setActiveGenre(first)
              }
              setFilterBarOpen(false)
            }}
            style={activeGenre?.scene === s.scene ? { borderColor: s.color, color: s.color } : {}}
          >
            {s.scene}
            <span style={{ fontSize: 10, opacity: 0.4, marginLeft: 4 }}>{s.count}</span>
          </button>
        ))}
      </div>
    </>
  )
}
