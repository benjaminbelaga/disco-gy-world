/**
 * Share Card Generator — creates shareable images for genre discoveries.
 *
 * Generates a canvas-based OG image with:
 * - Genre name + biome colors
 * - Scene label + year of emergence
 * - Stats (track count, releases)
 * - DiscoWorld branding
 *
 * Output: data URL or blob for sharing via Web Share API.
 */

const CARD_WIDTH = 1200
const CARD_HEIGHT = 630

// Biome color palettes for card backgrounds
const BIOME_GRADIENTS = {
  'techno-massif': ['#0a0a1a', '#1a1a3a', '#2a1040'],
  'house-plains': ['#1a0a0a', '#2a1a10', '#3a2a15'],
  'disco-riviera': ['#1a0520', '#2a0830', '#400a40'],
  'ambient-depths': ['#050a1a', '#0a1530', '#102040'],
  'jungle-canopy': ['#0a1a0a', '#102a10', '#153a15'],
  'trance-highlands': ['#0a0a2a', '#1a1050', '#2a1570'],
  'industrial-wasteland': ['#0a0a0a', '#1a1a1a', '#2a2020'],
  'idm-crystalline': ['#0a0a1a', '#101530', '#152040'],
  'dubstep-rift': ['#0a0510', '#150a20', '#200f30'],
  'garage-district': ['#1a0a0a', '#2a1510', '#3a2015'],
  'urban-quarter': ['#0a0a0a', '#1a1510', '#2a2015'],
  'source-monuments': ['#0a0a05', '#1a1a10', '#2a2a15'],
  'unknown': ['#0a0a0a', '#1a1a1a', '#2a2a2a'],
}

/**
 * Generate a share card as a canvas data URL.
 */
export function generateShareCard(genre) {
  const canvas = document.createElement('canvas')
  canvas.width = CARD_WIDTH
  canvas.height = CARD_HEIGHT
  const ctx = canvas.getContext('2d')

  const biome = genre.biome || 'unknown'
  const colors = BIOME_GRADIENTS[biome] || BIOME_GRADIENTS['unknown']
  const accentColor = genre.color || '#ffffff'

  // Background gradient
  const grad = ctx.createLinearGradient(0, 0, CARD_WIDTH, CARD_HEIGHT)
  grad.addColorStop(0, colors[0])
  grad.addColorStop(0.5, colors[1])
  grad.addColorStop(1, colors[2])
  ctx.fillStyle = grad
  ctx.fillRect(0, 0, CARD_WIDTH, CARD_HEIGHT)

  // Decorative grid lines
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)'
  ctx.lineWidth = 1
  for (let x = 0; x < CARD_WIDTH; x += 40) {
    ctx.beginPath()
    ctx.moveTo(x, 0)
    ctx.lineTo(x, CARD_HEIGHT)
    ctx.stroke()
  }
  for (let y = 0; y < CARD_HEIGHT; y += 40) {
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(CARD_WIDTH, y)
    ctx.stroke()
  }

  // Accent glow (top-right)
  const glowGrad = ctx.createRadialGradient(
    CARD_WIDTH * 0.7, CARD_HEIGHT * 0.3, 0,
    CARD_WIDTH * 0.7, CARD_HEIGHT * 0.3, 300
  )
  glowGrad.addColorStop(0, accentColor + '20')
  glowGrad.addColorStop(1, 'transparent')
  ctx.fillStyle = glowGrad
  ctx.fillRect(0, 0, CARD_WIDTH, CARD_HEIGHT)

  // Genre name (large)
  ctx.fillStyle = accentColor
  ctx.font = 'bold 72px "Inter", "Helvetica Neue", sans-serif'
  ctx.textBaseline = 'top'

  // Truncate if too long
  let genreName = genre.name || 'Unknown'
  while (ctx.measureText(genreName).width > CARD_WIDTH - 160 && genreName.length > 5) {
    genreName = genreName.slice(0, -1)
  }
  ctx.fillText(genreName, 80, 120)

  // Scene label
  ctx.fillStyle = 'rgba(255, 255, 255, 0.5)'
  ctx.font = '24px "Inter", "Helvetica Neue", sans-serif'
  ctx.fillText(genre.scene || '', 80, 210)

  // Emerged year
  if (genre.emerged) {
    ctx.fillStyle = 'rgba(255, 255, 255, 0.35)'
    ctx.font = '20px "JetBrains Mono", monospace'
    ctx.fillText(`Emerged: ${genre.emerged}`, 80, 250)
  }

  // AKA
  if (genre.aka) {
    ctx.fillStyle = 'rgba(255, 255, 255, 0.25)'
    ctx.font = 'italic 18px "Inter", "Helvetica Neue", sans-serif'
    const akaText = genre.aka.length > 80 ? genre.aka.slice(0, 77) + '...' : genre.aka
    ctx.fillText(`aka ${akaText}`, 80, 290)
  }

  // Stats bar
  const statsY = 380
  ctx.fillStyle = 'rgba(255, 255, 255, 0.08)'
  ctx.fillRect(80, statsY, CARD_WIDTH - 160, 60)

  ctx.fillStyle = 'rgba(255, 255, 255, 0.6)'
  ctx.font = '18px "JetBrains Mono", monospace'
  const stats = []
  if (genre.trackCount) stats.push(`${genre.trackCount} tracks`)
  if (genre.release_count) stats.push(`${genre.release_count.toLocaleString()} releases`)
  stats.push(genre.biome?.replace(/-/g, ' ') || 'electronic')
  ctx.fillText(stats.join('  |  '), 100, statsY + 22)

  // Description snippet
  if (genre.description) {
    ctx.fillStyle = 'rgba(255, 255, 255, 0.3)'
    ctx.font = '16px "Inter", "Helvetica Neue", sans-serif'
    const desc = genre.description.length > 200 ? genre.description.slice(0, 197) + '...' : genre.description
    // Word wrap
    const words = desc.split(' ')
    let line = ''
    let y = 470
    for (const word of words) {
      const test = line + word + ' '
      if (ctx.measureText(test).width > CARD_WIDTH - 160) {
        ctx.fillText(line, 80, y)
        line = word + ' '
        y += 22
        if (y > 540) break
      } else {
        line = test
      }
    }
    if (y <= 540) ctx.fillText(line, 80, y)
  }

  // DiscoWorld branding (bottom-right)
  ctx.fillStyle = 'rgba(255, 255, 255, 0.2)'
  ctx.font = 'bold 24px "Inter", "Helvetica Neue", sans-serif'
  ctx.textAlign = 'right'
  ctx.fillText('DiscoWorld', CARD_WIDTH - 80, CARD_HEIGHT - 50)

  ctx.fillStyle = 'rgba(255, 255, 255, 0.12)'
  ctx.font = '14px "JetBrains Mono", monospace'
  ctx.fillText('non-linear musical exploration', CARD_WIDTH - 80, CARD_HEIGHT - 25)

  ctx.textAlign = 'left' // reset

  return canvas.toDataURL('image/png')
}

/**
 * Share a genre discovery via Web Share API or clipboard.
 */
export async function shareGenre(genre, url) {
  const shareUrl = url || window.location.href
  const text = `Exploring ${genre.name} on DiscoWorld — ${genre.scene}, emerged ${genre.emerged || 'unknown'}`

  // Try Web Share API first
  if (navigator.share) {
    try {
      const dataUrl = generateShareCard(genre)
      const blob = await (await fetch(dataUrl)).blob()
      const file = new File([blob], `discoworld-${genre.slug}.png`, { type: 'image/png' })

      await navigator.share({
        title: `${genre.name} — DiscoWorld`,
        text,
        url: shareUrl,
        files: [file],
      })
      return 'shared'
    } catch (e) {
      if (e.name === 'AbortError') return 'cancelled'
      // Fall through to clipboard
    }
  }

  // Fallback: copy URL to clipboard
  try {
    await navigator.clipboard.writeText(`${text}\n${shareUrl}`)
    return 'copied'
  } catch {
    return 'failed'
  }
}

export { BIOME_GRADIENTS }
