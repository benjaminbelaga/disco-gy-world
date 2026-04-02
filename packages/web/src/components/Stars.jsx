import { useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import useAudioStore from '../stores/useAudioStore'

// Generate star positions once at module level (deterministic per session)
function generateStarPositions(count) {
  const pos = new Float32Array(count * 3)
  for (let i = 0; i < count; i++) {
    const theta = Math.random() * Math.PI * 2
    const phi = Math.acos(2 * Math.random() - 1)
    const r = 80 + Math.random() * 60
    pos[i * 3] = r * Math.sin(phi) * Math.cos(theta)
    pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta) * 0.5 + 20
    pos[i * 3 + 2] = r * Math.cos(phi)
  }
  return pos
}

function generateStarSizes(count) {
  const s = new Float32Array(count)
  for (let i = 0; i < count; i++) {
    s[i] = 0.1 + Math.random() * 0.3
  }
  return s
}

// Pre-generated at module scope — no impure calls during render
const _cachedPositions = {}
const _cachedSizes = {}

function getCachedPositions(count) {
  if (!_cachedPositions[count]) _cachedPositions[count] = generateStarPositions(count)
  return _cachedPositions[count]
}

function getCachedSizes(count) {
  if (!_cachedSizes[count]) _cachedSizes[count] = generateStarSizes(count)
  return _cachedSizes[count]
}

export default function Stars({ count = 2000 }) {
  const meshRef = useRef()
  const positions = getCachedPositions(count)
  const sizes = getCachedSizes(count)

  useFrame((state) => {
    if (meshRef.current) {
      const { mid, high } = useAudioStore.getState()
      const baseSpeed = 0.005
      meshRef.current.rotation.y = state.clock.elapsedTime * (baseSpeed + baseSpeed * mid * 3)
      // Modulate opacity with high frequency band
      meshRef.current.material.opacity = 0.4 + high * 0.35
    }
  })

  return (
    <points ref={meshRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          array={positions}
          count={count}
          itemSize={3}
        />
        <bufferAttribute
          attach="attributes-size"
          array={sizes}
          count={count}
          itemSize={1}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.15}
        color="#ffffff"
        transparent
        opacity={0.4}
        sizeAttenuation
        depthWrite={false}
      />
    </points>
  )
}
