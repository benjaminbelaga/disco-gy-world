# DiscoWorld: Open Source Strategy

## The Playbook: WordPress Model (adapted)

### Lessons from Industry

| Company | Model | Lesson for DiscoWorld |
|---------|-------|----------------------|
| **Android/Google** | AOSP open, Play Services proprietary | Open layer must be useful standalone for YEARS before proprietary layer. Timeline: 5+ years |
| **WordPress/Automattic** | .org open, .com commercial | BEST MODEL. Founder openly runs both. Backlash only on trademark enforcement (WP Engine 2024) |
| **Elastic** | Open core → SSPL after AWS fork | Community/data moat > code moat. Our case is safer (data network effect) |
| **GitLab** | CE vs EE, "buyer-based" split | Features free if individuals need them, paid if orgs need them |
| **HashiCorp** | MIT → BSL switch | NEVER switch licenses after trust is built. Pick right from day 1 |
| **Mapbox** | BSD v1 → proprietary v2 | MapLibre fork happened instantly. Permissive license = can't take back |

---

## License Decision: AGPL-3.0

**Why AGPL:**
- Prevents cloud providers from hosting a closed fork (Elastic lesson)
- Doesn't scare individual contributors
- Signals "genuinely open but protected"
- If someone forks and hosts it, they must open-source their modifications

**NOT MIT/Apache** — too permissive, a competitor could close-source a fork.
**NOT BSL/SSPL** — too restrictive, scares contributors and signals "not really open."

---

## GitHub Organization

**Create: `github.com/discoworld`** — NOT `benjaminbelaga` or `yoyaku`.

Repos under this org:
- `discoworld/discoworld` — main app (AGPL-3.0)
- `discoworld/pipeline` — data pipeline (AGPL-3.0)
- `discoworld/contrib` — contribution SDK (MIT — to encourage adoption)
- `discoworld/docs` — documentation (CC BY 4.0)

---

## Founder Transparency

**State it openly in README:** "Created by Ben Belaga, who also runs YOYAKU records in Paris."

**Why be transparent:**
- Hiding it and having it discovered later = devastating (Elastic/HashiCorp backlash)
- WordPress model: Mullenweg never hid his Automattic role
- Vinyl community values authenticity above all else
- Being a record store owner ADDS credibility for a music discovery project

---

## The Phased Integration (Critical Sequencing)

### Phase 1 — Pure Community (Months 0-6)
- Zero YOYAKU branding, zero commercial features
- Focus: map, data, community contributions, Discogs integration
- Public roadmap on GitHub Projects
- Seek contributors from OUTSIDE YOYAKU
- Decisions made in public GitHub Issues
- Launch on Reddit (r/TheOverload, r/vinyl, r/musicproduction), Hacker News
- **Goal: project has identity independent of YOYAKU**

### Phase 2 — Generic Store API (Months 6-9)
- Announce "Record Store Plugin" system
- Define `RecordStoreAdapter` interface (open, documented)
- Ship reference implementation for a MOCK store
- Document so Phonica/Hard Wax/anyone could build their own
- **YOYAKU is NOT the first to integrate** — ship the API first, let it breathe

### Phase 3 — YOYAKU Integrates (Months 9-12)
- YOYAKU adapter is "just one implementation" of the store plugin
- Natural because Ben built both — community understands
- YOYAKU happens to have richer data (pressing, distribution, arrivals)
- Other stores invited to integrate too (genuine invitation, not lip service)

### Phase 4 — YOYAKU Advantage Emerges (Month 12+)
- "Currently pressing" data (Objects) — only YOYAKU has this
- Distribution arrival notifications — only YOYAKU has this
- In-store session tracklists → map → commerce pipeline
- These features are AVAILABLE to anyone with the data — but only YOYAKU has the data
- **This is the Play Services moment** — the open platform works alone, but the YOYAKU integration makes it 10x better

---

## Fork Risk Assessment

**Low concern.** The value isn't the code:
- **Data moat:** Map positions, community contributions, store inventory = network effect
- **Curation moat:** Genre classifications, building heights, biome assignments = editorial work
- **Community moat:** User collections, crate neighbors graph, DJ charts = social graph
- A fork without the dataset is an empty shell

This is the Android pattern: AOSP runs, but without Play Services (data, users, network) it's useless.

---

## Community Trust Checklist

- [ ] Public roadmap (GitHub Projects board)
- [ ] CONTRIBUTING.md with clear guidelines
- [ ] Code of Conduct (Contributor Covenant)
- [ ] Outside contributors before any commercial features
- [ ] Store plugin system announced and documented BEFORE YOYAKU integrates
- [ ] Monthly "State of DiscoWorld" blog post (transparent metrics)
- [ ] Discord or Matrix community for contributors
- [ ] First 6 months: zero mention of commerce/stores in marketing
