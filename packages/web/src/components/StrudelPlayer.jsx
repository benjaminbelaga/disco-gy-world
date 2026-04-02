import { useEffect, useRef, useState, useCallback } from 'react'
import useStore from '../stores/useStore'
import useAudioStore from '../stores/useAudioStore'
import { generatePattern } from '../lib/strudelPatterns'
import './StrudelPlayer.css'

/**
 * StrudelPlayer — live coding music overlay for DiscoWorld.
 *
 * When activated, generates a Strudel pattern matching the current genre's
 * biome/scene and plays it via the @strudel/repl web component.
 * Users can edit the pattern live and hear changes in real-time.
 */
export default function StrudelPlayer() {
  const activeGenre = useStore(s => s.activeGenre)
  const setAudioPlaying = useAudioStore(s => s.setPlaying)
  const [isOpen, setIsOpen] = useState(false)
  const [isLoaded, setIsLoaded] = useState(false)
  const [pattern, setPattern] = useState('')
  const [isEditing, setIsEditing] = useState(false)
  const editorRef = useRef(null)
  const textareaRef = useRef(null)
  const scriptLoaded = useRef(false)

  // Load Strudel REPL script on first open
  const loadStrudel = useCallback(() => {
    if (scriptLoaded.current) {
      setIsLoaded(true)
      return
    }
    const script = document.createElement('script')
    script.src = 'https://unpkg.com/@strudel/repl@latest'
    script.onload = () => {
      scriptLoaded.current = true
      setIsLoaded(true)
    }
    script.onerror = () => {
      console.warn('Failed to load Strudel REPL')
    }
    document.head.appendChild(script)
  }, [])

  // Generate pattern when genre changes
  useEffect(() => {
    if (activeGenre && isOpen) {
      const newPattern = generatePattern(activeGenre)
      setPattern(newPattern)
    }
  }, [activeGenre, isOpen])

  // Open Strudel player (keyboard shortcut: L)
  useEffect(() => {
    function handleKeyDown(e) {
      // Don't trigger if typing in input/textarea
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return
      if (e.key === 'l' || e.key === 'L') {
        e.preventDefault()
        setIsOpen(prev => !prev)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  // Load Strudel when opening
  useEffect(() => {
    if (isOpen) {
      loadStrudel()
      if (activeGenre && !pattern) {
        setPattern(generatePattern(activeGenre))
      }
    }
  }, [isOpen, loadStrudel, activeGenre, pattern])

  const handleRegenerate = useCallback(() => {
    if (activeGenre) {
      const newPattern = generatePattern(activeGenre)
      setPattern(newPattern)
    }
  }, [activeGenre])

  const handleToggleEdit = useCallback(() => {
    setIsEditing(prev => !prev)
  }, [])

  const handlePatternChange = useCallback((e) => {
    setPattern(e.target.value)
  }, [])

  const handleClose = useCallback(() => {
    setIsOpen(false)
    setIsEditing(false)
    setAudioPlaying(false)
  }, [setAudioPlaying])

  if (!isOpen) {
    return (
      <button
        className="strudel-toggle"
        onClick={() => setIsOpen(true)}
        title="Live Code Music (L)"
        aria-label="Open Strudel live coding player"
      >
        {'</>'}
      </button>
    )
  }

  const genreName = activeGenre?.name || 'No genre selected'

  return (
    <div className="strudel-player" role="region" aria-label="Strudel live coding player">
      <div className="strudel-header">
        <span className="strudel-title">
          strudel — {genreName}
        </span>
        <div className="strudel-actions">
          <button
            className="strudel-btn"
            onClick={handleRegenerate}
            title="Generate new pattern"
            aria-label="Regenerate pattern"
          >
            dice
          </button>
          <button
            className="strudel-btn"
            onClick={handleToggleEdit}
            title={isEditing ? 'Switch to player' : 'Edit code'}
            aria-label={isEditing ? 'Switch to player view' : 'Edit pattern code'}
          >
            {isEditing ? 'play' : 'edit'}
          </button>
          <button
            className="strudel-btn strudel-close"
            onClick={handleClose}
            title="Close (L)"
            aria-label="Close Strudel player"
          >
            x
          </button>
        </div>
      </div>

      <div className="strudel-body">
        {isEditing ? (
          <textarea
            ref={textareaRef}
            className="strudel-textarea"
            value={pattern}
            onChange={handlePatternChange}
            spellCheck={false}
            aria-label="Strudel pattern code"
          />
        ) : isLoaded ? (
          <div className="strudel-repl-container">
            <strudel-editor ref={editorRef}>
              {`<!--\n${pattern}\n-->`}
            </strudel-editor>
          </div>
        ) : (
          <div className="strudel-loading">Loading Strudel engine...</div>
        )}
      </div>

      {!activeGenre && (
        <div className="strudel-hint">
          Click a genre territory to generate a matching pattern
        </div>
      )}
    </div>
  )
}
