# Verification, README comparison, and handoff

## Test pyramid

1. Pure rule tests: fixed inputs and injected RNG.
2. Real-data parser tests: hashes, counts, anchors, malformed data.
3. Save round-trip and mutation diff tests.
4. Headless screen captures for stable states.
5. Original executable experiments.
6. Normal player-path vertical slice.
7. High-risk late-game sampling guided by a walkthrough.
8. Full packaging smoke on supported platforms.

Sampling is appropriate after mechanics and data-driven connectors are proven. Sample distinct rule
classes and high-risk state transitions, not merely geographically distant rooms.

## Screenshot comparison

Label every comparison with:

- original/remake build and platform;
- save hash or scenario;
- map and coordinate;
- RNG seed and clock;
- graphics mode/theme;
- whether it is exact-state, nearby-state, or layout-only.

Compare resolution, logical tile size, palette, viewport, typography, information hierarchy,
animation timing, controls, and intentional modernization. Never describe a nearby scene as a
pixel-perfect match.

## Player-path gate

Run without debug shortcuts:

- create a new character or start from the shipped default;
- move, enter/exit, acquire/equip/use, fight, heal/rest, save, quit, reload;
- verify writable save placement and that pristine originals are unchanged;
- check reachability/connectivity where a wrong spawn can soft-lock the game;
- repeat one late-game quest/state transition using a documented fixture.

## Handoff gate

Before stopping:

- ensure the worktree and running processes are understood;
- record exact HEAD and whether changes were pushed;
- list verified facts separately from open hypotheses;
- list commands and outputs for passing/failing gates;
- identify the next smallest reproducible action;
- link deep notes instead of pasting them;
- delete stale tasks contradicted by current evidence.

“Remaining work” must distinguish:

- implementation required;
- reverse engineering required;
- dynamic oracle required;
- visual/art production required;
- packaging/release required;
- optional modernization.

