import useAudioStore from '../stores/useAudioStore'

const modeLabels = {
  off: 'Audio off',
  simulated: 'Simulated',
  mic: 'Microphone',
}

/**
 * Small toggle button that cycles audio reactivity mode: off → simulated → mic → off.
 * Shows a mic/speaker icon with mode indicator dot.
 */
export default function AudioSourceToggle() {
  const audioMode = useAudioStore(s => s.audioMode)
  const cycleAudioMode = useAudioStore(s => s.cycleAudioMode)
  const energy = useAudioStore(s => s.energy)

  const isActive = audioMode !== 'off'
  const isMic = audioMode === 'mic'

  // Subtle glow when active, pulsing with energy
  const glowOpacity = isActive ? 0.3 + energy * 0.4 : 0

  return (
    <button
      onClick={cycleAudioMode}
      title={modeLabels[audioMode]}
      aria-label={`Audio reactivity: ${modeLabels[audioMode]}. Click to change.`}
      style={{
        position: 'relative',
        background: isActive ? 'rgba(255,255,255,0.08)' : 'transparent',
        border: '1px solid rgba(255,255,255,0.12)',
        borderRadius: 8,
        padding: '6px 8px',
        cursor: 'pointer',
        color: isActive ? '#fff' : 'rgba(255,255,255,0.4)',
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        fontSize: 13,
        transition: 'all 0.2s ease',
        boxShadow: isActive
          ? `0 0 ${8 + energy * 12}px rgba(100,140,255,${glowOpacity})`
          : 'none',
      }}
    >
      {/* Icon: mic for mic mode, waveform for simulated */}
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
        {isMic ? (
          <>
            <rect x="6" y="1" width="4" height="8" rx="2" stroke="currentColor" strokeWidth="1.3" />
            <path d="M4 7a4 4 0 008 0" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
            <line x1="8" y1="11" x2="8" y2="14" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
            <line x1="6" y1="14" x2="10" y2="14" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
          </>
        ) : (
          <>
            <line x1="2" y1="10" x2="2" y2="6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            <line x1="5" y1="12" x2="5" y2="4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            <line x1="8" y1="11" x2="8" y2="5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            <line x1="11" y1="13" x2="11" y2="3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            <line x1="14" y1="10" x2="14" y2="6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </>
        )}
      </svg>

      {/* Mode indicator dot */}
      <span
        style={{
          width: 6,
          height: 6,
          borderRadius: '50%',
          background: audioMode === 'off'
            ? 'rgba(255,255,255,0.2)'
            : audioMode === 'mic'
              ? '#4ade80'
              : '#60a5fa',
          transition: 'background 0.2s ease',
        }}
      />
    </button>
  )
}
