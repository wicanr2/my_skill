# Toolchain and compiler-runtime fingerprinting

## Contents

1. Why this is an early remake gate
2. Evidence matrix
3. Workflow
4. Runtime pattern classification
5. Cultural and clean-room outputs

## 1. Why this is an early remake gate

Before interpreting unknown functions as game logic, identify the compiler, linker, executable
format, DOS extender／platform runtime, middleware, drivers, packers, and custom asset tools.
Compiler-generated prologues, library code, thunks, error paths, and middleware wrappers can form
hundreds of cross-subsystem callers. Classifying them first reduces false product semantics and
prevents repeatedly reverse engineering the same runtime pattern.

Do not turn this into a completion metric. The objective is to separate product behavior from
toolchain output and preserve historically meaningful tooling, not to name every library routine.

## 2. Evidence matrix

Record each component independently:

| Component | Strong anchors | Common overclaim |
|---|---|---|
| Compiler family | embedded runtime copyright, startup ABI, multiple codegen idioms, FLIRT／signature match | copyright year proves exact compiler version |
| Linker／executable format | header magic and fields, overlay／fixup layout, linker strings | LE／NE／PE alone proves one linker version |
| DOS extender／platform runtime | bundled binary version string and hash, startup handoff, imported API | every protected-mode helper is game code |
| Middleware | versioned config／driver strings, API wrappers, resource signatures | one old driver version defines the entire middleware release |
| Packer／protector | entry stub, decompression transition, section entropy／layout, exact tool marker | unusual entry point always means packing |
| Custom tools | asset header signature, author／date, multiple real resources, player consumer | asset format name proves editor implementation details |

Use `proven`, `strong inference`, `hypothesis`, or `unknown`. Exact versions require an exact
version string, deterministic signature, release-specific bytes, or independently matching tool
output. A year range or compatible FLIRT family is not an exact version.

## 3. Workflow

1. Hash the executable, bundled extender, setup tools, drivers, configs, and representative assets.
2. Parse primary and secondary executable headers; record every address space separately.
3. Extract printable strings with file offsets, but treat them as leads until code／data consumers
   confirm they belong to the shipped path.
4. Run IDA first when required: apply configured signatures, export original names／flags／xrefs,
   and preserve unmatched functions as unknown.
5. Identify high-fan-in functions shared across unrelated subsystems. Inspect the body and failure
   consumer before labeling them runtime.
6. Cluster repeated prologues, epilogues, allocation, division, string／memory, exception, stack,
   thunk, I/O, and middleware-wrapper patterns. Validate at least three callers when using a pattern.
7. Build a non-destructive index: original location＋semantic＋confidence＋evidence＋scope. Never
   batch rename merely from caller count, mnemonic shape, or a decompiler-generated name.
8. Remove proven runtime calls from product-call statistics, then re-rank the remaining unknowns by
   player impact, writer／consumer closure, and existing research footprints.
9. Document the original toolchain as cultural history: commercial components, in-house tools,
   credited authors, dates, formats, and what remains uncertain.

## 4. Runtime pattern classification

For each candidate, record:

- exact function range and raw bytes;
- original analysis name and tool flags;
- representative callers before／after the call;
- inputs, outputs, preserved registers, stack net effect, and global side effects;
- success and failure consumers;
- whether the remake needs equivalent behavior or relies on the modern runtime;
- reopen conditions.

Distinguish similar patterns. For stack handling, separate stack-limit checks, page-touch probes,
and stack-grow allocators. For audio, separate game-owned cue wrappers from middleware library
functions. For BIOS／DOS helpers, preserve game-selected parameters but take documented platform
contracts from specifications rather than re-deriving hardware behavior.

Stop when direct evidence proves a helper is toolchain/runtime-only and it has no player-state side
effect. Do not transliterate it into the remake. Continue through the caller after the helper because
the real frame allocation, argument layout, and product calls still matter.

## 5. Cultural and clean-room outputs

Maintain two outputs:

1. A version-bound project evidence note with hashes, offsets, addresses, bytes, tool versions, and
   confidence levels.
2. A reusable pattern reference containing only the general method and validated signatures, with
   no proprietary binary, copyrighted asset, license, or project-only conclusion.

The clean-room remake may replace the compiler runtime, DOS extender, hardware driver, and
middleware internals. It should preserve player-visible choices such as file formats, cue selection,
timing gates, input behavior, and asset-tool cultural attribution when evidence supports them.
