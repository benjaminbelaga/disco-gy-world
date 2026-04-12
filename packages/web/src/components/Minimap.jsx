import { useCallback, useRef } from 'react'
import useStore from '../stores/useStore'

// Minimal equirectangular SVG world outline — continents only
const WORLD_PATH = `
M 32,12 L 34,10 36,11 38,9 40,10 42,9 44,10 46,12 48,11 50,10 52,11 54,12 56,11 58,10 60,12 62,13 64,14 66,15 68,16 70,18 72,20 74,22 73,24 71,26 70,28 68,30 66,28 64,26 63,28 62,30 60,32 58,34 56,36 54,38 52,36 50,34 48,33 46,34 44,36 42,34 40,32 38,30 36,28 34,26 32,24 30,22 28,20 26,18 28,16 30,14 Z
M 126,14 L 128,12 130,10 132,12 134,14 136,16 138,18 140,16 142,14 144,12 146,14 148,16 150,18 152,20 154,22 156,24 158,26 160,28 162,30 164,32 162,34 160,36 158,34 156,32 154,30 152,28 150,26 148,28 146,30 144,32 142,30 140,28 138,26 136,24 134,22 132,20 130,18 128,16 Z
M 80,18 L 82,16 84,14 86,12 88,14 90,16 92,18 94,20 96,22 98,20 100,18 102,16 104,18 106,20 108,22 110,24 112,26 114,28 116,30 118,32 120,34 118,36 116,38 114,40 112,42 110,44 108,46 106,44 104,42 102,40 100,38 98,36 96,38 94,40 92,42 90,40 88,38 86,36 84,34 82,32 80,30 78,28 76,26 74,24 76,22 78,20 Z
M 90,52 L 92,50 94,48 96,50 98,52 100,54 102,56 104,58 106,60 108,62 106,64 104,66 102,68 100,66 98,64 96,62 94,60 92,58 90,56 Z
M 48,56 L 50,54 52,52 54,50 56,48 58,50 60,52 62,54 64,56 62,58 60,60 58,62 56,64 54,66 52,68 50,70 48,72 46,70 44,68 42,66 40,64 42,62 44,60 46,58 Z
M 150,56 L 152,54 154,52 156,50 158,52 160,54 162,56 164,58 166,60 168,62 170,64 172,66 170,68 168,70 166,72 164,70 162,68 160,66 158,64 156,62 154,60 152,58 Z
`

const MAP_W = 200
const MAP_H = 100

// Convert lat/lng to minimap x/y (equirectangular)
function toXY(lat, lng) {
  const x = ((lng + 180) / 360) * MAP_W
  const y = ((90 - lat) / 180) * MAP_H
  return { x, y }
}

export default function Minimap() {
  const viewMode = useStore(s => s.viewMode)
  const globeCenter = useStore(s => s.globeCenter)
  const citiesData = useStore(s => s.citiesData)
  const flyToCity = useStore(s => s.flyToCity)
  const hasPlayer = useStore(s => !!s.currentTrack)
  const playerCollapsed = useStore(s => s.playerCollapsed)
  const svgRef = useRef(null)

  const handleClick = useCallback((e) => {
    const rect = svgRef.current?.getBoundingClientRect()
    if (!rect) return
    const mx = e.clientX - rect.left
    const my = e.clientY - rect.top
    const lng = (mx / MAP_W) * 360 - 180
    const lat = 90 - (my / MAP_H) * 180
    flyToCity(lat, lng)
  }, [flyToCity])

  if (viewMode !== 'earth') return null

  const center = toXY(globeCenter.lat, globeCenter.lng)

  // Viewport rectangle (roughly 60 degrees wide, 40 tall)
  const vpW = (60 / 360) * MAP_W
  const vpH = (40 / 180) * MAP_H

  return (
    <div className={`minimap${hasPlayer ? (playerCollapsed ? ' minimap--above-player-mini' : ' minimap--above-player') : ''}`}>
      <svg
        ref={svgRef}
        width={MAP_W}
        height={MAP_H}
        viewBox={`0 0 ${MAP_W} ${MAP_H}`}
        onClick={handleClick}
        style={{ cursor: 'crosshair' }}
      >
        {/* Background */}
        <rect width={MAP_W} height={MAP_H} fill="rgba(5,5,16,0.7)" rx="4" />

        {/* Continents */}
        <path
          d={WORLD_PATH}
          fill="rgba(100,200,255,0.08)"
          stroke="rgba(100,200,255,0.2)"
          strokeWidth="0.5"
        />

        {/* Viewport indicator */}
        <rect
          x={center.x - vpW / 2}
          y={center.y - vpH / 2}
          width={vpW}
          height={vpH}
          fill="rgba(100,200,255,0.08)"
          stroke="rgba(100,200,255,0.4)"
          strokeWidth="1"
          rx="2"
        />

        {/* City dots */}
        {citiesData.map(city => {
          const pos = toXY(city.lat, city.lng)
          return (
            <circle
              key={city.id}
              cx={pos.x}
              cy={pos.y}
              r={1.5}
              fill="#66ccff"
              opacity={0.6}
            />
          )
        })}

        {/* Center crosshair */}
        <circle cx={center.x} cy={center.y} r="2" fill="#66ccff" opacity={0.9} />
      </svg>
    </div>
  )
}
