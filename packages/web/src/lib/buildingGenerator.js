/**
 * Procedural building generator for DiscoWorld Genre Planet.
 * Generates deterministic building configs per biome type using seeded PRNG.
 */

// Mulberry32 seeded PRNG
function mulberry32(seed) {
  return function () {
    seed |= 0
    seed = (seed + 0x6d2b79f5) | 0
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

// Biome style definitions
const BIOME_STYLES = {
  techno: {
    color: '#2D1B1B',
    emissiveColor: '#00FFFF',
    windowDensity: 0.7,
    archetypes: [
      { type: 'box', name: 'brutalist-tower', scaleRange: [0.8, 2.5], heightRange: [3, 12], widthRange: [0.6, 1.8] },
      { type: 'cylinder', name: 'silo', scaleRange: [0.5, 1.2], heightRange: [4, 10], widthRange: [0.4, 1.0] },
      { type: 'cylinder', name: 'chimney', scaleRange: [0.3, 0.6], heightRange: [6, 15], widthRange: [0.2, 0.5] },
      { type: 'box', name: 'factory-block', scaleRange: [1.5, 3.0], heightRange: [1.5, 4], widthRange: [1.5, 3.0] },
      { type: 'box', name: 'warehouse', scaleRange: [1.0, 2.0], heightRange: [2, 5], widthRange: [1.2, 2.5] },
    ],
  },
  house: {
    color: '#8B6914',
    emissiveColor: '#FFB347',
    windowDensity: 0.6,
    archetypes: [
      { type: 'box', name: 'deco-tower', scaleRange: [0.6, 1.5], heightRange: [3, 8], widthRange: [0.8, 1.5] },
      { type: 'cylinder', name: 'rounded-top', scaleRange: [0.5, 1.2], heightRange: [3, 7], widthRange: [0.6, 1.2] },
      { type: 'box', name: 'arch-block', scaleRange: [0.8, 1.8], heightRange: [2, 5], widthRange: [1.0, 2.0] },
      { type: 'cone', name: 'dome', scaleRange: [0.6, 1.0], heightRange: [2, 4], widthRange: [0.8, 1.5] },
      { type: 'box', name: 'terracotta', scaleRange: [0.5, 1.2], heightRange: [2, 4], widthRange: [0.6, 1.4] },
    ],
  },
  ambient: {
    color: '#1B3A5C',
    emissiveColor: '#FFFFFF',
    windowDensity: 0.3,
    archetypes: [
      { type: 'cone', name: 'crystal-spire', scaleRange: [0.3, 0.8], heightRange: [5, 14], widthRange: [0.3, 0.7] },
      { type: 'box', name: 'floating-shard', scaleRange: [0.2, 0.6], heightRange: [2, 6], widthRange: [0.2, 0.5] },
      { type: 'cylinder', name: 'glass-pillar', scaleRange: [0.2, 0.5], heightRange: [4, 10], widthRange: [0.2, 0.4] },
      { type: 'cone', name: 'obelisk', scaleRange: [0.2, 0.4], heightRange: [6, 12], widthRange: [0.2, 0.4] },
      { type: 'box', name: 'prism', scaleRange: [0.3, 0.7], heightRange: [3, 8], widthRange: [0.3, 0.6] },
    ],
  },
  dnb: {
    color: '#4A4A4A',
    emissiveColor: '#FF6600',
    windowDensity: 0.5,
    archetypes: [
      { type: 'box', name: 'angular-wedge', scaleRange: [0.6, 1.5], heightRange: [3, 9], widthRange: [0.5, 1.2] },
      { type: 'box', name: 'tilted-tower', scaleRange: [0.5, 1.0], heightRange: [5, 12], widthRange: [0.4, 0.9] },
      { type: 'cylinder', name: 'overpass-pylon', scaleRange: [0.3, 0.6], heightRange: [4, 10], widthRange: [0.3, 0.6] },
      { type: 'box', name: 'cantilever', scaleRange: [0.8, 1.6], heightRange: [3, 7], widthRange: [0.6, 1.4] },
      { type: 'cone', name: 'spike', scaleRange: [0.2, 0.5], heightRange: [4, 10], widthRange: [0.2, 0.5] },
    ],
  },
  trance: {
    color: '#6B4E00',
    emissiveColor: '#9B30FF',
    windowDensity: 0.4,
    archetypes: [
      { type: 'cone', name: 'pyramid', scaleRange: [1.0, 2.5], heightRange: [3, 8], widthRange: [1.0, 2.5] },
      { type: 'box', name: 'ziggurat', scaleRange: [1.5, 3.0], heightRange: [2, 6], widthRange: [1.5, 3.0] },
      { type: 'cylinder', name: 'domed-temple', scaleRange: [0.8, 1.5], heightRange: [3, 6], widthRange: [0.8, 1.5] },
      { type: 'cone', name: 'obelisk', scaleRange: [0.3, 0.6], heightRange: [6, 14], widthRange: [0.3, 0.6] },
      { type: 'box', name: 'altar', scaleRange: [0.6, 1.2], heightRange: [1.5, 3], widthRange: [0.8, 1.5] },
    ],
  },
}

// Map biome slugs from GenrePlanet to our style keys
const BIOME_MAPPING = {
  'techno-massif': 'techno',
  'industrial-wasteland': 'techno',
  'house-plains': 'house',
  'disco-riviera': 'house',
  'garage-district': 'house',
  'urban-quarter': 'house',
  'ambient-depths': 'ambient',
  'idm-crystalline': 'ambient',
  'jungle-canopy': 'dnb',
  'dubstep-rift': 'dnb',
  'trance-highlands': 'trance',
  'source-monuments': 'trance',
}

function lerp(a, b, t) {
  return a + (b - a) * t
}

/**
 * Generate building configs for a given biome type.
 * @param {string} biomeType - Biome slug (e.g. 'techno-massif') or style key ('techno')
 * @param {number} count - Number of buildings to generate
 * @param {number} seed - Seed for deterministic generation
 * @returns {Array<Object>} Array of building config objects
 */
export function generateBuildings(biomeType, count, seed) {
  const styleKey = BIOME_MAPPING[biomeType] || biomeType
  const style = BIOME_STYLES[styleKey]
  if (!style) {
    console.warn(`Unknown biome type: ${biomeType}, falling back to techno`)
    return generateBuildings('techno', count, seed)
  }

  const rng = mulberry32(seed)
  const buildings = []

  for (let i = 0; i < count; i++) {
    const archetype = style.archetypes[Math.floor(rng() * style.archetypes.length)]

    const height = lerp(archetype.heightRange[0], archetype.heightRange[1], rng())
    const width = lerp(archetype.widthRange[0], archetype.widthRange[1], rng())
    const depth = lerp(archetype.widthRange[0], archetype.widthRange[1], rng())

    // Spread buildings in a circular area around territory center
    const angle = rng() * Math.PI * 2
    const radius = Math.sqrt(rng()) * 3.0 // sqrt for uniform disk distribution
    const offsetX = Math.cos(angle) * radius
    const offsetZ = Math.sin(angle) * radius

    // Slight random tilt for style (dnb gets more tilt)
    const tiltAmount = styleKey === 'dnb' ? 0.3 : styleKey === 'ambient' ? 0.15 : 0.05
    const tiltX = (rng() - 0.5) * tiltAmount
    const tiltZ = (rng() - 0.5) * tiltAmount

    buildings.push({
      position: [offsetX, 0, offsetZ], // Y will be set by surface projection
      rotation: [tiltX, rng() * Math.PI * 2, tiltZ],
      scale: [width, height, depth],
      geometry: archetype.type,
      archetype: archetype.name,
      color: style.color,
      emissiveColor: style.emissiveColor,
      windowDensity: style.windowDensity + (rng() - 0.5) * 0.2,
    })
  }

  return buildings
}

/**
 * Generate building configs for the flat-plane GenreWorld.
 * @param {Object} genre - Genre object with {x, z, biome, scene, trackCount, slug, color}
 * @param {number} seed - Seed for deterministic generation
 * @returns {Array<Object>} Array of building config objects positioned around the genre
 */
export function generateGenreBuildings(genre, seed) {
  // Determine biome style from scene name
  const sceneSlug = (genre.scene || '').toLowerCase().replace(/\s+/g, '-')
  const styleKey = BIOME_MAPPING[sceneSlug] || genre.biome || 'techno'
  const style = BIOME_STYLES[styleKey] || BIOME_STYLES.techno

  const rng = mulberry32(seed)

  // 3-15 buildings based on track count
  const count = Math.max(3, Math.min(15, Math.floor(3 + (genre.trackCount || 0) / 20)))
  const buildings = []
  const SCALE_FACTOR = 0.3
  const GROUND_Y = -2
  const SPREAD_RADIUS = 2.0

  for (let i = 0; i < count; i++) {
    const archetype = style.archetypes[Math.floor(rng() * style.archetypes.length)]

    const height = lerp(archetype.heightRange[0], archetype.heightRange[1], rng()) * SCALE_FACTOR
    const width = lerp(archetype.widthRange[0], archetype.widthRange[1], rng()) * SCALE_FACTOR
    const depth = lerp(archetype.widthRange[0], archetype.widthRange[1], rng()) * SCALE_FACTOR

    // Spread around genre center with uniform disk distribution
    const angle = rng() * Math.PI * 2
    const radius = Math.sqrt(rng()) * SPREAD_RADIUS
    const offsetX = Math.cos(angle) * radius
    const offsetZ = Math.sin(angle) * radius

    buildings.push({
      position: [genre.x + offsetX, GROUND_Y + height / 2, genre.z + offsetZ],
      rotation: [0, rng() * Math.PI * 2, 0],
      scale: [width, height, depth],
      geometry: archetype.type,
      color: style.color,
      emissiveColor: style.emissiveColor,
    })
  }

  return buildings
}

export { BIOME_STYLES, BIOME_MAPPING }
