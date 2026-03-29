import { useEffect, useRef, useCallback } from 'react'
import Globe from 'globe.gl'
import * as THREE from 'three'
import { feature } from 'topojson-client'
import { addAtmosphere } from './GlobeAtmosphere'
import { addStarfield } from './GlobeStarfield'
import { setupBloom } from './GlobeBloom'
import useStore from '../stores/useStore'
import './EarthGlobe.css'

// NASA Blue Marble textures (bundled with three-globe)
const TEXTURES = {
  globe: '//unpkg.com/three-globe/example/img/earth-blue-marble.jpg',
  night: '//unpkg.com/three-globe/example/img/earth-night.jpg',
  bump: '//unpkg.com/three-globe/example/img/earth-topology.png',
  water: '//unpkg.com/three-globe/example/img/earth-water.png',
  sky: '//unpkg.com/three-globe/example/img/night-sky.png',
}

// Low-res country borders (Natural Earth 110m via three-globe examples)
const COUNTRY_BORDERS_URL = '//unpkg.com/world-atlas@2/countries-110m.json'

// Format genre tag for display
function formatGenre(genre) {
  return genre.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

// Build a city HTML marker element using safe DOM methods
function createCityMarker(city, selectedCityId) {
  const el = document.createElement('div')
  el.className = 'city-marker'
  if (selectedCityId === city.id) el.classList.add('selected')

  const maxCount = 262800 // London = largest
  const minSize = 6
  const maxSize = 22
  const ratio = Math.sqrt(city.release_count / maxCount)
  const size = minSize + ratio * (maxSize - minSize)

  // Dot container
  const dot = document.createElement('div')
  dot.className = 'city-dot'
  dot.style.width = size + 'px'
  dot.style.height = size + 'px'

  const core = document.createElement('div')
  core.className = 'city-dot-core'
  dot.appendChild(core)

  // Outer pulsing ring
  const ring = document.createElement('div')
  ring.className = 'city-dot-ring'
  dot.appendChild(ring)

  // Second pulse ring (delayed) for premium effect
  const ring2 = document.createElement('div')
  ring2.className = 'city-dot-ring city-dot-ring-delayed'
  dot.appendChild(ring2)

  // Tooltip with city name + genre tags
  const tooltip = document.createElement('div')
  tooltip.className = 'city-tooltip'

  const tooltipName = document.createElement('div')
  tooltipName.className = 'city-tooltip-name'
  tooltipName.textContent = city.name
  tooltip.appendChild(tooltipName)

  const tooltipMeta = document.createElement('div')
  tooltipMeta.className = 'city-tooltip-meta'
  tooltipMeta.textContent = `${(city.release_count / 1000).toFixed(0)}k releases`
  tooltip.appendChild(tooltipMeta)

  if (city.genres && city.genres.length > 0) {
    const tagsRow = document.createElement('div')
    tagsRow.className = 'city-tooltip-tags'
    city.genres.slice(0, 3).forEach(g => {
      const tag = document.createElement('span')
      tag.className = 'city-tooltip-tag'
      tag.textContent = formatGenre(g)
      tagsRow.appendChild(tag)
    })
    tooltip.appendChild(tagsRow)
  }

  // Label (minimal, shown always)
  const label = document.createElement('div')
  label.className = 'city-label'
  label.textContent = city.name

  el.appendChild(dot)
  el.appendChild(tooltip)
  el.appendChild(label)

  el.addEventListener('mouseenter', () => el.classList.add('hovered'))
  el.addEventListener('mouseleave', () => el.classList.remove('hovered'))

  return el
}

// Resolve arcs from arcs.json using city id lookups
function resolveArcs(arcsJson, citiesById) {
  const resolved = []

  const processArc = (arc, type) => {
    const from = citiesById[arc.from]
    const to = citiesById[arc.to]
    if (!from || !to) return
    resolved.push({
      startLat: from.lat,
      startLng: from.lng,
      endLat: to.lat,
      endLng: to.lng,
      fromId: arc.from,
      toId: arc.to,
      genre: arc.genre,
      weight: arc.weight || arc.flow_strength || 0.5,
      label: arc.label || '',
      type,
    })
  }

  if (arcsJson.label_arcs) {
    arcsJson.label_arcs.forEach(a => processArc(a, 'label'))
  }
  if (arcsJson.genre_flows) {
    arcsJson.genre_flows.forEach(a => processArc(a, 'genre'))
  }
  return resolved
}

// Country ISO2 → approximate centroid for collection markers
const COUNTRY_COORDS = {
  DE: { lat: 51.2, lng: 10.4 }, GB: { lat: 51.5, lng: -0.1 }, US: { lat: 39.8, lng: -98.6 },
  FR: { lat: 46.2, lng: 2.2 }, SE: { lat: 62.0, lng: 15.0 }, BE: { lat: 50.5, lng: 4.5 },
  NL: { lat: 52.1, lng: 5.3 }, IT: { lat: 41.9, lng: 12.5 }, JP: { lat: 36.2, lng: 138.3 },
  AU: { lat: -25.3, lng: 133.8 }, CA: { lat: 56.1, lng: -106.3 }, BR: { lat: -14.2, lng: -51.9 },
  ES: { lat: 40.5, lng: -3.7 }, PT: { lat: 39.4, lng: -8.2 }, AT: { lat: 47.5, lng: 14.6 },
  CH: { lat: 46.8, lng: 8.2 }, DK: { lat: 56.3, lng: 9.5 }, NO: { lat: 60.5, lng: 8.5 },
  FI: { lat: 61.9, lng: 25.7 }, PL: { lat: 51.9, lng: 19.1 }, CZ: { lat: 49.8, lng: 15.5 },
}

function updateCollectionRings(globe, state) {
  const show = state.showCollectionOverlay && state.globeLayers.collection !== false
  const countries = state.collectionCountries
  if (!show || !countries || Object.keys(countries).length === 0) {
    globe.ringsData([])
    return
  }
  const maxCount = Math.max(1, ...Object.values(countries))
  const rings = Object.entries(countries)
    .map(([iso2, count]) => {
      const coords = COUNTRY_COORDS[iso2]
      if (!coords) return null
      return {
        lat: coords.lat,
        lng: coords.lng,
        maxR: 2 + (count / maxCount) * 6,
        propagationSpeed: 2,
        repeatPeriod: 1200,
        count,
        iso2,
      }
    })
    .filter(Boolean)
  globe.ringsData(rings)
}

export default function EarthGlobe({ paused = false }) {
  const containerRef = useRef(null)
  const globeRef = useRef(null)
  const animFrameRef = useRef(null)
  const povIntervalRef = useRef(null)
  const pausedRef = useRef(paused)
  const composerRef = useRef(null)

  const setSelectedCity = useStore(s => s.setSelectedCity)
  const setCitiesData = useStore(s => s.setCitiesData)
  const setArcsData = useStore(s => s.setArcsData)
  const setHeatmapData = useStore(s => s.setHeatmapData)
  const setShopsData = useStore(s => s.setShopsData)

  const onCityClick = useCallback((city) => {
    setSelectedCity(city)
    const globe = globeRef.current
    if (globe) {
      // Stop auto-rotate when city is selected
      const controls = globe.controls()
      controls.autoRotate = false
      // Smooth fly-to animation
      globe.pointOfView({ lat: city.lat, lng: city.lng, altitude: 1.5 }, 1200)
    }
  }, [setSelectedCity])

  useEffect(() => {
    if (!containerRef.current || globeRef.current) return

    const globe = Globe({
        rendererConfig: { antialias: true, alpha: false },
      })
      .globeImageUrl(TEXTURES.globe)
      .bumpImageUrl(TEXTURES.bump)
      .backgroundImageUrl(TEXTURES.sky)
      .showAtmosphere(true)
      .atmosphereColor('#4466cc')
      .atmosphereAltitude(0.25)
      .showGraticules(true)
      .width(containerRef.current.clientWidth)
      .height(containerRef.current.clientHeight)

    globe(containerRef.current)

    // Access Three.js internals
    const scene = globe.scene()
    const renderer = globe.renderer()
    const camera = globe.camera()

    // Upgrade globe material — MeshStandardMaterial with emissive glow (worldmonitor style)
    const textureLoader = new THREE.TextureLoader()
    const globeGroup = scene.children.find(c => c.type === 'Group')
    if (globeGroup) {
      globeGroup.traverse(child => {
        if (child.isMesh && child.geometry?.type === 'SphereGeometry' && child.material?.map) {
          const oldMat = child.material
          const newMat = new THREE.MeshStandardMaterial({
            map: oldMat.map,
            roughness: 0.72,
            metalness: 0.08,
            emissive: new THREE.Color(0x0a1f2e),
            emissiveIntensity: 0.25,
            bumpScale: 0.6,
          })
          // Load bump + roughness/specular maps
          textureLoader.load(TEXTURES.bump, tex => { newMat.bumpMap = tex; newMat.needsUpdate = true })
          textureLoader.load(TEXTURES.water, tex => { newMat.roughnessMap = tex; newMat.needsUpdate = true })
          child.material = newMat
          oldMat.dispose()
        }
      })
    }

    // Renderer settings
    renderer.toneMapping = THREE.ACESFilmicToneMapping
    renderer.toneMappingExposure = 1.15

    // Lighting — 4-point setup: sun, fill, ambient, cyan rim (worldmonitor-inspired)
    const ambient = new THREE.AmbientLight(0x223344, 0.45)
    scene.add(ambient)
    const sunLight = new THREE.DirectionalLight(0xffeedd, 1.2)
    sunLight.position.set(5, 3, 5)
    scene.add(sunLight)
    const fillLight = new THREE.DirectionalLight(0x334466, 0.3)
    fillLight.position.set(-3, -1, -3)
    scene.add(fillLight)
    // Cyan point light from behind — adds depth and rim glow
    const cyanRimLight = new THREE.PointLight(0x00d4ff, 0.35)
    cyanRimLight.position.set(-10, -10, -10)
    scene.add(cyanRimLight)

    // Auto-rotate — stops on interaction, resumes after idle
    const controls = globe.controls()
    controls.autoRotate = true
    controls.autoRotateSpeed = 0.3
    controls.enableDamping = true
    controls.dampingFactor = 0.1
    // Touch: one finger rotate, two fingers pinch-zoom/pan
    controls.touches = {
      ONE: THREE.TOUCH.ROTATE,
      TWO: THREE.TOUCH.DOLLY_PAN,
    }

    // Pause auto-rotate on user interaction, resume after 10s idle
    let autoRotateTimer = null
    const pauseAutoRotate = () => {
      controls.autoRotate = false
      if (autoRotateTimer) clearTimeout(autoRotateTimer)
      autoRotateTimer = setTimeout(() => {
        // Only resume if no city is selected
        if (!useStore.getState().selectedCity) {
          controls.autoRotate = true
        }
      }, 10000)
    }
    controls.addEventListener('start', pauseAutoRotate)

    // Double-tap to fly-to on globe
    let lastTap = 0
    const onDoubleTap = (e) => {
      const now = Date.now()
      if (now - lastTap < 300) {
        // Double tap detected — fly to tapped location
        const touch = e.changedTouches?.[0]
        if (!touch || !containerRef.current) return
        // Get current POV and zoom in
        const pov = globe.pointOfView()
        if (pov) {
          globe.pointOfView({ ...pov, altitude: Math.max(0.5, pov.altitude * 0.5) }, 800)
        }
      }
      lastTap = now
    }
    containerRef.current.addEventListener('touchend', onDoubleTap)

    globeRef.current = globe
    useStore.getState().setGlobeInstance(globe)

    // Periodically sync globe center to store for minimap + altitude-based shop visibility
    let shopsVisible = false
    povIntervalRef.current = setInterval(() => {
      const pov = globe.pointOfView()
      if (pov) {
        useStore.setState({ globeCenter: { lat: pov.lat, lng: pov.lng } })
        // Show/hide shops based on zoom altitude
        const state = useStore.getState()
        if (state.globeLayers.shops) {
          const shouldShow = pov.altitude < 2.5
          if (shouldShow !== shopsVisible) {
            shopsVisible = shouldShow
            globe.pointsData(shouldShow ? state.shopsData : [])
          }
        }
      }
    }, 200)

    // Add atmosphere + starfield
    const cleanupAtmosphere = addAtmosphere(scene)
    const cleanupStarfield = addStarfield(scene)

    // Setup bloom post-processing
    const { composer, resize: resizeBloom, cleanup: cleanupBloom } = setupBloom(
      renderer, scene, camera
    )

    // Store composer for pause/resume
    composerRef.current = composer

    // Take over the render loop from globe.gl for bloom
    renderer.setAnimationLoop(null)
    const animate = () => {
      animFrameRef.current = requestAnimationFrame(animate)
      controls.update()
      composer.render()
    }
    if (!pausedRef.current) {
      animate()
    }

    // Resize handler
    const onResize = () => {
      if (!containerRef.current) return
      const w = containerRef.current.clientWidth
      const h = containerRef.current.clientHeight
      globe.width(w).height(h)
      resizeBloom(w, h)
    }
    window.addEventListener('resize', onResize)

    // --- Load data and configure globe layers ---
    Promise.all([
      fetch('/data/cities.json').then(r => r.json()),
      fetch('/data/arcs.json').then(r => r.json()),
      fetch('/data/country_stats.json').then(r => r.json()),
      fetch('/data/record_shops.json').then(r => r.json()).catch(() => ({ shops: [] })),
      fetch('/data/label_cities.json').then(r => r.json()).catch(() => []),
    ]).then(([citiesJson, arcsJson, countryJson, shopsJson, labelCities]) => {
      const cities = citiesJson.cities

      // Enrich cities with label data from Discogs dump
      if (labelCities.length > 0) {
        const labelByCity = {}
        labelCities.forEach(lc => {
          const key = lc.city.toLowerCase()
          labelByCity[key] = lc
        })
        cities.forEach(c => {
          const match = labelByCity[c.name?.toLowerCase()]
          if (match) {
            c.label_count = match.label_count
            c.total_label_releases = match.total_releases
            c.top_labels = match.top_labels
          }
        })
      }
      const citiesById = {}
      cities.forEach(c => { citiesById[c.id] = c })

      // Store in Zustand
      setCitiesData(cities)

      // ---- City markers (HTML elements) ----
      globe
        .htmlElementsData(cities)
        .htmlElement(d => {
          const el = createCityMarker(d)
          el.addEventListener('click', () => onCityClick(d))
          return el
        })
        .htmlLat(d => d.lat)
        .htmlLng(d => d.lng)
        .htmlAltitude(0.01)

      // ---- Arcs ----
      const allArcs = resolveArcs(arcsJson, citiesById)
      setArcsData(allArcs)

      // Start with no arcs (shown on city select)
      globe
        .arcsData([])
        .arcStartLat(d => d.startLat)
        .arcStartLng(d => d.startLng)
        .arcEndLat(d => d.endLat)
        .arcEndLng(d => d.endLng)
        .arcColor(() => [
          'rgba(0, 255, 255, 0)',       // start: transparent
          'rgba(0, 230, 255, 0.85)',    // cyan
          'rgba(255, 191, 0, 0.85)',    // amber
          'rgba(255, 191, 0, 0)',       // end: transparent
        ])
        .arcAltitudeAutoScale(0.3)
        .arcAltitude(d => {
          // Distance-based altitude: longer arcs fly higher
          const dLat = d.endLat - d.startLat
          const dLng = d.endLng - d.startLng
          const dist = Math.sqrt(dLat * dLat + dLng * dLng)
          const distNorm = Math.min(1, dist / 180) // normalize to 0-1
          const base = 0.08
          // Weight factor
          const w = typeof d.weight === 'number' && d.weight > 1
            ? d.weight
            : d.weight * 6000
          const wNorm = Math.min(1, w / 12000)
          return base + distNorm * 0.35 + wNorm * 0.1
        })
        .arcStroke(d => {
          const w = typeof d.weight === 'number' && d.weight > 1
            ? d.weight : d.weight * 6000
          return 0.2 + Math.min(1, w / 12000) * 0.6
        })
        .arcDashLength(0.4)
        .arcDashGap(0.2)
        .arcDashAnimateTime(() => 1500 + Math.random() * 1500)

      // ---- Collection rings layer (amber markers) ----
      globe
        .ringsData([])
        .ringLat(d => d.lat)
        .ringLng(d => d.lng)
        .ringMaxRadius(d => d.maxR)
        .ringPropagationSpeed(d => d.propagationSpeed)
        .ringRepeatPeriod(d => d.repeatPeriod)
        .ringColor(() => t => `rgba(255, 191, 0, ${1 - t})`)
        .ringAltitude(0.015)

      // Initialize collection layer from current state
      updateCollectionRings(globe, useStore.getState())

      // ---- Hexbin heatmap ----
      const heatPoints = countryJson.countries.map(c => ({
        lat: c.lat,
        lng: c.lng,
        weight: c.release_count,
        country: c.country,
      }))
      setHeatmapData(heatPoints)

      globe
        .hexBinPointsData(heatPoints)
        .hexBinPointWeight('weight')
        .hexBinResolution(3)
        .hexAltitude(d => d.sumWeight * 0.0000004)
        .hexTopColor(d => {
          const intensity = Math.min(1, d.sumWeight / 500000)
          const alpha = 0.15 + intensity * 0.45
          return `rgba(180, 80, 255, ${alpha})`
        })
        .hexSideColor(d => {
          const intensity = Math.min(1, d.sumWeight / 500000)
          const alpha = 0.08 + intensity * 0.25
          return `rgba(140, 40, 220, ${alpha})`
        })
        .hexBinMerge(true)
        .hexTransitionDuration(800)

      // ---- Record shops (points layer — amber dots, shown when zoomed in) ----
      const shops = shopsJson.shops || []
      setShopsData(shops)

      globe
        .pointsData([]) // Start hidden; toggled via globeLayers.shops
        .pointLat(d => d.lat)
        .pointLng(d => d.lng)
        .pointAltitude(0.005)
        .pointRadius(0.12)
        .pointColor(() => '#F5A623')
        .pointsMerge(true)
        .pointResolution(6)
        .pointLabel(d => {
          const lines = [`<b style="color:#F5A623">${d.name}</b>`]
          if (d.city) lines.push(d.city + (d.country ? `, ${d.country}` : ''))
          else if (d.address) lines.push(d.address)
          if (d.vinyl) lines.push('<span style="color:#F5A623">&#9679; Vinyl</span>')
          if (d.website) lines.push(`<a href="${d.website}" target="_blank" style="color:#88ccff">${d.website.replace(/^https?:\/\//, '').slice(0, 40)}</a>`)
          if (d.opening_hours) lines.push(`<span style="opacity:0.7">${d.opening_hours}</span>`)
          return `<div style="font-size:12px;line-height:1.5;padding:4px 0">${lines.join('<br/>')}</div>`
        })

      // ---- Country borders (thin, low-opacity polygon outlines) ----
      fetch(COUNTRY_BORDERS_URL)
        .then(r => r.json())
        .then(topo => {
          const countries = feature(topo, topo.objects.countries)
          globe
            .polygonsData(countries.features)
            .polygonGeoJsonGeometry(d => d.geometry)
            .polygonCapColor(() => 'rgba(0, 0, 0, 0)')
            .polygonSideColor(() => 'rgba(0, 0, 0, 0)')
            .polygonStrokeColor(() => 'rgba(80, 180, 255, 0.12)')
            .polygonAltitude(0.002)
            .polygonLabel(() => '')
        })
        .catch(() => {}) // non-critical
    }).catch(err => {
      console.error('EarthGlobe: failed to load data', err)
    })

    return () => {
      window.removeEventListener('resize', onResize)
      if (containerRef.current) {
        containerRef.current.removeEventListener('touchend', onDoubleTap)
      }
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current)
      if (povIntervalRef.current) clearInterval(povIntervalRef.current)
      if (autoRotateTimer) clearTimeout(autoRotateTimer)
      controls.removeEventListener('start', pauseAutoRotate)
      cleanupAtmosphere()
      cleanupStarfield()
      cleanupBloom()
      useStore.getState().setGlobeInstance(null)
      globe._destructor?.()
      globeRef.current = null
    }
  }, [onCityClick, setCitiesData, setArcsData, setHeatmapData, setShopsData])

  // Pause/resume animation loop when visibility changes
  useEffect(() => {
    pausedRef.current = paused
    if (!globeRef.current) return

    if (paused) {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current)
        animFrameRef.current = null
      }
    } else if (!animFrameRef.current) {
      const controls = globeRef.current.controls()
      const composer = composerRef.current
      const animate = () => {
        animFrameRef.current = requestAnimationFrame(animate)
        controls.update()
        if (composer) {
          composer.render()
        }
      }
      animate()
    }
  }, [paused])

  // React to selectedCity changes — show related arcs
  useEffect(() => {
    const unsub = useStore.subscribe((state, prevState) => {
      if (state.selectedCity === prevState.selectedCity) return
      const globe = globeRef.current
      if (!globe) return

      const city = state.selectedCity
      if (!city) {
        globe.arcsData([])
        // Resume auto-rotate when city is deselected
        globe.controls().autoRotate = true
        return
      }

      // Stop auto-rotate when city is selected
      globe.controls().autoRotate = false

      const allArcs = state.arcsData
      const related = allArcs.filter(
        a => a.fromId === city.id || a.toId === city.id
      )
      globe.arcsData(related)
    })
    return unsub
  }, [])

  // React to heatmap visibility toggle (legacy)
  useEffect(() => {
    const unsub = useStore.subscribe((state, prevState) => {
      if (state.heatmapVisible === prevState.heatmapVisible) return
      const globe = globeRef.current
      if (!globe) return
      globe.hexBinPointsData(state.heatmapVisible ? state.heatmapData : [])
    })
    return unsub
  }, [])

  // React to globeLayers changes (cities, arcs, heatmap, collection toggles)
  useEffect(() => {
    const unsub = useStore.subscribe((state, prevState) => {
      if (state.globeLayers === prevState.globeLayers) return
      const globe = globeRef.current
      if (!globe) return

      const { cities, arcs, heatmap, shops, collection } = state.globeLayers

      // Cities: toggle HTML elements visibility
      if (cities !== prevState.globeLayers.cities) {
        globe.htmlElementsData(cities ? state.citiesData : [])
      }

      // Arcs: toggle arc display
      if (arcs !== prevState.globeLayers.arcs) {
        if (!arcs) {
          globe.arcsData([])
        } else if (state.selectedCity) {
          const related = state.arcsData.filter(
            a => a.fromId === state.selectedCity.id || a.toId === state.selectedCity.id
          )
          globe.arcsData(related)
        }
      }

      // Heatmap: toggle hex bins
      if (heatmap !== prevState.globeLayers.heatmap) {
        globe.hexBinPointsData(heatmap ? state.heatmapData : [])
      }

      // Shops: toggle points layer
      if (shops !== prevState.globeLayers.shops) {
        globe.pointsData(shops ? state.shopsData : [])
      }

      // Collection: toggle ring markers
      if (collection !== prevState.globeLayers.collection) {
        updateCollectionRings(globe, state)
      }
    })
    return unsub
  }, [])

  // React to collection data changes — update ring markers on globe
  useEffect(() => {
    const unsub = useStore.subscribe((state, prevState) => {
      if (state.collectionCountries === prevState.collectionCountries &&
          state.showCollectionOverlay === prevState.showCollectionOverlay) return
      const globe = globeRef.current
      if (!globe) return
      updateCollectionRings(globe, state)
    })
    return unsub
  }, [])

  return (
    <div className="earth-globe-container" ref={containerRef} />
  )
}
