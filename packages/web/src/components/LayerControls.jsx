import useStore from '../stores/useStore'

const LAYERS = [
  { key: 'cities', label: 'Cities', icon: 'M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z' },
  { key: 'arcs', label: 'Arcs', icon: 'M2 20 Q12 2 22 20' },
  { key: 'heatmap', label: 'Heat', icon: 'M12 2a7 7 0 0 0-7 7c0 5 7 13 7 13s7-8 7-13a7 7 0 0 0-7-7zm0 9.5a2.5 2.5 0 1 1 0-5 2.5 2.5 0 0 1 0 5z' },
  { key: 'shops', label: 'Shops', icon: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14c-2.33 0-4.32-1.45-5.12-3.5h1.67c.69 1.19 1.97 2 3.45 2s2.75-.81 3.45-2h1.67c-.8 2.05-2.79 3.5-5.12 3.5z', activeColor: '#F5A623' },
  { key: 'collection', label: 'Collection', icon: 'M12 2l3.09 6.26L22 9.27l-5 4.87L18.18 22 12 18.27 5.82 22 7 14.14 2 9.27l6.91-1.01z', requiresCollection: true },
]

export default function LayerControls() {
  const viewMode = useStore(s => s.viewMode)
  const globeLayers = useStore(s => s.globeLayers)
  const setGlobeLayer = useStore(s => s.setGlobeLayer)
  const tasteProfile = useStore(s => s.tasteProfile)
  const showOverlay = useStore(s => s.showCollectionOverlay)
  const hasPlayer = useStore(s => !!s.currentTrack)
  const playerCollapsed = useStore(s => s.playerCollapsed)

  if (viewMode !== 'earth') return null

  const playerClass = hasPlayer
    ? (playerCollapsed ? ' layer-controls--above-player-mini' : ' layer-controls--above-player')
    : ''

  return (
    <div className={`layer-controls${playerClass}`}>
      {LAYERS.map(({ key, label, icon, requiresCollection, activeColor }) => {
        // Hide collection layer when no profile loaded or overlay not active
        if (requiresCollection && (!tasteProfile || !showOverlay)) return null
        const active = key === 'collection' ? (globeLayers[key] !== false) : globeLayers[key]
        const isGold = key === 'collection'
        const customColor = activeColor && active ? { color: activeColor, borderColor: `${activeColor}44` } : undefined
        return (
          <button
            key={key}
            className={`layer-btn ${active ? 'active' : ''}`}
            onClick={() => setGlobeLayer(key, !active)}
            title={`Toggle ${label}`}
            style={isGold && active ? { color: '#FFD700', borderColor: 'rgba(255,215,0,0.3)' } : customColor}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
              <path d={icon} />
            </svg>
            <span>{label}</span>
          </button>
        )
      })}
    </div>
  )
}
