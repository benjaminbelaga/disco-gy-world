import { describe, it, expect, beforeEach, vi } from 'vitest'
import useStore from '../stores/useStore'

// Mock localStorage
const localStorageMock = {
  store: {},
  getItem: vi.fn((key) => localStorageMock.store[key] || null),
  setItem: vi.fn((key, value) => { localStorageMock.store[key] = value }),
  removeItem: vi.fn((key) => { delete localStorageMock.store[key] }),
  clear: vi.fn(() => { localStorageMock.store = {} }),
}
Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock })

function resetStore() {
  useStore.setState({
    year: 2026,
    activeGenre: null,
    selectedRelease: null,
    hoveredRelease: null,
    viewMode: 'genre',
    activePlanetTerritory: null,
    playing: false,
    currentTrack: null,
    playerQueue: [],
    playerIndex: 0,
    sidebarOpen: false,
    filterBarOpen: false,
    cameraTarget: null,
    autoTour: false,
    discogsReleases: [],
    genres: [],
    releases: [],
    links: [],
    selectedCity: null,
    globeCenter: { lat: 30, lng: 0 },
    heatmapVisible: true,
    arcsVisible: true,
    citiesData: [],
    arcsData: [],
    heatmapData: [],
    shopsData: [],
    globeLayers: { cities: true, arcs: true, heatmap: true, shops: false },
    discogsUsername: null,
    tasteProfile: null,
    collectionLoaded: false,
    passportOpen: false,
    recommendationsOpen: false,
    collectionGenres: {},
    collectionCountries: {},
    showCollectionOverlay: false,
    onboardingStep: 'vibe',
    onboardingInteractions: 0,
    onboardingStartTime: null,
    activeLabel: null,
    labelReleases: [],
    activeArtist: null,
    artistTimeline: [],
    digPathMode: null,
    digPathWaypoints: [],
    digPathTitle: '',
    digPathDescription: '',
    digPathPlaying: false,
    digPathPlaybackIndex: 0,
  })
  localStorageMock.clear()
}

describe('useStore — Initial state', () => {
  beforeEach(resetStore)

  it('has default year 2026', () => {
    expect(useStore.getState().year).toBe(2026)
  })

  it('has default viewMode genre', () => {
    expect(useStore.getState().viewMode).toBe('genre')
  })

  it('has empty genres, releases, links', () => {
    const s = useStore.getState()
    expect(s.genres).toEqual([])
    expect(s.releases).toEqual([])
    expect(s.links).toEqual([])
  })

  it('has no active genre or selected release', () => {
    const s = useStore.getState()
    expect(s.activeGenre).toBeNull()
    expect(s.selectedRelease).toBeNull()
  })

  it('player is not playing with no track', () => {
    const s = useStore.getState()
    expect(s.playing).toBe(false)
    expect(s.currentTrack).toBeNull()
    expect(s.playerQueue).toEqual([])
  })
})

describe('useStore — Data setters', () => {
  beforeEach(resetStore)

  it('setGenres updates genres', () => {
    const genres = [{ slug: 'techno', name: 'Techno' }]
    useStore.getState().setGenres(genres)
    expect(useStore.getState().genres).toEqual(genres)
  })

  it('setReleases updates releases', () => {
    const releases = [{ id: 1, title: 'Test' }]
    useStore.getState().setReleases(releases)
    expect(useStore.getState().releases).toEqual(releases)
  })

  it('setLinks updates links', () => {
    const links = [{ source: 'techno', target: 'house' }]
    useStore.getState().setLinks(links)
    expect(useStore.getState().links).toEqual(links)
  })
})

describe('useStore — View & Navigation', () => {
  beforeEach(resetStore)

  it('setActiveGenre updates active genre', () => {
    const genre = { slug: 'techno', name: 'Techno' }
    useStore.getState().setActiveGenre(genre)
    expect(useStore.getState().activeGenre).toEqual(genre)
  })

  it('setCameraTarget sets target', () => {
    const target = { x: 1, y: 2, z: 3 }
    useStore.getState().setCameraTarget(target)
    expect(useStore.getState().cameraTarget).toEqual(target)
  })

  it('resetCamera sets default target and clears genre', () => {
    useStore.getState().setActiveGenre({ slug: 'house' })
    useStore.getState().resetCamera()
    const s = useStore.getState()
    expect(s.activeGenre).toBeNull()
    expect(s.cameraTarget).toMatchObject({ x: 0, y: 0, z: 0, _reset: true })
  })

  it('setViewMode updates viewMode', () => {
    useStore.getState().setViewMode('earth')
    expect(useStore.getState().viewMode).toBe('earth')

    useStore.getState().setViewMode('planet')
    expect(useStore.getState().viewMode).toBe('planet')

    useStore.getState().setViewMode('genre')
    expect(useStore.getState().viewMode).toBe('genre')
  })
})

describe('useStore — Player', () => {
  beforeEach(resetStore)

  it('setCurrentTrack sets track and starts playing', () => {
    const track = { artist: 'Test', title: 'Song' }
    useStore.getState().setCurrentTrack(track)
    const s = useStore.getState()
    expect(s.currentTrack).toEqual(track)
    expect(s.playing).toBe(true)
    expect(s.playerQueue).toEqual([track])
    expect(s.playerIndex).toBe(0)
  })

  it('setCurrentTrack with null stops playing', () => {
    useStore.getState().setCurrentTrack({ artist: 'A', title: 'B' })
    useStore.getState().setCurrentTrack(null)
    const s = useStore.getState()
    expect(s.currentTrack).toBeNull()
    expect(s.playing).toBe(false)
  })

  it('setPlayerQueue sets queue and starts at given index', () => {
    const queue = [
      { artist: 'A', title: '1' },
      { artist: 'B', title: '2' },
      { artist: 'C', title: '3' },
    ]
    useStore.getState().setPlayerQueue(queue, 1)
    const s = useStore.getState()
    expect(s.playerQueue).toEqual(queue)
    expect(s.playerIndex).toBe(1)
    expect(s.currentTrack).toEqual(queue[1])
    expect(s.playing).toBe(true)
  })

  it('playNext advances to next track', () => {
    const queue = [
      { artist: 'A', title: '1' },
      { artist: 'B', title: '2' },
    ]
    useStore.getState().setPlayerQueue(queue, 0)
    useStore.getState().playNext()
    const s = useStore.getState()
    expect(s.playerIndex).toBe(1)
    expect(s.currentTrack).toEqual(queue[1])
  })

  it('playNext does nothing at end of queue', () => {
    const queue = [{ artist: 'A', title: '1' }]
    useStore.getState().setPlayerQueue(queue, 0)
    useStore.getState().playNext()
    expect(useStore.getState().playerIndex).toBe(0) // unchanged
  })

  it('playPrev goes to previous track', () => {
    const queue = [
      { artist: 'A', title: '1' },
      { artist: 'B', title: '2' },
    ]
    useStore.getState().setPlayerQueue(queue, 1)
    useStore.getState().playPrev()
    const s = useStore.getState()
    expect(s.playerIndex).toBe(0)
    expect(s.currentTrack).toEqual(queue[0])
  })

  it('playPrev does nothing at start of queue', () => {
    const queue = [{ artist: 'A', title: '1' }]
    useStore.getState().setPlayerQueue(queue, 0)
    useStore.getState().playPrev()
    expect(useStore.getState().playerIndex).toBe(0)
  })

  it('setCurrentTrack with existing queue track updates index', () => {
    const queue = [
      { artist: 'A', title: '1' },
      { artist: 'B', title: '2' },
    ]
    useStore.getState().setPlayerQueue(queue, 0)
    useStore.getState().setCurrentTrack({ artist: 'B', title: '2' })
    expect(useStore.getState().playerIndex).toBe(1)
  })
})

describe('useStore — Onboarding', () => {
  beforeEach(resetStore)

  it('advanceOnboarding increments interactions', () => {
    useStore.getState().advanceOnboarding()
    expect(useStore.getState().onboardingInteractions).toBe(1)
  })

  it('advanceOnboarding completes after 5 interactions', () => {
    for (let i = 0; i < 5; i++) {
      useStore.getState().advanceOnboarding()
    }
    expect(useStore.getState().onboardingStep).toBe('complete')
  })

  it('completeOnboarding sets step to complete and writes localStorage', () => {
    useStore.getState().completeOnboarding()
    expect(useStore.getState().onboardingStep).toBe('complete')
    expect(localStorageMock.setItem).toHaveBeenCalledWith('discoworld-onboarded', '1')
  })

  it('advanceOnboarding transitions tooltip to discogs after 3 interactions', () => {
    useStore.setState({ onboardingStep: 'tooltip', onboardingInteractions: 0 })
    useStore.getState().advanceOnboarding() // 1
    useStore.getState().advanceOnboarding() // 2
    useStore.getState().advanceOnboarding() // 3
    expect(useStore.getState().onboardingStep).toBe('discogs')
  })
})

describe('useStore — Dig Paths', () => {
  beforeEach(resetStore)

  it('addDigPathWaypoint adds waypoint with timestamp', () => {
    useStore.getState().addDigPathWaypoint({ slug: 'techno', note: 'Start' })
    const wps = useStore.getState().digPathWaypoints
    expect(wps).toHaveLength(1)
    expect(wps[0].slug).toBe('techno')
    expect(wps[0].note).toBe('Start')
    expect(wps[0].timestamp).toBeGreaterThan(0)
  })

  it('removeDigPathWaypoint removes by index', () => {
    useStore.getState().addDigPathWaypoint({ slug: 'techno' })
    useStore.getState().addDigPathWaypoint({ slug: 'house' })
    useStore.getState().removeDigPathWaypoint(0)
    const wps = useStore.getState().digPathWaypoints
    expect(wps).toHaveLength(1)
    expect(wps[0].slug).toBe('house')
  })

  it('clearDigPath resets all dig path state', () => {
    useStore.getState().addDigPathWaypoint({ slug: 'techno' })
    useStore.setState({ digPathTitle: 'Test', digPathMode: 'record' })
    useStore.getState().clearDigPath()
    const s = useStore.getState()
    expect(s.digPathWaypoints).toEqual([])
    expect(s.digPathTitle).toBe('')
    expect(s.digPathMode).toBeNull()
  })

  it('loadDigPath sets waypoints and mode to playback', () => {
    const path = {
      title: 'Journey',
      description: 'A test path',
      waypoints: [
        { slug: 'techno', note: 'First' },
        { slug: 'house', note: 'Second' },
      ],
    }
    useStore.getState().loadDigPath(path)
    const s = useStore.getState()
    expect(s.digPathTitle).toBe('Journey')
    expect(s.digPathDescription).toBe('A test path')
    expect(s.digPathMode).toBe('playback')
    expect(s.digPathWaypoints).toHaveLength(2)
    expect(s.digPathWaypoints[0].slug).toBe('techno')
    expect(s.digPathPlaybackIndex).toBe(0)
    expect(s.digPathPlaying).toBe(false)
  })
})

describe('useStore — Collection / Taste Profile', () => {
  beforeEach(resetStore)

  it('setTasteProfile with genres computes collectionGenres', () => {
    // Need genres in store first for the name lookup
    useStore.setState({
      genres: [
        { slug: 'techno', name: 'Techno', aka: 'tech' },
        { slug: 'house', name: 'House' },
      ],
    })

    useStore.getState().setTasteProfile({
      genres: [{ name: 'Techno', count: 10 }],
      styles: [{ name: 'House', count: 5 }],
    })

    const s = useStore.getState()
    expect(s.collectionGenres.techno).toBe(10)
    expect(s.collectionGenres.house).toBe(5)
    expect(s.collectionLoaded).toBe(true)
  })

  it('setTasteProfile with null clears collection', () => {
    useStore.setState({ collectionGenres: { techno: 10 }, collectionLoaded: true })
    useStore.getState().setTasteProfile(null)
    const s = useStore.getState()
    expect(s.collectionGenres).toEqual({})
    expect(s.collectionLoaded).toBe(false)
  })
})
