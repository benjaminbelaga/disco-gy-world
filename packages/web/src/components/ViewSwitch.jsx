import useStore from '../stores/useStore'

const VIEWS = [
  {
    id: 'genre',
    label: 'Genres',
    shortcut: '1',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <polygon points="12,2 22,8.5 22,15.5 12,22 2,15.5 2,8.5" />
        <line x1="12" y1="2" x2="12" y2="22" />
        <line x1="2" y1="8.5" x2="22" y2="8.5" />
      </svg>
    ),
  },
  {
    id: 'earth',
    label: 'Earth',
    shortcut: '2',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <circle cx="12" cy="12" r="10" />
        <path d="M2 12h20" />
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
      </svg>
    ),
  },
  {
    id: 'planet',
    label: 'Planet',
    shortcut: '3',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <circle cx="12" cy="12" r="8" />
        <ellipse cx="12" cy="12" rx="12" ry="4" transform="rotate(-30 12 12)" />
      </svg>
    ),
  },
]

export default function ViewSwitch() {
  const viewMode = useStore(s => s.viewMode)
  const setViewMode = useStore(s => s.setViewMode)

  return (
    <div className="view-switch" role="tablist" aria-label="View mode">
      {VIEWS.map(v => (
        <button
          key={v.id}
          role="tab"
          aria-selected={viewMode === v.id}
          aria-keyshortcuts={v.shortcut}
          className={`view-switch-btn ${viewMode === v.id ? 'active' : ''}`}
          onClick={() => setViewMode(v.id)}
          title={`${v.label} (${v.shortcut} or G to cycle)`}
          aria-label={`${v.label} view (press ${v.shortcut})`}
        >
          <span aria-hidden="true">{v.icon}</span>
          <span>{v.label}</span>
        </button>
      ))}
    </div>
  )
}
