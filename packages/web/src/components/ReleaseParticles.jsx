import { useRef, useMemo, useState, useEffect } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import useStore from '../stores/useStore'
import useAudioStore from '../stores/useAudioStore'

const _color = new THREE.Color()

// Deterministic-ish y offsets to avoid impure Math.random in render
function buildParticleBuffers(particles) {
  const n = particles.length
  const pos = new Float32Array(n * 3)
  const col = new Float32Array(n * 3)
  for (let i = 0; i < n; i++) {
    const p = particles[i]
    pos[i * 3] = p.x
    // Use index-based pseudo-random offset instead of Math.random
    pos[i * 3 + 1] = 0.2 + ((i * 7919) % 1000) / 2000
    pos[i * 3 + 2] = p.z

    _color.set(p.color)
    col[i * 3] = _color.r
    col[i * 3 + 1] = _color.g
    col[i * 3 + 2] = _color.b
  }
  return { positions: pos, colors: col, count: n }
}

export default function ReleaseParticles({ maxCount }) {
  const [data, setData] = useState(null)
  const pointsRef = useRef()
  const prevYearRef = useRef(null)
  const year = useStore(s => s.year)


  // Load particle data
  useEffect(() => {
    fetch('/data/release_particles.json')
      .then(r => r.json())
      .then(d => setData(d))
      .catch(() => {}) // Silently fail if not available
  }, [])

  const { positions, colors, count } = useMemo(() => {
    if (!data) return { positions: null, colors: null, count: 0 }
    const particles = maxCount ? data.particles.slice(0, maxCount) : data.particles
    return buildParticleBuffers(particles)
  }, [data, maxCount])

  // Animate opacity based on timeline year + audio-reactive position kicks
  const yearDirtyRef = useRef(true)
  useEffect(() => { yearDirtyRef.current = true }, [year])

  useFrame((state) => {
    if (!pointsRef.current || !colors || !data) return

    const { energy, beat } = useAudioStore.getState()
    const posAttr = pointsRef.current.geometry.getAttribute('position')

    // Update colors only when year changes
    if (yearDirtyRef.current) {
      yearDirtyRef.current = false
      prevYearRef.current = year

      const colorAttr = pointsRef.current.geometry.getAttribute('color')
      if (!colorAttr) return

      const particles = data.particles
      for (let i = 0; i < count; i++) {
        const p = particles[i]
        const visible = p.year <= year
        const opacity = visible ? Math.min(0.6, (year - p.year + 3) / 15) : 0

        _color.set(p.color)
        colorAttr.array[i * 3] = _color.r * opacity
        colorAttr.array[i * 3 + 1] = _color.g * opacity
        colorAttr.array[i * 3 + 2] = _color.b * opacity
      }
      colorAttr.needsUpdate = true
    }

    // Pulse particle size on beat
    if (pointsRef.current.material) {
      pointsRef.current.material.size = 0.15 + energy * 0.08 + (beat ? 0.06 : 0)
    }

    // Audio-reactive: subtle y-axis float driven by energy + beat kick
    if (posAttr && energy > 0.01) {
      const t = state.clock.elapsedTime
      const beatLift = beat ? 0.4 : 0
      const particles = data.particles
      for (let i = 0; i < count; i++) {
        const baseY = 0.2 + ((i * 7919) % 1000) / 2000
        // Each particle oscillates slightly, phase-offset by index
        const audioY = Math.sin(t * 1.5 + i * 0.37) * energy * 0.3 + beatLift
        posAttr.array[i * 3 + 1] = baseY + audioY
      }
      posAttr.needsUpdate = true
    }
  })

  if (!positions) return null

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          array={positions}
          count={count}
          itemSize={3}
        />
        <bufferAttribute
          attach="attributes-color"
          array={colors}
          count={count}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.15}
        vertexColors
        transparent
        opacity={0.7}
        sizeAttenuation
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </points>
  )
}
