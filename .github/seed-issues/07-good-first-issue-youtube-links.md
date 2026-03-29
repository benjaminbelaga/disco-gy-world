---
title: "Add YouTube links for 10 genre tracks"
labels: ["good first issue", "data", "help wanted"]
---

## What

Many genre territories in DiscoWorld have tracks listed but no YouTube links. Help us connect these tracks to playable audio.

## How

1. Pick a genre from [the world.json file](packages/web/public/data/world.json)
2. Find tracks that have `youtube: null`
3. Search YouTube for the track (artist + title)
4. Add the YouTube URL to the track entry
5. Submit a PR

## Acceptance Criteria

- [ ] At least 10 tracks updated with valid YouTube URLs
- [ ] URLs use the `https://www.youtube.com/watch?v=` format
- [ ] Tracks are verified to be the correct version (original, not a cover/remix unless specified)

## Notes

Focus on iconic/defining tracks for each genre first. The enrichment pipeline (`packages/pipeline/enrich_youtube.py`) can also be used for bulk updates.
