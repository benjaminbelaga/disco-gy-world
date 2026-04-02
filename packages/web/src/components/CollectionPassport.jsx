import { useState, useCallback, useEffect } from 'react'
import useStore from '../stores/useStore'
import { importCollection, clearCachedProfile } from '../lib/discogsApi'

const GENRE_COLORS = {
  Electronic: '#66ccff',
  Techno: '#66ccff',
  House: '#ff6b9d',
  Ambient: '#88eebb',
  'Dub Techno': '#9999ff',
  Electro: '#ffaa44',
  IDM: '#cc88ff',
  Acid: '#ffee55',
  Breakbeat: '#ff8866',
  Downtempo: '#77ddaa',
  'Drum n Bass': '#ff6666',
  Experimental: '#bbaaff',
  Industrial: '#888888',
  Trance: '#44ddff',
  Disco: '#ffaa88',
  Dub: '#aaddaa',
  'Hip Hop': '#ddaa66',
  Jazz: '#ddbb88',
  Funk: '#ee9966',
  Rock: '#dd8888',
  Pop: '#ffbbcc',
  Reggae: '#88dd88',
  Classical: '#ccbbaa',
}

function GenreBar({ genre, maxPct }) {
  const color = GENRE_COLORS[genre.name] || '#66ccff'
  const width = maxPct > 0 ? (genre.pct / maxPct) * 100 : 0
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
      <span style={{
        fontSize: 11, fontFamily: "'JetBrains Mono', monospace",
        color: 'rgba(255,255,255,0.5)', minWidth: 90, textAlign: 'right',
        whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
      }}>
        {genre.name}
      </span>
      <div style={{ flex: 1, height: 14, background: 'rgba(255,255,255,0.04)', borderRadius: 3, overflow: 'hidden' }}>
        <div style={{
          width: `${width}%`, height: '100%', background: color,
          borderRadius: 3, transition: 'width 0.6s ease-out',
          boxShadow: `0 0 8px ${color}44`,
        }} />
      </div>
      <span style={{
        fontSize: 10, fontFamily: "'JetBrains Mono', monospace",
        color: 'rgba(255,255,255,0.35)', minWidth: 50, textAlign: 'right',
      }}>
        {genre.count} <span style={{ opacity: 0.5 }}>({genre.pct}%)</span>
      </span>
    </div>
  )
}

function StyleBars({ styles }) {
  if (!styles || styles.length === 0) return null
  const maxPct = Math.max(...styles.map(s => s.pct))
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{
        fontSize: 11, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase',
        letterSpacing: 1, marginBottom: 8,
      }}>
        Style Fingerprint
      </div>
      {styles.slice(0, 12).map(s => (
        <GenreBar key={s.name} genre={s} maxPct={maxPct} />
      ))}
    </div>
  )
}

function DiversityMeter({ score }) {
  const pct = (score / 10) * 100
  const color = score >= 7 ? '#88eebb' : score >= 4 ? '#ffaa44' : '#ff6b6b'
  return (
    <div style={{ flex: 1 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', letterSpacing: 1 }}>
          Diversity
        </span>
        <span style={{ fontSize: 14, fontWeight: 600, color, fontFamily: "'JetBrains Mono', monospace" }}>
          {score}/10
        </span>
      </div>
      <div style={{ height: 4, background: 'rgba(255,255,255,0.06)', borderRadius: 2, overflow: 'hidden' }}>
        <div style={{
          width: `${pct}%`, height: '100%', background: color,
          borderRadius: 2, transition: 'width 0.8s ease-out',
          boxShadow: `0 0 12px ${color}66`,
        }} />
      </div>
    </div>
  )
}

function RarityBadge({ score }) {
  return (
    <div style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      padding: '4px 10px', borderRadius: 6,
      background: 'rgba(204,136,255,0.08)', border: '1px solid rgba(204,136,255,0.15)',
    }}>
      <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)' }}>Rarity</span>
      <span style={{ fontSize: 13, fontWeight: 600, color: '#cc88ff', fontFamily: "'JetBrains Mono', monospace" }}>
        {score}%
      </span>
      <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)' }}>rare releases</span>
    </div>
  )
}

function DecadeTimeline({ decades }) {
  if (!decades || decades.length === 0) return null
  const max = Math.max(...decades.map(d => d.pct))
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{
        fontSize: 11, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase',
        letterSpacing: 1, marginBottom: 8,
      }}>
        Timeline
      </div>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 4, height: 60 }}>
        {decades.map(d => {
          const h = max > 0 ? Math.max(4, (d.pct / max) * 52) : 4
          return (
            <div key={d.decade} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
              <span style={{ fontSize: 9, fontFamily: "'JetBrains Mono', monospace", color: 'rgba(255,255,255,0.25)' }}>
                {d.count}
              </span>
              <div style={{
                width: '100%', height: h, background: 'rgba(102,204,255,0.3)',
                borderRadius: '3px 3px 0 0', transition: 'height 0.6s ease-out',
                border: '1px solid rgba(102,204,255,0.15)',
              }} />
              <span style={{ fontSize: 9, fontFamily: "'JetBrains Mono', monospace", color: 'rgba(255,255,255,0.3)' }}>
                {d.decade.slice(2)}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function TopLabels({ labels }) {
  if (!labels || labels.length === 0) return null
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{
        fontSize: 11, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase',
        letterSpacing: 1, marginBottom: 8,
      }}>
        Top Labels
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
        {labels.map((l, i) => (
          <span key={l.name} style={{
            padding: '3px 8px', borderRadius: 4, fontSize: 11,
            background: i === 0 ? 'rgba(102,204,255,0.1)' : 'rgba(255,255,255,0.04)',
            border: `1px solid ${i === 0 ? 'rgba(102,204,255,0.2)' : 'rgba(255,255,255,0.06)'}`,
            color: i === 0 ? '#66ccff' : 'rgba(255,255,255,0.5)',
            fontFamily: "'JetBrains Mono', monospace",
          }}>
            {l.name} <span style={{ opacity: 0.5 }}>{l.count}</span>
          </span>
        ))}
      </div>
    </div>
  )
}

function GapAnalysis({ gaps }) {
  if (!gaps || gaps.length === 0) return null
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{
        fontSize: 11, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase',
        letterSpacing: 1, marginBottom: 8,
      }}>
        Discovery Gaps — Explore Next
      </div>
      {gaps.map(g => (
        <div key={g.genre} style={{
          padding: '8px 10px', marginBottom: 4, borderRadius: 6,
          background: 'rgba(255,170,68,0.04)', border: '1px solid rgba(255,170,68,0.08)',
        }}>
          <div style={{ fontSize: 12, fontWeight: 500, color: '#ffaa44', marginBottom: 2 }}>
            {g.genre}
          </div>
          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.35)', lineHeight: 1.4 }}>
            {g.reason}
          </div>
        </div>
      ))}
    </div>
  )
}

function WantlistSummary({ count }) {
  if (!count) return null
  return (
    <div style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      padding: '4px 10px', borderRadius: 6,
      background: 'rgba(255,107,157,0.08)', border: '1px solid rgba(255,107,157,0.15)',
    }}>
      <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)' }}>Wantlist</span>
      <span style={{ fontSize: 13, fontWeight: 600, color: '#ff6b9d', fontFamily: "'JetBrains Mono', monospace" }}>
        {count}
      </span>
      <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)' }}>releases</span>
    </div>
  )
}

function LoadingProgress({ phase, loaded, total }) {
  const messages = {
    collection: 'Loading collection',
    wantlist: 'Loading wantlist',
    analyzing: 'Analyzing your taste',
    cached: 'Loading from cache',
  }
  const msg = messages[phase] || 'Loading'
  const showCount = (phase === 'collection' || phase === 'wantlist') && total > 0

  return (
    <div style={{ textAlign: 'center', padding: '32px 0' }}>
      <div style={{
        fontSize: 13, color: 'rgba(255,255,255,0.6)', marginBottom: 12,
        fontFamily: "'JetBrains Mono', monospace",
      }}>
        {msg}...
      </div>
      {showCount && (
        <>
          <div style={{
            fontSize: 24, fontWeight: 600, color: '#66ccff',
            fontFamily: "'JetBrains Mono', monospace", marginBottom: 8,
          }}>
            {loaded}/{total}
          </div>
          <div style={{
            height: 3, background: 'rgba(255,255,255,0.06)', borderRadius: 2,
            overflow: 'hidden', maxWidth: 200, margin: '0 auto',
          }}>
            <div style={{
              width: total > 0 ? `${(loaded / total) * 100}%` : '0%',
              height: '100%', background: '#66ccff', borderRadius: 2,
              transition: 'width 0.3s ease-out',
            }} />
          </div>
        </>
      )}
      {phase === 'analyzing' && (
        <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.3)', marginTop: 8 }}>
          Computing genre fingerprint, rarity scores, gap analysis...
        </div>
      )}
    </div>
  )
}

export default function CollectionPassport() {
  const passportOpen = useStore(s => s.passportOpen)
  const setPassportOpen = useStore(s => s.setPassportOpen)
  const setDiscogsUsername = useStore(s => s.setDiscogsUsername)
  const tasteProfile = useStore(s => s.tasteProfile)
  const setTasteProfile = useStore(s => s.setTasteProfile)
  const setRecommendationsOpen = useStore(s => s.setRecommendationsOpen)
  const setShowCollectionOverlay = useStore(s => s.setShowCollectionOverlay)

  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [progress, setProgress] = useState({ phase: '', loaded: 0, total: 0 })

  // Restore from localStorage on mount
  useEffect(() => {
    if (tasteProfile) return
    try {
      const raw = localStorage.getItem('discoworld-discogs-cache')
      if (raw) {
        const cache = JSON.parse(raw)
        if (cache.profile && cache.username) {
          setDiscogsUsername(cache.username)
          setTasteProfile(cache.profile)
        }
      }
    } catch {
      // ignore
    }
  }, [tasteProfile, setDiscogsUsername, setTasteProfile])

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault()
    const username = inputValue.trim()
    if (!username) return

    setLoading(true)
    setError(null)

    try {
      const result = await importCollection(
        username,
        (phase, loaded, total) => setProgress({ phase, loaded, total }),
      )

      setDiscogsUsername(username)
      setTasteProfile(result.profile)

      if (!result.fromCache) {
        // Auto-enable collection overlay on first import
        setShowCollectionOverlay(true)
      }
    } catch (err) {
      if (err.message === 'USER_NOT_FOUND') {
        setError(`User "${username}" not found on Discogs. Check the username.`)
      } else if (err.message === 'COLLECTION_PRIVATE') {
        setError(`Collection for "${username}" is private. Make it public in Discogs settings.`)
      } else {
        setError(`Failed to fetch collection: ${err.message}`)
      }
    } finally {
      setLoading(false)
    }
  }, [inputValue, setDiscogsUsername, setTasteProfile, setShowCollectionOverlay])

  const handleRefresh = useCallback(async () => {
    const username = tasteProfile?.username
    if (!username) return

    setLoading(true)
    setError(null)
    clearCachedProfile()

    try {
      const result = await importCollection(
        username,
        (phase, loaded, total) => setProgress({ phase, loaded, total }),
        { force: true },
      )
      setTasteProfile(result.profile)
    } catch (err) {
      setError(`Refresh failed: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }, [tasteProfile, setTasteProfile])

  const handleDisconnect = useCallback(() => {
    setTasteProfile(null)
    setDiscogsUsername(null)
    setShowCollectionOverlay(false)
    clearCachedProfile()
  }, [setTasteProfile, setDiscogsUsername, setShowCollectionOverlay])

  if (!passportOpen) return null

  const profile = tasteProfile
  const maxGenrePct = profile ? Math.max(...profile.genres.map(g => g.pct)) : 0

  return (
    <div
      className="collection-passport-backdrop"
      onClick={() => setPassportOpen(false)}
      role="dialog"
      aria-modal="true"
      aria-label="Collection Passport"
      onKeyDown={(e) => { if (e.key === 'Escape') setPassportOpen(false) }}
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
          width: 440, maxWidth: 'calc(100vw - 32px)',
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
            <div style={{ fontSize: 16, fontWeight: 600, color: '#fff', letterSpacing: 0.5 }}>
              Collection Passport
            </div>
            <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.3)', fontFamily: "'JetBrains Mono', monospace" }}>
              Musical DNA
            </div>
          </div>
          <button
            onClick={() => setPassportOpen(false)}
            aria-label="Close Collection Passport"
            style={{
              background: 'none', border: 'none', color: 'rgba(255,255,255,0.4)',
              fontSize: 18, cursor: 'pointer', padding: '4px 8px',
            }}
          >
            x
          </button>
        </div>

        {/* Input form */}
        {!profile && !loading && (
          <form onSubmit={handleSubmit} style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.4)', marginBottom: 8, lineHeight: 1.5 }}>
              Enter your Discogs username to visualize your collection.
              <br />
              <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.25)' }}>
                Works with public collections — no login needed.
              </span>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <input
                type="text"
                value={inputValue}
                onChange={e => setInputValue(e.target.value)}
                placeholder="Discogs username"
                aria-label="Discogs username"
                autoFocus
                style={{
                  flex: 1, padding: '8px 12px', borderRadius: 8,
                  background: 'rgba(255,255,255,0.06)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  color: '#e0e0e0', fontFamily: 'inherit', fontSize: 13,
                  outline: 'none',
                }}
                onFocus={e => { e.target.style.borderColor = 'rgba(102,204,255,0.3)' }}
                onBlur={e => { e.target.style.borderColor = 'rgba(255,255,255,0.1)' }}
              />
              <button
                type="submit"
                disabled={!inputValue.trim()}
                aria-label="Import Discogs collection"
                style={{
                  padding: '8px 16px', borderRadius: 8,
                  background: 'rgba(102,204,255,0.12)',
                  border: '1px solid rgba(102,204,255,0.2)',
                  color: '#66ccff',
                  fontSize: 12, fontWeight: 500, cursor: 'pointer',
                  fontFamily: 'inherit',
                }}
              >
                Import
              </button>
            </div>
            {error && (
              <div style={{ fontSize: 11, color: '#ff6b6b', marginTop: 6, lineHeight: 1.4 }}>{error}</div>
            )}
          </form>
        )}

        {/* Loading progress */}
        {loading && (
          <LoadingProgress phase={progress.phase} loaded={progress.loaded} total={progress.total} />
        )}

        {/* Profile display */}
        {profile && !loading && (
          <>
            {/* User info */}
            <div style={{
              display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16,
              padding: '8px 10px', borderRadius: 8,
              background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)',
            }}>
              <div style={{
                width: 32, height: 32, borderRadius: '50%',
                background: 'rgba(102,204,255,0.15)', border: '1px solid rgba(102,204,255,0.2)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 14, color: '#66ccff',
              }}>
                {profile.username[0].toUpperCase()}
              </div>
              <div>
                <div style={{ fontSize: 13, fontWeight: 500, color: '#fff' }}>{profile.username}</div>
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.3)', fontFamily: "'JetBrains Mono', monospace" }}>
                  {profile.total_releases} releases
                  {profile.wantlist_count > 0 && ` + ${profile.wantlist_count} wanted`}
                </div>
              </div>
              <div style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
                <button
                  onClick={handleRefresh}
                  title="Refresh from Discogs"
                  aria-label="Refresh collection from Discogs"
                  style={{
                    background: 'none', border: 'none',
                    color: 'rgba(255,255,255,0.25)', fontSize: 13, cursor: 'pointer',
                    padding: '2px 6px',
                  }}
                  onMouseEnter={e => { e.target.style.color = '#66ccff' }}
                  onMouseLeave={e => { e.target.style.color = 'rgba(255,255,255,0.25)' }}
                >
                  &#x21bb;
                </button>
                <button
                  onClick={handleDisconnect}
                  aria-label="Disconnect Discogs account"
                  style={{
                    background: 'none', border: 'none',
                    color: 'rgba(255,255,255,0.25)', fontSize: 11, cursor: 'pointer',
                    fontFamily: "'JetBrains Mono', monospace",
                  }}
                >
                  disconnect
                </button>
              </div>
            </div>

            {/* Scores row */}
            <div style={{ display: 'flex', gap: 12, marginBottom: 16, alignItems: 'flex-start' }}>
              <DiversityMeter score={profile.diversity_score} />
              <RarityBadge score={profile.rarity_score} />
            </div>
            {profile.wantlist_count > 0 && (
              <div style={{ marginBottom: 16 }}>
                <WantlistSummary count={profile.wantlist_count} />
              </div>
            )}

            {/* Genre distribution */}
            <div style={{
              fontSize: 11, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase',
              letterSpacing: 1, marginBottom: 8,
            }}>
              Genre Distribution
            </div>
            <div style={{ marginBottom: 16 }}>
              {profile.genres.map(g => (
                <GenreBar key={g.name} genre={g} maxPct={maxGenrePct} />
              ))}
            </div>

            {/* Style fingerprint (more specific than genres) */}
            <StyleBars styles={profile.styles} />

            {/* Timeline */}
            <DecadeTimeline decades={profile.decades} />

            {/* Top labels */}
            <TopLabels labels={profile.top_labels} />

            {/* Gap analysis */}
            <GapAnalysis gaps={profile.gaps} />

            {/* Actions */}
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                onClick={() => { setPassportOpen(false); setShowCollectionOverlay(true) }}
                style={{
                  flex: 1, padding: '10px 16px', borderRadius: 8,
                  background: 'rgba(255,215,0,0.08)', border: '1px solid rgba(255,215,0,0.2)',
                  color: '#FFD700', fontSize: 12, fontWeight: 500,
                  cursor: 'pointer', fontFamily: 'inherit',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={e => { e.target.style.background = 'rgba(255,215,0,0.15)' }}
                onMouseLeave={e => { e.target.style.background = 'rgba(255,215,0,0.08)' }}
              >
                Show on Map
              </button>
              <button
                onClick={() => { setPassportOpen(false); setRecommendationsOpen(true) }}
                style={{
                  flex: 1, padding: '10px 16px', borderRadius: 8,
                  background: 'rgba(102,204,255,0.1)', border: '1px solid rgba(102,204,255,0.2)',
                  color: '#66ccff', fontSize: 12, fontWeight: 500,
                  cursor: 'pointer', fontFamily: 'inherit',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={e => { e.target.style.background = 'rgba(102,204,255,0.18)' }}
                onMouseLeave={e => { e.target.style.background = 'rgba(102,204,255,0.1)' }}
              >
                Recommendations
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
