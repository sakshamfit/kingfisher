"""Visual + geometric QA for the Saksham Moments bottle swap.

Checks run here:
  A. Framing sheet  - new asset vs the Kingfisher asset it replaced, cropped
     exactly as the page crops it, on both page palettes.
  B. Pour simulator - reproduces the pour scene's real transform
     (translate(P) rotate(REST), image at x=-bw/2 y=-3 w=bw h=bh) and draws the
     falling stream from P, so we can see the liquid still leaves the mouth.
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rebrand import ASSETS, DECK, ROOT  # noqa: E402

OLD = {  # slot -> the Kingfisher file that occupied it (same size/box)
    "premium-grain": "strong-cut.webp",
    "triple-distilled": "max.webp",
    "dazzle-gold": "premium.png",
    "verve-super": "ultra.png",
    "verve-cranberry": "storm-cut.webp",
    "verve-orange": "blue-cut.webp",
    "remix-green-apple": "witbier.webp",
    "remix-lemongrass": "mango.png",
    "remix-raspberry": "lemon.png",
}

DAY = (242, 240, 228, 255)      # --paper, day palette
NIGHT = (25, 21, 48, 255)       # --paper, Diwali-night palette


def crop_of(path: str, box) -> Image.Image:
    im = Image.open(path).convert("RGBA")
    bx, by, bw, bh = box
    return im.crop((bx, by, bx + bw, by + bh))


def framing_sheet(height: int = 300) -> Image.Image:
    cols, pad, lab = 3, 14, 26
    tiles = []
    for p in DECK:
        new = crop_of(os.path.join(ASSETS, p["file"]), p["box"])
        old = crop_of(os.path.join(ASSETS, OLD[p["id"]]), p["box"])
        tiles.append((p, old, new))

    def strip(bg):
        out = []
        for p, old, new in tiles:
            for img in (old, new):
                w = max(int(img.width * height / img.height), 6)
                canvas = Image.new("RGBA", (w, height), bg)
                canvas.alpha_composite(img.resize((w, height), Image.LANCZOS))
                out.append(canvas)
        return out

    strips = [strip(DAY), strip(NIGHT)]
    total_w = max(sum(t.width + pad for t in s) + pad for s in strips)
    total_h = sum(height + lab + pad for _ in strips) + lab
    sheet = Image.new("RGBA", (total_w, total_h), (255, 255, 255, 255))
    d = ImageDraw.Draw(sheet)
    y = lab
    for label, s in zip(("day", "night"), strips):
        x = pad
        for t in s:
            sheet.alpha_composite(t, (x, y))
            x += t.width + pad
        d.text((pad, y - 16), f"{label} background  (each pair: Kingfisher -> Saksham Moments)",
               fill=(0, 0, 0))
        y += height + lab + pad
    return sheet


def pour_sim(deck_index: int, out_path: str, angle_deg: float = -78.0) -> dict:
    """Recreate the pour scene's bottle placement and stream origin.

    Geometry copied from dist/app.js:
        P = {x:214, y:128}; REST = -78; bw = 62; bh = 62 * size[1]/size[0]
        <g transform="translate(P.x P.y) rotate(REST)">
          <image x="-bw/2" y="-3" width="bw" height="bh"/>
    The stream is emitted from exactly P (emitParcel), so the bottle's mouth must
    land on P for the pour to look correct.
    """
    p = DECK[deck_index]
    img_path = os.path.join(ASSETS, p["file"])
    img = Image.open(img_path).convert("RGBA")

    bw = 62.0
    bh = bw * p["size"][1] / p["size"][0]
    P = (214.0, 128.0)
    theta = math.radians(angle_deg)

    W, H = 460, 580          # viewBox "0 -40 460 580"
    YOFF = 40.0              # pixel y = view y + 40

    k = img.width / bw
    s = img.height / bh
    a = math.cos(theta) * k
    b = math.sin(theta) * k
    c = (-P[0] * math.cos(theta) - (P[1] + YOFF) * math.sin(theta) + bw / 2) * k
    d = -math.sin(theta) * s
    e = math.cos(theta) * s
    f = (P[0] * math.sin(theta) - (P[1] + YOFF) * math.cos(theta) + 3.0) * s

    placed = img.transform((W, H), Image.AFFINE, (a, b, c, d, e, f),
                           resample=Image.BICUBIC)

    canvas = Image.new("RGBA", (W, H), NIGHT)
    canvas.alpha_composite(placed)
    dr = ImageDraw.Draw(canvas)
    # The falling stream: emitted at P and falling to the glass.
    px, py = P[0], P[1] + YOFF
    dr.line([(px, py), (px, 490 + YOFF)], fill=(249, 200, 79, 255), width=3)
    dr.ellipse([px - 5, py - 5, px + 5, py + 5], outline=(255, 60, 60, 255), width=2)
    canvas.convert("RGB").save(out_path)

    # Where does the artwork's mouth (topmost opaque row, centred) actually sit?
    alpha = np.asarray(placed)[:, :, 3]
    ys, xs = np.where(alpha > 40)
    dist = math.hypot(xs.min() and (xs[ys == ys.min()].mean() - px), ys.min() - py)
    return dict(file=p["file"], bw=bw, bh=round(bh, 1),
                top_row=int(ys.min()), top_x=round(float(xs[ys == ys.min()].mean()), 1),
                P=(px, py), distance_from_P=round(dist, 1))


def main() -> int:
    sheet = framing_sheet()
    sheet.convert("RGB").save("/home/user/qa_framing.png")
    print("wrote /home/user/qa_framing.png", sheet.size)

    print(f"\n{'asset':24} {'bh':>7} {'mouth px':>16} {'P':>12} {'dist':>7}")
    print("-" * 72)
    for i in (0, 4):
        out = f"/home/user/qa_pour_{DECK[i]['id']}.png"
        r = pour_sim(i, out)
        print(f"{r['file']:24} {r['bh']:7} "
              f"({r['top_x']},{r['top_row']})".rjust(24) + f"{str(r['P']):>12} "
              f"{r['distance_from_P']:7}")
        print(f"   -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
