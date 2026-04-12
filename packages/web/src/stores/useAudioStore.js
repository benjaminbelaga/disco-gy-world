import { create } from 'zustand'
import {
  connectMicrophone,
  disconnect as disconnectAnalyzer,
  getFrequencyData,
} from '../lib/audioAnalyzer'

function lerp(a, b, t) {
  return a + (b - a) * t
}

/**
 * Audio store — drives all audio-reactive visuals.
 *
 * Modes:
 *   'off'       — static visuals (default)
 *   'simulated' — fake random data when YouTube is playing (cross-origin, no Web Audio)
 *   'mic'       — real microphone input via Web Audio API
 */
const useAudioStore = create((set, get) => {
  let rafId = null
  // Simulated-mode state
  let phase = 0
  let nextChangeTime = 0
  let targetBass = 0.5
  let targetMid = 0.4
  let targetHigh = 0.3
  let lastTime = 0

  function simulatedLoop(timestamp) {
    const state = get()
    if (!state.isPlaying || state.audioMode !== 'simulated') return

    const dt = lastTime ? Math.min((timestamp - lastTime) / 1000, 0.05) : 0.016
    lastTime = timestamp
    phase += dt

    if (phase > nextChangeTime) {
      targetBass = 0.3 + Math.random() * 0.7
      targetMid = 0.2 + Math.random() * 0.7
      targetHigh = 0.1 + Math.random() * 0.7
      nextChangeTime = phase + 0.2 + Math.random() * 0.6
    }

    const bass = lerp(state.bass, targetBass, 0.08)
    const mid = lerp(state.mid, targetMid, 0.06)
    const high = lerp(state.high, targetHigh, 0.1)
    const energy = (bass + mid + high) / 3

    set({ bass, mid, high, energy, beat: false })
    rafId = requestAnimationFrame(simulatedLoop)
  }

  function realLoop() {
    const state = get()
    if (!state.isPlaying || state.audioMode !== 'mic') return

    const data = getFrequencyData()
    // Smooth the real data for visual comfort
    const bass = lerp(state.bass, data.bass, 0.15)
    const mid = lerp(state.mid, data.mid, 0.12)
    const high = lerp(state.high, data.treble, 0.14)
    const energy = lerp(state.energy, data.energy, 0.12)

    set({ bass, mid, high, energy, beat: data.beat })
    rafId = requestAnimationFrame(realLoop)
  }

  function startLoop() {
    if (rafId) return
    const state = get()
    lastTime = 0
    phase = 0
    nextChangeTime = 0

    if (state.audioMode === 'mic') {
      rafId = requestAnimationFrame(realLoop)
    } else if (state.audioMode === 'simulated') {
      rafId = requestAnimationFrame(simulatedLoop)
    }
  }

  function stopLoop() {
    if (rafId) {
      cancelAnimationFrame(rafId)
      rafId = null
    }
    // Smooth decay to zero
    let decayFrames = 30
    function decay() {
      const s = get()
      const bass = lerp(s.bass, 0, 0.06)
      const mid = lerp(s.mid, 0, 0.06)
      const high = lerp(s.high, 0, 0.06)
      const energy = (bass + mid + high) / 3
      set({ bass, mid, high, energy, beat: false })
      decayFrames--
      if (decayFrames > 0 && energy > 0.005) {
        requestAnimationFrame(decay)
      } else {
        set({ bass: 0, mid: 0, high: 0, energy: 0, beat: false })
      }
    }
    requestAnimationFrame(decay)
  }

  return {
    bass: 0,
    mid: 0,
    high: 0,
    energy: 0,
    beat: false,
    isPlaying: false,
    audioMode: 'off', // 'off' | 'simulated' | 'mic'

    setPlaying: (playing) => {
      set({ isPlaying: playing })
      if (playing) {
        // Only start loop if user has manually enabled an audio mode
        // Do NOT auto-switch from 'off' — that would drive audio-reactive visuals with fake data
        const mode = get().audioMode
        if (mode !== 'off') startLoop()
      } else {
        stopLoop()
      }
    },

    /**
     * Toggle audio source mode: off → simulated → mic → off
     * Called by the UI toggle button.
     */
    cycleAudioMode: async () => {
      const state = get()
      const current = state.audioMode

      // Stop current loop
      stopLoop()
      disconnectAnalyzer()

      if (current === 'off') {
        set({ audioMode: 'simulated', isPlaying: true })
        startLoop()
      } else if (current === 'simulated') {
        const ok = await connectMicrophone()
        if (ok) {
          set({ audioMode: 'mic', isPlaying: true })
          startLoop()
        } else {
          // Mic denied — cycle back to off
          set({ audioMode: 'off', isPlaying: false })
        }
      } else {
        // mic → off
        set({ audioMode: 'off', isPlaying: false, bass: 0, mid: 0, high: 0, energy: 0, beat: false })
      }
    },

    /**
     * Set a specific mode directly.
     */
    setAudioMode: async (mode) => {
      stopLoop()
      disconnectAnalyzer()

      if (mode === 'mic') {
        const ok = await connectMicrophone()
        if (!ok) {
          set({ audioMode: 'off', isPlaying: false })
          return
        }
      }

      set({ audioMode: mode, isPlaying: mode !== 'off' })
      if (mode !== 'off') startLoop()
    },

    startLoop,
    stopLoop,
  }
})

export default useAudioStore
