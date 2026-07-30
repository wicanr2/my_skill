---
name: compose-rpg-remake-music
description: Design distinctive, evidence-grounded music briefs and generation prompts for classic RPG remakes, including D&D-like fantasy, Gold Box, dungeon crawlers, exploration, towns, dungeons, turn-based combat, bosses, trailers, leitmotifs, loops, adaptive stems, MIDI mockups, sound-effects integration, and music-rights records. Use when a remake needs new music, trailer scoring, Suno/Udio prompts, orchestral direction, original-hardware sound identity, or when multiple retro projects risk receiving the same generic “epic fantasy” soundtrack.
---

# Compose RPG remake music

Build music from the game’s identity and player state, not from genre adjectives alone. Never
present new remake music as an unreleased original soundtrack.

## Start with evidence

Before drafting a prompt, inspect the project’s audio research, original executable/data, manuals,
screenshots, story, gameplay states, and rights notes. Record:

1. original year, platform, sound hardware, and whether BGM existed;
2. three core player actions;
3. three audible world materials or cultures;
4. every proven original melody, interval, rhythm, or sound effect;
5. required states: exploration, town, dungeon, danger, combat, boss, victory, defeat, trailer;
6. output contract: linear cue, seamless loop, stinger, synchronized stems, or fixed timecode;
7. what must be labeled as original, arrangement, or entirely new work.

Classify uncertain musical claims as proven, strong inference, hypothesis, or unknown. Do not
invent an “original theme” from an unlabeled byte table.

## Create the project sound identity

Complete this sentence:

> `[player action]` in a world made of `[three materials/cultures]`, identified by
> `[3–7 note/rhythm motif]`, heard through `[era treatment]`, with victory meaning
> `[triumph/survival/tragedy/unresolved cost]`.

Choose a 3–7 note motif unique to the project. Prefer a legally usable, verified original cue;
otherwise compose a new motif and document its notes. State how it transforms:

- exploration: sparse, low, elongated;
- danger: incomplete or rhythmically compressed;
- combat: pulse or ostinato fragment;
- boss: inverted, reharmonized, or transferred to antagonist timbre;
- victory/ending: resolved, interrupted, or deliberately left open.

Do not name living composers or request imitation of a specific franchise soundtrack. Describe
the musical mechanics instead.

## Write prompts in seven layers

Always specify:

1. purpose and exact length;
2. world and historical identity;
3. gameplay state and emotional arc;
4. explicit motif behavior;
5. instrumentation with each section’s role and entry point;
6. form, loop boundary, stems, transitions, and mix deliverables;
7. exclusions, authenticity label, and rights requirements.

Weak: `epic D&D orchestral soundtrack`.

Strong: `90-second seamless frozen-coast exploration loop; cello states B-A-B-C-G-C once every
14 seconds; basses sustain open fifths; frame drum enters only after danger rises; separate
ambience/harmony/pulse stems; no choir, EDM drop, constant ostinato, or heroic major cadence`.

Read [references/prompt-patterns.md](references/prompt-patterns.md) for scene templates and QA.

## Design for interaction

For gameplay, do not deliver only a stereo master. Prefer a hybrid of:

- horizontal resequencing: exploration → danger bridge → combat;
- vertical layering: ambience + harmony + pulse + threat;
- short stingers: discovery, danger, victory, defeat;
- bar-aligned transition points and reverb-safe loop tails.

Require synchronized stems with identical start, duration, sample rate, and bar grid. Test every
allowed stem combination for harmony, phase, loudness, and clipping.

For a trailer, use fixed timecodes and preserve dynamic contrast. Include at least one genuine
low-density or silent beat before the climax. Leave spectral space for dialogue and authentic
game sound effects.

## Keep projects distinct

Do not copy the previous project’s prompt or design tokens. Change at least three:

- sonic geography/materials;
- rhythmic ethic: march, breath, ritual, rowing, investigation;
- motif source;
- treatment of original hardware sound;
- emotional cost of victory.

Run a blind identity check: without filenames, a listener should describe this game’s world, not
only say “fantasy”.

## Protect rights and truthfulness

Save the platform, model version, date, full prompt, seed, generation chain, subscription tier,
terms snapshot, source motif, human MIDI/audio edits, and intended uses. Recheck current service
terms before public or commercial release; generation rights and download rules change.

Prefer, in order:

1. commissioned/human composition with written rights;
2. project-authored MIDI rendered with a redistributable SoundFont or owned library;
3. a verified licensed generation service/tier;
4. a music library explicitly licensed for the intended use.

Never infer that “royalty-free” means public domain, sublicensable, or suitable for source-code
distribution.

## Validate

Check:

- identity blind test;
- three-loop fatigue;
- dialogue and UI audibility;
- seamless waveform and reverb at loop points;
- transition timing;
- arbitrary stem combinations;
- integrated loudness and true peak;
- original/remake labeling;
- reproducible source and rights record.

For trailers, inspect the waveform to confirm the intended build, pre-climax void, climax, and
tail exist at their specified times. Listening remains mandatory; a valid file is not musical
approval.

