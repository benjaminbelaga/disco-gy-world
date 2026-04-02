/**
 * Dig Path serializer — encode/decode curated genre journeys to URL-safe strings.
 *
 * Format: title|desc|slug1:note1,slug2:note2,...
 * Compressed via base64 encoding for URL hash sharing.
 */

const SEPARATOR = '|'
const WAYPOINT_SEP = ','
const NOTE_SEP = ':'

/**
 * Serialize a dig path to a URL-safe base64 string.
 * @param {{ title: string, description: string, waypoints: Array<{ slug: string, note: string }> }} path
 * @returns {string} base64-encoded string
 */
export function serializePath(path) {
  const waypointStr = path.waypoints
    .map(w => {
      const note = (w.note || '').replace(/[|,:]/g, ' ').trim()
      return note ? `${w.slug}${NOTE_SEP}${note}` : w.slug
    })
    .join(WAYPOINT_SEP)

  const title = (path.title || '').replace(/\|/g, ' ').trim()
  const desc = (path.description || '').replace(/\|/g, ' ').trim()
  const raw = `${title}${SEPARATOR}${desc}${SEPARATOR}${waypointStr}`

  // Encode UTF-8 string to base64 without deprecated unescape()
  const bytes = new TextEncoder().encode(raw)
  const binary = Array.from(bytes, b => String.fromCharCode(b)).join('')
  return btoa(binary)
}

/**
 * Deserialize a base64 string back into a dig path object.
 * @param {string} encoded
 * @returns {{ title: string, description: string, waypoints: Array<{ slug: string, note: string }> } | null}
 */
export function deserializePath(encoded) {
  try {
    // Decode base64 to UTF-8 string without deprecated escape()
    const binary = atob(encoded)
    const bytes = Uint8Array.from(binary, c => c.charCodeAt(0))
    const raw = new TextDecoder().decode(bytes)
    const [title, description, waypointStr] = raw.split(SEPARATOR)

    if (!waypointStr) return null

    const waypoints = waypointStr.split(WAYPOINT_SEP).map(w => {
      const idx = w.indexOf(NOTE_SEP)
      if (idx === -1) return { slug: w, note: '' }
      return { slug: w.substring(0, idx), note: w.substring(idx + 1) }
    }).filter(w => w.slug)

    if (waypoints.length === 0) return null

    return { title: title || '', description: description || '', waypoints }
  } catch {
    return null
  }
}

/**
 * Generate a shareable URL hash from a path.
 * @param {{ title: string, description: string, waypoints: Array<{ slug: string, note: string }> }} path
 * @returns {string} URL with #path= hash
 */
export function pathToUrl(path) {
  const encoded = serializePath(path)
  return `${window.location.origin}${window.location.pathname}#path=${encoded}`
}

/**
 * Try to load a path from the current URL hash.
 * @returns {{ title: string, description: string, waypoints: Array<{ slug: string, note: string }> } | null}
 */
export function pathFromUrl() {
  const hash = window.location.hash
  if (!hash.startsWith('#path=')) return null
  const encoded = hash.slice(6)
  return deserializePath(encoded)
}
