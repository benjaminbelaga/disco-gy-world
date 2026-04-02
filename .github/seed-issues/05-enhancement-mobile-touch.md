# Mobile touch controls for 3D globe

**Labels:** enhancement, frontend, mobile

## Description

The 3D globe currently only supports mouse interaction. We need touch controls for mobile and tablet users.

## Requirements

- Pinch to zoom (two-finger gesture)
- Single finger drag to rotate the globe
- Double tap to zoom into a genre territory
- Swipe between Earth Mode and Genre World
- Touch-friendly UI panels (larger tap targets, bottom sheet for details)

## Use Case

Music discovery is often mobile-first. Many users will share DiscoWorld Passport links on social media, which open on phones.

## Alternatives Considered

- drei's `OrbitControls` supports touch natively but may need tuning for globe UX
- Custom gesture handler with `@use-gesture/react` for finer control

## References
- [drei OrbitControls](https://github.com/pmndrs/drei#orbitcontrols)
- [@use-gesture/react](https://use-gesture.netlify.app/)
