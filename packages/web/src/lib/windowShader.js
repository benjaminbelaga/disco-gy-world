/**
 * Custom ShaderMaterial for emissive window grids on procedural buildings.
 * Grid pattern with random on/off per window cell, animated flicker.
 */
import * as THREE from 'three'

const vertexShader = /* glsl */ `
  varying vec2 vUv;
  varying vec3 vNormal;
  varying vec3 vWorldPosition;

  void main() {
    vUv = uv;
    vNormal = normalize(normalMatrix * normal);
    vec4 worldPos = modelMatrix * instanceMatrix * vec4(position, 1.0);
    vWorldPosition = worldPos.xyz;
    gl_Position = projectionMatrix * viewMatrix * worldPos;
  }
`

const fragmentShader = /* glsl */ `
  uniform vec3 emissiveColor;
  uniform vec3 baseColor;
  uniform vec2 windowGrid;
  uniform float litProbability;
  uniform float time;

  varying vec2 vUv;
  varying vec3 vNormal;
  varying vec3 vWorldPosition;

  // Hash function for per-window randomness
  float hash(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
  }

  void main() {
    // Only show windows on vertical faces (not top/bottom)
    float facingUp = abs(vNormal.y);
    float isVertical = 1.0 - smoothstep(0.5, 0.8, facingUp);

    // Window grid coordinates
    vec2 gridPos = vUv * windowGrid;
    vec2 cellId = floor(gridPos);
    vec2 cellUv = fract(gridPos);

    // Window inset (margin within each cell)
    float margin = 0.15;
    float isWindow = step(margin, cellUv.x) * step(cellUv.x, 1.0 - margin)
                   * step(margin, cellUv.y) * step(cellUv.y, 1.0 - margin);

    // Per-window random lit state
    float windowHash = hash(cellId);
    float isLit = step(1.0 - litProbability, windowHash);

    // Subtle flicker animation (slow, per-window phase)
    float flicker = 0.9 + 0.1 * sin(time * 0.5 + windowHash * 6.28);

    // Combine: base color + emissive window glow
    vec3 color = baseColor * 0.6;
    float windowEmission = isWindow * isLit * isVertical * flicker;
    color += emissiveColor * windowEmission * 1.5;

    // Simple directional lighting
    float diffuse = max(dot(vNormal, normalize(vec3(1.0, 1.0, 0.5))), 0.0);
    color += baseColor * diffuse * 0.3;

    gl_FragColor = vec4(color, 1.0);
  }
`

/**
 * Create a window shader material for instanced buildings.
 * @param {Object} options
 * @param {string} options.emissiveColor - Hex color for lit windows
 * @param {string} options.baseColor - Hex color for building walls
 * @param {number[]} options.windowGrid - [columns, rows] per face
 * @param {number} options.litProbability - 0-1, fraction of windows lit
 * @returns {THREE.ShaderMaterial}
 */
export function createWindowMaterial({
  emissiveColor = '#00FFFF',
  baseColor = '#2D1B1B',
  windowGrid = [4, 8],
  litProbability = 0.6,
} = {}) {
  return new THREE.ShaderMaterial({
    vertexShader,
    fragmentShader,
    uniforms: {
      emissiveColor: { value: new THREE.Color(emissiveColor) },
      baseColor: { value: new THREE.Color(baseColor) },
      windowGrid: { value: new THREE.Vector2(windowGrid[0], windowGrid[1]) },
      litProbability: { value: litProbability },
      time: { value: 0 },
    },
    flatShading: true,
  })
}

/**
 * Update time uniform for animation.
 * @param {THREE.ShaderMaterial} material
 * @param {number} time - elapsed time in seconds
 */
export function updateWindowMaterial(material, time) {
  if (material?.uniforms?.time) {
    material.uniforms.time.value = time
  }
}
