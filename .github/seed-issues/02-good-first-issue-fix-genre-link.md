# Fix genre connection: Breakbeat Hardcore should link to Jungle

**Labels:** good first issue, genre, bug

## Current State

Breakbeat Hardcore has no outgoing connection to Jungle in our genre graph, but historically Jungle evolved directly from Breakbeat Hardcore in the early 1990s (UK rave scene, ~1991-1993).

## Proposed Change

Add a directed edge from Breakbeat Hardcore → Jungle with relationship type `evolved_into`.

## How to fix

1. Check `data/ishkur-dataset/` for the original connection data
2. Add the link in the appropriate data file
3. Run `python packages/pipeline/taxonomy_bridge.py` to verify the graph

## Sources
- Ishkur's Guide v3 shows this connection
- [Wikipedia — Jungle music](https://en.wikipedia.org/wiki/Jungle_music)
