import useStore from '../stores/useStore'

export default function CollectionButton() {
  const setPassportOpen = useStore(s => s.setPassportOpen)
  const discogsUsername = useStore(s => s.discogsUsername)

  return (
    <button
      onClick={() => setPassportOpen(true)}
      title="My Collection"
      style={{
        display: 'flex', alignItems: 'center', gap: 6,
        padding: discogsUsername ? '4px 10px 4px 4px' : '6px 12px',
        borderRadius: 8,
        background: discogsUsername ? 'rgba(102,204,255,0.08)' : 'rgba(255,255,255,0.06)',
        border: `1px solid ${discogsUsername ? 'rgba(102,204,255,0.15)' : 'rgba(255,255,255,0.08)'}`,
        color: discogsUsername ? '#66ccff' : 'rgba(255,255,255,0.5)',
        fontSize: 12, fontWeight: 500, cursor: 'pointer',
        fontFamily: "'JetBrains Mono', monospace",
        transition: 'all 0.2s',
        backdropFilter: 'blur(8px)',
      }}
      onMouseEnter={e => {
        e.currentTarget.style.background = discogsUsername ? 'rgba(102,204,255,0.14)' : 'rgba(255,255,255,0.1)'
        e.currentTarget.style.color = '#fff'
      }}
      onMouseLeave={e => {
        e.currentTarget.style.background = discogsUsername ? 'rgba(102,204,255,0.08)' : 'rgba(255,255,255,0.06)'
        e.currentTarget.style.color = discogsUsername ? '#66ccff' : 'rgba(255,255,255,0.5)'
      }}
    >
      {discogsUsername ? (
        <>
          <div style={{
            width: 22, height: 22, borderRadius: '50%',
            background: 'rgba(102,204,255,0.15)', border: '1px solid rgba(102,204,255,0.25)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 11, fontWeight: 600,
          }}>
            {discogsUsername[0].toUpperCase()}
          </div>
          <span style={{ maxWidth: 80, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {discogsUsername}
          </span>
        </>
      ) : (
        <>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <circle cx="12" cy="12" r="3" />
            <line x1="12" y1="2" x2="12" y2="6" />
            <line x1="12" y1="18" x2="12" y2="22" />
            <line x1="2" y1="12" x2="6" y2="12" />
            <line x1="18" y1="12" x2="22" y2="12" />
          </svg>
          Collection
        </>
      )}
    </button>
  )
}
