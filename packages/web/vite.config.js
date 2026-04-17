import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg', 'icons/*.svg'],
      manifest: {
        name: 'DiscoWorld — Non-Linear Musical Exploration',
        short_name: 'DiscoWorld',
        description: 'Explore 4.8 million electronic music releases on an interactive 3D map.',
        theme_color: '#0a0a0f',
        background_color: '#0a0a0f',
        display: 'standalone',
        orientation: 'any',
        start_url: '/',
        scope: '/',
        categories: ['music', 'entertainment', 'education'],
        icons: [
          {
            src: '/icons/icon-192.svg',
            sizes: '192x192',
            type: 'image/svg+xml',
            purpose: 'any'
          },
          {
            src: '/icons/icon-512.svg',
            sizes: '512x512',
            type: 'image/svg+xml',
            purpose: 'any'
          },
          {
            src: '/icons/icon-512.svg',
            sizes: '512x512',
            type: 'image/svg+xml',
            purpose: 'maskable'
          }
        ]
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,svg,woff,woff2}'],
        // Precache world.json (large but essential for offline)
        additionalManifestEntries: [
          { url: '/data/world.json', revision: null },
          { url: '/data/cities.json', revision: null }
        ],
        maximumFileSizeToCacheInBytes: 5 * 1024 * 1024, // 5MB for world.json
        runtimeCaching: [
          {
            // YouTube / external API calls — network first, fall back to cache
            urlPattern: /^https:\/\/(www\.googleapis\.com|i\.ytimg\.com|img\.youtube\.com)/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60 * 24 // 24 hours
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },
          {
            // Google Fonts
            urlPattern: /^https:\/\/fonts\.(googleapis|gstatic)\.com/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'google-fonts',
              expiration: {
                maxEntries: 20,
                maxAgeSeconds: 60 * 60 * 24 * 365 // 1 year
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },
          {
            // CDN assets (three.js examples, etc.)
            urlPattern: /^https:\/\/cdn\./,
            handler: 'CacheFirst',
            options: {
              cacheName: 'cdn-cache',
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 60 * 60 * 24 * 30 // 30 days
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          }
        ]
      }
    })
  ],
  server: {
    proxy: {
      '/api': 'http://localhost:8787',
    },
  },
  preview: {
    proxy: {
      '/api': 'http://localhost:8787',
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test-setup.js',
    css: true,
    exclude: ['e2e/**', 'node_modules/**'],
  },
  build: {
    // Exclude postfx from modulepreload — it's desktop-only and lazy-loaded
    // via React.lazy() in App.jsx, so preloading forces mobile to download
    // ~397 KB gzip it will never execute (audit 2026-04-17 AGENT-E).
    modulePreload: {
      resolveDependencies: (_filename, deps) => deps.filter((d) => !d.includes('postfx-')),
    },
    rollupOptions: {
      output: {
        manualChunks(id) {
          // React core
          if (id.includes('node_modules/react/') || id.includes('node_modules/react-dom/') || id.includes('node_modules/scheduler/')) return 'react-vendor'
          // Globe view (earth mode) — isolates globe.gl's huge d3/topojson/three-globe deps
          if (id.includes('globe.gl') || id.includes('three-globe') || id.includes('topojson-client')) return 'globe'
          if (id.includes('/d3-') || id.match(/node_modules\/d3-[a-z]+/)) return 'globe'
          // Three.js core + ecosystem — shared between earth and genre views
          if (
            id.includes('node_modules/three/') ||
            id.includes('three-stdlib') ||
            id.includes('three-mesh-bvh') ||
            id.includes('three-conic-polygon') ||
            id.includes('three-geojson-geometry') ||
            id.includes('three-render-objects') ||
            id.includes('troika-')
          ) return 'three'
          // R3F
          if (id.includes('@react-three/fiber') || id.includes('@react-three/drei')) return 'r3f'
          // Postprocessing (pmndrs) — only needed on desktop bloom
          if (id.includes('@react-three/postprocessing') || id.includes('node_modules/postprocessing/')) return 'postfx'
          // gsap / maath — animation helpers
          if (id.includes('node_modules/gsap/') || id.includes('node_modules/maath/')) return 'anim'
          // zustand — tiny, keep in main bundle
        }
      }
    }
  }
})
