import { describe, it, expect } from 'vitest'
import { buildSearchIndex, searchGenres } from '../utils/vibeSearch'

const mockGenres = [
  { slug: 'techno', name: 'Techno', aka: 'tech,detroit techno', scene: 'Berlin' },
  { slug: 'house', name: 'House', aka: 'deep house,chicago house', scene: 'Chicago' },
  { slug: 'ambient', name: 'Ambient', aka: 'ambient music', scene: 'Global' },
  { slug: 'drum-and-bass', name: 'Drum and Bass', aka: 'dnb,jungle', scene: 'London' },
  { slug: 'trance', name: 'Trance', aka: 'psytrance,goa', scene: 'Goa' },
]

describe('vibeSearch — buildSearchIndex', () => {
  it('creates an index from genres', () => {
    const index = buildSearchIndex(mockGenres)
    expect(index).toBeInstanceOf(Map)
    expect(index.size).toBeGreaterThan(0)
  })

  it('indexes genre names', () => {
    const index = buildSearchIndex(mockGenres)
    expect(index.has('techno')).toBe(true)
    expect(index.has('house')).toBe(true)
  })

  it('indexes aka aliases', () => {
    const index = buildSearchIndex(mockGenres)
    expect(index.has('dnb')).toBe(true)
    expect(index.has('jungle')).toBe(true)
    expect(index.has('deep house')).toBe(true)
  })

  it('indexes scenes', () => {
    const index = buildSearchIndex(mockGenres)
    expect(index.has('berlin')).toBe(true)
    expect(index.has('chicago')).toBe(true)
  })
})

describe('vibeSearch — searchGenres', () => {
  let index

  // Build index once
  index = buildSearchIndex(mockGenres)

  it('returns empty for empty query', () => {
    expect(searchGenres('', index, mockGenres)).toEqual([])
  })

  it('returns empty for single-char query', () => {
    expect(searchGenres('a', index, mockGenres)).toEqual([])
  })

  it('finds techno by name', () => {
    const results = searchGenres('techno', index, mockGenres)
    expect(results.length).toBeGreaterThan(0)
    expect(results[0].genre.slug).toBe('techno')
  })

  it('finds house by name', () => {
    const results = searchGenres('house', index, mockGenres)
    expect(results.length).toBeGreaterThan(0)
    const slugs = results.map(r => r.genre.slug)
    expect(slugs).toContain('house')
  })

  it('finds genre by aka alias', () => {
    const results = searchGenres('jungle', index, mockGenres)
    expect(results.length).toBeGreaterThan(0)
    expect(results[0].genre.slug).toBe('drum-and-bass')
  })

  it('finds genre by scene', () => {
    const results = searchGenres('berlin', index, mockGenres)
    expect(results.length).toBeGreaterThan(0)
    const slugs = results.map(r => r.genre.slug)
    expect(slugs).toContain('techno')
  })

  it('respects limit parameter', () => {
    const results = searchGenres('techno house ambient', index, mockGenres, 2)
    expect(results.length).toBeLessThanOrEqual(2)
  })

  it('results are sorted by score descending', () => {
    const results = searchGenres('techno', index, mockGenres, 10)
    for (let i = 1; i < results.length; i++) {
      expect(results[i - 1].score).toBeGreaterThanOrEqual(results[i].score)
    }
  })
})
