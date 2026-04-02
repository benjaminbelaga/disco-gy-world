import { useRef, useEffect, useCallback, useMemo } from 'react'
import useStore from '../stores/useStore'

const GOLD = '#FFD700'
const EDGE_COLOR = 'rgba(255,215,0,0.12)'
const BG = '#0a0a14'
const FONT = "'JetBrains Mono', monospace"

// Layout: force-directed positions for collection genres
function computeLayout(nodes, edges, width, height) {
  const cx = width / 2
  const cy = height / 2
  const positions = new Map()

  // Initial placement: radial by index
  nodes.forEach((n, i) => {
    const angle = (i / nodes.length) * Math.PI * 2 - Math.PI / 2
    const radius = Math.min(width, height) * 0.32
    positions.set(n.slug, {
      x: cx + Math.cos(angle) * radius,
      y: cy + Math.sin(angle) * radius,
    })
  })

  // Simple force-directed relaxation (50 iterations)
  for (let iter = 0; iter < 50; iter++) {
    const forces = new Map()
    nodes.forEach(n => forces.set(n.slug, { fx: 0, fy: 0 }))

    // Repulsion between all nodes
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = positions.get(nodes[i].slug)
        const b = positions.get(nodes[j].slug)
        const dx = b.x - a.x
        const dy = b.y - a.y
        const dist = Math.max(1, Math.sqrt(dx * dx + dy * dy))
        const force = 800 / (dist * dist)
        const fx = (dx / dist) * force
        const fy = (dy / dist) * force
        forces.get(nodes[i].slug).fx -= fx
        forces.get(nodes[i].slug).fy -= fy
        forces.get(nodes[j].slug).fx += fx
        forces.get(nodes[j].slug).fy += fy
      }
    }

    // Attraction along edges
    edges.forEach(e => {
      const a = positions.get(e.source)
      const b = positions.get(e.target)
      if (!a || !b) return
      const dx = b.x - a.x
      const dy = b.y - a.y
      const dist = Math.sqrt(dx * dx + dy * dy)
      const force = (dist - 60) * 0.02
      const fx = (dx / Math.max(1, dist)) * force
      const fy = (dy / Math.max(1, dist)) * force
      forces.get(e.source).fx += fx
      forces.get(e.source).fy += fy
      forces.get(e.target).fx -= fx
      forces.get(e.target).fy -= fy
    })

    // Center gravity
    nodes.forEach(n => {
      const p = positions.get(n.slug)
      forces.get(n.slug).fx += (cx - p.x) * 0.01
      forces.get(n.slug).fy += (cy - p.y) * 0.01
    })

    // Apply forces with damping
    const damping = 0.8 - iter * 0.01
    nodes.forEach(n => {
      const p = positions.get(n.slug)
      const f = forces.get(n.slug)
      p.x += f.fx * damping
      p.y += f.fy * damping
      // Clamp to canvas
      p.x = Math.max(30, Math.min(width - 30, p.x))
      p.y = Math.max(30, Math.min(height - 30, p.y))
    })
  }

  return positions
}

function drawTopology(ctx, nodes, edges, positions, maxCount, width, height) {
  ctx.clearRect(0, 0, width, height)

  // Background
  ctx.fillStyle = BG
  ctx.fillRect(0, 0, width, height)

  // Draw edges
  ctx.strokeStyle = EDGE_COLOR
  ctx.lineWidth = 1
  edges.forEach(e => {
    const a = positions.get(e.source)
    const b = positions.get(e.target)
    if (!a || !b) return
    ctx.beginPath()
    ctx.moveTo(a.x, a.y)
    // Slight curve
    const mx = (a.x + b.x) / 2 + (a.y - b.y) * 0.1
    const my = (a.y + b.y) / 2 + (b.x - a.x) * 0.1
    ctx.quadraticCurveTo(mx, my, b.x, b.y)
    ctx.stroke()
  })

  // Draw nodes
  nodes.forEach(n => {
    const p = positions.get(n.slug)
    if (!p) return
    const intensity = 0.4 + 0.6 * (n.count / maxCount)
    const radius = 4 + (n.count / maxCount) * 12

    // Glow
    const gradient = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, radius * 2.5)
    gradient.addColorStop(0, `rgba(255,215,0,${intensity * 0.25})`)
    gradient.addColorStop(1, 'rgba(255,215,0,0)')
    ctx.fillStyle = gradient
    ctx.beginPath()
    ctx.arc(p.x, p.y, radius * 2.5, 0, Math.PI * 2)
    ctx.fill()

    // Core
    ctx.fillStyle = `rgba(255,215,0,${intensity})`
    ctx.beginPath()
    ctx.arc(p.x, p.y, radius, 0, Math.PI * 2)
    ctx.fill()

    // Border
    ctx.strokeStyle = GOLD
    ctx.lineWidth = 1.5
    ctx.beginPath()
    ctx.arc(p.x, p.y, radius, 0, Math.PI * 2)
    ctx.stroke()

    // Label
    ctx.fillStyle = `rgba(255,255,255,${0.4 + intensity * 0.4})`
    ctx.font = `${Math.max(9, 10 + (n.count / maxCount) * 3)}px ${FONT}`
    ctx.textAlign = 'center'
    ctx.fillText(n.name, p.x, p.y + radius + 14)
  })

  // Title
  ctx.fillStyle = 'rgba(255,255,255,0.5)'
  ctx.font = `11px ${FONT}`
  ctx.textAlign = 'left'
  ctx.fillText('YOUR MUSICAL DNA', 16, 24)

  // Signature
  ctx.fillStyle = 'rgba(255,255,255,0.2)'
  ctx.font = `9px ${FONT}`
  ctx.textAlign = 'right'
  ctx.fillText('discoworld.fm', width - 12, height - 10)
}

export default function TasteTopology() {
  const canvasRef = useRef(null)
  const tasteProfile = useStore(s => s.tasteProfile)
  const collectionGenres = useStore(s => s.collectionGenres)
  const genres = useStore(s => s.genres)
  const links = useStore(s => s.links)
  const passportOpen = useStore(s => s.passportOpen)

  const WIDTH = 400
  const HEIGHT = 320

  // Compute nodes and edges from collection
  const { nodes, edges, maxCount } = useMemo(() => {
    if (!tasteProfile || Object.keys(collectionGenres).length === 0) {
      return { nodes: [], edges: [], maxCount: 1 }
    }
    const slugToGenre = {}
    genres.forEach(g => { slugToGenre[g.slug] = g })

    const nodes = Object.entries(collectionGenres)
      .map(([slug, count]) => {
        const g = slugToGenre[slug]
        return g ? { slug, name: g.name, count, color: g.color } : null
      })
      .filter(Boolean)
      .sort((a, b) => b.count - a.count)
      .slice(0, 20) // Top 20 genres for readability

    const nodeSet = new Set(nodes.map(n => n.slug))
    const edges = links
      .filter(l => nodeSet.has(l.source) && nodeSet.has(l.target))

    const maxCount = Math.max(1, ...nodes.map(n => n.count))
    return { nodes, edges, maxCount }
  }, [tasteProfile, collectionGenres, genres, links])

  // Draw the topology
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || nodes.length === 0) return
    const ctx = canvas.getContext('2d')

    const dpr = window.devicePixelRatio || 1
    canvas.width = WIDTH * dpr
    canvas.height = HEIGHT * dpr
    ctx.scale(dpr, dpr)

    const positions = computeLayout(nodes, edges, WIDTH, HEIGHT)
    drawTopology(ctx, nodes, edges, positions, maxCount, WIDTH, HEIGHT)
  }, [nodes, edges, maxCount])

  const handleExport = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const dataUrl = canvas.toDataURL('image/png')
    const a = document.createElement('a')
    a.href = dataUrl
    a.download = `discoworld-taste-${Date.now()}.png`
    a.click()
  }, [])

  // Only show when passport is open and collection is loaded
  if (!passportOpen || !tasteProfile || nodes.length === 0) return null

  return (
    <div
      style={{
        position: 'fixed', bottom: 80, left: 24, zIndex: 160,
        background: 'rgba(10,10,20,0.9)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        border: '1px solid rgba(255,215,0,0.15)',
        borderRadius: 12, overflow: 'hidden',
        boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
        animation: 'onboarding-fade-in 0.4s ease-out',
      }}
    >
      <canvas
        ref={canvasRef}
        style={{ width: WIDTH, height: HEIGHT, display: 'block' }}
      />
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '8px 12px',
        borderTop: '1px solid rgba(255,255,255,0.05)',
      }}>
        <span style={{
          fontSize: 10, color: 'rgba(255,255,255,0.3)',
          fontFamily: FONT,
        }}>
          {nodes.length} genres connected
        </span>
        <button
          onClick={handleExport}
          style={{
            padding: '4px 10px', borderRadius: 6,
            background: 'rgba(255,215,0,0.08)',
            border: '1px solid rgba(255,215,0,0.2)',
            color: GOLD, fontSize: 10, cursor: 'pointer',
            fontFamily: FONT,
          }}
          onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,215,0,0.15)' }}
          onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,215,0,0.08)' }}
        >
          Export PNG
        </button>
      </div>
    </div>
  )
}
