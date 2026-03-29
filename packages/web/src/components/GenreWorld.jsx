import { useRef, useMemo, useCallback } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import { Html, Text } from '@react-three/drei'
import * as THREE from 'three'
import useStore from '../stores/useStore'
import useAudioStore from '../stores/useAudioStore'
import GenreWorldBuildings from './GenreWorldBuildings'
import MysteryNode from './MysteryNode'
import DigPath from './DigPath'
import LabelConstellation from './LabelConstellation'
import ArtistThread from './ArtistThread'

// Shared geometry + material refs (created once)
const _sphere = new THREE.SphereGeometry(1, 24, 24)
const _wireframeSphere = new THREE.SphereGeometry(1, 12, 12)
const _color = new THREE.Color()
const _obj = new THREE.Object3D()
// Module-level mutable color buffer for instanced mesh (avoids ref-during-render lint)
let _instanceColors = null
let _instanceColorsCount = 0
function getInstanceColors(count) {
  if (_instanceColorsCount !== count) {
    _instanceColors = new Float32Array(count * 3)
    _instanceColorsCount = count
  }
  return _instanceColors
}

// Ground plane with grid
function Ground() {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -2, 0]} receiveShadow>
      <planeGeometry args={[200, 200]} />
      <meshStandardMaterial
        color="#0a0a0e"
        transparent
        opacity={0.8}
      />
    </mesh>
  )
}

// Grid lines on ground
function Grid() {
  return (
    <gridHelper
      args={[200, 80, '#1a1a2e', '#12121f']}
      position={[0, -1.9, 0]}
    />
  )
}

// Ground glow rings beneath each scene cluster
function GlowRings({ genres }) {
  const ringsRef = useRef()

  const rings = useMemo(() => {
    const groups = {}
    genres.forEach(g => {
      if (!groups[g.scene]) groups[g.scene] = { xs: [], zs: [], color: g.color }
      groups[g.scene].xs.push(g.x)
      groups[g.scene].zs.push(g.z)
    })
    return Object.entries(groups).map(([scene, data]) => {
      const cx = data.xs.reduce((a, b) => a + b, 0) / data.xs.length
      const cz = data.zs.reduce((a, b) => a + b, 0) / data.zs.length
      // radius = max distance from centroid + padding
      const maxDist = Math.max(
        ...data.xs.map((x, i) => Math.sqrt((x - cx) ** 2 + (data.zs[i] - cz) ** 2))
      )
      return { scene, cx, cz, radius: maxDist + 4, color: data.color }
    })
  }, [genres])

  useFrame((state) => {
    if (!ringsRef.current) return
    const bass = useAudioStore.getState().bass
    ringsRef.current.children.forEach((mesh, i) => {
      // Subtle pulse, amplified by bass
      const baseAmplitude = 0.02
      const amplitude = baseAmplitude + bass * 0.13
      const s = 1 + Math.sin(state.clock.elapsedTime * 0.3 + i * 1.5) * amplitude
      mesh.scale.set(s, s, 1)
    })
  })

  return (
    <group ref={ringsRef}>
      {rings.map(r => (
        <mesh
          key={r.scene}
          rotation={[-Math.PI / 2, 0, 0]}
          position={[r.cx, -1.85, r.cz]}
        >
          <ringGeometry args={[r.radius * 0.85, r.radius, 64]} />
          <meshBasicMaterial
            color={r.color}
            transparent
            opacity={0.06}
            side={THREE.DoubleSide}
            depthWrite={false}
          />
        </mesh>
      ))}
    </group>
  )
}

// Gold ring geometry for collection overlay (created once)
const _ring = new THREE.TorusGeometry(1, 0.06, 8, 32)
const _goldColor = new THREE.Color('#FFD700')

// Collection gold rings around owned genres
function CollectionRings({ genres }) {
  const meshRef = useRef()
  const year = useStore(s => s.year)
  const collectionGenres = useStore(s => s.collectionGenres)
  const showOverlay = useStore(s => s.showCollectionOverlay)

  const ownedGenres = useMemo(() => {
    if (!showOverlay) return []
    return genres
      .map((g, i) => ({ ...g, idx: i, count: collectionGenres[g.slug] || 0 }))
      .filter(g => g.count > 0)
  }, [genres, collectionGenres, showOverlay])

  const count = ownedGenres.length

  useFrame((state) => {
    if (!meshRef.current || count === 0) return
    const t = state.clock.elapsedTime
    const maxCount = Math.max(1, ...ownedGenres.map(g => g.count))

    for (let i = 0; i < count; i++) {
      const g = ownedGenres[i]
      const visible = g.year <= year
      if (!visible) {
        _obj.position.set(0, -999, 0)
        _obj.scale.setScalar(0.001)
      } else {
        const floatY = g.y + Math.sin(t * 0.5 + g.x * 0.1) * 0.3
        _obj.position.set(g.x, floatY, g.z)
        // Ring scale proportional to sphere size, intensity by count
        const intensity = 0.6 + 0.4 * (g.count / maxCount)
        const ringScale = g.size * 1.3 * intensity
        _obj.scale.setScalar(ringScale)
        // Gentle rotation
        _obj.rotation.set(Math.PI / 2, 0, t * 0.3 + g.x)
      }
      _obj.updateMatrix()
      meshRef.current.setMatrixAt(i, _obj.matrix)
    }
    meshRef.current.instanceMatrix.needsUpdate = true
  })

  if (count === 0) return null

  return (
    <instancedMesh ref={meshRef} args={[_ring, undefined, count]}>
      <meshBasicMaterial
        color={_goldColor}
        transparent
        opacity={0.6}
        toneMapped={false}
        depthWrite={false}
      />
    </instancedMesh>
  )
}

// Wireframe overlay for genre spheres — adds holographic depth
function GenreWireframes({ genres, activeSlug, hoveredSlug }) {
  const meshRef = useRef()
  const year = useStore(s => s.year)

  const count = genres.length

  useFrame((state) => {
    if (!meshRef.current) return
    const t = state.clock.elapsedTime
    const { bass } = useAudioStore.getState()
    const bassPulse = 1 + bass * 0.15
    const colors = getInstanceColors(count)

    for (let i = 0; i < count; i++) {
      const g = genres[i]
      const visible = g.year <= year
      if (!visible) {
        _obj.position.set(0, -999, 0)
        _obj.scale.setScalar(0.001)
      } else {
        const floatY = g.y + Math.sin(t * 0.5 + g.x * 0.1) * 0.3
        _obj.position.set(g.x, floatY, g.z)
        // Wireframe slightly larger than solid sphere
        let scale = g.size * 1.02 * bassPulse
        if (g.slug === activeSlug) scale *= (1 + Math.sin(t * 3) * 0.15)
        else if (g.slug === hoveredSlug) scale *= 1.12
        _obj.scale.setScalar(scale)
      }
      _obj.updateMatrix()
      meshRef.current.setMatrixAt(i, _obj.matrix)

      const isHovered = g.slug === hoveredSlug
      const isActive = g.slug === activeSlug
      const opacity = visible ? Math.min(1, (year - g.year + 5) / 10) : 0
      const boost = isActive ? 1.2 : isHovered ? 0.8 : 0.3
      _color.set(g.color).multiplyScalar(boost * opacity)
      colors[i * 3] = _color.r
      colors[i * 3 + 1] = _color.g
      colors[i * 3 + 2] = _color.b
    }
    meshRef.current.instanceMatrix.needsUpdate = true
    const attr = meshRef.current.geometry.getAttribute('instanceColor')
    if (attr) {
      attr.array.set(colors)
      attr.needsUpdate = true
    }
  })

  return (
    <instancedMesh ref={meshRef} args={[_wireframeSphere, undefined, count]} raycast={() => null}>
      <instancedBufferAttribute
        attach="geometry-attributes-instanceColor"
        args={[getInstanceColors(count), 3]}
      />
      <meshBasicMaterial
        wireframe
        vertexColors
        transparent
        opacity={0.12}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </instancedMesh>
  )
}

// Orbiting ring around selected genre
const _selectRing = new THREE.TorusGeometry(1, 0.03, 8, 64)

function SelectionRing({ genre }) {
  const meshRef = useRef()

  useFrame((state) => {
    if (!meshRef.current || !genre) return
    const t = state.clock.elapsedTime
    const floatY = genre.y + Math.sin(t * 0.5 + genre.x * 0.1) * 0.3
    meshRef.current.position.set(genre.x, floatY, genre.z)
    meshRef.current.rotation.set(
      Math.sin(t * 0.7) * 0.3,
      t * 0.8,
      Math.cos(t * 0.5) * 0.2
    )
    const scale = genre.size * 1.6
    meshRef.current.scale.setScalar(scale)
  })

  if (!genre) return null

  return (
    <mesh ref={meshRef} geometry={_selectRing}>
      <meshBasicMaterial
        color={genre.color}
        transparent
        opacity={0.5}
        toneMapped={false}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </mesh>
  )
}

// Instanced mesh for all genre spheres
function GenreInstances({ genres, onClickGenre, onHoverGenre, activeSlug, hoveredSlug }) {
  const meshRef = useRef()
  const year = useStore(s => s.year)
  const collectionGenres = useStore(s => s.collectionGenres)
  const showOverlay = useStore(s => s.showCollectionOverlay)
  const count = genres.length
  // Smooth hover scale per instance
  const hoverScales = useRef(new Float32Array(count).fill(1))

  useFrame((state, delta) => {
    if (!meshRef.current) return
    const t = state.clock.elapsedTime
    const { bass, beat } = useAudioStore.getState()
    const colors = getInstanceColors(count)
    const hasCollection = showOverlay && Object.keys(collectionGenres).length > 0

    // Bass pulse: subtle 1.0-1.15x range
    const bassPulse = 1 + bass * 0.15
    // Beat kick: quick pop that decays via lerp in the store
    const beatKick = beat ? 1.06 : 1
    const scales = hoverScales.current

    for (let i = 0; i < count; i++) {
      const g = genres[i]
      const visible = g.year <= year
      const opacity = visible ? Math.min(1, (year - g.year + 5) / 10) : 0

      // Smooth hover lerp
      const targetScale = g.slug === hoveredSlug ? 1.1 : 1.0
      scales[i] += (targetScale - scales[i]) * Math.min(1, delta * 8)

      if (!visible) {
        // Move off-screen
        _obj.position.set(0, -999, 0)
        _obj.scale.setScalar(0.001)
      } else {
        const floatY = g.y + Math.sin(t * 0.5 + g.x * 0.1) * 0.3
        _obj.position.set(g.x, floatY, g.z)

        let scale = g.size * bassPulse * beatKick * scales[i]
        if (g.slug === activeSlug) {
          scale *= (1 + Math.sin(t * 3) * 0.15)
        }
        _obj.scale.setScalar(scale)
      }
      _obj.updateMatrix()
      meshRef.current.setMatrixAt(i, _obj.matrix)

      // Emissive-boosted colour — dim non-collection genres when overlay is active
      const isActive = g.slug === activeSlug
      const isHovered = g.slug === hoveredSlug
      const inCollection = hasCollection && collectionGenres[g.slug]
      const dimFactor = hasCollection && !inCollection && !isActive && !isHovered ? 0.35 : 1
      const boost = isActive ? 2.5 : isHovered ? 1.6 : 0.7
      _color.set(g.color).multiplyScalar(boost * opacity * dimFactor)
      colors[i * 3] = _color.r
      colors[i * 3 + 1] = _color.g
      colors[i * 3 + 2] = _color.b
    }

    meshRef.current.instanceMatrix.needsUpdate = true

    // Update instance colours
    const attr = meshRef.current.geometry.getAttribute('instanceColor')
    if (attr) {
      attr.array.set(colors)
      attr.needsUpdate = true
    }
  })

  // Raycast helper — find which instance was hit
  const handlePointer = useCallback((e, action) => {
    e.stopPropagation()
    const idx = e.instanceId
    if (idx === undefined || idx < 0 || idx >= genres.length) return
    action(genres[idx])
  }, [genres])

  return (
    <instancedMesh
      ref={meshRef}
      args={[_sphere, undefined, count]}
      onClick={(e) => handlePointer(e, onClickGenre)}
      onPointerOver={(e) => handlePointer(e, onHoverGenre)}
      onPointerOut={() => onHoverGenre(null)}
    >
      <instancedBufferAttribute
        attach="geometry-attributes-instanceColor"
        args={[getInstanceColors(count), 3]}
      />
      <meshStandardMaterial
        vertexColors
        toneMapped={false}
        roughness={0.3}
        metalness={0.1}
        emissive="#ffffff"
        emissiveIntensity={0.08}
      />
    </instancedMesh>
  )
}

// Glass-morphism hover tooltip
function HoverTooltip({ genre }) {
  if (!genre) return null

  return (
    <Html
      position={[genre.x, genre.y + genre.size + 2, genre.z]}
      center
      style={{ pointerEvents: 'none', userSelect: 'none' }}
    >
      <div className="genre-tooltip">
        <div className="genre-tooltip-name" style={{ color: genre.color }}>
          {genre.name}
        </div>
        <div className="genre-tooltip-scene">{genre.scene}</div>
        {genre.emerged && (
          <div className="genre-tooltip-meta">Emerged {genre.emerged}</div>
        )}
        <div className="genre-tooltip-meta">{genre.trackCount} tracks</div>
      </div>
    </Html>
  )
}

// Billboard genre labels — only for genres with >50 releases, fade with distance
function GenreLabels({ genres, activeSlug }) {
  const year = useStore(s => s.year)
  const { camera } = useThree()

  const labelGenres = useMemo(() => {
    return genres.filter(g => g.trackCount > 50)
  }, [genres])

  return (
    <group>
      {labelGenres.map(g => {
        const visible = g.year <= year
        if (!visible) return null
        return (
          <GenreLabel
            key={g.slug}
            genre={g}
            camera={camera}
            isActive={g.slug === activeSlug}
          />
        )
      })}
    </group>
  )
}

function GenreLabel({ genre, camera, isActive }) {
  const textRef = useRef()

  useFrame(() => {
    if (!textRef.current) return
    const dist = camera.position.distanceTo(
      new THREE.Vector3(genre.x, genre.y, genre.z)
    )
    // Fade: fully visible under 30, fade out by 60, invisible beyond 70
    const opacity = isActive
      ? Math.min(1, Math.max(0.3, 1 - (dist - 40) / 40))
      : Math.min(0.5, Math.max(0, 1 - (dist - 25) / 35))
    textRef.current.fillOpacity = opacity
    textRef.current.visible = opacity > 0.01
  })

  return (
    <Text
      ref={textRef}
      position={[genre.x, genre.y + genre.size + 1.2, genre.z]}
      fontSize={0.6}
      color={genre.color}
      anchorX="center"
      anchorY="bottom"
      fillOpacity={0.4}
      outlineWidth={0.02}
      outlineColor="#000000"
      outlineOpacity={0.5}
      depthOffset={-1}
    >
      {genre.name}
    </Text>
  )
}

// Connection lines between genres
function GenreLinks({ genres, links, activeSlug, hoveredSlug }) {
  const year = useStore(s => s.year)

  const lineData = useMemo(() => {
    return links
      .filter(l => l.startYear <= year)
      .map(link => {
        const source = genres.find(g => g.slug === link.source)
        const target = genres.find(g => g.slug === link.target)
        if (!source || !target) return null

        const points = [
          new THREE.Vector3(source.x, source.y, source.z),
          new THREE.Vector3(
            (source.x + target.x) / 2,
            Math.max(source.y, target.y) + 2,
            (source.z + target.z) / 2
          ),
          new THREE.Vector3(target.x, target.y, target.z),
        ]
        const curve = new THREE.QuadraticBezierCurve3(...points)
        const geo = new THREE.BufferGeometry().setFromPoints(curve.getPoints(20))
        const isActive = activeSlug && (link.source === activeSlug || link.target === activeSlug)
        const isHovered = hoveredSlug && (link.source === hoveredSlug || link.target === hoveredSlug)
        return { geo, isActive, isHovered, sourceColor: source.color, targetColor: target.color }
      })
      .filter(Boolean)
  }, [genres, links, year, activeSlug, hoveredSlug])

  return (
    <group>
      {lineData.map((d, i) => (
        <line key={i} geometry={d.geo}>
          <lineBasicMaterial
            color={d.isActive || d.isHovered ? d.sourceColor : '#ffffff'}
            transparent
            opacity={d.isActive ? 0.35 : d.isHovered ? 0.2 : 0.06}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        </line>
      ))}
    </group>
  )
}

// Ambient dust particles — slowly drifting upward, color-tinted by nearby genres
function AmbientDust({ genres }) {
  const pointsRef = useRef()
  const count = 600

  const { positions, velocities, genreColors } = useMemo(() => {
    const pos = new Float32Array(count * 3)
    const vel = new Float32Array(count * 3)
    const col = new Float32Array(count * 3)

    for (let i = 0; i < count; i++) {
      // Spread across the scene
      pos[i * 3] = (((i * 7919 + 1) % 2003) / 2003 - 0.5) * 120
      pos[i * 3 + 1] = (((i * 6271 + 3) % 1009) / 1009) * 30 - 2
      pos[i * 3 + 2] = (((i * 4813 + 7) % 1999) / 1999 - 0.5) * 120

      // Slow upward drift with slight horizontal wander
      vel[i * 3] = (((i * 3571) % 1000) / 1000 - 0.5) * 0.02
      vel[i * 3 + 1] = 0.01 + (((i * 2791) % 1000) / 1000) * 0.02
      vel[i * 3 + 2] = (((i * 4999) % 1000) / 1000 - 0.5) * 0.02

      // Find nearest genre for color tinting
      const px = pos[i * 3]
      const pz = pos[i * 3 + 2]
      let minDist = Infinity
      let nearestColor = '#334466'
      for (let j = 0; j < Math.min(genres.length, 50); j++) {
        const dx = genres[j].x - px
        const dz = genres[j].z - pz
        const d = dx * dx + dz * dz
        if (d < minDist) {
          minDist = d
          nearestColor = genres[j].color
        }
      }
      _color.set(nearestColor).multiplyScalar(0.3)
      col[i * 3] = _color.r
      col[i * 3 + 1] = _color.g
      col[i * 3 + 2] = _color.b
    }
    return { positions: pos, velocities: vel, genreColors: col }
  }, [genres])

  useFrame((_state, delta) => {
    if (!pointsRef.current) return
    const posAttr = pointsRef.current.geometry.getAttribute('position')
    if (!posAttr) return

    const dt = Math.min(delta, 0.05)
    for (let i = 0; i < count; i++) {
      posAttr.array[i * 3] += velocities[i * 3] * dt * 20
      posAttr.array[i * 3 + 1] += velocities[i * 3 + 1] * dt * 20
      posAttr.array[i * 3 + 2] += velocities[i * 3 + 2] * dt * 20

      // Wrap around when too high
      if (posAttr.array[i * 3 + 1] > 30) {
        posAttr.array[i * 3 + 1] = -2
      }
    }
    posAttr.needsUpdate = true
  })

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
          array={genreColors}
          count={count}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.08}
        vertexColors
        transparent
        opacity={0.35}
        sizeAttenuation
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </points>
  )
}

// Genre-colored point lights at major cluster centroids
function ClusterLights({ genres }) {
  const lights = useMemo(() => {
    const groups = {}
    genres.forEach(g => {
      if (!groups[g.scene]) groups[g.scene] = { xs: [], ys: [], zs: [], color: g.color, count: 0 }
      groups[g.scene].xs.push(g.x)
      groups[g.scene].ys.push(g.y)
      groups[g.scene].zs.push(g.z)
      groups[g.scene].count++
    })
    return Object.entries(groups)
      .filter(([, data]) => data.count >= 3)
      .map(([scene, data]) => {
        const cx = data.xs.reduce((a, b) => a + b, 0) / data.xs.length
        const cy = Math.max(...data.ys) + 6
        const cz = data.zs.reduce((a, b) => a + b, 0) / data.zs.length
        return { scene, x: cx, y: cy, z: cz, color: data.color }
      })
  }, [genres])

  return (
    <group>
      {lights.map(l => (
        <pointLight
          key={l.scene}
          position={[l.x, l.y, l.z]}
          color={l.color}
          intensity={0.15}
          distance={25}
          decay={2}
        />
      ))}
    </group>
  )
}

// Scene labels for biome regions — clickable to fly to scene center
function BiomeLabels({ genres }) {
  const setActiveGenre = useStore(s => s.setActiveGenre)
  const setCameraTarget = useStore(s => s.setCameraTarget)

  const biomes = useMemo(() => {
    const groups = {}
    genres.forEach(g => {
      if (!groups[g.scene]) groups[g.scene] = { genres: [], color: g.color }
      groups[g.scene].genres.push(g)
    })
    return Object.entries(groups).map(([scene, data]) => {
      const cx = data.genres.reduce((s, g) => s + g.x, 0) / data.genres.length
      const cz = data.genres.reduce((s, g) => s + g.z, 0) / data.genres.length
      // Pick the most representative genre (highest track count) for selection
      const primary = data.genres.reduce((best, g) => g.trackCount > best.trackCount ? g : best, data.genres[0])
      return { scene, x: cx, z: cz, color: data.color, count: data.genres.length, primary }
    })
  }, [genres])

  return (
    <group>
      {biomes.map(b => (
        <Html
          key={b.scene}
          position={[b.x, -1, b.z]}
          center
          style={{
            color: b.color,
            fontSize: '12px',
            fontFamily: "'JetBrains Mono', monospace",
            fontWeight: 400,
            textTransform: 'uppercase',
            letterSpacing: '2px',
            opacity: 0.35,
            whiteSpace: 'nowrap',
            cursor: 'pointer',
            userSelect: 'none',
            transition: 'opacity 0.2s',
          }}
          onPointerEnter={(e) => { e.target.style.opacity = '0.8' }}
          onPointerLeave={(e) => { e.target.style.opacity = '0.35' }}
          onClick={() => {
            setActiveGenre(b.primary)
            setCameraTarget(b.primary)
          }}
        >
          {b.scene}
        </Html>
      ))}
    </group>
  )
}

// Gentle idle camera bob
function CameraIdleBob() {
  const idleTimer = useRef(0)
  const lastMouse = useRef({ x: 0, y: 0 })

  useFrame((state, delta) => {
    // Track if mouse has moved recently
    const pointer = state.pointer
    const dx = Math.abs(pointer.x - lastMouse.current.x)
    const dy = Math.abs(pointer.y - lastMouse.current.y)
    lastMouse.current.x = pointer.x
    lastMouse.current.y = pointer.y

    if (dx > 0.001 || dy > 0.001) {
      idleTimer.current = 0
    } else {
      idleTimer.current += delta
    }

    // Only bob after 2s of idle
    if (idleTimer.current < 2) return

    const t = state.clock.elapsedTime
    const intensity = Math.min(1, (idleTimer.current - 2) / 3) * 0.06
    state.camera.position.y += Math.sin(t * 0.3) * intensity * 0.15
    state.camera.position.x += Math.cos(t * 0.2) * intensity * 0.1
  })

  return null
}

export default function GenreWorld() {
  const genres = useStore(s => s.genres)
  const activeGenre = useStore(s => s.activeGenre)
  const setActiveGenre = useStore(s => s.setActiveGenre)
  const hoveredRelease = useStore(s => s.hoveredRelease)
  const setHoveredRelease = useStore(s => s.setHoveredRelease)
  const setCameraTarget = useStore(s => s.setCameraTarget)
  const links = useStore(s => s.links)
  const digPathMode = useStore(s => s.digPathMode)
  const addDigPathWaypoint = useStore(s => s.addDigPathWaypoint)

  const handleClick = useCallback((genre) => {
    // In record mode, add waypoint instead of normal selection
    if (digPathMode === 'record') {
      addDigPathWaypoint({ slug: genre.slug, note: '' })
      setActiveGenre(genre)
      setCameraTarget(genre)
      return
    }
    const newGenre = activeGenre?.slug === genre.slug ? null : genre
    setActiveGenre(newGenre)
    setCameraTarget(newGenre)
  }, [activeGenre, setActiveGenre, setCameraTarget, digPathMode, addDigPathWaypoint])

  const handleHover = useCallback((genre) => {
    setHoveredRelease(genre)
    document.body.style.cursor = genre ? 'pointer' : 'auto'
  }, [setHoveredRelease])

  return (
    <group>
      <Ground />
      <Grid />
      <GlowRings genres={genres} />

      <GenreInstances
        genres={genres}
        onClickGenre={handleClick}
        onHoverGenre={handleHover}
        activeSlug={activeGenre?.slug}
        hoveredSlug={hoveredRelease?.slug}
      />

      {/* Instanced buildings around genre clusters */}
      <GenreWorldBuildings genres={genres} />

      {/* Wireframe overlay on spheres */}
      <GenreWireframes
        genres={genres}
        activeSlug={activeGenre?.slug}
        hoveredSlug={hoveredRelease?.slug}
      />

      {/* Orbiting ring on selected genre */}
      <SelectionRing genre={activeGenre} />

      <CollectionRings genres={genres} />
      <HoverTooltip genre={hoveredRelease} />

      <GenreLinks
        genres={genres}
        links={links}
        activeSlug={activeGenre?.slug}
        hoveredSlug={hoveredRelease?.slug}
      />

      {/* Billboard labels for major genres */}
      <GenreLabels genres={genres} activeSlug={activeGenre?.slug} />

      <BiomeLabels genres={genres} />

      {/* Ambient dust particles */}
      <AmbientDust genres={genres} />

      {/* Genre-colored cluster lights */}
      <ClusterLights genres={genres} />

      {/* Gentle idle camera bob */}
      <CameraIdleBob />

      <MysteryNode />
      <LabelConstellation />
      <ArtistThread />
      <DigPath />
    </group>
  )
}
