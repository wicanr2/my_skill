---
name: reverse-engineer-retro-game-remake
description: Reverse engineer 1980s–1990s games and build clean, cross-platform remakes with evidence-backed behavior, decoded legacy assets, localization, deterministic tests, original-versus-remake screenshots, and player-path verification. Use for DOS/MZ or other legacy binaries, Ghidra/IDA analysis, unknown map/save/item/monster/graphics formats, clean-room engine rewrites, Traditional Chinese bitmap-font integration, remake parity audits, or handoff/worklist cleanup.
---

# Reverse engineer a retro game and remake it

Treat the original executable as a behavioral oracle. Reimplement typed, maintainable rules; do
not transliterate decompiler output or distribute copyrighted game data.

## Start from evidence

1. Inventory executables, data, platform variants, manuals, saves, screenshots, tools, and hashes.
2. Establish a writable research workspace. Mount or treat pristine originals as read-only.
3. Create the four ledgers from `assets/project-template/`:
   `RESEARCH-LOG.md`, `REMAKE-PLAN.md`, `VERIFICATION-MATRIX.md`, and `HANDOFF.md`.
4. Classify every claim as `proven`, `strong inference`, `hypothesis`, or `unknown`.
5. Attach an address, byte range, data diff, original screenshot, or reproducible experiment to
   every `proven` claim.

Read [references/evidence-and-re.md](references/evidence-and-re.md) when analyzing binaries,
jump tables, offsets, unknown fields, or conflicting notes.

## Build vertical slices

Work in this order:

1. Decode one real asset or record and render/dump it.
2. Implement one rule end-to-end: source bytes → typed parser → rule → UI → save round-trip.
3. Compare against the original at the same state, coordinate, seed, and theme.
4. Only then generalize the subsystem or batch-convert remaining content.

Keep layers one-way:

```text
platform/UI → game adapter/rules → parsed data
            → reusable runtime/render/grid/storage/RNG
```

Do not call product-specific rules a generic engine until a second real game consumes the same
API without product-name branches.

Read [references/remake-architecture.md](references/remake-architecture.md) for package boundaries,
localization, theme handling, and engine-extraction gates.

## Validate with independent oracles

Require all applicable checks:

- parser invariants: record count, stride, bounds, round-trip, and real-file anchors;
- visual dumps: atlas/contact sheet plus human inspection;
- deterministic rule tests with fixed RNG and save fixtures;
- original executable experiments using adjacent boundary values;
- normal player path without teleport, grant-item, forced-win, or other debug hooks;
- stop a sampled player path immediately after a legitimate whole-party wipe; record the wipe as the terminal outcome, never continue issuing post-death inputs, and never silently remove the sample from parity statistics;
- save/load from a writable overlay without modifying pristine originals;
- original/remake screenshots labeled with state, coordinate, seed, mode, and known differences;
- build, static analysis, translation checks, packaging smoke, and dirty-tree review.

Read [references/verification-and-handoff.md](references/verification-and-handoff.md) before
claiming completion, doing sampling, writing README comparisons, or handing work to another agent.

## Avoid recurring false conclusions

- File-size divisibility proves only that a layout is possible. Render it and compare.
- Decompiled C can silently invent control flow around 16-bit jump tables. Read instructions and
  raw table words; use a decompiler jump override when available.
- A field name is not evidence. Trace both its write origin and at least one consumer.
- A passing unit test against the remake validates internal consistency, not original parity.
- A debug-assisted completion path does not prove the game is normally playable.
- A stale worklist can contradict already-resolved research. Audit documents against code and
  evidence before starting new reverse engineering.
- Theme switching must exchange complete, prevalidated asset groups atomically; never show a
  half-loaded atlas.
- Preserve source formats and theme identities. Do not call CGA an inferior EGA setting or a
  modern redraw an original restoration.

## Use the bundled project template

Copy `assets/project-template/` into a new project’s documentation area and fill every bracketed
field. Keep the handoff short enough to reread at the start of each session; link deep research
instead of duplicating it.
