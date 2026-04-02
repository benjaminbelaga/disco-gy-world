/**
 * Premium atmosphere: Fresnel backface shader + double glow spheres.
 * Adds to the globe.gl Three.js scene directly.
 */
import * as THREE from 'three'

const FRESNEL_VERTEX = `
  varying vec3 vNormal;
  varying vec3 vPosition;
  void main() {
    vNormal = normalize(normalMatrix * normal);
    vPosition = (modelViewMatrix * vec4(position, 1.0)).xyz;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`

const FRESNEL_FRAGMENT = `
  varying vec3 vNormal;
  varying vec3 vPosition;
  uniform vec3 glowColor;
  uniform float intensity;
  uniform float power;
  void main() {
    vec3 viewDir = normalize(-vPosition);
    float fresnel = pow(1.0 - abs(dot(vNormal, viewDir)), power);
    gl_FragColor = vec4(glowColor, fresnel * intensity);
  }
`

/**
 * @param {THREE.Scene} scene
 * @param {number} globeRadius - globe.gl default is 100
 * @returns {Function} cleanup function
 */
export function addAtmosphere(scene, globeRadius = 100) {
  const meshes = []

  // 1. Fresnel atmosphere shell (BackSide)
  const atmosGeom = new THREE.SphereGeometry(globeRadius * 1.015, 64, 64)
  const atmosMat = new THREE.ShaderMaterial({
    vertexShader: FRESNEL_VERTEX,
    fragmentShader: FRESNEL_FRAGMENT,
    uniforms: {
      glowColor: { value: new THREE.Color(0x00ddff) },
      intensity: { value: 0.7 },
      power: { value: 3.5 },
    },
    side: THREE.BackSide,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  })
  const atmosMesh = new THREE.Mesh(atmosGeom, atmosMat)
  scene.add(atmosMesh)
  meshes.push(atmosMesh)

  // 2. Outer glow sphere (larger, subtler)
  const outerGeom = new THREE.SphereGeometry(globeRadius * 1.08, 48, 48)
  const outerMat = new THREE.MeshBasicMaterial({
    color: 0x0088cc,
    transparent: true,
    opacity: 0.08,
    side: THREE.BackSide,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  })
  const outerMesh = new THREE.Mesh(outerGeom, outerMat)
  scene.add(outerMesh)
  meshes.push(outerMesh)

  // 3. Inner glow sphere (tighter, brighter)
  const innerGeom = new THREE.SphereGeometry(globeRadius * 1.03, 48, 48)
  const innerMat = new THREE.MeshBasicMaterial({
    color: 0x00ccff,
    transparent: true,
    opacity: 0.05,
    side: THREE.BackSide,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  })
  const innerMesh = new THREE.Mesh(innerGeom, innerMat)
  scene.add(innerMesh)
  meshes.push(innerMesh)

  // Slowly rotate outer glow for a living feel (worldmonitor-inspired)
  let animId = null
  const rotateGlows = () => {
    animId = requestAnimationFrame(rotateGlows)
    if (outerMesh) outerMesh.rotation.y += 0.0003
    if (innerMesh) innerMesh.rotation.y += 0.0001
  }
  rotateGlows()

  return () => {
    if (animId) cancelAnimationFrame(animId)
    meshes.forEach(m => {
      scene.remove(m)
      m.geometry.dispose()
      m.material.dispose()
    })
  }
}
