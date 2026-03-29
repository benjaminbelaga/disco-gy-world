import { RecordStoreAdapter } from '../RecordStoreAdapter'

/**
 * YOYAKU reference adapter — example integration for a real record store.
 */
export class YoyakuAdapter extends RecordStoreAdapter {
  get id() { return 'yoyaku' }
  get name() { return 'YOYAKU' }
  get url() { return 'https://yoyaku.io' }
  get description() { return 'Independent record store in Paris — techno, house, electro, ambient' }

  async search(query, options = {}) {
    const limit = options.limit || 20
    const url = `https://yoyaku.io/?s=${encodeURIComponent(query)}&post_type=product`
    return [{ title: query, artist: '', price: null, currency: 'EUR', url, format: 'Vinyl', inStock: true }]
  }

  async getRelease(storeId) {
    return { url: `https://yoyaku.io/product/${storeId}` }
  }

  async checkAvailability(release) {
    const q = `${release.artist || ''} ${release.title || ''}`.trim()
    return {
      available: true,
      url: `https://yoyaku.io/?s=${encodeURIComponent(q)}&post_type=product`,
      price: null,
    }
  }

  async getFeatured(limit = 20) {
    return []
  }

  getLocations() {
    return [{
      name: 'YOYAKU',
      lat: 48.87,
      lng: 2.35,
      address: 'Paris, France',
      city: 'Paris',
      country: 'FR',
    }]
  }
}
