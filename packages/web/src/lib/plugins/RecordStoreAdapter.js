/**
 * RecordStoreAdapter — interface for record store integrations.
 *
 * Any shop can implement this adapter to integrate with DiscoWorld.
 * The adapter provides search, availability checks, and store metadata
 * that appear on the Earth Globe and in release panels.
 */
export class RecordStoreAdapter {
  /** Unique store identifier (lowercase, no spaces) */
  get id() { throw new Error('RecordStoreAdapter: id not implemented') }

  /** Display name */
  get name() { throw new Error('RecordStoreAdapter: name not implemented') }

  /** Store website URL */
  get url() { throw new Error('RecordStoreAdapter: url not implemented') }

  /** Store logo URL (optional, square, min 64px) */
  get logoUrl() { return null }

  /** Store description (optional, 1-2 sentences) */
  get description() { return '' }

  /**
   * Search the store's catalog.
   * @param {string} query — search text
   * @param {Object} options — {limit, format, inStockOnly}
   * @returns {Promise<Array<{title, artist, price, currency, url, format, inStock}>>}
   */
  async search(query, options = {}) {
    throw new Error('RecordStoreAdapter: search not implemented')
  }

  /**
   * Get release details by store-specific ID.
   * @param {string} storeId
   * @returns {Promise<{title, artist, price, currency, url, format, inStock, tracks}|null>}
   */
  async getRelease(storeId) {
    throw new Error('RecordStoreAdapter: getRelease not implemented')
  }

  /**
   * Check availability by release metadata or Discogs ID.
   * @param {{title, artist, discogsId, catno}} release
   * @returns {Promise<{available: boolean, url: string, price: number|null}>}
   */
  async checkAvailability(release) {
    return { available: false, url: this.url, price: null }
  }

  /**
   * Get featured/new releases.
   * @param {number} limit
   * @returns {Promise<Array>}
   */
  async getFeatured(limit = 20) { return [] }

  /**
   * Get physical store location(s) for the globe map.
   * @returns {Array<{name, lat, lng, address, city, country}>}
   */
  getLocations() { return [] }
}

/**
 * Validate that an object implements the RecordStoreAdapter interface.
 */
export function validateAdapter(adapter) {
  const errors = []
  if (!adapter.id || typeof adapter.id !== 'string') errors.push('id must be a non-empty string')
  if (!adapter.name || typeof adapter.name !== 'string') errors.push('name must be a non-empty string')
  if (!adapter.url || typeof adapter.url !== 'string') errors.push('url must be a non-empty string')
  if (typeof adapter.search !== 'function') errors.push('search must be a function')
  if (typeof adapter.getRelease !== 'function') errors.push('getRelease must be a function')
  if (typeof adapter.checkAvailability !== 'function') errors.push('checkAvailability must be a function')
  if (typeof adapter.getLocations !== 'function') errors.push('getLocations must be a function')
  return { valid: errors.length === 0, errors }
}
