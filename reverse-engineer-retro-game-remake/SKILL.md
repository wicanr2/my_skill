---
name: reverse-engineer-retro-game-remake
description: Reverse engineer 1980s–1990s games and build clean, cross-platform remakes with evidence-backed behavior, compiler／linker／runtime fingerprinting, decoded legacy assets, localization, deterministic tests, original-versus-remake screenshots, and player-path verification. Use for DOS/MZ or other legacy binaries, Ghidra/IDA analysis, unknown functions or data formats, original toolchain archaeology, clean-room engine rewrites, Traditional Chinese bitmap-font integration, remake parity audits, or handoff/worklist cleanup.
---

# Reverse engineer a retro game and remake it

Treat the original executable as a behavioral oracle. Reimplement typed, maintainable rules; do
not transliterate decompiler output or distribute copyrighted game data.

For an end-to-end project lifecycle—completion states, evidence contracts, toolchain triage,
spec gates, vertical slices, movement／event state, same-state comparison, localization,
audio-visual verification, statistical completion, licensing, packaging, promo media, and stopping
conditions—read
[`retro-remake-end-to-end-playbook.md`](../knowledge-base/re-methodology/retro-remake-end-to-end-playbook.md).
Treat any named game's thresholds, addresses, constants, and license choice as examples, not
universal rules.
For my own remakes the license is settled: copy `assets/project-template/LICENSE` (non-commercial
free, showcase and streaming expressly allowed, contribution grant-back, commercial by agreement)
and fill its `@…@` placeholders; the rationale per clause is in
`knowledge-base/retro/retro-remake-license-v2.md`.

When several platform versions of the same game exist, pick the rule／data source by whether its
game logic can be read statically (p-code／bytecode versus native code), keep the others as
cross-check oracles, and pin every rule to a byte signature; read
[`retro-remake-source-selection-and-byte-signatures.md`](../knowledge-base/re-methodology/retro-remake-source-selection-and-byte-signatures.md)
before choosing a source version or building the evidence JSON layer.

## Start from evidence

1. Inventory executables, data, platform variants, manuals, saves, screenshots, tools, and hashes.
2. Establish a writable research workspace. Mount or treat pristine originals as read-only.
3. Create the five ledgers from `assets/project-template/`:
   `WORKLOG.md`, `RESEARCH-LOG.md`, `REMAKE-PLAN.md`, `VERIFICATION-MATRIX.md`, and `HANDOFF.md`.
   Keep chronological work history in `WORKLOG.md`; never accumulate it in `README.md`.
4. Classify every claim as `proven`, `strong inference`, `hypothesis`, or `unknown`.
5. Attach an address, byte range, data diff, original screenshot, or reproducible experiment to
   every `proven` claim.

Read [references/evidence-and-re.md](references/evidence-and-re.md) when analyzing binaries,
jump tables, offsets, unknown fields, or conflicting notes.

## Fingerprint the original toolchain before product semantics

Before interpreting a large unknown-function inventory, identify the compiler family, linker and
executable format, platform runtime／DOS extender, middleware, drivers, packers, and custom asset
tools. Separate compiler-generated prologues, libraries, thunks, error paths, and middleware
wrappers from player-visible product code. Preserve exact versions only when version strings or
release-specific bytes prove them; copyright years and compatible signatures establish a family or
range, not an exact release.

Read [references/toolchain-and-runtime-fingerprints.md](references/toolchain-and-runtime-fingerprints.md)
when many unrelated functions share a callee／prologue, when investigating how an original game was
built, or before using unknown-function counts as remake work.

Read [references/borland-turbo-cpp-16-runtime-patterns.md](references/borland-turbo-cpp-16-runtime-patterns.md)
after direct binary evidence identifies Borland Turbo C++ 16-bit DOS, especially when classifying
32-bit arithmetic, huge-pointer, or near-to-far bridge helpers. Treat the patterns as candidates,
not cross-binary names or proof of an exact compiler version.

## Gate implementation through a spec

Never send RE conclusions directly into production code. Use this state machine:

```text
RE evidence → DRAFT spec → evidence review → READY spec
            → implementation → same-state verification → CONFORMED spec
```

Only a `READY` spec may authorize behavior, format, player-path, or fidelity changes. Disposable
probes may support a `DRAFT`, but cannot become production paths. If implementation exposes an
unknown, return to RE and revise the spec; do not silently guess in code or tests.

Read [references/spec-gated-workflow.md](references/spec-gated-workflow.md) before implementing
behavior derived from an executable, unknown data, screenshots, saves, or original playtests.

## Separate platform contracts from game RE

Before tracing standard DOS hardware timing or a documented platform API, read
[`retro-hardware-spec-first`](../knowledge-base/retro-cht/retro-hardware-spec-first/SKILL.md).
Use public specifications for PIT／DAC／DMA、BIOS and operating-system contracts. Record only the
game's chosen values, call sites, data flow, completion gate, and nonstandard behavior. Once the
remaining difference is BIOS、DOS TSR or device wall-clock detail, implement a reproducible
hardware-spec approximation and stop that RE branch unless the user explicitly requests hardware
archaeology.

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
Read [references/readme-standard.md](references/readme-standard.md) before creating or substantially
rewriting a remake README, completion summary, screenshot comparison, or release landing page.

For translated or dynamic UI, derive a text-safe rectangle from the visible／clickable control,
measure the active runtime font, and define width, height, line count, padding, overflow, and shared
center explicitly. Test the longest realistic CJK and English values, then capture the normal player
path at native logical size and production scale. Geometry-only tests do not prove glyph containment.

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
