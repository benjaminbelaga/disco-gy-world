#!/usr/bin/env node
/**
 * Prepare genre data from Ishkur dataset + our taxonomy
 * Generates positioned genre data for the 3D world
 */

import { readFileSync, writeFileSync } from 'fs'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const ROOT = join(__dirname, '..', '..', '..')

// Load Ishkur data
const genresCSV = readFileSync(join(ROOT, 'data/ishkur-dataset/v3_genres.csv'), 'utf-8')
const linksCSV = readFileSync(join(ROOT, 'data/ishkur-dataset/v3_links.csv'), 'utf-8')
const tracksCSV = readFileSync(join(ROOT, 'data/ishkur-dataset/v3_tracks.csv'), 'utf-8')
const guideMD = readFileSync(join(ROOT, 'data/ishkur-dataset/v3_guide.md'), 'utf-8')

// Parse genre descriptions from v3_guide.md
function parseDescriptions(md) {
  const descriptions = {}
  // Split on ## headings (subgenres)
  const sections = md.split(/^## /m).slice(1)
  for (const section of sections) {
    const lines = section.split('\n')
    const name = lines[0].trim()
    // Skip the *aka:...* line and blank lines, collect paragraph text
    const paragraphs = []
    let pastMeta = false
    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim()
      // Skip aka line
      if (line.startsWith('*aka:')) { pastMeta = true; continue }
      if (!pastMeta) continue
      // Stop at tab-indented lines (track references) or empty sections
      if (line.startsWith('\t') || line.startsWith('(') && line.endsWith(')')) continue
      if (line === '') { if (paragraphs.length > 0) break; continue }
      paragraphs.push(line)
    }
    if (paragraphs.length > 0) {
      descriptions[name] = paragraphs.join(' ')
    }
  }
  return descriptions
}

const genreDescriptions = parseDescriptions(guideMD)
console.log(`Parsed ${Object.keys(genreDescriptions).length} genre descriptions from guide`)

// Load our taxonomy
const taxonomy = JSON.parse(readFileSync(join(ROOT, 'docs/electronic-music-taxonomy.json'), 'utf-8'))

// Parse CSV
function parseCSV(csv) {
  const lines = csv.trim().split('\n')
  const headers = lines[0].split(',')
  return lines.slice(1).map(line => {
    // Handle quoted fields with commas
    const values = []
    let current = ''
    let inQuotes = false
    for (const char of line) {
      if (char === '"') { inQuotes = !inQuotes; continue }
      if (char === ',' && !inQuotes) { values.push(current); current = ''; continue }
      current += char
    }
    values.push(current)
    return Object.fromEntries(headers.map((h, i) => [h, values[i] || '']))
  })
}

const genres = parseCSV(genresCSV)
const links = parseCSV(linksCSV)
const tracks = parseCSV(tracksCSV)

console.log(`Loaded: ${genres.length} genres, ${links.length} links, ${tracks.length} tracks`)

// Scene-to-biome mapping (from our world design doc)
const sceneBiomes = {
  'Techno': { color: '#00d4ff', biome: 'techno-massif', baseAngle: 0 },
  'House': { color: '#ff8c00', biome: 'house-plains', baseAngle: 40 },
  'Ambient': { color: '#0066cc', biome: 'ambient-depths', baseAngle: 80 },
  'Trance': { color: '#9933ff', biome: 'trance-highlands', baseAngle: 110 },
  'Eurotrance': { color: '#cc66ff', biome: 'trance-highlands', baseAngle: 120 },
  'Psy Trance': { color: '#00ff88', biome: 'trance-highlands', baseAngle: 130 },
  'Drum n Bass': { color: '#33cc33', biome: 'jungle-canopy', baseAngle: 150 },
  'Breakbeat': { color: '#66ff66', biome: 'jungle-canopy', baseAngle: 165 },
  'Hardcore': { color: '#ff0000', biome: 'industrial-wasteland', baseAngle: 185 },
  'Hard Dance': { color: '#ff3333', biome: 'industrial-wasteland', baseAngle: 195 },
  'Industrial/Goth': { color: '#8b0000', biome: 'industrial-wasteland', baseAngle: 210 },
  'Downtempo': { color: '#4a90d9', biome: 'ambient-depths', baseAngle: 90 },
  'Chill Out': { color: '#66b3ff', biome: 'ambient-depths', baseAngle: 95 },
  'Intelligent Dance Music': { color: '#ffffff', biome: 'idm-crystalline', baseAngle: 230 },
  'Electro': { color: '#00cccc', biome: 'techno-massif', baseAngle: 15 },
  'Eurodisco': { color: '#ff66b3', biome: 'disco-riviera', baseAngle: 250 },
  'Europop': { color: '#ff99cc', biome: 'disco-riviera', baseAngle: 265 },
  'Eurotrash': { color: '#ff44aa', biome: 'disco-riviera', baseAngle: 275 },
  'UK Garage': { color: '#cc9900', biome: 'garage-district', baseAngle: 290 },
  'Bass': { color: '#6600cc', biome: 'dubstep-rift', baseAngle: 305 },
  'Garage/Deep House': { color: '#ff9933', biome: 'house-plains', baseAngle: 50 },
  'Tech House': { color: '#00aaff', biome: 'house-plains', baseAngle: 25 },
  'Progressive': { color: '#9966ff', biome: 'trance-highlands', baseAngle: 140 },
  'Hip Hop': { color: '#ffcc00', biome: 'urban-quarter', baseAngle: 320 },
  'Urban': { color: '#ffaa00', biome: 'urban-quarter', baseAngle: 330 },
  'Pioneers': { color: '#aaaaaa', biome: 'source-monuments', baseAngle: 345 },
  'Chiptune': { color: '#00ff00', biome: 'idm-crystalline', baseAngle: 240 },
}

// Parse emerged period to approximate year
function emergedToYear(emerged) {
  const decades = { '50s': 1955, '60s': 1965, '70s': 1975, '80s': 1985, '90s': 1995, '00s': 2005, '10s': 2015 }
  const modifiers = { 'early': -3, 'mid': 0, 'late': 3 }
  if (!emerged) return 1990
  const parts = emerged.toLowerCase().split(' ')
  let year = 1990
  for (const p of parts) {
    if (decades[p]) year = decades[p]
    if (modifiers[p] !== undefined) year += modifiers[p]
  }
  return year
}

// Position genres in a spiral layout: angle = scene, radius = era
// Inner ring = older genres (1960s), outer ring = newer (2020s)
const MIN_RADIUS = 8
const MAX_RADIUS = 55
const MIN_YEAR = 1960
const MAX_YEAR = 2026

// Seed random for reproducibility
let seed = 42
function seededRandom() {
  seed = (seed * 16807) % 2147483647
  return (seed - 1) / 2147483646
}

const genreData = genres.map((g, i) => {
  const scene = sceneBiomes[g.scene] || { color: '#888888', biome: 'unknown', baseAngle: (i * 13) % 360 }
  const sceneGenres = genres.filter(sg => sg.scene === g.scene)
  const indexInScene = sceneGenres.indexOf(g)
  const year = emergedToYear(g.emerged)

  // Radius based on year (older = inner, newer = outer)
  const yearNorm = Math.max(0, Math.min(1, (year - MIN_YEAR) / (MAX_YEAR - MIN_YEAR)))
  const baseRadius = MIN_RADIUS + yearNorm * (MAX_RADIUS - MIN_RADIUS)
  const radiusJitter = (seededRandom() - 0.5) * 8
  const radius = Math.max(MIN_RADIUS, baseRadius + radiusJitter)

  // Angle based on scene + offset within scene
  const sceneSpread = 25 // degrees per scene cluster
  const genreSpread = sceneSpread / Math.max(sceneGenres.length, 1)
  const baseAngle = scene.baseAngle - sceneSpread / 2 + indexInScene * genreSpread
  const angleJitter = (seededRandom() - 0.5) * 5
  const angle = (baseAngle + angleJitter) * (Math.PI / 180)

  // Get description, truncate to ~200 chars at word boundary
  let description = genreDescriptions[g.genre] || ''
  if (description.length > 200) {
    description = description.slice(0, 200).replace(/\s+\S*$/, '') + '...'
  }

  return {
    slug: g.slug,
    name: g.genre,
    scene: g.scene,
    biome: scene.biome,
    color: scene.color,
    emerged: g.emerged,
    year,
    aka: g.aka,
    description,
    // Position: spiral layout
    x: Math.cos(angle) * radius,
    z: Math.sin(angle) * radius,
    y: 0, // Flat plane — height will be used for buildings later
  }
})

// Count tracks per genre for sizing
const trackCounts = {}
tracks.forEach(t => {
  trackCounts[t.slug] = (trackCounts[t.slug] || 0) + 1
})
genreData.forEach(g => {
  g.trackCount = trackCounts[g.slug] || 0
  g.size = Math.max(0.5, Math.log2(g.trackCount + 1) * 0.8)
})

// Parse links for genre connections
const genreLinks = links
  .filter(l => l.source !== l.target) // Remove self-links
  .map(l => ({
    source: l.source,
    target: l.target,
    startYear: parseInt(l.start) || 1980,
    endYear: parseInt(l.end) || 2020,
  }))

// Sample tracks (take up to 5 per genre for the prototype)
const sampleTracks = {}
tracks.forEach(t => {
  if (!sampleTracks[t.slug]) sampleTracks[t.slug] = []
  if (sampleTracks[t.slug].length < 5) {
    sampleTracks[t.slug].push({
      artist: t.artist,
      title: t.title,
      year: parseInt(t.year) || 2000,
      genre: t.genre,
      scene: t.scene,
    })
  }
})

// Output
const output = {
  meta: {
    version: '0.1.0',
    generatedAt: new Date().toISOString(),
    genreCount: genreData.length,
    linkCount: genreLinks.length,
    trackCount: tracks.length,
  },
  genres: genreData,
  links: genreLinks,
  tracks: sampleTracks,
  biomes: Object.entries(sceneBiomes).map(([scene, data]) => ({
    scene,
    ...data,
  })),
}

const outPath = join(__dirname, '..', 'public', 'data', 'world.json')
writeFileSync(outPath, JSON.stringify(output, null, 2))
console.log(`Written to ${outPath}`)
console.log(`Genres: ${genreData.length}, Links: ${genreLinks.length}, Sample tracks: ${Object.keys(sampleTracks).length} genres`)
