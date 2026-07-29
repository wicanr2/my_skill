# Remake architecture and reusable boundaries

## Clean rewrite boundary

Use the original binary only to establish behavior and formats. Express the remake with domain
types, small rules, injected RNG, explicit state transitions, and parsers that retain raw bytes when
semantics are incomplete.

Recommended dependency direction:

```text
cmd/product
  games/product/runtime
  games/product/rules
  games/product/data
        ↓
  engine/runtime  engine/render  engine/grid  engine/storage  engine/random
        ↓
  formats/legacy (only formats proven across products)
```

Do not initially extract combat, spells, towns, plot flags, product save layouts, or tile meanings.
They are commonly game-specific even when their names sound generic.

## Asset pipeline

For every format:

1. document header, dimensions, stride, planes, palette, bit order, and frame indexing;
2. write a decoder returning standard pixel data;
3. assert byte length and frame count;
4. dump an atlas and inspect recognizable frames;
5. compare an original screenshot;
6. keep original files outside version control.

Arithmetic success is not visual validation. Wrong dimensions and plane orders often divide the
file perfectly.

Represent presentation themes separately from source decode modes:

```text
ThemeOriginalEGA → EGA decoder + original atlas
ThemeOriginalCGA → CGA decoder + original atlas
ThemeModern      → validated replacement atlas
```

Preload complete theme groups and switch pointers atomically. A modern theme must preserve index,
anchor, direction, collision semantics, and secret information.

## Localization and fonts

- Store translations as overlays keyed by stable source identity.
- Verify source text drift, coverage, orphan keys, encoding, and fallback behavior.
- Use a bitmap font designed for the target size. Do not downscale a large CJK font and assume
  legibility.
- Keep line breaking, punctuation prohibition, and cell widths deterministic.
- Separate redistributable engine code from user-supplied proprietary fonts and game data.

## Engine extraction decision

First make code “extractable” inside the monorepo. Publish a generic module only after a second
legally held game passes:

- executable/toolchain comparison;
- graphics and palette visual oracle;
- map and coordinate schema comparison;
- record stride and consumer comparison;
- save round-trip comparison;
- minimal second adapter without product-name branches.

Shared company, sequel status, extensions, or visual resemblance are candidates for investigation,
not proof of a common engine.

