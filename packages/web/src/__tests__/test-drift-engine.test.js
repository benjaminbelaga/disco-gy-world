import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { startDrift, stopDrift } from '../lib/driftEngine'

describe('driftEngine — startDrift', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    stopDrift()
    vi.useRealTimers()
  })

  const genres = [
    { slug: 'techno', name: 'Techno' },
    { slug: 'house', name: 'House' },
    { slug: 'ambient', name: 'Ambient' },
    { slug: 'trance', name: 'Trance' },
  ]

  const links = [
    { source: 'techno', target: 'house' },
    { source: 'house', target: 'ambient' },
    { source: 'ambient', target: 'trance' },
    { source: 'trance', target: 'techno' },
  ]

  const tracks = {
    techno: [{ artist: 'A', title: 'T1' }],
    house: [{ artist: 'B', title: 'T2' }],
    ambient: [{ artist: 'C', title: 'T3' }],
    trance: [{ artist: 'D', title: 'T4' }],
  }

  it('returns a stop function', () => {
    const stop = startDrift({
      genres,
      links,
      tracks,
      onGenreChange: vi.fn(),
      onTrackPlay: vi.fn(),
      onFlyTo: vi.fn(),
    })
    expect(typeof stop).toBe('function')
  })

  it('calls onGenreChange and onFlyTo immediately with start genre', () => {
    const onGenreChange = vi.fn()
    const onFlyTo = vi.fn()

    startDrift({
      genres,
      links,
      tracks,
      startSlug: 'techno',
      onGenreChange,
      onTrackPlay: vi.fn(),
      onFlyTo,
    })

    expect(onGenreChange).toHaveBeenCalledWith(genres[0])
    expect(onFlyTo).toHaveBeenCalledWith(genres[0])
  })

  it('plays a track shortly after starting', () => {
    const onTrackPlay = vi.fn()

    startDrift({
      genres,
      links,
      tracks,
      startSlug: 'techno',
      onGenreChange: vi.fn(),
      onTrackPlay,
      onFlyTo: vi.fn(),
    })

    // Track plays after 1500ms
    vi.advanceTimersByTime(1500)
    expect(onTrackPlay).toHaveBeenCalled()
  })

  it('moves to next genre after timeout', () => {
    const onGenreChange = vi.fn()
    const onFlyTo = vi.fn()

    startDrift({
      genres,
      links,
      tracks,
      startSlug: 'techno',
      adventurousness: 50,
      onGenreChange,
      onTrackPlay: vi.fn(),
      onFlyTo,
    })

    // Initial call
    expect(onGenreChange).toHaveBeenCalledTimes(1)

    // After 10s (first move timeout) + 2.5s (camera travel) = step runs
    vi.advanceTimersByTime(10000)
    // onFlyTo called again for next genre
    expect(onFlyTo.mock.calls.length).toBeGreaterThanOrEqual(2)
  })

  it('stopDrift prevents further moves', () => {
    const onGenreChange = vi.fn()

    startDrift({
      genres,
      links,
      tracks,
      startSlug: 'techno',
      onGenreChange,
      onTrackPlay: vi.fn(),
      onFlyTo: vi.fn(),
    })

    stopDrift()
    const callCount = onGenreChange.mock.calls.length

    // Advance time significantly
    vi.advanceTimersByTime(60000)
    expect(onGenreChange.mock.calls.length).toBe(callCount)
  })

  it('returns no-op if start genre not found', () => {
    const stop = startDrift({
      genres,
      links,
      tracks,
      startSlug: 'nonexistent',
      onGenreChange: vi.fn(),
      onTrackPlay: vi.fn(),
      onFlyTo: vi.fn(),
    })
    expect(typeof stop).toBe('function')
  })
})
