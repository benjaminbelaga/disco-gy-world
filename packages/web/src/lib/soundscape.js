/**
 * Biome Soundscape Engine — procedural ambient audio for each DiscoWorld biome.
 *
 * Uses Web Audio API to generate unique ambient drones/textures per biome.
 * Crossfades between soundscapes as the user navigates genres.
 * No audio files needed — everything is synthesized in real-time.
 */

let audioCtx = null
let masterGain = null
let currentBiome = null
let activeNodes = []
let crossfadeTimer = null

const BIOME_CONFIGS = {
  'techno-massif': {
    // Deep, dark, industrial — sub bass + filtered noise
    layers: [
      { type: 'oscillator', wave: 'sawtooth', freq: 40, gain: 0.08, detune: -5, filter: { type: 'lowpass', freq: 120, Q: 8 } },
      { type: 'oscillator', wave: 'sine', freq: 55, gain: 0.05, lfo: { rate: 0.1, depth: 3 } },
      { type: 'noise', gain: 0.015, filter: { type: 'bandpass', freq: 800, Q: 2 } },
    ],
  },
  'house-plains': {
    // Warm, groovy, open — warm pad + soft bass
    layers: [
      { type: 'oscillator', wave: 'triangle', freq: 65, gain: 0.06, filter: { type: 'lowpass', freq: 200, Q: 1 } },
      { type: 'oscillator', wave: 'sine', freq: 130, gain: 0.03, lfo: { rate: 0.2, depth: 5 } },
      { type: 'oscillator', wave: 'sine', freq: 196, gain: 0.02, lfo: { rate: 0.15, depth: 2 } },
    ],
  },
  'disco-riviera': {
    // Bright, sparkly, warm — major harmony shimmer
    layers: [
      { type: 'oscillator', wave: 'sine', freq: 174, gain: 0.04, lfo: { rate: 0.3, depth: 4 } },
      { type: 'oscillator', wave: 'sine', freq: 220, gain: 0.03, lfo: { rate: 0.25, depth: 3 } },
      { type: 'oscillator', wave: 'triangle', freq: 65, gain: 0.04, filter: { type: 'lowpass', freq: 300, Q: 1 } },
    ],
  },
  'ambient-depths': {
    // Ethereal, spacious, oceanic — reverberant drones
    layers: [
      { type: 'oscillator', wave: 'sine', freq: 82, gain: 0.06, lfo: { rate: 0.05, depth: 2 } },
      { type: 'oscillator', wave: 'sine', freq: 123, gain: 0.04, lfo: { rate: 0.07, depth: 3 } },
      { type: 'oscillator', wave: 'sine', freq: 164, gain: 0.03, lfo: { rate: 0.03, depth: 1 } },
      { type: 'noise', gain: 0.008, filter: { type: 'lowpass', freq: 400, Q: 0.5 } },
    ],
  },
  'jungle-canopy': {
    // Dense, organic, rhythmic — layered sub + texture
    layers: [
      { type: 'oscillator', wave: 'sawtooth', freq: 55, gain: 0.06, filter: { type: 'lowpass', freq: 150, Q: 5 } },
      { type: 'noise', gain: 0.02, filter: { type: 'bandpass', freq: 2000, Q: 3 } },
      { type: 'oscillator', wave: 'triangle', freq: 110, gain: 0.03, lfo: { rate: 0.4, depth: 8 } },
    ],
  },
  'trance-highlands': {
    // Soaring, melodic, euphoric — stacked fifths
    layers: [
      { type: 'oscillator', wave: 'sine', freq: 110, gain: 0.05, lfo: { rate: 0.08, depth: 2 } },
      { type: 'oscillator', wave: 'sine', freq: 165, gain: 0.04, lfo: { rate: 0.12, depth: 3 } },
      { type: 'oscillator', wave: 'sine', freq: 220, gain: 0.03, lfo: { rate: 0.06, depth: 2 } },
      { type: 'oscillator', wave: 'triangle', freq: 55, gain: 0.04, filter: { type: 'lowpass', freq: 200, Q: 1 } },
    ],
  },
  'industrial-wasteland': {
    // Harsh, metallic, dystopian — distorted noise + low drone
    layers: [
      { type: 'oscillator', wave: 'sawtooth', freq: 36, gain: 0.07, filter: { type: 'lowpass', freq: 100, Q: 10 } },
      { type: 'noise', gain: 0.025, filter: { type: 'bandpass', freq: 1200, Q: 5 } },
      { type: 'oscillator', wave: 'square', freq: 73, gain: 0.02, lfo: { rate: 0.6, depth: 15 }, filter: { type: 'lowpass', freq: 300, Q: 3 } },
    ],
  },
  'idm-crystalline': {
    // Glitchy, precise, mathematical — detuned harmonics
    layers: [
      { type: 'oscillator', wave: 'sine', freq: 220, gain: 0.03, lfo: { rate: 0.33, depth: 7 } },
      { type: 'oscillator', wave: 'sine', freq: 277, gain: 0.02, lfo: { rate: 0.41, depth: 5 } },
      { type: 'oscillator', wave: 'sine', freq: 330, gain: 0.015, lfo: { rate: 0.57, depth: 3 } },
      { type: 'noise', gain: 0.006, filter: { type: 'highpass', freq: 4000, Q: 1 } },
    ],
  },
  'dubstep-rift': {
    // Heavy, dark, seismic — wobble bass + deep sub
    layers: [
      { type: 'oscillator', wave: 'sawtooth', freq: 44, gain: 0.08, filter: { type: 'lowpass', freq: 100, Q: 12 }, lfo: { rate: 0.5, depth: 20 } },
      { type: 'oscillator', wave: 'sine', freq: 33, gain: 0.06 },
      { type: 'noise', gain: 0.012, filter: { type: 'bandpass', freq: 600, Q: 4 } },
    ],
  },
  'garage-district': {
    // Skippy, urban, warm ��� syncopated feel
    layers: [
      { type: 'oscillator', wave: 'triangle', freq: 73, gain: 0.05, filter: { type: 'lowpass', freq: 250, Q: 2 } },
      { type: 'oscillator', wave: 'sine', freq: 146, gain: 0.03, lfo: { rate: 0.2, depth: 4 } },
      { type: 'oscillator', wave: 'sine', freq: 220, gain: 0.02, lfo: { rate: 0.15, depth: 2 } },
    ],
  },
  'urban-quarter': {
    // Gritty, street, rhythmic — lo-fi texture
    layers: [
      { type: 'oscillator', wave: 'triangle', freq: 55, gain: 0.05, filter: { type: 'lowpass', freq: 200, Q: 1 } },
      { type: 'noise', gain: 0.015, filter: { type: 'bandpass', freq: 500, Q: 1 } },
      { type: 'oscillator', wave: 'sine', freq: 110, gain: 0.03, lfo: { rate: 0.1, depth: 2 } },
    ],
  },
  'source-monuments': {
    // Historic, warm, reverential — organ-like
    layers: [
      { type: 'oscillator', wave: 'sine', freq: 65, gain: 0.05 },
      { type: 'oscillator', wave: 'sine', freq: 130, gain: 0.03 },
      { type: 'oscillator', wave: 'sine', freq: 195, gain: 0.02 },
      { type: 'oscillator', wave: 'sine', freq: 260, gain: 0.01 },
    ],
  },
  'unknown': {
    layers: [
      { type: 'oscillator', wave: 'sine', freq: 82, gain: 0.04, lfo: { rate: 0.1, depth: 2 } },
      { type: 'noise', gain: 0.008, filter: { type: 'lowpass', freq: 600, Q: 0.5 } },
    ],
  },
}

function getContext() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)()
    masterGain = audioCtx.createGain()
    masterGain.gain.value = 0
    masterGain.connect(audioCtx.destination)
  }
  return audioCtx
}

function createNoiseBuffer(ctx, duration = 2) {
  const size = ctx.sampleRate * duration
  const buf = ctx.createBuffer(1, size, ctx.sampleRate)
  const data = buf.getChannelData(0)
  for (let i = 0; i < size; i++) {
    data[i] = Math.random() * 2 - 1
  }
  return buf
}

function createLayer(ctx, config, destination) {
  const nodes = []

  if (config.type === 'oscillator') {
    const osc = ctx.createOscillator()
    osc.type = config.wave || 'sine'
    osc.frequency.value = config.freq || 110
    if (config.detune) osc.detune.value = config.detune
    nodes.push(osc)

    // LFO for frequency modulation
    if (config.lfo) {
      const lfo = ctx.createOscillator()
      lfo.frequency.value = config.lfo.rate || 0.1
      const lfoGain = ctx.createGain()
      lfoGain.gain.value = config.lfo.depth || 2
      lfo.connect(lfoGain)
      lfoGain.connect(osc.frequency)
      lfo.start()
      nodes.push(lfo, lfoGain)
    }

    let lastNode = osc

    // Filter
    if (config.filter) {
      const filter = ctx.createBiquadFilter()
      filter.type = config.filter.type || 'lowpass'
      filter.frequency.value = config.filter.freq || 1000
      filter.Q.value = config.filter.Q || 1
      lastNode.connect(filter)
      lastNode = filter
      nodes.push(filter)
    }

    // Output gain
    const gain = ctx.createGain()
    gain.gain.value = config.gain || 0.05
    lastNode.connect(gain)
    gain.connect(destination)
    nodes.push(gain)

    osc.start()

    return { nodes, stop: () => { osc.stop(); nodes.forEach(n => n.disconnect()) } }
  }

  if (config.type === 'noise') {
    const noise = ctx.createBufferSource()
    noise.buffer = createNoiseBuffer(ctx)
    noise.loop = true
    nodes.push(noise)

    let lastNode = noise

    if (config.filter) {
      const filter = ctx.createBiquadFilter()
      filter.type = config.filter.type || 'lowpass'
      filter.frequency.value = config.filter.freq || 1000
      filter.Q.value = config.filter.Q || 1
      lastNode.connect(filter)
      lastNode = filter
      nodes.push(filter)
    }

    const gain = ctx.createGain()
    gain.gain.value = config.gain || 0.01
    lastNode.connect(gain)
    gain.connect(destination)
    nodes.push(gain)

    noise.start()

    return { nodes, stop: () => { noise.stop(); nodes.forEach(n => n.disconnect()) } }
  }

  return null
}

/**
 * Transition to a new biome soundscape with crossfade.
 */
export function setBiome(biomeName) {
  if (biomeName === currentBiome) return
  currentBiome = biomeName

  const ctx = getContext()
  if (ctx.state === 'suspended') {
    ctx.resume()
  }

  const config = BIOME_CONFIGS[biomeName] || BIOME_CONFIGS['unknown']

  // Fade out current layers
  const fadeTime = 3 // seconds
  const now = ctx.currentTime

  // Fade out master
  masterGain.gain.cancelScheduledValues(now)
  masterGain.gain.setValueAtTime(masterGain.gain.value, now)
  masterGain.gain.linearRampToValueAtTime(0, now + fadeTime * 0.5)

  // Schedule cleanup + new layers
  if (crossfadeTimer) clearTimeout(crossfadeTimer)
  crossfadeTimer = setTimeout(() => {
    // Stop old layers
    activeNodes.forEach(layer => {
      try { layer.stop() } catch {}
    })
    activeNodes = []

    // Create new layers
    config.layers.forEach(layerConfig => {
      const layer = createLayer(ctx, layerConfig, masterGain)
      if (layer) activeNodes.push(layer)
    })

    // Fade in
    const t = ctx.currentTime
    masterGain.gain.cancelScheduledValues(t)
    masterGain.gain.setValueAtTime(0, t)
    masterGain.gain.linearRampToValueAtTime(1, t + fadeTime)
  }, fadeTime * 500) // Half the fade time in ms
}

/**
 * Set master volume (0-1).
 */
export function setVolume(vol) {
  if (!masterGain) return
  const ctx = getContext()
  masterGain.gain.cancelScheduledValues(ctx.currentTime)
  masterGain.gain.setValueAtTime(masterGain.gain.value, ctx.currentTime)
  masterGain.gain.linearRampToValueAtTime(vol, ctx.currentTime + 0.5)
}

/**
 * Stop all soundscape audio.
 */
export function stopSoundscape() {
  if (crossfadeTimer) clearTimeout(crossfadeTimer)
  if (!audioCtx) return

  const now = audioCtx.currentTime
  masterGain.gain.cancelScheduledValues(now)
  masterGain.gain.setValueAtTime(masterGain.gain.value, now)
  masterGain.gain.linearRampToValueAtTime(0, now + 1)

  setTimeout(() => {
    activeNodes.forEach(layer => {
      try { layer.stop() } catch {}
    })
    activeNodes = []
    currentBiome = null
  }, 1100)
}

/**
 * Check if soundscape is currently active.
 */
export function isActive() {
  return currentBiome !== null && activeNodes.length > 0
}

export { BIOME_CONFIGS }
