/**
 * Drift Engine — serendipity-driven auto-navigation through the genre graph.
 *
 * Picks adjacent genres via the link graph, flies the camera smoothly,
 * and auto-plays sample tracks. The "adventurous" slider (0-100) controls
 * how far from the starting genre the drift is willing to wander.
 */

// BFS shortest-path distance from a source genre to all others
function buildDistanceMap(sourceSlug, genres, links) {
  const dist = {}
  const slugSet = new Set(genres.map(g => g.slug))
  slugSet.forEach(s => { dist[s] = Infinity })
  dist[sourceSlug] = 0

  const adj = {}
  genres.forEach(g => { adj[g.slug] = [] })
  links.forEach(l => {
    if (adj[l.source]) adj[l.source].push(l.target)
    if (adj[l.target]) adj[l.target].push(l.source)
  })

  const queue = [sourceSlug]
  while (queue.length) {
    const cur = queue.shift()
    const d = dist[cur]
    for (const nb of (adj[cur] || [])) {
      if (dist[nb] > d + 1) {
        dist[nb] = d + 1
        queue.push(nb)
      }
    }
  }
  return { dist, adj }
}

// Pick a track from genre's slug in the tracks dict
function pickTrack(slug, tracks) {
  const list = tracks[slug]
  if (!list || !list.length) return null
  return list[Math.floor(Math.random() * list.length)]
}

let _timer = null
let _stopped = false

/**
 * Start drifting through genres.
 *
 * @param {Object} opts
 * @param {Array}  opts.genres     - genre objects from world.json
 * @param {Array}  opts.links      - link objects from world.json
 * @param {Object} opts.tracks     - tracks dict keyed by slug
 * @param {number} opts.adventurousness - 0..100
 * @param {string|null} opts.startSlug  - slug to start from (null = random)
 * @param {Function} opts.onGenreChange - (genre) => void
 * @param {Function} opts.onTrackPlay   - (track) => void
 * @param {Function} opts.onFlyTo       - (genre) => void
 * @returns {Function} cleanup / stop function
 */
export function startDrift(opts) {
  const {
    genres,
    links,
    tracks,
    adventurousness = 50,
    startSlug = null,
    onGenreChange,
    onTrackPlay,
    onFlyTo,
  } = opts

  _stopped = false

  const startGenre = startSlug
    ? genres.find(g => g.slug === startSlug)
    : genres[Math.floor(Math.random() * genres.length)]

  if (!startGenre) return () => {}

  const originSlug = startGenre.slug
  const { dist, adj } = buildDistanceMap(originSlug, genres, links)
  const maxDist = Math.max(...Object.values(dist).filter(d => d < Infinity), 1)

  // Compute allowed distance based on adventurousness
  // 0 = same scene only (dist <= 2), 50 = moderate, 100 = anything
  function maxAllowedDist() {
    const a = adventurousness / 100
    return Math.max(1, Math.round(2 + a * (maxDist - 2)))
  }

  let currentSlug = startGenre.slug
  const visited = new Set([currentSlug])

  function pickNext() {
    const allowed = maxAllowedDist()
    const neighbors = adj[currentSlug] || []

    // Prefer unvisited neighbors within distance limit
    let candidates = neighbors.filter(s =>
      !visited.has(s) && dist[s] <= allowed
    )

    // Fallback: allow visited
    if (!candidates.length) {
      candidates = neighbors.filter(s => dist[s] <= allowed)
    }

    // High adventurousness: allow random jumps
    if (!candidates.length || (adventurousness > 80 && Math.random() < 0.3)) {
      candidates = genres
        .filter(g => g.slug !== currentSlug && dist[g.slug] <= allowed)
        .map(g => g.slug)
    }

    // Ultimate fallback
    if (!candidates.length) {
      candidates = genres.filter(g => g.slug !== currentSlug).map(g => g.slug)
    }

    return candidates[Math.floor(Math.random() * candidates.length)]
  }

  function step() {
    if (_stopped) return

    const nextSlug = pickNext()
    if (!nextSlug) return

    const nextGenre = genres.find(g => g.slug === nextSlug)
    if (!nextGenre) return

    currentSlug = nextSlug
    visited.add(nextSlug)

    // Notify: fly camera
    onFlyTo(nextGenre)
    onGenreChange(nextGenre)

    // After camera travel (2.5s), play a track
    _timer = setTimeout(() => {
      if (_stopped) return
      const track = pickTrack(nextSlug, tracks)
      if (track) {
        onTrackPlay(track)
      }

      // After preview (8-15s depending on adventurousness), move on
      const previewDuration = 8000 + Math.random() * 7000
      _timer = setTimeout(() => {
        if (!_stopped) step()
      }, previewDuration)
    }, 2500)
  }

  // Start with current genre
  onGenreChange(startGenre)
  onFlyTo(startGenre)
  const track = pickTrack(startGenre.slug, tracks)
  if (track) {
    setTimeout(() => {
      if (!_stopped) onTrackPlay(track)
    }, 1500)
  }

  // First move after initial preview
  _timer = setTimeout(() => {
    if (!_stopped) step()
  }, 10000)

  return stopDrift
}

export function stopDrift() {
  _stopped = true
  if (_timer) {
    clearTimeout(_timer)
    _timer = null
  }
}
