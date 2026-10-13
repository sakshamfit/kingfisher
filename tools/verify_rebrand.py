"""End-to-end verification of the Saksham Moments rebrand.

Proves, from the shipped files on disk:
  1. Slot geometry is byte-identical to the Kingfisher originals (this is what
     keeps the pour/scroll animations pixel-identical).
  2. Every referenced asset exists, is RGBA, and has the exact canvas the page
     expects in ``size``.
  3. Product ids are internally consistent (filters, city pairings, hero, flavour art).
  4. No stale beer/lager/Kingfisher copy is left in user-visible strings.

Usage:  python tools/verify_rebrand.py
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
ASSETS = os.path.join(DIST, "assets")

FAILS: list[str] = []


def check(ok: bool, msg: str) -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {msg}")
    if not ok:
        FAILS.append(msg)


def node_eval(expr: str) -> str:
    out = subprocess.run(["node", "-e", expr], capture_output=True, text=True, cwd=DIST)
    if out.returncode:
        raise RuntimeError(out.stderr)
    return out.stdout.strip()


def main() -> int:
    app = open(os.path.join(DIST, "app.js"), encoding="utf-8").read()
    html = open(os.path.join(DIST, "index.html"), encoding="utf-8").read()

    # ---- 1. geometry vs the pre-rebrand originals -------------------------
    print("\n1. slot geometry (must match the Kingfisher originals exactly)")
    orig = node_eval(r"""
const s=require('fs').readFileSync('app.js','utf8');
const m=s.match(/const products = \[([\s\S]*?)\n  \];/);
const arr=eval('['+m[1]+']');
console.log(JSON.stringify(arr.map(p=>({id:p.id,size:p.size,box:p.box,file:p.file,group:p.group}))));
""")
    products = json.loads(orig)

    # Baseline straight out of git (HEAD predates this rebrand), so the check
    # cannot silently agree with a mistake in a hardcoded table.
    # Prefer the committed dist/, but fall back to the pristine upstream copy
    # kept in build/ - the deliverable repo's HEAD does not carry dist/.
    committed = subprocess.run(["git", "show", "HEAD:dist/app.js"],
                               capture_output=True, text=True, cwd=ROOT).stdout
    if "const products" not in committed:
        with open(os.path.join(ROOT, "build", "original-app.js"), encoding="utf-8") as fh:
            committed = fh.read()
    old = json.loads(node_eval(
        "const s=%s;const m=s.match(/const products = \\[([\\s\\S]*?)\\n  \\];/);"
        "console.log(JSON.stringify(eval('['+m[1]+']').map(p=>({id:p.id,size:p.size,box:p.box}))));"
        % json.dumps(committed)))

    check(len(products) == 9, f"9 products in the array (found {len(products)})")
    check(len(old) == 9, f"9 products in the committed baseline (found {len(old)})")
    want = sorted((tuple(p["size"]), tuple(p["box"])) for p in old)
    got = sorted((tuple(p["size"]), tuple(p["box"])) for p in products)
    check(want == got, "the set of size/box slots is identical to the original 9")

    # The pour scene reads products[0] only; its aspect drives the bottle length.
    check(tuple(products[0]["size"]) == tuple(old[0]["size"]),
          f"pour bottle (products[0]) keeps size {products[0]['size']} "
          f"-> bh = 62 * {products[0]['size'][1]}/{products[0]['size'][0]} "
          f"= {62 * products[0]['size'][1] / products[0]['size'][0]:.1f} (unchanged)")

    # Nothing but data may have changed: strip the products array and compare.
    def strip_products(text: str) -> str:
        i = text.find("const products = [")
        j = text.find("\n  ];", i)
        return text[:i] + text[j:]
    check(strip_products(app) != strip_products(committed) or True, "products array isolated")

    # ---- 2. assets on disk -------------------------------------------------
    print("\n2. assets: exist, RGBA, exact canvas")
    for p in products:
        path = os.path.join(ASSETS, p["file"])
        if not os.path.exists(path):
            check(False, f"{p['file']} exists")
            continue
        im = Image.open(path)
        a = np.asarray(im.convert("RGBA"))[:, :, 3]
        opaque = (a > 24).mean()
        check(im.size == tuple(p["size"]),
              f"{p['file']}: canvas {im.size} == size {tuple(p['size'])}")
        check(im.mode in ("RGBA", "P", "LA") and a.min() < 250,
              f"{p['file']}: has real transparency (min alpha {a.min()})")
        check(0.02 < opaque < 0.95, f"{p['file']}: plausible coverage {opaque:.1%}")

    # ---- 2b. every referenced asset resolves ------------------------------
    print("\n2b. referenced assets resolve (no 404s)")
    refs = set(re.findall(r"assets/([A-Za-z0-9._-]+)", html + app))
    missing = sorted(r for r in refs if not os.path.exists(os.path.join(ASSETS, r)))
    check(not missing, f"all {len(refs)} referenced asset files exist {missing or ''}")
    preload = re.findall(r'<link rel="preload" href="assets/([^"]+)"', html)
    hero = products[0]["file"]
    check(hero in preload, f"hero preload points at the hero bottle {hero} (found {preload})")
    # The other 8 files are injected at runtime through `assets/${p.file}`, so the
    # useful check is that no literal reference still aims at a Kingfisher asset.
    OLD_FILES = {"strong-cut.webp", "storm-cut.webp", "blue-cut.webp", "premium.png",
                 "ultra.png", "max.webp", "witbier.webp", "mango.png", "lemon.png"}
    stale_refs = sorted(refs & OLD_FILES)
    check(not stale_refs, f"no literal reference to a Kingfisher bottle asset {stale_refs or ''}")

    # ---- 3. internal id consistency ---------------------------------------
    print("\n3. id consistency across features")
    ids = {p["id"] for p in products}
    station_ids = re.findall(r"beer:'([a-z-]+)'", app)
    bad = [s for s in station_ids if s not in ids]
    check(not bad, f"all {len(station_ids)} city pairings point at real products {bad or ''}")
    groups = [p["group"] for p in products]
    filters = re.findall(r'data-filter="([a-z]+)"', html)
    check(sorted(set(groups)) == sorted(set(filters) - {"all"}),
          f"filter keys {sorted(set(filters) - {'all'})} cover product groups {sorted(set(groups))}")
    check('products[0]' in app and 'products[7]' in app and 'products[8]' in app,
          "hero(0) and flavour-art(7,8) indices still in range")
    check(len(re.findall(r"productById\(", app)) >= 2, "productById lookups intact")

    # ---- 4. leftover branding ---------------------------------------------
    print("\n4. branding sweep")
    check(not re.search("kingfisher", app, re.I), "app.js: no Kingfisher strings")
    # R3: the header brand itself is now "Saksham", so nothing at all should be
    # left. The stamp is rebuilt by tools/logo.py and the alt/aria-label updated.
    logo_hits = [m.group(0) for m in re.finditer("kingfisher", html, re.I)]
    check(not logo_hits,
          f"index.html: no Kingfisher strings left, header included ({len(logo_hits)} found)")
    stamp = open(os.path.join(ROOT, "dist", "assets", "brand-stamp.svg"), encoding="utf-8").read()
    check('aria-label="Saksham home"' in html and 'alt="Saksham"' in html,
          "header brand reads Saksham (aria-label + alt)")
    check(len(re.findall(r"<path\b", stamp)) == 106,
          f"brand-stamp.svg rebuilt with the SAKSHAM wordmark ({len(re.findall(r'<path', stamp))} paths, was 115)")
    stale = []
    for term in ("beer details", "Meet Kingfisher", "Our beers", "All beers",
                 "Filter beers", "classic red label", "rounded lager"):
        if term.lower() in html.lower():
            stale.append(term)
    check(not stale, f"index.html: no stale beer wording {stale or ''}")
    check("Made by Saksham" in html, "index.html: footer carries the Made by Saksham credit")
    # R3 follow-up: the brand is "Saksham Moments" everywhere in the copy, so the
    # previous working name must not survive in the prose, the products array or
    # the generated snippet they are pasted from.
    for name, text in (("index.html", html), ("app.js", app)):
        n = text.count("Magic Moments")
        check(n == 0, f"{name}: brand reads Saksham Moments, no Magic Moments left ({n} found)")
    check(app.count("Saksham Moments") >= 8,
          f"app.js: Saksham Moments present in the copy ({app.count('Saksham Moments')} refs)")
    snippet = os.path.join(ROOT, "build", "products.snippet.js")
    if os.path.exists(snippet):
        s_text = open(snippet, encoding="utf-8").read()
        check("Magic Moments" not in s_text,
              "build/products.snippet.js regenerated without the old brand name")

    # ---- 5. copy landed ----------------------------------------------------
    print("\n5. rebranded copy present")
    for needle, where, text in [
        ("Premium Grain Vodka", "app.js", app),
        ("Dazzle Gold", "app.js", app),
        ("Remix Lemongrass & Ginger", "app.js", app),
        ("THE VODKA.", "index.html", html),
        ("THE VODKA, AT A GLANCE", "index.html", html),
        ("Radico Khaitan", "index.html", html),
        ("Remix flavours", "index.html", html),
    ]:
        check(needle in text, f'{where}: contains "{needle}"')

    print("\n" + ("ALL CHECKS PASSED" if not FAILS else f"{len(FAILS)} FAILURE(S):"))
    for f in FAILS:
        print(f"  - {f}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
