# Evidence and reverse-engineering workflow

## Contents

1. Evidence ladder
2. Binary entry workflow
3. Address and control-flow checks
4. Unknown data fields
5. Dynamic experiments
6. Research closure

## 1. Evidence ladder

| Level | Acceptable basis | Wording |
|---|---|---|
| Proven | instruction/data address plus consumer; byte diff; original run | “is”, “verified” |
| Strong inference | independent schema/value/consumer agreement | “strong inference” |
| Hypothesis | plausible pattern with one evidence class | “may”, “candidate” |
| Unknown | contradictory or absent evidence | “unknown” |

Never promote a claim because an old note says “verified”. Recheck its cited evidence.

## 2. Binary entry workflow

1. Hash and parse executable headers. Identify native executable, overlay, bytecode, or loader.
2. Export strings, functions, disassembly, relocations, and decompiler output.
3. Anchor subsystem discovery with unique UI strings, magic constants, table bases, interrupts,
   file names, and save offsets.
4. Follow both callers and consumers. Record function boundaries and data flow in one research note.
5. Use a second disassembler or direct byte decoding for high-impact conclusions.

For MZ real mode, derive rather than assume:

```text
file_offset = (segment - analysis_load_base) * 16 + offset + header_paragraphs * 16
```

Verify the formula using at least three known strings read back from the raw binary.

## 3. Address and control-flow checks

Treat decompiler output as untrusted when:

- output lines greatly exceed function bytes;
- unreachable-block warnings are numerous;
- an indirect jump has no recovered cases;
- code gaps sit behind a switch;
- a far-call segment differs by the loader base;
- a claimed call site cannot be found in raw instructions.

Decode jump-table words directly. In Ghidra, listing references alone do not repair decompiler
p-code; write a `JumpTable` override. IDA can be a stronger code-discovery oracle even when no
16-bit Hex-Rays decompiler is available.

## 4. Unknown data fields

For each record:

1. Preserve raw fields before naming them.
2. Dump all values and distributions.
3. Compare same-name or same-sprite records across tables.
4. Trace loader writes into runtime structures.
5. Trace every meaningful consumer: formula, branch, display string, save write.
6. Rename only after evidence is stable; update parser, tests, docs, and runtime wiring together.

A resolved field that is never copied into the remake runtime is still an implementation bug.

## 5. Dynamic experiments

Prefer boundary injection over long input scripts:

- write counter `limit-1` and `limit`, then perform one action;
- set encounter countdown to one;
- clone a save and modify exactly one field;
- fix RNG seed and state;
- capture before/after bytes, screen, and log.

Use adjacent values to distinguish off-by-one conditions. Keep original data immutable; run from a
copy or writable overlay.

## 6. Research closure

Close a topic only when the note includes:

- question and prior ambiguity;
- tool/version and input hash;
- exact address/offset evidence;
- behavioral interpretation;
- remake mapping;
- verification method;
- remaining uncertainty.

Then search the entire repository for stale claims and update the worklist’s single source of truth.

