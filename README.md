# Saksham Moments

A buildless, responsive single-page site for a fictional vodka brand, produced by
rebranding an existing Kingfisher (beer) page into **Saksham Moments** (vodka).

Everything the site needs is in `dist/` — HTML, CSS, JS, fonts and imagery. There
is no framework, no bundler and no build step to run the site itself:

```bash
python -m http.server 8741 --directory dist
```

Deployment is configured two ways: `.openai/hosting.json` serves `dist/`, and
`deploy/pages.workflow.yml` is a GitHub Pages workflow you can enable (see
[Deploying](#deploying)).

---

## The rebrand process

The rebrand is reproducible rather than hand-edited. Four tools run in order and
write into `dist/`; two more verify the result. Every one of them is idempotent —
re-running the whole chain on a fresh checkout reproduces the site byte-for-byte
(where the output is deterministic, which it is for the header stamp and the
product array).

```
tools/rebrand.py  →  tools/patch_text.py  →  tools/logo.py  →  tools/newbottles.py
                                                                        ↓
                                            tools/verify_rebrand.py + tools/dom_check.mjs
```

### 1. Bottles — `tools/rebrand.py`

Source photographs live in `image-search/`. The tool holds a `DECK` of nine
products, each with its art direction, copy and the **geometry slot** it must
occupy (`size`, `box`, `bbox`).

- `cutout.py` removes the background: it estimates the backdrop colour per row
  from the left/right edge strips, builds a soft alpha ramp from the colour
  distance, keeps only large connected components, fills interior holes and
  de-fringes the edge. The result is a clean alpha cutout that sits correctly on
  both light and dark page backgrounds.
- `wordmark.py` finds the two-line brand lockup on the label and redraws the top
  line in Cinzel, matching the surrounding ink colour (the two lines are paired
  by proximity, height ratio and a hue check, which is what keeps it from
  latching onto a flame graphic instead of the real wordmark).
- `compose()` scales the cutout into its slot, centred horizontally and pinned to
  the top or bottom edge — `anchor="top"` for the premium-grain bottle only,
  because that one is the pour bottle and its neck must land exactly on the fixed
  pour point.

Output: `dist/assets/mm-*.webp` plus `build/products.snippet.js`, the generated
`products` array.

### 2. Copy — `tools/patch_text.py`

Rewrites product copy in `dist/app.js` and `dist/index.html`: the page title and
meta description, the hero and portfolio copy, the station pairings, the story,
the footer, and the alt text of the two branded photographs. It also renames the
header brand (`aria-label` / `alt`) and appends the footer credit.

Two things are deliberately **left alone** and reported on every run: the hero's
"Same familiar bird." / "BREWED FOR THE INDIAN SPIRIT.", and the footer's
"THE BIRD YOU KNOW." / "GOOD TIMES." wordmark. Those are beer-era brand lines
that were never in scope.

The tool operates on the pristine upstream sources, so it can be re-run from a
clean checkout at any time. It cannot be re-run over an already-patched `dist/`
(brand strings are the substitution target), which is why the pipeline order
matters.

### 3. Header stamp — `tools/logo.py`

`dist/assets/brand-stamp.svg` is rebuilt rather than replaced. The tool keeps the
original bird and the distress-speck field, redraws the wordmark as a single
`SAKSHAM` outline, and re-places all 118 specks — nudging each one onto the new
letters and dropping any that cannot reach. 115 paths become 106.

At `--weight 600` (the default) it reproduces the shipped stamp exactly:
167,847 bytes.

### 4. Generated bottles — `tools/newbottles.py`

The bottle bodies are also available as generated art. This stage composites
them under the label artwork rather than redrawing anything:

- Each generated render in `bottles-src/raw-<nn>-<id>.png` is cut out with the
  same `cutout.py` used above.
- **The label is lifted verbatim** out of the signed-off asset archived in
  `build/labels/`, then re-placed on the new body. The crest, the wordmark, the
  figures, the Remix script and the flavour line are therefore pixel-identical to
  the approved design — only the glass changes.
- Placement is expressed in **fractions of the bottle**, not pixels, because the
  generated bodies are a different size from the originals (≈1185px tall against
  2731px). A pixel offset measured on one lands in the wrong place on the other.
- A shoulder nudge clears the crest where the shoulders are still sloping, capped
  by the label's original distance from the base so it can never be driven into
  the base.
- A `SAKSHAM` neck mark is printed on the capsule, with the ink chosen against
  the cap colour so it stays legible on both dark (navy, green) and light
  (champagne, gold) capsules.
- Finally the mouth is measured and the canvas shifted to put it back on the
  canvas centre. The pour scene draws the bottle image at `x = -bw/2`, so the
  mouth only meets the fixed stream origin `P` if it sits on that centre; drift is
  brought back to ≤0.5px on all nine.

Run `python tools/newbottles.py` after `rebrand.py` (it needs `build/labels/`).
Products with no render in `bottles-src/` are reported and left untouched.

---

## What is guaranteed not to change

The rebrand is explicitly a rename, not a redesign. These hold in every pass and
are asserted by the checks:

- **Slot geometry.** Each product keeps the `size`/`box` it had in the original,
  so the SVG viewBoxes, the grid, the dialogs and the station plates all render
  identically.
- **The pour.** Bottle length stays `bh = 62 × 886 / 234 = 234.8` and the
  transform origin stays `translate(214 128) rotate(-78.00)`.
- **Every interaction.** Filters, dialogs, the departures board, the pour, the
  horn, the toran, the diyas.

---

## Verification

```bash
python tools/verify_rebrand.py                      # static + geometry checks
npm i jsdom && node tools/dom_check.mjs dist        # behavioural checks in jsdom
```

`verify_rebrand.py` compares the live `products` array against a pristine copy of
the upstream file in `build/original-app.js`, so it cannot quietly agree with a
mistake in a hardcoded table. `dom_check.mjs` mounts the real `dist/` in jsdom and
drives it: nine grid products, eight cities, the filters, a dialog, and the pour
readings above.

Both must pass before any commit.

**Dependencies:** `pillow`, `numpy`, `scipy`, `fonttools`; Node with `jsdom` for
the DOM check. The site itself needs none of them.

---

## Deploying

`.openai/hosting.json` points at `dist/`, which is committed, so the site
deploys as-is.

`deploy/pages.workflow.yml` is a GitHub Pages workflow. It lives there rather
than at `.github/workflows/` because this repository is pushed by a GitHub App
that lacks the `workflows` permission, and GitHub rejects any push that creates
or updates a file under `.github/workflows/`. To enable Pages, either move it
back:

```bash
mkdir -p .github/workflows && mv deploy/pages.workflow.yml .github/workflows/pages.yml
```

…or add it through the GitHub web UI, where the scope does not apply.

---

## Layout

```
dist/              the site - served directly, no build step
  index.html
  app.js           products array + all interaction
  styles.css
  assets/          mm-*.webp bottle art, brand-stamp.svg, fonts, photos
tools/             the rebrand pipeline and its checks
image-search/      source photography
bottles-src/       generated bottle renders (optional stage 4 input)
build/labels/      pristine label artwork, the source for stage 4
build/original-app.js   pristine upstream app.js, the geometry baseline
deploy/            GitHub Pages workflow template
```

`dist/` and `build/` are committed deliberately: some sandboxed environments
exclude those directory names from filesystem snapshots, so keeping them in git —
and pushing — is what makes the site durable there.
