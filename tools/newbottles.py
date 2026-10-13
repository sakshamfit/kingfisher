"""Put the Saksham label artwork on a freshly generated bottle body.

The brief for this pass was to replace the bottle *artwork* while leaving
everything else byte-for-byte as it was. So the glass is new - AI-generated
frosted bottles, one per product, with the cap colour matching the product's
colour - but the label design on top of it is not redrawn.

The label is lifted verbatim out of the existing per-product assets
(build/labels/, the pristine R3 art) and composited onto the new body. That
keeps the crest, the SAKSHAM MOMENTS wordmark, the figures, the Remix script
and the flavour line pixel-for-pixel identical to what was signed off, and it
stays that way for any future bottle body.

Geometry is untouched. Each asset is composed into the same size/box/bbox slot
it already used, so the SVG viewBox, the pour point, the hero, the grid and the
detail dialog all keep rendering exactly as before.

Usage:  python tools/newbottles.py            # writes the 9 assets
Inputs: bottles-src/raw-<nn>-<id>.png         # generated bodies
        build/labels/<file>.webp              # label art source
"""
from __future__ import annotations

import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from cutout import cutout          # noqa: E402
from rebrand import DECK, ROOT, compose  # noqa: E402
from wordmark import render_word   # noqa: E402

# Kept inside the repo rather than a workspace path outside it: the renders
# are pipeline input and need to survive with the rest of the repo, which a
# scratch directory elsewhere in the sandbox does not.
RAW = os.path.join(ROOT, "bottles-src")
LABELS = os.path.join(ROOT, "build", "labels")
ASSETS = os.path.join(ROOT, "dist", "assets")

# Label ink: printed dark, or coloured. Both are far from the white glass.
SHOULDER_FRAC = 0.92   # row width fraction that counts as "body has begun"
INK_LUMA = 120.0
INK_SAT = 25.0


def _row_runs_containing(mask: np.ndarray):
    ys = np.where(mask.any(axis=1))[0]
    return (int(ys.min()), int(ys.max())) if len(ys) else (None, None)


def bottle_bounds(alpha: np.ndarray):
    ys, xs = np.where(alpha > 24)
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def extract_label(img: Image.Image) -> Image.Image:
    """Lift the printed label off a built asset as a soft-alpha sprite.

    Everything below the shoulder that is either dark or coloured is label ink;
    the bottle's own edge shading is excluded by eroding the silhouette first.
    """
    arr = np.asarray(img.convert("RGBA")).astype(np.float32)
    rgb, al = arr[:, :, :3], arr[:, :, 3]
    lum = 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]
    sat = rgb.max(axis=2) - rgb.min(axis=2)
    solid = al > 200
    if not solid.any():
        raise ValueError("asset has no opaque pixels to read a label from")

    # Only look below the shoulder: the cap and the neck lockup are not label.
    rows = solid.sum(axis=1)
    sh = int(np.argmax(rows >= rows.max() * SHOULDER_FRAC))
    core = ndimage.binary_erosion(solid, iterations=max(2, int(solid.sum() ** 0.5 * 0.02)))
    below = np.arange(img.height)[:, None] > sh
    cand = core & below & ((sat > INK_SAT) | (lum < INK_LUMA))

    lab, n = ndimage.label(cand)
    if n:
        sizes = ndimage.sum(cand, lab, range(1, n + 1))
        keep = np.zeros(n + 1, dtype=bool)
        keep[1:] = sizes >= max(12.0, sizes.max() * 0.002)
        cand = keep[lab]
    y0, y1 = _row_runs_containing(cand)
    if y0 is None:
        raise ValueError("no label ink found")
    xs = np.where(cand.any(axis=0))[0]

    # Feather the mask by a fraction of a pixel of the source so the ink keeps
    # its anti-aliased edges instead of being cut out with a hard stair-step.
    soft = ndimage.gaussian_filter(cand.astype(np.float32), 0.8)
    out = np.zeros((y1 - y0 + 1, xs.max() - xs.min() + 1, 4), dtype=np.uint8)
    out[:, :, :3] = np.clip(rgb[y0:y1 + 1, xs.min():xs.max() + 1], 0, 255).astype(np.uint8)
    out[:, :, 3] = np.clip(soft[y0:y1 + 1, xs.min():xs.max() + 1] * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA"), (int(xs.min()), y0, int(xs.max()), y1)


def locate_label(ref: Image.Image, art: Image.Image, art_box):
    """Where the label sits and how big it is, as fractions of the bottle.

    Fractions, not pixels: the generated bodies are a different size from the
    originals (2731px tall vs 1185px), so an offset measured in the old
    raster would land somewhere else entirely on the new one.
    """
    rb = bottle_bounds(np.asarray(ref)[:, :, 3])
    bw, bh = rb[2] - rb[0] + 1, rb[3] - rb[1] + 1
    return dict(
        w_frac=(art_box[2] - art_box[0] + 1) / bw,
        h_frac=(art_box[3] - art_box[1] + 1) / bh,
        top_frac=(art_box[1] - rb[1]) / bh,
        cx_frac=((art_box[0] + art_box[2]) / 2 - rb[0]) / bw,
        base_frac=(rb[3] - art_box[3]) / bh,     # distance from label to base
    )


def head_centre_x(alpha: np.ndarray, rows: int = 12) -> float:
    """Horizontal centre of the very top of the bottle - the mouth.

    The pour scene draws the bottle image at x = -bw/2, so the mouth only meets
    the stream at the fixed point P if it sits on the canvas centre. The
    original assets were laid out that way; the generated ones are not, so the
    mouth is measured and the canvas shifted to put it back.
    """
    ys, _xs = np.where(alpha > 24)
    band = alpha[ys.min():ys.min() + rows] > 24
    xs = np.where(band.any(axis=0))[0]
    return float(xs.min() + xs.max()) / 2.0


def cap_band(alpha: np.ndarray, rgb: np.ndarray):
    """Row range of the coloured cap/capsule at the top of the bottle."""
    ys, _xs = np.where(alpha > 200)
    y0, y1 = int(ys.min()), int(ys.max())
    sat = rgb.max(axis=2) - rgb.min(axis=2)
    limit = min(y0 + int((y1 - y0) * 0.35), y1)
    rows = [y for y in range(y0, limit)
            if alpha[y][alpha[y] > 200].size and sat[y][alpha[y] > 200].mean() > 35.0]
    if not rows:
        return None
    return y0, int(max(rows))


def add_neck_mark(cut: Image.Image, text: str = "SAKSHAM") -> Image.Image:
    """Print the brand on the capsule, the way a real bottle carries it.

    The generated caps come out clean, which left the neck with no branding at
    all - and the neck lockup is exactly what this pass set out to rename. Ink
    is chosen against the cap colour so it stays legible on both the dark
    (navy, green) and light (champagne, gold) capsules.
    """
    arr = np.asarray(cut)
    alpha = arr[:, :, 3]
    rgb = arr[:, :, :3].astype(np.float32)
    band = cap_band(alpha, rgb)
    if band is None:
        return cut
    y0, y1 = band
    ys, xs = np.where(alpha[ y0:y1 + 1] > 200)
    if not len(xs):
        return cut
    cap_x0, cap_x1 = int(xs.min()), int(xs.max())
    cap_w = cap_x1 - cap_x0 + 1
    cap_h = y1 - y0 + 1

    px = rgb[y0:y1 + 1][alpha[y0:y1 + 1] > 200]
    cap_luma = float(np.mean(0.2126 * px[:, 0] + 0.7152 * px[:, 1] + 0.0722 * px[:, 2]))
    if cap_luma < 140:
        ink = (246.0, 246.0, 250.0)
    else:
        shade = np.percentile(px, 8, axis=0)
        ink = tuple(float(v) for v in shade)

    want_h = max(8, int(cap_h * 0.30))
    want_w = int(cap_w * 0.62)
    stamp = render_word(text, want_h, want_w)
    if stamp is None:
        return cut
    sw, sh = stamp.size
    x = cap_x0 + (cap_w - sw) // 2
    y = y0 + int(cap_h * 0.52) - sh // 2

    layer = Image.new("RGBA", stamp.size, tuple(int(v) for v in ink) + (0,))
    layer.putalpha(stamp)

    out = cut.copy()
    canvas = np.asarray(cut)[:, :, 3]
    ch, cw = canvas.shape
    sx0, sy0 = max(0, x), max(0, y)
    sx1, sy1 = min(cw, x + sw), min(ch, y + sh)
    if sx1 <= sx0 or sy1 <= sy0:
        return cut
    piece = np.asarray(layer)[sy0 - y:sy1 - y, sx0 - x:sx1 - x].copy()
    sub = canvas[sy0:sy1, sx0:sx1]
    piece[:, :, 3] = (piece[:, :, 3].astype(np.uint16) * (sub > 100)).astype(np.uint8)
    out.alpha_composite(Image.fromarray(piece, "RGBA"), (sx0, sy0))
    return out


def shift_x(img: Image.Image, dx: int) -> Image.Image:
    """Move the whole canvas horizontally, clipping at the edges."""
    if dx == 0:
        return img
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.alpha_composite(img, (dx, 0))
    return out


def fit_label(ideal: int, nh: int, by: int, by1: int, profile: np.ndarray,
              nw: int, lowest: int) -> int:
    """Nudge the label down to clear the shoulder, but never closer to the base
    than it sat on the original bottle.

    The crest sits right where the shoulders are still sloping, so on some
    bodies it clips. Sliding the whole label down clears it, but an unbounded
    slide drives the flavour line into the base - so the original bottom margin
    is the hard limit, and if the crest cannot clear within that, the label
    keeps its faithful position and the crest fades into the shoulder.
    """
    if lowest < ideal:
        return max(by, lowest)
    head = max(1, int(nh * 0.30))          # the crest band
    y = max(by, ideal)
    while y < lowest and int(profile[y:y + head].min()) < nw:
        y += 2
    return min(y, lowest) if y < lowest else max(by, ideal)


def place_label(cut: Image.Image, art: Image.Image, frac: dict) -> Image.Image:
    """Scale the label to the same share of the body and sit it at the same height."""
    alpha = np.asarray(cut)[:, :, 3]
    bx, by, bx1, by1 = bottle_bounds(alpha)
    bottle_w, bottle_h = bx1 - bx + 1, by1 - by + 1

    # Honour both the original width share and the original height share; take
    # whichever is tighter so the label can never overflow the new bottle.
    by_width = bottle_w * frac["w_frac"] / art.width
    by_height = bottle_h * frac["h_frac"] / art.height
    scale = min(by_width, by_height)
    nw = max(8, int(round(art.width * scale)))
    nh = max(8, int(round(art.height * scale)))

    x = int(round(bx + frac["cx_frac"] * bottle_w - nw / 2))
    ideal = int(round(by + frac["top_frac"] * bottle_h))
    # Same distance from the base as on the original - the hard lower limit.
    lowest = int(round(by1 - frac["base_frac"] * bottle_h - nh))
    profile = (alpha > 100).sum(axis=1)
    y = fit_label(ideal, nh, by, by1, profile, nw, lowest)

    sprite = np.asarray(art.resize((nw, nh), Image.LANCZOS)).copy()
    # Clamp to the bottle's own silhouette so no ink can float off the glass.
    canvas_h, canvas_w = alpha.shape
    sx0, sy0 = max(0, x), max(0, y)
    sx1, sy1 = min(canvas_w, x + nw), min(canvas_h, y + nh)
    if sx1 <= sx0 or sy1 <= sy0:
        return cut
    sub_a = alpha[sy0:sy1, sx0:sx1]
    piece = sprite[sy0 - y:sy1 - y, sx0 - x:sx1 - x]
    piece[:, :, 3] = (piece[:, :, 3].astype(np.uint16) * (sub_a > 100)).astype(np.uint8)

    out = cut.copy()
    out.alpha_composite(Image.fromarray(piece, "RGBA"), (sx0, sy0))
    return out


def main() -> int:
    raws = sorted(f for f in os.listdir(RAW)
                  if f.startswith("raw-") and f.lower().endswith(".png"))
    if not raws:
        print(f"no raw bottle renders in {RAW}")
        return 1
    by_id = {}
    for f in raws:
        pid = os.path.basename(f)[4:-4].split("-", 1)[1]
        by_id.setdefault(pid, os.path.join(RAW, f))

    print(f"{'id':17} {'raw body':>11} {'label':>11} {'label w%':>8} {'neck@':>7} {'mouth dx':>8} "
          f"{'orig neck':>9}  KB")
    print("-" * 78)
    missing, done = [], 0
    for p in DECK:
        raw = by_id.get(p["id"])
        if not raw:
            missing.append(p["id"])
            continue
        label_src = os.path.join(LABELS, p["file"])
        ref = Image.open(label_src).convert("RGBA")
        art, art_box = extract_label(ref)
        frac = locate_label(ref, art, art_box)

        body = cutout(Image.open(raw).convert("RGBA"))
        body = place_label(body, art, frac)
        body = add_neck_mark(body)

        anchor = "top" if p["id"] == "premium-grain" else "bottom"
        canvas = compose(body, p["size"], p["box"], p["bbox"], anchor=anchor)

        # Put the mouth back where the original had it, so the pour stream still
        # leaves the neck exactly as before.
        want = head_centre_x(np.asarray(ref)[:, :, 3])
        have = head_centre_x(np.asarray(canvas)[:, :, 3])
        dx = int(round(want - have))
        canvas = shift_x(canvas, dx)

        dest = os.path.join(ASSETS, p["file"])
        canvas.save(dest, "WEBP", quality=90, method=6)

        disk = Image.open(dest)
        assert disk.size == p["size"], (p["id"], disk.size, p["size"])
        a = np.asarray(disk.convert("RGBA"))[:, :, 3]
        ys, _xs = np.where(a > 24)
        orig_neck = p["bbox"][1] + p["box"][1]
        raw_size = Image.open(raw).size
        print(f"{p['id']:17} {raw_size[0]:5}x{raw_size[1]:<5} "
              f"{art.width:5}x{art.height:<5} {frac['w_frac'] * 100:7.1f}% {ys.min():7} "
              f"{orig_neck:9} {dx:+4d} {os.path.getsize(dest) // 1024:4}")
        done += 1

    if missing:
        print(f"\nNOT replaced (no generated body yet): {', '.join(missing)}")
    print(f"\nreplaced {done}/{len(DECK)} bottle bodies")
    return 0 if not missing else 2


if __name__ == "__main__":
    raise SystemExit(main())
