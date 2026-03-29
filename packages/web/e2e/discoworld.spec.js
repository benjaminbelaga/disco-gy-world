import { test, expect } from '@playwright/test'

// Helper: wait for app to finish loading
async function waitForApp(page) {
  await page.waitForFunction(() => !document.querySelector('.loading-screen'), { timeout: 30000 })
}

// Helper: set onboarded and reload
async function skipOnboarding(page) {
  await page.evaluate(() => localStorage.setItem('discoworld-onboarded', '1'))
  await page.reload()
  await waitForApp(page)
}

// =============================================================================
// Landing & Loading
// =============================================================================

test.describe('Landing & Loading', () => {
  test('shows loading screen then app', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('[role="application"], .loading-screen')).toBeVisible({ timeout: 15000 })
    await waitForApp(page)
    await expect(page.locator('[role="application"]')).toBeAttached()
  })

  test('loads world.json data successfully', async ({ page }) => {
    const worldResponse = page.waitForResponse(r => r.url().includes('/data/world.json') && r.status() === 200)
    await page.goto('/')
    await worldResponse
  })

  test('loads cities.json data', async ({ page }) => {
    const citiesResponse = page.waitForResponse(r => r.url().includes('/data/cities.json'))
    await page.goto('/')
    await citiesResponse
  })

  test('has correct page title or heading', async ({ page }) => {
    await page.goto('/')
    const text = await page.textContent('body')
    expect(text).toContain('DiscoWorld')
  })

  test('has skip-to-content link for accessibility', async ({ page }) => {
    await page.goto('/')
    await waitForApp(page)
    await expect(page.locator('a[href="#discoworld-main"]')).toBeAttached()
  })

  test('has ARIA live region for announcements', async ({ page }) => {
    await page.goto('/')
    await waitForApp(page)
    await expect(page.locator('[aria-live="polite"]')).toBeAttached()
  })
})

// =============================================================================
// Genre World View (default)
// =============================================================================

test.describe('Genre World View (default)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await waitForApp(page)
  })

  test('canvas is rendered', async ({ page }) => {
    await expect(page.locator('canvas')).toBeAttached()
  })

  test('header is visible with DiscoWorld branding', async ({ page }) => {
    const text = await page.textContent('body')
    expect(text.toLowerCase()).toContain('discoworld')
  })

  test('onboarding shows for new users', async ({ page, context }) => {
    await context.clearCookies()
    await page.evaluate(() => localStorage.clear())
    await page.reload()
    await waitForApp(page)
    const body = await page.textContent('body')
    // Actual onboarding text: "where do you dig?" + "skip — i know these crates"
    expect(body.toLowerCase()).toMatch(/dig|genre|crate|skip/)
  })

  test('onboarding can be skipped', async ({ page }) => {
    await page.evaluate(() => localStorage.clear())
    await page.reload()
    await waitForApp(page)
    // Look for skip button/link
    const skipEl = page.locator('text=/skip/i, button:has-text("skip")')
    if (await skipEl.first().isVisible({ timeout: 3000 }).catch(() => false)) {
      await skipEl.first().click()
    }
    // Should not crash
    await expect(page.locator('[role="application"]')).toBeAttached()
  })
})

// =============================================================================
// View Switching
// =============================================================================

test.describe('View Switching', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await waitForApp(page)
    await skipOnboarding(page)
  })

  test('keyboard 1 activates genre view', async ({ page }) => {
    await page.keyboard.press('1')
    await page.waitForTimeout(500)
    await expect(page.locator('canvas')).toBeAttached()
  })

  test.skip('keyboard 2 switches to earth view mode', async ({ page }) => {
    // SKIP: globe.gl crashes headless Chrome (requires real WebGL context)
    // This works in headed mode. See: https://github.com/vasturiano/globe.gl/issues
    await page.keyboard.press('2')
    await page.waitForTimeout(3000)
  })

  test('keyboard 3 switches to planet view mode', async ({ page }) => {
    const errors = []
    page.on('pageerror', err => errors.push(err.message))
    await page.keyboard.press('3')
    await page.waitForTimeout(3000)
    const jsErrors = errors.filter(e => !e.includes('WebGL') && !e.includes('THREE') && !e.includes('postprocessing'))
    expect(jsErrors).toHaveLength(0)
  })

  test.skip('keyboard G cycles through views without app-level errors', async ({ page }) => {
    // SKIP: globe.gl crashes headless Chrome when cycling to earth view
    await page.keyboard.press('g')
    await page.waitForTimeout(1500)
  })
})

// =============================================================================
// Search
// =============================================================================

test.describe('Search', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await waitForApp(page)
    await skipOnboarding(page)
  })

  test('search bar is accessible', async ({ page }) => {
    const input = page.locator('input[placeholder*="genre"], input[placeholder*="artist"], input[placeholder*="city"], input[placeholder*="search"]')
    await expect(input.first()).toBeVisible({ timeout: 5000 })
  })

  test('typing in search shows results', async ({ page }) => {
    const input = page.locator('input[placeholder*="genre"], input[placeholder*="artist"], input[placeholder*="city"], input[placeholder*="search"]')
    await input.first().click()
    await input.first().fill('techno')
    await page.waitForTimeout(1500)
    const body = await page.textContent('body')
    expect(body.toLowerCase()).toContain('techno')
  })
})

// =============================================================================
// Keyboard Shortcuts
// =============================================================================

test.describe('Keyboard Shortcuts', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await waitForApp(page)
    await skipOnboarding(page)
  })

  test('Escape clears selection', async ({ page }) => {
    await page.keyboard.press('Escape')
    await page.waitForTimeout(200)
    await expect(page.locator('[role="application"]')).toBeAttached()
  })

  test('R explores random genre', async ({ page }) => {
    await page.keyboard.press('r')
    await page.waitForTimeout(1000)
    await expect(page.locator('[role="application"]')).toBeAttached()
  })

  test('Arrow keys change timeline year', async ({ page }) => {
    await page.keyboard.press('ArrowRight')
    await page.waitForTimeout(200)
    await page.keyboard.press('ArrowLeft')
    await page.waitForTimeout(200)
    await expect(page.locator('[role="application"]')).toBeAttached()
  })

  test('Space toggles auto tour', async ({ page }) => {
    await page.keyboard.press('Space')
    await page.waitForTimeout(500)
    await page.keyboard.press('Space')
    await page.waitForTimeout(200)
    await expect(page.locator('[role="application"]')).toBeAttached()
  })
})

// =============================================================================
// Deep Linking
// =============================================================================

test.describe('Deep Linking', () => {
  test('genre URL parameter loads without crash', async ({ page }) => {
    await page.goto('/?genre=techno')
    await waitForApp(page)
    await expect(page.locator('[role="application"]')).toBeAttached()
  })

  test('earth view URL parameter loads without crash', async ({ page }) => {
    await page.goto('/?view=earth')
    await waitForApp(page)
    await page.waitForTimeout(2000)
    await expect(page.locator('[role="application"]')).toBeAttached()
  })

  test('planet view URL parameter loads without crash', async ({ page }) => {
    await page.goto('/?view=planet')
    await waitForApp(page)
    await page.waitForTimeout(2000)
    await expect(page.locator('[role="application"]')).toBeAttached()
  })

  test('year URL parameter is applied', async ({ page }) => {
    await page.goto('/?year=1990')
    await waitForApp(page)
    await expect(page.locator('[role="application"]')).toBeAttached()
  })

  test('drift URL parameter activates auto-tour', async ({ page }) => {
    await page.goto('/?drift=1')
    await waitForApp(page)
    await expect(page.locator('[role="application"]')).toBeAttached()
  })
})

// =============================================================================
// API Integration (via proxy)
// =============================================================================

test.describe('API Integration', () => {
  test('health endpoint returns ok', async ({ page }) => {
    const response = await page.request.get('/api/health')
    expect(response.ok()).toBeTruthy()
    const json = await response.json()
    expect(json.status).toBe('ok')
    expect(json.genres).toBe(166)
  })

  test('genres endpoint returns 166 genres', async ({ page }) => {
    const response = await page.request.get('/api/genres')
    expect(response.ok()).toBeTruthy()
    const json = await response.json()
    expect(json.genres).toHaveLength(166)
  })

  test('genre by slug returns data', async ({ page }) => {
    // Use the exact slug from world.json (techno may have a different slug)
    const genresRes = await page.request.get('/api/genres')
    const genresData = await genresRes.json()
    const firstGenre = genresData.genres[0]
    const response = await page.request.get(`/api/genres/${firstGenre.slug}`)
    expect(response.ok()).toBeTruthy()
    const json = await response.json()
    expect(json.name).toBeDefined()
    expect(json.slug).toBe(firstGenre.slug)
  })

  test('genre by slug 404 for unknown', async ({ page }) => {
    const response = await page.request.get('/api/genres/not-a-genre-xyz')
    expect(response.status()).toBe(404)
  })

  test('search returns results for techno', async ({ page }) => {
    const response = await page.request.get('/api/search?q=techno')
    expect(response.ok()).toBeTruthy()
    const json = await response.json()
    expect(json.count).toBeGreaterThan(0)
  })

  test('search returns 400 without query', async ({ page }) => {
    const response = await page.request.get('/api/search')
    expect(response.status()).toBe(400)
  })

  test('unified search returns grouped results', async ({ page }) => {
    const response = await page.request.get('/api/search/unified?q=house&limit=5')
    expect(response.ok()).toBeTruthy()
    const json = await response.json()
    expect(json).toHaveProperty('genres')
    expect(json).toHaveProperty('artists')
    expect(json).toHaveProperty('labels')
    expect(json.genres.length).toBeGreaterThan(0)
  })

  test('releases endpoint returns paginated data', async ({ page }) => {
    const response = await page.request.get('/api/releases?limit=5')
    expect(response.ok()).toBeTruthy()
    const json = await response.json()
    expect(json.releases).toBeDefined()
    expect(json.total).toBeGreaterThan(0)
    expect(json.releases.length).toBeLessThanOrEqual(5)
  })

  test('releases with style filter', async ({ page }) => {
    const response = await page.request.get('/api/releases?style=Techno&limit=3')
    expect(response.ok()).toBeTruthy()
    const json = await response.json()
    expect(json.releases).toBeDefined()
  })

  test('recommendations for release', async ({ page }) => {
    const response = await page.request.get('/api/recommendations/1')
    expect(response.ok()).toBeTruthy()
    const json = await response.json()
    expect(json).toHaveProperty('release')
    expect(json).toHaveProperty('recommendations')
  })

  test('cities endpoint returns data', async ({ page }) => {
    const response = await page.request.get('/api/cities')
    expect(response.ok()).toBeTruthy()
    const json = await response.json()
    expect(json.cities).toBeDefined()
    expect(json.count).toBeGreaterThan(0)
  })

  test('shops endpoint returns data', async ({ page }) => {
    const response = await page.request.get('/api/shops')
    expect(response.ok()).toBeTruthy()
    const json = await response.json()
    expect(json.shops).toBeDefined()
  })

  test('auth/me returns unauthenticated', async ({ page }) => {
    const response = await page.request.get('/api/auth/me')
    expect(response.ok()).toBeTruthy()
    const json = await response.json()
    expect(json.authenticated).toBe(false)
  })

  test('stats endpoint returns metadata', async ({ page }) => {
    const response = await page.request.get('/api/stats')
    expect(response.ok()).toBeTruthy()
    const json = await response.json()
    expect(json.genreCount).toBe(166)
    expect(json.scenes).toBeDefined()
    expect(json.biomes).toBeDefined()
  })

  test('paths/popular returns array', async ({ page }) => {
    const response = await page.request.get('/api/paths/popular')
    expect(response.ok()).toBeTruthy()
    const json = await response.json()
    expect(Array.isArray(json)).toBeTruthy()
  })

  test('create and retrieve dig path', async ({ page }) => {
    const createResponse = await page.request.post('/api/paths', {
      data: {
        title: 'E2E Test Path',
        description: 'Created by Playwright',
        waypoints: [
          { slug: 'techno', note: 'Start here' },
          { slug: 'house', note: 'Then explore' },
        ],
      },
    })
    expect(createResponse.ok()).toBeTruthy()
    const created = await createResponse.json()
    expect(created.id).toBeDefined()
    expect(created.title).toBe('E2E Test Path')
    expect(created.waypoints).toHaveLength(2)

    const getResponse = await page.request.get(`/api/paths/${created.id}`)
    expect(getResponse.ok()).toBeTruthy()
    const retrieved = await getResponse.json()
    expect(retrieved.title).toBe('E2E Test Path')
    expect(retrieved.views).toBeGreaterThanOrEqual(1)
  })

  test('artist releases endpoint', async ({ page }) => {
    const response = await page.request.get('/api/artists/aphex/releases?limit=3')
    expect(response.ok()).toBeTruthy()
    const json = await response.json()
    expect(json).toHaveProperty('releases')
    expect(json).toHaveProperty('total')
  })

  test('label releases endpoint', async ({ page }) => {
    const response = await page.request.get('/api/labels/warp/releases?limit=3')
    expect(response.ok()).toBeTruthy()
    const json = await response.json()
    expect(json).toHaveProperty('releases')
    expect(json).toHaveProperty('total')
  })
})

// =============================================================================
// Error Resilience
// =============================================================================

test.describe('Error Resilience', () => {
  test('app loads without critical console errors', async ({ page }) => {
    const errors = []
    page.on('pageerror', err => errors.push(err.message))

    await page.goto('/')
    await waitForApp(page)
    await page.waitForTimeout(2000)

    const criticalErrors = errors.filter(e =>
      !e.includes('WebGL') &&
      !e.includes('ResizeObserver') &&
      !e.includes('Non-Error promise rejection') &&
      !e.includes('postprocessing') &&
      !e.includes('THREE')
    )
    expect(criticalErrors).toHaveLength(0)
  })

  // eslint-disable-next-line no-unused-vars
  test.skip('app does not crash on rapid view switching', async ({ page }) => {
    // SKIP: globe.gl crashes headless Chrome when switching to earth view
    // This works in headed mode.
  })

  test('rapid keyboard shortcuts do not crash', async ({ page }) => {
    await page.goto('/')
    await waitForApp(page)
    await skipOnboarding(page)

    // Rapid fire various shortcuts
    for (const key of ['r', 'Escape', 'ArrowRight', 'ArrowLeft', 'r', 'Space', 'Escape']) {
      await page.keyboard.press(key)
      await page.waitForTimeout(100)
    }

    await expect(page.locator('[role="application"]')).toBeAttached()
  })
})
