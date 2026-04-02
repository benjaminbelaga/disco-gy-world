/**
 * Real-time audio analyzer using Web Audio API.
 * Exposes bass/mid/treble (0-1) and beat detection from any audio source.
 * Singleton — one analyzer shared across the app.
 */

const FFT_SIZE = 256
const BEAT_THRESHOLD = 0.42
const BEAT_COOLDOWN_MS = 180

let audioCtx = null
let analyser = null
let freqData = null
let source = null
let micStream = null
let _mode = 'off' // 'off' | 'mic' | 'element'
let lastBeatTime = 0

// Frequency bin ranges (for FFT_SIZE=256 → 128 bins, ~86Hz per bin at 22050Hz Nyquist)
// Bass: 20-250Hz → bins 0-2, Mid: 250-4000Hz → bins 3-46, Treble: 4000-16000Hz → bins 47-127
const BASS_END = 3
const MID_END = 46

function ensureContext() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window['webkitAudioContext'])()
    analyser = audioCtx.createAnalyser()
    analyser.fftSize = FFT_SIZE
    analyser.smoothingTimeConstant = 0.8
    freqData = new Uint8Array(analyser.frequencyBinCount)
  }
  // Resume if suspended (autoplay policy)
  if (audioCtx.state === 'suspended') {
    audioCtx.resume()
  }
}

function disconnectSource() {
  if (source) {
    try { source.disconnect() } catch (_) { /* ignore */ }
    source = null
  }
  if (micStream) {
    micStream.getTracks().forEach(t => t.stop())
    micStream = null
  }
}

/**
 * Connect to microphone input.
 * Returns true on success, false if permission denied or unavailable.
 */
export async function connectMicrophone() {
  ensureContext()
  disconnectSource()

  try {
    micStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false })
    source = audioCtx.createMediaStreamSource(micStream)
    source.connect(analyser)
    _mode = 'mic'
    return true
  } catch (err) {
    console.warn('[audioAnalyzer] Mic access denied:', err.message)
    _mode = 'off'
    return false
  }
}

/**
 * Connect to an HTMLMediaElement (audio/video tag).
 * YouTube iframes cannot be connected (cross-origin), so this is for future use
 * with direct audio elements.
 */
export function connectElement(mediaEl) {
  if (!mediaEl) return false
  ensureContext()
  disconnectSource()

  try {
    source = audioCtx.createMediaElementSource(mediaEl)
    source.connect(analyser)
    analyser.connect(audioCtx.destination) // pass-through so audio still plays
    _mode = 'element'
    return true
  } catch (err) {
    console.warn('[audioAnalyzer] Element connect failed:', err.message)
    _mode = 'off'
    return false
  }
}

/**
 * Disconnect all sources and stop analysis.
 */
export function disconnect() {
  disconnectSource()
  _mode = 'off'
}

/**
 * Get current analysis mode.
 */
export function getMode() {
  return _mode
}

/**
 * Read current frequency data and return normalized bands + beat.
 * Call this every frame (inside useFrame or rAF).
 * Returns { bass, mid, treble, energy, beat } all 0-1 except beat (boolean).
 */
export function getFrequencyData() {
  if (_mode === 'off' || !analyser || !freqData) {
    return { bass: 0, mid: 0, treble: 0, energy: 0, beat: false }
  }

  analyser.getByteFrequencyData(freqData)
  const bins = freqData.length

  let bassSum = 0
  let midSum = 0
  let trebleSum = 0

  for (let i = 0; i < bins; i++) {
    const v = freqData[i] / 255
    if (i < BASS_END) bassSum += v
    else if (i < MID_END) midSum += v
    else trebleSum += v
  }

  const bass = Math.min(1, bassSum / BASS_END)
  const mid = Math.min(1, midSum / (MID_END - BASS_END))
  const treble = Math.min(1, trebleSum / (bins - MID_END))
  const energy = bass * 0.5 + mid * 0.3 + treble * 0.2

  // Simple beat detection: bass spike above threshold with cooldown
  const now = performance.now()
  let beat = false
  if (bass > BEAT_THRESHOLD && now - lastBeatTime > BEAT_COOLDOWN_MS) {
    beat = true
    lastBeatTime = now
  }

  return { bass, mid, treble, energy, beat }
}

/**
 * Check if Web Audio API is available.
 */
export function isSupported() {
  return !!(window.AudioContext || window['webkitAudioContext'])
}
