---
name: reverse-engineer-borland-dos-pc98
description: Reverse engineer Borland and Turbo Pascal DOS or PC-98 binaries with MZ load-image boundaries, embedded 0x52FB debug symbols, Turbo Pascal TPOV overlays, resident-to-overlay calls, and PC-98 interrupt drivers. Use for GAME.EXE/GAME.OVR, Borland debug names, symbol-to-segment mapping, overlay control records, INT D2h music callers, IDA/Ghidra imports, or SSI Gold Box PC-9801 executable research.
---

# Reverse Engineer Borland DOS／PC-98

Treat embedded Borland debug information as first-class evidence before naming
procedures from decompiler guesses. Keep all binary analysis, conversion, disassembly,
testing, and tool execution inside a bounded Docker container.

## Reference loading

- Read [references/borland-debug-and-overlay-notes.md](references/borland-debug-and-overlay-notes.md)
  for the compact workflow, legacy record layouts, and validation checks.
- Search `references/borland-open-architecture.txt` for exact structures. Useful search
  terms include `debug_header`, `symbol_record`, `module_record`, `Names Table`, and
  `pascal overlay`.
- Consult `references/Turbo_Pascal_7_Programmers_Reference_1992.pdf` when compiler,
  overlay manager, calling convention, or runtime-library behavior matters.
- Keep `references/BC4BOA.ZIP` as the pristine archive. Do not execute its bundled DOS
  utilities; use the extracted text reference instead.
- Read [references/SOURCES.md](references/SOURCES.md) before redistributing any bundled
  historical document.

## Workflow

1. Hash every input and preserve a read-only research copy.
2. Derive the DOS MZ load-image size from `e_cp` and `e_cblp`. Inspect bytes after that
   boundary for `FB 52`; do not assume the filesystem EOF is executable code.
3. Decode the debug header according to its version. Borland C++ 4 documentation uses
   wider counts than older 16-bit Turbo Pascal tables; validate all widths against file
   bounds and observed table sizes.
4. Enumerate the name pool exactly and map name indexes to symbol records. Promote a
   routine name only when index, record, segment, and executable address all validate.
5. Parse overlay control records from the resident executable. For `TPOV`, separate
   executable bytes from relocation data before scanning opcodes.
6. Trace resident wrappers, interrupt-vector calls, and driver contracts. A missing
   literal `CD xx` does not prove an interrupt is unused; check indirect calls and
   installed vectors.
7. Cross-check static conclusions with runtime traces in DOSBox-X, NP2kai, or another
   appropriate emulator. Record platform, input hash, addresses, and confidence.
8. Store title-specific addresses and behavior in the project repository. Promote only
   reusable format knowledge into this skill.

## Evidence rules

- Distinguish file offsets, load-image offsets, runtime `segment:offset`, and overlay
  local offsets in every report.
- Exclude relocation tables, appended debug data, names, and packed resources from
  instruction searches.
- Do not infer scene-to-track mappings from symbol names alone. Require a caller,
  argument value, or runtime trace.
- Cite the exact reference section and input hash for parsed structures.
- Never bundle proprietary game binaries, disk images, commercial debugger executables,
  or extracted game assets in this skill.
