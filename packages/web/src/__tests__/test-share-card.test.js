import { describe, it, expect } from 'vitest'
import { BIOME_GRADIENTS } from '../lib/shareCard'

describe('Share Card', () => {
  describe('BIOME_GRADIENTS', () => {
    const expectedBiomes = [
      'techno-massif', 'house-plains', 'disco-riviera', 'ambient-depths',
      'jungle-canopy', 'trance-highlands', 'industrial-wasteland', 'idm-crystalline',
      'dubstep-rift', 'garage-district', 'urban-quarter', 'source-monuments', 'unknown',
    ]

    it('covers all 13 biomes', () => {
      for (const biome of expectedBiomes) {
        expect(BIOME_GRADIENTS[biome]).toBeDefined()
      }
    })

    it('each gradient has 3 color stops', () => {
      for (const colors of Object.values(BIOME_GRADIENTS)) {
        expect(colors).toHaveLength(3)
      }
    })

    it('all colors are valid hex', () => {
      const hexRegex = /^#[0-9a-f]{6}$/i
      for (const colors of Object.values(BIOME_GRADIENTS)) {
        for (const color of colors) {
          expect(color).toMatch(hexRegex)
        }
      }
    })
  })

  // Note: generateShareCard requires a canvas DOM context which isn't
  // available in jsdom. The function is tested via Playwright E2E instead.
})
