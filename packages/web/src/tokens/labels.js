// Typography + LOD tokens for the GenreWorld 3D labels.
//
// This module was extracted during PR #15 ("LOD labels phase B") but the
// file itself was never committed, leaving GenreWorld.jsx importing a
// missing module. Restored from the project's own specs:
//   - LABEL_TOKENS : audit-2026/EXECUTION-PLAN.md §PR-12B
//   - TIER_LOD     : original inline values from commit 9a2b131 (PR #11)
export const LABEL_TOKENS = {
  // Spec named Medium/SemiBold .woff, but only the variable woff2 ships in
  // public/fonts — point at what actually exists so labels don't 404.
  font: '/fonts/SpaceGrotesk-Variable.woff2',
  fontBold: '/fonts/SpaceGrotesk-Variable.woff2',
  tiers: {
    0: { size: 2.2, weight: 'bold', tracking: 0.22, case: 'upper', colorMode: 'biome' },
    1: { size: 1.6, weight: 'medium', tracking: 0, case: 'sentence', colorMode: 'genre' },
    2: { size: 1.1, weight: 'medium', tracking: 0, case: 'sentence', colorMode: 'genre-muted' },
    3: { size: 0.85, weight: 'medium', tracking: 0, case: 'sentence', colorMode: 'genre-muted' },
    4: { size: 3.0, weight: 'medium', tracking: 0.3, case: 'upper', color: '#d4a574', alpha: 0.35 },
  },
  outline: { width: '8%', color: '#1c1917', opacity: 1, blur: '15%' },
  minPixelSize: 11,
}

// Per-tier level-of-detail: distance fade window + proportional font sizing.
// fontSize = baseSize + sqrt(trackCount/maxTrackCount) * weightScale
export const TIER_LOD = {
  0: { fadeStart: 140, fadeEnd: 220, baseSize: 2.2, weightScale: 1.6 },
  1: { fadeStart: 80, fadeEnd: 140, baseSize: 1.4, weightScale: 1.4 },
  2: { fadeStart: 45, fadeEnd: 80, baseSize: 0.95, weightScale: 0.7 },
  3: { fadeStart: 20, fadeEnd: 38, baseSize: 0.7, weightScale: 0.3 },
  4: { fadeStart: 200, fadeEnd: 320, baseSize: 3.0, weightScale: 0 },
}
