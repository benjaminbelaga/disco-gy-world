import { useEffect, useMemo, useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import useStore from '../stores/useStore'

// Color gradient: blue (past) to amber (present)
const PAST_COLOR = new THREE.Color('#4488ff')
const PRESENT_COLOR = new THREE.Color('#ffaa33')

function lerp(a, b, t) {
  return a + (b - a) * t
}

// Thread line connecting release positions across genres
function ThreadLine({ points }) {
  const ref = useRef()

  const geometry = useMemo(() => {
    if (points.length < 2) return null

    // Build a smooth curve through all points
    const vectors = points.map(p => new THREE.Vector3(p.x, p.y + 1, p.z))
    const curve = new THREE.CatmullRomCurve3(vectors, false, 'centripetal', 0.5)
    const segmentCount = Math.max(points.length * 8, 24)
    const curvePoints = curve.getPoints(segmentCount)

    const geo = new THREE.BufferGeometry().setFromPoints(curvePoints)

    // Per-vertex color gradient from past to present
    const colors = new Float32Array(curvePoints.length * 3)
    const tmpColor = new THREE.Color()
    for (let i = 0; i < curvePoints.length; i++) {
      const t = i / (curvePoints.length - 1)
      tmpColor.copy(PAST_COLOR).lerp(PRESENT_COLOR, t)
      colors[i * 3] = tmpColor.r
      colors[i * 3 + 1] = tmpColor.g
      colors[i * 3 + 2] = tmpColor.b
    }
    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3))
    return geo
  }, [points])

  useFrame((state) => {
    if (!ref.current) return
    // Subtle pulse on the line opacity
    const t = state.clock.elapsedTime
    ref.current.material.opacity = 0.35 + Math.sin(t * 1.5) * 0.1
  })

  if (!geometry) return null

  return (
    <line ref={ref} geometry={geometry}>
      <lineBasicMaterial
        vertexColors
        transparent
        opacity={0.4}
        linewidth={2}
      />
    </line>
  )
}

// Marker at each release position along the thread
function ReleaseMarker({ position, color, size }) {
  const ref = useRef()

  useFrame((state) => {
    if (!ref.current) return
    const t = state.clock.elapsedTime
    ref.current.material.opacity = 0.4 + Math.sin(t * 2 + position.x) * 0.15
  })

  return (
    <mesh ref={ref} position={[position.x, position.y + 1, position.z]}>
      <sphereGeometry args={[size, 12, 12]} />
      <meshBasicMaterial
        color={color}
        transparent
        opacity={0.5}
        depthWrite={false}
      />
    </mesh>
  )
}

// Artist info panel with discography + mini timeline
function ArtistPanel({ artist, timeline, genres, yearMin, yearMax, onClose, onClickRelease }) {
  const currentTrack = useStore(s => s.currentTrack)
  const playing = useStore(s => s.playing)
  const yearsText = yearMin && yearMax
    ? yearMin === yearMax ? `${yearMin}` : `${yearMin} - ${yearMax}`
    : ''

  const timelineSpan = yearMax && yearMin ? yearMax - yearMin : 1

  return (
    <div
      style={{
        position: 'fixed',
        right: 24,
        top: 72,
        width: 320,
        maxHeight: 'calc(100vh - 160px)',
        background: 'rgba(15, 15, 25, 0.92)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        border: '1px solid rgba(68, 136, 255, 0.2)',
        borderRadius: 12,
        padding: 20,
        zIndex: 16,
        overflowY: 'auto',
        animation: 'onboarding-card-in 0.3s ease-out',
      }}
    >
      <button
        className="close-btn"
        onClick={onClose}
        aria-label="Close artist panel"
      >
        &times;
      </button>

      <div style={{
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: 10, textTransform: 'uppercase', letterSpacing: 1.5,
        color: 'rgba(68, 136, 255, 0.6)', marginBottom: 4,
      }}>
        Artist Thread
      </div>

      <h2 style={{ fontSize: 20, fontWeight: 600, color: '#fff', marginBottom: 4 }}>
        {artist}
      </h2>

      {yearsText && (
        <div style={{
          fontSize: 12, color: 'rgba(255,255,255,0.4)',
          fontFamily: "'JetBrains Mono', monospace",
          marginBottom: 12,
        }}>
          {yearsText} / {timeline.length} releases / {genres.length} genres
        </div>
      )}

      {/* Mini timeline bar */}
      {yearMin && yearMax && timelineSpan > 0 && (
        <div style={{
          position: 'relative',
          height: 24,
          marginBottom: 16,
          background: 'rgba(255,255,255,0.04)',
          borderRadius: 4,
          overflow: 'hidden',
        }}>
          {/* Gradient background */}
          <div style={{
            position: 'absolute', inset: 0,
            background: 'linear-gradient(to right, rgba(68,136,255,0.15), rgba(255,170,51,0.15))',
            borderRadius: 4,
          }} />
          {/* Release dots */}
          {timeline.map((r, i) => {
            const pct = timelineSpan > 0 ? ((r.year - yearMin) / timelineSpan) * 100 : 50
            return (
              <div
                key={i}
                title={`${r.title} (${r.year})`}
                style={{
                  position: 'absolute',
                  left: `${pct}%`,
                  top: '50%',
                  transform: 'translate(-50%, -50%)',
                  width: 6,
                  height: 6,
                  borderRadius: '50%',
                  background: '#fff',
                  opacity: 0.7,
                  cursor: 'pointer',
                  boxShadow: '0 0 4px rgba(255,255,255,0.5)',
                }}
                onClick={() => onClickRelease(r)}
              />
            )
          })}
          {/* Year labels */}
          <span style={{
            position: 'absolute', left: 4, bottom: 2,
            fontSize: 9, color: 'rgba(68,136,255,0.6)',
            fontFamily: "'JetBrains Mono', monospace",
          }}>
            {yearMin}
          </span>
          <span style={{
            position: 'absolute', right: 4, bottom: 2,
            fontSize: 9, color: 'rgba(255,170,51,0.6)',
            fontFamily: "'JetBrains Mono', monospace",
          }}>
            {yearMax}
          </span>
        </div>
      )}

      {/* Genre tags */}
      {genres.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 14 }}>
          {genres.map(g => (
            <span key={g.slug} style={{
              fontSize: 10, padding: '2px 8px', borderRadius: 4,
              background: 'rgba(68,136,255,0.08)',
              border: '1px solid rgba(68,136,255,0.15)',
              color: 'rgba(68,136,255,0.7)',
              fontFamily: "'JetBrains Mono', monospace",
              textTransform: 'uppercase', letterSpacing: 0.5,
            }}>
              {g.name}
            </span>
          ))}
        </div>
      )}

      {/* Discography list */}
      <div style={{
        fontSize: 11, textTransform: 'uppercase', letterSpacing: 1,
        opacity: 0.4, marginBottom: 8,
      }}>
        Discography
      </div>
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {timeline.map((r, i) => {
          const isPlaying = currentTrack && playing &&
            currentTrack.artist === artist && currentTrack.title === r.title
          // Color gradient per release position
          const t = timeline.length > 1 ? i / (timeline.length - 1) : 0
          const dotColor = `rgb(${Math.round(lerp(68, 255, t))}, ${Math.round(lerp(136, 170, t))}, ${Math.round(lerp(255, 51, t))})`

          return (
            <li
              key={i}
              onClick={() => onClickRelease(r)}
              style={{
                padding: '8px 0',
                borderBottom: '1px solid rgba(255,255,255,0.05)',
                fontSize: 13,
                cursor: 'pointer',
                color: isPlaying ? '#88ccff' : 'rgba(255,255,255,0.75)',
                transition: 'color 0.2s',
                display: 'flex',
                alignItems: 'flex-start',
                gap: 8,
              }}
            >
              <span style={{
                width: 8, height: 8, borderRadius: '50%',
                background: dotColor,
                flexShrink: 0, marginTop: 4,
                boxShadow: `0 0 6px ${dotColor}`,
              }} />
              <div style={{ minWidth: 0 }}>
                <div style={{ fontWeight: 500 }}>{r.title}</div>
                <div style={{
                  fontSize: 11, opacity: 0.4, marginTop: 1,
                  fontFamily: "'JetBrains Mono', monospace",
                }}>
                  {r.label}{r.catno ? ` [${r.catno}]` : ''} / {r.year}
                </div>
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

export default function ArtistThread() {
  const activeArtist = useStore(s => s.activeArtist)
  const artistTimeline = useStore(s => s.artistTimeline)
  const setArtistTimeline = useStore(s => s.setArtistTimeline)
  const genres = useStore(s => s.genres)

  // Fetch artist data when activeArtist changes
  useEffect(() => {
    if (!activeArtist) {
      setArtistTimeline([])
      return
    }

    fetch(`/api/artists/${encodeURIComponent(activeArtist)}/timeline`)
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data) setArtistTimeline(data)
      })
      .catch(() => setArtistTimeline([]))
  }, [activeArtist, setArtistTimeline])

  // Map timeline releases to genre world positions
  const threadPoints = useMemo(() => {
    if (!artistTimeline?.timeline || !genres.length) return []

    const points = []
    for (const release of artistTimeline.timeline) {
      if (!release.genres?.length) continue
      // Find the genre sphere position for the first genre
      const genreMatch = genres.find(g =>
        release.genres.some(rg => rg.slug === g.slug)
      )
      if (genreMatch) {
        points.push({
          x: genreMatch.x,
          y: genreMatch.y,
          z: genreMatch.z,
          year: release.year,
          release,
        })
      }
    }
    return points
  }, [artistTimeline, genres])

  if (!activeArtist) return null

  return (
    <>
      {/* R3F thread line + markers */}
      {threadPoints.length >= 2 && (
        <group>
          <ThreadLine
            points={threadPoints}
            yearMin={artistTimeline?.year_min}
            yearMax={artistTimeline?.year_max}
          />
          {threadPoints.map((p, i) => {
            const t = threadPoints.length > 1 ? i / (threadPoints.length - 1) : 0
            const color = new THREE.Color().copy(PAST_COLOR).lerp(PRESENT_COLOR, t)
            return (
              <ReleaseMarker
                key={i}
                position={p}
                color={color}
                size={0.6}
              />
            )
          })}
        </group>
      )}
    </>
  )
}

// Separate panel component (rendered outside Canvas in the DOM)
export function ArtistThreadPanel() {
  const activeArtist = useStore(s => s.activeArtist)
  const setActiveArtist = useStore(s => s.setActiveArtist)
  const artistTimeline = useStore(s => s.artistTimeline)
  const setCurrentTrack = useStore(s => s.setCurrentTrack)
  const setCameraTarget = useStore(s => s.setCameraTarget)
  const genres = useStore(s => s.genres)

  const handleClickRelease = (release) => {
    // Fly to the genre sphere and play the track
    if (release.genres?.length) {
      const genreMatch = genres.find(g =>
        release.genres.some(rg => rg.slug === g.slug)
      )
      if (genreMatch) {
        setCameraTarget(genreMatch)
      }
    }
    if (release.youtube_url) {
      setCurrentTrack({
        artist: activeArtist,
        title: release.title,
        youtube: release.youtube_url,
        year: release.year,
      })
    }
  }

  if (!activeArtist || !artistTimeline?.timeline) return null

  return (
    <ArtistPanel
      artist={activeArtist}
      timeline={artistTimeline.timeline || []}
      genres={artistTimeline.genres || []}
      yearMin={artistTimeline.year_min}
      yearMax={artistTimeline.year_max}
      onClose={() => setActiveArtist(null)}
      onClickRelease={handleClickRelease}
    />
  )
}
