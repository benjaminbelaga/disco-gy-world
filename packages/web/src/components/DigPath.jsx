import { useRef, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import { Html } from '@react-three/drei'
import * as THREE from 'three'
import useStore from '../stores/useStore'
import useAudioStore from '../stores/useAudioStore'

// Glowing path line connecting waypoints in 3D space
function PathLine({ points, color }) {
  const lineRef = useRef()

  useFrame((state) => {
    if (!lineRef.current) return
    const t = state.clock.elapsedTime
    const energy = useAudioStore.getState().energy
    // Pulse opacity with music
    lineRef.current.material.opacity = 0.4 + Math.sin(t * 2) * 0.1 + energy * 0.2
  })

  const geometry = useMemo(() => {
    if (points.length < 2) return null
    // Build smooth curve through all waypoints
    const vectors = points.map(p => new THREE.Vector3(p.x, p.y + 1, p.z))

    if (vectors.length === 2) {
      const mid = new THREE.Vector3().lerpVectors(vectors[0], vectors[1], 0.5)
      mid.y += 3
      const curve = new THREE.QuadraticBezierCurve3(vectors[0], mid, vectors[1])
      return new THREE.BufferGeometry().setFromPoints(curve.getPoints(32))
    }

    // CatmullRom for 3+ points
    const curve = new THREE.CatmullRomCurve3(vectors, false, 'centripetal', 0.5)
    return new THREE.BufferGeometry().setFromPoints(curve.getPoints(points.length * 16))
  }, [points])

  if (!geometry) return null

  return (
    <line ref={lineRef} geometry={geometry}>
      <lineBasicMaterial
        color={color || '#ff66ff'}
        transparent
        opacity={0.5}
        linewidth={2}
        depthWrite={false}
      />
    </line>
  )
}

// Waypoint markers along the path
function WaypointMarkers({ waypoints, genreMap, activeIndex }) {
  const groupRef = useRef()

  useFrame((state) => {
    if (!groupRef.current) return
    const t = state.clock.elapsedTime
    groupRef.current.children.forEach((child, i) => {
      // Gentle float
      const baseY = child.userData.baseY || 0
      child.position.y = baseY + Math.sin(t * 1.5 + i * 0.8) * 0.2
      // Active waypoint pulses
      if (i === activeIndex) {
        const s = 1 + Math.sin(t * 4) * 0.2
        child.scale.setScalar(s)
      } else {
        child.scale.setScalar(1)
      }
    })
  })

  return (
    <group ref={groupRef}>
      {waypoints.map((wp, i) => {
        const genre = genreMap[wp.slug]
        if (!genre) return null

        return (
          <group
            key={`${wp.slug}-${i}`}
            position={[genre.x, genre.y + 2, genre.z]}
            userData={{ baseY: genre.y + 2 }}
          >
            {/* Diamond marker */}
            <mesh rotation={[0, 0, Math.PI / 4]}>
              <planeGeometry args={[0.8, 0.8]} />
              <meshBasicMaterial
                color={i === activeIndex ? '#ffffff' : '#ff66ff'}
                transparent
                opacity={i === activeIndex ? 0.9 : 0.6}
                side={THREE.DoubleSide}
                depthWrite={false}
              />
            </mesh>

            {/* Waypoint number */}
            <Html center style={{ pointerEvents: 'none', userSelect: 'none' }}>
              <div style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 10,
                color: '#ff66ff',
                background: 'rgba(12, 12, 20, 0.7)',
                backdropFilter: 'blur(8px)',
                padding: '2px 6px',
                borderRadius: 4,
                border: '1px solid rgba(255, 100, 255, 0.2)',
                whiteSpace: 'nowrap',
                transform: 'translateY(-18px)',
              }}>
                {i + 1}{wp.note ? ` — ${wp.note}` : ''}
              </div>
            </Html>
          </group>
        )
      })}
    </group>
  )
}

export default function DigPath() {
  const digPathMode = useStore(s => s.digPathMode)
  const waypoints = useStore(s => s.digPathWaypoints)
  const genres = useStore(s => s.genres)
  const playbackIndex = useStore(s => s.digPathPlaybackIndex)
  const digPathPlaying = useStore(s => s.digPathPlaying)

  // Build slug -> genre lookup
  const genreMap = useMemo(() => {
    const map = {}
    genres.forEach(g => { map[g.slug] = g })
    return map
  }, [genres])

  // Resolve waypoints to 3D positions
  const points = useMemo(() => {
    return waypoints
      .map(w => genreMap[w.slug])
      .filter(Boolean)
  }, [waypoints, genreMap])

  if (!digPathMode || waypoints.length === 0) return null

  return (
    <group>
      <PathLine points={points} color="#ff66ff" />
      <WaypointMarkers
        waypoints={waypoints}
        genreMap={genreMap}
        activeIndex={digPathPlaying ? playbackIndex : -1}
      />
    </group>
  )
}
