import { useEffect, useState } from 'react'

const SHORTCUTS = [
  ['Space', 'Toggle auto-tour'],
  ['E / R', 'Explore random genre'],
  ['Escape', 'Close panel / clear'],
  ['← →', 'Year ±1'],
  ['Shift + ← →', 'Year ±10'],
  ['1 / 2 / 3', 'Switch view mode'],
  ['G', 'Cycle view modes'],
  ['P', 'Toggle dig path recording'],
  ['Cmd+K', 'Focus search'],
  ['?', 'Toggle this overlay'],
]

export default function ShortcutHelp() {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const handler = (e) => {
      if (e.key === '?' || (e.key === '/' && e.shiftKey)) {
        e.preventDefault()
        setVisible(v => !v)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  if (!visible) return null

  return (
    <div role="dialog" aria-label="Keyboard shortcuts" aria-keyshortcuts="?" style={{
      position: 'fixed',
      bottom: 24,
      right: 24,
      background: 'rgba(10, 10, 20, 0.75)',
      backdropFilter: 'blur(16px)',
      WebkitBackdropFilter: 'blur(16px)',
      border: '1px solid rgba(255,255,255,0.1)',
      borderRadius: 12,
      padding: '16px 20px',
      zIndex: 100,
      color: 'rgba(255,255,255,0.85)',
      fontFamily: "'JetBrains Mono', monospace",
      fontSize: 12,
      minWidth: 220,
      boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
    }}>
      <div style={{
        fontSize: 11,
        textTransform: 'uppercase',
        letterSpacing: 1.5,
        opacity: 0.4,
        marginBottom: 10,
      }}>
        Keyboard Shortcuts
      </div>
      <table style={{ borderCollapse: 'collapse', width: '100%' }}>
        <tbody>
          {SHORTCUTS.map(([key, desc]) => (
            <tr key={key}>
              <td style={{
                padding: '4px 12px 4px 0',
                whiteSpace: 'nowrap',
              }}>
                <kbd style={{
                  background: 'rgba(255,255,255,0.08)',
                  border: '1px solid rgba(255,255,255,0.15)',
                  borderRadius: 4,
                  padding: '2px 6px',
                  fontSize: 11,
                }}>{key}</kbd>
              </td>
              <td style={{
                padding: '4px 0',
                opacity: 0.6,
              }}>{desc}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
