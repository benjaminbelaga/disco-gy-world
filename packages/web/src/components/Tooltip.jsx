import { useState, useEffect, useRef, useCallback } from 'react'

const AUTO_DISMISS_MS = 5000

/**
 * Reusable glass tooltip for contextual onboarding hints.
 * Positions near a target element or at explicit coordinates.
 *
 * Props:
 *   - visible: boolean
 *   - text: string
 *   - targetRef: React ref to position near (optional)
 *   - position: { top, left, bottom, right } explicit CSS (optional, fallback)
 *   - placement: 'top' | 'bottom' | 'left' | 'right' (default: 'bottom')
 *   - onDismiss: callback when tooltip auto-dismisses or is clicked away
 *   - autoDismiss: ms before auto-dismiss (default: 5000, 0 = no auto)
 */
export default function Tooltip({
  visible,
  text,
  targetRef,
  position,
  placement = 'bottom',
  onDismiss,
  autoDismiss = AUTO_DISMISS_MS,
}) {
  const [show, setShow] = useState(false)
  const [coords, setCoords] = useState(null)
  const tooltipRef = useRef(null)

  // Calculate position from target element
  const updatePosition = useCallback(() => {
    if (!targetRef?.current) {
      if (position) setCoords(position)
      return
    }
    const rect = targetRef.current.getBoundingClientRect()
    const gap = 8

    let top, left
    switch (placement) {
      case 'top':
        top = rect.top - gap
        left = rect.left + rect.width / 2
        break
      case 'left':
        top = rect.top + rect.height / 2
        left = rect.left - gap
        break
      case 'right':
        top = rect.top + rect.height / 2
        left = rect.right + gap
        break
      case 'bottom':
      default:
        top = rect.bottom + gap
        left = rect.left + rect.width / 2
        break
    }

    setCoords({ top, left })
  }, [targetRef, position, placement])

  useEffect(() => {
    if (visible) {
      updatePosition()
      setShow(true)
    } else {
      setShow(false)
    }
  }, [visible, updatePosition])

  // Auto-dismiss
  useEffect(() => {
    if (!show || !autoDismiss) return
    const timer = setTimeout(() => {
      setShow(false)
      onDismiss?.()
    }, autoDismiss)
    return () => clearTimeout(timer)
  }, [show, autoDismiss, onDismiss])

  // Click outside to dismiss
  useEffect(() => {
    if (!show) return
    const handler = (e) => {
      if (tooltipRef.current && !tooltipRef.current.contains(e.target)) {
        setShow(false)
        onDismiss?.()
      }
    }
    // Delay to avoid immediate dismiss from the click that triggered it
    const id = setTimeout(() => document.addEventListener('mousedown', handler), 100)
    return () => {
      clearTimeout(id)
      document.removeEventListener('mousedown', handler)
    }
  }, [show, onDismiss])

  if (!show || !coords) return null

  const transformOrigin = {
    top: 'bottom center',
    bottom: 'top center',
    left: 'center right',
    right: 'center left',
  }[placement]

  const translate = {
    top: 'translate(-50%, -100%)',
    bottom: 'translate(-50%, 0)',
    left: 'translate(-100%, -50%)',
    right: 'translate(0, -50%)',
  }[placement]

  return (
    <div
      ref={tooltipRef}
      className="dw-tooltip"
      style={{
        position: 'fixed',
        top: coords.top,
        left: coords.left,
        transform: translate,
        transformOrigin,
        zIndex: 250,
      }}
      onClick={() => { setShow(false); onDismiss?.() }}
    >
      <span className="dw-tooltip-text">{text}</span>
    </div>
  )
}
