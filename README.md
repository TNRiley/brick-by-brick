# 🧱 Brick by Brick

**Every piece in 18,000 LEGO sets, counted by colour and year. The classic six colours went from 89% of the bricks to 40%, and the greys changed overnight.**

→ **[Open it](https://tnriley.github.io/brick-by-brick/)**

Rebrickable's parts lists for every official LEGO set, 1949 to 2026, counted by colour. Each year becomes a column of studs, and the page is styled as an instruction booklet with a 3D house behind it that builds itself as you scroll and repaints in each era's colours. Red, yellow, blue, white, black and green were 89% of 1970s pieces and are 40% now. In 2004 the old greys fell from about a fifth of all pieces to 3% within a year, replaced by the bluish greys, and Brown became Reddish Brown at the same moment. The number of colours making up at least 0.1% of a year's pieces grew from 10 in 1975 to 52 in 2004, was cut to 34 by 2007, and has since grown back with nougats, azures, lavenders and coral. You can see every theme's palette and tip out any set to compare it with another, such as the 1979 and 2022 Galaxy Explorer.

## Running it

One self-contained HTML file. No build step, no server, no network access at runtime — open `index.html` in a browser, or serve the directory with any static host.

```bash
python3 -m http.server 8000   # then visit http://localhost:8000
```

## Rebuilding it from scratch

[REBUILD.md](REBUILD.md) is written for an LLM with a shell and nothing else: the data sources and their quirks, the processing decisions, the page's structure and interactions, and a table of expected values to check the result against.

## Source

The full build pipeline is in [`src/`](src/), with a README describing how to regenerate the page from scratch.

## Data

- **[Rebrickable LEGO catalogue downloads: colors, themes, sets, inventories, inventory_parts](https://rebrickable.com/downloads/)** — Free to use for any purpose, including commercial, with acknowledgement of Rebrickable as the source

Every figure on the page is computed from the data shipped with it. Check the page's own methods panel for how each number is derived and where it should not be pushed.

## Built with

python 3 stdlib, largest-remainder stud mosaics, base64 typed-array payload, vanilla JS, canvas, three.js r128 instanced meshes.

## Licence

Code is MIT (see [LICENSE](LICENSE)). Data keeps the licence of its source, listed above.

---

Part of [Quick Projects](https://github.com/TNRiley/quick-projects) — one self-contained thing, built in one session. First published 2026-09-16.
