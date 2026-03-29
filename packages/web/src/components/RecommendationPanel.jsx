import { useState, useEffect, useCallback } from 'react'
import useStore from '../stores/useStore'

const MOCK_RECOMMENDATIONS = [
  { id: 1, title: 'Substrata', artist: 'Biosphere', label: 'All Saints', year: 1997, similarity: 0.94, youtube_id: 'xL1DRq3GrKc', genre: 'Ambient' },
  { id: 2, title: 'Radio', artist: 'Robert Hood', label: 'Tresor', year: 1994, similarity: 0.91, youtube_id: null, genre: 'Minimal Techno' },
  { id: 3, title: 'Replica', artist: 'Oneohtrix Point Never', label: 'Software', year: 2011, similarity: 0.88, youtube_id: 'hIGjXLmqxEI', genre: 'Experimental' },
  { id: 4, title: 'Selected Ambient Works 85-92', artist: 'Aphex Twin', label: 'Apollo', year: 1992, similarity: 0.87, youtube_id: 'Xw5AiRVqfqk', genre: 'Ambient Techno' },
  { id: 5, title: 'Incunabula', artist: 'Autechre', label: 'Warp', year: 1993, similarity: 0.85, youtube_id: null, genre: 'IDM' },
  { id: 6, title: 'Drexciya 2', artist: 'Drexciya', label: 'Underground Resistance', year: 1994, similarity: 0.83, youtube_id: null, genre: 'Electro' },
  { id: 7, title: 'Versions', artist: 'Vladislav Delay', label: 'Chain Reaction', year: 2000, similarity: 0.81, youtube_id: null, genre: 'Dub Techno' },
  { id: 8, title: 'Quaristice', artist: 'Autechre', label: 'Warp', year: 2008, similarity: 0.79, youtube_id: null, genre: 'IDM' },
  { id: 9, title: 'LP5', artist: 'Autechre', label: 'Warp', year: 1998, similarity: 0.78, youtube_id: null, genre: 'IDM' },
  { id: 10, title: 'Ravedeath, 1972', artist: 'Tim Hecker', label: 'Kranky', year: 2011, similarity: 0.76, youtube_id: null, genre: 'Ambient' },
  { id: 11, title: 'Scintilli', artist: 'Monolake', label: 'Imbalance', year: 2003, similarity: 0.74, youtube_id: null, genre: 'Techno' },
  { id: 12, title: 'Transient Random-Noise Bursts', artist: 'Stereolab', label: 'Duophonic', year: 1993, similarity: 0.72, youtube_id: null, genre: 'Krautrock' },
]

function ReleaseCard({ release, onPlay, onLabelClick, onArtistClick }) {
  const color = release.similarity >= 0.9 ? '#88eebb' : release.similarity >= 0.8 ? '#66ccff' : 'rgba(255,255,255,0.5)'

  return (
    <div style={{
      background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)',
      borderRadius: 10, padding: 12, cursor: 'pointer',
      transition: 'all 0.2s',
    }}
      onMouseEnter={e => {
        e.currentTarget.style.background = 'rgba(255,255,255,0.06)'
        e.currentTarget.style.borderColor = 'rgba(102,204,255,0.15)'
      }}
      onMouseLeave={e => {
        e.currentTarget.style.background = 'rgba(255,255,255,0.03)'
        e.currentTarget.style.borderColor = 'rgba(255,255,255,0.06)'
      }}
      onClick={() => onPlay(release)}
    >
      {/* Cover art placeholder */}
      <div style={{
        width: '100%', aspectRatio: '1', borderRadius: 6, marginBottom: 10,
        background: 'rgba(255,255,255,0.04)',
        border: '1px solid rgba(255,255,255,0.04)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 24, color: 'rgba(255,255,255,0.08)',
        position: 'relative', overflow: 'hidden',
      }}>
        <div style={{
          width: '60%', height: '60%', borderRadius: '50%',
          border: '2px solid rgba(255,255,255,0.06)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <div style={{
            width: '15%', height: '15%', borderRadius: '50%',
            background: 'rgba(255,255,255,0.08)',
          }} />
        </div>
        {/* Play indicator */}
        {release.youtube_id && (
          <div style={{
            position: 'absolute', bottom: 6, right: 6,
            width: 24, height: 24, borderRadius: '50%',
            background: 'rgba(102,204,255,0.15)', border: '1px solid rgba(102,204,255,0.25)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 10, color: '#66ccff',
          }}>
            &#9654;
          </div>
        )}
      </div>

      {/* Info */}
      <div style={{ fontSize: 12, fontWeight: 500, color: '#fff', marginBottom: 2, lineHeight: 1.3, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        {release.title}
      </div>
      <div
        style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginBottom: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', cursor: 'pointer' }}
        onClick={(e) => { e.stopPropagation(); onArtistClick?.(release.artist) }}
        onMouseEnter={(e) => { e.target.style.color = '#4488ff' }}
        onMouseLeave={(e) => { e.target.style.color = 'rgba(255,255,255,0.5)' }}
      >
        {release.artist}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span
          style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)', fontFamily: "'JetBrains Mono', monospace", cursor: 'pointer' }}
          onClick={(e) => { e.stopPropagation(); onLabelClick?.(release.label) }}
          onMouseEnter={(e) => { e.target.style.color = '#ffcc66' }}
          onMouseLeave={(e) => { e.target.style.color = 'rgba(255,255,255,0.3)' }}
        >
          {release.label} / {release.year}
        </span>
        <span style={{ fontSize: 10, fontWeight: 600, color, fontFamily: "'JetBrains Mono', monospace" }}>
          {Math.round(release.similarity * 100)}%
        </span>
      </div>

      {/* Genre tag */}
      <div style={{
        marginTop: 6, fontSize: 9, padding: '2px 6px', borderRadius: 3,
        background: 'rgba(102,204,255,0.06)', border: '1px solid rgba(102,204,255,0.1)',
        color: 'rgba(102,204,255,0.6)', display: 'inline-block',
        fontFamily: "'JetBrains Mono', monospace", textTransform: 'uppercase', letterSpacing: 0.5,
      }}>
        {release.genre}
      </div>

      {/* Future buttons (disabled for MVP) */}
      <div style={{ display: 'flex', gap: 4, marginTop: 8 }}>
        <button disabled style={{
          flex: 1, padding: '4px 0', borderRadius: 4, fontSize: 9,
          background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)',
          color: 'rgba(255,255,255,0.15)', cursor: 'not-allowed', fontFamily: 'inherit',
        }}>
          Already own
        </button>
        <button disabled style={{
          flex: 1, padding: '4px 0', borderRadius: 4, fontSize: 9,
          background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)',
          color: 'rgba(255,255,255,0.15)', cursor: 'not-allowed', fontFamily: 'inherit',
        }}>
          + Wantlist
        </button>
      </div>
    </div>
  )
}

export default function RecommendationPanel() {
  const recommendationsOpen = useStore(s => s.recommendationsOpen)
  const setRecommendationsOpen = useStore(s => s.setRecommendationsOpen)
  const discogsUsername = useStore(s => s.discogsUsername)
  const setCurrentTrack = useStore(s => s.setCurrentTrack)
  const setActiveLabel = useStore(s => s.setActiveLabel)
  const setActiveArtist = useStore(s => s.setActiveArtist)

  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(false)
  const [hiddenGemsOnly, setHiddenGemsOnly] = useState(false)

  useEffect(() => {
    if (!recommendationsOpen || !discogsUsername) return

    let cancelled = false
    setLoading(true)

    fetch(`/api/recommendations/personal?discogs_username=${encodeURIComponent(discogsUsername)}`)
      .then(res => {
        if (res.ok) return res.json()
        throw new Error('API not ready')
      })
      .then(data => {
        if (!cancelled) setRecommendations(data.recommendations || data)
      })
      .catch(() => {
        if (!cancelled) setRecommendations(MOCK_RECOMMENDATIONS)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => { cancelled = true }
  }, [recommendationsOpen, discogsUsername])

  const handlePlay = useCallback((release) => {
    if (release.youtube_id) {
      setCurrentTrack({
        artist: release.artist,
        title: release.title,
        youtubeId: release.youtube_id,
      })
    }
  }, [setCurrentTrack])

  if (!recommendationsOpen) return null

  const filtered = hiddenGemsOnly
    ? recommendations.filter(r => r.similarity < 0.85)
    : recommendations

  return (
    <div
      onClick={() => setRecommendationsOpen(false)}
      style={{
        position: 'fixed', inset: 0, zIndex: 150,
        background: 'rgba(5,5,10,0.6)', backdropFilter: 'blur(4px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        animation: 'onboarding-fade-in 0.3s ease-out',
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          width: 680, maxWidth: 'calc(100vw - 32px)',
          maxHeight: 'calc(100vh - 64px)', overflowY: 'auto',
          background: 'rgba(12,12,25,0.85)', backdropFilter: 'blur(24px)',
          WebkitBackdropFilter: 'blur(24px)',
          border: '1px solid rgba(100,200,255,0.12)', borderRadius: 16,
          padding: '24px 20px',
          boxShadow: '0 8px 48px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.06)',
          animation: 'onboarding-card-in 0.4s ease-out',
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <div style={{ fontSize: 16, fontWeight: 600, color: '#fff' }}>
              Recommendations
            </div>
            <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.3)', fontFamily: "'JetBrains Mono', monospace" }}>
              Based on your collection
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {/* Hidden gems toggle */}
            <label style={{
              display: 'flex', alignItems: 'center', gap: 6,
              fontSize: 11, color: 'rgba(255,255,255,0.4)', cursor: 'pointer',
              fontFamily: "'JetBrains Mono', monospace",
            }}>
              <input
                type="checkbox"
                checked={hiddenGemsOnly}
                onChange={e => setHiddenGemsOnly(e.target.checked)}
                style={{ accentColor: '#66ccff' }}
              />
              Hidden gems only
            </label>
            <button
              onClick={() => setRecommendationsOpen(false)}
              style={{
                background: 'none', border: 'none', color: 'rgba(255,255,255,0.4)',
                fontSize: 18, cursor: 'pointer', padding: '4px 8px',
              }}
            >
              x
            </button>
          </div>
        </div>

        {/* Loading state */}
        {loading && (
          <div style={{ textAlign: 'center', padding: '40px 0', color: 'rgba(255,255,255,0.3)', fontSize: 13 }}>
            Analyzing collection...
          </div>
        )}

        {/* Grid */}
        {!loading && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
            gap: 12,
          }}>
            {filtered.map(r => (
              <ReleaseCard key={r.id} release={r} onPlay={handlePlay} onLabelClick={setActiveLabel} onArtistClick={setActiveArtist} />
            ))}
          </div>
        )}

        {!loading && filtered.length === 0 && (
          <div style={{ textAlign: 'center', padding: '40px 0', color: 'rgba(255,255,255,0.3)', fontSize: 13 }}>
            No recommendations found. Try adjusting filters.
          </div>
        )}
      </div>
    </div>
  )
}
