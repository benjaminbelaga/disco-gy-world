import { describe, it, expect } from 'vitest'
import { generateBuildings, BIOME_MAPPING, BIOME_STYLES } from '../lib/buildingGenerator'

describe('buildingGenerator — BIOME_MAPPING', () => {
  it('maps known biome slugs to style keys', () => {
    expect(BIOME_MAPPING['techno-massif']).toBe('techno')
    expect(BIOME_MAPPING['house-plains']).toBe('house')
    expect(BIOME_MAPPING['ambient-depths']).toBe('ambient')
    expect(BIOME_MAPPING['jungle-canopy']).toBe('dnb')
    expect(BIOME_MAPPING['trance-highlands']).toBe('trance')
  })

  it('has style definitions for all mapped values', () => {
    const uniqueStyles = new Set(Object.values(BIOME_MAPPING))
    for (const style of uniqueStyles) {
      expect(BIOME_STYLES[style]).toBeDefined()
    }
  })
})

describe('buildingGenerator — generateBuildings', () => {
  it('generates the requested number of buildings', () => {
    const buildings = generateBuildings('techno', 30, 42)
    expect(buildings).toHaveLength(30)
  })

  it('each building has required properties', () => {
    const buildings = generateBuildings('house', 5, 123)
    for (const b of buildings) {
      expect(b).toHaveProperty('position')
      expect(b).toHaveProperty('rotation')
      expect(b).toHaveProperty('scale')
      expect(b).toHaveProperty('geometry')
      expect(b).toHaveProperty('archetype')
      expect(b).toHaveProperty('color')
      expect(b).toHaveProperty('emissiveColor')
      expect(b).toHaveProperty('windowDensity')
      expect(b.position).toHaveLength(3)
      expect(b.rotation).toHaveLength(3)
      expect(b.scale).toHaveLength(3)
    }
  })

  it('is deterministic — same seed produces same output', () => {
    const a = generateBuildings('techno', 10, 999)
    const b = generateBuildings('techno', 10, 999)
    expect(a).toEqual(b)
  })

  it('different seeds produce different output', () => {
    const a = generateBuildings('techno', 10, 1)
    const b = generateBuildings('techno', 10, 2)
    // Very unlikely to be identical
    const aPositions = a.map(b => b.position[0])
    const bPositions = b.map(b => b.position[0])
    expect(aPositions).not.toEqual(bPositions)
  })

  it('works with biome slug mapping (techno-massif -> techno)', () => {
    const buildings = generateBuildings('techno-massif', 5, 42)
    expect(buildings).toHaveLength(5)
    expect(buildings[0].color).toBe(BIOME_STYLES.techno.color)
  })

  it('uses correct colors per biome', () => {
    for (const [key, style] of Object.entries(BIOME_STYLES)) {
      const buildings = generateBuildings(key, 1, 1)
      expect(buildings[0].color).toBe(style.color)
      expect(buildings[0].emissiveColor).toBe(style.emissiveColor)
    }
  })

  it('geometry types come from archetype definitions', () => {
    const validTypes = new Set(['box', 'cylinder', 'cone'])
    const buildings = generateBuildings('ambient', 50, 77)
    for (const b of buildings) {
      expect(validTypes.has(b.geometry)).toBe(true)
    }
  })

  it('falls back to techno for unknown biome', () => {
    const buildings = generateBuildings('unknown-biome', 5, 42)
    expect(buildings).toHaveLength(5)
    expect(buildings[0].color).toBe(BIOME_STYLES.techno.color)
  })
})
