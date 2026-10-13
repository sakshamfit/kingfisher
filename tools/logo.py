"""Rebuild the header brand stamp with a new wordmark.

The stock brand-stamp.svg is a distressed stamp: a kingfisher bird, the word
KINGFISHER set on a rising diagonal, an "INDIA'S NO 1 PREMIUM BEER" tagline and
a dotted border. Every element is anonymous vector paths - there is no <text>,
so the wordmark has to be re-set from a font and dropped in.

Measured from the original (tools/svgrender.py holds the rasteriser):

    rotation      +10.36 deg in SVG convention (rotate(-10.36) maps the upright
                  design frame onto the stamp frame)
    upright word  ink box x -1.9..283.0, baseline y 171.95, cap height 43.72,
                  ink width 284.8
    viewBox       0 0 320.305 214.258
    fill rule     nonzero; the 10 letter outlines are negative-wound and 118
                  small positive-wound speck subpaths punch the distress holes

Glyphs come from Cinzel (tools/fonts/Cinzel.ttf), a Trajan-style serif matching
the original letterforms. The new word is set to the exact measured box, rotated
by the exact measured angle, and the original's 118 distress specks are
transplanted on top so the texture is the genuine article rather than a
simulation.

Usage:
    python tools/logo.py                 # rebuild dist/assets/brand-stamp.svg
    python tools/logo.py --compare       # weight comparison sheet
    python tools/logo.py --dry-run       # report metrics, write nothing
"""
from __future__ import annotations

import argparse
import math
import re
import sys

from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

HERE = __file__.rsplit("/", 1)[0]
sys.path.insert(0, HERE)
from svgrender import _translate, parse_path, rasterise  # noqa: E402

# ------------------------------------------------------------ measured facts
ROT_DEG = -10.36            # SVG angle mapping the design frame -> stamp frame
BASELINE = 171.95           # baseline y in the design frame
CAP_H = 43.72               # cap height of the body letters
INK_W = 284.8               # word ink width
INK_CX = 140.55             # word ink centre x in the design frame
VIEWBOX = "0 0 320.305 214.258"
VB_W, VB_H = 320.305, 214.258

WORD = "SAKSHAM"
FONT = f"{HERE}/fonts/Cinzel.ttf"
SRC = "/home/user/kingfisher/dist/assets/brand-stamp.svg"

BIRD_K, OUT_OF_FRAME_K, TAGLINE_K = 113, 114, 25
WORD_K = (8, 11, 14, 17, 19, 41, 45, 57, 64, 67)
SPECK_MAX_AREA = 20.0       # viewBox units^2; separates specks from outlines

PATH_RE = re.compile(r"<path\b[^>]*?/?>", re.S)
SUB_RE = re.compile(r"[Mm]")


# ------------------------------------------------------------ font helpers
def _instantiate(wght: int, text: str = WORD) -> dict:
    f = TTFont(FONT)
    if "fvar" in f and wght != 400:
        f = instancer.instantiateVariableFont(f, {"wght": wght}, inplace=False)
    gs, cmap = f.getGlyphSet(), f.getBestCmap()
    glyphs, pen, left, right = [], 0.0, None, None
    for ch in text:
        gn = cmap[ord(ch)]
        bp = BoundsPen(gs)
        gs[gn].draw(bp)
        x0, _, x1, _ = bp.bounds
        if left is None:
            left = pen + x0
        right = pen + x1
        glyphs.append(dict(ch=ch, name=gn, pen=pen, ink=bp.bounds,
                           adv=gs[gn].width))
        pen += gs[gn].width
    # cap height comes from a flat-topped letter, so round-letter overshoot
    # (S, A, M climb ~2% above the cap line in Cinzel) does not shrink the word
    flat = [g["ink"][3] for g in glyphs if g["ch"] in "HIEFKLNTZ"]
    cap = max(flat) if flat else max(g["ink"][3] for g in glyphs)
    return dict(f=f, gs=gs, glyphs=glyphs, upem=f["head"].unitsPerEm,
                ink_left=left, ink_w=right - left, cap=cap,
                overshoot=max(g["ink"][3] for g in glyphs) - cap)


def word_transform(wght: int = 600, cap_h: float = CAP_H, ink_w: float = INK_W,
                   ink_cx: float = INK_CX, rotate: bool = True) -> tuple[Transform, dict]:
    m = _instantiate(wght)
    s = cap_h / m["cap"]
    gaps = len(m["glyphs"]) - 1
    track = (ink_w - m["ink_w"] * s) / s / gaps if gaps else 0.0   # font units
    origin = (ink_cx - ink_w / 2.0) - m["ink_left"] * s
    rot = Transform().rotate(math.radians(ROT_DEG)) if rotate else Transform()
    info = dict(scale=s, track=track, origin=origin, cap_h=cap_h, ink_w=ink_w,
                wght=wght, rot=rot, m=m, rotate=rotate)
    return rot, info


def build_word(wght: int = 600, **kw) -> tuple[str, dict]:
    """SVG path data for WORD, baked into the stamp frame."""
    rot, info = word_transform(wght=wght, **kw)
    m, s, origin, track = info["m"], info["scale"], info["origin"], info["track"]
    parts = []
    for i, g in enumerate(m["glyphs"]):
        px = origin + g["pen"] * s + i * track * s
        t = Transform(s, 0, 0, -s, px, BASELINE)     # design frame, y-down
        t = rot.transform(t)                          # -> stamp frame
        pen = SVGPathPen(m["gs"])
        m["gs"][g["name"]].draw(TransformPen(pen, t))
        parts.append(pen.getCommands())
    return " ".join(parts), info


# ------------------------------------------------------------ speck transplant
def _subpath_slices(d: str) -> list[str]:
    """Split raw path data into one string per subpath (M/m starts each)."""
    starts = [m.start() for m in SUB_RE.finditer(d)]
    return [d[a:b] for a, b in zip(starts, starts[1:] + [len(d)])]


def _poly_area(pts) -> float:
    return abs(sum(pts[i][0] * pts[i + 1][1] - pts[i + 1][0] * pts[i][1]
                   for i in range(len(pts) - 1))) / 2.0


def collect_specks(src: str = SRC) -> list[dict]:
    """The genuine distress specks from the original wordmark."""
    text = open(src, encoding="utf-8").read()
    gx, gy = _translate(re.search(r'<g[^>]*transform="([^"]*)"', text).group(1))
    tags = PATH_RE.findall(text)
    out = []
    for k in WORD_K:
        d = re.search(r'\bd="([^"]*)"', tags[k]).group(1)
        tm = re.search(r'transform="([^"]*)"', tags[k])
        tx, ty = _translate(tm.group(1) if tm else "")
        ox, oy = gx + tx, gy + ty
        subs = _subpath_slices(d)
        parsed = parse_path(d)
        assert len(subs) == len(parsed), \
            f"path #{k}: {len(subs)} slices vs {len(parsed)} parsed"
        for raw, pts in zip(subs, parsed):
            area = _poly_area(pts)
            if area > SPECK_MAX_AREA:
                continue                     # letter outline or an R counter
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            out.append(dict(raw=raw, pts=pts, area=area,
                            cx=(min(xs) + max(xs)) / 2 + ox,
                            cy=(min(ys) + max(ys)) / 2 + oy,
                            ox=ox, oy=oy))
    return out


def specks_as_polygons(specks, keep=None, moved=None) -> str:
    parts = []
    for i, sp in enumerate(specks):
        if keep is not None and not keep[i]:
            continue
        dx, dy = moved[i] if moved else (0.0, 0.0)
        pts = [(x + sp["ox"] + dx, y + sp["oy"] + dy) for x, y in sp["pts"]]
        body = "L".join(f"{x:.2f},{y:.2f}" for x, y in pts[1:])
        parts.append(f"M{pts[0][0]:.2f},{pts[0][1]:.2f}L{body}Z")
    return "".join(parts)


def filter_specks(specks: list[dict], word_path: str, snap: float = 12.0
                  ) -> tuple[list[bool], list[tuple[float, float]]]:
    """Decide which specks to keep and where they land.

    Every speck was a hole punched in the old letterforms. The new word has
    different letters, so a speck can end up over blank paper - there it would
    print as a fleck instead of a pit. Those are nudged onto the nearest ink
    within `snap` units; anything further away is dropped.
    """
    import numpy as np
    from scipy import ndimage

    sub = ('<svg xmlns="http://www.w3.org/2000/svg" '
           f'viewBox="{VIEWBOX}"><path d="{word_path}"/></svg>')
    W = 3000
    mask = np.array(rasterise(sub, W)) > 0
    px = VB_W / W
    dist = ndimage.distance_transform_edt(mask)              # px to nearest edge
    _, ind = ndimage.distance_transform_edt(~mask, return_indices=True)

    keep, moved = [], []
    for sp in specks:
        col, row = int(sp["cx"] / px), int(sp["cy"] / px)
        inside = 0 <= row < mask.shape[0] and 0 <= col < mask.shape[1]
        if inside and dist[row, col] > 0:
            keep.append(True)
            moved.append((0.0, 0.0))
            continue
        if not inside:
            keep.append(False)
            moved.append((0.0, 0.0))
            continue
        nr, nc = int(ind[0, row, col]), int(ind[1, row, col])
        dx, dy = (nc - col) * px, (nr - row) * px
        d = math.hypot(dx, dy)
        if d <= snap:
            keep.append(True)
            moved.append((dx, dy))
        else:
            keep.append(False)
            moved.append((0.0, 0.0))
    return keep, moved


# ------------------------------------------------------------ assembly
def rebuild(dest: str = SRC, src: str = SRC, wght: int = 600,
            specks_on: bool = True, dry_run: bool = False) -> dict:
    text = open(src, encoding="utf-8").read()
    spans = [m.span() for m in PATH_RE.finditer(text)]
    assert len(spans) > max(WORD_K), f"expected >{max(WORD_K)} paths, got {len(spans)}"

    d_word, info = build_word(wght=wght)
    d_specks, n_taken, n_all, n_moved = "", 0, 0, 0
    if specks_on:
        specks = collect_specks(src)
        n_all = len(specks)
        keep, moved = filter_specks(specks, d_word)
        n_taken = sum(keep)
        n_moved = sum(1 for k, mv in zip(keep, moved) if k and mv != (0.0, 0.0))
        d_specks = specks_as_polygons(specks, keep, moved)

    d_all = d_word + d_specks
    block = f'<path fill="#fff" fill-rule="evenodd" d="{d_all}"/>'

    pieces, last = [], 0
    for k, (a, b) in enumerate(spans):
        if k in WORD_K:
            pieces.append(text[last:a])
            last = b
    pieces.append(text[last:])
    new_text = "".join(pieces)
    # the word and the transplanted specks are already in the final (post
    # translate) frame, so the block goes in as a sibling of the wrapper <g>,
    # not inside it - otherwise the group's translate applies twice
    close = new_text.rfind("</g>") + len("</g>")
    new_text = new_text[:close] + block + new_text[close:]

    print(f"  word '{WORD}' wght {wght}: scale {info['scale']:.6f}, "
          f"cap {info['cap_h']:.2f}u, ink width {info['ink_w']:.2f}u, "
          f"tracking {info['track']:+.1f}/1000em, rotation {ROT_DEG}deg")
    print(f"  specks: {n_taken}/{n_all} placed ({n_moved} nudged onto the new "
          f"letters, {n_all - n_taken} too far to move)")
    print(f"  paths {len(spans)} -> {len(spans) - len(WORD_K) + 1}, "
          f"{len(text)} -> {len(new_text)} bytes")
    if not dry_run:
        open(dest, "w", encoding="utf-8").write(new_text)
        print(f"  wrote {dest}")
    info.update(specks_taken=n_taken, specks_all=n_all, specks_moved=n_moved,
                text=new_text if dry_run else None)
    return info


def sheet(out_png: str, src: str = SRC, weights=(400, 500, 700, 900)) -> None:
    """Original wordmark above each candidate weight, de-rotated and upright."""
    from PIL import Image, ImageDraw

    text = open(src, encoding="utf-8").read()
    tags = PATH_RE.findall(text)
    gx, gy = _translate(re.search(r'<g[^>]*transform="([^"]*)"', text).group(1))
    keep = []
    for k in WORD_K:
        d = re.search(r'\bd="([^"]*)"', tags[k]).group(1)
        tm = re.search(r'transform="([^"]*)"', tags[k])
        tx, ty = _translate(tm.group(1) if tm else "")
        keep.append(f'<path d="{d}" transform="translate({gx + tx:.3f} '
                    f'{gy + ty:.3f})"/>')
    view = f"{INK_CX - 168} {BASELINE - 76} 336 104"
    W = 1500

    def tile(svg):
        return rasterise(svg, W)

    tiles = [("original  K I N G F I S H E R",
              tile('<svg xmlns="http://www.w3.org/2000/svg" '
                   f'viewBox="{view}"><g transform="rotate({-ROT_DEG})">'
                   + "".join(keep) + "</g></svg>"), (255, 235, 170))]
    for wt in weights:
        d, info = build_word(wght=wt, rotate=False)
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" '
               f'viewBox="{view}"><path d="{d}"/></svg>')
        tiles.append((f"Cinzel {wt}   S A K S H A M", tile(svg), (185, 225, 255)))

    pad, lab = 12, 24
    H = sum(t[1].size[1] for t in tiles) + lab * len(tiles) + pad * (len(tiles) + 1)
    out = Image.new("RGB", (W + pad * 2, H), (198, 28, 48))
    dr = ImageDraw.Draw(out)
    y = pad
    for name, m, col in tiles:
        dr.text((pad, y), name, fill=col)
        y += lab
        for yy in range(m.size[1]):
            for x in range(m.size[0]):
                if m.getpixel((x, yy)):
                    out.putpixel((pad + x, y + yy), (255, 255, 255))
        y += m.size[1] + pad
    out.save(out_png)
    print(f"wrote {out_png} {out.size}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--out", default=None)
    ap.add_argument("--weight", type=int, default=600)
    ap.add_argument("--no-specks", action="store_true")
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.sheet:
        sheet("/home/user/logo_sheet.png", src=a.src)
    else:
        rebuild(dest=a.out or a.src, src=a.src, wght=a.weight,
                specks_on=not a.no_specks, dry_run=a.dry_run)
