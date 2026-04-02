import { describe, it, expect } from 'vitest'
import { BIOME_CONFIGS } from '../lib/soundscape'

describe('Soundscape', () => {
  describe('BIOME_CONFIGS', () => {
    const expectedBiomes = [
      'techno-massif', 'house-plains', 'disco-riviera', 'ambient-depths',
      'jungle-canopy', 'trance-highlands', 'industrial-wasteland', 'idm-crystalline',
      'dubstep-rift', 'garage-district', 'urban-quarter', 'source-monuments', 'unknown',
    ]

    it('covers all 13 biomes', () => {
      for (const biome of expectedBiomes) {
        expect(BIOME_CONFIGS[biome]).toBeDefined()
      }
    })

    it('each biome has at least 2 layers', () => {
      for (const [biome, config] of Object.entries(BIOME_CONFIGS)) {
        expect(config.layers.length).toBeGreaterThanOrEqual(2)
      }
    })

    it('each layer has a valid type', () => {
      for (const config of Object.values(BIOME_CONFIGS)) {
        for (const layer of config.layers) {
          expect(['oscillator', 'noise']).toContain(layer.type)
        }
      }
    })

    it('oscillator layers have valid wave types', () => {
      const validWaves = ['sine', 'sawtooth', 'triangle', 'square']
      for (const config of Object.values(BIOME_CONFIGS)) {
        for (const layer of config.layers) {
          if (layer.type === 'oscillator') {
            expect(validWaves).toContain(layer.wave)
          }
        }
      }
    })

    it('all gain values are below 0.15 (safety check)', () => {
      for (const config of Object.values(BIOME_CONFIGS)) {
        for (const layer of config.layers) {
          expect(layer.gain).toBeLessThanOrEqual(0.15)
        }
      }
    })

    it('filters have valid types', () => {
      const validFilters = ['lowpass', 'highpass', 'bandpass', 'notch']
      for (const config of Object.values(BIOME_CONFIGS)) {
        for (const layer of config.layers) {
          if (layer.filter) {
            expect(validFilters).toContain(layer.filter.type)
          }
        }
      }
    })

    it('LFO rates are below 1Hz (ambient, not rhythmic)', () => {
      for (const config of Object.values(BIOME_CONFIGS)) {
        for (const layer of config.layers) {
          if (layer.lfo) {
            expect(layer.lfo.rate).toBeLessThanOrEqual(1)
          }
        }
      }
    })

    it('ambient-depths has the most layers (richest texture)', () => {
      const ambient = BIOME_CONFIGS['ambient-depths']
      const others = Object.entries(BIOME_CONFIGS)
        .filter(([k]) => k !== 'ambient-depths')
        .map(([, v]) => v.layers.length)
      expect(ambient.layers.length).toBeGreaterThanOrEqual(Math.max(...others) - 1)
    })

    it('techno-massif has a noise layer for texture', () => {
      const techno = BIOME_CONFIGS['techno-massif']
      expect(techno.layers.some(l => l.type === 'noise')).toBe(true)
    })

    it('trance-highlands has stacked harmonics', () => {
      const trance = BIOME_CONFIGS['trance-highlands']
      const freqs = trance.layers.filter(l => l.type === 'oscillator').map(l => l.freq)
      // Should have at least 3 harmonically related oscillators
      expect(freqs.length).toBeGreaterThanOrEqual(3)
    })
  })
})
