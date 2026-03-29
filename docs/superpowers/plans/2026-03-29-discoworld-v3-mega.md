# DiscoWorld v3 Mega Plan — Private YOYAKU Integration + Immersive World + Git Hygiene

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship 5 major improvements: (1) private YOYAKU.io login with order history, (2) separate private integration code from public repo, (3) squash git history into one clean mega-push, (4) Minecraft-inspired immersive 3D world, (5) improved cartography/terrain.

**Architecture:** The YOYAKU integration lives in a PRIVATE repo (`discoworld-yoyaku`) that extends the public DiscoWorld via the RecordStoreAdapter plugin API. The public repo stays clean. Git history is squashed into a single initial commit. The 3D world gets buildings on the GenreWorld (default view), better terrain shading, fog, particles, and clickable buildings.

**Tech Stack:** React 19, Three.js r183, React Three Fiber, FastAPI, WooCommerce REST API, SQLite

---

## File Structure

### Public Repo (discoworld) — no YOYAKU private code
```
packages/web/src/
├── components/GenreWorld.jsx          MODIFY — add building instances, fog, enhanced terrain
├── components/GenreWorldBuildings.jsx CREATE — instanced building meshes for GenreWorld
├── components/GenreWorldTerrain.jsx   CREATE — enhanced terrain with biome-specific materials
├── lib/buildingGenerator.js           MODIFY — add GenreWorld flat-plane building generation
├── lib/terrainColors.js               CREATE — biome-specific color palettes for terrain
├── index.css                          MODIFY — adjust z-index/positioning polish
```

### Private Repo (discoworld-yoyaku) — separate repo
```
discoworld-yoyaku/
├── package.json
├── README.md
├── src/
│   ├── YoyakuPrivateAdapter.js      — real WooCommerce API integration
│   ├── YoyakuAuthProvider.jsx       — login form + session management
│   ├── YoyakuOrderHistory.jsx       — order history panel
│   └── yoyakuApi.js                 — YOYAKU REST API client
├── api/
│   └── yoyaku_proxy.py              — FastAPI proxy for YOYAKU API (CORS + auth)
└── tests/
    └── test_yoyaku_adapter.test.js
```

---

### Task 1: Squash Git History for Clean Public Repo

**Files:**
- Modify: Git history (rewrite)

> **WARNING: Destructive operation.** This replaces all 142 commits with ONE clean initial commit. The current HEAD is preserved — only history changes. All current code stays identical.

- [ ] **Step 1: Create a backup branch**

```bash
cd ~/repos/discoworld
git branch backup-before-squash
git tag v2.0-pre-squash
```

- [ ] **Step 2: Verify no YOYAKU private data in codebase**

```bash
grep -rn "yoyaku-hetzner\|b@yoyaku.fr\|188\.40\.232\|95\.111\.255\|consumer_key\|consumer_secret\|wc/v3" packages/ --include="*.py" --include="*.js" --include="*.jsx" | grep -v node_modules | grep -v YoyakuAdapter
```

Expected: NO matches (YoyakuAdapter is the public mock, which is OK).

- [ ] **Step 3: Remove YOYAKU private references from YoyakuAdapter**

Replace `packages/web/src/lib/plugins/adapters/YoyakuAdapter.js` — remove the real store address (35 rue des Petites Ecuries) and replace with generic location:

```js
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
```

- [ ] **Step 4: Squash all commits into one**

```bash
cd ~/repos/discoworld
git checkout --orphan fresh-main
git add -A
git commit -m "Initial release: DiscoWorld v2.0

3D music discovery platform mapping 4.87M electronic music releases.

Features:
- Genre World: procedural planet with 166 genre territories across 13 biomes
- Earth Globe: 7,121 record shops + 30,188 geocoded labels
- Genre Planet: orbital view with clickable territories
- Hybrid recommendations (collaborative + content-based filtering)
- Discogs collection sync + taste profiling
- Community genre editing with voting system
- Contributor recognition with leaderboard
- Discogs OAuth 1.0a multi-user authentication
- RecordStoreAdapter plugin API for store integrations
- 8 curated dig paths (Detroit→Berlin, Birth of House, etc.)
- Biome soundscape engine (procedural ambient audio)
- Social sharing with OG image generation
- MusicBrainz cross-reference pipeline
- 346 automated tests (API, pipeline, frontend, E2E)

Tech: React 19, Three.js, globe.gl, FastAPI, SQLite
Data: Discogs CC0 dump, OpenStreetMap, MusicBrainz
License: AGPL-3.0 (code), CC0 (community data)"
```

- [ ] **Step 5: Replace main branch**

```bash
git branch -D main
git branch -m main
git push origin main --force
```

- [ ] **Step 6: Verify**

```bash
git log --oneline
# Should show exactly 1 commit
gh repo view --json url
```

---

### Task 2: Create Private YOYAKU Repo

**Files:**
- Create: `~/repos/discoworld-yoyaku/` (new private repo)

- [ ] **Step 1: Create repo structure**

```bash
mkdir -p ~/repos/discoworld-yoyaku/{src,api,tests}
cd ~/repos/discoworld-yoyaku
git init
```

- [ ] **Step 2: Create package.json**

```json
{
  "name": "discoworld-yoyaku",
  "version": "1.0.0",
  "private": true,
  "description": "YOYAKU.io private integration for DiscoWorld",
  "main": "src/YoyakuPrivateAdapter.js",
  "scripts": {
    "test": "vitest run"
  }
}
```

- [ ] **Step 3: Create the YOYAKU API client**

Create `src/yoyakuApi.js`:

```js
/**
 * YOYAKU.io REST API client.
 * Talks to WooCommerce REST API + YIO custom endpoints.
 */

const YOYAKU_API = 'https://yoyaku.io/wp-json'

export async function authenticateCustomer(email, password) {
  // Use WooCommerce customer authentication
  // POST to a custom YIO endpoint that validates credentials
  // and returns a session token + customer data
  const resp = await fetch(`${YOYAKU_API}/yoyaku/v1/discoworld/auth`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!resp.ok) throw new Error('Authentication failed')
  return resp.json()
}

export async function getOrderHistory(sessionToken, limit = 50) {
  const resp = await fetch(`${YOYAKU_API}/yoyaku/v1/discoworld/orders?limit=${limit}`, {
    headers: { 'Authorization': `Bearer ${sessionToken}` },
  })
  if (!resp.ok) throw new Error('Failed to fetch orders')
  return resp.json()
  // Returns: [{id, date, total, items: [{name, artist, label, sku, discogs_id, image}]}]
}

export async function getCustomerProfile(sessionToken) {
  const resp = await fetch(`${YOYAKU_API}/yoyaku/v1/discoworld/profile`, {
    headers: { 'Authorization': `Bearer ${sessionToken}` },
  })
  if (!resp.ok) throw new Error('Failed to fetch profile')
  return resp.json()
  // Returns: {email, name, tier, lifetime_value, order_count, top_genres, top_labels, top_artists}
}

export async function getCustomerFeed(sessionToken, limit = 20) {
  const resp = await fetch(`${YOYAKU_API}/yoyaku/v1/discoworld/feed?limit=${limit}`, {
    headers: { 'Authorization': `Bearer ${sessionToken}` },
  })
  if (!resp.ok) throw new Error('Failed to fetch feed')
  return resp.json()
  // Returns products with discogs_ids for mapping to DiscoWorld genres
}
```

- [ ] **Step 4: Create the private adapter**

Create `src/YoyakuPrivateAdapter.js`:

```js
import { getOrderHistory, getCustomerFeed, getCustomerProfile } from './yoyakuApi'

/**
 * YOYAKU Private Adapter — extends the public RecordStoreAdapter
 * with real WooCommerce API integration.
 *
 * This file lives in a PRIVATE repo. The public DiscoWorld repo
 * has a mock YoyakuAdapter that only links to the website.
 */
export class YoyakuPrivateAdapter {
  constructor(sessionToken) {
    this.sessionToken = sessionToken
  }

  get id() { return 'yoyaku-private' }
  get name() { return 'YOYAKU' }
  get url() { return 'https://yoyaku.io' }

  async search(query) {
    const resp = await fetch(
      `https://yoyaku.io/wp-json/yoyaku/v1/filters/search?q=${encodeURIComponent(query)}&limit=20`
    )
    return resp.json()
  }

  async getOrderHistory(limit = 50) {
    return getOrderHistory(this.sessionToken, limit)
  }

  async getFeed(limit = 20) {
    return getCustomerFeed(this.sessionToken, limit)
  }

  async getProfile() {
    return getCustomerProfile(this.sessionToken)
  }

  getLocations() {
    return [{
      name: 'YOYAKU Paris',
      lat: 48.8744,
      lng: 2.3526,
      address: '35 rue des Petites Ecuries, 75010 Paris',
      city: 'Paris',
      country: 'FR',
    }]
  }
}
```

- [ ] **Step 5: Create YIO WordPress endpoint for DiscoWorld auth**

This goes into the YIO plugin (on yoyaku.io server), NOT in the DiscoWorld repo.

Create `~/repos/yio/includes/api/class-yio-discoworld-endpoint.php`:

```php
<?php
/**
 * YIO DiscoWorld API — Customer auth + order history for DiscoWorld app.
 *
 * Endpoints:
 *   POST /wp-json/yoyaku/v1/discoworld/auth     — authenticate customer
 *   GET  /wp-json/yoyaku/v1/discoworld/profile   — customer profile + taste data
 *   GET  /wp-json/yoyaku/v1/discoworld/orders     — order history with Discogs IDs
 *   GET  /wp-json/yoyaku/v1/discoworld/feed       — personalized product feed
 */

if (!defined('ABSPATH')) exit;

class YIO_DiscoWorld_Endpoint {

    public function __construct() {
        add_action('rest_api_init', [$this, 'register_routes']);
    }

    public function register_routes() {
        $ns = 'yoyaku/v1';

        register_rest_route($ns, '/discoworld/auth', [
            'methods'  => 'POST',
            'callback' => [$this, 'authenticate'],
            'permission_callback' => '__return_true',
        ]);

        register_rest_route($ns, '/discoworld/profile', [
            'methods'  => 'GET',
            'callback' => [$this, 'get_profile'],
            'permission_callback' => [$this, 'verify_token'],
        ]);

        register_rest_route($ns, '/discoworld/orders', [
            'methods'  => 'GET',
            'callback' => [$this, 'get_orders'],
            'permission_callback' => [$this, 'verify_token'],
        ]);

        register_rest_route($ns, '/discoworld/feed', [
            'methods'  => 'GET',
            'callback' => [$this, 'get_feed'],
            'permission_callback' => [$this, 'verify_token'],
        ]);
    }

    public function authenticate($request) {
        $email = sanitize_email($request->get_param('email'));
        $password = $request->get_param('password');

        $user = get_user_by('email', $email);
        if (!$user || !wp_check_password($password, $user->user_pass, $user->ID)) {
            return new \WP_Error('auth_failed', 'Invalid credentials', ['status' => 401]);
        }

        // Generate session token (stored as user meta)
        $token = wp_generate_password(64, false);
        update_user_meta($user->ID, '_discoworld_session', $token);
        update_user_meta($user->ID, '_discoworld_session_at', time());

        return [
            'token' => $token,
            'user' => [
                'email' => $user->user_email,
                'name' => $user->display_name,
            ],
        ];
    }

    public function verify_token($request) {
        $auth = $request->get_header('Authorization');
        if (!$auth || !str_starts_with($auth, 'Bearer ')) return false;
        $token = substr($auth, 7);

        $users = get_users(['meta_key' => '_discoworld_session', 'meta_value' => $token, 'number' => 1]);
        if (empty($users)) return false;

        // Check token age (24h max)
        $created = get_user_meta($users[0]->ID, '_discoworld_session_at', true);
        if (time() - intval($created) > 86400) return false;

        $request->set_param('_dw_user_id', $users[0]->ID);
        return true;
    }

    public function get_profile($request) {
        $user_id = $request->get_param('_dw_user_id');
        $customer = new \WC_Customer($user_id);

        // Get order stats
        $orders = wc_get_orders(['customer_id' => $user_id, 'limit' => -1, 'status' => ['completed', 'processing']]);
        $total_spent = array_sum(array_map(fn($o) => $o->get_total(), $orders));

        // Get top genres/artists/labels from order items
        $genre_counts = [];
        $artist_counts = [];
        $label_counts = [];

        foreach ($orders as $order) {
            foreach ($order->get_items() as $item) {
                $product_id = $item->get_product_id();
                $artists = wp_get_object_terms($product_id, 'musicartist', ['fields' => 'names']);
                $labels = wp_get_object_terms($product_id, 'musiclabel', ['fields' => 'names']);
                $styles = wp_get_object_terms($product_id, 'musicstyle', ['fields' => 'names']);
                foreach ($artists as $a) $artist_counts[$a] = ($artist_counts[$a] ?? 0) + 1;
                foreach ($labels as $l) $label_counts[$l] = ($label_counts[$l] ?? 0) + 1;
                foreach ($styles as $s) $genre_counts[$s] = ($genre_counts[$s] ?? 0) + 1;
            }
        }

        arsort($genre_counts);
        arsort($artist_counts);
        arsort($label_counts);

        // Tier
        $tier = 'standard';
        if ($total_spent >= 2000) $tier = 'platinum';
        elseif ($total_spent >= 1000) $tier = 'gold';
        elseif ($total_spent >= 500) $tier = 'black';

        return [
            'name' => $customer->get_display_name(),
            'email' => $customer->get_email(),
            'tier' => $tier,
            'order_count' => count($orders),
            'lifetime_value' => round($total_spent, 2),
            'top_genres' => array_slice($genre_counts, 0, 10, true),
            'top_artists' => array_slice($artist_counts, 0, 10, true),
            'top_labels' => array_slice($label_counts, 0, 10, true),
        ];
    }

    public function get_orders($request) {
        $user_id = $request->get_param('_dw_user_id');
        $limit = min(intval($request->get_param('limit') ?: 50), 100);

        $orders = wc_get_orders([
            'customer_id' => $user_id,
            'limit' => $limit,
            'status' => ['completed', 'processing'],
            'orderby' => 'date',
            'order' => 'DESC',
        ]);

        $results = [];
        foreach ($orders as $order) {
            $items = [];
            foreach ($order->get_items() as $item) {
                $product = $item->get_product();
                if (!$product) continue;

                $discogs_id = $product->get_meta('_discogs_release_id');
                $artists = wp_get_object_terms($product->get_id(), 'musicartist', ['fields' => 'names']);
                $labels = wp_get_object_terms($product->get_id(), 'musiclabel', ['fields' => 'names']);

                $items[] = [
                    'name' => $product->get_name(),
                    'sku' => $product->get_sku(),
                    'artist' => implode(', ', $artists),
                    'label' => implode(', ', $labels),
                    'discogs_id' => $discogs_id ?: null,
                    'image' => wp_get_attachment_url($product->get_image_id()),
                ];
            }

            $results[] = [
                'id' => $order->get_id(),
                'date' => $order->get_date_created()->format('Y-m-d'),
                'total' => $order->get_total(),
                'currency' => $order->get_currency(),
                'item_count' => count($items),
                'items' => $items,
            ];
        }

        return ['orders' => $results, 'total' => count($results)];
    }

    public function get_feed($request) {
        $user_id = $request->get_param('_dw_user_id');
        $limit = min(intval($request->get_param('limit') ?: 20), 50);

        // Get products from "Arrivals" category, enriched with Discogs IDs
        $args = [
            'limit' => $limit,
            'status' => 'publish',
            'stock_status' => 'instock',
            'category' => ['arrivals'],
            'orderby' => 'date',
            'order' => 'DESC',
        ];

        $products = wc_get_products($args);
        $results = [];

        foreach ($products as $product) {
            $discogs_id = $product->get_meta('_discogs_release_id');
            $artists = wp_get_object_terms($product->get_id(), 'musicartist', ['fields' => 'names']);
            $labels = wp_get_object_terms($product->get_id(), 'musiclabel', ['fields' => 'names']);
            $styles = wp_get_object_terms($product->get_id(), 'musicstyle', ['fields' => 'names']);

            $results[] = [
                'id' => $product->get_id(),
                'name' => $product->get_name(),
                'sku' => $product->get_sku(),
                'price' => $product->get_price(),
                'artist' => implode(', ', $artists),
                'label' => implode(', ', $labels),
                'styles' => $styles,
                'discogs_id' => $discogs_id ?: null,
                'url' => $product->get_permalink(),
                'image' => wp_get_attachment_url($product->get_image_id()),
            ];
        }

        return ['products' => $results, 'total' => count($results)];
    }
}
```

- [ ] **Step 6: Register endpoint in YIO**

Add to `~/repos/yio/yio.php` after the other API class instantiations:

```php
require_once __DIR__ . '/includes/api/class-yio-discoworld-endpoint.php';
new YIO_DiscoWorld_Endpoint();
```

- [ ] **Step 7: Create GitHub private repo**

```bash
cd ~/repos/discoworld-yoyaku
git add -A
git commit -m "Initial: YOYAKU private integration for DiscoWorld"
gh repo create benjaminbelaga/discoworld-yoyaku --private --source=. --push
```

- [ ] **Step 8: Deploy YIO endpoint to production**

```bash
cd ~/repos/yio
# Add, commit, deploy the new endpoint via standard YIO deploy process
```

---

### Task 3: Immersive 3D World — Buildings on GenreWorld (Default View)

**Files:**
- Create: `packages/web/src/components/GenreWorldBuildings.jsx`
- Modify: `packages/web/src/components/GenreWorld.jsx`
- Modify: `packages/web/src/lib/buildingGenerator.js`

Currently buildings only appear on GenrePlanet (the globe). The default GenreWorld (flat plane) has no buildings — just colored spheres. This task adds instanced buildings to GenreWorld.

- [ ] **Step 1: Add flat-plane building generation to buildingGenerator.js**

Add to `packages/web/src/lib/buildingGenerator.js` after the existing `generateBuildings` function:

```js
/**
 * Generate buildings for GenreWorld flat-plane layout.
 * Buildings are positioned around genre center (x, z) coordinates.
 * @param {Object} genre — genre object with {x, z, biome, scene, trackCount, slug}
 * @param {number} seed — deterministic seed
 * @returns {Array} building configs with world-space positions
 */
export function generateGenreBuildings(genre, seed) {
  const biomeKey = BIOME_MAPPING[genre.biome] || 'techno'
  const style = BIOME_STYLES[biomeKey] || BIOME_STYLES.techno
  const rng = mulberry32(seed)

  // More tracks = more buildings (3 to 15)
  const count = Math.min(15, Math.max(3, Math.floor((genre.trackCount || 5) / 3)))
  const buildings = []

  // Scale factor for GenreWorld (smaller than GenrePlanet)
  const SCALE = 0.3

  for (let i = 0; i < count; i++) {
    const archetype = style.archetypes[Math.floor(rng() * style.archetypes.length)]
    const height = lerp(archetype.heightRange[0], archetype.heightRange[1], rng()) * SCALE
    const width = lerp(archetype.widthRange[0], archetype.widthRange[1], rng()) * SCALE
    const depth = lerp(archetype.widthRange[0], archetype.widthRange[1], rng()) * SCALE

    // Spread around genre center
    const angle = rng() * Math.PI * 2
    const radius = Math.sqrt(rng()) * 2.0
    const ox = genre.x + Math.cos(angle) * radius
    const oz = genre.z + Math.sin(angle) * radius
    const oy = -2 + height / 2  // Ground level is Y=-2 in GenreWorld

    buildings.push({
      position: [ox, oy, oz],
      rotation: [0, rng() * Math.PI * 2, 0],
      scale: [width, height, depth],
      geometry: archetype.type,
      color: style.color,
      emissiveColor: style.emissiveColor,
    })
  }

  return buildings
}
```

- [ ] **Step 2: Create GenreWorldBuildings component**

Create `packages/web/src/components/GenreWorldBuildings.jsx`:

```jsx
import { useRef, useMemo, useEffect } from 'react'
import * as THREE from 'three'
import { generateGenreBuildings } from '../lib/buildingGenerator'

const _obj = new THREE.Object3D()
const _color = new THREE.Color()

const MAX_BOXES = 2000
const MAX_CYLINDERS = 500
const MAX_CONES = 500

/**
 * Instanced buildings for the GenreWorld flat-plane view.
 * One InstancedMesh per geometry type for draw call efficiency.
 */
export default function GenreWorldBuildings({ genres }) {
  const boxRef = useRef()
  const cylRef = useRef()
  const coneRef = useRef()

  const allBuildings = useMemo(() => {
    if (!genres || genres.length === 0) return { box: [], cylinder: [], cone: [] }

    const boxes = []
    const cylinders = []
    const cones = []

    genres.forEach((genre, gi) => {
      const buildings = generateGenreBuildings(genre, gi * 1337 + 42)
      buildings.forEach(b => {
        const target = b.geometry === 'cylinder' ? cylinders : b.geometry === 'cone' ? cones : boxes
        target.push(b)
      })
    })

    return {
      box: boxes.slice(0, MAX_BOXES),
      cylinder: cylinders.slice(0, MAX_CYLINDERS),
      cone: cones.slice(0, MAX_CONES),
    }
  }, [genres])

  useEffect(() => {
    function updateMesh(ref, buildings) {
      if (!ref.current || buildings.length === 0) return
      buildings.forEach((b, i) => {
        _obj.position.set(...b.position)
        _obj.rotation.set(...b.rotation)
        _obj.scale.set(...b.scale)
        _obj.updateMatrix()
        ref.current.setMatrixAt(i, _obj.matrix)
        _color.set(b.emissiveColor)
        ref.current.setColorAt(i, _color)
      })
      ref.current.instanceMatrix.needsUpdate = true
      if (ref.current.instanceColor) ref.current.instanceColor.needsUpdate = true
      ref.current.count = buildings.length
    }

    updateMesh(boxRef, allBuildings.box)
    updateMesh(cylRef, allBuildings.cylinder)
    updateMesh(coneRef, allBuildings.cone)
  }, [allBuildings])

  return (
    <group>
      <instancedMesh ref={boxRef} args={[undefined, undefined, MAX_BOXES]} frustumCulled={false}>
        <boxGeometry args={[1, 1, 1]} />
        <meshStandardMaterial
          color="#1a1a2e"
          roughness={0.7}
          metalness={0.3}
          emissive="#000000"
          emissiveIntensity={0.5}
          toneMapped={false}
        />
      </instancedMesh>
      <instancedMesh ref={cylRef} args={[undefined, undefined, MAX_CYLINDERS]} frustumCulled={false}>
        <cylinderGeometry args={[0.5, 0.5, 1, 8]} />
        <meshStandardMaterial
          color="#1a1a2e"
          roughness={0.7}
          metalness={0.3}
          emissive="#000000"
          emissiveIntensity={0.5}
          toneMapped={false}
        />
      </instancedMesh>
      <instancedMesh ref={coneRef} args={[undefined, undefined, MAX_CONES]} frustumCulled={false}>
        <coneGeometry args={[0.5, 1, 6]} />
        <meshStandardMaterial
          color="#1a1a2e"
          roughness={0.7}
          metalness={0.3}
          emissive="#000000"
          emissiveIntensity={0.5}
          toneMapped={false}
        />
      </instancedMesh>
    </group>
  )
}
```

- [ ] **Step 3: Integrate buildings into GenreWorld Scene**

In `packages/web/src/components/GenreWorld.jsx`, add to the `Scene` function:

```jsx
import GenreWorldBuildings from './GenreWorldBuildings'

// Inside Scene component, after <GenreInstances> and before </group>:
<GenreWorldBuildings genres={genres} />
```

- [ ] **Step 4: Build and verify**

```bash
cd ~/repos/discoworld/packages/web
source ~/.nvm/nvm.sh && nvm use 20
npm run build
```

Expected: Build succeeds, no errors.

- [ ] **Step 5: Commit**

```bash
git add packages/web/src/components/GenreWorldBuildings.jsx packages/web/src/components/GenreWorld.jsx packages/web/src/lib/buildingGenerator.js
git commit -m "feat: instanced buildings on GenreWorld — Minecraft-inspired genre architecture"
```

---

### Task 4: Enhanced Terrain — Fog, Atmosphere, Biome Colors

**Files:**
- Modify: `packages/web/src/components/GenreWorld.jsx` (Scene function)
- Create: `packages/web/src/lib/terrainColors.js`

- [ ] **Step 1: Create terrain color palette**

Create `packages/web/src/lib/terrainColors.js`:

```js
/**
 * Biome-specific terrain colors for the GenreWorld ground plane.
 * Matched to each biome's visual identity.
 */
export const TERRAIN_COLORS = {
  'techno-massif': { ground: '#0a0a12', fog: '#050510', ambient: '#1a1a3a' },
  'house-plains': { ground: '#12100a', fog: '#0a0805', ambient: '#2a2010' },
  'disco-riviera': { ground: '#100810', fog: '#080508', ambient: '#201530' },
  'ambient-depths': { ground: '#050a14', fog: '#030510', ambient: '#102030' },
  'jungle-canopy': { ground: '#081008', fog: '#040804', ambient: '#102a10' },
  'trance-highlands': { ground: '#080820', fog: '#040410', ambient: '#151050' },
  'industrial-wasteland': { ground: '#0a0a0a', fog: '#050505', ambient: '#1a1515' },
  'idm-crystalline': { ground: '#080a14', fog: '#040510', ambient: '#101530' },
  'dubstep-rift': { ground: '#0a0510', fog: '#050308', ambient: '#150a20' },
  'garage-district': { ground: '#100a08', fog: '#080504', ambient: '#201510' },
  'urban-quarter': { ground: '#0a0a08', fog: '#050504', ambient: '#151510' },
  'source-monuments': { ground: '#0a0a06', fog: '#050503', ambient: '#1a1a10' },
}

export const DEFAULT_TERRAIN = { ground: '#0a0a0e', fog: '#050508', ambient: '#1a1a2e' }
```

- [ ] **Step 2: Add fog + atmosphere to GenreWorld Scene**

In `packages/web/src/components/GenreWorld.jsx`, inside the `Scene` function, add after the opening `<group>`:

```jsx
import { TERRAIN_COLORS, DEFAULT_TERRAIN } from '../lib/terrainColors'

// Inside Scene, add fog:
<fog attach="fog" args={['#050508', 60, 200]} />

// Enhance the existing ambient light:
<ambientLight intensity={0.15} color="#8888cc" />
```

- [ ] **Step 3: Add ground particles for atmosphere**

Already exists as `AmbientDust` component in GenreWorld.jsx — verify it's rendered in the Scene. If not, add:

```jsx
<AmbientDust genres={genres} />
```

- [ ] **Step 4: Build and verify**

```bash
cd ~/repos/discoworld/packages/web && npm run build
```

- [ ] **Step 5: Commit**

```bash
git add packages/web/src/lib/terrainColors.js packages/web/src/components/GenreWorld.jsx
git commit -m "feat: enhanced terrain — fog, atmosphere, biome color palettes"
```

---

### Task 5: Deploy + Final Verification

**Files:**
- Modify: production deployment

- [ ] **Step 1: Run full test suite**

```bash
cd ~/repos/discoworld
python3 -m pytest packages/api/tests/ -q
cd packages/web && npx vitest run --reporter=dot && npm run build
```

Expected: All tests pass, build succeeds.

- [ ] **Step 2: Deploy to production**

```bash
cd ~/repos/discoworld
rsync -avz --exclude='__pycache__' --exclude='tests/' packages/api/ yoyaku-server:/var/www/world.yoyaku.io/packages/api/
rsync -avz --exclude='data/' packages/web/dist/ yoyaku-server:/var/www/world.yoyaku.io/
rsync -avz packages/web/public/data/ yoyaku-server:/var/www/world.yoyaku.io/data/
ssh yoyaku-server "pm2 restart discoworld-api"
```

- [ ] **Step 3: Verify production**

```bash
curl -s https://world.yoyaku.io/api/health
curl -s https://world.yoyaku.io/ | grep '<title>'
```

- [ ] **Step 4: Push to public GitHub (single commit after squash)**

Only if Task 1 was completed:

```bash
cd ~/repos/discoworld
git push origin main
```

---

## Execution Order

| # | Task | Depends On | Risk |
|---|------|-----------|------|
| 1 | Git squash | None | HIGH (destructive) |
| 2 | Private YOYAKU repo | None | LOW |
| 3 | Buildings on GenreWorld | None | LOW |
| 4 | Terrain enhancement | None | LOW |
| 5 | Deploy + verify | 1, 3, 4 | MEDIUM |

Tasks 2, 3, 4 are fully independent and can run in parallel.
Task 1 (git squash) requires user confirmation before force-push.
Task 5 depends on everything else completing.
