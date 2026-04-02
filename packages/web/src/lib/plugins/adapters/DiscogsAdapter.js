import { RecordStoreAdapter } from '../RecordStoreAdapter'

/**
 * Discogs Marketplace adapter — links to Discogs for purchases.
 */
export class DiscogsAdapter extends RecordStoreAdapter {
  get id() { return 'discogs' }
  get name() { return 'Discogs Marketplace' }
  get url() { return 'https://www.discogs.com' }
  get logoUrl() { return 'https://www.discogs.com/favicon.ico' }
  get description() { return 'The world\'s largest vinyl marketplace' }

  async search(query) {
    const url = `https://www.discogs.com/search/?q=${encodeURIComponent(query)}&type=release&format_exact=Vinyl`
    return [{ title: query, artist: '', price: null, currency: 'USD', url, format: 'Vinyl', inStock: true }]
  }

  async getRelease(storeId) {
    return { url: `https://www.discogs.com/release/${storeId}` }
  }

  async checkAvailability(release) {
    const id = release.discogsId || ''
    return {
      available: true,
      url: id ? `https://www.discogs.com/sell/release/${id}` : `https://www.discogs.com/search/?q=${encodeURIComponent(release.title || '')}`,
      price: null,
    }
  }

  getLocations() { return [] }
}
