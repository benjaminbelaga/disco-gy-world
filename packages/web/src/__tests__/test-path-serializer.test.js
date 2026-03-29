import { describe, it, expect } from 'vitest'
import { serializePath, deserializePath, pathToUrl, pathFromUrl } from '../lib/pathSerializer'

describe('pathSerializer — serializePath / deserializePath', () => {
  it('round-trips a simple path', () => {
    const path = {
      title: 'My Journey',
      description: 'A test path',
      waypoints: [
        { slug: 'techno', note: 'Start here' },
        { slug: 'house', note: 'Then here' },
      ],
    }
    const encoded = serializePath(path)
    expect(typeof encoded).toBe('string')
    expect(encoded.length).toBeGreaterThan(0)

    const decoded = deserializePath(encoded)
    expect(decoded).not.toBeNull()
    expect(decoded.title).toBe('My Journey')
    expect(decoded.description).toBe('A test path')
    expect(decoded.waypoints).toHaveLength(2)
    expect(decoded.waypoints[0].slug).toBe('techno')
    expect(decoded.waypoints[0].note).toBe('Start here')
    expect(decoded.waypoints[1].slug).toBe('house')
  })

  it('handles waypoints without notes', () => {
    const path = {
      title: 'Minimal',
      description: '',
      waypoints: [{ slug: 'ambient', note: '' }, { slug: 'trance', note: '' }],
    }
    const decoded = deserializePath(serializePath(path))
    expect(decoded.waypoints).toHaveLength(2)
    expect(decoded.waypoints[0].slug).toBe('ambient')
    expect(decoded.waypoints[0].note).toBe('')
  })

  it('strips pipe chars from title/description', () => {
    const path = {
      title: 'Title|With|Pipes',
      description: 'Desc|Pipes',
      waypoints: [{ slug: 'techno', note: '' }],
    }
    const decoded = deserializePath(serializePath(path))
    expect(decoded.title).not.toContain('|')
    expect(decoded.description).not.toContain('|')
  })

  it('strips special separator chars from notes', () => {
    const path = {
      title: 'Test',
      description: '',
      waypoints: [{ slug: 'techno', note: 'note|with:special,chars' }],
    }
    const decoded = deserializePath(serializePath(path))
    expect(decoded.waypoints[0].note).not.toContain('|')
    expect(decoded.waypoints[0].note).not.toContain(',')
    // Colons are the note separator, so they get replaced
  })

  it('handles UTF-8 characters', () => {
    const path = {
      title: 'Musique electronique',
      description: 'Decouverte des genres',
      waypoints: [{ slug: 'techno', note: 'Berlin scene' }],
    }
    const decoded = deserializePath(serializePath(path))
    expect(decoded.title).toBe('Musique electronique')
  })

  it('returns null for invalid encoded data', () => {
    expect(deserializePath('not-valid-base64!!!')).toBeNull()
  })

  it('returns null for empty waypoints', () => {
    // Manually encode something with no waypoints
    const raw = 'title|desc|'
    const bytes = new TextEncoder().encode(raw)
    const binary = Array.from(bytes, b => String.fromCharCode(b)).join('')
    const encoded = btoa(binary)
    expect(deserializePath(encoded)).toBeNull()
  })
})

describe('pathSerializer — pathToUrl', () => {
  it('generates URL with #path= hash', () => {
    const path = {
      title: 'Test',
      description: '',
      waypoints: [{ slug: 'techno', note: '' }],
    }
    const url = pathToUrl(path)
    expect(url).toContain('#path=')
  })
})

describe('pathSerializer — pathFromUrl', () => {
  it('returns null when no path hash', () => {
    // jsdom default hash is empty
    window.location.hash = ''
    expect(pathFromUrl()).toBeNull()
  })

  it('parses path from hash', () => {
    const path = {
      title: 'Shared',
      description: 'A shared path',
      waypoints: [{ slug: 'house', note: 'Go' }],
    }
    const encoded = serializePath(path)
    window.location.hash = `#path=${encoded}`
    const result = pathFromUrl()
    expect(result).not.toBeNull()
    expect(result.title).toBe('Shared')
    expect(result.waypoints[0].slug).toBe('house')
  })
})
