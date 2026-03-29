import useStore from '../stores/useStore'

export default function CollectionToggle() {
  const tasteProfile = useStore(s => s.tasteProfile)
  const showOverlay = useStore(s => s.showCollectionOverlay)
  const setShowCollectionOverlay = useStore(s => s.setShowCollectionOverlay)

  // Only show toggle when a collection is loaded
  if (!tasteProfile) return null

  return (
    <button
      onClick={() => setShowCollectionOverlay(!showOverlay)}
      title={showOverlay ? 'Hide collection overlay' : 'Show my collection'}
      style={{
        display: 'flex', alignItems: 'center', gap: 5,
        padding: '4px 10px',
        borderRadius: 8,
        background: showOverlay ? 'rgba(255,215,0,0.12)' : 'rgba(255,255,255,0.04)',
        border: `1px solid ${showOverlay ? 'rgba(255,215,0,0.3)' : 'rgba(255,255,255,0.08)'}`,
        color: showOverlay ? '#FFD700' : 'rgba(255,255,255,0.4)',
        fontSize: 11, fontWeight: 500, cursor: 'pointer',
        fontFamily: "'JetBrains Mono', monospace",
        transition: 'all 0.2s',
        backdropFilter: 'blur(8px)',
      }}
      onMouseEnter={e => {
        if (!showOverlay) {
          e.currentTarget.style.background = 'rgba(255,215,0,0.08)'
          e.currentTarget.style.color = '#FFD700'
        }
      }}
      onMouseLeave={e => {
        if (!showOverlay) {
          e.currentTarget.style.background = 'rgba(255,255,255,0.04)'
          e.currentTarget.style.color = 'rgba(255,255,255,0.4)'
        }
      }}
    >
      <svg width="12" height="12" viewBox="0 0 24 24" fill={showOverlay ? '#FFD700' : 'none'} stroke="currentColor" strokeWidth="2" strokeLinecap="round">
        <circle cx="12" cy="12" r="10" />
        <circle cx="12" cy="12" r="4" />
      </svg>
      My Collection
    </button>
  )
}
