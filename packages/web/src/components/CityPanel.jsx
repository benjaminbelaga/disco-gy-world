import useStore from '../stores/useStore'

// Format genre slug to readable name
function formatGenre(slug) {
  return slug
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase())
}

export default function CityPanel() {
  const selectedCity = useStore(s => s.selectedCity)
  const setSelectedCity = useStore(s => s.setSelectedCity)
  const releases = useStore(s => s.releases)
  const setCurrentTrack = useStore(s => s.setCurrentTrack)
  const currentTrack = useStore(s => s.currentTrack)
  const playing = useStore(s => s.playing)

  if (!selectedCity) return null

  // Find a playable track matching one of the city genres
  const cityGenres = selectedCity.genres || []
  let sampleTrack = null
  for (const genre of cityGenres) {
    const tracks = releases[genre] || releases[genre.replace(/_/g, ' ')] || []
    if (tracks.length > 0) {
      sampleTrack = tracks[0]
      break
    }
  }

  // Also check variations (lowercase, spaces)
  if (!sampleTrack && releases) {
    const allKeys = Object.keys(releases)
    for (const genre of cityGenres) {
      const normalized = genre.toLowerCase().replace(/_/g, ' ')
      const match = allKeys.find(k => k.toLowerCase().replace(/_/g, ' ') === normalized)
      if (match && releases[match].length > 0) {
        sampleTrack = releases[match][0]
        break
      }
    }
  }

  const isPlaying = sampleTrack && currentTrack && playing &&
    currentTrack.artist === sampleTrack.artist &&
    currentTrack.title === sampleTrack.title

  const releaseStr = selectedCity.release_count
    ? selectedCity.release_count.toLocaleString()
    : '?'

  return (
    <div className="city-panel">
      <button
        className="close-btn"
        onClick={() => setSelectedCity(null)}
        aria-label="Close city panel"
      >
        &times;
      </button>

      <h2>{selectedCity.name}</h2>
      <div className="city-panel-country">{selectedCity.country}</div>

      <div className="city-panel-meta">
        <span>{releaseStr} releases</span>
        {selectedCity.scene_peak && (
          <span>Peak: {selectedCity.scene_peak}</span>
        )}
      </div>

      {selectedCity.description && (
        <p className="city-panel-description">{selectedCity.description}</p>
      )}

      <div className="city-panel-genres">
        {cityGenres.map(g => (
          <span key={g} className="city-genre-tag">{formatGenre(g)}</span>
        ))}
      </div>

      {selectedCity.top_labels && selectedCity.top_labels.length > 0 && (
        <div className="city-panel-labels">
          <h3>{selectedCity.label_count} labels</h3>
          <div className="city-label-list">
            {selectedCity.top_labels.slice(0, 8).map(l => (
              <span key={l.name} className="city-label-tag" title={`${l.releases} releases`}>
                {l.name}
              </span>
            ))}
          </div>
        </div>
      )}

      {sampleTrack && (
        <button
          className={`city-panel-play ${isPlaying ? 'playing' : ''}`}
          onClick={() => setCurrentTrack(sampleTrack)}
        >
          {isPlaying ? (
            <span className="playing-indicator"><span /><span /><span /></span>
          ) : (
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="5,3 19,12 5,21" />
            </svg>
          )}
          <span>
            {sampleTrack.artist} &mdash; {sampleTrack.title}
          </span>
        </button>
      )}
    </div>
  )
}
