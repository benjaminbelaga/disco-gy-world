import taxonomyData from '../../../../docs/electronic-music-taxonomy.json'

/**
 * Build a search index mapping lowercase keywords to genre slugs (with weight).
 * Sources: world.json genres (name, aka, scene) + taxonomy.json (mood, sounds).
 * Extracted from VibeSearch.jsx for reuse in Onboarding.
 */
export function buildSearchIndex(genres) {
  const index = new Map()

  const add = (slug, keyword, weight) => {
    const k = keyword.toLowerCase().trim()
    if (!k || k.length < 2) return
    if (!index.has(k)) index.set(k, [])
    index.get(k).push({ slug, weight })
  }

  for (const genre of genres) {
    const { slug, name, aka, scene } = genre
    name.toLowerCase().split(/[\s/&,()-]+/).filter(Boolean).forEach(t => add(slug, t, 3))
    add(slug, name, 5)
    if (aka) {
      aka.split(',').forEach(a => {
        const trimmed = a.trim()
        add(slug, trimmed, 4)
        trimmed.toLowerCase().split(/[\s/&()-]+/).filter(Boolean).forEach(t => add(slug, t, 2))
      })
    }
    if (scene) {
      add(slug, scene, 2)
      scene.toLowerCase().split(/[\s/&()-]+/).filter(Boolean).forEach(t => add(slug, t, 1.5))
    }
  }

  const slugSet = new Set(genres.map(g => g.slug))

  const indexTaxonomy = (genreKey, data, parentSlug) => {
    const candidateSlugs = [
      genreKey,
      genreKey.replace(/_/g, ''),
      parentSlug
    ].filter(Boolean)

    let matchedSlug = null
    for (const s of candidateSlugs) {
      if (slugSet.has(s)) { matchedSlug = s; break }
    }
    if (!matchedSlug) {
      const normalized = genreKey.replace(/_/g, '')
      for (const s of slugSet) {
        if (s.includes(normalized) || normalized.includes(s.replace(/-/g, ''))) {
          matchedSlug = s
          break
        }
      }
    }

    if (matchedSlug) {
      if (data.mood) data.mood.forEach(m => add(matchedSlug, m, 3))
      if (data.sounds) data.sounds.forEach(s => {
        add(matchedSlug, s, 2)
        s.split(/[\s/]+/).filter(t => t.length > 2).forEach(t => add(matchedSlug, t, 1))
      })
      if (data.origin?.city) {
        data.origin.city.split('/').forEach(c => add(matchedSlug, c.trim(), 2.5))
      }
    }

    if (data.sub) {
      for (const [subKey, subData] of Object.entries(data.sub)) {
        indexTaxonomy(subKey, subData, matchedSlug)
      }
    }
  }

  for (const [key, data] of Object.entries(taxonomyData.genres)) {
    indexTaxonomy(key, data, null)
  }
  for (const [key, data] of Object.entries(taxonomyData.neighbor_genres || {})) {
    indexTaxonomy(key, data, null)
  }

  for (const [city, genreKeys] of Object.entries(taxonomyData.geography_matrix || {})) {
    for (const gk of genreKeys) {
      const normalized = gk.replace(/_/g, '')
      for (const s of slugSet) {
        if (s.includes(normalized) || normalized.includes(s.replace(/-/g, ''))) {
          add(s, city, 2)
          break
        }
      }
    }
  }

  const vibeAliases = {
    '3am': ['dark', 'hypnotic', 'deep', 'meditative'],
    'sunrise': ['uplifting', 'euphoric', 'melodic', 'warm'],
    'sunset': ['warm', 'mellow', 'soulful', 'deep'],
    'rave': ['energetic', 'intense', 'aggressive', 'euphoric'],
    'chill': ['mellow', 'peaceful', 'contemplative', 'warm'],
    'club': ['groovy', 'driving', 'functional', 'energetic'],
    'festival': ['euphoric', 'energetic', 'anthemic', 'festival'],
    'afterhours': ['dark', 'hypnotic', 'deep', 'minimal'],
    'underground': ['dark', 'raw', 'minimal', 'deep'],
    'dreamy': ['ethereal', 'contemplative', 'nostalgic', 'warm'],
    'heavy': ['aggressive', 'intense', 'dark', 'heavy'],
    'funky': ['groovy', 'funky', 'soulful', 'playful'],
    'melodic': ['melodic', 'emotional', 'uplifting', 'soulful'],
    'dark': ['dark', 'ominous', 'sinister', 'industrial'],
    'fast': ['intense', 'energetic', 'manic', 'aggressive'],
    'slow': ['mellow', 'contemplative', 'peaceful', 'downtempo'],
    'trippy': ['psychedelic', 'trippy', 'hypnotic', 'surreal'],
    'emotional': ['emotional', 'euphoric', 'melancholic', 'soulful'],
    'nocturnal': ['nocturnal', 'dark', 'deep', 'cinematic'],
    'morning': ['uplifting', 'gentle', 'warm', 'melodic'],
    'warehouse': ['industrial', 'raw', 'dark', 'aggressive'],
    'beach': ['warm', 'groovy', 'soulful', 'fun'],
    'detroit': ['detroit', 'soulful', 'cosmic', 'futurist'],
    'berlin': ['minimal', 'dark', 'hypnotic', 'deep'],
    'london': ['slick', 'bouncy', 'raw', 'energetic'],
  }

  for (const [alias, expandedKeywords] of Object.entries(vibeAliases)) {
    const slugScores = new Map()
    for (const ek of expandedKeywords) {
      const entries = index.get(ek) || []
      for (const { slug, weight } of entries) {
        slugScores.set(slug, (slugScores.get(slug) || 0) + weight)
      }
    }
    for (const [slug, score] of slugScores) {
      if (score >= 3) add(slug, alias, 1.5)
    }
  }

  return index
}

/**
 * Score genres against search query using keyword matching.
 */
export function searchGenres(query, index, genres, limit = 5) {
  if (!query || query.length < 2) return []

  const tokens = query.toLowerCase().split(/[\s,;.]+/).filter(t => t.length >= 2)
  if (tokens.length === 0) return []

  const slugScores = new Map()

  for (const token of tokens) {
    const exactMatches = index.get(token)
    if (exactMatches) {
      for (const { slug, weight } of exactMatches) {
        slugScores.set(slug, (slugScores.get(slug) || 0) + weight)
      }
    }

    for (const [keyword, entries] of index) {
      if (keyword === token) continue
      if (keyword.includes(token) || token.includes(keyword)) {
        const partialWeight = 0.5
        for (const { slug, weight } of entries) {
          slugScores.set(slug, (slugScores.get(slug) || 0) + weight * partialWeight)
        }
      }
    }
  }

  const results = []
  const genreMap = new Map(genres.map(g => [g.slug, g]))

  for (const [slug, score] of slugScores) {
    const genre = genreMap.get(slug)
    if (genre) {
      results.push({ genre, score })
    }
  }

  results.sort((a, b) => b.score - a.score)
  return results.slice(0, limit)
}
