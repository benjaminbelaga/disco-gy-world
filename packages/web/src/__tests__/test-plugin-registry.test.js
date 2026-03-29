import { describe, it, expect, beforeEach } from 'vitest'
import { validateAdapter } from '../lib/plugins/RecordStoreAdapter'
import { registerAdapter, getAdapter, getAllAdapters, removeAdapter, hasAdapter, getAdapterCount, clearAdapters } from '../lib/plugins/registry'
import { DiscogsAdapter } from '../lib/plugins/adapters/DiscogsAdapter'
import { YoyakuAdapter } from '../lib/plugins/adapters/YoyakuAdapter'

describe('RecordStoreAdapter', () => {
  describe('validateAdapter', () => {
    it('validates a proper adapter', () => {
      const adapter = new DiscogsAdapter()
      const { valid, errors } = validateAdapter(adapter)
      expect(valid).toBe(true)
      expect(errors).toHaveLength(0)
    })

    it('rejects adapter missing id', () => {
      const { valid } = validateAdapter({ name: 'x', url: 'x', search: () => {}, getRelease: () => {}, checkAvailability: () => {}, getLocations: () => {} })
      expect(valid).toBe(false)
    })

    it('rejects adapter missing search', () => {
      const { valid, errors } = validateAdapter({ id: 'x', name: 'x', url: 'x', getRelease: () => {}, checkAvailability: () => {}, getLocations: () => {} })
      expect(valid).toBe(false)
      expect(errors.some(e => e.includes('search'))).toBe(true)
    })
  })
})

describe('Plugin Registry', () => {
  beforeEach(() => clearAdapters())

  it('registers an adapter', () => {
    registerAdapter(new DiscogsAdapter())
    expect(getAdapterCount()).toBe(1)
  })

  it('retrieves adapter by id', () => {
    registerAdapter(new DiscogsAdapter())
    const adapter = getAdapter('discogs')
    expect(adapter).not.toBeNull()
    expect(adapter.name).toBe('Discogs Marketplace')
  })

  it('returns null for unknown id', () => {
    expect(getAdapter('nonexistent')).toBeNull()
  })

  it('lists all adapters', () => {
    registerAdapter(new DiscogsAdapter())
    registerAdapter(new YoyakuAdapter())
    expect(getAllAdapters()).toHaveLength(2)
  })

  it('removes an adapter', () => {
    registerAdapter(new DiscogsAdapter())
    expect(removeAdapter('discogs')).toBe(true)
    expect(getAdapterCount()).toBe(0)
  })

  it('hasAdapter works', () => {
    registerAdapter(new YoyakuAdapter())
    expect(hasAdapter('yoyaku')).toBe(true)
    expect(hasAdapter('discogs')).toBe(false)
  })

  it('throws on invalid adapter', () => {
    expect(() => registerAdapter({})).toThrow('Invalid adapter')
  })

  it('clears all adapters', () => {
    registerAdapter(new DiscogsAdapter())
    registerAdapter(new YoyakuAdapter())
    clearAdapters()
    expect(getAdapterCount()).toBe(0)
  })
})

describe('DiscogsAdapter', () => {
  const adapter = new DiscogsAdapter()

  it('has correct id', () => expect(adapter.id).toBe('discogs'))
  it('has correct name', () => expect(adapter.name).toBe('Discogs Marketplace'))

  it('search returns discogs URL', async () => {
    const results = await adapter.search('aphex twin')
    expect(results[0].url).toContain('discogs.com')
  })

  it('checkAvailability with discogs ID', async () => {
    const result = await adapter.checkAvailability({ discogsId: 12345, title: 'Test' })
    expect(result.url).toContain('12345')
    expect(result.available).toBe(true)
  })

  it('getLocations returns empty', () => {
    expect(adapter.getLocations()).toHaveLength(0)
  })
})

describe('YoyakuAdapter', () => {
  const adapter = new YoyakuAdapter()

  it('has correct id', () => expect(adapter.id).toBe('yoyaku'))
  it('has correct name', () => expect(adapter.name).toBe('YOYAKU'))

  it('search returns yoyaku URL', async () => {
    const results = await adapter.search('techno')
    expect(results[0].url).toContain('yoyaku.io')
  })

  it('getLocations returns Paris store', () => {
    const locs = adapter.getLocations()
    expect(locs).toHaveLength(1)
    expect(locs[0].city).toBe('Paris')
    expect(locs[0].lat).toBeCloseTo(48.87, 1)
  })

  it('checkAvailability returns yoyaku URL', async () => {
    const result = await adapter.checkAvailability({ artist: 'Dettmann', title: 'Range' })
    expect(result.url).toContain('yoyaku.io')
  })
})
