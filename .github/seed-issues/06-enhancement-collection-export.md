# Collection export as shareable image

**Labels:** enhancement, feature, frontend

## Description

After connecting a Discogs collection, users should be able to export their "DiscoWorld Passport" — a shareable image showing their musical footprint on the globe.

## Requirements

- Render a styled card with:
  - User's globe view with collection highlights
  - Musical DNA breakdown (top genres, countries, decades)
  - Stats: total releases, rarity score, collection breadth
  - DiscoWorld.fm branding and URL
- Export as PNG (for sharing on social media)
- "Share" button that copies image or opens native share sheet

## Use Case

Shareable collection cards drive organic growth. Users post them on Reddit, Twitter, and Discord — each card is an advertisement for DiscoWorld.

## Technical Approach

- Use `html2canvas` or Three.js `renderer.domElement.toDataURL()` for the globe snapshot
- Overlay stats with Canvas 2D or SVG
- Target dimensions: 1200x630 (Open Graph) and 1080x1080 (Instagram)
