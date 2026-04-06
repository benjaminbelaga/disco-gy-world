/**
 * Discogs public API client — no OAuth needed for public collections.
 *
 * Fetches collection + wantlist, computes taste profile client-side,
 * caches everything in localStorage.
 */

const DISCOGS_API = 'https://api.discogs.com'
const USER_AGENT = 'DiscoWorld/1.0 +https://github.com/discoworld/discoworld'
const CACHE_KEY = 'discoworld-discogs-cache'
const CACHE_TTL = 3600 * 1000 // 1 hour

// Rate limiter: Discogs allows 25 req/min for unauthenticated
let lastRequestTime = 0
const MIN_INTERVAL = 2500 // ~24 req/min with margin

async function rateLimitedFetch(url) {
  const now = Date.now()
  const wait = Math.max(0, MIN_INTERVAL - (now - lastRequestTime))
  if (wait > 0) await new Promise(r => setTimeout(r, wait))
  lastRequestTime = Date.now()

  const res = await fetch(url, {
    headers: {
      'User-Agent': USER_AGENT,
    },
  })

  if (res.status === 404) throw new Error('USER_NOT_FOUND')
  if (res.status === 403) throw new Error('COLLECTION_PRIVATE')
  if (res.status === 429) {
    // Rate limited — wait and retry once
    await new Promise(r => setTimeout(r, 5000))
    return fetch(url, { headers: { 'User-Agent': USER_AGENT } })
  }
  if (!res.ok) throw new Error(`Discogs API error: ${res.status}`)
  return res
}

/**
 * Fetch all pages of a user's collection with progress callback.
 * @param {string} username
 * @param {(loaded: number, total: number) => void} onProgress
 * @returns {Promise<Array>} releases
 */
export async function fetchCollection(username, onProgress) {
  const allReleases = []

  // First page to get total
  const firstUrl = `${DISCOGS_API}/users/${encodeURIComponent(username)}/collection/folders/0/releases?page=1&per_page=100&sort=added&sort_order=desc`
  const firstRes = await rateLimitedFetch(firstUrl)
  const firstData = await firstRes.json()

  const pagination = firstData.pagination || {}
  const totalPages = pagination.pages || 1
  const totalItems = pagination.items || 0
  const releases = firstData.releases || []
  allReleases.push(...releases)
  onProgress?.(allReleases.length, totalItems)

  for (let p = 2; p <= totalPages; p++) {
    const url = `${DISCOGS_API}/users/${encodeURIComponent(username)}/collection/folders/0/releases?page=${p}&per_page=100&sort=added&sort_order=desc`
    const res = await rateLimitedFetch(url)
    const data = await res.json()
    allReleases.push(...(data.releases || []))
    onProgress?.(allReleases.length, totalItems)
  }

  return allReleases
}

/**
 * Fetch all pages of a user's wantlist (may fail if private).
 */
export async function fetchWantlist(username, onProgress) {
  const allWants = []

  try {
    const firstUrl = `${DISCOGS_API}/users/${encodeURIComponent(username)}/wants?page=1&per_page=100`
    const firstRes = await rateLimitedFetch(firstUrl)
    const firstData = await firstRes.json()

    const pagination = firstData.pagination || {}
    const totalPages = pagination.pages || 1
    const totalItems = pagination.items || 0
    allWants.push(...(firstData.wants || []))
    onProgress?.(allWants.length, totalItems)

    for (let p = 2; p <= totalPages; p++) {
      const url = `${DISCOGS_API}/users/${encodeURIComponent(username)}/wants?page=${p}&per_page=100`
      const res = await rateLimitedFetch(url)
      const data = await res.json()
      allWants.push(...(data.wants || []))
      onProgress?.(allWants.length, totalItems)
    }
  } catch {
    // Wantlist may be private — not fatal
  }

  return allWants
}

/**
 * Parse a Discogs release into a normalized object.
 */
function parseRelease(rel, source = 'collection') {
  const basic = rel.basic_information || {}
  return {
    id: rel.id || basic.id,
    title: basic.title || 'Unknown',
    artists: (basic.artists || []).map(a => a.name).join(', ') || 'Unknown',
    year: basic.year || 0,
    genres: basic.genres || [],
    styles: basic.styles || [],
    labels: (basic.labels || []).map(l => l.name),
    formats: (basic.formats || []).map(f => f.name),
    thumb: basic.thumb || '',
    cover: basic.cover_image || '',
    rating: rel.rating || 0,
    dateAdded: rel.date_added || '',
    // Discogs community stats for rarity
    haveCount: basic.community?.have || 0,
    wantCount: basic.community?.want || 0,
    source,
  }
}

/**
 * Compute Shannon entropy (normalized 0-10).
 */
function shannonDiversity(counts) {
  const total = Object.values(counts).reduce((a, b) => a + b, 0)
  if (total === 0) return 0
  const n = Object.keys(counts).length
  if (n <= 1) return 0

  let entropy = 0
  for (const count of Object.values(counts)) {
    if (count > 0) {
      const p = count / total
      entropy -= p * Math.log2(p)
    }
  }
  const maxEntropy = Math.log2(n)
  return maxEntropy > 0 ? Math.round((entropy / maxEntropy) * 100) / 10 : 0
}

/**
 * Compute a full taste profile from parsed releases.
 */
export function computeTasteProfile(username, releases, wantlistReleases = []) {
  const genreCounts = {}
  const styleCounts = {}
  const labelCounts = {}
  const yearCounts = {}
  const decadeCounts = {}
  let totalHave = 0
  let totalWant = 0
  let rareCount = 0

  for (const rel of releases) {
    // Genres
    for (const g of rel.genres) {
      genreCounts[g] = (genreCounts[g] || 0) + 1
    }
    // Styles (more specific)
    for (const s of rel.styles) {
      styleCounts[s] = (styleCounts[s] || 0) + 1
    }
    // Labels
    for (const l of rel.labels) {
      labelCounts[l] = (labelCounts[l] || 0) + 1
    }
    // Years
    if (rel.year > 0) {
      yearCounts[rel.year] = (yearCounts[rel.year] || 0) + 1
      const decade = `${Math.floor(rel.year / 10) * 10}s`
      decadeCounts[decade] = (decadeCounts[decade] || 0) + 1
    }
    // Rarity: if want/have ratio > 1.5, it's rare
    totalHave += rel.haveCount
    totalWant += rel.wantCount
    if (rel.haveCount > 0 && rel.wantCount / rel.haveCount > 1.5) {
      rareCount++
    }
  }

  const totalReleases = releases.length

  // Sort genres by count, compute percentages
  const sortedGenres = Object.entries(genreCounts)
    .sort((a, b) => b[1] - a[1])
    .map(([name, count]) => ({
      name,
      count,
      pct: Math.round((count / totalReleases) * 1000) / 10,
    }))

  // Sort styles by count (top 15)
  const sortedStyles = Object.entries(styleCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 15)
    .map(([name, count]) => ({
      name,
      count,
      pct: Math.round((count / totalReleases) * 1000) / 10,
    }))

  // Sort decades
  const sortedDecades = Object.entries(decadeCounts)
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([decade, count]) => ({
      decade,
      count,
      pct: Math.round((count / totalReleases) * 1000) / 10,
    }))

  // Top labels
  const topLabels = Object.entries(labelCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([name, count]) => ({ name, count }))

  // Diversity score (Shannon entropy on styles — more granular than genres)
  const diversityScore = shannonDiversity(styleCounts)

  // Rarity score (percentage of rare releases)
  const rarityScore = totalReleases > 0 ? Math.round((rareCount / totalReleases) * 100) : 0

  // Gap analysis: find genres adjacent to owned styles but not in collection
  const ownedGenres = new Set(Object.keys(genreCounts))
  const ownedStyles = new Set(Object.keys(styleCounts))
  const gaps = computeGaps(ownedGenres, ownedStyles, sortedGenres, sortedStyles)

  return {
    username,
    total_releases: totalReleases,
    wantlist_count: wantlistReleases.length,
    diversity_score: diversityScore,
    rarity_score: rarityScore,
    genres: sortedGenres,
    styles: sortedStyles,
    decades: sortedDecades,
    top_labels: topLabels,
    gaps,
    // Raw data for map overlay
    genreCounts,
    styleCounts,
    yearCounts,
  }
}

/**
 * Genre adjacency map for gap analysis.
 * Maps genre -> related genres that a collector might explore next.
 */
const GENRE_ADJACENCY = {
  'Electronic': ['Ambient', 'Experimental', 'Synth-pop'],
  'Techno': ['Acid', 'Electro', 'Industrial', 'EBM', 'Minimal'],
  'House': ['Deep House', 'Garage House', 'Disco', 'Boogie'],
  'Ambient': ['New Age', 'Downtempo', 'Drone', 'Field Recording'],
  'Electro': ['Breakbeat', 'Miami Bass', 'Hip Hop'],
  'IDM': ['Glitch', 'Microsound', 'Braindance'],
  'Dub': ['Dub Techno', 'Reggae', 'Dancehall'],
  'Drum n Bass': ['Jungle', 'Breakbeat', 'Hardcore'],
  'Trance': ['Psytrance', 'Goa Trance', 'Progressive Trance'],
  'Industrial': ['EBM', 'Noise', 'Power Electronics'],
  'Experimental': ['Musique Concrete', 'Sound Art', 'Noise'],
  'Disco': ['Italo-Disco', 'Boogie', 'Nu-Disco', 'Funk'],
  'Hip Hop': ['Trip Hop', 'Abstract', 'Instrumental'],
  'Jazz': ['Free Jazz', 'Spiritual Jazz', 'Nu Jazz', 'Fusion'],
  'Funk': ['Disco', 'Boogie', 'P-Funk', 'Electro'],
  'Minimal': ['Minimal Techno', 'Microhouse', 'Click House'],
  'Dubstep': ['Grime', 'UK Garage', 'Bass Music'],
}

function computeGaps(ownedGenres, ownedStyles, sortedGenres, sortedStyles) {
  const gaps = []
  const seen = new Set()

  // Check adjacency for top genres
  for (const { name, count } of sortedGenres.slice(0, 8)) {
    const adjacent = GENRE_ADJACENCY[name] || []
    for (const adj of adjacent) {
      if (!ownedGenres.has(adj) && !ownedStyles.has(adj) && !seen.has(adj)) {
        gaps.push({
          genre: adj,
          reason: `${count} ${name} releases, 0 ${adj} — natural bridge`,
        })
        seen.add(adj)
        if (gaps.length >= 5) return gaps
      }
    }
  }

  // Also check style-level gaps
  for (const { name, count } of sortedStyles.slice(0, 10)) {
    const adjacent = GENRE_ADJACENCY[name] || []
    for (const adj of adjacent) {
      if (!ownedGenres.has(adj) && !ownedStyles.has(adj) && !seen.has(adj)) {
        gaps.push({
          genre: adj,
          reason: `Strong ${name} base (${count}), ${adj} is the missing link`,
        })
        seen.add(adj)
        if (gaps.length >= 5) return gaps
      }
    }
  }

  return gaps
}

// ---------------------------------------------------------------------------
// Auth helpers — Discogs OAuth 1.0a + token fallback
// ---------------------------------------------------------------------------

const API_BASE = '/api'
const SESSION_KEY = 'discoworld-session-token'

/**
 * Initiate Discogs login. If OAuth is configured server-side, opens the
 * authorize URL. Otherwise falls back to personal token flow.
 *
 * @param {string} callbackUrl - Where Discogs redirects after authorization
 * @returns {Promise<{mode: string, authorize_url?: string, session_token?: string, user?: object}>}
 */
export async function initiateLogin(callbackUrl) {
  try {
    const url = `${API_BASE}/auth/discogs/login?callback_url=${encodeURIComponent(callbackUrl)}`
    const res = await fetch(url)
    if (!res.ok) return null
    const data = await res.json()

    if (data.mode === 'oauth' && data.authorize_url) {
      // OAuth mode — redirect user to Discogs authorization page
      window.location.href = data.authorize_url
      return data
    }

    // Token fallback — already authenticated
    if (data.session_token) {
      sessionStorage.setItem(SESSION_KEY, data.session_token)
    }
    return data
  } catch {
    // API unavailable — fail silently in static-only mode
    return null
  }
}

/**
 * Handle the OAuth callback. Called from the /auth/callback page after
 * Discogs redirects back with a session_token in the URL query.
 *
 * @param {URLSearchParams} params - URL search params from the callback
 * @returns {{session_token: string} | null}
 */
export function handleCallback(params) {
  const sessionToken = params.get('session_token')
  if (!sessionToken) return null
  sessionStorage.setItem(SESSION_KEY, sessionToken)
  return { session_token: sessionToken }
}

/**
 * Check if there is an active session and return user info.
 *
 * @returns {Promise<{authenticated: boolean, user: object|null}>}
 */
export async function checkSession() {
  const token = sessionStorage.getItem(SESSION_KEY)
  if (!token) return { authenticated: false, user: null }

  try {
    const res = await fetch(`${API_BASE}/auth/me?session_token=${encodeURIComponent(token)}`)
    if (!res.ok) return { authenticated: false, user: null }
    return res.json()
  } catch {
    // API unavailable — fail silently in static-only mode
    return { authenticated: false, user: null }
  }
}

/**
 * Get the stored session token (for authenticated API calls).
 * @returns {string|null}
 */
export function getSessionToken() {
  return sessionStorage.getItem(SESSION_KEY)
}

/**
 * Logout — clear session server-side and locally.
 */
export async function logout() {
  const token = sessionStorage.getItem(SESSION_KEY)
  if (token) {
    await fetch(`${API_BASE}/auth/logout?session_token=${encodeURIComponent(token)}`, {
      method: 'POST',
    }).catch(() => {})
  }
  sessionStorage.removeItem(SESSION_KEY)
}

// ---------------------------------------------------------------------------
// localStorage cache
// ---------------------------------------------------------------------------

function getCachedProfile(username) {
  try {
    const raw = localStorage.getItem(CACHE_KEY)
    if (!raw) return null
    const cache = JSON.parse(raw)
    if (cache.username !== username) return null
    if (Date.now() - cache.timestamp > CACHE_TTL) return null
    return cache.profile
  } catch {
    return null
  }
}

function setCachedProfile(username, profile) {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify({
      username,
      profile,
      timestamp: Date.now(),
    }))
  } catch {
    // localStorage full or unavailable
  }
}

export function clearCachedProfile() {
  try {
    localStorage.removeItem(CACHE_KEY)
  } catch {
    // ignore
  }
}

/**
 * Full import flow: fetch collection + wantlist, compute profile, cache.
 *
 * @param {string} username
 * @param {(phase: string, loaded: number, total: number) => void} onProgress
 * @param {object} options
 * @param {boolean} options.force - skip cache
 * @returns {Promise<{profile: object, releases: Array, wantlist: Array}>}
 */
export async function importCollection(username, onProgress, { force = false } = {}) {
  // Check cache first
  if (!force) {
    const cached = getCachedProfile(username)
    if (cached) {
      onProgress?.('cached', 0, 0)
      return { profile: cached, releases: [], wantlist: [], fromCache: true }
    }
  }

  // Fetch collection
  onProgress?.('collection', 0, 0)
  const rawReleases = await fetchCollection(username, (loaded, total) => {
    onProgress?.('collection', loaded, total)
  })

  // Parse releases
  const releases = rawReleases.map(r => parseRelease(r, 'collection'))

  // Fetch wantlist
  onProgress?.('wantlist', 0, 0)
  const rawWantlist = await fetchWantlist(username, (loaded, total) => {
    onProgress?.('wantlist', loaded, total)
  })
  const wantlist = rawWantlist.map(r => parseRelease(r, 'wantlist'))

  // Compute profile
  onProgress?.('analyzing', 0, 0)
  const profile = computeTasteProfile(username, releases, wantlist)

  // Cache
  setCachedProfile(username, profile)

  return { profile, releases, wantlist, fromCache: false }
}
