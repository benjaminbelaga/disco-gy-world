import { describe, it, expect, beforeEach } from 'vitest'
import useStore from '../stores/useStore'
import { buildShareUrl } from '../hooks/useUrlState'

function resetStore() {
  useStore.setState({
    viewMode: 'genre',
    activeGenre: null,
    selectedCity: null,
    autoTour: false,
    globeCenter: { lat: 30, lng: 0 },
    year: 2026,
  })
}

describe('useUrlState — buildShareUrl', () => {
  beforeEach(resetStore)

  it('returns base URL with no params for default state', () => {
    const url = buildShareUrl()
    // Default genre view, year 2026, no genre selected -> no params
    expect(url).not.toContain('?')
  })

  it('includes view param when not genre', () => {
    useStore.setState({ viewMode: 'earth' })
    const url = buildShareUrl()
    expect(url).toContain('view=earth')
  })

  it('includes genre param when genre is active', () => {
    useStore.setState({ activeGenre: { slug: 'techno', name: 'Techno' } })
    const url = buildShareUrl()
    expect(url).toContain('genre=techno')
  })

  it('includes city param when city is selected', () => {
    useStore.setState({ selectedCity: { name: 'Berlin', slug: 'berlin' } })
    const url = buildShareUrl()
    expect(url).toContain('city=berlin')
  })

  it('includes drift param when auto tour is on', () => {
    useStore.setState({ autoTour: true })
    const url = buildShareUrl()
    expect(url).toContain('drift=1')
  })

  it('includes lat/lng when in earth view', () => {
    useStore.setState({ viewMode: 'earth', globeCenter: { lat: 52.5, lng: 13.4 } })
    const url = buildShareUrl()
    expect(url).toContain('lat=52.5')
    expect(url).toContain('lng=13.4')
  })

  it('does NOT include lat/lng when in genre view', () => {
    useStore.setState({ viewMode: 'genre', globeCenter: { lat: 52.5, lng: 13.4 } })
    const url = buildShareUrl()
    expect(url).not.toContain('lat=')
  })

  it('includes year when not 2026', () => {
    useStore.setState({ year: 1990 })
    const url = buildShareUrl()
    expect(url).toContain('year=1990')
  })

  it('does NOT include year when 2026', () => {
    useStore.setState({ year: 2026 })
    const url = buildShareUrl()
    expect(url).not.toContain('year=')
  })

  it('combines multiple params', () => {
    useStore.setState({
      viewMode: 'earth',
      autoTour: true,
      globeCenter: { lat: 40.7, lng: -74.0 },
      year: 2000,
    })
    const url = buildShareUrl()
    expect(url).toContain('view=earth')
    expect(url).toContain('drift=1')
    expect(url).toContain('lat=40.7')
    expect(url).toContain('year=2000')
  })
})
