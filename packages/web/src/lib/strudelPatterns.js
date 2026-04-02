/**
 * Strudel Pattern Generator — maps DiscoWorld genres to live-coded music patterns.
 *
 * Each biome/scene has characteristic BPM, scales, sounds, and rhythmic patterns.
 * Patterns use Strudel mini-notation (TidalCycles for the browser).
 */

// BPM ranges by scene
const SCENE_BPM = {
  'Techno': [128, 140],
  'Tech House': [124, 130],
  'House': [118, 128],
  'Garage/Deep House': [118, 126],
  'Drum n Bass': [170, 180],
  'Jungle': [160, 175],
  'Breakbeat': [125, 140],
  'Ambient': [70, 100],
  'Chill Out': [80, 110],
  'Downtempo': [85, 110],
  'Trance': [135, 145],
  'Eurotrance': [138, 148],
  'Psy Trance': [140, 150],
  'Progressive': [126, 134],
  'Hard Dance': [145, 160],
  'Hardcore': [160, 200],
  'Industrial/Goth': [120, 140],
  'Electro': [120, 135],
  'Bass': [135, 150],
  'UK Garage': [130, 140],
  'Hip Hop': [85, 100],
  'Urban': [90, 110],
  'Europop': [120, 130],
  'Eurodisco': [118, 128],
  'Eurotrash': [125, 140],
  'Intelligent Dance Music': [100, 140],
  'Acid': [130, 140],
  'Chiptune': [130, 160],
  'Pioneers': [115, 130],
}

// Scale choices by biome mood
const BIOME_SCALES = {
  'techno-massif': ['C3:minor', 'D3:minor', 'A2:minor', 'E3:phrygian'],
  'house-plains': ['C3:dorian', 'F3:mixolydian', 'G3:major', 'Bb3:major'],
  'disco-riviera': ['C4:major', 'F3:major', 'G3:mixolydian', 'A3:dorian'],
  'ambient-depths': ['C3:lydian', 'E3:lydian', 'A3:minor', 'D3:dorian'],
  'jungle-canopy': ['C3:minor', 'G2:minor', 'Bb2:dorian', 'D3:phrygian'],
  'trance-highlands': ['A3:minor', 'D3:minor', 'E3:minor', 'C3:major'],
  'industrial-wasteland': ['C2:phrygian', 'D2:locrian', 'A2:minor', 'E2:phrygian'],
  'idm-crystalline': ['C3:lydian', 'E3:whole tone', 'Ab3:lydian', 'D3:dorian'],
  'dubstep-rift': ['C2:minor', 'F2:minor', 'G2:phrygian', 'D2:minor'],
  'garage-district': ['C3:dorian', 'G3:minor', 'F3:mixolydian', 'A3:dorian'],
  'urban-quarter': ['C3:dorian', 'G3:minor', 'F3:mixolydian', 'D3:minor'],
  'source-monuments': ['C3:major', 'G3:mixolydian', 'D3:dorian', 'A3:minor'],
  'unknown': ['C3:minor', 'A3:minor'],
}

// Sound palettes by biome
const BIOME_SOUNDS = {
  'techno-massif': {
    kick: 'bd:3', snare: 'cp', hat: 'hh:2', bass: 'sawtooth',
    pad: 'gm_synth_strings_1', lead: 'gm_lead_1_square',
  },
  'house-plains': {
    kick: 'bd:1', snare: 'cp:1', hat: 'hh:0', bass: 'triangle',
    pad: 'gm_warm_pad', lead: 'gm_lead_6_voice',
  },
  'disco-riviera': {
    kick: 'bd:0', snare: 'sd:3', hat: 'hh:4', bass: 'square',
    pad: 'gm_string_ensemble_1', lead: 'gm_synth_brass_1',
  },
  'ambient-depths': {
    kick: 'bd:5', snare: '~', hat: '~', bass: 'sine',
    pad: 'gm_pad_2_warm', lead: 'gm_pad_4_choir',
  },
  'jungle-canopy': {
    kick: 'bd:2', snare: 'sd:1', hat: 'hh:3', bass: 'sawtooth',
    pad: 'gm_synth_strings_2', lead: 'gm_lead_5_charang',
  },
  'trance-highlands': {
    kick: 'bd:4', snare: 'cp:2', hat: 'hh:1', bass: 'supersaw',
    pad: 'gm_pad_3_polysynth', lead: 'gm_lead_1_square',
  },
  'industrial-wasteland': {
    kick: 'bd:6', snare: 'metal:3', hat: 'noise:1', bass: 'sawtooth',
    pad: 'gm_pad_8_sweep', lead: 'gm_lead_8_bass_lead',
  },
  'idm-crystalline': {
    kick: 'bd:7', snare: 'cp:4', hat: 'hh:6', bass: 'sine',
    pad: 'gm_pad_1_new_age', lead: 'gm_celesta',
  },
  'dubstep-rift': {
    kick: 'bd:3', snare: 'sd:2', hat: 'hh:5', bass: 'sawtooth',
    pad: 'gm_pad_7_halo', lead: 'gm_lead_3_calliope',
  },
  'garage-district': {
    kick: 'bd:1', snare: 'sd:4', hat: 'hh:2', bass: 'triangle',
    pad: 'gm_electric_piano_1', lead: 'gm_lead_6_voice',
  },
  'urban-quarter': {
    kick: 'bd:0', snare: 'sd:1', hat: 'hh:0', bass: 'triangle',
    pad: 'gm_electric_piano_2', lead: 'gm_vibraphone',
  },
  'source-monuments': {
    kick: 'bd:2', snare: 'cp:1', hat: 'hh:1', bass: 'square',
    pad: 'gm_pad_2_warm', lead: 'gm_lead_2_sawtooth',
  },
  'unknown': {
    kick: 'bd:0', snare: 'cp', hat: 'hh', bass: 'sine',
    pad: 'gm_pad_1_new_age', lead: 'gm_lead_1_square',
  },
}

// Rhythmic templates by scene category
const RHYTHM_TEMPLATES = {
  fourOnFloor: {
    kick: '[bd, ~ ~ ~ ~]',
    hat:  '[~ hh]*4',
    snare: '[~ cp ~ ~]',
  },
  breakbeat: {
    kick: '[bd ~ ~ bd ~ ~ bd ~]',
    hat:  '[hh hh hh hh hh hh hh hh]',
    snare: '[~ ~ sd ~ ~ sd ~ ~]',
  },
  halftime: {
    kick: '[bd ~ ~ ~ ~ ~ ~ ~]',
    hat:  '[~ hh]*4',
    snare: '[~ ~ ~ ~ sd ~ ~ ~]',
  },
  dnb: {
    kick: '[bd ~ ~ ~ ~ ~ bd ~]',
    hat:  '[hh hh]*4',
    snare: '[~ ~ sd ~ ~ ~ ~ sd]',
  },
  ambient: {
    kick: '[bd ~ ~ ~ ~ ~ ~ ~]',
    hat:  '[~ ~ ~ ~ ~ ~ ~ ~]',
    snare: '[~ ~ ~ ~ ~ ~ ~ ~]',
  },
  industrial: {
    kick: '[bd bd ~ bd bd ~ bd ~]',
    hat:  '[hh ~ hh ~ hh ~ hh hh]',
    snare: '[~ ~ metal ~ ~ metal ~ ~]',
  },
}

function getSceneRhythm(scene) {
  if (['Techno', 'Tech House', 'House', 'Garage/Deep House', 'Trance', 'Eurotrance',
       'Psy Trance', 'Progressive', 'Eurodisco', 'Europop', 'Hard Dance'].includes(scene)) {
    return 'fourOnFloor'
  }
  if (['Breakbeat', 'Electro', 'UK Garage', 'Eurotrash'].includes(scene)) return 'breakbeat'
  if (['Drum n Bass'].includes(scene)) return 'dnb'
  if (['Hip Hop', 'Urban', 'Downtempo'].includes(scene)) return 'halftime'
  if (['Ambient', 'Chill Out', 'Intelligent Dance Music'].includes(scene)) return 'ambient'
  if (['Industrial/Goth', 'Hardcore'].includes(scene)) return 'industrial'
  return 'fourOnFloor'
}

function pick(arr) {
  return arr[Math.floor(Math.random() * arr.length)]
}

function randBpm(scene) {
  const range = SCENE_BPM[scene] || [120, 130]
  return range[0] + Math.floor(Math.random() * (range[1] - range[0]))
}

/**
 * Generate a Strudel pattern string for a given genre.
 */
export function generatePattern(genre) {
  const { scene = 'House', biome = 'house-plains', name = 'Unknown' } = genre
  const bpm = randBpm(scene)
  const scale = pick(BIOME_SCALES[biome] || BIOME_SCALES['unknown'])
  const sounds = BIOME_SOUNDS[biome] || BIOME_SOUNDS['unknown']
  const rhythmKey = getSceneRhythm(scene)
  const rhythm = RHYTHM_TEMPLATES[rhythmKey]

  // Build the pattern layers
  const lines = []
  lines.push(`// ${name} — ${scene} @ ${bpm} BPM`)
  lines.push(`setcps(${(bpm / 60 / 4).toFixed(4)})`)
  lines.push('')

  // Drums
  if (rhythmKey !== 'ambient') {
    const kickPattern = rhythm.kick.replace('bd', sounds.kick).replace('hh', sounds.hat)
    const snarePattern = rhythm.snare.replace('cp', sounds.snare).replace('sd', sounds.snare).replace('metal', sounds.snare)
    const hatPattern = rhythm.hat.replace('hh', sounds.hat)
    lines.push(`// drums`)
    lines.push(`stack(`)
    lines.push(`  s("${kickPattern}").gain(0.9),`)
    lines.push(`  s("${hatPattern}").gain(0.5),`)
    lines.push(`  s("${snarePattern}").gain(0.7),`)
  } else {
    lines.push(`stack(`)
    lines.push(`  s("${sounds.kick} ~ ~ ~ ~ ~ ~ ~").gain(0.4),`)
  }

  // Bass line — genre-appropriate
  lines.push('')
  lines.push(`  // bass`)
  if (rhythmKey === 'dnb') {
    lines.push(`  note("<0 [3 ~] 5 [7 5]>").scale("${scale}")`)
    lines.push(`    .s("${sounds.bass}").gain(0.8).lpf(400),`)
  } else if (rhythmKey === 'ambient') {
    lines.push(`  note("<0 ~ 3 ~>/2").scale("${scale}")`)
    lines.push(`    .s("${sounds.bass}").gain(0.5).lpf(200).room(0.8),`)
  } else if (rhythmKey === 'halftime') {
    lines.push(`  note("<0 ~ [3 5] ~>").scale("${scale}")`)
    lines.push(`    .s("${sounds.bass}").gain(0.8).lpf(500),`)
  } else {
    lines.push(`  note("<0 0 3 5>").scale("${scale}")`)
    lines.push(`    .s("${sounds.bass}").gain(0.8).lpf(600),`)
  }

  // Pad / atmosphere
  lines.push('')
  lines.push(`  // pad`)
  if (rhythmKey === 'ambient') {
    lines.push(`  note("<[0,2,4] [1,3,5]>/4").scale("${scale}")`)
    lines.push(`    .s("${sounds.pad}").gain(0.35).room(1).lpf(2000).slow(2),`)
  } else {
    lines.push(`  note("<[0,2,4] [1,3,5] [0,3,5] [2,4,6]>/2").scale("${scale}")`)
    lines.push(`    .s("${sounds.pad}").gain(0.25).room(0.5).lpf(3000),`)
  }

  // Lead melody — varies by genre complexity
  lines.push('')
  lines.push(`  // lead`)
  if (['Trance', 'Eurotrance', 'Psy Trance', 'Progressive'].includes(scene)) {
    lines.push(`  note("<0 2 4 7 4 2 0 ~>*2").scale("${scale}")`)
    lines.push(`    .s("${sounds.lead}").gain(0.3).lpf(sine.range(800,4000).slow(8))`)
  } else if (['Ambient', 'Chill Out', 'Intelligent Dance Music'].includes(scene)) {
    lines.push(`  note("<0 ~ 4 ~ 7 ~ 4 ~>/2").scale("${scale}")`)
    lines.push(`    .s("${sounds.lead}").gain(0.2).room(1).delay(0.5).lpf(2000)`)
  } else if (['Drum n Bass', 'Breakbeat', 'UK Garage'].includes(scene)) {
    lines.push(`  note("<0 3 5 [7 ~] 5 3 0 ~>").scale("${scale}")`)
    lines.push(`    .s("${sounds.lead}").gain(0.3).lpf(perlin.range(800,6000).slow(4))`)
  } else {
    lines.push(`  note("<0 [2 ~] 4 [~ 5] 7 [5 ~] 4 [2 ~]>").scale("${scale}")`)
    lines.push(`    .s("${sounds.lead}").gain(0.3).lpf(perlin.range(600,5000).slow(6))`)
  }

  lines.push(`)`)

  return lines.join('\n')
}

/**
 * Quick pattern preview — shorter, less complex, for hover/tooltip.
 */
export function generateMiniPattern(genre) {
  const { scene = 'House', biome = 'house-plains' } = genre
  const bpm = randBpm(scene)
  const scale = pick(BIOME_SCALES[biome] || BIOME_SCALES['unknown'])
  const sounds = BIOME_SOUNDS[biome] || BIOME_SOUNDS['unknown']

  return `setcps(${(bpm / 60 / 4).toFixed(4)})
note("<0 2 4 7>*2").scale("${scale}")
.s("${sounds.lead}").gain(0.4).room(0.3)
.lpf(sine.range(600,3000).slow(4))`
}

export { SCENE_BPM, BIOME_SCALES, BIOME_SOUNDS }
