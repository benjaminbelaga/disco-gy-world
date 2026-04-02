import { useEffect, useMemo, useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import useStore from '../stores/useStore'

// Curved line between two genre positions
function ConstellationLine({ from, to, color, opacity }) {
  const points = useMemo(() => {
    const mid = new THREE.Vector3(
      (from.x + to.x) / 2,
      Math.max(from.y, to.y) + 3,
      (from.z + to.z) / 2
    )
    const curve = new THREE.QuadraticBezierCurve3(
      new THREE.Vector3(from.x, from.y, from.z),
      mid,
      new THREE.Vector3(to.x, to.y, to.z)
    )
    return curve.getPoints(24)
  }, [from, to])

  const geo = useMemo(() => {
    return new THREE.BufferGeometry().setFromPoints(points)
  }, [points])

  return (
    <line geometry={geo}>
      <lineBasicMaterial color={color} transparent opacity={opacity} />
    </line>
  )
}

// Pulsing glow ring around a connected genre sphere
function GlowMarker({ position, color, size }) {
  const ref = useRef()

  useFrame((state) => {
    if (!ref.current) return
    const t = state.clock.elapsedTime
    const s = 1 + Math.sin(t * 2) * 0.2
    ref.current.scale.setScalar(s)
    ref.current.material.opacity = 0.15 + Math.sin(t * 3) * 0.08
  })

  return (
    <mesh ref={ref} position={[position.x, position.y, position.z]}>
      <ringGeometry args={[size * 1.2, size * 1.8, 32]} />
      <meshBasicMaterial
        color={color}
        transparent
        opacity={0.15}
        side={THREE.DoubleSide}
        depthWrite={false}
      />
    </mesh>
  )
}

// Label info overlay (glassmorphism)
function LabelOverlay({ label, genreCount, releaseCount, yearMin, yearMax, onClose }) {
  const yearsText = yearMin && yearMax
    ? yearMin === yearMax ? `${yearMin}` : `${yearMin} - ${yearMax}`
    : 'Unknown'

  return (
    <div
      className="label-overlay"
      style={{
        position: 'fixed',
        left: 24,
        bottom: 80,
        zIndex: 25,
        background: 'rgba(12, 12, 25, 0.88)',
        backdropFilter: 'blur(24px)',
        WebkitBackdropFilter: 'blur(24px)',
        border: '1px solid rgba(255, 200, 100, 0.2)',
        borderRadius: 14,
        padding: '16px 20px',
        minWidth: 220,
        boxShadow: '0 8px 32px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.06)',
        animation: 'onboarding-card-in 0.3s ease-out',
      }}
      onClick={(e) => e.stopPropagation()}
    >
      <button
        onClick={onClose}
        style={{
          position: 'absolute', top: 8, right: 10,
          background: 'none', border: 'none',
          color: 'rgba(255,255,255,0.35)', fontSize: 16,
          cursor: 'pointer', padding: '2px 6px',
        }}
      >
        x
      </button>
      <div style={{
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: 10, textTransform: 'uppercase', letterSpacing: 1.5,
        color: 'rgba(255, 200, 100, 0.6)', marginBottom: 6,
      }}>
        Label
      </div>
      <div style={{ fontSize: 18, fontWeight: 600, color: '#fff', marginBottom: 10 }}>
        {label}
      </div>
      <div style={{
        display: 'flex', gap: 16,
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: 11, color: 'rgba(255,255,255,0.5)',
      }}>
        <span>{releaseCount} releases</span>
        <span>{genreCount} genres</span>
      </div>
      <div style={{
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: 11, color: 'rgba(255,255,255,0.35)',
        marginTop: 6,
      }}>
        Active: {yearsText}
      </div>
    </div>
  )
}

export default function LabelConstellation() {
  const activeLabel = useStore(s => s.activeLabel)
  const setActiveLabel = useStore(s => s.setActiveLabel)
  const labelReleases = useStore(s => s.labelReleases)
  const setLabelReleases = useStore(s => s.setLabelReleases)
  const genres = useStore(s => s.genres)

  // Fetch label data when activeLabel changes
  useEffect(() => {
    if (!activeLabel) {
      setLabelReleases([])
      return
    }

    fetch(`/api/labels/${encodeURIComponent(activeLabel)}/genres`)
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data) setLabelReleases(data)
      })
      .catch(() => setLabelReleases([]))
  }, [activeLabel, setLabelReleases])

  // Map label genres to genre world positions
  const connectedGenres = useMemo(() => {
    if (!labelReleases?.genres || !genres.length) return []
    const slugSet = new Set(labelReleases.genres.map(g => g.slug))
    return genres.filter(g => slugSet.has(g.slug))
  }, [labelReleases, genres])

  // Generate connection lines between all connected genre pairs
  const connections = useMemo(() => {
    const lines = []
    for (let i = 0; i < connectedGenres.length; i++) {
      for (let j = i + 1; j < connectedGenres.length; j++) {
        lines.push({
          from: connectedGenres[i],
          to: connectedGenres[j],
          key: `${connectedGenres[i].slug}-${connectedGenres[j].slug}`,
        })
      }
    }
    // Limit to avoid visual clutter
    return lines.slice(0, 30)
  }, [connectedGenres])

  if (!activeLabel || connectedGenres.length === 0) {
    // Still render overlay if we have label data but no genre matches yet
    if (activeLabel && labelReleases?.release_count) {
      return (
        <LabelOverlay
          label={activeLabel}
          genreCount={labelReleases.genres?.length || 0}
          releaseCount={labelReleases.release_count || 0}
          yearMin={labelReleases.year_min}
          yearMax={labelReleases.year_max}
          onClose={() => setActiveLabel(null)}
        />
      )
    }
    return null
  }

  const lineColor = '#ffcc66'

  return (
    <>
      {/* R3F elements — rendered inside Canvas via GenreWorld */}
      <group>
        {connections.map(c => (
          <ConstellationLine
            key={c.key}
            from={c.from}
            to={c.to}
            color={lineColor}
            opacity={0.25}
          />
        ))}
        {connectedGenres.map(g => (
          <GlowMarker
            key={g.slug}
            position={g}
            color={lineColor}
            size={g.size || 1}
          />
        ))}
      </group>
    </>
  )
}

// Separate HTML overlay component (rendered outside Canvas)
export function LabelConstellationOverlay() {
  const activeLabel = useStore(s => s.activeLabel)
  const setActiveLabel = useStore(s => s.setActiveLabel)
  const labelReleases = useStore(s => s.labelReleases)

  if (!activeLabel || !labelReleases?.release_count) return null

  return (
    <LabelOverlay
      label={activeLabel}
      genreCount={labelReleases.genres?.length || 0}
      releaseCount={labelReleases.release_count || 0}
      yearMin={labelReleases.year_min}
      yearMax={labelReleases.year_max}
      onClose={() => setActiveLabel(null)}
    />
  )
}
