"""Locate the two-line wordmark on a Saksham Moments label.

The label sets its wordmark as two centred lines of large dark serif caps:

        M A G I C
      M O M E N T S

The brand is the top line, so that is what gets renamed. Detection works from
ink geometry rather than fixed offsets so it survives different bottle crops:

  1. Mask dark ink inside the label, ignoring transparent pixels.
  2. Restrict to the horizontal middle of the bottle (excludes bottle edges and
     the label's side decorations).
  3. Group ink rows into runs; keep runs tall enough to be glyphs, not rules.
  4. The wordmark is the tallest *stack* of two such runs separated by a small
     gap. The upper run is the brand line.

Run ``python tools/wordmark.py --debug`` to write an overlay for eyeballing.
"""
from __future__ import annotations

import os
import sys

import numpy as np
from PIL import Image, ImageDraw

FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Cinzel.ttf")

INK_LUMA = 165.0        # "dark ink" threshold
HUE_MAX = 40.0          # max ink-colour distance between the two wordmark lines
MIN_ALPHA = 150
LINE_GAP_MAX = 1.30     # gap between the two wordmark lines, as a fraction of line 1 height
NECK_SAT = 28.0         # a "coloured band" is at least this far from grey
NECK_CONTRAST = 42.0    # neck type differs from its band by this much in luma
NECK_BAND_HI = 0.42     # neck band search region, as a fraction of bottle height
NECK_CLUSTER_MIN = 0.45 # a partial word at the wrap edge is left alone
MIN_LINE_W_FRAC = 0.16  # a real word line spans at least this much of the bottle width
BAND_LO = 0.16          # wordmark search band, as a fraction of bottle height
BAND_HI = 0.62


def _luma(rgb: np.ndarray) -> np.ndarray:
    return 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]


def ink_mask(img: Image.Image) -> np.ndarray:
    a = np.asarray(img.convert("RGBA")).astype(np.float32)
    return (a[:, :, 3] > MIN_ALPHA) & (_luma(a) < INK_LUMA)


def bottle_box(img: Image.Image):
    """Bounding box of the bottle itself.

    Studio sources come in two flavours: pre-matted (real alpha) and opaque
    photos on a flat backdrop. For the opaque ones the alpha channel is
    useless, so the backdrop is keyed out first - otherwise the "bottle box"
    would be the whole frame and every band fraction would be wrong.
    """
    ys, xs = np.where(subject_mask(img))
    if not len(xs):
        return None
    return int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)


def _row_runs(mask: np.ndarray, x0: int, x1: int, min_h: int):
    """Contiguous bands of rows containing ink inside the column window.

    The cut is adaptive (a fraction of the busiest row) so that anti-aliased
    wisps between the two wordmark lines do not bridge them into one run.
    """
    col = mask[:, x0:x1]
    rows = col.sum(axis=1).astype(np.float32)
    if rows.max() <= 0:
        return []
    cut = max(2.0, 0.12 * float(rows.max()))
    runs, start = [], None
    for y in range(len(rows)):
        if rows[y] > cut and start is None:
            start = y
        elif rows[y] <= cut and start is not None:
            runs.append((start, y))
            start = None
    if start is not None:
        runs.append((start, len(rows)))

    out = []
    for y0, y1 in runs:
        if y1 - y0 < min_h:
            continue
        cols = np.where(col[y0:y1].any(axis=0))[0]
        if not len(cols):
            continue
        out.append(dict(y0=y0, y1=y1, x0=int(x0 + cols.min()), x1=int(x0 + cols.max() + 1)))
    return out


def find_wordmark(img: Image.Image):
    """Return (brand_line, second_line) boxes, or (None, None).

    Each box is a dict with x0, y0, x1, y1 and the label's ink colour.
    """
    bb = bottle_box(img)
    if bb is None:
        return None, None
    bx, by, bx1, by1 = bb
    bw, bh = bx1 - bx, by1 - by

    mask = ink_mask(img)
    # Middle of the bottle only.
    wx0 = int(bx + bw * 0.18)
    wx1 = int(bx1 - bw * 0.18)
    # And only the label band: the wordmark sits in the upper-middle of the body.
    # This keeps dark caps, neck rings and foot text out of the running.
    wy0 = int(by + bh * BAND_LO)
    wy1 = int(by + bh * BAND_HI)
    band = np.zeros_like(mask)
    band[wy0:wy1] = True
    mask = mask & band
    min_h = max(4, int(bh * 0.012))          # a glyph line, not a hairline rule
    runs = [r for r in _row_runs(mask, wx0, wx1, min_h)
            if (r["x1"] - r["x0"]) >= bw * MIN_LINE_W_FRAC]
    if len(runs) < 2:
        return None, None

    # Ink colour per candidate run - the two lines of a wordmark lockup are set
    # in one colour, which separates them from a decorative device (a coloured
    # flame, an emblem) that happens to sit directly above the word.
    ink_rgb = np.asarray(img.convert("RGB")).astype(np.float32)
    for r in runs:
        sub = ink_rgb[r["y0"]:r["y1"], r["x0"]:r["x1"]].reshape(-1, 3)
        sub_m = mask[r["y0"]:r["y1"], r["x0"]:r["x1"]].reshape(-1)
        px = sub[sub_m] if sub_m.any() else sub
        lum = px.sum(axis=1)
        idx = np.argsort(lum)[: max(1, len(lum) // 3)]
        r["ink"] = px[idx].mean(axis=0)

    best = None
    for i in range(len(runs) - 1):
        a, b = runs[i], runs[i + 1]
        gap = b["y0"] - a["y1"]
        ha = a["y1"] - a["y0"]
        if gap < 0 or gap > max(6, ha * LINE_GAP_MAX):
            continue
        # Both lines should be similar in height - a real two-line wordmark.
        hb = b["y1"] - b["y0"]
        if min(ha, hb) / max(ha, hb) < 0.55:
            continue
        # ... and set in the same ink. A near-identical colour is required
        # unless nothing else offers a two-line pair at all.
        hue = float(np.abs(a["ink"] - b["ink"]).mean())
        r["hue"] = hue
        # Score on the width of the *pair* (both lines must be wide) and their
        # height match; the wordmark is the widest stacked pair on the label.
        width = min(a["x1"] - a["x0"], b["x1"] - b["x0"])
        score = width + (ha + hb) * (min(ha, hb) / max(ha, hb)) * 0.35
        cand = (score, a, b, i, hue)
        if hue <= HUE_MAX:
            if best is None or best[4] > HUE_MAX or score > best[0]:
                best = cand
        elif best is None:
            best = cand
    if best is None:
        return None, None

    _, a, b, _, _ = best
    return a, b


def label_fill(img: Image.Image, box) -> np.ndarray:
    """Median non-ink colour around ``box`` - the label stock behind the text."""
    rgb = np.asarray(img.convert("RGB")).astype(np.float32)
    m = ink_mask(img)
    x0, x1 = box["x0"], box["x1"]
    h = box["y1"] - box["y0"]
    ys, ye = max(0, box["y0"] - h), min(rgb.shape[0], box["y0"] - 1)
    patch, pm = rgb[ys:ye, x0:x1], m[ys:ye, x0:x1]
    if patch.size == 0:
        return np.array([245.0, 245.0, 245.0])
    keep = patch[~pm].reshape(-1, 3)
    if len(keep) < 20:
        keep = patch.reshape(-1, 3)
    return np.median(keep, axis=0)


def render_word(text: str, target_h: int, max_w: int, weight: str = "SemiBold"):
    """Render ``text`` as an L-mode ink image sized to target_h / max_w."""
    size = 240
    font = _font(size, weight)
    probe = Image.new("L", (size * len(text) + size * 2, size * 3), 0)
    ImageDraw.Draw(probe).text((size, size), text, font=font, fill=255)
    bb = probe.getbbox()
    if not bb:
        return None
    cap = bb[3] - bb[1]

    scale = target_h / cap
    # Never exceed the available width.
    width = bb[2] - bb[0]
    scale = min(scale, max_w / width)
    size2 = max(8, int(round(size * scale)))
    font2 = _font(size2, weight)
    canvas = Image.new("L", (size2 * (len(text) + 2), size2 * 3), 0)
    ImageDraw.Draw(canvas).text((size2, size2), text, font=font2, fill=255)
    bb2 = canvas.getbbox()
    if not bb2:
        return None
    return canvas.crop(bb2)


def _font(size: int, weight: str):
    from PIL import ImageFont
    f = ImageFont.truetype(FONT_PATH, size)
    try:
        f.set_variation_by_name(weight)
    except Exception:
        try:
            f.set_variation_by_axes([700])
        except Exception:
            pass
    return f


def replace_brand(img: Image.Image, text: str = "SAKSHAM",
                  height_scale: float = 1.0, width_limit: float = 0.86,
                  debug: dict | None = None, neck: bool = False) -> Image.Image:
    """Rename the label's top wordmark line. Everything else is left untouched."""
    line1, line2 = find_wordmark(img)
    if line1 is None:
        return img
    bb = bottle_box(img)
    bx, by, bx1, by1 = bb
    bw = bx1 - bx

    out = img.convert("RGBA").copy()
    fill = label_fill(out, line1)

    x0, y0, x1, y1 = line1["x0"], line1["y0"], line1["x1"], line1["y1"]
    old_h, old_w = y1 - y0, x1 - x0

    # Erase exactly the old word (with a 1px guard), nothing more.
    d = ImageDraw.Draw(out)
    d.rectangle([x0 - 1, y0 - 1, x1, y1],
                fill=(int(fill[0]), int(fill[1]), int(fill[2]), 255))

    target_h = int(round(old_h * height_scale))
    max_w = int(bw * width_limit)
    ink = render_word(text, target_h, max_w)
    if ink is None:
        return img

    col = tuple(int(v) for v in line1["ink"])
    layer = Image.new("RGBA", ink.size, col + (0,))
    layer.putalpha(ink)
    px = int(round((x0 + x1) / 2 - ink.width / 2))
    py = int(round((y0 + y1) / 2 - ink.height / 2))
    out.alpha_composite(layer, (px, py))

    # Never paint outside the bottle's own silhouette.
    orig_a = np.asarray(img.convert("RGBA"))[:, :, 3]
    arr = np.asarray(out).copy()
    arr[:, :, 3] = np.minimum(arr[:, :, 3], orig_a)
    out = Image.fromarray(arr, "RGBA")
    # The neck band repeats the lockup in light type at roughly 1.5% of the
    # rendered bottle height - a smudge on screen. The detector is reliable on
    # flat caps but not on ribbed/gradient ones, so it stays opt-in rather than
    # risking a flat patch on a cap that reads fine.
    if neck:
        out = replace_neck_brand(out, text)

    if debug is not None:
        debug.update(line1=dict(x0=x0, y0=y0, x1=x1, y1=y1),
                     line2=dict(x0=line2["x0"], y0=line2["y0"],
                                x1=line2["x1"], y1=line2["y1"]),
                     drawn=dict(x=px, y=py, w=ink.width, h=ink.height),
                     fill=[int(v) for v in fill], ink=col)
    return out


def subject_mask(img: Image.Image) -> np.ndarray:
    """True where the bottle is - for pre-matted images and opaque studio shots."""
    a = np.asarray(img.convert("RGBA")).astype(np.float32)
    al = a[:, :, 3]
    if al.min() < 250:
        return al > 40
    rgb = a[:, :, :3]
    border = np.concatenate([rgb[0, :], rgb[-1, :], rgb[:, 0], rgb[:, -1]])
    bg = np.median(border, axis=0)
    return np.abs(rgb - bg).max(axis=2) > 26


def _neck_bands(img: Image.Image, by: int, by1: int):
    """Coloured, flat bands in the bottle's top.

    The neck lockup is printed on a solid band (gold, navy, green, orange...).
    Locating the band first keeps the bottle's own shading, cap ribs and
    highlights out of the search, which a plain contrast mask happily picks up.
    """
    sub = subject_mask(img)
    rgb = np.asarray(img.convert("RGB")).astype(np.float32)
    limit = min(by + int((by1 - by) * 0.32), by1)
    rows = []
    for y in range(by, limit):
        xs = np.where(sub[y])[0]
        if len(xs) < 10:
            continue
        x0, x1 = int(xs.min()), int(xs.max()) + 1
        inset = int((x1 - x0) * 0.24)
        x0, x1 = x0 + inset, x1 - inset
        if x1 - x0 < 12:
            continue
        px = rgb[y, x0:x1]
        med = np.median(px, axis=0)
        if med.max() - med.min() < NECK_SAT:      # not a coloured band
            continue
        if np.mean(np.abs(px - med).max(axis=1) < 34) < 0.5:
            continue                              # not flat enough
        rows.append((y, x0, x1, med))
    bands, start = [], None
    for i, r in enumerate(rows):
        if start is None:
            start = i
        elif r[0] > rows[i - 1][0] + 3:
            bands.append(rows[start:i])
            start = i
    if rows:
        bands.append(rows[start:])
    out = []
    for grp in bands:
        if len(grp) < 10:
            continue
        # union, not intersection: a few clipped rows must not collapse the window
        out.append(dict(y0=grp[0][0], y1=grp[-1][0] + 1,
                        x0=min(g[1] for g in grp), x1=max(g[2] for g in grp),
                        rgb=np.median([g[3] for g in grp], axis=0)))
    return out


def _band_text_mask(img: Image.Image, band: dict) -> np.ndarray:
    """Type printed on ``band``: the pixels that differ from the band colour."""
    lum = _luma(np.asarray(img.convert("RGBA")).astype(np.float32))
    sub = subject_mask(img)
    y0, y1, x0, x1 = band["y0"], band["y1"], band["x0"], band["x1"]
    ref = float(_luma(band["rgb"].reshape(1, 1, 3))[0, 0])
    out = np.zeros(lum.shape, dtype=bool)
    out[y0:y1, x0:x1] = (np.abs(lum[y0:y1, x0:x1] - ref) > NECK_CONTRAST) & sub[y0:y1, x0:x1]
    return out


def _two_line_pair(runs, bw: int):
    """Pick the two stacked runs that make up the lockup."""
    best = None
    for i in range(len(runs) - 1):
        a, b = runs[i], runs[i + 1]
        gap = b["y0"] - a["y1"]
        ha, hb = a["y1"] - a["y0"], b["y1"] - b["y0"]
        if gap < 0 or gap > max(4, ha * LINE_GAP_MAX):
            continue
        if min(ha, hb) / max(ha, hb) < 0.5:
            continue
        wa, wb = a["x1"] - a["x0"], b["x1"] - b["x0"]
        if min(wa, wb) / max(wa, wb) < 0.55 or min(wa, wb) < bw * 0.10:
            continue
        score = min(wa, wb) + (ha + hb) * 0.35
        if best is None or score > best[0]:
            best = (score, a, b)
    return (best[1], best[2]) if best else (None, None)


def find_neck_wordmark(img: Image.Image, bb, y_limit: int):
    """Locate the two-line brand lockup printed on the neck band."""
    bx, by, bx1, by1 = bb
    bw, bh = bx1 - bx, by1 - by
    rgb = np.asarray(img.convert("RGB")).astype(np.float32)
    min_h = max(3, int(bh * 0.005))
    chosen = None
    for band in _neck_bands(img, by, min(by1, y_limit)):
        if band["y1"] > y_limit or (band["x1"] - band["x0"]) < bw * 0.15:
            continue
        mask = _band_text_mask(img, band)
        runs = [r for r in _row_runs(mask, band["x0"], band["x1"], min_h)
                if (r["x1"] - r["x0"]) >= bw * 0.06]
        if len(runs) < 2:
            continue
        a, b = _two_line_pair(runs, bw)
        if a is None:
            continue
        light = float(_luma(band["rgb"].reshape(1, 1, 3))[0, 0]) < 140
        for box in (a, b):
            sub = rgb[box["y0"]:box["y1"], box["x0"]:box["x1"]].reshape(-1, 3)
            sm = mask[box["y0"]:box["y1"], box["x0"]:box["x1"]].reshape(-1)
            px = sub[sm] if sm.any() else sub
            lum = px.sum(axis=1)
            n = max(1, len(lum) // 3)
            idx = np.argsort(lum)[-n:] if light else np.argsort(lum)[:n]
            box["ink"] = px[idx].mean(axis=0)
        if float(np.abs(a["ink"] - b["ink"]).mean()) > HUE_MAX:
            continue
        score = (a["x1"] - a["x0"]) + (a["y1"] - a["y0"]) + (b["y1"] - b["y0"])
        if chosen is None or score > chosen[0]:
            chosen = (score, a, b, band)
    if chosen is None:
        return None, None, None
    return chosen[1], chosen[2], chosen[3]


def _word_clusters(mask: np.ndarray, box, bw: int):
    """Split one line into separate word boxes (a wrapped neck band repeats it)."""
    x0, x1 = box["x0"], box["x1"]
    col = mask[box["y0"]:box["y1"], x0:x1].any(axis=0)
    if not col.any():
        return []
    gap_min = max(3, int((x1 - x0) * 0.035))
    groups, start, run = [], None, 0
    for i, on in enumerate(col):
        if on:
            if start is None:
                start = i
            run = 0
        elif start is not None:
            run += 1
            if run >= gap_min:
                groups.append((start, i - run + 1))
                start = None
    if start is not None:
        groups.append((start, len(col)))
    out = [dict(x0=x0 + a, x1=x0 + b, y0=box["y0"], y1=box["y1"],
                ink=box["ink"]) for a, b in groups]
    if not out:
        return []
    widest = max(g["x1"] - g["x0"] for g in out)
    return [g for g in out
            if (g["x1"] - g["x0"]) >= widest * NECK_CLUSTER_MIN]


def replace_neck_brand(img: Image.Image, text: str = "SAKSHAM",
                       height_scale: float = 1.0) -> Image.Image:
    """Rename the brand word on the neck band, leaving the rest of the lockup."""
    bb = bottle_box(img)
    if bb is None:
        return img
    label = find_wordmark(img)[0]
    y_limit = label["y0"] if label else bb[3]
    l1, l2, band = find_neck_wordmark(img, bb, y_limit)
    if l1 is None:
        return img

    bx, by, bx1, _by1 = bb
    bw = bx1 - bx
    mask = _band_text_mask(img, band)
    rgb = np.asarray(img.convert("RGB")).astype(np.float32)
    alpha = np.asarray(img.convert("RGBA"))[:, :, 3]
    out = img.convert("RGBA").copy()
    d = ImageDraw.Draw(out)

    for word in _word_clusters(mask, l1, bw) + _word_clusters(mask, l2, bw):
        x0, y0, x1, y1 = word["x0"], word["y0"], word["x1"], word["y1"]
        rows = slice(max(0, y0 - 2), min(rgb.shape[0], y1 + 2))
        band_px = rgb[rows, :].reshape(-1, 3)
        band_m = (alpha[rows, :] > MIN_ALPHA).reshape(-1)
        keep = band_px[band_m] if band_m.any() else band_px
        band_col = np.median(keep, axis=0)

        d.rectangle([x0 - 1, y0 - 1, x1, y1],
                    fill=(int(band_col[0]), int(band_col[1]), int(band_col[2]), 255))
        want_h = max(4, int(round((y1 - y0) * height_scale)))
        ink = render_word(text, want_h, max(4, int((x1 - x0) * 1.02)))
        if ink is None:
            continue
        col = tuple(int(v) for v in word["ink"])
        layer = Image.new("RGBA", ink.size, col + (0,))
        layer.putalpha(ink)
        out.alpha_composite(layer, (int(round((x0 + x1) / 2 - ink.width / 2)),
                                    int(round((y0 + y1) / 2 - ink.height / 2))))

    # Never paint outside the bottle's own silhouette.
    orig_a = np.asarray(img.convert("RGBA"))[:, :, 3]
    arr = np.asarray(out).copy()
    arr[:, :, 3] = np.minimum(arr[:, :, 3], orig_a)
    return Image.fromarray(arr, "RGBA")


def main() -> int:
    src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "image-search")
    want = sys.argv[1:]
    files = (want if want else sorted(
        f for f in os.listdir(src) if f.lower().endswith((".webp", ".png", ".jpg"))))
    tiles = []
    for f in files:
        path = os.path.join(src, f)
        try:
            im = Image.open(path)
            im = im.convert("RGBA")
            dbg: dict = {}
            out = replace_brand(im, debug=dbg)
        except Exception as exc:  # noqa: BLE001
            print(f"{f[:50]:52} ERROR {exc}")
            continue
        l1, l2 = find_wordmark(im)
        print(f"{f[:50]:52} line1={None if not l1 else (l1['x0'], l1['y0'], l1['x1'], l1['y1'])}")
        # overlay on the ORIGINAL: green box = detected brand line
        ov = im.copy()
        d = ImageDraw.Draw(ov)
        if l1:
            d.rectangle([l1["x0"], l1["y0"], l1["x1"], l1["y1"]], outline=(0, 200, 0, 255), width=3)
        if l2:
            d.rectangle([l2["x0"], l2["y0"], l2["x1"], l2["y1"]], outline=(0, 90, 255, 255), width=3)
        bb = bottle_box(im)
        if bb:
            x0, y0, x1, y1 = bb
            crop = (x0, y0, x1, y1)
            ov = ov.crop(crop)
            out = out.crop(crop)
        H = 360
        cw = []
        for img_ in (ov, out):
            w = max(int(img_.width * H / img_.height), 8)
            c = Image.new("RGBA", (w, H), (245, 245, 245, 255))
            c.alpha_composite(img_.resize((w, H), Image.LANCZOS))
            cw.append(c)
        tiles.append((f, cw))

    if not tiles:
        return 1
    pad, lab = 14, 16
    rows = len(tiles)
    W = max(sum(t.width + pad for t in c) + pad for _, c in tiles)
    Hh = rows * (360 + lab) + pad
    sheet = Image.new("RGBA", (W, Hh), (255, 255, 255, 255))
    dd = ImageDraw.Draw(sheet)
    y = pad
    for f, c in tiles:
        dd.text((pad, y), f"{f}   [green=brand line, blue=second line]  left: original   right: SAKSHAM",
                fill=(0, 0, 0, 255))
        x = pad
        for t in c:
            sheet.alpha_composite(t, (x, y + lab))
            x += t.width + pad
        y += 360 + lab
    dest = "/home/user/wm_debug.png"
    sheet.convert("RGB").save(dest)
    print(f"\nwrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
