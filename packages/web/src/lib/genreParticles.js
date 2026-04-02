import * as THREE from 'three'

const MAX_PARTICLES = 500

// Biome particle configurations
const BIOME_PARTICLES = {
  // Techno: smoke/steam rising from buildings (gray, slow upward drift)
  'techno-massif': {
    color: [0.4, 0.42, 0.45],
    colorVariance: 0.08,
    size: 3.0,
    speed: 0.3,
    movement: 'rise',      // slow upward drift
    spread: 40,
    opacity: 0.35,
  },
  'industrial-wasteland': {
    color: [0.35, 0.38, 0.40],
    colorVariance: 0.1,
    size: 3.5,
    speed: 0.25,
    movement: 'rise',
    spread: 45,
    opacity: 0.3,
  },
  // House: warm firefly-like dots (amber, random float)
  'house-plains': {
    color: [0.9, 0.65, 0.2],
    colorVariance: 0.12,
    size: 2.0,
    speed: 0.15,
    movement: 'float',     // random gentle drift
    spread: 35,
    opacity: 0.6,
  },
  'disco-riviera': {
    color: [0.85, 0.6, 0.25],
    colorVariance: 0.15,
    size: 2.2,
    speed: 0.12,
    movement: 'float',
    spread: 38,
    opacity: 0.55,
  },
  // Ambient: crystal sparkles (white/blue, slow random)
  'ambient-depths': {
    color: [0.7, 0.8, 1.0],
    colorVariance: 0.15,
    size: 1.5,
    speed: 0.1,
    movement: 'sparkle',   // slow random + pulse
    spread: 50,
    opacity: 0.5,
  },
  'idm-crystalline': {
    color: [0.75, 0.85, 1.0],
    colorVariance: 0.2,
    size: 1.8,
    speed: 0.12,
    movement: 'sparkle',
    spread: 45,
    opacity: 0.45,
  },
  // DnB: sparks (orange, fast diagonal movement)
  'jungle-canopy': {
    color: [1.0, 0.5, 0.1],
    colorVariance: 0.1,
    size: 1.8,
    speed: 0.8,
    movement: 'diagonal',  // fast diagonal streaks
    spread: 35,
    opacity: 0.7,
  },
  'dubstep-rift': {
    color: [0.95, 0.45, 0.12],
    colorVariance: 0.12,
    size: 2.0,
    speed: 0.9,
    movement: 'diagonal',
    spread: 38,
    opacity: 0.65,
  },
  // Trance: light beams (vertical gold pillars, slow pulse)
  'trance-highlands': {
    color: [1.0, 0.85, 0.3],
    colorVariance: 0.08,
    size: 2.5,
    speed: 0.2,
    movement: 'beam',      // vertical slow pulse
    spread: 30,
    opacity: 0.4,
  },
  // Hardcore: embers/ash (red, chaotic movement)
  'urban-quarter': {
    color: [1.0, 0.2, 0.05],
    colorVariance: 0.15,
    size: 2.0,
    speed: 0.6,
    movement: 'chaotic',   // random fast
    spread: 40,
    opacity: 0.6,
  },
  // Experimental: geometry distortion particles
  'garage-district': {
    color: [0.5, 0.5, 0.5],
    colorVariance: 0.3,
    size: 2.5,
    speed: 0.4,
    movement: 'glitch',    // random teleport
    spread: 35,
    opacity: 0.5,
  },
  'source-monuments': {
    color: [0.6, 0.55, 0.4],
    colorVariance: 0.1,
    size: 2.0,
    speed: 0.08,
    movement: 'float',
    spread: 30,
    opacity: 0.35,
  },
}

const DEFAULT_PARTICLES = {
  color: [0.5, 0.5, 0.6],
  colorVariance: 0.1,
  size: 2.0,
  speed: 0.15,
  movement: 'float',
  spread: 35,
  opacity: 0.4,
}

// Pseudo-random seeded by index
function seededRandom(i) {
  return (Math.sin(i * 127.1 + 311.7) * 43758.5453) % 1
}

/**
 * Create genre-specific ambient particles near the camera.
 * Returns { points, update(delta, cameraPosition), dispose(), transitionTo(biomeType), setVisible(bool) }
 */
export function createGenreParticles(biomeType, count = 300) {
  count = Math.min(count, MAX_PARTICLES)
  const config = BIOME_PARTICLES[biomeType] || DEFAULT_PARTICLES

  const positions = new Float32Array(count * 3)
  const colors = new Float32Array(count * 3)
  const velocities = new Float32Array(count * 3) // internal state
  const phases = new Float32Array(count) // per-particle phase offset
  // Initialize positions randomly in a sphere around origin
  for (let i = 0; i < count; i++) {
    const r = Math.random() * config.spread
    const theta = Math.random() * Math.PI * 2
    const phi = Math.acos(2 * Math.random() - 1)
    positions[i * 3] = r * Math.sin(phi) * Math.cos(theta)
    positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta)
    positions[i * 3 + 2] = r * Math.cos(phi)

    // Color with variance
    const variance = (seededRandom(i) - 0.5) * config.colorVariance * 2
    colors[i * 3] = Math.max(0, Math.min(1, config.color[0] + variance))
    colors[i * 3 + 1] = Math.max(0, Math.min(1, config.color[1] + variance * 0.7))
    colors[i * 3 + 2] = Math.max(0, Math.min(1, config.color[2] + variance * 0.5))

    // Random velocity direction
    velocities[i * 3] = (Math.random() - 0.5) * 2
    velocities[i * 3 + 1] = (Math.random() - 0.5) * 2
    velocities[i * 3 + 2] = (Math.random() - 0.5) * 2

    phases[i] = Math.random() * Math.PI * 2
  }

  const geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))

  const material = new THREE.PointsMaterial({
    size: config.size,
    vertexColors: true,
    transparent: true,
    opacity: config.opacity,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    sizeAttenuation: true,
  })

  const points = new THREE.Points(geometry, material)

  let currentConfig = { ...config }
  let elapsedTime = 0

  function update(delta, cameraPosition) {
    elapsedTime += delta
    const posAttr = geometry.attributes.position
    const speed = currentConfig.speed

    for (let i = 0; i < count; i++) {
      let x = posAttr.getX(i)
      let y = posAttr.getY(i)
      let z = posAttr.getZ(i)
      const phase = phases[i]

      switch (currentConfig.movement) {
        case 'rise':
          // Slow upward drift
          y += speed * delta * 8
          x += Math.sin(elapsedTime + phase) * delta * 0.5
          z += Math.cos(elapsedTime * 0.7 + phase) * delta * 0.5
          // Reset particles that go too high
          if (y > currentConfig.spread) y = -currentConfig.spread
          break

        case 'float':
          // Gentle random float (firefly)
          x += Math.sin(elapsedTime * 0.5 + phase) * speed * delta * 3
          y += Math.cos(elapsedTime * 0.3 + phase * 1.3) * speed * delta * 3
          z += Math.sin(elapsedTime * 0.4 + phase * 0.7) * speed * delta * 3
          break

        case 'sparkle':
          // Very slow drift + occasional brightness handled by opacity
          x += Math.sin(elapsedTime * 0.2 + phase) * speed * delta * 2
          y += Math.cos(elapsedTime * 0.15 + phase * 1.5) * speed * delta * 2
          z += Math.sin(elapsedTime * 0.25 + phase * 0.8) * speed * delta * 2
          break

        case 'diagonal':
          // Fast diagonal movement (sparks)
          x += velocities[i * 3] * speed * delta * 15
          y += velocities[i * 3 + 1] * speed * delta * 15
          z += velocities[i * 3 + 2] * speed * delta * 15
          break

        case 'beam':
          // Vertical slow pulse (columns of light)
          y += Math.sin(elapsedTime * 0.5 + phase) * speed * delta * 5
          // Stay mostly vertical, minimal horizontal drift
          x += Math.sin(elapsedTime * 0.1 + phase) * speed * delta * 0.5
          z += Math.cos(elapsedTime * 0.1 + phase) * speed * delta * 0.5
          break

        case 'chaotic':
          // Random fast movement (embers)
          x += (Math.sin(elapsedTime * 3 + phase) + velocities[i * 3]) * speed * delta * 8
          y += (Math.cos(elapsedTime * 2.5 + phase * 0.8) + Math.abs(velocities[i * 3 + 1])) * speed * delta * 6
          z += (Math.sin(elapsedTime * 2.8 + phase * 1.2) + velocities[i * 3 + 2]) * speed * delta * 8
          break

        case 'glitch':
          // Occasional teleport
          if (Math.random() < 0.005) {
            x = (Math.random() - 0.5) * currentConfig.spread * 2
            y = (Math.random() - 0.5) * currentConfig.spread * 2
            z = (Math.random() - 0.5) * currentConfig.spread * 2
          } else {
            x += Math.sin(elapsedTime + phase) * speed * delta * 4
            y += Math.cos(elapsedTime * 0.8 + phase) * speed * delta * 4
            z += Math.sin(elapsedTime * 1.2 + phase) * speed * delta * 4
          }
          break
      }

      // Keep particles within spread radius (wrap around)
      const dist = Math.sqrt(x * x + y * y + z * z)
      if (dist > currentConfig.spread) {
        const scale = currentConfig.spread / dist * 0.1
        x *= scale
        y *= scale
        z *= scale
      }

      posAttr.setXYZ(i, x, y, z)
    }

    posAttr.needsUpdate = true

    // Follow camera (parallax: particles sit near camera, not at planet surface)
    if (cameraPosition) {
      points.position.copy(cameraPosition)
    }
  }

  function transitionTo(newBiomeType) {
    const target = BIOME_PARTICLES[newBiomeType] || DEFAULT_PARTICLES

    // Update colors smoothly by re-assigning
    const colAttr = geometry.attributes.color
    for (let i = 0; i < count; i++) {
      const variance = (seededRandom(i) - 0.5) * target.colorVariance * 2
      colAttr.setXYZ(
        i,
        Math.max(0, Math.min(1, target.color[0] + variance)),
        Math.max(0, Math.min(1, target.color[1] + variance * 0.7)),
        Math.max(0, Math.min(1, target.color[2] + variance * 0.5))
      )
    }
    colAttr.needsUpdate = true

    material.size = target.size
    material.opacity = target.opacity
    currentConfig = { ...target }
  }

  function setVisible(visible) {
    points.visible = visible
  }

  function dispose() {
    geometry.dispose()
    material.dispose()
  }

  return { points, update, dispose, transitionTo, setVisible }
}
