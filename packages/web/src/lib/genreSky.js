import * as THREE from 'three'

// Biome sky configurations
const BIOME_SKIES = {
  // Techno: dark stormy, deep gray-blue, lightning flashes
  'techno-massif': {
    topColor: [0.02, 0.03, 0.08],
    horizonColor: [0.08, 0.10, 0.18],
    bottomColor: [0.04, 0.05, 0.10],
    animationType: 1, // lightning
    animationSpeed: 0.8,
  },
  'industrial-wasteland': {
    topColor: [0.03, 0.03, 0.07],
    horizonColor: [0.10, 0.08, 0.15],
    bottomColor: [0.05, 0.04, 0.09],
    animationType: 1,
    animationSpeed: 1.0,
  },
  // House: warm sunset gradient (amber -> orange -> purple)
  'house-plains': {
    topColor: [0.15, 0.05, 0.20],
    horizonColor: [0.90, 0.45, 0.15],
    bottomColor: [0.80, 0.30, 0.10],
    animationType: 2, // gentle pulse
    animationSpeed: 0.3,
  },
  'disco-riviera': {
    topColor: [0.12, 0.04, 0.22],
    horizonColor: [0.85, 0.50, 0.20],
    bottomColor: [0.75, 0.35, 0.12],
    animationType: 2,
    animationSpeed: 0.25,
  },
  // Ambient: aurora borealis (animated color bands, green/blue/purple)
  'ambient-depths': {
    topColor: [0.02, 0.04, 0.10],
    horizonColor: [0.05, 0.15, 0.12],
    bottomColor: [0.03, 0.06, 0.14],
    animationType: 3, // aurora
    animationSpeed: 0.4,
  },
  'idm-crystalline': {
    topColor: [0.03, 0.05, 0.12],
    horizonColor: [0.06, 0.12, 0.15],
    bottomColor: [0.04, 0.07, 0.16],
    animationType: 3,
    animationSpeed: 0.5,
  },
  // DnB: night sky with orange horizon glow
  'jungle-canopy': {
    topColor: [0.01, 0.01, 0.04],
    horizonColor: [0.40, 0.18, 0.05],
    bottomColor: [0.15, 0.08, 0.03],
    animationType: 2,
    animationSpeed: 0.6,
  },
  'dubstep-rift': {
    topColor: [0.02, 0.01, 0.05],
    horizonColor: [0.35, 0.15, 0.06],
    bottomColor: [0.12, 0.06, 0.03],
    animationType: 2,
    animationSpeed: 0.7,
  },
  // Trance: golden sunset with aurora beams
  'trance-highlands': {
    topColor: [0.05, 0.03, 0.15],
    horizonColor: [0.70, 0.50, 0.10],
    bottomColor: [0.50, 0.35, 0.08],
    animationType: 4, // aurora beams
    animationSpeed: 0.35,
  },
  // Hardcore: red-tinted storm clouds
  'urban-quarter': {
    topColor: [0.10, 0.02, 0.02],
    horizonColor: [0.30, 0.05, 0.03],
    bottomColor: [0.20, 0.03, 0.02],
    animationType: 1,
    animationSpeed: 1.2,
  },
  // Experimental: glitch sky
  'garage-district': {
    topColor: [0.05, 0.05, 0.05],
    horizonColor: [0.15, 0.10, 0.20],
    bottomColor: [0.08, 0.08, 0.10],
    animationType: 5, // glitch
    animationSpeed: 1.5,
  },
  'source-monuments': {
    topColor: [0.04, 0.04, 0.08],
    horizonColor: [0.12, 0.12, 0.18],
    bottomColor: [0.06, 0.06, 0.10],
    animationType: 2,
    animationSpeed: 0.2,
  },
}

// Default sky (neutral deep space)
const DEFAULT_SKY = {
  topColor: [0.02, 0.02, 0.05],
  horizonColor: [0.06, 0.06, 0.12],
  bottomColor: [0.04, 0.04, 0.08],
  animationType: 0,
  animationSpeed: 0.2,
}

const vertexShader = /* glsl */ `
varying vec3 vWorldPosition;
void main() {
  vec4 worldPos = modelMatrix * vec4(position, 1.0);
  vWorldPosition = worldPos.xyz;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`

const fragmentShader = /* glsl */ `
uniform vec3 uTopColor;
uniform vec3 uHorizonColor;
uniform vec3 uBottomColor;
uniform float uTime;
uniform float uAnimationSpeed;
uniform int uAnimationType;
uniform float uOpacity;

varying vec3 vWorldPosition;

// Simple hash for pseudo-random
float hash(float n) {
  return fract(sin(n) * 43758.5453);
}

// Smooth noise
float noise(float x) {
  float i = floor(x);
  float f = fract(x);
  return mix(hash(i), hash(i + 1.0), f * f * (3.0 - 2.0 * f));
}

void main() {
  // Normalized vertical position (-1 bottom to 1 top)
  float h = normalize(vWorldPosition).y;

  // Base gradient: bottom -> horizon -> top
  vec3 color;
  if (h > 0.0) {
    float t = pow(h, 0.6);
    color = mix(uHorizonColor, uTopColor, t);
  } else {
    float t = pow(-h, 0.6);
    color = mix(uHorizonColor, uBottomColor, t);
  }

  float time = uTime * uAnimationSpeed;

  // Animation type 1: Lightning flashes
  if (uAnimationType == 1) {
    float flash = step(0.97, hash(floor(time * 3.0)));
    float flashIntensity = flash * hash(floor(time * 3.0) + 100.0) * 0.4;
    // Lightning concentrated near horizon
    float horizonMask = 1.0 - abs(h);
    color += vec3(0.6, 0.65, 0.9) * flashIntensity * horizonMask;
  }

  // Animation type 2: Gentle color pulse
  if (uAnimationType == 2) {
    float pulse = sin(time * 0.5) * 0.5 + 0.5;
    color *= 0.9 + pulse * 0.15;
  }

  // Animation type 3: Aurora bands
  if (uAnimationType == 3) {
    float band1 = sin(h * 8.0 + time * 0.3) * 0.5 + 0.5;
    float band2 = sin(h * 12.0 - time * 0.2 + 2.0) * 0.5 + 0.5;
    float upperMask = smoothstep(0.1, 0.6, h);
    vec3 aurora1 = vec3(0.1, 0.8, 0.4) * band1 * 0.12 * upperMask;
    vec3 aurora2 = vec3(0.3, 0.2, 0.9) * band2 * 0.08 * upperMask;
    color += aurora1 + aurora2;
  }

  // Animation type 4: Aurora beams (vertical gold pillars)
  if (uAnimationType == 4) {
    float band = sin(h * 6.0 + time * 0.4) * 0.5 + 0.5;
    float upperMask = smoothstep(0.0, 0.5, h);
    vec3 beam = vec3(0.9, 0.7, 0.2) * band * 0.1 * upperMask;
    color += beam;
  }

  // Animation type 5: Glitch (random color shifts)
  if (uAnimationType == 5) {
    float glitchTrigger = step(0.85, hash(floor(time * 5.0)));
    float offset = hash(floor(time * 5.0) + 50.0) * 0.3 * glitchTrigger;
    color.r += offset;
    color.b -= offset * 0.5;
    // Static noise
    float staticNoise = hash(h * 100.0 + time * 10.0) * 0.04;
    color += vec3(staticNoise);
  }

  gl_FragColor = vec4(color, uOpacity);
}
`

/**
 * Create a genre-specific sky dome.
 * Returns { mesh, uniforms, update(delta), dispose(), transitionTo(biomeType, duration) }
 */
export function createGenreSky(biomeType) {
  const config = BIOME_SKIES[biomeType] || DEFAULT_SKY

  const uniforms = {
    uTopColor: { value: new THREE.Vector3(...config.topColor) },
    uHorizonColor: { value: new THREE.Vector3(...config.horizonColor) },
    uBottomColor: { value: new THREE.Vector3(...config.bottomColor) },
    uTime: { value: 0 },
    uAnimationSpeed: { value: config.animationSpeed },
    uAnimationType: { value: config.animationType },
    uOpacity: { value: 1.0 },
  }

  const geometry = new THREE.SphereGeometry(500, 32, 32)
  const material = new THREE.ShaderMaterial({
    vertexShader,
    fragmentShader,
    uniforms,
    side: THREE.BackSide,
    depthWrite: false,
    transparent: true,
  })

  const mesh = new THREE.Mesh(geometry, material)
  mesh.renderOrder = -1

  // Transition state
  let transitionState = null

  function update(delta) {
    uniforms.uTime.value += delta

    // Handle color transitions
    if (transitionState) {
      transitionState.elapsed += delta
      const t = Math.min(1, transitionState.elapsed / transitionState.duration)
      const eased = t * t * (3 - 2 * t) // smoothstep

      uniforms.uTopColor.value.lerpVectors(transitionState.fromTop, transitionState.toTop, eased)
      uniforms.uHorizonColor.value.lerpVectors(transitionState.fromHorizon, transitionState.toHorizon, eased)
      uniforms.uBottomColor.value.lerpVectors(transitionState.fromBottom, transitionState.toBottom, eased)
      uniforms.uAnimationSpeed.value = transitionState.fromSpeed + (transitionState.toSpeed - transitionState.fromSpeed) * eased

      // Snap animation type at midpoint
      if (eased >= 0.5 && !transitionState.typeSwapped) {
        uniforms.uAnimationType.value = transitionState.toType
        transitionState.typeSwapped = true
      }

      if (t >= 1) transitionState = null
    }
  }

  function transitionTo(newBiomeType, duration = 1.0) {
    const target = BIOME_SKIES[newBiomeType] || DEFAULT_SKY
    transitionState = {
      fromTop: uniforms.uTopColor.value.clone(),
      fromHorizon: uniforms.uHorizonColor.value.clone(),
      fromBottom: uniforms.uBottomColor.value.clone(),
      toTop: new THREE.Vector3(...target.topColor),
      toHorizon: new THREE.Vector3(...target.horizonColor),
      toBottom: new THREE.Vector3(...target.bottomColor),
      fromSpeed: uniforms.uAnimationSpeed.value,
      toSpeed: target.animationSpeed,
      fromType: uniforms.uAnimationType.value,
      toType: target.animationType,
      typeSwapped: false,
      duration,
      elapsed: 0,
    }
  }

  function dispose() {
    geometry.dispose()
    material.dispose()
  }

  return { mesh, uniforms, update, dispose, transitionTo }
}
