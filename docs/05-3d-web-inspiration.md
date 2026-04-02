# DiscoWorld: 3D Web Design Inspiration

## Award-Winning 3D Sites

| Site | Stack | What makes it special | Lesson for DiscoWorld |
|------|-------|----------------------|----------------------|
| [Lusion v3](https://lusion.co) | Three.js + custom shaders | SOTY 2023. Fluid physics, particle systems. Premium, not gimmicky | 3D must serve the content, not the reverse |
| [Bruno Simon](https://bruno-simon.com) | Three.js + Cannon.js | Driveable car in 3D world. Gamified navigation | Interaction = engagement. Consider "driving" through genre world |
| [Igloo Inc](https://www.awwwards.com/websites/sites_of_the_year/) | Heavy shader work | SOTY 2024-2025 | Shader quality = perceived quality |

## Globe / World Experiences

| Site | Tech | What to learn |
|------|------|--------------|
| [Globe.GL](https://globe.gl) | Three.js wrapper | Open-source. Fork-able for vinyl-planet prototype |
| [Stripe Globe](https://stripe.com/blog/globe) | Custom WebGL | Technical breakdown available. Arcs + glow aesthetic |
| [GitHub Globe](https://github.blog/2020-12-21-how-we-built-the-github-globe/) | Custom WebGL (not Three.js) | Dot-matrix sphere + data arcs. Atmosphere shader technique |

## Music + 3D

| Site | Stack | Relevance |
|------|-------|-----------|
| [Music Galaxy](https://cprimozic.net/blog/building-music-galaxy/) | Three.js + WebAudio | **Most directly relevant.** 70K+ Spotify artists as 3D point cloud. Spatial proximity = similarity |
| [Codrops 3D Audio Visualizer](https://tympanus.net/codrops/) | Three.js + GSAP + Web Audio API | Glowing orb reacting to beats. Tutorial available |
| [Airtight Interactive](https://www.airtightinteractive.com/demos/) | WebGL | Legendary music visualizers |

## Procedural Generation

| Project | Tech | Relevance |
|---------|------|-----------|
| [THREE.Terrain](https://github.com/IceCreamYou/THREE.Terrain) | Three.js | Noise-based heightmaps for terrain generation |
| [Procedural City Generator](https://medium.com/@Rototu/making-a-procedural-skyscraper-city-generator-with-three-js-and-webgl2-8f8b721bd044) | Three.js + WebGL2 | Shader-based skyscrapers. Directly applicable |
| [Procedural Planet GPGPU](https://discourse.threejs.org/t/procedural-planet-mesh-generator-gpgpu/69389) | Compute shaders | For vinyl-world terrain generation |
| [Azgaar's Fantasy Map Generator](https://azgaar.github.io/Fantasy-Map-Generator/) | Browser JS | Procedural continents, biomes, political boundaries. Best reference for "genre continents" |

## Aesthetic References

| Reference | What to take |
|-----------|-------------|
| [Synthrazer](https://synthrazer.com/) | Working synthwave aesthetic for retrowave district |
| GitHub Globe atmosphere shader | Atmospheric haze around the DiscoWorld planet |
| Spotify Wrapped Globe | Particle-based data arcs. Stream lines between countries |
| Townscaper | Color palette reference for organic world building |

## Design Rules (from research)

1. **Every 3D element must map to a data dimension.** Genre→terrain, era→altitude, labels→neighborhoods. No decoration without meaning.
2. **Load time < 3 seconds.** Use Draco compression (90-95% reduction), KTX2 textures (10x savings), GLB format.
3. **Mobile: cap at DPR 2.** Cut shadows, post-processing. Under 100 draw calls/frame.
4. **Dispose everything.** Three.js has no GPU garbage collection. Manual cleanup on scene transitions.
5. **Dark base (#0d1117) + genre-coded accent palette.** Warm amber (#f4a261) on near-black better than Spotify green for vinyl culture.
6. **Typography:** Space Grotesk (headers), JetBrains Mono (data). Both free.
