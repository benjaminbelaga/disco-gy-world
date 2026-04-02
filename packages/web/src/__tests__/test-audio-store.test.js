import { describe, it, expect, beforeEach, vi } from 'vitest'

// Mock the audioAnalyzer module before importing the store
vi.mock('../lib/audioAnalyzer', () => ({
  connectMicrophone: vi.fn(() => Promise.resolve(true)),
  disconnect: vi.fn(),
  getFrequencyData: vi.fn(() => ({ bass: 0.5, mid: 0.4, treble: 0.3, energy: 0.4, beat: false })),
}))

// Mock requestAnimationFrame / cancelAnimationFrame
let rafCallback = null
globalThis.requestAnimationFrame = vi.fn((cb) => {
  rafCallback = cb
  return 1
})
globalThis.cancelAnimationFrame = vi.fn()

const { default: useAudioStore } = await import('../stores/useAudioStore')

function resetAudioStore() {
  useAudioStore.setState({
    bass: 0,
    mid: 0,
    high: 0,
    energy: 0,
    beat: false,
    isPlaying: false,
    audioMode: 'off',
  })
}

describe('useAudioStore — Initial state', () => {
  beforeEach(resetAudioStore)

  it('starts with all levels at 0', () => {
    const s = useAudioStore.getState()
    expect(s.bass).toBe(0)
    expect(s.mid).toBe(0)
    expect(s.high).toBe(0)
    expect(s.energy).toBe(0)
  })

  it('starts not playing in off mode', () => {
    const s = useAudioStore.getState()
    expect(s.isPlaying).toBe(false)
    expect(s.audioMode).toBe('off')
  })

  it('beat is false initially', () => {
    expect(useAudioStore.getState().beat).toBe(false)
  })
})

describe('useAudioStore — setPlaying', () => {
  beforeEach(resetAudioStore)

  it('setPlaying(true) auto-switches from off to simulated', () => {
    useAudioStore.getState().setPlaying(true)
    const s = useAudioStore.getState()
    expect(s.isPlaying).toBe(true)
    expect(s.audioMode).toBe('simulated')
  })

  it('setPlaying(false) stops playing', () => {
    useAudioStore.getState().setPlaying(true)
    useAudioStore.getState().setPlaying(false)
    expect(useAudioStore.getState().isPlaying).toBe(false)
  })
})

describe('useAudioStore — cycleAudioMode', () => {
  beforeEach(resetAudioStore)

  it('cycles off -> simulated', async () => {
    await useAudioStore.getState().cycleAudioMode()
    const s = useAudioStore.getState()
    expect(s.audioMode).toBe('simulated')
    expect(s.isPlaying).toBe(true)
  })

  it('cycles simulated -> mic', async () => {
    useAudioStore.setState({ audioMode: 'simulated', isPlaying: true })
    await useAudioStore.getState().cycleAudioMode()
    const s = useAudioStore.getState()
    expect(s.audioMode).toBe('mic')
    expect(s.isPlaying).toBe(true)
  })

  it('cycles mic -> off', async () => {
    useAudioStore.setState({ audioMode: 'mic', isPlaying: true })
    await useAudioStore.getState().cycleAudioMode()
    const s = useAudioStore.getState()
    expect(s.audioMode).toBe('off')
    expect(s.isPlaying).toBe(false)
  })
})
