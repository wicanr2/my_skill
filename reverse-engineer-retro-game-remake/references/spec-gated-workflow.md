# Spec-gated remake workflow

Use `DRAFT`, `READY`, `CONFORMED`, and `SUPERSEDED` as explicit spec states.

- `DRAFT`: behavior-changing unknowns remain; research and disposable probes only.
- `READY`: evidence supports typed inputs, state transitions, boundaries, outputs, and acceptance tests.
- `CONFORMED`: implementation passes its internal checks and every applicable original-oracle check.
- `SUPERSEDED`: later evidence invalidated the spec; retain the old evidence and correction reason.

A `READY` spec records scope, excluded scope, input/version hashes, tool and address space, original
addresses/offsets/bytes/xrefs or experiments, claim grades, typed behavior, failure modes, vertical
player-path impact, save impact, internal tests, original-oracle tests, known differences, stop lines,
and rights boundaries.

Implementation may not promote a hypothesis by encoding it. When code exposes a missing case, move
the spec back to `DRAFT`, collect evidence, and review it again. Pure refactors that do not change
behavior need no new RE spec, but must preserve existing tests and contracts.
