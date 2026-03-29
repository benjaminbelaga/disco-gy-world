import { useState, useEffect, useRef, useMemo, useCallback } from 'react'
import useStore from '../stores/useStore'
import Tooltip from './Tooltip'
import { buildSearchIndex, searchGenres } from '../utils/vibeSearch'

/**
 * Progressive onboarding flow for DiscoWorld.
 *
 * Steps:
 *   1. "vibe" — Full-screen genre search ("Start digging")
 *   2. "exploring" — Camera flies to genre, samples auto-play
 *   3. "tooltip" — After first genre click, contextual hint
 *   4. "discogs" — After 3 genre interactions, optional Discogs import
 *   5. "complete" — Full UI visible
 *
 * Progressive disclosure:
 *   - After genre select: only 3D world + genre panel (30s or 3 interactions)
 *   - After 30s/3 interactions: timeline, filter bar, shortcuts
 *   - After Discogs import or 2min: everything
 */
export default function Onboarding() {
  const onboardingStep = useStore(s => s.onboardingStep)
  const completeOnboarding = useStore(s => s.completeOnboarding)
  const setOnboardingStep = useStore(s => s.setOnboardingStep)
  const advanceOnboarding = useStore(s => s.advanceOnboarding)
  const startOnboardingTimer = useStore(s => s.startOnboardingTimer)
  const genres = useStore(s => s.genres)
  const setActiveGenre = useStore(s => s.setActiveGenre)
  const setCameraTarget = useStore(s => s.setCameraTarget)
  const releases = useStore(s => s.releases)
  const setCurrentTrack = useStore(s => s.setCurrentTrack)

  const [vibeQuery, setVibeQuery] = useState('')
  const [vibeResults, setVibeResults] = useState([])
  const [showDiscogsDismissed, setShowDiscogsDismissed] = useState(false)
  const inputRef = useRef(null)
  const debounceRef = useRef(null)

  const searchIndex = useMemo(() => buildSearchIndex(genres), [genres])

  // Auto-focus input on mount
  useEffect(() => {
    if (onboardingStep === 'vibe' && inputRef.current) {
      const timer = setTimeout(() => inputRef.current?.focus(), 600)
      return () => clearTimeout(timer)
    }
  }, [onboardingStep])

  // 2-minute timer for auto-completing onboarding
  useEffect(() => {
    if (onboardingStep === 'vibe' || onboardingStep === 'complete') return
    const timer = setTimeout(() => {
      completeOnboarding()
    }, 2 * 60 * 1000)
    return () => clearTimeout(timer)
  }, [onboardingStep, completeOnboarding])

  const handleVibeInput = useCallback((e) => {
    const val = e.target.value
    setVibeQuery(val)
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      const matches = searchGenres(val, searchIndex, genres)
      setVibeResults(matches)
    }, 150)
  }, [searchIndex, genres])

  const handleVibeSubmit = useCallback((genre) => {
    if (!genre) return

    // Fly camera to genre
    setActiveGenre(genre)
    setCameraTarget(genre)

    // Auto-play a sample track from that genre
    // releases is always a dict keyed by genre slug
    const genreTracks = (releases && releases[genre.slug]) || []
    if (genreTracks.length > 0) {
      setCurrentTrack(genreTracks[0])
    }

    // Advance to exploring state
    setOnboardingStep('exploring')
    startOnboardingTimer()

    // After a short delay, move to tooltip step
    setTimeout(() => {
      setOnboardingStep('tooltip')
    }, 3000)
  }, [releases, setActiveGenre, setCameraTarget, setCurrentTrack, setOnboardingStep, startOnboardingTimer])

  const handleVibeKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && vibeResults.length > 0) {
      e.preventDefault()
      handleVibeSubmit(vibeResults[0].genre)
    }
  }, [vibeResults, handleVibeSubmit])

  const handleSkip = useCallback(() => {
    completeOnboarding()
  }, [completeOnboarding])

  // Step 1: "Start digging" full-screen
  if (onboardingStep === 'vibe') {
    return (
      <div className="onboarding-backdrop onboarding-vibe" role="dialog" aria-label="Welcome to DiscoWorld" aria-modal="true">
        <div className="onboarding-vibe-container">
          <h1 className="onboarding-vibe-title">4.8 million records.<br />One world.</h1>
          <p className="onboarding-vibe-subtitle">
            Search a genre, artist, or city — or just start digging
          </p>

          <div className="onboarding-vibe-input-wrap">
            <input
              ref={inputRef}
              type="text"
              className="onboarding-vibe-input"
              placeholder="acid techno, deep house, Berlin..."
              value={vibeQuery}
              onChange={handleVibeInput}
              onKeyDown={handleVibeKeyDown}
              autoComplete="off"
              spellCheck={false}
              aria-label="Search for a genre, artist, or city to start exploring"
              role="combobox"
              aria-expanded={vibeResults.length > 0}
              aria-controls="onboarding-results"
              aria-autocomplete="list"
            />
          </div>

          {vibeResults.length > 0 && (
            <div className="onboarding-vibe-results" id="onboarding-results" role="listbox" aria-label="Genre suggestions">
              {vibeResults.map((r) => (
                <button
                  key={r.genre.slug}
                  className="onboarding-vibe-result"
                  onClick={() => handleVibeSubmit(r.genre)}
                  role="option"
                  aria-label={`Explore ${r.genre.name}${r.genre.scene ? `, ${r.genre.scene}` : ''}`}
                >
                  <span
                    className="onboarding-vibe-result-dot"
                    style={{ background: r.genre.color }}
                    aria-hidden="true"
                  />
                  <span className="onboarding-vibe-result-name">{r.genre.name}</span>
                  {r.genre.scene && (
                    <span className="onboarding-vibe-result-scene">{r.genre.scene}</span>
                  )}
                </button>
              ))}
            </div>
          )}

          <div className="onboarding-actions">
            <button className="onboarding-skip-link" onClick={handleSkip} aria-label="Skip and explore freely">
              Just explore
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Step 2: Tooltip hint after first genre click
  if (onboardingStep === 'tooltip') {
    return (
      <Tooltip
        visible={true}
        text="Click genres to explore. Press R to discover something random."
        position={{ top: '50%', left: '50%' }}
        placement="bottom"
        onDismiss={() => advanceOnboarding()}
        autoDismiss={5000}
      />
    )
  }

  // Step 3: Discogs import prompt
  if (onboardingStep === 'discogs' && !showDiscogsDismissed) {
    return (
      <div className="onboarding-discogs-prompt" role="dialog" aria-label="Import Discogs collection">
        <p>Got a Discogs collection? Bring your crates in.</p>
        <div className="onboarding-discogs-actions">
          <button
            className="onboarding-discogs-btn"
            onClick={() => {
              useStore.setState({ passportOpen: true })
              completeOnboarding()
            }}
          >
            Connect Discogs
          </button>
          <button
            className="onboarding-discogs-dismiss"
            onClick={() => {
              setShowDiscogsDismissed(true)
              completeOnboarding()
            }}
          >
            Maybe later
          </button>
        </div>
      </div>
    )
  }

  // Complete or returning user — render nothing
  return null
}
