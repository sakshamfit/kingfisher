"""Minimal SVG path rasteriser (PIL only, no native deps).

Enough of the SVG spec to render logo artwork for inspection and diffing:
  * M/m L/l H/h V/v C/c S/s Q/q T/t A/a Z/z
  * elliptical arcs are converted per SVG 1.1 appendix F.6
  * each <path> is filled even-odd over its own subpaths (so counters in
    letters stay open), then all paths are unioned

Not a general purpose renderer - transforms other than translate/rotate and
gradients/strokes are ignored. Used by tools/logo.py to eyeball the brand mark.

Usage:  python tools/svgrender.py in.svg out.png [width] [bg]
"""
from __future__ import annotations

import math
import re
import sys

from PIL import Image

CMD_RE = re.compile(r"([MmLlHhVvCcSsQqTtAaZz])|(-?\d*\.?\d+(?:[eE][-+]?\d+)?)")
NUM = re.compile(r"-?\d*\.?\d+(?:[eE][-+]?\d+)?")


def parse_path(d: str):
    """Return a list of subpaths, each a list of (x, y) points."""
    tokens = [(m.group(1), m.group(2)) for m in CMD_RE.finditer(d)]
    subpaths: list[list[tuple[float, float]]] = []
    cur: list[tuple[float, float]] = []

    x = y = 0.0
    sx = sy = 0.0          # subpath start
    prev_ctrl = None       # for S/T reflection
    prev_cmd = ""
    i = 0

    def nums(n):
        nonlocal i
        out = []
        while i < len(tokens) and len(out) < n:
            cmd, val = tokens[i]
            if cmd is not None:
                break
            out.append(float(val))
            i += 1
        return out

    def flush():
        nonlocal cur
        # keep degenerate (1-2 point) subpaths too: callers rely on a 1:1
        # mapping between subpaths and the raw M/m-delimited slices
        if len(cur) >= 2:
            subpaths.append(cur)
        cur = []

    def line_to(px, py):
        cur.append((px, py))

    def cubic(p0, p1, p2, p3, steps=24):
        for s in range(1, steps + 1):
            t = s / steps
            mt = 1 - t
            bx = (mt ** 3 * p0[0] + 3 * mt ** 2 * t * p1[0]
                  + 3 * mt * t ** 2 * p2[0] + t ** 3 * p3[0])
            by = (mt ** 3 * p0[1] + 3 * mt ** 2 * t * p1[1]
                  + 3 * mt * t ** 2 * p2[1] + t ** 3 * p3[1])
            line_to(bx, by)

    def arc_to(x1, y1, rx, ry, phi_deg, large, sweep):
        """SVG 1.1 F.6: endpoint -> centre parameterisation."""
        nonlocal x, y
        if rx == 0 or ry == 0:
            line_to(x1, y1); x, y = x1, y1; return
        rx, ry = abs(rx), abs(ry)
        phi = math.radians(phi_deg)
        cp, sp = math.cos(phi), math.sin(phi)
        dx2, dy2 = (x - x1) / 2.0, (y - y1) / 2.0
        x1p = cp * dx2 + sp * dy2
        y1p = -sp * dx2 + cp * dy2
        lam = (x1p ** 2) / (rx ** 2) + (y1p ** 2) / (ry ** 2)
        if lam > 1:
            s = math.sqrt(lam)
            rx *= s; ry *= s
        num = rx ** 2 * ry ** 2 - rx ** 2 * y1p ** 2 - ry ** 2 * x1p ** 2
        den = rx ** 2 * y1p ** 2 + ry ** 2 * x1p ** 2
        co = math.sqrt(max(0.0, num / den)) if den else 0.0
        if large == sweep:
            co = -co
        cxp = co * rx * y1p / ry
        cyp = -co * ry * x1p / rx
        cx = cp * cxp - sp * cyp + (x + x1) / 2.0
        cy = sp * cxp + cp * cyp + (y + y1) / 2.0

        def ang(ux, uy, vx, vy):
            dot = ux * vx + uy * vy
            n = math.hypot(ux, uy) * math.hypot(vx, vy)
            a = math.acos(max(-1.0, min(1.0, dot / n))) if n else 0.0
            return -a if (ux * vy - uy * vx) < 0 else a

        th1 = ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
        dth = ang((x1p - cxp) / rx, (y1p - cyp) / ry,
                  (-x1p - cxp) / rx, (-y1p - cyp) / ry)
        if not sweep and dth > 0:
            dth -= 2 * math.pi
        elif sweep and dth < 0:
            dth += 2 * math.pi
        steps = max(6, int(abs(dth) / (math.pi / 18)))
        for s in range(1, steps + 1):
            t = th1 + dth * s / steps
            ex = cx + rx * math.cos(t) * cp - ry * math.sin(t) * sp
            ey = cy + rx * math.cos(t) * sp + ry * math.sin(t) * cp
            line_to(ex, ey)
        x, y = x1, y1

    while i < len(tokens):
        cmd = tokens[i][0]
        if cmd is None:
            i += 1
            continue
        i += 1
        rel = cmd.islower()
        c = cmd.upper()

        if c == "Z":
            if cur:
                cur.append((sx, sy))
                flush()
            x, y = sx, sy
            prev_ctrl = None
            prev_cmd = cmd
            continue

        if c == "M":
            a = nums(2)
            if len(a) < 2:
                continue
            px, py = (x + a[0], y + a[1]) if rel else (a[0], a[1])
            flush()
            x, y = px, py
            sx, sy = px, py
            cur = [(px, py)]
            # implicit lineto for following pairs
            while True:
                more = nums(2)
                if len(more) < 2:
                    break
                px, py = (x + more[0], y + more[1]) if rel else (more[0], more[1])
                line_to(px, py)
                x, y = px, py
            prev_ctrl = None
        elif c == "L":
            while True:
                a = nums(2)
                if len(a) < 2:
                    break
                x, y = (x + a[0], y + a[1]) if rel else (a[0], a[1])
                line_to(x, y)
            prev_ctrl = None
        elif c == "H":
            while True:
                a = nums(1)
                if not a:
                    break
                x = x + a[0] if rel else a[0]
                line_to(x, y)
            prev_ctrl = None
        elif c == "V":
            while True:
                a = nums(1)
                if not a:
                    break
                y = y + a[0] if rel else a[0]
                line_to(x, y)
            prev_ctrl = None
        elif c in ("C", "S"):
            while True:
                if c == "C":
                    a = nums(6)
                    if len(a) < 6:
                        break
                    p1 = (x + a[0], y + a[1]) if rel else (a[0], a[1])
                    p2 = (x + a[2], y + a[3]) if rel else (a[2], a[3])
                    p3 = (x + a[4], y + a[5]) if rel else (a[4], a[5])
                else:
                    a = nums(4)
                    if len(a) < 4:
                        break
                    if prev_ctrl and prev_cmd.upper() in ("C", "S"):
                        p1 = (2 * x - prev_ctrl[0], 2 * y - prev_ctrl[1])
                    else:
                        p1 = (x, y)
                    p2 = (x + a[0], y + a[1]) if rel else (a[0], a[1])
                    p3 = (x + a[2], y + a[3]) if rel else (a[2], a[3])
                cubic((x, y), p1, p2, p3)
                prev_ctrl = p2
                x, y = p3
            prev_cmd = cmd
        elif c in ("Q", "T"):
            while True:
                if c == "Q":
                    a = nums(4)
                    if len(a) < 4:
                        break
                    q1 = (x + a[0], y + a[1]) if rel else (a[0], a[1])
                    q2 = (x + a[2], y + a[3]) if rel else (a[2], a[3])
                else:
                    a = nums(2)
                    if len(a) < 2:
                        break
                    q1 = (2 * x - prev_ctrl[0], 2 * y - prev_ctrl[1]) \
                        if (prev_ctrl and prev_cmd.upper() in ("Q", "T")) else (x, y)
                    q2 = (x + a[0], y + a[1]) if rel else (a[0], a[1])
                # quadratic -> cubic
                p1 = (x + 2 / 3 * (q1[0] - x), y + 2 / 3 * (q1[1] - y))
                p2 = (q2[0] + 2 / 3 * (q1[0] - q2[0]), q2[1] + 2 / 3 * (q1[1] - q2[1]))
                cubic((x, y), p1, p2, q2)
                prev_ctrl = q1
                x, y = q2
            prev_cmd = cmd
        elif c == "A":
            while True:
                a = nums(7)
                if len(a) < 7:
                    break
                ex, ey = (x + a[5], y + a[6]) if rel else (a[5], a[6])
                arc_to(ex, ey, a[0], a[1], a[2], int(a[3]), int(a[4]))
            prev_ctrl = None
        prev_cmd = cmd
    flush()
    return subpaths


def _fill_even_odd(edges, w, h, ss=3):
    """Scanline even-odd fill of a set of edges -> boolean rows."""
    pix = bytearray(w * h)
    # bucket edges by scanline for speed
    for row in range(h):
        yy = row + 0.5
        xs = []
        for (x0, y0, x1, y1) in edges:
            if (y0 > yy) == (y1 > yy):
                continue
            t = (yy - y0) / (y1 - y0)
            xs.append(x0 + t * (x1 - x0))
        if len(xs) < 2:
            continue
        xs.sort()
        base = row * w
        for k in range(0, len(xs) - 1, 2):
            a = max(0, int(math.floor(xs[k])))
            b = min(w, int(math.ceil(xs[k + 1])))
            for px in range(a, b):
                pix[base + px] = 1
    return pix


def rasterise(svg_text: str, width: int = 900):
    """Rasterise SVG paths. Returns (L-mode mask, (minx, miny, maxx, maxy))."""
    vb = re.search(r'viewBox="([-\d.\s]+)"', svg_text)
    if not vb:
        raise ValueError("no viewBox")
    vx0, vy0, vw, vh = (float(v) for v in vb.group(1).split())
    height = max(1, int(round(width * vh / vw)))

    # Collect every <path> tag, applying the wrapper group's translate only to
    # the paths that actually sit inside that group.
    gx = gy = 0.0
    gm = re.search(r"<g\b[^>]*transform=\"([^\"]*)\"[^>]*>", svg_text)
    g_open, g_close = -1, -1
    if gm:
        gx, gy = _translate(gm.group(1))
        g_open = gm.end()
        g_close = svg_text.find("</g>", g_open)
        if g_close < 0:
            g_close = len(svg_text)

    shapes = []
    for pm in re.finditer(r"<path\b[^>]*?/?>", svg_text, re.S):
        tag = pm.group(0)
        dm = re.search(r'\bd="([^"]*)"', tag)
        if not dm:
            continue
        tm = re.search(r'transform="([^"]*)"', tag)
        tx, ty = _translate(tm.group(1) if tm else "")
        if g_open <= pm.start() < g_close:
            tx, ty = tx + gx, ty + gy
        shapes.append((dm.group(1), tx, ty))

    scale = width / vw
    out = bytearray(width * height)
    for d, tx, ty in shapes:
        subs = parse_path(d)
        edges = []
        for sp in subs:
            pts = [((px + tx - vx0) * scale, (py + ty - vy0) * scale) for px, py in sp]
            for k in range(len(pts) - 1):
                (ax, ay), (bx, by) = pts[k], pts[k + 1]
                if ay != by:
                    edges.append((ax, ay, bx, by))
        if not edges:
            continue
        pix = _fill_even_odd(edges, width, height)
        for idx, v in enumerate(pix):
            if v:
                out[idx] = 1
    mask = Image.frombytes("L", (width, height),
                           bytes(255 if v else 0 for v in out))
    return mask


def _translate(transform: str):
    m = re.search(r"translate\(\s*(-?[\d.]+)[ ,]+(-?[\d.]+)\s*\)", transform or "")
    return (float(m.group(1)), float(m.group(2))) if m else (0.0, 0.0)


def render_file(src: str, dest: str, width: int = 900, bg=(200, 30, 50)) -> None:
    svg = open(src, encoding="utf-8").read()
    mask = rasterise(svg, width)
    img = Image.new("RGB", mask.size, bg)
    white = Image.new("RGB", mask.size, (255, 255, 255))
    img.paste(white, (0, 0), mask)
    img.save(dest)
    ink = sum(1 for p in mask.getdata() if p)
    print(f"{src} -> {dest}  {mask.size}  ink {ink / (mask.size[0] * mask.size[1]):.1%}")


if __name__ == "__main__":
    a = sys.argv[1:]
    render_file(a[0], a[1], int(a[2]) if len(a) > 2 else 900)
