/**
 * 2K-point starfield using InstancedMesh for single draw call.
 */
import * as THREE from 'three'

/**
 * @param {THREE.Scene} scene
 * @param {number} count - number of stars
 * @param {number} radius - sphere radius to place stars on
 * @returns {Function} cleanup
 */
export function addStarfield(scene, count = 2000, radius = 800) {
  const geometry = new THREE.SphereGeometry(0.3, 4, 4)
  const material = new THREE.MeshBasicMaterial({
    color: 0xffffff,
    transparent: true,
    opacity: 0.8,
  })

  const mesh = new THREE.InstancedMesh(geometry, material, count)
  const dummy = new THREE.Object3D()
  const color = new THREE.Color()

  for (let i = 0; i < count; i++) {
    // Random point on sphere
    const theta = Math.random() * Math.PI * 2
    const phi = Math.acos(2 * Math.random() - 1)
    const r = radius + (Math.random() - 0.5) * 200

    dummy.position.set(
      r * Math.sin(phi) * Math.cos(theta),
      r * Math.sin(phi) * Math.sin(theta),
      r * Math.cos(phi)
    )
    // Random size variation
    const scale = 0.3 + Math.random() * 1.2
    dummy.scale.setScalar(scale)
    dummy.updateMatrix()
    mesh.setMatrixAt(i, dummy.matrix)

    // Slight color variation (white to pale blue)
    const hue = 0.55 + Math.random() * 0.1
    const sat = Math.random() * 0.3
    const lum = 0.7 + Math.random() * 0.3
    color.setHSL(hue, sat, lum)
    mesh.setColorAt(i, color)
  }

  mesh.instanceMatrix.needsUpdate = true
  mesh.instanceColor.needsUpdate = true
  scene.add(mesh)

  return () => {
    scene.remove(mesh)
    geometry.dispose()
    material.dispose()
  }
}
