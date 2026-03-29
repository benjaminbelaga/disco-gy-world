# DiscoWorld Plugin API — RecordStoreAdapter

Any record store can integrate with DiscoWorld by implementing the `RecordStoreAdapter` interface.

## Quick Start

```js
import { RecordStoreAdapter } from './lib/plugins/RecordStoreAdapter'
import { registerAdapter } from './lib/plugins/registry'

class MyShopAdapter extends RecordStoreAdapter {
  get id() { return 'myshop' }
  get name() { return 'My Record Shop' }
  get url() { return 'https://myshop.com' }

  async search(query) {
    const res = await fetch(`https://myshop.com/api/search?q=${query}`)
    return res.json()
  }

  async getRelease(storeId) {
    const res = await fetch(`https://myshop.com/api/releases/${storeId}`)
    return res.json()
  }

  async checkAvailability(release) {
    return { available: true, url: `https://myshop.com/search?q=${release.title}`, price: null }
  }

  getLocations() {
    return [{ name: 'My Shop', lat: 52.52, lng: 13.41, city: 'Berlin', country: 'DE' }]
  }
}

registerAdapter(new MyShopAdapter())
```

## Interface Reference

| Method | Required | Returns |
|--------|----------|---------|
| `get id` | Yes | `string` — unique identifier |
| `get name` | Yes | `string` — display name |
| `get url` | Yes | `string` — website URL |
| `get logoUrl` | No | `string\|null` — square logo |
| `get description` | No | `string` — 1-2 sentences |
| `search(query, options)` | Yes | `Promise<Array>` — search results |
| `getRelease(storeId)` | Yes | `Promise<Object\|null>` — release details |
| `checkAvailability(release)` | Yes | `Promise<{available, url, price}>` |
| `getFeatured(limit)` | No | `Promise<Array>` — featured releases |
| `getLocations()` | Yes | `Array<{name, lat, lng, ...}>` — physical stores |

## Search Result Format

```js
{
  title: 'Release Title',
  artist: 'Artist Name',
  price: 12.99,
  currency: 'EUR',
  url: 'https://myshop.com/release/123',
  format: 'Vinyl',
  inStock: true
}
```

## Built-in Adapters

- **DiscogsAdapter** — Links to Discogs Marketplace
- **YoyakuAdapter** — YOYAKU record store (Paris)

## Registry API

```js
import { registerAdapter, getAdapter, getAllAdapters, removeAdapter } from './lib/plugins/registry'

registerAdapter(adapter)     // Register a store adapter
getAdapter('id')             // Get adapter by ID
getAllAdapters()              // List all registered adapters
removeAdapter('id')          // Unregister an adapter
```
