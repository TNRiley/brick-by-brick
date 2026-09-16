# Rebuilding Brick by Brick

Written for an LLM with a shell and nothing else.

## What this is

A single self-contained HTML page that counts every piece in every official LEGO set by colour
and release year, using Rebrickable's public database. It is styled like a LEGO instruction
booklet, and behind the page a three.js house builds itself as you scroll and repaints in each
era's colours. The finding it exists to show is that the LEGO palette was redesigned twice, with
a sharp break each time. The classic six colours (red, yellow, blue, white, black, green) were 89%
of 1970s pieces and are 40% in the 2020s. In 2004 the old greys fell from 20% of pieces to 3% in
one year, replaced by bluish greys, and Brown became Reddish Brown at the same moment. The number
of colours in real use went from 10 in 1975 to 52 in 2004, was cut to 34 by 2007, and has grown back.

## Data sources

`https://cdn.rebrickable.com/media/downloads/<table>.csv.gz`, for `colors`, `themes`, `sets`,
`inventories` and `inventory_parts` (about 16 MB gzipped, 1.5 M rows in `inventory_parts`).
They are updated daily. Licence: free for any purpose, including commercial, with acknowledgement.
Rebrickable asks that automated downloads run at most once a day, so `fetch.py` keeps cached files.
The downloads page itself sits behind Cloudflare and returns 403 to scripts, but the CDN files do not.

Quirks that will bite:
- `inventories` has several `version`s per set. Use version 1 only, or pieces double-count.
- `inventory_parts.is_spare` is the string `"True"`/`"False"`. Drop spares.
- Minifigures are separate inventories (`inventory_minifigs`), not followed here.
- Colour `-1` is `[Unknown]` and `9999` is `[No Color/Any Color]`. Drop both.
- **The trap:** theme `Other > Database Sets` holds placeholder records such as "Unused Modulex parts
  sold by LEGO" and "Database Set for 1:87 Mercedes". They carry dozens of Modulex and HO colours,
  and left in they create a fake 1963 spike of about 32 colours in use and inflate the colour count
  from 197 to 264. Exclude that theme by name, as well as the root themes Modulex, Books, Gear and
  Service Packs.
- Years after 2026 exist (announced sets); drop them. 2026 is partial and is labelled so.

## Processing (`src/build_payload.py`)

- Per set: sum quantity by colour. Only sets that end up with parts are kept (17,945).
- Colour families: **classic** = Red, Yellow, Blue, White, Black, Green; **grey** = Light/Dark Gray,
  Light/Dark Bluish Gray, Very Light (Bluish) Gray; **earth** = tans, browns, nougats;
  **trans** = `is_trans` or a Trans-/Glitter Trans-/Opal Trans- name; **shiny** = names containing
  Pearl, Chrome, Metallic, Metal, Flat Silver, Flat Dark Gold, Speckle, Two-tone, Copper, Glitter,
  Opal; **other** = everything else.
- Colours are ordered grey → classic → earth → other → shiny → trans (hue inside a family). The
  page stacks columns in that order, so the index order is the stacking order.
- Year rows store sparse `[colourIndex, pieces, round(sum of per-set shares × 1000)]`. The third
  number powers the "every set equally" weighting.
- Themes: root themes with 40+ sets, minus catch-alls (Other, Promotional, Seasonal, Icons, etc.).
- The set table is base64 typed arrays: year offset (Uint8), theme label (Uint16), CSR offsets
  (Uint32), colour index (Uint16), quantity (Uint16; the script asserts < 65,536).
- "Colours in use" means colours making up at least 0.1% of that year's pieces. Arrivals and
  retirements count colours with at least 100 pieces in total; a last year of 2024 or later is
  treated as still in use.

## The page (`src/template.html`, spliced by `src/inject.py`)

- Identity: a baseplate of CSS radial-gradient studs as the page ground. Cards are "plates" with
  a 3px ink border, a hard offset shadow and side-on studs along the top edge. Headings use Fredoka,
  body text Nunito. Numbered build steps and blue "parts" callout boxes copy instruction booklets.
  Buttons are bricks that press down. No LEGO logo or trade dress; a trademark notice is in the footer.
- Charts are canvas and drawn as top-down 1×1 plates with studs, in the real Rebrickable RGB values:
  the wall (30 studs per year, largest-remainder allocation), step 1 old-vs-new small multiples,
  step 2 colours-in-use bars stacked from each year's colours plus arrival/retirement studs,
  step 3 family 100% columns, step 4 theme strips as DOM, step 5 set search with two compare slots
  and "then & now" pairs.
- The 3D house: three.js r128 from cdnjs. A voxel model (house, stepped gable roof, chimney,
  tree, path, flowers on a 16×16 baseplate) is merged into 1×2–1×4 bricks with alternating
  direction per level. It uses InstancedMesh, one opaque and one transparent group, with studs as
  instanced cylinders; hidden studs are skipped. Scroll turns the camera 2.5 revolutions over the
  page. Build progress comes from scroll through the first viewport. Each layer owns an equal slice
  of progress, and the target snaps to whole layers and eases, so no brick is left mid-air.
  `[data-era]` markers repaint the house (1978, 1990, 2003, 2005, 2024 role→colour maps) in a
  staggered ripple, top first. It honours `prefers-reduced-motion` (static, instant repaint),
  has an on/off toggle kept in localStorage, and falls back to the CSS baseplate if WebGL or the CDN fails.
- **three.js r128 bug to avoid:** every InstancedMesh sharing a material must have `setColorAt`
  called for every instance before the first render. The window studs are all covered, so that
  mesh would otherwise have no instance colours and three throws `isInterleavedBufferAttribute` of null.
- Prose numbers are computed from the payload at load (`data-k` spans), never typed in.

## Verification table (downloaded 2026-09-16)

| check | expected |
|---|---|
| sets with parts / pieces / colours | 17,945 / 4,481,891 / 197 |
| classic six share of pieces, 1970s / 2010s / 2020s | 89.2% / 42.8% / 39.8% |
| greys, 2010s / earth, 2020s / other, 2020s | 26.8% / 15.9% / 18.3% |
| old greys vs bluish greys, 2003 | 20.4% / 5.0% |
| 2004 | 3.2% / 17.4% |
| 2005 | 0.6% / 22.1% |
| 2006 | 0.2% / 25.7% |
| Brown in 2003 / last year Brown appears | 1.9% / 2006 |
| colours ≥ 0.1%: 1975, 2004, 2007, 2009, 2022, 2025 | 10, 52, 34, 33, 57, 51 |
| greyest theme / least grey | Star Wars 44.9% / Clikits 0.0% |
| Galaxy Explorer 497-1 (1979) | 322 pieces, 7 colours |
| Galaxy Explorer 10497-1 (2022) | 1,234 pieces, 11 colours |
| Millennium Falcon 10179-1 (2007) / 75192-1 (2017) | 5,176 pieces in 13 colours / 7,498 in 23 |
| Castle 375-2 (1978) | 700 pieces, 6 colours |

Values drift as Rebrickable corrects inventories and adds sets, mostly in the current year.

## What the page must say about itself

- Rebrickable is fan-maintained, and inventories are not always verified.
- Minifigure parts are excluded.
- Sets are not sales: every set counts once, however many were sold.
- Piece weighting lets huge sets dominate (hence the "every set equally" toggle).
- Pre-1958 years are thin and 2026 is partial.
- Colour names are Rebrickable's, and the families are the page's own grouping.
- The house's era colours are illustrative, picked by hand.
