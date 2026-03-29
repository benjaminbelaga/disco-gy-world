/**
 * Vanilla Three.js building system for GenrePlanet.
 * Uses InstancedMesh for efficient rendering (one draw call per geometry type per genre).
 * Buildings appear when camera is close to a territory and are removed when far.
 */
import * as THREE from 'three'
import { generateBuildings, BIOME_MAPPING } from './buildingGenerator'
import { createWindowMaterial, updateWindowMaterial } from './windowShader'

const MAX_INSTANCES = 500
const SHOW_DISTANCE = 180 // Camera distance threshold to show buildings
const HIDE_DISTANCE = 220 // Hysteresis to prevent flicker
const GLOBE_RADIUS = 100

// Shared geometry pool (created once)
const geometryPool = {
  box: null,
  cylinder: null,
  cone: null,
}

function getGeometry(type) {
  if (!geometryPool.box) {
    geometryPool.box = new THREE.BoxGeometry(1, 1, 1)
    geometryPool.cylinder = new THREE.CylinderGeometry(0.5, 0.5, 1, 8)
    geometryPool.cone = new THREE.ConeGeometry(0.5, 1, 6)
  }
  return geometryPool[type] || geometryPool.box
}

/**
 * Project a point onto the displaced sphere surface.
 * Uses the planet mesh geometry to find the actual surface height at a direction.
 */
function getSurfacePoint(direction, planetMesh) {
  const posAttr = planetMesh.geometry.attributes.position
  const count = posAttr.count
  const tmpVec = new THREE.Vector3()

  let bestDot = -1
  let bestPoint = null

  // Sample nearby vertices to find surface height
  for (let i = 0; i < count; i += 3) { // Skip some for performance
    tmpVec.set(posAttr.getX(i), posAttr.getY(i), posAttr.getZ(i))
    const d = tmpVec.clone().normalize().dot(direction)
    if (d > bestDot) {
      bestDot = d
      bestPoint = tmpVec.clone()
    }
  }

  if (!bestPoint) {
    return direction.clone().multiplyScalar(GLOBE_RADIUS)
  }

  return bestPoint
}

/**
 * Create the building system.
 * @param {THREE.Scene} scene
 * @param {THREE.Mesh} planetMesh - The displaced sphere mesh
 * @returns {Object} Building system controller
 */
export function createBuildingSystem(scene, planetMesh) {
  const activeTerritories = new Map() // territorySlug -> { group, materials }
  const clock = new THREE.Clock()
  let currentTerritory = null

  /**
   * Spawn buildings for a territory.
   */
  function spawnBuildings(territory) {
    const slug = territory.slug
    if (activeTerritories.has(slug)) return

    const seed = hashString(slug)
    const buildingConfigs = generateBuildings(territory.biome, 60, seed)

    const group = new THREE.Group()
    group.name = `buildings-${slug}`

    // Group buildings by geometry type for instancing
    const byType = {}
    for (const cfg of buildingConfigs) {
      if (!byType[cfg.geometry]) byType[cfg.geometry] = []
      byType[cfg.geometry].push(cfg)
    }

    const materials = []
    const surfacePoint = getSurfacePoint(territory.dir, planetMesh)
    const surfaceRadius = surfacePoint.length()

    // Build a local coordinate frame on the sphere surface
    const up = territory.dir.clone().normalize()
    const tangent = new THREE.Vector3()
    if (Math.abs(up.y) < 0.99) {
      tangent.crossVectors(up, new THREE.Vector3(0, 1, 0)).normalize()
    } else {
      tangent.crossVectors(up, new THREE.Vector3(1, 0, 0)).normalize()
    }
    const bitangent = new THREE.Vector3().crossVectors(up, tangent).normalize()

    // Basis matrix to transform local XZ offsets to world coords on sphere
    const basisMatrix = new THREE.Matrix4().makeBasis(tangent, up, bitangent)
    basisMatrix.setPosition(up.clone().multiplyScalar(surfaceRadius))

    for (const [geoType, configs] of Object.entries(byType)) {
      const geometry = getGeometry(geoType)
      const material = createWindowMaterial({
        emissiveColor: configs[0].emissiveColor,
        baseColor: configs[0].color,
        windowGrid: [4, Math.round(6 + Math.random() * 4)],
        litProbability: configs[0].windowDensity,
      })
      materials.push(material)

      const instanceCount = Math.min(configs.length, MAX_INSTANCES)
      const mesh = new THREE.InstancedMesh(geometry, material, instanceCount)
      mesh.frustumCulled = false // Buildings are small, let GPU handle it

      const dummy = new THREE.Object3D()

      for (let i = 0; i < instanceCount; i++) {
        const cfg = configs[i]

        // Find actual surface height at this offset
        const worldDir = up.clone()
          .add(tangent.clone().multiplyScalar(cfg.position[0] * 0.01))
          .add(bitangent.clone().multiplyScalar(cfg.position[2] * 0.01))
          .normalize()
        const sPoint = getSurfacePoint(worldDir, planetMesh)
        const sRadius = sPoint.length()

        // Position building base on surface
        const worldPos = worldDir.clone().multiplyScalar(sRadius)

        dummy.position.copy(worldPos)

        // Orient building to stand perpendicular to sphere surface
        dummy.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), worldDir)

        // Apply building-specific rotation (around local Y axis)
        const localRot = new THREE.Quaternion().setFromEuler(
          new THREE.Euler(cfg.rotation[0], cfg.rotation[1], cfg.rotation[2])
        )
        dummy.quaternion.multiply(localRot)

        // Scale: width, height, depth (height along local Y = outward from sphere)
        dummy.scale.set(cfg.scale[0], cfg.scale[1], cfg.scale[2])

        // Offset upward by half height so base sits on surface
        const halfHeight = cfg.scale[1] * 0.5
        dummy.position.add(worldDir.clone().multiplyScalar(halfHeight))

        dummy.updateMatrix()
        mesh.setMatrixAt(i, dummy.matrix)
      }

      mesh.instanceMatrix.needsUpdate = true
      group.add(mesh)
    }

    scene.add(group)
    activeTerritories.set(slug, { group, materials })
  }

  /**
   * Remove buildings for a territory.
   */
  function removeBuildings(slug) {
    const entry = activeTerritories.get(slug)
    if (!entry) return

    scene.remove(entry.group)
    entry.group.traverse((child) => {
      if (child.geometry) child.geometry.dispose()
      if (child.material) child.material.dispose()
    })
    activeTerritories.delete(slug)
  }

  /**
   * Show buildings for a specific territory (called on territory click).
   */
  function showForTerritory(territory) {
    // Remove previous territory buildings
    if (currentTerritory && currentTerritory.slug !== territory.slug) {
      removeBuildings(currentTerritory.slug)
    }
    currentTerritory = territory
    spawnBuildings(territory)
  }

  /**
   * Update LOD based on camera position.
   * @param {THREE.Camera} camera
   */
  function update(camera) {
    const elapsed = clock.getElapsedTime()

    // Update shader time uniforms
    for (const [, entry] of activeTerritories) {
      for (const mat of entry.materials) {
        updateWindowMaterial(mat, elapsed)
      }
    }

    // LOD: hide buildings if camera moves too far from territory
    if (currentTerritory) {
      const territoryWorldPos = currentTerritory.dir.clone().multiplyScalar(GLOBE_RADIUS)
      const dist = camera.position.distanceTo(territoryWorldPos)

      if (dist > HIDE_DISTANCE && activeTerritories.has(currentTerritory.slug)) {
        removeBuildings(currentTerritory.slug)
      } else if (dist < SHOW_DISTANCE && !activeTerritories.has(currentTerritory.slug)) {
        spawnBuildings(currentTerritory)
      }
    }
  }

  /**
   * Cleanup all buildings.
   */
  function dispose() {
    for (const slug of [...activeTerritories.keys()]) {
      removeBuildings(slug)
    }
    // Dispose shared geometries
    for (const geo of Object.values(geometryPool)) {
      if (geo) geo.dispose()
    }
    geometryPool.box = null
    geometryPool.cylinder = null
    geometryPool.cone = null
  }

  return { showForTerritory, update, dispose, removeBuildings }
}

// Simple string hash for deterministic seeds
function hashString(str) {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash |= 0
  }
  return Math.abs(hash)
}
