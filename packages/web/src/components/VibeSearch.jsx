import { useState, useEffect, useRef, useMemo, useCallback } from 'react'
import useStore from '../stores/useStore'
import { buildSearchIndex, searchGenres } from '../utils/vibeSearch'

export default function VibeSearch() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [isOpen, setIsOpen] = useState(false)
  const [selectedIdx, setSelectedIdx] = useState(0)
  const inputRef = useRef(null)
  const containerRef = useRef(null)
  const debounceRef = useRef(null)

  const genres = useStore(s => s.genres)
  const setActiveGenre = useStore(s => s.setActiveGenre)
  const setCameraTarget = useStore(s => s.setCameraTarget)
  const viewMode = useStore(s => s.viewMode)
  const citiesData = useStore(s => s.citiesData)
  const flyToCity = useStore(s => s.flyToCity)

  const searchIndex = useMemo(() => buildSearchIndex(genres), [genres])

  // Build a city name lookup for globe fly-to
  const cityLookup = useMemo(() => {
    const map = new Map()
    for (const city of citiesData) {
      map.set(city.name.toLowerCase(), city)
      map.set(city.id.toLowerCase(), city)
    }
    return map
  }, [citiesData])

  // Find best city match from query tokens + genre's associated cities
  const findCityForQuery = useCallback((queryStr, genre) => {
    const tokens = queryStr.toLowerCase().split(/[\s,;.]+/).filter(t => t.length >= 2)
    // Direct city name in query
    for (const token of tokens) {
      const city = cityLookup.get(token)
      if (city) return city
    }
    // Multi-word city names (e.g., "new york", "sao paulo", "mexico city", "tel aviv")
    const lowerQuery = queryStr.toLowerCase()
    for (const [name, city] of cityLookup) {
      if (name.includes(' ') && lowerQuery.includes(name)) return city
    }
    // Match via genre's associated cities in cities.json
    if (genre) {
      const slug = genre.slug?.replace(/-/g, '_')
      for (const city of citiesData) {
        if (city.genres?.includes(slug)) return city
      }
    }
    return null
  }, [cityLookup, citiesData])

  const handleSearch = useCallback((q) => {
    const matches = searchGenres(q, searchIndex, genres)
    setResults(matches)
    setSelectedIdx(0)
    setIsOpen(matches.length > 0)
  }, [searchIndex, genres])

  const handleInputChange = useCallback((e) => {
    const val = e.target.value
    setQuery(val)
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => handleSearch(val), 150)
  }, [handleSearch])

  const selectGenre = useCallback((genre) => {
    if (viewMode === 'earth') {
      // In Earth view, fly globe to matching city
      const city = findCityForQuery(query, genre)
      if (city) {
        flyToCity(city.lat, city.lng)
      }
    } else {
      setActiveGenre(genre)
      setCameraTarget(genre)
    }
    setQuery('')
    setResults([])
    setIsOpen(false)
    inputRef.current?.blur()
  }, [viewMode, setActiveGenre, setCameraTarget, flyToCity, findCityForQuery, query])

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape') {
      setQuery('')
      setResults([])
      setIsOpen(false)
      inputRef.current?.blur()
      return
    }
    if (!isOpen || results.length === 0) return
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIdx(i => Math.min(i + 1, results.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIdx(i => Math.max(i - 1, 0))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      selectGenre(results[selectedIdx].genre)
    }
  }, [isOpen, results, selectedIdx, selectGenre])

  // Global keyboard shortcut: / to focus search
  useEffect(() => {
    const handler = (e) => {
      if (e.key === '/' && !e.ctrlKey && !e.metaKey) {
        const tag = document.activeElement?.tagName
        if (tag === 'INPUT' || tag === 'TEXTAREA') return
        e.preventDefault()
        inputRef.current?.focus()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  // Close on outside click
  useEffect(() => {
    const handler = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  return (
    <div className="vibe-search" ref={containerRef}>
      <div className="vibe-search-input-wrap">
        <svg className="vibe-search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.35-4.35" />
        </svg>
        <input
          ref={inputRef}
          type="text"
          className="vibe-search-input"
          placeholder="Search genres, moods, cities..."
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => { if (results.length > 0) setIsOpen(true) }}
        />
        {query && (
          <button
            className="vibe-search-clear"
            onClick={() => { setQuery(''); setResults([]); setIsOpen(false) }}
          >
            x
          </button>
        )}
        <kbd className="vibe-search-kbd">/</kbd>
      </div>

      {isOpen && results.length > 0 && (
        <div className="vibe-search-results">
          {results.map((r, i) => (
            <button
              key={r.genre.slug}
              className={`vibe-search-result ${i === selectedIdx ? 'selected' : ''}`}
              onClick={() => selectGenre(r.genre)}
              onMouseEnter={() => setSelectedIdx(i)}
            >
              <span
                className="vibe-search-result-dot"
                style={{ background: r.genre.color }}
              />
              <div className="vibe-search-result-info">
                <span className="vibe-search-result-name">{r.genre.name}</span>
                <span className="vibe-search-result-scene">{r.genre.scene}</span>
              </div>
              <span className="vibe-search-result-score">
                {Math.round(r.score)}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
