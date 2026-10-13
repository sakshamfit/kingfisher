"""Build the Saksham bottle set for dist/assets/ and emit the products array.

Hard constraints honoured here (see notes in each function):

1. ``size`` (canvas) and ``box`` (crop) are copied verbatim from the original
   Kingfisher product definitions. The pour scene derives its bottle length from
   ``bh = bw * size[1] / size[0]`` and its stream origin from the fixed point
   ``P``; the image's TOP edge sits on ``P``. Keeping ``size``/``box`` and
   anchoring each new bottle's neck (top of artwork) on the original's top row is
   what keeps every animation pixel-identical.
2. Each source is placed in the slot whose crop region it can fill at >= 1:1
   resolution, so the range grid and detail dialogs stay sharp.

Usage:  python tools/rebrand.py            # writes assets + build/products.snippet.js
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cutout import cutout  # noqa: E402
from wordmark import replace_brand  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "dist", "assets")
SEARCH = os.path.join(ROOT, "image-search")
BUILD = os.path.join(ROOT, "build")

# ---------------------------------------------------------------------------
# Deck: id -> everything the products array and the image builder need.
# `size` / `box` are the ORIGINAL values for that slot and are asserted at write
# time against dist/app.js so the page geometry can never drift.
# ---------------------------------------------------------------------------
DECK = [
    dict(
        id="premium-grain", name="Premium Grain Vodka", hi="प्रीमियम ग्रेन वोदका",
        type="Premium grain vodka", group="lager", tone="#1f4b8f",
        file="mm-premium-grain.webp",
        # every source below is renamed MAGIC -> SAKSHAM on the label first
        src="magic-moments-remix-lemongrass-ginger-fl-1.jpg",
        size=(234, 886), box=(0, 0, 234, 886), bbox=(3, 4, 227, 879),
        style="Premium grain vodka", character="Clean & smooth",
        description="The original Saksham Moments. A triple-distilled grain vodka with a clean, "
                    "smooth character, from Radico Khaitan.",),
    dict(
        id="triple-distilled", name="Triple Distilled", hi="ट्रिपल डिस्टिल्ड",
        type="Triple distilled vodka", group="lager", tone="#1b3f7a",
        file="mm-triple-distilled.webp",
        src="sipdirect-magic-moments-triple-distilled-1.webp",
        size=(1999, 2999), box=(627, 124, 745, 2751), bbox=(10, 10, 725, 2731),
        style="Triple distilled vodka", character="Soft & clean",
        description="Triple distilled from fine grain for a soft, almost weightless character. "
                    "The everyday pour that anchors the table."),
    dict(
        id="dazzle-gold", name="Dazzle Gold", hi="डैज़ल गोल्ड",
        type="Special edition grain vodka", group="strong", tone="#c9a227",
        file="mm-dazzle-gold.webp",
        src="sipdirect-magic-moments-dazzle-gold-spec-1.webp",
        size=(1000, 1406), box=(315, 150, 350, 1165), bbox=(0, 7, 350, 1150),
        style="Special edition grain vodka", character="Gold & premium",
        description="The special-edition expression of the family, dressed in gold. A grain vodka "
                    "with a distinctly premium identity."),
    dict(
        id="verve-super", name="Verve Super Premium", hi="वर्व सुपर प्रीमियम",
        type="Super premium vodka", group="strong", tone="#274b86",
        file="mm-verve-super.webp",
        src="magic-moments-triple-distilled-grain-vod-2.jpg",
        size=(600, 600), box=(229, 55, 142, 506), bbox=(6, 4, 129, 495),
        style="Super premium vodka", character="Smooth & refined",
        description="The super-premium chapter of Saksham Moments. A smoother, more considered "
                    "pour for the occasions that ask for one."),
    dict(
        id="verve-cranberry", name="Verve Cranberry", hi="वर्व क्रैनबेरी",
        type="Cranberry flavoured vodka", group="wheat", tone="#b8224a",
        file="mm-verve-cranberry.webp",
        src="sipdirect-magic-moments-premium-grain-vo-1.webp",
        size=(293, 1113), box=(0, 0, 293, 1113), bbox=(4, 4, 285, 1106),
        style="Cranberry flavoured vodka", character="Bright & lightly tart",
        description="Cranberry, bright and lightly tart, naturally infused for a flavoured vodka "
                    "that stays clean rather than sweet."),
    dict(
        id="verve-orange", name="Verve Orange", hi="वर्व ऑरेंज",
        type="Orange flavoured vodka", group="wheat", tone="#e06a1f",
        file="mm-verve-orange.webp",
        src="sipdirect-magic-moments-remix-lemon-flav-1.webp",
        size=(369, 1394), box=(0, 0, 369, 1394), bbox=(3, 3, 363, 1388),
        style="Orange flavoured vodka", character="Bright & citrus",
        description="Sun-ripe orange over a triple-distilled base. A clean flavoured pour that "
                    "works neat, long or over ice."),
    dict(
        id="remix-green-apple", name="Remix Green Apple", hi="रीमिक्स ग्रीन एप्पल",
        type="Green apple flavoured vodka", group="flavour", tone="#5a9e2f",
        file="mm-remix-green-apple.webp",
        src="sipdirect-magic-moments-remix-green-appl-1.webp",
        size=(2188, 3283), box=(656, 0, 874, 3283), bbox=(11, 3, 852, 3280),
        style="Green apple flavoured vodka", character="Crisp & tart",
        description="The flavour that made Remix a household name. Tart green apple, naturally "
                    "infused and refreshingly crisp."),
    dict(
        id="remix-lemongrass", name="Remix Lemongrass & Ginger", hi="रीमिक्स लेमनग्रास एंड जिंजर",
        type="Lemongrass & ginger flavoured vodka", group="flavour", tone="#7d8f2a",
        file="mm-remix-lemongrass.webp",
        src="magic-moments-remix-lemongrass-and-ginge-1.webp",
        size=(934, 1625), box=(303, 348, 335, 1230), bbox=(9, 9, 316, 1211),
        style="Lemongrass & ginger flavoured vodka", character="Warm & aromatic",
        description="Lemongrass and ginger over grain vodka, an Indian flavour pairing that is "
                    "infused rather than sweetened."),
    dict(
        id="remix-raspberry", name="Remix Raspberry", hi="रीमिक्स रास्पबेरी",
        type="Raspberry flavoured vodka", group="flavour", tone="#c02b52",
        file="mm-remix-raspberry.webp",
        src="sipdirect-magic-moments-premium-grain-vo-2.webp",
        size=(934, 1625), box=(305, 346, 336, 1230), bbox=(10, 10, 316, 1211),
        style="Raspberry flavoured vodka", character="Soft & rounded",
        description="Raspberry, naturally infused for a soft, rounded flavoured vodka that keeps "
                    "its bite at the finish."),
]


def source_cutout(path: str, opts: dict) -> Image.Image:
    """RGBA cutout of the single product in ``path``.

    Uses the file's own alpha when it has one (most studio sources are already
    matted), otherwise keys the backdrop out. Never resamples: the caller scales.
    """
    img = Image.open(path) if isinstance(path, str) else path
    if img.mode in ("P", "LA"):
        img = img.convert("RGBA")
    rgba = img.convert("RGBA")

    if np.asarray(rgba)[:, :, 3].min() < 250:
        arr = np.asarray(rgba).astype(np.float32)
        alpha = arr[:, :, 3] / 255.0
        solid = ndimage.binary_fill_holes(alpha > 0.45)
        alpha = np.clip(alpha, 0, 1) * ndimage.binary_dilation(solid, iterations=1)
        img = Image.fromarray(
            np.dstack([arr[:, :, :3], alpha * 255.0]).astype(np.uint8), "RGBA")
    else:
        keys = {k: v for k, v in opts.items() if k != "pick"}
        img = cutout(path, crop=True, **keys)

    # Isolate a single object. Product shots sometimes carry a second object
    # (gift tube, stand) or loose specks from the matte.
    a = np.asarray(img)[:, :, 3]
    labels, n = ndimage.label(a > 40)
    if n > 1:
        sizes = ndimage.sum(a > 40, labels, range(1, n + 1))
        order = list(np.argsort(sizes)[::-1] + 1)
        pick = opts.get("pick")
        if pick in ("left", "right"):
            keep, best = order[0], None
            for lab in order[:6]:
                if sizes[lab - 1] < sizes[order[0] - 1] * 0.12:
                    continue
                cols = np.where((labels == lab).any(axis=0))[0]
                score = cols.mean() * (1 if pick == "right" else -1)
                if best is None or score > best:
                    best, keep = score, lab
        else:
            keep = order[0]
        mask = np.isin(labels, [keep])
        # Retain anything enclosed by the kept object's bounding box (a separated
        # cap or label fragment belongs to it).
        ys, xs = np.where(mask)
        inside = np.zeros_like(mask)
        inside[ys.min():ys.max() + 1, xs.min():xs.max() + 1] = True
        mask |= (a > 40) & inside & (labels != 0)
        out = np.asarray(img).copy()
        out[:, :, 3] = np.where(mask, out[:, :, 3], 0)
        img = Image.fromarray(out, "RGBA")

    bbox = img.getbbox()
    return img.crop(bbox) if bbox else img


def compose(cut: Image.Image, size, box, target, anchor: str = "bottom") -> Image.Image:
    """Scale ``cut`` to fit ``target`` inside ``box`` on a blank ``size`` canvas.

    Horizontally centred; vertically the artwork is pinned to the same edge of the
    target region that the original Kingfisher bottle occupied.

    ``anchor="top"``    - the neck/top row matches the original (REQUIRED for the
                          pour slot: the stream leaves the bottle at image row 0,
                          which the scene pins to the fixed point P).
    ``anchor="bottom"`` - the base row matches the original. `.product-visual` is
                          bottom-aligned in the grid, so this keeps every bottle
                          standing on the same baseline instead of floating.
    """
    bx, by, _bw, _bh = box
    tl, tt, tw, th = target
    scale = min(tw / cut.width, th / cut.height)
    nw, nh = max(1, round(cut.width * scale)), max(1, round(cut.height * scale))
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    top = by + tt if anchor == "top" else by + tt + th - nh
    canvas.alpha_composite(cut.resize((nw, nh), Image.LANCZOS),
                           (bx + tl + (tw - nw) // 2, top))
    return canvas


def js_array(deck: list[dict]) -> str:
    """Render the products array exactly as dist/app.js expects it."""
    rows = []
    for p in deck:
        rows.append(
            "    {id:'%(id)s',name:'%(name)s',hi:'%(hi)s',type:'%(type)s',group:'%(group)s',"
            "tone:'%(tone)s',file:'%(file)s',size:[%(sw)d,%(sh)d],box:[%(bx)d,%(by)d,%(bw)d,%(bh)d],"
            "description:'%(description)s',style:'%(style)s',character:'%(character)s'}" % dict(
                p, sw=p["size"][0], sh=p["size"][1],
                bx=p["box"][0], by=p["box"][1], bw=p["box"][2], bh=p["box"][3]))
    return "  const products = [\n" + ",\n".join(rows) + "\n  ];\n"


def original_geometry() -> dict:
    """Pull the current size/box out of dist/app.js so we can assert no drift."""
    import re
    src = open(os.path.join(ROOT, "dist", "app.js"), encoding="utf-8").read()
    out = {}
    for m in re.finditer(
            r"id:'([a-z-]+)'.*?size:\[(\d+),(\d+)\],box:\[(\d+),(\d+),(\d+),(\d+)\]", src):
        out[m.group(1)] = (int(m.group(2)), int(m.group(3)),
                           int(m.group(4)), int(m.group(5)),
                           int(m.group(6)), int(m.group(7)))
    return out


def main() -> int:
    os.makedirs(BUILD, exist_ok=True)
    # Geometry guard: our deck's slots must correspond to slots that really exist
    # in the current page (matched by size/box, since ids are being renamed).
    live = set(original_geometry().values())
    for p in DECK:
        key = (p["size"][0], p["size"][1], p["box"][0], p["box"][1], p["box"][2], p["box"][3])
        assert key in live, f"slot {p['id']} does not match any original size/box: {key}"

    report = []
    for p in DECK:
        src = os.path.join(SEARCH, p["src"])
        if not os.path.exists(src):
            print(f"MISSING {src}")
            return 1
        img = Image.open(src)
        img = replace_brand(img.convert("RGBA"))
        cut = source_cutout(img, p.get("src_opts", {}))
        # Slot 0 is the hero + pour bottle: its neck must sit on P, so pin the top.
        # Every other slot only needs to stand on the grid baseline.
        anchor = "top" if p["id"] == "premium-grain" else "bottom"
        img = compose(cut, p["size"], p["box"], p["bbox"], anchor=anchor)
        assert img.size == p["size"] and img.mode == "RGBA"

        dest = os.path.join(ASSETS, p["file"])
        img.save(dest, "WEBP", quality=88, method=6)

        disk = Image.open(dest)
        assert disk.size == p["size"], (p["id"], disk.size, p["size"])
        a = np.asarray(disk.convert("RGBA"))[:, :, 3]
        ys, xs = np.where(a > 24)
        bw, bh = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
        # Effective upscale relative to the source pixels we had to work with.
        up = max(bw / cut.width, bh / cut.height)
        report.append(dict(id=p["id"], name=p["name"], size=disk.size, src_w=cut.width,
                           src_h=cut.height, out_w=bw, out_h=bh, neck=ys.min(),
                           orig_neck=p["bbox"][1] + p["box"][1], upscale=up,
                           kb=os.path.getsize(dest) // 1024))

    print(f"{'id':17} {'product':26} {'canvas':>10} {'src bottle':>11} {'placed':>11} "
          f"{'neck@':>10} {'scale':>6} {'KB':>5}")
    print("-" * 106)
    for r in report:
        print(f"{r['id']:17} {r['name']:26} {r['size'][0]:4}x{r['size'][1]:<5} "
              f"{r['src_w']:5}x{r['src_h']:<5} {r['out_w']:5}x{r['out_h']:<5} "
              f"{r['neck']:4}/{r['orig_neck']:<5} {r['upscale']:6.2f} {r['kb']:5}")

    snippet = js_array(DECK)
    with open(os.path.join(BUILD, "products.snippet.js"), "w", encoding="utf-8") as fh:
        fh.write(snippet)
    print(f"\nwrote {len(DECK)} assets and build/products.snippet.js")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
