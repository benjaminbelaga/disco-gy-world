---
title: "Improve Strudel patterns for underrepresented genres"
labels: ["enhancement", "audio", "help wanted"]
---

## What

DiscoWorld generates Strudel live coding patterns for each genre biome. Some biomes could use more musically accurate patterns. Help us make them sound better!

## Current Coverage

See `packages/web/src/lib/strudelPatterns.js` for the current biome→pattern mappings.

13 biomes covered: techno-massif, house-plains, disco-riviera, ambient-depths, jungle-canopy, trance-highlands, industrial-wasteland, idm-crystalline, dubstep-rift, garage-district, urban-quarter, source-monuments, unknown.

## How to Improve

1. Open the Strudel player (press L) and navigate to different genres
2. Listen to the generated pattern — does it capture the genre's feel?
3. Edit `strudelPatterns.js` to improve:
   - BPM ranges per scene
   - Scale choices per biome
   - Sound selections (use `gm_*` General MIDI sounds from Strudel)
   - Rhythmic patterns (mini-notation)
4. Test with the Strudel editor and submit a PR

## Resources

- [Strudel documentation](https://strudel.cc)
- [Mini-notation reference](https://strudel.cc/learn/mini-notation)
