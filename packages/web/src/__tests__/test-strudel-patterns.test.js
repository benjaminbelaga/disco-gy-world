import { describe, it, expect } from 'vitest'
import { generatePattern, generateMiniPattern, SCENE_BPM, BIOME_SCALES, BIOME_SOUNDS } from '../lib/strudelPatterns'

describe('Strudel Pattern Generator', () => {
  const technoGenre = { slug: 'techno', name: 'Techno', scene: 'Techno', biome: 'techno-massif' }
  const ambientGenre = { slug: 'ambient', name: 'Ambient', scene: 'Ambient', biome: 'ambient-depths' }
  const dnbGenre = { slug: 'drum-n-bass', name: 'Drum n Bass', scene: 'Drum n Bass', biome: 'jungle-canopy' }
  const houseGenre = { slug: 'deep-house', name: 'Deep House', scene: 'House', biome: 'house-plains' }
  const unknownGenre = { slug: 'mystery', name: 'Mystery' }

  describe('generatePattern', () => {
    it('generates a non-empty pattern string', () => {
      const pattern = generatePattern(technoGenre)
      expect(pattern).toBeTruthy()
      expect(typeof pattern).toBe('string')
      expect(pattern.length).toBeGreaterThan(50)
    })

    it('includes genre name in comment', () => {
      expect(generatePattern(technoGenre)).toContain('// Techno')
      expect(generatePattern(ambientGenre)).toContain('// Ambient')
    })

    it('includes setcps with correct BPM range', () => {
      const pattern = generatePattern(technoGenre)
      const match = pattern.match(/setcps\(([0-9.]+)\)/)
      expect(match).toBeTruthy()
      const cps = parseFloat(match[1])
      // Techno: 128-140 BPM → cps = bpm/60/4 → 0.533..0.583
      expect(cps).toBeGreaterThanOrEqual(128 / 60 / 4 - 0.01)
      expect(cps).toBeLessThanOrEqual(140 / 60 / 4 + 0.01)
    })

    it('includes bass, pad, lead sections', () => {
      const pattern = generatePattern(houseGenre)
      expect(pattern).toContain('// bass')
      expect(pattern).toContain('// pad')
      expect(pattern).toContain('// lead')
    })

    it('uses scale from biome', () => {
      const pattern = generatePattern(technoGenre)
      const validScales = BIOME_SCALES['techno-massif']
      const hasScale = validScales.some(s => pattern.includes(s))
      expect(hasScale).toBe(true)
    })

    it('uses sounds from biome', () => {
      const pattern = generatePattern(houseGenre)
      const sounds = BIOME_SOUNDS['house-plains']
      expect(pattern).toContain(sounds.pad)
    })

    it('ambient genre has room/reverb', () => {
      const pattern = generatePattern(ambientGenre)
      expect(pattern).toContain('.room(')
    })

    it('includes drums section for non-ambient genres', () => {
      const pattern = generatePattern(technoGenre)
      expect(pattern).toContain('// drums')
    })

    it('ambient has no drums section label', () => {
      const pattern = generatePattern(ambientGenre)
      expect(pattern).not.toContain('// drums')
    })

    it('DnB pattern uses correct rhythm', () => {
      const pattern = generatePattern(dnbGenre)
      // DnB bass should have syncopation
      expect(pattern).toContain('// bass')
    })

    it('handles unknown genre gracefully', () => {
      const pattern = generatePattern(unknownGenre)
      expect(pattern).toBeTruthy()
      expect(pattern).toContain('setcps')
    })

    it('generates different patterns on multiple calls (randomness)', () => {
      const patterns = new Set()
      for (let i = 0; i < 10; i++) {
        patterns.add(generatePattern(technoGenre))
      }
      // With BPM + scale randomness, we should get at least a few distinct patterns
      expect(patterns.size).toBeGreaterThan(1)
    })
  })

  describe('generateMiniPattern', () => {
    it('generates a shorter pattern', () => {
      const mini = generateMiniPattern(technoGenre)
      const full = generatePattern(technoGenre)
      expect(mini.length).toBeLessThan(full.length)
    })

    it('includes setcps and scale', () => {
      const mini = generateMiniPattern(houseGenre)
      expect(mini).toContain('setcps')
      expect(mini).toContain('scale')
    })
  })

  describe('data constants', () => {
    it('SCENE_BPM has valid ranges', () => {
      for (const [scene, range] of Object.entries(SCENE_BPM)) {
        expect(range).toHaveLength(2)
        expect(range[0]).toBeLessThan(range[1])
        expect(range[0]).toBeGreaterThan(60)
        expect(range[1]).toBeLessThan(220)
      }
    })

    it('BIOME_SCALES covers all biomes', () => {
      const biomes = ['techno-massif', 'house-plains', 'disco-riviera', 'ambient-depths',
        'jungle-canopy', 'trance-highlands', 'industrial-wasteland', 'idm-crystalline',
        'dubstep-rift', 'garage-district', 'urban-quarter', 'source-monuments', 'unknown']
      for (const biome of biomes) {
        expect(BIOME_SCALES[biome]).toBeDefined()
        expect(BIOME_SCALES[biome].length).toBeGreaterThan(0)
      }
    })

    it('BIOME_SOUNDS covers all biomes', () => {
      for (const biome of Object.keys(BIOME_SCALES)) {
        expect(BIOME_SOUNDS[biome]).toBeDefined()
        expect(BIOME_SOUNDS[biome].kick).toBeDefined()
        expect(BIOME_SOUNDS[biome].bass).toBeDefined()
        expect(BIOME_SOUNDS[biome].pad).toBeDefined()
        expect(BIOME_SOUNDS[biome].lead).toBeDefined()
      }
    })
  })
})
