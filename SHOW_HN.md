# Show HN: DiscoWorld — Explore 5M electronic releases as a 3D world

DiscoWorld maps millions of music releases into an explorable 3D world where spatial proximity reflects musical similarity. Two modes:

**Genre Planet** — A procedural planet where 166 genres form continents. Techno mountains, ambient oceans, house plains. Each territory has its own ambient soundscape synthesized in real-time via Web Audio API. Click a territory to hear genre-appropriate live coding patterns (powered by Strudel). Buildings grow as sub-genres emerge through decades.

**Earth Globe** — Real geography with 7K+ record shops from OpenStreetMap, 30K geocoded labels from Discogs, and city scenes from Detroit to Berlin to Tokyo. Distribution arcs trace how genres traveled across continents.

**Discovery** — Connect your Discogs collection (no account needed) to see your musical footprint, get personalized recommendations via hybrid collaborative + content-based filtering, and find "crate neighbors" — collectors with similar taste.

Built with: React 19, Three.js r183, globe.gl, React Three Fiber, FastAPI, SQLite. Strudel for live coding. 4.87M releases from the Discogs CC0 data dump. 280+ automated tests.

AGPL-3.0 licensed. Data CC0. Zero account required for first exploration. RecordStoreAdapter plugin API for any shop to integrate.

The idea: what if you could walk into the world's largest record shop and the crates organized themselves around you?

https://github.com/benjaminbelaga/discoworld
