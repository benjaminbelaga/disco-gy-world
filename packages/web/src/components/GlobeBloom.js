/**
 * UnrealBloomPass at half resolution for premium glow.
 * Applied to globe.gl's renderer directly.
 */
import * as THREE from 'three'
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js'
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js'
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js'
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js'

/**
 * @param {THREE.WebGLRenderer} renderer
 * @param {THREE.Scene} scene
 * @param {THREE.Camera} camera
 * @returns {{ composer: EffectComposer, resize: Function, cleanup: Function }}
 */
export function setupBloom(renderer, scene, camera) {
  const size = renderer.getSize(new THREE.Vector2())

  const composer = new EffectComposer(renderer)
  composer.setSize(size.x, size.y)
  composer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5))

  const renderPass = new RenderPass(scene, camera)
  composer.addPass(renderPass)

  // Half-res bloom for performance
  const bloomPass = new UnrealBloomPass(
    new THREE.Vector2(size.x / 2, size.y / 2),
    1.2,    // strength
    0.4,    // radius
    0.8     // threshold
  )
  composer.addPass(bloomPass)

  const outputPass = new OutputPass()
  composer.addPass(outputPass)

  const resize = (width, height) => {
    composer.setSize(width, height)
    bloomPass.resolution.set(width / 2, height / 2)
  }

  const cleanup = () => {
    composer.dispose()
  }

  return { composer, resize, cleanup }
}
