import { EffectComposer, Bloom } from '@react-three/postprocessing'

// Bloom post-processing — desktop only. Extracted to own module so the
// ~397KB @react-three/postprocessing chunk can be lazy-imported
// (audit 2026-04-17 AGENT-E perf note: was statically imported and
// shipped to mobile despite runtime gate).
export default function AudioReactiveBloom() {
  return (
    <EffectComposer>
      <Bloom
        luminanceThreshold={0.35}
        luminanceSmoothing={0.5}
        intensity={0.55}
        mipmapBlur={false}
      />
    </EffectComposer>
  )
}
